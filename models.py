"""Data models — dataclasses and enums for the Roth Conversion Calculator."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, Optional


class PipelinePhase(str, Enum):
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    COMPLETE = "complete"


@dataclass
class UserProfile:
    """Holds all 17+ user financial inputs."""

    current_age: Optional[int] = None
    retirement_age: Optional[int] = None
    filing_status: Optional[str] = None
    state: Optional[str] = None
    annual_income: Optional[float] = None
    trad_ira_balance: Optional[float] = None
    conversion_amount: Optional[float] = None
    conversion_schedule: Optional[list[float]] = None
    roth_ira_balance_initial: float = 0.0
    cost_basis: float = 0.0
    annual_return: float = 0.07
    model_years: int = 30
    social_security: float = 0.0
    rmd: float = 0.0

    REQUIRED_FIELDS: ClassVar[list[str]] = [
        "current_age",
        "retirement_age",
        "filing_status",
        "state",
        "annual_income",
        "trad_ira_balance",
    ]

    @property
    def missing_required(self) -> list[str]:
        return [f for f in self.REQUIRED_FIELDS if getattr(self, f) is None]

    @property
    def has_conversion_spec(self) -> bool:
        return self.conversion_amount is not None or self.conversion_schedule is not None

    def to_tool_args(self) -> dict:
        """Return dict with only non-None values (for MCP tool calls)."""
        result = {}
        for fld in dataclasses.fields(self):
            val = getattr(self, fld.name)
            if val is not None:
                result[fld.name] = val
        return result


@dataclass
class ModelAssumptions:
    """Default rates and horizons."""

    annual_return: float = 0.07
    taxable_account_annual_return: float = 0.07
    inflation_rate: float = 0.03
    model_years: int = 30
    rmd_start_age: int = 73
    ss_start_age: int = 67


@dataclass
class TaxEstimate:
    """Complete tax breakdown for a single conversion scenario."""

    federal_tax: float = 0.0
    state_tax: float = 0.0
    irmaa_impact: float = 0.0
    ss_tax_impact: float = 0.0
    rmd_tax: float = 0.0
    total_tax_cost: float = 0.0
    effective_rate: float = 0.0
    marginal_rate: float = 0.0
    bracket_before: str = ""
    bracket_after: str = ""
    conversion_amount: float = 0.0


@dataclass
class ProjectionData:
    """Year-by-year comparison of convert vs. no-convert scenarios."""

    projections: list[dict] = field(default_factory=list)
    summary: dict = field(default_factory=lambda: {
        "final_roth_value": 0.0,
        "final_trad_value": 0.0,
        "net_benefit": 0.0,
        "crossover_year": 0,
    })


@dataclass
class OptimizationResult:
    """Optimal multi-year conversion schedule."""

    optimal_schedule: list[float] = field(default_factory=list)
    total_tax_cost: float = 0.0
    tax_saved_vs_baseline: float = 0.0
    optimization_goal: str = "minimize_tax"
    converged: bool = True
    confidence: float = 1.0


@dataclass
class BreakevenResult:
    """How many years until Roth path >= Traditional path."""

    breakeven_years: int = 0
    breakeven_age: int = 0
    assessment: str = ""


@dataclass
class CalculationResults:
    """Container for all tool results. Stored in session state."""

    tax_estimate: Optional[TaxEstimate] = None
    projection: Optional[ProjectionData] = None
    optimization: Optional[OptimizationResult] = None
    breakeven: Optional[BreakevenResult] = None
    report_html: str = ""
    tools_completed: list[str] = field(default_factory=list)


@dataclass
class TokenTracker:
    """Track GPT API token usage and estimated cost."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    calls: list = field(default_factory=list)

    def record(self, response) -> None:
        """Extract usage from OpenAI response."""
        if hasattr(response, "usage") and response.usage:
            self.total_prompt_tokens += response.usage.prompt_tokens
            self.total_completion_tokens += response.usage.completion_tokens
            self.calls.append({
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            })

    @property
    def estimated_cost(self) -> float:
        """gpt-4o-mini pricing: $0.15/M prompt, $0.60/M completion."""
        return (
            self.total_prompt_tokens * 0.15 / 1_000_000
            + self.total_completion_tokens * 0.60 / 1_000_000
        )
