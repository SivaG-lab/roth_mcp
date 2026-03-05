"""T018 — Tool schema validation tests."""

from __future__ import annotations

import asyncio
import json

import pytest

from mcp_server import mcp


FILING_STATUS_VALUES = ["head_of_household", "married_joint", "married_separate", "single"]

EXPECTED_TOOLS = [
    "validate_projection_inputs",
    "estimate_tax_components",
    "analyze_roth_projections",
    "optimize_conversion_schedule",
    "breakeven_analysis",
    "generate_conversion_report",
    "health_check",
]


def _get_tool_schemas() -> dict[str, dict]:
    """Extract tool schemas from the FastMCP server."""
    tools_list = asyncio.run(mcp.list_tools())
    tools = {}
    for tool in tools_list:
        schema = tool.parameters if isinstance(tool.parameters, dict) else {}
        tools[tool.name] = {
            "name": tool.name,
            "description": tool.description or "",
            "schema": schema,
        }
    return tools


class TestToolDiscovery:
    def test_all_tools_registered(self):
        schemas = _get_tool_schemas()
        for tool_name in EXPECTED_TOOLS:
            assert tool_name in schemas, f"Tool {tool_name} not registered"

    def test_seven_tools_total(self):
        schemas = _get_tool_schemas()
        assert len(schemas) == 7


class TestToolDescriptions:
    def test_all_tools_have_descriptions(self):
        schemas = _get_tool_schemas()
        for name, info in schemas.items():
            assert len(info["description"]) > 20, f"{name} has insufficient description"


class TestEnumParameters:
    def test_filing_status_has_enum(self):
        schemas = _get_tool_schemas()
        for tool_name in ["validate_projection_inputs", "estimate_tax_components",
                          "analyze_roth_projections", "optimize_conversion_schedule"]:
            schema = schemas[tool_name]["schema"]
            props = schema.get("properties", {})
            fs_prop = props.get("filing_status", {})
            # Check for enum in the property or its anyOf variants
            has_enum = False
            if "enum" in fs_prop:
                has_enum = True
            for variant in fs_prop.get("anyOf", []):
                if "enum" in variant:
                    has_enum = True
            assert has_enum, f"{tool_name}.filing_status should have enum values"
