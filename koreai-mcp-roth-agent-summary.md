# Kore.ai MCP Agent + Roth Conversion Agent — Summary & Takeaways

---

## 1. How MCP Agents Work with Kore.ai

### What Happens Under the Hood
- Kore.ai MCP Agent uses an **internal LLM (GPT by default)** to orchestrate everything
- The LLM decides **which tool to call**, **what inputs to collect**, and **how to respond**
- Your **FastMCP server** exposes tools that Kore.ai auto-discovers
- Kore.ai handles conversation flow — you don't wire nodes manually in MCP Agents

### Architecture
```
User Input
    ↓
Kore.ai MCP Agent (LLM: GPT / Custom Model)
    ↓
LLM selects tool + extracts inputs from conversation
    ↓
Calls your FastMCP tool via MCP protocol
    ↓
LLM summarizes result → sends back to UI
```

---

## 2. MCP Agent vs Dialog Task — Key Difference

| Feature | Dialog Task (Old) | MCP Agent (New) |
|---|---|---|
| Flow control | You define nodes manually | LLM decides flow |
| Input collection | Entity nodes in the canvas | LLM collects conversationally |
| Tool connection | Service node | MCP server URL |
| HTML rendering | Message node | Tool returns HTML string |
| Flexibility | More rigid, more control | More dynamic, AI-driven |

> **Takeaway:** In MCP Agents, there are **no nodes to add**. You configure Rules, not a visual canvas.

---

## 3. Entity Rules vs Answering Rules

### Entity Rules — Validate Inputs
Validate what the user provides **before** passing to your tool.

| Example | Rule |
|---|---|
| Age must be valid | `age >= 18 AND age <= 100` |
| Income must be positive | `annual_income >= 0` |
| Can't convert more than balance | `conversion_amount <= ira_balance` |
| Filing status must be valid | `filing_status IN [single, married_joint, ...]` |

### Answering Rules — Auto-fill / Skip Inputs
Tell the LLM to **skip asking** for a field when a condition is already true.

| Example | Rule |
|---|---|
| Skip spouse income if single | `if filing_status == "single" → spouse_income = 0` |
| Auto-set conversion if user says "convert all" | `conversion_amount = ira_balance` |
| Skip Roth balance if user has none | `if has_roth == "no" → roth_balance = 0` |

---

## 4. HTML Forms — Where & How to Use Them

### The Problem
MCP tools return text/data. Forms need to be rendered by the chat UI (Kore.ai webchat).

### Option A — LLM Collects Conversationally (Default)
- LLM asks one question at a time
- No HTML needed
- ✅ Works on all channels (web, voice, mobile)
- ❌ Slow for 5+ inputs — bad UX

### Option B — Tool Returns HTML Form ✅ Recommended for Web
- Tool detects missing inputs → returns an HTML form string
- Kore.ai webchat renders it
- User fills all fields at once → submits
- ✅ Best UX for many inputs
- ❌ Only works on web/chat channels (not voice)

### Where to Return HTML in Your Code
| Location | When to Use |
|---|---|
| Input collection tool | When required fields are missing |
| Final report tool | Always — rich styled HTML summary |
| Error handling | When validation fails, show correctable form |

### Critical Setting in Kore.ai
> Go to: **Agent Config → Response Handling**  
> Set: ✅ **"Pass tool response directly to UI"**  
> (NOT "Summarize with LLM" — or the LLM will strip your HTML!)

---

## 5. Roth Conversion Agent — Recommended Tools (6 Total)

| # | Tool | Purpose | Returns HTML? |
|---|---|---|---|
| 1 | `collect_roth_inputs` | Collect age, income, IRA balance, filing status, state | ✅ If missing inputs |
| 2 | `collect_account_details` | Roth balance, 401k, basis in IRA | ✅ If missing inputs |
| 3 | `calculate_tax_impact` | Federal + state tax on conversion amount | ❌ Returns JSON data |
| 4 | `find_optimal_conversion_amount` | Best amount to stay within tax bracket | ❌ Returns JSON data |
| 5 | `breakeven_analysis` | How many years until Roth pays off | ❌ Returns JSON data |
| 6 | `generate_conversion_report` | Final styled HTML summary + recommendation | ✅ Always HTML |

