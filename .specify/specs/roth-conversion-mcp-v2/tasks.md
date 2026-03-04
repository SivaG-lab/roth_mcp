# Tasks: Roth Conversion Calculator MCP Server v2.0

**Input**: Design documents from `.specify/specs/roth-conversion-mcp-v2/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mcp-tools.md, contracts/openai-schema.md

**Tests**: Test tasks are included per spec (US10 explicitly requires tests; US1-9 acceptance scenarios define test criteria). Unit tests for tax engine, validators, dual-return, HTML templates (≥80% coverage target per SC-008).

**Organization**: Tasks grouped by user story (10 stories from spec.md) enabling independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — directories, dependencies, configuration files

- [X] T001 Create project directory structure: `tax/`, `html/`, `prompts/`, `tests/`, `.streamlit/` per plan.md
- [X] T002 Create `requirements.txt` with all dependencies (FastMCP >=2.14,<4.0, Streamlit >=1.33,<2.0, openai >=1.0,<3.0, mcp >=1.0,<3.0, nest-asyncio >=1.6,<2.0, python-dotenv >=1.0,<2.0, structlog >=24.0,<26.0, pytest >=8.0, pytest-asyncio >=0.23)
- [X] T003 [P] Create `.env.example` with OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, MAX_SESSION_COST, MCP_SERVER_CMD, MCP_SERVER_ARGS
- [X] T004 [P] Create `.streamlit/config.toml` with theme configuration
- [X] T005 [P] Create `tax/__init__.py`, `html/__init__.py` package init files with public API exports

**Checkpoint**: Project skeleton ready, dependencies installable via `pip install -r requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core modules that ALL user stories depend on — config, models, dual-return envelope

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `config.py` — load .env, validate OPENAI_API_KEY exists, export all config constants with types
- [X] T007 Implement `models.py` — all 8 dataclasses (UserProfile, ModelAssumptions, TaxEstimate, ProjectionData, OptimizationResult, BreakevenResult, CalculationResults, TokenTracker) + enums (FilingStatus, PipelinePhase, Assessment) per data-model.md
- [X] T008 Implement `dual_return.py` — dual_return(), extract_html(), extract_data(), compact_result() per contracts/mcp-tools.md envelope pattern

**Checkpoint**: Foundation ready — models importable, dual-return works, config loads from .env

---

## Phase 3: User Story 1 — Tax Engine & Shared Computation Layer (Priority: P1) 🎯 MVP

**Goal**: Build the pure-logic tax computation layer: federal+state brackets, IRMAA, RMD, Social Security, and the main `compute_tax_components()` function.

**Independent Test**: Run `pytest tests/test_tax_calculator.py tests/test_irmaa.py tests/test_rmd.py tests/test_ss_taxation.py -v` — pass financial inputs, verify tax outputs against known scenarios. No server or UI needed.

### Tests for User Story 1

> **Write tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Create `tests/test_tax_calculator.py` — test federal+state tax for all 4 filing statuses, standard deduction application, bracket boundary crossing, known scenarios from spec acceptance criteria (e.g., $150k MFJ + $50k conversion in CA)
- [X] T010 [P] [US1] Create `tests/test_irmaa.py` — test IRMAA surcharge for all 6 tiers × single + MFJ, boundary values ($103k, $129k, $206k, $258k, etc.), zero case (below threshold)
- [X] T011 [P] [US1] Create `tests/test_rmd.py` — test RMD for ages 73-90+ against Uniform Lifetime Table, zero case (age < 73), zero balance case
- [X] T012 [P] [US1] Create `tests/test_ss_taxation.py` — test SS taxation for all filing statuses, provisional income thresholds ($25k/$32k/$34k/$44k), married_separate special rule (85% taxable)

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `tax/brackets.py` — FEDERAL_BRACKETS dict (4 filing statuses × 7 brackets), STANDARD_DEDUCTIONS dict, additional deduction for age 65+, `compute_federal_tax(taxable_income, filing_status)` function
- [X] T014 [P] [US1] Implement `tax/state_rates.py` — STATE_TAX_RATES dict (50 states + DC with flat effective rates), `compute_state_tax(taxable_conversion, state)` function
- [X] T015 [P] [US1] Implement `tax/irmaa.py` — IRMAA_THRESHOLDS dict (6 tiers × single/MFJ), `compute_irmaa_surcharge(magi, filing_status)` returning annual surcharge
- [X] T016 [P] [US1] Implement `tax/rmd.py` — RMD_TABLE dict (ages 73-120), `compute_rmd(age, ira_balance)` returning distribution amount
- [X] T017 [P] [US1] Implement `tax/ss.py` — `compute_ss_taxation(ss_benefit, other_income, filing_status)` with provisional income formula for all 4 statuses
- [X] T018 [US1] Implement `tax/calculator.py` — `compute_tax_components()` main entry point (imports brackets, state_rates, irmaa, rmd, ss; applies standard deduction before brackets; returns full TaxEstimate dict), `compute_bracket_boundaries(annual_income, filing_status)` for optimizer
- [X] T019 [US1] Update `tax/__init__.py` — export compute_tax_components, compute_bracket_boundaries, compute_rmd, compute_irmaa_surcharge, compute_ss_taxation
- [X] T020 [US1] Run all US1 tests — verify all pass, fix any failures

