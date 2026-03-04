"""
MCP roundtrip integration tests -- call tool functions directly (no MCP transport).

Tests verify the full pipeline flow, tool chaining, and partial/edge-case
input scenarios.  Each tool returns a JSON string with the dual-return
envelope: {"display": "<html>", "data": {...}}.
"""

import json
import pytest

from mcp_server import (
    validate_projection_inputs,
    estimate_tax_components,
    analyze_roth_projections,
    optimize_conversion_schedule,
    breakeven_analysis,
    generate_conversion_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(result: str) -> dict:
    """Parse a tool result and assert it has the dual-return shape."""
    parsed = json.loads(result)
    assert "display" in parsed, "Missing 'display' key in dual-return"
    assert "data" in parsed, "Missing 'data' key in dual-return"
    assert isinstance(parsed["display"], str)
    assert isinstance(parsed["data"], dict)
    return parsed


# ===========================================================================
# 1. TestEndToEndFlow
# ===========================================================================

class TestEndToEndFlow:
    """Full pipeline: validate -> tax -> projections -> optimize -> breakeven -> report."""

    # Shared test profile
    PROFILE = dict(
        current_age=55,
        retirement_age=65,
        filing_status="married_joint",
        state="CA",
        annual_income=150_000,
        trad_ira_balance=500_000,
        conversion_amount=50_000,
    )

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self):
        """Call all 6 tools in sequence; verify each returns valid dual-return
        JSON and that data flows correctly between stages."""

        # --- Step 1: validate ---
        validate_result = validate_projection_inputs(**self.PROFILE)
        v_parsed = _parse(validate_result)
        v_data = v_parsed["data"]
        assert v_data["status"] == "complete"
        assert v_data["errors"] == []
        assert v_data["missing"] == []
        assert "inputs" in v_data
        assert "assumptions" in v_data

        validated_inputs = v_data["inputs"]

        # --- Step 2: tax estimate ---
        tax_result = estimate_tax_components(
            annual_income=validated_inputs["annual_income"],
            conversion_amount=validated_inputs["conversion_schedule"][0],
            filing_status=validated_inputs["filing_status"],
            state=validated_inputs["state"],
        )
        t_parsed = _parse(tax_result)
        t_data = t_parsed["data"]
        assert t_data["federal_tax"] > 0, "Federal tax must be positive"
        assert t_data["state_tax"] > 0, "CA state tax must be positive"
        assert t_data["total_tax_cost"] > 0
        assert 0 <= t_data["effective_rate"] <= 1.0

        # --- Step 3: projections ---
        proj_result = analyze_roth_projections(
            trad_ira_balance=validated_inputs["trad_ira_balance"],
            roth_ira_balance_initial=validated_inputs.get("roth_ira_balance_initial", 0),
            conversion_schedule=validated_inputs["conversion_schedule"],
            annual_return=v_data["assumptions"]["annual_return"],
            model_years=v_data["assumptions"]["model_years"],
            current_age=validated_inputs["current_age"],
            annual_income=validated_inputs["annual_income"],
            filing_status=validated_inputs["filing_status"],
            state=validated_inputs["state"],
        )
        p_parsed = _parse(proj_result)
        p_data = p_parsed["data"]
        assert "projections" in p_data
        assert len(p_data["projections"]) == v_data["assumptions"]["model_years"]
        assert "summary" in p_data
        assert "final_roth_value" in p_data["summary"]
        assert "net_benefit" in p_data["summary"]

        # --- Step 4: optimize ---
        opt_result = optimize_conversion_schedule(
            trad_ira_balance=validated_inputs["trad_ira_balance"],
            annual_income=validated_inputs["annual_income"],
            filing_status=validated_inputs["filing_status"],
            state=validated_inputs["state"],
            current_age=validated_inputs["current_age"],
            retirement_age=validated_inputs["retirement_age"],
            annual_return=v_data["assumptions"]["annual_return"],
        )
        o_parsed = _parse(opt_result)
        o_data = o_parsed["data"]
        assert "optimal_schedule" in o_data
        assert isinstance(o_data["optimal_schedule"], list)
        assert len(o_data["optimal_schedule"]) > 0
        assert "total_tax_cost" in o_data
        assert isinstance(o_data["converged"], bool)
        assert 0.0 <= o_data["confidence"] <= 1.0

        # --- Step 5: breakeven ---
        be_result = breakeven_analysis(
            conversion_amount=validated_inputs["conversion_schedule"][0],
            total_tax_cost=t_data["total_tax_cost"],
            current_age=validated_inputs["current_age"],
            annual_return=v_data["assumptions"]["annual_return"],
            retirement_age=validated_inputs["retirement_age"],
        )
        b_parsed = _parse(be_result)
        b_data = b_parsed["data"]
        assert "breakeven_years" in b_data
        assert isinstance(b_data["breakeven_years"], int)
        assert b_data["breakeven_years"] >= 0
        assert "breakeven_age" in b_data
        assert b_data["assessment"] in ("worth_it", "marginal", "not_worth_it")

        # --- Step 6: report ---
        report_result = generate_conversion_report(
            validated_inputs=validate_result,
            tax_analysis=tax_result,
            projection_data=proj_result,
            optimization_data=opt_result,
            breakeven_data=be_result,
        )
        r_parsed = _parse(report_result)
        r_data = r_parsed["data"]
        assert "summary" in r_data
        summary = r_data["summary"]
        assert summary["total_tax_cost"] > 0
        assert "sections_included" in summary
        # All five sections should be present
        for section in ("inputs", "tax", "projection", "optimization", "breakeven"):
            assert section in summary["sections_included"], (
                f"Section '{section}' missing from report"
            )
        # Display should contain HTML
        assert "<" in r_parsed["display"] and ">" in r_parsed["display"]


