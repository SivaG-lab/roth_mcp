"""
T025 -- Tests for the 6 MCP tool functions (bypass MCP transport, call directly).

Tests cover:
  - validate_projection_inputs: complete/incomplete/error status, dual-return format
  - estimate_tax_components: federal+state tax breakdown, all expected keys
  - analyze_roth_projections: year-by-year projections, summary fields
  - optimize_conversion_schedule: optimal schedule, converged/confidence fields
  - breakeven_analysis: breakeven_years, assessment values
  - generate_conversion_report: full report assembly, missing section handling

Each tool returns a JSON string in dual-return format:
  {"display": "<html>...</html>", "data": {...}}
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

def _parse_result(result: str) -> dict:
    """Parse a tool result JSON string and return the full envelope."""
    parsed = json.loads(result)
    assert isinstance(parsed, dict), "Tool result must be a JSON object"
    return parsed


def _assert_dual_return(result: str) -> dict:
    """Assert that a result has valid dual-return format and return parsed dict."""
    parsed = _parse_result(result)
    assert "display" in parsed, "Dual-return must contain 'display' key"
    assert "data" in parsed, "Dual-return must contain 'data' key"
    assert isinstance(parsed["data"], dict), "'data' must be a dict"
    assert isinstance(parsed["display"], str), "'display' must be a string"
    return parsed


def _complete_validate_args(**overrides) -> dict:
    """Return a complete set of valid arguments for validate_projection_inputs."""
    base = dict(
        current_age=55,
        retirement_age=65,
        filing_status="married_joint",
        state="CA",
        annual_income=150_000,
        trad_ira_balance=500_000,
        conversion_amount=50_000,
    )
    base.update(overrides)
    return base


# ===========================================================================
# Tool 1: validate_projection_inputs
# ===========================================================================

class TestValidateProjectionInputs:
    """Test validate_projection_inputs tool function."""

    def test_complete_inputs_returns_complete_status(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = _assert_dual_return(result)
        assert parsed["data"]["status"] == "complete"

    def test_complete_inputs_no_errors(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = _assert_dual_return(result)
        assert parsed["data"]["errors"] == []

    def test_complete_inputs_no_missing(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = _assert_dual_return(result)
        assert parsed["data"]["missing"] == []

    def test_missing_required_field_returns_incomplete(self):
        args = _complete_validate_args()
        del args["current_age"]
        result = validate_projection_inputs(**args)
        parsed = _assert_dual_return(result)
        assert parsed["data"]["status"] == "incomplete"
        assert "current_age" in parsed["data"]["missing"]

    def test_invalid_input_returns_errors(self):
        result = validate_projection_inputs(**_complete_validate_args(current_age=5))
        parsed = _assert_dual_return(result)
        assert len(parsed["data"]["errors"]) > 0

    def test_result_has_inputs_key(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = _assert_dual_return(result)
        assert "inputs" in parsed["data"]
        assert isinstance(parsed["data"]["inputs"], dict)

    def test_result_has_assumptions_key(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = _assert_dual_return(result)
        assert "assumptions" in parsed["data"]
        assert isinstance(parsed["data"]["assumptions"], dict)

    def test_result_has_auto_filled_key(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = _assert_dual_return(result)
        assert "auto_filled" in parsed["data"]
        assert isinstance(parsed["data"]["auto_filled"], dict)

    def test_display_contains_html(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = _assert_dual_return(result)
        assert "<" in parsed["display"] and ">" in parsed["display"]


# ===========================================================================
# Tool 2: estimate_tax_components
# ===========================================================================

class TestEstimateTaxComponents:
    """Test estimate_tax_components tool function."""

    def test_mfj_150k_income_50k_conversion_ca(self):
        """$150k MFJ income + $50k conversion in CA produces positive taxes."""
        result = estimate_tax_components(
            annual_income=150_000,
            conversion_amount=50_000,
            filing_status="married_joint",
            state="CA",
        )
        parsed = _assert_dual_return(result)
        data = parsed["data"]
        assert data["federal_tax"] > 0
        assert data["state_tax"] > 0
        assert data["total_tax_cost"] > 0

    def test_result_has_all_expected_keys(self):
        result = estimate_tax_components(
            annual_income=100_000,
            conversion_amount=25_000,
            filing_status="single",
            state="NY",
        )
        parsed = _assert_dual_return(result)
        data = parsed["data"]
        expected_keys = [
            "federal_tax",
            "state_tax",
            "total_tax_cost",
            "effective_rate",
            "marginal_rate",
            "bracket_before",
            "bracket_after",
            "conversion_amount",
        ]
        for key in expected_keys:
            assert key in data, f"Missing expected key: {key}"

    def test_effective_rate_is_fraction(self):
        """Effective rate should be between 0 and 1 (a fraction, not percentage)."""
        result = estimate_tax_components(
            annual_income=150_000,
            conversion_amount=50_000,
            filing_status="married_joint",
            state="CA",
        )
        parsed = _assert_dual_return(result)
        rate = parsed["data"]["effective_rate"]
        assert 0 <= rate <= 1.0

    def test_dual_return_format(self):
        result = estimate_tax_components(
            annual_income=80_000,
            conversion_amount=20_000,
            filing_status="single",
            state="TX",
        )
        parsed = _assert_dual_return(result)
        # TX has no state income tax
        assert parsed["data"]["state_tax"] == 0.0 or parsed["data"]["state_tax"] == 0

    def test_zero_conversion_in_no_tax_state(self):
        """TX has no state income tax, so state_tax should be 0."""
        result = estimate_tax_components(
            annual_income=100_000,
            conversion_amount=30_000,
            filing_status="single",
            state="TX",
        )
        parsed = _assert_dual_return(result)
        assert parsed["data"]["state_tax"] == 0 or parsed["data"]["state_tax"] == 0.0


# ===========================================================================
# Tool 3: analyze_roth_projections
# ===========================================================================

class TestAnalyzeRothProjections:
    """Test analyze_roth_projections tool function."""

    def test_valid_projection_returns_entries(self):
        result = analyze_roth_projections(
            trad_ira_balance=500_000,
            conversion_schedule=[50_000, 50_000, 50_000],
            annual_return=0.07,
            model_years=30,
            current_age=55,
            federal_tax=5_500,
            state_tax=2_000,
        )
        parsed = _assert_dual_return(result)
        data = parsed["data"]
        assert "projections" in data
        assert isinstance(data["projections"], list)
        assert len(data["projections"]) > 0

    def test_summary_has_all_keys(self):
        result = analyze_roth_projections(
            trad_ira_balance=500_000,
            conversion_schedule=[50_000],
            annual_return=0.07,
            model_years=20,
            current_age=55,
            federal_tax=5_500,
            state_tax=2_000,
        )
        parsed = _assert_dual_return(result)
        summary = parsed["data"]["summary"]
        expected_keys = [
            "final_roth_value",
            "final_trad_value",
            "net_benefit",
            "crossover_year",
        ]
        for key in expected_keys:
            assert key in summary, f"Missing summary key: {key}"

    def test_model_years_determines_projection_length(self):
        """Number of projection entries should relate to model_years."""
        model_years = 15
        result = analyze_roth_projections(
            trad_ira_balance=300_000,
            conversion_schedule=[30_000],
            annual_return=0.07,
            model_years=model_years,
            current_age=50,
            federal_tax=3_000,
            state_tax=1_500,
        )
        parsed = _assert_dual_return(result)
        projections = parsed["data"]["projections"]
        assert len(projections) == model_years

    def test_dual_return_format(self):
        result = analyze_roth_projections(
            trad_ira_balance=500_000,
            conversion_schedule=[50_000],
            annual_return=0.07,
            model_years=10,
            current_age=55,
            federal_tax=5_000,
            state_tax=2_000,
        )
        _assert_dual_return(result)


# ===========================================================================
# Tool 4: optimize_conversion_schedule
# ===========================================================================

class TestOptimizeConversionSchedule:
    """Test optimize_conversion_schedule tool function."""

    def test_returns_optimal_schedule_list(self):
        result = optimize_conversion_schedule(
            trad_ira_balance=500_000,
            annual_income=150_000,
            filing_status="married_joint",
            state="CA",
            current_age=55,
            retirement_age=65,
        )
        parsed = _assert_dual_return(result)
        data = parsed["data"]
        assert "optimal_schedule" in data
        assert isinstance(data["optimal_schedule"], list)
        assert len(data["optimal_schedule"]) > 0

    def test_converged_is_bool(self):
        result = optimize_conversion_schedule(
            trad_ira_balance=500_000,
            annual_income=150_000,
            filing_status="married_joint",
            state="CA",
            current_age=55,
            retirement_age=65,
        )
        parsed = _assert_dual_return(result)
        assert isinstance(parsed["data"]["converged"], bool)

    def test_confidence_is_float(self):
        result = optimize_conversion_schedule(
            trad_ira_balance=500_000,
            annual_income=150_000,
            filing_status="married_joint",
            state="CA",
            current_age=55,
            retirement_age=65,
        )
        parsed = _assert_dual_return(result)
        confidence = parsed["data"]["confidence"]
        assert isinstance(confidence, (int, float))
        assert 0.0 <= confidence <= 1.0

    def test_total_tax_cost_present(self):
        result = optimize_conversion_schedule(
            trad_ira_balance=500_000,
            annual_income=150_000,
            filing_status="married_joint",
            state="CA",
            current_age=55,
            retirement_age=65,
        )
        parsed = _assert_dual_return(result)
        assert "total_tax_cost" in parsed["data"]
        assert isinstance(parsed["data"]["total_tax_cost"], (int, float))

    def test_dual_return_format(self):
        result = optimize_conversion_schedule(
            trad_ira_balance=300_000,
            annual_income=100_000,
            filing_status="single",
            state="TX",
            current_age=50,
            retirement_age=65,
        )
        _assert_dual_return(result)


# ===========================================================================
# Tool 5: breakeven_analysis
# ===========================================================================

class TestBreakevenAnalysis:
    """Test breakeven_analysis tool function."""

    def test_returns_valid_assessment(self):
        result = breakeven_analysis(
            conversion_amount=50_000,
            total_tax_cost=12_000,
            current_age=55,
            annual_return=0.07,
            retirement_age=65,
            future_tax_rate=0.22,
            federal_tax=8_000,
            state_tax=4_000,
        )
        parsed = _assert_dual_return(result)
        assessment = parsed["data"]["assessment"]
        assert assessment in ("worth_it", "marginal", "not_worth_it")

    def test_breakeven_years_is_non_negative_int(self):
        result = breakeven_analysis(
            conversion_amount=50_000,
            total_tax_cost=12_000,
            current_age=55,
            annual_return=0.07,
            retirement_age=65,
            future_tax_rate=0.22,
            federal_tax=8_000,
            state_tax=4_000,
        )
        parsed = _assert_dual_return(result)
        years = parsed["data"]["breakeven_years"]
        assert isinstance(years, int)
        assert years >= 0

    def test_breakeven_age_present(self):
        result = breakeven_analysis(
            conversion_amount=50_000,
            total_tax_cost=12_000,
            current_age=55,
            annual_return=0.07,
            retirement_age=65,
            future_tax_rate=0.22,
            federal_tax=8_000,
            state_tax=4_000,
        )
        parsed = _assert_dual_return(result)
        assert "breakeven_age" in parsed["data"]
        assert isinstance(parsed["data"]["breakeven_age"], int)

    def test_dual_return_format(self):
        result = breakeven_analysis(
            conversion_amount=30_000,
            total_tax_cost=7_000,
            current_age=50,
            annual_return=0.07,
            retirement_age=65,
            future_tax_rate=0.24,
            federal_tax=5_000,
            state_tax=2_000,
        )
        _assert_dual_return(result)


# ===========================================================================
# Tool 6: generate_conversion_report
# ===========================================================================

class TestGenerateConversionReport:
    """Test generate_conversion_report tool function."""

    def test_with_all_sections(self):
        """Providing all 5 JSON-string inputs produces a full report."""
        validated = json.dumps({
            "status": "complete",
            "inputs": {
                "current_age": 55,
                "retirement_age": 65,
                "filing_status": "married_joint",
                "state": "CA",
                "annual_income": 150_000,
                "trad_ira_balance": 500_000,
                "conversion_schedule": [50_000],
            },
            "assumptions": {"annual_return": 0.07, "model_years": 30},
            "auto_filled": {},
            "missing": [],
            "errors": [],
        })
        tax = json.dumps({
            "federal_tax": 5_500,
            "state_tax": 2_000,
            "total_tax_cost": 7_500,
            "effective_rate": 0.15,
            "marginal_rate": 0.22,
            "bracket_before": "22%",
            "bracket_after": "22%",
            "conversion_amount": 50_000,
        })
        projection = json.dumps({
            "projections": [
                {"year": 1, "age": 56, "conversion": 50_000,
                 "roth_balance": 35_260, "trad_balance": 481_500,
                 "tax_paid": 5_500, "rmd_amount": 0},
            ],
            "summary": {
                "final_roth_value": 450_000,
                "final_trad_value": 380_000,
                "net_benefit": 70_000,
                "crossover_year": 12,
            },
        })
        optimization = json.dumps({
            "optimal_schedule": [50_000, 50_000, 50_000],
            "total_tax_cost": 22_500,
            "tax_saved_vs_baseline": 5_000,
            "converged": True,
            "confidence": 1.0,
        })
        be = json.dumps({
            "breakeven_years": 8,
            "breakeven_age": 63,
            "assessment": "worth_it",
        })

        result = generate_conversion_report(
            validated_inputs=validated,
            tax_analysis=tax,
            projection_data=projection,
            optimization_data=optimization,
            breakeven_data=be,
        )
        parsed = _assert_dual_return(result)
        assert "summary" in parsed["data"]

    def test_display_contains_html(self):
        """The display field should contain HTML markup for the report."""
        validated = json.dumps({
            "status": "complete",
            "inputs": {"current_age": 55, "filing_status": "married_joint"},
            "assumptions": {},
            "auto_filled": {},
            "missing": [],
            "errors": [],
        })
        tax = json.dumps({
            "federal_tax": 5_500,
            "state_tax": 2_000,
            "total_tax_cost": 7_500,
            "effective_rate": 0.15,
            "marginal_rate": 0.22,
            "bracket_before": "22%",
            "bracket_after": "22%",
            "conversion_amount": 50_000,
        })
        result = generate_conversion_report(
            validated_inputs=validated,
            tax_analysis=tax,
        )
        parsed = _assert_dual_return(result)
        display = parsed["display"]
        assert "<" in display and ">" in display

    def test_handles_missing_sections_gracefully(self):
        """When some sections are omitted, the report should still generate
        without raising an error."""
        validated = json.dumps({
            "status": "complete",
            "inputs": {"current_age": 55},
            "assumptions": {},
            "auto_filled": {},
            "missing": [],
            "errors": [],
        })
        result = generate_conversion_report(
            validated_inputs=validated,
        )
        parsed = _assert_dual_return(result)
        # Should not raise, and should still return a valid dual-return
        assert isinstance(parsed["data"], dict)

    def test_handles_empty_string_sections(self):
        """When sections are provided as empty strings, report still works."""
        result = generate_conversion_report(
            validated_inputs="",
            tax_analysis="",
            projection_data="",
            optimization_data="",
            breakeven_data="",
        )
        parsed = _assert_dual_return(result)
        assert isinstance(parsed["data"], dict)
