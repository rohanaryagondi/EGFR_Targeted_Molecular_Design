# Remaining Goals: Gap Analysis

**Last updated:** 2026-03-30T00:00:00+00:00
**Briefing session:** 1 (first briefing)

---

## The Central Question

StateBind exists to answer: does conformational state-aware design outperform static
single-structure design? As of today, **the project cannot answer this question.** The
null hypothesis has not been rejected. The observed score deltas (+0.020 mean, +0.035
diversity) are small, lack statistical backing, and are computed with a docking proxy
trained on 9 molecules and 25 decoys.

---

## Goal-by-Goal Status

### Targets MET

| Goal | Target | Current | Notes |
|------|--------|---------|-------|
| Test count | 450+ | 540 | Exceeded by 90. Progression: 359 → 540 across 9 workstreams |
| Similarity method | Morgan/ECFP4 | Morgan/ECFP4 Tanimoto (radius=2, 2048 bits) | Fallback to n-gram when RDKit unavailable |
| Drug-likeness method | RDKit QED + Lipinski + SA | QED(0.5) + Lipinski(0.25) + SA(0.25) | Weighted composite with heuristic fallback |
| Workstreams complete | 9/9 | 9/9 | All merged, zero conflicts |
| Statistical framework | Mann-Whitney U + CI | Framework built | Ready but not yet run on real scores |

### Targets PARTIALLY MET

| Goal | Target | Current | Gap |
|------|--------|---------|-----|
| Docking scoring | MPNN (RMSE < 1.0 pIC50) | Proxy MLP (9 binders + 25 decoys) | MLP discriminates known binders but is not a real affinity predictor. MPNN adapter written, model untrained. Training data prepared (1,678 compounds). |
| CI/CD | Clean GitHub Actions | Pipeline configured but ~40 ruff violations remain | Tests pass in CI; lint job fails due to pre-existing violations |

### Targets NOT MET

| Goal | Target | Current | What's Needed |
|------|--------|---------|---------------|
| Statistical significance | p < 0.05 Mann-Whitney U | No test run | Train models, re-run pipeline, execute statistical tests |
| Novel candidates | 100+ VAE-generated | 49 string-modified | Train VAE, generate from latent space, filter for validity |
| VAE reconstruction | > 80% | N/A (untrained) | GPU training ~2-4 hours |
| VAE validity | >= 50% | N/A (untrained) | GPU training, then generation |
| VAE uniqueness | >= 80% | N/A (untrained) | Depends on training quality |
| MPNN RMSE | < 1.0 pIC50 | N/A (untrained) | GPU training ~1-2 hours on 1,678 compounds |
| MPNN R-squared | > 0.5 | N/A (untrained) | Same |
| MPNN Pearson r | > 0.7 | N/A (untrained) | Same |
| hERG AUROC | > 0.75 | N/A (untrained) | GPU training ~2-3 hours |
| CYP3A4 AUROC | > 0.70 | N/A (untrained) | Same |
| ADMET endpoints | >= 4/6 Spearman > 0.5 | N/A (untrained) | Same |
| Synthetic accessibility | RDKit SA score | Implemented but not in scoring weights | SA is part of drug-likeness sub-score; not a standalone gate |

**Summary: 5 goals met, 2 partially met, 11 goals not met.** All unmet goals depend
on ML model training.

---

## Critical Path

The minimum path from current state to hypothesis testing:

```
1. Train 3 ML models on GPU (5-9 hours total, parallelizable)
   |
   v
2. Verify model quality metrics
   - VAE: reconstruction > 80%, validity >= 50%
   - MPNN: RMSE < 1.0, R-squared > 0.5
   - ADMET: hERG AUROC > 0.75
   |
   v
3. Generate VAE candidates (100+ per state, filter for validity)
   |
   v
4. Re-score all candidates with MPNN replacing docking proxy
   |
   v
5. Apply ADMET safety filter (flag hERG, CYP3A4 liabilities)
   |
   v
6. Re-run unified scoring for both pipelines
   |
   v
7. Execute Mann-Whitney U test on score distributions
   |
   v
8. Accept or reject null hypothesis
```

