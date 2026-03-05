# Requirements Document: roth_mcp Kore.ai MCP Agent Compatibility

**Version:** 1.0
**Date:** 2026-03-04
**Status:** Draft
**Author:** Claude Code (deep research + codebase audit)

---

## 1. Executive Summary

The roth_mcp server is a Roth IRA Conversion Calculator exposed as a FastMCP server with 6 financial analysis tools. It currently runs over **stdio transport** with a **Streamlit UI** and **GPT-powered orchestration**. The primary production use case is **Kore.ai MCP Agents**, which requires specific adaptations to transport, response format, parameter schemas, and architecture.

### Current State
- 6 MCP tools (validate, tax, projections, optimize, breakeven, report)
- Stdio transport only
- Dual-return response envelope (HTML + JSON data)
- GPT-specific orchestration layer (agent_loop.py, pipeline.py)
- Streamlit-specific UI components (html_templates/, streamlit_app.py)
- 305+ unit tests, comprehensive tax engine

### Target State
- MCP server compatible with Kore.ai's HTTP/SSE MCP client
- Rich JSON Schema tool definitions enabling Kore.ai form auto-generation
- Lean response format (data-only mode for Kore.ai, dual-return for Streamlit)
- Clean separation of MCP server core vs client-specific code
- Each tool independently callable (no pipeline dependency)

---

## 2. Kore.ai MCP Agent Capabilities (Research Findings)

### 2.1 How Kore.ai Consumes MCP Servers
- Kore.ai acts as an **MCP client** using JSON-RPC 2.0 protocol
- Supports **HTTP** and **SSE** transport types (NOT stdio)
- Tool discovery via `tools/list` endpoint
- Tool invocation via `tools/call` endpoint
- LLM-driven tool selection based on tool descriptions and user intent

### 2.2 Form-Based Input Collection
- Kore.ai **auto-generates input forms** from tool `inputSchema`
- Parameters configured as **Static** (pre-set) or **Dynamic** (extracted/collected)
- Dynamic parameters: "Extract from Query" (entity extraction) or "Collect from Form"
- **Continue button disabled** until all required fields are filled
- `enum` values rendered as **dropdowns**
- `description` shown as field **labels/help text**

### 2.3 Response Processing
- Tool output passed to LLM for natural language response generation
- `isError: true` flag for tool-level errors
- "Include Tool Response in Artifacts" option for programmatic access
- LLM synthesizes natural language from structured tool output

### 2.4 Multi-Tool Orchestration
- LLM decides tool sequence based on descriptions (not hardcoded pipeline)
- Supports sequential and parallel tool execution
- Tools from multiple MCP servers can be combined
- No declarative workflow chaining — LLM-driven

### 2.5 Limitations
- No automatic tool sync when server definitions change
- Only tool discovery and invocation supported (not MCP Resources/Prompts)
- Manual reconfiguration required for schema updates
- Requires commercial LLMs (GPT-4, Claude 3.x, Gemini) for tool calling

---

## 3. Requirements

### REQ-001: Add HTTP/SSE Transport Support

**Priority:** CRITICAL
**Current:** `mcp.run(transport="stdio")` hardcoded in mcp_server.py:447
**Required:** Support HTTP and SSE transports configurable via environment variable

**Acceptance Criteria:**
- [ ] Environment variable `MCP_TRANSPORT` controls transport type (default: "stdio")
- [ ] Valid values: "stdio", "sse", "streamable-http"
- [ ] SSE transport binds to configurable `MCP_HOST` (default: "0.0.0.0") and `MCP_PORT` (default: 8080)
- [ ] Stdio transport preserved for local/Streamlit development
- [ ] Server starts successfully with each transport type
- [ ] Kore.ai can discover tools via HTTP/SSE endpoint

**Implementation Notes:**
```python
# mcp_server.py - bottom
transport = os.getenv("MCP_TRANSPORT", "stdio")
if transport == "stdio":
    sys.stdout.reconfigure(line_buffering=True)
    mcp.run(transport="stdio")
elif transport == "sse":
    mcp.run(transport="sse", host=MCP_HOST, port=MCP_PORT)
elif transport == "streamable-http":
    mcp.run(transport="streamable-http", host=MCP_HOST, port=MCP_PORT)
```

