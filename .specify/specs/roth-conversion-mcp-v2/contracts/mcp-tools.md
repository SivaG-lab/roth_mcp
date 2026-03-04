# MCP Tool Contracts: Roth Conversion Calculator

**Protocol**: MCP (Model Context Protocol) via stdio transport
**Server**: FastMCP Python SDK
**Tools**: 6 tools, all returning dual-format JSON

---

## Universal Response Envelope (Dual-Return)

Every tool returns a JSON string with this structure:

```json
{
  "display": "<div>...styled HTML card...</div>",
  "data": { /* tool-specific structured data */ }
}
```

**Client functions**:
- `extract_html(result)` → returns `display` string
- `extract_data(result)` → returns `data` dict
- `compact_result(tool_name, result)` → returns `data` without HTML (for GPT context)

---

## Tool 1: validate_projection_inputs

**Purpose**: Gateway tool. Validates all inputs, applies auto-fill defaults, returns status.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "trad_ira_balance":              {"type": ["number", "null"], "default": null},
    "current_age":                   {"type": ["integer", "null"], "default": null},
    "retirement_age":                {"type": ["integer", "null"], "default": null},
    "filing_status":                 {"type": ["string", "null"], "enum": ["single", "married_joint", "married_separate", "head_of_household", null], "default": null},
    "state":                         {"type": ["string", "null"], "default": null},
    "annual_income":                 {"type": ["number", "null"], "default": null},
    "conversion_amount":             {"type": ["number", "null"], "default": null},
    "conversion_schedule":           {"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}], "default": null},
    "roth_ira_balance_initial":      {"type": ["number", "null"], "default": null},
    "taxable_dollars_available":     {"type": ["number", "null"], "default": null},
    "annual_return":                 {"type": ["number", "null"], "default": null},
    "taxable_account_annual_return": {"type": ["number", "null"], "default": null},
    "model_years":                   {"type": ["integer", "null"], "default": null},
    "social_security":               {"type": ["number", "null"], "default": null},
    "rmd":                           {"type": ["number", "null"], "default": null},
    "irmaa":                         {"type": ["number", "null"], "default": null},
    "cost_basis":                    {"type": "number", "default": 0},
    "other_ordinary_income_by_year": {"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}], "default": null},
    "spending_need_after_tax_by_year": {"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}], "default": null}
  }
}
```

### Output Data Schema

```json
{
  "status": "complete | incomplete",
  "inputs": {
    "current_age": 55,
    "retirement_age": 65,
    "filing_status": "married_joint",
    "state": "CA",
    "annual_income": 150000,
    "trad_ira_balance": 500000,
    "conversion_schedule": [50000, 50000, 50000, 50000, 50000],
    "roth_ira_balance_initial": 0,
    "taxable_dollars_available": 0,
    "cost_basis": 0
  },
  "assumptions": {
    "annual_return": 0.07,
    "taxable_account_annual_return": 0.07,
    "model_years": 30
  },
  "auto_filled": {
    "social_security": {"value": 0, "source": "age_based_default", "reason": "Age < 62"},
    "rmd": {"value": 0, "source": "age_based_default", "reason": "Age < 73"},
    "irmaa": {"value": 0, "source": "age_based_default", "reason": "Income < MFJ threshold"}
  },
  "missing": ["retirement_age"],
  "errors": []
}
```

### Error Response

```json
{
  "status": "error",
  "errors": [
    {"field": "current_age", "message": "Age must be between 18 and 100"},
    {"field": "conversion_amount", "message": "Conversion amount must be ≤ IRA balance"}
  ]
}
```

---

## Tool 2: estimate_tax_components

**Purpose**: Compute full tax breakdown for a conversion amount.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "annual_income":        {"type": ["number", "null"], "default": null},
    "conversion_amount":    {"type": ["number", "null"], "default": null},
    "filing_status":        {"type": ["string", "null"], "default": null},
    "state":                {"type": ["string", "null"], "default": null},
    "cost_basis":           {"type": "number", "default": 0},
    "social_security":      {"type": "number", "default": 0},
    "rmd":                  {"type": "number", "default": 0},
    "irmaa":                {"type": "number", "default": 0},
    "other_ordinary_income": {"type": "number", "default": 0}
  }
}
```

### Output Data Schema

```json
{
  "federal_tax": 16500.00,
  "state_tax": 4650.00,
  "irmaa_impact": 1977.60,
  "ss_tax_impact": 0,
  "rmd_tax": 0,
  "total_tax_cost": 23127.60,
  "effective_rate": 0.4625,
  "marginal_rate": 0.24,
  "bracket_before": "22%",
  "bracket_after": "24%",
  "conversion_amount": 50000
}
```

---

## Tool 3: analyze_roth_projections

**Purpose**: Year-by-year convert vs. no-convert comparison.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "trad_ira_balance":              {"type": ["number", "null"], "default": null},
    "roth_ira_balance_initial":      {"type": "number", "default": 0},
    "conversion_schedule":           {"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}], "default": null},
    "annual_return":                 {"type": "number", "default": 0.07},
    "taxable_account_annual_return": {"type": "number", "default": 0.07},
    "taxable_dollars_available":     {"type": "number", "default": 0},
    "model_years":                   {"type": "integer", "default": 30},
    "current_age":                   {"type": ["integer", "null"], "default": null},
    "federal_tax":                   {"type": ["number", "null"], "default": null},
    "state_tax":                     {"type": ["number", "null"], "default": null},
    "social_security":               {"type": "number", "default": 0},
    "rmd":                           {"type": "number", "default": 0},
    "other_ordinary_income_by_year": {"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}], "default": null},
    "spending_need_after_tax_by_year": {"anyOf": [{"type": "array", "items": {"type": "number"}}, {"type": "null"}], "default": null}
  }
}
```

### Output Data Schema

```json
{
  "projections": [
    {
      "year": 1,
      "age": 56,
      "conversion": 50000,
      "roth_balance": 35260.00,
      "trad_balance": 481500.00,
      "tax_paid": 16500.00,
      "rmd_amount": 0
    }
  ],
  "summary": {
    "final_roth_value": 450000.00,
    "final_trad_value": 380000.00,
    "net_benefit": 70000.00,
    "crossover_year": 12
  }
}
```

---

## Tool 4: optimize_conversion_schedule

**Purpose**: Find optimal multi-year conversion schedule using greedy bracket-fill.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "trad_ira_balance":        {"type": ["number", "null"], "default": null},
    "annual_income":           {"type": ["number", "null"], "default": null},
    "filing_status":           {"type": ["string", "null"], "default": null},
    "state":                   {"type": ["string", "null"], "default": null},
    "current_age":             {"type": ["integer", "null"], "default": null},
    "retirement_age":          {"type": ["integer", "null"], "default": null},
    "model_years":             {"type": "integer", "default": 30},
    "annual_return":           {"type": "number", "default": 0.07},
    "max_annual_conversion":   {"type": ["number", "null"], "default": null},
    "target_tax_bracket":      {"type": ["string", "null"], "enum": ["10%", "12%", "22%", "24%", "32%", "35%", "37%", null], "default": null},
    "optimization_goal":       {"type": "string", "enum": ["minimize_tax", "maximize_wealth"], "default": "minimize_tax"}
  }
}
```

### Output Data Schema

```json
{
  "optimal_schedule": [50000, 50000, 50000, 45000, 0, 0, 0, 0, 0, 0],
  "total_tax_cost": 52000.00,
  "tax_saved_vs_baseline": 15000.00,
  "optimization_goal": "minimize_tax",
  "converged": true,
  "confidence": 1.0
}
```

---

## Tool 5: breakeven_analysis

**Purpose**: Compute years until Roth path >= Traditional path.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "conversion_amount":  {"type": ["number", "null"], "default": null},
    "total_tax_cost":     {"type": ["number", "null"], "default": null},
    "current_age":        {"type": ["integer", "null"], "default": null},
    "annual_return":      {"type": "number", "default": 0.07},
    "retirement_age":     {"type": "integer", "default": 65},
    "future_tax_rate":    {"type": ["number", "null"], "default": null},
    "federal_tax":        {"type": ["number", "null"], "default": null},
    "state_tax":          {"type": ["number", "null"], "default": null}
  }
}
```

### Output Data Schema

```json
{
  "breakeven_years": 8,
  "breakeven_age": 63,
  "assessment": "worth_it"
}
```

**Assessment Rules**:
- `breakeven_years < 10` → `"worth_it"`
- `10 ≤ breakeven_years ≤ 20` → `"marginal"`
- `breakeven_years > 20` or never → `"not_worth_it"`

---

## Tool 6: generate_conversion_report

**Purpose**: Assemble all tool results into comprehensive styled HTML report.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "validated_inputs":  {"type": ["string", "null"], "default": null},
    "tax_analysis":      {"type": ["string", "null"], "default": null},
    "projection_data":   {"type": "string", "default": ""},
    "optimization_data": {"type": "string", "default": ""},
    "breakeven_data":    {"type": "string", "default": ""}
  }
}
```

**Note**: All inputs are JSON strings (serialized tool results). The report tool parses them internally.

### Output Data Schema

```json
{
  "summary": {
    "total_tax_cost": 23127.60,
    "net_benefit": 70000.00,
    "breakeven_years": 8,
    "assessment": "worth_it",
    "sections_included": ["inputs", "tax", "projection", "optimization", "breakeven"]
  }
}
```

The `display` field contains the full styled HTML report (1000+ chars).

---

## Tool Dependency Graph

```
Tool 1 (validate) ──> Tool 2 (tax) ──┬──> Tool 3 (projection)  ──┐
                                      ├──> Tool 4 (optimizer)    ──┼──> Tool 6 (report)
                                      └──> Tool 5 (breakeven)    ──┘
```

- Tool 1 is always called first (gateway)
- Tool 2 depends on Tool 1 outputs
- Tools 3, 4, 5 depend on Tool 2 but NOT on each other (parallel execution)
- Tool 6 depends on all prior tools (handles missing sections gracefully)
