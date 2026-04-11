# Gate G2 Report: Ablation C -- State Conditioning Effect on Molecular Generation

**Date:** 2026-04-11
**Pre-registration:** commit 9e7cf96 (`docs/pre-registration.md`)
**Gate decision: NO_GO (definitive, n=10 seeds)**

---

## 1. Executive Summary

Gate G2 tests the core StateBind thesis: does conformational state-conditioned
molecular generation outperform unconditioned generation for EGFR inhibitors?

We trained 10 conditioned (3-state) and 10 unconditioned (1-state) Transformer VAE
models across independent random seeds, generated ~600 candidates per seed per
condition, and scored all ~6,800 molecules with identical unified scoring
(state_specificity zeroed for fairness).

**Result:** Cohen's d = 0.059 (stochastic) / 0.020 (greedy) on per-molecule
composite scores. Cohen's d = 0.162 (stochastic) / -0.024 (greedy) on per-seed
EF@10. All metrics fall deep within the pre-registered NO_GO zone (d < 0.3).
State conditioning provides no measurable benefit to molecular quality under the
current experimental design.

---

## 2. Background

### 2.1 Project Thesis

StateBind hypothesizes that conditioning molecular generation on EGFR
conformational states (DFGin/aCin, DFGin/aCout, DFGout/aCin) produces better
drug candidates than a single unconditioned model trained on all EGFR ligands.

### 2.2 Gate G2 Pre-Registered Thresholds

From `docs/pre-registration.md` (commit 9e7cf96), fixed a priori:

| Outcome    | Cohen's d   | Interpretation |
|------------|-------------|----------------|
| STRONG GO  | >= 0.8      | Large effect, thesis robustly supported |
| GO         | [0.5, 0.8)  | Moderate effect, publishable |
| PIVOT      | [0.3, 0.5)  | Weak effect, reframe thesis |
| NO-GO      | < 0.3       | No meaningful benefit |

### 2.3 VAE Architecture History

The experiment went through three model versions:

**v1/v2: SELFIES GRU VAE (FAILED)**
- Architecture: SELFIES tokenization + bidirectional GRU encoder/decoder
- Result: Total model failure -- 0% reconstruction, 0 aromatic rings, 0 active
  latent dimensions
- Root cause: Posterior collapse + decoder incapacity. SELFIES tokens (Ring1/Ring2)
  create long-range dependencies that the GRU decoder cannot learn. All 64 latent
  dimensions collapsed to the prior (per-dim KL < 0.001), meaning the decoder
  ignores z entirely.
- Gate G2 (v2): NO_GO (d = -0.039), but uninformative due to model failure

**v3: Transformer VAE (WORKING)**
- Architecture: SMILES tokenization + bidirectional GRU encoder + Transformer
  decoder (4 layers, 4 heads, d_model=256)
- Key fixes: Free-bits KL (0.25/dim), word dropout (0.1), kl_weight=1.0
- State conditioning: State one-hot projected to 8 prefix tokens prepended to
  decoder input
- Training: 2000 epochs max, patience 300, cosine LR schedule with warmup
- Training data: 8,109 EGFR molecules (ChEMBL IC50 < 10uM + known binders)
- Gate G2 (v3): NO_GO (d = 0.059), but now informative -- the model works,
  conditioning just doesn't help

---

## 3. Transformer VAE Validation

Before running the ablation, we validated all 6 original models (3 conditioned +
3 unconditioned, seeds 42/123/7). Key findings confirming the model is working:

### 3.1 Reconstruction Quality

| Seed | Exact Match | Mean Tanimoto | Valid Recon Rate | Tan > 0.7 |
|------|-------------|---------------|------------------|-----------|
| 42 (cond)  | 2.4% | 0.4043 | 97.2% | 74/500  |
| 123 (cond) | 4.2% | 0.4620 | 97.4% | 103/500 |
| 7 (cond)   | 2.2% | 0.3963 | 93.0% | 72/500  |
| 42 (uncond)| 3.4% | 0.4191 | 93.8% | 90/500  |

