---
name: security-bluebook-builder
description: "Build comprehensive security Blue Books (security documentation packages) for sensitive applications. Use when creating security assessments, threat models, security architecture documentation, compliance evidence packages, or security review documents for applications handling sensitive data."
metadata:
    source: "https://github.com/SHADOWPR0/security-bluebook-builder"
    risk: safe
---

# Security Bluebook Builder

## Purpose

Create comprehensive security Blue Books — structured documentation packages that capture an application's security posture, threat model, controls, and compliance evidence.

## When to Use

- Creating security documentation for new applications
- Preparing for security audits or compliance reviews
- Documenting threat models and risk assessments
- Building security architecture documentation
- Creating incident response plans
- Preparing evidence packages for SOC2, PCI DSS, HIPAA

## Blue Book Structure

### 1. Application Overview
- Application name, version, and purpose
- Data classification (public, internal, confidential, restricted)
- Technology stack and dependencies
- Architecture diagram (use mermaid-expert skill)
- Data flow diagram

### 2. Threat Model
- **Assets**: What needs protection (data, services, credentials)
- **Threat Actors**: Who might attack (external, insider, automated)
- **Attack Surface**: Entry points (APIs, UI, file uploads, integrations)
- **STRIDE Analysis**: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege
- **Risk Matrix**: Likelihood x Impact scoring

### 3. Security Controls
- **Authentication**: Method (OAuth2, JWT, SAML), MFA, session management
- **Authorization**: RBAC, ABAC, resource-level permissions
- **Data Protection**: Encryption at rest (AES-256), in transit (TLS 1.3)
- **Input Validation**: Sanitization, parameterized queries, CSP
- **Logging & Monitoring**: Audit logs, alerting, SIEM integration
- **Network Security**: Firewall rules, VPC, WAF, rate limiting

### 4. Compliance Mapping
- Map controls to compliance frameworks (SOC2, PCI DSS, HIPAA, GDPR)
- Evidence artifacts for each control
- Gap analysis and remediation plan

### 5. Incident Response
- Severity classification (P1-P4)
- Escalation procedures
- Communication templates
- Recovery procedures
- Post-incident review process

## Template

```markdown
# Security Blue Book: [Application Name]

**Version:** 1.0 | **Date:** YYYY-MM-DD | **Classification:** CONFIDENTIAL
**Owner:** [Team/Person] | **Review Cycle:** Quarterly

## 1. Application Profile
- **Purpose:** [What the app does]
- **Data Sensitivity:** [Classification level]
- **Users:** [Who uses it, estimated count]
- **Dependencies:** [External services, APIs]

## 2. Architecture
[Mermaid diagram or description]

## 3. Threat Model
| Threat | Likelihood | Impact | Risk | Mitigation |
|--------|-----------|--------|------|------------|
| [Threat] | H/M/L | H/M/L | Score | [Control] |

## 4. Security Controls
| Control | Status | Evidence | Owner |
|---------|--------|----------|-------|
| [Control] | Implemented/Planned | [Link] | [Person] |

## 5. Compliance
| Requirement | Framework | Status | Evidence |
|-------------|-----------|--------|----------|
| [Req] | SOC2/PCI/HIPAA | Met/Gap | [Link] |

## 6. Incident Response
[Procedures and contacts]
```

## Best Practices

1. **Review quarterly** — Security posture changes with every deployment
2. **Version control** — Track changes to security documentation
3. **Evidence-based** — Link to actual artifacts, not just descriptions
4. **Living document** — Update after incidents, audits, architecture changes
5. **Accessible** — Store where the security team can find and update it

## Related Skills

- `vulnerability-scanner` — Identify vulnerabilities to document
- `security-scanning-security-sast` — Static analysis findings for evidence
- `security-compliance-compliance-check` — Compliance framework mapping
