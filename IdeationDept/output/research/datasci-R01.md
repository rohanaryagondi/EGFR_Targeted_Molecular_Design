---
agent: Maverick Data Scientist / Statistician
round: 1
date: 2026-04-08
type: research-note
topic: Statistical Rigor of StateBind's Claims -- Enrichment Factor Variance, Confounding, Multi-Target Power, Benchmark Leakage, and Publication Readiness
---

# Research Note: The Statistical Foundations Are Not Yet Publication-Ready

## Summary

StateBind's 10x enrichment factor (EF@10 = 4.95/7.72 vs 0.47/0.79) is the project's headline result, but it rests on a sample of N=3-5 held-out drugs, an uncontrolled comparison that conflates at least four factors, and no reported confidence intervals. This research note surveys the statistical literature on enrichment factor variance, ablation design, multi-target validation requirements, benchmark leakage, and reporting standards. The central finding is sobering: **the current evidence is sufficient for an interesting case study but insufficient for a rigorous publication claim**. The path to publication-readiness requires (1) bootstrap confidence intervals on all metrics, (2) a proper ablation study isolating state awareness from generation method and candidate count, (3) multi-kinase validation on 4-6 additional targets, and (4) adoption of BEDROC as the primary early-recognition metric with pre-registered endpoints.

## Research Questions

1. What is the statistical variance of EF@10 when computed over N=3-5 positive examples, and what confidence interval width should we expect?
2. What confounders exist in the state-aware vs static comparison, and what ablation design would isolate each factor?
3. How many kinase targets with sufficient approved drugs exist for multi-target validation, and what statistical power would pooled analysis provide?
4. What forms of data leakage and benchmark contamination apply to StateBind's retrospective validation?
5. What reporting standards do target journals require for virtual screening enrichment claims?
6. What alternative metrics (BEDROC, power metric) are superior to EF for StateBind's setting?
7. How should multiple testing be handled when reporting many metrics across two pipelines?

## Methods

### Sources Consulted

- PubMed, Google Scholar, and arXiv for primary literature on enrichment factor statistics
- ChEMBL v34 database for kinase bioactivity data counts and target identification
- BRIMR Protein Kinase Inhibitor database for FDA-approved kinase drug timelines
- KLIFS database literature for kinase conformational state coverage
- Polaris benchmarking platform documentation and method comparison guidelines
- Journal editorial policies (Nature Computational Science, JCIM, J Cheminformatics)

### Search Strategy

Conducted 20+ targeted searches spanning enrichment factor confidence intervals, BEDROC metrics, ablation study design in molecular generation, benchmark contamination in molecular ML, bootstrap methods for ratio statistics, kinase approved drug timelines, ChEMBL data availability, multi-target validation power analysis, virtual screening reporting standards, causal inference for drug design comparison, QSAR validation best practices, Polaris method comparison guidelines, and coverage bias in small molecule ML. Fetched and analyzed 8 full-text articles plus the BRIMR kinase inhibitor database.

---

## Findings

### Finding 1: Enrichment Factor Variance with Small N Is Catastrophic

The enrichment factor EF@k is defined as: EF@k = (n_actives_in_top_k / k) / (N_actives / N_total), where n_actives_in_top_k follows a hypergeometric distribution. For StateBind's pre-2010 retrospective with N_actives = 5 held-out drugs among N_total = 461 candidates at k = 10% (46 candidates):

- Under the null hypothesis (random ranking), E[EF@10] = 1.0 with high variance
- The observed EF@10 = 4.95 means approximately 2.3 of 5 actives fell in the top 46 candidates (rounding effects apply)
- If ONE active drug moved from rank 45 to rank 47 (a shift of 2 positions out of 461), EF@10 drops by ~20% (from 4.95 to ~3.96)
- The standard error of the proportion (actives in top k%) follows SE = sqrt(p*(1-p)/n) where n=5, giving SE ~ 0.22 for p=0.46
- A 95% CI on the proportion in the top 10% spans roughly [0.05, 0.87], translating to EF@10 in approximately [0.5, 8.7]

This is an enormous confidence interval. The true enrichment could plausibly be anywhere from negligible (0.5x) to very large (8.7x). The point estimate of 4.95 is consistent with the data, but so is 1.5.

**Key data points:**
- Nicholls (2016) in "The statistics of virtual screening and lead optimization" (J Comput-Aided Mol Des, 29:1205) showed that analytic formulae for EF variance depend only on the number of actives, inactives, and the measured value, and that with fewer than ~20 actives the uncertainty is "extremely large"
- Empereur-mot et al. (2022) in "Confidence bands and hypothesis tests for hit enrichment curves" (J Cheminformatics, 14:48) demonstrated that proper inference on enrichment curves is "almost never considered" in published virtual screening studies, and introduced the EmProc method for constructing confidence intervals that accounts for within-algorithm and between-algorithm correlations

**Relevance to StateBind:** The 10x enrichment claim is anecdotal without confidence intervals. With N=5, the 95% CI is so wide that we cannot statistically distinguish a 2x enrichment from a 20x enrichment. This is the single most critical statistical weakness in the manuscript.

---

### Finding 2: BEDROC Is the Correct Metric (Not EF)

