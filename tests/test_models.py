"""T050 — Tests for dataclass properties and config validation."""

import pytest
from models import (
    UserProfile, ModelAssumptions, TaxEstimate, ProjectionData,
    OptimizationResult, BreakevenResult, CalculationResults, TokenTracker,
    FilingStatus, PipelinePhase, Assessment,
)


class TestUserProfileMissingRequired:
    def test_all_missing_when_default(self):
        p = UserProfile()
        assert set(p.missing_required) == {
            "current_age", "retirement_age", "filing_status",
            "state", "annual_income", "trad_ira_balance",
        }

    def test_none_missing_when_filled(self):
        p = UserProfile(
            current_age=55, retirement_age=65, filing_status="single",
            state="CA", annual_income=100000, trad_ira_balance=500000,
        )
        assert p.missing_required == []

    def test_partial_missing(self):
        p = UserProfile(current_age=55, state="CA")
        assert "retirement_age" in p.missing_required
        assert "current_age" not in p.missing_required


class TestUserProfileHasConversionSpec:
    def test_no_conversion(self):
        p = UserProfile()
        assert p.has_conversion_spec is False

    def test_with_amount(self):
        p = UserProfile(conversion_amount=50000)
        assert p.has_conversion_spec is True

    def test_with_schedule(self):
        p = UserProfile(conversion_schedule=[50000, 50000])
        assert p.has_conversion_spec is True

    def test_with_both(self):
        p = UserProfile(conversion_amount=50000, conversion_schedule=[30000])
        assert p.has_conversion_spec is True


class TestUserProfileToToolArgs:
    def test_excludes_none_values(self):
        p = UserProfile(current_age=55, annual_income=100000)
        args = p.to_tool_args()
        assert "current_age" in args
        assert "annual_income" in args
        assert "retirement_age" not in args
        assert "filing_status" not in args

    def test_includes_default_values(self):
        p = UserProfile()
        args = p.to_tool_args()
        assert "annual_return" in args
        assert args["annual_return"] == 0.07

    def test_excludes_required_fields_list(self):
        p = UserProfile(current_age=55)
        args = p.to_tool_args()
        assert "REQUIRED_FIELDS" not in args


class TestTokenTracker:
    def test_initial_cost_zero(self):
        t = TokenTracker()
        assert t.estimated_cost == 0.0

    def test_cost_calculation(self):
        t = TokenTracker()
        t.total_prompt_tokens = 1_000_000
        t.total_completion_tokens = 1_000_000
        # $0.15/M prompt + $0.60/M completion = $0.75
        assert t.estimated_cost == pytest.approx(0.75, abs=0.01)


class TestEnums:
    def test_filing_status_values(self):
        assert FilingStatus.SINGLE.value == "single"
        assert FilingStatus.MARRIED_JOINT.value == "married_joint"
        assert FilingStatus.MARRIED_SEPARATE.value == "married_separate"
        assert FilingStatus.HEAD_OF_HOUSEHOLD.value == "head_of_household"

    def test_pipeline_phase_values(self):
        assert PipelinePhase.COLLECTING.value == "collecting"
        assert PipelinePhase.ANALYZING.value == "analyzing"
        assert PipelinePhase.COMPLETE.value == "complete"

    def test_assessment_values(self):
        assert Assessment.WORTH_IT.value == "worth_it"
        assert Assessment.MARGINAL.value == "marginal"
        assert Assessment.NOT_WORTH_IT.value == "not_worth_it"


class TestConfigValidation:
    def test_config_loads(self):
        from config import OPENAI_MODEL, OPENAI_TIMEOUT, MAX_SESSION_COST
        assert isinstance(OPENAI_MODEL, str)
        assert isinstance(OPENAI_TIMEOUT, int)
        assert isinstance(MAX_SESSION_COST, float)

    def test_config_defaults(self):
        from config import OPENAI_MODEL, OPENAI_TIMEOUT
        assert OPENAI_MODEL  # non-empty
        assert OPENAI_TIMEOUT > 0
