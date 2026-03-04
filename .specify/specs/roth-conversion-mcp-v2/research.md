# Research: Roth Conversion Calculator MCP Server v2.0

**Date**: 2026-03-03
**Phase**: 0 — Research & Unknowns Resolution

---

## R1: FastMCP Server Pattern (stdio transport)

**Decision**: Use FastMCP >=2.14 with stdio transport for MCP server.

**Rationale**: FastMCP is the official Python SDK for building MCP servers. The PRD specifies stdio transport (subprocess spawned by client). FastMCP's `@mcp.tool()` decorator pattern is straightforward — each tool function returns a JSON string (our dual-return envelope).

**Alternatives Considered**:
- Raw `mcp` SDK without FastMCP — more boilerplate, no advantage
- SSE/HTTP transport — requires separate server process, adds complexity for local-only use
- WebSocket transport — overkill for single-user local app

**Key Implementation Notes**:
- `mcp = FastMCP("roth-conversion-calculator")` at module level
- Tools registered via `@mcp.tool()` decorator
- Entry point: `mcp.run(transport="stdio")`
- All tool parameters use `float | None`, `int | None`, `list[float] | None` union types
- FastMCP handles JSON schema generation for these types automatically

---

## R2: MCP Client Session Management in Streamlit

**Decision**: Use `mcp` Python package with `stdio_client` + `ClientSession`, cached via `@st.cache_resource`.

**Rationale**: Streamlit re-runs the entire script on each interaction. The MCP session (subprocess) must persist across re-runs. `@st.cache_resource` keeps the session alive. `nest-asyncio` resolves the async/sync boundary since Streamlit is sync but MCP client is async.

**Alternatives Considered**:
- Creating new session per request — too slow (subprocess spawn ~500ms)
- Using `streamlit-extras` async support — immature, unreliable
- Running MCP server as separate process (not subprocess) — complicates startup

**Key Implementation Notes**:
- `nest_asyncio.apply()` at top of `streamlit_app.py`
- Session init in `@st.cache_resource` with `asyncio.new_event_loop()`
- `ResilientToolExecutor` wraps session for retry/restart on crash
- Windows requires careful stdout flushing in MCP server (buffering issues)

---

## R3: OpenAI Function Calling with MCP Schema Translation

**Decision**: Translate MCP tool schemas to OpenAI function calling format at tool discovery time.

**Rationale**: MCP tools have `inputSchema` (JSON Schema). OpenAI function calling uses a similar but slightly different format. Translation is done once at session init, not per-call. The main complexity is `list[float] | None` → `{"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}]}`.

**Alternatives Considered**:
- Manual OpenAI function definitions (duplicates schema) — maintenance burden
- Using LangChain MCP adapter — adds heavy dependency for simple translation
- Anthropic Claude API instead of OpenAI — user specified OpenAI/GPT-4o-mini for cost

**Key Implementation Notes**:
- `mcp_tool_to_openai_function(mcp_tool)` maps `name`, `description`, `inputSchema`
- Override descriptions with `TOOL_DESCRIPTIONS` dict for better GPT tool selection
- `parallel_tool_calls=False` in OpenAI call to avoid concurrent MCP tool calls (stdio is serial)

---

## R4: Hybrid Orchestrator-Pipeline Pattern

**Decision**: GPT handles conversation (Phase 1 + 3), deterministic pipeline handles computation (Phase 2).

**Rationale**: Keeps GPT cost to ~$0.005/conversation by limiting GPT to input collection and summarization. The 6-tool pipeline runs without GPT round-trips. 3-way parallelism in Stage 2 via `asyncio.gather`.

**Alternatives Considered**:
- Pure GPT agent (all tools via function calling) — 10-15 GPT calls, $0.02-0.05/conversation
- Pure deterministic (no GPT) — loses conversational UX
- LangChain agent — heavy dependency, harder to control cost

**Key Implementation Notes**:
- `agent_loop.py`: GPT conversation loop, calls `validate_projection_inputs`
- `pipeline.py`: Deterministic `run_analysis_pipeline()` — tax → (3-way parallel) → report
- Pipeline triggered when `validate_projection_inputs` returns `status=complete`
- `compact_result()` strips HTML before adding tool results to GPT context

---

## R5: Tax Calculation Architecture

**Decision**: Shared computation layer (`tax/`) with pure functions, imported directly by MCP tools.

**Rationale**: Tools like `optimize_conversion_schedule` need to call `compute_tax_components` hundreds of times during optimization. Going through MCP protocol for internal calls would be prohibitively slow. Direct function import is the correct pattern.

**Alternatives Considered**:
- All computation inside MCP tool functions — code duplication, no reuse
- Separate tax microservice — overkill for local app
- Tool-to-tool MCP calls — MCP doesn't support server-side tool composition natively

