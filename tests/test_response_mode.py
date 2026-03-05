"""T020 — Response mode tests."""

from __future__ import annotations

import json

import pytest

from mcp_server import validate_projection_inputs, estimate_tax_components
from dual_return import dual_return


def _complete_validate_args(**overrides):
    base = dict(
        current_age=55, retirement_age=65, filing_status="single",
        state="CA", annual_income=100_000, trad_ira_balance=500_000,
        conversion_amount=50_000,
    )
    base.update(overrides)
    return base


class TestResponseModeFull:
    def test_full_mode_returns_envelope(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = json.loads(result)
        assert "display" in parsed
        assert "data" in parsed
        assert isinstance(parsed["display"], str)

    def test_full_mode_has_html(self):
        result = validate_projection_inputs(**_complete_validate_args())
        parsed = json.loads(result)
        assert len(parsed["display"]) > 0


class TestDualReturnDataOnlyLogic:
    def test_dual_return_full_mode(self):
        # Direct test of dual_return with full mode (default)
        result = dual_return("<b>test</b>", {"key": "value"})
        parsed = json.loads(result)
        assert "display" in parsed
        assert "data" in parsed
        assert parsed["display"] == "<b>test</b>"

    def test_dual_return_none_html_full_mode(self):
        # When html is None in full mode, display should be empty string
        result = dual_return(None, {"key": "value"})
        parsed = json.loads(result)
        assert "display" in parsed
        assert parsed["display"] == ""
        assert parsed["data"]["key"] == "value"
