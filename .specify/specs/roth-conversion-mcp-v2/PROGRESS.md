# Project Progress

## Current Phase: implement
## Phase Status: in_progress
## Next Phase: DONE (after implement)
## Completed Phases: specify, clarify, plan, tasks, analyze
## Last Action: Phase 5 (US3 MCP Server) complete — MVP milestone, 6 tools working, 234 tests passing
## Feature Branch: roth-conversion-mcp-v2
## Feature Dir: .specify/specs/roth-conversion-mcp-v2

## Implementation Progress
- Current Task: T032 (Phase 6: US4 HTML Templates)
- Tasks Completed: [T001-T031]
- Tasks Remaining: [T032-T059]
- Total: 31 of 59

## Context Budget
- File Reads This Cycle: 18
- Tool Calls This Cycle: 50
- Debug Cycles This Cycle: 2
- Estimated Usage: HIGH
- Last Compaction: N/A

## Key Decisions
- Feature: Roth Conversion Calculator MCP Server v2.0
- Two components: FastMCP Server (6 tools) + Streamlit Chat Agent
- Tech stack: FastMCP >=2.14,<4.0, Streamlit >=1.33,<2.0, OpenAI SDK >=1.0,<3.0, mcp >=1.0,<3.0
- RENAMED html/ to html_templates/ to avoid shadowing Python stdlib html module
- Flat project structure, sub-packages: tax/, html_templates/, prompts/
- Shared computation layer: tools import tax functions directly, NOT via MCP
- Standard deduction applied BEFORE federal brackets
- Dual-return pattern on all 6 tools — JSON: {"display": "html", "data": {...}}
- Errors in validators return list of dicts: {"field": "...", "message": "..."}
- Auto-filled returns dicts: {"value": 0, "source": "age_based_default", "reason": "..."}
- compute_state_tax: guard for negative conversion amounts
- retirement_age must be strictly > current_age (not >=)

## Modified Files
- config.py, models.py, dual_return.py, validators.py, mcp_server.py
- tax/__init__.py, tax/brackets.py, tax/state_rates.py, tax/irmaa.py, tax/rmd.py, tax/ss.py, tax/calculator.py
- html_templates/__init__.py (renamed from html/)
- tests/test_tax_calculator.py, tests/test_irmaa.py, tests/test_rmd.py, tests/test_ss_taxation.py
- tests/test_validators.py, tests/test_dual_return.py, tests/test_tools.py
- requirements.txt, .env.example, .streamlit/config.toml, .gitignore

## Failed Attempts
- html/ package shadowed Python stdlib html module → renamed to html_templates/

## Blockers
