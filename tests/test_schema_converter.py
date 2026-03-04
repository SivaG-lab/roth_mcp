"""T038 — Tests for MCP to OpenAI schema translation."""

import pytest
from schema_converter import mcp_tool_to_openai_function, TOOL_DESCRIPTIONS


class _MockMCPTool:
    """Mock MCP tool for testing schema conversion."""
    def __init__(self, name, description="", input_schema=None):
        self.name = name
        self.description = description
        self.inputSchema = input_schema


class TestMCPToolToOpenAIFunction:
    def test_returns_function_type(self):
        tool = _MockMCPTool("validate_projection_inputs", "desc", {"type": "object", "properties": {}})
        result = mcp_tool_to_openai_function(tool)
        assert result["type"] == "function"

    def test_preserves_name(self):
        tool = _MockMCPTool("estimate_tax_components", "desc", {"type": "object", "properties": {}})
        result = mcp_tool_to_openai_function(tool)
        assert result["function"]["name"] == "estimate_tax_components"

    def test_uses_enhanced_description(self):
        tool = _MockMCPTool("validate_projection_inputs", "original desc", {"type": "object", "properties": {}})
        result = mcp_tool_to_openai_function(tool)
        assert "ALWAYS call this tool first" in result["function"]["description"]

    def test_preserves_input_schema(self):
        schema = {"type": "object", "properties": {"age": {"type": "integer"}}}
        tool = _MockMCPTool("some_tool", "desc", schema)
        result = mcp_tool_to_openai_function(tool)
        assert result["function"]["parameters"] == schema

    def test_handles_none_schema(self):
        tool = _MockMCPTool("some_tool", "desc", None)
        result = mcp_tool_to_openai_function(tool)
        assert result["function"]["parameters"] == {"type": "object", "properties": {}}

    def test_falls_back_to_tool_description(self):
        tool = _MockMCPTool("unknown_tool", "fallback description", {"type": "object", "properties": {}})
        result = mcp_tool_to_openai_function(tool)
        assert result["function"]["description"] == "fallback description"

    def test_anyof_schema_preserved(self):
        schema = {
            "type": "object",
            "properties": {
                "schedule": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "number"}},
                        {"type": "null"},
                    ]
                }
            },
        }
        tool = _MockMCPTool("test_tool", "desc", schema)
        result = mcp_tool_to_openai_function(tool)
        assert "anyOf" in result["function"]["parameters"]["properties"]["schedule"]


class TestToolDescriptions:
    def test_all_six_tools_have_descriptions(self):
        expected = [
            "validate_projection_inputs",
            "estimate_tax_components",
            "analyze_roth_projections",
            "optimize_conversion_schedule",
            "breakeven_analysis",
            "generate_conversion_report",
        ]
        for name in expected:
            assert name in TOOL_DESCRIPTIONS, f"Missing description for {name}"

    def test_descriptions_are_non_empty(self):
        for name, desc in TOOL_DESCRIPTIONS.items():
            assert len(desc) > 10, f"Description too short for {name}"