**Key Implementation Notes**:
- `tax/calculator.py` — `compute_tax_components()` main entry point
- `tax/brackets.py` — 2024 federal brackets for all 4 filing statuses
- `tax/state_rates.py` — simplified flat effective rates for 50 states + DC
- `tax/irmaa.py` — IRMAA surcharge lookup with 2-year lookback note
- `tax/rmd.py` — Uniform Lifetime Table, ages 73-120
- `tax/ss.py` — provisional income formula for all filing statuses
- Standard deduction applied BEFORE bracket calculation

---

## R6: HTML Template Strategy

**Decision**: Inline CSS in Python f-string templates, one formatter per tool, no external CSS files.

**Rationale**: HTML is rendered via `st.html()` and `components.html()` in Streamlit. These render in iframes, so external CSS doesn't work. Inline styles are the only reliable approach. Each tool has a distinct color code for visual differentiation.

**Alternatives Considered**:
- Jinja2 templates — adds dependency, complicates for simple HTML cards
- Streamlit native components — can't achieve the styled card design
- React components via `streamlit-component-lib` — massive overkill

**Key Implementation Notes**:
- `html/templates.py` — 6 formatter functions
- `html/styles.py` — shared style constants (colors, fonts, spacing)
- Color scheme: green (validation), red (tax), blue (projection/breakeven), purple (optimization)
- `<details>` for collapsible projection table (show 5 years, expand for all)
- Report template is a full styled document with all sections

---

## R7: Input Validation Strategy

**Decision**: Single `validators.py` module with per-field validation + cross-field rules.

**Rationale**: All 17+ inputs validated in `validate_projection_inputs`. Returns structured result with `status` (complete/incomplete), validated values, auto-filled defaults, and any errors. This is the gateway — all other tools depend on it.

**Alternatives Considered**:
- Pydantic model validation — adds dependency for simple rules
- Validation in each tool — duplicates rules
- Client-side only validation — MCP tools must be self-validating

**Key Implementation Notes**:
- Range checks: age 18-100, income >= 0, return -1 to 0.30, model_years 1-50
- Enum checks: filing_status, state code
- Cross-field: conversion_amount <= trad_ira_balance, retirement_age > current_age
- Auto-fill: SS=0 if age<62, RMD=0 if age<73, IRMAA=0 if income below threshold
- conversion_amount → conversion_schedule=[conversion_amount] auto-wrap

---

## R8: Streamlit Session State Architecture

**Decision**: Session state with 7 keys: messages, profile, assumptions, results, html_cards, token_data, pipeline_phase.

**Rationale**: Streamlit re-runs on every interaction. All state must be in `st.session_state`. The 7 keys cover conversation history, user data, calculation results, rendered HTML, API tracking, and pipeline progress.

**Alternatives Considered**:
- Database-backed sessions — overkill for single-user local app
- File-based state — fragile, race conditions
- Redux-style state management — not available in Streamlit

**Key Implementation Notes**:
- `initialize_session_state()` called at app start
- `UserProfile` dataclass stored in `st.session_state.profile`
- `html_cards` dict maps tool_name → HTML string for rendering
- `pipeline_phase` enum: collecting → analyzing → complete
- "Start Over" button resets all session state

---

## R9: Anti-Hallucination Guardrail

**Decision**: Post-GPT regex check for dollar amounts, percentages, and breakeven years not found in tool results.

**Rationale**: GPT-4o-mini occasionally fabricates financial numbers. The system prompt instructs it not to, but a runtime check provides a safety net. Flagged numbers trigger a warning in the UI.

**Alternatives Considered**:
- Structured output (JSON mode) — doesn't prevent hallucinated values in text
- Fine-tuned model — too expensive for this use case
- No guardrail — acceptable for demo but risky for user trust

**Key Implementation Notes**:
- `check_hallucinated_numbers(gpt_response, tool_results)` returns list of suspicious values
- Regex patterns: `\$[\d,]+(?:\.\d{2})?`, `(\d+(?:\.\d+)?)\s*%`, `(\d+)\s*years?\s*(?:to break|until)`
- If suspicious found, append warning to GPT response
- This is a best-effort check, not foolproof

---

## R10: Windows Compatibility

**Decision**: Target Windows as primary dev platform with Linux/macOS compatibility.

**Rationale**: The developer works on Windows 11. Key risk: MCP stdio transport on Windows has buffering issues. Must flush stdout explicitly in server, handle `OSError` in client.

**Key Implementation Notes**:
- MCP server: `sys.stdout.flush()` or set `PYTHONUNBUFFERED=1`
- Path handling: use `pathlib.Path` or forward slashes
- Async: `nest-asyncio` required for Streamlit + asyncio on all platforms
- Process spawning: `StdioServerParameters(command="python", args=["mcp_server.py"])` — works on Windows
- Test early on Windows for subprocess/pipe issues