# ===========================================================================
# 2. TestToolChaining
# ===========================================================================

class TestToolChaining:
    """Verify output from one tool feeds correctly into the next."""

    PROFILE = dict(
        current_age=55,
        retirement_age=65,
        filing_status="married_joint",
        state="CA",
        annual_income=150_000,
        trad_ira_balance=500_000,
        conversion_amount=50_000,
    )

    @pytest.mark.asyncio
    async def test_validation_feeds_tax(self):
        """validate_projection_inputs output drives estimate_tax_components."""
        v_result = validate_projection_inputs(**self.PROFILE)
        v_data = _parse(v_result)["data"]
        inputs = v_data["inputs"]

        # Feed validated fields into tax tool
        tax_result = estimate_tax_components(
            annual_income=inputs["annual_income"],
            conversion_amount=inputs["conversion_schedule"][0],
            filing_status=inputs["filing_status"],
            state=inputs["state"],
            social_security=inputs.get("social_security", 0),
            rmd=inputs.get("rmd", 0),
        )
        t_parsed = _parse(tax_result)
        t_data = t_parsed["data"]

        assert t_data["federal_tax"] > 0
        assert t_data["total_tax_cost"] > 0
        assert "conversion_amount" in t_data
        assert t_data["conversion_amount"] == inputs["conversion_schedule"][0]

    @pytest.mark.asyncio
    async def test_tax_feeds_projections(self):
        """estimate_tax_components output feeds into analyze_roth_projections."""
        tax_result = estimate_tax_components(
            annual_income=150_000,
            conversion_amount=50_000,
            filing_status="married_joint",
            state="CA",
        )
        t_data = _parse(tax_result)["data"]

        proj_result = analyze_roth_projections(
            trad_ira_balance=500_000,
            conversion_schedule=[50_000],
            annual_return=0.07,
            model_years=20,
            current_age=55,
            annual_income=150_000,
            filing_status="married_joint",
            state="CA",
        )
        p_parsed = _parse(proj_result)
        p_data = p_parsed["data"]

        assert len(p_data["projections"]) == 20
        # First year should show the conversion
        first_year = p_data["projections"][0]
        assert first_year["conversion"] == 50_000
        assert first_year["tax_paid"] > 0
        # Summary should be populated
        assert p_data["summary"]["final_roth_value"] > 0

    @pytest.mark.asyncio
    async def test_all_feed_report(self):
        """Collect outputs from all tools and feed into generate_conversion_report."""
        # 1 - validate
        v_raw = validate_projection_inputs(**self.PROFILE)
        v_data = _parse(v_raw)["data"]
        inputs = v_data["inputs"]

        # 2 - tax
        t_raw = estimate_tax_components(
            annual_income=inputs["annual_income"],
            conversion_amount=inputs["conversion_schedule"][0],
            filing_status=inputs["filing_status"],
            state=inputs["state"],
        )
        t_data = _parse(t_raw)["data"]

        # 3 - projections
        p_raw = analyze_roth_projections(
            trad_ira_balance=inputs["trad_ira_balance"],
            conversion_schedule=inputs["conversion_schedule"],
            annual_return=v_data["assumptions"]["annual_return"],
            model_years=v_data["assumptions"]["model_years"],
            current_age=inputs["current_age"],
            annual_income=inputs["annual_income"],
            filing_status=inputs["filing_status"],
            state=inputs["state"],
        )

        # 4 - optimize
        o_raw = optimize_conversion_schedule(
            trad_ira_balance=inputs["trad_ira_balance"],
            annual_income=inputs["annual_income"],
            filing_status=inputs["filing_status"],
            state=inputs["state"],
            current_age=inputs["current_age"],
            retirement_age=inputs["retirement_age"],
        )

        # 5 - breakeven
        b_raw = breakeven_analysis(
            conversion_amount=inputs["conversion_schedule"][0],
            total_tax_cost=t_data["total_tax_cost"],
            current_age=inputs["current_age"],
            annual_return=v_data["assumptions"]["annual_return"],
            retirement_age=inputs["retirement_age"],
        )

        # 6 - report (takes raw JSON strings from each tool)
        report_raw = generate_conversion_report(
            validated_inputs=v_raw,
            tax_analysis=t_raw,
            projection_data=p_raw,
            optimization_data=o_raw,
            breakeven_data=b_raw,
        )
        r_parsed = _parse(report_raw)
        summary = r_parsed["data"]["summary"]

        assert summary["total_tax_cost"] == t_data["total_tax_cost"]
        assert summary["breakeven_years"] == _parse(b_raw)["data"]["breakeven_years"]
        assert summary["assessment"] == _parse(b_raw)["data"]["assessment"]
        assert len(summary["sections_included"]) == 5


