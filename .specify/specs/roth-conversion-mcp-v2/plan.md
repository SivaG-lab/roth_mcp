# Implementation Plan: Roth Conversion Calculator MCP Server v2.0

**Branch**: `roth-conversion-mcp-v2` | **Date**: 2026-03-03 | **Spec**: `.specify/specs/roth-conversion-mcp-v2/spec.md`
**Input**: Feature specification + PRD-roth-conversion-mcp-v2.md (2199 lines, architect-reviewed)

## Summary

Build a two-component Roth IRA conversion analysis system: (1) a FastMCP server exposing 6 financial analysis tools via stdio transport, and (2) a Streamlit chat agent that acts as MCP client with GPT-4o-mini orchestration. The system uses a Hybrid Orchestrator-Pipeline pattern — GPT handles conversation (input collection + summary), while a deterministic pipeline runs the 6 tools sequentially/in parallel without GPT round-trips. All tools return dual-format JSON (`{"data": {...}, "display": "...html..."}`). The tax engine covers federal + state + IRMAA + RMD + Social Security with 2024 IRS data.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastMCP >=2.14,<4.0, Streamlit >=1.33,<2.0, OpenAI SDK >=1.0,<3.0, mcp >=1.0,<3.0, nest-asyncio >=1.6,<2.0, python-dotenv >=1.0,<2.0, structlog >=24.0,<26.0
**Storage**: N/A (stateless, session-only via `st.session_state`)
**Testing**: pytest >=8.0, pytest-asyncio >=0.23
**Target Platform**: Windows 11 (primary), Linux/macOS (compatible)
**Project Type**: MCP server + Streamlit web application (local, single-user)
**Performance Goals**: Full 6-tool pipeline < 15 seconds, GPT cost < $0.01/conversation, < 8,000 tokens/conversation
**Constraints**: Local-only, no auth, no persistence, no cloud deployment
**Scale/Scope**: Single user, 6 MCP tools, ~20 source files, 1 Streamlit page

## Constitution Check

*No constitution.md found. Gate passes by default — no project-level constraints to check.*

**Post-design re-check**: N/A (no constitution)

## Project Structure

### Documentation (this feature)

```text
.specify/specs/roth-conversion-mcp-v2/
├── spec.md              # Feature specification (Clarified)
├── plan.md              # This file
├── research.md          # Phase 0 output — technology decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — setup guide
├── contracts/
│   ├── mcp-tools.md     # MCP tool input/output schemas
│   └── openai-schema.md # OpenAI function calling translation
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
roth_mcp/
├── mcp_server.py               # FastMCP server entry point (6 tools)
├── streamlit_app.py            # Streamlit chat UI entry point
├── agent_loop.py               # GPT conversation loop (Phase 1 + Phase 3)
├── pipeline.py                 # Deterministic computation pipeline (Phase 2)
├── mcp_client.py               # MCP session management + ResilientToolExecutor
├── schema_converter.py         # MCP → OpenAI schema translation
├── models.py                   # Dataclasses (UserProfile, TaxEstimate, etc.)
├── config.py                   # Environment config (.env loading + validation)
├── dual_return.py              # dual_return(), extract_html(), extract_data(), compact_result()
├── validators.py               # Input validation functions (17+ fields)
├── prompts/
│   └── system.md               # GPT system prompt
├── tax/
│   ├── __init__.py             # Exports all compute_* functions
│   ├── brackets.py             # 2024 federal brackets (4 filing statuses) + standard deductions
│   ├── state_rates.py          # Flat effective rates (50 states + DC)
│   ├── calculator.py           # compute_tax_components() — main shared computation
│   ├── irmaa.py                # IRMAA surcharge lookup (6 tiers × 2 filing groups)
│   ├── rmd.py                  # RMD with Uniform Lifetime Table (ages 73-120)
│   └── ss.py                   # Social Security taxation (provisional income formula)
├── html/
│   ├── __init__.py
│   ├── templates.py            # 6 HTML formatter functions (one per tool)
│   └── styles.py               # Inline CSS constants (colors, fonts)
├── tests/
│   ├── test_tax_calculator.py  # Federal+state tax accuracy
│   ├── test_irmaa.py           # IRMAA threshold tests
│   ├── test_rmd.py             # RMD calculation tests
│   ├── test_ss_taxation.py     # Social Security taxation tests
│   ├── test_validators.py      # Input validation edge cases
│   ├── test_dual_return.py     # Dual-return envelope tests
│   ├── test_html_templates.py  # HTML output structure tests
│   ├── test_tools.py           # MCP tool-level tests
│   ├── test_schema_converter.py # MCP→OpenAI schema translation
│   ├── test_integration.py     # MCP roundtrip + pipeline tests
│   └── prompt_eval_cases.json  # 14 prompt regression test cases
├── .env.example                # Environment template
├── .streamlit/
│   └── config.toml             # Streamlit configuration
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

**Structure Decision**: Flat single-project layout (not src/ subdirectory). All Python modules at project root. Sub-packages for `tax/`, `html/`, `prompts/`. This matches the PRD file structure and avoids import complexity for a local-only application.

## Complexity Tracking

> No constitution violations to justify.

| Aspect | Complexity Level | Justification |
|--------|-----------------|---------------|
| Tax engine (5 sub-modules) | Moderate | Required by spec — IRMAA, RMD, SS are distinct IRS rules |
| 6 MCP tools | Moderate | Each has unique computation + HTML template |
| Hybrid orchestrator-pipeline | Moderate | Keeps GPT cost low; alternative (pure agent) costs 5-10x more |
| 3-way parallelism | Low | Simple asyncio.gather, well-understood pattern |
| Dual-return pattern | Low | 4 small functions, consistent across all tools |

## Key Design Decisions

### D1: Shared Computation Layer (Direct Import, Not MCP)

Tools 3-5 call `compute_tax_components()` directly via Python import, not through MCP protocol. The optimizer calls it hundreds of times — MCP round-trips would be prohibitively slow. See `research.md#R5`.

### D2: Standard Deduction Before Brackets

Federal tax calculation applies standard deduction to total income BEFORE applying bracket rates. This matches IRS methodology: `taxable_income = gross_income - standard_deduction`, then brackets apply to `taxable_income`.

### D3: IRMAA 2-Year Lookback (Simplified)

IRMAA surcharge is based on MAGI from 2 years prior. The tool computes the IRMAA impact that would apply 2 years after the conversion year. The HTML card notes this is a 2-year-ahead impact.

### D4: Optimizer Greedy Bracket-Fill

The optimizer uses a greedy algorithm (not global optimization) that fills up to a bracket ceiling each year. Max 100 iterations. Returns best-so-far if non-convergent with `confidence < 1.0`. See `research.md#R5`.

### D5: Pipeline Triggers on Validation Complete

When `validate_projection_inputs` returns `status=complete`, the pipeline automatically runs: tax → (projection ∥ optimization ∥ breakeven) → report. No additional GPT call needed to trigger computation.

### D6: Windows stdio Buffering

MCP server on Windows must flush stdout explicitly or use `PYTHONUNBUFFERED=1`. The `ResilientToolExecutor` handles `OSError` and `BrokenPipeError` with subprocess restart. See `research.md#R10`.
