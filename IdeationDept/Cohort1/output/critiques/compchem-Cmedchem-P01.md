---
agent: Senior Computational Chemist
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: medchem-P01
---

# Critique: Scoring Function Revision with ADMET and Selectivity Integration

## Reviewing Agent

Dr. Senior Computational Chemist (compchem). 20+ years in molecular modeling, free
energy calculations, force field development, and the physics of molecular recognition.
This review evaluates medchem-P01 from the perspective of physical validity,
thermodynamic consistency, and whether the proposed scoring components are on sound
theoretical footing. I focus on what physics the revision captures, what it still
ignores, and whether the heterogeneous components can be meaningfully combined in a
weighted sum.

## Proposal Summary

medchem-P01 proposes replacing StateBind's 4-component scoring function (reference
similarity 0.35, drug-likeness 0.30, docking 0.20, state specificity 0.15) with a
6-component function that adds ADMET safety and a cross-docking selectivity proxy while
reducing reference similarity weight from 0.35 to 0.10 and replacing QED with
kinase-specific desirability functions. All results would be reported under both
original and revised scoring.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The diagnosis of the current scoring function's pathologies is
excellent and well-evidenced, but the proposed cure -- adding two more heterogeneous
components to a linear weighted sum -- lacks thermodynamic coherence and ignores the
dominant physical driving force in kinase binding: water displacement.

---

## Strengths

1. **The problem diagnosis is rigorous and damning.** The observation that reference
   similarity at 35% weight penalizes the very novelty a generative model should
   produce is a first-order scientific flaw. The Chen et al. (2025) evidence that 60%
   of similarly bioactive pairs have Tanimoto < 0.30 is quantitative and compelling.
   The QED calibration failure -- osimertinib scoring 0.31, 48% of approved kinase
   inhibitors violating Lipinski (Roskoski 2026) -- is a clear indictment of the
   current drug-likeness component. This problem identification alone is a publishable
   contribution.

2. **Kinase-calibrated ADMET thresholds are pharmacologically sound.** Centering the
   hERG sigmoid at 1.0 uM rather than the standard 10 uM threshold, justified by
   osimertinib's approved status at 0.57 uM, is defensible under ICH S9 oncology
   guidelines. The evidence base (Zhong et al. 2023, Wang et al. 2021) is specific and
   verifiable. This is the kind of domain-appropriate calibration that reviewers want to
   see.

3. **Dual reporting protocol is scientifically essential.** Presenting results under
   both original and revised scoring prevents accusations of score-hacking. The proposal
   correctly identifies this as non-negotiable and specifies component-ablation analysis
   and Dirichlet weight sensitivity across 6 components. The transparency of this
   approach is a genuine strength.

4. **The state-selectivity hypothesis is testable and valuable.** If DFG-out-targeting
   candidates show higher selectivity scores than DFGin/aCin candidates (consistent with
   Ung et al. 2015, Gini 0.76 vs 0.58 for type II vs type I), this transforms the
   paper's narrative from retrospective enrichment to mechanistic insight. This is the
   most publication-impactful element of the proposal.

5. **Kinase-specific desirability functions are an improvement.** Replacing QED's
   general oral-drug calibration with property ranges derived from 94 FDA-approved kinase
   inhibitors is a meaningful correction. The geometric mean composite with per-property
   decay functions is a standard and defensible approach in medicinal chemistry MPO
   (Waring et al. 2015).

## Weaknesses

