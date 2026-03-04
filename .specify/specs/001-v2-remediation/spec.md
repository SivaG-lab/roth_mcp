# Feature Specification: Roth MCP v2.0 Remediation Pass

**Feature Branch**: `001-v2-remediation`
**Created**: 2026-03-04
**Status**: Draft
**Input**: Remediation pass fixing 52 issues from 6 parallel Opus review agents across security, correctness, robustness, code quality, and polish categories.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Security & Crash Prevention (Priority: P1)

The system must not crash on malformed inputs, must not leak resources, and must not expose users to XSS attacks. When the MCP server subprocess dies, the system must recover gracefully rather than becoming permanently broken. All user-provided values displayed in HTML must be escaped.

**Why this priority**: Security vulnerabilities and crash bugs are the highest priority — they affect every user and represent the most severe risk to the application.

**Independent Test**: Run the full test suite with edge-case inputs (malformed JSON, zero values, empty arrays). Verify no XSS in rendered HTML by passing HTML-injection test strings through validators. Verify session cleanup by simulating MCP subprocess death.

**Acceptance Scenarios**:

1. **Given** the MCP server returns a Python traceback instead of JSON, **When** the agent loop processes the response, **Then** the system logs the error and continues gracefully without crashing.
2. **Given** a user provides a state value containing `<script>alert(1)</script>`, **When** the validator error message is rendered in HTML, **Then** the HTML-special characters are escaped and no script executes.
3. **Given** the MCP server subprocess crashes mid-session, **When** the user sends their next message, **Then** the system detects the broken connection and creates a new session automatically.
4. **Given** the Streamlit app is stopped and restarted, **When** checking for orphan processes, **Then** no leaked MCP server subprocesses remain.
5. **Given** the agent loop function is called, **When** the OpenAI API call is made, **Then** it uses async I/O and does not block the event loop.

---

### User Story 2 - Financial Calculation Correctness (Priority: P1)

The tax calculations must produce accurate results for multi-year conversion schedules. Each year's conversion tax must be computed independently using progressive brackets, not linearly scaled. Dead parameters that create a false API surface must be removed. Edge cases (zero conversion, empty schedules, negative balances) must be handled correctly.

**Why this priority**: Financial calculation errors directly mislead users making important retirement decisions. Incorrect tax estimates can cause real financial harm.

**Independent Test**: Run projection and optimization tools with known multi-year schedules and verify per-year tax against manual bracket calculations. Test edge cases: zero conversion amount, empty schedule, conversion exceeding balance.

**Acceptance Scenarios**:

1. **Given** a multi-year conversion schedule of [$50k, $100k, $30k], **When** projections are generated, **Then** each year's tax is computed independently via `compute_tax_components()`, not scaled from year 1.
2. **Given** `conversion_amount=0` passed to breakeven analysis, **When** the tool executes, **Then** it returns a "no conversion" result, not "worth_it".
3. **Given** the `irmaa` parameter is no longer in the `estimate_tax_components` tool signature, **When** the tool is called, **Then** IRMAA is computed internally from MAGI without misleading unused parameters.
4. **Given** a conversion amount exceeding the traditional IRA balance in a projection year, **When** that year is computed, **Then** the conversion is capped at the available balance.
5. **Given** an empty conversion schedule `[]`, **When** validation runs, **Then** it is treated as "no conversion specified" rather than silently accepting it.

---

### User Story 3 - Robustness & Cost Control (Priority: P2)

The system must enforce the configured session cost limit, protect against unbounded conversation history growth, handle API timeouts gracefully, and display safe error messages to users. The anti-hallucination guardrail must be improved to reduce false positives and catch more fabricated numbers.

**Why this priority**: Robustness issues cause degraded user experience and potential runaway API costs, but do not directly cause security vulnerabilities or financial miscalculations.

**Independent Test**: Set `MAX_SESSION_COST=0.01` and verify the agent loop stops after exceeding the limit. Test anti-hallucination with known good/bad GPT responses. Verify timeout retries work.

**Acceptance Scenarios**:

1. **Given** `MAX_SESSION_COST=0.50` and token usage has accumulated $0.51, **When** the agent loop attempts the next API call, **Then** it returns a "cost limit reached" message instead of calling the API.
2. **Given** GPT produces a response containing "$50,000" and the tool results contain the value `50000`, **When** anti-hallucination check runs, **Then** the number is recognized as legitimate and not flagged.
3. **Given** the MCP tool call times out, **When** the ResilientToolExecutor handles the error, **Then** it retries the call (up to max_retries) instead of immediately failing.
4. **Given** an unexpected exception occurs in the agent loop, **When** the error is displayed to the user, **Then** a generic user-friendly message is shown and the raw exception details are logged server-side only.
5. **Given** conversation history exceeds 50 messages, **When** the next API call is prepared, **Then** older messages are trimmed to keep the context within bounds.

