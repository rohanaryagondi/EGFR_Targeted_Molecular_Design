# Admin AI -- Running Log

## Status

- **Last session:** 2026-04-05
- **Suggestions written:** 24 (S001-S012 session 1, S013-S024 session 2)
- **Last updated:** 2026-04-05

---

## Sessions

<!-- Newest entries first. Each session gets its own heading. -->

### Session 2 -- 2026-04-05

#### Context

Follow-up audit after Head AI implemented 10 of 12 Session 1 suggestions. Session 1 fixed root-level CRITICAL.md and CLAUDE.md line references, but module-level CRITICAL.md files were not updated. This session focuses on the module-level documentation drift that survived the first triage.

#### Files Audited

**Core Documentation (5 files):**
1. `CLAUDE.md` -- re-read in full; verified source file counts and script counts
2. `CRITICAL.md` -- re-read in full; verified import list accuracy for ranking/scoring.py
3. `GOALS.md` -- re-read in full; found stale "Method (current)" column in Section 4
4. `TODO.md` -- re-read in full; no new issues beyond Session 1 findings
5. `pyproject.toml` -- re-read; version 0.1.0 matches __init__.py

**Module CRITICAL.md Files (12 files, deep line-reference verification):**
6. `ranking/CRITICAL.md` -- 10+ stale line refs (worst file in project)
7. `baselines/CRITICAL.md` -- 4 stale line refs + internal contradiction
8. `evaluation/CRITICAL.md` -- 5+ stale line refs (off by 3-18 lines)
9. `generation/CRITICAL.md` -- 2 stale cross-module refs to ranking/scoring.py
10. `ml/CRITICAL.md` -- claims MPNN data prep script doesn't exist (it does)
11. `data/CRITICAL.md` -- references verified, all correct
12. `chemistry/CRITICAL.md` -- not deeply verified (small file, newer)
13. `structure/CRITICAL.md` -- not deeply verified
14. `context/CRITICAL.md` -- not deeply verified
15. `dynamics/CRITICAL.md` -- not deeply verified
16. `utils/CRITICAL.md` -- not deeply verified
17. `processing/CRITICAL.md` -- not deeply verified

**Module __init__.py Files (13 files):**
18. All 12 subpackage `__init__.py` + root `__init__.py` -- checked for version and export consistency

**Module README Files (12 files):**
19. `evaluation/README.md` -- verified current and accurate
20. `ml/README.md` -- verified current
21. `ranking/README.md` -- verified current and detailed

**Config Files (8 files):**
22. All 6 YAML configs -- clean, no issues
23. `.github/workflows/ci.yml` -- CRITICAL: triggers on `main` not `ML`
24. `.gitignore` -- missing coverage for ML training data

**Test Infrastructure:**
25. All 19 test files listed; 538 `def test_` + parametrize variants = 548 total (matches docs)

**Reports and Logs:**
26. `reports/head-ai-log.md` -- current as of 2026-03-30
27. `workstreams/README.md` -- accurate, all 9 complete
28. `workstreams/INTERFACES.md` -- found missing script reference
29. `admin/suggestions.md` -- read prior suggestions
30. `admin/log/admin-log.md` -- read prior session

**Source Code (spot checks for line reference verification):**
31. `ranking/scoring.py` -- verified ALL function locations against all CRITICAL.md refs
32. `baselines/scoring.py` -- verified key function locations
33. `evaluation/comparison.py` -- verified key function locations
34. `evaluation/statistics.py` -- verified HAS_SCIPY location
35. `evaluation/sensitivity.py` -- verified _COMPONENT_NAMES and _rescore_merged locations
36. `generation/models.py` -- verified model class locations
37. `baselines/models.py` -- verified CandidateSource and FilteredLibrary locations

#### Suggestions Written

- **S013 (P0):** CI triggers on `main` branch but default branch is `ML` -- CI never runs
- **S014 (P0):** ranking/CRITICAL.md has 10+ wrong line references (worst offender)
- **S015 (P1):** baselines/CRITICAL.md has 4 wrong line refs + self-contradictory docking stub refs
- **S016 (P1):** evaluation/CRITICAL.md has 5+ stale line references (off by 3-18 lines)
- **S017 (P1):** generation/CRITICAL.md cross-references ranking/scoring.py at wrong lines
- **S018 (P1):** ml/CRITICAL.md says MPNN data prep script doesn't exist (it does)
- **S019 (P1):** GOALS.md Section 4 scoring table shows pre-WS02 "current" methods
- **S020 (P1):** CLAUDE.md says "84 source files" and "37 scripts" -- actual is 86 and 40
- **S021 (P1):** Root CRITICAL.md import list for ranking/scoring.py missing 2 imports
- **S022 (P2):** .gitignore doesn't cover ML training data files in data/processed/
- **S023 (P2):** CLAUDE.md Section 9 file tree says "BioForge/" instead of "statebind"
- **S024 (P2):** scripts/generate_vae_candidates.py referenced but does not exist

