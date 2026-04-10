---
phase: "Phase 1: Core Experiments"
task_id: P1-T02
task_name: "VAE Quality Metrics (FCD/Recon/Novelty)"
implementation_plan_ref: "P8: VAE Metrics Replacement"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "2-3 days"
---

# Task: VAE Quality Metrics (FCD/Recon/Novelty)

## Objective

Replace the vacuous "99.9% validity" metric (guaranteed by SELFIES encoding) with
meaningful VAE quality metrics: Frechet ChemNet Distance (FCD), reconstruction
accuracy, novelty, and internal diversity. These metrics assess whether the VAE
actually learns a useful latent space.

## Context

SELFIES encoding guarantees syntactic validity, making the current 99.9% validity
metric uninformative. Reviewers at JCIM will flag this. FCD measures distributional
quality (how similar generated molecules are to the training distribution), while
reconstruction accuracy tests whether the autoencoder preserves molecular identity
through the bottleneck. Novelty and diversity confirm the model generates new,
varied molecules rather than memorizing training data.

## Prerequisites

- [x] Phase 0 complete (VAE retrained with 3-state model)
- [x] Existing VAE checkpoints available at `artifacts/models/vae/`

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/ml/vae.py:371-532` | encode(), sample(), generate() -- needed for reconstruction |
| `src/statebind/ml/vae_dataset.py:97-195` | SMILESDataset -- understand data format for FCD input |
| `src/statebind/evaluation/statistics.py` | Existing evaluation patterns to follow |
| `src/statebind/chemistry/fingerprints.py` | Tanimoto similarity (for internal diversity) |
| `pyproject.toml:54-58` | [ml] extras group -- where to add fcd_torch |
| `tests/test_evaluation.py` | Existing evaluation test patterns |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `src/statebind/evaluation/vae_metrics.py` | -- | All 4 metric functions + VaeMetricsResult model |
| `pyproject.toml` | 54-58 | Add `fcd_torch` to [ml] extras |
| NEW: `tests/test_vae_metrics.py` | -- | Tests for all metric functions |

## Implementation Steps

1. **Add `fcd_torch` to `pyproject.toml`**:

   In the `[ml]` extras group (line 54-58), add `fcd_torch`:
   ```toml
   ml = [
       "torch>=2.0",
       "torch-geometric>=2.4",
       "rdkit",
       "fcd_torch",
   ]
   ```

2. **Create `src/statebind/evaluation/vae_metrics.py`**:

   ```python
   from __future__ import annotations
   # Standard imports, logging, typing

   from pydantic import BaseModel, Field

   class VaeMetricsResult(BaseModel):
       """Results from VAE quality metric evaluation."""
       fcd_score: float | None = Field(default=None, description="Frechet ChemNet Distance")
       reconstruction_accuracy: float | None = Field(default=None, description="Exact SMILES match rate")
       novelty: float = Field(description="Fraction of valid generated not in training set")
       internal_diversity: float = Field(description="1 - mean pairwise Tanimoto similarity")
       n_generated: int = Field(description="Total generated molecules evaluated")
       n_valid: int = Field(description="Valid molecules (RDKit parseable)")
       n_novel: int = Field(description="Valid molecules not in training set")
   ```

   Functions to implement:

   a. **`compute_fcd(generated_smiles, reference_smiles) -> float`**:
      - Import fcd_torch as optional dependency (try/except)
      - Use `fcd_torch.FCD()` to compute FCD between two SMILES lists
      - FCD < 1.0 is generally good; lower is better
      - If fcd_torch unavailable, return None and log warning

   b. **`compute_reconstruction_accuracy(model, dataset, vocab, device) -> float`**:
      - For each molecule in dataset: encode -> sample z -> decode -> compare SMILES
      - Use greedy decoding (temperature=0) for deterministic reconstruction
      - Return fraction of exact SMILES matches
      - This requires torch -- guard with HAS_TORCH check

   c. **`compute_novelty(generated_smiles, training_smiles) -> float`**:
      - Canonicalize all SMILES (RDKit if available, else string comparison)
      - Return fraction of valid generated not in training set
      - Pure Python, no ML deps required

   d. **`compute_internal_diversity(smiles_list, n_sample=1000) -> float`**:
      - Compute Morgan fingerprints (radius=2) for up to n_sample molecules
      - Calculate pairwise Tanimoto similarities
      - Return 1 - mean(pairwise_tanimoto)
      - If n > n_sample, randomly sample to avoid O(n^2) explosion
      - RDKit required; return None if unavailable

   e. **`evaluate_vae_quality(generated_smiles, training_smiles, ...) -> VaeMetricsResult`**:
      - Orchestrator function that calls all 4 metrics
      - Accepts optional model/dataset for reconstruction accuracy
      - Returns VaeMetricsResult with all metrics populated

3. **Create `tests/test_vae_metrics.py`**:

   - Test `compute_novelty` with known overlap (e.g., 50% overlap -> 0.5 novelty)
   - Test `compute_internal_diversity` with identical molecules (diversity=0) and
     diverse molecules (diversity>0)
   - Test `compute_fcd` with mock or skip if fcd_torch unavailable
   - Test `compute_reconstruction_accuracy` with mock model or skip if torch unavailable
   - Test `VaeMetricsResult` Pydantic model serialization
   - Test edge cases: empty lists, single molecule, all duplicates

## Verification

- [ ] `pip install fcd_torch` succeeds in ML environment
- [ ] `from statebind.evaluation.vae_metrics import evaluate_vae_quality` works
- [ ] `compute_novelty(["CCO", "CCN"], ["CCO"])` returns 0.5
- [ ] `compute_internal_diversity(["CCO"]*10)` returns 0.0 (all identical)
- [ ] `pytest tests/test_vae_metrics.py -v` -- all tests pass
- [ ] `pytest -v --tb=short` -- 669+ tests pass, no regressions
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- Follow StateBind conventions: typed Python, optional deps with fallback paths
- `fcd_torch` and `torch` are optional deps -- provide clean fallback if unavailable
- `rdkit` is optional -- fingerprint-based diversity should have a fallback
- Place the module in `src/statebind/evaluation/` alongside existing evaluation code
- Use Pydantic BaseModel for the result class (cross-module data)
- Round scores to 4 decimal places (StateBind convention)
- Do NOT add fcd_torch to core `[project.dependencies]` -- it goes in `[ml]` extras only

## Notes and Gotchas

- **FCD computation requires SMILES lists of reasonable size** (>100 molecules).
  With fewer molecules, FCD estimates are unreliable. Log a warning if n < 100.
- **Reconstruction accuracy uses greedy decoding** (temperature=0), not stochastic.
  This makes the metric deterministic and comparable across runs.
- **Internal diversity with O(n^2) pairwise comparison** can be slow for large
  datasets. Cap at n_sample=1000 with random subsampling.
- **Canonicalization matters** for novelty -- "CCO" and "OCC" are the same molecule.
  Use RDKit canonicalization when available.
- **fcd_torch downloads a pretrained ChemNet model** on first use (~300MB).
  This happens automatically but may take time on first run.
