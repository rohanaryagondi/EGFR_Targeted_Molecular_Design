---
agent: Maverick Data Scientist / Statistician
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: medchem-P01
---

# Critique: Scoring Function Revision with ADMET and Selectivity Integration

## Reviewing Agent

Dr. Maverick Data Scientist / Statistician. Expertise in statistical experimental
design, bias prevention, multiple testing correction, sensitivity analysis methodology,
and causal inference. This review focuses on whether the proposed scoring revision
introduces statistical confounds, whether the dual reporting design actually prevents
cherry-picking, and whether the sensitivity analysis is adequately powered for a
6-dimensional weight space.

---

## Proposal Summary

medchem-P01 proposes replacing StateBind's 4-component scoring function (reference
similarity 0.35, drug-likeness 0.30, docking 0.20, state specificity 0.15) with a
6-component function adding ADMET safety and selectivity proxy, while reducing reference
similarity to 0.10 and drug-likeness to 0.15. Results would be reported under both
original and revised scoring. Three weight configurations (MPO, Conservative, Discovery)
are offered.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The scientific case for scoring revision is strong, but the
statistical execution plan has five concrete weaknesses that, if unaddressed, will
give reviewers grounds to dismiss the revision as post-hoc optimization favoring the
preferred outcome.

---

## Strengths

1. **The problem diagnosis is well-evidenced and correct.** The proposal marshals
   specific, quantitative evidence that the current scoring function is miscalibrated
   for kinase inhibitors: QED penalizes 48% of approved kinase inhibitors (Roskoski
   2026), Tanimoto misses 60% of bioactive pairs at TC < 0.30 (Chen et al. 2025),
   and erlotinib is not conformationally selective (Park et al. 2012). These are not
   opinions -- they are citable facts. This is exactly the kind of evidence-based
   argument that reviewers at JCIM will find compelling, and it correctly identifies
   that the scoring function is actively working against the stated thesis.

2. **Kinase-calibrated ADMET thresholds are clinically defensible.** The argument that
   osimertinib (hERG IC50 = 0.57 uM) is an approved, clinically used drug, and
   therefore a 10 uM "safe" threshold is inappropriate for kinase inhibitor scoring,
   is sound. The ICH S9 guideline explicitly permits higher safety risks in oncology.
   A reviewer cannot attack the kinase-calibrated thresholds without implicitly arguing
   that osimertinib should not have been approved. This is a strong rhetorical and
   scientific position.

3. **Dual reporting is the right structural safeguard.** Reporting all results under
   both original and revised scoring is the single most important design element. It
   transforms the scoring revision from "we changed the scoring to make our method win"
   into "we show how scoring design interacts with pipeline design." This is essential.

4. **The component ablation analysis is well-designed.** Zeroing each of the 6
   components individually and measuring the impact on the static vs state-aware
   comparison is a clean experimental design that isolates the marginal contribution
   of each scoring dimension. This directly addresses the question "does the scoring
   function design determine the winner?"

5. **The selectivity-via-state-specificity argument is novel and testable.** Connecting
   DFG-out state targeting to the known type II selectivity advantage (Gini 0.76 vs
   0.58; Ung et al. 2015) creates a compelling narrative bridge. If DFG-out-targeting
   candidates show higher cross-docking selectivity scores, this is a genuine mechanistic
   insight, not just a scoring trick.

---

## Weaknesses

1. **Dual reporting does not prevent bias if the primary analysis is selected post-hoc.**

   - **Severity:** Critical
   - **Addressable?** Yes -- with a pre-specified primary configuration

   The proposal says "report all results under BOTH original and revised scoring." But
   which is the PRIMARY analysis? If the paper leads with revised scoring in the main
   text and relegates original scoring to supplementary materials (as Open Question #5
   explicitly recommends), and if revised scoring happens to favor state-aware while
   original scoring favors static, a sophisticated reader will recognize this as having
   chosen the primary analysis to match the desired conclusion.

   Dual reporting is necessary but not sufficient. What is needed is a pre-specified
   decision rule for which scoring function is primary BEFORE seeing the results. The
   proposal should commit: "The primary analysis uses [X] scoring. The secondary
   analysis uses [Y] scoring. The primary was selected because [justification that
   does not reference outcomes]."

   The strongest justification for making revised scoring primary would be an independent
   validation step: score the 94 approved kinase inhibitors under both scoring functions
   and demonstrate that revised scoring better discriminates approved kinase drugs from
   random drug-like molecules. This validation uses no StateBind data and no pipeline
   comparison results, so it cannot be accused of outcome-driven selection. Perform this
   calibration step FIRST, lock the primary scoring function, THEN run the head-to-head
   comparison.

