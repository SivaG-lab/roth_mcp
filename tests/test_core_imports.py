"""T045 — Core import independence tests."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock

import pytest


class TestCoreImports:
    def test_config_imports_without_streamlit(self):
        # config.py should not require streamlit
        import config
        assert hasattr(config, "MCP_TRANSPORT")

    def test_validators_imports_without_streamlit(self):
        import validators
        assert hasattr(validators, "FilingStatus")
        assert hasattr(validators, "StateCode")

    def test_dual_return_imports_without_streamlit(self):
        import dual_return
        assert hasattr(dual_return, "dual_return")
        assert hasattr(dual_return, "error_response")

    def test_rate_limiter_imports_without_streamlit(self):
        import rate_limiter
        assert hasattr(rate_limiter, "RateLimiter")

    def test_tax_modules_import_without_streamlit(self):
        import tax.calculator
        import tax.brackets
        import tax.rmd
        import tax.irmaa
        import tax.ss
        import tax.state_rates