For comparison, the GRU VAE had 0% exact match and 0.031 mean Tanimoto.

### 3.2 Latent Space

| Seed | Active Dims (KL > 0.01) | Total KL/sample | Mean mu norm |
|------|-------------------------|-----------------|-------------|
| 42 (cond)  | 64/64 | 14.13 | 4.26 |
| 123 (cond) | 64/64 | 14.38 | 4.42 |
| 7 (cond)   | 64/64 | 13.89 | 4.23 |

GRU VAE had 0/64 active dimensions.

### 3.3 State Centroid Separation

The conditioned model learns mild state clustering in latent space:

| Seed | DFGin_aCin vs DFGin_aCout | DFGin_aCin vs DFGout_aCin | DFGin_aCout vs DFGout_aCin |
|------|---------------------------|---------------------------|----------------------------|
| 42   | 0.329 | 0.371 | 0.419 |
| 123  | 0.320 | 0.361 | 0.321 |
| 7    | 0.319 | 0.261 | 0.261 |

These distances are small relative to the overall latent space scale (mu norm ~4.3),
indicating the model learned to distinguish states only weakly.

### 3.4 Generation Quality

| Metric | Conditioned (avg) | GRU VAE |
|--------|-------------------|---------|
| Mean aromatic rings | 3.49 | 0.03 |
| Scaffold overlap with training | 98-136 | 0 |
| Mean NN similarity to training | 0.73-0.79 | 0.125 |
| Max drug similarity (any EGFR drug) | 0.90-1.00 | 0.167 |
| Drug scaffolds recovered | erlotinib, gefitinib, osimertinib, lazertinib | none |
| 100% aromatic-containing | yes | no |

**Conclusion:** The Transformer VAE generates pharmacologically relevant EGFR-like
molecules. The model is not the problem.

---

## 4. Ablation C Results (Definitive, n=10)

### 4.1 Experimental Design

- **Conditioned model:** 3-state Transformer VAE (DFGin_aCin, DFGin_aCout,
  DFGout_aCin). 200 candidates/state/seed = 600 raw/seed.
- **Unconditioned model:** 1-state Transformer VAE. 600 candidates/seed.
- **Seeds:** 42, 123, 7, 13, 37, 99, 256, 314, 512, 777 (10 per condition)
- **Scoring:** Identical unified scoring with weights: reference_similarity=0.35,
  druglikeness=0.30, docking_proxy=0.20, state_specificity=0.15.
  **state_specificity forced to 0 for both arms** (empty state_smiles_map) to
  ensure scoring fairness.
- **Generation modes:** Stochastic (T=0.8) and greedy (T=0.0)
- **Retrospective enrichment:** Cutoff year 2010, Tanimoto threshold 0.4,
  10,000 BCa bootstrap iterations

### 4.2 Aggregate Results -- Stochastic (T=0.8)

| Metric | Conditioned | Unconditioned | Difference |
|--------|------------|---------------|------------|
| n candidates (pooled, unique) | 3,396 | 3,449 | -- |
| Mean composite score | 0.4240 | 0.4197 | +0.0043 |
| Median composite | 0.4140 | 0.4088 | +0.0052 |
| Pooled EF@10 | 7.789 | 5.425 | +2.364 |
| Pooled EF@50 | 5.141 | 5.270 | -0.129 |
| Pooled BEDROC(20) | 0.484 | 0.459 | +0.025 |
| Novelty vs training | 69.5% | 68.5% | +1.0% |
| Internal diversity | 0.821 | 0.825 | -0.004 |

| Effect Size | Value | Interpretation |
|-------------|-------|----------------|
| Cohen's d (composite, pooled) | 0.0594 | Negligible |
| Cohen's d (EF@10, per-seed) | 0.1617 | Negligible |
| Cliff's delta (composite) | 0.0327 | Negligible |
| Mann-Whitney U p-value | 0.0191 | Marginally significant |
| Mean diff BCa CI | [0.0019, 0.0068] | Nonzero but trivially small |

### 4.3 Aggregate Results -- Greedy (T=0.0)