2. **Three weight configurations constitute a multiplicity problem.**

   - **Severity:** Major
   - **Addressable?** Yes -- designate one as primary before analysis

   The proposal presents Config A (MPO), Config B (Conservative), and Config C (Discovery)
   as alternative weight sets. If all three are run and the one that most favors state-aware
   is featured prominently, this is a form of undisclosed multiple testing. Three
   configurations means three chances for the desired result to emerge.

   The standard approach: designate ONE primary configuration a priori with an explicit
   rationale (e.g., "Config A mirrors published pharma MPO weight distributions"). Report
   the other two as pre-specified sensitivity analyses. Apply appropriate adjustment to
   any claims based on concordance across configurations.

   Better still: do not hand-pick ANY configuration. Use the Dirichlet random weight
   analysis as the primary result. Report: "Under X% of 6-component weight configurations,
   state-aware outperforms static." This avoids the multiplicity issue entirely because
   it integrates over the weight space rather than testing specific points.

3. **100 Dirichlet samples are insufficient for a 6-dimensional simplex.**

   - **Severity:** Major
   - **Addressable?** Yes -- increase to 1000-5000 samples

   The proposal retains the current sensitivity analysis design of 100 random Dirichlet
   weight configurations but expands from 4 to 6 components. This is problematic.

   The 4-component simplex is 3-dimensional; the 6-component simplex is 5-dimensional.
   The volume of a K-simplex scales as 1/K!, so the 5-simplex has volume 1/720 of its
   bounding hypercube vs 1/24 for the 3-simplex. Coverage deteriorates rapidly with
   dimension. To maintain equivalent coverage density when moving from a 3-simplex to a
   5-simplex, the sample count must increase roughly by a factor of (5!/3!) = 20, i.e.,
   from 100 to approximately 2000 samples.

   More formally: for a uniform Dirichlet(1,1,...,1) on K components, the expected
   minimum L-infinity distance between any sample point and a target point scales as
   O(N^{-1/(K-1)}). Going from K=4 to K=6 means going from O(N^{-1/3}) to O(N^{-1/5}).
   At N=100, the coverage gap in 5D is 100^{-1/5} = 0.40, meaning roughly 40% of the
   simplex is poorly represented. At N=2000, this drops to 2000^{-1/5} = 0.22.

   Practical recommendation: run at least 1000 Dirichlet samples (the compute cost is
   trivial -- this is just re-weighting precomputed per-component scores). 5000 would
   be better. Report the fraction favoring state-aware with a 95% bootstrap CI on that
   fraction (the fraction is itself a statistic that has uncertainty). At N=100, a
   fraction of 0.60 has a 95% CI of [0.50, 0.70] -- barely excluding 0.50. At N=5000,
   a fraction of 0.60 has a 95% CI of [0.586, 0.614] -- much more informative.

