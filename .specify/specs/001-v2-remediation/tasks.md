# Tasks: Roth MCP v2.0 Remediation Pass

**Input**: review-findings.md (52 issues), plan.md, spec.md
**Constraint**: All 305 existing tests must pass after each phase

## Phase A: Security & Crashes (P1)

- [ ] T001 [CR-03] Add `html.escape()` to all user-derived values in `html_templates/templates.py` — escape keys, values, error messages, report fields. Import `html` module.
- [ ] T002 [CR-05] Add try/except to `extract_html()` and `extract_data()` in `dual_return.py` — return `""` and `{}` on `JSONDecodeError`/`TypeError`. Add logging warning.
- [ ] T003 [CR-01,CR-02,CR-08] Refactor `mcp_client.py` — store context manager references in `MCPConnection` class, add `close()` method, implement session factory pattern for `ResilientToolExecutor`, add `asyncio.Lock` for stdio serialization [HI-15].
- [ ] T004 [CR-04,HI-16] Switch `agent_loop.py` to `AsyncOpenAI` — replace `from openai import OpenAI` with `from openai import AsyncOpenAI`, change `client.chat.completions.create` to `await client.chat.completions.create`, cache client at module level.
- [ ] T005 [CR-02,HI-12] Fix `streamlit_app.py` event loop and session management — use `asyncio.get_event_loop()` with `nest_asyncio`, don't cache failures, move `nest_asyncio.apply()` inside `main()`, fix "Start Over" to clear only app-specific keys + invalidate MCP cache [ME-08].
- [ ] T006 [HI-01] Fix double user message append — remove `st.session_state.messages.append(...)` from `streamlit_app.py:166`.
- [ ] T007 [HI-14] Add zero/negative conversion guard to `breakeven_analysis` in `mcp_server.py` — return `{"breakeven_years": 0, "assessment": "no_conversion"}` when `conversion_amount <= 0`.
- [ ] T008 Run full test suite — verify all 305 tests pass. Fix any failures from T001-T007.

## Phase B: Financial Correctness (P1)

- [ ] T009 [CR-06] Remove `irmaa` parameter from `estimate_tax_components` tool signature in `mcp_server.py`.
- [ ] T010 [CR-07] Replace proportional tax scaling in `analyze_roth_projections` — call `compute_tax_components()` per year with that year's conversion amount, filing_status, state, and annual_income. Remove the `total_tax_per_conversion` scaling pattern.
- [ ] T011 [CR-09] Remove dead parameters from tool signatures and validators — remove `taxable_dollars_available`, `taxable_account_annual_return` from `validate_projection_inputs` and `analyze_roth_projections`. Remove `other_ordinary_income_by_year`, `spending_need_after_tax_by_year` from both. Update validators.py to not process these fields.
- [ ] T012 [ME-20] Fix `locals()` leak in `validate_projection_inputs` — exclude `start` from the kwargs dict passed to `validate_inputs`.
- [ ] T013 [ME-22] Reject empty `conversion_schedule=[]` in `validators.py` — add check `if not conversion_schedule:` to treat empty list as missing.
- [ ] T014 [ME-23] Cap conversion at available balance in `analyze_roth_projections` — add `conversion = min(conversion, max(trad_balance - rmd_amount, 0))` before deducting.
- [ ] T015 Run full test suite — verify all tests pass. Update test_tools.py and test_integration.py for removed parameters.

## Phase C: Robustness (P2)