### Recommended Tool Flow
```
collect_roth_inputs → collect_account_details
    → calculate_tax_impact
    → find_optimal_conversion_amount
    → breakeven_analysis
    → generate_conversion_report
```

---

## 6. About the Internal LLM

Kore.ai uses GPT by default but supports custom models:
- Azure OpenAI (your own GPT deployment)
- Anthropic Claude
- Google Gemini
- Your own fine-tuned model

> Configure at: **Settings → Generative AI → Model Configuration**

### What the LLM Does in MCP Agent
| Task | LLM Responsibility |
|---|---|
| Tool selection | Picks which FastMCP tool to call |
| Input extraction | Pulls values from natural language |
| Rule enforcement | Validates against entity/answering rules |
| Response rendering | Wraps tool output for UI (or passes through) |

---

## 7. DOs and DON'Ts

### ✅ DOs
- Write **clear, descriptive docstrings** on every `@mcp.tool()` — the LLM uses them to decide when to call each tool
- Use **typed parameters** with defaults of `None` so tools can detect missing inputs
- Return **HTML forms** from your tool when multiple inputs are missing (better UX)
- Return a **rich HTML report** from your final summary tool
- Use **Answering Rules** to auto-fill predictable values (e.g. spouse income = 0 if single)
- Use **Entity Rules** to validate inputs before they hit your tool
- Set **"Pass tool response directly to UI"** if your tool returns HTML
- Use a **central `build_html_form()` helper** function — reuse across tools

### ❌ DON'Ts
- Don't try to add **nodes** inside an MCP Agent — that's Dialog Task behavior, not MCP Agent
- Don't let the LLM **summarize your HTML** — it will strip the formatting
- Don't make tools that **do too many things** — one tool per responsibility
- Don't skip docstrings — the LLM won't know when to invoke your tool correctly
- Don't use HTML forms on **voice channels** — only works on webchat/web SDK
- Don't hardcode all inputs as required — use `= None` defaults so tools gracefully handle partial data
- Don't assume Kore.ai will collect inputs for you — define Entity Rules to guide the LLM

---

## 8. Quick Reference — FastMCP Tool Pattern

```python
@mcp.tool()
def your_tool(
    param1: float = None,   # Always default to None
    param2: str = None,
    param3: int = None
) -> str:
    """
    Clear description — the LLM reads this to decide when to call this tool.
    List what it does, what it needs, and what it returns.
    """
    
    # Step 1: Check for missing inputs
    missing = [k for k, v in {"param1": param1, "param2": param2}.items() if v is None]
    
    if missing:
        return build_html_form(missing)   # ← Return HTML form
    
    # Step 2: Validate
    if param1 < 0:
        return "Error: param1 must be positive"
    
    # Step 3: Do the work
    result = do_calculation(param1, param2, param3)
    
    # Step 4: Return result (data or HTML)
    return result
```

---

## 9. Recommended Architecture for Roth Conversion Agent

```
Kore.ai MCP Agent
    ├── LLM: GPT-4o or Custom Model
    │     └── Response Mode: Pass-through (for HTML tools)
    ├── MCP Server: your FastMCP server URL
    ├── Tools (6 total — auto-discovered via FastMCP)
    ├── Entity Rules:
    │     ├── age: 18 to 100
    │     ├── conversion_amount ≤ ira_balance
    │     ├── annual_income ≥ 0
    │     └── filing_status: valid enum
    └── Answering Rules:
          ├── spouse_income = 0 if filing_status == single
          ├── conversion_amount = ira_balance if user says "convert all"
          └── roth_balance = 0 if user says "I don't have a Roth"
```

---

---

## 10. Entity Rules, Answering Rules & Input Enforcement for `analyze_roth_projection`

### Tool Inputs (17 Total)
`trad_ira_balance`, `annual_return`, `conversion_schedule`, `taxable_dollars_available`, `roth_ira_balance_initial`, `taxable_account_annual_return`, `current_age`, `retirement_age`, `years_to_retirement`, `model_years`, `other_ordinary_income_by_year`, `spending_need_after_tax_by_year`, `federal_tax`, `state_tax`, `social_security`, `rmd`, `irmaa`

### Entity Rules — Validate Inputs

