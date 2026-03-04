# Feature Specification: Test Hardening & Quality Assurance

**Feature Branch**: `008-test-hardening`
**Created**: 2026-03-02
**Status**: Draft
**Input**: User description: "Build the Test Hardening & Quality Assurance feature from docs/Test_Hardening_Requirements_v1.md. 44-requirement test infrastructure initiative covering P0-P5 priorities."
**Source Document**: `docs/Test_Hardening_Requirements_v1.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix All Broken Tests (Priority: P1)

A developer runs the full test suite and expects all tests to pass. Currently 19 tests fail and 1 is skipped across 4 suites due to stale assertions, outdated selectors, and mismatched API mocks from the v4 migration. The developer needs these fixed so the test suite provides a trustworthy signal.

**Why this priority**: Broken tests undermine confidence in the entire test suite. No other improvements matter if the baseline tests are failing. This is the prerequisite for all other work.

**Independent Test**: Run `pytest tests/integration/test_v4_api_playwright.py -k health`, `npx playwright test accessibility.spec.ts`, `npx playwright test document-viewer.spec.ts`, and `npx playwright test extract-flow.spec.ts`. All should pass.

**Acceptance Scenarios**:

1. **Given** the V4 API test suite, **When** the health check test runs, **Then** it asserts the status is one of "healthy", "degraded", or "unhealthy" (not "ok").
2. **Given** the UI accessibility tests, **When** sidebar navigation buttons are located, **Then** selectors use the v4 label names ("Extract", "Generator") not the v3 names ("Extract & Compare", "Schema Generator").
3. **Given** the document viewer E2E tests, **When** extraction API calls are mocked, **Then** mocks intercept `/v4/extract` (not `/v1/extract`) and return the `ExtractionResponseV4` shape with `request_id`, `documents[]`, and `fields[]`.
4. **Given** the extract flow tests, **When** the "Extract" navigation button is clicked, **Then** the selector is scoped to the navigation region to avoid matching "Use in Extract" action buttons.

---

### User Story 2 - Reliable Test Infrastructure (Priority: P1)

A developer working on the IDP pipeline runs `pytest tests/integration/test_idp_e2e.py` and all 14 tests fail because there is no automated server lifecycle management. The test fixtures also use Windows-only process management (`taskkill`), preventing macOS/Linux contributors from running the suite. Developers need tests that start their own servers, handle crashes gracefully, and work on any operating system.

**Why this priority**: 14 out of 149 tests are structurally broken (not just assertion failures). Without infrastructure fixes, these tests can never pass regardless of other improvements.

**Independent Test**: Run `pytest tests/integration/test_idp_e2e.py` on a clean checkout without manually starting the server. Tests should either pass or skip gracefully with a clear message. Run the same on Windows, macOS, and Linux.

**Acceptance Scenarios**:

1. **Given** the IDP E2E test suite, **When** no server is running, **Then** a session-scoped fixture automatically starts the FastAPI server, polls `/health` for readiness (30s timeout), and tears it down after tests complete.
2. **Given** a test fixture that manages server processes, **When** running on any operating system, **Then** process termination uses cross-platform APIs (not `taskkill`).
3. **Given** a module-scoped server fixture, **When** the server process crashes mid-suite, **Then** subsequent tests detect the dead server and skip with a diagnostic message instead of cascading 9+ failures.
4. **Given** auth tests that modify internal state, **When** a test fails mid-execution, **Then** the `_valid_keys` dict is automatically restored via `monkeypatch` (no manual cleanup required).
5. **Given** tests using `asyncio.get_event_loop()`, **When** running on Python 3.12+, **Then** the deprecated call is replaced with `asyncio.run()` and no deprecation warnings are emitted.

---

### User Story 3 - Close FR Coverage Gaps (Priority: P2)

A quality engineer reviews the API hardening spec (006) and finds that 14 of 37 functional requirements have zero test coverage, and 4 more have only superficial coverage. Security-critical requirements like JWT validation (FR-004), rate limiting (FR-015), and file size validation (FR-034) are untested. The engineer needs dedicated tests for each gap.

**Why this priority**: 41% FR coverage gap is unacceptable for a security hardening initiative. Coverage gaps mean security-critical behaviors could regress silently.

**Independent Test**: Run each new test file/class independently. Each covers a specific FR and can be verified against the FR's specification in the hardening doc.

**Acceptance Scenarios**:

1. **Given** JWT validation code, **When** an expired token is submitted, **Then** the API returns 401. **When** a tampered token is submitted, **Then** the API returns 401. **When** a valid token is submitted, **Then** authentication succeeds.
2. **Given** the extraction endpoint, **When** processing a request asynchronously, **Then** the `/health` endpoint responds within 500ms (event loop is not blocked).
3. **Given** a `safe_node()`-wrapped pipeline function, **When** it raises an exception, **Then** the error is captured in `state["errors"]` and state is returned (no propagation).
4. **Given** a rate-limited endpoint, **When** N+1 requests are sent in rapid succession, **Then** the (N+1)th request returns 429 with `RATE_LIMITED` error code.
5. **Given** a request with a spoofed `Content-Length` header, **When** the actual body exceeds the declared size, **Then** the post-read validation rejects it.
6. **Given** the visual verification agent with default config, **When** extraction runs, **Then** the agent logs a skip message and does not call the external API.
7. **Given** the disk-based cache, **When** image bytes are written through the cache, **Then** a file is created on disk and retrieval returns identical bytes.
8. **Given** the `rapidfuzz` dependency, **When** the fuzz module is accessed, **Then** its module path starts with "rapidfuzz" (not "thefuzz").
9. **Given** SSE progress tracking, **When** an extraction completes, **Then** the progress endpoint returns events with `event:` and `data:` fields containing valid JSON.

---

### User Story 4 - Improve Test Quality and Patterns (Priority: P3)

A developer reviews test results and notices that extraction tests accept both 200 and 500 status codes, making regressions invisible. The CORS test permits wildcard origins which contradicts the security spec. HTML reports inject unescaped user data. Old evidence files accumulate. The developer needs tests that are precise, safe, and clean.

**Why this priority**: Quality issues reduce test signal — tests that always pass regardless of outcome are worse than no tests because they create false confidence.

**Independent Test**: Run each quality improvement in isolation. Verify CORS test rejects wildcards, extraction tests are split by expected outcome, HTML reports are XSS-safe, evidence directories are cleaned between runs.

**Acceptance Scenarios**:

1. **Given** the CORS preflight test, **When** checking `Access-Control-Allow-Origin`, **Then** the wildcard `"*"` is not in the acceptable values list.
2. **Given** an extraction test with no OpenAI key, **When** it runs, **Then** it expects 500 (not 200-or-500). **Given** an extraction test with a valid key, **When** it runs, **Then** it expects 200.
3. **Given** Playwright-based test scripts, **When** they execute, **Then** they use in-process `playwright.sync_api` (not subprocess spawning).
4. **Given** extraction results containing user data, **When** the HTML report is generated, **Then** all user-controlled values are escaped via `html.escape()`.
5. **Given** a new test session, **When** it starts, **Then** stale evidence files from previous runs are cleaned up.

---

### User Story 5 - Automated CI/CD Test Execution (Priority: P4)

A team lead wants to ensure tests run automatically on every push and PR. Currently there is no CI/CD pipeline — all test execution is manual. The team needs GitHub Actions workflows for both Python and TypeScript test suites, with evidence artifacts uploaded for debugging.

**Why this priority**: Without CI/CD, all testing improvements are only as reliable as the developer who remembers to run them. Automation is the force multiplier.

**Independent Test**: Push a commit and verify GitHub Actions runs both workflows, executes tests, and uploads artifacts.

**Acceptance Scenarios**:

1. **Given** a push to `main` or a PR, **When** GitHub Actions triggers, **Then** a Python test workflow installs Python 3.12, runs `pytest tests/test_api_hardening.py -v`, and uploads evidence artifacts.
2. **Given** a push to `main` or a PR, **When** GitHub Actions triggers, **Then** a UI E2E workflow installs Node.js, runs `npx playwright test`, configures `trace: 'on-first-retry'`, and uploads screenshots/traces as artifacts.
3. **Given** test configuration, **When** `pytest-asyncio` runs, **Then** no deprecation warning is emitted (default scope configured).
4. **Given** concurrent CI jobs running test suites, **When** servers start, **Then** dynamic port allocation prevents port conflicts.

---

### User Story 6 - UI E2E Test Alignment with V4 (Priority: P5)

A front-end developer working on the v4 UI needs comprehensive E2E test coverage. Currently there are no accessibility scans (axe-core), screenshot tests never compare baselines, mock responses use the v1 shape, locators are duplicated across specs, and there are zero error-state tests. The developer needs a modern, maintainable E2E test suite aligned with the v4 API.

**Why this priority**: These are enhancements that improve long-term maintainability and coverage. They build on the foundation established by P0-P4 work.

**Independent Test**: Run `npx playwright test` in the `prism-ui` directory. Verify axe-core scans pass, visual regression baselines are compared, Page Object Models are used, and error states are covered.

**Acceptance Scenarios**:

1. **Given** the accessibility test suite, **When** axe-core scans a page, **Then** zero WCAG 2.1 AA violations are reported.
2. **Given** screenshot tests, **When** they run, **Then** screenshots are compared against baselines using `toHaveScreenshot()` with a pixel tolerance, not just captured and ignored.
3. **Given** tests that mock extraction responses, **When** building mock data, **Then** a shared `ExtractionResponseV4` builder is used (not inline v1-shaped objects).
4. **Given** E2E tests for navigation and extraction, **When** locating UI elements, **Then** Page Object Models (`SidebarNav`, `ExtractView`, `SchemaGenerator`) encapsulate selectors.
5. **Given** the UI E2E suite, **When** the API returns 500 or times out, **Then** error state tests verify appropriate user-facing error messages.
6. **Given** theme toggle buttons, **When** each theme is selected, **Then** the appropriate CSS class or `data-theme` attribute is applied.
7. **Given** mobile viewports (375x667, 768x1024), **When** the app loads, **Then** layout adapts correctly.

---

### Edge Cases

- What happens when the test server fails to start within the 30-second timeout? Tests skip gracefully with a diagnostic message.
- How does the system handle concurrent test suites binding to the same port? Dynamic port allocation (`port=0`) prevents conflicts.
- What happens when OpenAI API key is not configured? Tests that require it are skipped with a clear message; tests that don't need it use mocks.
- What happens when Playwright browsers are not installed? CI workflows include explicit browser installation steps; local runs provide actionable error messages.
- How does the visual regression system handle cross-platform font rendering differences? Baselines are maintained on a single consistent platform (Linux CI runner) with pixel tolerance.
- What if a bare `except` is reintroduced in a future commit? AST-based or grep-based static analysis tests catch regressions automatically.

## Requirements *(mandatory)*

### Functional Requirements

**P0 — Critical Test Fixes**
- **FR-001**: System MUST fix the V4 API health check assertion to accept "healthy", "degraded", or "unhealthy" status values instead of "ok".
- **FR-002**: System MUST update UI E2E sidebar selectors to use v4 label names ("Extract", "Generator") instead of v3 names.
- **FR-003**: System MUST update document viewer E2E mocks to intercept `/v4/extract` and return `ExtractionResponseV4`-shaped responses.
- **FR-004**: System MUST scope the extract flow navigation button selector to the navigation region to avoid ambiguous matches.

**P1 — Test Infrastructure**
- **FR-005**: System MUST provide an automated server lifecycle fixture for IDP E2E tests that starts, health-checks, and tears down the FastAPI server.
- **FR-006**: System MUST use cross-platform process management APIs for server termination (not Windows-only `taskkill`).
- **FR-007**: System MUST detect server crashes mid-suite and skip remaining tests with a diagnostic message instead of cascading failures.
- **FR-008**: System MUST replace deprecated `asyncio.get_event_loop()` calls with `asyncio.run()` or `@pytest.mark.asyncio`.
- **FR-009**: System MUST use `monkeypatch.setattr()` for `_valid_keys` mutation in auth tests for automatic cleanup.

**P2 — Coverage Gaps**
- **FR-010**: System MUST test JWT validation including valid tokens, expired tokens, wrong issuer, tampered payloads, and unreachable JWKS endpoints.
- **FR-011**: System MUST verify that extraction processing does not block the event loop (health endpoint responds within 500ms during extraction).
- **FR-012**: System MUST test `safe_node()` error recovery: exception capture in state, normal operation, and all node wrapping verification.
- **FR-013**: System MUST test rate limiting: verify 429 response with `RATE_LIMITED` code after exceeding the request limit.
- **FR-014**: System MUST test post-read file size validation: spoofed `Content-Length` rejection and malformed header handling.
- **FR-015**: System MUST test visual verification agent default-off behavior: skip message logged, no external API calls.
- **FR-016**: System MUST test async file I/O usage: verify `asyncio.to_thread()` is called for file writes.
- **FR-017**: System MUST test classification confidence threshold comparison as float (not string-keyed dict).
- **FR-018**: System MUST test checkpoint saver wiring in `compile_v4_graph()`.
- **FR-019**: System MUST test that `render_bridge.py` uses a module-level `ThreadPoolExecutor`.
- **FR-020**: System MUST test batch visual verification grouping: one VLM call per page, not per field.
- **FR-021**: System MUST verify no bare `except` patterns exist in ingestion, parallel, and classify agent modules.
- **FR-022**: System MUST test token usage capture in agents calling `get_openai_client()`.
- **FR-023**: System MUST test structured logging output format: JSON with required fields.
- **FR-024**: System MUST test classify agent optimization: first-page-only by default, retry with additional pages on low confidence.
- **FR-025**: System MUST strengthen disk-based cache test with actual write/read/verify cycle.
- **FR-026**: System MUST strengthen rapidfuzz test to assert module path starts with "rapidfuzz".
- **FR-027**: System MUST strengthen SSE progress test to verify event/data fields with valid JSON payloads.

**P3 — Test Quality & Patterns**
- **FR-028**: System MUST remove wildcard `"*"` from acceptable CORS origin values in the preflight test.
- **FR-029**: System MUST split extraction tests into API-dependent (200 expected) and API-independent (500 expected) variants.
- **FR-030**: System MUST add `@pytest.mark.slow` marker for long-running tests with pytest configuration.
- **FR-031**: System MUST replace Playwright subprocess spawning with in-process `playwright.sync_api` usage.
- **FR-032**: System MUST apply `html.escape()` to all user-controlled values in HTML report generation.
- **FR-033**: System MUST add session-scoped cleanup of stale evidence files.

**P4 — CI/CD & Automation**
- **FR-034**: System MUST create a GitHub Actions workflow for Python tests triggered on push/PR.
- **FR-035**: System MUST create a GitHub Actions workflow for UI E2E tests triggered on push/PR.
- **FR-036**: System MUST configure `pytest-asyncio` default fixture loop scope to suppress deprecation warnings.
- **FR-037**: System MUST implement dynamic port allocation for test servers to prevent CI conflicts.

**P5 — UI E2E Migration Alignment**
- **FR-038**: System MUST integrate `@axe-core/playwright` for WCAG 2.1 AA compliance scanning.
- **FR-039**: System MUST convert screenshot captures to visual regression tests using `toHaveScreenshot()` with pixel tolerance.
- **FR-040**: System MUST create a shared V4 mock response builder replacing inline v1 mock objects.
- **FR-041**: System MUST create Page Object Models for sidebar navigation, extract view, and schema generator.
- **FR-042**: System MUST add error state UI tests: API failure, network timeout, unsupported file type, empty schema, multi-file upload.
- **FR-043**: System MUST add theme switching tests verifying CSS class/attribute application.
- **FR-044**: System MUST add mobile/responsive viewport tests for 375x667 and 768x1024 viewports.

### Key Entities

- **Test Suite**: A collection of related test cases organized by scope (unit, integration, E2E). Key attributes: file path, test count, pass/fail rate, priority tier.
- **Functional Requirement (FR)**: A specific behavior from the API hardening spec that needs test coverage. Key attributes: FR ID, coverage status (untested/partial/full), associated test IDs.
- **Test Fixture**: Shared setup/teardown logic for test execution. Key attributes: scope (function/module/session), dependencies (server, browser, API key).
- **CI/CD Workflow**: An automated pipeline definition. Key attributes: trigger events, job steps, artifact outputs.
- **Evidence Artifact**: Test output files (screenshots, JSON results, HTML reports) retained for audit. Key attributes: test run ID, file type, retention policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All tests pass — 0 failures across all test suites (currently 19 failures + 1 skip).
- **SC-002**: FR coverage reaches 95% or higher (currently 51% — 19/37 FRs fully tested).
- **SC-003**: Test count reaches 200+ (currently 149 tests across 5 suites).
- **SC-004**: Flaky test rate stays below 2% (max 4 flaky tests out of 200+).
- **SC-005**: Full test suite completes within 5 minutes on a standard development machine.
- **SC-006**: Tests run successfully on Windows, macOS, and Linux without platform-specific modifications.
- **SC-007**: CI/CD pipeline executes all test suites automatically on every push and PR.
- **SC-008**: No test requires manual server startup — all server lifecycle is automated via fixtures.
- **SC-009**: UI E2E tests detect visual regressions via baseline comparison (not just screenshot capture).
- **SC-010**: Zero WCAG 2.1 AA violations detected by automated accessibility scanning.

## Assumptions

- The existing API implementation is correct — only test-side changes are in scope.
- OpenAI API key availability is optional; tests that require it will be skipped when unavailable.
- GitHub Actions is the CI/CD platform; no other CI systems are in scope.
- Playwright and pytest are the test frameworks — no migration to other frameworks.
- The v4 API and UI are the target; no backward-compatibility testing for v1/v3 is needed.
- Python 3.12+ and Node.js (current LTS) are the runtime environments.
- `psutil` can be added as a test dependency for cross-platform process management.
- The `@axe-core/playwright` package can be added as a dev dependency for accessibility testing.
