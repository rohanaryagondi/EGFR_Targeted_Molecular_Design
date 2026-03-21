# Workstream 09: Multi-Task ADMET Predictor

## Goal

Add ML-powered ADMET safety filtering to the candidate evaluation pipeline. A multi-task Graph Neural Network predicts six drug-safety and pharmacokinetic endpoints simultaneously (Caco-2 permeability, hERG inhibition, CYP3A4 inhibition, hepatic clearance, lipophilicity, solubility). Candidates that fail critical ADMET thresholds (especially hERG) are flagged or removed before ranking, and per-task ADMET scores are included in evaluation reports.

## Why This Matters

- The current pipeline scores candidates by reference similarity, druglikeness, docking, and state specificity — but has **no safety filtering**. A molecule with perfect binding but hERG liability is a non-starter in drug development.
- ADMET failures account for ~40% of clinical trial failures. Early computational filtering removes obviously problematic candidates.
- The multi-task architecture enables shared learning across endpoints, which improves performance on individual tasks (especially those with sparse labels like CYP3A4).

## Prerequisites

- **Workstream 01 (Chemistry Foundation)** is REQUIRED. The ADMET model uses `statebind.ml.graphs.smiles_to_graph()` which depends on RDKit for SMILES parsing and molecular graph construction.
- **PyTorch** and **PyTorch Geometric** must be installed (`pip install torch torch_geometric`).
- **ML infrastructure** in `src/statebind/ml/` is already built.

## Files Already Created

These files are fully implemented and tested. Read them before starting remaining work.

| File | Purpose |
|------|---------|
| `src/statebind/ml/admet.py` | `MultiTaskADMET` model: shared GIN/GCN backbone + task-specific heads. Includes `ADMETConfig`, `TaskHead`, `admet_loss` (with NaN masking). |
| `src/statebind/ml/admet_dataset.py` | `ADMETDataset` + `load_admet_dataset` + `split_admet_dataset`. Loads JSON records with per-task labels, handles NaN masking for missing endpoints. |
| `src/statebind/ml/graphs.py` | `smiles_to_graph()` — converts SMILES to PyG Data with atom features (35-dim) and bond features (11-dim). Requires RDKit. |
| `scripts/train_admet.py` | Full training pipeline: config loading, dataset loading/splitting, multi-task training loop with per-task loss weighting, test evaluation (RMSE/MAE/R2 for regression, accuracy/AUROC for classification), checkpointing, model card. |
| `configs/admet.yaml` | Default hyperparameters, task definitions, and per-task loss weights (hERG weighted 1.5x for safety criticality). |

## ADMET Endpoints

| Task | Type | Unit | Source | Threshold (flag if) |
|------|------|------|--------|-------------------|
| `caco2` | Regression | log cm/s | TDC Caco-2_Wang | < -6.0 (poor permeability) |
| `herg` | Classification | binary | TDC hERG | probability > 0.5 (hERG blocker) |
| `cyp3a4` | Classification | binary | TDC CYP3A4_Veith | probability > 0.7 (strong inhibitor) |
| `clearance` | Regression | mL/min/kg | TDC Clearance_Hepatocyte_AZ | > 50 (rapid clearance) |
| `lipophilicity` | Regression | LogD | TDC Lipophilicity_AstraZeneca | > 5.0 (too lipophilic) |
| `solubility` | Regression | LogS | TDC Solubility_AqSolDB | < -5.0 (insoluble) |

## Remaining Work

### Step 1: Data Preparation

Create the training data file expected by `configs/admet.yaml`:

- `data/processed/admet_combined.json`

**Data source:** Therapeutics Data Commons (TDC) ADMET benchmark datasets. Each task has its own dataset in TDC; this step merges them into a single multi-task JSON.

**Required JSON format:**
```json
[
    {"smiles": "CCO", "caco2": -5.12, "herg": 0.0, "cyp3a4": null, "clearance": 35.2, "lipophilicity": 1.3, "solubility": -1.8},
    {"smiles": "c1ccccc1", "caco2": null, "herg": 1.0, "cyp3a4": 0.0, "clearance": null, "lipophilicity": 2.1, "solubility": -2.5},
    ...
]
```

**Note:** Most molecules will NOT have labels for all 6 tasks — `null` values are expected and handled by NaN masking in the loss function. The `min_tasks` config parameter (default 1) controls the minimum number of non-null labels required to include a molecule.

**Script to create:** `scripts/prepare_admet_data.py`

