---
name: n8n-code-python
description: >
  Write Python code in n8n Code nodes. Use when writing Python in n8n,
  understanding _input/_json/_node syntax, working with standard library only,
  or debugging Python limitations in n8n. Covers mode selection, data access
  patterns, return format, webhook data nesting, and common error prevention.
  Triggers: n8n python, n8n code python, python code node, n8n _input,
  n8n _json, n8n standard library, python n8n webhook.
user-invokable: true
argument-hint: "<python task or pattern>"
metadata:
  origin: "https://github.com/czlonkowski/n8n-skills"
---

# Python Code Node (Beta)

Expert guidance for writing Python in n8n Code nodes.

## When to Use

- Writing Python logic in n8n Code nodes
- Need specific Python standard library functions
- Data transformations suited to list comprehensions
- Statistical analysis with `statistics` module

## Important: JavaScript First

Use **JavaScript for 95% of use cases**. Python only when you need standard library
features, are significantly more comfortable with Python, or need `statistics` module.

---

## Quick Start

```python
items = _input.all()

processed = []
for item in items:
    processed.append({
        "json": {
            **item["json"],
            "processed": True,
            "timestamp": datetime.now().isoformat()
        }
    })

return processed
```

### Essential Rules

1. Access data via `_input.all()`, `_input.first()`, or `_input.item`
2. **Must return** `[{"json": {...}}]` format (list of dicts with "json" key)
3. Webhook data is under `_json["body"]` (not `_json` directly)
4. **No external libraries** — standard library only
5. Use Python (Beta) mode for `_input`, `_now`, `_jmespath()` helpers

---

## Mode Selection

### Run Once for All Items (Default — 95% of cases)

Code runs once. Access all items with `_input.all()`.

```python
all_items = _input.all()
total = sum(item["json"].get("amount", 0) for item in all_items)

return [{"json": {"total": total, "count": len(all_items)}}]
```

### Run Once for Each Item

Code runs per item. Access current item with `_input.item`.

```python
item = _input.item
return [{"json": {**item["json"], "processed": True}}]
```

---

## Data Access Patterns

### _input.all() — Most Common

```python
all_items = _input.all()
valid = [item for item in all_items if item["json"].get("status") == "active"]

return [{"json": {"id": item["json"]["id"]}} for item in valid]
```

### _input.first() — Single Item

```python
data = _input.first()["json"]
return [{"json": {"result": process(data)}}]
```

### _node — Reference Other Nodes

```python
webhook_data = _node["Webhook"]["json"]
return [{"json": {"from_webhook": webhook_data}}]
```

See [DATA_ACCESS.md](DATA_ACCESS.md) for comprehensive patterns.

---

## Critical: Webhook Data Structure

**Most common mistake** — webhook data is nested under `["body"]`:

```python
# WRONG — KeyError
name = _json["name"]

# CORRECT — access via body
name = _json["body"]["name"]

# SAFEST — use .get()
webhook_data = _json.get("body", {})
name = webhook_data.get("name", "Unknown")
```

---

## Return Format

**Always return list of dicts with `"json"` key.**

```python
# Single result
return [{"json": {"field": value}}]

# Multiple results
return [{"json": {"id": 1}}, {"json": {"id": 2}}]

# From list comprehension
return [{"json": {"id": item["json"]["id"]}} for item in _input.all()]

# Empty (no results)
return []
```

**Wrong formats** (will break downstream nodes):

```python
return {"json": {"field": value}}       # Missing list wrapper
return [{"field": value}]               # Missing "json" key
return "processed"                       # Not a list of dicts
```

---

## No External Libraries

**Cannot import**: requests, pandas, numpy, scipy, BeautifulSoup, lxml.

**Available** (standard library only):