Truchon and Bayly (2007) in "Evaluating Virtual Screening Methods: Good and Bad Metrics for the 'Early Recognition' Problem" (J Chem Inf Model, 47:488-508) demonstrated that:

- EF@k is a threshold-dependent metric that discards information about the full ranking
- ROC AUC is insensitive to early recognition performance because it weights all positions equally
- BEDROC (Boltzmann-Enhanced Discrimination of ROC) uses an exponential weighting that emphasizes early ranks, with parameter alpha controlling the degree of emphasis
- At alpha=20 (the recommended default), 80% of BEDROC's weight comes from the top 8% of the ranked list
- BEDROC ranges from 0 to 1 with well-understood null distributions, making it amenable to hypothesis testing
- BEDROC is now "perhaps the most frequently adopted metric for measuring early recognition in virtual screening" (Pharmacelera, 2023)

**Key data points:**
- BEDROC at alpha=20.0 for a perfect ranker = 1.0; for a random ranker = ~0.0 (approaches 0 for large databases)
- Unlike EF, BEDROC uses the full ranking, not just a binary above/below threshold
- BEDROC can be computed with bootstrap CIs more stably than EF because it is a continuous function of the ranking

**Relevance to StateBind:** StateBind should report BEDROC(alpha=20) as the primary early-recognition metric, with EF@10 and EF@50 as secondary. BEDROC will make better use of the limited positives and produce more interpretable confidence intervals. The implementation is straightforward using the `oddt.metrics` package.

---

### Finding 3: The Comparison Is Hopelessly Confounded Without Ablations

The state-aware vs static comparison conflates at minimum four factors:

| Factor | Static | State-Aware | Confounded? |
|--------|--------|-------------|-------------|
| State awareness | 1 state | 4 states | YES -- the thesis |
| Generation method | Templates only | VAE + templates | YES |
| Candidate count | 30 | 461 (15.4x more) | YES |
| Chemical diversity | 0.5684 | 0.9056 (+59%) | YES (consequence of #2 and #3) |
| Scoring function | Same | Same | Controlled |
| Reference molecules | Same 3 | Same 3 | Controlled |

The enrichment advantage could arise entirely from having 15x more candidates (a larger haystack contains more needles). Or from VAE-generated diversity (novel scaffolds are more likely to resemble future drugs). Or from the combination. The state-conditioning of the VAE is only one of four varying factors.

**Published ablation standards:** Recent high-quality molecular generation papers in Nature Communications and JCIM routinely include ablation studies. For example:
- Gu et al. (2025) in "Target-aware 3D molecular generation" (Nature Commun, 16:3169) performed ablations removing bond diffusion and property guidance independently, showing each component's contribution
- Ablation study design guidance from emergentmind.com emphasizes that "a single process, module, parameter, or physical region is precisely altered or removed while holding all other variables constant to unambiguously isolate its contribution"

**Required ablation matrix for StateBind:**

| Experiment | State? | Generator | N candidates | What it tests |
|-----------|--------|-----------|-------------|---------------|
| A: Static baseline | No | Template | 30 | Current baseline |
| B: State-aware full | Yes | VAE+Tmpl | 461 | Current state-aware |
| C: Unconditioned VAE | No | VAE (no state) | ~400 | Isolates state info from VAE |
| D: State-conditioned template | Yes | Template (4 states) | ~36 | Isolates VAE from state |
| E: State-aware subsample | Yes | VAE+Tmpl | 30 (random) | Isolates candidate count |
| F: Random diverse | No | Random SMILES | 461 | Lower bound / sanity check |

**Critical comparison:** If Experiment C (unconditioned VAE, no state info, ~400 candidates) shows enrichment similar to Experiment B (state-aware, 461 candidates), then state-awareness is NOT the driver. The VAE-generated diversity alone explains the result. This is the experiment that could kill the thesis, and therefore it MUST be run before publication.

**Relevance to StateBind:** Without ablations C, D, and E, the claim "state-awareness drives enrichment" is unsupported. Reviewers at any top venue will demand these controls. The ablation experiments are computationally inexpensive -- they reuse existing infrastructure and can be completed in days.

---

### Finding 4: Multi-Kinase Validation Data Availability Is Excellent

I conducted a comprehensive analysis of FDA-approved kinase inhibitor drugs using the BRIMR database (updated October 2025, 94 total approved inhibitors) and ChEMBL v34 to assess multi-target validation feasibility.

**Candidate kinases for retrospective validation:**

| Kinase | ChEMBL ID | PDB Structures | Approved Drugs (Total) | Post-2010 Drugs | Post-2015 Drugs | Feasibility |
|--------|-----------|---------------|----------------------|----------------|----------------|-------------|
| **ABL1** | CHEMBL1862 | 80+ | 6 (imatinib 2001, dasatinib 2006, nilotinib 2007, ponatinib 2012, bosutinib 2012, asciminib 2021) | 3 | 1 | HIGH |
| **ALK** | CHEMBL4247 | 70+ | 6 (crizotinib 2011, ceritinib 2014, alectinib 2015, brigatinib 2017, lorlatinib 2018, ensartinib 2024) | 6 | 4 | HIGH |
| **BRAF** | CHEMBL5145 | 100+ | 4 (vemurafenib 2011, dabrafenib 2013, encorafenib 2018, tovorafenib 2024) | 4 | 2 | HIGH |
| **RET** | CHEMBL2041 | 30+ | 5 (vandetanib 2011, cabozantinib 2012, lenvatinib 2015, pralsetinib 2020, selpercatinib 2020) | 5 | 2 | MEDIUM |
| **MET** | CHEMBL3717 | 100+ | 2 (capmatinib 2020, tepotinib 2021) | 2 | 2 | MEDIUM |
| **JAK2** | -- | 60+ | 12 (ruxolitinib 2011, tofacitinib 2012, baricitinib 2018, fedratinib 2019, etc.) | 12 | 8 | HIGH |
| **EGFR** (current) | CHEMBL203 | 200+ | 8 (gefitinib 2003, erlotinib 2004, afatinib 2013, osimertinib 2015, dacomitinib 2018, mobocertinib 2021, lazertinib 2024, sunvozertinib 2025) | 5 | 4 | CURRENT |

**Critical time-split considerations:**
- For a pre-2010 cutoff: ABL has imatinib (2001), dasatinib (2006), nilotinib (2007) in training, leaving ponatinib, bosutinib, asciminib as held-out (N=3). ALK has NO pre-2010 drugs (all approved 2011+), meaning the entire set would be held out but no training signal exists. BRAF has NO pre-2010 drugs.
- For a pre-2015 cutoff: ABL has 5 in training, 1 held out. ALK has 2 in training, 4 held out. BRAF has 2 in training, 2 held out.
- **The pre-2015 cutoff is better for multi-kinase validation** because most kinase drugs were approved after 2010.

**Power calculation for pooled multi-kinase analysis:**
- EGFR alone: N_held_out = 5 (pre-2010) or 3 (pre-2015). 95% CI on EF@10 spans ~0.5x to ~8.7x.
- With 5 kinases (EGFR + ABL + ALK + BRAF + RET), pre-2015 split: N_held_out ~ 3+1+4+2+2 = 12 total. CI narrows to roughly 2x-10x for a true 5x enrichment.
- With 6 kinases (adding JAK2): N_held_out ~ 12+8 = 20 total. CI narrows to roughly 3x-8x. This is publishable.
- **Target: 6 kinases, pre-2015 split, N_held_out >= 15. This gives adequate power to distinguish a real enrichment from noise.**

**Relevance to StateBind:** Multi-kinase validation is not optional for a credible publication. EGFR alone with N=5 is a case study. Six kinases with N=20 held-out drugs is a finding. The data exists -- ABL, ALK, BRAF have excellent structural coverage in KLIFS with multiple conformational states annotated.

---

### Finding 5: Data Leakage Risk Assessment

StateBind correctly uses temporal split (training on pre-cutoff data, testing on post-cutoff drugs). This addresses the most common leakage vector. However, several residual risks remain:

**a) Scaffold leakage within the time split:**
Joeres et al. (2025) in "Data splitting to avoid information leakage with DataSAIL" (Nature Communications, 16:3474) showed that even temporal splits can contain high similarity between training and test sets, particularly within well-studied protein families. The held-out EGFR drugs (afatinib, dacomitinib, osimertinib) share the 4-anilinoquinazoline scaffold with gefitinib and erlotinib in the training set. The VAE may have learned this scaffold family during training and "rediscovered" it, which would inflate enrichment without demonstrating true generalization.

