# OpenAI Function Calling Schema Contract

**Purpose**: MCP tool schemas are translated to OpenAI function calling format at tool discovery time.

---

## Translation Function

```python
def mcp_tool_to_openai_function(mcp_tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": TOOL_DESCRIPTIONS.get(mcp_tool.name, mcp_tool.description),
            "parameters": mcp_tool.inputSchema or {"type": "object", "properties": {}},
        },
    }
```

## Enhanced Tool Descriptions

Override MCP tool descriptions for better GPT tool selection:

```python
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
```

## List Parameter Handling

MCP schema `list[float] | None` translates to:

```json
{
  "anyOf": [
    {"type": "array", "items": {"type": "number"}},
    {"type": "null"}
  ]
}
```

GPT correctly produces `[50000, 50000, 50000]` for these parameters.

## OpenAI Call Configuration

```python
response = openai_client.chat.completions.create(
    model=OPENAI_MODEL,         # from .env, default gpt-4o-mini
    messages=messages,
    tools=openai_tools,         # translated MCP schemas
    tool_choice="auto",
    parallel_tool_calls=False,  # MCP stdio is serial
    timeout=OPENAI_TIMEOUT,     # from .env, default 30s
)
```
