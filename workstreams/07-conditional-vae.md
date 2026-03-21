# Workstream 07: Conditional SMILES VAE

## Goal

Train a state-conditioned Variational Autoencoder to generate novel EGFR-targeted molecules. The VAE learns to encode and decode SMILES strings conditioned on EGFR conformational states (DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout), then generates novel candidates for each state from sampled latent codes. Generated candidates are piped into the existing generation pipeline as `StateConditionedCandidate` objects, giving the state-aware pipeline access to ML-generated molecular diversity beyond rule-based enumeration.

## Why This Matters

- The current generation pipeline (`src/statebind/generation/`) relies on template-based SMILES enumeration — ring swaps, chain extensions, and fragment substitutions. This produces incremental analogs, not structurally novel scaffolds.
- A conditional VAE can learn the manifold of EGFR-active chemistry from ChEMBL data and sample molecules that are chemically plausible but structurally distinct from known binders.
- State conditioning ensures generated molecules are biased toward the chemical features preferred by each EGFR conformation (e.g., Type-II inhibitors for DFGout states).

## Prerequisites

- **ML infrastructure** in `src/statebind/ml/` is already built. The model (`vae.py`), dataset (`vae_dataset.py`), training script (`scripts/train_vae.py`), and config (`configs/vae.yaml`) exist and are structurally complete.
- **Workstream 01 (Chemistry Foundation)** is helpful for SMILES validation and Morgan fingerprint novelty analysis, but is NOT required. The VAE pipeline has its own tokenizer and can operate without RDKit.
- **PyTorch** must be installed (`pip install torch`).

## Files Already Created

These files are fully implemented and tested. Read them before starting remaining work.

| File | Purpose |
|------|---------|
| `src/statebind/ml/vae.py` | `ConditionalSMILESVAE` model: GRU encoder (bidirectional) + GRU decoder with state conditioning. Includes `VAEConfig`, `SMILESEncoder`, `SMILESDecoder`, `vae_loss`. |
| `src/statebind/ml/vae_dataset.py` | `SMILESDataset` + `collate_smiles` + `load_smiles_dataset`. Loads JSON records with `smiles` and `state` keys. |
| `src/statebind/ml/tokenizer.py` | `SMILESTokenizer` — character-level tokenizer for SMILES strings. |
| `src/statebind/ml/vocabulary.py` | `Vocabulary` — token-to-index mapping with SOS/EOS/PAD tokens. |
| `scripts/train_vae.py` | Full training pipeline: config loading, data loading, vocabulary building, training loop with KL annealing, early stopping, checkpointing, model card. |
| `configs/vae.yaml` | Default hyperparameters and data paths. |

## Remaining Work

### Step 1: Data Preparation

Create the training data files expected by `configs/vae.yaml`:

- `data/processed/egfr_smiles_train.json`
- `data/processed/egfr_smiles_val.json`

**Data source:** ChEMBL EGFR bioactivity (target CHEMBL203). Query for compounds with IC50 < 10 uM.

**Required JSON format** (one record per compound):
```json
[
    {"smiles": "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC", "state": "DFGin_aCin"},
    {"smiles": "CC(=O)Nc1ccc...", "state": "DFGout_aCout"},
    ...
]
```

**State assignment strategy:** Assign each compound to the conformational state of the PDB structure it was co-crystallized with. For compounds without co-crystal structures, assign state labels based on inhibitor type heuristics:
- Type-I inhibitors (bind active conformation): `DFGin_aCin`
- Type-I.5 inhibitors (bind inactive aC-helix): `DFGin_aCout`
- Type-II inhibitors (bind DFG-out): `DFGout_aCin`
- Type-III/allosteric: `DFGout_aCout`

If inhibitor type is unknown, assign uniformly at random across states (document this as a limitation).

**Script to create:** `scripts/prepare_vae_data.py`

This script should:
1. Load raw ChEMBL EGFR data from `data/raw/` (or download via ChEMBL API if not present)
2. Filter for IC50 < 10 uM, valid SMILES
3. Assign state labels
4. Split into train (80%) and validation (20%) sets
5. Write JSON files to `data/processed/`
6. Print summary statistics (N per state, SMILES length distribution)

### Step 2: Training on HPC Cluster

Run the existing training script:
```bash
python scripts/train_vae.py --config configs/vae.yaml
```

