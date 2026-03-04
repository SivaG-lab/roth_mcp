# Data Model: Roth Conversion Calculator MCP Server v2.0

**Date**: 2026-03-03
**Source**: spec.md User Stories 1-10, PRD Sections 6, 8, 9, 12

---

## Entity Relationship Overview

```
UserProfile ──(1:1)──> ModelAssumptions
     │
     └──(input to)──> validate_projection_inputs
                           │
                           v
                      TaxEstimate <── estimate_tax_components
                           │
            ┌──────────────┼──────────────┐
            v              v              v
     ProjectionData  OptimizationResult  BreakevenResult
            │              │              │
            └──────────────┼──────────────┘
                           v
                   CalculationResults ──> generate_conversion_report
                           │
                   TokenTracker (orthogonal, tracks GPT API usage)
```

---

## Enums

### FilingStatus

```python
class FilingStatus(str, Enum):
    SINGLE = "single"
    MARRIED_JOINT = "married_joint"
    MARRIED_SEPARATE = "married_separate"
    HEAD_OF_HOUSEHOLD = "head_of_household"
```

**Used by**: UserProfile.filing_status, all tax computation functions, IRMAA lookup, SS taxation

### AutoFillSource

```python
class AutoFillSource(str, Enum):
    USER_PROVIDED = "user_provided"
    AUTO_CALCULATED = "auto_calculated"
    AGE_BASED_DEFAULT = "age_based_default"
    SYSTEM_DEFAULT = "system_default"
    USER_IMPLICIT = "user_implicit"
```

**Used by**: validate_projection_inputs to track which fields were auto-filled

### PipelinePhase

```python
class PipelinePhase(str, Enum):
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
```

**Used by**: Streamlit session state to track UI phase

### Assessment

```python
class Assessment(str, Enum):
    WORTH_IT = "worth_it"        # breakeven < 10 years
    MARGINAL = "marginal"        # breakeven 10-20 years
    NOT_WORTH_IT = "not_worth_it" # breakeven > 20 years or never
```

**Used by**: BreakevenResult.assessment

---

## Core Entities

### UserProfile

**Purpose**: Holds all 17+ user financial inputs. Central entity passed to validate_projection_inputs.

| Field | Type | Default | Validation | Source |
|-------|------|---------|-----------|--------|
| current_age | int \| None | None | 18-100, required | User |
| retirement_age | int \| None | None | > current_age, ≤ 100, required | User |
| filing_status | str \| None | None | FilingStatus enum, required | User |
| state | str \| None | None | Valid 2-letter US code, required | User |
| annual_income | float \| None | None | ≥ 0, required | User |
| trad_ira_balance | float \| None | None | ≥ 0, required | User |
| conversion_amount | float \| None | None | > 0, ≤ trad_ira_balance | User |
| conversion_schedule | list[float] \| None | None | each ≥ 0, sum ≤ trad_ira_balance | User |
| roth_ira_balance_initial | float | 0 | ≥ 0 | User/Default |
| taxable_dollars_available | float | 0 | ≥ 0 | User/Default |
| cost_basis | float | 0 | ≥ 0 | User/Default |
| annual_return | float | 0.07 | > -1, ≤ 0.30 | User/Default |
| taxable_account_annual_return | float | 0.07 | > -1, ≤ 0.30 | User/Default |
| model_years | int | 30 | 1-50 | User/Default |
| social_security | float | 0 | ≥ 0 | User/Auto-fill |
| rmd | float | 0 | ≥ 0 | User/Auto-fill |
| irmaa | float | 0 | ≥ 0 | User/Auto-fill |
| other_ordinary_income_by_year | list[float] \| None | None | each ≥ 0 | User |
| spending_need_after_tax_by_year | list[float] \| None | None | each ≥ 0 | User |

**Properties**:
- `required_fields` → `["current_age", "retirement_age", "filing_status", "state", "annual_income", "trad_ira_balance"]`
- `missing_required` → list of required fields that are None
- `has_conversion_spec` → True if conversion_amount or conversion_schedule is set
- `to_tool_args()` → dict with only non-None values

**Cross-field Rules**:
- If conversion_amount set but not conversion_schedule → auto-wrap to `[conversion_amount]`
- If both set → conversion_schedule takes precedence, conversion_amount ignored
- retirement_age must be > current_age

### ModelAssumptions

**Purpose**: Default rates and horizons. Displayed in sidebar and report.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| annual_return | float | 0.07 | 7% nominal |
| taxable_account_annual_return | float | 0.07 | Same default |
| inflation_rate | float | 0.03 | Display only (not used in core calcs) |
| model_years | int | 30 | Projection horizon |
| rmd_start_age | int | 73 | IRS 2024 rule |
| ss_start_age | int | 67 | Full retirement age |

### TaxEstimate

**Purpose**: Complete tax breakdown for a single conversion scenario. Output of `estimate_tax_components`.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| federal_tax | float | 0 | From bracket calculation |
| state_tax | float | 0 | Flat rate × taxable_conversion |
| irmaa_impact | float | 0 | Annual surcharge (2-year lookback) |
| ss_tax_impact | float | 0 | Marginal SS tax increase from conversion |
| rmd_tax | float | 0 | Tax on RMD at marginal rate |
| total_tax_cost | float | 0 | Sum of all above |
| effective_rate | float | 0 | total_tax_cost / conversion_amount |
| marginal_rate | float | 0 | Top bracket rate after conversion |
| bracket_before | str | "" | e.g., "22%" |
| bracket_after | str | "" | e.g., "24%" |
| conversion_amount | float | 0 | Echo back for reference |