**Checkpoint**: Tax engine fully functional. `compute_tax_components(150000, 50000, "married_joint", "CA")` returns correct federal+state+IRMAA+SS breakdown.

---

## Phase 4: User Story 2 — Input Validation & Dual-Return Pattern (Priority: P1)

**Goal**: Validate all 17+ inputs with entity rules, apply smart auto-fill defaults. Ensure dual-return envelope works for all tools.

**Independent Test**: Run `pytest tests/test_validators.py tests/test_dual_return.py -v` — test validators with valid/invalid inputs, test dual-return functions.

### Tests for User Story 2

- [X] T021 [P] [US2] Create `tests/test_validators.py` — test age range (18-100), retirement > current, income ≥ 0, filing_status enum, state code, conversion ≤ balance, annual_return range, model_years range, cross-field rules, auto-fill logic (SS=0 age<62, RMD=0 age<73, IRMAA=0 below threshold)
- [X] T022 [P] [US2] Create `tests/test_dual_return.py` — test dual_return() creates valid JSON, extract_html() returns HTML, extract_data() returns dict, compact_result() strips HTML, compact_result for report returns placeholder, compact_result for projections returns summary only

### Implementation for User Story 2

- [X] T023 [US2] Implement `validators.py` — validate_inputs() with per-field range checks, enum checks, cross-field validation (conversion ≤ balance, retirement > current), auto-fill defaults (SS, RMD, IRMAA based on age/income), auto-wrap conversion_amount → conversion_schedule, return structured result {status, inputs, assumptions, auto_filled, missing, errors}
- [X] T024 [US2] Run all US2 tests — verify all pass, fix any failures

**Checkpoint**: `validate_inputs(current_age=55, ...)` returns complete validated result with auto-fills. `dual_return(html, data)` produces correct JSON envelope.

---

## Phase 5: User Story 3 — FastMCP Server with 6 Tools (Priority: P1)

**Goal**: FastMCP server exposes 6 tools via stdio transport. Each tool wraps shared computation + returns dual-format.

**Independent Test**: Start server as subprocess, connect via MCP client, call each tool with test data, verify dual-return format.

### Tests for User Story 3

- [ ] T025 [P] [US3] Create `tests/test_tools.py` — test each of 6 tool functions directly (bypass MCP transport): validate_projection_inputs with complete/incomplete inputs, estimate_tax_components with known values, analyze_roth_projections produces year-by-year data, optimize_conversion_schedule returns schedule, breakeven_analysis returns assessment, generate_conversion_report assembles sections

### Implementation for User Story 3