**References:**
- [Configure MCP Server - Kore.ai](https://docs.kore.ai/agent-platform/ai-agents/tools/configure-mcp-server/)
- [MCP Transports Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)

---

### REQ-002: Enhance Tool JSON Schemas for Kore.ai Form Generation

**Priority:** CRITICAL
**Current:** FastMCP auto-generates basic schemas from Python type hints — missing `enum`, `description`, and proper `required` arrays
**Required:** Rich JSON schemas that enable Kore.ai to auto-generate proper input forms with dropdowns, descriptions, and validation

**Acceptance Criteria:**
- [ ] `filing_status` parameter has `enum: ["single", "married_joint", "married_separate", "head_of_household"]` — renders as dropdown in Kore.ai
- [ ] `state` parameter has `enum` of all 50 states + DC — renders as dropdown
- [ ] Every parameter has a human-readable `description` — shown as field label/help text
- [ ] `required` array correctly lists mandatory parameters per tool
- [ ] `type` correctly set for all parameters (string, number, integer, array)
- [ ] Optional parameters have sensible `default` values in schema
- [ ] Schemas validated against JSON Schema Draft 2020-12

**Per-Tool Schema Requirements:**

#### validate_projection_inputs
```
Required: current_age, retirement_age, filing_status, state, annual_income, trad_ira_balance
Optional with defaults: roth_ira_balance_initial(0), cost_basis(0), annual_return(0.07),
                        model_years(30), social_security(0), rmd(0)
Optional no default: conversion_amount, conversion_schedule
Enums: filing_status, state
```

#### estimate_tax_components
```
Required: annual_income, conversion_amount, filing_status, state
Optional with defaults: cost_basis(0), social_security(0), rmd(0), other_ordinary_income(0)
Enums: filing_status, state
```

#### analyze_roth_projections
```
Required: trad_ira_balance, current_age
Optional with defaults: roth_ira_balance_initial(0), annual_return(0.07), model_years(30),
                        annual_income(0), filing_status("single"), state("CA"), social_security(0)
Optional no default: conversion_schedule
Enums: filing_status, state
```

#### optimize_conversion_schedule
```
Required: trad_ira_balance, annual_income, filing_status, state, current_age, retirement_age
Optional with defaults: model_years(30), annual_return(0.07), optimization_goal("minimize_tax")
Optional no default: max_annual_conversion, target_tax_bracket
Enums: filing_status, state, optimization_goal
```

#### breakeven_analysis
```
Required: conversion_amount, current_age
Optional with defaults: annual_return(0.07), retirement_age(65)
Optional no default: total_tax_cost, future_tax_rate, federal_tax, state_tax
```

#### generate_conversion_report
```
Required: validated_inputs, tax_analysis
Optional: projection_data(""), optimization_data(""), breakeven_data("")
```

**Implementation Approach:**
Use FastMCP's `Field()` with `description` and custom schema injection, or use Pydantic models as tool input types with `Field(description=..., json_schema_extra={"enum": [...]})`.

---

### REQ-003: Add Lean Response Mode (Data-Only)

**Priority:** HIGH
**Current:** Every tool returns `{"display": "<html>...", "data": {...}}` — HTML wastes Kore.ai LLM context tokens
**Required:** Configurable response mode that omits HTML for non-Streamlit clients

**Acceptance Criteria:**
- [ ] Environment variable `RESPONSE_MODE` controls output format
- [ ] `RESPONSE_MODE=full` (default): Returns `{"display": html, "data": dict}` (current behavior)
- [ ] `RESPONSE_MODE=data_only`: Returns only the `data` dict as JSON string (no HTML generation)
- [ ] HTML template functions NOT called when `RESPONSE_MODE=data_only` (performance improvement)
- [ ] All 6 tools respect the response mode setting
- [ ] Kore.ai receives clean, structured JSON without HTML noise
- [ ] Existing Streamlit functionality unaffected in `full` mode

**Implementation Notes:**
```python
# dual_return.py
RESPONSE_MODE = os.getenv("RESPONSE_MODE", "full")

def dual_return(html: str, data: dict) -> str:
    if RESPONSE_MODE == "data_only":
        return json.dumps(data)
    return json.dumps({"display": html, "data": data})
```

---

### REQ-004: Improve Tool Descriptions for LLM Intent Detection

**Priority:** HIGH
**Current:** Tool docstrings exist but are not optimized for Kore.ai's LLM tool selection
**Required:** Descriptive, specific tool descriptions that help Kore.ai's LLM correctly select tools

**Acceptance Criteria:**
- [ ] Each tool docstring clearly states: (1) what it does, (2) when to use it, (3) what it returns
- [ ] Descriptions include trigger phrases that match common user queries
- [ ] Descriptions specify prerequisite tools (e.g., "Call validate_projection_inputs first")
- [ ] No ambiguity between tools — each has a distinct purpose statement

**Proposed Descriptions:**

| Tool | Current | Proposed |
|---|---|---|
| validate_projection_inputs | "Validate and prepare all user financial inputs..." | "Validate user financial inputs for Roth IRA conversion analysis. Use this FIRST when a user provides their age, income, IRA balance, filing status, or state. Returns validation status and auto-fills defaults for social security, RMD, and growth assumptions." |
| estimate_tax_components | "Calculate federal tax, state tax, IRMAA surcharge..." | "Calculate the total tax cost of a specific Roth IRA conversion amount. Breaks down federal income tax, state income tax, Medicare IRMAA surcharge, Social Security tax impact, and RMD tax. Use when the user asks 'how much tax would I pay' or 'what's the tax cost'." |
| analyze_roth_projections | "Generate year-by-year comparison..." | "Project year-by-year IRA balances comparing Roth conversion vs. no conversion scenarios over 30 years. Shows crossover point where Roth path becomes advantageous. Use when the user asks about 'projections', 'what happens over time', or 'compare scenarios'." |
| optimize_conversion_schedule | "Find the optimal multi-year Roth conversion schedule..." | "Find the optimal multi-year Roth conversion schedule that minimizes total lifetime tax cost using a bracket-filling strategy. Use when the user asks 'what's the best strategy', 'how should I split conversions', or 'optimize my conversion'." |
| breakeven_analysis | "Calculate how many years until the Roth conversion pays for itself." | "Calculate how many years until a Roth conversion pays for itself in after-tax wealth. Returns breakeven age and assessment (worth_it/marginal/not_worth_it). Use when the user asks 'how long until it pays off', 'is it worth it', or 'breakeven point'." |
| generate_conversion_report | "Generate a comprehensive HTML report..." | "Generate a comprehensive summary report combining all prior analysis results (validation, tax estimate, projections, optimization, breakeven). Call this LAST after all other analyses are complete. Use when the user asks for a 'full report', 'summary', or 'put it all together'." |

---

### REQ-005: Ensure Tool Independence (No Pipeline Dependency)

**Priority:** HIGH
**Current:** `pipeline.py` auto-triggers a 3-stage sequence when validation returns `status: "complete"`. Kore.ai's LLM handles orchestration — tools must work independently.
**Required:** Each tool must be callable independently without relying on pipeline orchestration

**Acceptance Criteria:**
- [ ] Each tool validates its own required parameters independently
- [ ] No tool assumes another tool was called first (except generate_conversion_report which needs prior results)
- [ ] Error messages clearly state what inputs are missing
- [ ] Tools return meaningful results even when called in isolation
- [ ] Pipeline auto-trigger logic remains in agent_loop.py (Streamlit path only) — NOT in mcp_server.py

**Current Status:** Already satisfied — tools in mcp_server.py already validate independently. The pipeline auto-trigger is in agent_loop.py, not in the MCP server. No changes needed to tool code itself, but this must be verified and documented.

---

### REQ-006: Separate Codebase into MCP Core vs Client-Specific

**Priority:** HIGH
**Current:** GPT-specific, Streamlit-specific, and MCP core code are mixed in the same directory
**Required:** Clear separation so Kore.ai deployment only includes necessary files

**Acceptance Criteria:**
- [ ] Project structure reorganized into clear modules:

```
roth_mcp/
├── mcp_server.py          # MCP server entry point (CORE)
├── dual_return.py          # Response envelope (CORE)
├── validators.py           # Input validation (CORE)
├── models.py               # Data models (CORE - remove GPT-specific models)
├── config.py               # Configuration (CORE - multi-mode)
├── tax/                    # Tax calculations (CORE)
│   ├── __init__.py
│   ├── brackets.py
│   ├── calculator.py
│   ├── irmaa.py
│   ├── rmd.py
│   ├── ss.py
│   └── state_rates.py
├── clients/                # Client-specific code (NEW directory)
│   ├── streamlit/
│   │   ├── streamlit_app.py
│   │   ├── agent_loop.py
│   │   ├── pipeline.py
│   │   ├── mcp_client.py
│   │   ├── schema_converter.py
│   │   └── html_templates/
│   └── koreai/
│       └── README.md       # Kore.ai setup instructions
├── prompts/                # GPT prompts (Streamlit-specific)
│   └── system.md
├── tests/                  # All tests
├── docs/                   # Documentation
│   ├── KOREAI_REQUIREMENTS.md
│   └── KOREAI_SETUP_GUIDE.md
├── requirements.txt        # Full requirements
├── requirements-core.txt   # MCP server only (NEW)
└── requirements-streamlit.txt  # Streamlit extras (NEW)
```

- [ ] `requirements-core.txt` contains only MCP server dependencies:
  ```
  fastmcp>=2.14,<4.0
  mcp>=1.0,<3.0
  python-dotenv>=1.0,<2.0
  ```
- [ ] `requirements-streamlit.txt` adds Streamlit/GPT dependencies:
  ```
  -r requirements-core.txt
  streamlit>=1.33,<2.0
  openai>=1.0,<3.0
  nest-asyncio>=1.6,<2.0
  ```
- [ ] MCP server starts with only core dependencies installed
- [ ] Streamlit app starts with full dependencies installed
- [ ] No circular imports between core and client-specific code

---

### REQ-007: Add Authentication Support

**Priority:** MEDIUM
**Current:** No authentication — stdio transport doesn't need it
**Required:** Authentication mechanism for HTTP/SSE transport (Kore.ai passes Authorization headers)

**Acceptance Criteria:**
- [ ] Environment variable `MCP_AUTH_TOKEN` sets expected bearer token
- [ ] When set, server validates `Authorization: Bearer <token>` header on all requests
- [ ] When not set, server runs without authentication (development mode)
- [ ] Invalid/missing token returns 401 Unauthorized
- [ ] Stdio transport ignores authentication (not applicable)
- [ ] Kore.ai configuration documentation includes Authorization header setup

---

### REQ-008: Add Kore.ai Setup Guide

**Priority:** MEDIUM
**Required:** Step-by-step guide for configuring roth_mcp as an MCP server in Kore.ai

**Acceptance Criteria:**
- [ ] Document covers:
  1. Prerequisites (Python, dependencies, Kore.ai account)
  2. Starting the MCP server with SSE/HTTP transport
  3. Configuring the MCP server in Kore.ai (URL, headers, transport type)
  4. Testing tool discovery
  5. Selecting tools and configuring parameters
  6. Setting up Entity Rules for auto-extraction
  7. Setting up Answering Rules (optional)
  8. Configuring conversation starters
  9. Testing the agent end-to-end
  10. Troubleshooting common issues

**Recommended Parameter Configuration Table:**

| Tool | Parameter | Kore.ai Mode | Notes |
|---|---|---|---|
| validate_projection_inputs | current_age | Dynamic > Extract from Query | Auto-extracts age |
| validate_projection_inputs | retirement_age | Dynamic > Extract from Query | "retire at 65" |
| validate_projection_inputs | filing_status | Dynamic > Extract from Query | Entity rule for "married" |
| validate_projection_inputs | state | Dynamic > Extract from Query | Entity rule for state names |
| validate_projection_inputs | annual_income | Dynamic > Extract from Query | "$150k income" |
| validate_projection_inputs | trad_ira_balance | Dynamic > Extract from Query | "$500k in IRA" |
| validate_projection_inputs | conversion_amount | Dynamic > Collect from Form | User decides amount |
| validate_projection_inputs | annual_return | Static = 0.07 | Hidden from user |
| validate_projection_inputs | model_years | Static = 30 | Hidden from user |
| validate_projection_inputs | social_security | Static = 0 | Server auto-fills based on age |
| validate_projection_inputs | rmd | Static = 0 | Server auto-fills based on age |
| validate_projection_inputs | cost_basis | Static = 0 | Hidden from user |

**Recommended Entity Rules:**

| Keyword Pattern | Entity | Value |
|---|---|---|
| "married", "joint", "jointly" | filing_status | married_joint |
| "single", "unmarried" | filing_status | single |
| "head of household", "HOH" | filing_status | head_of_household |
| "married separate", "separately" | filing_status | married_separate |
| State names (California, Texas...) | state | CA, TX, etc. |
| Age patterns ("I'm 55", "age 55") | current_age | extracted integer |
| Income patterns ("$150k", "150000") | annual_income | extracted float |

**Recommended Conversation Starters:**
1. "Help me decide if a Roth conversion makes sense"
2. "How much tax would I owe on a Roth IRA conversion?"
3. "What's the best Roth conversion strategy to minimize taxes?"
4. "How many years until a Roth conversion pays off?"
5. "Analyze my Roth conversion options"

---

### REQ-009: Standardize Error Responses for Kore.ai

**Priority:** MEDIUM
**Current:** Errors return dual_return with HTML error div + error dict (inconsistent structure)
**Required:** Consistent, structured error responses that Kore.ai's LLM can interpret

**Acceptance Criteria:**
- [ ] All error responses follow a standard structure:
  ```json
  {
    "error": true,
    "error_type": "missing_required_fields|validation_error|computation_error",
    "message": "Human-readable error description",
    "missing_fields": ["field1", "field2"],
    "details": [
      {"field": "current_age", "message": "Age must be between 18 and 100"}
    ]
  }
  ```
- [ ] Error messages are actionable — tell the user exactly what to provide
- [ ] Validation errors list ALL problems at once (not just the first)
- [ ] FastMCP `isError` flag set correctly on tool-level failures
- [ ] No raw Python exceptions leak to the client

---

### REQ-010: Add Health Check / Ping Endpoint

**Priority:** LOW
**Current:** No health check mechanism
**Required:** Simple endpoint for Kore.ai to verify server availability

**Acceptance Criteria:**
- [ ] MCP server exposes a lightweight tool or endpoint for health checking
- [ ] Returns server version, uptime, and available tool count
- [ ] Response time < 100ms
- [ ] Can be used by Kore.ai's "Test" button during configuration

---

### REQ-011: Add Rate Limiting for HTTP/SSE Transport

**Priority:** LOW
**Current:** No rate limiting — stdio is single-client
**Required:** Basic rate limiting for multi-client HTTP/SSE deployment

**Acceptance Criteria:**
- [ ] Configurable rate limit via `MCP_RATE_LIMIT` env var (default: 60 requests/minute)
- [ ] Rate limiting applied per-client (by IP or auth token)
- [ ] Exceeded rate limit returns appropriate error response
- [ ] Stdio transport has no rate limiting

---

### REQ-012: Add Request/Response Logging

**Priority:** LOW
**Current:** Minimal logging (tool execution timing only)
**Required:** Structured logging for debugging Kore.ai integration

**Acceptance Criteria:**
- [ ] Every tool call logged: tool name, parameters (sanitized), execution time, response status
- [ ] Log level configurable via `LOG_LEVEL` env var
- [ ] Sensitive data (if any) masked in logs
- [ ] JSON-formatted logs for production (configurable)
- [ ] Request correlation ID for tracing

---

## 4. Environment Variables (Complete List)

### Existing (Keep)
| Variable | Default | Used By | Notes |
|---|---|---|---|
| LOG_LEVEL | WARNING | All | Logging verbosity |
| MCP_SERVER_CMD | python | Streamlit client | Server command |
| MCP_SERVER_ARGS | mcp_server.py | Streamlit client | Server args |

### Existing (Streamlit-Only, Keep for Streamlit)
| Variable | Default | Used By | Notes |
|---|---|---|---|
| OPENAI_API_KEY | "" | Streamlit | GPT API key |
| OPENAI_MODEL | gpt-4o-mini | Streamlit | GPT model |
| OPENAI_TIMEOUT | 30 | Streamlit | API timeout |
| MAX_SESSION_COST | 0.50 | Streamlit | Cost limit |

### New (Add for Kore.ai)
| Variable | Default | Used By | Notes |
|---|---|---|---|
| MCP_TRANSPORT | stdio | MCP server | Transport: stdio, sse, streamable-http |
| MCP_HOST | 0.0.0.0 | MCP server | Bind host for HTTP/SSE |
| MCP_PORT | 8080 | MCP server | Bind port for HTTP/SSE |
| MCP_AUTH_TOKEN | "" | MCP server | Bearer token (empty = no auth) |
| RESPONSE_MODE | full | MCP server | full or data_only |
| MCP_RATE_LIMIT | 60 | MCP server | Requests per minute (0 = disabled) |

---

## 5. Migration Path

### Phase 1: Non-Breaking Changes (Can deploy immediately)
1. REQ-001: Add transport support (env var, no code changes to tools)
2. REQ-003: Add response mode toggle (env var in dual_return.py)
3. REQ-004: Improve tool docstrings (text changes only)
4. REQ-008: Write Kore.ai setup guide (documentation only)

### Phase 2: Schema Enhancement
5. REQ-002: Add enum, description, required to tool schemas
6. REQ-009: Standardize error responses
7. REQ-005: Verify tool independence (audit + tests)

### Phase 3: Architecture Cleanup
8. REQ-006: Reorganize project structure
9. REQ-007: Add authentication
10. REQ-010: Add health check
11. REQ-011: Add rate limiting
12. REQ-012: Add structured logging

---

## 6. Testing Strategy

### Unit Tests (Existing — Verify)
- All 305+ existing tests must pass after changes
- No regression in tax calculations
- No regression in validation logic

### New Tests Required
- [ ] Transport tests: server starts with stdio, sse, streamable-http
- [ ] Response mode tests: data_only returns clean JSON, full returns dual envelope
- [ ] Schema tests: all tools have correct required/enum/description in schema
- [ ] Error format tests: all error responses match standard structure
- [ ] Auth tests: valid token accepted, invalid rejected, no token in dev mode
- [ ] Integration test: Kore.ai-simulated tool discovery and invocation

### Kore.ai Integration Testing
- [ ] Configure MCP server in Kore.ai test environment
- [ ] Verify all 6 tools discovered correctly
- [ ] Verify form auto-generation with correct field types and dropdowns
- [ ] Verify entity extraction works for common phrases
- [ ] Verify end-to-end flow: conversation starter → form → results
- [ ] Verify error handling: missing fields, invalid values

---

## 7. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Schema changes break existing tests | Medium | Medium | Run full test suite after each change |
| Transport change introduces latency | Low | Low | Benchmark stdio vs SSE performance |
| Kore.ai doesn't support all JSON Schema features | Medium | Medium | Test with minimal schema first, add features incrementally |
| Tool descriptions too long for Kore.ai context | Low | Low | Keep under 200 chars, test with Kore.ai |
| Breaking Streamlit functionality | High | Medium | Maintain backward compatibility via env vars |
| SSE transport deprecated by MCP spec | Medium | High | Implement streamable-http as primary, SSE as fallback |

---

## 8. Sources

### Kore.ai Documentation
- [MCP Tools Overview](https://docs.kore.ai/agent-platform/ai-agents/tools/mcp-tools/)
- [Configure MCP Server](https://docs.kore.ai/agent-platform/ai-agents/tools/configure-mcp-server/)
- [MCP Agents (AI for Work)](https://docs.kore.ai/ai-for-work/custom-agents/mcp-agents/)
- [Tool Calling Overview](https://docs.kore.ai/agent-platform/ai-agents/tools/tool-calling/)
- [AgenticAI SDK Architecture](https://docs.kore.ai/agent-platform/sdk/design-decisions/architecture/)
- [About Agent Node](https://docs.kore.ai/xo/automation/agent-node/working-with-agent-node/)

### Kore.ai Blog/Insights
- [Introducing MCP](https://www.kore.ai/ai-insights/introducing-mcp-a-new-standard-for-dynamic-ai-integration)
- [MCP Orchestration for Scalable Enterprise AI](https://www.kore.ai/ai-insights/mcp-orchestration-for-scalable-enterprise-ai-kore-ai)

### MCP Specification
- [MCP Transports](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [MCP Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)

### Best Practices
- [7 MCP Server Best Practices - MarkTechPost](https://www.marktechpost.com/2025/07/23/7-mcp-server-best-practices-for-scalable-ai-integrations-in-2025/)
- [MCP Server Best Practices 2026 - CData](https://www.cdata.com/blog/mcp-server-best-practices-2026)
- [MCP Security Best Practices - Akto](https://www.akto.io/blog/mcp-security-best-practices)
