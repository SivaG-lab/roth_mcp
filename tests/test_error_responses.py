"""T029 — Standardized error response tests."""

from __future__ import annotations

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
from dual_return import error_response


def _parse(result: str) -> dict:
    return json.loads(result)


class TestErrorResponseHelper:
    def test_error_response_structure(self):
        result = error_response("validation_error", "Test message", ["field1"], [{"field": "f", "message": "m"}])
        parsed = _parse(result)
        assert parsed["error"] is True
        assert parsed["error_type"] == "validation_error"
        assert parsed["message"] == "Test message"
        assert parsed["missing_fields"] == ["field1"]
        assert len(parsed["details"]) == 1

    def test_error_response_defaults(self):
        result = error_response("test_error", "msg")
        parsed = _parse(result)
        assert parsed["missing_fields"] == []
        assert parsed["details"] == []


class TestValidateProjectionInputsErrors:
    def test_validation_error_format(self):
        result = validate_projection_inputs(current_age=5, retirement_age=65,
            filing_status="single", state="CA", annual_income=100_000,
            trad_ira_balance=500_000, conversion_amount=50_000)
        parsed = _parse(result)
        assert parsed["error"] is True
        assert parsed["error_type"] == "validation_error"
        assert len(parsed["details"]) > 0


class TestEstimateTaxMissingFields:
    def test_missing_fields_error(self):
        result = estimate_tax_components()
        parsed = _parse(result)
        assert parsed["error"] is True
        assert parsed["error_type"] == "missing_required_fields"
        assert "annual_income" in parsed["missing_fields"]
        assert "conversion_amount" in parsed["missing_fields"]


class TestAnalyzeProjectionsMissingFields:
    def test_missing_fields_error(self):
        result = analyze_roth_projections()
        parsed = _parse(result)
        assert parsed["error"] is True
        assert "trad_ira_balance" in parsed["missing_fields"]
        assert "current_age" in parsed["missing_fields"]


class TestOptimizeMissingFields:
    def test_missing_fields_error(self):
        result = optimize_conversion_schedule()
        parsed = _parse(result)
        assert parsed["error"] is True
        assert parsed["error_type"] == "missing_required_fields"


class TestBreakevenMissingFields:
    def test_missing_fields_error(self):
        result = breakeven_analysis()
        parsed = _parse(result)
        assert parsed["error"] is True
        assert "conversion_amount" in parsed["missing_fields"]
        assert "current_age" in parsed["missing_fields"]


class TestReportMissingFields:
    def test_missing_required_inputs(self):
        result = generate_conversion_report()
        parsed = _parse(result)
        assert parsed["error"] is True
        assert "validated_inputs" in parsed["missing_fields"]
        assert "tax_analysis" in parsed["missing_fields"]