#### Key Findings

1. **Module-level CRITICAL.md files are the primary remaining documentation problem.** Session 1 fixed root-level CRITICAL.md and CLAUDE.md, but the module-level CRITICAL.md files (especially ranking/, baselines/, evaluation/, generation/) were not touched. These files contain the most line-reference-dense documentation in the project and nearly every reference is wrong.

2. **ranking/CRITICAL.md is the worst file.** Every single line reference to scoring.py is wrong, most by 50-100 lines. This is because WS02, WS04, and WS08 all added code to scoring.py, pushing existing code downward. An agent reading this file would look at the wrong code for every critical fact.

3. **The CI workflow has TWO independent blockers.** S010 (ruff violations, from session 1) AND S013 (wrong branch trigger, new this session). Even if ruff violations are fixed, CI still won't run because it watches `main` instead of `ML`.

4. **Source file and script counts drifted.** CLAUDE.md was updated in session 1 to say "84 source files" and "37 scripts" but the actual counts are 86 and 40 (data prep scripts were added during workstreams). These are small discrepancies but the kind of thing that erodes trust in the documentation.

5. **The .gitignore has a structural gap.** ML training data files (JSON, potentially large) sit directly in `data/processed/` and are not covered by the existing gitignore rules, which only cover subdirectories of `data/processed/`.

6. **Overall documentation quality has improved significantly since session 1.** The P0 issues from session 1 (missing chemistry module, wrong test counts, massively stale GOALS.md) are all fixed. The remaining issues are module-level line references and incremental count drift.

#### Changes Since Last Session

- Head AI implemented 10 of 12 Session 1 suggestions
- S010 (ruff violations) accepted but deferred
- S012 (init.py exports) marked wont-fix
- Root CRITICAL.md and CLAUDE.md line references are now accurate
- GOALS.md, TODO.md updated for post-workstream state
- 4 module READMEs updated
- INTERFACES.md contracts 5 and 6 updated

---

### Session 1 -- 2026-03-30

#### Files Audited

**Core Documentation (5 files):**
1. `CLAUDE.md` — read in full, verified all numeric claims and file:line references
2. `CRITICAL.md` — read in full, verified line references and test count
3. `GOALS.md` — read in full, checked success criteria table against reality
4. `TODO.md` — read in full, checked task status against actual file system
5. `pyproject.toml` — read in full, verified version, dependencies, extras

**Module Scaffolding (36 files):**
6. All 12 `src/statebind/*/__init__.py` files + root `__init__.py`
7. All 12 `src/statebind/*/README.md` files
8. All 12 `src/statebind/*/CRITICAL.md` files (existence confirmed)

**Config Files (8 files):**
9. `configs/default.yaml`, `configs/structure.yaml`, `configs/context.yaml`
10. `configs/vae.yaml`, `configs/mpnn.yaml`, `configs/admet.yaml`
11. `.github/workflows/ci.yml`
12. `.gitignore`

**Test Infrastructure:**
13. All 19 test files in `tests/` — counted 538 test functions

**Reports and Logs:**
14. `reports/head-ai-log.md`
15. All 9 `reports/workstreams/ws{01-09}-report.md`
16. `workstreams/README.md`
17. `workstreams/INTERFACES.md`

**Source Code (spot checks for line reference verification):**
18. `src/statebind/ranking/scoring.py` — verified all documented line numbers
19. `src/statebind/baselines/scoring.py` — verified all documented line numbers
20. `src/statebind/processing/models.py` — verified ConformationalState location
21. `src/statebind/ml/__init__.py` — verified HAS_TORCH location
22. `src/statebind/ml/graphs.py` — verified ATOM_FEATURE_DIM location
23. `src/statebind/ml/vocabulary.py` — verified special tokens location
24. `src/statebind/baselines/models.py` — verified CandidateSource location
25. `src/statebind/ml/affinity_predictor.py` — verified contract compliance
26. `src/statebind/ml/admet_predictor.py` — verified contract compliance
27. `src/statebind/generation/vae_integration.py` — verified contract compliance
28. `src/statebind/chemistry/docking_proxy.py` — verified contract compliance

