# StateBind Pre-Registration: Ablation C

## Date

2026-04-09T23:30:00+00:00

## Authors

Rohan Aryagondi

## Overview

This document pre-registers the hypothesis, experimental design, success
thresholds, and analysis plan for Ablation C of the StateBind project. It is
committed to version control before any ablation experiments begin. The commit
hash serves as a cryptographic timestamp proving the thresholds and analysis
plan were fixed a priori, preventing post-hoc adjustment.

## Hypothesis

State-conditioned VAE (using discrete conformational state labels as an
auxiliary input) produces higher retrospective enrichment than an
unconditioned VAE with identical architecture and training procedure.

Formally:

> EF@10(conditioned) > EF@10(unconditioned) with Cohen's d >= 0.5.

The null hypothesis is that state conditioning provides no meaningful benefit
to molecular generation quality as measured by retrospective enrichment.

## State Model

The project uses a **3-state** conformational model for EGFR:

| State | Description | Representative PDB |
|-------|-------------|--------------------|
| DFGin_aCin | Active kinase conformation | 1M17, 4ZAU |
| DFGin_aCout | Inactive, aC-helix rotated out | 5D41 |
| DFGout_aCin | Inactive, DFG motif flipped | 3W2R |

**Structural verification (P0-T01):**
- 4ZAU: DFG Asp855-Phe856 CA-CA = 3.80 A (DFGin). Lys745-Glu762 salt bridge = 3.51 A (aCin). Reclassified from DFGout_aCout to **DFGin_aCin**.
- 5D41: DFG Asp855-Phe856 CA-CA = 3.79 A (DFGin). Lys745-Glu762 distance = 11.37 A (aCout). Reclassified from DFGout_aCout to **DFGin_aCout**.
- No genuine EGFR DFGout structures exist in the PDB; the former DFGout_aCout category was removed.
- Verification artifact: `artifacts/verification/4zau_dfg_verification.json`

## MPNN Scoring Component Status

**Gate G1 outcome: GO** (P0-T05, 2026-04-09)

| Metric | Value |
|--------|-------|
| Scaffold split R-squared | 0.5153 |
| Random split R-squared | 0.7016 |
| Degradation | 0.1863 |
| Threshold | >= 0.35 |
| Scaffold overlap (train/test) | 0 |

The MPNN remains a credible scoring component under structurally challenging
evaluation. Artifact: `artifacts/evaluation/mpnn_scaffold_metrics.json`

## Prior Methodological Fixes

The following corrections were completed before this pre-registration:

1. **Osimertinib removed** from reference binders (P0-T02) -- eliminates temporal leakage in retrospective evaluation.
2. **BCa bootstrap + BEDROC** implemented (P0-T04) -- provides rigorous confidence intervals via 10,000-fold bias-corrected and accelerated bootstrap, plus BEDROC(alpha=20) for early enrichment assessment.
3. **Scaffold and temporal splits** implemented (P0-T03) -- enables fair generalization evaluation without scaffold leakage between train and test sets.
4. **3-state model switch** completed (P0-T07) -- DFGout_aCout removed from enum, configs, and all downstream code.
5. **Structural annotations fixed** (P0-T06) -- removed 3iku (ParM, not EGFR); corrected state assignments and mutation annotations.

## Experimental Design

### Conditioned VAE (Treatment)

- **Architecture:** SELFIES VAE with state-conditioning. A one-hot state vector (dimension 3) is concatenated with the latent code before decoding.
- **n_states:** 3 (DFGin_aCin=0, DFGin_aCout=1, DFGout_aCin=2)
- **Training data:** ChEMBL EGFR bioactivity compounds (IC50 < 10 uM) labeled by conformational state.
- **Hyperparameters:** As specified in `configs/vae.yaml`:
  - Latent dimension: 64
  - Hidden dimension: 512
  - Embedding dimension: 128
  - Number of layers: 2
  - Dropout: 0.2
  - KL weight: 0.01
  - KL annealing: linear warmup over 50 epochs
  - Teacher forcing: ratio decays from 1.0 to 0.0 over training, held at 1.0 for first 30 epochs
  - Epochs: 300 (early stopping on val_recon_loss, patience 40)
  - Batch size: 128
  - Learning rate: 0.001
  - Gradient clipping: 1.0

### Unconditioned VAE (Ablation C Control)

- **Architecture:** IDENTICAL to conditioned VAE in every respect.
- **n_states:** 1. All molecules assigned to state 0. The conditioning input is a constant one-hot vector [1.0].
- **Mathematical equivalence:** A constant input vector adds no information to the decoder. The model cannot use it to distinguish between states, making it functionally unconditioned while preserving the same architecture and parameter count. This eliminates confounds from architectural differences.
- **Same training data, same preprocessing, same hyperparameters** as the conditioned VAE.
- **Same training epochs, same early stopping criterion, same optimizer settings.**

### Generation Protocol

- Generate the **same total number** of candidates from each condition.
- For the conditioned VAE: sample equally across all 3 states.
- For the unconditioned VAE: sample from the single pseudo-state.
- Generation temperature: 0.8 (as in `configs/vae.yaml`).

### Scoring Protocol

- Score ALL candidates (both conditions) with the **same unified scoring function** (`ranking/scoring.py`).
- No modifications to scoring weights or components between conditions.
- Scoring components: MPNN pIC50 prediction, SA score, QED, Lipinski, similarity to reference binders, docking proxy.
- The same `DEFAULT_WEIGHTS` apply to both conditions.

