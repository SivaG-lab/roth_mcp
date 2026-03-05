"""Dual-return envelope — every MCP tool returns both data and styled HTML."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def dual_return(html: str | None, data: dict[str, Any]) -> str:
    """Create the universal response envelope as a JSON string.

    When RESPONSE_MODE is 'data_only', returns only the data dict as JSON.
    When html is None, behaves the same as data_only mode.
    """
    from config import RESPONSE_MODE

    if RESPONSE_MODE == "data_only":
        return json.dumps(data)
    return json.dumps({"display": html or "", "data": data})


def error_response(
    error_type: str,
    message: str,
    missing_fields: list[str] | None = None,
    details: list[dict[str, str]] | None = None,
) -> str:
    """Create a standardized error response as a JSON string."""
    return json.dumps({
        "error": True,
        "error_type": error_type,
        "message": message,
        "missing_fields": missing_fields or [],
        "details": details or [],
    })


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
