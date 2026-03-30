# Admin AI: Suggestions

Structured suggestions from the Admin AI for the Head AI to triage.
Only the Head AI changes status fields.

**Status lifecycle:** `suggested` --> `accepted` --> `implemented` / `wont-fix`

---

## Active Suggestions

<!-- Newest first. Admin AI adds entries here. Head AI updates status. -->

| ID | Priority | Category | Status | Summary |
|----|----------|----------|--------|---------|
| S001 | P0 | Documentation | suggested | CLAUDE.md architecture missing chemistry/ module, lists nonexistent pockets/ |
| S002 | P0 | Cross-Reference | suggested | 18 of 23 file:line references in CLAUDE.md and CRITICAL.md point to wrong lines |
| S003 | P0 | Stale Content | suggested | GOALS.md Section 6 says "0 of 9 workstreams", "359 tests", everything "Not started" |
| S004 | P1 | Stale Content | suggested | CLAUDE.md stale counts: "359 tests" (x4), "72 .py files", "14 test files" |
| S005 | P1 | Documentation | suggested | CLAUDE.md Section 3 module table has wrong file counts for 3 modules |
| S006 | P1 | Stale Content | suggested | CRITICAL.md and TODO.md say "540 tests" — actual count is 538 |
| S007 | P1 | Stale Content | suggested | Module READMEs stale: evaluation/ claims no stats, ml/ claims no training data |
| S008 | P1 | Cross-Reference | suggested | INTERFACES.md contracts 5 and 6 don't match actual implementations |
| S009 | P1 | Stale Content | suggested | TODO.md Section 2 data prep scripts shown unchecked but scripts and data exist |
| S010 | P2 | Config | suggested | CI workflow guaranteed to fail — ~40 ruff violations block `ruff check src/` |
| S011 | P2 | Stale Content | suggested | GOALS.md Section 3 discusses WS01/WS03 as future priorities — both complete |
| S012 | P3 | Scaffolding | suggested | Inconsistent __init__.py exports — 5 modules export, 6 modules have only docstrings |

---

## Suggestion Details

<!-- Each suggestion gets its own ### heading below, newest first. -->

### S001: CLAUDE.md architecture missing chemistry/ module, lists nonexistent pockets/

- **Priority:** P0
- **Category:** Documentation
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `CLAUDE.md` lines 36, 138, 152-178 (Section 3 table), 193-211 (Section 4), 405-418 (Section 9)

**Problem:** The `chemistry/` subpackage (created by WS01, 7 files, provides Morgan fingerprints, descriptors, validation, SA scores, docking proxy) is completely absent from CLAUDE.md. It does not appear in:
- Section 1 key numbers ("12 subpackages" — should be 12 but with chemistry/ replacing pockets/)
- Section 3 architecture table (12 modules listed, chemistry/ missing)
- Section 3 pipeline diagram
- Section 4 dependency graph
- Section 9 file tree

Meanwhile, `pockets/` is listed as a placeholder module in Section 3 ("0 files") but the directory does not exist — `src/statebind/pockets/` returns no files. A new AI agent would:
1. Not know chemistry/ exists and would miss RDKit fingerprints, docking proxy, etc.
2. Expect pockets/ to exist and be confused when it doesn't.

**Suggested Fix:**
1. Replace `pockets/` row in Section 3 table with `chemistry/` (7 files: `fingerprints.py`, `descriptors.py`, `validation.py`, `sa_score.py`, `docking_data.py`, `docking_proxy.py`, `__init__.py`).
2. Add chemistry/ to Section 4 dependency graph (consumed by baselines/, ranking/).
3. Add chemistry/ to Section 9 file tree.
4. Remove pockets/ from Section 3 and Section 9.

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S002: Nearly all file:line references in CLAUDE.md and CRITICAL.md are wrong

- **Priority:** P0
- **Category:** Cross-Reference
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `CLAUDE.md` Sections 5, 14; `CRITICAL.md` lines 7-13, 17-19, 30, 40-41, 63-64

**Problem:** Workstreams (especially WS02 and WS04) inserted code into `ranking/scoring.py` and `baselines/scoring.py`, shifting line numbers. 18 of 23 verified references are now wrong. A new AI agent following these references would land on the wrong code.

