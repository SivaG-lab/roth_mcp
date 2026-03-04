---
name: code-documentation-doc-generate
description: >
  Generate comprehensive, maintainable documentation from code. Produces
  API docs, architecture diagrams, user guides, and technical references
  using code analysis and industry best practices. Use when generating
  docs from code, building doc pipelines, or standardizing documentation.
  Triggers: generate docs, doc generation, api docs from code,
  auto document, documentation pipeline, living documentation.
user-invokable: true
argument-hint: "<codebase or module to document>"
---

# Automated Documentation Generation

Generate comprehensive, maintainable documentation from code with consistent terminology and structure.

## When to Use

- Generating API, architecture, or user documentation from code
- Building documentation pipelines or automation
- Standardizing docs across a repository

## When NOT to Use

- No codebase or source of truth exists
- Only need ad-hoc explanations (use code-explain)
- Cannot access code or requirements

---

## Documentation Types

| Type | Audience | Source | Output |
|------|----------|--------|--------|
| **API Reference** | Developers | Route handlers, schemas | Endpoint docs |
| **Architecture** | Tech leads | Module structure, imports | System diagrams |
| **User Guide** | End users | Features, workflows | How-to guides |
| **Code Comments** | Contributors | Complex logic | Inline docs |
| **Changelog** | All | Git history, PRs | Release notes |

---

## Generation Workflow

### Step 1: Analyze Codebase

```bash
# Identify documentation targets
# - Public API surface (routes, exported functions)
# - Data models (Pydantic, TypedDict, dataclasses)
# - Configuration (env vars, settings)
# - Entry points (main, CLI, app factory)
```

### Step 2: Extract Documentation Sources

| Source | What to Extract |
|--------|----------------|
| **Docstrings** | Function/class descriptions |
| **Type hints** | Parameter and return types |
| **Decorators** | Route paths, methods, auth |
| **Pydantic models** | Field names, types, defaults, descriptions |
| **Config files** | Environment variables, feature flags |
| **Tests** | Usage examples, expected behavior |

### Step 3: Generate Structured Output

**API Endpoint Template:**

```markdown
## `POST /v1/extract`

Extract structured data from a document.

**Request:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | PDF or image file |
| schema | object | Yes | JSON Schema for extraction |
| prompt | string | No | Additional instructions |

**Response (200):**
```json
{
  "data": { ... },
  "confidence": { ... },
  "sources": [ ... ]
}
```

**Errors:**
- `400` — Invalid schema or missing file
- `422` — Extraction failed validation
```

### Step 4: Add Automation

```yaml
# .github/workflows/docs.yml
name: Generate Docs
on:
  push:
    branches: [main]
    paths: ['src/**', 'docs/**']
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pdoc mkdocs
      - run: pdoc src/ -o docs/api/
      - run: mkdocs build
```

---

## Tools by Language

| Language | Tool | Command |
|----------|------|---------|
| Python | pdoc | `pdoc src/ -o docs/` |
| Python | Sphinx | `sphinx-apidoc -o docs/ src/` |
| Python | mkdocstrings | `mkdocs serve` |
| TypeScript | TypeDoc | `typedoc --out docs src/` |
| Rust | rustdoc | `cargo doc --open` |
| Go | godoc | `godoc -http=:6060` |

---

## Best Practices

| Do | Don't |
|----|-------|
| Generate from code (single source of truth) | Write docs manually that drift |
| Include working examples from tests | Use placeholder data |
| Document public API surface | Document every private function |
| Add CI step to regenerate on change | Rely on manual updates |
| Use consistent terminology | Mix naming conventions |

---

## Safety

- Never expose secrets, internal URLs, or credentials in generated docs
- Redact PII from example outputs
- Mark internal-only APIs clearly

## Checklist

- [ ] Documentation targets identified (API, architecture, user guide)
- [ ] Code analysis extracts types, routes, models
- [ ] Generated docs match actual code behavior
- [ ] CI pipeline regenerates on code changes
- [ ] Examples are tested and working
- [ ] No secrets or sensitive data exposed