**Expected outputs:**
- `artifacts/models/vae/best_model.pt` — best checkpoint
- `artifacts/models/vae/vocabulary.json` — trained vocabulary
- `artifacts/models/vae/model_card.json` — metadata
- `artifacts/logs/vae/training_log.csv` — per-epoch metrics

**Tuning notes:**
- If reconstruction loss plateaus above 2.0, increase `hidden_dim` to 512 or `n_layers` to 3
- If KL collapses to near zero, reduce `kl_weight` to 0.001 or increase `warmup_epochs` to 40
- Monitor `val_recon_loss` — it should decrease monotonically during early training

### Step 3: Generation Script

Create `scripts/generate_vae_candidates.py` that:

1. Loads the trained checkpoint and vocabulary from `artifacts/models/vae/`
2. For each of the 4 conformational states:
   a. Creates a state one-hot vector
   b. Samples `n_samples_per_state` latent codes from N(0, I)
   c. Decodes to SMILES via `ConditionalSMILESVAE.generate()`
   d. Filters for valid SMILES (syntactic check at minimum; RDKit validation if available)
   e. Deduplicates within and across states
3. Writes output to `artifacts/generation/vae_candidates.json`

**Output JSON format:**
```json
{
    "model_checkpoint": "artifacts/models/vae/best_model.pt",
    "temperature": 0.8,
    "n_samples_per_state": 100,
    "generated_at": "2026-03-21T...",
    "candidates": [
        {
            "smiles": "...",
            "state": "DFGin_aCin",
            "source": "vae_latent_sample",
            "is_valid": true,
            "is_novel": true
        },
        ...
    ],
    "summary": {
        "total_generated": 400,
        "total_valid": 312,
        "total_novel": 290,
        "per_state": {
            "DFGin_aCin": {"generated": 100, "valid": 82, "novel": 74},
            ...
        }
    }
}
```

**Config support:** The generation section of `configs/vae.yaml` already specifies `n_samples_per_state`, `temperature`, `max_len`, and `output_path`. Use those values.

### Step 4: Integration with Generation Pipeline

Create a loader function that converts VAE output into `StateConditionedCandidate` objects compatible with the existing ranking pipeline.

**File to create:** `src/statebind/generation/vae_integration.py`

```python
"""Convert VAE-generated candidates to StateConditionedCandidate objects."""

from __future__ import annotations

import json
from pathlib import Path

from statebind.baselines.models import CandidateSource
from statebind.generation.models import (
    GenerationStrategy,
    StateConditionedCandidate,
    StateConditionedLibrary,
)


def load_vae_candidates(
    path: Path | str,
) -> list[StateConditionedCandidate]:
    """Load VAE candidates from JSON and wrap as StateConditionedCandidate.

    Each candidate gets:
        source = CandidateSource.ML_GENERATED
        strategy = GenerationStrategy.VAE_GENERATED
        candidate_id = "vae_{state}_{index:04d}"
    """
    ...


def build_vae_libraries(
    candidates: list[StateConditionedCandidate],
) -> list[StateConditionedLibrary]:
    """Group VAE candidates by target_state into StateConditionedLibrary objects."""
    ...
```

**Integration point:** The `scripts/generate_state_conditioned_candidates.py` or `scripts/filter_generated_candidates.py` should be able to optionally load VAE candidates and merge them into the candidate pool before ranking. This can be done by adding a `--vae-candidates` CLI flag, or by checking for the existence of `artifacts/generation/vae_candidates.json`.

## Interface Contracts

### VAE Candidate Output Contract

Every VAE candidate entering the ranking pipeline MUST be a valid `StateConditionedCandidate`:

```python
StateConditionedCandidate(
    candidate_id="vae_DFGin_aCin_0001",
    smiles="<valid SMILES>",
    source=CandidateSource.ML_GENERATED,
    parent_id="",            # No parent for de novo generation
    target_state="DFGin_aCin",
    target_pdb_id="",        # Can be empty — state is the primary label
    strategy=GenerationStrategy.VAE_GENERATED,
    pocket_volume=0.0,       # Not applicable for VAE candidates
    back_pocket=False,
    gatekeeper_clearance=0.0,
    notes="VAE latent sample, temperature=0.8",
)
```

### Scoring Compatibility

VAE candidates are scored by the same `ranking/scoring.py:score_unified()` function as all other candidates. No special treatment is needed. The `state_specificity` component will credit VAE candidates that are unique to a single state.