### ProjectionData

**Purpose**: Year-by-year comparison of convert vs. no-convert scenarios.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| projections | list[dict] | [] | One dict per year |
| summary | dict | {final_roth_value, final_trad_value, net_benefit, crossover_year} | Aggregated metrics |

**Projection year dict schema**:
```python
{
    "year": int,           # 1-based index
    "age": int,            # current_age + year
    "conversion": float,   # conversion amount this year
    "roth_balance": float, # Roth path balance
    "trad_balance": float, # Traditional path balance (no-convert)
    "tax_paid": float,     # Tax on this year's conversion
    "rmd_amount": float,   # RMD if age >= 73
}
```

### OptimizationResult

**Purpose**: Optimal multi-year conversion schedule from greedy bracket-fill algorithm.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| optimal_schedule | list[float] | [] | Amounts per year |
| total_tax_cost | float | 0 | Total tax across all years |
| tax_saved_vs_baseline | float | 0 | Savings vs. single lump-sum |
| optimization_goal | str | "minimize_tax" | Goal used |
| converged | bool | True | Did algorithm converge? |
| confidence | float | 1.0 | 0-1, < 1.0 if non-convergent |

### BreakevenResult

**Purpose**: How many years until Roth path >= Traditional path.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| breakeven_years | int | 0 | Years to breakeven |
| breakeven_age | int | 0 | current_age + breakeven_years |
| assessment | str | "" | worth_it / marginal / not_worth_it |

### CalculationResults

**Purpose**: Container for all tool results. Stored in session state.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| tax_estimate | TaxEstimate \| None | None | From tool 2 |
| projection | ProjectionData \| None | None | From tool 3 |
| optimization | OptimizationResult \| None | None | From tool 4 |
| breakeven | BreakevenResult \| None | None | From tool 5 |
| report_html | str | "" | From tool 6 |
| tools_completed | list[str] | [] | Track which tools ran |

### TokenTracker

**Purpose**: Track GPT API token usage and estimated cost.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| total_prompt_tokens | int | 0 | Cumulative |
| total_completion_tokens | int | 0 | Cumulative |
| calls | list | [] | Individual call records |

**Methods**:
- `record(response)` — extract usage from OpenAI response
- `estimated_cost` (property) — `prompt_tokens × $0.15/M + completion_tokens × $0.60/M` (gpt-4o-mini pricing)

---

## Tax Data Tables (Reference Data, not entities)

### Federal Brackets 2024

Stored as dict of lists in `tax/brackets.py`:
```python
FEDERAL_BRACKETS = {
    "single": [(11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24), (243725, 0.32), (609350, 0.35), (float('inf'), 0.37)],
    "married_joint": [(23200, 0.10), (94300, 0.12), (201050, 0.22), (383900, 0.24), (487450, 0.32), (731200, 0.35), (float('inf'), 0.37)],
    "married_separate": [(11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24), (243725, 0.32), (365600, 0.35), (float('inf'), 0.37)],
    "head_of_household": [(16550, 0.10), (63100, 0.12), (100500, 0.22), (191950, 0.24), (243700, 0.32), (609350, 0.35), (float('inf'), 0.37)],
}
```

### Standard Deductions 2024

```python
STANDARD_DEDUCTIONS = {
    "single": 14600,
    "married_joint": 29200,
    "married_separate": 14600,
    "head_of_household": 21900,
}
ADDITIONAL_DEDUCTION_SINGLE = 1550  # age 65+
ADDITIONAL_DEDUCTION_MARRIED = 1300  # age 65+
```

### State Tax Rates

Stored as dict in `tax/state_rates.py`:
```python
STATE_TAX_RATES = {
    "AL": 0.0500, "AK": 0.0, "AZ": 0.0259, "AR": 0.0440, "CA": 0.0930,
    # ... all 50 states + DC
    "TX": 0.0, "FL": 0.0, "NV": 0.0, "WA": 0.0, "WY": 0.0, "SD": 0.0,
    "NH": 0.0, "TN": 0.0,
}
```

### IRMAA Thresholds

Stored as dict of lists in `tax/irmaa.py`:
```python
IRMAA_THRESHOLDS = {
    "single": [(103000, 0), (129000, 65.90), (161000, 164.80), (193000, 263.70), (500000, 362.60), (float('inf'), 395.60)],
    "married_joint": [(206000, 0), (258000, 65.90), (322000, 164.80), (386000, 263.70), (750000, 362.60), (float('inf'), 395.60)],
    # married_separate and head_of_household use single thresholds
}
```

### RMD Uniform Lifetime Table

Stored as dict in `tax/rmd.py`:
```python
RMD_TABLE = {
    73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
    78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
    83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4,
    88: 13.7, 89: 12.9, 90: 12.2,
    # ... continues to 120
}
```

---

## State Transitions

### Pipeline Phase

```
collecting ──(validate returns complete)──> analyzing ──(report generated)──> complete
     ^                                                                          │
     └───────────────────── (Start Over button) ────────────────────────────────┘
```

### Validation Status

```
incomplete ──(more inputs provided)──> incomplete ──(all required + conversion spec)──> complete
```