# ===========================================================================
# 3. TestPartialInputScenarios
# ===========================================================================

class TestPartialInputScenarios:
    """Edge-case flows: minimal inputs, high income, zero conversion, multi-year."""

    @pytest.mark.asyncio
    async def test_minimum_inputs(self):
        """Only required fields; auto-fill handles the rest."""
        result = validate_projection_inputs(
            current_age=40,
            retirement_age=67,
            filing_status="single",
            state="TX",
            annual_income=75_000,
            trad_ira_balance=200_000,
            conversion_amount=20_000,
        )
        parsed = _parse(result)
        data = parsed["data"]
        assert data["status"] == "complete"
        assert data["errors"] == []

        # Auto-filled fields should be present in inputs
        inputs = data["inputs"]
        assert "social_security" in inputs
        assert "rmd" in inputs

        # Defaults should have been applied in assumptions
        assumptions = data["assumptions"]
        assert assumptions["annual_return"] == 0.07
        assert assumptions["model_years"] == 30

        # Should also work in a downstream tool
        tax_result = estimate_tax_components(
            annual_income=inputs["annual_income"],
            conversion_amount=inputs["conversion_schedule"][0],
            filing_status=inputs["filing_status"],
            state=inputs["state"],
        )
        t_parsed = _parse(tax_result)
        # TX has no state income tax
        assert t_parsed["data"]["state_tax"] == 0 or t_parsed["data"]["state_tax"] == 0.0
        assert t_parsed["data"]["federal_tax"] > 0

    @pytest.mark.asyncio
    async def test_high_income_scenario(self):
        """$500k income should trigger higher tax brackets."""
        result = validate_projection_inputs(
            current_age=50,
            retirement_age=67,
            filing_status="married_joint",
            state="CA",
            annual_income=500_000,
            trad_ira_balance=1_000_000,
            conversion_amount=100_000,
        )
        v_parsed = _parse(result)
        v_data = v_parsed["data"]
        assert v_data["status"] == "complete"
        inputs = v_data["inputs"]

        tax_result = estimate_tax_components(
            annual_income=inputs["annual_income"],
            conversion_amount=inputs["conversion_schedule"][0],
            filing_status=inputs["filing_status"],
            state=inputs["state"],
        )
        t_parsed = _parse(tax_result)
        t_data = t_parsed["data"]

        # At $500k income + $100k conversion, effective rate should be substantial
        assert t_data["federal_tax"] > 0
        assert t_data["state_tax"] > 0
        assert t_data["total_tax_cost"] > 0
        # Marginal rate at this income should be >= 32%
        assert t_data["marginal_rate"] >= 0.32

        # Breakeven should still produce a valid assessment
        be_result = breakeven_analysis(
            conversion_amount=inputs["conversion_schedule"][0],
            total_tax_cost=t_data["total_tax_cost"],
            current_age=inputs["current_age"],
            annual_return=0.07,
            retirement_age=inputs["retirement_age"],
        )
        b_parsed = _parse(be_result)
        assert b_parsed["data"]["assessment"] in ("worth_it", "marginal", "not_worth_it")
        assert b_parsed["data"]["breakeven_age"] > inputs["current_age"]

    @pytest.mark.asyncio
    async def test_zero_conversion(self):
        """$0 conversion amount: projections should run but show no conversions."""
        proj_result = analyze_roth_projections(
            trad_ira_balance=500_000,
            conversion_schedule=[0],
            annual_return=0.07,
            model_years=10,
            current_age=55,
            annual_income=75_000,
            filing_status="single",
            state="CA",
        )
        p_parsed = _parse(proj_result)
        p_data = p_parsed["data"]

        assert len(p_data["projections"]) == 10
        # Every year should have zero conversion
        for entry in p_data["projections"]:
            assert entry["conversion"] == 0
            assert entry["tax_paid"] == 0

        # Roth balance should remain 0 (no contributions, started at 0)
        last = p_data["projections"][-1]
        assert last["roth_balance"] == 0

    @pytest.mark.asyncio
    async def test_multi_year_schedule(self):
        """Multi-year conversion schedule: [50000, 40000, 30000]."""
        schedule = [50_000, 40_000, 30_000]

        # Validate with schedule
        v_result = validate_projection_inputs(
            current_age=55,
            retirement_age=65,
            filing_status="married_joint",
            state="CA",
            annual_income=150_000,
            trad_ira_balance=500_000,
            conversion_schedule=schedule,
        )
        v_parsed = _parse(v_result)
        v_data = v_parsed["data"]
        assert v_data["status"] == "complete"
        assert v_data["inputs"]["conversion_schedule"] == [50_000.0, 40_000.0, 30_000.0]

        # Tax for the first year amount
        tax_result = estimate_tax_components(
            annual_income=150_000,
            conversion_amount=schedule[0],
            filing_status="married_joint",
            state="CA",
        )
        t_data = _parse(tax_result)["data"]

        # Run projections with multi-year schedule
        proj_result = analyze_roth_projections(
            trad_ira_balance=500_000,
            conversion_schedule=schedule,
            annual_return=0.07,
            model_years=20,
            current_age=55,
            annual_income=150_000,
            filing_status="married_joint",
            state="CA",
        )
        p_parsed = _parse(proj_result)
        p_data = p_parsed["data"]
        projections = p_data["projections"]

        assert len(projections) == 20

        # First 3 years should show the scheduled conversions
        assert projections[0]["conversion"] == 50_000
        assert projections[1]["conversion"] == 40_000
        assert projections[2]["conversion"] == 30_000

        # Years after schedule should have zero conversion
        for entry in projections[3:]:
            assert entry["conversion"] == 0

        # Final Roth balance should be positive (received 120k total)
        assert p_data["summary"]["final_roth_value"] > 0
