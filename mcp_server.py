"""FastMCP server — Roth Conversion Calculator with 6 tools."""

from __future__ import annotations

import json
import sys

from fastmcp import FastMCP

from dual_return import dual_return
from validators import validate_inputs
from tax.calculator import compute_tax_components, compute_bracket_boundaries
from tax.brackets import STANDARD_DEDUCTIONS, get_marginal_rate
from tax.rmd import compute_rmd
from tax.irmaa import compute_irmaa_surcharge
from tax.ss import compute_ss_taxation
from html_templates import (
    format_validation_result,
    format_tax_estimate,
    format_projection_table,
    format_optimization_schedule,
    format_breakeven,
    format_report,
)

mcp = FastMCP("roth-conversion-calculator")


# ---------------------------------------------------------------------------
# Tool 1: validate_projection_inputs
# ---------------------------------------------------------------------------
@mcp.tool()
def validate_projection_inputs(
    trad_ira_balance: float | None = None,
    current_age: int | None = None,
    retirement_age: int | None = None,
    filing_status: str | None = None,
    state: str | None = None,
    annual_income: float | None = None,
    conversion_amount: float | None = None,
    conversion_schedule: list[float] | None = None,
    roth_ira_balance_initial: float | None = None,
    taxable_dollars_available: float | None = None,
    annual_return: float | None = None,
    taxable_account_annual_return: float | None = None,
    model_years: int | None = None,
    social_security: float | None = None,
    rmd: float | None = None,
    irmaa: float | None = None,
    cost_basis: float = 0,
    other_ordinary_income_by_year: list[float] | None = None,
    spending_need_after_tax_by_year: list[float] | None = None,
) -> str:
    """Validate and prepare all user financial inputs for Roth conversion analysis.
    ALWAYS call this tool first with any financial information the user provides."""
    kwargs = {k: v for k, v in locals().items() if v is not None}
    result = validate_inputs(**kwargs)
    html = format_validation_result(result)
    return dual_return(html, result)


# ---------------------------------------------------------------------------
# Tool 2: estimate_tax_components
# ---------------------------------------------------------------------------
@mcp.tool()
def estimate_tax_components(
    annual_income: float | None = None,
    conversion_amount: float | None = None,
    filing_status: str | None = None,
    state: str | None = None,
    cost_basis: float = 0,
    social_security: float = 0,
    rmd: float = 0,
    irmaa: float = 0,
    other_ordinary_income: float = 0,
) -> str:
    """Calculate federal tax, state tax, IRMAA surcharge, Social Security tax impact,
    and RMD tax for a specific Roth conversion amount."""
    if not all([annual_income is not None, conversion_amount is not None,
                filing_status, state]):
        return dual_return(
            "<div style='color:#ef4444'>Missing required inputs for tax estimate</div>",
            {"error": "Missing required: annual_income, conversion_amount, filing_status, state"},
        )

    result = compute_tax_components(
        annual_income=annual_income,
        conversion_amount=conversion_amount,
        filing_status=filing_status,
        state=state,
        cost_basis=cost_basis,
        social_security=social_security,
        rmd=rmd,
        other_ordinary_income=other_ordinary_income,
    )

    html = format_tax_estimate(result)
    return dual_return(html, result)