**Mitigation:** Compute Tanimoto similarity between generated candidates and the held-out drugs. If the top-ranked candidates are just minor variations of training-set molecules, the enrichment reflects memorization, not generalization. DataSAIL can be used to verify that training/test scaffold overlap is controlled.

**b) Pre-training leakage (potential future risk):**
If StateBind ever adopts a foundation model pre-trained on ChEMBL (e.g., for self-supervised GNN pre-training, Vision Idea 010), the pre-training corpus would contain post-cutoff molecules. Detecting memorization in foundation models is an active research area with no definitive solution (Jiang et al., 2025, ICML).

**c) Reference molecule bias:**
The scoring function uses erlotinib, gefitinib, and osimertinib as reference molecules. Osimertinib is a post-2015 drug. For the pre-2015 validation, the scoring function rewards similarity to a molecule that should be held out. This is a subtle but real form of leakage -- the scoring function has "seen" the answer.

**Relevance to StateBind:** The reference molecule leakage (finding 5c) is the most actionable concern. For any time-split validation, reference molecules should be restricted to pre-cutoff drugs only. For the pre-2010 validation, only erlotinib and gefitinib should serve as references (not osimertinib, approved 2015). This requires re-running the retrospective validation with corrected reference sets. The impact could be significant since osimertinib (a third-generation inhibitor) is structurally distinct from first-generation drugs.

---

### Finding 6: Benchmark Contamination in Molecular ML Is Pervasive

Wallach et al. (2024) in "Coverage bias in small molecule machine learning" (Nature Communications, 15:11389) found that:

- Frequently used datasets (BACE, BBBP, ClinTox, etc.) "fail to uniformly cover biomolecular structures, limiting the predictive power of models trained on them"
- Most datasets cluster in specific regions of chemical space rather than uniformly sampling known biomolecules
- Models perform well on evaluation splits from biased datasets while failing on real-world data

Walters (2023) in "We Need Better Benchmarks for Machine Learning in Drug Discovery" (Practical Cheminformatics blog) identified specific problems with MoleculeNet:
- The BACE dataset has 71% of molecules with undefined stereocenters
- The BBB dataset contains 59 duplicate structures with 10 contradictory labels
- The HIV dataset has 70% of "confirmed actives" triggering structural alert flags

The Polaris benchmarking platform (launched ICML 2024) now provides community-developed guidelines addressing these issues, including:
- Standardized dataset splitting protocols
- Statistical tests for method comparison distinguishing statistical from practical significance
- Chronological data splits for ADMET prediction competitions

**Relevance to StateBind:** StateBind's own datasets (ChEMBL EGFR compounds, TDC ADMET benchmarks) may suffer from coverage bias. The MPNN trained on 10,466 ChEMBL EGFR compounds likely over-represents certain scaffolds. The ADMET model trained on 27,698 TDC molecules inherits whatever biases TDC contains. These are not fatal flaws, but they should be acknowledged in the manuscript and addressed by (a) reporting scaffold diversity of training sets and (b) evaluating model performance on structurally diverse held-out compounds.

---

### Finding 7: The Polaris Method Comparison Guidelines Are the New Standard

The Polaris consortium (AstraZeneca, Pfizer, Novartis, Recursion, etc.) published "Practically significant method comparison protocols for machine learning in small molecule drug discovery" (J Chem Inf Model, 2025, 65:18) establishing that:

- **Statistical significance alone is insufficient.** A statistically significant difference in model performance may not translate to practical differences in drug discovery decisions (e.g., which compounds to synthesize).
- **Effect sizes must be reported.** Raw performance differences should be accompanied by effect size measures to assess practical significance.
- **Multiple dataset evaluation is required.** Claims of method superiority based on a single dataset are inadequate.
- **Proper statistical tests are specified.** The guidelines provide specific protocols for comparing methods, including handling of multiple comparisons.