1. **GNINA cross-docking is physically inadequate for selectivity prediction.**
   - **Severity:** Critical
   - **Addressable?** Partially -- with significant caveats in the write-up and
     additional normalization work

   The proposal treats GNINA cross-docking against 5 off-target kinases as a selectivity
   proxy. This is physically problematic for several reasons:

   **(a) Rigid receptor approximation across different kinase families.** GNINA uses a
   rigid receptor. Different kinases have different backbone flexibility, loop dynamics,
   and induced-fit behavior. EGFR, ABL1, SRC, BRAF, and MET have structurally distinct
   hinge regions, P-loops, and activation loops. A molecule docked rigidly into an EGFR
   crystal structure and rigidly into an ABL1 crystal structure is not undergoing the
   same physical process. Kinase cross-docking benchmarks (Godbey et al., JCIM 2024)
   show that even within a single kinase family, cross-docking success rates drop from
   73% (self-docking) to 37% (cross-docking with GNINA). Across kinase families with
   different conformational preferences, accuracy degrades further.

   **(b) Scoring bias from pocket geometry differences.** Wang et al. (PLoS ONE 2017)
   demonstrated that docking scores are systematically biased by pocket size and
   hydrophobicity: correlation between pocket contact area and median docking score
   reached r = -0.73 for DOCK and r = -0.74 for Vina. Larger, more hydrophobic pockets
   receive systematically higher (more favorable) docking scores regardless of true
   binding affinity. The five proposed off-target kinases have pockets of different
   sizes: the DFG-out allosteric extension in ABL1 (2HYY) is substantially larger
   than the active-state ATP pocket in SRC (2SRC). A molecule would score "better"
   in ABL1 purely because of pocket volume, not because of genuine binding. The
   proposal's acknowledgment of this issue (Section: Risk Assessment) is appropriate,
   but the proposed per-target z-score normalization requires reference compound sets
   for each off-target kinase. These reference sets must include both known binders AND
   known non-binders at each kinase, and the non-binders must be matched for
   physicochemical properties to avoid artificial separation. This calibration effort is
   non-trivial and is not adequately scoped.

   **(c) GNINA's CNN scoring function was trained on PDBbind, not on selectivity data.**
   GNINA's CNN models were trained to predict binding (pose correctness and affinity),
   not to discriminate between on-target and off-target binding. There is no published
   benchmark demonstrating that GNINA score differences across targets correlate with
   experimental selectivity ratios. The MMCLKin contrastive learning framework (Nature
   Communications, 2025) was specifically designed for kinase selectivity prediction and
   outperformed Glide SP -- a program with better cross-target calibration than GNINA.
   Using GNINA for selectivity when purpose-built tools exist is a suboptimal choice.

   **(d) Single structure per off-target kinase is a snapshot, not an ensemble.** The
   proposal assigns one PDB structure per off-target kinase. But each kinase samples
   multiple conformational states. ABL1 has 136 KinCore chains spanning active and
   inactive states (per structbio-R02). Using one structure (2HYY, DFGout) means the
   selectivity proxy tests whether a molecule binds inactive ABL1, not whether it binds
   ABL1 in its preferred binding state. A molecule might dock poorly to DFGout ABL1 but
   well to DFGin ABL1, which is the therapeutically relevant off-target concern.

2. **Mixing physics-based and ML-based scores in a linear sum is thermodynamically
   incoherent.**
   - **Severity:** Major
   - **Addressable?** Yes -- by acknowledging the limitation explicitly and considering
     Pareto-based alternatives

   The proposal combines in a linear weighted sum: (a) GNINA docking scores --
   empirical energy function approximating binding free energy in kcal/mol, mapped to
   [0,1] via sigmoid; (b) ADMET composite -- ML-predicted probabilities of biological
   endpoints (hERG inhibition, CYP3A4 metabolism), mapped to [0,1] via kinase-calibrated
   sigmoids; (c) Tanimoto similarity -- a unitless topological metric with no energy
   correspondence; (d) kinase desirability functions -- empirical property ranges with no
   thermodynamic basis; (e) state specificity -- a geometric measure of pocket-ligand
   complementarity.

   These quantities are not on the same thermodynamic footing. A 0.7 from GNINA docking
   approximates (poorly) a binding free energy near -7 kcal/mol. A 0.7 from the hERG
   sigmoid means the predicted hERG IC50 is near the kinase-calibrated threshold. A 0.7
   from Tanimoto means 70% of fingerprint bits overlap with reference drugs. These are
   physically incommensurable quantities. Summing them with weights assumes that a 0.1
   improvement in docking score is equivalent to a 0.1 improvement in ADMET score, which
   has no physical justification.

   This is a recognized problem in the field. BMC Bioinformatics (2024) notes that
   standard scoring functions "incorrectly assume that individual interactions contribute
   toward total binding affinity in an additive manner when in reality noncovalent
   interactions often depend on one another in a nonlinear manner." Multi-objective
   optimization theory (Fromer & Coley, Patterns 2023) establishes that weighted sum
   scalarization can only find solutions on the convex hull of the Pareto front, missing
   potentially optimal solutions in non-convex regions. With 6 heterogeneous objectives,
   the Pareto front is likely highly non-convex.

   The proposal compounds this problem by going from 4 to 6 components. More components
   in a weighted sum means more arbitrary weight choices, more normalization sensitivity,
   and more opportunities for the weight vector to determine the outcome rather than the
   underlying molecular properties.