Entity rules fire **after** a value is provided. They validate what the user gave — they don't force the user to provide anything.

| Input | Rule | Reason |
|---|---|---|
| `trad_ira_balance` | `>= 0` | Can't have negative balance |
| `roth_ira_balance_initial` | `>= 0` | No negative balances |
| `annual_return` | `> -1 AND <= 0.30` | Reasonable return range (-100% to 30%) |
| `taxable_account_annual_return` | `> -1 AND <= 0.30` | Same logic |
| `taxable_dollars_available` | `>= 0` | No negative cash |
| `current_age` | `>= 18 AND <= 100` | Valid adult age |
| `retirement_age` | `> current_age AND <= 100` | Must be after current age |
| `years_to_retirement` | `>= 0 AND <= 82` | Can't be negative |
| `model_years` | `>= 1 AND <= 50` | Reasonable projection horizon |
| `federal_tax` | `>= 0 AND <= 1` | Rate as decimal, 0–100% |
| `state_tax` | `>= 0 AND <= 1` | Same |
| `social_security` | `>= 0` | Benefit can't be negative |
| `rmd` | `>= 0` | Distribution can't be negative |
| `irmaa` | `>= 0` | Surcharge can't be negative |
| `conversion_schedule` | Each entry `>= 0` | No negative conversion amounts |

#### How to Configure in Kore.ai

In the MCP Agent config under **Rules → Entity Rules**:

```
trad_ira_balance >= 0
roth_ira_balance_initial >= 0
annual_return > -1 AND annual_return <= 0.30
taxable_account_annual_return > -1 AND taxable_account_annual_return <= 0.30
taxable_dollars_available >= 0
current_age >= 18 AND current_age <= 100
retirement_age > current_age AND retirement_age <= 100
years_to_retirement >= 0 AND years_to_retirement <= 82
model_years >= 1 AND model_years <= 50
federal_tax >= 0 AND federal_tax <= 1
state_tax >= 0 AND state_tax <= 1
social_security >= 0
rmd >= 0
irmaa >= 0
```

### Answering Rules — Auto-fill / Skip Inputs

Answering rules tell the LLM "don't ask — just use this value" when a condition is met.

| Condition | Auto-fill Rule |
|---|---|
| User provided `current_age` and `retirement_age` | `years_to_retirement = retirement_age - current_age` |
| User says "I don't have a Roth yet" | `roth_ira_balance_initial = 0` |
| User says "no taxable account" | `taxable_dollars_available = 0` and `taxable_account_annual_return = 0` |
| User doesn't mention Social Security or age < 62 | `social_security = 0` |
| User says "no IRMAA concerns" or income below threshold | `irmaa = 0` |
| User says "I'm not retired yet" or age < 73 (RMD age) | `rmd = 0` |
| `model_years` not specified | `model_years = 30` |
| `annual_return` not specified | `annual_return = 0.07` (7% default) |
| `taxable_account_annual_return` not specified | `taxable_account_annual_return = 0.07` |
| User says "convert all at once" | `conversion_schedule = [trad_ira_balance]` |

#### How to Configure in Kore.ai

In the MCP Agent config under **Rules → Answering Rules**:

```
If current_age AND retirement_age are both provided:
  Set years_to_retirement = retirement_age - current_age

If user says "no Roth account" or "starting fresh":
  Set roth_ira_balance_initial = 0

If user says "no taxable account":
  Set taxable_dollars_available = 0
  Set taxable_account_annual_return = 0

If current_age < 62:
  Set social_security = 0

If current_age < 73:
  Set rmd = 0

If user says "no IRMAA" or annual_income < 103000:
  Set irmaa = 0

If model_years not provided:
  Set model_years = 30

If annual_return not provided:
  Set annual_return = 0.07

If taxable_account_annual_return not provided:
  Set taxable_account_annual_return = 0.07

If user says "convert all" or "full conversion":
  Set conversion_schedule = [trad_ira_balance]
```

---

## 11. Can Entity/Answering Rules Enforce Required Inputs?

**No.** Neither rule type is designed to force a user to provide a value.

- **Entity Rules** only fire *after* a value is provided — they validate, they don't demand.
- **Answering Rules** do the opposite of enforcing — they *skip* asking by auto-filling.

So neither one says "you must provide this before we proceed."