| Metric | Conditioned | Unconditioned | Difference |
|--------|------------|---------------|------------|
| Mean composite score | 0.4262 | 0.4226 | +0.0015 |
| Pooled EF@10 | 7.375 | 4.270 | +3.105 |

| Effect Size | Value | Interpretation |
|-------------|-------|----------------|
| Cohen's d (composite, pooled) | 0.0196 | Negligible |
| Cohen's d (EF@10, per-seed) | -0.0238 | Zero / wrong direction |
| Mann-Whitney U p-value | 0.532 | Not significant |
| Mean diff BCa CI | [-0.0016, 0.0047] | Crosses zero |

### 4.4 Per-Seed EF@10 Breakdown

This is the critical data. The per-seed EF@10 shows high variance with no
consistent direction:

**Stochastic (T=0.8):**

| Seed | Cond EF@10 | Uncond EF@10 | Cond wins? |
|------|-----------|-------------|------------|
| 42   | 6.832 | 6.792 | yes (barely) |
| 123  | 3.291 | 4.572 | no |
| 7    | 7.357 | 5.022 | yes |
| 13   | 4.343 | 2.574 | yes |
| 37   | 4.509 | 4.866 | no |
| 99   | 6.211 | 4.245 | yes |
| 256  | 3.237 | 4.633 | no |
| 314  | 3.929 | 7.200 | no |
| 512  | 5.829 | 1.727 | yes |
| 777  | 4.322 | 5.679 | no |
| **Mean** | **4.986** | **4.731** | **5 vs 5** |

Conditioned wins 5/10 seeds. Mean difference is noise.

**Greedy (T=0.0):**

| Seed | Cond EF@10 | Uncond EF@10 | Cond wins? |
|------|-----------|-------------|------------|
| 42   | 4.704 | 5.775 | no |
| 123  | 8.224 | 6.921 | yes |
| 7    | 6.245 | 1.300 | yes |
| 13   | 3.514 | 2.893 | yes |
| 37   | 3.976 | 5.818 | no |
| 99   | 3.359 | 1.467 | yes |
| 256  | 3.673 | 7.478 | no |
| 314  | 1.449 | 6.076 | no |
| 512  | 6.974 | 3.215 | yes |
| 777  | 2.167 | 3.860 | no |
| **Mean** | **4.428** | **4.480** | **5 vs 5** |

Again, 5/5 split. The greedy conditioned mean is actually 0.052 lower.

### 4.5 Per-Seed Composite Score Cohen's d

| Seed | d (stochastic) | d (greedy) |
|------|----------------|------------|
| 42   | +0.123 | +0.089 |
| 123  | +0.066 | +0.001 |
| 7    | -0.012 | 0.000 |
| 13   | +0.173 | +0.103 |
| 37   | +0.014 | -0.163 |
| 99   | -0.061 | -0.238 |
| 256  | -0.119 | +0.220 |
| 314  | +0.052 | +0.117 |
| 512  | +0.060 | +0.032 |
| 777  | +0.166 | +0.090 |

No seed reaches d > 0.3. Direction flips across seeds.

### 4.6 Component Analysis (Stochastic)

| Component | Cond mean | Uncond mean | d | Cliff's delta |
|-----------|----------|------------|---|---------------|
| reference_similarity | 0.268 | 0.260 | 0.060 | 0.033 |
| druglikeness | 0.616 | 0.615 | 0.006 | 0.004 |
| docking_proxy | 0.728 | 0.722 | 0.059 | 0.034 |
| state_specificity | 0.000 | 0.000 | 0.000 | 0.000 |

No component shows a meaningful effect. The conditioning signal does not
propagate to any individual scoring dimension.

---

## 5. The n=3 False Alarm

### 5.1 What We Saw at n=3

The initial 3-seed results appeared to show a promising EF@10 signal, particularly
for greedy generation:

| Mode | d(composite) n=3 | d(EF@10) n=3 | Interpretation |
|------|-------------------|--------------|----------------|
| Stochastic | 0.085 | 0.206 | Weak signal? |
| Greedy | 0.045 | **0.706** | Near-GO signal |

