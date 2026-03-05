"""FastMCP server — Roth Conversion Calculator with 6 tools."""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

BREAKEVEN_MAX_YEARS = 50
SERVER_VERSION = "2.1.0"
_SERVER_START_TIME = time.monotonic()

import functools

from config import RESPONSE_MODE, MCP_RATE_LIMIT, new_correlation_id
from dual_return import dual_return, error_response
from rate_limiter import RateLimiter
from validators import validate_inputs, FilingStatus, StateCode
from tax.calculator import compute_tax_components, compute_bracket_boundaries
from tax.brackets import STANDARD_DEDUCTIONS, get_marginal_rate
from tax.rmd import compute_rmd
from tax.irmaa import compute_irmaa_surcharge
from tax.ss import compute_ss_taxation

if RESPONSE_MODE != "data_only":
    from html_templates import (
        format_validation_result,
        format_tax_estimate,
        format_projection_table,
        format_optimization_schedule,
        format_breakeven,
        format_report,
    )


def _html(formatter, data):
    """Generate HTML only when RESPONSE_MODE is 'full'."""
    if RESPONSE_MODE == "data_only":
        return None
    return formatter(data)

mcp = FastMCP("roth-conversion-calculator")

_rate_limiter = RateLimiter(MCP_RATE_LIMIT)