---

## 12. What Actually Enforces Required Inputs — 3 Layers

Input enforcement happens through **three layers working together**:

### Layer 1: Tool Docstring (Guides the LLM)

The LLM reads your docstring to decide what it needs before calling the tool. Be explicit about what's required vs optional:

```python
@mcp.tool()
def analyze_roth_projection(
    trad_ira_balance: float = None,
    annual_return: float = None,
    conversion_schedule: list = None,
    taxable_dollars_available: float = None,
    roth_ira_balance_initial: float = None,
    taxable_account_annual_return: float = None,
    current_age: int = None,
    retirement_age: int = None,
    years_to_retirement: int = None,
    model_years: int = None,
    other_ordinary_income_by_year: list = None,
    spending_need_after_tax_by_year: list = None,
    federal_tax: float = None,
    state_tax: float = None,
    social_security: float = None,
    rmd: float = None,
    irmaa: float = None
) -> str:
    """
    Runs a multi-year Roth conversion projection comparing convert vs. no-convert scenarios.

    REQUIRED inputs (must collect before calling):
    - trad_ira_balance: Current traditional IRA balance
    - current_age: User's current age
    - retirement_age: Planned retirement age
    - conversion_schedule: List of yearly conversion amounts
    - federal_tax: Federal tax rate (decimal, e.g. 0.22)
    - state_tax: State tax rate (decimal, e.g. 0.05)

    OPTIONAL inputs (use defaults if not provided):
    - annual_return: Expected annual return (default 7%)
    - taxable_account_annual_return: Taxable account return (default 7%)
    - model_years: Number of years to project (default 30)
    - roth_ira_balance_initial: Starting Roth balance (default 0)
    - taxable_dollars_available: Cash available to pay taxes (default 0)
    - social_security: Annual SS benefit (default 0)
    - rmd: Required minimum distribution (default 0)
    - irmaa: Medicare surcharge (default 0)
    - other_ordinary_income_by_year: List of other income per year
    - spending_need_after_tax_by_year: List of spending needs per year

    Returns: JSON projection data or HTML form if required inputs are missing.
    """
```

The LLM reads "REQUIRED" and knows: **don't call this tool until you have those fields.**

### Layer 2: LLM Conversational Collection

The LLM will naturally ask for inputs it knows are needed. This is its default behavior. It will say things like:

- "What is your current age?"
- "What's your traditional IRA balance?"
- "What federal tax bracket are you in?"

This works, but for 17 inputs it can be slow (bad UX). That's why Layer 3 matters.

### Layer 3: Tool Code — HTML Form for Missing Inputs (Primary Input Collection)

When the tool is called with missing required values, it **returns an HTML form** for the user to fill out — not an error. This is the **intended input collection method** for web channels, especially when you have many inputs. The form gives users a clean UI to enter everything at once instead of answering questions one by one.

```python
    # Inside the tool function:

    # Derive what we can (mirrors answering rules)
    if current_age and retirement_age and years_to_retirement is None:
        years_to_retirement = retirement_age - current_age

    # Apply defaults for optional fields
    annual_return = annual_return if annual_return is not None else 0.07
    taxable_account_annual_return = taxable_account_annual_return if taxable_account_annual_return is not None else 0.07
    model_years = model_years if model_years is not None else 30
    roth_ira_balance_initial = roth_ira_balance_initial if roth_ira_balance_initial is not None else 0.0
    taxable_dollars_available = taxable_dollars_available if taxable_dollars_available is not None else 0.0
    social_security = social_security if social_security is not None else 0.0
    rmd = rmd if rmd is not None else 0.0
    irmaa = irmaa if irmaa is not None else 0.0

    # Check required fields — if any are missing, return HTML form for user to fill out
    required = {
        "trad_ira_balance": trad_ira_balance,
        "current_age": current_age,
        "retirement_age": retirement_age,
        "conversion_schedule": conversion_schedule,
        "federal_tax": federal_tax,
        "state_tax": state_tax,
    }
    missing = [k for k, v in required.items() if v is None]

    if missing:
        return build_html_form(missing)  # Return HTML form — user fills it out and submits

    # All required inputs present — run the projection
    result = run_projection(...)
    return result
```

### How the 3 Layers Work Together

