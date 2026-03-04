"""Pipeline orchestration tests and anti-hallucination guard tests.

Tests cover:
  - TestPipelineOrchestration: Verifies tool call order, return structure,
    and partial-failure resilience using a MockExecutor.
  - TestPipelineWithFailures: Verifies pipeline continues when individual
    tools raise exceptions (FailingExecutor).
  - TestAntiHallucination: Verifies check_hallucinated_numbers detects
    dollar amounts, percentages, and breakeven years that do not appear
    in tool results.
"""

import json

import pytest

from pipeline import run_analysis_pipeline
from agent_loop import check_hallucinated_numbers


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

VALIDATED_INPUTS = {
    "status": "complete",
    "inputs": {
        "current_age": 55,
        "retirement_age": 65,
        "filing_status": "married_joint",
        "state": "CA",
        "annual_income": 150000,
        "trad_ira_balance": 500000,
        "roth_ira_balance_initial": 0,
        "conversion_schedule": [50000],
        "social_security": 0,
        "rmd": 0,
        "cost_basis": 0,
    },
    "assumptions": {
        "annual_return": 0.07,
        "model_years": 30,
        "inflation_rate": 0.03,
    },
}

ALL_TOOL_NAMES = [
    "estimate_tax_components",
    "analyze_roth_projections",
    "optimize_conversion_schedule",
    "breakeven_analysis",
    "generate_conversion_report",
]

PARALLEL_TOOLS = {
    "analyze_roth_projections",
    "optimize_conversion_schedule",
    "breakeven_analysis",
}


# ---------------------------------------------------------------------------
# Mock executors
# ---------------------------------------------------------------------------