**Wrong references in `ranking/scoring.py`:**
| Documented | Claimed content | Actual line now |
|------------|----------------|-----------------|
| :40-45 | DEFAULT_WEIGHTS | :86-91 |
| :47-52 | SCORING_METHOD | :93-97 |
| :55-86 | state_specificity | :139-170 |
| :89-97 | _validate_weights() | :173-181 |
| :100 | score_unified() | :184 |
| :191-239 | rank_state_aware() | :288-336 |
| :242-275 | merge_rankings() | :339-372 |

**Wrong references in `baselines/scoring.py`:**
| Documented | Claimed content | Actual line now |
|------------|----------------|-----------------|
| :69 | reference_similarity scorer | :78 |
| :83 | druglikeness scorer | :101 |
| :135-149 | docking stub | :202-216 |
| :155 | score_candidates() | :248 |
| :176-180 | baseline weights | :269-273 |

**Correct references (still valid):**
- `baselines/scoring.py:59-66` (_REFERENCE_BINDERS) — STILL CORRECT
- `processing/models.py:52-57` (ConformationalState) — STILL CORRECT
- `ml/__init__.py:25-30` (HAS_TORCH) — STILL CORRECT
- `baselines/models.py:53-57` (CandidateSource) — STILL CORRECT

**Suggested Fix:** Update all file:line references in CLAUDE.md Sections 5 and 14, and in CRITICAL.md, to match current line numbers. Consider using function/class names as anchors alongside line numbers to make references more durable.

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S003: GOALS.md Section 6 Success Criteria Table is massively stale

- **Priority:** P0
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `GOALS.md` lines 182-201 (Section 6)

**Problem:** The Success Criteria Table says nearly every metric is "Not started" with pre-workstream values. This is the primary reference for progress tracking and is completely wrong:

| Metric | GOALS.md says | Reality |
|--------|--------------|---------|
| Passing tests | 359 / In progress | 538 (19 test files) |
| Similarity method | Not started | Complete (WS02: Morgan/ECFP4) |
| Statistical testing | Not started | Complete (WS03: Mann-Whitney U, bootstrap CI) |
| CI/CD | Not started | Complete (WS06: GitHub Actions) |
| Druglikeness method | Not started | Complete (WS02: RDKit QED + Lipinski) |
| Synthetic accessibility | Not started | Complete (WS01: SA score) |
| Workstreams complete | 0 of 9 / Not started | 9 of 9 / Complete |
| Docking scoring | Not started | Integration code complete (WS04+WS08), training pending |
| Training data | Not started | Prepared (ChEMBL EGFR + TDC ADMET) |

A new agent reading GOALS.md would think no workstreams have started and plan from scratch.

**Suggested Fix:** Update every row in the Success Criteria Table to reflect actual status. Change "Current" column values and "Status" column. Mark completed items. Note which items are pending only on ML training.

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S004: CLAUDE.md stale numeric counts in 4+ locations

- **Priority:** P1
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `CLAUDE.md` lines 36, 38, 94, 411, 412, 484

**Problem:** Multiple hardcoded counts in CLAUDE.md are pre-workstream values:

| Location | Current text | Should be |
|----------|-------------|-----------|
| Line 36 | "72 Python source files across 12 subpackages" | "86 Python source files across 12 subpackages" |
| Line 38 | "12 test modules + test_imports.py + test_cli.py = 14 test files, 359 tests" | "19 test files, 538 tests" |
| Line 94 | "Existing 359 tests must continue to pass" | "Existing 538 tests must continue to pass" |
| Line 411 | "72 .py files across 12 subpackages" | "86 .py files across 12 subpackages" |
| Line 412 | "14 test files, 359 tests" | "19 test files, 538 tests" |
| Line 484 | "total count must be >= 359" | "total count must be >= 538" |

**Suggested Fix:** Find-and-replace all instances. Also update the line 36 line count (~13,700 lines is likely stale too but I did not verify).

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S005: CLAUDE.md Section 3 module table has wrong file counts

- **Priority:** P1
- **Category:** Documentation
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `CLAUDE.md` Section 3 module details table (lines ~152-178)