---

### User Story 4 - Code Quality & Maintainability (Priority: P3)

Dead code, unused dependencies, inconsistent patterns, and missing test coverage must be cleaned up. The CI pipeline must reference the correct project. Logging must be properly configured. Schema translation must include required parameter signals.

**Why this priority**: Code quality issues do not affect end users directly but increase maintenance burden and risk of introducing future bugs.

**Independent Test**: Run linting checks, verify all imports are used, verify logging output appears when configured, run the CI pipeline and verify it passes.

**Acceptance Scenarios**:

1. **Given** the requirements.txt file, **When** checking for unused dependencies, **Then** `structlog` is not listed (standard `logging` is used instead).
2. **Given** `LOG_LEVEL=INFO` is set, **When** an MCP tool executes, **Then** the tool name and execution time appear in log output.
3. **Given** the CI pipeline runs, **When** checking the workflow file, **Then** it references the actual project structure, not a different project.
4. **Given** the OpenAI function schemas generated by schema_converter, **When** examining the output, **Then** each tool has a `required` array indicating mandatory parameters.
5. **Given** the models.py file, **When** examining REQUIRED_FIELDS on UserProfile, **Then** it is a `ClassVar` not a mutable instance field.

---

### User Story 5 - Polish & Consistency (Priority: P3)

Minor code quality improvements: shared test fixtures, consistent type annotations, proper stdout flushing on Windows, version pinning, dead code removal, and formatting helper improvements.

**Why this priority**: Polish items have minimal impact individually but collectively improve codebase quality.

**Independent Test**: Run the full test suite and verify all 305+ tests pass. Check that conftest.py reduces test code duplication.

**Acceptance Scenarios**:

1. **Given** a `tests/conftest.py` file exists, **When** test files import shared fixtures, **Then** duplicated helper functions (like profile dicts) are consolidated.
2. **Given** the `PYTHONUNBUFFERED` workaround in mcp_server.py, **When** the server starts on Windows, **Then** stdout uses `sys.stdout.reconfigure(line_buffering=True)` for reliable unbuffered output.
3. **Given** version ranges in requirements.txt, **When** reviewing dependency constraints, **Then** major version ranges are tightened (e.g., `fastmcp>=2.14,<3.0` not `<4.0`).

---

### Edge Cases

- What happens when the OpenAI API returns an empty `choices` list? System returns a user-friendly error message.
- What happens when `MCP_SERVER_ARGS` contains spaces or shell metacharacters? `shlex.split()` is used for proper argument parsing.
- What happens when `OPENAI_TIMEOUT=abc` is set in .env? Config parsing falls back to default values with a warning.
- What happens when `trad_balance` goes negative during a projection year? Conversion is capped at available balance before deduction.
- What happens when three parallel MCP tool calls are sent over a single stdio pipe? An asyncio.Lock serializes concurrent calls to prevent message interleaving.

## Requirements *(mandatory)*

### Functional Requirements

**Security & Crash Prevention (P1)**:
- **FR-001**: System MUST escape all user-derived values with `html.escape()` before HTML template interpolation
- **FR-002**: System MUST properly close MCP session context managers (`__aexit__`) when sessions end
- **FR-003**: System MUST use `AsyncOpenAI` client for non-blocking API calls in async functions
- **FR-004**: System MUST handle malformed JSON in `extract_html()`/`extract_data()` by returning safe defaults
- **FR-005**: System MUST implement session reconnection in `ResilientToolExecutor` via a session factory pattern
- **FR-006**: System MUST not cache failed MCP session initialization results in `@st.cache_resource`
- **FR-007**: System MUST properly close event loops and provide cache invalidation for cached resources

**Financial Correctness (P1)**:
- **FR-008**: System MUST compute tax independently for each year's conversion amount in projections, not scale proportionally
- **FR-009**: System MUST remove the unused `irmaa` parameter from `estimate_tax_components` tool signature
- **FR-010**: System MUST remove dead parameters (`taxable_dollars_available`, `taxable_account_annual_return`, `other_ordinary_income_by_year`, `spending_need_after_tax_by_year`) from tool signatures and validators
- **FR-011**: System MUST return a "no conversion" result when `conversion_amount <= 0` in breakeven analysis
- **FR-012**: System MUST reject empty `conversion_schedule=[]` as invalid input
- **FR-013**: System MUST cap conversion at available traditional IRA balance in projection years
- **FR-014**: System MUST exclude the `start` timer variable from `locals()` passed to validators