| Module | Use |
|--------|-----|
| `json` | Parse/serialize JSON |
| `datetime` | Date/time operations |
| `re` | Regular expressions |
| `base64` | Encoding/decoding |
| `hashlib` | Hashing (SHA256, MD5) |
| `urllib.parse` | URL parsing, query strings |
| `math` | Math functions |
| `statistics` | mean, median, stdev |
| `random` | Random numbers |

### Workarounds

| Need | Solution |
|------|----------|
| HTTP requests | Use **HTTP Request** node before Code node |
| Data analysis | Use `statistics` module or manual calculations |
| Web scraping | Use **HTTP Request** + **HTML Extract** nodes |
| Complex dates | Switch to JavaScript (Luxon available) |

See [STANDARD_LIBRARY.md](STANDARD_LIBRARY.md) for complete reference.

---

## Common Patterns

### Data Transformation

```python
items = _input.all()
return [
    {"json": {
        "id": item["json"].get("id"),
        "name": item["json"].get("name", "Unknown").upper(),
    }}
    for item in items
]
```

### Filtering & Aggregation

```python
items = _input.all()
total = sum(item["json"].get("amount", 0) for item in items)
valid = [i for i in items if i["json"].get("amount", 0) > 0]

return [{"json": {"total": total, "count": len(valid)}}]
```

### Regex Extraction

```python
import re
items = _input.all()
email_re = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

emails = set()
for item in items:
    emails.update(re.findall(email_re, item["json"].get("text", "")))

return [{"json": {"emails": list(emails), "count": len(emails)}}]
```

### Data Validation

```python
items = _input.all()
validated = []
for item in items:
    d = item["json"]
    errors = []
    if not d.get("email"): errors.append("Email required")
    if not d.get("name"): errors.append("Name required")
    validated.append({"json": {**d, "valid": not errors, "errors": errors or None}})

return validated
```

### Statistics

```python
from statistics import mean, median, stdev

values = [i["json"].get("value", 0) for i in _input.all() if "value" in i["json"]]
if not values:
    return [{"json": {"error": "No values found"}}]

return [{"json": {
    "mean": mean(values),
    "median": median(values),
    "stdev": stdev(values) if len(values) > 1 else 0,
    "min": min(values),
    "max": max(values),
}}]
```

See [COMMON_PATTERNS.md](COMMON_PATTERNS.md) for more patterns.

---

## Top 5 Mistakes

| # | Mistake | Fix |
|---|---------|-----|
| 1 | `import requests` | Use HTTP Request node or switch to JS |
| 2 | No return statement | Always `return [{"json": ...}]` |
| 3 | `return {"json": ...}` | Wrap in list: `return [{"json": ...}]` |
| 4 | `_json["name"]` (KeyError) | Use `.get("name", "default")` |
| 5 | `_json["email"]` from webhook | Access via `_json["body"]["email"]` |

See [ERROR_PATTERNS.md](ERROR_PATTERNS.md) for detailed solutions.

---

## Best Practices

- Always use `.get()` for dictionary access (prevents KeyError)
- Handle None/null: `amount = item["json"].get("amount") or 0`
- Use list comprehensions for filtering and transformation
- Return consistent structure from all code paths
- Debug with `print()` (appears in browser console F12)

---

## Python vs JavaScript Decision

| Use Python | Use JavaScript |
|------------|---------------|
| `statistics` module needed | HTTP requests (`$helpers.httpRequest`) |
| Strong Python syntax preference | Advanced dates (Luxon) |
| List comprehension-heavy logic | Better n8n integration |
| Specific stdlib functions | **95% of all use cases** |

---

## Pre-Deploy Checklist

- [ ] Considered JavaScript first
- [ ] Return statement exists in all code paths
- [ ] Return format: `[{"json": {...}}]`
- [ ] No external library imports
- [ ] Safe `.get()` for all dictionary access
- [ ] Webhook data accessed via `["body"]`
- [ ] Mode: "All Items" for batch, "Each Item" for per-item
- [ ] Output structure consistent across branches