The greedy d(EF@10) = 0.706 fell in the GO range, suggesting state conditioning
provided a large benefit to enrichment.

### 5.2 What n=10 Revealed

| Mode | d(composite) n=10 | d(EF@10) n=10 | Change |
|------|--------------------|--------------------|--------|
| Stochastic | 0.059 | 0.162 | d(EF@10) dropped 21% |
| Greedy | 0.020 | **-0.024** | d(EF@10) collapsed to ~zero |

The greedy d(EF@10) collapsed from 0.706 to -0.024. The apparent signal was
driven entirely by one seed outlier: unconditioned seed 7 produced EF@10 = 1.3
(far below the cross-seed mean of ~4.5), which inflated the 3-seed effect size.

### 5.3 Lesson

EF@10 is inherently high-variance because it depends on the top ~10% of the
ranked list. With n=3 seeds and EF@10 standard deviations of ~2.0, a paired
t-test has only ~20% power to detect d=0.5. The n=3 "signal" was
indistinguishable from noise -- this was a Type I near-miss.

The n=10 design provides ~60% power at d=0.5 and ~80% at d=1.0. The observed
d=0.16 and d=-0.02 are definitively in the noise floor.

---

## 6. Root Cause Analysis

### 6.1 Why Conditioning Doesn't Help

The Transformer VAE is generating good molecules (EF@10 = 5-8 for both arms).
The issue is that the conditioned model does not generate *better* molecules.
Three hypotheses for why:

**H1: Weak conditioning mechanism.** The state one-hot is projected to 8 prefix
tokens, which the Transformer decoder attends to. The latent space shows state
centroids only 0.26-0.42 apart (vs mu norm ~4.3), suggesting the model treats
state labels as a minor signal. A stronger mechanism (cross-attention, separate
decoders, or adversarial state prediction) might force more state-specific generation.

**H2: Insufficient state-specific structure in training data.** The 3 EGFR states
may not represent chemically distinct binding preferences in the 8,109-molecule
training set. If the same scaffolds (4-anilinoquinazolines, pyrimidines) appear
across all 3 states, the model correctly learns that state labels are weak
predictors of molecular structure.

**H3: Wrong evaluation metric.** The ablation scores both arms with
state_specificity = 0. This tests whether conditioning improves *generic*
molecular quality. It does not test the actual thesis -- whether conditioned
molecules are better *for their target state's pocket conformation*. The right
evaluation would dock conditioned molecules against their target state's pocket
and compare to unconditioned molecules docked against the same pocket.

### 6.2 The state_specificity = 0 Design Issue

The unified scoring function has 4 components:
- reference_similarity (weight 0.35)
- druglikeness (weight 0.30)
- docking_proxy (weight 0.20)
- state_specificity (weight 0.15)

For ablation fairness, state_specificity was zeroed by passing an empty
state_smiles_map to both arms. This means 15% of the scoring signal is
structurally excluded. More importantly, the remaining 3 components measure
*generic* EGFR drug quality, not *state-specific* quality.

The docking_proxy component uses a fixed reference pocket (1M17, DFGin/aCin).
It does not measure how well a molecule docks to DFGin/aCout or DFGout/aCin
pockets. A molecule conditioned on DFGin/aCout that would dock excellently in
the 4HJO pocket gets no credit for this -- it's scored only against 1M17.

This means **the ablation was structurally unable to detect the conditioning
signal even if it existed.** The test asked: "does knowing the conformational
state help you make generically good EGFR molecules?" The answer is no. But
the thesis question is: "does knowing the conformational state help you make
molecules that are good *for that specific conformation*?" That question remains
untested.

---

## 7. What the Experiment Does Establish

Despite the NO_GO outcome, the experiment produced several clear findings:

1. **The Transformer VAE is a working EGFR molecular generator.** EF@10 = 5-8,
   drug scaffold recovery, 64/64 active latent dims, 2-4% exact reconstruction.
   This is a positive methodological contribution independent of the state
   conditioning thesis.