# ---------------------------------------------------------------------------
# Tool 3: analyze_roth_projections
# ---------------------------------------------------------------------------
@mcp.tool()
def analyze_roth_projections(
    trad_ira_balance: float | None = None,
    roth_ira_balance_initial: float = 0,
    conversion_schedule: list[float] | None = None,
    annual_return: float = 0.07,
    taxable_account_annual_return: float = 0.07,
    taxable_dollars_available: float = 0,
    model_years: int = 30,
    current_age: int | None = None,
    federal_tax: float | None = None,
    state_tax: float | None = None,
    social_security: float = 0,
    rmd: float = 0,
    other_ordinary_income_by_year: list[float] | None = None,
    spending_need_after_tax_by_year: list[float] | None = None,
) -> str:
    """Generate year-by-year comparison of convert vs. no-convert scenarios."""
    if trad_ira_balance is None or current_age is None:
        return dual_return(
            "<div style='color:#ef4444'>Missing required inputs for projections</div>",
            {"error": "Missing required: trad_ira_balance, current_age"},
        )

    schedule = conversion_schedule or []
    total_tax_per_conversion = (federal_tax or 0) + (state_tax or 0)

    # Year-by-year projection
    roth_balance = roth_ira_balance_initial
    trad_balance = trad_ira_balance
    trad_no_convert = trad_ira_balance
    projections = []
    crossover_year = 0

    for year in range(1, model_years + 1):
        age = current_age + year
        conversion = schedule[year - 1] if year - 1 < len(schedule) else 0.0

        # Tax on this year's conversion (proportional to first year's tax)
        if conversion > 0 and schedule and schedule[0] > 0:
            tax_paid = total_tax_per_conversion * (conversion / schedule[0])
        else:
            tax_paid = 0.0

        # RMD for both paths
        rmd_amount = compute_rmd(age, trad_balance)
        rmd_no_convert = compute_rmd(age, trad_no_convert)

        # Convert path: move conversion from trad to roth, pay tax
        trad_balance = trad_balance - conversion - rmd_amount
        roth_balance = roth_balance + conversion
        # Growth
        trad_balance = max(trad_balance * (1 + annual_return), 0)
        roth_balance = roth_balance * (1 + annual_return)

        # No-convert path: just growth + RMDs
        trad_no_convert = trad_no_convert - rmd_no_convert
        trad_no_convert = max(trad_no_convert * (1 + annual_return), 0)

        # Total wealth comparison (Roth is tax-free, trad needs future tax)
        total_convert = roth_balance + trad_balance
        total_no_convert = trad_no_convert

        if crossover_year == 0 and total_convert > total_no_convert and year > 1:
            crossover_year = year

        projections.append({
            "year": year,
            "age": age,
            "conversion": round(conversion, 2),
            "roth_balance": round(roth_balance, 2),
            "trad_balance": round(trad_balance, 2),
            "tax_paid": round(tax_paid, 2),
            "rmd_amount": round(rmd_amount, 2),
        })

    final = projections[-1] if projections else {}
    summary = {
        "final_roth_value": final.get("roth_balance", 0),
        "final_trad_value": final.get("trad_balance", 0),
        "net_benefit": round(
            (final.get("roth_balance", 0) + final.get("trad_balance", 0)) - trad_no_convert, 2
        ),
        "crossover_year": crossover_year,
    }

    data = {"projections": projections, "summary": summary}
    html = format_projection_table(data)
    return dual_return(html, data)


# ---------------------------------------------------------------------------
# Tool 4: optimize_conversion_schedule
# ---------------------------------------------------------------------------
@mcp.tool()
def optimize_conversion_schedule(
    trad_ira_balance: float | None = None,
    annual_income: float | None = None,
    filing_status: str | None = None,
    state: str | None = None,
    current_age: int | None = None,
    retirement_age: int | None = None,
    model_years: int = 30,
    annual_return: float = 0.07,
    max_annual_conversion: float | None = None,
    target_tax_bracket: str | None = None,
    optimization_goal: str = "minimize_tax",
) -> str:
    """Find the optimal multi-year Roth conversion schedule that minimizes
    total tax cost using bracket-filling strategy."""
    if not all([trad_ira_balance, annual_income is not None, filing_status, state,
                current_age is not None, retirement_age is not None]):
        return dual_return(
            "<div style='color:#ef4444'>Missing required inputs for optimization</div>",
            {"error": "Missing required inputs"},
        )

    years_to_retire = max(retirement_age - current_age, 1)
    std_deduction = STANDARD_DEDUCTIONS.get(filing_status, 0)
    taxable_base = max(annual_income - std_deduction, 0)

    # Determine target bracket ceiling
    boundaries = compute_bracket_boundaries(taxable_base, filing_status)
    target_ceiling = None
    if target_tax_bracket:
        for b in boundaries:
            if b["rate_label"] == target_tax_bracket:
                target_ceiling = b["ceiling"]
                break
    if target_ceiling is None:
        # Default: fill current bracket
        for b in boundaries:
            if b["room_remaining"] > 0 and b["ceiling"] != float("inf"):
                target_ceiling = b["ceiling"]
                break
        if target_ceiling is None:
            target_ceiling = taxable_base + 100000  # fallback

    # Greedy bracket-fill
    remaining_balance = trad_ira_balance
    schedule = []
    total_tax = 0.0

    for year in range(years_to_retire):
        if remaining_balance <= 0:
            schedule.append(0.0)
            continue

        room = max(target_ceiling - taxable_base, 0)
        conversion = min(room, remaining_balance)
        if max_annual_conversion is not None:
            conversion = min(conversion, max_annual_conversion)

        if conversion > 0:
            tax_result = compute_tax_components(
                annual_income=annual_income,
                conversion_amount=conversion,
                filing_status=filing_status,
                state=state,
            )
            total_tax += tax_result["total_tax_cost"]

        remaining_balance -= conversion
        remaining_balance *= (1 + annual_return)  # growth on remaining
        schedule.append(round(conversion, 2))

    # Compare to baseline (lump sum)
    baseline_tax_result = compute_tax_components(
        annual_income=annual_income,
        conversion_amount=trad_ira_balance,
        filing_status=filing_status,
        state=state,
    )
    baseline_tax = baseline_tax_result["total_tax_cost"]
    tax_saved = round(baseline_tax - total_tax, 2)

    converged = remaining_balance <= trad_ira_balance * 0.01
    confidence = 1.0 if converged else round(1.0 - remaining_balance / trad_ira_balance, 2)

    data = {
        "optimal_schedule": schedule,
        "total_tax_cost": round(total_tax, 2),
        "tax_saved_vs_baseline": max(tax_saved, 0),
        "optimization_goal": optimization_goal,
        "converged": converged,
        "confidence": max(confidence, 0),
    }

    html = format_optimization_schedule(data)
    return dual_return(html, data)


