# PRD: Roth Conversion Calculator — MCP Server + Streamlit Chat Agent

**Version:** 1.1 (Final — Post Architectural Review)
**Date:** 2026-03-03
**Status:** Approved with conditions met — Ready for Implementation
**Reviews:** Backend Architect (10 issues addressed) + Senior Architect (3 blockers resolved)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Non-Goals](#3-goals--non-goals)
4. [Target Users & Use Cases](#4-target-users--use-cases)
5. [System Architecture](#5-system-architecture)
6. [Component 1: FastMCP Server](#6-component-1-fastmcp-server)
7. [Component 2: Streamlit Chat Agent](#7-component-2-streamlit-chat-agent)
8. [Agent Orchestration Design](#8-agent-orchestration-design)
9. [MCP Protocol Integration](#9-mcp-protocol-integration)
10. [Tax Calculation Engine](#10-tax-calculation-engine)
11. [User Interface Design](#11-user-interface-design)
12. [Error Handling & Reliability](#12-error-handling--reliability)
13. [Testing Strategy](#13-testing-strategy)
14. [Observability & Logging](#14-observability--logging)
15. [Non-Functional Requirements](#15-non-functional-requirements)
16. [File Structure & Tech Stack](#16-file-structure--tech-stack)
17. [Implementation Phases](#17-implementation-phases)
18. [Decision Log](#18-decision-log)
19. [Risks & Mitigations](#19-risks--mitigations)
20. [Appendix: System Prompt](#20-appendix-system-prompt)

---

## 1. Executive Summary

This PRD defines a two-component system for analyzing Roth IRA conversions:

1. **FastMCP Server** — A Python-based MCP server exposing 5 financial analysis tools via the Model Context Protocol (MCP).
2. **Streamlit Chat Agent** — A chat-based UI that acts as an MCP client, using OpenAI GPT API to orchestrate tool selection, input collection, and response formatting.

The Streamlit Chat Agent replaces Kore.ai MCP Agent (a paid platform) with a free, local alternative that demonstrates the same MCP agent patterns: LLM-driven tool selection, conversational input collection, and rich HTML report rendering.

### Key Architectural Decision

The system uses a **Hybrid Orchestrator-Pipeline** pattern:
- **GPT handles conversation** — input collection, intent classification, response summarization
- **Deterministic pipeline handles computation** — tax calculations, optimization, breakeven analysis run sequentially/in parallel without GPT round-trips
- This reduces GPT API calls from ~12 to ~3 per conversation, cutting cost by ~95%

---

## 2. Problem Statement

A user wants to evaluate whether converting their Traditional IRA to a Roth IRA makes financial sense. This involves:
- Collecting personal financial data (age, income, IRA balance, filing status, state)
- Computing federal + state tax impact of the conversion
- Finding the optimal conversion amount within their tax bracket
- Running a breakeven analysis (how many years until Roth pays off)
- Generating a comprehensive report with recommendations

The original design targeted Kore.ai MCP Agent, which is a paid platform. This project creates an equivalent free, local system using Streamlit + OpenAI GPT + FastMCP.

---

## 3. Goals & Non-Goals

### Goals
- Demonstrate MCP agent patterns (tool discovery, tool calling, LLM orchestration)
- Provide accurate Roth conversion analysis using simplified tax brackets
- Deliver a conversational UX where the LLM collects inputs naturally
- Generate a styled HTML report with tax impact, optimal amounts, and breakeven timeline
- Support configurable GPT model (GPT-4o, GPT-4o-mini, etc.) via environment variable
- Minimize OpenAI API cost for personal/demo use

### Non-Goals
- Production-grade tax engine (no AMT, IRMAA, NIIT, credits, deductions)
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
- Analyze their own Roth conversion scenario
- Explore LLM-based tool orchestration with GPT + FastMCP

### Use Cases

| UC# | Use Case | Flow |
|-----|----------|------|
| UC1 | Full Roth analysis | User provides info → all 5 tools run → HTML report generated |
| UC2 | Quick tax check | User asks "what tax on $50k conversion?" → input collection + tax tool only |
| UC3 | Optimal amount query | User asks "how much should I convert?" → input collection + optimization tool |
| UC4 | What-if scenario | After initial analysis, user changes conversion amount → recalculate |
| UC5 | Comparison | User compares multiple conversion amounts side-by-side |

---

## 5. System Architecture

### High-Level Architecture

```
+===========================================================================+
|                    ROTH CONVERSION CALCULATOR                              |
+===========================================================================+
|                                                                           |
|  +-----------------------+        +-----------------------------------+   |
|  |   STREAMLIT UI        |        |        CONFIGURATION              |   |
|  |                       |        |                                   |   |
|  |  st.chat_input()      |        |  OPENAI_API_KEY = sk-...          |   |
|  |  st.chat_message()    |        |  OPENAI_MODEL = gpt-4o           |   |
|  |  st.html() (reports)  |        |  MCP_TRANSPORT = stdio            |   |
|  |  st.session_state     |        |  MCP_SERVER_CMD = python server.py|   |
|  +-----------+-----------+        +-----------------------------------+   |
|              |                                                            |
|              v  user message                                              |
|  +-----------+-------------------------------+                            |
|  |        ORCHESTRATION CORE                  |                            |
|  |                                            |                            |
|  |  Phase 1: GPT Conversation Loop            |                            |
|  |    GPT extracts entities, collects inputs  |                            |
|  |    GPT calls validate_user_inputs tool        |                            |
|  |                                            |                            |
|  |  Phase 2: Deterministic Pipeline           |                            |
|  |    calculate_tax_impact                     |                            |
|  |    find_optimal + breakeven (parallel)      |                            |
|  |    generate_conversion_report               |                            |
|  |                                            |                            |
|  |  Phase 3: GPT Summary                      |                            |
|  |    GPT summarizes results for user          |                            |
|  |    HTML report rendered in chat             |                            |
|  +-----------+-------------------------------+                            |
|              |                                                            |
|              v  MCP protocol (stdio)                                      |
|  +-----------+-------------------------------+                            |
|  |        FastMCP SERVER (subprocess)         |                            |
|  |                                            |                            |
|  |  Tools:                                    |                            |
|  |  [1] validate_user_inputs                     |                            |
|  |  [2] calculate_tax_impact                   |                            |
|  |  [3] find_optimal_conversion_amount         |                            |
|  |  [4] breakeven_analysis                     |                            |
|  |  [5] generate_conversion_report             |                            |
|  |                                            |                            |
|  |  Shared Modules:                           |                            |
|  |  tax_brackets.py | state_rates.py          |                            |
|  |  html_builder.py | validators.py           |                            |
|  +--------------------------------------------+                            |
+===========================================================================+
```

### Communication Pattern

```
User types message
    |
    v
Streamlit appends to message history
    |
    v
Send messages + tool definitions to OpenAI API
    |
    v
GPT returns: text response OR tool_calls
    |
    +---> [text] → render to user, DONE
    |
    +---> [tool_calls] → execute via MCP stdio
              |
              v
         Tool result fed back to GPT
              |
              v
         GPT processes and responds again (loop)
              |
              v
         Final text/HTML → render to user
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture pattern | Hybrid Orchestrator-Pipeline | GPT for conversation, deterministic pipeline for computation. Optimal cost/reliability balance. |
| Agent pattern | Guided Tool-Use Loop | Standard OpenAI function calling loop with system prompt guidance. Not enough complexity for Plan-and-Execute. |
| Number of LLM agents | 1 (single GPT instance) | 5 tools is well within single-context capacity. Multi-agent adds overhead without benefit. |
| MCP transport | stdio (subprocess) | Single user, localhost. Lowest latency, simplest config. |
| Tool count | 5 (merged from original 6) | Combined `collect_roth_inputs` + `collect_account_details` into `validate_user_inputs`. Saves one GPT round-trip. |
| State management | Implicit in GPT message history + `st.session_state` | No server-side sessions. Stateless tools. |
| Input collection | Conversational-first, Streamlit form fallback | Natural UX. GPT extracts values from free text. Native Streamlit forms for 3+ missing fields. |
| HTML rendering | `st.html()` for reports only; native Streamlit forms for input | HTML forms in iframes can't communicate back to Streamlit. Native forms integrate properly. |
| Tool choice | `tool_choice: "auto"` | Allows GPT to respond conversationally when no tool is needed. |
| Parallel tool calls | Disabled at GPT level; parallel at pipeline level | Sequential GPT calls avoid misordering. Pipeline-level parallelism for compute tools. |

---

## 6. Component 1: FastMCP Server

### 6.1 Tool Inventory (5 Tools)

| # | Tool | Purpose | Input | Output |
|---|------|---------|-------|--------|
| 1 | `validate_user_inputs` | Collect all user financial data | age, income, ira_balance, filing_status, state, roth_balance, 401k_balance, cost_basis, conversion_amount | JSON: missing fields list OR confirmed data |
| 2 | `calculate_tax_impact` | Federal + state tax on conversion | annual_income, conversion_amount, filing_status, state | JSON: federal_tax, state_tax, total_tax, effective_rate, marginal_rate |
| 3 | `find_optimal_conversion_amount` | Best amount within tax bracket | annual_income, filing_status, ira_balance, state | JSON: optimal_amount, bracket_info, tax_at_optimal |
| 4 | `breakeven_analysis` | Years until Roth pays off | conversion_amount, total_tax, age, expected_return (0.07), retirement_age (65), tax_rate_in_retirement | JSON: breakeven_years, years_to_retirement, projected_values |
| 5 | `generate_conversion_report` | Final styled HTML report | All inputs + all calculation results | HTML: complete report document |

### 6.2 Tool Dependency Graph

```
validate_user_inputs
       |
       v
calculate_tax_impact
       |
       +---> find_optimal_conversion_amount --+
       |                                       |
       +---> breakeven_analysis ---------------+
                                               |
                                               v
                                  generate_conversion_report
```

- `find_optimal_conversion_amount` and `breakeven_analysis` CAN run in parallel after `calculate_tax_impact`
- `generate_conversion_report` requires ALL prior results (gracefully handles missing sections)

### 6.3 Tool Specifications

#### Tool 1: `validate_user_inputs`

```python
@mcp.tool()
def validate_user_inputs(
    age: int = None,
    annual_income: float = None,
    ira_balance: float = None,
    filing_status: str = None,
    state: str = None,
    roth_balance: float = None,
    balance_401k: float = None,
    cost_basis: float = None,
    conversion_amount: float = None,
) -> str:
    """
    WHEN TO USE: Call this FIRST when starting a new Roth conversion analysis.
    Collects ALL financial inputs needed for the analysis.

    WHAT IT NEEDS: age, annual_income (gross), ira_balance (Traditional IRA),
    filing_status (single/married_joint/married_separate/head_of_household),
    state (2-letter code), roth_balance, balance_401k, cost_basis, conversion_amount.

    RETURNS: JSON with {"status": "missing_inputs", "missing": [...]} if fields
    are incomplete, or {"status": "complete", "inputs": {...}} when all required
    fields are present.

    DO NOT USE FOR: Any calculation or report generation.
    """
```

**Required fields**: age, annual_income, ira_balance, filing_status, state
**Optional fields** (smart defaults): roth_balance (0), balance_401k (0), cost_basis (0), conversion_amount (ira_balance)

**Validation rules**:
- age: integer, 18-100
- annual_income: float, >= 0
- ira_balance: float, >= 0
- filing_status: enum [single, married_joint, married_separate, head_of_household]
- state: valid 2-letter US state code
- conversion_amount: float, > 0, <= ira_balance

#### Tool 2: `calculate_tax_impact`

```python
@mcp.tool()
def calculate_tax_impact(
    annual_income: float,
    conversion_amount: float,
    filing_status: str,
    state: str,
    cost_basis: float = 0
) -> str:
    """
    WHEN TO USE: After validate_user_inputs has gathered user data.
    Calculate federal and state tax impact of converting a specific amount.

    WHAT IT NEEDS: annual_income, conversion_amount, filing_status, state.
    Optional: cost_basis (reduces taxable portion).

    RETURNS: JSON with federal_tax, state_tax, total_tax, effective_rate,
    marginal_rate, bracket_before, bracket_after.

    DO NOT USE FOR: Finding optimal amounts (use find_optimal_conversion_amount).
    """
```

**Calculation logic**:
1. Taxable conversion = conversion_amount - cost_basis
2. Total taxable income = annual_income + taxable_conversion
3. Apply 2024/2025 federal brackets for filing_status
4. Federal tax = tax on (total_taxable) - tax on (annual_income alone)
5. State tax = taxable_conversion * flat_state_rate
6. Return breakdown

#### Tool 3: `find_optimal_conversion_amount`

```python
@mcp.tool()
def find_optimal_conversion_amount(
    annual_income: float,
    filing_status: str,
    ira_balance: float,
    state: str
) -> str:
    """
    WHEN TO USE: When user asks "how much should I convert?" or wants bracket optimization.
    Finds the amount that stays within the current tax bracket or minimizes tax burden.

    RETURNS: JSON with optimal_amount, current_bracket, next_bracket_threshold,
    room_in_bracket, tax_at_optimal, marginal_rate_if_exceeded.
    """
```

**Algorithm**: Find the gap between current income and next bracket threshold. The optimal amount = next_bracket_threshold - annual_income. Also calculate "fill the bracket" for the bracket above.

#### Tool 4: `breakeven_analysis`

```python
@mcp.tool()
def breakeven_analysis(
    conversion_amount: float,
    total_tax: float,
    age: int,
    expected_return: float = 0.07,
    retirement_age: int = 65,
    tax_rate_in_retirement: float = None,
    filing_status: str = "single"
) -> str:
    """
    WHEN TO USE: When user asks "is it worth it?" or "how long until it pays off?"
    Calculates breakeven period comparing Roth vs. Traditional IRA growth.

    WHAT IT NEEDS: conversion_amount, total_tax (from calculate_tax_impact),
    age (current), expected_return (default 7%), retirement_age (default 65),
    tax_rate_in_retirement (estimated from income if not provided).

    RETURNS: JSON with breakeven_years, years_to_retirement, yearly_projections (list),
    roth_value_at_breakeven, traditional_value_at_breakeven.

    DO NOT USE FOR: Calculating tax amounts (use calculate_tax_impact).
    """
```

**Assumptions**:
- Default retirement age: 65 (configurable)
- Default expected return: 7% nominal (configurable)
- If `tax_rate_in_retirement` not provided, estimated at 15% (typical for moderate retirement income)

**Model**: Compare year-over-year:
- Roth path: (conversion_amount - total_tax) * (1 + return)^n (tax-free withdrawals)
- Traditional path: conversion_amount * (1 + return)^n * (1 - retirement_tax_rate)
- Breakeven = year when Roth path >= Traditional path

#### Tool 5: `generate_conversion_report`

```python
@mcp.tool()
def generate_conversion_report(
    # User profile fields
    age: int,
    annual_income: float,
    ira_balance: float,
    filing_status: str,
    state: str,
    conversion_amount: float,
    roth_balance: float = 0,
    balance_401k: float = 0,
    cost_basis: float = 0,
    # Tax analysis results
    federal_tax: float = None,
    state_tax: float = None,
    total_tax: float = None,
    effective_rate: float = None,
    marginal_rate: float = None,
    # Optimal conversion results (optional)
    optimal_amount: float = None,
    room_in_bracket: float = None,
    # Breakeven results (optional)
    breakeven_years: int = None,
) -> str:
    """
    WHEN TO USE: LAST tool in the workflow. Call only after running calculations.

    WHAT IT NEEDS: All user profile fields plus calculation results from
    calculate_tax_impact (federal_tax, state_tax, total_tax, effective_rate).
    Optional: results from find_optimal and breakeven tools.

    RETURNS: Complete styled HTML report with sections for: User Profile,
    Tax Impact Summary, Optimal Conversion Analysis, Breakeven Timeline,
    Recommendations, and Disclaimer.

    Handles missing sections gracefully — if optimal or breakeven
    data is absent (None), generates report without those sections.

    DO NOT USE FOR: Any calculations. This tool only formats/renders data.
    """
```

> **Note:** This tool uses flat parameters (not JSON strings) for type safety and schema documentation. Since it's primarily called from the deterministic pipeline, the pipeline passes values directly. When called by GPT, GPT extracts values from prior tool results.

**Report sections**:
1. Header with user profile summary
2. Tax Impact table (federal, state, total, effective rate)
3. Optimal Conversion section (bracket analysis, recommendation)
4. Breakeven Timeline (year-by-year projection table, summary)
5. Recommendations (based on age, bracket headroom, breakeven period)
6. Disclaimer ("For educational purposes only...")
7. Styled with inline CSS (dark/light theme support)

### 6.4 Shared Modules

#### `tax_brackets.py`
- 2024/2025 federal tax brackets for all filing statuses
- Data structure: dict mapping filing_status → list of (threshold, rate) tuples
- Function: `compute_federal_tax(taxable_income, filing_status) → float`
- Function: `get_bracket_info(taxable_income, filing_status) → dict`

#### `state_rates.py`
- Flat effective state income tax rates for all 50 states + DC
- No-income-tax states (TX, FL, NV, WA, WY, SD, AK, NH, TN): rate = 0
- High-tax states (CA: 9.3%, NY: 6.85%, NJ: 6.37%, etc.)
- Function: `get_state_tax(taxable_amount, state) → float`

#### `html_builder.py`
- `build_report_html(data: dict) → str` — full styled report
- Inline CSS with responsive design
- Table formatting for tax breakdowns and projections
- Color-coded recommendations (green/yellow/red)

#### `validators.py`
- `validate_age(age) → (bool, str)`
- `validate_income(income) → (bool, str)`
- `validate_filing_status(status) → (bool, str)`
- `validate_state(state) → (bool, str)`
- `validate_conversion_amount(amount, ira_balance) → (bool, str)`
- Returns structured error: `{"error": True, "field": "age", "message": "Age must be 18-100"}`

---

## 7. Component 2: Streamlit Chat Agent

### 7.1 Page Layout

```
+-----------------------------------------------------------------------+
|  [Roth Conversion Advisor]                                    [⚙️]    |
+-------------------+---------------------------------------------------+
|                   |                                                   |
|  SIDEBAR          |              MAIN CHAT AREA                       |
|                   |                                                   |
|  Your Info        |  [Bot] Welcome! I can help you analyze a Roth    |
|  ─────────        |        IRA conversion. What's your situation?     |
|  Age: 55          |                                                   |
|  Income: $150,000 |  [User] I'm 55, married filing jointly, make     |
|  IRA: $500,000    |         $150k, have $500k in my Traditional IRA, |
|  Status: MFJ      |         live in California.                       |
|  State: CA        |                                                   |
|                   |  [Bot] Great! Let me also ask — do you have an   |
|  Calculations     |        existing Roth IRA or 401k?                  |
|  ─────────        |                                                   |
|  Tax Impact: ...  |  [User] No Roth, no 401k, all pre-tax.           |
|  Optimal: ...     |                                                   |
|                   |  [Bot] ⏳ Running your analysis...                 |
|  API Usage        |        ✅ Tax impact calculated                    |
|  ─────────        |        ✅ Optimal conversion found                 |
|  Tokens: 2,340    |        ✅ Breakeven analysis complete              |
|  Cost: ~$0.004    |                                                   |
|                   |  [Bot] Here's your complete analysis:              |
|  [Start Over]     |        +================================+         |
|                   |        | ROTH CONVERSION REPORT        |         |
|                   |        | ... styled HTML report ...     |         |
|                   |        +================================+         |
|                   |                                                   |
|                   |  [📥 Download HTML] [📥 Download PDF]             |
|                   |                                                   |
|                   |  +-------------------------------------------+   |
|                   |  | Ask about Roth conversions...       [Send] |   |
|                   |  +-------------------------------------------+   |
+-------------------+---------------------------------------------------+
```

### 7.2 Data Models (`models.py`)

```python
from dataclasses import dataclass, field

@dataclass
class UserProfile:
    age: int | None = None
    annual_income: float | None = None
    ira_balance: float | None = None
    filing_status: str | None = None
    state: str | None = None
    roth_balance: float = 0
    balance_401k: float = 0
    cost_basis: float = 0
    conversion_amount: float | None = None

@dataclass
class CalculationResults:
    tax_impact: dict | None = None
    optimal_amount: dict | None = None
    breakeven: dict | None = None

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
        return (self.total_prompt_tokens * 2.50 / 1_000_000 +
                self.total_completion_tokens * 10.00 / 1_000_000)
```

### 7.3 Session State Structure

```python
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []  # OpenAI message history
    if "profile" not in st.session_state:
        st.session_state.profile = UserProfile()
    if "results" not in st.session_state:
        st.session_state.results = CalculationResults()
    if "collected_data" not in st.session_state:
        # Flat dict mirror of UserProfile for quick access
        st.session_state.collected_data = {
            "age": None, "annual_income": None, "ira_balance": None,
            "filing_status": None, "state": None, "roth_balance": None,
            "balance_401k": None, "cost_basis": None, "conversion_amount": None,
        }
    if "calculation_results" not in st.session_state:
        st.session_state.calculation_results = {
            "tax_impact": None, "optimal_amount": None, "breakeven": None,
        }
    if "tools_called" not in st.session_state:
        st.session_state.tools_called = []
    if "report_html" not in st.session_state:
        st.session_state.report_html = None
    if "token_data" not in st.session_state:
        # Store raw data (not class instance) for Streamlit serialization safety
        st.session_state.token_data = {"prompt_tokens": 0, "completion_tokens": 0, "calls": []}
```

### 7.3 Sidebar Features

1. **Your Information** — Live display of all collected inputs (updates after each tool call)
2. **Calculation Results** — Summary metrics after calculations run
3. **API Usage** — Token count and estimated cost (transparency)
4. **Start Over** — Resets all session state
5. **Model Config** — Shows current model name (read from env)

### 7.4 Chat Message Rendering

```python
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue  # Never render system messages
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant" and msg.get("content"):
        with st.chat_message("assistant"):
            if msg.get("has_html"):
                st.markdown(msg["text_part"])
                st.html(msg["html_part"])
            else:
                st.markdown(msg["content"])
    # tool messages not rendered directly
```

---

## 8. Agent Orchestration Design

### 8.1 Pattern: Guided Tool-Use Loop (Hybrid Orchestrator-Pipeline)

The agent operates in three phases per user conversation:

**Phase 1: GPT Conversation Loop (input collection)**
- GPT receives user message, extracts entities, calls `validate_user_inputs`
- If inputs missing, GPT asks conversationally (1-2 fields) or renders Streamlit form (3+ fields)
- Loop continues until all required inputs are confirmed
- Typically 1-3 GPT API calls

**Phase 2: Deterministic Pipeline (computation)**
- Once inputs confirmed, Streamlit runs calculations directly (no GPT involvement):
  1. `calculate_tax_impact` → result
  2. `find_optimal_conversion_amount` + `breakeven_analysis` → run in parallel
  3. `generate_conversion_report` with all results
- Zero GPT API calls in this phase

**Phase 3: GPT Summary (presentation)**
- Feed all pipeline results to GPT
- GPT generates a conversational summary
- HTML report rendered separately via `st.html()`
- 1 GPT API call

### 8.2 Agent Loop Implementation

```python
async def agent_loop(user_message: str, mcp_session: ClientSession):
    messages = st.session_state.messages
    messages.append({"role": "user", "content": user_message})

    # Inject context into system message
    messages[0] = build_system_message(
        st.session_state.collected_data,
        st.session_state.tools_called
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
        )

        assistant_msg = response.choices[0].message
        messages.append(assistant_msg.to_dict())
        st.session_state.token_tracker.record(response)

        if not assistant_msg.tool_calls:
            return assistant_msg.content, html_outputs

        # Phase 1: Process ALL tool calls first (preserve OpenAI message ordering)
        inputs_just_completed = False
        for tool_call in assistant_msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            result = await call_mcp_tool(mcp_session, name, args)

            update_session_data(name, args, result)
            st.session_state.tools_called.append(name)

            # Append tool result IMMEDIATELY after processing (required by OpenAI API)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": compact_result(name, result),
            })

            if name == "validate_user_inputs" and is_inputs_complete(result):
                inputs_just_completed = True

        # Phase 2: AFTER all tool results appended, check if pipeline should run
        if inputs_just_completed:
            pipeline_results = await run_analysis_pipeline(mcp_session)
            html_outputs.append(pipeline_results.get("report_html", ""))
            # Inject pipeline summary as a user message for GPT to summarize
            messages.append({
                "role": "user",
                "content": format_pipeline_summary(pipeline_results),
            })

        iteration += 1

    return "I've processed several steps. Could you clarify what you'd like next?", html_outputs
```

### 8.3 Deterministic Pipeline

```python
async def run_analysis_pipeline(mcp_session: ClientSession) -> dict:
    inputs = st.session_state.collected_data
    results = {}

    # Step 1: Tax impact (required)
    tax_result = await mcp_session.call_tool("calculate_tax_impact", {
        "annual_income": inputs["annual_income"],
        "conversion_amount": inputs["conversion_amount"],
        "filing_status": inputs["filing_status"],
        "state": inputs["state"],
        "cost_basis": inputs.get("cost_basis", 0),
    })
    results["tax_impact"] = json.loads(tax_result)

    # Step 2: Optimal + Breakeven IN PARALLEL
    optimal_task = asyncio.create_task(
        mcp_session.call_tool("find_optimal_conversion_amount", {...})
    )
    breakeven_task = asyncio.create_task(
        mcp_session.call_tool("breakeven_analysis", {...})
    )
    optimal_result, breakeven_result = await asyncio.gather(
        optimal_task, breakeven_task, return_exceptions=True
    )

    # Handle partial failures gracefully
    if not isinstance(optimal_result, Exception):
        results["optimal_conversion"] = json.loads(optimal_result)
    if not isinstance(breakeven_result, Exception):
        results["breakeven"] = json.loads(breakeven_result)

    # Step 3: Generate report with whatever we have
    report_result = await mcp_session.call_tool("generate_conversion_report", {
        "user_profile": json.dumps(inputs),
        "tax_analysis": json.dumps(results.get("tax_impact", {})),
        "optimal_conversion": json.dumps(results.get("optimal_conversion", {})),
        "breakeven": json.dumps(results.get("breakeven", {})),
    })
    results["report_html"] = report_result

    return results
```

### 8.4 Helper Function Specifications

These functions are called in the agent loop and must be implemented:

```python
def is_inputs_complete(tool_result: str) -> bool:
    """Check if validate_user_inputs returned all required fields."""
    try:
        data = json.loads(tool_result)
        return data.get("status") == "complete"
    except json.JSONDecodeError:
        return False

def update_session_data(tool_name: str, args: dict, result: str):
    """Merge tool results into session state. Non-None values only."""
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return  # HTML or non-JSON result, skip

    if tool_name == "validate_user_inputs" and data.get("status") == "complete":
        for k, v in data.get("inputs", {}).items():
            if v is not None:
                st.session_state.collected_data[k] = v
    elif tool_name == "calculate_tax_impact":
        st.session_state.calculation_results["tax_impact"] = data
    elif tool_name == "find_optimal_conversion_amount":
        st.session_state.calculation_results["optimal_amount"] = data
    elif tool_name == "breakeven_analysis":
        st.session_state.calculation_results["breakeven"] = data

def compact_result(tool_name: str, result: str) -> str:
    """Compress tool results for GPT context window efficiency."""
    if tool_name == "validate_user_inputs":
        try:
            data = json.loads(result)
            if data["status"] == "complete":
                return f"Inputs confirmed: {', '.join(data['inputs'].keys())}"
        except (json.JSONDecodeError, KeyError):
            pass
        return result  # Keep missing-fields response as-is
    elif tool_name == "generate_conversion_report":
        return "[HTML report rendered to user]"
    return result  # Keep calculation JSON for GPT summary

def format_pipeline_summary(pipeline_results: dict) -> str:
    """Format pipeline results as a user message for GPT to summarize."""
    parts = ["[System: Analysis pipeline completed. Results below:]"]
    if "tax_impact" in pipeline_results:
        tax = pipeline_results["tax_impact"]
        parts.append(f"Tax Impact: {json.dumps(tax)}")
    if "optimal_conversion" in pipeline_results:
        parts.append(f"Optimal Conversion: {json.dumps(pipeline_results['optimal_conversion'])}")
    if "breakeven" in pipeline_results:
        parts.append(f"Breakeven: {json.dumps(pipeline_results['breakeven'])}")
    parts.append("HTML report has been rendered to the user.")
    parts.append("Please summarize these results conversationally.")
    return "\n".join(parts)
```

### 8.5 Context Window Management

**Strategy: Compact tool results after summarization**

| Content | Action |
|---------|--------|
| System prompt | Always present (~400 tokens) |
| Confirmed inputs | Injected as context summary in system message |
| Collection tool results | Compacted to `"Inputs confirmed: {field_list}"` |
| Calculation JSON results | Kept (needed for GPT to summarize) |
| HTML report | Replaced with `"[HTML report rendered to user]"` |
| Old conversation turns | Trimmed at 100 messages (safety cap) |

**Token budget per conversation** (estimated):
- System prompt: ~400 tokens
- User messages (5-8 turns): ~500 tokens
- Tool definitions (5 tools): ~600 tokens
- Tool results (compacted): ~1,000 tokens
- **Total: ~2,500 tokens per GPT call** (well within 128k context)

### 8.5 Tool Description Optimization

Each tool description follows the **WHEN/WHAT/RETURNS/DO NOT USE** pattern to maximize GPT routing accuracy:

```
WHEN TO USE: [specific trigger conditions]
WHAT IT NEEDS: [parameter list with descriptions]
RETURNS: [exact output structure]
DO NOT USE FOR: [negative boundary — what this tool does NOT handle]
```

The "DO NOT USE FOR" line is critical for preventing GPT misrouting between similar tools.

### 8.6 Few-Shot Disambiguation (in System Prompt)

Three examples targeting the top ambiguity patterns:

1. **Ambiguous start**: "I want to convert my IRA" → call `validate_user_inputs` (not calculate)
2. **Partial info upfront**: "I'm 55, make $120k" → call `validate_user_inputs(age=55, annual_income=120000)` (extract what's given)
3. **Direct calculation request without inputs**: "What tax on $50k conversion?" → call `validate_user_inputs` first (not `calculate_tax_impact`)

---

## 9. MCP Protocol Integration

### 9.1 Transport: stdio

The FastMCP server runs as a subprocess of the Streamlit app, communicating via stdin/stdout pipes.

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        # session ready for tool calls
```

**Why stdio over SSE**: Single user, localhost, no network overhead, simplest configuration. Upgrade to SSE later if multi-client support is needed (no tool/business logic changes required).

### 9.2 Schema Translation: MCP → OpenAI

MCP tool schemas and OpenAI function schemas both use JSON Schema, with different envelope formats:

```python
def mcp_tool_to_openai_function(mcp_tool) -> dict:
    """Convert MCP tool definition to OpenAI function calling format."""
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": TOOL_DESCRIPTIONS.get(mcp_tool.name, mcp_tool.description),
            "parameters": mcp_tool.inputSchema or {"type": "object", "properties": {}},
        },
    }

async def discover_tools(session: ClientSession) -> list[dict]:
    tools_response = await session.list_tools()
    return [mcp_tool_to_openai_function(t) for t in tools_response.tools]
```

Tool descriptions may be overridden with GPT-optimized versions (richer "WHEN TO USE" / "DO NOT USE FOR" structure) while the parameter schemas come directly from MCP.

### 9.3 Session Lifecycle

**Persistent MCP session via `@st.cache_resource`.** The MCP subprocess and session are created once and reused across Streamlit reruns. This avoids spawning a new Python subprocess per user message (~300-500ms overhead per spawn on Windows).

```python
import nest_asyncio
nest_asyncio.apply()  # REQUIRED: Streamlit's Tornado event loop conflicts with asyncio.run()

@st.cache_resource
def get_mcp_session():
    """Spawn MCP server subprocess once, persist across Streamlit reruns."""
    import asyncio
    loop = asyncio.new_event_loop()

    async def _init():
        server_params = StdioServerParameters(
            command="python", args=["mcp_server.py"],
        )
        transport = await stdio_client(server_params).__aenter__()
        read, write = transport
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()
        return session

    return loop.run_until_complete(_init()), loop

# Usage in message handler:
session, loop = get_mcp_session()

def run_async(coro):
    """Bridge async MCP/OpenAI calls into Streamlit's sync execution."""
    return asyncio.run_coroutine_threadsafe(coro, loop).result(timeout=60)
```

> **Why persistent:** On Windows, subprocess creation costs ~300-500ms. Over 5-8 conversation turns, per-request sessions waste 1.5-4 seconds. The MCP server is stateless, so a persistent connection is safe. Only recreate on crash (via `ResilientToolExecutor`).

---

## 10. Tax Calculation Engine

### 10.1 Federal Tax Brackets (2024)

| Filing Status | Bracket | Rate |
|---------------|---------|------|
| Single | $0 - $11,600 | 10% |
| Single | $11,601 - $47,150 | 12% |
| Single | $47,151 - $100,525 | 22% |
| Single | $100,526 - $191,950 | 24% |
| Single | $191,951 - $243,725 | 32% |
| Single | $243,726 - $609,350 | 35% |
| Single | $609,351+ | 37% |

(Similar tables for married_joint, married_separate, head_of_household)

### 10.2 State Tax Rates (Simplified Flat Rates)

| State | Effective Rate | Notes |
|-------|---------------|-------|
| CA | 9.30% | Highest marginal |
| NY | 6.85% | |
| NJ | 6.37% | |
| IL | 4.95% | Flat rate |
| PA | 3.07% | Flat rate |
| MA | 5.00% | Flat rate |
| TX, FL, NV, WA, WY, SD, AK | 0.00% | No income tax |
| NH, TN | 0.00% | No income tax (wages) |
| ... | ... | All 50 states + DC covered |

### 10.3 Calculation Assumptions

- Standard deduction applied (not itemized)
- No AMT, NIIT, or IRMAA calculations
- State taxes use flat effective rate (not progressive brackets)
- Expected investment return default: 7% nominal
- Retirement tax rate: estimated from projected retirement income if not provided
- All IRA contributions assumed pre-tax unless cost_basis specified
- Disclaimer: "For educational purposes only. Consult a tax professional."

---

## 11. User Interface Design

### 11.1 Conversation Flow — Happy Path

```
Bot:  Welcome! I'm your Roth Conversion Advisor. I can help you analyze
      whether converting your Traditional IRA to a Roth IRA makes sense.

      Tell me about yourself — your age, income, IRA balance, filing
      status, and state to get started.

User: I'm 55, married filing jointly, make $150k, have $500k in my
      Traditional IRA, and live in California.

Bot:  Got it! A couple more questions:
      • Do you have an existing Roth IRA balance?
      • Do you have a 401(k)?
      • Is your entire IRA balance pre-tax, or do you have after-tax
        (cost basis) contributions?

User: No Roth, no 401k, all pre-tax.

Bot:  Perfect. Let me run your analysis now...

      ⏳ Calculating tax impact...
      ✅ Tax impact: $42,800 total tax on full $500K conversion

      ⏳ Finding optimal conversion amount...
      ✅ Optimal: $41,950 stays within the 24% bracket

      ⏳ Running breakeven analysis...
      ✅ Breakeven: ~8 years (age 63)

      Here's your complete Roth Conversion Report:

      ╔══════════════════════════════════════╗
      ║     ROTH CONVERSION ANALYSIS         ║
      ║     [Full styled HTML report]        ║
      ╚══════════════════════════════════════╝

      Key takeaways:
      • Converting the full $500K would cost ~$42,800 in taxes this year
      • The sweet spot is converting ~$42K to stay in the 24% bracket
      • The conversion pays for itself in about 8 years (by age 63)

      Would you like to explore a different conversion amount?

User: What if I convert $100k instead?

Bot:  Let me recalculate with $100K...
      [Re-runs calculate_tax_impact + breakeven with new amount]
```

### 11.2 Input Collection Strategy

| Missing Fields | Strategy |
|---------------|----------|
| 1-2 fields | GPT asks conversationally |
| 3+ fields | Render native Streamlit form |
| 0 fields | Proceed to calculation |

```python
def render_input_form(missing_fields: list):
    with st.form("roth_inputs"):
        values = {}
        if "age" in missing_fields:
            values["age"] = st.number_input("Age", 18, 100, 55)
        if "annual_income" in missing_fields:
            values["annual_income"] = st.number_input("Annual Income ($)", 0, 10000000, 100000)
        if "filing_status" in missing_fields:
            values["filing_status"] = st.selectbox("Filing Status", [
                "single", "married_joint", "married_separate", "head_of_household"
            ])
        if "state" in missing_fields:
            values["state"] = st.selectbox("State", US_STATES)
        if "ira_balance" in missing_fields:
            values["ira_balance"] = st.number_input("Traditional IRA Balance ($)", 0, 100000000, 500000)
        submitted = st.form_submit_button("Submit")
        if submitted:
            return values
    return None
```

### 11.3 Report Rendering

The HTML report from `generate_conversion_report` is rendered via `st.html()` (Streamlit 1.33+):

```python
if report_html:
    # Use st.components.v1.html for explicit height control (reports may exceed default)
    import streamlit.components.v1 as components
    components.html(report_html, height=800, scrolling=True)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download HTML", report_html, "roth_report.html", "text/html")
    with col2:
        # PDF export (post-MVP)
        pass
```

### 11.4 Progress Indicators

During the deterministic pipeline phase, show live progress:

```python
with st.status("Running your Roth conversion analysis...", expanded=True) as status:
    st.write("Calculating tax impact...")
    tax_result = await call_tool("calculate_tax_impact", ...)
    st.write(f"✅ Federal tax: ${tax_result['federal_tax']:,.0f} | State tax: ${tax_result['state_tax']:,.0f}")

    st.write("Finding optimal conversion amount...")
    optimal, breakeven = await asyncio.gather(...)
    st.write(f"✅ Optimal: ${optimal['optimal_amount']:,.0f}")
    st.write(f"✅ Breakeven: ~{breakeven['breakeven_years']} years")

    st.write("Generating report...")
    report = await call_tool("generate_conversion_report", ...)
    status.update(label="Analysis complete!", state="complete")
```

---

## 12. Error Handling & Reliability

### 12.1 Error Taxonomy

| Error Type | Detection | Recovery | Max Retries |
|-----------|-----------|----------|-------------|
| Tool validation error | Tool returns `{"error": true, "field": ...}` | GPT explains error, asks for correction | Unlimited (user-driven) |
| Tool execution exception | try/except in tool call wrapper | Retry once, then show error | 1 |
| MCP server crash | ConnectionError / BrokenPipeError | Restart subprocess, retry | 2 |
| GPT malformed tool call | JSON parse error on arguments | Re-prompt GPT | 2 |
| GPT hallucinated tool name | tool_name not in known_tools | Ignore, re-prompt | 1 |
| OpenAI rate limit | HTTP 429 | Exponential backoff | 3 |
| OpenAI API down | HTTP 5xx | Fail fast, show error message | 0 |
| Pipeline partial failure | Exception in one tool | Generate report with available data | 1 |

### 12.2 Dual-Layer Input Validation

**Layer 1: GPT pre-validation (soft)** — System prompt instructs GPT to sanity-check values before calling tools. Catches ~90% of obvious errors.

**Layer 2: Tool validation (hard, authoritative)** — Every tool validates its inputs in Python code. Returns structured errors:
```json
{"error": true, "field": "age", "message": "Age must be between 18 and 100", "received": 150}
```

### 12.3 Anti-Hallucination Guardrail (Critical)

GPT must NEVER compute tax amounts itself. This is the highest-risk failure mode.

**Prevention**:
1. System prompt rule (top priority, first rule): "NEVER perform tax calculations yourself. ALL tax calculations MUST go through tools."
2. Post-processing check in Streamlit: scan GPT responses for dollar amounts/percentages not present in any tool result. Log warning if detected.

```python
def check_hallucinated_numbers(gpt_response: str, tool_results: list[str]) -> bool:
    """Returns True if GPT appears to have invented financial numbers."""
    import re
    amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', gpt_response)
    all_tool_text = " ".join(str(r) for r in tool_results)
    return any(amt not in all_tool_text for amt in amounts)
```

### 12.4 Resilient Tool Executor

```python
class ResilientToolExecutor:
    def __init__(self, session, max_retries=2):
        self.session = session
        self.max_retries = max_retries

    async def call_tool(self, name: str, args: dict) -> dict:
        for attempt in range(self.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self.session.call_tool(name, args), timeout=10.0
                )
                if isinstance(result, dict) and "error" in result:
                    return {"status": "validation_error", "error": result["error"]}
                return {"status": "success", "data": result}
            except (ConnectionError, BrokenPipeError):
                if attempt < self.max_retries:
                    await self._restart_session()
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
        return {"status": "fatal_error", "error": f"{name} failed after {self.max_retries} retries"}
```

### 12.5 Graceful Degradation

| Failure | Degraded Behavior |
|---------|------------------|
| OpenAI API down | Show static input form, bypass GPT, call MCP tools directly |
| MCP server down | Show "calculation service unavailable" + retry button |
| Partial pipeline failure | Generate report with available sections, note missing analysis |
| Context overflow | Trim old messages, keep system prompt + confirmed inputs + recent turns |

---

## 13. Testing Strategy

### 13.1 Test Pyramid

```
            +------------------+
           /   E2E Tests (5%)  \
          /  Full conversation  \
         /   flows with real    \
        /     API calls          \
       +------------------------+
      /  Integration Tests (20%) \
     /  Streamlit ↔ MCP roundtrip \
    /   Tool chain execution       \
   +------------------------------+
  /     Unit Tests (75%)           \
 /  Tax calculations, validators,  \
/   tool logic, schema conversion   \
+-----------------------------------+
```

### 13.2 Unit Tests (75% of test effort)

**MCP tool tests** — Pure Python, no GPT dependency:
```python
def test_calculate_tax_impact_single_filer():
    result = calculate_tax_impact(100000, 50000, "single", "CA")
    data = json.loads(result)
    assert data["federal_tax"] > 0
    assert data["state_tax"] == 50000 * 0.093  # CA rate
    assert data["effective_rate"] > 0

def test_calculate_tax_no_income_tax_state():
    result = calculate_tax_impact(100000, 50000, "single", "TX")
    data = json.loads(result)
    assert data["state_tax"] == 0

def test_validate_user_inputs_missing_fields():
    result = validate_user_inputs(age=55, annual_income=150000)
    data = json.loads(result)
    assert data["status"] == "missing_inputs"
    assert "filing_status" in data["missing"]

def test_breakeven_analysis_basic():
    result = breakeven_analysis(50000, 12000, 55, 0.07)
    data = json.loads(result)
    assert data["breakeven_years"] > 0
    assert data["breakeven_years"] < 50  # Sanity check
```

**Tax engine tests**:
```python
def test_federal_brackets_2024_single():
    assert compute_federal_tax(50000, "single") == pytest.approx(6307.50, abs=1)

def test_federal_brackets_2024_married_joint():
    assert compute_federal_tax(100000, "married_joint") == pytest.approx(11788, abs=1)
```

**Schema translation tests**:
```python
def test_mcp_to_openai_schema_conversion():
    mcp_tool = MockMCPTool(name="test", description="test tool", inputSchema={...})
    result = mcp_tool_to_openai_function(mcp_tool)
    assert result["type"] == "function"
    assert result["function"]["name"] == "test"
```

**Orchestrator helper function tests** (`test_orchestrator.py`):
```python
def test_is_inputs_complete_all_present():
    result = '{"status": "complete", "inputs": {"age": 55, "income": 150000}}'
    assert is_inputs_complete(result) == True

def test_is_inputs_complete_missing():
    result = '{"status": "missing_inputs", "missing": ["filing_status"]}'
    assert is_inputs_complete(result) == False

def test_compact_result_report_replaces_html():
    html = "<html><body>Big report...</body></html>"
    assert compact_result("generate_conversion_report", html) == "[HTML report rendered to user]"

def test_compact_result_keeps_calculation_json():
    json_result = '{"federal_tax": 12000, "state_tax": 4000}'
    assert compact_result("calculate_tax_impact", json_result) == json_result

def test_update_session_data_merges_inputs():
    # Verify non-None values are merged, None values don't overwrite
    ...

def test_format_pipeline_summary_includes_all_sections():
    results = {"tax_impact": {...}, "optimal_conversion": {...}, "breakeven": {...}}
    summary = format_pipeline_summary(results)
    assert "Tax Impact" in summary
    assert "Optimal Conversion" in summary
```

### 13.3 Integration Tests (20%)

**MCP roundtrip**: Start FastMCP server, call tools via MCP protocol, verify responses.

```python
@pytest.fixture(scope="session")
def mcp_server():
    proc = subprocess.Popen(["python", "mcp_server.py"], ...)
    yield proc
    proc.terminate()

async def test_mcp_roundtrip_calculate_tax(mcp_server):
    result = await call_via_mcp("calculate_tax_impact", {
        "annual_income": 100000, "conversion_amount": 50000,
        "filing_status": "single", "state": "CA"
    })
    assert "federal_tax" in json.loads(result)
```

**Pipeline test**: Run the full deterministic pipeline end-to-end.

### 13.4 Prompt Regression Tests (5%)

Maintained as a JSON test suite, run against real OpenAI API:

```json
[
  {
    "id": "start_flow",
    "input": "I want to convert my IRA",
    "expected_tool": "validate_user_inputs",
    "forbidden_tools": ["calculate_tax_impact"]
  },
  {
    "id": "bulk_input",
    "input": "55 years old, single, $120k income, $400k IRA, New York",
    "expected_tool": "validate_user_inputs",
    "expected_args_contain": {"age": 55, "filing_status": "single"}
  },
  {
    "id": "no_hallucination",
    "input": "What tax bracket am I in?",
    "expected_tool": "validate_user_inputs",
    "response_must_not_contain": ["$", "%"]
  }
]
```

Run on every system prompt change. Block changes that drop pass rate >5%.

---

## 14. Observability & Logging

### 14.1 Logging Strategy

Structured JSON logging with 4 categories:

| Category | Events | Fields |
|----------|--------|--------|
| User interaction | message_received, form_submitted | session_id, message_length, timestamp |
| Tool calls | tool_initiated, tool_completed, tool_failed | session_id, tool_name, duration_ms, success |
| GPT API | api_call, api_error | session_id, model, prompt_tokens, completion_tokens, duration_ms |
| Errors | validation_error, connection_error, timeout | session_id, error_type, error_message, retry_attempt |

**Privacy**: Log field names, not financial values. No PII in logs.

### 14.2 Token Usage Tracking

```python
class TokenTracker:
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.calls = []

    def record(self, response):
        usage = response.usage
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens

    @property
    def estimated_cost(self):
        # Configurable per model
        return (self.total_prompt_tokens * PROMPT_COST_PER_M / 1_000_000 +
                self.total_completion_tokens * COMPLETION_COST_PER_M / 1_000_000)
```

Displayed in sidebar for cost transparency.

### 14.3 Quality Metrics (Post-MVP)

| Metric | Target |
|--------|--------|
| Turns to completion | ≤ 8 turns |
| Tool misroute rate | < 5% |
| User corrections per session | < 2 |
| Flow completion rate | > 70% |
| Average cost per conversation | < $0.01 |

---

## 15. Non-Functional Requirements

| Requirement | Target | Notes |
|-------------|--------|-------|
| Latency (per user turn) | < 5 seconds | Dominated by GPT API call (~2s) |
| Latency (full pipeline) | < 10 seconds | 1 GPT call + 4 MCP calls + 1 GPT summary |
| Token usage per conversation | < 5,000 tokens | With context compaction |
| Cost per conversation | < $0.01 (GPT-4o) / < $0.003 (GPT-4o-mini) | |
| Concurrent users | 1 (single user, localhost) | |
| Data persistence | None (session-only, ephemeral) | |
| Browser support | Chrome, Firefox, Safari (modern) | Streamlit standard |
| Python version | 3.10+ | For FastMCP + asyncio support |
| Authentication | None | localhost only |
| Security | No PII logging, API key in .env | |

---

## 16. File Structure & Tech Stack

### 16.1 File Structure

```
roth_mcp/
├── mcp_server.py               # FastMCP server entry point (5 tools)
├── streamlit_app.py            # Streamlit chat UI entry point
├── agent_loop.py               # GPT conversation loop (Phase 1 + Phase 3)
├── pipeline.py                 # Deterministic computation pipeline (Phase 2)
├── mcp_client.py               # MCP session management + ResilientToolExecutor
├── schema_converter.py         # MCP → OpenAI schema translation
├── models.py                   # Data classes (UserProfile, CalculationResults, TokenTracker)
├── config.py                   # Environment config (validation, path resolution)
├── prompts/
│   └── system.md               # System prompt (separate file for easy iteration)
├── tax/
│   ├── __init__.py
│   ├── brackets.py             # Federal tax brackets (2024/2025)
│   ├── state_rates.py          # Flat state tax rates (all 50 states)
│   └── calculator.py           # Tax computation functions
├── html/
│   ├── __init__.py
│   ├── reports.py              # HTML report template + generator
│   └── styles.py               # Inline CSS for report
├── ui/
│   ├── __init__.py
│   ├── forms.py                # Streamlit native form builder
│   └── sidebar.py              # Sidebar components (inputs summary, metrics)
├── validators.py               # Input validation functions
├── tests/
│   ├── test_tax_calculator.py  # Tax computation unit tests
│   ├── test_tools.py           # MCP tool logic tests
│   ├── test_validators.py      # Validation tests
│   ├── test_schema_converter.py # Schema translation tests
│   ├── test_orchestrator.py    # Agent loop + pipeline helper tests
│   ├── test_integration.py     # MCP roundtrip tests
│   └── prompt_eval_cases.json  # Prompt regression test data
├── .env.example                # Template for environment variables
├── .streamlit/
│   └── config.toml             # Streamlit config (localhost binding)
├── requirements.txt            # Python dependencies (version-pinned)
├── CLAUDE.md                   # Project instructions
└── README.md                   # Setup and usage guide
```

### 16.2 Tech Stack

**Startup validation** (`config.py`):
```python
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).parent
MCP_SERVER_SCRIPT = str(PROJECT_ROOT / os.getenv("MCP_SERVER_ARGS", "mcp_server.py"))

def validate_config():
    """Call at top of streamlit_app.py. Fail fast with actionable errors."""
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not set. Copy .env.example to .env and add your key.")
        st.stop()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if model not in ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]:
        st.warning(f"Unknown model '{model}'. Proceeding but may not support function calling.")
```

| Component | Technology | Version |
|-----------|-----------|---------|
| MCP Server | FastMCP (Python SDK) | latest |
| Chat UI | Streamlit | >= 1.33 |
| LLM Orchestration | OpenAI Python SDK | >= 1.0 |
| MCP Client | mcp Python package | >=1.0,<3.0 |
| Tax Data | Python dicts (no external API) | -- |
| Environment Config | python-dotenv | latest |
| Testing | pytest + pytest-asyncio | latest |
| Logging | structlog | latest |

### 16.3 `requirements.txt`

```
fastmcp>=2.14,<4.0       # MCP server framework (@mcp.tool() decorator)
streamlit>=1.33,<2.0      # Chat UI framework (st.html, st.chat_input)
openai>=1.0,<3.0          # GPT API client (function calling support)
mcp>=1.0,<3.0             # MCP Python SDK (ClientSession, stdio_client)
nest-asyncio>=1.6,<2.0    # Required: Streamlit's Tornado loop + asyncio.run()
python-dotenv>=1.0,<2.0   # Environment config (.env loading)
structlog>=24.0,<26.0     # Structured JSON logging
pytest>=8.0               # Testing framework
pytest-asyncio>=0.23      # Async test support
```

> **Package roles:** `fastmcp` is the **server** framework (tool registration via `@mcp.tool()`). The `mcp` package is the **client** SDK (`ClientSession`, `stdio_client`) used by the Streamlit app. Both are required.
>
> **Version pinning rationale:** FastMCP 3.0 introduced breaking changes (import paths, removed transports). Pin to `<4.0` to prevent surprise breaks. See [FastMCP breaking change incident](https://www.basicmemory.com/blog/fastmcp-breaking-change-incident).

### 16.4 `.env.example`

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Model Configuration
OPENAI_MODEL=gpt-4o-mini     # Options: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
OPENAI_TIMEOUT=30             # Seconds per API call
MAX_SESSION_COST=0.50         # Dollar cap per conversation session

# MCP Server (resolved relative to project root)
MCP_SERVER_CMD=python
MCP_SERVER_ARGS=mcp_server.py
```

### 16.5 `.streamlit/config.toml`

```toml
[server]
address = "localhost"         # Bind to localhost only — prevents LAN exposure
```

---

## 17. Implementation Phases

### Phase 1: Foundation (MVP Core)

| Task | Description | Files |
|------|-------------|-------|
| T001 | Tax calculation engine | tax/brackets.py, tax/state_rates.py, tax/calculator.py |
| T002 | Input validators | validators.py |
| T003 | FastMCP server with 5 tools | mcp_server.py |
| T004 | HTML report generator | html/reports.py, html/styles.py |
| T005 | Unit tests for tax + tools | tests/test_tax_calculator.py, tests/test_tools.py |

### Phase 2: Client + Orchestration

| Task | Description | Files |
|------|-------------|-------|
| T006 | MCP client with schema translation + persistent session | mcp_client.py, schema_converter.py |
| T007 | Agent loop (GPT conversation) + Pipeline (deterministic compute) | agent_loop.py, pipeline.py, models.py |
| T008 | Streamlit chat UI | streamlit_app.py |
| T009 | Sidebar (inputs summary, token tracking) | streamlit_app.py |
| T010 | Native Streamlit input forms | html/forms.py |

### Phase 3: Polish + Testing

| Task | Description | Files |
|------|-------------|-------|
| T011 | System prompt tuning + few-shot examples | orchestrator.py |
| T012 | Error handling + resilient executor | mcp_client.py |
| T013 | Progress indicators + status messages | streamlit_app.py |
| T014 | Anti-hallucination guardrail | orchestrator.py |
| T015 | Integration tests + prompt eval | tests/ |

### Phase 4: Post-MVP Enhancements

| Task | Description | Priority |
|------|-------------|----------|
| T016 | Scenario comparison (multiple amounts) | High |
| T017 | Value change → recalculation cascade | High |
| T018 | Report export (HTML download, PDF) | Medium |
| T019 | LLM provider abstraction (swap OpenAI/Claude/Ollama) | Medium |
| T020 | Graceful degradation (fallback UI when API down) | Medium |
| T021 | Conversation quality metrics dashboard | Low |

---

## 18. Decision Log

| # | Decision | Alternatives Considered | Rationale |
|---|----------|------------------------|-----------|
| D1 | Merge 2 input tools into 1; rename to `validate_user_inputs` | Keep separate as `collect_roth_inputs` + `collect_account_details` | Saves 1 GPT round-trip. Name "validate" reflects actual behavior (tool validates/confirms, doesn't collect). Backend architect review recommendation. |
| D2 | Hybrid Orchestrator-Pipeline pattern | Pure GPT loop (all tool calls via GPT), Pure state machine, DAG executor | Optimal balance: GPT handles messy conversation; deterministic pipeline handles computation. Reduces GPT calls from ~12 to ~3. |
| D3 | stdio transport for MCP | SSE transport, HTTP transport | Single user, localhost. Lowest latency, no network config. Easy upgrade to SSE later. |
| D4 | Native Streamlit forms instead of HTML forms from tools | HTML forms rendered via st.html(), No forms (conversational only) | HTML forms in iframes can't POST data back to Streamlit. Native forms integrate with session_state. |
| D5 | Conversational-first input collection | Form-first (always show form), Hybrid (form for all, conversation for few) | More natural UX. GPT extracts values from free text. Forms only when 3+ fields missing. |
| D6 | tool_choice: "auto" | "required" (always call tool), "none" (never call tool) | GPT needs to respond conversationally sometimes (greetings, explanations, follow-ups). |
| D7 | GPT-4o-mini as recommended default | GPT-4o, GPT-3.5-turbo | Cheapest model with reliable function calling. ~$0.003/conversation. User can override via env var. |
| D8 | Per-request MCP sessions | Persistent session across Streamlit reruns | Streamlit reruns the script on every interaction. Persistent async sessions add complexity. Stateless server means no state to preserve. |
| D9 | Implicit state management (GPT + session_state) | Explicit state machine, Finite automaton | Only 5 tools with linear flow. State machine adds code without benefit. GPT tracks state naturally in message history. |
| D10 | Post-processing hallucination check | Trust system prompt only, Manual review | Defense-in-depth. System prompt is primary defense; regex check is secondary. Low effort, high value for financial accuracy. |
| D11 | Structured JSON logging (structlog) | Print statements, Python logging module | Structured logs are grep-able and parseable. Easy to add dashboarding later. |
| D12 | 3 few-shot examples in system prompt | 0 (no examples), 5+ examples | Research shows 2-5 examples optimal. 3 covers the top ambiguity patterns without token bloat. |
| D13 | Persistent MCP session via `@st.cache_resource` | Per-request sessions (new subprocess each message) | Avoids ~300-500ms subprocess spawn per message on Windows. Backend architect review. |
| D14 | `nest_asyncio` for Streamlit event loop compatibility | Custom threading solution, sync-only code | Simplest fix for Streamlit Tornado + asyncio.run() conflict. Senior architect blocker. |
| D15 | System prompt in separate file (`prompts/system.md`) | Hardcoded string literal in Python | Enables independent prompt iteration, cleaner git diffs, non-developer review. |
| D16 | Version-pinned dependencies (`<major.0` caps) | Unpinned (`>=0.1`) | FastMCP 3.0 broke real projects. Major version pins prevent surprise breaks. |

---

## 19. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | GPT computes tax amounts itself instead of calling tools | Medium | Critical | Anti-hallucination system prompt rule + post-processing check |
| R2 | GPT calls tools in wrong order | Low | Medium | Tool descriptions include sequencing hints ("call AFTER..."). System prompt lists order. collected_data summary shows GPT what exists. |
| R3 | OpenAI API rate limiting during demo | Low | Low | Exponential backoff retry. GPT-4o-mini has generous rate limits. |
| R4 | MCP server process crashes mid-conversation | Low | Medium | ResilientToolExecutor restarts subprocess + retries. Session state preserves user data. |
| R5 | Tax bracket data becomes outdated | Certain (annual) | Medium | 2024 brackets hardcoded. Document in README to update annually. Single file change (tax/brackets.py). |
| R6 | Streamlit session_state lost on browser refresh | Low | Low | No persistence by design. User restarts conversation. Acceptable for demo. |
| R7 | Large HTML report bloats GPT context window | Low | Low | Compact report to summary after rendering. Replace with "[report displayed]" in message history. |
| R8 | User enters unreasonable values (age=5, income=$1B) | Medium | Low | Dual-layer validation: GPT asks to confirm, tool rejects hard. |
| R9 | Streamlit async/sync mismatch | Certain (without fix) | Fatal | **Fixed:** Use `nest_asyncio.apply()` at startup. Streamlit's Tornado loop conflicts with `asyncio.run()`. Added to requirements.txt. |
| R10 | Dependency version drift (FastMCP 3.0 broke projects) | Certain (annually) | Critical | **Fixed:** Pin to major version ranges in requirements.txt (`fastmcp>=2.14,<4.0`). Review pins quarterly. |
| R11 | No timeout/cost cap on OpenAI API calls | Medium | Medium | Add `OPENAI_TIMEOUT=30` and `MAX_SESSION_COST=0.50` to config. Abort on threshold. |
| R12 | OpenAI message ordering violation | Certain (in original code) | Fatal | **Fixed:** Process all tool calls and append results before triggering pipeline. See Section 8.2 revised code. |

---

## 20. Appendix: System Prompt

```
You are a Roth Conversion Advisor, an AI assistant that helps users analyze
whether converting their Traditional IRA to a Roth IRA makes financial sense.

## ABSOLUTE RULE — NEVER VIOLATE
You MUST NOT compute, estimate, or state any tax amount, tax rate, bracket
threshold, or state tax rate from your own knowledge. ALL numerical tax
information MUST come from the calculate_tax_impact or
find_optimal_conversion_amount tools. If asked about taxes without tool
results, say: "Let me calculate that for you" and call the appropriate tool.

## TOOL SELECTION ORDER
1. validate_user_inputs — ALWAYS call first for a new analysis
2. calculate_tax_impact — Requires inputs from step 1
3. find_optimal_conversion_amount — Requires inputs from step 1
4. breakeven_analysis — Requires results from step 2
5. generate_conversion_report — Call last, requires ALL prior results

## HOW TO COLLECT INFORMATION
- Extract any values the user mentions naturally. If they say "I'm 55 and
  make $120k", extract age=55 and annual_income=120000.
- Pass all known values to validate_user_inputs, leaving unknown values as null.
- If 1-2 values are missing: ask conversationally.
- If 3+ values are missing: the app will show a form.
- Never ask for information already provided.

## INPUT VALIDATION
Before calling tools, verify:
- Age: 18-100
- Income: >= 0
- IRA balance: >= 0
- Filing status: single, married_joint, married_separate, head_of_household
- State: valid 2-letter US state code
- Conversion amount: > 0, <= IRA balance
If a value seems unreasonable, ask the user to confirm.

## HOW TO PRESENT RESULTS
- For JSON results: explain in plain language with specific numbers.
- For HTML content: say you're displaying it, add a brief summary.
- Always explain what numbers mean practically.
  Example: "The conversion would pay for itself in about 8 years, meaning
  if you're 55 now, you'd break even around age 63."

## TOOL SELECTION EXAMPLES
User: "I want to convert my IRA"
→ Call validate_user_inputs (not calculate)

User: "I'm 55, make $120k, should I convert?"
→ Call validate_user_inputs(age=55, annual_income=120000)

User: "What would the tax be on converting $50k?"
→ Call validate_user_inputs first (need income, status, state)

## BOUNDARIES
- You are NOT a licensed financial advisor. Include disclaimer after results.
- Do NOT make up tax rates or financial data.
- Do NOT provide advice on non-Roth topics (stocks, crypto, real estate).
- If asked about related topics (Traditional vs Roth), briefly answer
  then steer back to the analysis.

## TONE
- Professional but approachable ("friendly advisor at a coffee shop")
- Use plain language. Explain jargon when first used.
- Be concise. Lead with the answer, not the reasoning.
- Use specific numbers from tool results, not vague statements.

## DISCLAIMER (include after any results)
"This analysis is for informational and educational purposes only. It uses
simplified tax brackets and assumptions. Please consult a qualified tax
professional or financial advisor before making any Roth conversion decisions."
```

---

## 21. Architectural Review Summary

### Review Process

This PRD was generated and reviewed through a multi-stage process:

1. **Brainstorming** — Initial design exploration and requirements clarification
2. **Deep Research** (4 parallel Opus 4.6 sub-agents):
   - `agent-orchestration-multi-agent-optimize` — Workload distribution, cost optimization, tool chaining
   - `ai-agents-architect` — Agent design patterns, tool use strategy, system prompt design
   - `multi-agent-patterns` — MCP protocol integration, coordination patterns, state management
   - `agent-orchestration-improve-agent` — Prompt engineering, UX, testing, observability
3. **Consolidation** — Merged all research into unified PRD
4. **Backend Architect Review** — 10 issues identified (2 Critical, 5 Major, 3 Minor)
5. **Senior Architect Review** — 3 blocking conditions + 7 advisory items

### Issues Resolved in v1.1

| # | Severity | Issue | Fix Applied |
|---|----------|-------|-------------|
| 1 | CRITICAL | Agent loop message ordering bug | Restructured: process all tool calls first, then trigger pipeline |
| 2 | CRITICAL | `asyncio.run()` fails inside Streamlit | Added `nest_asyncio` to requirements + startup |
| 3 | MAJOR | Per-request MCP sessions spawn subprocess every message | Changed to persistent session via `@st.cache_resource` |
| 4 | MAJOR | Tool name "collect_all_inputs" misleading | Renamed to `validate_user_inputs` |
| 5 | MAJOR | `generate_conversion_report` used JSON string params | Changed to flat structured parameters |
| 6 | MAJOR | Inconsistent parameter naming (`current_age` vs `age`) | Standardized across all tools |
| 7 | MAJOR | `breakeven_analysis` params contradicted between table and signature | Reconciled: signature is authoritative, table updated |
| 8 | MAJOR | Dependency versions dangerously loose (`>=0.1`) | Pinned to major version ranges |
| 9 | MAJOR | Missing orchestrator unit tests | Added `test_orchestrator.py` with helper function tests |
| 10 | MAJOR | No timeout/cost cap for OpenAI calls | Added `OPENAI_TIMEOUT` and `MAX_SESSION_COST` config |
| 11 | MINOR | Helper functions (`compact_result`, etc.) undefined | Added full specifications in Section 8.4 |
| 12 | MINOR | `forms.py` in `html/` directory misleading | Moved to `ui/forms.py` |
| 13 | MINOR | System prompt hardcoded in Python | Moved to `prompts/system.md` |
| 14 | MINOR | Streamlit default binds to 0.0.0.0 | Added `.streamlit/config.toml` with localhost binding |
| 15 | MINOR | `models.py` data classes undefined | Specified `UserProfile`, `CalculationResults` dataclasses |

### Final Verdict

**APPROVED FOR IMPLEMENTATION** — All blocking conditions resolved. 5 advisory items deferred to post-MVP (YAGNI-compliant).

---

*Document generated from multi-agent deep research using: agent-orchestration-multi-agent-optimize, ai-agents-architect, multi-agent-patterns, and agent-orchestration-improve-agent skills. Reviewed by backend-architect and senior-architect skills. All agents ran on Claude Opus 4.6.*
