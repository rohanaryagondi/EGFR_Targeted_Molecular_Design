# Remaining Goals: Gap Analysis

**Last updated:** 2026-04-07T00:00:00+00:00
**Briefing session:** 2 (final update)

---

## The Central Question

StateBind exists to answer: does conformational state-aware design outperform static
single-structure design? As of today, **the project has answered this question: the
null hypothesis is formally retained.** The static baseline achieved higher mean scores
(0.5437 vs 0.4378, p<0.001, Cohen's d=1.36 favoring static). However, the state-aware
pipeline produced far more candidates (461 vs 30), greater diversity (0.9056 vs 0.5684),
higher max score (0.7794 vs 0.7288), and 431 novel molecules.

---

## Goal-by-Goal Status

### Targets MET

| Goal | Target | Current | Notes |
|------|--------|---------|-------|
| Test count | 450+ | 548 | Exceeded by 98. Progression: 359 → 548 across 9 workstreams + post-training |
| Similarity method | Morgan/ECFP4 | Morgan/ECFP4 Tanimoto (radius=2, 2048 bits) | Fallback to n-gram when RDKit unavailable |
| Drug-likeness method | RDKit QED + Lipinski + SA | QED(0.5) + Lipinski(0.25) + SA(0.25) | Weighted composite with heuristic fallback |
| Workstreams complete | 9/9 | 9/9 | All merged, zero conflicts |
| Statistical framework | Mann-Whitney U + CI | Complete — run on trained model scores | p<0.001, d=1.36, null retained |

### Targets ALSO MET (previously partial or unmet)

| Goal | Target | Achieved | Notes |
|------|--------|----------|-------|
| Docking scoring | MPNN (RMSE < 1.0 pIC50) | RMSE=0.7182, R²=0.6863, Pearson=0.8323 | Trained on 10,466 ChEMBL EGFR compounds (12.7M params). Active in scoring cascade. |
| CI/CD | Clean GitHub Actions | All 121 ruff violations fixed (121→0) | Lint job now passes clean |
| Statistical significance | p < 0.05 Mann-Whitney U | p<0.001, d=1.36 | Test run; null formally retained (static favored on mean score) |
| Novel candidates | 100+ VAE-generated | 395 VAE-generated (431 total novel) | VAE v3 (SELFIES) generating valid, unique molecules |
| VAE validity | >= 50% | 99.9% | SELFIES encoding guarantees near-perfect validity |
| VAE uniqueness | >= 80% | 94.8% | Exceeded target |
| MPNN RMSE | < 1.0 pIC50 | 0.7182 | Met target on 10,466 compounds |
| MPNN R-squared | > 0.5 | 0.6863 | Met target |
| MPNN Pearson r | > 0.7 | 0.8323 | Met target |
| hERG AUROC | > 0.75 | 0.7745 | Met target (but hard filtering rejects ALL kinase inhibitors — used informational only) |
| CYP3A4 AUROC | > 0.70 | 0.7323 | Met target |
| Synthetic accessibility | RDKit SA score | In drug-likeness sub-score | SA is part of drug-likeness composite (25% weight) |

**Summary: all planned goals met.** The null hypothesis was retained — static baseline
outperforms on mean score — but the state-aware pipeline excels on diversity, novelty,
and candidate volume.

---

## Critical Path (COMPLETED)

All steps in the critical path have been executed:

```
1. Train 3 ML models on GPU                              DONE
   - VAE v3 (SELFIES): 300 epochs on H200               DONE
   - MPNN: trained on 10,466 compounds                   DONE
   - ADMET: trained on 27,698 molecules                  DONE
   |
   v
2. Verify model quality metrics                           DONE
   - VAE: 99.9% valid, 94.8% unique                     EXCEEDED
   - MPNN: RMSE=0.7182, R²=0.6863, Pearson=0.8323      MET
   - ADMET: hERG AUROC=0.7745, CYP3A4 AUROC=0.7323     MET
   |
   v
3. Generate VAE candidates (395 generated)                DONE
   |
   v
4. Re-score all candidates with MPNN active               DONE
   |
   v
5. ADMET safety filter (informational only — hard         DONE
   filtering rejects ALL kinase inhibitors on hERG)
   |
   v
6. Re-run unified scoring for both pipelines              DONE
   |
   v
7. Execute Mann-Whitney U test on score distributions     DONE
   |
   v
8. Null hypothesis formally retained                      DONE
```

**Outcome:** Static baseline had higher mean scores (0.5437 vs 0.4378, p<0.001,
d=1.36). State-aware pipeline produced more candidates (461 vs 30), greater diversity
(0.9056 vs 0.5684), and 431 novel molecules.

---

## What Was Achieved

All models trained to or above target quality. The project now has:

- A real affinity predictor (MPNN) active in the scoring cascade (20% of scoring weight)
- 395 VAE-generated novel molecules (SELFIES-encoded, 99.9% valid)
- ADMET safety profiling (informational — hard filtering proved too aggressive for kinase inhibitors)
- A statistically-tested comparison: p<0.001, d=1.36, null retained

**Significant gaps remain for future work:**

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

6. **Training data is modest.** 10,466 compounds for MPNN is moderate but still small
   by modern standards. Pre-training on larger datasets (e.g., ChEMBL-wide, PubChem)
   followed by fine-tuning on EGFR data would likely improve generalization.

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

StateBind has built solid infrastructure and completed the full experimental cycle.
The pipeline, testing, scoring, and statistical frameworks are production-quality for
a research project. The scientific question — does state-awareness help? — has been
answered: **the null hypothesis is retained.** The static baseline outperforms on mean
score under the current scoring function.

However, the result is nuanced. The state-aware pipeline produces vastly more
candidates (461 vs 30), greater chemical diversity (0.9056 vs 0.5684), a higher
maximum score (0.7794 vs 0.7288), and 431 novel molecules. Weight sensitivity
analysis shows 44% of weight combinations favor state-aware design. The deficit is
concentrated in the reference similarity component — VAE-generated molecules are
structurally diverse but less similar to the 3 reference drugs.

The 10 gaps listed above are not failures — they are opportunities. Each one represents
a potential leap in the project's scientific credibility and practical utility. A
Visionary looking at this project should focus on: which of these gaps, if closed,
would most change the answer to the central question? In particular, expanding the
reference set beyond 3 drugs and integrating physics-based docking could shift the
balance significantly.
