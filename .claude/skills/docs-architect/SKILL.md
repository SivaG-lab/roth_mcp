---
name: docs-architect
description: >
  Create comprehensive technical documentation from existing codebases.
  Analyzes architecture, design patterns, and implementation details to
  produce long-form technical manuals. Use when creating system
  documentation, architecture guides, onboarding docs, or technical
  deep-dives. Triggers: system documentation, architecture guide,
  technical manual, codebase documentation, onboarding docs.
user-invokable: true
argument-hint: "<codebase or system to document>"
metadata:
  model: sonnet
---

# Technical Documentation Architect

Create comprehensive, long-form documentation that captures both the "what" and the "why" of complex systems.

## When to Use

- Documenting entire systems or major components
- Creating architecture guides or technical manuals
- Building onboarding documentation for new team members
- Writing deep-dive technical references

## When NOT to Use

- Quick code explanations (use code-explain)
- API-only documentation (use api-documentation-generator)
- Ad-hoc notes or informal summaries

---

## Documentation Process

### Phase 1: Discovery

1. **Analyze structure** — map directories, modules, dependencies
2. **Identify components** — find key classes, services, data models
3. **Extract patterns** — recognize architecture decisions and conventions
4. **Map data flows** — trace how data moves through the system

### Phase 2: Structure

Plan the document hierarchy with progressive disclosure:

```markdown
# System Name — Technical Reference

## 1. Executive Summary (1 page)
## 2. Architecture Overview
## 3. Design Decisions & Rationale
## 4. Core Components (deep dive each)
## 5. Data Models & Storage
## 6. Integration Points & APIs
## 7. Deployment & Operations
## 8. Performance & Scaling
## 9. Security Model
## 10. Appendices (glossary, references)
```

### Phase 3: Write

- Start with executive summary for stakeholders
- Progress from bird's-eye to implementation details
- Include rationale for design decisions
- Use `file_path:line_number` references to actual code
- Add diagrams for every major component relationship

---

## Document Sections Guide

### Executive Summary

| Element | Purpose |
|---------|---------|
| One-liner | What the system does |
| Key metrics | Scale, performance, users |
| Tech stack | Languages, frameworks, infra |
| Architecture style | Monolith, microservices, event-driven |

### Architecture Overview

Use ASCII or Mermaid diagrams:

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client   │────▶│  API GW  │────▶│ Service  │
└──────────┘     └──────────┘     └──────────┘
                       │                │
                       ▼                ▼
                 ┌──────────┐    ┌──────────┐
                 │  Auth    │    │ Database │
                 └──────────┘    └──────────┘
```

### Design Decisions

For each major decision, use ADR-style format:

```markdown
### Decision: [Title]
**Context:** Why was this decision needed?
**Decision:** What was chosen?
**Alternatives:** What else was considered?
**Consequences:** What are the trade-offs?
```

---

## Output Standards

- **Format**: Markdown with clear heading hierarchy
- **Code blocks**: Syntax highlighting with language tags
- **References**: `file_path:line_number` for code locations
- **Diagrams**: ASCII art or Mermaid for every relationship
- **Length**: 10-100+ pages depending on system complexity
- **Audience paths**: Tag sections for developers, architects, operations

---

## Best Practices

| Do | Don't |
|----|-------|
| Explain the "why" behind decisions | Just describe the "what" |
| Use concrete code examples | Write abstract descriptions |
| Create mental models for readers | Assume domain knowledge |
| Document current state AND history | Only describe current code |
| Include troubleshooting guides | Ignore operational concerns |
| Provide reading paths by role | Write one-size-fits-all |

---

## Checklist

- [ ] Executive summary is understandable by non-technical stakeholders
- [ ] Architecture diagram covers all major components
- [ ] Each design decision has documented rationale
- [ ] Code references use `file_path:line_number` format
- [ ] Data flow is traced end-to-end
- [ ] Deployment and operations are documented
- [ ] Glossary defines all domain-specific terms