**Estimated time:** Steps 1-2 are the bottleneck (~5-9 hours GPU). Steps 3-8 are
automated by existing scripts and should complete in minutes once models are trained.

**Risk:** If model quality targets are not met (e.g., MPNN RMSE > 1.5, VAE validity
< 20%), the trained models may not produce meaningful improvements over the current
proxy scores. The project would need to iterate on hyperparameters, training data, or
architectures before proceeding.

---

## What Completion of Current Plans Looks Like

If everything goes perfectly — all models train to target quality, VAE generates
100+ valid candidates, MPNN achieves RMSE < 1.0, ADMET hits AUROC targets — the
project would have:

- A real affinity predictor replacing the docking proxy (20% of scoring weight activated)
- VAE-generated novel molecules (not string modifications)
- Safety filtering via ADMET predictions
- A statistically-tested comparison with p-value

**But even in this best case, significant gaps remain:**

### Gaps That Current Plans Do NOT Address

1. **No physics-based docking.** The MPNN predicts pIC50 from molecular graphs — it
   never simulates actual protein-ligand binding. It is a learned proxy, not a docking
   calculation. Real docking (AutoDock Vina, GNINA, Glide) would give physically
   interpretable binding poses and energies.

2. **No experimental validation.** Zero wet-lab data. No binding assays, no cell
   viability, no animal models. The entire pipeline is computational. Peer reviewers
   will flag this as a fundamental limitation.

3. **No selectivity profiling.** The pipeline scores binding to EGFR only. It does
   not check whether candidates also bind off-target kinases (ABL, BRAF, ALK, etc.).
   A molecule that binds everything is not a drug.

4. **No retrosynthetic analysis.** The pipeline generates molecular structures but
   does not assess whether they can actually be synthesized in a lab. SA score is
   a rough estimate; real retrosynthetic planning (e.g., ASKCOS, IBM RXN) would
   identify synthesis routes.

5. **Conformational model is discretized.** Real kinase dynamics are continuous —
   the protein breathes through a landscape of intermediate conformations, not 4
   discrete states. The 4-state model is a useful simplification but misses
   intermediate geometries.

6. **Training data is modest.** 1,678 compounds for MPNN is small by modern
   standards. Pre-training on larger datasets (e.g., ChEMBL-wide, PubChem) followed
   by fine-tuning on EGFR data would likely improve generalization.

7. **No multi-objective optimization.** Scoring is a weighted sum. Pareto
   optimization across competing objectives (affinity vs. selectivity vs. ADMET vs.
   synthesis) would explore a richer design space.

8. **ADMET is not in the scoring weights.** The ADMET predictor filters candidates
   but does not contribute to the unified score. A candidate with perfect affinity
   but terrible hERG liability still scores high — it just gets flagged afterward.
   Integrating ADMET into scoring would make the ranking itself safety-aware.

9. **No uncertainty quantification.** The models produce point predictions. There
   is no epistemic uncertainty estimate (how confident is the MPNN in this pIC50?)
   or aleatoric uncertainty (how noisy is the data?). Bayesian methods or ensembles
   would provide confidence intervals.

10. **No active learning loop.** The pipeline is one-shot: generate → score → rank.
    An active learning cycle (generate → score → identify most informative candidates
    → retrain → generate again) could iteratively improve both the model and the
    candidate pool.

---

## The Honest Assessment

StateBind has built solid infrastructure. The pipeline, testing, scoring, and
statistical frameworks are production-quality for a research project. But the
scientific question — does state-awareness help? — remains unanswered.

**The project is at a make-or-break point.** ML training is the immediate bottleneck.
If models train successfully and the Mann-Whitney U test shows p < 0.05, the project
has a publishable result. If the null hypothesis is retained even with trained models,
the project needs to investigate why — and the gaps listed above become the next
frontier.

The 10 gaps listed above are not failures — they are opportunities. Each one represents
a potential leap in the project's scientific credibility and practical utility. A
Visionary looking at this project should focus on: which of these gaps, if closed,
would most change the answer to the central question?