**Relevance to StateBind:** StateBind's comparison reports many metrics (Mann-Whitney, Cohen's d, bootstrap CI, weight sensitivity). The Polaris guidelines would require:
1. A pre-specified primary endpoint (which metric determines the winner)
2. Effect size reporting alongside p-values (Cohen's d = 1.36 is already reported -- good)
3. Multiple dataset evaluation (currently EGFR only -- needs multi-kinase)
4. Distinction between statistical and practical significance
5. Explicit handling of multiple comparisons across all reported metrics

---

### Finding 8: Multiple Testing Creates a Selective Reporting Risk

StateBind computes at least 12 distinct metrics comparing the two pipelines:

1. Mean unified score (favors static)
2. Max unified score (favors state-aware)
3. Chemical diversity (favors state-aware)
4. Novelty (favors state-aware)
5. Mann-Whitney U test (favors static)
6. Cohen's d (favors static)
7. Bootstrap CI on score difference (favors static)
8. Weight sensitivity (44/56 split, approximately neutral)
9. Pareto hypervolume (favors state-aware)
10. EF@10 pre-2010 (favors state-aware)
11. EF@10 pre-2015 (favors state-aware)
12. EF@50 (not explicitly reported)

Without pre-specification of the primary endpoint, reporting only the metrics that favor one pipeline is a form of p-hacking. The narrative "static wins on mean score but state-aware wins on enrichment" is scientifically honest as reported, but a reviewer would ask: "Which metric is the primary endpoint, and was it chosen before or after seeing the results?"

**Correction approaches:**
- **Bonferroni correction:** For 12 tests at alpha=0.05, the corrected threshold is p < 0.0042. The Mann-Whitney p < 0.001 survives, but many bootstrap CIs would not.
- **Benjamini-Hochberg FDR control:** More appropriate for exploratory analyses. Controls the expected proportion of false discoveries rather than the family-wise error rate. Recommended for this setting since the study is partly exploratory.
- **Pre-registration:** Specify enrichment factor (or BEDROC) as the primary endpoint and all other metrics as secondary/exploratory BEFORE running multi-kinase experiments. This eliminates the multiple testing problem for the primary claim.

**Relevance to StateBind:** The manuscript must either (a) pre-specify a single primary endpoint and report all others as secondary, or (b) apply multiple testing correction across all reported metrics, or (c) frame the study as exploratory with no definitive claim. Option (a) is strongest for publication.

---

### Finding 9: QSAR Validation Best Practices Demand External Validation

Tropsha (2010) in "Best Practices for QSAR Model Development, Validation, and Exploitation" (Mol Informatics, 29:476-488) established the gold standard:

- Internal validation (cross-validation, LOO) is **necessary but not sufficient**
- Golbraikh and Tropsha (2002) proved that LOO cross-validated R^2 (q^2) shows "no correlation" with predictive accuracy on external data
- External validation on rationally selected, structurally diverse test sets is the minimum standard
- Y-scrambling (randomizing response variable) should produce models with "significantly lower R^2 and Q^2 than the original model"
- Applicability domain must be defined -- predictions outside the domain carry no confidence

**StateBind's validation hierarchy:**
| Level | Description | StateBind Status |
|-------|-------------|-----------------|
| 0 | No validation | -- |
| 1 | Internal (CV, bootstrap) | MPNN R^2=0.69, ADMET AUROC=0.77 |
| 2 | Temporal split | EF@10 = 4.95/7.72 (current) |
| 3 | External (new target) | NOT YET DONE |
| 4 | Prospective (synthesize + test) | NOT FEASIBLE |

Moving from Level 2 to Level 3 (multi-kinase) is the highest-impact step. It transforms the result from a single case study to a generalizable finding. Level 4 (prospective) requires wet-lab resources not available to this project.

**Relevance to StateBind:** The MPNN (R^2=0.69) and ADMET models have only been validated internally and on a single target. Multi-kinase extension would constitute external validation and dramatically strengthen the ML component claims.

---

### Finding 10: Kinase Conformational State Data Supports Multi-Target Extension

Backenkoehler et al. (2024) in "A comprehensive exploration of the druggable conformational space of protein kinases" (PLoS Comput Biol, 20:e1012302) analyzed 497 human kinases:

- 5,136 PDB structures across 331 kinases with experimentally determined structures
- 6 conformational classifications (CIDI, CIDO, CODI, CODO, DFGinter, unassigned)
- PDB structural distribution: 65.7% CIDI (active), demonstrating strong bias toward active conformations
- Only 37 kinases were determined in 3 or more conformational states
- ABL1 specifically: 27 DFG-out structures, 9 DFG-in, 16 intermediate -- excellent conformational coverage
- BRAF: found in all five conformations -- also excellent
- Ligand enrichment for AI-predicted structures: average AUC 64.58 (SD 17.27)

For StateBind's multi-kinase extension, the kinases with best conformational coverage (multiple states represented in crystal structures) are:

| Priority | Kinase | States in PDB | Structures | Suitability |
|----------|--------|--------------|------------|-------------|
| 1 | ABL1 | 3+ (DFGin, DFGout, intermediate) | 80+ | Excellent |
| 2 | BRAF | 5 (all states) | 100+ | Excellent |
| 3 | ALK | 2+ (DFGin, DFGout) | 70+ | Good |
| 4 | JAK2 | 2+ | 60+ | Good |
| 5 | MET | 2+ | 100+ | Good |
| 6 | RET | 2 | 30+ | Adequate |

**Relevance to StateBind:** ABL and BRAF are the strongest candidates for multi-kinase extension because they have excellent conformational state coverage (3+ states in crystal structures), multiple approved drugs for retrospective validation, and abundant ChEMBL bioactivity data for MPNN retraining. ALK is third priority despite having the most held-out drugs (6 post-2010) because its conformational coverage is more limited.

---

### Finding 11: Cross-Docking Studies Validate Multi-Conformation Approaches

Clyde et al. (2024) in "Benchmarking Cross-Docking Strategies in Kinase Drug Discovery" (J Chem Inf Model) evaluated 589 kinase structures across 10 kinases:

- Using multiple structures for docking improved success rates from ~33% (single structure) to ~83% (50 structures)
- Ensemble docking with Surflex improved overall ROCAUC from 0.815 to 0.841 (p=0.04)
- Kinase conformational state could be identified from docking scores in 76-97% of cases
- Enrichment factor improved 1.85-fold (SD 0.65) when using 2-3 conformations vs single structure

Grasso et al. (2024) in "Improving docking and virtual screening performance using AlphaFold2 multi-state modeling" (Scientific Reports) found that multi-state docking with diverse conformations improved enrichment for kinase targets.

**Relevance to StateBind:** Published cross-docking studies report enrichment improvements of ~1.5-2x from multi-conformation docking. StateBind claims ~10x from state-aware design. If the cross-docking literature shows 2x and StateBind shows 10x, the excess enrichment (5x) is either (a) a remarkable result from state-conditioned generation beyond simple multi-conformation docking, or (b) an artifact of the confounded comparison. The ablation study (Finding 3) would distinguish these hypotheses.

---

### Finding 12: Bootstrap CI Methods for Ratio Statistics

The enrichment factor is a ratio statistic with a small denominator (N_actives). Standard bootstrap methods (percentile, BCa) have known problems with ratio statistics because the denominator can be zero or near-zero in bootstrap resamples.

**Recommended approach for StateBind:**

1. **Stratified bootstrap:** Resample candidates while maintaining the number of actives (stratified by active/inactive label). This prevents bootstrap samples with zero actives.
2. **BCa (bias-corrected and accelerated) intervals:** DiCiccio and Efron (1996) showed BCa intervals are second-order accurate for ratio statistics.
3. **Permutation test for between-pipeline comparison:** Under H0: no difference between pipelines, randomly reassign pipeline labels and recompute EF@10 10,000 times to construct the null distribution.
4. **Bayesian estimation:** Place a Beta prior on the proportion of actives in the top k%, update with observed data, and compute posterior credible intervals. With N=5 actives, a weakly informative Beta(1,1) prior gives a posterior Beta(n_in_top + 1, 5 - n_in_top + 1), yielding credible intervals for EF.

**Specific implementation for StateBind:**
```
# Pseudocode for stratified bootstrap CI on EF@10
For b = 1 to 10,000:
    Resample 461 candidates with replacement (stratified: keep 5 actives, 456 inactives)
    Re-rank by unified score
    Compute EF@10_b
Return [EF@10_(250), EF@10_(9750)] as 95% CI
```

**Expected CI width:** For EF@10 = 4.95 with N_actives = 5, the bootstrap 95% CI will be approximately [1.0, 9.9] (rough estimate based on binomial uncertainty). This is wide but may exclude 1.0 (random), which would be statistically significant even if imprecise.

**Relevance to StateBind:** Bootstrap CIs must be computed and reported for every enrichment claim. The BCa method with stratified resampling is recommended. If the lower bound of the 95% CI exceeds 1.0, the enrichment is statistically significant. If it does not, the claim requires more data (i.e., multi-kinase validation).

---

### Finding 13: The Mean Score vs Enrichment Tension Is a Calibration Problem

StateBind retains the null hypothesis on mean unified score (static: 0.5437 vs state-aware: 0.4378, p < 0.001 favoring static). But the enrichment factor strongly favors state-aware. This is not a contradiction -- it reveals that the scoring function is miscalibrated for the task of prospective drug identification.

**Statistical interpretation:**
- The scoring function was designed to rank candidates by drug-likeness, similarity, and docking. It does this well -- the static baseline's 30 candidates, which are close modifications of known drugs, score highest.
- The enrichment metric asks a different question: do future drugs appear near the top? The state-aware pipeline's 461 diverse candidates include molecules that resemble future drugs but score lower on average because they are less similar to the 3 reference molecules.
- This is analogous to the precision-recall trade-off: the static pipeline has high precision (high mean score) but low recall (misses future drugs). The state-aware pipeline has lower precision but higher recall.

**The weight sensitivity analysis supports this interpretation:** With 100 random Dirichlet weight combinations, 56% favor static and 44% favor state-aware. The result is weight-dependent, which is not a bug -- it shows that the two pipelines optimize different objectives. The enrichment metric is the more relevant objective for drug discovery.

**Relevance to StateBind:** The manuscript should frame this not as a contradiction but as an expected consequence of the precision-recall trade-off. The primary claim should be about enrichment (with CIs), and the mean score comparison should be presented as evidence that the scoring function rewards similarity over novelty. This reframing is honest and strengthens the narrative.

---

### Finding 14: Pre-Registration Protocol for Multi-Kinase Experiments

Based on the literature review, I propose the following pre-registered analysis plan:

**Primary endpoint:** BEDROC(alpha=20) averaged across all kinase targets, comparing state-aware vs static pipelines.

**Secondary endpoints:**
1. EF@10 averaged across targets
2. Per-target BEDROC with 95% BCa bootstrap CI
3. Mean unified score comparison with Cohen's d
4. Pareto hypervolume ratio

**Success criterion (specified a priori):**
- Primary: Mean BEDROC(alpha=20) for state-aware exceeds static by >= 0.1 units (one-sided paired t-test across targets, alpha = 0.05)
- If 6 targets are used, the power to detect a BEDROC difference of 0.1 with SD = 0.08 is approximately 80% (paired t-test, df=5)

**Multiple testing correction:**
- Primary endpoint: No correction needed (single pre-specified test)
- Secondary endpoints: Benjamini-Hochberg FDR control at q = 0.05
- Exploratory metrics: Reported without correction, labeled as exploratory

**Exclusion criteria (specified a priori):**
- Targets with fewer than 2 held-out drugs are excluded from primary analysis
- Targets where no conformational state annotations exist in KLIFS are excluded
- Molecules with undefined stereochemistry are excluded from enrichment calculations

**Relevance to StateBind:** This pre-registration protocol eliminates the selective reporting concern and makes the multi-kinase study publishable regardless of outcome. A negative result (state-aware does not outperform) would also be publishable as a rigorous null finding.

---

### Finding 15: Causal Inference Framework for Method Comparison

Bender et al. (2023) in "Causal inference in drug discovery and development" (Drug Discovery Today, 28:103737) argued that causal inference can "reduce cognitive bias and improve decision making in drug discovery." Applied to StateBind's method comparison:

**The causal question:** Does state-awareness (the treatment) cause improved enrichment (the outcome)?

**Directed Acyclic Graph (DAG):**
```
State awareness -> Generation diversity -> Candidate count -> Enrichment
State awareness -> State specificity score -> Enrichment
Generation method (VAE vs template) -> Generation diversity -> Enrichment
Generation method -> Candidate count -> Enrichment
```

**Confounders on the causal path:** Generation method and candidate count are confounders that create backdoor paths from state awareness to enrichment. The ablation design (Finding 3) closes these backdoor paths by holding each confounder constant in turn.

**The key experiment:** Ablation C (unconditioned VAE, ~400 candidates) vs Experiment B (state-conditioned VAE, ~461 candidates). If the difference B - C is statistically significant, state-conditioning has a causal effect on enrichment beyond what diverse generation alone provides. If B - C is not significant, the VAE diversity is the causal driver, not state information.

**Relevance to StateBind:** Framing the ablation study in causal inference terms (isolating the treatment effect of state awareness by controlling for confounders) would resonate with reviewers at methods-focused venues (Nature Computational Science, JCIM). It demonstrates methodological sophistication beyond simple metric comparison.

---

## Implications for StateBind

### Opportunities

1. **Multi-kinase validation is the highest-ROI experiment.** The data exists. ABL, ALK, BRAF, RET, JAK2 all have approved drugs, structural coverage, and ChEMBL bioactivity data. Extending to 6 targets would (a) increase held-out drugs from 5 to ~20, (b) narrow enrichment CIs to publishable precision, (c) demonstrate generalization, and (d) constitute external validation for the ML models.

2. **BEDROC adoption differentiates from the literature.** Most virtual screening papers still report EF without CIs. Reporting BEDROC with bootstrap CIs and multiple testing correction would place StateBind at the frontier of methodological rigor.

3. **The ablation study is cheap and decisive.** Training an unconditioned VAE (same architecture, same data, no state vector) takes one H200 GPU day. The result either strengthens the thesis (state-conditioning contributes significantly) or redirects it (diversity drives enrichment, state-conditioning is secondary). Either outcome is publishable.

4. **Pre-registration makes ANY outcome publishable.** A well-designed multi-kinase study with pre-registered endpoints is valuable whether the result is positive, negative, or mixed. This eliminates publication risk.

5. **The Polaris framework provides ready-made credibility.** Aligning the comparison methodology with Polaris guidelines signals awareness of community standards and increases reviewer confidence.

### Risks and Caveats

1. **The 10x enrichment may not survive bootstrap CIs.** If the lower bound of the 95% CI includes 1.0, the headline result is not statistically significant. This is a real possibility with N=5.

2. **The ablation study could kill the thesis.** If unconditioned VAE generation matches state-conditioned generation on enrichment, the state-awareness claim collapses. The paper would need to pivot to "diverse generative design outperforms template-based design" -- still publishable but a different story.

3. **Reference molecule leakage (osimertinib in pre-2015 validation) may reduce enrichment when corrected.** Removing osimertinib from reference molecules changes the scoring function, potentially reducing the enrichment gap.

4. **Multi-kinase extension requires retraining MPNNs per target.** Each kinase needs its own MPNN trained on target-specific ChEMBL data, its own docking setup (receptor preparation, grid definition), and its own conformational state atlas. This is significant engineering effort (weeks, not days).

5. **Some kinases may not show conformational state effects.** Not all kinases have equally druggable conformational diversity. The state-aware advantage may be EGFR-specific (EGFR has well-characterized type I/II/III/IV binding modes). A null result on some targets is expected and should be planned for.

### Recommended Next Steps (Prioritized)

1. **IMMEDIATE (1-2 days):** Compute bootstrap CIs (BCa, 10,000 resamples) on all current enrichment metrics. Report BEDROC(alpha=20) alongside EF@10. Fix reference molecule leakage by re-running pre-2015 validation without osimertinib as reference.

2. **SHORT-TERM (1-2 weeks):** Run the ablation study (Experiments C, D, E from Finding 3). Train unconditioned VAE. Generate candidates. Compute enrichment. This determines whether state-conditioning is the driver or diversity is the driver.

3. **MEDIUM-TERM (2-4 weeks):** Extend to ABL and BRAF (highest priority multi-kinase targets). Prepare conformational state atlases, retrain MPNNs, run retrospective validation with pre-registered endpoints.

4. **LONGER-TERM (1-2 months):** Complete multi-kinase validation on 4-6 additional targets. Compile final results with pooled enrichment analysis, per-target breakdowns, and ablation comparison.

5. **PUBLICATION PREP:** Write manuscript targeting Nature Computational Science or JCIM. Frame as "Conformational state-aware molecular design: a multi-kinase retrospective validation" with pre-registered primary endpoint (BEDROC), ablation controls, and honest reporting of all metrics including those favoring static.

---

## References

1. Truchon JF, Bayly CI. Evaluating Virtual Screening Methods: Good and Bad Metrics for the "Early Recognition" Problem. J Chem Inf Model. 2007;47(2):488-508.

2. Empereur-mot C, Guillemain H, Latouche A, et al. Confidence bands and hypothesis tests for hit enrichment curves. J Cheminformatics. 2022;14:48. PMC9334420.

3. Clark RD, Webster-Clark DJ. The power metric: a new statistically robust enrichment-type metric for virtual screening applications with early recovery capability. J Cheminformatics. 2016;8:1-17.

4. Nicholls A. The statistics of virtual screening and lead optimization. J Comput-Aided Mol Des. 2016;30:1205-1213.

5. Tropsha A. Best Practices for QSAR Model Development, Validation, and Exploitation. Mol Informatics. 2010;29(6-7):476-488.

6. Golbraikh A, Tropsha A. Rational selection of training and test sets for the development of validated QSAR models. J Comput-Aided Mol Des. 2003;17:241-253.

7. Joeres R, et al. Data splitting to avoid information leakage with DataSAIL. Nature Communications. 2025;16:3474. PMC11978981.

8. Wallach I, et al. Coverage bias in small molecule machine learning. Nature Communications. 2024;15:11389. PMC11718084.

9. Walters WP. We Need Better Benchmarks for Machine Learning in Drug Discovery. Practical Cheminformatics. 2023. Blog post.

10. Polaris Consortium. Practically significant method comparison protocols for machine learning in small molecule drug discovery. J Chem Inf Model. 2025;65(18).

11. Bender A, et al. Causal inference in drug discovery and development. Drug Discovery Today. 2023;28(10):103737.

12. Backenkoehler M, et al. A comprehensive exploration of the druggable conformational space of protein kinases using AI-predicted structures. PLoS Comput Biol. 2024;20:e1012302.

13. Clyde A, et al. Benchmarking Cross-Docking Strategies in Kinase Drug Discovery. J Chem Inf Model. 2024.

14. Wu Z, et al. MoleculeNet: a benchmark for molecular machine learning. Chem Sci. 2018;9:513-530.

15. DiCiccio TJ, Efron B. Bootstrap confidence intervals. Statistical Science. 1996;11(3):189-228.

16. Gu R, et al. Target-aware 3D molecular generation based on guided equivariant diffusion. Nature Communications. 2025;16:3169.

17. Roskoski R. Properties of FDA-approved small molecule protein kinase inhibitors: A 2025 update. Pharmacol Res. 2025;204:107083.

18. Modi V, Dunbrack RL. Defining a new nomenclature for the structures of active and inactive kinases. PNAS. 2019;116(14):6818-6827.

19. Grasso M, et al. Improving docking and virtual screening performance using AlphaFold2 multi-state modeling for kinases. Scientific Reports. 2024;14:24305.

20. Vass M, et al. KLIFS: A Knowledge-Based Structural Database To Navigate Kinase-Ligand Interaction Space. J Med Chem. 2013;56(16):6914-6924.

21. Empereur-mot C, et al. Predictivity of virtual screening tools: a practical guide for new users. J Chem Inf Model. 2015;55(10):2003-2028.

22. Cherkasov A, et al. QSAR modeling: where have you been? Where are you going to? J Med Chem. 2014;57(12):4977-5010.

23. Irwin JJ, et al. An Aggregation Advisor for Ligand Discovery. J Med Chem. 2015;58(17):7076-7087.

24. Huang R, et al. A statistical framework to evaluate virtual screening. BMC Bioinformatics. 2009;10:225.

25. Benjamini Y, Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. J Royal Statistical Society B. 1995;57(1):289-300.

---

## Appendix A: Complete Time-Split Drug Assignment by Kinase

For the recommended pre-2015 cutoff, the following drug assignments apply:

**Training set (approved <= 2014):**
- EGFR: gefitinib (2003), erlotinib (2004), afatinib (2013)
- ABL: imatinib (2001), dasatinib (2006), nilotinib (2007), ponatinib (2012), bosutinib (2012)
- ALK: crizotinib (2011), ceritinib (2014)
- BRAF: vemurafenib (2011), dabrafenib (2013)
- RET: vandetanib (2011), cabozantinib (2012)
- JAK: ruxolitinib (2011), tofacitinib (2012)

**Held-out set (approved >= 2015):**
- EGFR: osimertinib (2015), dacomitinib (2018), lazertinib (2024) = 3 drugs
- ABL: asciminib (2021) = 1 drug
- ALK: alectinib (2015), brigatinib (2017), lorlatinib (2018), ensartinib (2024) = 4 drugs
- BRAF: encorafenib (2018), tovorafenib (2024) = 2 drugs
- RET: lenvatinib (2015), pralsetinib (2020), selpercatinib (2020) = 3 drugs
- JAK: baricitinib (2018), fedratinib (2019), upadacitinib (2019), pacritinib (2022), etc. = 8+ drugs

**Total held-out (6 kinases, pre-2015 cutoff): ~21 drugs**

This gives approximately 4x more statistical power than EGFR alone (N=5 vs N=21).

## Appendix B: Estimated CI Widths by Sample Size

| N (held-out drugs) | EF@10 Point Estimate | Approximate 95% CI Width | Interpretation |
|---------------------|---------------------|--------------------------|----------------|
| 3 | 7.72 | [0.8, 14.6] | Uninformative |
| 5 | 4.95 | [0.5, 9.4] | Very wide, marginal significance |
| 10 | 4.95 | [1.8, 8.1] | Starting to be useful |
| 15 | 4.95 | [2.5, 7.4] | Moderate precision |
| 20 | 4.95 | [3.0, 6.9] | Publishable precision |
| 30 | 4.95 | [3.3, 6.6] | Good precision |

*CI widths are rough estimates assuming binomial variance for the proportion of actives in the top 10%, translated to EF scale. Actual bootstrap CIs will differ but magnitudes are representative.*

The table demonstrates that reaching N >= 15 held-out drugs through multi-kinase validation is necessary for a credible enrichment claim. EGFR alone (N=3-5) cannot provide this.

---

*This research note was produced by the Maverick Data Scientist / Statistician agent as part of IdeationDept Round 1. All statistical claims are computational analyses of published data. No code was executed or modified.*
