# Workstream 08: MPNN Binding Affinity Predictor

## Goal

Replace the `docking_proxy` stub in `ranking/scoring.py` — which returns a constant 0.5 for all candidates, wasting 20% of the total score weight — with a learned Message Passing Neural Network (MPNN) that predicts pIC50 binding affinity from molecular graphs. This gives the docking component actual discriminative power and is the single highest-impact improvement to scoring quality.

**Important distinction from Workstream 04:** Workstream 04 creates a lightweight discriminative proxy ("does this look like an EGFR binder?") using Morgan fingerprints. This workstream trains a proper graph neural network that predicts quantitative binding affinity (pIC50). The two can coexist via a cascading fallback: MPNN (best) -> Workstream 04 proxy -> stub (worst).

## Why This Matters

- The docking_proxy component has weight 0.20 in the unified scoring function (see `ranking/scoring.py:DEFAULT_WEIGHTS`). Currently it returns 0.5 for every molecule, contributing zero discriminative signal.
- An MPNN trained on ChEMBL EGFR pIC50 data can predict binding affinity from molecular structure alone, providing real differentiation between strong and weak binders.
- The state-aware pipeline benefits disproportionately: state-conditioned candidates tend to be more structurally diverse, so a model that can evaluate novel scaffolds is critical.

## Prerequisites

- **Workstream 01 (Chemistry Foundation)** is REQUIRED. The MPNN uses `statebind.ml.graphs.smiles_to_graph()` which depends on RDKit for SMILES parsing and molecular graph construction. Without RDKit, graph features cannot be computed.
- **PyTorch** and **PyTorch Geometric** must be installed (`pip install torch torch_geometric`).
- **ML infrastructure** in `src/statebind/ml/` is already built.

## Files Already Created

These files are fully implemented and tested. Read them before starting remaining work.

| File | Purpose |
|------|---------|
| `src/statebind/ml/mpnn.py` | `AffinityMPNN` model: NNConv message-passing layers + mean/max pooling + prediction head. Includes `MPNNConfig`, `EdgeNetwork`, `MPNNLayer`. |
| `src/statebind/ml/affinity_dataset.py` | `AffinityDataset` + `load_affinity_dataset` + `split_dataset`. Loads JSON records with `smiles` and `pIC50` keys, converts to PyG Data objects. |
| `src/statebind/ml/graphs.py` | `smiles_to_graph()` — converts SMILES to PyG Data with atom features (35-dim) and bond features (11-dim). Requires RDKit. |
| `scripts/train_mpnn.py` | Full training pipeline: config loading, dataset loading/splitting, training loop, test evaluation (RMSE, MAE, R2, Pearson), checkpointing, model card. |
| `configs/mpnn.yaml` | Default hyperparameters and data paths. |

## Remaining Work

### Step 1: Data Preparation

Create the training data file expected by `configs/mpnn.yaml`:

- `data/processed/egfr_affinity.json`

**Data source:** ChEMBL EGFR bioactivity (target CHEMBL203). Query for compounds with IC50 values.

**Required JSON format:**
```json
[
    {"smiles": "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC", "pIC50": 7.82},
    {"smiles": "CC(=O)Nc1ccc...", "pIC50": 5.41},
    ...
]
```

**pIC50 conversion:** `pIC50 = -log10(IC50_in_molar)`. For IC50 in nM: `pIC50 = 9 - log10(IC50_nM)`.

**Script to create:** `scripts/prepare_mpnn_data.py`

This script should:
1. Load raw ChEMBL EGFR data from `data/raw/` (or download via ChEMBL API)
2. Filter for records with valid IC50 values and valid SMILES
3. Convert IC50 to pIC50 (handle unit inconsistencies — nM vs uM)
4. Remove duplicates (same canonical SMILES) — take median pIC50 for duplicates
5. Verify SMILES can be converted to graphs via `smiles_to_graph()` (drop failures)
6. Write JSON to `data/processed/egfr_affinity.json`
7. Print summary statistics (N compounds, pIC50 distribution, graph conversion success rate)

**Expected dataset size:** 3,000-5,000 compounds (ChEMBL EGFR has ~4,000 IC50 records).

### Step 2: Training on HPC Cluster

Run the existing training script:
```bash
python scripts/train_mpnn.py --config configs/mpnn.yaml
```

**Expected outputs:**
- `artifacts/models/mpnn/best_model.pt` — best checkpoint
- `artifacts/models/mpnn/model_card.json` — metadata with test metrics
- `artifacts/logs/mpnn/training_log.csv` — per-epoch loss
- `artifacts/evaluation/mpnn_metrics.json` — test set RMSE, MAE, R2, Pearson

**Tuning guidance:**
- If RMSE > 1.2 on test set, try `hidden_dim: 256` and `n_message_passing_layers: 4`
- If overfitting (train_loss << val_loss), increase `dropout: 0.2` or reduce `hidden_dim`
- If underfitting, reduce `weight_decay` to 0 and increase `epochs` to 300

