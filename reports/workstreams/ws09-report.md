# WS09: ADMET Predictor -- Progress Report

## Status

- **State:** Complete (code, data prep, model trained and verified)
- **Last updated:** 2026-04-06T00:00:00+00:00
- **Session count:** 1
- **Test count added:** 32
- **Files created:** 5
- **Files modified:** 3

## Objective

Create the ADMET data preparation pipeline (TDC benchmarks), the ADMET predictor
adapter that loads a trained checkpoint, and the ADMET filter gate that flags or
excludes candidates with hERG liability or CYP3A4 inhibition. This adds safety
screening to the generation pipeline.

---

## Progress Log

### Session 1 -- 2026-03-28 (retrospective)

> This workstream was completed before the documentation system was established.
> This report was reconstructed from git history and commit messages.

#### Completed (5 commits)
1. `scripts/prepare_admet_data.py` -- ADMET data preparation with 3-tier TDC fallback
2. `src/statebind/ml/admet_predictor.py` -- ADMET prediction adapter with singleton model loading
3. `src/statebind/generation/admet_filter.py` -- ADMET filter gate for candidate safety screening
4. `tests/test_admet_integration.py` -- 32 integration tests
5. Report integration, CRITICAL.md updates, lint fixes

#### Decisions Made
- Singleton pattern for model loading (load once, predict many)
- 3-tier fallback for data: TDC API -> cached download -> embedded minimal set
- Filter works in permissive fallback mode without trained checkpoint
- Updated `tests/test_imports.py` with ADMET import checks

---

## Current State

**What is done:** All code, integration, and model training complete.

### ADMET Training Results (2026-04-06)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| hERG AUROC | 0.7745 | > 0.75 | Exceeded |
| CYP3A4 AUROC | 0.7323 | > 0.70 | Exceeded |
| Solubility R² | 0.46 | -- | Weak (low data coverage) |
| Parameters | 187K | -- | -- |
| Best epoch | 40 / 150 | -- | -- |
| Training time | 197s on L40S | -- | -- |
| Training data | 27,698 molecules (6 TDC endpoints) | -- | -- |
| Checkpoint | `artifacts/models/admet/best_model.pt` (775KB) | -- | -- |

**Key finding:** Hard pass/fail ADMET filtering eliminates ALL kinase inhibitor candidates (100% hERG failure). Kinase inhibitors are inherently hERG-liable. ADMET is best used as **informational annotation**, not a pre-ranking gate. Documented as a project limitation.

---

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `scripts/prepare_admet_data.py` | TDC data download and processing | 784 |
| `src/statebind/ml/admet_predictor.py` | ADMET prediction adapter | 390 |
| `src/statebind/generation/admet_filter.py` | Safety filter gate | 133 |
| `tests/test_admet_integration.py` | ADMET integration tests | 391 |
| `data/processed/admet_combined.json` | Processed ADMET training data | -- |
| `data/processed/admet_metadata.json` | ADMET data metadata | -- |

## Files Modified

| File | What Changed | Lines Changed |
|------|-------------|---------------|
| `scripts/report_comparative_results.py` | ADMET report integration | +63 |
| `src/statebind/ml/CRITICAL.md` | ADMET predictor notes | +12 |
| `tests/test_imports.py` | ADMET import checks | +17 |

## Handoff Notes

Workstream is fully complete: integration code written, ADMET model trained on HPC (L40S), classification targets met, scoring verified. Hard ADMET filtering too aggressive for kinase inhibitors — use as informational annotation only.