- [ ] T026 [US3] Implement `mcp_server.py` — FastMCP("roth-conversion-calculator") server with stdio transport, tool 1: validate_projection_inputs (calls validators.py, returns dual-return), tool 2: estimate_tax_components (calls tax/calculator.py, returns dual-return)
- [ ] T027 [US3] Add tool 3 to `mcp_server.py` — analyze_roth_projections: year-by-year loop calling compute_tax_components() per year, track convert vs no-convert balances, apply RMDs at age 73+, return projections + summary via dual-return
- [ ] T028 [US3] Add tool 4 to `mcp_server.py` — optimize_conversion_schedule: greedy bracket-fill algorithm, iterate years from current_age to retirement_age, call compute_bracket_boundaries() + compute_tax_components() per candidate, max 100 iterations, return optimal_schedule via dual-return
- [ ] T029 [US3] Add tool 5 to `mcp_server.py` — breakeven_analysis: Roth path vs Traditional path comparison, compute breakeven year, assessment logic (worth_it/marginal/not_worth_it), return via dual-return
- [ ] T030 [US3] Add tool 6 to `mcp_server.py` — generate_conversion_report: parse JSON string inputs (validated_inputs, tax_analysis, projection_data, optimization_data, breakeven_data), assemble comprehensive HTML report, handle missing sections gracefully, return via dual-return
- [ ] T031 [US3] Run all US3 tests — verify all 6 tools return valid dual-return JSON, fix any failures

**Checkpoint**: `python mcp_server.py` starts, 6 tools discoverable via MCP protocol. Each tool returns `{"data": {...}, "display": "...html..."}`.

---

## Phase 6: User Story 4 — HTML Templates & Styling (Priority: P2)

**Goal**: Each tool produces a styled HTML card with tool-specific color coding.

**Independent Test**: Run `pytest tests/test_html_templates.py -v` — call each template function with mock data, verify HTML structure and color coding.

### Tests for User Story 4

