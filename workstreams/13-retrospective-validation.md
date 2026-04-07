# Workstream 13: Retrospective Time-Split Validation

## Goal

Validate the pipeline retrospectively using a time-split strategy: train models on EGFR data available before a cutoff date (2010 and 2015), then test whether the pipeline identifies molecules resembling drugs that were later approved or advanced to clinical trials. This is the most impactful validation available to a purely computational project -- it demonstrates real predictive power without wet lab work.

## Why This Matters

- The null hypothesis was retained. The pipeline needs external validation to demonstrate scientific value beyond self-benchmarking.
- Peer reviewers will ask "Where is the experimental validation?" Time-split retrospective validation is the gold-standard computational alternative.
- If the state-aware pipeline retrospectively identifies osimertinib-like molecules (approved 2015) from pre-2015 data, that is a publishable finding regardless of the mean score comparison.
- A negative result is equally valuable: it identifies where the pipeline fails and motivates specific improvements.

## Prerequisites

- **ChEMBL database** access (API or local download) with deposition/publication dates.
- **Trained MPNN** that can be retrained on restricted (pre-cutoff) datasets.
- **Full pipeline** running end-to-end (all phases).
- **Drug approval date database** (DrugBank or FDA Orange Book for validation targets).
- **RDKit** for structural similarity to future drugs.

## Origin

Vision Idea 009 (Retrospective Time-Split Validation). Accepted 2026-04-07.

## Files to Create

| File | Purpose |
|------|---------|
| `scripts/build_timesplit_datasets.py` | Pull all EGFR bioactivity data from ChEMBL with dates. Split by first_publication date at each cutoff (2010, 2015). Identify "future drugs" held out from training. |
| `scripts/run_retrospective_validation.py` | Execute the full pipeline under time restriction: retrain MPNN on pre-cutoff data, remove post-cutoff references, generate and score candidates, evaluate against held-out future compounds. |
| `src/statebind/evaluation/retrospective.py` | Retrospective validation metrics: enrichment factor, structural similarity to future drugs, state prediction accuracy, novelty relative to pre-cutoff chemical space. |
| `configs/retrospective.yaml` | Cutoff dates, future drug SMILES, enrichment K values, similarity thresholds. |
| `tests/test_retrospective.py` | 15+ tests for time-split integrity, enrichment computation, no-leakage verification. |

## Files to Modify

| File | Change |
|------|--------|
| `src/statebind/evaluation/comparison.py` | Add optional retrospective validation section to `ComparativeResult` when retrospective results are available. |
| `src/statebind/evaluation/figures.py` | Add retrospective performance-vs-cutoff plot, enrichment bar charts, similarity distributions. |

## Time-Split Design

### Cutoff Dates

| Cutoff | Training Data Available | Held-Out Validation Targets |
|--------|------------------------|---------------------------|
| 2010 | Erlotinib (2004), gefitinib (2003), early EGFR actives | Afatinib (2013), osimertinib (2015), dacomitinib (2018), lazertinib (2021) |
| 2015 | All above + afatinib, osimertinib in ChEMBL | Lazertinib (2021), mobocertinib (2021), furmonertinib (2021) |

### What Gets Time-Restricted

1. **MPNN training data** -- only compounds published before cutoff
2. **Reference binder list** -- remove post-cutoff approved drugs from similarity scoring
3. **VAE training data** -- only SMILES from pre-cutoff compounds
4. **Structure atlas** -- optionally restrict PDB structures to those deposited pre-cutoff (configurable: strict vs. relaxed mode)
5. **Context module** -- mutation annotations available pre-cutoff only

### What Does NOT Change

- Pipeline code (same scoring function, same generation strategies)
- Statistical tests (same Mann-Whitney U, same effect size measures)
- Scoring weights (same 0.35/0.30/0.20/0.15)

## Interface Contracts

### Primary Interface

