"""Deterministic computation pipeline — runs 6 tools without GPT round-trips."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from dual_return import extract_data, compact_result

logger = logging.getLogger(__name__)


async def run_analysis_pipeline(
    executor: Any,
    validated_inputs: dict,
) -> dict[str, Any]:
    """Run the full analysis pipeline after inputs are validated.

    Pipeline order:
    1. estimate_tax_components (serial)
    2. analyze_projections + optimize_schedule + breakeven (3-way parallel)
    3. generate_report (serial)

    Returns dict with html_cards and compacted results.
    """
    inputs = validated_inputs.get("inputs", {})
    assumptions = validated_inputs.get("assumptions", {})

    html_cards = {}
    compacted = {}
    logger.info("Pipeline started")

    # Stage 1: Tax estimate (serial)
    tax_args = {
        "annual_income": inputs.get("annual_income"),
        "conversion_amount": inputs.get("conversion_schedule", [0])[0] if inputs.get("conversion_schedule") else 0,
        "filing_status": inputs.get("filing_status"),
        "state": inputs.get("state"),
        "cost_basis": inputs.get("cost_basis", 0),
        "social_security": inputs.get("social_security", 0),
        "rmd": inputs.get("rmd", 0),
    }

    try:
        tax_result = await executor.call_tool("estimate_tax_components", tax_args)
        tax_data = extract_data(tax_result)
        html_cards["estimate_tax_components"] = tax_result
        compacted["estimate_tax_components"] = compact_result("estimate_tax_components", tax_result)
    except Exception as e:
        logger.error("Tax estimate failed: %s", e)
        tax_result = ""
        tax_data = {}

    # Stage 2: 3-way parallel
    proj_args = {
        "trad_ira_balance": inputs.get("trad_ira_balance"),
        "roth_ira_balance_initial": inputs.get("roth_ira_balance_initial", 0),
        "conversion_schedule": inputs.get("conversion_schedule"),
        "annual_return": assumptions.get("annual_return", 0.07),
        "model_years": assumptions.get("model_years", 30),
        "current_age": inputs.get("current_age"),
        "annual_income": inputs.get("annual_income"),
        "filing_status": inputs.get("filing_status"),
        "state": inputs.get("state"),
        "social_security": inputs.get("social_security", 0),
    }

    opt_args = {
        "trad_ira_balance": inputs.get("trad_ira_balance"),
        "annual_income": inputs.get("annual_income"),
        "filing_status": inputs.get("filing_status"),
        "state": inputs.get("state"),
        "current_age": inputs.get("current_age"),
        "retirement_age": inputs.get("retirement_age"),
        "model_years": assumptions.get("model_years", 30),
        "annual_return": assumptions.get("annual_return", 0.07),
    }

    conv_total = sum(inputs.get("conversion_schedule", [0]))
    be_args = {
        "conversion_amount": conv_total,
        "total_tax_cost": tax_data.get("total_tax_cost"),
        "current_age": inputs.get("current_age"),
        "annual_return": assumptions.get("annual_return", 0.07),
        "retirement_age": inputs.get("retirement_age", 65),
        "federal_tax": tax_data.get("federal_tax"),
        "state_tax": tax_data.get("state_tax"),
    }

    async def _call_safe(tool_name, args):
        try:
            result = await executor.call_tool(tool_name, args)
            return tool_name, result
        except Exception as e:
            logger.error("%s failed: %s", tool_name, e)
            return tool_name, None

    results = await asyncio.gather(
        _call_safe("analyze_roth_projections", proj_args),
        _call_safe("optimize_conversion_schedule", opt_args),
        _call_safe("breakeven_analysis", be_args),
    )

    logger.info("Stage 2 parallel calls complete")
    for tool_name, result in results:
        if result is not None:
            html_cards[tool_name] = result
            compacted[tool_name] = compact_result(tool_name, result)

    # Stage 3: Generate report (serial)
    report_args = {
        "validated_inputs": json.dumps(validated_inputs),
        "tax_analysis": json.dumps(tax_data) if tax_data else "",
        "projection_data": json.dumps(extract_data(html_cards.get("analyze_roth_projections", "{}"))) if html_cards.get("analyze_roth_projections") else "",
        "optimization_data": json.dumps(extract_data(html_cards.get("optimize_conversion_schedule", "{}"))) if html_cards.get("optimize_conversion_schedule") else "",
        "breakeven_data": json.dumps(extract_data(html_cards.get("breakeven_analysis", "{}"))) if html_cards.get("breakeven_analysis") else "",
    }

    try:
        report_result = await executor.call_tool("generate_conversion_report", report_args)
        html_cards["generate_conversion_report"] = report_result
        compacted["generate_conversion_report"] = compact_result("generate_conversion_report", report_result)
    except Exception as e:
        logger.error("Report generation failed: %s", e)

    logger.info("Pipeline complete, %d tools succeeded", len(html_cards))
    return {
        "html_cards": html_cards,
        "compacted": compacted,
    }
