# WS04: Docking Proxy -- Progress Report

## Status

- **State:** Complete
- **Last updated:** 2026-03-28T15:00:00+00:00
- **Session count:** 1
- **Test count added:** 19
- **Files created:** 3
- **Files modified:** 6

## Objective

Create a lightweight MLP docking proxy trained on embedded SAR data from known EGFR
inhibitors. The proxy replaces the constant-0.5 docking stub with a function that
returns varied, chemically meaningful scores. It sits in the cascading fallback chain:
MPNN (WS08) -> Docking Proxy (this WS) -> constant 0.5 stub.

---

## Progress Log

### Session 1 — 2026-03-28

1. **Read all prerequisite files:** workstream brief, INTERFACES.md Contract 2, baselines/scoring.py (stub at lines 202-216), ranking/scoring.py (unified scorer), dynamics/world_model.py (MLP pattern), chemistry module.

2. **Created `src/statebind/chemistry/docking_data.py`** — Embedded training data: 9 EGFR binders (erlotinib, gefitinib, osimertinib, afatinib, lapatinib, dacomitinib, neratinib, poziotinib, vandetanib) + 25 decoys (metformin, aspirin, caffeine, etc.). All with SMILES, labels, names, source citations. First 3 binder SMILES match `_REFERENCE_BINDERS` exactly.

3. **Created `src/statebind/chemistry/docking_proxy.py`** — DockingProxy MLP class:
   - Architecture: Linear(20→16) → ReLU → Linear(16→1) → Sigmoid
   - Features: 13 top-variance Morgan FP bits + 7 normalized descriptors (MW, LogP, TPSA, HBA, HBD, rings, rotatable bonds)
   - Training: Xavier init, SGD, gradient clipping ±1.0, binary cross-entropy, 200 epochs
   - Singleton via `get_default_proxy()` with double-checked locking
   - Graceful fallback: returns 0.5 when RDKit unavailable

4. **Smoke tested proxy** — Results:
   - Erlotinib: 0.9994, Caffeine: 0.018, Invalid: 0.5
   - Mean binder: 0.9963, Mean decoy: 0.0031
   - Std: 0.4382 (vs 0.0 for stub)

5. **Created `tests/test_docking_proxy.py`** — 19 tests in 5 classes:
   - TestTrainingData: labels, SMILES validity, sufficient count
   - TestDockingProxyModel: output range, loss decreases, binders > decoys, AUROC > 0.7, non-constant, batch consistency, invalid/empty SMILES
   - TestDefaultProxy: singleton, trained predictions differ
   - TestDockingProxyFallback: RDKit absence handling
   - TestDockingProxySpecific: erlotinib > 0.7, caffeine < 0.4, training < 5s

6. **Modified `src/statebind/baselines/scoring.py`** — Added `_score_docking()` function with proxy fallback. Wired into `score_candidates()`. Updated ScoreComponent construction and scoring_method string to reflect proxy status dynamically.

7. **Modified `src/statebind/ranking/scoring.py`** — Added `_score_docking()` function locally. Wired into `score_unified()`. Updated `_get_scoring_method()` to report proxy status. Updated UnifiedScoreComponent construction.

8. **Updated `src/statebind/chemistry/__init__.py`** — Added exports for `DockingProxy` and `get_default_proxy`.

9. **Updated `tests/test_imports.py`** — Added `test_import_docking_proxy` for docking_data and docking_proxy imports.

10. **Updated existing tests:**
    - `tests/test_ranking.py:178` — `test_docking_proxy_is_stub` → `test_docking_proxy_status` (conditional on RDKit)
    - `tests/test_baselines.py:246` — `test_docking_stub_is_labeled` → `test_docking_proxy_is_labeled` (conditional on RDKit)

11. **Full test suite: 518 passed, 8 skipped, 0 failed** in 22.86s.

---

## Current State

