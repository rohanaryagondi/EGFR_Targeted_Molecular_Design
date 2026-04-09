---
agent: Maverick Protein ML Expert
round: 3
date: 2026-04-09
type: critique
proposal_reviewed: cheminfo-P01
---

# Critique: Scoring Reform and Publication-Quality Chemical Space Analysis for StateBind

## Reviewing Agent

**Maverick Protein ML Expert (protml)** -- Cohort2, IdeationDept

Expertise: Protein language models (ESM-2, ProstT5, ESM Cambrian), pre-trained molecular representations (Uni-Mol, GEM, GROVER), protein-ligand co-embedding (DrugCLIP, ProFSA), conformational ensemble prediction (AlphaFlow, Str2Str). My review focuses on whether the proposal sufficiently leverages learned representations and protein-side information, and whether its conservative stance on foundation models is justified by evidence or driven by inertia.

## Proposal Summary

cheminfo-P01 proposes three interconnected interventions over 5 person-weeks:

1. **Reference set expansion and multi-metric similarity analysis**: Replace the current 3-drug reference set with 100-300 ChEMBL EGFR scaffold centroids and test 6 scoring configurations (3 metrics x 2 reference sets) to decompose the mean-score gap (static 0.5437 vs state-aware 0.4378) into its component artifacts.

