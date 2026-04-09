---
agent: Senior Cheminformatician
round: 3
date: 2026-04-09
type: critique
proposal_reviewed: biophys-P01
---

# Critique: Kinetic Dimension -- Integrating Binding Kinetics into StateBind via a 3-Tier Scoring Cascade and the Conformational Selection Narrative

## Reviewing Agent

**Senior Cheminformatician (cheminfo)** -- Cohort2, IdeationDept

Expertise: Molecular representations, similarity metrics, scoring function design and
mathematical properties, chemical descriptor spaces, applicability domains, and
publication-standard quantitative methodology for computational drug design.

---

## Proposal Summary

biophys-P01 proposes adding a kinetic dimension to StateBind through three components:
(A) a 5th scoring component using a 3-tier cascade (tauRAMD -> ML koff -> state-kinetic
heuristic) weighted at 10%, (B) a zero-compute conformational selection narrative
reframing the 10x enrichment as implicit kinetic optimization, and (C) a 10-compound
SPR validation panel with HDX-MS conformational state confirmation. The weight
rebalancing reduces reference_similarity from 0.35 to 0.30 and druglikeness from 0.30
to 0.25. The proposal claims this would make StateBind "the first conformational-state-
aware drug design pipeline with integrated kinetic prediction."

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The biophysical reasoning is rigorous and the conformational selection
narrative is genuinely publication-enhancing, but the scoring component needs mathematical
justification for its weight, the Tier 3 heuristic creates problematic redundancy with
state_specificity, and the proposal must be coordinated with scoring reform (cheminfo-P01)
to avoid conflicting weight changes.

---

## Strengths

### S1. The Conformational Selection Narrative (Component B) Is Excellent

The 5-step causal chain linking state-aware design to conformational selection to slow
koff to long residence time to in vivo efficacy is well-constructed and well-cited. Each
link rests on published evidence from independent groups (Copeland, Wood, Kokh, Holdgate,
Manley). The lapatinib vs. gefitinib comparison (430 min vs. <14 min RT despite weaker
equilibrium affinity) is the single most compelling biophysical argument for why state-
aware design matters. The draft Discussion section text (Section B.5) is essentially
publication-ready.

This component requires zero compute, zero code changes, and zero external cost, yet it
arguably adds more publication value than Components A or C. The prioritization of
B -> A -> C is well-judged.

### S2. The Zero-Approved-Type-II-EGFR-Inhibitor Angle Is Novel

The observation that no FDA-approved EGFR inhibitor occupies the Type II DFG-out design
space, despite strong biophysical rationale for long residence time and high selectivity,
is a genuinely insightful framing. This positions StateBind's DFGout-targeting pipeline
as exploring a clinically underexploited opportunity. This is not overclaiming -- it is a
factual observation about the clinical landscape combined with a well-supported biophysical
hypothesis.

### S3. The Three-Tier Cascade Architecture Is Consistent with StateBind

The proposal correctly identifies the docking_proxy fallback pattern (GNINA -> MPNN ->
DockingProxy MLP -> stub) as architectural precedent. Mirroring this with
tauRAMD -> ML koff -> heuristic maintains the existing design philosophy of graceful
degradation. The config-driven approach (`configs/kinetics.yaml`) follows StateBind
conventions.

### S4. The Experimental Validation Design (Component C) Is Thorough

The SPR panel selection logic is sensible: 3 compounds where pipelines diverge maximally
(state-aware top / static bottom), 2 reversed, 2 concordant, 3 known references. The
inclusion of 4 EGFR variants (WT, L858R, T790M, L858R/T790M) tests mutation sensitivity.
The HDX-MS protocol targets specific structural regions (DFG motif, alpha-C helix,
activation loop) with clear expected outcomes. The cost estimates ($10-52K for SPR,
$30-50K for HDX-MS) are realistic.

### S5. Honest Risk Assessment

The proposal explicitly acknowledges a 50% probability that the kinetic score will not
change the mean score ranking, and states this must be reported honestly. This scientific
honesty is essential and appropriate.

---

## Weaknesses (with Severity and Addressable?)

### W1. The 10% Kinetic Weight Is Not Mathematically Justified [Severity: HIGH, Addressable: YES]

The proposal states that 10% is "carved from reference_similarity (-5%) and druglikeness
(-5%)" with the rationale that "these two components are the most mature and can absorb a
small reduction." This is an appeal to intuition, not a mathematical justification.

