# CLAUDE.md — Speckit Autonomous Workflow (v2)

## Auto-Resume Protocol (READ THIS FIRST)

If you are starting a new conversation or resuming after `/clear`:
1. **Immediately** scan for active progress files — `ls .specify/specs/*/PROGRESS.md 2>/dev/null`
2. Read the PROGRESS.md for the active feature (the one with Phase Status != completed, or the most recently modified)
3. If PROGRESS.md exists and shows an active workflow, **resume from the indicated phase** without asking.
4. Read the relevant speckit artifacts for your current phase from the same feature directory.
5. If the user's message is just "go", "continue", "resume", or similar — this is your cue to resume the pipeline. Do NOT ask for clarification.
6. If no PROGRESS.md exists in any feature dir, wait for the user to provide a feature description to begin.

---

## Workflow Phase Order (STRICT)

Execute phases in this exact sequence. Never skip or reorder.
```
specify → clarify → plan → tasks → analyze → implement
```

### Phase Dependency Map
```
specify ──creates──> spec.md
clarify ──refines──> spec.md
plan    ──creates──> plan.md, data-model.md, contracts/, research.md
tasks   ──creates──> tasks.md
analyze ──reads────> spec.md + plan.md + tasks.md (NO file writes)
implement ──reads──> tasks.md + plan.md → produces source code
```

---

## Checkpoint File: `.specify/specs/<feature>/PROGRESS.md`

Each feature has its own PROGRESS.md inside its feature directory (e.g., `.specify/specs/1-my-feature/PROGRESS.md`). This prevents conflicts when multiple tmux sessions work on different features in parallel.

**YOU MUST** update the feature's PROGRESS.md after every phase completion, after every task completion during implementation, and before every `/compact` or `/clear`. This file is your ONLY ground truth after context resets.

### Format (STRICT — use exactly these headers):
```markdown
# Project Progress

## Current Phase: [specify|clarify|plan|tasks|analyze|implement]
## Phase Status: [in_progress|completed]
## Next Phase: [next_phase_name or DONE]
## Completed Phases: [comma-separated list]
## Last Action: [what was just done — be specific]
## Feature Branch: [branch name, e.g. 1-my-feature]
## Feature Dir: [e.g. .specify/specs/1-my-feature]

## Implementation Progress
<!-- Only populated during implement phase -->
- Current Task: [T00X]
- Tasks Completed: [T001, T002, ...]
- Tasks Remaining: [T00X, T00Y, ...]
- Total: [X of Y]

## Context Budget
<!-- Heuristic tracking — update after each significant action -->
- File Reads This Cycle: [count]
- Tool Calls This Cycle: [count]
- Debug Cycles This Cycle: [count]
- Estimated Usage: [LOW|MODERATE|HIGH|CRITICAL]
- Last Compaction: [timestamp or phase:task]

## Key Decisions
<!-- Critical architectural/spec decisions that MUST survive context resets -->
- [decision 1]
- [decision 2]

## Modified Files
<!-- Files changed in current phase/task -->
- [file path 1]
- [file path 2]

## Failed Attempts
<!-- Record what was tried and failed — prevents repeating mistakes after context resets -->
- [what was tried] → [why it failed]

## Blockers
<!-- Only if unresolvable issues encountered -->
- [blocker description + phase where it occurred]
```

---

## Phase Transition Rules

### Classification: Minor vs Major Transitions

| Transition | Type | Method | Rationale |
|---|---|---|---|
| specify → clarify | Minor | `/compact` | Same paradigm (requirements) |
| clarify → plan | **MAJOR** | `/clear` | Paradigm shift: WHAT → HOW |
| plan → tasks | Minor | `/compact` | Same paradigm (planning) |
| tasks → analyze | Minor | `/compact` | Same paradigm (planning) |
| analyze → implement | **MAJOR** | `/clear` | Paradigm shift: PLANNING → CODING |

### Minor Transition — `/compact`
Preserves conversation continuity with summarization.
```
/compact Preserve: current phase=[PHASE], feature branch=[BRANCH], feature dir=[DIR], next phase=[NEXT], modified files, key decisions, PROGRESS.md path=.specify/specs/<feature>/PROGRESS.md. Discard: file contents, intermediate reasoning.
```

### Major Transition — `/clear`
Full context wipe for maximum reclamation. Requires user to type "go" to resume.

**Before issuing `/clear`, you MUST:**
1. Git commit all changes: `git add -A && git commit -m "phase: [phase_name] complete"`
2. Update the feature's PROGRESS.md with ALL current state (this is the lifeline)
3. Output a clear message to the user:
```
Phase [X] complete. All progress saved to .specify/specs/<feature>/PROGRESS.md.
Issuing /clear for maximum context reclamation before [next phase].
Type "go" to resume the pipeline.
```
4. Issue `/clear`

