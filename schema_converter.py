"""MCP to OpenAI schema translation for function calling."""

from __future__ import annotations

from typing import Any

TOOL_DESCRIPTIONS = {
    "validate_projection_inputs": (
        "Validate and prepare all user financial inputs for Roth conversion analysis. "
        "ALWAYS call this tool first with any financial information the user provides."
    ),
    "estimate_tax_components": (
        "Calculate federal tax, state tax, IRMAA surcharge, Social Security tax impact, "
        "and RMD tax for a specific Roth conversion amount."
    ),
    "analyze_roth_projections": (
        "Generate year-by-year comparison of convert vs. no-convert scenarios "
        "showing Roth and Traditional IRA balance projections."
    ),
    "optimize_conversion_schedule": (
        "Find the optimal multi-year Roth conversion schedule that minimizes total tax cost "
        "using bracket-filling strategy. Only call if user wants help choosing amounts."
    ),
    "breakeven_analysis": (
        "Calculate how many years until the Roth conversion pays for itself "
        "and provide worth-it/marginal/not-worth-it assessment."
    ),
    "generate_conversion_report": (
        "Generate a comprehensive HTML report combining all analysis results. "
        "Call this LAST after all other tools have completed."
    ),
}


def mcp_tool_to_openai_function(mcp_tool: Any) -> dict:
    """Translate an MCP tool definition to OpenAI function calling format."""
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": TOOL_DESCRIPTIONS.get(mcp_tool.name, mcp_tool.description or ""),
            "parameters": mcp_tool.inputSchema or {"type": "object", "properties": {}},
        },
    }
