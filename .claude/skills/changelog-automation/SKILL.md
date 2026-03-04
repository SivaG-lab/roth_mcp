---
name: changelog-automation
description: >
  Automate changelog generation from commits, PRs, and releases following
  Keep a Changelog format. Use when setting up release workflows, generating
  release notes, standardizing commit conventions, or managing semantic
  versioning. Triggers: changelog, release notes, conventional commits,
  semver, keep a changelog, version bump, release workflow.
user-invokable: true
argument-hint: "<release workflow or changelog task>"
---

# Changelog Automation

Patterns and tools for automating changelog generation, release notes, and version management.

## When to Use

- Setting up automated changelog generation
- Implementing conventional commits
- Creating release note workflows
- Standardizing commit message formats
- Managing semantic versioning

---

## 1. Conventional Commits

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | SemVer | Description |
|------|--------|-------------|
| `feat` | MINOR | New feature |
| `fix` | PATCH | Bug fix |
| `docs` | — | Documentation only |
| `style` | — | Formatting, no logic change |
| `refactor` | — | Code change, no feature/fix |
| `perf` | PATCH | Performance improvement |
| `test` | — | Adding/fixing tests |
| `chore` | — | Build, tooling, deps |
| `ci` | — | CI/CD changes |
| `BREAKING CHANGE` | MAJOR | Footer or `!` after type |

### Examples

```bash
feat(auth): add OAuth2 login with Google
fix(api): prevent race condition in rate limiter
docs: update API reference for v2 endpoints
feat!: drop Node 16 support

BREAKING CHANGE: minimum Node version is now 18.
```

---

## 2. Keep a Changelog Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New user dashboard with analytics

### Changed
- Upgraded to React 19

### Fixed
- Memory leak in WebSocket handler

## [1.2.0] - 2026-02-10

### Added
- Export to CSV feature

### Deprecated
- Legacy `/api/v1/users` endpoint (use `/api/v2/users`)

## [1.1.0] - 2026-01-15

### Added
- Dark mode support
```

### Section Order

1. **Added** — New features
2. **Changed** — Changes to existing functionality
3. **Deprecated** — Soon-to-be removed features
4. **Removed** — Removed features
5. **Fixed** — Bug fixes
6. **Security** — Vulnerability fixes

---

## 3. Tooling

### conventional-changelog (Node.js)

```bash
npm install -D conventional-changelog-cli

# Generate CHANGELOG.md
npx conventional-changelog -p angular -i CHANGELOG.md -s

# First release (include all commits)
npx conventional-changelog -p angular -i CHANGELOG.md -s -r 0
```

### standard-version / release-please

```bash
# standard-version (local)
npx standard-version          # auto bump + changelog + tag
npx standard-version --dry-run # preview changes

# release-please (GitHub Action)
# .github/workflows/release.yml
```

```yaml
name: Release
on:
  push:
    branches: [main]
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: node
```

### Python: bump2version

```bash
pip install bump2version

# .bumpversion.cfg
# [bumpversion]
# current_version = 1.0.0
# commit = True
# tag = True

bump2version patch   # 1.0.0 → 1.0.1
bump2version minor   # 1.0.1 → 1.1.0
bump2version major   # 1.1.0 → 2.0.0
```

---

## 4. Git Tag Workflow

```bash
# Create annotated tag
git tag -a v1.2.0 -m "Release v1.2.0"

# Push tag
git push origin v1.2.0

# List tags
git tag -l "v1.*"

# Delete tag (local + remote)
git tag -d v1.2.0
git push origin --delete v1.2.0
```

---

## 5. GitHub Release Notes

```bash
# Auto-generate from PRs
gh release create v1.2.0 --generate-notes

# With custom notes
gh release create v1.2.0 --notes-file RELEASE_NOTES.md

# Draft release
gh release create v1.2.0 --draft --generate-notes
```

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Write changelogs manually from memory | Generate from structured commits |
| Mix commit types in one commit | One logical change per commit |
| Skip version tags | Tag every release |
| Expose internal details in notes | Write user-facing descriptions |
| Include merge commits in changelog | Filter to meaningful changes only |

---

## Checklist

- [ ] Conventional commit format enforced (commitlint or hook)
- [ ] Changelog tool configured (conventional-changelog / release-please)
- [ ] SemVer strategy defined (patch/minor/major rules)
- [ ] CI generates release notes on tag push
- [ ] Breaking changes clearly documented
- [ ] No secrets or internal URLs in release notes