This script should:
1. Download or load TDC benchmark datasets for each of the 6 endpoints
2. Canonicalize all SMILES (use RDKit if available, otherwise keep as-is)
3. Merge datasets by SMILES — same molecule may appear in multiple task datasets
4. For duplicates within a task: take median value (regression) or majority vote (classification)
5. Verify SMILES can be converted to graphs via `smiles_to_graph()` (drop failures)
6. Write merged JSON to `data/processed/admet_combined.json`
7. Print summary: N total molecules, label coverage per task, value distributions

**Expected dataset size:** 10,000-30,000 unique molecules (union across all 6 TDC datasets).

**TDC installation:**
```bash
pip install PyTDC
```

**TDC loading example:**
```python
from tdc.single_pred import ADME, Tox
caco2 = ADME(name="Caco2_Wang")
herg = Tox(name="hERG")
cyp3a4 = ADME(name="CYP3A4_Veith")
clearance = ADME(name="Clearance_Hepatocyte_AZ")
lipo = ADME(name="Lipophilicity_AstraZeneca")
solubility = ADME(name="Solubility_AqSolDB")
```

### Step 2: Training on HPC Cluster

Run the existing training script:
```bash
python scripts/train_admet.py --config configs/admet.yaml
```

**Expected outputs:**
- `artifacts/models/admet/best_model.pt` — best checkpoint (by total val loss)
- `artifacts/models/admet/final_model.pt` — final epoch checkpoint
- `artifacts/models/admet/model_card.json` — metadata with per-task metrics
- `artifacts/logs/admet/training_log.csv` — per-epoch total and per-task losses
- `artifacts/evaluation/admet_metrics.json` — per-task test evaluation

**Tuning guidance:**
- If hERG AUROC < 0.7, increase `task_weights.herg` to 2.0 and try `hidden_dim: 256`
- If regression tasks have RMSE >> 1.0, increase `n_gnn_layers` to 4
- If training is unstable, reduce `learning_rate` to 0.0005
- The GIN backbone (`gnn_type: gin`) generally outperforms GCN on molecular tasks; try GCN only if GIN converges poorly

### Step 3: ADMET Predictor Adapter

Create a scoring adapter that loads the trained model and exposes a simple prediction interface.

**File to create:** `src/statebind/ml/admet_predictor.py`

```python
"""Scoring adapter: wraps trained MultiTaskADMET for use in the filtering pipeline.

Provides `predict_admet(smiles) -> dict[str, float]` returning per-task scores.
Classification tasks return probabilities (sigmoid applied). Regression tasks
return raw predicted values.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Singleton model instance
_MODEL: MultiTaskADMET | None = None
_DEVICE: torch.device | None = None


def predict_admet(smiles: str) -> dict[str, float]:
    """Predict ADMET properties for a single molecule.

    Args:
        smiles: A SMILES string.

    Returns:
        Dictionary mapping task name to predicted value:
            - Classification tasks (herg, cyp3a4): probability in [0, 1]
            - Regression tasks (caco2, clearance, lipophilicity, solubility): raw value
        Returns empty dict on failure (invalid SMILES, model not loaded, etc.).
    """
    ...


def predict_admet_batch(smiles_list: list[str]) -> list[dict[str, float]]:
    """Batch version of predict_admet(). More efficient for large candidate sets."""
    ...


def check_admet_pass(
    predictions: dict[str, float],
    thresholds: dict[str, tuple[str, float]] | None = None,
) -> tuple[bool, list[str]]:
    """Check if ADMET predictions pass safety thresholds.

    Args:
        predictions: Output from predict_admet().
        thresholds: Optional override. Default thresholds:
            herg: (">", 0.5) — flag if P(hERG blocker) > 0.5
            cyp3a4: (">", 0.7) — flag if P(CYP3A4 inhibitor) > 0.7
            caco2: ("<", -6.0) — flag if poor permeability
            clearance: (">", 50.0) — flag if rapid clearance
            lipophilicity: (">", 5.0) — flag if too lipophilic
            solubility: ("<", -5.0) — flag if insoluble

    Returns:
        (passed, failures): Boolean pass/fail and list of failed task names.
    """
    ...


def _load_model(
    checkpoint_path: Path | str = "artifacts/models/admet/best_model.pt",
) -> tuple[MultiTaskADMET, torch.device] | None:
    """Load the trained ADMET model. Returns None on failure."""
    ...
```

### Step 4: Integration into Filtering Pipeline

Add an ADMET gate to the candidate filtering process. This creates a new filtering step that runs after the existing property-based filters.

**File to create:** `src/statebind/generation/admet_filter.py`

