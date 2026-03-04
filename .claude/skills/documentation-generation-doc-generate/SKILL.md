---
name: documentation-generation-doc-generate
description: >
  Generate and maintain living documentation that stays synchronized with
  code. Covers doc pipelines, CI integration, multi-format output, and
  docs-as-code workflows. Use when building documentation systems,
  automating doc updates, or creating doc-as-code pipelines.
  Triggers: documentation pipeline, docs as code, auto docs,
  living documentation, doc generation system, mkdocs, sphinx.
user-invokable: true
argument-hint: "<documentation system or pipeline to build>"
---

# Documentation Generation Pipeline

Build documentation systems that stay synchronized with code through automation, CI integration, and docs-as-code workflows.

## When to Use

- Building documentation pipelines (CI/CD integrated)
- Setting up docs-as-code workflows
- Automating multi-format doc generation (HTML, PDF, Markdown)
- Creating living documentation that updates with code changes

## When NOT to Use

- One-time doc writing (use doc-coauthoring)
- Explaining specific code (use code-explain)
- API-only docs (use api-documentation-generator)

---

## Docs-as-Code Stack

| Layer | Tool Options | Purpose |
|-------|-------------|---------|
| **Source** | Markdown, RST, AsciiDoc | Content format |
| **Build** | MkDocs, Sphinx, Docusaurus | Static site generation |
| **API** | pdoc, TypeDoc, Swagger | Auto-generated from code |
| **Diagram** | Mermaid, PlantUML, D2 | Visual documentation |
| **CI** | GitHub Actions, GitLab CI | Auto-build on push |
| **Host** | GitHub Pages, Netlify, Vercel | Deployment |

---

## Quick Start: MkDocs (Python)

### Setup

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]

mkdocs new my-docs
```

### Configuration

```yaml
# mkdocs.yml
site_name: My Project
theme:
  name: material
  palette:
    scheme: slate

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
            show_root_heading: true

nav:
  - Home: index.md
  - API Reference: api/
  - Architecture: architecture.md
  - Contributing: contributing.md
```

### Auto-Generate API Docs

```markdown
<!-- docs/api/index.md -->
# API Reference

::: mypackage.core
    options:
      show_root_heading: true
      members_order: source

::: mypackage.models
```

---

## Quick Start: Sphinx (Python)

```bash
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

sphinx-quickstart docs/
sphinx-apidoc -o docs/api/ src/
sphinx-build -b html docs/ docs/_build/
```

---

## CI Integration

### GitHub Actions

```yaml
name: Docs
on:
  push:
    branches: [main]
    paths: ['src/**', 'docs/**', 'mkdocs.yml']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install mkdocs-material mkdocstrings[python]
      - run: mkdocs gh-deploy --force
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: docs-build
        name: Verify docs build
        entry: mkdocs build --strict
        language: system
        pass_filenames: false
```

---

## Multi-Format Output

| Format | Tool | Use Case |
|--------|------|----------|
| **HTML** | MkDocs/Sphinx | Web docs site |
| **PDF** | mkdocs-with-pdf, Sphinx LaTeX | Offline/printed docs |
| **Markdown** | pdoc --format md | GitHub-native docs |
| **OpenAPI** | FastAPI auto-docs | Interactive API explorer |

---

## Documentation Quality Checks

```bash
# Link checking
linkchecker site/

# Spell checking
npx cspell "docs/**/*.md"

# Vale prose linting
vale docs/
```

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Hand-write API docs | Generate from code + docstrings |
| Deploy docs manually | CI auto-deploys on merge |
| Let docs drift from code | Build fails if docs break |
| One giant README | Structured site with navigation |
| Skip version pinning | Pin doc tool versions in CI |

---

## Checklist

- [ ] Docs build tool selected and configured
- [ ] API docs auto-generated from code
- [ ] CI pipeline builds and deploys docs
- [ ] Link checker runs in CI
- [ ] Docs build fails on broken references
- [ ] Search is enabled
- [ ] No secrets or internal URLs in published docs