- [ ] T032 [P] [US4] Create `tests/test_html_templates.py` — test format_validation_result (green #22c55e), format_tax_estimate (red #ef4444, table rows), format_projection_table (blue, 5-year summary + details), format_optimization_schedule (purple), format_breakeven (blue, assessment text), format_report (all sections present, styled)

### Implementation for User Story 4

- [ ] T033 [P] [US4] Implement `html/styles.py` — color constants (VALIDATION_GREEN=#22c55e, TAX_RED=#ef4444, PROJECTION_BLUE=#3b82f6, OPTIMIZATION_PURPLE, REPORT_FULL), font/spacing constants, shared CSS snippets
- [ ] T034 [US4] Implement `html/templates.py` — format_validation_result(), format_tax_estimate() with table, format_projection_table() with 5-year summary + collapsible `<details>` for full table, format_optimization_schedule(), format_breakeven() with assessment, format_report() comprehensive styled document with all sections
- [ ] T035 [US4] Update `html/__init__.py` — export all 6 formatter functions
- [ ] T036 [US4] Wire HTML templates into `mcp_server.py` tools — each tool calls its formatter before dual_return()
- [ ] T037 [US4] Run all US4 tests — verify HTML structure, colors, all sections present

**Checkpoint**: Each tool returns styled HTML cards. Validation=green, Tax=red, Projection/Breakeven=blue, Optimization=purple, Report=full style.

---

## Phase 7: User Story 5 — MCP Client & Schema Translation (Priority: P2)

**Goal**: Streamlit app manages MCP client session, translates schemas to OpenAI format, wraps tool calls with resilient execution.

**Independent Test**: Run `pytest tests/test_schema_converter.py -v` — verify schema translation produces valid OpenAI function definitions.

### Tests for User Story 5

- [ ] T038 [P] [US5] Create `tests/test_schema_converter.py` — test mcp_tool_to_openai_function() produces valid OpenAI format, test list[float]|None → anyOf schema, test all 6 tool descriptions present in TOOL_DESCRIPTIONS

### Implementation for User Story 5

- [ ] T039 [US5] Implement `schema_converter.py` — mcp_tool_to_openai_function(), TOOL_DESCRIPTIONS dict with enhanced descriptions for all 6 tools per contracts/openai-schema.md
- [ ] T040 [US5] Implement `mcp_client.py` — get_mcp_session() with @st.cache_resource, StdioServerParameters(command, args from config), ClientSession init with nest_asyncio, tool discovery via session.list_tools(), ResilientToolExecutor class (max_retries=2, per-tool timeouts, subprocess restart on ConnectionError/BrokenPipeError)
- [ ] T041 [US5] Run US5 tests — verify schema translation, fix any failures

**Checkpoint**: MCP client connects to server subprocess, discovers 6 tools, translates schemas to OpenAI format. ResilientToolExecutor handles crashes.

---

## Phase 8: User Story 6 — GPT Agent Loop & Deterministic Pipeline (Priority: P2)

**Goal**: agent_loop.py handles GPT conversation, pipeline.py runs deterministic computation. Pipeline triggers on input completion.

**Independent Test**: Mock MCP session + OpenAI responses, verify agent loop triggers pipeline, pipeline runs 6 tools in correct order with 3-way parallelism.

### Implementation for User Story 6

- [ ] T042 [US6] Implement `pipeline.py` — run_analysis_pipeline(mcp_session, validated_inputs): call estimate_tax_components (serial), then asyncio.gather(analyze_projections, optimize_schedule, breakeven) (3-way parallel), then generate_report (serial). Handle partial failures — if one parallel tool fails, report generates with available sections. Return dict with html_cards + compacted results.
- [ ] T043 [US6] Implement `agent_loop.py` — agent_loop(user_message, mcp_session): build system message, discover tools as OpenAI functions, GPT conversation loop (max 10 iterations), handle tool_calls, call MCP tools via ResilientToolExecutor, update session state, trigger pipeline on validate_projection_inputs status=complete, return (assistant_content, html_outputs)
- [ ] T044 [US6] Create `prompts/system.md` — full GPT system prompt per PRD Section 23: absolute rule (never compute financials), tool selection order, input collection instructions, auto-fill rules, conversion schedule parsing, boundaries, tone, disclaimer

**Checkpoint**: GPT agent collects inputs → validates → pipeline runs tax → (projection ∥ optimization ∥ breakeven) → report. Full flow works end-to-end.

---

## Phase 9: User Story 7 — Streamlit Chat UI (Priority: P2)

**Goal**: Streamlit chat interface with sidebar, HTML card rendering, session state management.

**Independent Test**: Run `streamlit run streamlit_app.py` — verify welcome message, sidebar sections, chat input, HTML rendering.

### Implementation for User Story 7

- [ ] T045 [US7] Implement `streamlit_app.py` — main app: initialize_session_state() (messages, profile, assumptions, results, html_cards, token_data, pipeline_phase), nest_asyncio.apply(), st.chat_input(), st.chat_message() loop, render HTML cards via st.html(), render final report via components.html() with scrolling, download button for report
- [ ] T046 [US7] Add sidebar to `streamlit_app.py` — user profile section (live-updating from session state), model assumptions, calculation results summary, API usage (tokens, cost), model config display, "Start Over" button (resets session state)
- [ ] T047 [US7] Wire agent_loop into `streamlit_app.py` — on user submit: call agent_loop(), display assistant response, render HTML cards inline during st.status progress, update sidebar

**Checkpoint**: Full Streamlit chat UI working. User types message → GPT responds → HTML cards render → sidebar updates → report displays with download.

---

## Phase 10: User Story 8 — System Prompt & Anti-Hallucination (Priority: P3)

**Goal**: System prompt instructs GPT on tool selection, anti-hallucination guardrail checks GPT responses.

**Independent Test**: Verify tool routing for known prompts. Test anti-hallucination regex against known good/bad responses.

### Implementation for User Story 8

- [ ] T048 [US8] Implement anti-hallucination guardrail in `agent_loop.py` — check_hallucinated_numbers(gpt_response, tool_results): regex for $amounts, percentages, breakeven years not in tool results. Append warning to response if suspicious numbers found.
- [ ] T049 [US8] Create `tests/prompt_eval_cases.json` — 14 prompt regression test cases from PRD: "I want to convert my IRA" → validate, "I'm 55, MFJ..." → validate with params, "What tax on $50k?" → validate first, "$50k/year for 5 years" → conversion_schedule, "What's the best amount?" → optimize, etc.

**Checkpoint**: GPT routes to correct tools for all 14 test cases. Anti-hallucination catches fabricated numbers.

---

## Phase 11: User Story 9 — Data Models & Configuration (Priority: P3)

**Goal**: Verify models.py dataclass properties work correctly, config.py loads all env vars.

**Independent Test**: Instantiate each dataclass, verify defaults, test to_tool_args(), missing_required, has_conversion_spec.

> Note: models.py and config.py were created in Phase 2 (Foundational). This phase adds property tests and ensures all dataclass behaviors work correctly.

### Implementation for User Story 9

- [ ] T050 [US9] Add UserProfile property tests to `tests/test_validators.py` or new `tests/test_models.py` — test missing_required returns correct fields, has_conversion_spec with amount/schedule/neither, to_tool_args() excludes None values
- [ ] T051 [US9] Verify `config.py` handles missing OPENAI_API_KEY gracefully (error message), verify all config values have correct types and defaults

**Checkpoint**: All dataclass properties work. Config loads with validation.

---

## Phase 12: User Story 10 — Integration & E2E Testing (Priority: P3)

**Goal**: Full test suite — unit (80%), integration (MCP roundtrip), prompt regression.

**Independent Test**: Run `pytest tests/ -v` — all tests pass.

### Implementation for User Story 10

- [ ] T052 [US10] Create `tests/test_integration.py` — MCP roundtrip tests: start mcp_server.py as subprocess, connect via MCP client, call all 6 tools with test data, verify dual-return JSON for each, verify pipeline runs tools in correct order
- [ ] T053 [US10] Create `tests/test_orchestrator.py` — pipeline tests: mock MCP session, verify run_analysis_pipeline() calls tools in order (tax → 3-way parallel → report), verify partial failure handling (one parallel tool fails, report still generates)
- [ ] T054 [US10] Run full test suite `pytest tests/ -v` — verify all tests pass, verify coverage ≥ 80% for tax engine, validators, dual-return, HTML templates

**Checkpoint**: All tests green. Coverage target met. MCP roundtrip verified.

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Final quality improvements across all stories

- [ ] T055 [P] Add structlog logging to `mcp_server.py` — log tool calls, execution time, errors
- [ ] T056 [P] Add structlog logging to `agent_loop.py` and `pipeline.py` — log GPT calls, token usage, pipeline stages
- [ ] T057 Create `README.md` — project description, setup instructions, architecture overview, usage examples
- [ ] T058 Run quickstart.md validation — follow quickstart steps on clean environment, verify everything works
- [ ] T059 Final end-to-end test — start Streamlit, enter "I'm 55, MFJ, $150k income, $500k IRA, CA, convert $50k/yr for 5 years", verify full pipeline runs, report generates

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 Tax Engine (Phase 3)**: Depends on Foundational — BLOCKS US3 (tools call tax functions)
- **US2 Validation (Phase 4)**: Depends on Foundational — BLOCKS US3 (tools call validators)
- **US3 MCP Server (Phase 5)**: Depends on US1 + US2 (tools need tax engine + validators)
- **US4 HTML Templates (Phase 6)**: Depends on Foundational only (templates are standalone functions) — integrates with US3
- **US5 MCP Client (Phase 7)**: Depends on US3 (needs server to connect to)
- **US6 Agent Loop (Phase 8)**: Depends on US3 + US5 (needs server + client)
- **US7 Streamlit UI (Phase 9)**: Depends on US6 (needs agent loop)
- **US8 System Prompt (Phase 10)**: Depends on US6 (adds to agent loop)
- **US9 Models Verification (Phase 11)**: Depends on Foundational only
- **US10 Integration Tests (Phase 12)**: Depends on US3 + US6 + US7
- **Polish (Phase 13)**: Depends on all prior phases

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                         │
              ┌──────────┼──────────┐
              v          v          v
         Phase 3     Phase 4    Phase 6    Phase 11
         (US1 Tax)   (US2 Val)  (US4 HTML) (US9 Models)
              │          │          │
              └────┬─────┘          │
                   v                │
              Phase 5 (US3 Server) ←┘
                   │
              ┌────┴────┐
              v         v
         Phase 7    Phase 10
         (US5 Client) (US8 Prompt)
              │         │
              └────┬────┘
                   v
         Phase 8 (US6 Agent Loop)
                   │
                   v
         Phase 9 (US7 Streamlit UI)
                   │
                   v
         Phase 12 (US10 Integration)
                   │
                   v
         Phase 13 (Polish)
```

### Within Each User Story

- Tests FIRST → ensure they FAIL
- Data/reference tables before computation functions
- Core logic before integration wiring
- Run tests after implementation → ensure they PASS

### Parallel Opportunities

**Phase 1**: T003, T004, T005 can run in parallel
**Phase 3 (US1)**: T009-T012 (tests) in parallel; T013-T017 (tax modules) in parallel
**Phase 4 (US2)**: T021, T022 (tests) in parallel
**Phase 5 (US3)**: T025 (tests) standalone
**Phase 6 (US4)**: T032 (tests), T033 (styles) in parallel
**Phase 7 (US5)**: T038 (tests) standalone
**Phase 13**: T055, T056, T057 in parallel

**Cross-story parallelism**: US1, US2, US4, US9 can all run in parallel after Foundational phase (they have no inter-dependencies)

---

## Parallel Example: Phase 3 (User Story 1)

```bash
# Launch all US1 tests in parallel:
Task: T009 "test_tax_calculator.py"
Task: T010 "test_irmaa.py"
Task: T011 "test_rmd.py"
Task: T012 "test_ss_taxation.py"

# Launch all US1 tax modules in parallel:
Task: T013 "tax/brackets.py"
Task: T014 "tax/state_rates.py"
Task: T015 "tax/irmaa.py"
Task: T016 "tax/rmd.py"
Task: T017 "tax/ss.py"

# Then sequential:
Task: T018 "tax/calculator.py" (depends on T013-T017)
Task: T019 "tax/__init__.py"
Task: T020 "Run tests"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (config, models, dual-return)
3. Complete Phase 3: US1 Tax Engine — fully testable standalone
4. Complete Phase 4: US2 Validators — fully testable standalone
5. Complete Phase 5: US3 MCP Server — **MVP milestone: 6 tools callable via MCP**
6. **STOP and VALIDATE**: All 6 tools return valid dual-return JSON via MCP protocol

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 Tax Engine → Test tax computations → **Tax MVP**
3. US2 Validators → Test validation → **Validation ready**
4. US3 MCP Server → Test 6 tools → **MCP Server MVP**
5. US4 HTML Templates → Rich styled output → **Visual upgrade**
6. US5 MCP Client → Client connection → **Client bridge**
7. US6 Agent Loop → GPT orchestration → **Agent MVP**
8. US7 Streamlit UI → Full chat interface → **Full Product**
9. US8-10 → Prompt tuning, model verification, integration tests → **Production quality**
10. Polish → Logging, docs → **Release ready**

### Estimated Task Counts

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|----------|
| Phase 1 | Setup | 5 | 3 |
| Phase 2 | Foundational | 3 | 0 |
| Phase 3 | US1 Tax Engine | 12 | 9 |
| Phase 4 | US2 Validation | 4 | 2 |
| Phase 5 | US3 MCP Server | 7 | 1 |
| Phase 6 | US4 HTML | 6 | 2 |
| Phase 7 | US5 Client | 4 | 1 |
| Phase 8 | US6 Agent Loop | 3 | 0 |
| Phase 9 | US7 Streamlit | 3 | 0 |
| Phase 10 | US8 Prompt | 2 | 0 |
| Phase 11 | US9 Models | 2 | 0 |
| Phase 12 | US10 Integration | 3 | 0 |
| Phase 13 | Polish | 5 | 3 |
| **Total** | | **59** | **21** |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable at its checkpoint
- Commit after each task: `git add -A && git commit -m "task [T0XX]: [description]"`
- Stop at any checkpoint to validate story independently
- Tax data (brackets, IRMAA thresholds, RMD table, state rates) sourced from PRD Section 12
- All tool signatures sourced from contracts/mcp-tools.md
