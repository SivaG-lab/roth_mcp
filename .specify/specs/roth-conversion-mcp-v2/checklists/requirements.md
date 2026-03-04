# Requirements Checklist: Roth Conversion Calculator MCP Server v2.0

**Purpose**: Track all functional requirements from spec.md
**Created**: 2026-03-03
**Feature**: .specify/specs/roth-conversion-mcp-v2/spec.md

## Tax Engine

- [ ] CHK001 FR-001: Federal tax with 2024 brackets for all 4 filing statuses + standard deduction
- [ ] CHK002 FR-002: State tax with flat rates for all 50 states + DC
- [ ] CHK003 FR-003: IRMAA surcharge with 6 tiers for single and MFJ
- [ ] CHK004 FR-004: RMD with IRS Uniform Lifetime Table (ages 73+)
- [ ] CHK005 FR-005: Social Security taxation with provisional income formula
- [ ] CHK006 FR-006: Standard deduction with age 65+ additional amounts
- [ ] CHK007 FR-007: Bracket boundaries computation

## Input Validation

- [ ] CHK008 FR-008: Age, retirement age, income, IRA balance validation
- [ ] CHK009 FR-009: Filing status enum validation
- [ ] CHK010 FR-010: State code validation
- [ ] CHK011 FR-011: Conversion amount/schedule validation
- [ ] CHK012 FR-012: Annual return and model years validation

## Auto-Fill & Defaults

- [ ] CHK013 FR-013: Auto-fill SS=0 when age < 62
- [ ] CHK014 FR-014: Auto-fill RMD=0 when age < 73
- [ ] CHK015 FR-015: Auto-fill IRMAA=0 when income below threshold
- [ ] CHK016 FR-016: Default return rate, model years, account balances
- [ ] CHK017 FR-017: Auto-wrap single amount to schedule list

## MCP Server & Tools

- [ ] CHK018 FR-018: 6 tools via FastMCP stdio transport
- [ ] CHK019 FR-019: All tools return dual-format (data + display)
- [ ] CHK020 FR-020: validate_projection_inputs as gateway tool
- [ ] CHK021 FR-021: estimate_tax_components full breakdown
- [ ] CHK022 FR-022: analyze_roth_projections year-by-year
- [ ] CHK023 FR-023: optimize_conversion_schedule bracket-fill
- [ ] CHK024 FR-024: breakeven_analysis with assessment
- [ ] CHK025 FR-025: generate_conversion_report full HTML
- [ ] CHK026 FR-026: Server-side composition via shared functions

## Agent & Pipeline

- [ ] CHK027 FR-027: GPT conversation loop for input collection
- [ ] CHK028 FR-028: Deterministic pipeline without GPT round-trips
- [ ] CHK029 FR-029: 3-way parallel in pipeline stage 2
- [ ] CHK030 FR-030: Partial failure handling
- [ ] CHK031 FR-031: compact_result strips HTML for GPT context
- [ ] CHK032 FR-032: Configurable GPT model via env var

## Streamlit UI

- [ ] CHK033 FR-033: Chat interface with st.chat_input/message
- [ ] CHK034 FR-034: Inline HTML card rendering via st.html
- [ ] CHK035 FR-035: Sidebar with profile, assumptions, results, usage
- [ ] CHK036 FR-036: Final report via components.html with download
- [ ] CHK037 FR-037: Session state management

## Error Handling

- [ ] CHK038 FR-038: ResilientToolExecutor with retry + restart
- [ ] CHK039 FR-039: Per-tool configurable timeouts
- [ ] CHK040 FR-040: Anti-hallucination guardrail

## Configuration

- [ ] CHK041 FR-041: Environment variable loading from .env

## Notes

- Check items off as completed: `[x]`
- Items map 1:1 to FR-XXX in spec.md