#### Suggestions Written

- **S001 (P0):** CLAUDE.md architecture missing chemistry/ module, lists nonexistent pockets/
- **S002 (P0):** 18 of 23 file:line references in CLAUDE.md and CRITICAL.md are wrong
- **S003 (P0):** GOALS.md Section 6 success criteria table massively stale
- **S004 (P1):** CLAUDE.md stale counts: "359 tests" (x4), "72 .py files", "14 test files"
- **S005 (P1):** CLAUDE.md Section 3 module table wrong file counts for evaluation/, generation/, ml/
- **S006 (P1):** CRITICAL.md and TODO.md say "540 tests" — actual is 538
- **S007 (P1):** Module READMEs stale: evaluation/ says no stats, ml/ says no training data
- **S008 (P1):** INTERFACES.md contracts 5 and 6 don't match implementations
- **S009 (P1):** TODO.md Section 2 data prep scripts shown unchecked but exist
- **S010 (P2):** CI workflow fails due to ~40 ruff violations
- **S011 (P2):** GOALS.md Section 3 discusses completed workstreams as future priorities
- **S012 (P3):** Inconsistent __init__.py exports across modules

#### Key Findings

1. **The #1 issue is documentation drift.** All 9 workstreams completed and merged, but the
   core documentation (CLAUDE.md, GOALS.md, CRITICAL.md) was not updated to reflect post-
   workstream state. A new AI agent reading these files would operate on a false picture.

2. **File:line references are fragile.** 78% of checked references (18/23) are wrong because
   workstreams inserted code that shifted line numbers. The references that survived are in
   files that workstreams didn't modify (processing/models.py, ml/__init__.py, baselines/models.py).

3. **The test infrastructure is healthy.** 538 tests across 19 well-named files. Every module
   with source code has a corresponding test file. No conftest.py, but tests are self-contained.

4. **All 9 workstream reports are filled in** — no template placeholders. Quality documentation.

5. **Config files are clean.** All 6 YAMLs are well-structured, pyproject.toml version matches
   __init__.py, .gitignore covers artifacts appropriately.

6. **CI is technically broken.** The workflow exists (WS06) but ~40 ruff violations in src/
   prevent it from passing. This should be an easy fix.

7. **Training data exists but isn't reflected in docs.** The data prep scripts ran successfully
   and produced training datasets, but TODO.md and ml/README.md still say data doesn't exist.

8. **INTERFACES.md has 2 contract mismatches** out of 7. Contracts 5 (VAE) and 6 (ADMET) diverged
   from their specifications during implementation. The other 5 contracts match.

#### Changes Since Last Session

First session — no prior sessions to compare against.

---

## Current State

**What is done:**
- Two full audits completed (Session 1: 2026-03-30, Session 2: 2026-04-05)
- 24 total suggestions written (S001-S024)
- Session 1: 12 suggestions, 10 implemented, 1 accepted/deferred (S010), 1 wont-fix (S012)
- Session 2: 12 new suggestions (2 P0, 7 P1, 3 P2) focused on module-level CRITICAL.md files
- Root-level documentation (CLAUDE.md, CRITICAL.md, GOALS.md) is now mostly accurate
- Module-level CRITICAL.md files identified as the main remaining documentation gap

**What is NOT done:**
- Head AI triage of Session 2 suggestions (S013-S024)
- Implementation of Session 2 fixes (not my responsibility)
- Deep line-reference audit of chemistry/, structure/, context/, dynamics/, utils/, processing/ CRITICAL.md files (smaller files, less likely to have drift, but not fully verified)
- S010 (ruff violations) still deferred from Session 1

**Next steps:**
1. Head AI reads `admin/suggestions.md` and triages S013-S024
2. P0 items first: S013 (CI branch) and S014 (ranking/CRITICAL.md) are the most critical
3. P1 items: S015-S021 address module CRITICAL.md drift and stale content
4. P2 items: S022-S024 are improvements (gitignore, naming, missing script)
5. After fixes, a third session should do a final verification pass and audit the remaining 6 module CRITICAL.md files not deeply checked in this session

---

## Context Recovery

If your context compacts:
1. Re-read this log
2. Re-read `admin/INSTRUCTIONS.md`
3. Check `admin/suggestions.md` for your prior suggestions
4. Resume from "Next steps" above