**After `/clear`** (when user types "go"):
- The Auto-Resume Protocol at the top of this file kicks in automatically.
- Read PROGRESS.md → read relevant artifacts → continue pipeline.

### Transition Procedure Checklist (EVERY transition):
1. [ ] Verify all phase artifacts are written to disk
2. [ ] Git commit: `git add -A && git commit -m "phase: [phase_name] complete"`
3. [ ] Update the feature's PROGRESS.md with completed phase + next phase + all state
4. [ ] Reset Context Budget counters in PROGRESS.md
5. [ ] Execute `/compact` (minor) or `/clear` (major)
6. [ ] After resumption: read the feature's PROGRESS.md FIRST
7. [ ] Read the relevant speckit artifacts for the next phase
8. [ ] Continue to next phase immediately

---

## Phase Execution

### 1. specify
Run `/speckit.specify` with the user's feature description.

**On completion:**
- Update PROGRESS.md (Next Phase: clarify)
- Git commit
- `/compact` (minor transition)
- Proceed to clarify

### 2. clarify
Run `/speckit.clarify` to resolve ambiguities in spec.md.

**On completion:**
- Update PROGRESS.md (Next Phase: plan)
- Git commit
- `/clear` **(MAJOR — paradigm shift to technical planning)**
- Output resume message → user types "go" → resume

### 3. plan
Read PROGRESS.md first. Run `/speckit.plan` using tech stack from spec.

**On completion:**
- Update PROGRESS.md (Next Phase: tasks)
- Git commit
- `/compact` (minor transition)
- Proceed to tasks

### 4. tasks
Run `/speckit.tasks` to generate task breakdown.

**On completion:**
- Update PROGRESS.md (Next Phase: analyze)
- Git commit
- `/compact` (minor transition)
- Proceed to analyze

### 5. analyze
Run `/speckit.analyze` for cross-artifact consistency check.

**If CRITICAL issues found:**
1. Fix them in the relevant artifacts (spec.md, plan.md, or tasks.md)
2. Re-run `/speckit.analyze`
3. Repeat until no CRITICAL issues remain (max 3 cycles)
4. If still unresolvable after 3 cycles, log in PROGRESS.md Blockers and proceed

**On completion:**
- Update PROGRESS.md (Next Phase: implement)
- Git commit
- `/clear` **(MAJOR — paradigm shift to implementation)**
- Output resume message → user types "go" → resume

### 6. implement
Run `/speckit.implement`. This is the longest phase — follow implementation context rules below.

**On completion:**
- Run final `/speckit.analyze` to verify completeness
- Update PROGRESS.md (Current Phase: completed, Next Phase: DONE)
- Git commit: `git add -A && git commit -m "feat: [feature-name] implementation complete"`

---

## Implementation Phase — Context Management (CRITICAL)

The implementation phase is the longest and most context-intensive. Context degradation is the #1 risk. Follow these rules with zero exceptions.

### Rule 1: Compact After Every Task/User Story
After completing each task (marking `[X]` in tasks.md):
1. Git commit: `git add -A && git commit -m "task [T00X]: [description]"`
2. Update PROGRESS.md with completed task + increment counters
3. `/compact Preserve: current task=[NEXT_TASK], completed tasks=[LIST], remaining tasks=[LIST], feature branch=[BRANCH], feature dir=[DIR], modified files=[LIST], test results=[PASS/FAIL]. Read .specify/specs/<feature>/PROGRESS.md to resume.`
4. After compact: re-read PROGRESS.md and current task from tasks.md

### Rule 2: Proactive Compaction at 60-70% Context (CONTINUOUS MONITORING)
Track these heuristics in PROGRESS.md Context Budget section:

| Heuristic | Threshold | Action |
|---|---|---|
| File reads since last compaction | > 15 files | Compact NOW |
| Tool calls since last compaction | > 40 calls | Compact NOW |
| Debug/retry cycles on single task | > 3 cycles | Compact NOW |
| Long tool outputs (>200 lines) | > 5 occurrences | Compact NOW |
| Estimated context usage | HIGH or CRITICAL | Compact NOW |

**How to estimate context usage:**
- **LOW**: < 10 file reads, < 20 tool calls, no debug cycles
- **MODERATE**: 10-15 file reads, 20-35 tool calls, 1-2 debug cycles
- **HIGH**: 15+ file reads, 35+ tool calls, 3+ debug cycles → **COMPACT IMMEDIATELY**
- **CRITICAL**: Responses feel slow, outputs seem truncated, reasoning quality drops → **EMERGENCY COMPACT**

**Proactive compaction command:**
```
/compact PROACTIVE MID-TASK COMPACTION. Current task=[T00X] status=[in_progress|debugging]. Completed tasks=[LIST]. Remaining tasks=[LIST]. Feature branch=[BRANCH]. Feature dir=[DIR]. Modified files=[LIST]. Current task context: [1-2 sentence summary of what you're doing and what's left]. Read .specify/specs/<feature>/PROGRESS.md to resume.
```