3. **The dominant physics of kinase binding -- water displacement -- remains absent.**
   - **Severity:** Major
   - **Addressable?** Yes -- by integrating the GIST analysis from compchem-P01

   The proposal adds ADMET and selectivity but does not address the single largest
   thermodynamic driving force in kinase-ligand binding: displacement of ordered water
   molecules from the ATP pocket. Published data from WaterMap studies on SRC kinase
   (Robinson et al. 2010, 2014) show 21 hydration sites with positive (unfavorable) free
   energy in the ATP pocket, with individual water displacement contributions of 2.6-6.6
   kcal/mol per water. AutoDock-GIST (Uehara & Tanaka 2016) demonstrated that
   incorporating water thermodynamics improves affinity prediction R-squared from 0.49 to
   0.58 and docking success rate from 82.6% to 95.7% on test sets. The improvement from
   incorporating water thermodynamics (9 percentage points in R-squared) is likely larger
   than the improvement from adding any of the proposed new scoring components.

   Different conformational states have different water networks -- this is directly
   relevant to the state-aware hypothesis. The DFG-out pocket is more hydrophobic than
   the DFG-in pocket and gains more binding free energy from water displacement. Adding
   a GIST-derived solvation term would simultaneously improve scoring accuracy AND
   provide physics-based evidence for why different states yield different binding
   outcomes. This is a missed opportunity that my own proposal (compchem-P01) addresses.

   At minimum, the proposal should acknowledge that water thermodynamics is the largest
   omitted physical term and discuss how the GIST analysis could be integrated as a 7th
   component or as a correction to the docking component.

4. **Score normalization across 6 heterogeneous components is under-specified.**
   - **Severity:** Major
   - **Addressable?** Yes -- with additional methodological detail

   The proposal maps all components to [0,1] using sigmoid transforms, but the
   resulting distributions may have very different shapes, means, and variances. A
   sigmoid(-vina_score / 3) applied to GNINA outputs and a sigmoid((predicted_IC50 -
   1.0) / 0.5) applied to hERG predictions produce [0,1] values with different
   distributional properties. If the docking component is tightly clustered around 0.6
   with standard deviation 0.05, while the ADMET component spans 0.2-0.9 with standard
   deviation 0.20, then a 0.15 weight on ADMET has 4x the effective discriminative power
   of a 0.20 weight on docking. The nominal weights do not reflect the actual
   contribution of each component to the final ranking.

   The proposal mentions this issue for selectivity (cross-target score normalization)
   but does not address it for the overall function. Standard practice in multi-criteria
   decision analysis requires either: (a) rank-based normalization (convert each
   component to ranks, then combine), which is distribution-free but loses magnitude
   information; or (b) z-score normalization within each component, which equalizes
   variance but can amplify noise in low-variance components; or (c) probability density
   function normalization as proposed by Wang et al. (2017), which improved Glide
   accuracy by 21.5 percentage points in cross-target scoring. The proposal should
   specify which normalization strategy is used and demonstrate that the chosen weights
   have the intended effect on ranking.

