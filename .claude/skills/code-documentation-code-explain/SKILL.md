---
name: code-documentation-code-explain
description: >
  Explain complex code through clear narratives, visual diagrams, and
  step-by-step breakdowns. Use when explaining algorithms, onboarding
  walkthroughs, teaching patterns, or debugging reasoning. Transforms
  difficult concepts into understandable explanations.
  Triggers: explain code, code walkthrough, how does this work,
  code explanation, algorithm breakdown, onboarding guide.
user-invokable: true
argument-hint: "<code or concept to explain>"
---

# Code Explanation & Analysis

Expert at explaining complex code through clear narratives, diagrams, and step-by-step breakdowns for developers at all levels.

## When to Use

- Explaining complex code, algorithms, or system behavior
- Creating onboarding walkthroughs or learning materials
- Producing step-by-step breakdowns with diagrams
- Teaching design patterns or debugging reasoning

## When NOT to Use

- Implementing new features or refactoring (use coding skills)
- Writing API docs or user documentation (use doc-generate)
- No code or design to analyze

---

## Explanation Framework

### Step 1: High-Level Summary

Start with the "what" and "why" before diving into "how."

```markdown
## What This Does
[One sentence: purpose and context]

## Why It Exists
[The problem it solves or requirement it fulfills]

## How It Works (Overview)
[2-3 sentence summary of the approach]
```

### Step 2: Architecture Map

Show the big picture with ASCII diagrams or Mermaid:

```
Input → [Parser] → AST → [Transformer] → IR → [Generator] → Output
                     ↓
               [Validator]
                     ↓
              Error Reports
```

### Step 3: Walk Through Key Components

For each component:
1. **Purpose** — What role it plays
2. **Inputs/Outputs** — What goes in, what comes out
3. **Key Logic** — The core algorithm or decision point
4. **Edge Cases** — What could go wrong

### Step 4: Annotated Code Walkthrough

```python
# STEP 1: Parse the document into pages
pages = re.split(r"--- Page \d+ ---\n?", raw_text)
# Why: Each page may contain different form sections.
# The regex matches the page delimiter inserted by ingestion.

# STEP 2: Extract fields per page
for i, page in enumerate(pages):
    fields = extract_fields(page, schema)
    # Why: Per-page extraction prevents cross-page hallucination.
    # The schema constrains what fields are valid.
```

### Step 5: Pitfalls & Edge Cases

| Scenario | What Happens | Why |
|----------|-------------|-----|
| Empty input | Returns `[]` | Guard clause at line 12 |
| Malformed JSON | Raises `ValueError` | Strict parsing mode |
| Concurrent access | Thread-safe via lock | `threading.Lock` at line 5 |

---

## Explanation Patterns

### Pattern 1: Top-Down (Recommended for Systems)

1. System purpose and boundaries
2. Major components and their relationships
3. Data flow between components
4. Deep dive into each component
5. Cross-cutting concerns (error handling, logging)

### Pattern 2: Bottom-Up (Recommended for Algorithms)

1. Core data structures
2. Basic operations on those structures
3. How operations compose into the algorithm
4. Complexity analysis (time and space)
5. Optimization techniques used

### Pattern 3: Trace-Through (Recommended for Debugging)

1. Pick a concrete input
2. Trace execution step by step
3. Show state at each decision point
4. Highlight where behavior diverges from expectation
5. Identify the root cause

---

## Diagram Types

| Type | Use For | Tool |
|------|---------|------|
| **Flowchart** | Control flow, decisions | Mermaid `flowchart` |
| **Sequence** | API calls, message passing | Mermaid `sequenceDiagram` |
| **Class/ER** | Data models, relationships | Mermaid `classDiagram` |
| **ASCII** | Quick inline diagrams | Plain text |
| **State** | State machines, lifecycles | Mermaid `stateDiagram` |

---

## Quality Checklist

- [ ] High-level summary comes before details
- [ ] Diagram shows component relationships
- [ ] Key decision points are explained (the "why")
- [ ] Edge cases and error paths are covered
- [ ] Code annotations reference specific line numbers
- [ ] Complexity analysis included for algorithms
- [ ] Reader can follow without running the code