### Rule 3: Subagents for Large Tasks
If a single task requires:
- Reading more than 8 files
- Understanding a complex existing system
- Extensive research or investigation

Delegate the **research/investigation** portion to a subagent to keep the main context clean:
```
Use Agent tool with subagent_type="Explore" for codebase research
Use Agent tool with subagent_type="general-purpose" for complex multi-step investigation
```
Keep the **writing/editing** in the main context. Only offload reading and research.

### Rule 4: Post-Compaction Recovery (Implementation)
After ANY compaction during implementation:
1. Read the feature's PROGRESS.md — read full state
2. Read current task from `.specify/specs/<feature>/tasks.md`
3. Read any files listed in "Modified Files" that are relevant to current task
4. Resume work on current task
5. Do NOT re-read completed tasks or their files

### Rule 5: Commit Before Every Compaction
**NEVER compact without committing first.** Uncommitted work + failed compaction = lost work.
```bash
git add -A && git commit -m "task [T00X]: [description]"
```
Then compact. Then resume.

### Rule 6: User Story Boundaries = Natural Compact Points
When finishing the last task of a user story phase:
1. Commit all tasks in the story
2. Update PROGRESS.md with story completion
3. Compact with story-level summary
4. This is the BEST time to compact — natural boundary, minimal context loss

---

## Auto-Continuation Protocol

**YOU MUST** continue to the next phase automatically after each phase completes. Never stop and ask "should I continue?", "would you like me to proceed?", or any variation — the answer is always YES.

The ONLY time you pause is at major transitions (`/clear`), where you output the resume message and wait for the user to type "go".

### Error Handling
If a phase fails or produces errors:
1. Attempt to fix the error (max 3 retries per error)
2. If fix succeeds, continue normally
3. If unresolvable after 3 retries:
   a. Log the error in PROGRESS.md under `## Blockers` with phase name, error description, and attempted fixes
   b. Continue to next phase (analyze phase will catch inconsistencies)
   c. Do NOT stop the pipeline for non-critical errors

### Forbidden Behaviors
- **NEVER** ask "should I continue to the next phase?"
- **NEVER** ask "would you like me to proceed?"
- **NEVER** summarize what you just did and wait — summarize and CONTINUE
- **NEVER** ask for confirmation to run a speckit command
- **NEVER** stop between tasks during implementation to ask if the approach is correct
- **NEVER** output "I'll wait for your input" during autonomous execution

---

## Post-Clear / Post-Compact Recovery

### After `/clear` (user types "go"):
1. Scan for active progress files — `ls .specify/specs/*/PROGRESS.md`
2. Read the active feature's PROGRESS.md — this is your ONLY context
3. Read the speckit artifacts needed for the current phase from the Feature Dir
4. Resume execution from where PROGRESS.md indicates
5. Do NOT re-read artifacts from completed phases unless needed for the current phase

### After `/compact`:
1. Read the feature's PROGRESS.md — verify state
2. Read current task/phase artifacts
3. Continue immediately — do NOT ask for confirmation

### Recovery Priority Order:
```
PROGRESS.md → tasks.md (if implementing) → plan.md (if needed) → spec.md (if needed)
```
Only read what you need for the CURRENT phase. Minimize context consumption on recovery.

---

## General Rules

1. **Never ask for human confirmation between phases** (except the "go" after `/clear`)
2. **Always commit before compaction or clearing** — uncommitted work = lost work
3. **Feature PROGRESS.md is the single source of truth** after any context reset — located at `.specify/specs/<feature>/PROGRESS.md`
4. **Keep speckit artifacts in `.specify/specs/<feature>/`** — never delete them
5. **If unsure what phase you're in** → read the feature's PROGRESS.md
6. **When compacting, ALWAYS preserve**: current phase, task progress, feature branch, feature dir, modified files, key decisions
7. **Parallelize where marked**: Tasks with `[P]` can run in parallel; use subagents for truly independent work
8. **Fail forward**: If a non-critical error occurs, log it and continue. Only halt for data corruption or security issues.
9. **One feature at a time**: Complete the current feature pipeline before starting another
10. **Git hygiene**: One commit per task during implementation, one commit per phase during planning

---

## Compact Instructions

When compacting (manually or auto-compaction), ALWAYS preserve the following:
1. Current phase name and status from the feature's PROGRESS.md
2. Feature branch name and feature directory path
3. Current task ID and completion status (during implementation)
4. All modified file paths in the current phase/task
5. Key architectural decisions that affect remaining work
6. Failed approaches and why they failed (to avoid repeating)
7. The path `.specify/specs/<feature>/PROGRESS.md` and instruction to read it first after compaction
8. Any test commands and their pass/fail results

ALWAYS discard:
- Full file contents (re-read from disk after compaction)
- Intermediate reasoning and exploration paths
- Tool output beyond summary results
- Completed phase details (already committed to git)