### Evaluation Protocol

- **Metrics:**
  - EF@10 (enrichment factor at top 10 candidates) -- primary metric
  - BEDROC(alpha=20) -- standard virtual screening early enrichment metric
  - Mean composite score
- **Confidence intervals:** 10,000-fold BCa (bias-corrected and accelerated) bootstrap confidence intervals for all metrics. Falls back to percentile bootstrap if scipy is unavailable.
- **Replication:** Minimum 3 random seeds (seeds 42, 123, 456). Each seed produces an independent training run and generation.
- **Effect size:** Cohen's d between conditioned and unconditioned EF@10 distributions across seeds, computed with pooled standard deviation.

## Success Thresholds (Pre-Registered)

These thresholds are fixed a priori and will not be adjusted after observing results.

| Metric | STRONG GO | GO | PIVOT | NO-GO |
|--------|-----------|-----|-------|-------|
| Cohen's d (EF@10) | >= 0.8 | [0.5, 0.8) | [0.3, 0.5) | < 0.3 |

### Interpretation of Outcomes

- **STRONG GO (d >= 0.8):** Large effect. The project thesis (state-aware design outperforms static design) is robustly supported. Proceed with full manuscript preparation and multi-kinase generalization.
- **GO (d in [0.5, 0.8)):** Moderate effect. Publishable with appropriately tempered claims. Proceed with manuscript preparation.
- **PIVOT (d in [0.3, 0.5)):** Weak effect. State conditioning provides marginal benefit. Pivot framing to "diversity + multi-pocket docking" rather than "state conditioning drives enrichment."
- **NO-GO (d < 0.3):** State conditioning provides no meaningful benefit over the unconditioned baseline. Pivot to a negative-result publication or benchmark-only contribution.

### Gate G2

This ablation constitutes **Gate G2** in the project plan. The GO/NO-GO decision
will be recorded in `IdeationDept/Planner/output/logs/progress.md` with the
observed Cohen's d value, date, and interpretation.

## Covariates

The following covariates will be recorded and reported to enable interpretation
of results and identification of confounds:

| Covariate | Purpose |
|-----------|---------|
| Pool size (candidates per condition) | Ensures fair comparison |
| Chemical diversity (number of unique Murcko scaffolds) | Controls for diversity confound |
| FCD (Frechet ChemNet Distance to training set) | Measures distributional similarity to known chemistry |
| MPNN scoring component R-squared (scaffold split) | Established at 0.5153; documents scoring reliability |
| Validity rate (fraction of valid SMILES/SELFIES) | Controls for generation quality confound |
| Novelty (fraction not in training set) | Controls for memorization |

## Analysis Plan

### Primary Analysis

1. **Mann-Whitney U test** on EF@10 distributions (conditioned vs. unconditioned).
   - Two-sided test.
   - If scipy is unavailable, falls back to permutation test (10,000 permutations).

2. **Cohen's d** with pooled standard deviation.
   - Positive d indicates conditioned > unconditioned.
   - Thresholds as defined in the Success Thresholds table above.

3. **BCa bootstrap confidence intervals** (10,000 resamples) for:
   - EF@10 point estimates per condition
   - BEDROC(alpha=20) point estimates per condition
   - Mean composite score per condition
   - Difference in means between conditions

### Secondary Analyses

4. **BEDROC comparison:** BEDROC(alpha=20) between conditions. BEDROC provides
   a complementary early-enrichment metric that is less sensitive to threshold
   choice than EF@K.

5. **Scoring component ablation:** Report per-component scores (MPNN, SA, QED,
   Lipinski, similarity, docking) to identify which components drive any
   observed difference.

6. **Cliff's delta:** Non-parametric effect size as a robustness check on
   Cohen's d, since Cliff's delta does not assume normality.

### Visualization

7. **Box plot** of per-seed EF@10 values (conditioned vs. unconditioned).

8. **Distribution overlay** of composite scores for both conditions.

9. **Per-state enrichment breakdown** (conditioned arm only) to assess whether
   specific states contribute disproportionately.

### Reporting

- All results will be reported regardless of outcome (positive, negative, or null).
- Both point estimates and confidence intervals will be presented.
- Full per-seed metrics will be deposited as JSON artifacts.
- No cherry-picking of seeds or metrics.

## Data Availability

- **Code:** GitHub repository (this repository)
- **Training data:** ChEMBL (public database, EGFR bioactivity)
- **Structural data:** PDB (public, structures 1M17, 4ZAU, 5D41, 3W2R)
- **Generated candidates:** Will be deposited as JSON artifacts with manuscript
- **Statistical analysis code:** `src/statebind/evaluation/statistics.py` (Mann-Whitney U, Cohen's d, Cliff's delta, BCa bootstrap, permutation test)
- **Retrospective evaluation code:** `src/statebind/evaluation/retrospective.py` (EF@K, BEDROC, enrichment with CI)

## Commitment

This document was committed to version control before any Ablation C experiments
were conducted. The git commit hash and timestamp serve as proof of
pre-registration. The following commitments are made:

1. Results will be reported regardless of outcome (positive or negative).
2. The success thresholds defined above will not be modified after data collection.
3. The analysis plan will be followed as specified; any deviations will be documented and justified.
4. All random seeds and their results will be reported (no selective reporting).
5. The unconditioned VAE will use an identical architecture to the conditioned VAE, differing only in the n_states parameter.
