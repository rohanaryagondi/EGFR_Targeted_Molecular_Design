# Head AI -- Running Log

<!--
  The Head AI operates directly on the ML branch. It coordinates workstreams, merges
  completed work, and converts Visionary ideas into actionable tasks.

  Update this log after every major action:
  - Merging a worktree
  - Making an architectural decision
  - Accepting or deferring a Visionary idea
  - Creating a new workstream from an idea
  - Resolving a cross-cutting issue

  If context compacts, re-read this log + CLAUDE.md + workstreams/README.md to recover.
-->

## Status

- **Last session:** 2026-03-28
- **Branch:** ML (always)
- **Last updated:** 2026-03-28T23:59:00+00:00
- **Head AI generation:** 1 (first Head AI; this is the handoff document for generation 2)

---

## Merge Log

<!-- Newest entries first. Record every merge with test results. -->

| Date | Branch | Workstream | Tests Before | Tests After | Conflicts |
|------|--------|------------|-------------|-------------|-----------|
| 2026-03-28 | ws08/mpnn | WS08: MPNN Affinity | 518 | 540 | None |
| 2026-03-28 | ws04/docking | WS04: Docking Proxy | 498 | 518 | None |
| 2026-03-27 | ws09/admet | WS09: ADMET Predictor | ~498 | 498 | None (merged with WS02, WS05) |
| 2026-03-27 | ws05/viz | WS05: Visualization | ~498 | 498 | None (merged with WS02, WS09) |
| 2026-03-27 | ws02/scoring | WS02: Scoring Integration | ~359 | ~498 | None (merged with WS05, WS09) |
| 2026-03-26 | ws07/vae | WS07: Conditional VAE | ~359 | ~359 | None |
| 2026-03-26 | ws03/stats | WS03: Statistical Testing | ~359 | ~359 | None |
| 2026-03-26 | ws06/cicd | WS06: CI/CD | ~359 | ~359 | None |
| 2026-03-25 | ws01/chemistry | WS01: Chemistry Foundation | 359 | ~384 | None |

**Notes on merge order:**
- WS02, WS05, WS09 were run by agents simultaneously and merged as a batch (no conflicts).
- WS04 and WS08 were merged strictly sequentially (both modify `ranking/scoring.py`).
- Exact intermediate counts for Group A merges are approximate; the definitive progression
  is 359 -> 498 -> 518 -> 540.

**Auto-generated worktree names encountered:**
- Agents used names like `charming-liskov`, `clever-blackburn`, `modest-wilbur`,
  `eager-ellis`, `epic-bell`, `sad-ishizaka` instead of the prescribed `ws{NN}-{description}`.
- Worktrees were identified by running `git log --oneline -1` on each branch.
- Future Head AIs: explicitly include worktree names in agent prompts.

---

## Vision Review Log

<!-- Record every review of Visionary ideas. -->

| Date | Ideas Reviewed | Accepted | Deferred | Notes |
|------|---------------|----------|----------|-------|
| (none yet) | -- | -- | -- | Vision system scaffolded (commit 22c2694) but never run. No briefings written, no ideas proposed. |

**Next action:** Run Assistant AI to write briefings, then Visionary AI to propose ideas,
then review ideas here.

---

## Task Assignments

<!-- Record workstream creation from Visionary ideas. -->

| Date | Idea | Workstream Created | Assigned To | Status |
|------|------|--------------------|-------------|--------|
| (none yet) | -- | -- | -- | -- |

---

## Decisions Made

<!-- Non-obvious architectural or priority decisions. -->

| Date | Decision | Alternatives | Rationale |
|------|----------|-------------|-----------|
| 2026-03-25 | Changed default GitHub branch from `main` to `ML` | Keep `main` as default | ML is the sole active development branch; all work happens there. Simplifies push commands. |
| 2026-03-26 | Scoring chain merge order: WS02 -> WS04 -> WS08 strictly sequential | Parallel merge with conflict resolution | All three modify `ranking/scoring.py`. Each builds a fallback layer on top of the previous. Sequential merge avoids conflicts entirely. |
| 2026-03-27 | Merged WS02, WS05, WS09 as a batch | Merge one at a time | No file conflicts between these three. Verified with `git diff --name-only`. Batch merge was safe and faster. |
| 2026-03-28 | Removed errant WS08 worktree (`sad-ishizaka`) that ran before WS04 was merged | Keep it and try to merge | WS08 was based on pre-WS04 code. The cascading fallback would be wrong. Deleted and re-ran WS08 after WS04 merged. |
| 2026-03-28 | Created `epic-clarke` stub directory | Let shell fail after worktree removal | After `git worktree remove --force`, the shell CWD was invalid. Creating a stub directory (`mkdir -p`) allowed the shell to recover. |
| 2026-03-28 | Always run `pip install -e ".[dev]"` on ML before definitive tests | Trust individual worktree test results | Discovered that editable installs in one worktree contaminate all others' import paths. Only ML-branch installs give reliable results. |
| 2026-03-28 | Created Vision System (3 roles: Assistant, Visionary, Head AI) | Single "improvement suggestions" file | Three-role separation ensures: (1) Visionary thinks at strategic level without code access, (2) Assistant curates context honestly, (3) Head AI triages with implementation knowledge. |
| 2026-03-28 | Created Admin AI role for infrastructure monitoring | Rely on Head AI to spot stale docs | Dedicated role ensures systematic audits rather than ad-hoc discovery. Admin AI writes suggestions; Head AI implements. Parallels the Visionary -> Head AI pattern. |
| 2026-03-28 | All AI roles must maintain running documentation (Rule 10) | Only modular agents document | Context compaction is universal. Every role needs a recovery mechanism. Running logs serve as handoff documents when any AI is replaced. |