```
User sends message
    ↓
Layer 1: LLM reads docstring → knows what's REQUIRED vs OPTIONAL
    ↓
Layer 2: LLM asks user for required fields conversationally
         (Answering Rules auto-fill what they can → fewer questions)
    ↓
Layer 3: LLM calls tool → tool checks for missing required fields
         If missing → returns HTML form for user to fill out
         User submits form → tool is called again with complete data
         If complete → runs projection, returns result
         (Entity Rules validate any values before they reach the tool)
```

---

## 13. Summary — Which Mechanism Does What

| Mechanism | Purpose | Enforces Input? |
|---|---|---|
| **Entity Rules** | Validates values after user provides them | ❌ No — only fires when value exists |
| **Answering Rules** | Auto-fills / skips fields when conditions are met | ❌ No — it skips, not enforces |
| **Tool Docstring** | Tells the LLM what's required vs optional | ✅ Yes — guides LLM to ask before calling |
| **LLM Conversation** | Asks user for missing required fields naturally | ✅ Yes — but slow for many inputs |
| **Tool Code Check** | Returns HTML form when required fields are missing | ✅ Yes — primary input collection for web |

> **The docstring is the most important piece.** A clear, explicit docstring with REQUIRED/OPTIONAL labels is the closest thing to enforcing input collection in an MCP Agent.

---

## 14. Revised Tool Architecture — 7 Tools

| # | Tool | Purpose | Returns HTML? |
|---|---|---|---|
| 1 | `validate_projection_inputs` | Collect & validate all inputs, return HTML form if missing | ✅ Form if missing, confirmation card if valid |
| 2 | `get_model_assumptions` | Return default assumptions (rates, brackets, inflation) | ✅ Small info card |
| 3 | `estimate_tax_components` | Calculate federal, state, IRMAA, SS tax, RMD tax | ✅ Mini tax table |
| 4 | `analyze_roth_projections` | Year-by-year convert vs. no-convert projection | ✅ Year-by-year table |
| 5 | `optimize_conversion_schedule` | Find best conversion amounts per year | ✅ Schedule table + summary |
| 6 | `breakeven_analysis` | How many years until Roth conversion pays off | ✅ Highlight card |
| 7 | `generate_conversion_report` | Final styled HTML report with recommendation | ✅ Full report |

### Recommended Tool Flow

```
validate_projection_inputs
    → get_model_assumptions (if user wants to see/override defaults)
    → estimate_tax_components
    → analyze_roth_projections
    → optimize_conversion_schedule
    → breakeven_analysis
    → generate_conversion_report (final HTML output)
```

---

## 15. Consistent Output Templates Per Tool

### The Problem

If you let the LLM generate the output format, it will vary every time. Different wording, different layout, different level of detail — inconsistent UX.

### The Solution

**Hardcode the HTML template inside each tool's Python code.** The LLM never touches the output format — your code controls it. Combined with **"Pass tool response directly to UI"** in Kore.ai, the output will look identical every conversation.

### Template Style Per Tool

Each tool gets its **own** template suited to what it returns — but within each tool, the template is always the same:

| Tool | Template Style | Size |
|---|---|---|
| `validate_projection_inputs` | Compact confirmation card OR HTML form | Small — 3-5 lines of confirmation |
| `get_model_assumptions` | Simple key-value list | Small — 5-8 lines |
| `estimate_tax_components` | Mini table (2 columns) | Medium — 6-10 rows |
| `analyze_roth_projections` | Year-by-year table with totals | Medium-Large — depends on years |
| `optimize_conversion_schedule` | Yearly schedule table + summary line | Medium — one row per year |
| `breakeven_analysis` | Single highlight card with number | Small — 2-3 lines |
| `generate_conversion_report` | Full styled report with sections | Large — final deliverable |

### Response Size Guide for Chat Agents

Responses should feel like **chat messages, not reports**. Only the final report should feel like a document.

| Tool Type | Max Lines | Max Width | Feels Like |
|---|---|---|---|
| Confirmation (validate) | 3-5 lines | 420px | Chat bubble |
| Key-value (assumptions) | 5-8 lines | 420px | Info card |
| Mini table (tax, optimize) | 6-12 rows | 420px | Small widget |
| Breakeven highlight | 2-3 lines | 420px | Alert card |
| Final report | 30-50 lines | 600px | Mini document |

