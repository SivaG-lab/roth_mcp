# Feature Specification: Roth Conversion Calculator MCP Server v2.0

**Feature Branch**: `roth-conversion-mcp-v2`
**Created**: 2026-03-03
**Status**: Draft
**Input**: PRD-roth-conversion-mcp-v2.md — Two-component system: FastMCP Server (6 tools) + Streamlit Chat Agent (MCP client with OpenAI GPT orchestration)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tax Engine & Shared Computation Layer (Priority: P1)

A developer sets up the project foundation: federal+state tax brackets, IRMAA surcharge, RMD calculation, Social Security taxation, and the shared computation layer that all MCP tools depend on. This is the pure-logic layer with zero MCP/UI dependencies.

**Why this priority**: Every tool in the system depends on accurate tax computation. Without this, nothing works.

**Independent Test**: Can be fully tested with unit tests — pass financial inputs, verify tax outputs against known scenarios. No server or UI needed.

**Acceptance Scenarios**:

1. **Given** annual_income=$150,000, filing_status=married_joint, conversion_amount=$50,000, state=CA, **When** compute_tax_components() is called, **Then** returns federal_tax, state_tax, irmaa_impact, ss_tax_impact, rmd_tax, total_tax_cost, effective_rate, marginal_rate, bracket_before, bracket_after.
2. **Given** MAGI=$260,000 and filing_status=married_joint, **When** compute_irmaa_surcharge() is called, **Then** returns $1,977.60/year (monthly $164.80 × 12).
3. **Given** age=75 and ira_balance=$500,000, **When** compute_rmd() is called, **Then** returns $500,000/24.6 = $20,325.20.
4. **Given** ss_benefit=$24,000, other_income=$60,000, filing_status=married_joint, **When** compute_ss_taxation() is called, **Then** returns taxable portion based on provisional income formula.
5. **Given** annual_income=$150,000, filing_status=married_joint, **When** compute_bracket_boundaries() is called, **Then** returns the top of the current bracket and next bracket ceiling.

---

### User Story 2 - Input Validation & Dual-Return Pattern (Priority: P1)

The system validates all 17+ financial inputs with entity rules, applies smart auto-fill defaults, and every tool returns dual-format: `{"data": JSON, "display": HTML}`. The validators module and dual_return module are foundational.

**Why this priority**: All tools need input validation and the dual-return envelope. This is the API contract.

**Independent Test**: Unit test validators with valid/invalid inputs, test dual_return/extract_html/extract_data/compact_result functions.

**Acceptance Scenarios**:

1. **Given** current_age=55, retirement_age=65, filing_status=married_joint, state=CA, annual_income=150000, trad_ira_balance=500000, conversion_amount=50000, **When** validate_projection_inputs is called, **Then** returns status=complete with all validated inputs + auto-filled defaults (annual_return=0.07, model_years=30, social_security=0, rmd=0, irmaa=0).
2. **Given** current_age=110, **When** validation runs, **Then** returns error "Age must be between 18 and 100".
3. **Given** conversion_amount=600000 with trad_ira_balance=500000, **When** validation runs, **Then** returns error "Conversion amount must be ≤ IRA balance".
4. **Given** any tool returns dual-return JSON, **When** extract_html() is called, **Then** returns HTML string. **When** extract_data() is called, **Then** returns data dict. **When** compact_result() is called, **Then** returns data without HTML (for GPT context).

---

### User Story 3 - FastMCP Server with 6 Tools (Priority: P1)

The FastMCP server exposes 6 tools via MCP stdio transport: validate_projection_inputs, estimate_tax_components, analyze_roth_projections, optimize_conversion_schedule, breakeven_analysis, generate_conversion_report. Each tool wraps shared computation + returns dual-format.

**Why this priority**: The MCP server is the core backend — tools must be callable via MCP protocol before the client can work.

**Independent Test**: Start server as subprocess, connect via MCP client, call each tool with test data, verify dual-return format.

**Acceptance Scenarios**:

1. **Given** mcp_server.py is running, **When** MCP client lists tools, **Then** 6 tools are discovered with correct schemas (including list[float] parameters).
2. **Given** validated inputs, **When** estimate_tax_components is called via MCP, **Then** returns `{"data": {federal_tax, state_tax, ...}, "display": "<div>...HTML...</div>"}`.
3. **Given** validated inputs + tax data, **When** analyze_roth_projections is called, **Then** returns year-by-year projection data for model_years with convert vs no-convert comparison.
4. **Given** trad_ira_balance=$500k, annual_income=$150k, filing_status=married_joint, state=CA, **When** optimize_conversion_schedule is called, **Then** returns optimal multi-year schedule with bracket-fill algorithm.
5. **Given** conversion_amount=$50k, total_tax_cost=$16k, current_age=55, **When** breakeven_analysis is called, **Then** returns breakeven_years, breakeven_age, assessment (worth_it/marginal/not_worth_it).
6. **Given** all prior tool results as JSON strings, **When** generate_conversion_report is called, **Then** returns comprehensive styled HTML report with all sections.

---

### User Story 4 - HTML Templates & Styling (Priority: P2)

Each of the 6 tools produces a styled HTML card with tool-specific color coding: green (validation), red (tax), blue (projection/breakeven), purple (optimization), full-style (report). Templates use inline CSS for portability.

**Why this priority**: HTML output is the user-facing deliverable. Without styled cards, the Streamlit UI has nothing to render.

**Independent Test**: Call each HTML template function with mock data, verify HTML structure and color coding.

**Acceptance Scenarios**:

1. **Given** validation data, **When** format_validation_result() is called, **Then** returns HTML with green border-left (#22c55e), shows age range, IRA balance, schedule length, assumptions.
2. **Given** tax data, **When** format_tax_estimate() is called, **Then** returns HTML with red border-left (#ef4444), shows federal/state/IRMAA/SS tax breakdown table.
3. **Given** projection data list, **When** format_projection_table() is called, **Then** returns HTML with blue border-left, 5-year summary + expandable full table via `<details>`.
4. **Given** breakeven data, **When** format_breakeven() is called, **Then** returns HTML with blue border-left, breakeven years, age, assessment.
5. **Given** all tool results, **When** generate_conversion_report builds HTML, **Then** produces full styled report with header, assumptions, tax breakdown, projection table, schedule, breakeven, recommendations, disclaimer.

---

### User Story 5 - MCP Client & Schema Translation (Priority: P2)

The Streamlit app manages the MCP client session (persistent, stdio transport), translates MCP tool schemas to OpenAI function calling format, and wraps tool calls with resilient execution (retry, timeout, subprocess restart).

**Why this priority**: The client bridge between GPT and MCP server. Without it, the Streamlit agent can't discover or call tools.

**Independent Test**: Start MCP server, create client session, verify tool discovery, call each tool, verify schema translation produces valid OpenAI function definitions.

**Acceptance Scenarios**:

1. **Given** mcp_server.py as subprocess, **When** MCP session initializes, **Then** connection is established and 6 tools are listed.
2. **Given** MCP tool schema with `list[float] | None`, **When** mcp_tool_to_openai_function() translates, **Then** produces valid OpenAI function JSON with `{"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}]}`.
3. **Given** MCP server crashes, **When** ResilientToolExecutor retries, **Then** restarts subprocess and retries (max 2 retries).
4. **Given** optimize_conversion_schedule takes >30s, **When** timeout fires, **Then** returns graceful error with best available result.

---

### User Story 6 - GPT Agent Loop & Deterministic Pipeline (Priority: P2)

The agent_loop.py handles the GPT conversation loop (Phase 1: input collection, Phase 3: summary). The pipeline.py runs the deterministic computation pipeline (Phase 2: tax → 3-way parallel → report) without GPT round-trips. HTML cards are rendered via st.html() during st.status progress.

**Why this priority**: This is the orchestration core — the hybrid pattern that keeps GPT costs to ~$0.005/conversation.

**Independent Test**: Mock MCP session + OpenAI responses, verify agent loop calls validate_projection_inputs, triggers pipeline on input completion, pipeline runs 6 tools in correct order with 3-way parallelism.

**Acceptance Scenarios**:

1. **Given** user says "I'm 55, MFJ, $150k income, $500k IRA, CA, convert $50k/yr for 5 years", **When** agent_loop processes message, **Then** GPT calls validate_projection_inputs with extracted values, inputs are complete, pipeline triggers automatically.
2. **Given** inputs are complete, **When** run_analysis_pipeline() executes, **Then** tools run in order: estimate_tax → (analyze_projections ∥ optimize_schedule ∥ breakeven) → generate_report.
3. **Given** one parallel tool fails, **When** asyncio.gather catches exception, **Then** remaining tools still complete and report generates with available sections.
4. **Given** pipeline completes, **When** GPT receives compacted summary, **Then** generates conversational summary using only tool-provided numbers (no hallucination).

---

### User Story 7 - Streamlit Chat UI (Priority: P2)

The streamlit_app.py provides a chat interface with st.chat_input(), st.chat_message(), sidebar with live user info + assumptions + API usage, session state management, and HTML card rendering for all 6 tools.

**Why this priority**: The user-facing interface. Without it, there's no way to interact with the system.

**Independent Test**: Run streamlit_app.py, verify welcome message, sidebar sections, chat input, HTML rendering areas.

**Acceptance Scenarios**:

1. **Given** fresh session, **When** app loads, **Then** welcome message appears, sidebar shows empty profile, pipeline_phase=collecting.
2. **Given** user submits message in chat, **When** agent_loop processes, **Then** response appears as assistant message, HTML cards render inline via st.html().
3. **Given** pipeline running, **When** st.status shows progress, **Then** each tool's HTML card appears as it completes (tax → projection → optimization → breakeven → report).
4. **Given** analysis complete, **When** report HTML is ready, **Then** rendered via components.html() with scrolling, download button available.
5. **Given** sidebar, **When** inputs are collected, **Then** sidebar updates live with user profile, assumptions, token usage, cost estimate.

---

### User Story 8 - System Prompt & Anti-Hallucination (Priority: P3)

The system prompt (prompts/system.md) instructs GPT on tool selection order, auto-fill rules, conversion schedule parsing, entity extraction, and the absolute rule against computing financial numbers. The anti-hallucination guardrail checks GPT responses for numbers not in tool results.

**Why this priority**: Quality and correctness of GPT behavior. Important but the system works without it (just less reliably).

**Independent Test**: Run prompt regression tests (14 cases from PRD), verify tool routing. Test anti-hallucination regex against known good/bad responses.

**Acceptance Scenarios**:

1. **Given** user says "I want to convert my IRA", **When** GPT processes with system prompt, **Then** GPT calls validate_projection_inputs (not estimate_tax or other tools).
2. **Given** user says "$50k per year for 5 years", **When** GPT extracts entities, **Then** passes conversion_schedule=[50000,50000,50000,50000,50000].
3. **Given** user asks "What bracket am I in?" without prior tool calls, **When** GPT responds, **Then** does NOT include dollar amounts or percentages (no hallucination).
4. **Given** GPT response contains "$45,000 tax" but tool result only has "$16,650", **When** check_hallucinated_numbers() runs, **Then** flags "$45,000" as suspicious.

---

### User Story 9 - Data Models & Configuration (Priority: P3)

models.py defines UserProfile, ModelAssumptions, TaxEstimate, ProjectionData, OptimizationResult, BreakevenResult, CalculationResults, TokenTracker dataclasses. config.py handles environment variable loading with validation.

**Why this priority**: Supporting infrastructure. The system could work with dicts, but dataclasses improve reliability.

**Independent Test**: Instantiate each dataclass, verify defaults, test to_tool_args(), missing_required, has_conversion_spec properties.

**Acceptance Scenarios**:

1. **Given** UserProfile with only current_age=55, **When** missing_required is checked, **Then** returns [retirement_age, filing_status, state, annual_income, trad_ira_balance].
2. **Given** .env with OPENAI_API_KEY, OPENAI_MODEL=gpt-4o-mini, **When** config loads, **Then** all values available with correct types.
3. **Given** UserProfile with all fields, **When** to_tool_args() called, **Then** returns dict with only non-None values.

---

### User Story 10 - Integration & E2E Testing (Priority: P3)

Full test suite: unit tests (80%, tax/IRMAA/RMD/SS/validators/dual-return/HTML/schemas), integration tests (15%, MCP roundtrip, pipeline), prompt regression tests (14 cases).

**Why this priority**: Quality assurance. The system should be tested at all layers.

**Independent Test**: Run `pytest` — all tests pass.

**Acceptance Scenarios**:

1. **Given** test_tax_calculator.py, **When** pytest runs, **Then** federal+state tax calculations match expected for all filing statuses.
2. **Given** test_irmaa.py, **When** pytest runs, **Then** IRMAA surcharges match IRS 2024 thresholds for all brackets and filing statuses.
3. **Given** test_rmd.py, **When** pytest runs, **Then** RMD calculations match Uniform Lifetime Table for ages 73-90+.
4. **Given** test_integration.py, **When** MCP server starts and tools are called, **Then** all 6 tools return valid dual-return JSON.
5. **Given** prompt_eval_cases.json, **When** regression tests run, **Then** GPT routes to correct tools for all 14 test cases.

---

### Edge Cases

- What happens when conversion_amount exceeds trad_ira_balance? → Validation error returned with clear message.
- What happens when user provides both conversion_amount and conversion_schedule? → conversion_schedule takes precedence; conversion_amount ignored.
- What happens when age < 18 or > 100? → Validation error.
- What happens when state code is invalid (e.g., "XX")? → Validation error with "Invalid state code".
- What happens when MCP server process crashes mid-pipeline? → ResilientToolExecutor restarts subprocess, retries (max 2).
- What happens when one of 3 parallel tools fails? → Pipeline continues with available results, report generates without failed section.
- What happens when OpenAI API rate limits? → Exponential backoff, max 3 retries.
- What happens when optimizer doesn't converge? → Returns best-so-far with converged=False, confidence<1.0.
- What happens when user says "convert all" with $0 IRA balance? → Validation error "IRA balance must be > 0".
- What happens when model_years=0 or negative? → Validation error "Model horizon must be 1-50 years".
- What happens when filing_status=married_separate for SS taxation? → 85% taxable (IRS special rule).

## Requirements *(mandatory)*

### Functional Requirements

**Tax Engine**:
- **FR-001**: System MUST compute federal tax using 2024 brackets for all 4 filing statuses (single, married_joint, married_separate, head_of_household) with standard deduction applied.
- **FR-002**: System MUST compute state tax using simplified flat rates for all 50 states + DC.
- **FR-003**: System MUST compute IRMAA surcharge based on MAGI and filing status using 2024 thresholds (6 tiers for single, 6 tiers for MFJ).
- **FR-004**: System MUST compute RMD using IRS Uniform Lifetime Table (2024) for ages 73+.
- **FR-005**: System MUST compute Social Security taxable portion using provisional income formula for all filing statuses.
- **FR-006**: System MUST apply standard deduction (2024: $14,600 single, $29,200 MFJ, $14,600 MFS, $21,900 HoH) with additional $1,550/$1,300 for age 65+.
- **FR-007**: System MUST compute bracket boundaries to identify current bracket ceiling and next bracket ceiling.

**Input Validation**:
- **FR-008**: System MUST validate current_age (18-100), retirement_age (> current_age, ≤ 100), annual_income (≥ 0), trad_ira_balance (≥ 0).
- **FR-009**: System MUST validate filing_status as enum [single, married_joint, married_separate, head_of_household].
- **FR-010**: System MUST validate state as valid 2-letter US state code.
- **FR-011**: System MUST validate conversion_amount (> 0, ≤ trad_ira_balance) or conversion_schedule (each ≥ 0, sum ≤ trad_ira_balance).
- **FR-012**: System MUST validate annual_return (> -1, ≤ 0.30) and model_years (1-50).

**Auto-Fill & Defaults**:
- **FR-013**: System MUST auto-fill social_security=0 when current_age < 62.
- **FR-014**: System MUST auto-fill rmd=0 when current_age < 73.
- **FR-015**: System MUST auto-fill irmaa=0 when annual_income < $103,000 (single) or $206,000 (MFJ).
- **FR-016**: System MUST default annual_return=0.07, model_years=30, roth_ira_balance_initial=0, taxable_dollars_available=0 when not specified.
- **FR-017**: System MUST auto-wrap single conversion_amount into conversion_schedule=[conversion_amount].

**MCP Server & Tools**:
- **FR-018**: System MUST expose 6 tools via FastMCP with stdio transport.
- **FR-019**: All 6 tools MUST return dual-format: `{"data": JSON, "display": HTML}`.
- **FR-020**: validate_projection_inputs MUST be the gateway tool — all other tools require its output first.
- **FR-021**: estimate_tax_components MUST compute federal + state + IRMAA + SS + RMD tax breakdown.
- **FR-022**: analyze_roth_projections MUST produce year-by-year convert vs no-convert comparison for full model_years horizon.
- **FR-023**: optimize_conversion_schedule MUST use greedy bracket-fill algorithm to find optimal multi-year schedule.
- **FR-024**: breakeven_analysis MUST compute years until Roth path ≥ Traditional path with assessment (worth_it/marginal/not_worth_it).
- **FR-025**: generate_conversion_report MUST assemble all tool results into comprehensive styled HTML report.
- **FR-026**: Tools 3, 4, 5 MUST call shared computation functions directly (not via MCP) for server-side composition.

**Agent & Pipeline**:
- **FR-027**: GPT conversation loop MUST collect inputs via natural language entity extraction.
- **FR-028**: Deterministic pipeline MUST run without GPT round-trips: tax → (projection ∥ optimization ∥ breakeven) → report.
- **FR-029**: Pipeline stage 2 MUST execute 3-way parallel via asyncio.gather.
- **FR-030**: Pipeline MUST handle partial failures — if one parallel tool fails, report generates with available sections.
- **FR-031**: compact_result() MUST strip HTML from tool results before adding to GPT context.
- **FR-032**: System MUST support configurable GPT model via OPENAI_MODEL environment variable.

**Streamlit UI**:
- **FR-033**: Streamlit MUST render chat interface with st.chat_input() and st.chat_message().
- **FR-034**: Streamlit MUST display each tool's HTML card inline via st.html() during st.status progress.
- **FR-035**: Streamlit MUST show sidebar with user profile, assumptions, calculation results, API usage, model config, "Start Over" button.
- **FR-036**: Streamlit MUST render final report via components.html() with scrolling and download button.
- **FR-037**: Streamlit MUST manage session state (messages, profile, assumptions, results, html_cards, token_data, pipeline_phase).

**Error Handling**:
- **FR-038**: ResilientToolExecutor MUST retry on ConnectionError/BrokenPipeError (max 2 retries with subprocess restart).
- **FR-039**: System MUST apply per-tool configurable timeouts (validate: 5s, tax: 5s, projection: 15s, optimizer: 30s, breakeven: 5s, report: 10s).
- **FR-040**: Anti-hallucination guardrail MUST flag GPT-generated dollar amounts, percentages, and breakeven years not found in tool results.

**Configuration**:
- **FR-041**: System MUST load OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, MAX_SESSION_COST, MCP_SERVER_CMD, MCP_SERVER_ARGS from .env file.

### Key Entities

- **UserProfile**: Core user financial data (17 fields: age, income, IRA balances, filing status, state, conversion spec, rates, horizons, tax-adjacent inputs).
- **ModelAssumptions**: Default rates and horizons (annual_return, inflation_rate, model_years, rmd_start_age, ss_start_age).
- **TaxEstimate**: Federal + state + IRMAA + SS + RMD tax breakdown for a single conversion (11 fields).
- **ProjectionData**: Year-by-year convert vs no-convert projections array + summary (final_roth_value, final_trad_value, net_benefit, crossover_year).
- **OptimizationResult**: Optimal multi-year schedule + tax savings + convergence info.
- **BreakevenResult**: Years to breakeven, age at breakeven, assessment.
- **CalculationResults**: Container for all tool results + tools_completed list.
- **TokenTracker**: GPT API usage tracking (prompt_tokens, completion_tokens, estimated_cost).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 6 MCP tools discoverable and callable via stdio transport, returning valid dual-return JSON.
- **SC-002**: Tax calculations match expected values for test scenarios across all 4 filing statuses and all 50 states + DC.
- **SC-003**: Full analysis pipeline (6 tools) completes in < 15 seconds with 3-way parallel stage 2.
- **SC-004**: GPT API cost per conversation < $0.01 using gpt-4o-mini.
- **SC-005**: Token usage per conversation < 8,000 tokens.
- **SC-006**: User can go from first message to complete HTML report in ≤ 10 turns (quick mode).
- **SC-007**: Tool misroute rate < 5% (GPT selects correct tool for 14 prompt regression cases).
- **SC-008**: Unit test coverage for tax engine, validators, dual-return, HTML templates ≥ 80%.
- **SC-009**: Integration tests verify MCP roundtrip for all 6 tools.
- **SC-010**: Anti-hallucination guardrail catches 100% of fabricated numbers in test scenarios.
- **SC-011**: Partial pipeline failure (1 of 3 parallel tools) still produces report with available sections.
- **SC-012**: System runs on Python 3.10+ on Windows/Linux/macOS.
