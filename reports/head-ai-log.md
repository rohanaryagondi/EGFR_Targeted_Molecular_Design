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

- **Last session:** 2026-04-05
- **Branch:** ML (always)
- **Last updated:** 2026-04-05T18:30:00+00:00
- **Head AI generation:** 3

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

## Admin AI Triage Log

<!-- Record every triage of Admin AI suggestions. -->

| Date | Suggestions | Implemented | Accepted | Wont-fix | Notes |
|------|------------|-------------|----------|----------|-------|
| 2026-03-30 | S001-S012 (12 total) | 10 | 1 (S010) | 1 (S012) | First Admin AI audit. Fixed all P0s and P1s. Deferred S010 (ruff). |
| 2026-04-05 | S013-S024 (12 total) | 2 (S013, S014) | 5 (S015-S018, S021, S024) | 4 (S019, S020, S022, S023) | Second Admin AI audit. P0s fixed immediately. CLAUDE.md already restructured by human (makes S020, S023 moot). |

**Detail:**
- S001 (P0): Implemented. Added chemistry/ to CLAUDE.md Sections 3, 4, 9. Removed nonexistent pockets/.
- S002 (P0): Implemented. Fixed 18 stale file:line refs in CLAUDE.md and CRITICAL.md. Added function name anchors.
- S003 (P0): Implemented. Updated GOALS.md Success Criteria Table (18 rows, 10 marked Complete).
- S004 (P1): Implemented. Updated "359 tests" → "548 tests", "72 .py files" → "84" across CLAUDE.md.
- S005 (P1): Implemented. Fixed module file counts: eval 4→7, gen 7→9, ml 13→15.
- S006 (P1): Implemented. Admin AI counted 538, pytest reports 548. Updated all "540" refs to 548.
- S007 (P1): Implemented. Updated 4 module READMEs (evaluation, ml, ranking, generation).
- S008 (P1): Implemented. Fixed INTERFACES.md Contracts 5 (VAE) and 6 (ADMET) to match code.
- S009 (P1): Implemented. Checked 3 data prep items in TODO.md.
- S010 (P2): Accepted, deferred. ~40 ruff violations need dedicated cleanup session.
- S011 (P2): Implemented. Updated GOALS.md Section 3 to mark WS01/WS03 as complete.
- S012 (P3): Wont-fix. __init__.py exports work as-is; adding them is maintenance burden.

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
| 2026-03-30 | Triaged all 12 Admin AI suggestions: 10 implemented, 1 accepted/deferred (S010 ruff), 1 wont-fix (S012 __init__.py) | Implement all, or defer more | P0s are actively misleading (wrong line refs, missing module). Fixing them immediately prevents agents from wasting time on wrong code. S010 deferred because ruff fixes touch ~40 files and need careful review. S012 wont-fix because the code works as-is. |
| 2026-03-30 | Authoritative test count is 548 (from `pytest --co -q`), not 538 (Admin AI's `def test_` grep) or 540 (documented) | Use Admin AI's count | pytest collection is authoritative — it counts parametrized tests and dynamically generated tests that grep misses. |
| 2026-04-05 | WS10: Fix training data scarcity by adding pagination and installing PyTDC | Leave small datasets, add data augmentation | Root causes were purely technical (missing pagination, missing dependency). Fixing them gives 29x-503x more data with no scientific compromise. |
| 2026-04-05 | Clear stale VAE checkpoint and retrain on expanded data | Keep old model, fine-tune | Old model trained on 276 samples is not meaningful. Clean retrain on 8,109 samples. |
| 2026-04-05 | Increase SLURM time limits: MPNN 1h→4h, ADMET 1h→6h, ADMET mem 16G→32G | Keep original limits | Datasets are 6-500x larger; original 1h limits would cause timeout failures. |

---

## Current State

**What is done:**
- All 9 workstreams complete and merged to ML (548 tests passing)
- WS10: Training data scarcity fixed (ADMET 55→27,698, VAE 276→8,109, MPNN 1,678→10,466)
- VAE trained on expanded data (8,109 SMILES, best val loss 2.3246, checkpoint saved)
- MPNN and ADMET training jobs submitted (SLURM 7285710, 7285711, pending GPU allocation)
- All integration adapters written: MPNN, ADMET, VAE, Docking Proxy
- Admin AI session 2 triaged: S013-S014 (P0) implemented, S015-S024 triaged
- CI workflow now triggers on ML branch (was only `main`)
- ranking/CRITICAL.md line references all corrected with function name anchors
- CLAUDE.md restructured by human (concise version with `docs/ai-guide/` references)
- Vision System scaffolded + 12 ideas proposed (all status: proposed, awaiting review)

**What is NOT done:**
- MPNN and ADMET model training (jobs submitted, pending GPU queue)
- Wire MPNN into scoring cascade (after training completes)
- Generate VAE candidates with trained model
- Full pipeline re-run with trained models
- Statistical hypothesis testing with real (non-stub) scores
- Vision idea review (12 ideas proposed, none accepted/deferred yet)
- ~40 pre-existing ruff violations in `src/` (S010 accepted, deferred)
- Accepted admin suggestions S015-S018, S021, S024 (module CRITICAL.md refs, stale content)

**Known artifacts on disk:**
- `data/processed/egfr_affinity.json` -- 10,466 ChEMBL EGFR compounds (pIC50)
- `data/processed/admet_combined.json` -- 27,698 TDC ADMET molecules (6 endpoints)
- `data/processed/egfr_smiles_train.json` -- 8,109 VAE training SMILES
- `artifacts/models/vae/best_model.pt` -- 30MB, trained on 8,109 SMILES, epoch 9

---

## Next Steps

1. **Monitor MPNN/ADMET training** -- jobs 7285710/7285711 in GPU queue. Check
   `squeue -u rag88` and `tail logs/train_mpnn_7285710.out` when running.

2. **After training completes** -- wire models into pipeline:
   - MPNN: verify `ml/affinity_predictor.py` loads checkpoint, test scoring cascade
   - ADMET: verify `ml/admet_predictor.py` loads checkpoint, test filtering
   - VAE: run `scripts/generate_vae_candidates.py` (S024: script needs to be created)
   - Re-run full comparison: `scripts/compare_baseline_vs_state_aware.py`
   - Apply statistical tests (Mann-Whitney U), report p-values

3. **Review 12 Vision ideas** -- all in `vision/ideas/` with status "proposed". Accept
   or defer each. Create workstream briefs for accepted ideas.

4. **Fix accepted admin items** -- S015-S018, S021, S024 (module CRITICAL.md refs, stale
   content, missing VAE generation script).

5. **Fix ruff violations (S010)** -- ~40 violations block CI.

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

## Handoff Notes

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

6. **The AI org chart** is in HumanOnly/AI-Operations-Manual.md Section 10. Five roles: Head AI (you),
   Modular Agents, Assistant AI, Visionary AI, Admin AI. You consume output from
   Visionary (ideas) and Admin (suggestions).

7. **Admin AI has been run.** 12 suggestions triaged. 10 implemented, 1 deferred (S010
   ruff violations), 1 wont-fix (S012 __init__.py). See `admin/suggestions.md`.

8. **Documentation is now current.** All stale refs fixed (2026-03-30). But line numbers
   drift with every code change — consider function name anchors as primary references.

9. **Rule 10 applies to you.** Update this log after every major action. This is your
   context recovery and handoff mechanism.
