---
name: incident-response-smart-fix
description: "Systematic incident response and debugging workflow using multi-agent orchestration. Four phases: Issue Analysis, Root Cause Investigation, Fix Implementation, Verification. Use when diagnosing production incidents, performing root cause analysis, debugging distributed system failures, or resolving complex bugs with AI-assisted tools."
---

# Intelligent Issue Resolution with Multi-Agent Orchestration

## Purpose

Systematic four-phase debugging and resolution pipeline that combines AI-assisted debugging tools with observability platforms to diagnose and resolve production issues.

## When to Use

- Investigating production incidents or outages
- Debugging complex multi-service failures
- Performing root cause analysis on recurring issues
- Resolving regressions after deployments

## When NOT to Use

- Simple bugs with obvious fixes
- Feature development without incidents
- Issues with no logs, traces, or reproduction steps

## Four-Phase Workflow

### Phase 1: Issue Analysis
**Goal:** Understand the full context of the failure.

1. Collect error traces, logs, and reproduction steps
2. Identify affected services and upstream/downstream impacts
3. Check recent deployments, config changes, or dependency updates
4. Establish timeline: when did it start? Is it intermittent?

**Tools:** Sentry, DataDog, OpenTelemetry, CloudWatch, structured logs

### Phase 2: Root Cause Investigation
**Goal:** Isolate the exact failure mechanism.

1. Deep code analysis around the failure point
2. Run `git bisect` to identify the introducing commit
3. Check dependency compatibility (version conflicts, breaking changes)
4. Inspect state: database, cache, queue, external API responses
5. Reproduce locally with minimal test case

**Techniques:**
- Distributed tracing to follow request flow across services
- Binary search through recent commits
- State inspection at each service boundary

### Phase 3: Fix Implementation
**Goal:** Implement minimal, safe fix with test coverage.

1. Write failing test that reproduces the bug
2. Implement minimal fix (smallest change that resolves the issue)
3. Add unit + integration tests for the fix
4. Add edge case tests for related scenarios
5. Follow production-safe practices (feature flags, gradual rollout)

**Principle:** Understand root cause before fixing symptoms.

### Phase 4: Verification
**Goal:** Confirm fix resolves the issue without regressions.

1. Run full regression suite
2. Performance benchmarks (ensure no degradation)
3. Security scan (if relevant)
4. Deploy to staging, verify with production-like traffic
5. Monitor for 24-48h after production deploy

### Post-Incident

1. Write blameless postmortem documenting timeline, root cause, fix
2. Add monitoring/alerting for the failure mode
3. Implement preventive measures (type checks, validation, static analysis)
4. Update runbooks with new failure pattern

## Success Metrics

- **MTTR** (Mean Time to Recovery) — reduced over time
- **Recurrence rate** — same issue should not repeat
- **Blast radius** — fix should not introduce new issues
- **Detection time** — improved monitoring catches issues earlier

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.