## Files NOT to Touch

- `src/statebind/ml/vae.py` — model architecture is finalized
- `src/statebind/ml/vae_dataset.py` — dataset loading is finalized
- `src/statebind/ml/tokenizer.py` — tokenizer is finalized
- `src/statebind/ml/vocabulary.py` — vocabulary is finalized
- `scripts/train_vae.py` — training loop is finalized
- `src/statebind/ranking/scoring.py` — scoring function is shared; do not modify
- `src/statebind/baselines/*` — separate workstreams handle these
- Any existing test files

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| VAE model | `ml/vae.py:ConditionalSMILESVAE` | Load checkpoint, call `.generate()` |
| Vocabulary | `ml/vocabulary.py:Vocabulary` | Load from `vocabulary.json`, use `.decode()` |
| State mapping | `ml/vae_dataset.py:DEFAULT_STATE_MAPPING` | Import for consistent state indices |
| Candidate model | `generation/models.py:StateConditionedCandidate` | Wrap VAE output |
| CandidateSource enum | `baselines/models.py:CandidateSource.ML_GENERATED` | Set source field |
| GenerationStrategy enum | `generation/models.py:GenerationStrategy.VAE_GENERATED` | Set strategy field |

## Testing Requirements

### `tests/test_vae_integration.py` — ~15-20 tests

**1. Data preparation tests:**
- `test_data_format_train()` — train JSON has correct keys (`smiles`, `state`)
- `test_data_format_val()` — val JSON has correct keys
- `test_state_labels_valid()` — all state labels are in DEFAULT_STATE_MAPPING
- `test_no_empty_smiles()` — no empty or whitespace-only SMILES
- `test_train_val_no_overlap()` — no SMILES in both train and val

**2. Generation quality tests** (after training):
- `test_validity_rate()` — >= 50% of generated SMILES parse as valid molecules
- `test_novelty_rate()` — >= 30% of valid SMILES are not in the training set
- `test_uniqueness_rate()` — >= 70% of valid SMILES are unique (no duplicates)
- `test_reconstruction_accuracy()` — encode-decode round-trip recovers >= 70% of input tokens

**3. Integration tests:**
- `test_vae_candidates_are_state_conditioned()` — every candidate has a valid `target_state`
- `test_vae_candidates_have_correct_source()` — `source == CandidateSource.ML_GENERATED`
- `test_vae_candidates_have_correct_strategy()` — `strategy == GenerationStrategy.VAE_GENERATED`
- `test_vae_candidates_scorable()` — `score_unified()` runs without error on VAE candidates
- `test_vae_candidate_ids_unique()` — no duplicate `candidate_id` values
- `test_load_vae_candidates_from_json()` — round-trip: generate, save, load, verify fields

**4. Edge case tests:**
- `test_generate_with_temperature_zero()` — greedy decoding produces deterministic output
- `test_generate_empty_latent()` — zero vector latent produces valid (if boring) output
- `test_unknown_state_rejected()` — invalid state label raises error in dataset

## Definition of Done

- [ ] `scripts/prepare_vae_data.py` creates valid train/val JSON from ChEMBL data
- [ ] Training completes with val_recon_loss < 2.0 (reasonable reconstruction)
- [ ] `scripts/generate_vae_candidates.py` produces `artifacts/generation/vae_candidates.json`
- [ ] Validity rate >= 50% of generated SMILES
- [ ] `src/statebind/generation/vae_integration.py` converts VAE output to `StateConditionedCandidate`
- [ ] VAE candidates pass through `ranking/scoring.py:score_unified()` without error
- [ ] `tests/test_vae_integration.py` with 15+ tests, all passing
- [ ] No existing tests broken (`pytest -v --tb=short` passes all 359+ tests)
- [ ] Model card saved with training metadata and quality metrics
- [ ] All new functions have type annotations and docstrings

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation — edge cases, gotchas, implicit assumptions, or things that broke unexpectedly — add them to the relevant CRITICAL.md file(s):

- **Module-level**: `src/statebind/{module}/CRITICAL.md` for facts specific to the module you modified
- **Project-level**: `/CRITICAL.md` for facts that cross module boundaries

Format: one fact per line, include `file:line` references. Be detailed yet concise.

## Agent Instructions

Be detailed yet concise in all code, comments, and documentation. Include `file:line` references when noting important locations. No fluff — every line should carry information.
