# PRD: Roth Conversion Calculator — MCP Server + Streamlit Chat Agent

**Version:** 2.0 (Comprehensive Upgrade — Post Multi-Agent Review)
**Date:** 2026-03-03
**Status:** Approved — Backend Architect + Senior Architect Reviewed
**Supersedes:** PRD v1.1
**Reviews:** 4 parallel Opus 4.6 research agents + consolidation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Non-Goals](#3-goals--non-goals)
4. [Target Users & Use Cases](#4-target-users--use-cases)
5. [System Architecture](#5-system-architecture)
6. [Component 1: FastMCP Server](#6-component-1-fastmcp-server)
7. [Dual-Return Pattern](#7-dual-return-pattern)
8. [Shared Computation Layer](#8-shared-computation-layer)
9. [Component 2: Streamlit Chat Agent](#9-component-2-streamlit-chat-agent)
10. [Agent Orchestration Design](#10-agent-orchestration-design)
11. [MCP Protocol Integration](#11-mcp-protocol-integration)
12. [Tax Calculation Engine](#12-tax-calculation-engine)
13. [User Interface Design](#13-user-interface-design)
14. [Entity Rules & Answering Rules](#14-entity-rules--answering-rules)
15. [Error Handling & Reliability](#15-error-handling--reliability)
16. [Testing Strategy](#16-testing-strategy)
17. [Observability & Logging](#17-observability--logging)
18. [Non-Functional Requirements](#18-non-functional-requirements)
19. [File Structure & Tech Stack](#19-file-structure--tech-stack)
20. [Implementation Phases](#20-implementation-phases)
21. [Decision Log](#21-decision-log)
22. [Risks & Mitigations](#22-risks--mitigations)
23. [Appendix: System Prompt](#23-appendix-system-prompt)
24. [Appendix: HTML Template Patterns](#24-appendix-html-template-patterns)
25. [Architectural Review Summary](#25-architectural-review-summary)

---

## 1. Executive Summary

This PRD defines a two-component system for analyzing Roth IRA conversions:

1. **FastMCP Server** — A Python-based MCP server exposing **6 financial analysis tools** via the Model Context Protocol (MCP), with full tax component modeling including IRMAA, RMD, and Social Security.
2. **Streamlit Chat Agent** — A chat-based UI that acts as an MCP client, using OpenAI GPT API to orchestrate tool selection, input collection, and response formatting.

The Streamlit Chat Agent replaces Kore.ai MCP Agent (a paid platform) with a free, local alternative that demonstrates the same MCP agent patterns: LLM-driven tool selection, conversational input collection, and rich HTML rendering from all tools.

### Key Changes from v1.1

| Aspect | v1.1 | v2.0 |
|--------|------|------|
| Tool count | 5 | 6 (merged validate + assumptions) |
| Input count | 9 | 17 (adds multi-year, IRMAA, RMD, SS) |
| Tool output | JSON (4 tools) + HTML (1 report) | All 6 tools return HTML via dual-return |
| Tax scope | Federal brackets + flat state | Federal + state + IRMAA + RMD + Social Security taxation |
| Conversion input | Single amount | Single amount OR multi-year schedule (list) |
| Projection | None | Year-by-year convert vs no-convert table |
| Optimization | Single bracket fill | Multi-year schedule optimization |

### Key Architectural Decision

The system uses a **Hybrid Orchestrator-Pipeline** pattern (unchanged from v1.1):
- **GPT handles conversation** — input collection, intent classification, response summarization
- **Deterministic pipeline handles computation** — 6 tools run sequentially/in parallel without GPT round-trips
- **All tools return dual-format** — `{"data": {...}, "display": "...html..."}` — enabling both programmatic pipeline use and rich UI rendering
- This reduces GPT API calls to ~3-5 per conversation, costing ~$0.005 with GPT-4o-mini

---

## 2. Problem Statement

A user wants to evaluate whether converting their Traditional IRA to a Roth IRA makes financial sense. This involves:
- Collecting personal financial data (17 inputs: age, income, IRA balance, filing status, state, conversion schedule, Social Security, RMDs, IRMAA, and more)
- Computing federal + state + IRMAA + Social Security tax impact of the conversion
- Running year-by-year projections comparing convert vs. no-convert scenarios
- Finding the optimal multi-year conversion schedule within tax bracket constraints
- Running a breakeven analysis (how many years until Roth pays off)
- Generating a comprehensive HTML report with all analysis sections

The original design targeted Kore.ai MCP Agent, which is a paid platform. This project creates an equivalent free, local system using Streamlit + OpenAI GPT + FastMCP.

---

## 3. Goals & Non-Goals

### Goals
- Demonstrate MCP agent patterns (tool discovery, tool calling, LLM orchestration)
- Provide comprehensive Roth conversion analysis with federal, state, IRMAA, RMD, and Social Security tax components
- Support both single-year and multi-year conversion schedules
- Deliver year-by-year projection tables comparing convert vs. no-convert scenarios
- Return styled HTML from ALL tools (consistent with Kore.ai MCP Agent pattern)
- Deliver a conversational UX where the LLM collects inputs naturally with smart auto-fill
- Generate a styled HTML report with all analysis sections
- Support configurable GPT model via environment variable
- Minimize OpenAI API cost for personal/demo use

### Non-Goals
- Production-grade tax engine (no AMT, NIIT, credits, itemized deductions)
- Multi-user authentication or authorization
- Cloud deployment or horizontal scaling
- Persistent data storage or conversation history across sessions
- Voice channel support
- Real financial advice (educational/informational only)
- Mobile-native UI

---

## 4. Target Users & Use Cases

### Primary User
Individual developer/learner running the system locally to:
- Learn MCP protocol patterns (tool discovery, calling, result handling)
- Analyze their own Roth conversion scenario with comprehensive tax modeling
- Explore LLM-based tool orchestration with GPT + FastMCP

### Use Cases

| UC# | Use Case | Flow |
|-----|----------|------|
| UC1 | Full Roth analysis (quick mode) | User provides core info → all 6 tools run → HTML report |
| UC2 | Full analysis with advanced inputs | User provides SS, IRMAA, spending needs → comprehensive projection |
| UC3 | Quick tax check | "What tax on $50k conversion?" → input collection + tax tool only |
| UC4 | Optimal schedule query | "How much should I convert?" → optimizer runs multi-year analysis |
| UC5 | Multi-year conversion plan | "$50k/year for 5 years" → year-by-year projection |
| UC6 | What-if scenario | After initial analysis, user changes amount → full re-run (selective cascade post-MVP) |
| UC7 | Comparison (Post-MVP) | User compares multiple conversion amounts side-by-side |

---

## 5. System Architecture

### High-Level Architecture

```
+===========================================================================+
|                    ROTH CONVERSION CALCULATOR v2.0                         |
+===========================================================================+
|                                                                           |
|  +-----------------------+        +-----------------------------------+   |
|  |   STREAMLIT UI        |        |        CONFIGURATION              |   |
|  |                       |        |                                   |   |
|  |  st.chat_input()      |        |  OPENAI_API_KEY = sk-...          |   |
|  |  st.chat_message()    |        |  OPENAI_MODEL = gpt-4o-mini      |   |
|  |  st.html() (all tools)|        |  MCP_TRANSPORT = stdio            |   |
|  |  st.session_state     |        |  MCP_SERVER_CMD = python server.py|   |
|  +-----------+-----------+        +-----------------------------------+   |
|              |                                                            |
|              v  user message                                              |
|  +-----------+-------------------------------+                            |
|  |        ORCHESTRATION CORE                  |                            |
|  |                                            |                            |
|  |  Phase 1: GPT Conversation Loop            |                            |
|  |    GPT extracts entities, collects inputs  |                            |
|  |    GPT calls validate_projection_inputs    |                            |
|  |                                            |                            |
|  |  Phase 2: Deterministic Pipeline           |                            |
|  |    estimate_tax_components (serial)        |                            |
|  |    analyze_projections + optimize +        |                            |
|  |      breakeven (3-way parallel)            |                            |
|  |    generate_conversion_report (serial)     |                            |
|  |                                            |                            |
|  |  Phase 3: GPT Summary                      |                            |
|  |    GPT summarizes compacted data results   |                            |
|  |    HTML cards rendered in chat via st.html()|                            |
|  +-----------+-------------------------------+                            |
|              |                                                            |
|              v  MCP protocol (stdio)                                      |
|  +-----------+-------------------------------+                            |
|  |        FastMCP SERVER (subprocess)         |                            |
|  |                                            |                            |
|  |  ┌────────────────────────────────┐       |                            |
|  |  │   Shared Computation Layer     │       |                            |
|  |  │   compute_tax_components()     │       |                            |
|  |  │   compute_year_projection()    │       |                            |
|  |  │   compute_breakeven()          │       |                            |
|  |  │   compute_bracket_boundaries() │       |                            |
|  |  └──────────┬─────────────────────┘       |                            |
|  |             │  imported by                 |                            |
|  |  ┌──────────v─────────────────────┐       |                            |
|  |  │   MCP Tool Layer (6 tools)     │       |                            |
|  |  │   [1] validate_projection_inputs│       |                            |
|  |  │   [2] estimate_tax_components  │       |                            |
|  |  │   [3] analyze_roth_projections │       |                            |
|  |  │   [4] optimize_conversion_schedule│     |                            |
|  |  │   [5] breakeven_analysis       │       |                            |
|  |  │   [6] generate_conversion_report│       |                            |
|  |  └────────────────────────────────┘       |                            |
|  |                                            |                            |
|  |  Shared Modules:                           |                            |
|  |  tax/brackets.py | tax/state_rates.py      |                            |
|  |  tax/irmaa.py | tax/rmd.py | tax/ss.py     |                            |
|  |  html/templates.py | validators.py         |                            |
|  +--------------------------------------------+                            |
+===========================================================================+
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------:|
| Architecture pattern | Hybrid Orchestrator-Pipeline | GPT for conversation, deterministic pipeline for computation |
| Tool count | 6 (merged from reference doc's 7) | Combined validate + get_model_assumptions. Saves 1 GPT round-trip. |
| Tool output format | Dual-return: `{"data": JSON, "display": HTML}` | Pipeline needs structured data; UI needs HTML. Satisfies both. |
| MCP transport | stdio (subprocess) | Single user, localhost. Lowest latency. |
| Server-side composition | Shared computation layer | Tools 3 & 4 call internal functions directly, not via MCP |
| State management | Client accumulates, tools stateless | MCP-idiomatic. Client passes JSON to report tool. |
| Input collection | Conversational-first, Streamlit form fallback at 4+ missing | Natural UX. GPT extracts from free text. |
| Parallel tool calls | 3-way parallel in pipeline stage 2 | analyze + optimize + breakeven run concurrently |
| Conversion input | Dual: single amount OR schedule list | Backward compatible + multi-year analysis |

---

## 6. Component 1: FastMCP Server

### 6.1 Tool Inventory (6 Tools)

| # | Tool | Purpose | Input Count | Returns |
|---|------|---------|-------------|---------|
| 1 | `validate_projection_inputs` | Collect all user data + apply model assumptions | 18 params | HTML confirmation card + JSON validated data |
| 2 | `estimate_tax_components` | Federal + state + IRMAA + SS + RMD tax breakdown | 10 params | HTML mini tax table + JSON tax data |
| 3 | `analyze_roth_projections` | Year-by-year convert vs no-convert projection | 14 params | HTML year-by-year table + JSON projection data |
| 4 | `optimize_conversion_schedule` | Find optimal multi-year conversion schedule | 11 params | HTML schedule table + JSON optimization data |
| 5 | `breakeven_analysis` | Years until Roth conversion pays off | 8 params | HTML highlight card + JSON breakeven data |
| 6 | `generate_conversion_report` | Final comprehensive styled HTML report | 5 JSON params | Full HTML report + JSON summary |

### 6.2 Tool Dependency Graph

```
validate_projection_inputs
       |
       v
estimate_tax_components
       |
       +---> analyze_roth_projections --------+
       |        (year-by-year table)           |
       |                                       |
       +---> optimize_conversion_schedule ----+
       |        (uses internal tax functions)   |
       |                                       |
       +---> breakeven_analysis --------------+
                                               |
                                               v
                                  generate_conversion_report
```

- Stage 1 (serial): validate → estimate_tax
- Stage 2 (3-way parallel): analyze_projections || optimize_schedule || breakeven
- Stage 3 (serial): generate_report

### 6.3 Tool Specifications

#### Tool 1: `validate_projection_inputs`

```python
@mcp.tool()
def validate_projection_inputs(
    trad_ira_balance: float | None = None,
    current_age: int | None = None,
    retirement_age: int | None = None,
    filing_status: str | None = None,
    state: str | None = None,
    annual_income: float | None = None,
    conversion_amount: float | None = None,
    conversion_schedule: list[float] | None = None,
    roth_ira_balance_initial: float | None = None,
    taxable_dollars_available: float | None = None,
    annual_return: float | None = None,
    taxable_account_annual_return: float | None = None,
    model_years: int | None = None,
    social_security: float | None = None,
    rmd: float | None = None,
    irmaa: float | None = None,
    cost_basis: float = 0,
    other_ordinary_income_by_year: list[float] | None = None,
    spending_need_after_tax_by_year: list[float] | None = None,
) -> str:
    """
    WHEN TO USE: Call this FIRST when starting any Roth conversion analysis.
    This is the ONLY tool that collects user inputs. It validates all financial
    data AND applies model assumptions (default return rates, RMD age, SS age).
    Merges input validation + model assumptions into a single step.

    PIPELINE POSITION: 1 of 6 (gateway — all other tools require this first)

    WHAT IT NEEDS:
    REQUIRED (must collect from user before calling):
    - trad_ira_balance: Traditional IRA balance ($)
    - current_age: User's current age (18-100)
    - retirement_age: Target retirement age (must be > current_age)
    - filing_status: single | married_joint | married_separate | head_of_household
    - state: 2-letter US state code
    - annual_income: Gross annual income ($)

    REQUIRED (one of these two):
    - conversion_amount: Single conversion amount ($), OR
    - conversion_schedule: List of yearly conversion amounts [$y1, $y2, ...]

    AUTO-FILL (do NOT ask if conditions met):
    - social_security: 0 if current_age < 62
    - rmd: 0 if current_age < 73
    - irmaa: 0 if annual_income < $103,000
    - roth_ira_balance_initial: 0 if user says "no Roth"
    - taxable_dollars_available: 0 if user says "no taxable account"

    DEFAULT (use if not specified):
    - annual_return: 0.07 (7%)
    - taxable_account_annual_return: 0.07 (7%)
    - model_years: 30

    RETURNS: Dual-return JSON with:
    - "display": HTML confirmation card showing validated inputs + assumptions,
      OR HTML form if required inputs are missing
    - "data": JSON with {status, inputs, assumptions, auto_filled}

    DO NOT USE FOR: Tax calculations (use estimate_tax_components),
    projections (use analyze_roth_projections), or optimization
    (use optimize_conversion_schedule).
    """
```

**Required fields**: trad_ira_balance, current_age, retirement_age, filing_status, state, annual_income, plus one of conversion_amount/conversion_schedule

**Smart defaults applied by tool code**:
- `years_to_retirement = retirement_age - current_age`
- `annual_return = 0.07` if not specified
- `taxable_account_annual_return = 0.07` if not specified
- `model_years = 30` if not specified
- `social_security = 0` if age < 62
- `rmd = 0` if age < 73
- `irmaa = 0` if income < $103,000
- `roth_ira_balance_initial = 0` if not specified
- `taxable_dollars_available = 0` if not specified
- Single `conversion_amount` auto-wrapped to `conversion_schedule = [conversion_amount]`

**Validation rules**:
- current_age: integer, 18-100
- retirement_age: integer, > current_age, <= 100
- annual_income: float, >= 0
- trad_ira_balance: float, >= 0
- filing_status: enum [single, married_joint, married_separate, head_of_household]
- state: valid 2-letter US state code
- conversion_amount: float, > 0, <= trad_ira_balance
- conversion_schedule: each entry >= 0, sum <= trad_ira_balance
- annual_return: float, > -1, <= 0.30
- model_years: integer, 1-50

#### Tool 2: `estimate_tax_components`

```python
@mcp.tool()
def estimate_tax_components(
    annual_income: float | None = None,
    conversion_amount: float | None = None,
    filing_status: str | None = None,
    state: str | None = None,
    cost_basis: float = 0,
    social_security: float = 0,
    rmd: float = 0,
    irmaa: float = 0,
    other_ordinary_income: float = 0,
) -> str:
    """
    WHEN TO USE: After validate_projection_inputs confirms all data.
    Estimates the TAX COST of a specific conversion amount in a single year.
    Breaks down: federal tax, state tax, IRMAA surcharge impact,
    Social Security taxation impact, and RMD tax interaction.

    PIPELINE POSITION: 2 of 6

    RETURNS: Dual-return with HTML mini tax table and JSON tax breakdown
    {federal_tax, state_tax, irmaa_impact, ss_tax_impact, rmd_tax, total_tax_cost,
    effective_rate, marginal_rate, bracket_before, bracket_after, conversion_amount}.
    Note: For MFJ, spouse income is included in annual_income.

    DO NOT USE FOR:
    - Year-by-year projections (use analyze_roth_projections)
    - Finding optimal amounts (use optimize_conversion_schedule)

    KEY DISTINCTION: This tool answers "how much TAX on THIS amount?"
    analyze_roth_projections answers "what happens OVER TIME?"
    """
```

**Calculation logic**:
1. Taxable conversion = conversion_amount - cost_basis
2. Total taxable income = annual_income + taxable_conversion + other_ordinary_income
3. Apply 2024 federal brackets for filing_status → federal_tax
4. State tax = taxable_conversion * flat_state_rate
5. IRMAA surcharge = lookup(annual_income + conversion_amount, filing_status)
6. SS tax impact = [calculate_ss_taxable_portion(social_security, income_with_conversion) - calculate_ss_taxable_portion(social_security, income_without_conversion)] * marginal_rate
7. RMD tax interaction = rmd * marginal_rate (if applicable)
8. Total = federal + state + irmaa + ss_tax + rmd_tax

#### Tool 3: `analyze_roth_projections`

```python
@mcp.tool()
def analyze_roth_projections(
    trad_ira_balance: float | None = None,
    roth_ira_balance_initial: float = 0,
    conversion_schedule: list[float] | None = None,
    annual_return: float = 0.07,
    taxable_account_annual_return: float = 0.07,
    taxable_dollars_available: float = 0,
    model_years: int = 30,
    current_age: int | None = None,
    federal_tax: float | None = None,
    state_tax: float | None = None,
    social_security: float = 0,
    rmd: float = 0,
    other_ordinary_income_by_year: list[float] | None = None,
    spending_need_after_tax_by_year: list[float] | None = None,
) -> str:
    """
    WHEN TO USE: After estimate_tax_components has calculated the tax cost.
    Runs a YEAR-BY-YEAR projection comparing "convert" vs "don't convert"
    scenarios over the full model horizon.

    PIPELINE POSITION: 3 of 6 (NEW tool — did not exist in v1)

    WHAT IT DOES: For each year in the projection:
    - Tracks Traditional IRA, Roth IRA, and taxable account balances
    - Applies conversions per the conversion_schedule
    - Deducts tax cost from taxable_dollars_available (or IRA if insufficient)
    - Applies RMDs starting at age 73 (uses internal compute_rmd function)
    - Calculates Social Security income and taxation
    - Compares total after-tax wealth: convert path vs. no-convert path

    NOTE: This tool contains internal iteration loops over model_years.
    It calls shared computation functions directly, NOT via MCP.

    RETURNS: Dual-return with HTML year-by-year table (5-year summary +
    expandable full table) and JSON projection data {projections[],
    summary{final_roth_value, final_trad_value, net_benefit, crossover_year}}.

    DO NOT USE FOR:
    - Single-year tax cost (use estimate_tax_components)
    - Finding OPTIMAL conversion amounts (use optimize_conversion_schedule)
    - Simple "how long to break even" (use breakeven_analysis)
    """
```

**Internal iteration pattern**:
```python
for year in range(model_years):
    conversion = conversion_schedule[year] if year < len(conversion_schedule) else 0
    year_tax = compute_tax_components(conversion, other_income, ...)  # Internal call
    trad_balance = (trad_balance - conversion) * (1 + annual_return)
    roth_balance = (roth_balance + conversion - year_tax) * (1 + annual_return)
    # Track no-convert scenario in parallel
    # Apply RMDs when age >= 73
    # Apply Social Security when age >= ss_start_age
```

#### Tool 4: `optimize_conversion_schedule`

```python
@mcp.tool()
def optimize_conversion_schedule(
    trad_ira_balance: float | None = None,
    annual_income: float | None = None,
    filing_status: str | None = None,
    state: str | None = None,
    current_age: int | None = None,
    retirement_age: int | None = None,
    model_years: int = 30,
    annual_return: float = 0.07,
    max_annual_conversion: float | None = None,
    target_tax_bracket: str | None = None,
    optimization_goal: str = "minimize_tax",
) -> str:
    """
    WHEN TO USE: When the user asks "how much SHOULD I convert?" or
    "what's the best conversion strategy?" or "optimize my conversions."

    PIPELINE POSITION: 4 of 6

    WHAT IT DOES: Calculates the optimal multi-year conversion schedule.
    Considers tax bracket boundaries, IRMAA thresholds, RMD interactions,
    and time value of tax-free growth.

    NOTE: Internally calls compute_tax_components() for each candidate
    amount evaluation. Does NOT call estimate_tax_components via MCP.

    AUTO-FILL:
    - optimization_goal = "minimize_tax" if not specified
    - max_annual_conversion = trad_ira_balance if not specified

    RETURNS: Dual-return with HTML schedule table (year × amount × tax)
    and JSON {optimal_schedule[], total_tax_cost, tax_saved_vs_baseline,
    converged, confidence}.

    DO NOT USE FOR:
    - Running projections with KNOWN amounts (use analyze_roth_projections)
    - Single-year tax calculation (use estimate_tax_components)

    KEY DISTINCTION: This tool OUTPUTS a conversion_schedule.
    analyze_roth_projections CONSUMES a conversion_schedule.
    """
```

#### Tool 5: `breakeven_analysis`

```python
@mcp.tool()
def breakeven_analysis(
    conversion_amount: float | None = None,
    total_tax_cost: float | None = None,
    current_age: int | None = None,
    annual_return: float = 0.07,
    retirement_age: int = 65,
    future_tax_rate: float | None = None,
    federal_tax: float | None = None,
    state_tax: float | None = None,
) -> str:
    """
    WHEN TO USE: When the user asks "is it worth it?" or "how long until
    it pays off?" or "when do I break even?"

    PIPELINE POSITION: 5 of 6

    AUTO-FILL:
    - total_tax_cost: from estimate_tax_components result
    - future_tax_rate: defaults to current federal_tax if not specified

    RETURNS: Dual-return with HTML highlight card {breakeven_years,
    breakeven_age, assessment: "worth_it"|"marginal"|"not_worth_it"}
    and JSON breakeven data.

    DO NOT USE FOR:
    - Full year-by-year projections (use analyze_roth_projections)
    - Tax amount calculation (use estimate_tax_components)
    """
```

**Model**:
- Roth path: (conversion_amount - total_tax_cost) * (1 + return)^n (tax-free withdrawals)
- Traditional path: conversion_amount * (1 + return)^n * (1 - future_tax_rate)
- Breakeven = year when Roth path >= Traditional path

**Assessment logic**:
- breakeven_years < 10: "worth_it"
- breakeven_years 10-20: "marginal"
- breakeven_years > 20 or never: "not_worth_it"

#### Tool 6: `generate_conversion_report`

```python
@mcp.tool()
def generate_conversion_report(
    validated_inputs: str | None = None,
    tax_analysis: str | None = None,
    projection_data: str = "",
    optimization_data: str = "",
    breakeven_data: str = "",
) -> str:
    """
    WHEN TO USE: LAST tool in every workflow. Call only after all analysis
    tools have completed. Assembles everything into a final styled report.

    PIPELINE POSITION: 6 of 6 (terminal)

    WHAT IT NEEDS: JSON strings from prior tool results.
    - validated_inputs: Output data from validate_projection_inputs
    - tax_analysis: Output data from estimate_tax_components
    - projection_data: Output data from analyze_roth_projections (optional)
    - optimization_data: Output data from optimize_conversion_schedule (optional)
    - breakeven_data: Output data from breakeven_analysis (optional)

    Handles missing sections gracefully — if optional data is absent,
    generates report without those sections.

    RETURNS: Dual-return with full styled HTML report and JSON summary.

    DO NOT USE FOR: ANY calculations. This tool ONLY formats and renders.
    """
```

**Report sections**:
1. Header with user profile summary
2. Model Assumptions Used (return rates, horizon, defaults)
3. Tax Impact Breakdown (federal, state, IRMAA, SS, RMD, total)
4. Year-by-Year Projection Table (from analyze_roth_projections, if available)
5. Optimal Conversion Schedule (from optimizer, if available)
6. Breakeven Timeline
7. Recommendations (data-driven, based on all results)
8. Disclaimer
9. Styled with inline CSS (dark/light theme support)

---

## 7. Dual-Return Pattern

### The Problem

v1.1 returned JSON from computation tools and HTML only from the report. The v2.0 requirement is HTML from ALL tools. But the deterministic pipeline needs structured data to chain tools — HTML is not programmatically parseable.

### The Solution

Every tool returns a JSON envelope with both formats:

```python
import json

def dual_return(html: str, data: dict) -> str:
    """All tools use this pattern."""
    return json.dumps({
        "display": html,
        "data": data,
    })
```

### Client-Side Access

```python
def extract_html(result: str) -> str:
    """Extract HTML from dual-return for Streamlit rendering."""
    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict) and "display" in parsed:
            return parsed["display"]
    except (json.JSONDecodeError, KeyError):
        pass
    return result  # Fallback: assume raw HTML

def extract_data(result: str) -> dict:
    """Extract structured data from dual-return for pipeline consumption."""
    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict) and "data" in parsed:
            return parsed["data"]
    except (json.JSONDecodeError, KeyError):
        pass
    return {}
```

### Context Window Compaction

HTML never enters the GPT context. The `compact_result` function extracts `data` only:

```python
def compact_result(tool_name: str, result: str) -> str:
    """v2.0: Extract data from dual-return, discard HTML for GPT context."""
    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict) and "data" in parsed and "display" in parsed:
            if tool_name == "generate_conversion_report":
                return "[HTML report rendered to user]"
            elif tool_name == "analyze_roth_projections":
                data = parsed["data"]
                return json.dumps({
                    "summary": data.get("summary", {}),
                    "total_years": len(data.get("projections", [])),
                })
            else:
                return json.dumps(parsed["data"])
    except (json.JSONDecodeError, KeyError):
        pass
    return result
```

### Token Impact

| Content | v1.1 Tokens | v2.0 Tokens (compacted) |
|---------|-------------|-------------------------|
| System prompt | ~400 | ~1,280 |
| Tool definitions (schemas) | ~600 | ~2,200 |
| User messages (5-8 turns) | ~500 | ~500 |
| Tool results (compacted) | ~1,000 | ~1,200 |
| Pipeline summary | ~400 | ~500 |
| **Total per GPT call** | **~2,500** | **~5,680** |

Still well within GPT-4o-mini's 128k context. Cost increase: ~$0.003 → ~$0.005 per conversation.

---

## 8. Shared Computation Layer

### Architecture

MCP tools are thin wrappers around shared business logic functions. Tools that need to compose (like optimize_conversion_schedule calling tax computation iteratively) call shared functions directly, not through MCP:

```
┌─────────────────────────────────────────────────┐
│                  MCP Server                      │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │         Shared Computation Layer          │   │
│  │                                          │   │
│  │  compute_tax_components()                │   │
│  │  compute_year_projection()               │   │
│  │  compute_breakeven()                     │   │
│  │  compute_bracket_boundaries()            │   │
│  │  compute_rmd()                           │   │
│  │  compute_irmaa_surcharge()               │   │
│  │  compute_ss_taxation()                   │   │
│  └──────────┬───────────────────────────────┘   │
│             │  imported by                       │
│             v                                    │
│  ┌──────────────────────────────────────────┐   │
│  │          MCP Tool Layer (6 tools)         │   │
│  │  Each tool: validate → compute → format   │   │
│  │  Returns: dual_return(html=..., data=...) │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Key Pattern: Internal vs External Calls

```python
# Shared computation (NO MCP dependency)
from tax.calculator import compute_tax_components

# MCP tool wrapper
@mcp.tool()
def estimate_tax_components(...) -> str:
    result = compute_tax_components(...)
    html = format_tax_estimate(result)
    return dual_return(html=html, data=result)

# Optimization tool uses shared function DIRECTLY
@mcp.tool()
def optimize_conversion_schedule(...) -> str:
    for candidate in generate_candidates(trad_ira_balance):
        # Direct call — no MCP round-trip
        tax = compute_tax_components(candidate, annual_income, ...)
        score = evaluate_schedule(candidate, tax, ...)
    return dual_return(html=format_schedule(best), data=best)
```

---

## 9. Component 2: Streamlit Chat Agent

### 9.1 Page Layout

```
+-----------------------------------------------------------------------+
|  [Roth Conversion Advisor v2.0]                              [⚙️]    |
+-------------------+---------------------------------------------------+
|                   |                                                   |
|  SIDEBAR          |              MAIN CHAT AREA                       |
|                   |                                                   |
|  Your Info        |  [Bot] Welcome! I can help you analyze a Roth    |
|  ─────────        |        conversion. Tell me about yourself.        |
|  Age: 55 → 65     |                                                   |
|  Income: $150,000 |  [User] I'm 55, MFJ, $150k income, $500k IRA,   |
|  IRA: $500,000    |         California. Convert $50k/yr for 5 years. |
|  Status: MFJ      |                                                   |
|  State: CA        |  [Bot] ✅ Inputs Validated (HTML card)            |
|  Schedule: 5yr    |        Assumptions: 7% return, 30yr horizon      |
|                   |                                                   |
|  Assumptions      |  [st.status: Running analysis...]                 |
|  ─────────        |    📊 Tax Impact (HTML mini table)                |
|  Return: 7%       |    📈 Year-by-Year Projection (HTML table)        |
|  Horizon: 30yr    |    🎯 Optimal Schedule (HTML table)               |
|  SS: $0 (age<62)  |    ⏱ Breakeven: 12 years (HTML card)             |
|  IRMAA: $0        |  [st.status: Analysis complete!]                  |
|                   |                                                   |
|  API Usage        |  [Bot] Here's your complete analysis:              |
|  ─────────        |        ╔══════════════════════════════╗            |
|  Tokens: 5,680    |        ║  ROTH CONVERSION REPORT      ║            |
|  Cost: ~$0.005    |        ║  [Full styled HTML report]   ║            |
|                   |        ╚══════════════════════════════╝            |
|  [Start Over]     |                                                   |
|                   |  [📥 Download HTML]                               |
+-------------------+---------------------------------------------------+
```

### 9.2 Data Models (`models.py`)

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class FilingStatus(str, Enum):
    SINGLE = "single"
    MARRIED_JOINT = "married_joint"
    MARRIED_SEPARATE = "married_separate"
    HEAD_OF_HOUSEHOLD = "head_of_household"


class AutoFillSource(str, Enum):
    USER_PROVIDED = "user_provided"
    AUTO_CALCULATED = "auto_calculated"
    AGE_BASED_DEFAULT = "age_based_default"
    SYSTEM_DEFAULT = "system_default"
    USER_IMPLICIT = "user_implicit"


@dataclass
class UserProfile:
    # Core identity (REQUIRED)
    current_age: int | None = None
    retirement_age: int | None = None
    filing_status: str | None = None
    state: str | None = None
    annual_income: float | None = None
    trad_ira_balance: float | None = None

    # Conversion specification (REQUIRED — one of two)
    conversion_amount: float | None = None
    conversion_schedule: list[float] | None = None

    # Account details (AUTO-FILLABLE)
    roth_ira_balance_initial: float = 0
    taxable_dollars_available: float = 0
    cost_basis: float = 0

    # Rates and horizons (DEFAULTABLE)
    annual_return: float = 0.07
    taxable_account_annual_return: float = 0.07
    model_years: int = 30

    # Tax-adjacent inputs (AUTO-FILLABLE based on age/income)
    social_security: float = 0
    rmd: float = 0
    irmaa: float = 0

    # Year-by-year overrides (OPTIONAL)
    other_ordinary_income_by_year: list[float] | None = None
    spending_need_after_tax_by_year: list[float] | None = None

    @property
    def required_fields(self) -> list[str]:
        return ["current_age", "retirement_age", "filing_status",
                "state", "annual_income", "trad_ira_balance"]

    @property
    def missing_required(self) -> list[str]:
        return [f for f in self.required_fields
                if getattr(self, f) is None]

    @property
    def has_conversion_spec(self) -> bool:
        return (self.conversion_amount is not None or
                self.conversion_schedule is not None)

    def to_tool_args(self) -> dict:
        result = {}
        for fname in self.__dataclass_fields__:
            val = getattr(self, fname)
            if val is not None:
                result[fname] = val
        return result


@dataclass
class ModelAssumptions:
    annual_return: float = 0.07
    taxable_account_annual_return: float = 0.07
    inflation_rate: float = 0.03
    model_years: int = 30
    rmd_start_age: int = 73
    ss_start_age: int = 67


@dataclass
class TaxEstimate:
    federal_tax: float = 0
    state_tax: float = 0
    irmaa_impact: float = 0
    ss_tax_impact: float = 0
    rmd_tax: float = 0
    total_tax_cost: float = 0
    effective_rate: float = 0
    marginal_rate: float = 0
    bracket_before: str = ""
    bracket_after: str = ""
    conversion_amount: float = 0


@dataclass
class ProjectionData:
    projections: list[dict] = field(default_factory=list)
    summary: dict = field(default_factory=lambda: {
        "final_roth_value": 0,
        "final_trad_value": 0,
        "net_benefit": 0,
        "crossover_year": None,
    })

    @classmethod
    def from_tool_data(cls, data: dict) -> "ProjectionData":
        """Construct from tool output, handling nested structure."""
        return cls(
            projections=data.get("projections", []),
            summary=data.get("summary", {}),
        )


@dataclass
class OptimizationResult:
    optimal_schedule: list[float] = field(default_factory=list)
    total_tax_cost: float = 0
    tax_saved_vs_baseline: float = 0
    optimization_goal: str = "minimize_tax"
    converged: bool = True
    confidence: float = 1.0


@dataclass
class BreakevenResult:
    breakeven_years: int = 0
    breakeven_age: int = 0
    assessment: str = ""


@dataclass
class CalculationResults:
    tax_estimate: TaxEstimate | None = None
    projection: ProjectionData | None = None
    optimization: OptimizationResult | None = None
    breakeven: BreakevenResult | None = None
    report_html: str = ""
    tools_completed: list[str] = field(default_factory=list)


@dataclass
class TokenTracker:
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    calls: list = field(default_factory=list)

    def record(self, response):
        self.total_prompt_tokens += response.usage.prompt_tokens
        self.total_completion_tokens += response.usage.completion_tokens

    @property
    def estimated_cost(self):
        return (self.total_prompt_tokens * 0.15 / 1_000_000 +
                self.total_completion_tokens * 0.60 / 1_000_000)
```

### 9.3 Session State Structure

```python
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "profile" not in st.session_state:
        st.session_state.profile = UserProfile()
    if "assumptions" not in st.session_state:
        st.session_state.assumptions = ModelAssumptions()
    if "results" not in st.session_state:
        st.session_state.results = CalculationResults()
    if "html_cards" not in st.session_state:
        st.session_state.html_cards = {}  # tool_name → HTML string
    if "token_data" not in st.session_state:
        st.session_state.token_data = {"prompt_tokens": 0, "completion_tokens": 0, "calls": []}
    if "pipeline_phase" not in st.session_state:
        st.session_state.pipeline_phase = "collecting"
```

### 9.4 Sidebar Features

1. **Your Information** — Live display of all collected inputs with auto-fill indicators
2. **Model Assumptions** — Shows return rate, horizon, SS/RMD/IRMAA assumptions
3. **Calculation Results** — Summary metrics after calculations run
4. **API Usage** — Token count and estimated cost
5. **Start Over** — Resets all session state
6. **Model Config** — Shows current model name

---

## 10. Agent Orchestration Design

### 10.1 Pattern: Hybrid Orchestrator-Pipeline (unchanged from v1.1, expanded)

**Phase 1: GPT Conversation Loop (input collection)**
- GPT receives user message, extracts entities, calls `validate_projection_inputs`
- If inputs missing, GPT asks conversationally (1-3 fields) or renders Streamlit form (4+ fields)
- Loop continues until all required inputs are confirmed
- Typically 1-3 GPT API calls

**Phase 2: Deterministic Pipeline (computation)**
- Once inputs confirmed, pipeline runs without GPT:
  1. `estimate_tax_components` → tax data (serial)
  2. `analyze_roth_projections` + `optimize_conversion_schedule` + `breakeven_analysis` → 3-way parallel
  3. `generate_conversion_report` with all results (serial)
- Zero GPT API calls in this phase
- Each tool's HTML card rendered via `st.html()` during `st.status`

**Phase 3: GPT Summary (presentation)**
- Feed compacted data results (no HTML) to GPT
- GPT generates a conversational summary
- HTML cards already displayed during Phase 2
- 1 GPT API call

### 10.2 Agent Loop Implementation

```python
async def agent_loop(user_message: str, mcp_session):
    messages = st.session_state.messages
    messages.append({"role": "user", "content": user_message})

    messages[0] = build_system_message(
        st.session_state.profile,
        st.session_state.results
    )

    openai_tools = await discover_tools(mcp_session)
    html_outputs = []
    iteration = 0

    while iteration < MAX_ITERATIONS:  # MAX_ITERATIONS = 10
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
            parallel_tool_calls=False,
            timeout=OPENAI_TIMEOUT,
        )

        assistant_msg = response.choices[0].message
        messages.append(assistant_msg.to_dict())

        if not assistant_msg.tool_calls:
            return assistant_msg.content, html_outputs

        # Phase 1: Process ALL tool calls first
        inputs_just_completed = False
        for tool_call in assistant_msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            result = await call_mcp_tool(mcp_session, name, args)

            # Extract and store both data and HTML
            tool_data = extract_data(result)
            tool_html = extract_html(result)
            update_session_data(name, tool_data)
            st.session_state.html_cards[name] = tool_html

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": compact_result(name, result),
            })

            if name == "validate_projection_inputs" and is_inputs_complete(tool_data):
                inputs_just_completed = True

        # Phase 2: AFTER all tool results appended, run pipeline
        if inputs_just_completed:
            pipeline_results = await run_analysis_pipeline(mcp_session)
            html_outputs.extend(pipeline_results.get("html_cards", []))
            messages.append({
                "role": "system",
                "content": format_pipeline_summary(pipeline_results),
            })

        iteration += 1

    return "I've processed several steps. What would you like next?", html_outputs
```

### 10.3 Deterministic Pipeline

```python
async def run_analysis_pipeline(mcp_session) -> dict:
    inputs = st.session_state.profile.to_tool_args()
    results = {}
    html_cards = []

    with st.status("Running Roth conversion analysis...", expanded=True) as status:

        # Step 1: Tax components (required by all downstream tools)
        st.write("Estimating tax components...")
        tax_raw = await call_mcp_tool(mcp_session, "estimate_tax_components", {
            "annual_income": inputs["annual_income"],
            "conversion_amount": inputs.get("conversion_schedule", [0])[0],
            "filing_status": inputs["filing_status"],
            "state": inputs["state"],
            "cost_basis": inputs.get("cost_basis", 0),
            "social_security": inputs.get("social_security", 0),
            "rmd": inputs.get("rmd", 0),
            "irmaa": inputs.get("irmaa", 0),
        })
        tax_data = extract_data(tax_raw)
        tax_html = extract_html(tax_raw)
        results["tax"] = tax_data
        html_cards.append(tax_html)
        st.html(tax_html)

        # Step 2: THREE tools in parallel
        st.write("Running projections, optimization, and breakeven...")
        projection_task = asyncio.create_task(
            call_mcp_tool(mcp_session, "analyze_roth_projections", {
                "trad_ira_balance": inputs["trad_ira_balance"],
                "roth_ira_balance_initial": inputs.get("roth_ira_balance_initial", 0),
                "conversion_schedule": inputs.get("conversion_schedule"),
                "annual_return": inputs.get("annual_return", 0.07),
                "taxable_account_annual_return": inputs.get("taxable_account_annual_return", 0.07),
                "taxable_dollars_available": inputs.get("taxable_dollars_available", 0),
                "model_years": inputs.get("model_years", 30),
                "current_age": inputs["current_age"],
                "federal_tax": tax_data.get("marginal_rate", 0.22),
                "state_tax": tax_data.get("state_tax", 0) / max(inputs.get("conversion_schedule", [1])[0], 1),
                "social_security": inputs.get("social_security", 0),
                "rmd": inputs.get("rmd", 0),
                "other_ordinary_income_by_year": inputs.get("other_ordinary_income_by_year"),
                "spending_need_after_tax_by_year": inputs.get("spending_need_after_tax_by_year"),
            })
        )
        optimize_task = asyncio.create_task(
            call_mcp_tool(mcp_session, "optimize_conversion_schedule", {
                "trad_ira_balance": inputs["trad_ira_balance"],
                "annual_income": inputs["annual_income"],
                "filing_status": inputs["filing_status"],
                "state": inputs["state"],
                "current_age": inputs["current_age"],
                "retirement_age": inputs["retirement_age"],
                "model_years": inputs.get("model_years", 30),
                "annual_return": inputs.get("annual_return", 0.07),
            })
        )
        breakeven_task = asyncio.create_task(
            call_mcp_tool(mcp_session, "breakeven_analysis", {
                "conversion_amount": inputs.get("conversion_schedule", [0])[0],
                "total_tax_cost": tax_data.get("total_tax_cost", 0),
                "current_age": inputs["current_age"],
                "annual_return": inputs.get("annual_return", 0.07),
                "retirement_age": inputs.get("retirement_age", 65),
                "federal_tax": tax_data.get("marginal_rate", 0.22),
                "state_tax": tax_data.get("state_tax", 0) / max(inputs.get("conversion_schedule", [1])[0], 1),
            })
        )

        proj_raw, opt_raw, brk_raw = await asyncio.gather(
            projection_task, optimize_task, breakeven_task,
            return_exceptions=True
        )

        # Handle partial failures gracefully
        for name, raw in [("projection", proj_raw), ("optimization", opt_raw), ("breakeven", brk_raw)]:
            if not isinstance(raw, Exception):
                results[name] = extract_data(raw)
                html = extract_html(raw)
                html_cards.append(html)
                st.html(html)
            else:
                st.write(f"⚠️ {name} failed: {raw}")

        # Step 3: Generate report
        st.write("Generating final report...")
        report_raw = await call_mcp_tool(mcp_session, "generate_conversion_report", {
            "validated_inputs": json.dumps(inputs),
            "tax_analysis": json.dumps(results.get("tax", {})),
            "projection_data": json.dumps(results.get("projection", {})),
            "optimization_data": json.dumps(results.get("optimization", {})),
            "breakeven_data": json.dumps(results.get("breakeven", {})),
        })
        results["report_html"] = extract_html(report_raw)
        html_cards.append(results["report_html"])

        status.update(label="Analysis complete!", state="complete", expanded=False)

    # Render final report outside status (always visible)
    import streamlit.components.v1 as components
    components.html(results["report_html"], height=800, scrolling=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download HTML", results["report_html"],
                           "roth_report.html", "text/html")

    results["html_cards"] = html_cards
    return results
```

### 10.4 Helper Functions

```python
def is_inputs_complete(tool_data: dict) -> bool:
    return tool_data.get("status") == "complete"

def update_session_data(tool_name: str, data: dict):
    if tool_name == "validate_projection_inputs" and data.get("status") == "complete":
        inputs = data.get("inputs", {})
        profile = st.session_state.profile
        for k, v in inputs.items():
            if v is not None and hasattr(profile, k):
                setattr(profile, k, v)
        assumptions = data.get("assumptions", {})
        for k, v in assumptions.items():
            if hasattr(st.session_state.assumptions, k):
                setattr(st.session_state.assumptions, k, v)
    elif tool_name == "estimate_tax_components":
        safe = {k: v for k, v in data.items() if k in TaxEstimate.__dataclass_fields__}
        st.session_state.results.tax_estimate = TaxEstimate(**safe)
    elif tool_name == "analyze_roth_projections":
        st.session_state.results.projection = ProjectionData.from_tool_data(data)
    elif tool_name == "optimize_conversion_schedule":
        safe = {k: v for k, v in data.items() if k in OptimizationResult.__dataclass_fields__}
        st.session_state.results.optimization = OptimizationResult(**safe)
    elif tool_name == "breakeven_analysis":
        safe = {k: v for k, v in data.items() if k in BreakevenResult.__dataclass_fields__}
        st.session_state.results.breakeven = BreakevenResult(**safe)
    st.session_state.results.tools_completed.append(tool_name)

def format_pipeline_summary(pipeline_results: dict) -> str:
    parts = ["[System: Analysis pipeline completed. Results below:]"]
    if "tax" in pipeline_results:
        tax = pipeline_results["tax"]
        parts.append(f"Tax Impact: total=${tax.get('total_tax_cost', 0):,.0f}, "
                     f"effective_rate={tax.get('effective_rate', 0):.1%}")
    if "projection" in pipeline_results:
        proj = pipeline_results["projection"]
        parts.append(f"Projection: net_benefit=${proj.get('wealth_difference', 0):,.0f}, "
                     f"crossover_year={proj.get('crossover_year', 'N/A')}")
    if "optimization" in pipeline_results:
        opt = pipeline_results["optimization"]
        parts.append(f"Optimal: tax_saved=${opt.get('tax_saved_vs_baseline', 0):,.0f}")
    if "breakeven" in pipeline_results:
        brk = pipeline_results["breakeven"]
        parts.append(f"Breakeven: {brk.get('breakeven_years', 'N/A')} years "
                     f"(age {brk.get('breakeven_age', 'N/A')})")
    parts.append("HTML cards have been rendered. Summarize conversationally.")
    return "\n".join(parts)

def build_system_message(profile: UserProfile, results: CalculationResults) -> dict:
    base = load_system_prompt()
    context = ["\n## CURRENT STATE"]
    if profile.missing_required:
        context.append(f"Missing: {', '.join(profile.missing_required)}")
        context.append("→ Next: validate_projection_inputs")
    elif not results.tax_estimate:
        context.append("Inputs collected. Tax not yet estimated.")
    elif not results.projection:
        context.append("Tax estimated. Projection not yet run.")
    else:
        context.append("Analysis complete.")
    if results.tools_completed:
        context.append(f"Tools called: {', '.join(results.tools_completed)}")
    return {"role": "system", "content": base + "\n".join(context)}
```

---

## 11. MCP Protocol Integration

### 11.1 Transport: stdio (unchanged from v1.1)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python", args=["mcp_server.py"],
)
```

### 11.2 Schema Translation: MCP → OpenAI

```python
def mcp_tool_to_openai_function(mcp_tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": TOOL_DESCRIPTIONS.get(mcp_tool.name, mcp_tool.description),
            "parameters": mcp_tool.inputSchema or {"type": "object", "properties": {}},
        },
    }
```

**List parameter handling**: `list[float] | None` generates `{"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}]}` in JSON Schema. Both MCP and OpenAI function calling support this natively.

**MCP result unwrapping**: FastMCP wraps tool return values in `TextContent`. The `call_mcp_tool` helper must extract the text:
```python
async def call_mcp_tool(session, name: str, args: dict) -> str:
    result = await session.call_tool(name, args)
    return result.content[0].text  # Unwrap TextContent
```

**Note on parallel tool calls over stdio**: The MCP protocol supports request/response multiplexing via JSON-RPC IDs, but stdio transport is a single byte stream. The 3-way parallel dispatch via `asyncio.gather` achieves concurrent *waiting* but requests may serialize at the transport layer. For true parallelism, SSE/HTTP transport would be needed. For this single-user demo, concurrent stdio is sufficient.

### 11.3 Session Lifecycle (persistent, unchanged from v1.1)

```python
import nest_asyncio
nest_asyncio.apply()

@st.cache_resource
def get_mcp_session():
    import asyncio
    loop = asyncio.new_event_loop()
    async def _init():
        server_params = StdioServerParameters(command="python", args=["mcp_server.py"])
        transport = await stdio_client(server_params).__aenter__()
        read, write = transport
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()
        return session
    return loop.run_until_complete(_init()), loop
```

---

## 12. Tax Calculation Engine

### 12.1 Federal Tax Brackets (2024)

(Same as v1.1 — all filing statuses covered)

### 12.2 State Tax Rates (Simplified Flat Rates)

(Same as v1.1 — all 50 states + DC)

### 12.3 IRMAA Surcharge Calculation (NEW)

| MAGI Threshold (Single) | MAGI Threshold (MFJ) | Monthly Part B Surcharge | Annual Impact |
|--------------------------|----------------------|--------------------------|---------------|
| ≤ $103,000 | ≤ $206,000 | $0 | $0 |
| $103,001 - $129,000 | $206,001 - $258,000 | $65.90 | $790.80 |
| $129,001 - $161,000 | $258,001 - $322,000 | $164.80 | $1,977.60 |
| $161,001 - $193,000 | $322,001 - $386,000 | $263.70 | $3,164.40 |
| $193,001 - $500,000 | $386,001 - $750,000 | $362.60 | $4,351.20 |
| > $500,000 | > $750,000 | $395.60 | $4,747.20 |

```python
def compute_irmaa_surcharge(magi: float, filing_status: str) -> float:
    """Compute annual IRMAA surcharge based on MAGI and filing status."""
    thresholds = IRMAA_THRESHOLDS[filing_status]  # Lookup table
    for threshold, surcharge in reversed(thresholds):
        if magi > threshold:
            return surcharge * 12  # Monthly to annual
    return 0.0
```

### 12.4 RMD Calculation (NEW)

Uses the IRS Uniform Lifetime Table (2024):

```python
RMD_TABLE = {
    73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
    78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
    83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4,
    88: 13.7, 89: 12.9, 90: 12.2, # ... continues to 120
}

def compute_rmd(age: int, ira_balance: float) -> float:
    """Compute Required Minimum Distribution."""
    if age < 73 or ira_balance <= 0:
        return 0.0
    distribution_period = RMD_TABLE.get(age, 12.0)
    return ira_balance / distribution_period
```

### 12.5 Social Security Taxation (NEW)

```python
def compute_ss_taxation(ss_benefit: float, other_income: float,
                         filing_status: str) -> float:
    """Compute taxable portion of Social Security benefits."""
    combined_income = other_income + (ss_benefit / 2)

    if filing_status in ("single", "head_of_household"):
        if combined_income <= 25000:
            return 0.0
        elif combined_income <= 34000:
            return min(ss_benefit * 0.50, (combined_income - 25000) * 0.50)
        else:
            return min(ss_benefit * 0.85,
                      4500 + (combined_income - 34000) * 0.85)
    elif filing_status == "married_joint":
        if combined_income <= 32000:
            return 0.0
        elif combined_income <= 44000:
            return min(ss_benefit * 0.50, (combined_income - 32000) * 0.50)
        else:
            return min(ss_benefit * 0.85,
                      6000 + (combined_income - 44000) * 0.85)
    elif filing_status == "married_separate":
        # IRS: if lived with spouse at any time during year, 85% is taxable
        return min(ss_benefit * 0.85, max(0, combined_income) * 0.85)
    return ss_benefit * 0.85  # Conservative fallback
```

### 12.6 Standard Deduction (2024)

Applied before federal bracket calculation. Subtracted from total taxable income (annual_income + taxable_conversion + other_ordinary_income) before applying brackets.

| Filing Status | Standard Deduction |
|---------------|-------------------|
| Single | $14,600 |
| Married Filing Jointly | $29,200 |
| Married Filing Separately | $14,600 |
| Head of Household | $21,900 |

Additional deduction for age 65+: $1,550 (single/HoH), $1,300 (married).

### 12.7 Optimizer Algorithm

The `optimize_conversion_schedule` tool uses a **greedy bracket-fill** approach:

1. For each year from `current_age` to `retirement_age`:
   a. Call `compute_bracket_boundaries(annual_income, filing_status)` to find the top of the current bracket
   b. Candidate conversion = bracket_ceiling - current_taxable_income
   c. If `target_tax_bracket` specified, use that bracket's ceiling instead
   d. Cap at `max_annual_conversion` and remaining `trad_ira_balance`
   e. Call `compute_tax_components(candidate, ...)` to score the candidate
2. Score function: total after-tax wealth at `model_years` horizon
3. Valid `optimization_goal` values: `"minimize_tax"` (minimize total tax paid), `"maximize_wealth"` (maximize terminal after-tax wealth)
4. Valid `target_tax_bracket` values: `"10%"`, `"12%"`, `"22%"`, `"24%"`, `"32%"`, `"35%"`, `"37%"` or `None` (auto-optimize)
5. Convergence: if schedule does not improve score after full iteration, mark `converged=True`
6. Non-convergence: if iteration limit (100) reached, return best-so-far with `converged=False, confidence=<0-1>`

### 12.8 Calculation Assumptions

- Standard deduction applied (not itemized) — see Section 12.6
- No AMT or NIIT calculations
- IRMAA uses simplified threshold lookup (2024 rates). Note: IRMAA uses a 2-year lookback; this model simplifies by showing the IRMAA impact that would occur 2 years after the conversion year.
- RMD uses Uniform Lifetime Table (not Joint Life table)
- Social Security taxation uses provisional income formula; SS tax impact is the *marginal* impact of the conversion (difference in SS taxation with and without conversion)
- State taxes use flat effective rate
- Expected investment return default: 7% nominal (not inflation-adjusted)
- `inflation_rate` in `ModelAssumptions` is reserved for future use (real-return projections)
- Disclaimer: "For educational purposes only. Consult a tax professional."

---

## 13. User Interface Design

### 13.1 Conversation Flow — Quick Mode Happy Path

```
Turn 1 - Bot:
    Welcome! I'm your Roth Conversion Advisor. I can help you analyze
    whether converting your Traditional IRA to a Roth IRA makes sense.
    Tell me about yourself — your age, income, IRA balance, filing
    status, and state. You can also tell me how much you'd like to convert.

Turn 2 - User:
    I'm 55, married filing jointly, make $150k, $500k in my Traditional
    IRA, live in California. I want to convert $50k per year for 5 years.

Turn 3 - Bot:
    [Calls validate_projection_inputs → extracts all values]
    [Auto-fills: social_security=0 (age<62), rmd=0 (age<73), irmaa=0,
     annual_return=7%, model_years=30, roth_balance=0, taxable=0]

    ✅ Inputs Validated (HTML confirmation card)
    I'm assuming 7% annual return and a 30-year horizon.
    Let me run your analysis now...

    [st.status: "Running Roth conversion analysis..."]
      📊 Tax Impact on $50K Conversion (HTML mini table)
        Federal: $12,000 | State: $4,650 | IRMAA: $0 | Total: $16,650
      📈 Year-by-Year Projection (HTML expandable table)
      🎯 Optimal Schedule: $42K/yr stays in 24% bracket (HTML table)
      ⏱ Breakeven: 12 years (age 67) (HTML card)
      Generating final report...
    [st.status: "Analysis complete!"]

Turn 4 - Bot (GPT Summary):
    Here are your key findings:
    • Converting $50K/year for 5 years costs ~$16,650/year in taxes
    • The conversion breaks even at age 67 (12 years)
    • The optimizer suggests $42K/year to stay in the 24% bracket
    Would you like to explore a different amount or schedule?

Turn 5 - User:
    What if I convert $75k per year instead?

Turn 6 - Bot:
    [Re-runs pipeline with conversion_schedule=[75000]*5]
    With $75K/year: tax cost ~$22,200/year, breakeven at age 69.
```

### 13.2 Input Collection Strategy

| Tier | Fields | Count | Method |
|------|--------|-------|--------|
| **Tier 1: Must Ask** | current_age, trad_ira_balance, annual_income, filing_status, state | 5 | Conversational or form |
| **Tier 2: Must Ask** | retirement_age, conversion_amount/schedule | 2 | Conversational follow-up |
| **Tier 3: Auto-fill** | years_to_retirement, social_security, rmd, irmaa | 4 | Never ask — calculate/default |
| **Tier 4: Defaults** | annual_return, taxable_account_annual_return, model_years | 3 | Inform user of assumption |
| **Tier 5: Rare** | roth_balance, taxable_dollars, per-year lists, cost_basis | 5 | Only if user mentions them |

**Effective user question count: 5-7, not 17.**

| Missing Fields | Strategy |
|---------------|----------|
| 0 | Proceed to pipeline |
| 1-3 | GPT asks conversationally |
| 4+ | Render multi-step Streamlit form (grouped by section) |

### 13.3 Conversion Schedule Collection

GPT is instructed to recognize natural language patterns:

| User Says | Parsed As |
|-----------|-----------|
| "convert $50k" | conversion_amount = 50000 |
| "convert all" | conversion_schedule = [trad_ira_balance] |
| "$50k per year for 5 years" | conversion_schedule = [50000] * 5 |
| "spread over 5 years" | conversion_schedule = [balance/5] * 5 |
| "$50k this year, $75k next year" | conversion_schedule = [50000, 75000] |
| "help me figure it out" | Skip schedule, run optimize tool |

GPT never asks user to type a Python list. Instead:
> "How much would you like to convert? You can say '$50k per year for 5 years',
> 'convert it all at once', or 'help me find the best amount.'"

### 13.4 HTML Output Rendering in Chat

Each tool's HTML card is rendered inline via `st.html()` during the `st.status` progress indicator. After the pipeline completes, the status collapses and the final report is displayed prominently below.

**Color coding by tool type**:

| Tool | Border Color | Feels Like |
|------|-------------|------------|
| validate_projection_inputs | Green | Confirmation bubble |
| estimate_tax_components | Red | Cost/expense card |
| analyze_roth_projections | Blue | Data table |
| optimize_conversion_schedule | Purple | Recommendation |
| breakeven_analysis | Blue | Alert card |
| generate_conversion_report | Full style | Mini document |

### 13.5 Multi-Step Form (4+ missing fields)

```python
def render_multi_step_form(missing_fields: list):
    sections = {
        "Personal Info": ["current_age", "retirement_age"],
        "Income & Accounts": ["annual_income", "trad_ira_balance",
                              "filing_status", "state"],
        "Conversion Plan": ["conversion_amount"],
    }
    with st.form("roth_inputs"):
        for section_name, fields in sections.items():
            relevant = [f for f in fields if f in missing_fields]
            if relevant:
                st.subheader(section_name)
                for field in relevant:
                    render_field_input(field, values)
        submitted = st.form_submit_button("Run Analysis")
        if submitted:
            return values
    return None
```

---

## 14. Entity Rules & Answering Rules

### 14.1 Entity Rules (Validation — enforced in tool code)

| Input | Rule | Error Message |
|-------|------|---------------|
| current_age | 18-100 | "Age must be between 18 and 100" |
| retirement_age | > current_age, <= 100 | "Retirement age must be after current age" |
| trad_ira_balance | >= 0 | "IRA balance cannot be negative" |
| annual_income | >= 0 | "Income cannot be negative" |
| filing_status | IN [single, married_joint, married_separate, head_of_household] | "Invalid filing status" |
| state | valid 2-letter code | "Invalid state code" |
| conversion_amount | > 0, <= trad_ira_balance | "Conversion amount must be > 0 and ≤ IRA balance" |
| conversion_schedule | each >= 0, sum <= trad_ira_balance | "Schedule entries must be ≥ 0, total ≤ IRA balance" |
| annual_return | > -1, <= 0.30 | "Return rate must be between -100% and 30%" |
| model_years | 1-50 | "Model horizon must be 1-50 years" |
| social_security | >= 0 | "SS benefit cannot be negative" |
| rmd | >= 0 | "RMD cannot be negative" |
| irmaa | >= 0 | "IRMAA cannot be negative" |

### 14.2 Answering Rules (Auto-fill — enforced in tool code + system prompt)

| Condition | Auto-fill | Where Encoded |
|-----------|-----------|---------------|
| current_age and retirement_age both provided | years_to_retirement = retirement_age - current_age | Tool code |
| current_age < 62 | social_security = 0 | Tool code + system prompt |
| current_age < 73 | rmd = 0 | Tool code + system prompt |
| annual_income < $103,000 (single) or $206,000 (MFJ) | irmaa = 0 | Tool code + system prompt |
| User says "no Roth" / "starting fresh" | roth_ira_balance_initial = 0 | System prompt |
| User says "no taxable account" | taxable_dollars_available = 0 | System prompt |
| annual_return not specified | annual_return = 0.07 | Tool code |
| model_years not specified | model_years = 30 | Tool code |
| filing_status == "single" | spouse_income = 0 | Tool code |
| User says "convert all" | conversion_schedule = [trad_ira_balance] | System prompt |

---

## 15. Error Handling & Reliability

### 15.1 Error Taxonomy (expanded from v1.1)

| Error Type | Detection | Recovery | Max Retries |
|-----------|-----------|----------|-------------|
| Tool validation error | Tool returns `{"error": true, "field": ...}` | GPT explains, asks correction | Unlimited |
| Tool execution exception | try/except in wrapper | Retry once, show error | 1 |
| MCP server crash | ConnectionError / BrokenPipeError | Restart subprocess, retry | 2 |
| GPT malformed tool call | JSON parse error | Re-prompt GPT | 2 |
| OpenAI rate limit | HTTP 429 | Exponential backoff | 3 |
| Pipeline partial failure | Exception in one parallel tool | Report with available sections | 1 |
| Projection mid-calculation failure | Exception at year N | Return partial results with flag | 0 |
| Optimizer non-convergence | Iteration limit reached | Return best-so-far with confidence | 0 |

### 15.2 Dual-Layer Input Validation (unchanged)

**Layer 1: GPT pre-validation (soft)** — System prompt instructs sanity checks
**Layer 2: Tool validation (hard)** — Python code validates, returns structured errors

### 15.3 Anti-Hallucination Guardrail (expanded)

```python
def check_hallucinated_numbers(gpt_response: str, tool_results: list[str]) -> list[str]:
    import re
    all_tool_text = " ".join(str(r) for r in tool_results)
    suspicious = []
    for match in re.finditer(r'\$[\d,]+(?:\.\d{2})?', gpt_response):
        if match.group() not in all_tool_text:
            suspicious.append(f"Dollar: {match.group()}")
    for match in re.finditer(r'(\d+(?:\.\d+)?)\s*%', gpt_response):
        if match.group() not in all_tool_text:
            suspicious.append(f"Percent: {match.group()}")
    for match in re.finditer(r'(\d+)\s*years?\s*(?:to break|until|to pay)', gpt_response):
        if match.group(1) not in all_tool_text:
            suspicious.append(f"Years: {match.group()}")
    return suspicious
```

### 15.4 Resilient Tool Executor (expanded with per-tool timeouts)

```python
TOOL_TIMEOUTS = {
    "validate_projection_inputs": 5.0,
    "estimate_tax_components": 5.0,
    "analyze_roth_projections": 15.0,
    "optimize_conversion_schedule": 30.0,
    "breakeven_analysis": 5.0,
    "generate_conversion_report": 10.0,
}

class ResilientToolExecutor:
    def __init__(self, session, max_retries=2):
        self.session = session
        self.max_retries = max_retries

    async def call_tool(self, name: str, args: dict) -> str:
        timeout = TOOL_TIMEOUTS.get(name, 10.0)
        for attempt in range(self.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self.session.call_tool(name, args), timeout=timeout
                )
                return result
            except (ConnectionError, BrokenPipeError):
                if attempt < self.max_retries:
                    await self._restart_session()
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    if name == "optimize_conversion_schedule":
                        args["max_iterations"] = args.get("max_iterations", 100) // 2
                    continue
        return json.dumps({"error": f"{name} failed after {self.max_retries} retries"})
```

---

## 16. Testing Strategy

### 16.1 Test Pyramid (expanded)

```
            +------------------+
           /   E2E Tests (5%)  \
          /  Full conversation  \
         +------------------------+
        /  Integration Tests (15%) \
       /  MCP roundtrip, pipeline  \
      +------------------------------+
     /     Unit Tests (80%)           \
    /  Tax, IRMAA, RMD, SS, tools,   \
   /   validators, schemas, helpers,   \
  /    HTML templates, list params      \
 +---------------------------------------+
```

### 16.2 New Unit Tests Required

**Tax components**: `test_irmaa_surcharge`, `test_rmd_calculation`, `test_ss_taxation`
**List parameters**: `test_conversion_schedule_validation`, `test_per_year_list_defaults`
**HTML templates**: `test_format_tax_estimate`, `test_format_projection_table`, `test_format_breakeven_card`
**Dual-return**: `test_extract_html`, `test_extract_data`, `test_compact_result_v2`
**Projection**: `test_30_year_projection`, `test_partial_projection_failure`
**Optimizer**: `test_bracket_fill_optimization`, `test_optimizer_convergence`

### 16.3 Prompt Regression Tests (14 cases)

```json
[
  {"id": "start_flow", "input": "I want to convert my IRA",
   "expected_tool": "validate_projection_inputs"},
  {"id": "bulk_input", "input": "55, MFJ, $120k, $400k IRA, NY",
   "expected_tool": "validate_projection_inputs",
   "expected_args_contain": {"current_age": 55}},
  {"id": "tax_without_context", "input": "What tax on $50k conversion?",
   "expected_tool": "validate_projection_inputs"},
  {"id": "optimization_request", "input": "What's the best amount to convert?",
   "expected_tool": "validate_projection_inputs"},
  {"id": "schedule_input", "input": "$50k per year for 5 years",
   "expected_tool": "validate_projection_inputs",
   "expected_args_contain": {"conversion_schedule": [50000,50000,50000,50000,50000]}},
  {"id": "projection_request", "input": "Show me year by year projection",
   "expected_tool": "validate_projection_inputs"},
  {"id": "no_hallucination", "input": "What bracket am I in?",
   "response_must_not_contain": ["$", "%"]},
  {"id": "what_if", "input": "What if I convert $75k instead?",
   "expected_tool": "estimate_tax_components"},
  {"id": "spread_schedule", "input": "Spread my $500k over 10 years",
   "expected_tool": "validate_projection_inputs",
   "expected_args_contain": {"conversion_schedule": [50000,50000,50000,50000,50000,50000,50000,50000,50000,50000]}},
  {"id": "auto_fill_ss", "input": "I'm 45, single, $100k, $300k IRA, TX, convert $30k",
   "expected_tool": "validate_projection_inputs",
   "expected_args_contain": {"social_security": null}},
  {"id": "invalid_state", "input": "I'm 55, MFJ, $120k, $400k IRA, XX, convert $50k",
   "expected_tool": "validate_projection_inputs",
   "expected_result_contain": {"error": true}},
  {"id": "negative_amount", "input": "Convert -$50k from my IRA",
   "expected_tool": "validate_projection_inputs",
   "expected_result_contain": {"error": true}},
  {"id": "help_optimize", "input": "Help me figure out the best amount to convert",
   "expected_tool": "validate_projection_inputs"},
  {"id": "convert_all", "input": "Convert all of my IRA",
   "expected_tool": "validate_projection_inputs"}
]
```

### 16.4 Additional Required Tests

- **Pipeline partial failure**: Mock one parallel tool to raise an exception; verify report generates with available sections only
- **compact_result function**: Unit test with each tool's output format; verify HTML is stripped, data is preserved
- **Auto-fill rules**: Verify age < 62 → SS=0, age < 73 → RMD=0, income < threshold → IRMAA=0
- **MAX_SESSION_COST enforcement**: Verify GPT calls are blocked when cost cap is reached

---

## 17. Observability & Logging

### 17.1 Logging (structured JSON, expanded)

| Category | Events | Fields |
|----------|--------|--------|
| User interaction | message_received, form_submitted | session_id, message_length |
| Tool calls | tool_initiated, tool_completed, tool_failed | tool_name, duration_ms, success |
| GPT API | api_call, api_error | model, prompt_tokens, completion_tokens |
| Pipeline | pipeline_started, pipeline_completed | tools_run, parallel_time_ms, total_time_ms |
| Auto-fill | answering_rule_fired | field_name, auto_fill_source, value_applied |
| Errors | validation_error, timeout, partial_result | error_type, tool_name |

### 17.2 Token Usage Tracking (in sidebar)

### 17.3 Quality Metrics

| Metric | Target |
|--------|--------|
| Turns to completion | ≤ 10 turns (quick mode), ≤ 16 (detailed) |
| Tool misroute rate | < 5% |
| Average cost per conversation | < $0.01 (GPT-4o-mini) |

---

## 18. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Latency (per user turn) | < 5 seconds |
| Latency (full pipeline) | < 15 seconds (6 tools, 3-way parallel) |
| Token usage per conversation | < 8,000 tokens |
| Cost per conversation | < $0.01 (GPT-4o-mini) |
| Concurrent users | 1 (localhost) |
| Python version | 3.10+ |
| Authentication | None |

---

## 19. File Structure & Tech Stack

### 19.1 File Structure

```
roth_mcp/
├── mcp_server.py               # FastMCP server entry point (6 tools)
├── streamlit_app.py            # Streamlit chat UI entry point
├── agent_loop.py               # GPT conversation loop (Phase 1 + Phase 3)
├── pipeline.py                 # Deterministic computation pipeline (Phase 2)
├── mcp_client.py               # MCP session management + ResilientToolExecutor
├── schema_converter.py         # MCP → OpenAI schema translation
├── models.py                   # Data classes (UserProfile, CalculationResults, etc.)
├── config.py                   # Environment config (validation, path resolution)
├── dual_return.py              # dual_return(), extract_html(), extract_data()
├── prompts/
│   └── system.md               # System prompt (separate file)
├── tax/
│   ├── __init__.py
│   ├── brackets.py             # Federal tax brackets (2024)
│   ├── state_rates.py          # Flat state tax rates (all 50 states)
│   ├── calculator.py           # compute_tax_components() — shared computation
│   ├── irmaa.py                # IRMAA surcharge calculation (NEW)
│   ├── rmd.py                  # RMD calculation with Uniform Lifetime Table (NEW)
│   └── ss.py                   # Social Security taxation (NEW)
├── html/
│   ├── __init__.py
│   ├── templates.py            # HTML template formatters (6 formatters)
│   └── styles.py               # Inline CSS for all cards/reports
├── ui/
│   ├── __init__.py
│   ├── forms.py                # Streamlit native form builder (multi-step)
│   └── sidebar.py              # Sidebar components
├── validators.py               # Input validation functions
├── tests/
│   ├── test_tax_calculator.py  # Federal + state tax tests
│   ├── test_irmaa.py           # IRMAA surcharge tests (NEW)
│   ├── test_rmd.py             # RMD calculation tests (NEW)
│   ├── test_ss_taxation.py     # Social Security taxation tests (NEW)
│   ├── test_tools.py           # MCP tool logic tests
│   ├── test_validators.py      # Validation tests
│   ├── test_list_params.py     # List parameter handling tests (NEW)
│   ├── test_dual_return.py     # Dual-return pattern tests (NEW)
│   ├── test_html_templates.py  # HTML formatter tests (NEW)
│   ├── test_schema_converter.py# Schema translation tests
│   ├── test_orchestrator.py    # Agent loop + pipeline helper tests
│   ├── test_integration.py     # MCP roundtrip tests
│   └── prompt_eval_cases.json  # Prompt regression test data (8 cases)
├── .env.example
├── .streamlit/
│   └── config.toml             # localhost binding
├── requirements.txt
├── CLAUDE.md
└── README.md
```

### 19.2 Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| MCP Server | FastMCP (Python SDK) | >=2.14,<4.0 |
| Chat UI | Streamlit | >=1.33,<2.0 |
| LLM Orchestration | OpenAI Python SDK | >=1.0,<3.0 |
| MCP Client | mcp Python package | >=1.0,<3.0 |
| Async compatibility | nest-asyncio | >=1.6,<2.0 |
| Environment Config | python-dotenv | >=1.0,<2.0 |
| Logging | structlog | >=24.0,<26.0 |
| Testing | pytest + pytest-asyncio | >=8.0 / >=0.23 |

### 19.3 `.env.example`

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Model Configuration
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30
MAX_SESSION_COST=0.50

# MCP Server
MCP_SERVER_CMD=python
MCP_SERVER_ARGS=mcp_server.py
```

---

## 20. Implementation Phases

### Phase 1: Foundation (Tax Engine + Tools)

| Task | Description | Files |
|------|-------------|-------|
| T001 | Federal + state tax engine (from v1.1) | tax/brackets.py, tax/state_rates.py, tax/calculator.py |
| T002 | IRMAA surcharge calculation | tax/irmaa.py |
| T003 | RMD calculation | tax/rmd.py |
| T004 | Social Security taxation | tax/ss.py |
| T005 | Input validators (expanded for 17 inputs + lists) | validators.py |
| T006 | Dual-return pattern module | dual_return.py |
| T007 | HTML template formatters (6 templates) | html/templates.py, html/styles.py |
| T008 | FastMCP server with 6 tools | mcp_server.py |
| T009 | Unit tests for all tax + tools | tests/ |

### Phase 2: Client + Orchestration

| Task | Description | Files |
|------|-------------|-------|
| T010 | MCP client + schema translation | mcp_client.py, schema_converter.py |
| T011 | Data models | models.py |
| T012 | Agent loop + Pipeline (3-way parallel) | agent_loop.py, pipeline.py |
| T013 | Streamlit chat UI | streamlit_app.py |
| T014 | Sidebar + multi-step forms | ui/forms.py, ui/sidebar.py |

### Phase 3: Polish + Testing

| Task | Description | Files |
|------|-------------|-------|
| T015 | System prompt (v2.0 with auto-fill rules, 6 examples) | prompts/system.md |
| T016 | Error handling + resilient executor | mcp_client.py |
| T017 | Progress indicators + status messages | streamlit_app.py |
| T018 | Anti-hallucination guardrail (expanded) | agent_loop.py |
| T019 | Integration + prompt regression tests | tests/ |

### Phase 4: Post-MVP Enhancements

| Task | Priority |
|------|----------|
| Scenario comparison (multiple amounts side-by-side) | High |
| Value change → selective re-calculation cascade | High |
| Report export (HTML download, PDF) | Medium |
| LLM provider abstraction (swap OpenAI/Claude/Ollama) | Medium |
| Streamlit data_editor for conversion schedule | Medium |
| Graceful degradation (fallback UI when API down) | Medium |

---

## 21. Decision Log

| # | Decision | Alternatives | Rationale |
|---|----------|-------------|-----------|
| D1 | 6 tools (merge validate + assumptions) | 7 tools (separate), 5 tools (keep v1.1) | Eliminates routing decision for GPT. Assumptions always needed. |
| D2 | Dual-return pattern (data + display) | JSON only (v1.1), HTML only (Kore.ai), separate endpoints | Pipeline needs data, UI needs HTML. Satisfies both. |
| D3 | Shared computation layer | Tools call other tools via MCP, All logic in tools | MCP tools don't support inter-tool calls. Shared functions avoid round-trips. |
| D4 | Client accumulates state | Server-side session state, Pass everything as params | MCP-idiomatic. Stateless tools are easier to test. |
| D5 | 3-way parallel in pipeline stage 2 | Sequential (simpler), 2-way parallel (v1.1) | All 3 tools depend on tax data, not each other. Max parallelism. |
| D6 | Per-tool configurable timeouts | Uniform 10s timeout (v1.1) | Optimizer may take 30s; validation takes 5s. |
| D7 | 5-tier input collection (5-7 questions) | Ask all 17, Form for all, Conversational only | Most inputs have safe defaults. Don't overwhelm user. |
| D8 | HTML from all tools | JSON + HTML report only (v1.1) | Matches Kore.ai MCP Agent pattern. Consistent UX. |
| D9 | Conversion schedule as list with natural language parsing | Require list syntax, Form only, Single amount only | Users speak naturally. GPT parses "$50k/yr for 5 years". |
| D10 | Full tax upgrade (IRMAA + RMD + SS) | Simplified only (v1.1), Partial (RMD + SS, skip IRMAA) | User requested full upgrade. Makes tool more realistic. |
| D11 | Hybrid Orchestrator-Pipeline (unchanged) | Pure GPT loop, Pure state machine | Still optimal balance of cost and reliability. |
| D12 | Persistent MCP session (unchanged) | Per-request sessions | Avoid ~300-500ms subprocess spawn per message. |
| D13 | nest_asyncio (unchanged) | Custom threading, sync-only | Simplest fix for Streamlit Tornado + asyncio conflict. |
| D14 | System prompt in separate file (unchanged) | Hardcoded string | Enables independent prompt iteration. |
| D15 | Version-pinned dependencies (unchanged) | Unpinned | FastMCP 3.0 broke real projects. |
| D16 | 6 few-shot examples in system prompt | 3 (v1.1), 10+ | 6 covers the top ambiguity patterns for 6 tools. |

---

## 22. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | GPT computes tax/IRMAA/RMD amounts itself | Medium | Critical | Expanded anti-hallucination rule + regex check |
| R2 | GPT calls tools in wrong order | Low | Medium | PIPELINE POSITION tags + tool descriptions + CURRENT STATE injection |
| R3 | HTML bloats GPT context window | Medium | Medium | Dual-return pattern — HTML never enters GPT context |
| R4 | 17-parameter tool causes GPT argument extraction errors | Medium | Medium | 5-tier input collection — GPT fills 5-7, tool defaults rest |
| R5 | Optimizer non-convergence | Low | Low | Return best-so-far with confidence score |
| R6 | 30-year projection performance | Low | Low | Pure Python arithmetic loop — < 1 second |
| R7 | IRMAA/RMD data becomes outdated | Certain (annual) | Medium | Single-file update per tax year (tax/irmaa.py, tax/rmd.py) |
| R8 | MCP server crash | Low | Medium | ResilientToolExecutor with subprocess restart |
| R9 | Streamlit async mismatch | Certain (without fix) | Fatal | nest_asyncio.apply() at startup |
| R10 | Dependency version drift | Certain (annually) | Critical | Pin to major version ranges |
| R11 | No timeout/cost cap | Medium | Medium | OPENAI_TIMEOUT + MAX_SESSION_COST config |
| R12 | List parameters in MCP schema | Low | Low | list[float] | None translates correctly to JSON Schema arrays |
| R13 | Windows stdio subprocess buffering | Medium | Medium | Flush stdout after each tool response; handle OSError in ResilientToolExecutor; test on Windows early |
| R14 | st.html() height clipping for tool cards | Low | Low | Use components.html() with estimated height for all tool cards, or st.markdown with unsafe_allow_html=True |

---

## 23. Appendix: System Prompt

```
You are a Roth Conversion Advisor, an AI assistant that helps users analyze
whether converting their Traditional IRA to a Roth IRA makes financial sense.

## ABSOLUTE RULE — NEVER VIOLATE
You MUST NOT compute, estimate, or state any of the following from your own
knowledge: tax amounts, tax rates, bracket thresholds, state tax rates,
IRMAA surcharges, Social Security taxation amounts, RMD amounts, breakeven
years, or projected account balances.

ALL numerical financial information MUST come from tool results:
- Tax data → estimate_tax_components
- Projections → analyze_roth_projections
- Optimal amounts → optimize_conversion_schedule
- Breakeven → breakeven_analysis

If asked without tool results, say: "Let me calculate that for you."

## TOOL SELECTION ORDER
1. validate_projection_inputs — ALWAYS first
2. estimate_tax_components — Tax cost breakdown
3. analyze_roth_projections — Year-by-year comparison
4. optimize_conversion_schedule — ONLY if user wants help choosing amounts
5. breakeven_analysis — When does it pay off
6. generate_conversion_report — Call LAST

Note: Tool 4 is OPTIONAL. Skip if user already specified amounts.
Tools 3, 4, 5 can run in parallel after tool 2.

## HOW TO COLLECT INFORMATION
- Extract values from natural language
- Pass all known values to validate_projection_inputs
- PRIORITY: current_age, trad_ira_balance, annual_income, filing_status,
  state, retirement_age, conversion_amount/schedule
- If 1-3 missing: ask conversationally. If 4+: app shows form.

## AUTO-FILL RULES (do NOT ask)
- social_security = 0 if age < 62
- rmd = 0 if age < 73
- irmaa = 0 if income < $103,000 (single) / $206,000 (MFJ)
- annual_return = 0.07, model_years = 30 if not specified
- roth_ira_balance = 0 if user says "no Roth"
When auto-filling, mention: "I'm assuming 7% return and 30-year horizon."

## CONVERSION SCHEDULE
- "convert $50k" → conversion_amount = 50000
- "$50k per year for 5 years" → conversion_schedule = [50000,50000,50000,50000,50000]
- "convert all" → conversion_schedule = [trad_ira_balance]
- "help me figure it out" → run optimize_conversion_schedule
Never ask user to type a Python list.

## TOOL SELECTION EXAMPLES

1. "I want to convert my IRA" → validate_projection_inputs
2. "I'm 55, MFJ, $150k, $500k IRA, California" → validate_projection_inputs(...)
3. "What tax on $50k conversion?" → validate_projection_inputs first
4. "What's the best amount?" → validate → tax → optimize_conversion_schedule
5. "$100k/year for 3 years" → validate with conversion_schedule=[100000,100000,100000]
6. "Show me year by year" → validate → tax → analyze_roth_projections

## BOUNDARIES
- NOT a financial advisor. Include disclaimer.
- Do NOT make up rates, IRMAA thresholds, RMD amounts.
- Do NOT advise on non-Roth topics.

## TONE
- Professional but approachable
- Plain language, explain jargon
- Specific numbers from tool results

## DISCLAIMER
"This analysis is for informational and educational purposes only. It uses
simplified tax calculations including approximations for IRMAA, Social
Security taxation, and RMDs. Please consult a qualified tax professional
before making any Roth conversion decisions."
```

---

## 24. Appendix: HTML Template Patterns

### Validation Confirmation Card (Green)

```python
def format_validation_result(data: dict) -> str:
    inputs = data.get('inputs', data)
    assumptions = data.get('assumptions', {})
    years_to_ret = inputs.get('retirement_age', 0) - inputs.get('current_age', 0)
    return f"""
    <div style="background: #f0fdf4; border-left: 3px solid #22c55e;
                padding: 10px 14px; font-family: Arial; font-size: 13px;
                border-radius: 4px; max-width: 500px;">
      <strong>Inputs Validated</strong><br>
      Age: {inputs['current_age']} &rarr; {inputs['retirement_age']}
           ({years_to_ret} yrs to retirement)<br>
      IRA Balance: ${inputs['trad_ira_balance']:,.0f}<br>
      Schedule: {len(inputs.get('conversion_schedule', []))} year(s)<br>
      <em style="color: #666; font-size: 11px;">
        Assumptions: {assumptions.get('annual_return', 0.07):.0%} return,
        {assumptions.get('model_years', 30)}yr horizon
      </em>
    </div>
    """
```

### Tax Estimate Mini Table (Red)

```python
def format_tax_estimate(data: dict) -> str:
    return f"""
    <div style="font-family: Arial; font-size: 13px; max-width: 500px;
                border-left: 3px solid #ef4444; padding: 10px 14px;
                background: #fef2f2; border-radius: 4px;">
      <strong>Tax Impact on ${data['conversion_amount']:,.0f} Conversion</strong>
      <table style="width: 100%; margin-top: 8px; border-collapse: collapse;">
        <tr><td>Federal Tax</td><td style="text-align:right">${data['federal_tax']:,.0f}</td></tr>
        <tr><td>State Tax</td><td style="text-align:right">${data['state_tax']:,.0f}</td></tr>
        <tr><td>IRMAA Impact</td><td style="text-align:right">${data['irmaa_impact']:,.0f}</td></tr>
        <tr><td>SS Tax Impact</td><td style="text-align:right">${data['ss_tax_impact']:,.0f}</td></tr>
        <tr style="border-top: 1px solid #ccc; font-weight: 600;">
          <td>Total Tax Cost</td><td style="text-align:right">${data['total_tax_cost']:,.0f}</td></tr>
      </table>
    </div>
    """
```

### Breakeven Highlight Card (Blue)

```python
def format_breakeven(data: dict) -> str:
    return f"""
    <div style="background: #eff6ff; border-left: 3px solid #3b82f6;
                padding: 10px 14px; font-family: Arial; font-size: 13px;
                border-radius: 4px; max-width: 500px;">
      <strong>Breakeven: {data['breakeven_years']} years</strong><br>
      The Roth conversion pays off by age {data['breakeven_age']}.<br>
      Assessment: <strong>{data['assessment'].replace('_', ' ').title()}</strong>
    </div>
    """
```

### Projection Table (Blue, collapsible)

```python
def format_projection_table(projections: list, model_years: int) -> str:
    summary_rows = projections[:5]  # First 5 years
    last_row = projections[-1]      # Final year

    rows_html = "".join(
        f"<tr><td>{r['year']}</td><td>{r['age']}</td>"
        f"<td>${r.get('conversion', 0):,.0f}</td>"
        f"<td>${r['roth_balance']:,.0f}</td>"
        f"<td>${r['trad_balance']:,.0f}</td></tr>"
        for r in summary_rows
    )
    full_rows = "".join(
        f"<tr><td>{r['year']}</td><td>{r['age']}</td>"
        f"<td>${r.get('conversion', 0):,.0f}</td>"
        f"<td>${r['roth_balance']:,.0f}</td>"
        f"<td>${r['trad_balance']:,.0f}</td></tr>"
        for r in projections
    )

    return f"""
    <div style="font-family: Arial; font-size: 12px; max-width: 500px;
                border-left: 3px solid #3b82f6; padding: 10px 14px;
                background: #eff6ff; border-radius: 4px;">
      <strong>Year-by-Year Projection</strong>
      <table style="width: 100%; border-collapse: collapse; margin-top: 6px;">
        <thead><tr style="background: #dbeafe; font-size: 11px;">
          <th>Yr</th><th>Age</th><th>Convert</th><th>Roth</th><th>Trad</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
      <details style="margin-top: 6px;">
        <summary style="cursor: pointer; color: #3b82f6; font-size: 11px;">
          View all {model_years} years
        </summary>
        <table style="width: 100%; border-collapse: collapse; margin-top: 4px;">
          <thead><tr style="background: #dbeafe; font-size: 11px;">
            <th>Yr</th><th>Age</th><th>Convert</th><th>Roth</th><th>Trad</th>
          </tr></thead>
          <tbody>{full_rows}</tbody>
        </table>
      </details>
    </div>
    """
```

---

## 25. Architectural Review Summary

### Review Process

This PRD v2.0 was generated through:

1. **v1.1 PRD** — Existing approved PRD (5 tools, 9 inputs, simplified tax)
2. **Reference Document Analysis** — `koreai-mcp-roth-agent-summary.md` with expanded requirements (7 tools, 17 inputs, IRMAA/RMD/SS)
3. **Brainstorming** — 4 clarifying questions resolved: full tax upgrade, 6 tools (merged), dual conversion input, HTML from all tools
4. **Deep Research** (4 parallel Opus 4.6 sub-agents):
   - `agent-orchestration-multi-agent-optimize` — Pipeline graph, cost analysis, dual-return pattern, tool chaining
   - `ai-agents-architect` — Tool docstrings, system prompt, state architecture, input collection strategy
   - `multi-agent-patterns` — MCP schema for lists, data flow, server-side composition, error handling
   - `agent-orchestration-improve-agent` — Conversation flow, UX for complex inputs, HTML rendering, testing
5. **Consolidation** — Merged all research into unified PRD v2.0

### Key Architectural Contributions Per Agent

| Agent | Key Contribution |
|-------|-----------------|
| multi-agent-optimize | Dual-return pattern (`data` + `display`), 3-way parallel pipeline, projection compaction for GPT context |
| ai-agents-architect | PIPELINE POSITION + KEY DISTINCTION docstring pattern, 5-tier input collection, FieldMeta provenance tracking |
| multi-agent-patterns | Shared computation layer (tools call internal functions), `list[float]` schema handling, client-accumulates state pattern |
| agent-improvement | Quick/Detailed mode conversation flows, collapsible HTML in st.status, per-tool color coding, IRMAA/RMD/SS test suites |

### Reviews Completed

**Backend Architect Review** — APPROVE WITH CONDITIONS
- 18 findings: 4 HIGH, 8 MEDIUM, 6 LOW
- Key fixes applied: removed orphaned `spouse_income`, fixed SS tax impact formula, added missing dataclass fields, defensive unpacking in `update_session_data`

**Senior Architect Review** — APPROVE WITH CONDITIONS
- 16 findings: 2 CRITICAL, 5 HIGH, 5 MEDIUM, 4 LOW
- Key fixes applied: pipeline `**inputs` spread eliminated (CRITICAL), `cost_basis` added to Tool 1 (CRITICAL), breakeven amount fixed to first-year, HTML templates corrected for nested data, optimizer algorithm specified, standard deduction amounts added

### Status

**APPROVED** — All Critical and High issues resolved. Medium/Low items documented for implementation phase.

---

*Document generated from multi-agent deep research using 4 parallel Opus 4.6 agents. Reviewed by Backend Architect and Senior Architect agents. Consolidates expanded requirements from koreai-mcp-roth-agent-summary.md into the existing PRD v1.1 framework.*