```python
from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class TimeSplitDataset:
    """Training and validation data for one time-split cutoff."""
    cutoff_year: int
    train_smiles: list[str]
    train_pIC50: list[float]
    n_train: int
    held_out_drugs: list[dict]  # [{"name": "osimertinib", "smiles": "...", "approved": 2015}]
    n_held_out: int

@dataclass
class RetrospectiveResult:
    """Validation result for one cutoff + one pipeline."""
    cutoff_year: int
    pipeline: str                   # "static" or "state_aware"
    enrichment_factor_10: float     # EF at top 10
    enrichment_factor_50: float     # EF at top 50
    max_similarity_to_future: float # Best Tanimoto to any held-out drug
    mean_similarity_to_future: float
    n_candidates: int
    n_future_drugs: int
    future_drug_ranks: dict[str, int | None]  # drug_name -> rank in candidate list (None if not found)
    novelty_vs_training: float      # fraction of candidates not in pre-cutoff chemical space

@dataclass
class RetrospectiveComparison:
    """Comparison across cutoffs and pipelines."""
    results: list[RetrospectiveResult]
    cutoffs: list[int]
    summary: str                    # Natural-language summary of findings

def compute_enrichment_factor(
    candidate_similarities: list[float],
    threshold: float = 0.4,
    top_k: int = 10,
) -> float:
    """Enrichment factor: are high-similarity candidates enriched in top-K?

    EF = (hits_in_top_k / top_k) / (total_hits / total_candidates)
    """

def compute_retrospective_metrics(
    candidates: list[dict],
    future_drugs: list[dict],
    training_smiles: set[str],
) -> RetrospectiveResult:
    """Compute all retrospective validation metrics for one pipeline run."""
```

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| ChEMBL data loading | `scripts/prepare_mpnn_data.py` | Pagination patterns, ChEMBL API calls |
| MPNN training | `scripts/train_mpnn.py` | Retrain with restricted dataset |
| Morgan similarity | `chemistry/fingerprints.py` | Tanimoto similarity to future drugs |
| Full comparison | `scripts/compare_baseline_vs_state_aware.py` | Pipeline execution pattern |
| Statistical tests | `evaluation/statistics.py` | Mann-Whitney U on retrospective results |
| VAE data prep | `scripts/prepare_vae_data.py` | Time-restricted SMILES extraction |

## Files NOT to Touch

- `src/statebind/ranking/scoring.py` -- scoring function unchanged
- `src/statebind/ml/mpnn.py` -- model architecture unchanged (only retrain with different data)
- `src/statebind/ml/vae.py` -- model architecture unchanged
- `src/statebind/structure/` -- structure module unchanged
- Any existing test files

## Testing Requirements

### `tests/test_retrospective.py` -- ~15 tests

**1. Time-split integrity:**
- `test_no_future_leakage_2010()` -- no compounds published after 2010 in training set
- `test_no_future_leakage_2015()` -- no compounds published after 2015 in training set
- `test_future_drugs_excluded()` -- osimertinib not in pre-2010 training data
- `test_reference_binders_restricted()` -- post-cutoff drugs removed from reference set

**2. Enrichment computation:**
- `test_enrichment_perfect()` -- all hits in top-K gives max EF
- `test_enrichment_random()` -- random ordering gives EF ~1.0
- `test_enrichment_zero_hits()` -- no hits gives EF 0.0
- `test_enrichment_k_larger_than_n()` -- handles edge case

**3. Similarity metrics:**
- `test_max_similarity_known_drug()` -- erlotinib analog scores high against erlotinib
- `test_novelty_computation()` -- novel fraction in [0, 1]
- `test_future_drug_ranking()` -- future drug rank is correct position in sorted list

**4. Integration tests:**
- `test_retrospective_result_serialization()` -- serializes to JSON
- `test_retrospective_comparison_summary()` -- produces non-empty summary string
- `test_timesplit_dataset_valid()` -- dataset has expected fields and non-zero sizes

## Definition of Done

- [ ] `scripts/build_timesplit_datasets.py` creates clean time-split datasets for 2010 and 2015 cutoffs
- [ ] No data leakage: post-cutoff compounds never appear in training data
- [ ] `scripts/run_retrospective_validation.py` executes full pipeline under time restriction
- [ ] MPNN retrained on pre-cutoff data (2 separate training runs: 2010 and 2015)
- [ ] Reference binder list restricted to pre-cutoff approved drugs
- [ ] `evaluation/retrospective.py` computes enrichment, similarity, and novelty metrics
- [ ] Results reported for both static and state-aware pipelines at both cutoffs
- [ ] 15+ tests, all passing
- [ ] No existing tests broken
- [ ] All new functions have type annotations and docstrings
- [ ] Results interpretable regardless of direction (positive or negative finding)

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation, add them to the relevant CRITICAL.md file(s).

## Agent Instructions

Scientific honesty is paramount. Do NOT design the validation to favor a particular outcome. Report results as found. A well-characterized negative result is more valuable than a cherry-picked positive one.