> **Rule of thumb:** Intermediate tools should feel like chat messages (small, scannable). Only the final report should feel like a document.

---

## 16. Template Helper Pattern — Code Examples

Create a dedicated formatter function for each tool's output. This locks in the format so it's identical every time.

### Validation Confirmation Card

```python
def format_validation_result(data: dict) -> str:
    """Always returns the same compact confirmation card."""
    return f"""
    <div style="background: #f0fdf4; border-left: 3px solid #22c55e; 
                padding: 10px 14px; font-family: Arial; font-size: 13px; 
                border-radius: 4px; max-width: 420px;">
      <strong>✅ Inputs Validated</strong><br>
      Age: {data['current_age']} → {data['retirement_age']} 
           ({data['years_to_retirement']} yrs to retirement)<br>
      IRA Balance: ${data['trad_ira_balance']:,.0f}<br>
      Conversion: ${data['conversion_amount']:,.0f}<br>
      Tax Rate: {data['federal_tax']:.0%} federal + {data['state_tax']:.0%} state
    </div>
    """
```

### Tax Estimate Mini Table

```python
def format_tax_estimate(data: dict) -> str:
    """Always returns the same mini tax table."""
    return f"""
    <div style="font-family: Arial; font-size: 13px; max-width: 420px;">
      <strong>📊 Tax Impact on ${data['conversion_amount']:,.0f} Conversion</strong>
      <table style="width: 100%; margin-top: 8px; border-collapse: collapse;">
        <tr><td>Federal Tax</td>
            <td style="text-align:right">${data['federal']:,.0f}</td></tr>
        <tr><td>State Tax</td>
            <td style="text-align:right">${data['state']:,.0f}</td></tr>
        <tr><td>IRMAA Impact</td>
            <td style="text-align:right">${data['irmaa']:,.0f}</td></tr>
        <tr style="border-top: 1px solid #ccc; font-weight: 600;">
          <td>Total Tax Cost</td>
          <td style="text-align:right">${data['total']:,.0f}</td></tr>
      </table>
    </div>
    """
```

### Breakeven Highlight Card

```python
def format_breakeven(years: int, data: dict) -> str:
    """Always returns the same compact highlight card."""
    return f"""
    <div style="background: #eff6ff; border-left: 3px solid #3b82f6; 
                padding: 10px 14px; font-family: Arial; font-size: 13px; 
                border-radius: 4px; max-width: 420px;">
      <strong>⏱ Breakeven: {years} years</strong><br>
      The Roth conversion pays off by age {data['breakeven_age']}.<br>
      After that, every year is tax-free growth.
    </div>
    """
```

### Model Assumptions Info Card

```python
def format_assumptions(data: dict) -> str:
    """Always returns the same key-value assumptions card."""
    return f"""
    <div style="background: #fefce8; border-left: 3px solid #eab308; 
                padding: 10px 14px; font-family: Arial; font-size: 13px; 
                border-radius: 4px; max-width: 420px;">
      <strong>📋 Model Assumptions</strong><br>
      Annual Return: {data['annual_return']:.1%}<br>
      Inflation Rate: {data['inflation']:.1%}<br>
      RMD Start Age: {data['rmd_start_age']}<br>
      SS Start Age: {data['ss_start_age']}<br>
      Model Horizon: {data['model_years']} years
    </div>
    """
```

### Using Formatters in Your Tools

```python
@mcp.tool()
def validate_projection_inputs(...) -> str:
    """Validates all inputs. Returns HTML form if missing, confirmation card if valid."""
    
    # Check for missing required inputs
    missing = [k for k, v in required.items() if v is None]
    
    if missing:
        return build_html_form(missing)  # HTML form for user to fill out
    
    # All present — return confirmation card
    return format_validation_result(data)


@mcp.tool()
def estimate_tax_components(...) -> str:
    """Calculates federal, state, IRMAA, and total tax on conversion amount."""
    
    result = calculate_taxes(...)
    return format_tax_estimate(result)  # Always same table format


@mcp.tool()
def breakeven_analysis(...) -> str:
    """Calculates how many years until the Roth conversion pays off."""
    
    years = calculate_breakeven(...)
    return format_breakeven(years, data)  # Always same highlight card
```

