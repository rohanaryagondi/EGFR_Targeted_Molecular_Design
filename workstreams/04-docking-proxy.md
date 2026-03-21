# Workstream 04: Learned Docking Proxy

## Goal

Replace `_score_docking_stub()` (which returns a constant 0.5 for all candidates) with a learned discriminative model that separates EGFR-like molecules from non-binders. This gives the docking_proxy component (20% of score weight) actual discriminative power.

**Important scientific framing:** This is a _discriminative binding proxy_, NOT a binding affinity predictor. It answers "does this molecule look like an EGFR binder?" not "what is the binding affinity?" Document this clearly.

## Prerequisites

**Workstream 01 must be complete.** The proxy uses Morgan fingerprints + molecular descriptors as features.

**Cannot run in parallel with Workstream 02** — both modify `baselines/scoring.py` and `ranking/scoring.py`.

## Files to Create

### `src/statebind/chemistry/docking_data.py`

Training data for the proxy model. Embedded as constants (no external data files needed).

```python
"""Training data for the EGFR binding proxy.

Known binders: 9 EGFR inhibitors with literature-documented activity.
Decoys: ~25 drug-like molecules with no reported kinase activity.

IMPORTANT: This is a discriminative model, not a binding affinity predictor.
It separates EGFR-like molecules from random drug-like molecules.
"""

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class TrainingCompound:
    smiles: str
    label: int          # 1 = EGFR binder, 0 = decoy
    name: str
    source: str         # literature citation or database ID
    notes: str = ""

EGFR_BINDERS: list[TrainingCompound] = [
    TrainingCompound("COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC", 1, "Erlotinib", "Moyer et al. 1997"),
    TrainingCompound("COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1", 1, "Gefitinib", "Wakeling et al. 2002"),
    # ... (add osimertinib, afatinib, lapatinib, dacomitinib, neratinib, poziotinib, vandetanib)
]

DECOYS: list[TrainingCompound] = [
    # ~25 simple drug-like molecules from DrugBank with no kinase activity
    # e.g., metformin, aspirin, ibuprofen, acetaminophen, caffeine, etc.
    # Each with source citation
]

def get_training_data() -> tuple[list[str], list[int]]:
    """Return (smiles_list, label_list) for model training."""
```

### `src/statebind/chemistry/docking_proxy.py`

The learned proxy model.

```python
"""Learned EGFR binding proxy.

Architecture: hand-rolled MLP (same pattern as dynamics/world_model.py).
Features: Morgan fingerprint bits (top features by variance) + molecular descriptors.
Training: SGD with gradient clipping on embedded EGFR SAR data.

LIMITATION: This is a discriminative model trained on 9 binders vs ~25 decoys.
It measures "EGFR-likeness" not binding affinity. It cannot rank binders by potency.
"""

from __future__ import annotations
import numpy as np

class DockingProxy:
    """Learned EGFR binding discriminator."""

    def __init__(self, input_dim: int = 20, hidden_dim: int = 16):
        """Initialize with random weights."""

    def _featurize(self, smiles: str) -> np.ndarray | None:
        """Convert SMILES to feature vector.

        Features:
        - Top-N Morgan fingerprint bits (by variance across training set)
        - Molecular descriptors: MW, LogP, TPSA, HBA, HBD, rings, rotatable bonds
        Uses statebind.chemistry.fingerprints and descriptors.
        Returns None if featurization fails.
        """

    def fit(self, smiles_list: list[str], labels: list[int], n_epochs: int = 200, lr: float = 0.01) -> list[float]:
        """Train on (SMILES, label) pairs. Returns loss history."""

    def predict(self, smiles: str) -> float:
        """Predict EGFR-likeness score in [0, 1]. Returns 0.5 if featurization fails."""

    def predict_batch(self, smiles_list: list[str]) -> list[float]:
        """Batch prediction."""


# Singleton pattern for default proxy
_DEFAULT_PROXY: DockingProxy | None = None

def get_default_proxy() -> DockingProxy:
    """Get or create the default trained proxy.

    Trains on first call, caches for subsequent calls.
    Thread-safe via simple lock.
    """
```

**MLP pattern to reuse from `dynamics/world_model.py:81-100`:**
- Forward pass: `z = input @ W1 + b1`, `h = np.maximum(0, z)` (ReLU), `out = h @ W2 + b2`
- Sigmoid output for binary classification
- SGD with gradient clipping (`np.clip(grad, -1.0, 1.0)`)
- Loss: binary cross-entropy

### `tests/test_docking_proxy.py`

Target: ~15-20 tests.

