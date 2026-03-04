"""Dual-return envelope — every MCP tool returns both data and styled HTML."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def dual_return(html: str, data: dict[str, Any]) -> str:
    """Create the universal response envelope as a JSON string."""
    return json.dumps({"display": html, "data": data})


def extract_html(result: str) -> str:
    """Extract the HTML display string from a dual-return result."""
    try:
        parsed = json.loads(result)
        return parsed.get("display", "")
    except (json.JSONDecodeError, TypeError):
        logger.warning("extract_html: failed to parse result: %s", result[:200] if result else result)
        return ""


def extract_data(result: str) -> dict[str, Any]:
    """Extract the structured data dict from a dual-return result."""
    try:
        parsed = json.loads(result)
        return parsed.get("data", {})
    except (json.JSONDecodeError, TypeError):
        logger.warning("extract_data: failed to parse result: %s", result[:200] if result else result)
        return {}


def compact_result(tool_name: str, result: str) -> dict[str, Any]:
    """Return data without HTML — for GPT context window efficiency.

    For generate_conversion_report, returns a summary placeholder instead
    of the full data to save tokens.
    """
    data = extract_data(result)
    if tool_name == "generate_conversion_report":
        summary = data.get("summary", {})
        return {"tool": tool_name, "summary": summary}
    return {"tool": tool_name, **data}
