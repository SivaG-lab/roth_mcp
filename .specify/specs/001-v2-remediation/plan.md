# Implementation Plan: Roth MCP v2.0 Remediation Pass

**Branch**: `001-v2-remediation` | **Date**: 2026-03-04
**Input**: review-findings.md (52 deduplicated issues from 6 Opus review agents)

## Summary

Fix 52 issues across security, correctness, robustness, code quality, and polish. This is a remediation pass on the existing codebase — no new features, only fixes and improvements to existing code. All 305+ existing tests must continue passing.

## Technical Context

**Language/Version**: Python 3.10+
**Existing Codebase**: ~20 source files, 305 tests passing, 6 MCP tools
**Dependencies**: Same as v2.0 (minus structlog removal)
**Constraint**: All changes must be backwards-compatible with existing tool behavior

## Implementation Strategy

### Phase A — Security & Crashes (CR-01 through CR-05, CR-08, HI-01, HI-14, HI-15)
**Files**: `mcp_client.py`, `streamlit_app.py`, `agent_loop.py`, `dual_return.py`, `html_templates/templates.py`, `pipeline.py`, `mcp_server.py`

1. Add `html.escape()` to all user-derived values in `html_templates/templates.py`
2. Refactor `mcp_client.py` to store context managers, add `close()`, implement session factory
3. Switch `agent_loop.py` to `AsyncOpenAI` client
4. Add try/except to `extract_html()`/`extract_data()` in `dual_return.py`
5. Fix event loop management in `streamlit_app.py`
6. Add `asyncio.Lock` in `ResilientToolExecutor` for stdio serialization
7. Fix double message append (remove from `streamlit_app.py`)
8. Guard against zero conversion in breakeven

### Phase B — Financial Correctness (CR-06, CR-07, CR-09, ME-20 through ME-23)
**Files**: `mcp_server.py`, `validators.py`

1. Remove `irmaa` from `estimate_tax_components` signature
2. Replace proportional tax scaling with per-year `compute_tax_components()` calls
3. Remove dead parameters from tool signatures and validators
4. Fix `locals()` leak of `start` variable
5. Cap conversion at available balance in projections
6. Reject empty `conversion_schedule=[]`

### Phase C — Robustness (HI-02, HI-03, HI-09, HI-13, HI-16, ME-01, ME-05, ME-06, ME-13, ME-18, ME-19)
**Files**: `agent_loop.py`, `config.py`, `mcp_client.py`, `mcp_server.py`, `validators.py`, `prompts/system.md`, `streamlit_app.py`

1. Enforce `MAX_SESSION_COST` in agent loop
2. Rewrite anti-hallucination to use numeric value comparison
3. Add `logging.basicConfig()` configuration
4. Add `TimeoutError` to retryable exceptions
5. Cache OpenAI client at module level
6. Add message trimming for conversation history
7. Update system prompt with pipeline auto-trigger docs
8. Add array size limits in validators
9. Safe error display in Streamlit
10. Safe config parsing with fallbacks
11. Guard against empty `response.choices`

### Phase D — Code Quality (HI-05 through HI-08, HI-10 through HI-12, ME-07 through ME-17, ME-24, ME-25)
**Files**: `models.py`, `requirements.txt`, `schema_converter.py`, `.github/workflows/ci.yml`, multiple test files

1. Change `REQUIRED_FIELDS` to `ClassVar`
2. Remove unused `FilingStatus`/`Assessment` enums
3. Remove `structlog` from requirements.txt
4. Fix CI pipeline
5. Inject `required` arrays in schema converter
6. Call or remove `validate_config()`
7. Fix "Start Over" button
8. Replace `sys.exit(1)` with exception
9. Remove `@pytest.mark.asyncio` from sync tests
10. Move `nest_asyncio.apply()` inside `main()`

### Phase E — Polish (all LOW issues)
**Files**: Various

1. Create `tests/conftest.py` with shared fixtures
2. Fix `PYTHONUNBUFFERED` to use `sys.stdout.reconfigure()`
3. Tighten version ranges in requirements.txt
4. Remove dead `pass` in `compute_bracket_boundaries`
5. Move `_safe_parse` to module level
6. Add `from __future__ import annotations` to tax/ files
7. Use `dataclasses.fields()` instead of `__dataclass_fields__`

## Risk Assessment

- **Breaking existing tests**: MEDIUM — must run tests after each phase
- **Async refactoring**: HIGH — switching to AsyncOpenAI requires careful testing
- **Session lifecycle**: MEDIUM — context manager changes affect Streamlit integration