The core problem: in a weighted linear scoring function, the weight assigned to a
component should reflect either (a) its predictive importance for the objective (e.g.,
retrospective enrichment of known actives), (b) its information content relative to other
components (mutual information, ablation importance), or (c) its reliability/confidence
relative to other components. None of these are established for the kinetic score.

Specific concerns:

1. **No calibration data.** The 10% weight implies kinetic scoring contributes roughly
   half the information of state_specificity (15%) and one-third of docking_proxy (20%).
   What evidence supports this relative ranking? The kinetic score at Tier 3 (heuristic)
   is a deterministic function of conformational state -- it adds zero bits of information
   beyond what state_specificity already encodes. At Tier 2 (ML koff with Pearson r =
   0.729-0.838), the prediction noise may be large enough that the effective information
   is below 10%.

2. **Weight sensitivity is acknowledged but deferred.** The proposal mentions a sensitivity
   analysis across 5-20% "to be computed" and invokes Kendall tau > 0.8 as a stability
   criterion. This analysis must be performed BEFORE proposing a weight, not after. If the
   top-10 ranking is invariant across 5-20%, then the exact weight does not matter much;
   if it is sensitive, then 10% is no better than any other value in the range.

3. **The weight rebalancing interacts with cheminfo-P01.** My proposal (cheminfo-P01)
   independently argues for rebalancing reference_similarity based on the finding that
   this single component more than explains the mean-score gap. If both proposals proceed,
   reference_similarity could be reduced twice (from 0.35 to 0.30 in biophys-P01, then
   further in cheminfo-P01's multi-metric reform). The proposals need a coordinated
   weight allocation framework, not independent ad hoc adjustments.

**Suggested fix:** Replace the a priori 10% weight with a data-driven approach:
(a) implement the kinetic cascade first, (b) compute kinetic scores for all candidates,
(c) determine the weight that maximizes retrospective enrichment via grid search over
[0.05, 0.25] in steps of 0.025, (d) report the sensitivity curve as a publication
figure. This is standard practice in multi-objective scoring function design (Chaput
et al., 2016; Walters, 2019).

### W2. Tier 3 Heuristic Creates Redundancy with state_specificity [Severity: HIGH, Addressable: YES]

This is the most technically concerning aspect of the proposal. The Tier 3 state-kinetic
heuristic assigns kinetic scores as a deterministic function of conformational state:

| State | state_specificity typical value | kinetic_T3 |
|-------|--------------------------------|------------|
| DFGout_aCin (one state) | 1.0 | 0.70 |
| DFGout_aCout (one state) | 1.0 | 0.70 |
| DFGin_aCout (one state) | 1.0 | 0.50 |
| DFGin_aCin (one state) | 1.0 | 0.30 |
| Multiple states | < 1.0 | varies |

For a DFGout-specific compound, state_specificity and kinetic_T3 are perfectly correlated:
both are high. For a DFGin-specific compound, both are moderate-to-low. The proposal
acknowledges this synergy (Section A.4), calling it a "positive feedback loop" and arguing
it captures "complementary aspects of the same biophysics." But from a scoring function
design perspective, this is not complementary -- it is collinear.

The mathematical consequence: at Tier 3, the kinetic score is a monotone function of the
conformational state label that is already captured by state_specificity. Adding it as a
separate component with 10% weight is equivalent to increasing the effective weight of
state preference by approximately 7% (0.10 * 0.70 = 0.07 for DFGout binders). A reviewer
trained in multivariate statistics would immediately identify this as feature redundancy
inflating the effective weight of one concept.

The proposal's rebuttal -- "state_specificity measures how many states a compound appears
in, while kinetic_score measures the predicted kinetic consequence" -- is valid only at
Tier 1 (tauRAMD, which produces compound-specific values) and partially at Tier 2 (ML
koff, which depends on molecular structure). At Tier 3, the kinetic score IS the state
label, repackaged.

**Suggested fix:** Two options:
(a) **Remove Tier 3 entirely.** If neither tauRAMD nor ML koff is available, set
kinetic_score = 0.0 (neutral) rather than using a state-derived heuristic that duplicates
state_specificity. This is more honest: "we have no compound-specific kinetic information,
so we assign no kinetic score."
(b) **Merge kinetic and state_specificity into a single state-kinetic component.** Design
a 2D lookup where both the number of states AND the kinetic implications of those states
contribute to a single score, weighted at 20-25% combined. This avoids double-counting
while preserving the biophysical signal.

### W3. The Weight Rebalancing Conflicts with Scoring Reform (cheminfo-P01) [Severity: MODERATE, Addressable: YES]

biophys-P01 proposes: reference_similarity 0.35 -> 0.30, druglikeness 0.30 -> 0.25.
cheminfo-P01 proposes: replacing reference_similarity with a multi-metric, multi-reference
ensemble, and re-deriving all weights from enrichment optimization.

These are incompatible if pursued independently. The biophys-P01 weight rebalancing
assumes the reference_similarity component stays the same (Morgan/Tanimoto to 3 drugs)
but gets less weight. The cheminfo-P01 reform changes what reference_similarity means
(Tversky to 100-300 ChEMBL centroids). If the component changes, its optimal weight also
changes.

**Suggested fix:** The two proposals should be sequenced: first implement cheminfo-P01's
scoring reform (new metric, new reference set, re-derive weights), then add the kinetic
component (biophys-P01's Component A) with its weight determined relative to the reformed
scoring function. This avoids the situation where both proposals independently redistribute
the same weight budget without coordinating.

### W4. Adding a 5th Component to an Already-Questioned Scoring Function Increases Complexity Without Resolving Underlying Issues [Severity: MODERATE, Addressable: PARTIALLY]

The current 4-component scoring function has known issues: the reference_similarity
component explains the mean-score gap, the weights are not empirically optimized, and
the components may have unequal reliability. Adding a 5th component does not address
these problems; it compounds them. Each additional component in a linear combination
reduces the effective influence of every other component and increases the dimensionality
of the weight space that must be tuned.

Moreover, the Pareto optimization in `ranking/pareto.py` currently operates on 4
objectives. As the proposal's own Open Question 7 acknowledges, adding a 5th objective
exacerbates the curse of dimensionality: in high-dimensional Pareto analysis, the
fraction of solutions that are non-dominated grows exponentially, and the Pareto front
becomes less discriminating. For 5 objectives, a substantial fraction of candidates may
be Pareto-optimal, rendering the analysis uninformative.

This is not a reason to reject the kinetic dimension entirely, but it argues for
consolidation rather than expansion. See W2's suggested fix (b): merging kinetic and
state_specificity into a single richer component would add kinetic information without
increasing dimensionality.

### W5. ML koff Descriptor Selection (Tier 2) Is Underspecified [Severity: LOW-MODERATE, Addressable: YES]

The proposal lists four databases for training data (KOFFI, K4DD, PDBbind kinetic,
BindingDB kinetic) and three candidate models (STELLAR-koff, Ridge on PLIP fingerprints,
custom GNN). But it does not specify what molecular descriptors or representations the ML
model would use as input features.

For a koff prediction model, the choice of representation is critical because koff depends
on the unbinding pathway, not just the bound-state interactions. Specifically:

1. **PLIP interaction fingerprints** (Kokh et al., 2019) capture the bound-state
   protein-ligand interaction pattern. These are informative for koff because interactions
   that must be broken during unbinding directly affect the energy barrier. However, they
   require a docked pose, which means Tier 2 depends on docking quality.

2. **Morgan/ECFP fingerprints** capture 2D molecular topology but miss 3D binding mode
   information that determines unbinding kinetics.

3. **GNN on molecular graphs** (STELLAR-koff approach) can learn unbinding-relevant
   features from data, but the training set size for EGFR-specific kinetics (~300-500
   entries from the kinase subset of KOFFI) may be insufficient.

4. **The proposal mentions mu_EGFR and sigma_EGFR reference anchors** (log10(koff) mean
   = -3.5, std = 1.0) derived from known EGFR drugs. But with only 5-6 EGFR drugs having
   published koff values (gefitinib, erlotinib, lapatinib, afatinib, osimertinib, and
   perhaps neratinib), these statistics are estimated from a vanishingly small sample.
   The confidence interval around mu_EGFR = -3.5 is very wide.

**Suggested fix:** Specify the descriptor strategy explicitly: PLIP fingerprints for
compounds with docked poses, Morgan fingerprints + RDKit descriptors as fallback.
Acknowledge the small EGFR reference sample and use pan-kinase koff statistics as a
secondary anchor.

### W6. The Conformational Selection Narrative, While Rigorous, Contains One Overclaim [Severity: LOW, Addressable: YES]

The draft Discussion text (Section B.5) states: "State-aware candidates optimized for
DFG-out pocket geometry are therefore expected to inherit the favorable kinetic properties
of Type II inhibitors." The word "expected" is slightly too strong. The molecules are
computationally designed; they have not been experimentally characterized. A molecule
optimized for DFG-out pocket shape might fail to bind, bind in an unexpected mode, or
show anomalous kinetics.

The sentence should read "predicted to" or "hypothesized to inherit" rather than "expected
to." This is a minor wording issue but important for scientific honesty -- the project's
non-negotiable Rule 1.

The Type II selectivity claim (Gini 0.64-0.80 vs 0.49-0.52 for Type I) from Zhao et al.
(2017) is cited for kinome-wide selectivity, but Zhao et al. specifically studied
cysteine-targeting covalent inhibitors, not all Type II inhibitors. The Gini coefficient
comparison should cite Uitdehaag et al. (2012) or Davis et al. (2011) for a broader
kinase selectivity analysis, and should note that selectivity depends on the specific
allosteric pocket interactions, not solely on the DFG-out binding mode.

---

## Feasibility Assessment

### Tier 3 (Heuristic): Immediately Feasible

Implementing the state-kinetic lookup table is trivial: ~50 lines of Python, one config
entry, one test file. Could be done in a day. The concern is not feasibility but
redundancy (see W2).

### Tier 2 (ML koff): Feasible with Caveats

Training data assembly from KOFFI + K4DD + PDBbind is feasible. The concern is the
EGFR-specific data scarcity: KOFFI's kinase subset may yield only 300-500 entries, with
perhaps 20-40 EGFR-specific entries. Transfer learning from pan-kinase data is the right
approach, but the expected EGFR-specific accuracy should be characterized honestly. The
STELLAR-koff model (Pearson r = 0.729-0.838) was benchmarked on a pan-target set; its
EGFR-specific performance is unknown.

### Tier 1 (tauRAMD): Feasible but Expensive

150-250 GPU-days is substantial. The proposal's compute estimates (2-7 days wall clock
on Bouchet) assume full access to gpu or gpu_h200 partitions, which may not be
available on demand given shared cluster usage. Running as scavenge_gpu is noted as a
fallback, but scavenge jobs can be preempted, extending actual wall-clock time
significantly.

System preparation for tauRAMD (parameterizing 30 novel ligands in 4 EGFR conformational
states) is non-trivial: GROMACS topology generation, force field assignment (likely
GAFF2 via AmberTools or CGenFF), energy minimization, equilibration. The proposal does
not account for this overhead, which adds 1-2 weeks of effort.

### Component C (SPR/HDX-MS): Feasible but External

The proposal honestly notes this requires either a core facility collaborator or a CRO.
The cost range ($40-100K total) is realistic but substantial for an academic project
without an established wet-lab collaboration. This is correctly prioritized last.

---

## Suggested Modifications

### M1. Coordinate Weight Allocation with cheminfo-P01 [CRITICAL]

Before implementing any weight changes, both proposals should agree on a unified weight
allocation framework. Recommended approach:

1. Implement cheminfo-P01's reference set expansion and multi-metric reform first.
2. Implement biophys-P01's kinetic cascade (all three tiers).
3. Run a joint weight optimization: grid search over the full 5-component weight space
   (constrained to sum to 1.0) maximizing retrospective enrichment (EF@10).
4. Report the optimal weights and sensitivity curves as a publication figure.

This produces data-driven weights that account for the interactions between components,
rather than two independent ad hoc adjustments.

### M2. Eliminate or Redesign Tier 3 [HIGH PRIORITY]

Replace the state-kinetic heuristic with one of:
(a) Neutral fallback (kinetic_score = 0.5 for all molecules when Tier 1 and Tier 2
are unavailable), eliminating the redundancy with state_specificity.
(b) A merged state-kinetic component that replaces both state_specificity and the kinetic
heuristic, preserving the biophysical signal in a single dimension.

### M3. Define Descriptor Strategy for Tier 2 Explicitly

Specify: (a) which molecular representation (PLIP fingerprints with docked poses as
primary, Morgan + RDKit descriptors as fallback), (b) the training/validation split
strategy (scaffold split recommended for kinase data, per Sheridan, 2013), (c) the
expected EGFR-specific performance range with honest error bounds, (d) an applicability
domain assessment for the koff model itself.

### M4. Add an Ablation Study Design

The publication should include an ablation analysis: what happens when you remove the
kinetic component? If removing kinetic scoring barely changes EF@10, the component is
not earning its weight. If EF@10 drops meaningfully, the component is justified. This
is standard for multi-component scoring function papers (e.g., Moriwaki et al., 2018;
Chaput et al., 2016) and directly addresses the "is 10% arbitrary?" reviewer concern.

### M5. Soften the "First Pipeline" Claim

The claim that this would be "the first conformational-state-aware drug design pipeline
with integrated kinetic prediction" should be qualified. KinoML (Volkamer group) and
the HITS Heidelberg tauRAMD workflow already combine conformational information with
kinetic prediction, albeit not in the same pipeline architecture. The novelty is the
integration into a unified scoring function with a multi-tier cascade, not the individual
components.

---

## Alternative Approaches

### A1. Kinetics as a Post-Hoc Filter Rather Than a Scoring Component

Instead of adding kinetics to the scoring function (increasing dimensionality), use the
kinetic cascade as a post-hoc filter: score candidates with the existing 4-component
function, select the top-N, then rank by predicted kinetics. This avoids the weight
allocation problem entirely and is more aligned with how drug discovery actually
works -- kinetics is a late-stage selection criterion, not an early-stage scoring
component.

This approach would still support the conformational selection narrative and SPR
validation, but without modifying the scoring function. It also avoids the Pareto
dimensionality concern (W4).

### A2. Kinetics as a Publication Analysis, Not a Pipeline Feature

A lighter-weight alternative: do NOT modify the scoring function at all. Instead, compute
kinetic predictions (Tier 2 or Tier 3) for all candidates and analyze the correlation
between StateBind scores and predicted kinetics. If state-aware candidates have
significantly better predicted kinetics than static candidates, this supports the
conformational selection narrative without any scoring function modification. Present
kinetics as an independent validation dimension, not a scoring component.

This decouples the narrative contribution (very high value) from the scoring modification
(uncertain value and high technical risk).

### A3. Focus Resources on Tier 1 Validation Before Scoring Integration

Before adding kinetics to the scoring function, validate that tauRAMD works for EGFR
by running it on the 3 known drugs (erlotinib, gefitinib, lapatinib) plus 1-2 known
Type II kinase inhibitors docked into EGFR. If tauRAMD correctly ranks lapatinib >>
gefitinib in residence time (matching the published 430 min vs. <14 min), this validates
the method. If it fails, Tier 1 should not be trusted, and the proposal's compute
investment is wasted. The proposal mentions this as Open Question 5 but does not make
it a prerequisite. It should be.

---

## Impact on Publication Narrative

### Positive Interactions

1. **The conformational selection narrative enhances the enrichment story.** The 10x
   retrospective enrichment is currently a structural observation. Reframing it as
   implicit kinetic optimization adds a mechanistic layer that elevates the narrative
   from "our pipeline finds molecules that look like future drugs" to "our pipeline
   finds molecules that bind with pharmacologically favorable kinetics, as predicted
   by conformational selection theory." This is a significant upgrade for Nature
   Computational Science reviewers who expect mechanistic depth.

2. **The kinetic dimension differentiates from competitors.** Existing state-aware
   tools (e.g., KinFragLib from Volkamer group, DFG-Classifier from Modi/Bhatt) analyze
   conformational states but do not predict kinetic consequences. If kinetic scoring
   works (Tiers 1 or 2), this is a genuine methodological contribution.

### Negative Interactions

1. **Conflict with scoring reform (cheminfo-P01).** As detailed in W3, the two proposals
   modify the same weights independently. If not coordinated, this produces confusion
   about what the "correct" scoring function is.

2. **Adding a 5th component while the existing 4 are questioned weakens credibility.**
   If reviewers already doubt the weight allocation of the 4-component function (which
   they will, given the mean-score gap driven by reference_similarity), adding a 5th
   component with another ad hoc weight invites the criticism: "The authors keep adding
   components to their scoring function without principled weight selection."

3. **The Tier 3 redundancy undermines the intellectual contribution.** If the published
   version uses Tier 3 (heuristic) for most candidates (because tauRAMD is only feasible
   for top-30 and ML koff is uncertain), the kinetic score IS the state label, and
   reviewers will recognize this. The contribution would be perceived as a state-
   specificity bonus disguised as a kinetic score.

### Interaction with cheminfo-P01's Reference Set Expansion

The reference set expansion in cheminfo-P01 changes the reference_similarity landscape
in a way that interacts with the kinetic score. Specifically:

- With 3 references (current): static candidates have high reference_similarity, state-
  aware candidates have low. Adding kinetics helps state-aware candidates.
- With 100-300 references (cheminfo-P01): the reference_similarity gap narrows
  substantially. The marginal benefit of adding a kinetic score to help state-aware
  candidates is therefore SMALLER after reference set expansion.

This means the order of operations matters: if cheminfo-P01 is implemented first,
the kinetic score may contribute less to closing the gap, and a smaller weight may be
appropriate.

---

## References

1. Chaput L, et al. Benchmark of four popular virtual screening programs: construction
   of the active/decoy dataset remains a major determinant of measured performance.
   J Cheminform. 2016;8:56.

2. Walters WP. Virtual chemical libraries. J Med Chem. 2019;62(3):1116-1124.

3. Sheridan RP. Time-split cross-validation as a method for estimating the goodness
   of prospective prediction. J Chem Inf Model. 2013;53(4):783-790.

4. Moriwaki H, et al. Mordred: a molecular descriptor calculation software.
   J Cheminform. 2018;10:4.

5. Uitdehaag JCM, et al. A guide to picking the most selective kinase inhibitor
   tool compounds for pharmacological validation of drug targets. Br J Pharmacol.
   2012;166(3):858-876.

6. Davis MI, et al. Comprehensive analysis of kinase inhibitor selectivity. Nat
   Biotechnol. 2011;29(11):1046-1051.

7. Hert J, et al. Comparison of fingerprint-based methods for virtual screening using
   multiple bioactive reference structures. J Chem Inf Comput Sci. 2004;44(3):1177-1185.

8. Riniker S, Landrum GA. Open-source platform to benchmark fingerprints for
   ligand-based virtual screening. J Cheminform. 2013;5:26.

9. Bender A, et al. Molecular similarity searching using atom environments, information-
   based feature selection, and a naive Bayesian classifier. J Chem Inf Comput Sci.
   2004;44(1):170-178.

10. Tripp A, et al. Genetic algorithms are strong baselines for molecule generation.
    arXiv:2310.09267v2. 2024.

11. Sabando MV, et al. Using molecular embeddings in QSAR modeling: does it make a
    difference? Brief Bioinform. 2024;25(1):bbad365.

12. Kokh DB, et al. Estimation of Drug-Target Residence Times by tau-Random
    Acceleration Molecular Dynamics Simulations. J Chem Theory Comput.
    2018;14(7):3859-3869.

13. Kokh DB, et al. Machine Learning Analysis of tauRAMD Trajectories to Decipher
    Molecular Determinants of Drug-Target Residence Times. Front Mol Biosci.
    2019;6:36.

14. Copeland RA, Pompliano DL, Meek TD. Drug-target residence time and its implications
    for lead optimization. Nat Rev Drug Discov. 2006;5(9):730-739.

15. Holdgate GA, et al. Structure-kinetic relationships that control the residence time
    of drug-target complexes. Curr Opin Struct Biol. 2018;49:51-58.

16. Schuetz DA, et al. Kinetics for Drug Discovery: an industry-driven effort to target
    drug residence time. Drug Discov Today. 2017;22(6):896-911.

17. Wood ER, et al. A unique structure for EGFR bound to GW572016 (lapatinib). Cancer
    Res. 2004;64(18):6652-6659.

18. Praski A, Adamczyk J. Pretrained molecular embeddings for molecular property
    prediction: a comprehensive benchmark. 2025.

19. Zhao Z, et al. Determining cysteines available for covalent inhibition across the
    human kinome. J Med Chem. 2017;60(7):2879-2889.

20. Wood MJ, et al. Mutation in Abl kinase with altered drug-binding kinetics indicates
    a novel mechanism of imatinib resistance. PNAS. 2022;119(3):e2111451118.
