Orchestrate the full Speckit workflow autonomously for: $ARGUMENTS

## Instructions

### Step 0: Check for Existing Progress
Read `.specify/PROGRESS.md`. If it exists and shows an active workflow, **resume from the indicated phase**. If it doesn't exist, create it and start from `specify`.

### Step 1: Execute the Full Phase Pipeline
Follow ALL rules in CLAUDE.md. The phase sequence is:

```
specify → clarify → plan → tasks → analyze → implement
```

### Step 2: Context Management (CRITICAL)
- **Minor transitions** (specify→clarify, plan→tasks, tasks→analyze): Use `/compact`
- **Major transitions** (clarify→plan, analyze→implement): Use `/clear`
  - Before `/clear`: commit all changes, update PROGRESS.md with full state
  - Output: "Phase [X] complete. Type 'go' to resume."
  - After user types "go": read PROGRESS.md → continue pipeline

### Step 3: Phase Execution
1. `/speckit.specify` with the feature description provided above
2. `/speckit.clarify` to resolve ambiguities
3. `/speckit.plan` using tech stack from spec
4. `/speckit.tasks` to break down into actionable items
5. `/speckit.analyze` for consistency validation (fix CRITICAL issues and re-run, max 3 cycles)
6. `/speckit.implement` following implementation context rules from CLAUDE.md

### Step 4: Implementation Context Rules
During implementation, context is the bottleneck. Follow these strictly:
- **Compact after each completed task/user story** — always commit first
- **Proactive compaction at 60-70% context** — track heuristics (file reads > 15, tool calls > 40, debug cycles > 3)
- **Use subagents** for research-heavy subtasks to keep main context clean
- **Re-read PROGRESS.md** after every compact
- **Never compact without committing first**

### Step 5: Completion
1. Run final `/speckit.analyze` to verify implementation completeness
2. Update PROGRESS.md: Current Phase = completed, Next Phase = DONE
3. Git commit: `git add -A && git commit -m "feat: [feature-name] implementation complete"`

### Forbidden Actions
- Never ask "should I continue?" — always continue
- Never stop between phases to summarize and wait
- Never ask for confirmation to run a speckit command
- Never re-read completed phase artifacts unless needed for current phase

Begin now. Do not ask for confirmation.