1. **Data tests:**
   - `test_training_data_labels()` — all binders have label=1, all decoys label=0
   - `test_training_data_valid_smiles()` — all SMILES parse (if RDKit available)
   - `test_training_data_sufficient()` — at least 30 total compounds

2. **Model tests:**
   - `test_proxy_output_range()` — all predictions in [0, 1]
   - `test_proxy_training_loss_decreases()` — loss at epoch 0 > loss at final epoch
   - `test_proxy_binders_score_higher()` — mean binder score > mean decoy score
   - `test_proxy_discrimination()` — AUROC > 0.7 on training data (sanity check)
   - `test_proxy_non_constant_output()` — std(predictions) > 0.01 (unlike stub)
   - `test_proxy_predict_batch()` — batch matches individual predictions
   - `test_proxy_invalid_smiles()` — returns 0.5 for invalid SMILES

3. **Integration tests:**
   - `test_default_proxy_singleton()` — get_default_proxy() returns same instance
   - `test_default_proxy_trained()` — predictions differ from 0.5

4. **Fallback tests:**
   - `test_proxy_without_rdkit()` — returns 0.5 for everything (graceful degradation)

## Files to Modify

### `src/statebind/baselines/scoring.py`

Replace `_score_docking_stub()` call in `score_candidates()`:

```python
def _score_docking(smiles: str, pdb_id: str) -> tuple[float, bool, str]:
    """Score docking. Returns (score, is_stub, method_string)."""
    try:
        from statebind.chemistry.docking_proxy import get_default_proxy
        proxy = get_default_proxy()
        score = proxy.predict(smiles)
        if abs(score - 0.5) > 0.001:  # proxy is trained and producing real scores
            return score, False, "Learned EGFR binding proxy (MLP on Morgan+descriptors)"
    except ImportError:
        pass
    return _score_docking_stub(smiles, pdb_id), True, "STUB: constant 0.5"
```

Keep `_score_docking_stub()` as fallback. Update `ScoreComponent` construction in `score_candidates()` to use the returned `is_stub` and `method` values.

### `src/statebind/ranking/scoring.py`

Same pattern in `score_unified()` (line 119):

```python
# Replace:
dock = _score_docking_stub(smiles, "unified")
# With:
dock, dock_is_stub, dock_method = _score_docking(smiles, "unified")
```

Update the `UnifiedScoreComponent` for docking_proxy to use `dock_is_stub` and `dock_method`.

Update `SCORING_METHOD` string to reflect proxy status.

## Files NOT to Touch

- `src/statebind/chemistry/fingerprints.py` — Workstream 01 owns this
- `src/statebind/chemistry/descriptors.py` — Workstream 01 owns this
- `src/statebind/evaluation/*` — separate workstreams
- `src/statebind/generation/*`, `src/statebind/dynamics/*`, `src/statebind/context/*`

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| MLP architecture | `dynamics/world_model.py:81-100` | Copy the forward/backward pass pattern |
| SGD training loop | `dynamics/training.py` or `dynamics/world_model.py` | Reuse gradient clipping, loss tracking |
| `_score_docking_stub()` | `baselines/scoring.py:135-149` | Keep as fallback |
| Morgan fingerprints | `chemistry/fingerprints.py` (from WS01) | Feature extraction |
| Molecular descriptors | `chemistry/descriptors.py` (from WS01) | Feature extraction |
| Reference binder SMILES | `baselines/scoring.py:59-66` | Cross-reference with training data |

## Definition of Done

- [ ] `docking_data.py` with 9+ binders and 25+ decoys, all with citations
- [ ] `docking_proxy.py` with DockingProxy class and get_default_proxy()
- [ ] `tests/test_docking_proxy.py` with 15+ tests
- [ ] Proxy AUROC > 0.7 on training data
- [ ] `baselines/scoring.py` updated to use proxy with stub fallback
- [ ] `ranking/scoring.py` updated to use proxy with stub fallback
- [ ] `is_stub` flag correctly reflects proxy vs stub status
- [ ] All existing 359+ tests pass
- [ ] Model trains in < 5 seconds (lightweight)
- [ ] Documentation clearly states this is a discriminative model, not affinity prediction

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation — edge cases, gotchas, implicit assumptions, or things that broke unexpectedly — add them to the relevant CRITICAL.md file(s):

- **Module-level**: `src/statebind/{module}/CRITICAL.md` for facts specific to the module you modified
- **Project-level**: `/CRITICAL.md` for facts that cross module boundaries

Format: one fact per line, include `file:line` references. Be detailed yet concise.

## Agent Instructions

Be detailed yet concise in all code, comments, and documentation. Include `file:line` references when noting important locations. No fluff — every line should carry information.
