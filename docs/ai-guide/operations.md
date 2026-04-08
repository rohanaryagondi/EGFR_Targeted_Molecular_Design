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
   Submit `scripts/run_tests_all.slurm` and verify 646/646 pass, 0 skips.
   See `docs/ai-guide/testing-and-deps.md` for the full 3-tier policy.
7. **Push and verify:** `git push origin ML && git log --oneline -10`

---

## Post-Merge Documentation Audit

After merging workstreams and pushing to GitHub, the Head AI **must** perform a full
documentation audit. Every merge changes test counts, module counts, file:line references,
and workstream status — and these numbers are duplicated across 15+ files. If you skip
this step, the next AI agent (or human) inherits a codebase where the docs contradict
reality.

**When to run:** After every merge-and-push to `origin/ML`. Non-negotiable.

### What Goes Stale and Where

Documentation drift follows a predictable pattern. These are the specific things that
break after a merge, organized by how often they cause problems.

#### 1. Test Counts (highest frequency of staleness)

The test count appears in **all** of these files. Update every one:

| File | What to search for |
|------|--------------------|
| `CLAUDE.md` | Quick Reference block (`Tests: pytest ... (NNN passing)`), Rule 6 (`NNN+ tests must pass`), File Organization (`NNN tests`) |
| `CRITICAL.md` | Test count timeline (add new entry, don't change historical ones) |
| `GOALS.md` | Success criteria table |
| `TODO.md` | Quick Reference table |
| `docs/ai-guide/operations.md` | Merge procedure step 6 (SLURM test count) |
| `HumanOnly/Project-Overview.md` | Codebase at a Glance block, How to Run section |
| `HumanOnly/Project-Briefing.md` | Status at a Glance, What's Done section |
| `HumanOnly/AI-Operations-Manual.md` | Section 1 overview, testing policy line |
| `HumanOnly/Help-Needed.md` | Publication readiness checklist |

**How to verify:** Run `pytest --co -q | tail -1` on ML to get the authoritative count.
Then grep: `grep -rn '\b{OLD_COUNT}\b' CLAUDE.md CRITICAL.md GOALS.md TODO.md docs/ai-guide/ HumanOnly/`

#### 2. Workstream Status and Counts

After completing a new workstream, these all need updating:

| File | What changes |
|------|--------------|
| `workstreams/README.md` | Status table: mark Complete |
| `CLAUDE.md` | Architecture table (if new module), workstream brief count |
| `GOALS.md` | Workstream completion count, stretch goal checkboxes |
| `TODO.md` | Workstream brief count, stretch goal checkboxes |
| `HumanOnly/Project-Overview.md` | Workstream table (status column) and section header count |
| `HumanOnly/Project-Briefing.md` | What's Done list, workstream count |
| `HumanOnly/AI-Operations-Manual.md` | Section 1 overview ("N of 12 workstreams") |
| `HumanOnly/Pending-Workstreams.md` | Completion status, section headers |
| `HumanOnly/Project-Log.md` | Add new entry with merge details |

#### 3. File:Line References (hardest to catch)

`CRITICAL.md` and `docs/ai-guide/scoring-and-architecture.md` contain file:line
references like `ranking/scoring.py:125-130 (DEFAULT_WEIGHTS)`. These break whenever
code is added or removed above the referenced line.

**How to verify:** For each `file:line` reference, grep for the function/variable name
and confirm the line number matches. Example:
```bash
grep -n 'DEFAULT_WEIGHTS' src/statebind/ranking/scoring.py
# Compare output line number against what CRITICAL.md claims
```

**Files with line references:**
- `CRITICAL.md` — ~20 references across scoring, ranking, baselines, ml, evaluation
- `docs/ai-guide/scoring-and-architecture.md` — ~15 references in component table,
  weight definition, reference binders, scorers
- `docs/ai-guide/pipeline-and-config.md` — DEFAULT_WEIGHTS reference

**Pattern to check:** Search these files for the regex `:\d+` to find all line references,
then spot-check at least the scoring chain (DEFAULT_WEIGHTS, _validate_weights,
_score_reference_similarity, _compute_state_specificity, SCORING_METHOD, reference binders).

#### 4. Source File Counts

New workstreams add `.py` files, test files, config files, and scripts. These counts
appear in:

| Count | Where it appears |
|-------|-----------------|
| Python source files | `CLAUDE.md` File Organization, `HumanOnly/Project-Overview.md` Codebase block, `HumanOnly/AI-Operations-Manual.md` Section 1 |
| Test files | `CLAUDE.md` File Organization |
| Config files | `CLAUDE.md` File Organization (list them by name) |
| Scripts | `HumanOnly/Project-Overview.md` Codebase block |

**How to verify:**
```bash
find src/statebind -name '*.py' | wc -l        # Python source files
ls tests/test_*.py | wc -l                      # Test files
ls configs/*.yaml | wc -l                       # Config files
ls scripts/*.py scripts/*.sh 2>/dev/null | wc -l  # Scripts
```

#### 5. Vision System Inputs

If the Assistant AI will run next, its input docs must be current. The key file is
`vision/briefings/INSTRUCTIONS.md` which tells the Assistant what to read. Check:

- The "Progress Reports" reading list includes all workstream reports
- The architecture and limitations descriptions reflect completed work
- The docking cascade description matches reality (currently 4-tier: GNINA → MPNN → proxy → stub)

### Audit Procedure (Step-by-Step)

```
Step 1: Get authoritative numbers
   pytest --co -q | tail -1                          # test count
   find src/statebind -name '*.py' | wc -l           # source files
   ls tests/test_*.py | wc -l                        # test files
   ls configs/*.yaml | wc -l                         # configs

Step 2: Sweep for stale counts
   grep -rn '\b{OLD_TEST_COUNT}\b' CLAUDE.md CRITICAL.md GOALS.md TODO.md \
       docs/ai-guide/ HumanOnly/
   # Fix every hit that isn't a historical reference (e.g., Project-Log.md
   # entries describe what was true at that time — leave those alone)

Step 3: Verify workstream status tables
   - workstreams/README.md
   - HumanOnly/Project-Overview.md (workstream table)
   - GOALS.md (workstream section)

Step 4: Spot-check file:line references
   grep -n 'DEFAULT_WEIGHTS\|_validate_weights\|_score_reference_similarity' \
       src/statebind/ranking/scoring.py src/statebind/baselines/scoring.py
   # Compare against CRITICAL.md and docs/ai-guide/scoring-and-architecture.md

Step 5: Update head-ai-log.md
   - Add merge entry to the merge log table
   - Update "Current State" section
   - Update task assignments if applicable

Step 6: Update HumanOnly/Project-Log.md
   - Add timestamped entry describing what was merged and key results

Step 7: Commit and push
   git add <all-changed-docs>
   git commit -m "docs: comprehensive update for WS{NN} merge"
   git push origin ML
```

### Historical vs Current References

**Do not change historical entries.** Files like `HumanOnly/Project-Log.md`,
`CRITICAL.md` (test count timeline), and `admin/suggestions.md` contain entries that
describe what was true at a specific point in time. "Test count: 548 → 618" in the
Project-Log entry for 2026-04-07 is correct — that WAS the count at that time. Only
update lines that claim to describe the current state.

### Common Mistakes

1. **Forgetting HumanOnly/.** `CLAUDE.md` says "Do not read files in HumanOnly/" which
   applies to modular agents during normal work. The Head AI performing a doc audit MUST
   update HumanOnly files — they are the human operator's primary reference.

2. **Changing historical log entries.** A Project-Log entry from 2026-03-28 saying
   "548 tests" is correct for that date. Don't retroactively change it to 646.

3. **Missing the vision INSTRUCTIONS.md.** When new workstream reports are created,
   `vision/briefings/INSTRUCTIONS.md` must add them to the reading list or the
   Assistant AI won't know they exist.

4. **Incomplete file:line sweeps.** Checking only CRITICAL.md but forgetting
   `docs/ai-guide/scoring-and-architecture.md` and `docs/ai-guide/pipeline-and-config.md`.
   All three files have line references that can drift.

5. **Not verifying counts yourself.** Agent-reported counts (e.g., "23 test files") are
   sometimes wrong. Always run the shell commands to get authoritative numbers.

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
