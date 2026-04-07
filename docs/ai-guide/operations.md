# AI Operations: Merges, Documentation, Vision & Admin

Reference doc for AI agents. Auto-loaded CLAUDE.md points here.

---

## Head AI: Worktree Merge Procedure

The Head AI operates directly on the `ML` branch -- no worktree. All commits and
pushes go to `origin/ML`. **Never merge without explicit human confirmation.**

### Step-by-Step

1. **Locate worktrees:** `ls .claude/worktrees/` and `git worktree list`
2. **Ask the user** before merging each worktree. Do NOT proceed without "yes".
3. **Check for file conflicts:** `git diff --name-only ML...ws{NN}/{description}`.
   The scoring chain (WS02 -> WS04 -> WS08) always merges in that order.
4. **Run tests** in each worktree before merging:
   `cd .claude/worktrees/ws{NN}-{name} && pytest -v --tb=short`
5. **Merge:** `git merge ws{NN}/{description} -m "Merge WS{NN}: {title}"`
6. **SLURM GPU test** (mandatory if scoring/ML/docking/evaluation changed):
   Submit `scripts/run_tests_all.slurm` and verify 618/618 pass, 0 skips.
   See `docs/ai-guide/testing-and-deps.md` for the full 3-tier policy.
7. **Push and verify:** `git push origin ML && git log --oneline -10`

---

## Documentation System

Every AI agent must maintain a progress report at `reports/workstreams/ws{NN}-report.md`.

### Report Locations

```
reports/workstreams/TEMPLATE.md     -- The template (copy for new reports)
reports/workstreams/ws{NN}-report.md -- One report per workstream
reports/head-ai-log.md              -- Head AI running log
vision/log/assistant-log.md         -- Assistant AI running log
vision/log/visionary-log.md         -- Visionary AI running log
```

### When to Update

Update after every major action: file created, file modified, tests written,
non-obvious decision made, blocker hit, milestone completed.

**Minimum update frequency:** after every 2-3 tool calls that change the codebase.

### What Must Always Be Accurate

1. **Current State** -- what is done, what is in progress, what remains, any blockers.
2. **Next Steps** -- ordered list of what to do next.

### Context Recovery Procedure

If context compacts:
1. Read your report: `reports/workstreams/ws{NN}-report.md`
2. Read your workstream brief: `workstreams/{NN}-{name}.md`
3. Check git status: `git status` and `git log --oneline -5`
4. Resume from "Next Steps"

---

## Vision System

A strategic planning layer with three AI roles:

| Role | Reads | Writes | Purpose |
|------|-------|--------|---------|
| **Assistant AI** | Full codebase | `vision/briefings/*.md`, `vision/log/assistant-log.md` | Translates project state into briefings |
| **Visionary AI** | ONLY `vision/` | `vision/ideas/{NNN}-*.md`, `vision/log/visionary-log.md` | Proposes bold improvements, never implements |
| **Head AI** | `vision/ideas/*.md` | Idea status updates, new workstream briefs | Accepts/defers ideas |

### Idea Lifecycle

```
proposed  -->  accepted  -->  planned  -->  in-progress  -->  completed
    |                                                    |
    +----------->  deferred  <---------------------------+
```

### Head AI Obligations (Vision)

1. Read all `proposed` ideas in `vision/ideas/`
2. Accept or defer each (document in `reports/head-ai-log.md`)
3. For accepted: create workstream brief, update `workstreams/README.md`
4. Update idea status field

### Rules

1. Visionary AI reads ONLY `vision/`. Never reads source code.
2. Assistant AI writes only to `vision/briefings/` and its log.
3. Only Head AI modifies idea status fields.
4. Ideas are never deleted. Briefings refreshed before every Visionary session.

---

## Admin AI System

Infrastructure quality monitoring. Reads scaffolding/docs/configs to find staleness
and inconsistencies. Writes structured suggestions but NEVER implements changes.

### Folder Structure

```
admin/
+-- README.md, INSTRUCTIONS.md, suggestions.md, log/admin-log.md
```

### Suggestion Lifecycle

`suggested -> accepted -> implemented` or `suggested -> wont-fix`

### Head AI Obligations (Admin)

1. Read all `suggested` entries in `admin/suggestions.md`
2. P0 (broken): fix immediately. P1 (stale): fix or schedule.
3. P2/P3: accept, defer, or `wont-fix` with rationale.
4. Log decisions in `reports/head-ai-log.md`

### When to Run Admin AI

- Before a new Head AI takes over
- After merging a batch of workstreams
- After major documentation updates
