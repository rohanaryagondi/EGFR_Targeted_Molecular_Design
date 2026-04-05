# Admin AI: Suggestions

Structured suggestions from the Admin AI for the Head AI to triage.
Only the Head AI changes status fields.

**Status lifecycle:** `suggested` --> `accepted` --> `implemented` / `wont-fix`

---

## Active Suggestions

<!-- Newest first. Admin AI adds entries here. Head AI updates status. -->

| ID | Priority | Category | Status | Summary |
|----|----------|----------|--------|---------|
| S010 | P2 | Config | accepted | CI workflow guaranteed to fail — ~40 ruff violations block `ruff check src/` |
| S013 | P0 | Config | implemented | CI workflow triggers on `main` branch but default branch is `ML` — CI never runs |
| S014 | P0 | Cross-Reference | implemented | ranking/CRITICAL.md has 10+ wrong line references — most are off by 50-100 lines |
| S015 | P1 | Cross-Reference | accepted | baselines/CRITICAL.md has 4 wrong line references for scoring.py |
| S016 | P1 | Cross-Reference | accepted | evaluation/CRITICAL.md has 5+ stale line references (off by 3-18 lines) |
| S017 | P1 | Cross-Reference | accepted | generation/CRITICAL.md references ranking/scoring.py at wrong lines (192, 202-209) |
| S018 | P1 | Stale Content | accepted | ml/CRITICAL.md says "MPNN data prep script does not exist yet" but it exists |
| S019 | P1 | Stale Content | wont-fix | GOALS.md Section 4 scoring table shows pre-WS02 "current" methods |
| S020 | P1 | Stale Content | wont-fix | CLAUDE.md says "84 Python source files" and "37 pipeline scripts" — actual is 86 and 40 |
| S021 | P1 | Cross-Reference | accepted | Root CRITICAL.md import list for ranking/scoring.py is incomplete (missing 2 imports) |
| S022 | P2 | Config | wont-fix | .gitignore does not cover ML training data files in data/processed/ |
| S023 | P2 | Stale Content | wont-fix | CLAUDE.md Section 9 file tree header says "BioForge/" — project is "statebind" |
| S024 | P2 | Cross-Reference | accepted | scripts/generate_vae_candidates.py referenced in INTERFACES.md and CLAUDE.md but does not exist |

---

## Suggestion Details

<!-- Each suggestion gets its own ### heading below, newest first. -->

### S010: CI workflow guaranteed to fail due to ruff violations

- **Priority:** P2
- **Category:** Config
- **Status:** accepted
- **Date:** 2026-03-30
- **File(s):** `.github/workflows/ci.yml`; ~40 files in `src/` with ruff violations

**Problem:** The CI workflow runs `ruff check src/` in both the `test` and `lint` jobs. CRITICAL.md documents ~40 pre-existing ruff violations across `src/` (F401 unused imports, I001 import sorting, E501 line length, F541 f-strings, N815 naming). These violations guarantee CI failure on every push, making the CI/CD pipeline (WS06) non-functional despite being "complete."

**Suggested Fix:** Run `ruff check --fix src/` to auto-fix all fixable violations (I001, F401, most E501). Manually resolve remaining violations. Verify with `ruff check src/` before committing.

**Head AI Notes:** Accepted. Deferred to a dedicated cleanup session — fixing ~40 ruff violations across the codebase requires careful review to avoid breaking imports. Will be addressed as a standalone task, not bundled with the documentation triage.

---

### S013: CI workflow triggers on `main` branch but default branch is `ML`

- **Priority:** P0
- **Category:** Config
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `.github/workflows/ci.yml` lines 4-7

**Problem:** The CI workflow triggers on `push: branches: [main]` and `pull_request: branches: [main]`. However, the head-ai-log.md records that the default branch was changed from `main` to `ML` (Decision dated 2026-03-25). CRITICAL.md confirms: "The default branch on GitHub was changed from `main` to `ML`. All work happens on `ML`." This means CI never triggers on any push or PR to the active development branch. The entire CI/CD setup (WS06) is non-functional not just because of ruff violations (S010) but because it watches the wrong branch.