**Problem:** Workstreams added files to several modules. The file counts in the Section 3 table are stale:

| Module | CLAUDE.md says | Actual | New files |
|--------|---------------|--------|-----------|
| evaluation/ | 4 | 7 | +sensitivity.py, statistics.py, plotting.py (WS03, WS05) |
| generation/ | 7 | 9 | +vae_integration.py, admet_filter.py (WS07, WS09) |
| ml/ | 13 | 15 | +affinity_predictor.py, admet_predictor.py (WS08, WS09) |
| baselines/ | 8 | 8 | (correct) |
| ranking/ | 4 | 4 | (correct) |

The "Key Files" column for these modules should also list the new important files (e.g., `affinity_predictor.py` for ml/, `statistics.py` for evaluation/).

**Suggested Fix:** Update file counts and Key Files column for evaluation/, generation/, ml/. Also add chemistry/ row (7 files).

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S006: CRITICAL.md and TODO.md say "540 tests" — actual count is 538

- **Priority:** P1
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `CRITICAL.md` line 57; `TODO.md` lines 203, 208; `reports/head-ai-log.md` lines 32, 100

**Problem:** Multiple files reference "540 tests" as the current count. Counting all `def test_` functions across the 19 test files yields 538. The discrepancy is small but matters for accuracy — CLAUDE.md Rule 1 emphasizes scientific honesty.

Test count breakdown (538 total across 19 files):
- test_context.py: 52, test_dynamics.py: 50, test_baselines.py: 47, test_generation.py: 40, test_ranking.py: 39, test_processing.py: 33, test_chemistry.py: 32, test_admet_integration.py: 32, test_data.py: 31, test_structure.py: 31, test_statistics.py: 27, test_evaluation.py: 25, test_mpnn_integration.py: 22, test_imports.py: 19, test_docking_proxy.py: 19, test_vae_integration.py: 17, test_plotting.py: 14, test_utils.py: 5, test_cli.py: 3.

**Suggested Fix:** Update all "540" references to "538" (or run `pytest --co -q | tail -1` to get the authoritative count and use that number).

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S007: Module READMEs stale after workstreams

- **Priority:** P1
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `src/statebind/evaluation/README.md`, `src/statebind/ml/README.md`, `src/statebind/ranking/README.md`, `src/statebind/generation/README.md`

**Problem:** Several module READMEs describe pre-workstream state:

1. **evaluation/README.md** — Likely says "No statistical testing or matplotlib visualizations" but WS03 added `statistics.py` and `sensitivity.py`, and WS05 added `plotting.py` and updated `figures.py`. The README doesn't document these new files or their APIs.

2. **ml/README.md** — States "No training data exists yet" but training data is prepared: `data/processed/egfr_affinity.json` (1,678 compounds), `data/processed/admet_combined.json`, `data/processed/egfr_smiles_train.json`. Also doesn't mention `affinity_predictor.py` or `admet_predictor.py` (the integration adapters added by WS08/WS09).

3. **ranking/README.md** — References WS02, WS04, WS08 as future workstreams that "will modify" scoring. All three are complete and already merged.

4. **generation/README.md** — "VAE integration pending" but `vae_integration.py` exists (WS07). Also doesn't mention `admet_filter.py` (WS09).

**Suggested Fix:** Update each README to reflect post-workstream state: list new files, update APIs, remove "future"/"pending" language for completed work.

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S008: INTERFACES.md contracts 5 and 6 don't match implementations

- **Priority:** P1
- **Category:** Cross-Reference
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `workstreams/INTERFACES.md` (Contracts 5 and 6); `src/statebind/generation/vae_integration.py`; `src/statebind/ml/admet_predictor.py`

**Problem:**

**Contract 5 (VAE):** Specifies `generate_vae_candidates(state, n_samples, temperature, checkpoint_path) -> list[StateConditionedCandidate]`. This function does NOT exist. The actual implementation uses `load_vae_candidates(path)` and `build_vae_libraries(candidates)` — a different design that reads from a pre-generated JSON artifact rather than generating on the fly.

