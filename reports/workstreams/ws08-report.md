# WS08: MPNN Affinity -- Progress Report

## Status

- **State:** Integration complete (awaiting model training)
- **Last updated:** 2026-03-28T19:30:00+00:00
- **Session count:** 1
- **Test count added:** 22
- **Files created:** 3
- **Files modified:** 2

## Objective

Create the MPNN data preparation pipeline (ChEMBL EGFR affinity data), the affinity
predictor adapter that loads a trained MPNN checkpoint, and the cascading fallback in
`ranking/scoring.py`: MPNN -> docking proxy (WS04) -> constant 0.5 stub. The MPNN
architecture already exists in `ml/mpnn.py`; this workstream creates integration code.

---

## Progress Log

### Session 1 (2026-03-28)

1. **Read all required files:** CLAUDE.md, workstream brief, INTERFACES.md Contract 4,
   ml/README.md, ml/CRITICAL.md, ranking/CRITICAL.md, existing scoring.py (post-WS04),
   admet_predictor.py (pattern reference), prepare_vae_data.py (pattern reference).

2. **Created `scripts/prepare_mpnn_data.py`:**
   - 3-tier fallback: local file → ChEMBL REST API → curated ~90 compounds
   - ChEMBL API query: CHEMBL203, pchembl_value >= 3, IC50, paginated (5 pages)
   - Curated set includes ~60 EGFR inhibitors with type-based pIC50 assignments +
     ~30 non-binder decoys (aspirin, caffeine, etc.) with low pIC50 (3.0-4.5)
   - Deduplication by canonical SMILES, median pIC50 for duplicates
   - Output: `data/processed/egfr_affinity.json` + metadata JSON
   - **Test run:** ChEMBL API returned 1,678 unique compounds (pIC50 4.0-11.0, mean 6.50)

3. **Created `src/statebind/ml/affinity_predictor.py`:**
   - Singleton pattern matching `admet_predictor.py` exactly
   - `_MODEL`, `_DEVICE`, `_LOAD_ATTEMPTED` module-level globals
   - `_normalize_pic50(pic50)`: sigmoid((pIC50 - 5) / 2) → [0, 1]
   - `_model_loaded() -> bool`: disambiguates "predicted 0.5" from "failed"
   - `predict_affinity(smiles) -> float`: lazy load, never raises, returns 0.5 on failure
   - `predict_affinity_batch(smiles_list) -> list[float]`: chunked at 256, PyG Batch
   - `reset_singleton()`: for testing

4. **Modified `src/statebind/ranking/scoring.py`:**
   - `_score_docking()`: inserted MPNN as Priority 1 before DockingProxy (WS04)
   - `_get_scoring_method()`: checks MPNN first, then proxy, then stub
   - Updated module docstring (line 6)
   - All MPNN imports are lazy (inside function bodies) — no circular import risk

5. **Created `tests/test_mpnn_integration.py`:**
   - 22 tests across 5 groups: data prep (4), normalization (4), adapter (6),
     scoring integration (5), edge cases (3)
   - All 22 tests pass
   - Full suite: 540 passed, 8 skipped (GPU/checkpoint-dependent, expected)

6. **Lint verification:** ruff clean on all new files. Scoring.py lint issues are
   pre-existing (same count as main branch).

---

## Current State

**What is done:**
- `scripts/prepare_mpnn_data.py` — data preparation with 3-tier fallback ✅
- `data/processed/egfr_affinity.json` — 1,678 compounds from ChEMBL API ✅
- `src/statebind/ml/affinity_predictor.py` — singleton scoring adapter ✅
- `src/statebind/ranking/scoring.py` — 3-tier cascading fallback (MPNN → proxy → stub) ✅
- `tests/test_mpnn_integration.py` — 22 tests, all passing ✅
- Full test suite: 540 passed, 8 skipped ✅

**What is NOT done yet:**
- Train the MPNN model: `python scripts/train_mpnn.py --config configs/mpnn.yaml`
  (requires GPU; data is ready at `data/processed/egfr_affinity.json`)
- Model quality tests (test_rmse_below_threshold, etc.) — skipped until checkpoint exists

**Blockers:** None for integration code. Training requires GPU.

---

## Next Steps

1. Train MPNN on prepared data (GPU required):
   `python scripts/train_mpnn.py --config configs/mpnn.yaml`
2. Verify model quality: RMSE < 1.0, R² > 0.5, Pearson > 0.6
3. Re-run tests to confirm model-dependent tests pass with checkpoint

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/prepare_mpnn_data.py` | ChEMBL EGFR affinity data preparation (3-tier fallback) |
| `src/statebind/ml/affinity_predictor.py` | Singleton adapter wrapping MPNN for scoring pipeline |
| `tests/test_mpnn_integration.py` | 22 integration tests |

## Files Modified

| File | Changes |
|------|---------|
| `src/statebind/ranking/scoring.py` | `_score_docking()`: 3-tier cascade (MPNN→proxy→stub); `_get_scoring_method()`: MPNN check; docstring update |
| `data/processed/egfr_affinity.json` | Generated: 1,678 ChEMBL EGFR compounds with pIC50 |

## Tests Written

- `test_mpnn_integration.py`: 22 tests across 5 groups
  - Data preparation: 4 tests
  - Normalization: 4 tests
  - Adapter interface: 6 tests
  - Scoring integration: 5 tests
  - Edge cases: 3 tests

## Architecture Decisions

1. **`_model_loaded()` instead of `score != 0.5`:** `_normalize_pic50(5.0)` legitimately
   returns 0.5 (pIC50=5 means IC50=10µM). Using `_model_loaded()` checks whether the
   singleton loaded successfully, avoiding the ambiguity.

2. **Lazy imports in `_score_docking()`:** All MPNN imports are inside the function body
   to prevent circular imports and keep the module importable without torch.

3. **Curated fallback includes decoys:** ~30 non-EGFR molecules with low pIC50 (3.0-4.5)
   ensure the MPNN learns what a non-binder looks like, not just EGFR inhibitor potency.

---

## Handoff Notes

**To resume this workstream:**
1. Read `CLAUDE.md`
2. Read `workstreams/08-mpnn-affinity.md`
3. Read this file
4. The code is complete — next step is GPU training

**DO NOT:**
- Run in parallel with WS04 (both touch `ranking/scoring.py`)
- Change `DEFAULT_WEIGHTS` without updating `SCORING_METHOD`
- Remove the docking proxy fallback (WS04's contribution)
- Modify existing files listed in WS08 brief "Files NOT to Touch" section