**Suggested Fix:** Change `.github/workflows/ci.yml` lines 5 and 7 from `branches: [main]` to `branches: [ML]` (or `branches: [main, ML]` if main is kept as a stable reference).

---

### S014: ranking/CRITICAL.md has 10+ wrong line references

- **Priority:** P0
- **Category:** Cross-Reference
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `src/statebind/ranking/CRITICAL.md`

**Problem:** Session 1 (S002) fixed line references in the ROOT `CRITICAL.md` and `CLAUDE.md`, but the module-level `ranking/CRITICAL.md` was not updated. Nearly every line reference is wrong because workstreams (WS02, WS04, WS08) added code to `scoring.py` that shifted line numbers. Specific errors:

| What | CRITICAL.md says | Actual location |
|------|-----------------|-----------------|
| `_validate_weights()` | `scoring.py:89-97` | `scoring.py:173-181` |
| Required weight keys | `scoring.py:91` | `scoring.py:175` |
| `DEFAULT_WEIGHTS` | `scoring.py:40-45` | `scoring.py:86-91` |
| `SCORING_METHOD` | `scoring.py:47-52` | `scoring.py:93-97` |
| `merge_rankings()` | `scoring.py:242-275` | `scoring.py:339-372` |
| `rank_state_aware()` | `scoring.py:191-239` | `scoring.py:288-336` |
| `_compute_state_specificity()` | `scoring.py:55-86` | `scoring.py:139-170` |
| Static baseline specificity | `scoring.py:160,166` | Needs re-verification |
| Rank assignment | `scoring.py:178-179, 229-230` | `scoring.py:268-269, 326-327` |
| SCORING_METHOD constant | `scoring.py:49-54` | `scoring.py:93-97` |
| `_get_scoring_method()` | `scoring.py:57-69` | `scoring.py:100+` |
| `_get_scoring_method()` (WS08 ref) | `scoring.py:99` | `scoring.py:100` |

A new agent reading `ranking/CRITICAL.md` would look at wrong code for every single critical fact. This is the most actively misleading file in the project.

**Suggested Fix:** Update all line references in `ranking/CRITICAL.md` to match current code. Add function name anchors alongside line numbers (following the pattern established in S002 for root CRITICAL.md).

---

### S015: baselines/CRITICAL.md has 4 wrong line references for scoring.py

- **Priority:** P1
- **Category:** Cross-Reference
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `src/statebind/baselines/CRITICAL.md`

**Problem:** The baselines/CRITICAL.md has stale line references for `baselines/scoring.py` and `ranking/scoring.py`:

| What | CRITICAL.md says | Actual location |
|------|-----------------|-----------------|
| Docking stub | `scoring.py:135-149` | `scoring.py:202-216` |
| `_score_druglikeness` | `scoring.py:83-129` | `scoring.py:101-148` (heuristic) |
| Baseline weights | `scoring.py:176-180` | `scoring.py:269-273` |
| Unified weights (ranking) | `ranking/scoring.py:40-45` | `ranking/scoring.py:86-91` |

Note: The file does mention that "Docking stub line numbers shifted after WS04 additions. The stub is now around line 202" -- but the initial reference on line 3 still says 135-149. This is contradictory within the same file.

**Suggested Fix:** Update all stale line references. Remove the contradictory "now around line 202" note since the primary reference should just be correct.

---

### S016: evaluation/CRITICAL.md has 5+ stale line references

- **Priority:** P1
- **Category:** Cross-Reference
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `src/statebind/evaluation/CRITICAL.md`

**Problem:** Several line references in evaluation/CRITICAL.md are off by 3-18 lines:

| What | CRITICAL.md says | Actual location |
|------|-----------------|-----------------|
| `compute_novelty()` | `comparison.py:152-173` | `comparison.py:155` |
| HAS_SCIPY | `statistics.py:14-18` | `statistics.py:18-20` |
| `_COMPONENT_NAMES` | `sensitivity.py:20` | `sensitivity.py:17` |
| `_rescore_merged()` | `sensitivity.py:52-66` | `sensitivity.py:43` |
| `run_full_comparison` run_statistics | `comparison.py:200` | `comparison.py:182` |

These are smaller offsets (3-18 lines) compared to ranking/CRITICAL.md, but still misleading.

**Suggested Fix:** Update all line references. Consider function name anchors for durability.

---

### S017: generation/CRITICAL.md references ranking/scoring.py at wrong lines

- **Priority:** P1
- **Category:** Cross-Reference
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `src/statebind/generation/CRITICAL.md`

**Problem:** The generation/CRITICAL.md cross-references ranking module at stale locations:
- Says `ranking/scoring.py:rank_state_aware() at line 192` -- actual is line 288.
- Says `ranking/scoring.py:202-209` for deduplication -- actual deduplication is at lines 304-306.

**Suggested Fix:** Update the two cross-module references to ranking/scoring.py.

---

### S018: ml/CRITICAL.md says MPNN data prep script does not exist

- **Priority:** P1
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `src/statebind/ml/CRITICAL.md` line 1

**Problem:** The very first bullet in ml/CRITICAL.md says: "All three models (VAE, MPNN, ADMET) are code-complete but UNTRAINED. VAE training data prep script exists (`scripts/prepare_vae_data.py`); ADMET data prep script exists (`scripts/prepare_admet_data.py`); **MPNN data prep script does not exist yet**."

But `scripts/prepare_mpnn_data.py` exists (created during WS08). The file was created and the CRITICAL.md was not updated. This is misleading because an agent reading this would think they need to create the script.

**Suggested Fix:** Update the first bullet to list all three data prep scripts as existing. This was already noted in session 1 (S009 addressed the TODO.md version of this issue), but the ml/CRITICAL.md was not included in the fix.

---

### S019: GOALS.md Section 4 scoring table shows pre-WS02 "current" methods

- **Priority:** P1
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `GOALS.md` lines 120-125

**Problem:** The "Full Cascade Scoring" table in GOALS.md Section 4 has a "Method (current)" column that still shows pre-workstream values:
- reference_similarity: "SMILES 3-gram Tanimoto" (actual current: Morgan/ECFP4 when RDKit available)
- druglikeness: "Heuristic MW/HBA/HBD" (actual current: RDKit QED + Lipinski when RDKit available)

WS02 is complete and these methods are now the Morgan/ECFP4 and QED-based versions. The "current" column should reflect the post-WS02 state.

**Suggested Fix:** Either update the "Method (current)" column to show post-WS02 reality, or restructure the table to reflect that the pre-ML-training state uses WS02 chemistry and the only remaining "target" upgrade is the MPNN replacing the docking stub (the reference_similarity and druglikeness targets are already achieved).

---

### S020: CLAUDE.md says "84 Python source files" and "37 pipeline scripts"

- **Priority:** P1
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `CLAUDE.md` Section 1 ("Key numbers") and Section 9

**Problem:** CLAUDE.md Section 1 states "84 Python source files across 12 subpackages" and "37 pipeline scripts in `scripts/`". Actual counts:
- 86 Python source files (84 in subpackages + cli.py + root __init__.py)
- 40 pipeline scripts in scripts/

The 84 count was correct for the 12 subpackages (5+3+7+8+8+6+6+6+15+9+4+7=84) but omits `cli.py` and the root `__init__.py`. The 37 script count is 3 short -- the data prep scripts (`prepare_vae_data.py`, `prepare_mpnn_data.py`, `prepare_admet_data.py`) were added during workstreams but the count was not updated.

**Suggested Fix:** Update to "86 Python source files across 12 subpackages" (or "84 in subpackages + 2 root files") and "40 pipeline scripts in `scripts/`".