4. **BSI has not been validated for the retrospective enrichment task, and changing
   similarity metric AND weights simultaneously confounds the analysis.**

   - **Severity:** Major
   - **Addressable?** Yes -- keep them orthogonal

   The proposal's Option C suggests replacing Morgan Tanimoto with BSI (Chen et al.
   2025). BSI was validated for early retrieval of known bioactive compounds (EF@2%
   for retrieving actives from ChEMBL), not for retrospective enrichment of approved
   drugs across a time-split. These are different tasks. BSI was trained using
   leave-one-protein-out cross-validation on ChEMBL bioactivity data, meaning it has
   seen EGFR ligand-activity relationships during training. Applying BSI to score
   similarity for an EGFR retrospective enrichment test could introduce a subtle form
   of information leakage: BSI "knows" which molecules are bioactive at EGFR because
   it was trained on that data.

   More fundamentally, changing the similarity METRIC and the similarity WEIGHT
   simultaneously makes it impossible to attribute any change in outcome to either
   modification alone. If revised scoring with BSI at 0.10 weight favors state-aware
   while original scoring with Tanimoto at 0.35 does not, is it the weight change or
   the metric change?

   The proposal already recommends Option A (keep Tanimoto, reduce weight) as the
   primary approach, with Option B and C as sensitivity analyses. This is correct.
   I would strengthen this: Option A is the ONLY acceptable primary analysis. Option B
   and C are supplementary explorations that must be clearly labeled as such. If BSI
   is used at all, it must be tested at BOTH the original weight (0.35) and the revised
   weight (0.10) to separate metric effects from weight effects. This requires a 2x2
   factorial design: {Tanimoto, BSI} x {0.35, 0.10}, which is 4 comparisons. Report
   all 4; do not select the one that works best.

