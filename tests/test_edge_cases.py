"""T046 — Edge-case tests for remediation fixes."""

from __future__ import annotations

import json

import pytest

from mcp_server import (
    validate_projection_inputs,
    estimate_tax_components,
    analyze_roth_projections,
    breakeven_analysis,
)
from dual_return import extract_data, extract_html
from validators import validate_inputs


def _parse(result: str) -> dict:
    return json.loads(result)


# ---------------------------------------------------------------------------
# Zero conversion breakeven
# ---------------------------------------------------------------------------

class TestZeroConversionBreakeven:
    def test_zero_conversion_returns_no_conversion(self):
        result = breakeven_analysis(conversion_amount=0, current_age=55)
        data = _parse(result)["data"]
        assert data["assessment"] == "no_conversion"
        assert data["breakeven_years"] == 0

    def test_negative_conversion_returns_no_conversion(self):
        result = breakeven_analysis(conversion_amount=-1000, current_age=55)
        data = _parse(result)["data"]
        assert data["assessment"] == "no_conversion"


# ---------------------------------------------------------------------------
# Empty schedule validation
# ---------------------------------------------------------------------------

class TestEmptyScheduleValidation:
    def test_empty_schedule_rejected(self):
        result = validate_inputs(
            current_age=55, retirement_age=65,
            filing_status="single", state="CA",
            annual_income=100_000, trad_ira_balance=500_000,
            conversion_schedule=[],
        )
        assert result["status"] == "error"
        assert any("empty" in e["message"].lower() for e in result["errors"])

    def test_schedule_over_50_rejected(self):
        result = validate_inputs(
            current_age=55, retirement_age=65,
            filing_status="single", state="CA",
            annual_income=100_000, trad_ira_balance=10_000_000,
            conversion_schedule=[1000] * 51,
        )
        assert result["status"] == "error"
        assert any("50" in e["message"] for e in result["errors"])


# ---------------------------------------------------------------------------
# Malformed JSON in extract functions
# ---------------------------------------------------------------------------

class TestMalformedJsonExtract:
    def test_extract_html_bad_json(self):
        assert extract_html("not json") == ""

    def test_extract_data_bad_json(self):
        assert extract_data("not json") == {}

    def test_extract_html_none(self):
        assert extract_html(None) == ""

    def test_extract_data_none(self):
        assert extract_data(None) == {}


# ---------------------------------------------------------------------------
# Conversion exceeding balance
# ---------------------------------------------------------------------------

class TestConversionExceedingBalance:
    def test_projection_caps_conversion_at_balance(self):
        """Conversion should be capped at available trad balance."""
        result = analyze_roth_projections(
            trad_ira_balance=10_000,
            conversion_schedule=[50_000],  # much more than balance
            annual_return=0.07,
            model_years=5,
            current_age=55,
            annual_income=75_000,
            filing_status="single",
            state="CA",
        )
        data = _parse(result)["data"]
        # First year conversion should be capped
        first_year = data["projections"][0]
        assert first_year["conversion"] <= 10_000


# ---------------------------------------------------------------------------
# RMD at extreme ages
# ---------------------------------------------------------------------------

class TestRMDExtremeAge:
    def test_compute_rmd_age_over_120(self):
        from tax.rmd import compute_rmd
        # Should not crash, should return some value
        rmd = compute_rmd(130, 100_000)
        assert isinstance(rmd, (int, float))
        assert rmd >= 0


# ---------------------------------------------------------------------------
# XSS protection
# ---------------------------------------------------------------------------

class TestXSSProtection:
    def test_html_escape_in_validation_error(self):
        result = validate_projection_inputs(
            current_age=55,
            retirement_age=65,
            filing_status="<script>alert('xss')</script>",
            state="CA",
            annual_income=100_000,
            trad_ira_balance=500_000,
            conversion_amount=50_000,
        )
        data = _parse(result)
        # Standardized error response — no HTML at all (safe by design)
        assert data.get("error") is True
        assert data["error_type"] == "validation_error"
        assert "<script>" not in json.dumps(data)


# ---------------------------------------------------------------------------
# Anti-hallucination
# ---------------------------------------------------------------------------

class TestAntiHallucination:
    def test_exact_match_not_flagged(self):
        from agent_loop import check_hallucinated_numbers
        tool_results = {"tax": {"federal_tax": 5000.0, "state_tax": 2000.0}}
        response = "Your federal tax is $5,000.00 and state tax is $2,000.00"
        suspicious = check_hallucinated_numbers(response, tool_results)
        assert len(suspicious) == 0

    def test_fabricated_number_flagged(self):
        from agent_loop import check_hallucinated_numbers
        tool_results = {"tax": {"federal_tax": 5000.0}}
        response = "Your tax is $99,999.00"
        suspicious = check_hallucinated_numbers(response, tool_results)
        assert len(suspicious) > 0
