"""Shared test fixtures and helpers for Roth Conversion Calculator tests."""

from __future__ import annotations

import json

import pytest


def complete_profile(**overrides) -> dict:
    """Return a complete set of valid user inputs, with optional overrides."""
    base = dict(
        current_age=55,
        retirement_age=65,
        filing_status="single",
        state="CA",
        annual_income=100_000,
        trad_ira_balance=500_000,
        conversion_amount=50_000,
    )
    base.update(overrides)
    return base


def parse_dual_return(result: str) -> dict:
    """Parse a dual-return JSON string into {display, data}."""
    parsed = json.loads(result)
    assert "display" in parsed, "Missing 'display' in dual-return"
    assert "data" in parsed, "Missing 'data' in dual-return"
    return parsed