2. **State conditioning does not improve generic molecular quality.** Across 10
   seeds, 2 generation modes, ~6,800 molecules, and 4 scoring components, no
   metric shows d > 0.17. This is a definitive negative result.

3. **Small-sample EF@10 is unreliable.** The n=3 greedy EF@10 d=0.71 collapsed
   to d=-0.02 at n=10. Any ablation study reporting EF@10 effect sizes from
   fewer than ~8 seeds should be viewed with skepticism.

4. **The GRU decoder architecture fundamentally cannot handle molecular generation
   with SELFIES.** This was established in the diagnostic phase (v1/v2) and
   resolved by switching to a Transformer decoder with SMILES.

---

## 8. Possible Next Steps

### 8.1 State-Specific Docking Evaluation (tests H3)

Dock all ~6,800 molecules against 3 pocket conformers:
- DFGin/aCin: PDB 1M17
- DFGin/aCout: PDB 4HJO
- DFGout/aCin: PDB 3W2S

Test whether conditioned molecules for state X dock better to pocket X than
unconditioned molecules. This uses existing GNINA infrastructure and is the
real test of the thesis. Estimated: ~20,400 docking runs, 3 GPU SLURM jobs.

### 8.2 Stronger Conditioning Mechanism (tests H1)

Replace prefix-token conditioning with cross-attention from learned state
embeddings or train 3 separate decoder heads. If even strong conditioning
shows no signal, the null is about the data/biology (H2), not the architecture.
Estimated: code changes to transformer_vae.py + 20 GPU training jobs.

### 8.3 Negative-Result Publication (accepts the null)

Write up the full story: GRU failure diagnosis, Transformer fix, 10-seed
definitive null. Publishable at JCIM or Bioinformatics. The Transformer VAE
itself and the statistical power lesson are positive contributions. The null
result on state conditioning is valuable to the field.

---

## 9. Artifact References

| Artifact | Path |
|----------|------|
| Pre-registration | `docs/pre-registration.md` (commit 9e7cf96) |
| Stochastic results (10 seeds) | `artifacts/evaluation/ablation_c_results_v3_10seed.json` |
| Greedy results (10 seeds) | `artifacts/evaluation/ablation_c_results_v3_greedy_10seed.json` |
| Stochastic results (3 seeds) | `artifacts/evaluation/ablation_c_results_v3.json` |
| Greedy results (3 seeds) | `artifacts/evaluation/ablation_c_results_v3_greedy.json` |
| Transformer VAE validation | `artifacts/evaluation/transformer_vae_validation.json` |
| GRU VAE diagnostics | `artifacts/evaluation/vae_diagnostics/synthesis.json` |
| Conditioned model configs | `configs/transformer_vae.yaml` |
| Unconditioned model configs | `configs/transformer_vae_unconditioned.yaml` |
| Training script (conditioned) | `scripts/slurm_transformer_vae.sh` (seeds 42/123/7) |
| Training script (extended) | `scripts/slurm_transformer_vae_extended.sh` (seeds 13-777) |
| Training script (uncond) | `scripts/slurm_transformer_vae_uncond.sh` (seeds 42/123/7) |
| Training script (uncond ext) | `scripts/slurm_transformer_vae_uncond_extended.sh` (seeds 13-777) |
| Analysis script | `scripts/run_ablation_c_analysis_v3.py` |
| Validation script | `scripts/validate_transformer_vae_full.py` |

## 10. SLURM Job History

| Job ID | Description | Status |
|--------|-------------|--------|
| 7880395 | Conditioned training (seeds 42/123/7) | Completed |
| 7880397 | Unconditioned training (seeds 42/123/7) | Completed |
| 7896377 | Validation (failed: checkpoint loading bug) | Failed |
| 7898025 | Validation (fixed) | Completed |
| 7898026_[0-6] | Conditioned training (seeds 13/37/99/256/314/512/777) | Completed |
| 7898027_[0-6] | Unconditioned training (seeds 13/37/99/256/314/512/777) | Completed |
| 7903434 | Ablation C v3 10-seed analysis (stochastic + greedy) | Completed |