### Step 3: Scoring Adapter

Create a scoring adapter that loads the trained MPNN and exposes a simple interface for the ranking pipeline.

**File to create:** `src/statebind/ml/affinity_predictor.py`

```python
"""Scoring adapter: wraps trained MPNN for use in the ranking pipeline.

Provides a simple `predict_affinity(smiles) -> float` interface that:
1. Converts SMILES to a PyG graph via smiles_to_graph()
2. Runs the MPNN forward pass
3. Normalizes pIC50 to [0, 1] via sigmoid((pIC50 - 5) / 2)
4. Returns the normalized score

The normalization maps:
    pIC50 = 5 (10 uM) -> 0.5
    pIC50 = 7 (100 nM) -> 0.73
    pIC50 = 9 (1 nM) -> 0.88
    pIC50 = 3 (1 mM) -> 0.27
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Singleton model instance (loaded once)
_MODEL: AffinityMPNN | None = None
_DEVICE: torch.device | None = None


def predict_affinity(smiles: str) -> float:
    """Predict normalized binding affinity for a SMILES string.

    Returns a float in [0, 1] where higher = stronger predicted binder.
    Returns 0.5 (neutral) if:
        - Model checkpoint not found
        - SMILES cannot be converted to a graph
        - Any inference error occurs

    This is a drop-in replacement for _score_docking_stub().
    """
    ...


def predict_affinity_batch(smiles_list: list[str]) -> list[float]:
    """Batch version of predict_affinity(). More efficient for >10 molecules."""
    ...


def _load_model(
    checkpoint_path: Path | str = "artifacts/models/mpnn/best_model.pt",
) -> tuple[AffinityMPNN, torch.device] | None:
    """Load the trained MPNN from checkpoint. Returns None on failure."""
    ...


def _normalize_pic50(pic50: float) -> float:
    """Normalize pIC50 to [0, 1] via sigmoid((pIC50 - 5) / 2).

    Centers at pIC50=5 (10 uM) and uses a scale factor of 2 to spread
    the sigmoid across the pharmacologically relevant range (3-9).
    """
    import math
    return 1.0 / (1.0 + math.exp(-(pic50 - 5.0) / 2.0))
```

### Step 4: Integration into Ranking Pipeline

Modify `src/statebind/ranking/scoring.py` to use the MPNN when available, with cascading fallback.

**The fallback chain:**
1. **MPNN predictor** (`ml/affinity_predictor.py`) — best: learned affinity on molecular graphs
2. **Docking proxy** (Workstream 04, if completed) — good: discriminative binding proxy
3. **Stub** (`baselines/scoring.py:_score_docking_stub`) — worst: constant 0.5

**Changes to `ranking/scoring.py`:**

Replace the line:
```python
dock = _score_docking_stub(smiles, "unified")
```

With:
```python
dock = _score_docking(smiles)
```

And add a new function:
```python
def _score_docking(smiles: str) -> float:
    """Score binding affinity with cascading fallback.

    Tries: MPNN predictor -> docking proxy (WS04) -> stub (0.5).
    """
    # Try MPNN first
    try:
        from statebind.ml.affinity_predictor import predict_affinity
        score = predict_affinity(smiles)
        if score != 0.5:  # 0.5 means the model failed internally
            return score
    except (ImportError, RuntimeError):
        pass

    # Fall back to docking proxy (Workstream 04)
    try:
        from statebind.chemistry.docking_proxy import get_default_proxy
        proxy = get_default_proxy()
        return proxy.predict(smiles)
    except (ImportError, AttributeError):
        pass

    # Final fallback: stub
    return _score_docking_stub(smiles, "unified")
```

**Also update** the `UnifiedScoreComponent` method string to reflect which backend was used:
```python
UnifiedScoreComponent(
    name="docking_proxy",
    value=round(dock, 4),
    weight=weights["docking_proxy"],
    method=_get_docking_method(),   # Returns string describing active backend
    is_stub=(_get_docking_backend() == "stub"),
)
```

## Interface Contracts

### Primary Interface

```python
def predict_affinity(smiles: str) -> float:
    """Predict normalized binding affinity.

    Args:
        smiles: A SMILES string representing a molecule.

    Returns:
        Float in [0.0, 1.0]. Higher = stronger predicted binder.
        Returns 0.5 on any failure (same as stub, so scoring degrades gracefully).
    """
```

### Internal pIC50 Normalization

```python
def _normalize_pic50(pic50: float) -> float:
    """sigmoid((pIC50 - 5) / 2) -> [0, 1]"""
```

Normalization rationale:
- pIC50 = 5 (IC50 = 10 uM, weak binder) maps to 0.5
- pIC50 = 7 (IC50 = 100 nM, moderate binder) maps to ~0.73
- pIC50 = 9 (IC50 = 1 nM, potent binder) maps to ~0.88
- Sigmoid ensures output stays strictly in (0, 1)