def tool_call_logger(func):
    """Decorator that logs tool calls with correlation ID, duration, and status."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cid = new_correlation_id()
        tool_name = func.__name__

        # Rate limit check (exempt health_check)
        if tool_name != "health_check" and not _rate_limiter.check():
            logger.warning("Rate limit exceeded", extra={"tool_name": tool_name, "correlation_id": cid})
            return error_response("rate_limit_exceeded", f"Rate limit exceeded ({MCP_RATE_LIMIT} requests/minute)")

        start = time.monotonic()
        try:
            result = func(*args, **kwargs)
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            logger.info(
                "tool_call",
                extra={"tool_name": tool_name, "duration_ms": duration_ms, "status": "success"},
            )
            return result
        except Exception:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            logger.error(
                "tool_call",
                extra={"tool_name": tool_name, "duration_ms": duration_ms, "status": "error"},
                exc_info=True,
            )
            raise
    return wrapper


# ---------------------------------------------------------------------------
# Tool 1: validate_projection_inputs
# ---------------------------------------------------------------------------
@mcp.tool()
@tool_call_logger
def validate_projection_inputs(
    current_age: Annotated[int | None, Field(description="Current age of the user (18-100)")] = None,
    retirement_age: Annotated[int | None, Field(description="Target retirement age (must be > current_age, max 100)")] = None,
    filing_status: Annotated[FilingStatus | None, Field(description="Tax filing status")] = None,
    state: Annotated[StateCode | None, Field(description="US state code for state tax calculation")] = None,
    annual_income: Annotated[float | None, Field(description="Current annual gross income in USD")] = None,
    trad_ira_balance: Annotated[float | None, Field(description="Current Traditional IRA balance in USD")] = None,
    conversion_amount: Annotated[float | None, Field(description="One-time Roth conversion amount in USD")] = None,
    conversion_schedule: Annotated[list[float] | None, Field(description="Multi-year conversion schedule as list of annual amounts")] = None,
    roth_ira_balance_initial: Annotated[float | None, Field(description="Existing Roth IRA balance in USD (default 0)")] = None,
    annual_return: Annotated[float | None, Field(description="Expected annual investment return rate (e.g. 0.07 for 7%)")] = None,
    model_years: Annotated[int | None, Field(description="Number of years to model (1-50, default 30)")] = None,
    social_security: Annotated[float | None, Field(description="Annual Social Security income in USD")] = None,
    rmd: Annotated[float | None, Field(description="Required Minimum Distribution amount in USD")] = None,
    cost_basis: Annotated[float, Field(description="Non-deductible IRA cost basis in USD")] = 0,
) -> str:
    """Validate user financial inputs for Roth IRA conversion analysis. Use this FIRST when a user provides their age, income, IRA balance, filing status, or state. Call this before any other analysis tool. Returns validation status, auto-filled defaults for social security, RMD, and growth assumptions."""
    start = time.monotonic()
    try:
        kwargs = {k: v for k, v in locals().items() if v is not None and k != "start"}
        result = validate_inputs(**kwargs)
        if result.get("errors"):
            return error_response(
                "validation_error",
                f"{len(result['errors'])} validation error(s) found",
                missing_fields=result.get("missing", []),
                details=result["errors"],
            )
        html = _html(format_validation_result, result)
        logger.info("validate_projection_inputs completed", extra={"status": result.get("status"), "elapsed": round(time.monotonic() - start, 3)})
        return dual_return(html, result)
    except Exception as exc:
        logger.exception("validate_projection_inputs failed")
        return error_response("computation_error", str(exc))


# ---------------------------------------------------------------------------
# Tool 2: estimate_tax_components
# ---------------------------------------------------------------------------
@mcp.tool()
@tool_call_logger
def estimate_tax_components(
    annual_income: Annotated[float | None, Field(description="Current annual gross income in USD")] = None,
    conversion_amount: Annotated[float | None, Field(description="Roth conversion amount to estimate tax on in USD")] = None,
    filing_status: Annotated[FilingStatus | None, Field(description="Tax filing status")] = None,
    state: Annotated[StateCode | None, Field(description="US state code for state tax calculation")] = None,
    cost_basis: Annotated[float, Field(description="Non-deductible IRA cost basis in USD")] = 0,
    social_security: Annotated[float, Field(description="Annual Social Security income in USD")] = 0,
    rmd: Annotated[float, Field(description="Required Minimum Distribution amount in USD")] = 0,
    other_ordinary_income: Annotated[float, Field(description="Other ordinary income in USD")] = 0,
) -> str:
    """Calculate the total tax cost of a specific Roth IRA conversion amount. Breaks down federal income tax, state income tax, Medicare IRMAA surcharge, Social Security tax impact, and RMD tax. Use when the user asks 'how much tax would I pay' or 'what is the tax cost of converting'. Returns detailed tax breakdown with effective and marginal rates."""
    start = time.monotonic()
    try:
        missing = []
        if annual_income is None:
            missing.append("annual_income")
        if conversion_amount is None:
            missing.append("conversion_amount")
        if not filing_status:
            missing.append("filing_status")
        if not state:
            missing.append("state")
        if missing:
            return error_response("missing_required_fields", "Missing required fields for tax estimate", missing_fields=missing)

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

        html = _html(format_tax_estimate, result)
        logger.info("estimate_tax_components completed", extra={"conversion": conversion_amount, "elapsed": round(time.monotonic() - start, 3)})
        return dual_return(html, result)
    except Exception as exc:
        logger.exception("estimate_tax_components failed")
        return error_response("computation_error", str(exc))


# ---------------------------------------------------------------------------
# Tool 3: analyze_roth_projections
# ---------------------------------------------------------------------------
@mcp.tool()
@tool_call_logger
def analyze_roth_projections(
    trad_ira_balance: Annotated[float | None, Field(description="Current Traditional IRA balance in USD")] = None,
    current_age: Annotated[int | None, Field(description="Current age of the user")] = None,
    roth_ira_balance_initial: Annotated[float, Field(description="Existing Roth IRA balance in USD")] = 0,
    conversion_schedule: Annotated[list[float] | None, Field(description="Multi-year conversion schedule as list of annual amounts")] = None,
    annual_return: Annotated[float, Field(description="Expected annual investment return rate (e.g. 0.07 for 7%)")] = 0.07,
    model_years: Annotated[int, Field(description="Number of years to model (1-50)")] = 30,
    annual_income: Annotated[float, Field(description="Current annual gross income in USD")] = 0,
    filing_status: Annotated[FilingStatus, Field(description="Tax filing status")] = "single",
    state: Annotated[StateCode, Field(description="US state code for state tax calculation")] = "CA",
    social_security: Annotated[float, Field(description="Annual Social Security income in USD")] = 0,
) -> str:
    """Project year-by-year IRA balances comparing Roth conversion vs. no conversion scenarios over 30 years. Shows when the Roth path becomes more valuable. Use when the user asks about 'projections', 'what happens over time', 'compare scenarios', or 'long-term outlook'. Requires validated inputs from validate_projection_inputs. Returns yearly balances, crossover year, and net benefit."""
    start = time.monotonic()
    try:
        missing = []
        if trad_ira_balance is None:
            missing.append("trad_ira_balance")
        if current_age is None:
            missing.append("current_age")
        if missing:
            return error_response("missing_required_fields", "Missing required fields for projections", missing_fields=missing)

        schedule = conversion_schedule or []

        # Year-by-year projection
        roth_balance = roth_ira_balance_initial
        trad_balance = trad_ira_balance
        trad_no_convert = trad_ira_balance
        projections = []
        crossover_year = 0

        for year in range(1, model_years + 1):
            age = current_age + year
            conversion = schedule[year - 1] if year - 1 < len(schedule) else 0.0

            # Cap conversion at available balance (after RMD)
            rmd_amount = compute_rmd(age, trad_balance)
            conversion = min(conversion, max(trad_balance - rmd_amount, 0))

            # Compute actual tax for this year's conversion amount
            if conversion > 0:
                tax_result = compute_tax_components(
                    annual_income=annual_income,
                    conversion_amount=conversion,
                    filing_status=filing_status,
                    state=state,
                    social_security=social_security,
                    rmd=compute_rmd(age, trad_balance),
                )
                tax_paid = tax_result.get("total_tax_cost", 0.0)
            else:
                tax_paid = 0.0

            # RMD for no-convert path
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
        html = _html(format_projection_table, data)
        logger.info("analyze_roth_projections completed", extra={"years": model_years, "elapsed": round(time.monotonic() - start, 3)})
        return dual_return(html, data)
    except Exception as exc:
        logger.exception("analyze_roth_projections failed")
        return error_response("computation_error", str(exc))


# ---------------------------------------------------------------------------
# Tool 4: optimize_conversion_schedule
# ---------------------------------------------------------------------------
@mcp.tool()
@tool_call_logger
def optimize_conversion_schedule(
    trad_ira_balance: Annotated[float | None, Field(description="Current Traditional IRA balance in USD")] = None,
    annual_income: Annotated[float | None, Field(description="Current annual gross income in USD")] = None,
    filing_status: Annotated[FilingStatus | None, Field(description="Tax filing status")] = None,
    state: Annotated[StateCode | None, Field(description="US state code for state tax calculation")] = None,
    current_age: Annotated[int | None, Field(description="Current age of the user")] = None,
    retirement_age: Annotated[int | None, Field(description="Target retirement age")] = None,
    model_years: Annotated[int, Field(description="Number of years to model (1-50)")] = 30,
    annual_return: Annotated[float, Field(description="Expected annual investment return rate (e.g. 0.07 for 7%)")] = 0.07,
    max_annual_conversion: Annotated[float | None, Field(description="Maximum conversion amount per year in USD")] = None,
    target_tax_bracket: Annotated[str | None, Field(description="Target tax bracket rate to fill up to (e.g. '22%')")] = None,
    optimization_goal: Annotated[str, Field(description="Optimization objective")] = "minimize_tax",
) -> str:
    """Find the optimal multi-year Roth conversion schedule that minimizes total lifetime tax cost using a bracket-filling strategy. Use when the user asks 'what is the best strategy', 'how should I split conversions', 'optimize my conversion', or 'minimize taxes'. Returns optimal per-year conversion amounts and total tax savings."""
    start = time.monotonic()
    try:
        missing = []
        if not trad_ira_balance:
            missing.append("trad_ira_balance")
        if annual_income is None:
            missing.append("annual_income")
        if not filing_status:
            missing.append("filing_status")
        if not state:
            missing.append("state")
        if current_age is None:
            missing.append("current_age")
        if retirement_age is None:
            missing.append("retirement_age")
        if missing:
            return error_response("missing_required_fields", "Missing required fields for optimization", missing_fields=missing)

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

        html = _html(format_optimization_schedule, data)
        logger.info("optimize_conversion_schedule completed", extra={"years": years_to_retire, "elapsed": round(time.monotonic() - start, 3)})
        return dual_return(html, data)
    except Exception as exc:
        logger.exception("optimize_conversion_schedule failed")
        return error_response("computation_error", str(exc))


# ---------------------------------------------------------------------------
# Tool 5: breakeven_analysis
# ---------------------------------------------------------------------------
@mcp.tool()
@tool_call_logger
def breakeven_analysis(
    conversion_amount: Annotated[float | None, Field(description="Roth conversion amount in USD")] = None,
    current_age: Annotated[int | None, Field(description="Current age of the user")] = None,
    total_tax_cost: Annotated[float | None, Field(description="Total tax cost of the conversion in USD")] = None,
    annual_return: Annotated[float, Field(description="Expected annual investment return rate (e.g. 0.07 for 7%)")] = 0.07,
    retirement_age: Annotated[int, Field(description="Target retirement age")] = 65,
    future_tax_rate: Annotated[float | None, Field(description="Expected future tax rate on traditional IRA withdrawals")] = None,
    federal_tax: Annotated[float | None, Field(description="Federal tax amount from estimate_tax_components")] = None,
    state_tax: Annotated[float | None, Field(description="State tax amount from estimate_tax_components")] = None,
) -> str:
    """Calculate how many years until a Roth conversion pays for itself in after-tax wealth. Returns breakeven age and assessment (worth_it if under 10 years, marginal if 10-20, not_worth_it if over 20). Use when the user asks 'how long until it pays off', 'is it worth converting', or 'breakeven point'."""
    start = time.monotonic()
    try:
        missing = []
        if conversion_amount is None:
            missing.append("conversion_amount")
        if current_age is None:
            missing.append("current_age")
        if missing:
            return error_response("missing_required_fields", "Missing required fields for breakeven analysis", missing_fields=missing)

        if conversion_amount <= 0:
            return dual_return(
                None,
                {"breakeven_years": 0, "breakeven_age": current_age, "assessment": "no_conversion"},
            )

        # Compute total tax cost if not provided directly
        if total_tax_cost is None:
            total_tax_cost = (federal_tax or 0) + (state_tax or 0)

        # Future tax rate estimate (use current effective rate if not given)
        if future_tax_rate is None:
            future_tax_rate = total_tax_cost / conversion_amount if conversion_amount > 0 else 0.20

        # Breakeven: year where tax-free Roth growth > traditional path after tax
        roth_start = conversion_amount - total_tax_cost
        trad_start = conversion_amount

        breakeven_years = 0
        for year in range(1, BREAKEVEN_MAX_YEARS + 1):
            roth_value = roth_start * ((1 + annual_return) ** year)
            trad_after_tax = trad_start * ((1 + annual_return) ** year) * (1 - future_tax_rate)
            if roth_value >= trad_after_tax:
                breakeven_years = year
                break
        else:
            breakeven_years = BREAKEVEN_MAX_YEARS

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

        html = _html(format_breakeven, data)
        logger.info("breakeven_analysis completed", extra={"years": breakeven_years, "elapsed": round(time.monotonic() - start, 3)})
        return dual_return(html, data)
    except Exception as exc:
        logger.exception("breakeven_analysis failed")
        return error_response("computation_error", str(exc))


def _safe_parse(s: str) -> dict:
    """Parse JSON string, extracting 'data' key if present."""
    if not s:
        return {}
    try:
        parsed = json.loads(s)
        return parsed.get("data", parsed) if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        logger.warning("_safe_parse: failed to parse: %s", s[:200] if s else s)
        return {}


# ---------------------------------------------------------------------------
# Tool 6: generate_conversion_report
# ---------------------------------------------------------------------------
@mcp.tool()
@tool_call_logger
def generate_conversion_report(
    validated_inputs: Annotated[str | None, Field(description="JSON string output from validate_projection_inputs")] = None,
    tax_analysis: Annotated[str | None, Field(description="JSON string output from estimate_tax_components")] = None,
    projection_data: Annotated[str, Field(description="JSON string output from analyze_roth_projections")] = "",
    optimization_data: Annotated[str, Field(description="JSON string output from optimize_conversion_schedule")] = "",
    breakeven_data: Annotated[str, Field(description="JSON string output from breakeven_analysis")] = "",
) -> str:
    """Generate a comprehensive summary report combining all prior analysis results including validation, tax estimate, projections, optimization, and breakeven. Call this LAST after all other analyses are complete. Use when the user asks for a 'full report', 'summary', or 'put it all together'. Pass results from previous tool calls as JSON strings."""
    start = time.monotonic()
    try:
        missing = []
        if not validated_inputs:
            missing.append("validated_inputs")
        if not tax_analysis:
            missing.append("tax_analysis")
        if missing:
            return error_response("missing_required_fields", "Missing required inputs for report generation", missing_fields=missing)

        inputs_data = _safe_parse(validated_inputs)
        tax_data = _safe_parse(tax_analysis)
        proj_data = _safe_parse(projection_data)
        opt_data = _safe_parse(optimization_data)
        be_data = _safe_parse(breakeven_data)

        if RESPONSE_MODE == "data_only":
            report_html = None
        else:
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

        logger.info("generate_conversion_report completed", extra={"sections": sections_included, "elapsed": round(time.monotonic() - start, 3)})
        return dual_return(report_html, {"summary": summary})
    except Exception as exc:
        logger.exception("generate_conversion_report failed")
        return error_response("computation_error", str(exc))


# ---------------------------------------------------------------------------
# Tool 7: health_check
# ---------------------------------------------------------------------------
@mcp.tool()
@tool_call_logger
def health_check() -> str:
    """Check if the Roth IRA Conversion Calculator MCP server is running and healthy. Use this to verify server availability, get version info, and confirm tool count. Returns server status, version, tool count, and uptime."""
    data = {
        "status": "healthy",
        "version": SERVER_VERSION,
        "tools_available": 7,
        "uptime_seconds": round(time.monotonic() - _SERVER_START_TIME, 1),
    }
    return dual_return(None, data)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
_VALID_TRANSPORTS = {"stdio", "sse", "streamable-http"}

if __name__ == "__main__":
    from config import MCP_TRANSPORT, MCP_HOST, MCP_PORT

    if MCP_TRANSPORT not in _VALID_TRANSPORTS:
        print(
            f"ERROR: MCP_TRANSPORT={MCP_TRANSPORT!r} is invalid. "
            f"Must be one of: {', '.join(sorted(_VALID_TRANSPORTS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    if MCP_TRANSPORT == "stdio":
        sys.stdout.reconfigure(line_buffering=True)
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=MCP_TRANSPORT, host=MCP_HOST, port=MCP_PORT)
