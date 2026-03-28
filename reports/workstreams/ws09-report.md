# WS09: ADMET Predictor -- Progress Report

## Status

- **State:** Complete (code + data prep; model training is separate HPC task)
- **Last updated:** 2026-03-28T12:00:00+00:00
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

**What is done:** All code and integration. Model training requires HPC.

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

Workstream code is complete. Model training requires HPC -- see `HUMANONLY.md`
Section 4. The filter gate works in permissive fallback mode without a checkpoint
(all candidates pass).