**Robustness (P2)**:
- **FR-015**: System MUST enforce `MAX_SESSION_COST` by checking `TokenTracker.estimated_cost` before each API call
- **FR-016**: System MUST improve anti-hallucination by comparing numeric values instead of string substrings
- **FR-017**: System MUST configure logging with `logging.basicConfig()` so log messages are not silently dropped
- **FR-018**: System MUST retry `TimeoutError`/`asyncio.TimeoutError` in `ResilientToolExecutor`
- **FR-019**: System MUST cache the OpenAI client at module level, not recreate per call
- **FR-020**: System MUST trim conversation history when it exceeds a configurable message limit
- **FR-021**: System MUST display generic error messages to users and log details server-side
- **FR-022**: System MUST guard against empty `response.choices` from the OpenAI API
- **FR-023**: System MUST add `asyncio.Lock` around MCP `call_tool` to prevent stdio message interleaving
- **FR-024**: System MUST use `shlex.split()` for `MCP_SERVER_ARGS` parsing
- **FR-025**: System MUST add array size limits in validators (max 50 years for schedules)
- **FR-026**: System MUST handle non-numeric env var values in config with fallback defaults

**Code Quality (P3)**:
- **FR-027**: System MUST remove `structlog` from requirements.txt
- **FR-028**: System MUST change `REQUIRED_FIELDS` to `ClassVar[list[str]]` on `UserProfile`
- **FR-029**: System MUST remove unused `FilingStatus`/`Assessment` enums OR wire them into the data flow
- **FR-030**: System MUST fix or remove the CI pipeline to reference the correct project structure
- **FR-031**: System MUST inject `required` arrays into OpenAI function schemas in schema_converter
- **FR-032**: System MUST call `validate_config()` at startup or remove the dead import
- **FR-033**: System MUST update "Start Over" button to clear only app-specific keys and invalidate MCP cache
- **FR-034**: System MUST fix double user message append (remove from either streamlit_app.py or agent_loop.py)
- **FR-035**: System MUST update system prompt to document pipeline auto-trigger behavior
- **FR-036**: System MUST replace `validate_config()` sys.exit(1) with a raised exception

**Polish (P3)**:
- **FR-037**: System MUST create `tests/conftest.py` with shared fixtures
- **FR-038**: System MUST use `sys.stdout.reconfigure(line_buffering=True)` instead of late `PYTHONUNBUFFERED`
- **FR-039**: System MUST tighten version ranges in requirements.txt to single major versions
- **FR-040**: System MUST remove dead `pass` statement in `compute_bracket_boundaries`
- **FR-041**: System MUST move `_safe_parse` to module level or `dual_return.py`

### Key Entities

- **MCP Session**: Represents the connection to the MCP server subprocess, including transport and client session context managers
- **ResilientToolExecutor**: Wraps MCP tool calls with retry logic and session reconnection capability
- **TokenTracker**: Monitors API usage and cost, used for enforcing session cost limits
- **Dual-Return Envelope**: JSON format `{"display": "<html>", "data": {...}}` used by all 6 tools

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 305+ existing tests continue to pass after all changes
- **SC-002**: Zero XSS vulnerabilities — all user-derived HTML values pass through `html.escape()`
- **SC-003**: No MCP server subprocess leaks — `__aexit__` called on all context managers
- **SC-004**: Multi-year projection tax calculations match independent per-year bracket computation (within $1 tolerance)
- **SC-005**: Session cost enforcement activates when `TokenTracker.estimated_cost >= MAX_SESSION_COST`
- **SC-006**: Anti-hallucination check produces zero false positives on tool-verified numbers
- **SC-007**: System recovers from MCP subprocess crash within one user interaction
- **SC-008**: New edge-case tests added for: zero conversion, empty schedule, malformed JSON, age > 120, conversation cost limit
- **SC-009**: Logging output visible when `LOG_LEVEL=INFO` is set
- **SC-010**: CI pipeline passes on the actual project structure

## Assumptions

- The existing dual-return pattern and 6-tool architecture remain unchanged
- Dead parameters are removed rather than implemented (implementing taxable account modeling is out of scope)
- The `FilingStatus`/`Assessment` enums will be removed rather than wired in (to reduce scope)
- State tax remains flat-rate (progressive state brackets are out of scope for this remediation)
- IRMAA Part D surcharges are out of scope (documented as limitation)
- The optimizer's static income limitation is documented but not fixed (income modeling is a feature, not a bug fix)