5. **BSI as a Tanimoto replacement captures statistical patterns, not physics.**
   - **Severity:** Minor
   - **Addressable?** Yes -- by using BSI only as a sensitivity analysis, not as the
     primary similarity metric

   The proposal's Option C suggests replacing Tanimoto with BSI (Bioactivity Similarity
   Index, Chen et al. 2025). BSI is a neural network trained on ChEMBL co-activity data
   using leave-one-protein-out cross-validation with 256-bit Morgan fingerprint inputs.
   While BSI achieves 12x improvement over Tanimoto in mean active rank (3.9 vs 45.2),
   it is a learned statistical pattern, not a physics-based SAR model. BSI does not
   encode binding thermodynamics, conformational preferences, or interaction geometries.
   It predicts whether two molecules are co-active based on fingerprint similarity to
   training examples of co-activity. The Chen et al. paper itself acknowledges
   limitations: the model depends on training data diversity, suffers from scarcity of
   reliable negative data, and uses a "simple and efficient 256-bit representation" that
   may miss relevant structural features.

   For StateBind, where the goal is to evaluate generated molecules with potentially
   novel scaffolds outside ChEMBL's training distribution, BSI's learned patterns may
   not extrapolate. The proposal correctly recommends Option A (weight reduction alone)
   as the primary approach. BSI should remain a sensitivity analysis, clearly labeled as
   a data-driven alternative to a physics-free metric.

6. **The linear weighted sum lacks theoretical justification for 6 heterogeneous
   objectives.**
   - **Severity:** Major
   - **Addressable?** Yes -- by incorporating Pareto analysis as a complementary
     approach

   The proposal does not justify why a linear weighted sum is the appropriate aggregation
   method for 6 physically heterogeneous components. The mathematical literature
   establishes that weighted sum scalarization can only recover Pareto optimal solutions
   on the convex hull of the Pareto front (Marler & Arora 2004). For non-convex
   multi-objective problems -- which drug design problems almost certainly are, given
   the complex interdependencies between binding affinity, ADMET, and selectivity -- the
   weighted sum systematically misses optimal solutions.

   Multi-objective optimization research in drug design (Fromer & Coley, Patterns 2023;
   Liu et al., Advanced Science 2025) increasingly advocates Pareto-based approaches
   that reveal trade-off surfaces rather than collapsing them into a single scalar.
   StateBind already has Pareto optimization infrastructure in `ranking/pareto.py`. The
   PMMG algorithm (Advanced Science 2025) achieved 51.65% multi-objective success using
   Pareto MCTS, explicitly avoiding weighted sum scalarization.

   Furthermore, recent work on preferential multi-objective Bayesian optimization
   (CheapVS, arxiv 2503.16841) demonstrates that expert preferences can be captured
   through pairwise comparisons rather than explicit weight vectors, achieving 42%
   accuracy in identifying known EGFR drugs while screening only 6% of a 100K library
   -- outperforming affinity-only baselines (22%). This approach avoids the arbitrary
   weight assignment that is the fundamental weakness of the linear weighted sum.

   With 6 components, the dimensionality of the weight space is 5 (6 weights summing
   to 1). The Dirichlet sensitivity analysis samples this 5-simplex, but the proposal
   reports only the fraction of configurations favoring state-aware vs static. This
   collapses a 5-dimensional trade-off surface into a single binary statistic. Pareto
   analysis would preserve the full trade-off structure and show WHICH objectives create
   tension between the pipelines.

---

## Feasibility Assessment

### Technical Feasibility

The scoring revision itself is technically straightforward. StateBind's architecture
already supports arbitrary weight configurations and new scoring components. ADMET
integration requires only sigmoid transforms on existing model outputs. The kinase-
specific desirability functions are simple to implement.