# ---------------------------------------------------------------------------
# Tool 5: breakeven_analysis
# ---------------------------------------------------------------------------
@mcp.tool()
def breakeven_analysis(
    conversion_amount: float | None = None,
    total_tax_cost: float | None = None,
    current_age: int | None = None,
    annual_return: float = 0.07,
    retirement_age: int = 65,
    future_tax_rate: float | None = None,
    federal_tax: float | None = None,
    state_tax: float | None = None,
) -> str:
    """Calculate how many years until the Roth conversion pays for itself."""
    if conversion_amount is None or current_age is None:
        return dual_return(
            "<div style='color:#ef4444'>Missing required inputs for breakeven</div>",
            {"error": "Missing required inputs"},
        )

    # Compute total tax cost if not provided directly
    if total_tax_cost is None:
        total_tax_cost = (federal_tax or 0) + (state_tax or 0)

    # Future tax rate estimate (use current effective rate if not given)
    if future_tax_rate is None:
        future_tax_rate = total_tax_cost / conversion_amount if conversion_amount > 0 else 0.20

    # Breakeven: year where tax-free Roth growth > traditional path after tax
    # Roth path: (conversion - tax_cost) grows tax-free
    # Trad path: conversion grows, but withdrawals taxed at future_tax_rate
    roth_start = conversion_amount - total_tax_cost
    trad_start = conversion_amount

    breakeven_years = 0
    for year in range(1, 51):
        roth_value = roth_start * ((1 + annual_return) ** year)
        trad_after_tax = trad_start * ((1 + annual_return) ** year) * (1 - future_tax_rate)
        if roth_value >= trad_after_tax:
            breakeven_years = year
            break
    else:
        breakeven_years = 50  # never breaks even within 50 years

    breakeven_age = current_age + breakeven_years

    if breakeven_years < 10:
        assessment = "worth_it"
    elif breakeven_years <= 20:
        assessment = "marginal"
    else:
        assessment = "not_worth_it"

    data = {
        "breakeven_years": breakeven_years,
        "breakeven_age": breakeven_age,
        "assessment": assessment,
    }

    html = format_breakeven(data)
    return dual_return(html, data)


# ---------------------------------------------------------------------------
# Tool 6: generate_conversion_report
# ---------------------------------------------------------------------------
@mcp.tool()
def generate_conversion_report(
    validated_inputs: str | None = None,
    tax_analysis: str | None = None,
    projection_data: str = "",
    optimization_data: str = "",
    breakeven_data: str = "",
) -> str:
    """Generate a comprehensive HTML report combining all analysis results.
    Call this LAST after all other tools have completed."""

    def _safe_parse(s: str) -> dict:
        if not s:
            return {}
        try:
            parsed = json.loads(s)
            return parsed.get("data", parsed) if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    inputs_data = _safe_parse(validated_inputs) if validated_inputs else {}
    tax_data = _safe_parse(tax_analysis) if tax_analysis else {}
    proj_data = _safe_parse(projection_data)
    opt_data = _safe_parse(optimization_data)
    be_data = _safe_parse(breakeven_data)

    report_html = format_report(inputs_data, tax_data, proj_data, opt_data, be_data)

    sections_included = []
    if inputs_data:
        sections_included.append("inputs")
    if tax_data and "federal_tax" in tax_data:
        sections_included.append("tax")
    if proj_data and "projections" in proj_data:
        sections_included.append("projection")
    if opt_data and "optimal_schedule" in opt_data:
        sections_included.append("optimization")
    if be_data and "assessment" in be_data:
        sections_included.append("breakeven")

    summary = {
        "total_tax_cost": tax_data.get("total_tax_cost", 0),
        "net_benefit": proj_data.get("summary", {}).get("net_benefit", 0),
        "breakeven_years": be_data.get("breakeven_years", 0),
        "assessment": be_data.get("assessment", ""),
        "sections_included": sections_included,
    }

    return dual_return(report_html, {"summary": summary})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Windows stdout flush for MCP stdio transport
    if sys.platform == "win32":
        import os
        os.environ.setdefault("PYTHONUNBUFFERED", "1")
    mcp.run(transport="stdio")