---

### S021: Root CRITICAL.md import list for ranking/scoring.py is incomplete

- **Priority:** P1
- **Category:** Cross-Reference
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `CRITICAL.md` line 40

**Problem:** CRITICAL.md states: "`ranking/scoring.py` imports scoring functions FROM `baselines/scoring.py` (`_score_druglikeness`, `_score_reference_similarity`, `_score_docking_stub`, `_tanimoto_ngram`) at lines 19-24."

Actual imports at lines 19-26 are: `_has_rdkit`, `_score_druglikeness`, `_score_druglikeness_enhanced`, `_score_reference_similarity`, `_score_docking_stub`, `_tanimoto_ngram`. Two imports are missing from the documentation: `_has_rdkit` and `_score_druglikeness_enhanced` (both added by WS02). The line range is also slightly off (19-26, not 19-24).

**Suggested Fix:** Update the import list to include all 6 imported names and fix the line range to 19-26.

---

### S022: .gitignore does not cover ML training data files in data/processed/

- **Priority:** P2
- **Category:** Config
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `.gitignore`

**Problem:** The `.gitignore` covers `data/processed/context/*`, `data/processed/structures/*`, `data/processed/ligands/*`, and `data/processed/benchmark/*` but does NOT cover the ML training data files that sit directly in `data/processed/`:
- `egfr_affinity.json` (MPNN training data)
- `admet_combined.json` (ADMET training data)
- `egfr_smiles_train.json`, `egfr_smiles_val.json` (VAE training data)
- `admet_metadata.json`, `egfr_affinity_metadata.json`, `egfr_smiles_metadata.json`

These are generated by data prep scripts and are potentially large files that should not be committed to git. If someone runs `git add .` they would be included.

**Suggested Fix:** Add `data/processed/*.json` to `.gitignore` (with appropriate `!` exceptions for any small JSON files that should be tracked), or add specific entries for each ML training data file.

---

### S023: CLAUDE.md Section 9 file tree header says "BioForge/"

- **Priority:** P2
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `CLAUDE.md` Section 9

**Problem:** The file tree in CLAUDE.md Section 9 starts with `BioForge/` as the root directory name. The project is called "statebind" and the repository directory is `repo` under `statebind/`. "BioForge" appears to be an old project name or working title. A new agent might be confused about which project they are working on.

**Suggested Fix:** Change `BioForge/` to `statebind/` (or `.` or the actual directory name) in the file tree header.

---

### S024: scripts/generate_vae_candidates.py referenced but does not exist

- **Priority:** P2
- **Category:** Cross-Reference
- **Status:** suggested
- **Date:** 2026-04-05
- **File(s):** `workstreams/INTERFACES.md` Contract 5 (line ~251), `CLAUDE.md` Section 6 ("ML -> generation" integration)

**Problem:** INTERFACES.md Contract 5 states: "VAE generation runs via `scripts/generate_vae_candidates.py` as a separate GPU-bound process." CLAUDE.md Section 6 says: "VAE generation runs via `scripts/generate_vae_candidates.py` for GPU isolation." However, this script does not exist in `scripts/`. It was referenced as part of the design for WS07 but was apparently never created (WS07 focused on data prep and integration, with training deferred to HPC).

**Suggested Fix:** Either create the script (it should load a trained VAE, sample from it, and write `artifacts/generation/vae_candidates.json`) or update the documentation to note that this script is planned but not yet created, pending model training.

---

## Resolved Suggestions

<!-- Suggestions that have been implemented or marked wont-fix. Never delete. -->