class MockExecutor:
    """Records calls and returns valid dual-return JSON for every tool."""

    def __init__(self, responses=None):
        self.calls = []
        self.responses = responses or {}

    async def call_tool(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        if tool_name in self.responses:
            return self.responses[tool_name]
        # Return minimal valid dual-return JSON
        return json.dumps({"display": "<div>mock</div>", "data": {"tool": tool_name}})


class FailingExecutor(MockExecutor):
    """Raises ConnectionError for a specific tool; returns valid JSON for others."""

    def __init__(self, fail_tool):
        super().__init__()
        self.fail_tool = fail_tool

    async def call_tool(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        if tool_name == self.fail_tool:
            raise ConnectionError(f"Tool {tool_name} failed")
        return json.dumps({"display": "<div>ok</div>", "data": {"tool": tool_name}})


# ---------------------------------------------------------------------------
# TestPipelineOrchestration
# ---------------------------------------------------------------------------

class TestPipelineOrchestration:
    """Verify tool call order, return structure, and partial-failure handling."""

    @pytest.mark.asyncio
    async def test_pipeline_calls_all_six_tools(self):
        """All 5 distinct tools are called (stage 2 has 3 parallel tools)."""
        executor = MockExecutor()
        await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        called_tools = [name for name, _ in executor.calls]
        for tool in ALL_TOOL_NAMES:
            assert tool in called_tools, f"{tool} was not called"

    @pytest.mark.asyncio
    async def test_pipeline_calls_tax_first(self):
        """estimate_tax_components must be called before the parallel tools."""
        executor = MockExecutor()
        await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        called_tools = [name for name, _ in executor.calls]
        tax_idx = called_tools.index("estimate_tax_components")

        for parallel_tool in PARALLEL_TOOLS:
            parallel_idx = called_tools.index(parallel_tool)
            assert tax_idx < parallel_idx, (
                f"estimate_tax_components (idx={tax_idx}) should precede "
                f"{parallel_tool} (idx={parallel_idx})"
            )

    @pytest.mark.asyncio
    async def test_pipeline_calls_report_last(self):
        """generate_conversion_report must be the last tool called."""
        executor = MockExecutor()
        await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        called_tools = [name for name, _ in executor.calls]
        assert called_tools[-1] == "generate_conversion_report"

    @pytest.mark.asyncio
    async def test_pipeline_returns_html_cards(self):
        """Result dict contains html_cards with at least one entry."""
        executor = MockExecutor()
        result = await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        assert "html_cards" in result
        assert isinstance(result["html_cards"], dict)
        assert len(result["html_cards"]) > 0

    @pytest.mark.asyncio
    async def test_pipeline_returns_compacted(self):
        """Result dict contains compacted with at least one entry."""
        executor = MockExecutor()
        result = await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        assert "compacted" in result
        assert isinstance(result["compacted"], dict)
        assert len(result["compacted"]) > 0

    @pytest.mark.asyncio
    async def test_pipeline_handles_partial_failure(self):
        """If one parallel tool raises, the pipeline still completes with other results."""
        executor = FailingExecutor(fail_tool="breakeven_analysis")
        result = await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        # Pipeline should still return a result dict
        assert "html_cards" in result
        assert "compacted" in result

        # The failing tool should not appear in html_cards
        assert "breakeven_analysis" not in result["html_cards"]

        # But the other parallel tools should still be present
        assert "analyze_roth_projections" in result["html_cards"]
        assert "optimize_conversion_schedule" in result["html_cards"]

        # Report should still be generated
        assert "generate_conversion_report" in result["html_cards"]


# ---------------------------------------------------------------------------
# TestPipelineWithFailures
# ---------------------------------------------------------------------------

class TestPipelineWithFailures:
    """Verify the pipeline is resilient to individual tool failures."""

    @pytest.mark.asyncio
    async def test_tax_failure_still_runs_pipeline(self):
        """If tax estimation fails, the pipeline continues with empty tax data."""
        executor = FailingExecutor(fail_tool="estimate_tax_components")
        result = await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        called_tools = [name for name, _ in executor.calls]

        # Tax tool was attempted
        assert "estimate_tax_components" in called_tools

        # Pipeline still ran the parallel stage and report
        for tool in PARALLEL_TOOLS:
            assert tool in called_tools, f"{tool} should still be called after tax failure"
        assert "generate_conversion_report" in called_tools

        # Result structure is still valid
        assert "html_cards" in result
        assert "compacted" in result

        # Tax should NOT be in html_cards since it failed
        assert "estimate_tax_components" not in result["html_cards"]

    @pytest.mark.asyncio
    async def test_projection_failure_still_generates_report(self):
        """If projections fail, the report is still generated."""
        executor = FailingExecutor(fail_tool="analyze_roth_projections")
        result = await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        called_tools = [name for name, _ in executor.calls]

        # Report was still generated
        assert "generate_conversion_report" in called_tools
        assert "generate_conversion_report" in result["html_cards"]

        # Failed tool not in results
        assert "analyze_roth_projections" not in result["html_cards"]

        # Other parallel tools succeeded
        assert "optimize_conversion_schedule" in result["html_cards"]
        assert "breakeven_analysis" in result["html_cards"]

    @pytest.mark.asyncio
    async def test_optimization_failure_still_generates_report(self):
        """If optimization fails, the report is still generated."""
        executor = FailingExecutor(fail_tool="optimize_conversion_schedule")
        result = await run_analysis_pipeline(executor, VALIDATED_INPUTS)

        called_tools = [name for name, _ in executor.calls]

        # Report was still generated
        assert "generate_conversion_report" in called_tools
        assert "generate_conversion_report" in result["html_cards"]

        # Failed tool not in results
        assert "optimize_conversion_schedule" not in result["html_cards"]

        # Other parallel tools succeeded
        assert "analyze_roth_projections" in result["html_cards"]
        assert "breakeven_analysis" in result["html_cards"]


# ---------------------------------------------------------------------------
# TestAntiHallucination
# ---------------------------------------------------------------------------

class TestAntiHallucination:
    """Verify check_hallucinated_numbers catches suspicious numbers."""

    def test_no_suspicious_when_numbers_match(self):
        """Dollar amount in GPT response that exists in tool results is not flagged."""
        gpt_response = "Your conversion of $50,000 will incur taxes."
        tool_results = {
            "estimate_tax_components": {"federal_tax": 8000, "conversion_amount": 50000},
        }
        suspicious = check_hallucinated_numbers(gpt_response, tool_results)
        assert len(suspicious) == 0

    def test_suspicious_dollar_not_in_results(self):
        """Dollar amount in GPT response not found in any tool result is flagged."""
        gpt_response = "You could save $99,999 by converting."
        tool_results = {
            "estimate_tax_components": {"federal_tax": 8000, "total": 50000},
        }
        suspicious = check_hallucinated_numbers(gpt_response, tool_results)
        assert any("99" in s for s in suspicious), (
            f"Expected $99,999 to be flagged, got: {suspicious}"
        )

    def test_suspicious_percentage(self):
        """Percentage in GPT response not found in tool results is flagged."""
        gpt_response = "This puts you in the 25% tax bracket."
        tool_results = {
            "estimate_tax_components": {"effective_rate": 0.22, "bracket": 22},
        }
        suspicious = check_hallucinated_numbers(gpt_response, tool_results)
        assert any("25%" in s for s in suspicious), (
            f"Expected 25% to be flagged, got: {suspicious}"
        )

    def test_suspicious_breakeven_years(self):
        """Breakeven year count not in tool results is flagged."""
        gpt_response = "It will take 7 years to break even on this conversion."
        tool_results = {
            "breakeven_analysis": {"breakeven_year": 12, "years": 12},
        }
        suspicious = check_hallucinated_numbers(gpt_response, tool_results)
        assert any("7" in s for s in suspicious), (
            f"Expected '7 years' to be flagged, got: {suspicious}"
        )

    def test_no_numbers_no_suspicious(self):
        """GPT response with no numbers at all yields an empty list."""
        gpt_response = "A Roth conversion moves money from a traditional IRA to a Roth IRA."
        tool_results = {
            "estimate_tax_components": {"federal_tax": 8000},
        }
        suspicious = check_hallucinated_numbers(gpt_response, tool_results)
        assert suspicious == []

    def test_input_numbers_not_flagged(self):
        """Numbers that do appear in tool results should not be flagged."""
        gpt_response = (
            "Based on the analysis, your federal tax is $8,000 "
            "with an effective rate of 22% and breakeven in 12 years to break even."
        )
        tool_results = {
            "estimate_tax_components": {"federal_tax": 8000, "effective_rate": 22},
            "breakeven_analysis": {"breakeven_years": 12},
        }
        suspicious = check_hallucinated_numbers(gpt_response, tool_results)
        assert len(suspicious) == 0