**Contract 6 (ADMET):** Specifies `check_admet_pass(smiles: str, thresholds: dict[str, float] | None) -> tuple[bool, dict[str, float]]`. The actual implementation at `ml/admet_predictor.py:57` has an incompatible signature: `check_admet_pass(predictions: dict[str, float], thresholds: dict[str, tuple[str, float]] | None) -> tuple[bool, list[str]]`. Takes predictions dict (not SMILES) and returns failure task names (not predictions dict).

**Suggested Fix:** Update INTERFACES.md to match actual implementations. Add notes explaining design decisions (e.g., VAE generates via external script for GPU isolation rather than inline generation).

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S009: TODO.md Section 2 data preparation scripts shown unchecked

- **Priority:** P1
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `TODO.md` lines 31-33 (Section 2)

**Problem:** Three data preparation items are listed with `- [ ]` (unchecked):
- `scripts/prepare_vae_data.py`
- `scripts/prepare_mpnn_data.py`
- `scripts/prepare_admet_data.py`

All three scripts exist on disk. The head-ai-log confirms training data is prepared:
- `data/processed/egfr_affinity.json` — 1,678 ChEMBL EGFR compounds
- `data/processed/admet_combined.json` — TDC ADMET benchmark data
- `data/processed/egfr_smiles_train.json` — VAE training data

**Suggested Fix:** Check all three items `- [x]` in TODO.md Section 2. Add a note that data exists but models are not yet trained.

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S010: CI workflow guaranteed to fail due to ruff violations

- **Priority:** P2
- **Category:** Config
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `.github/workflows/ci.yml`; ~40 files in `src/` with ruff violations

**Problem:** The CI workflow runs `ruff check src/` in both the `test` and `lint` jobs. CRITICAL.md documents ~40 pre-existing ruff violations across `src/` (F401 unused imports, I001 import sorting, E501 line length, F541 f-strings, N815 naming). These violations guarantee CI failure on every push, making the CI/CD pipeline (WS06) non-functional despite being "complete."

**Suggested Fix:** Run `ruff check --fix src/` to auto-fix all fixable violations (I001, F401, most E501). Manually resolve remaining violations. Verify with `ruff check src/` before committing.

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S011: GOALS.md Section 3 discusses completed workstreams as future priorities

- **Priority:** P2
- **Category:** Stale Content
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `GOALS.md` lines 90-97 (Section 3, Priority 3)

**Problem:** Section 3 "Short-Term Goals — Priority 3" discusses WS01 (Chemistry Foundation) and WS03 (Statistical Testing) as if they are future work to start: "These two workstreams can start immediately and unblock downstream work." Both are complete and merged to ML. A new agent reading this section might try to re-execute them.

Similarly, Section 3 "Priority 1" and "Priority 2" discuss data preparation and model training as if not started — data preparation is done (see S009).

**Suggested Fix:** Rewrite GOALS.md Section 3 to reflect current state. Mark completed items. Reframe remaining work (model training, full pipeline re-run) as the actual current priorities.

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

### S012: Inconsistent __init__.py exports across modules

- **Priority:** P3
- **Category:** Scaffolding
- **Status:** suggested
- **Date:** 2026-03-30
- **File(s):** `src/statebind/baselines/__init__.py`, `src/statebind/structure/__init__.py`, `src/statebind/context/__init__.py`, `src/statebind/dynamics/__init__.py`, `src/statebind/ranking/__init__.py`, `src/statebind/evaluation/__init__.py`

**Problem:** Six modules have `__init__.py` files with only a docstring and no explicit exports or `__all__`. Meanwhile, six other modules (data, utils, processing, chemistry, ml, generation) have proper exports with `__all__` lists. This inconsistency means some modules support `from statebind.chemistry import compute_morgan_fingerprint` while others require direct submodule imports like `from statebind.baselines.scoring import score_candidates`.

**Suggested Fix:** Add explicit imports and `__all__` to the six bare modules. Low priority since the code works as-is — callers import from submodules directly.

**Head AI Notes:** _{filled in by Head AI when triaging}_

---

## Resolved Suggestions

<!-- Suggestions that have been implemented or marked wont-fix. Never delete. -->

| ID | Priority | Category | Status | Summary | Resolution Date |
|----|----------|----------|--------|---------|----------------|
| (none yet) | | | | | |