### Why This Works

| Approach | Consistent? | Why |
|---|---|---|
| Let LLM generate output | ❌ No — varies every time | LLM picks different wording, layout, detail level |
| Hardcode template in tool code | ✅ Yes — identical every time | Python f-string controls exact HTML output |
| Pass-through to UI | ✅ Yes — LLM can't modify | Kore.ai renders your HTML as-is |

> **Critical Kore.ai setting:** Go to **Agent Config → Response Handling** and set **"Pass tool response directly to UI"** — otherwise the LLM will summarize/rewrite your HTML and break the formatting.

---

## 17. Entity Rules & Answering Rules — Per Tool

### Tool 1: `validate_projection_inputs`

**Entity Rules (Validation):**

| Input | Rule |
|---|---|
| `current_age` | `>= 18 AND <= 100` |
| `retirement_age` | `> current_age AND <= 100` |
| `trad_ira_balance` | `>= 0` |
| `roth_ira_balance_initial` | `>= 0` |
| `annual_return` | `> -1 AND <= 0.30` |
| `taxable_account_annual_return` | `> -1 AND <= 0.30` |
| `taxable_dollars_available` | `>= 0` |
| `federal_tax` | `>= 0 AND <= 1` |
| `state_tax` | `>= 0 AND <= 1` |
| `social_security` | `>= 0` |
| `rmd` | `>= 0` |
| `irmaa` | `>= 0` |
| `model_years` | `>= 1 AND <= 50` |
| `years_to_retirement` | `>= 0 AND <= 82` |
| `conversion_schedule` | Each entry `>= 0` |

**Answering Rules (Auto-fill):**

| Condition | Auto-fill |
|---|---|
| `current_age` and `retirement_age` both provided | `years_to_retirement = retirement_age - current_age` |
| User says "I don't have a Roth yet" | `roth_ira_balance_initial = 0` |
| User says "no taxable account" | `taxable_dollars_available = 0` and `taxable_account_annual_return = 0` |
| `current_age < 62` | `social_security = 0` |
| `current_age < 73` | `rmd = 0` |
| User says "no IRMAA concerns" or income below threshold | `irmaa = 0` |
| `model_years` not provided | `model_years = 30` |
| `annual_return` not provided | `annual_return = 0.07` |
| `taxable_account_annual_return` not provided | `taxable_account_annual_return = 0.07` |

---

### Tool 2: `get_model_assumptions`

**Entity Rules (Validation):**

| Input | Rule |
|---|---|
| `annual_return` (if user overrides) | `> -1 AND <= 0.30` |
| `inflation_rate` (if user overrides) | `>= 0 AND <= 0.20` |
| `model_years` (if user overrides) | `>= 1 AND <= 50` |

**Answering Rules (Auto-fill):**

| Condition | Auto-fill |
|---|---|
| User doesn't specify return rate | `annual_return = 0.07` |
| User doesn't specify inflation | `inflation_rate = 0.03` |
| User doesn't specify model horizon | `model_years = 30` |
| User doesn't specify RMD start age | `rmd_start_age = 73` |
| User doesn't specify SS start age | `ss_start_age = 67` (full retirement age) |

> This tool mostly returns defaults. Answering rules pre-fill everything — the LLM only needs to ask if the user wants to override.

---

### Tool 3: `estimate_tax_components`

**Entity Rules (Validation):**

| Input | Rule |
|---|---|
| `conversion_amount` | `> 0 AND <= trad_ira_balance` |
| `annual_income` | `>= 0` |
| `filing_status` | `IN [single, married_joint, married_separate, head_of_household]` |
| `state` | Valid US state code |
| `federal_tax` | `>= 0 AND <= 1` |
| `state_tax` | `>= 0 AND <= 1` |

**Answering Rules (Auto-fill):**

| Condition | Auto-fill |
|---|---|
| `filing_status == "single"` | `spouse_income = 0` |
| `current_age < 65` | `irmaa = 0` (not yet on Medicare) |
| `current_age < 73` | `rmd = 0` |
| User already provided tax rates in `validate_projection_inputs` | Reuse `federal_tax` and `state_tax` from prior tool |
| User says "no other income" | `other_ordinary_income = 0` |