**What is done:** Everything. All definition-of-done criteria met:
- ✅ `docking_data.py` with 9 binders and 25 decoys, all with citations
- ✅ `docking_proxy.py` with DockingProxy class and get_default_proxy()
- ✅ `tests/test_docking_proxy.py` with 19 tests (exceeds 15 target)
- ✅ Proxy AUROC > 0.7 on training data (perfect separation in practice)
- ✅ `baselines/scoring.py` updated with proxy fallback
- ✅ `ranking/scoring.py` updated with proxy fallback
- ✅ `is_stub` flag correctly reflects proxy vs stub status
- ✅ All 518 tests pass (was 359+ baseline)
- ✅ Model trains in < 1 second (well under 5s limit)
- ✅ Documentation states this is discriminative, not affinity prediction

**What is NOT done:** Nothing. WS04 is complete.

---

## Next Steps

None — workstream complete. Ready for merge.

---

## Files Created

| File | Purpose |
|------|---------|
| `src/statebind/chemistry/docking_data.py` | 9 EGFR binders + 25 decoys as embedded constants |
| `src/statebind/chemistry/docking_proxy.py` | DockingProxy MLP class + singleton |
| `tests/test_docking_proxy.py` | 19 tests for proxy data, model, integration, fallback |

## Files Modified

| File | Change |
|------|--------|
| `src/statebind/baselines/scoring.py` | Added `_score_docking()`, wired into `score_candidates()` |
| `src/statebind/ranking/scoring.py` | Added `_score_docking()`, wired into `score_unified()` |
| `src/statebind/chemistry/__init__.py` | Added DockingProxy, get_default_proxy exports |
| `tests/test_imports.py` | Added `test_import_docking_proxy` |
| `tests/test_ranking.py` | Updated stub test → conditional proxy/stub test |
| `tests/test_baselines.py` | Updated stub test → conditional proxy/stub test |

## Tests Written

19 new tests in `tests/test_docking_proxy.py`:
- 3 data validation tests
- 8 model behavior tests
- 3 singleton/integration tests
- 2 fallback tests
- 3 specific behavior tests (erlotinib high, caffeine low, speed)

## Architecture Decisions

1. **numpy-only MLP** — No torch dependency for the proxy. Uses the same hand-rolled MLP pattern as `dynamics/world_model.py`. This keeps the proxy in the core dependency set (numpy is always available).

2. **Feature vector: 13 FP bits + 7 descriptors = 20 dims** — Top-13 Morgan fingerprint bits by variance capture discriminative substructure patterns. 7 molecular descriptors provide property-level context. Small feature space prevents overfitting on the 34-sample training set.

3. **Singleton with double-checked locking** — `get_default_proxy()` trains on first call and caches. Thread-safe. Training takes < 1s so the first scoring call has negligible overhead.

4. **`_score_docking()` defined locally in both scoring files** — Avoids coupling between baselines/scoring.py and ranking/scoring.py while keeping the fallback pattern identical. Small code duplication (10 lines) is acceptable for independence.

5. **Graceful RDKit degradation** — When RDKit is unavailable, `_featurize()` returns None, `predict()` returns 0.5, and `is_stub` is True. Functionally identical to the old stub behavior.

---

## Handoff Notes

**To resume this workstream:** It's done. No further work needed.

**Key facts for downstream consumers (WS08):**
- The cascading fallback in `_score_docking()` checks proxy first, then falls back to stub
- WS08 should add MPNN as priority 1 in the cascade: MPNN → proxy → stub
- The `_score_docking()` function signature is `(smiles, pdb_id) -> (score, is_stub, method)`
- Both `baselines/scoring.py` and `ranking/scoring.py` have their own `_score_docking()`

**DO NOT:**
- Modify `baselines/scoring.py` reference binders (lines 59-66)
- Change `DEFAULT_WEIGHTS` in `ranking/scoring.py`
- Delete `_score_docking_stub()` — it is the final fallback