The cross-docking selectivity proxy is feasible but requires more work than estimated.
Preparing 5 off-target receptor PDBQT files and running 2,455 docking calculations on
Bouchet H200 GPUs is within scope. However, the calibration step -- assembling
reference compound sets (known binders and property-matched non-binders) for each
off-target kinase from ChEMBL, running those through GNINA, and computing per-target
normalization parameters -- adds 1-2 weeks and is not included in the timeline.

### Scientific Feasibility

The diagnosis (scoring function bias) will hold. The proposed corrections (weight
reduction, kinase desirability, ADMET) are sound. The selectivity proxy will produce
numbers, but their physical meaning is uncertain: the correlation between GNINA
cross-docking differences and experimental selectivity ratios is unknown and likely
weak (R-squared < 0.3 based on the general accuracy of empirical docking for ranking).
The proposal should frame cross-docking selectivity as a "computational selectivity
indicator" not a "selectivity prediction."

The dual reporting protocol ensures scientific integrity regardless of how the
selectivity proxy performs. Even if selectivity scores are noisy, the component-ablation
analysis and weight sensitivity study will be informative.

### Timeline Feasibility

The 2-3 week estimate is optimistic. The cross-docking calibration work (reference sets,
normalization parameters, validation) adds at least 1 week. The comprehensive dual
reporting (all 9 metrics under both scoring regimes) adds another week. A more realistic
estimate is 4-5 weeks.

---

## Suggested Modifications

1. **Add a GIST water thermodynamics term or correction.** Instead of 6 components,
   consider replacing the raw GNINA docking score with a GIST-corrected docking score.
   AutoDock-GIST demonstrated that water thermodynamics improves affinity prediction
   R-squared by 9 percentage points. Alternatively, add a 7th component for water
   displacement favorability per state, which directly strengthens the state-aware
   hypothesis. The GIST analysis from compchem-P01 (estimated at 2-3 weeks, 5-7 GPU-
   days) could run in parallel with the selectivity cross-docking.

2. **Implement Pareto analysis as the primary aggregation with weighted sum as
   secondary.** StateBind already has Pareto infrastructure. Compute the Pareto front
   across all 6 (or 7) objectives for both static and state-aware candidates. Report
   Pareto dominance statistics (what fraction of state-aware candidates Pareto-dominate
   all static candidates, and vice versa) as the primary comparison. Report the weighted
   sum analysis as a secondary, simpler metric. This avoids the arbitrary weight
   assignment problem and provides richer information about multi-objective trade-offs.

3. **Normalize component distributions before weighting.** Apply z-score normalization
   within each component across the full candidate pool (static + state-aware) before
   computing the weighted sum. This ensures that nominal weights reflect actual
   discriminative power. Report the mean and standard deviation of each component's
   distribution before and after normalization. Alternatively, use rank-based
   normalization as a robustness check.

4. **Downgrade the selectivity proxy claims.** Frame cross-docking selectivity as a
   "computational selectivity indicator based on rigid-receptor docking" not a
   "selectivity prediction." Acknowledge that: (a) rigid-receptor docking across
   different kinase families introduces systematic biases from pocket geometry
   differences; (b) single structures per off-target kinase miss conformational
   diversity; (c) no benchmark exists for GNINA cross-target selectivity prediction.
   The selectivity signal may be directionally correct (DFG-out candidates scoring
   better) but should not be over-interpreted quantitatively.

5. **Specify the reference compound calibration protocol for selectivity normalization.**
   For each off-target kinase, assemble from ChEMBL: (a) 50-100 known binders with
   measured IC50 < 1 uM; (b) 50-100 property-matched non-binders (same MW, cLogP
   distribution but no reported activity). Dock all reference compounds, compute the
   per-target score distribution, and use the mean and standard deviation for z-score
   normalization. Without this calibration, raw GNINA scores across different targets
   are not comparable (Wang et al. 2017 showed pocket contact area correlates with
   median docking score at r = -0.73).

