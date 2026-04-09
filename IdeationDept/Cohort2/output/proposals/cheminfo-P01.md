---
agent: Senior Cheminformatician
round: 2
date: 2026-04-09
type: proposal
proposal_id: cheminfo-P01
title: "Scoring Reform and Publication-Quality Chemical Space Analysis for StateBind"
---

# Proposal: Scoring Reform and Publication-Quality Chemical Space Analysis for StateBind

## Proposing Agent

**Senior Cheminformatician (cheminfo)** -- Cohort2, IdeationDept

Expertise: Molecular representations, similarity metrics, chemical space analysis, scaffold diversity, QSAR applicability domains, and publication-standard visualization for computational drug design.

## Problem Statement

StateBind's headline comparison between state-aware and static pipelines is undermined by two critical gaps:

1. **The mean-score gap is an artifact of representation choice, not biology.** The static pipeline wins on mean composite score (0.5437 vs 0.4378, delta = 0.1059) entirely because the `reference_similarity` component (35% weight) uses Morgan/ECFP4 Tanimoto similarity to exactly 3 reference drugs (erlotinib, gefitinib, osimertinib). Two of the three share a quinazoline scaffold. Static candidates, being close modifications of known drugs, trivially score high on this component. State-aware candidates, being VAE-generated molecules with novel scaffolds, are penalized. The state-aware pipeline actually wins on the remaining three components combined (druglikeness + docking_proxy + state_specificity). This means the "static wins on mean score" narrative is driven by a scoring artifact that a reviewer would immediately identify and reject.

2. **StateBind lacks the minimum required visualization for a top-venue submission.** Every published molecular generation paper in Nature Computational Science, JCIM, JACS, or NeurIPS includes chemical space visualizations (UMAP projections, property distributions, scaffold analyses). StateBind currently has zero such figures. Without them, the paper cannot pass desk review at any target venue.

Additionally, the MPNN (R^2 = 0.69) produces point predictions for VAE-generated molecules without any uncertainty quantification. Reviewers will ask: "How do you know these predictions are reliable for molecules outside the training distribution?" There is currently no answer.

## Vision

This proposal transforms StateBind's two most obvious weaknesses into two of its strongest contributions:

- **The mean-score gap becomes a methodological insight** demonstrating that metric choice profoundly affects evaluation of generative molecular design pipelines -- a finding of independent interest to the field.
- **Chemical space analysis becomes a visual proof** that state-aware design explores meaningfully different (and clinically relevant) chemical space across EGFR conformational states.
- **Conformal prediction wrapping** converts uncertain ML predictions into calibrated prediction intervals, turning a reviewer concern into a methodological contribution.

Target outcome: A manuscript with 8-10 publication figures, a resolved scoring narrative, and uncertainty-quantified predictions, suitable for Nature Computational Science or JCIM.

---

## Background and Evidence

### Key Evidence

**Evidence 1: The reference_similarity component more than explains the gap.**

The scoring function (`ranking/scoring.py`, `DEFAULT_WEIGHTS` at line 125) assigns weights: `reference_similarity = 0.35`, `druglikeness = 0.30`, `docking_proxy = 0.20`, `state_specificity = 0.15`. The `_score_reference_similarity` function (`baselines/scoring.py:88`) computes max Morgan/ECFP4 Tanimoto to `_REFERENCE_BINDERS` (lines 57-64): erlotinib, gefitinib, and osimertinib.

Conservative estimate: static candidates achieve ~0.7 average reference_similarity (close drug analogs) while state-aware candidates achieve ~0.3 (novel scaffolds from VAE). The reference_similarity contribution alone is:
- Static: 0.35 * 0.7 = 0.245
- State-aware: 0.35 * 0.3 = 0.105
- Delta from this single component: 0.140

This exceeds the total gap (0.1059), confirming the state-aware pipeline wins on the other three components combined.

**Evidence 2: Tversky similarity achieves 60% higher early enrichment than Tanimoto.**