---

### Tool 4: `analyze_roth_projections`

**Entity Rules (Validation):**

| Input | Rule |
|---|---|
| `conversion_schedule` | Each entry `>= 0`, list length `<= model_years` |
| `model_years` | `>= 1 AND <= 50` |
| `annual_return` | `> -1 AND <= 0.30` |
| `spending_need_after_tax_by_year` (if provided) | Each entry `>= 0` |
| `other_ordinary_income_by_year` (if provided) | Each entry `>= 0` |

**Answering Rules (Auto-fill):**

| Condition | Auto-fill |
|---|---|
| All inputs already collected by `validate_projection_inputs` | Pass through — no new questions needed |
| `spending_need_after_tax_by_year` not provided | Default to `[0] * model_years` (no withdrawals during projection) |
| `other_ordinary_income_by_year` not provided | Default to `[0] * model_years` |
| `annual_return` not provided | `annual_return = 0.07` |

> This tool should rarely need to ask the user anything — prior tools already collected the data.

---

### Tool 5: `optimize_conversion_schedule`

**Entity Rules (Validation):**

| Input | Rule |
|---|---|
| `max_annual_conversion` (if provided) | `> 0 AND <= trad_ira_balance` |
| `target_tax_bracket` (if provided) | Valid bracket value for filing status |
| `optimization_goal` (if provided) | `IN [minimize_tax, maximize_roth, stay_in_bracket]` |

**Answering Rules (Auto-fill):**

| Condition | Auto-fill |
|---|---|
| User doesn't specify goal | `optimization_goal = "minimize_tax"` |
| User doesn't specify max annual conversion | `max_annual_conversion = trad_ira_balance` (no cap) |
| User says "stay in my current bracket" | `target_tax_bracket = current bracket from estimate_tax_components` |
| All financial data already collected by prior tools | Pass through — no new questions needed |

---

### Tool 6: `breakeven_analysis`

**Entity Rules (Validation):**

| Input | Rule |
|---|---|
| `tax_cost_of_conversion` | `> 0` (must have a cost to break even on) |
| `annual_return` | `> -1 AND <= 0.30` |
| `future_tax_rate` (if provided) | `>= 0 AND <= 1` |

**Answering Rules (Auto-fill):**

| Condition | Auto-fill |
|---|---|
| `tax_cost_of_conversion` already calculated by `estimate_tax_components` | Pass through from prior tool |
| `annual_return` already set | Reuse from prior tools |
| `future_tax_rate` not provided | `future_tax_rate = federal_tax` (assume same rate) |
| User says "I expect higher taxes later" | `future_tax_rate = federal_tax + 0.05` (bump by 5%) |

> This tool needs almost no user input — everything comes from prior tools.

---

### Tool 7: `generate_conversion_report`

**Entity Rules (Validation):**

None — this tool consumes output from all prior tools. No direct user input to validate.

**Answering Rules (Auto-fill):**

| Condition | Auto-fill |
|---|---|
| All prior tools have been called | Pass all results through — no questions needed |
| User says "include comparison" | `include_comparison = true` |
| User says "keep it simple" | `detail_level = "summary"` |
| Default | `detail_level = "full"` |

> This tool should **never** ask the user a question. It only assembles and formats results from prior tools.

---

### Quick Reference — Which Tools Ask Questions?

| Tool | Asks User Questions? | Why |
|---|---|---|
| `validate_projection_inputs` | ✅ Yes — primary input collection | This is where all user data is gathered |
| `get_model_assumptions` | ⚠️ Only if user wants to override | Defaults handle everything |
| `estimate_tax_components` | ⚠️ Maybe filing status, state | May need 1-2 new fields |
| `analyze_roth_projections` | ❌ No | Uses data from prior tools |
| `optimize_conversion_schedule` | ⚠️ Maybe optimization goal | Usually has a good default |
| `breakeven_analysis` | ❌ No | Uses data from prior tools |
| `generate_conversion_report` | ❌ No | Only assembles and formats |

> **Design principle:** Front-load all user questions into the first 1-2 tools. Tools 4-7 should run silently using data already collected.

---

*Summary generated from conversation on Kore.ai MCP Agents, FastMCP integration, and Roth Conversion Agent design.*
