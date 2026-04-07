# WS07: Conditional VAE -- Progress Report

## Status

- **State:** Complete (code, data prep, model trained, generation verified)
- **Last updated:** 2026-04-06T00:00:00+00:00
- **Session count:** 1
- **Test count added:** 15+
- **Files created:** 2+
- **Files modified:** 1+

## Objective

Create the VAE data preparation pipeline (ChEMBL EGFR actives) and the generation
integration module that converts VAE output into `StateConditionedCandidate` objects
compatible with the existing generation pipeline. The VAE architecture already exists
in `ml/vae.py`; this workstream creates the surrounding integration code.

---

## Progress Log

### Session 1 -- 2026-03-22 (retrospective)

> This workstream was completed before the documentation system was established.
> This report was reconstructed from git history and code review.

#### Completed
- Created `scripts/prepare_vae_data.py` -- ChEMBL EGFR data download and processing
- Created VAE integration code for `StateConditionedCandidate` generation
- Created 15+ tests for data prep and integration
- All tests pass (8 skipped for torch-dependent edge cases)

#### Decisions Made
- VAE candidates use `source=ML_GENERATED`, `strategy=VAE_GENERATED`
- Follows INTERFACES.md Contract 5

---

## Current State

**What is done:** All code, integration, and model training complete.

### VAE Training History

| Version | Params | Representation | kl_weight | Val Recon | Valid Rate | Notes |
|---------|--------|---------------|-----------|-----------|------------|-------|
| v1 | 2.6M | SMILES | 0.01 | 2.31 | 0% | Teacher forcing from epoch 0 |
| v2 | 9.5M | SMILES | 0.001 | 1.92 | 0% | Prior-posterior mismatch |
| **v3** | **9.5M** | **SELFIES** | **0.01** | **2.26** | **99.9%** | **300 epochs, H200, 31 min** |

### VAE v3 Generation Results (1000 candidates, temp=0.8)
- **Validity:** 999/1000 (99.9%) — SELFIES guarantees validity by construction
- **Uniqueness:** 948/999 (94.8%)
- **Mean MW:** 341, 79.5% in drug-like range (150-800), 31.5% QED>0.3
- **Checkpoint:** `artifacts/models/vae/best_model.pt`

### Full Comparison (with VAE candidates)
- State-aware: 461 candidates (395 VAE + 36 template + 30 shared), mean=0.4378, max=0.7794, diversity=0.9056
- Static: 30 candidates, mean=0.5437, max=0.7288, diversity=0.5684
- Mann-Whitney U: p<0.001, Cohen's d=1.36 (large, static favored)
- **Null hypothesis formally retained.** 431 novel candidates unique to state-aware pipeline.

---

## Handoff Notes

Workstream is fully complete including model training and generation verification. VAE v3 (SELFIES) produces 99.9% valid molecules. The integration code auto-detects SELFIES mode from checkpoint config.