---

## Current State

**What is done:**
- All 9 workstreams complete and merged to ML (540 tests passing)
- All integration adapters written: MPNN (`ml/affinity_predictor.py`), ADMET
  (`ml/admet_predictor.py`), VAE (`ml/vae_integration.py`), Docking Proxy
  (`chemistry/docking_proxy.py`)
- Cascading docking fallback: MPNN -> DockingProxy MLP -> constant 0.5 stub
- Statistical testing framework complete (Mann-Whitney U, bootstrap CI, sensitivity)
- Visualization module complete (score distributions, radar plots, comparison figures)
- CI/CD pipeline configured (GitHub Actions: test, lint, test-with-chemistry)
- Chemistry foundation integrated (RDKit fingerprints, descriptors, validation)
- Vision System scaffolded: `vision/` directory with README, instructions, templates, logs
- Admin AI scaffolded: `admin/` directory with README, instructions, suggestion template, log
- Documentation system established: all 9 workstream reports exist, TEMPLATE.md, this log
- AI Employee Directory added to HUMANONLY.md Section 10

**What is NOT done:**
- ML model training (requires GPU): VAE, MPNN, ADMET are code-complete but untrained
- Vision System has never been run (no briefings written, no ideas proposed)
- Admin AI has never been run (no audit performed, no suggestions written)
- Full pipeline re-run with trained models
- Statistical hypothesis testing with real (non-stub) scores
- ~40 pre-existing ruff violations in `src/` (documented in CRITICAL.md)
- Stale test count references: some places in CLAUDE.md still say "359 tests"
  (updated in CRITICAL.md, TODO.md, and workstreams/README.md but not exhaustively
  searched in CLAUDE.md)

**Known artifacts on disk:**
- `data/processed/egfr_affinity.json` -- 1,678 ChEMBL EGFR compounds (pIC50)
- `data/processed/admet_combined.json` -- TDC ADMET benchmark data
- `data/processed/egfr_smiles_train.json` -- VAE training data
- No model checkpoints yet (training required)

---

## Next Steps (for incoming Head AI)

1. **Run Admin AI** -- audit documentation accuracy, catch stale references (e.g.,
   "359 tests" in CLAUDE.md). Read `admin/INSTRUCTIONS.md` for its playbook. Process
   its suggestions by reading `admin/suggestions.md`.

2. **Run Vision System** -- refresh briefings (Assistant AI), generate ideas (Visionary AI),
   then review ideas. See HUMANONLY.md Sections 8.3-8.5 for prompts.

3. **Plan ML training** -- three models need GPU training:
   - VAE: `python scripts/train_vae.py --config configs/vae.yaml`
   - MPNN: `python scripts/train_mpnn.py --config configs/mpnn.yaml`
   - ADMET: `python scripts/train_admet.py --config configs/admet.yaml`
   See HUMANONLY.md Section 4 for HPC instructions.

4. **After training** -- re-run full comparison pipeline, apply statistical tests,
   update reports with real results. This is the path to rejecting the null hypothesis.

5. **Create new workstreams** from accepted Visionary ideas.

6. **Fix ruff violations** -- ~40 pre-existing violations block CI. Run
   `ruff check --fix src/` to auto-fix, then manually resolve remaining.

---

## Context Recovery

If your context compacts:
1. Re-read this log (you are here)
2. Re-read `CLAUDE.md` (Sections 11, 16, 17, 18, 19)
3. Re-read `workstreams/README.md` (status table -- all 9 complete)
4. Check `git log --oneline -10` for recent activity
5. Check `vision/ideas/` for pending proposals
6. Check `admin/suggestions.md` for pending infrastructure suggestions
7. Resume from "Next Steps" above

---

## Handoff Notes for Generation 2 Head AI

**Critical things to know:**

1. **You have no worktree.** You work directly on the ML branch. Push to `origin/ML`.
   See CLAUDE.md Section 16 for your merge procedure.

2. **All 9 workstreams are done.** The workstream system (`workstreams/README.md`) is
   complete. New workstreams will come from Visionary ideas (see `vision/ideas/`).

3. **The scoring chain is complete.** `ranking/scoring.py` now has the 3-tier cascade:
   MPNN -> DockingProxy MLP -> stub. No more merges needed for scoring.

4. **ML training is the critical path.** All integration code is written. The models
   just need to be trained on GPU. Data is prepared. See TODO.md Section 2.

5. **Read `CRITICAL.md` carefully.** It has operational gotchas about worktree naming,
   editable installs, shell CWD issues, and the scoring chain that will save you time.

6. **The AI org chart** is in HUMANONLY.md Section 10. Five roles: Head AI (you),
   Modular Agents, Assistant AI, Visionary AI, Admin AI. You consume output from
   Visionary (ideas) and Admin (suggestions).

7. **Rule 10 applies to you.** Update this log after every major action. This is your
   context recovery and handoff mechanism.