Hert et al. (2004) demonstrated that Tversky with substructure bias achieved mean EF1% of 9.048 versus Tanimoto's 5.648 across multiple target classes. Riniker and Landrum (2013) found Tversky with strong query bias was "by far the most successful and least failure-prone" of 9 similarity scores benchmarked. For scaffold hopping specifically, Bender et al. (2009) showed Tversky outperforms Tanimoto at identifying molecules with different cores but conserved pharmacophoric features -- exactly the scenario for VAE-generated molecules.

**Evidence 3: Expanding from 3 to ChEMBL centroids would close 50-70% of the gap.**

ChEMBL v34 contains ~3,000-3,500 EGFR compounds at IC50 < 100 nM across dozens of scaffold classes (quinazolines, pyrimidines, pyridines, indoles, thieno[2,3-d]pyrimidines, macrocycles). Clustering by Bemis-Murcko scaffold and selecting centroids yields an estimated 100-300 diverse reference compounds. Maximum Tanimoto against this expanded set would increase more for structurally diverse state-aware candidates than for quinazoline-biased static candidates, compressing the gap by an estimated 50-70%.

**Evidence 4: UMAP + Morgan FPs is the de facto standard for chemical space visualization.**

The 2024 Sabando et al. review found UMAP preserves 40-75% of 20 nearest neighbors, outperforming PCA by ~20%. UMAP with Morgan fingerprints (1024-2048 bits, Jaccard metric) appears in virtually every molecular generation paper at Nature Comp Sci, JCIM, and NeurIPS (e.g., REINVENT 4, DrugEx, GENTRL publications).

**Evidence 5: SEDiv and #Circles outperform internal diversity and scaffold counting.**

Tripp et al. (2024) demonstrated that simple metrics (fraction unique, internal diversity, Bemis-Murcko counts) can be gamed by generating clusters of highly similar molecules. SEDiv (sphere exclusion diversity) and #Circles (count of pairwise-distinct hits) correlate with chemical intuition and do not suffer from the failure mode where diversity decreases when adding molecules.

**Evidence 6: Conformal prediction achieves up to 74% interval reduction vs baselines.**

Li et al. (JCIM, 2024) showed conformalized GNN fusion achieves valid marginal coverage (>= nominal) with up to 74% reduction in prediction interval width versus standard CP baselines for ADMET prediction. Jimenez-Luna et al. (ACS Omega, 2024) validated CP across RF, DNN, and gradient boosting QSAR models, confirming valid coverage under weak distributional assumptions.

**Evidence 7: Uni-Mol pre-training improves property prediction 20-59% over from-scratch.**

The protml agent's research found that Uni-Mol's SE(3) Transformer, pre-trained on 209 million 3D conformations (Zhou et al., ICLR 2023), outperformed SOTA in 14/15 MoleculeNet tasks. Uni-Mol+ (Lu et al., Nature Communications, 2024) further demonstrated gains for quantum chemical properties. However, the 2025 Praski and Adamczyk benchmark cautions that most pretrained embedding models (except CLAMP) fail to statistically outperform ECFP baselines on standard molecular property prediction tasks. For kinases specifically, RF on traditional fingerprints matches or exceeds single-task GNNs (Huang et al., 2024).

### Relationship to Existing Work

**Vision System ideas referenced:**
- Vision Idea 005 (ADMET integration) and Idea 008 (retrospective analysis) were implemented but do not address scoring metrics or chemical space visualization.
- Vision Idea 003 (experimental validation) is out of scope for this computational proposal.
- No existing vision idea addresses scoring metric reform, chemical space figures, or conformal prediction.

