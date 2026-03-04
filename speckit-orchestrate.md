Orchestrate the full Speckit workflow autonomously for: $ARGUMENTS

## Instructions
1. First, read `.specify/PROGRESS.md` — if it exists, resume from the indicated phase. If it doesn't exist, create it and start from `specify`.

2. Execute the full phase pipeline. Follow ALL rules in CLAUDE.md — especially:
   - Update PROGRESS.md after every phase
   - Use lightweight /compact for minor transitions (specify→clarify, plan→tasks, tasks→analyze)
   - Use heavy /compact for major transitions (clarify→plan, analyze→implement)
   - Git commit before every compaction
   - Never ask for human confirmation — run the full pipeline

3. Phase sequence:
   - `/speckit.specify` with the feature description provided above
   - `/speckit.clarify` to resolve ambiguities
   - `/speckit.plan` using tech stack from spec
   - `/speckit.tasks` to break down into actionable items
   - `/speckit.analyze` for consistency validation (fix and re-run if issues found)
   - `/speckit.implement` following implementation context rules from CLAUDE.md

4. During implementation:
   - Compact after each completed task/user story
   - Proactively compact if context feels heavy mid-task
   - Commit after every task completion
   - Re-read PROGRESS.md after every compact

5. When all tasks are implemented, do a final `/speckit.analyze` to verify completeness.

6. End with a summary commit and update PROGRESS.md status to `completed`.

Begin now. Do not ask for confirmation.