6. **Consider ensemble docking for at least the EGFR on-target.** Even if off-target
   kinases use single structures (due to compute constraints), the EGFR on-target
   docking should use ensemble docking with 3-5 structures per state. Godbey et al.
   (JCIM 2024) showed that docking into multiple structures "significantly increased the
   chance to generate a low RMSD docking pose." This is particularly important for the
   DFG-out and aC-out states where crystal structure availability is limited and each
   structure represents a narrow snapshot of the conformational basin.

---

## Alternative Approaches

**Pareto dominance as the primary metric.** Rather than a 6-component weighted sum,
compute the 6-dimensional Pareto front for each pipeline and compare Pareto dominance
statistics. This is distribution-free, requires no weight assignment, and reveals
trade-off structure. StateBind's existing `ranking/pareto.py` infrastructure supports
this. The key metric becomes: "What fraction of state-aware candidates are Pareto-
non-dominated?" and "How does the Pareto front of state-aware candidates compare to
that of static candidates in the docking-selectivity plane, the ADMET-docking plane,
etc.?"

**GIST-corrected docking instead of raw GNINA.** Rather than adding more components to
compensate for GNINA's deficiencies, improve the docking component itself. GIST water
thermodynamics computed for all 4 EGFR states (from compchem-P01) could be used to
correct GNINA docking scores: GNINA_corrected = GNINA_raw + alpha * GIST_displacement.
This has the advantage of staying within the docking score's thermodynamic framework
rather than mixing in unrelated quantities.

**MMCLKin for selectivity instead of cross-docking.** If the goal is kinase selectivity
prediction, purpose-built ML models like MMCLKin (Nature Communications 2025) that
integrate geometric graph and sequence networks for kinase-inhibitor selectivity may
outperform GNINA cross-docking. MMCLKin was benchmarked against Glide SP and showed
superior generalizability on diverse kinase-drug datasets. This would require evaluating
MMCLKin's public availability and computational requirements.

---

## Impact on Publication Narrative

The scoring revision is essential for publication credibility. No reviewer at JCIM or
Nature Computational Science will accept a scoring function where 35% of the weight is
Tanimoto similarity to 3 known drugs. The diagnosis of this flaw and its correction is
itself a publishable insight.

However, the proposal's impact on the narrative is double-edged. If the revised scoring
causes state-aware to win on mean score (where it currently loses 0.4378 vs 0.5437),
sophisticated reviewers will ask: "Did you design the scoring function to produce the
desired result?" The dual reporting protocol mitigates this, but only if the original
scoring results are presented with equal prominence (not buried in supplements). The
proposal suggests presenting revised scoring as primary with original in supplementary
-- I recommend the opposite: present both in the main text, side by side, and let the
reader see that the conclusion depends on what you choose to measure.

The selectivity component, if the DFG-out selectivity hypothesis holds, adds genuine
mechanistic insight. But the cross-docking methodology is the weakest link in the
chain. Overstating the precision of GNINA cross-docking selectivity scores would
invite immediate criticism from any reviewer familiar with docking accuracy. Frame it
as a computational indicator, not a quantitative prediction.

The largest missed opportunity is the absence of water thermodynamics. A GIST-derived
figure showing different water networks in each conformational state would be the single
most visually compelling and physically grounded piece of evidence for the state-aware
hypothesis. It would also address the reviewers' most likely physics-based objection:
"You claim these states are different, but where is the physical evidence?" Adding
GIST to the scoring revision would make the paper substantially stronger than adding
ADMET and selectivity alone.

---

## References

1. Godbey E, et al. (2024). Benchmarking Cross-Docking Strategies in Kinase Drug
   Discovery. *J Chem Inf Model*, 64(24):9217-9230.
   DOI: 10.1021/acs.jcim.4c00905 -- Cross-docking success rates: 73% self-docking vs
   37% cross-docking with GNINA; ensemble docking improves success rates.

2. Wang C, et al. (2017). The scoring bias in reverse docking and the score
   normalization strategy to improve success rate of target fishing. *PLoS ONE*,
   12(2):e0171433. DOI: 10.1371/journal.pone.0171433 -- Pocket contact area correlates
   with median docking score at r = -0.73 (DOCK), -0.74 (Vina); normalization improves
   Glide accuracy by 21.5 percentage points.