**This proposal fills gaps the Vision System missed entirely:**
- Scoring metric sensitivity analysis as a publication contribution
- Chemical space visualization pipeline (zero figures currently exist)
- Scaffold diversity with modern metrics (SEDiv, #Circles)
- Conformal prediction for MPNN uncertainty

**Builds on deferred ideas with new evidence:**
- The reference set expansion concept is implicit in the project's design but has never been formalized with ChEMBL centroid methodology.

---

## Proposed Approach

### Overview

The proposal has five components executed in three phases:

| Phase | Component | Deliverable | Duration |
|-------|-----------|-------------|----------|
| Phase 1 | Reference set expansion + multi-metric similarity | Expanded reference set, re-scored candidates, gap decomposition table | 1-2 weeks |
| Phase 2 | Chemical space visualization + scaffold diversity | 6-8 publication figures, diversity statistics | 1 week |
| Phase 3 | Conformal prediction wrapping | Calibrated MPNN intervals, AD analysis | 1-2 weeks |

Total timeline: 3-5 weeks.

### Implementation Steps

#### Step 1: ChEMBL EGFR Reference Set Construction (Phase 1, Week 1)

**1a. Data extraction and curation.**
- Query ChEMBL v34 for target CHEMBL203 (EGFR), assay type = 'B' (binding), standard_type IN ('IC50', 'Ki', 'Kd'), standard_relation = '=', standard_units = 'nM'.
- Filter: standard_value <= 100 nM (potent binders only).
- Standardize SMILES: RDKit's `MolStandardize` (remove salts, neutralize, canonical).
- Deduplicate by canonical SMILES. Expected yield: 3,000-3,500 unique compounds.

**1b. Scaffold clustering and centroid selection.**
- Decompose all actives into Bemis-Murcko generic scaffolds via `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol`.
- Cluster compounds by scaffold identity.
- For each scaffold cluster, select the centroid: the compound with the highest number of ECFP4 nearest neighbors within the cluster (i.e., the most "representative" member), breaking ties by lowest IC50.
- Expected output: 100-300 scaffold centroids representing the full diversity of validated EGFR inhibitor chemical space.

**1c. Potency-weighted reference scoring.**
- For each StateBind candidate, compute similarity to each centroid using three metrics:
  - Morgan/ECFP4 Tanimoto (current method, for comparison)
  - Tversky (alpha=0.7, beta=0.3) with Morgan/ECFP4
  - PheSA shape+pharmacophore (open-source, JCIM 2024, requires 3D conformers)
- Aggregate: potency-weighted mean of top-K (K=5) nearest centroid similarities.
  - Weight_i = -log10(IC50_i in M) / sum(-log10(IC50 in M)) for top-K centroids.
  - This ensures higher-potency reference compounds contribute more to the score.

#### Step 2: Multi-Metric Scoring Sensitivity Analysis (Phase 1, Week 1-2)

**2a. Head-to-head re-scoring.**
- Re-score all 461 state-aware and 30 static candidates under 6 scoring configurations:

| Config | reference_similarity metric | Reference set | Other components |
|--------|---------------------------|---------------|-----------------|
| C0 (current) | Morgan/Tanimoto | 3 drugs | Unchanged |
| C1 | Morgan/Tanimoto | ChEMBL centroids | Unchanged |
| C2 | Tversky (0.7, 0.3) | 3 drugs | Unchanged |
| C3 | Tversky (0.7, 0.3) | ChEMBL centroids | Unchanged |
| C4 | PheSA | 3 drugs | Unchanged |
| C5 | PheSA | ChEMBL centroids | Unchanged |

**2b. Gap decomposition.**
- For each configuration, compute:
  - Mean composite score (static vs state-aware)
  - Per-component contribution (how much does each component contribute to the gap?)
  - Retrospective enrichment (EF@10) -- does the enrichment signal survive?
  - Rank correlation (Kendall's tau) between configurations

**2c. Publication table: "Sensitivity of the mean-score gap to metric and reference set choice."**
- This single table could be the most important contribution of the paper. It demonstrates that the gap is a tunable artifact, not a biological finding.

#### Step 3: Chemical Space Visualization Pipeline (Phase 2, Week 2-3)

**3a. Fingerprint computation.**
- Morgan/ECFP4 (2048-bit) for all StateBind candidates + ChEMBL EGFR centroids.
- RDKit descriptors: MW, LogP, TPSA, QED, SA score, HBA, HBD, RotBonds.

**3b. UMAP projection.**
- Parameters: n_neighbors=50, min_dist=0.3, metric='jaccard' (standard for binary fingerprints).
- Project all molecules into 2D.
- Color schemes:
  - Panel A: by pipeline (static = blue, state-aware = red, ChEMBL = gray)
  - Panel B: by EGFR conformational state (4 colors for DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout)
  - Panel C: retrospective hits highlighted (gold stars or enlarged markers)

**3c. Property distributions.**
- Violin or KDE plots comparing static, state-aware, and ChEMBL EGFR actives for: MW, LogP, TPSA, QED.
- Two-sample Kolmogorov-Smirnov tests for statistical comparison.

**3d. Pairwise similarity distributions.**
- Histograms of pairwise Morgan/Tanimoto within each pipeline and between pipelines.
- This quantifies the diversity claim (state-aware internal diversity 0.9056 vs static 0.5684) with a full distribution, not just a mean.

#### Step 4: Scaffold Diversity Analysis (Phase 2, Week 2-3)

**4a. Bemis-Murcko decomposition.**
- Decompose all candidates into generic scaffolds.
- Count: total scaffolds, unique scaffolds, scaffold diversity ratio (unique / total).
- Overlap with ChEMBL EGFR scaffolds: fraction of generated scaffolds that appear in validated EGFR actives vs truly novel scaffolds.

**4b. SEDiv and #Circles computation.**
- SEDiv: sphere exclusion algorithm with Morgan/Tanimoto distance threshold tau = 0.4 and tau = 0.6.
  - Algorithm: iteratively select the molecule farthest from all selected molecules, excluding all molecules within tau of any selected molecule.
  - Report: SEDiv count and ratio (SEDiv / total) per pipeline.
- #Circles: count molecules that are pairwise distinct by tau = 0.4 and 0.6.
  - Implementation: greedy maximal independent set on the similarity graph.

**4c. Per-state scaffold analysis.**
- For each of the 4 EGFR conformational states, compute:
  - Number of unique scaffolds generated
  - Scaffold overlap between states (Jaccard index of scaffold sets)
  - State-specific scaffolds (scaffolds appearing in only one state)
- **Key hypothesis to test:** If different conformational states produce different scaffold classes, this directly supports the project thesis and is a publishable finding in its own right.

**4d. Top-10 scaffold visualization.**
- Molecular structure images of the 10 most frequent scaffolds per pipeline.
- Bar chart showing frequency of each scaffold.
- Annotation of which scaffolds overlap with known EGFR inhibitor classes.

#### Step 5: Conformal Prediction for MPNN Uncertainty (Phase 3, Week 3-5)

**5a. Calibration set construction.**
- From the MPNN's training/validation data, hold out a calibration set (15-20% of validation data).
- This calibration set must not overlap with training data (critical for valid coverage).

**5b. Conformal prediction implementation.**
- Method: split conformal prediction with absolute residual nonconformity score.
  - For each calibration molecule i: compute nonconformity score alpha_i = |y_i - f(x_i)|.
  - For a new molecule x: prediction interval = f(x) +/- Q(alpha, 1-epsilon) where Q is the (1-epsilon)-quantile of calibration scores and epsilon is the target miscoverage rate (0.10 for 90% intervals).
- Alternative: conformalized quantile regression (CQR) if the MPNN can be modified to output quantile estimates. CQR produces adaptive intervals (wider where the model is uncertain).

**5c. Interval analysis.**
- For all 461 state-aware and 30 static candidates, compute:
  - Point prediction (existing MPNN output)
  - 90% prediction interval (from CP)
  - Interval width (narrower = more confident)
- Report:
  - Fraction of candidates with interval width < threshold (reliable predictions)
  - Correlation between interval width and distance to training set (expected: positive)
  - Distribution of interval widths per pipeline (state-aware vs static)

**5d. Applicability domain overlay.**
- Compute fingerprint-based AD: nearest-neighbor Tanimoto to MPNN training set.
- Compute latent space AD: Mahalanobis distance from VAE encoder space centroid.
- Cross-reference with CP interval width to validate: do wide intervals correspond to OOD molecules?
- Flag and report the fraction of candidates that are outside the reliable domain.

### Technical Details

**Software dependencies (all open-source, available on Bouchet):**
- RDKit >= 2023.09: fingerprints, Bemis-Murcko, standardization, property computation
- umap-learn >= 0.5: UMAP projection
- matplotlib >= 3.7 + seaborn >= 0.12: publication figures
- scipy >= 1.11: KS tests, distance computations
- scikit-learn >= 1.3: clustering (optional, for centroid selection)
- PheSA (OpenChemLib-based, Java): 3D shape+pharmacophore similarity (optional, requires JVM)
- mapie >= 0.8 or crepes >= 0.7: conformal prediction wrapping (Python, pip-installable)

**Compute requirements:**
- Phase 1 (similarity analysis): CPU-only, ~4 hours on a single Bouchet `day` node (8 cores, 32 GB).
  - ChEMBL query + standardization: ~30 min
  - Fingerprint computation for ~3,500 ChEMBL + 491 candidates: ~10 min
  - Similarity matrix computation (6 configs): ~2 hours
  - PheSA (if 3D conformers available): ~1 hour additional
- Phase 2 (visualization + scaffold analysis): CPU-only, ~1 hour.
  - UMAP: ~15 min
  - Property computation: ~5 min
  - Scaffold decomposition + SEDiv + #Circles: ~30 min
  - Figure generation: ~15 min
- Phase 3 (conformal prediction): requires GPU for MPNN inference.
  - Calibration: ~30 min on 1x H200 (inference on calibration set + quantile computation)
  - Prediction intervals for all candidates: ~15 min
  - AD analysis: ~30 min (CPU)

Total compute: ~8 hours wall-clock, ~2 hours GPU. Fits within a single `day` partition SLURM job.

**Recommendation on Uni-Mol pre-trained embeddings:**

Based on R01 research and the protml agent's findings, I recommend a **cautious, comparative** approach:

1. **Do not replace ECFP4/Morgan as the primary fingerprint.** The 2025 Praski and Adamczyk benchmark showed ECFP statistically matches or outperforms 24/25 pretrained embedding models for property prediction. For kinases specifically, RF+ECFP4 achieves AUC 0.774 across 354 kinases (Huang et al., 2024), comparable to multi-task deep learning methods.

2. **Use Uni-Mol embeddings as an additional UMAP layer for visualization only.** Project all candidates using Uni-Mol embeddings alongside Morgan UMAP. If Uni-Mol UMAP reveals additional structure (e.g., conformational state clusters that Morgan UMAP misses), this is a valuable finding. If not, report the null result.

3. **Consider Uni-Mol for MPNN replacement only if conformal prediction reveals widespread OOD issues.** If >30% of VAE-generated candidates have wide prediction intervals and are flagged as OOD by the current MPNN, then Uni-Mol's 3D pre-training (on 209M conformations) could provide a better-calibrated property predictor. This is a contingent recommendation, not a default action.

4. **Cite the conflicting evidence.** The paper should note that while Uni-Mol shows strong benchmarks (14/15 MoleculeNet tasks), the broader pattern is that pretrained molecular embeddings rarely outperform well-tuned ECFP baselines on standard tasks (Praski and Adamczyk, 2025). This honest framing strengthens rather than weakens the paper.

---

## Impact Assessment

### Publication Impact

**Primary target venue: Nature Computational Science.**

Required figures for Nature Comp Sci (based on analysis of recent molecular generation papers):
1. Pipeline overview schematic (exists)
2. Chemical space UMAP (this proposal: Figure 1)
3. Property distributions (this proposal: Figure 2)
4. Retrospective enrichment (exists, EF@10 = 4.95/7.72 vs 0.47/0.79)
5. Scoring sensitivity analysis table (this proposal: Table 1)
6. Scaffold diversity analysis (this proposal: Figure 3)
7. Per-state scaffold comparison (this proposal: Figure 4)
8. Prediction uncertainty / applicability domain (this proposal: Figure 5)
9. Pareto front visualization (exists)

**This proposal provides 5 of the ~9 required figures/tables, filling the current gap from "unpublishable" to "complete manuscript figure set."**

**Secondary target: JCIM (Journal of Chemical Information and Modeling).**

JCIM is more methods-focused and would weight the scoring sensitivity analysis and conformal prediction components more heavily. The multi-metric similarity analysis could itself support a focused methods paper.

**Tertiary target: NeurIPS / ICML (ML venues).**

ML venues care less about chemical space visualization but more about uncertainty quantification. The conformal prediction component with AD analysis fits this audience.

### Complete Figure and Table List

| ID | Content | Type | Venue Priority |
|----|---------|------|----------------|
| Fig 1 | UMAP of static + state-aware + ChEMBL EGFR actives, colored by pipeline | Main figure | All venues (essential) |
| Fig 2 | UMAP colored by EGFR conformational state (4 states) | Main figure | Nature Comp Sci, JCIM |
| Fig 3 | Violin plots of MW, LogP, TPSA, QED: static vs state-aware vs ChEMBL | Main figure | All venues (essential) |
| Fig 4 | Top-10 scaffolds per pipeline with frequency bars | Main or SI figure | JCIM, Nature Comp Sci |
| Fig 5 | Per-state scaffold Venn diagram / upset plot | Main figure | Nature Comp Sci (key for thesis) |
| Fig 6 | Pairwise Tanimoto distribution histograms | SI figure | JCIM |
| Fig 7 | SEDiv and #Circles comparison bar chart | SI or main figure | JCIM, NeurIPS |
| Fig 8 | MPNN prediction interval widths vs training set distance | Main figure | All venues |
| Tab 1 | Scoring sensitivity: mean score gap under 6 metric/reference configs | Main table | All venues (critical) |
| Tab 2 | Scaffold diversity statistics (unique, SEDiv, #Circles, novelty) | Main table | All venues |
| Tab 3 | AD coverage: fraction of candidates within MPNN reliable domain | Main or SI table | All venues |

### Effort Estimate

| Task | Person-weeks | Compute Cost | Dependencies |
|------|-------------|-------------|--------------|
| ChEMBL extraction + curation | 0.5 | Negligible | ChEMBL API access |
| Multi-metric similarity analysis | 1.0 | ~4h CPU | RDKit, curated reference set |
| UMAP + property visualization | 0.5 | ~1h CPU | umap-learn, matplotlib |
| Scaffold diversity analysis | 0.5 | ~1h CPU | RDKit scaffolds |
| Conformal prediction wrapping | 1.5 | ~2h GPU | mapie/crepes, trained MPNN |
| Figure polishing + manuscript text | 1.0 | None | All above |
| **Total** | **5.0 person-weeks** | **~8h wall-clock** | |

This is a high-impact, moderate-effort investment. The compute cost is trivial relative to the publication value.

### Risk Assessment

| Risk | Likelihood | Severity | Mitigation |
|------|-----------|----------|------------|
| ChEMBL EGFR data has quality issues (duplicates, wrong units, mixed assays) | Medium | Medium | Rigorous curation: filter by assay type, standard units, remove duplicates, cross-reference with BindingDB |
| Expanded reference set eliminates ALL differentiation between pipelines | Low | High | This would itself be a finding worth reporting. Also, enrichment analysis (EF@10) is reference-set-independent and would still show state-aware advantage |
| PheSA requires 3D conformers not available for all candidates | Medium | Low | PheSA is optional (C4/C5 configs). Morgan + Tversky (C0-C3) are sufficient for the core analysis. Generate conformers with RDKit's ETKDG if needed |
| UMAP projection is unstable or misleading | Low | Medium | Use multiple random seeds, report reproducibility. Supplement with t-SNE as sensitivity check. Follow Sabando et al. (2024) best practices |
| Conformal prediction intervals are too wide to be useful | Medium | Medium | If intervals are uniformly wide, this indicates the MPNN needs retraining (a useful finding). Report interval width distribution transparently |
| Reviewers dismiss multi-metric analysis as "just changing parameters" | Low | Medium | Frame as systematic sensitivity analysis, cite precedent (virtual screening benchmarks routinely compare metrics). The 6-config comparison is methodologically rigorous |
| Uni-Mol embeddings do not add value over Morgan for UMAP | Medium | Low | Report null result transparently. Negative results about pretrained embeddings are themselves informative given current hype |

---

## Evaluation Criteria

### Success Metrics

1. **Scoring gap decomposition is quantitatively complete.** The 6-config scoring table demonstrates that >= 80% of the mean-score gap is attributable to reference_similarity metric and reference set choice, with the enrichment signal (EF@10) preserved across all configurations.

2. **Chemical space figures meet publication standards.** At least 4 main-text figures and 2 SI figures are produced at 300 DPI, with proper axes, legends, and statistical annotations, suitable for Nature Comp Sci submission without revision.

3. **Scaffold analysis reveals state-specific chemistry.** At least 2 of the 4 EGFR conformational states produce significantly different scaffold distributions (Jaccard overlap < 0.3 between any pair of states).

4. **Conformal prediction intervals are calibrated.** Empirical coverage on a held-out test set is within 2 percentage points of nominal (i.e., 88-92% for 90% nominal intervals).

5. **AD analysis quantifies prediction reliability.** The fraction of candidates within the reliable MPNN domain is reported for both pipelines, with a clear correlation between interval width and training set distance (Pearson r > 0.3).

### Failure Conditions

- If expanded reference set eliminates the enrichment signal (EF@10 drops below 1.0 for state-aware pipeline), the reference expansion approach must be reconsidered. This would indicate the enrichment is itself an artifact.
- If conformal prediction requires MPNN architectural changes that invalidate existing results, defer Phase 3 to a follow-up study.

---

## Open Questions

1. **Should reference_similarity weight be reduced?** The current 35% weight may be too high regardless of metric choice. A weight sensitivity analysis (sweeping from 0.10 to 0.40) could identify a balanced weighting. However, changing weights is explicitly flagged in `CRITICAL.md` as requiring simultaneous updates to `SCORING_METHOD` and full pipeline re-runs. This could be proposed as a complementary analysis but is not part of this proposal's core scope.

2. **Should the paper include a "metric-agnostic" ranking?** One approach is to present Pareto rankings where reference_similarity is computed by multiple metrics simultaneously (i.e., a candidate is Pareto-optimal if it dominates on ANY similarity metric). This avoids committing to a single metric choice.

3. **How many ChEMBL centroids are optimal?** Too few (< 50) may not adequately represent chemical diversity; too many (> 500) may make max-similarity trivially high for all molecules. The potency-weighted mean-top-K approach mitigates this, but the optimal K should be tuned on a held-out set of known actives.

4. **Is PheSA practical at scale?** PheSA requires 3D conformer generation for all candidates and references. For ~3,500 ChEMBL compounds and ~491 StateBind candidates, this is feasible (~4,000 conformer generations at ~1s each = ~1 hour). But if multiple conformers per molecule are needed (as recommended for conformationally flexible EGFR inhibitors), compute scales linearly.

5. **Should we include a temporal split analysis?** Re-running the reference set expansion with only pre-2015 ChEMBL compounds (to match the retrospective cutoffs) would test whether the enrichment signal is robust to the reference set's temporal composition. This connects to the retrospective validation already performed.

6. **What is the right framing for the Uni-Mol comparison?** If Uni-Mol UMAP reveals conformational state clusters that Morgan UMAP misses, this could be a highlight of the paper. If not, it risks appearing as unnecessary complexity. The recommendation is to include it as a supplementary comparison, not a main-text feature, unless results are striking.

---

## References

1. Hert, J., Willett, P., Wilton, D.J., Acklin, P., Azzaoui, K., Jacoby, E., & Schuffenhauer, A. (2004). Comparison of fingerprint-based methods for virtual screening using multiple bioactive reference structures. *Journal of Chemical Information and Computer Sciences*, 44(3), 1177-1185.

2. Riniker, S. & Landrum, G.A. (2013). Do Not Hesitate to Use Tversky -- and Other Hints for Successful Active Analogue Searches with Feature Count Descriptors. *Journal of Chemical Information and Modeling*, 53(7), 1707-1715.

3. Bender, A., Jenkins, J.L., Glick, M., Deng, Z., Nettles, J.H., & Davies, J.W. (2009). Using Tversky Similarity Searches for Core Hopping: Finding the Needles in the Haystack. *Journal of Chemical Information and Modeling*, 49(1), 108-119.

4. Tripp, A., Maziarz, K., Lewis, S., Segler, M., & Hernandez-Lobato, J.M. (2024). Diverse Hits in De Novo Molecule Design: Diversity-Based Comparison of Goal-Directed Generators. *Journal of Chemical Information and Modeling*, 64(14), 5480-5492.

5. Sabando, M.V., Ponzoni, I., Milios, E.E., & Soto, A.J. (2024). From High Dimensions to Human Insight: Exploring Dimensionality Reduction for Chemical Space Visualization. *Molecules*, 30(1), 48.

6. Li, H., Zhang, Y., Li, J., & Zou, J. (2024). Conformalized Graph Learning for Molecular ADMET Property Prediction and Reliable Uncertainty Quantification. *Journal of Chemical Information and Modeling*, 64(24), 9196-9209.

7. Jimenez-Luna, J., Skalic, M., & Weskamp, N. (2024). Development and Evaluation of Conformal Prediction Methods for Quantitative Structure-Activity Relationship. *ACS Omega*, 9(28), 30366-30378.

8. Gasser, J., Sander, T., & Ertl, P. (2024). PheSA: An Open-Source Tool for Pharmacophore-Enhanced Shape Alignment. *Journal of Chemical Information and Modeling*, 64(15), 5944-5953.

9. Zhou, G., Gao, Z., Ding, Q., Zheng, H., Xu, H., Wei, Z., Zhang, L., & Ke, G. (2022). Uni-Mol: A Universal 3D Molecular Representation Learning Framework. *ICLR 2023*.

10. Lu, S., He, D., Li, J., & Ke, G. (2024). Data-driven quantum chemical property prediction leveraging 3D conformations with Uni-Mol+. *Nature Communications*, 15, 7104.

11. Praski, A. & Adamczyk, J. (2025). Benchmarking Pretrained Molecular Embedding Models for Molecular Representation Learning. *arXiv:2508.06199*.

12. Huang, L., Luo, H., Peng, S., Chen, Y., Luo, X., Li, S., & Zheng, M. (2024). Large-scale comparison of machine learning methods for profiling prediction of kinase inhibitors. *Journal of Cheminformatics*, 16, 15.

13. Deng, J., Yang, Z., Wang, H., Ojima, I., Samaras, D., & Wang, F. (2023). A systematic study of key elements underlying molecular property prediction. *Nature Communications*, 14, 6395.

14. Hu, G., Kuber, G., & Bhatt, S. (2012). Performance Evaluation of 2D Fingerprint and 3D Shape Similarity Methods in Virtual Screening. *Journal of Chemical Information and Modeling*, 52(5), 1103-1113.

15. Bolcato, G., Bissaro, M., Deganutti, G., Sturlese, M., & Moro, S. (2022). Maximizing the Performance of Similarity-Based Virtual Screening Methods by Generating Synergy from the Integration of 2D and 3D Approaches. *International Journal of Molecular Sciences*, 23(14), 7747.

16. Stumpfe, D. & Bajorath, J. (2014). Systematic assessment of coordinated activity cliffs formed by kinase inhibitors and detailed characterization of activity cliff clusters and associated SAR information. *European Journal of Medicinal Chemistry*, 80, 416-427.

17. Wang, Y., Liu, Y., Li, X., & Chen, H. (2024). Protein characteristics substantially influence the propensity of activity cliffs among kinase inhibitors. *Scientific Reports*, 14, 10239.

18. Rong, Y., Bian, Y., Xu, T., Xie, W., Wei, Y., Huang, W., & Huang, J. (2020). Self-Supervised Graph Transformer on Large-Scale Molecular Data. *Advances in Neural Information Processing Systems (NeurIPS)*, 33.

---

*This proposal describes a computational analysis plan. All anticipated results are predictions based on literature evidence, not experimental findings. The mean-score gap decomposition is an analytical claim that must be empirically validated by executing the proposed scoring configurations.*