```python
"""ADMET safety filter for candidate molecules.

Runs the MultiTaskADMET model on each candidate and flags/removes those
that fail critical ADMET thresholds. Designed to slot into the filtering
pipeline after property-based filtering.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from statebind.generation.models import StateConditionedCandidate


class ADMETFilterResult(BaseModel):
    """Result of ADMET filtering for a single candidate."""

    candidate_id: str
    smiles: str
    predictions: dict[str, float] = Field(default_factory=dict)
    passed: bool = True
    failed_tasks: list[str] = Field(default_factory=list)


class ADMETFilterSummary(BaseModel):
    """Summary of ADMET filtering across a candidate set."""

    n_input: int = 0
    n_passed: int = 0
    n_failed: int = 0
    n_skipped: int = 0         # Model unavailable or SMILES failed
    pass_rate: float = 0.0
    failure_counts: dict[str, int] = Field(default_factory=dict)
    results: list[ADMETFilterResult] = Field(default_factory=list)


def filter_candidates_admet(
    candidates: list[StateConditionedCandidate],
    thresholds: dict[str, tuple[str, float]] | None = None,
    remove_failures: bool = False,
) -> tuple[list[StateConditionedCandidate], ADMETFilterSummary]:
    """Apply ADMET safety filtering to a candidate list.

    Args:
        candidates: Input candidates to filter.
        thresholds: Per-task thresholds (see check_admet_pass).
        remove_failures: If True, remove failing candidates from output.
            If False (default), include all candidates but flag failures.

    Returns:
        (filtered_candidates, summary): Filtered list and filtering summary.
        If model is unavailable, returns all candidates with n_skipped = n_input.
    """
    ...
```

### Step 5: Wire into Evaluation Reports

Add ADMET summary statistics to the comparative evaluation output.

**File to modify:** `scripts/report_comparative_results.py`

Add an optional ADMET section that, when the trained model is available:
1. Runs ADMET predictions on all candidates (static baseline + state-aware)
2. Reports per-pipeline ADMET pass rates
3. Reports per-task failure rates
4. Highlights any top-ranked candidates with ADMET flags

This should be additive — the existing report continues to work when the ADMET model is not available.

## Interface Contracts

### Primary Interface

```python
def predict_admet(smiles: str) -> dict[str, float]:
    """Predict ADMET properties.

    Returns:
        Dict mapping task name to value. Empty dict on failure.
        Classification: probability in [0.0, 1.0]
        Regression: raw predicted value (task-specific units)
    """

def check_admet_pass(
    predictions: dict[str, float],
    thresholds: dict[str, tuple[str, float]] | None = None,
) -> tuple[bool, list[str]]:
    """Check if predictions pass thresholds.

    Returns:
        (passed, failed_task_names): True if all thresholds met.
    """
```

### Default ADMET Thresholds

```python
DEFAULT_ADMET_THRESHOLDS: dict[str, tuple[str, float]] = {
    "herg": (">", 0.5),           # P(blocker) > 0.5 -> fail
    "cyp3a4": (">", 0.7),         # P(inhibitor) > 0.7 -> fail
    "caco2": ("<", -6.0),         # log cm/s < -6.0 -> fail (poor permeability)
    "clearance": (">", 50.0),     # mL/min/kg > 50 -> fail (rapid clearance)
    "lipophilicity": (">", 5.0),  # LogD > 5.0 -> fail (too lipophilic)
    "solubility": ("<", -5.0),    # LogS < -5.0 -> fail (insoluble)
}
```

### Filtering Pipeline Compatibility

The ADMET filter MUST:
- Accept `list[StateConditionedCandidate]` as input
- Return `list[StateConditionedCandidate]` as output (same type, possibly fewer items)
- Be optional — the pipeline runs correctly when the ADMET model is not available
- Never raise exceptions — log warnings and pass through all candidates on failure

## Files NOT to Touch

- `src/statebind/ml/admet.py` — model architecture is finalized
- `src/statebind/ml/admet_dataset.py` — dataset loading is finalized
- `src/statebind/ml/graphs.py` — graph construction is finalized
- `scripts/train_admet.py` — training loop is finalized
- `src/statebind/ranking/scoring.py` — separate workstreams handle scoring changes
- `src/statebind/baselines/*` — separate workstreams
- Any existing test files

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| ADMET model | `ml/admet.py:MultiTaskADMET` | Load checkpoint, call `.predict(data)` for single molecule |
| ADMET loss | `ml/admet.py:admet_loss` | Used by training script (already wired) |
| Task definitions | `ml/admet.py:_DEFAULT_TASK_NAMES`, `_DEFAULT_TASK_TYPES` | Import for consistency |
| Graph construction | `ml/graphs.py:smiles_to_graph` | Convert SMILES -> PyG Data |
| Dataset loading | `ml/admet_dataset.py:load_admet_dataset` | Load and split training data |
| Model save/load | `ml/utils.py:save_model` | Checkpoint serialization |
| Candidate model | `generation/models.py:StateConditionedCandidate` | Input type for ADMET filter |