5. **The selectivity proxy (cross-docking) has uncertain correlation with experimental
   selectivity, and no internal validation is proposed.**

   - **Severity:** Major
   - **Addressable?** Yes -- add a calibration step

   The proposal defines selectivity score = 1.0 - max(off_target_normalized_scores),
   using GNINA cross-docking against 5 off-target kinases. The implicit assumption is
   that GNINA docking scores meaningfully discriminate selective from non-selective
   binders across different kinase targets. This assumption is not validated.

   Published evidence is mixed. Standard docking methods using rigid protein models
   show poor correlation with experimental binding affinities across different targets
   because pocket size, flexibility, and scoring artifacts differ systematically between
   proteins. Subramanian et al. (2019, J Chem Inf Model) found that standard docking
   achieves R^2 of only 0.15-0.30 for cross-target selectivity prediction. ML-enhanced
   scoring (e.g., the docking-informed ML approach from Sorgenfrei et al., JCIM 2024)
   achieves R^2 = 0.63-0.74, but this requires target-specific training.

   The Kinase-Bench benchmark (JCIM 2024) explicitly addresses this challenge: tailoring
   docking protocols to identify selective kinase inhibitors "has long been a substantial
   obstacle." The conserved ATP binding site across kinases means docking score
   differences are small relative to scoring noise.

   The proposal acknowledges the normalization problem (Open Question #1) and suggests
   per-target z-score normalization using known binder/non-binder distributions. This
   is the right approach but must be validated before the selectivity score is used in
   the scoring function.

   **Required calibration:** Take 50-100 kinase inhibitors with known experimental
   KINOMEscan or DiscoverX selectivity data (available from Karaman et al., Nat
   Biotechnol 2008 for 38 kinase inhibitors across 317 kinases). Dock these molecules
   against the 5 off-target kinases using GNINA. Compute Spearman correlation between
   the GNINA-derived selectivity score and the experimental selectivity index (e.g.,
   the S(10) selectivity score at 10 uM from KINOMEscan). If the Spearman rho is below
   0.3, the selectivity proxy has insufficient resolution to serve as a scoring
   component, and it should be downweighted or removed. Report this calibration
   regardless of outcome.

---

## Feasibility Assessment

### Technical Feasibility

High. The proposal builds on existing StateBind infrastructure. GNINA cross-docking
against 5 off-target kinases is straightforward (same protocol as EGFR docking). ADMET
scoring uses the existing model with sigmoid transforms. Weight changes are trivial.
The only technically uncertain element is BSI integration (Option C), which depends on
code availability and may introduce information leakage concerns. Recommendation: defer
BSI to supplementary analysis.

### Scientific Feasibility

Moderate-High. The scientific case for revision is strong. The risk is that the revision
is perceived as post-hoc optimization. The modifications suggested above (pre-specified
primary configuration, calibration-based primary selection, selectivity validation) are
designed to mitigate this perception. Without these safeguards, the scientific
feasibility drops to Moderate because reviewers will attack the motivation.

### Timeline Feasibility

Realistic. The 2-3 week estimate is credible for the core work (weight changes, ADMET
integration, retrospective re-run). The selectivity cross-docking (200 GPU-hours) is
the bottleneck. Adding the calibration step (50-100 known inhibitors x 5 off-targets =
250-500 docking runs) adds approximately 1 day. Adding the selectivity validation
against KINOMEscan data adds approximately 1 day of analysis. These are minor additions
that substantially strengthen the proposal.

---

## Suggested Modifications

1. **Pre-specify the primary scoring configuration using an outcome-independent
   calibration.** Before running ANY head-to-head comparisons, score the 94 approved
   kinase inhibitors under Config A, B, and C. Select the configuration that best
   discriminates approved kinase inhibitors from random drug-like molecules (highest
   AUC-ROC for "is this an approved kinase drug?"). Lock this as the primary
   configuration. This selection criterion is orthogonal to the static-vs-state-aware
   comparison, eliminating accusations of outcome-driven weight selection.

2. **Increase Dirichlet sensitivity samples from 100 to at least 1000 (preferably
   5000).** The compute cost is negligible (re-weighting precomputed component scores).
   The statistical benefit is substantial: 95% CIs on the "fraction favoring
   state-aware" shrink from +/- 0.10 to +/- 0.014. Report the fraction with a 95%
   bootstrap CI. Also report the median and IQR of the score difference between
   state-aware and static across all Dirichlet samples, not just the binary "which
   wins" count.

3. **Validate the selectivity proxy before incorporating it into scoring.** Dock 38
   kinase inhibitors from Karaman et al. (2008) against the 5 off-target kinases.
   Compute Spearman correlation between GNINA-derived selectivity and experimental
   S(10) selectivity. Report the correlation. If rho < 0.3, downweight selectivity
   from 0.15 to 0.05 in the primary configuration and label it an exploratory
   component. If rho >= 0.3, retain at 0.15. This decision rule is pre-specified and
   data-driven.

4. **Keep similarity metric changes strictly orthogonal to weight changes.** If BSI
   or pharmacophore fingerprints are tested, run a 2x2 factorial: {Tanimoto, BSI} x
   {original weight, revised weight}. Report all 4 cells. Do not confound metric and
   weight effects.

5. **Report the full Dirichlet joint distribution, not just the binary outcome.**
   Instead of only reporting "X% of configurations favor state-aware," report:
   - The mean score difference (state-aware minus static) as a function of each
     component weight (6 partial dependence plots)
   - The weight regions where state-aware wins vs where static wins (a 6D decision
     boundary, visualized via 2D projections or parallel coordinate plots)
   - The variance of the score difference across Dirichlet samples (high variance =
     scoring-sensitive; low variance = robust)
   This provides far richer information than a single percentage.

6. **Add a formal pre-registration statement.** Before running the revised scoring
   analysis, write a one-page analysis plan specifying: (a) the primary scoring
   configuration, (b) the primary comparison metric (BEDROC or EF@10), (c) the success
   criterion (non-overlapping 95% CIs), (d) the multiple testing adjustment (if any),
   and (e) the sensitivity analyses to be performed. Timestamp this on OSF or as a
   dated commit in the repository. This costs hours and provides substantial credibility.

---

## Alternative Approaches

**Approach 1: Learn the weights from data.** Rather than hand-specifying 3 weight
configurations, learn the weights that maximize discrimination between known approved
EGFR drugs and decoys using logistic regression or a simple MLP. The 6 component scores
are features; the label is "approved drug vs decoy." The learned weights reflect which
components are informative for identifying real drugs. This is more principled than
hand-tuning but introduces overfitting risk (mitigated by leave-one-drug-out
cross-validation). This approach has precedent: REINVENT 4 uses learned component
weights for multi-objective optimization (Loeffler et al. 2024).

**Approach 2: Report the Pareto front across scoring functions.** Rather than choosing
one scoring function, report which candidates appear on the Pareto front across ALL
scoring configurations (original, Config A, B, C). Candidates that are Pareto-optimal
under every configuration are "robustly optimal." This avoids the single-configuration
selection problem entirely. The fraction of robustly optimal candidates from each
pipeline (static vs state-aware) is a scoring-function-agnostic metric.

**Approach 3: Use rank aggregation instead of weighted sums.** Replace the weighted
sum of 6 component scores with a rank aggregation method (e.g., Borda count or
Kemeny-Young). Rank each candidate on each component, then aggregate ranks. This
eliminates the weight selection problem entirely -- there are no weights to choose.
Rank aggregation methods are well-studied in social choice theory and have been applied
to virtual screening (Swamidass et al., JCIM 2009). The downside is reduced sensitivity
to score magnitudes.

---

## Impact on Publication Narrative

This proposal is essential for publication credibility but is the most dangerous element
of the research agenda from a statistical perception standpoint. If executed without the
safeguards above, a skeptical reviewer can construct a devastating narrative: "The
authors changed the scoring function until their preferred method won, then reported
both scorings to appear balanced while featuring the favorable one as the primary
analysis." This narrative is unfair -- the scientific case for revision is genuine --
but it is easy to construct and difficult to refute without pre-registration.

With the modifications above (calibration-based primary selection, pre-specified
configuration, validated selectivity proxy, increased Dirichlet coverage), the narrative
becomes: "The authors identified evidence-based deficiencies in their scoring function,
validated the revision against an independent dataset of approved kinase drugs, pre-
specified the primary analysis, and showed that the enrichment result is robust to
scoring function design." This is a much stronger paper.

The scoring revision itself is a publishable methodological insight: "Conventional
similarity-based scoring systematically penalizes chemical exploration in generative
drug design." This claim stands regardless of the static-vs-state-aware outcome and
may be the most broadly impactful contribution of the paper.

---

## References

1. Karaman MW, Herrgard S, et al. (2008). A quantitative analysis of kinase inhibitor
   selectivity. *Nature Biotechnology*, 26(1):127-132. DOI: 10.1038/nbt1358 -- 38
   kinase inhibitors profiled across 317 kinases. Provides experimental selectivity
   data for GNINA cross-docking calibration.

2. Subramanian V, Srinivasan B, et al. (2019). Docking scoring functions -- current
   limitations and future developments. *Physical Chemistry Chemical Physics*. --
   Cross-target docking correlation limitations.

3. Sorgenfrei FA, Fulle S, Merget B. (2024). Kinase-Bench: Comprehensive Benchmarking
   Tools and Guidance for Achieving Selectivity in Kinase Drug Discovery. *JCIM*,
   64(24):9528-9550. DOI: 10.1021/acs.jcim.4c01830 -- 6875 selective ligands, 75
   kinases, benchmarks docking for selectivity.

4. Sorgenfrei FA, et al. (2024). Docking-Informed Machine Learning for Kinome-wide
   Affinity Prediction. *JCIM*. PMC11684025. -- ML-enhanced docking achieves R^2 =
   0.63-0.74, vs raw Vina R^2 = 0.04.

5. Chen Y, et al. (2025). Beyond Tanimoto: a learned bioactivity similarity index
   enhances ligand discovery. *Frontiers in Bioinformatics*, 5:1695353. -- BSI trained
   with leave-one-protein-out on ChEMBL; EGFR activity data in training set implies
   potential information leakage for EGFR retrospective task.

6. Nicholls A. (2016). Confidence limits, error bars, and method comparison in
   molecular modeling. *JCAMD*, 30:103-126. -- Statistical framework for method
   comparison in computational chemistry.

7. Swamidass SJ, Azencott CA, Daily K, Baldi P. (2009). A CROC stronger than ROC:
   measuring, visualizing and optimizing early retrieval. *Bioinformatics*,
   25(10):1348-1356. -- Rank aggregation approaches for virtual screening.

8. Polaris Consortium. (2025). Practically significant method comparison protocols for
   molecular property prediction. *JCIM*, 65:18. -- Pre-specified endpoints and
   multi-dataset evaluation as the new standard.

9. Loeffler HH, et al. (2024). Reinvent 4: Modern AI-driven generative molecule design.
   *Journal of Cheminformatics*, 16:20. -- Multi-component scoring with learned weights.

10. Benchmarking Cross-Docking Strategies in Kinase Drug Discovery. *JCIM*, 2024.
    DOI: 10.1021/acs.jcim.4c00905 -- Standard docking has fundamental limitations for
    cross-target selectivity prediction due to rigid protein models and scoring artifacts.