| ID | Priority | Category | Status | Summary | Resolution Date |
|----|----------|----------|--------|---------|----------------|
| S001 | P0 | Documentation | implemented | CLAUDE.md architecture missing chemistry/ module, lists nonexistent pockets/ | 2026-03-30 |
| S002 | P0 | Cross-Reference | implemented | 18 of 23 file:line references in CLAUDE.md and CRITICAL.md point to wrong lines | 2026-03-30 |
| S003 | P0 | Stale Content | implemented | GOALS.md Section 6 says "0 of 9 workstreams", "359 tests", everything "Not started" | 2026-03-30 |
| S004 | P1 | Stale Content | implemented | CLAUDE.md stale counts: "359 tests" (x4), "72 .py files", "14 test files" | 2026-03-30 |
| S005 | P1 | Documentation | implemented | CLAUDE.md Section 3 module table has wrong file counts for 3 modules | 2026-03-30 |
| S006 | P1 | Stale Content | implemented | CRITICAL.md and TODO.md say "540 tests" — actual count is 548 (pytest verified) | 2026-03-30 |
| S007 | P1 | Stale Content | implemented | Module READMEs stale: evaluation/ claims no stats, ml/ claims no training data | 2026-03-30 |
| S008 | P1 | Cross-Reference | implemented | INTERFACES.md contracts 5 and 6 don't match actual implementations | 2026-03-30 |
| S009 | P1 | Stale Content | implemented | TODO.md Section 2 data prep scripts shown unchecked but scripts and data exist | 2026-03-30 |
| S011 | P2 | Stale Content | implemented | GOALS.md Section 3 discusses WS01/WS03 as future priorities — both complete | 2026-03-30 |
| S012 | P3 | Scaffolding | wont-fix | Inconsistent __init__.py exports — 5 modules export, 6 modules have only docstrings | 2026-03-30 |

### Resolved Details

**S001** (implemented): Replaced pockets/ with chemistry/ (7 files) in CLAUDE.md Sections 3, 4, and 9. Added chemistry/ to pipeline diagram and dependency graph.

**S002** (implemented): Updated all file:line references in CLAUDE.md Sections 5, 13, and 15, and in CRITICAL.md. Added function name anchors alongside line numbers for durability (e.g., `:86 DEFAULT_WEIGHTS` instead of just `:40`). Note: Admin AI counted 538 tests but `pytest --co -q` yields 548 — used authoritative pytest count.

**S003** (implemented): Updated every row in GOALS.md Section 6 Success Criteria Table. Marked 10 items as Complete, 8 as Pending training. Updated "Current" column values to post-workstream reality.

**S004** (implemented): Updated all instances: "72 Python source files" → "84" (verified count), "14 test files, 359 tests" → "19 test files, 548 tests", "Existing 359 tests" → "Existing 548 tests", "total count must be >= 359" → ">= 548".

**S005** (implemented): Updated file counts: evaluation/ 4→7, generation/ 7→9, ml/ 13→15. Added chemistry/ row (7 files). Updated Key Files columns with new files (statistics.py, affinity_predictor.py, vae_integration.py, etc.).

**S006** (implemented): Admin AI counted 538, but `pytest --co -q` returns 548. Updated all references from "540" to "548" in CRITICAL.md and TODO.md.

**S007** (implemented): Updated 4 module READMEs (evaluation/, ml/, ranking/, generation/) to document new files, APIs, and completed workstreams. Removed "pending"/"future" language for completed work.

**S008** (implemented): Updated INTERFACES.md Contract 5 (VAE) to reflect actual `load_vae_candidates()` / `build_vae_libraries()` API. Updated Contract 6 (ADMET) to match actual `check_admet_pass(predictions, thresholds) -> (bool, list[str])` signature. Added design notes explaining decisions.

**S009** (implemented): Checked all three data prep items `[x]` in TODO.md Section 2.

**S011** (implemented): Updated GOALS.md Section 3 Priority 3 to mark WS01/WS03 as complete. Updated Section 4 to note all 9 workstreams are finished.

**S012** (wont-fix): Code works as-is — callers import from submodules directly. Adding `__all__` and explicit exports to 6 modules would increase maintenance burden without current benefit. If a future workstream needs clean public APIs from these modules, this can be revisited.