- [ ] T016 [HI-02] Enforce MAX_SESSION_COST in `agent_loop.py` — import MAX_SESSION_COST from config, check `token_tracker.estimated_cost >= MAX_SESSION_COST` before each API call, return cost-limit message if exceeded.
- [ ] T017 [HI-03] Rewrite `check_hallucinated_numbers` in `agent_loop.py` — extract all numeric values from tool results into a set, normalize GPT response numbers for comparison against the set (not substring matching).
- [ ] T018 [HI-09] Add logging configuration — add `logging.basicConfig(level=os.getenv("LOG_LEVEL", "WARNING"), format="%(asctime)s %(name)s %(levelname)s %(message)s")` to `config.py`.
- [ ] T019 [HI-13] Add `TimeoutError`, `asyncio.TimeoutError` to retryable exceptions in `ResilientToolExecutor`.
- [ ] T020 [ME-01] Add message trimming to `agent_loop.py` — keep system prompt + last N messages (configurable, default 40).
- [ ] T021 [ME-05] Update `prompts/system.md` — add section explaining pipeline auto-trigger on `validate_projection_inputs` status=complete.
- [ ] T022 [ME-06] Add array size limits in `validators.py` — max 50 elements for `conversion_schedule`.
- [ ] T023 [ME-13,ME-19] Safe error handling in `streamlit_app.py` — show generic message to user, log exception. Guard against empty `response.choices` in `agent_loop.py`.
- [ ] T024 [ME-18] Safe config parsing in `config.py` — wrap `int()`/`float()` in try/except with fallback defaults.
- [ ] T025 [ME-14] Use `shlex.split()` for `MCP_SERVER_ARGS` in `mcp_client.py`.
- [ ] T026 Run full test suite — verify all tests pass.

## Phase D: Code Quality (P3)

- [ ] T027 [HI-06,HI-07] Fix `models.py` — change `REQUIRED_FIELDS` to `ClassVar[list[str]]`, remove unused `FilingStatus`/`Assessment` enums, use `dataclasses.fields()` instead of `__dataclass_fields__` [LO-14].
- [ ] T028 [HI-08] Remove `structlog` from `requirements.txt`. Tighten version ranges [LO-11].
- [ ] T029 [HI-10] Inject `required` arrays into OpenAI schemas in `schema_converter.py` — define required params per tool.
- [ ] T030 [HI-11,ME-15] Fix `config.py` — remove `validate_config()` (replace with exception pattern), remove dead import from `streamlit_app.py`.
- [ ] T031 [ME-07] Fix or remove `.github/workflows/ci.yml` — update to reference actual project structure.
- [ ] T032 [ME-09] Extract magic numbers to named constants in `mcp_server.py` and `agent_loop.py`.
- [ ] T033 [ME-11] Remove `@pytest.mark.asyncio` from synchronous test functions in `test_integration.py`.
- [ ] T034 [ME-12] Add logging to `_safe_parse` when JSON parsing fails in `mcp_server.py`.
- [ ] T035 [ME-25] Fix schema_converter to use MCP descriptions as fallback instead of full override.
- [ ] T036 [ME-02] Pass only data (not full dual-return) to `generate_conversion_report` in `pipeline.py`.
- [ ] T037 [HI-05] Remove unused dataclass models from `models.py` or add TODO for future wiring. Keep only `UserProfile`, `TokenTracker`, `ModelAssumptions`.
- [ ] T038 Run full test suite — verify all tests pass.

## Phase E: Polish (P3)

- [ ] T039 [LO-06] Create `tests/conftest.py` with shared fixtures — `complete_profile()`, `_parse()` helper, common test data.
- [ ] T040 [LO-05] Fix PYTHONUNBUFFERED in `mcp_server.py` — use `sys.stdout.reconfigure(line_buffering=True)`.
- [ ] T041 [LO-07] Remove dead `pass` statement in `tax/calculator.py` `compute_bracket_boundaries`.
- [ ] T042 [LO-16] Move `_safe_parse` from nested function in `mcp_server.py` to module-level or `dual_return.py`.
- [ ] T043 [LO-08] Add `from __future__ import annotations` to tax/ files that lack it.
- [ ] T044 [LO-15] Replace `all([...])` with `all((...))` or explicit `and` in `mcp_server.py`.
- [ ] T045 [ME-35,HI-34] Fix `streamlit_app.py` double HTML card rendering [LO-01].
- [ ] T046 New edge-case tests — test zero conversion breakeven, empty schedule validation, malformed JSON in extract functions, conversion exceeding balance, `compute_rmd` age > 120, conversation cost limit.
- [ ] T047 Run full test suite — verify all tests pass. Final count should be > 305.

## Dependencies

- Phase A must complete first (security/crash fixes)
- Phase B depends on Phase A (parameter removal may affect tests)
- Phase C depends on Phase A (async changes in agent_loop)
- Phase D depends on Phase B (models cleanup after parameter removal)
- Phase E can partially overlap with Phase D