2. **Chemical space visualization pipeline**: Produce 8-10 publication figures including UMAP projections (Morgan/ECFP4 fingerprints), property distributions, scaffold diversity analyses (SEDiv, #Circles), and per-state scaffold comparisons.

3. **Conformal prediction wrapping**: Apply split conformal prediction to the MPNN (R^2 = 0.69) to produce calibrated prediction intervals and applicability domain analysis.

The proposal explicitly recommends Uni-Mol embeddings as "supplementary UMAP comparison only" and maintains Morgan/ECFP4 as the primary representation throughout.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** A well-structured, high-value proposal that correctly identifies the scoring artifact as the most urgent problem, but systematically underweights the protein-ligand interface -- treating molecular similarity as a ligand-only problem when the entire thesis of StateBind is that the protein's conformational state matters.

---

## Strengths

**S1. The scoring artifact diagnosis is the single most important insight for the publication.**

The observation that reference_similarity (35% weight, 3 quinazoline-biased drugs) more than explains the mean-score gap is devastating and correct. The estimated delta of 0.140 from this single component exceeding the total gap of 0.1059 means the state-aware pipeline actually wins when the artifact is removed. This transforms the narrative from "static wins on mean score" to "metric choice conceals state-aware advantage." No reviewer would accept the current framing. This analysis must be done regardless of any other disagreement.

**S2. The 6-configuration sensitivity table is methodologically rigorous.**

Testing 3 metrics (Morgan/Tanimoto, Tversky, PheSA) crossed with 2 reference sets (3 drugs, ChEMBL centroids) provides a clean factorial design. The inclusion of rank correlation (Kendall's tau) between configurations and per-component decomposition goes beyond what most papers provide. This table alone could justify a JCIM methods contribution.

**S3. The scaffold diversity analysis with SEDiv and #Circles uses modern metrics.**

Citing Tripp et al. (2024) on the failure modes of simple diversity metrics (fraction unique, internal diversity) and proposing SEDiv and #Circles as alternatives demonstrates genuine methodological sophistication. The per-state scaffold comparison -- testing whether different EGFR states produce different scaffold classes -- is the most publication-worthy component of the chemical space analysis.

**S4. The conformal prediction component addresses a real reviewer concern.**

Split conformal prediction with absolute residual nonconformity scores is the right starting point. The applicability domain overlay (nearest-neighbor Tanimoto + VAE latent space Mahalanobis distance cross-referenced with interval width) is well-conceived and would produce a compelling figure.

**S5. Compute estimates are realistic and transparent.**

The 8-hour total wall-clock time and 2-hour GPU requirement are honest and achievable within a single SLURM day partition job. This contrasts favorably with proposals requiring weeks of GPU time.

---

## Weaknesses (with Severity and Addressable?)

**W1. The proposal treats similarity as a purely ligand-side problem while the project thesis is that the protein's conformational state matters. (Severity: HIGH. Addressable: YES.)**

The entire reference_similarity component scores candidates based on 2D molecular similarity to reference drugs. It contains zero information about the protein pocket. This means the scoring function evaluates "Does this molecule look like a known EGFR drug?" rather than "Does this molecule complement this specific EGFR conformational state?" The proposal's solution -- expanding the reference set and changing the similarity metric -- still operates entirely in ligand-only space. It replaces 3 reference drugs with 100-300 reference drugs, but the fundamental problem persists: the score does not know which pocket shape the molecule is supposed to bind.

A protein-ligand co-embedding approach (DrugCLIP, ProFSA) would replace similarity-to-reference-drugs with compatibility-with-target-pocket. DrugCLIP achieves EF@1% of 31.89 on DUD-E in zero-shot mode and 67.17 when fine-tuned -- numbers that suggest a co-embedding score would be a more informative scoring component than any variant of ligand-only similarity. The proposal acknowledges the existence of co-embedding methods nowhere except implicitly through the Uni-Mol UMAP comparison.

This is not an abstract concern. StateBind generates molecules for 4 different EGFR pockets. A pocket-blind similarity score treats DFGin_aCin and DFGout_aCout candidates identically if they have the same fingerprint distance to reference drugs. A pocket-aware co-embedding score would differentiate them based on complementarity to their intended binding site.

**Suggested modification**: Add a 7th scoring configuration (C6) to the sensitivity analysis that replaces reference_similarity entirely with a DrugCLIP-style pocket-ligand compatibility score. This directly tests whether pocket-awareness in the scoring function changes the pipeline comparison. The compute cost is marginal (milliseconds per molecule for DrugCLIP inference). If C6 produces a fundamentally different ranking than C0-C5, this is the strongest possible evidence for the project thesis.

**W2. Relegating Uni-Mol to "supplementary UMAP comparison only" is underselling the technology by a large margin. (Severity: MEDIUM-HIGH. Addressable: YES.)**

The proposal's recommendation on Uni-Mol (Section "Recommendation on Uni-Mol pre-trained embeddings") cites the Praski and Adamczyk (2025) benchmark finding that ECFP matches or outperforms 24/25 pretrained embedding models on standard molecular property prediction. This is accurate but misapplied. The relevant question is not "Are Uni-Mol embeddings better than ECFP for property prediction?" but rather "Do Uni-Mol's 3D-aware representations capture chemical space structure that 2D fingerprints miss -- particularly for VAE-generated molecules with novel scaffolds?"

For molecules generated by a SELFIES VAE, 2D fingerprints may poorly capture the actual 3D pharmacophoric features that determine binding. VAE-generated molecules can have similar fingerprints but very different 3D conformations, or different fingerprints but similar 3D pharmacophore presentations. Uni-Mol's SE(3)-equivariant architecture, pre-trained on 209 million 3D conformations, is specifically designed to capture this kind of information. The Praski and Adamczyk benchmark evaluated property prediction on established molecules with well-characterized activities -- not chemical space analysis for de novo generated molecules, which is a fundamentally different use case.

My recommendation: Uni-Mol should be given equal standing with Morgan/ECFP4 in both the UMAP visualizations (which the proposal already acknowledges) AND in the scaffold diversity analysis AND in the similarity scoring. Specifically:
- Run a 12-configuration sensitivity table (6 metric/reference combinations x 2 fingerprint types: Morgan/ECFP4 and Uni-Mol embeddings)
- Report whether Uni-Mol-based UMAP reveals conformational state clusters that Morgan UMAP misses
- If Uni-Mol reveals additional structure, promote it to the main text; if not, report as a well-motivated null result

The additional compute cost is modest (Uni-Mol inference on 491 candidates: approximately 5 seconds on H200).

**W3. Conformal prediction without ensemble methods leaves uncertainty quantification incomplete. (Severity: MEDIUM. Addressable: YES.)**

Split conformal prediction provides calibrated marginal coverage guarantees but does not distinguish between epistemic uncertainty (model does not know, fixable with more data) and aleatoric uncertainty (intrinsic noise, not fixable). For reviewers at ML venues (NeurIPS, ICML), this distinction matters.

The proposal mentions conformalized quantile regression (CQR) as an alternative but does not propose ensemble-based methods. Deep ensembles (Lakshminarayanan et al., 2017) remain the gold standard for epistemic uncertainty in neural networks. Training 5 MPNNs with different random seeds and measuring prediction variance provides a direct estimate of epistemic uncertainty that conformal prediction cannot decompose. Li et al. (JCIM, 2024) -- cited in the proposal -- actually demonstrated that conformalized GNN *fusion* (combining multiple GNN architectures) achieved the best interval reduction (up to 74%), suggesting that ensembles and conformal prediction are complementary, not alternatives.

**Suggested modification**: Train 5 MPNN replicates with different random initializations. Compute ensemble mean and variance for all candidates. Then wrap the ensemble predictions with conformal prediction. Report: (a) ensemble variance as epistemic uncertainty, (b) conformal intervals as calibrated total uncertainty, (c) the correlation between ensemble variance and conformal interval width. If they are highly correlated, conformal prediction alone suffices. If not, the ensemble adds information. This adds approximately 2 hours of GPU training time (5x the current single model, which trains in roughly 25 minutes).

**W4. The ChEMBL centroid approach is the right step but stops short of the real solution. (Severity: MEDIUM. Addressable: PARTIALLY.)**

Expanding from 3 reference drugs to 100-300 ChEMBL centroids dramatically improves the reference set's chemical diversity. However, the centroids are still chosen solely by scaffold identity and potency. They carry no information about which EGFR conformational state they bind. Many ChEMBL EGFR compounds were tested against wild-type EGFR in a single (likely active) state, so their potency does not indicate selectivity for DFGin_aCin versus DFGout_aCout.

Ideally, reference compounds would be annotated by their preferred binding state using KLIFS binding mode data or re-docking to all 4 representative structures. Then the reference_similarity score could be computed against state-matched centroids -- e.g., a molecule generated for the DFGout_aCin pocket would be scored against reference drugs known to prefer DFGout_aCin, not against all EGFR actives indiscriminately.

I recognize this is a larger undertaking than the proposal intends. But the proposal should at least acknowledge this limitation and flag state-annotated reference scoring as a natural extension. Without it, the expanded reference set still scores a DFGout candidate the same as a DFGin candidate if they have the same fingerprint distance to the centroid pool.

**W5. The proposal misses an opportunity to incorporate protein-side information into the chemical space visualization. (Severity: MEDIUM. Addressable: YES.)**

The UMAP projections proposed in Step 3 are exclusively ligand-space projections. They show where molecules fall in fingerprint space, colored by pipeline or state assignment. But they do not show the protein-ligand interaction landscape. A co-embedding UMAP -- where pocket embeddings and ligand embeddings are projected into the same space -- would directly visualize whether state-aware candidates cluster near their intended pocket embedding while static candidates cluster near only the 1M17 pocket. This would be a far more compelling publication figure than a standard Morgan/UMAP plot, which every generation paper already includes.

The technical requirement is straightforward: extract pocket embeddings for the 4 EGFR states (using ESM-2, ProstT5, or DrugCLIP's pocket encoder), extract ligand embeddings (using Uni-Mol or DrugCLIP's molecule encoder), project all embeddings jointly via UMAP, and color by pipeline/state. If the state-aware candidates co-localize with their intended state pocket while static candidates cluster near only the active-state pocket, this is the visual proof of the project thesis.

**W6. The PheSA recommendation lacks critical evaluation. (Severity: LOW-MEDIUM. Addressable: YES.)**

The proposal recommends PheSA (Gasser et al., JCIM 2024) for 3D shape+pharmacophore similarity as configurations C4/C5. PheSA is a reasonable choice -- it is open-source, reasonably fast, and combines shape overlap with pharmacophore features. However, the proposal does not discuss limitations:

- PheSA requires 3D conformer generation for all molecules. For VAE-generated molecules that may not have chemically sensible 3D geometries, the conformer generation step could introduce artifacts. RDKit's ETKDG is mentioned but its failure rate on complex scaffolds (roughly 5-15% for drug-like molecules) is not acknowledged.
- PheSA's Java dependency (OpenChemLib) adds integration friction on HPC systems. This is acknowledged but underweighted.
- Alternative 3D similarity methods exist: ShaEP (Vainio et al.), ROCS (OpenEye, commercial but widely cited), and Uni-Mol's own 3D distance-based similarity. For the purpose of a sensitivity analysis, Uni-Mol 3D cosine similarity would be a more natural comparison than PheSA, since it avoids the conformer generation step entirely by operating on learned 3D representations.

**Suggested modification**: Consider replacing PheSA with Uni-Mol 3D cosine similarity for configurations C4/C5. This tests whether learned 3D representations capture shape/pharmacophore complementarity without explicit conformer generation. PheSA can be retained as a secondary comparison if desired.

---

## Feasibility Assessment

**Phase 1 (Reference set expansion + multi-metric similarity): HIGHLY FEASIBLE.** ChEMBL extraction, scaffold clustering, and fingerprint similarity computation are routine cheminformatics operations. The 4-hour CPU estimate is conservative. The only potential friction is PheSA's Java dependency, which can be sidestepped as noted above.

**Phase 2 (Chemical space visualization): HIGHLY FEASIBLE.** UMAP + Morgan fingerprints is standard. Figure generation with matplotlib/seaborn is straightforward. The only novel element (SEDiv, #Circles) requires implementing the sphere exclusion algorithm, which is approximately 50 lines of Python.

**Phase 3 (Conformal prediction): FEASIBLE WITH CAVEATS.** Split conformal prediction is mathematically simple and implementation via mapie or crepes is well-documented. The caveat is that the calibration set must be carefully constructed from the existing validation data without leaking information from training. If the MPNN was originally trained with a single train/val/test split, extracting a calibration set from validation data is straightforward. If the MPNN used cross-validation, the calibration procedure is more complex and must account for fold structure. The proposal does not address this.

**Suggested addition (DrugCLIP scoring tier): FEASIBLE.** DrugCLIP checkpoints are publicly available. Inference is approximately 1 millisecond per pocket-ligand pair. Scoring 491 candidates against 4 pockets is approximately 2 seconds of compute. This is negligible relative to the rest of the proposal.

**Overall timeline**: The proposed 5 person-weeks is realistic for Phases 1-3. Adding the DrugCLIP scoring configuration and ensemble MPNN training would add approximately 1 person-week, bringing the total to 6 person-weeks. This remains a moderate-effort, high-return investment.

---

## Suggested Modifications

In order of priority:

**Modification 1 (HIGH PRIORITY): Add a pocket-aware scoring configuration.**

Add configuration C6 to the sensitivity analysis that replaces reference_similarity with a DrugCLIP or ProFSA pocket-ligand compatibility score. This directly tests whether pocket-awareness in the scoring function changes the pipeline comparison. If C6 produces a qualitatively different result from C0-C5 (all of which are ligand-only similarity variants), this is the single most important finding the paper can report: that ligand-only similarity metrics are insufficient for evaluating conformational state-aware generation.

Implementation: Download DrugCLIP checkpoint. Extract pocket features for 4 EGFR structures (1M17, 2GS7, 3W2R, 4ZAU). Compute pocket-ligand compatibility scores for all 491 candidates against all 4 pockets. Use the score against the candidate's intended pocket as the reference_similarity replacement. Additional compute: less than 5 minutes on GPU.

**Modification 2 (HIGH PRIORITY): Elevate Uni-Mol from supplementary to co-primary representation.**

Run the full sensitivity analysis with both Morgan/ECFP4 and Uni-Mol 3D embeddings, producing a 12-configuration table (or a clean 2x3x2 factorial: {Morgan, Uni-Mol} x {Tanimoto, Tversky, cosine} x {3 drugs, ChEMBL centroids}). This doubles the analysis but provides a definitive answer on whether learned representations change the scoring landscape for VAE-generated molecules. If they do not, this is itself a publishable finding that supports ECFP4 for this task. If they do, the proposal's current recommendation would be leaving value on the table.

**Modification 3 (MEDIUM PRIORITY): Add ensemble MPNN for epistemic uncertainty.**

Train 5 MPNN replicates and use ensemble variance as a complementary uncertainty measure alongside conformal prediction. This strengthens the uncertainty quantification story for ML venue submissions and adds approximately 2 hours of GPU time.

**Modification 4 (MEDIUM PRIORITY): Add co-embedding UMAP as a main-text figure.**

Project pocket embeddings (4 EGFR states) and ligand embeddings (all candidates) into a shared 2D space. Color candidates by pipeline and pockets by state. This visual directly tests the thesis: do state-aware candidates cluster near their intended pocket while static candidates cluster near only the active-state pocket?

**Modification 5 (LOW PRIORITY): Acknowledge the state-annotation gap in reference scoring.**

In the Open Questions section, add a note that ChEMBL centroids are not annotated by binding mode/conformational state, and that state-matched reference scoring (using KLIFS binding mode annotations or re-docking) is a natural extension that would further reduce the scoring artifact.

---

## Alternative Approaches

**Alternative A: Pocket-conditioned scoring as a full replacement for reference_similarity.**

Rather than reforming reference_similarity by expanding the reference set and changing the metric, replace it entirely with a pocket-ligand compatibility score from a pre-trained co-embedding model. The scoring function would become:

- druglikeness (0.30): Unchanged
- pocket_compatibility (0.35): DrugCLIP/ProFSA score of candidate against its intended pocket
- docking_proxy (0.20): Unchanged (or replaced by Uni-Mol docking score)
- state_specificity (0.15): Unchanged

This approach has the advantage of making the scoring function inherently pocket-aware. It eliminates the reference set dependency entirely. The disadvantage is that it introduces a new dependency (DrugCLIP) and changes the scoring function more aggressively, which requires a full pipeline re-run. This is flagged in CRITICAL.md as requiring updates to SCORING_METHOD.

I do not propose this as a replacement for the cheminfo-P01 approach. The sensitivity analysis across multiple configurations is valuable regardless. But Alternative A should be discussed as the logical endpoint of the scoring reform trajectory.

**Alternative B: Hybrid scoring with learned and fingerprint-based components.**

Keep reference_similarity as one component but add a second similarity/compatibility component based on learned representations. The scoring function would have 5 components instead of 4:

- druglikeness (0.25)
- fingerprint_similarity (0.20): Current Morgan/Tversky approach with expanded reference set
- pocket_compatibility (0.20): DrugCLIP/ProFSA co-embedding score
- docking_proxy (0.20)
- state_specificity (0.15)

This preserves backward compatibility while adding protein-side information. It also allows a direct comparison of how much the pocket_compatibility component contributes beyond fingerprint_similarity, which is a publishable finding.

---

## Impact on Publication Narrative

The proposal correctly identifies that the current scoring narrative is unpublishable. The mean-score gap is an artifact, and any competent reviewer will find it. The sensitivity analysis resolves this problem.

However, the proposal's narrative stops at "the gap is a tunable artifact." This is necessary but not sufficient. The stronger narrative is: "Ligand-only similarity metrics are fundamentally insufficient for evaluating conformational state-aware generation. Pocket-aware scoring reveals the true advantage of state-aware design." This requires the pocket-aware scoring configuration (C6) I propose in Modification 1.

Without C6, the paper's conclusion would be: "The mean-score gap depends on metric choice, so we should be cautious about declaring a winner." With C6, the conclusion becomes: "Pocket-aware scoring, which is the appropriate metric for evaluating state-conditioned generation, demonstrates clear state-aware superiority." The second narrative is dramatically stronger and aligns directly with the project thesis.

The chemical space visualization and conformal prediction components are essential supporting material for any venue. My modifications (co-embedding UMAP, ensemble uncertainty) strengthen these components without changing their fundamental character.

For venue targeting:
- **Nature Computational Science**: The co-embedding UMAP (Modification 4) would be a standout figure. NCS reviewers will ask "What does state-aware generation give you that static does not?" and a visual showing state-aware candidates clustering near their intended pocket is the most direct answer.
- **JCIM**: The expanded sensitivity table (Modification 2, 12 configurations) fits JCIM's methods-focused audience perfectly. The Morgan vs Uni-Mol comparison adds methodological depth.
- **NeurIPS/ICML**: Ensemble MPNN + conformal prediction (Modification 3) is necessary for ML venues. Split conformal prediction alone is considered basic; ensemble + CP is the current standard.

---

## References

1. Gao, B., Qiang, B., Tan, H., et al. (2023). DrugCLIP: Contrastive Protein-Molecule Representation Learning for Virtual Screening. NeurIPS 2023.

2. Gao, B., Tan, H., Qiang, B., et al. (2025). Deep contrastive learning enables genome-wide virtual screening. Science.

3. Gao, B., Huang, T., Wen, Z., et al. (2024). ProFSA: Self-supervised Pocket Pretraining via Protein Fragment-Surroundings Alignment. ICLR 2024.

4. Zhou, G., Gao, Z., Ding, Q., et al. (2023). Uni-Mol: A Universal 3D Molecular Representation Learning Framework. ICLR 2023.

5. Praski, A. & Adamczyk, J. (2025). Benchmarking Pretrained Molecular Embedding Models for Molecular Representation Learning. arXiv:2508.06199.

6. Huang, L., Luo, H., Peng, S., et al. (2024). Large-scale comparison of machine learning methods for profiling prediction of kinase inhibitors. Journal of Cheminformatics, 16, 15.

7. Lakshminarayanan, B., Pritzel, A., & Blundell, C. (2017). Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles. NeurIPS 2017.

8. Li, H., Zhang, Y., Li, J., & Zou, J. (2024). Conformalized Graph Learning for Molecular ADMET Property Prediction and Reliable Uncertainty Quantification. Journal of Chemical Information and Modeling, 64(24), 9196-9209.

9. Lin, Z., Akin, H., Rao, R., et al. (2023). Evolutionary-scale prediction of atomic-level protein structure with a language model. Science, 379(6637), 1123-1130.

10. Heinzinger, M., Weissenow, K., Rost, B., et al. (2024). Bilingual Language Model for Protein Sequence and Structure (ProstT5). NAR Genomics and Bioinformatics, 6(4), lqae150.

11. Gasser, J., Sander, T., & Ertl, P. (2024). PheSA: An Open-Source Tool for Pharmacophore-Enhanced Shape Alignment. Journal of Chemical Information and Modeling, 64(15), 5944-5953.

12. Tripp, A., Maziarz, K., Lewis, S., Segler, M., & Hernandez-Lobato, J.M. (2024). Diverse Hits in De Novo Molecule Design: Diversity-Based Comparison of Goal-Directed Generators. Journal of Chemical Information and Modeling, 64(14), 5480-5492.

13. Hert, J., Willett, P., Wilton, D.J., et al. (2004). Comparison of fingerprint-based methods for virtual screening using multiple bioactive reference structures. Journal of Chemical Information and Computer Sciences, 44(3), 1177-1185.

14. Riniker, S. & Landrum, G.A. (2013). Do Not Hesitate to Use Tversky -- and Other Hints for Successful Active Analogue Searches with Feature Count Descriptors. Journal of Chemical Information and Modeling, 53(7), 1707-1715.

15. Lu, S., Gao, Z., He, D., et al. (2024). Uni-Mol2: Exploring Molecular Pretraining Model at Scale. NeurIPS 2024.

16. van Linden, O.P.J., Kooistra, A.J., Leurs, R., et al. (2014). KLIFS: A Knowledge-Based Structural Database To Navigate Kinase-Ligand Interaction Space. Journal of Medicinal Chemistry, 57(2), 249-277.