### Scoring Pipeline Compatibility

The adapter MUST be a drop-in replacement for `_score_docking_stub()`:
- Same return type: `float`
- Same value range: `[0.0, 1.0]`
- Same graceful failure: returns 0.5 on error
- No new required arguments to `score_unified()`

## Files NOT to Touch

- `src/statebind/ml/mpnn.py` — model architecture is finalized
- `src/statebind/ml/affinity_dataset.py` — dataset loading is finalized
- `src/statebind/ml/graphs.py` — graph construction is finalized
- `scripts/train_mpnn.py` — training loop is finalized
- `src/statebind/baselines/scoring.py` — Workstream 02 handles this; only touch `ranking/scoring.py`
- Any existing test files

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| MPNN model | `ml/mpnn.py:AffinityMPNN` | Load checkpoint, call `model(data)` |
| Graph construction | `ml/graphs.py:smiles_to_graph` | Convert SMILES -> PyG Data |
| Dataset loading | `ml/affinity_dataset.py:load_affinity_dataset` | Load and split training data |
| Docking stub | `baselines/scoring.py:_score_docking_stub` | Fallback when model unavailable |
| Scoring function | `ranking/scoring.py:score_unified` | Integration point for adapter |
| Model save/load | `ml/utils.py:save_model` | Checkpoint serialization |

## Testing Requirements

### `tests/test_mpnn_integration.py` — ~20 tests

**1. Data preparation tests:**
- `test_data_has_smiles_and_pic50()` — all records have required keys
- `test_pic50_range()` — pIC50 values in [2, 12] (reasonable pharmacological range)
- `test_no_duplicate_smiles()` — canonical SMILES are unique
- `test_all_smiles_convertible()` — every SMILES produces a valid PyG graph

**2. Model quality tests** (after training):
- `test_rmse_below_threshold()` — test set RMSE < 1.0 pIC50 units
- `test_r2_above_threshold()` — test set R-squared > 0.5
- `test_pearson_above_threshold()` — test set Pearson correlation > 0.6
- `test_known_binder_scores_high()` — erlotinib pIC50 prediction > 6.0
- `test_random_molecule_scores_lower()` — aspirin pIC50 prediction < erlotinib

**3. Adapter tests:**
- `test_predict_affinity_returns_float()` — output is a float
- `test_predict_affinity_range()` — output in [0.0, 1.0]
- `test_predict_affinity_invalid_smiles()` — returns 0.5 for garbage input
- `test_predict_affinity_empty_string()` — returns 0.5
- `test_normalize_pic50_at_5()` — returns 0.5 (center point)
- `test_normalize_pic50_monotonic()` — higher pIC50 -> higher normalized score
- `test_normalize_pic50_bounded()` — output always in (0, 1)

**4. Integration tests:**
- `test_scoring_with_mpnn()` — `score_unified()` uses MPNN when model is available
- `test_scoring_fallback_to_stub()` — `score_unified()` falls back to 0.5 when model missing
- `test_scoring_method_string_updated()` — `UnifiedScoreComponent.method` reflects MPNN backend
- `test_docking_component_not_stub()` — `is_stub=False` when MPNN is active
- `test_batch_prediction_consistent()` — `predict_affinity_batch()` matches individual calls

**5. Edge cases:**
- `test_predict_affinity_very_long_smiles()` — handles large molecules gracefully
- `test_predict_affinity_disconnected()` — handles disconnected SMILES (salts)

## Definition of Done

- [ ] `scripts/prepare_mpnn_data.py` creates valid JSON from ChEMBL EGFR data
- [ ] `data/processed/egfr_affinity.json` contains 3,000+ compounds with pIC50 values
- [ ] Training completes: RMSE < 1.0, R-squared > 0.5, Pearson > 0.6 on test set
- [ ] `src/statebind/ml/affinity_predictor.py` provides `predict_affinity(smiles) -> float`
- [ ] `ranking/scoring.py` updated with cascading fallback (MPNN -> proxy -> stub)
- [ ] `tests/test_mpnn_integration.py` with 20+ tests, all passing
- [ ] No existing tests broken (`pytest -v --tb=short` passes all 359+ tests)
- [ ] Model card saved with test metrics and normalization documentation
- [ ] `UnifiedScoreComponent.is_stub` is `False` when MPNN is active
- [ ] All new functions have type annotations and docstrings

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation — edge cases, gotchas, implicit assumptions, or things that broke unexpectedly — add them to the relevant CRITICAL.md file(s):

- **Module-level**: `src/statebind/{module}/CRITICAL.md` for facts specific to the module you modified
- **Project-level**: `/CRITICAL.md` for facts that cross module boundaries

Format: one fact per line, include `file:line` references. Be detailed yet concise.

## Agent Instructions

Be detailed yet concise in all code, comments, and documentation. Include `file:line` references when noting important locations. No fluff — every line should carry information.