## Testing Requirements

### `tests/test_admet_integration.py` — ~25 tests

**1. Data preparation tests:**
- `test_data_has_smiles()` — all records have `smiles` key
- `test_at_least_one_task_per_molecule()` — no records with all-null labels
- `test_task_coverage()` — each task has >= 100 labeled molecules
- `test_herg_labels_binary()` — hERG labels are 0.0 or 1.0
- `test_cyp3a4_labels_binary()` — CYP3A4 labels are 0.0 or 1.0
- `test_regression_values_finite()` — no inf values in regression tasks

**2. Model quality tests** (after training — compare vs TDC leaderboard):
- `test_herg_auroc()` — AUROC > 0.75 (TDC leaderboard baseline ~0.80)
- `test_cyp3a4_auroc()` — AUROC > 0.70 (TDC leaderboard baseline ~0.75)
- `test_caco2_rmse()` — RMSE < 0.6 (TDC leaderboard baseline ~0.5)
- `test_lipophilicity_rmse()` — RMSE < 0.8 (TDC leaderboard baseline ~0.6)
- `test_solubility_rmse()` — RMSE < 1.2 (TDC leaderboard baseline ~0.9)
- `test_clearance_rmse()` — RMSE < 40.0 (rough baseline)

**3. Adapter tests:**
- `test_predict_admet_returns_dict()` — output is dict[str, float]
- `test_predict_admet_has_all_tasks()` — output dict has all 6 task keys
- `test_predict_admet_classification_range()` — hERG, CYP3A4 values in [0, 1]
- `test_predict_admet_invalid_smiles()` — returns empty dict for garbage input
- `test_check_admet_pass_safe_molecule()` — aspirin passes all thresholds
- `test_check_admet_pass_returns_failures()` — failure list names specific tasks

**4. Filter tests:**
- `test_filter_preserves_passing_candidates()` — good candidates not removed
- `test_filter_flags_herg_liability()` — known hERG blocker gets flagged
- `test_filter_summary_counts()` — n_passed + n_failed + n_skipped == n_input
- `test_filter_graceful_without_model()` — all candidates pass through when model unavailable
- `test_filter_remove_mode()` — `remove_failures=True` actually removes candidates
- `test_filter_result_pydantic()` — `ADMETFilterResult` and `ADMETFilterSummary` serialize to JSON

**5. Edge cases:**
- `test_predict_admet_empty_smiles()` — returns empty dict
- `test_batch_prediction_matches_individual()` — batch and individual results are consistent
- `test_filter_empty_candidate_list()` — returns empty list with zero counts

## Definition of Done

- [ ] `scripts/prepare_admet_data.py` creates valid multi-task JSON from TDC datasets
- [ ] `data/processed/admet_combined.json` contains 10,000+ molecules with partial labels
- [ ] Training completes with per-task metrics within range of TDC leaderboard baselines
- [ ] hERG AUROC > 0.75 and CYP3A4 AUROC > 0.70 on test set
- [ ] `src/statebind/ml/admet_predictor.py` provides `predict_admet(smiles) -> dict[str, float]`
- [ ] `src/statebind/generation/admet_filter.py` provides ADMET gate for filtering pipeline
- [ ] ADMET filter is optional — pipeline runs correctly when model is unavailable
- [ ] `tests/test_admet_integration.py` with 25+ tests, all passing
- [ ] No existing tests broken (`pytest -v --tb=short` passes all 359+ tests)
- [ ] Model card saved with per-task test metrics
- [ ] Evaluation reports include ADMET summary when model is available
- [ ] All new functions have type annotations and docstrings

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation — edge cases, gotchas, implicit assumptions, or things that broke unexpectedly — add them to the relevant CRITICAL.md file(s):

- **Module-level**: `src/statebind/{module}/CRITICAL.md` for facts specific to the module you modified
- **Project-level**: `/CRITICAL.md` for facts that cross module boundaries

Format: one fact per line, include `file:line` references. Be detailed yet concise.

## Agent Instructions

Be detailed yet concise in all code, comments, and documentation. Include `file:line` references when noting important locations. No fluff — every line should carry information.