3. Uehara S, Tanaka S. (2016). AutoDock-GIST: Incorporating Thermodynamics of
   Active-Site Water into Scoring Function for Accurate Protein-Ligand Docking.
   *Molecules*, 21(11):1604. PMC6274120. -- GIST integration improves affinity
   prediction R^2 from 0.49 to 0.58; docking success rate from 82.6% to 95.7%.

4. Robinson DD, et al. (2010). Understanding Kinase Selectivity Through Energetic
   Analysis of Binding Site Waters. *ChemMedChem*, 5(4):618-627. -- WaterMap on SRC:
   21 hydration sites with positive free energy; displacement contributions 2.6-6.6
   kcal/mol per water.

5. Fromer JC, Coley CW. (2023). Computer-aided multi-objective optimization in small
   molecule discovery. *Patterns*, 4(2):100678. DOI: 10.1016/j.patter.2023.100678 --
   Weighted sum recovers only convex Pareto hull; Pareto methods preferred for
   non-convex drug design problems.

6. Liu Y, et al. (2025). A Multi-Objective Molecular Generation Method Based on
   Pareto Algorithm and Monte Carlo Tree Search. *Advanced Science*, 12:2410640.
   DOI: 10.1002/advs.202410640 -- PMMG achieves 51.65% multi-objective success;
   vectorized reward avoids weighted sum scalarization.

7. CheapVS: Preferential Multi-Objective Bayesian Optimization for Drug Discovery.
   (2025). arXiv:2503.16841. -- Expert preference-based BO on 100K EGFR library:
   42% accuracy identifying known drugs (vs 22% affinity-only) while screening 6%
   of library.

8. BMC Bioinformatics (2024). A comprehensive survey of scoring functions for protein
   docking models. DOI: 10.1186/s12859-024-05991-4 -- Common weights across energy
   terms are gene-family dependent; additive assumption ignores nonlinear interactions.

9. McNutt AT, et al. (2021). GNINA 1.0: molecular docking with deep learning. *J
   Cheminformatics*, 13:43. DOI: 10.1186/s13321-021-00522-2 -- CNN rescoring improves
   pose prediction (73% vs 58% Top1) but not thermodynamic ranking accuracy.

10. Sunseri J, Koes DR. (2025). GNINA 1.3: the next increment in molecular docking
    with deep learning. *J Cheminformatics*, 17:19. DOI: 10.1186/s13321-025-00973-x --
    Updated CNN on CrossDocked2020 v1.3; knowledge-distilled models for throughput.

11. Chen Y, et al. (2025). Beyond Tanimoto: a learned bioactivity similarity index
    enhances ligand discovery. *Frontiers in Bioinformatics*, 5:1695353. -- BSI mean
    active rank 3.9 vs Tanimoto 45.2; acknowledges training data diversity limitations
    and negative data scarcity.

12. Marler RT, Arora JS. (2004). Survey of multi-objective optimization methods for
    engineering. *Structural and Multidisciplinary Optimization*, 26:369-395. --
    Weighted sum finds only convex Pareto hull solutions.

13. Kim J, et al. (2025). Enhancing kinase-inhibitor activity and selectivity prediction
    through contrastive learning. *Nature Communications*, 16:5093. -- MMCLKin framework
    outperforms Glide SP on kinase selectivity prediction benchmarks.

14. Waring MJ, et al. (2015). An analysis of the attrition of drug candidates from four
    major pharmaceutical companies. *Nature Reviews Drug Discovery*, 14:475-486. --
    Multi-parameter optimization principles in pharma practice.

15. Multi-and many-objective optimization: present and future in de novo drug design.
    (2024). *Frontiers in Chemistry*, 11:1288626. PMC10773868. -- Beyond 3 objectives
    "almost all solutions become non-dominated," compromising convergence; NSGA-III
    recommended for 4+ objectives.
