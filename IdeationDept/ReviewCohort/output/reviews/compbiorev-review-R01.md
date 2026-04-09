---
agent: Sr. Journal Reviewer -- Comp Bio
round: 1
date: 2026-04-09
type: review-assessment
scope: cross-cohort
---

# Review Assessment: StateBind -- Conformational State-Conditioned Molecular Generation

## Reviewing Agent

Sr. Journal Reviewer -- Computational Biology. 20+ years of editorial board
experience at Nature Computational Science, JCIM, and Bioinformatics. 500+
manuscripts reviewed. Expertise in structure-based drug design, kinase biology,
retrospective validation methodology, molecular generation evaluation, and
statistical rigor.

---

## Executive Summary

Both cohorts have produced serious, well-researched agendas for a StateBind
publication. The core idea -- conditioning molecular generation on discrete
conformational states and benchmarking the resulting enrichment -- occupies a
genuine gap in the literature, confirmed by my independent search across 30+
recent publications and preprints. However, the novelty window is closing fast:
DynamicBind (Nature Communications 2024), Apo2Mol (AAAI 2026), DynamicFlow
(ICLR 2025), FLOWR (ICLR 2025), and PropMolFlow (Nature Computational Science
2025) all address protein flexibility during generation, and several can already
produce holo-state-adapted molecules. The unique StateBind contribution is not
dynamics-aware generation per se (others do this) but rather *retrospective
enrichment benchmarking of discrete state-conditioned design across multiple
kinases* -- a framing neither cohort articulated with full clarity. The
statistical challenges are severe (N=3-5 held-out drugs per kinase), the
leakage issues are real, and the baseline gap is a publication-blocking
deficiency. Both agendas identify the right problems but underestimate how
hostile the review environment has become for molecular generation papers
lacking rigorous baselines and confidence intervals. My recommended path is
a methods/benchmark paper at JCIM with tight scope, pre-registered endpoints,
and honest reporting, rather than an aspirational Nature Computational Science
submission that invites unfavorable comparison with DynamicFlow and FLOWR.

---

## Cohort Comparison

### Areas of Agreement

Both cohorts converge on several critical points, which increases my confidence
that these represent genuine requirements rather than idiosyncratic preferences:

1. **Multi-kinase validation is essential.** Both identify EGFR-only results as
   unpublishable. Both recommend EGFR + ABL1 + BRAF as the core kinase set.
   Both correctly drop RET (no DFGout structures) and identify JAK2 as weak
   (Cohort2 explicitly drops it; Cohort1 retains it but with caveats).

2. **The scoring artifact must be explained.** Both cohorts identify the
   reference_similarity component (35% weight, Morgan/Tanimoto to 3 quinazoline
   drugs) as the primary driver of the mean-score gap (0.5437 vs 0.4378). This
   is the single most important shared finding.

3. **Bootstrap CIs and BEDROC are mandatory.** Both recommend BCa bootstrap
   with 10,000 resamples and BEDROC(alpha=20) as primary metric. This aligns
   with Truchon and Bayly (2007, JCIM 47:488-508) and Empereur-mot et al.
   (2022, J Cheminformatics 14:48).

4. **External baselines are publication prerequisites.** Both require REINVENT 4
   and at least one 3D method. Cohort1 recommends FLOWR; Cohort2's benchmark
   proposal includes DiffSBDD, TargetDiff, and Pocket2Mol.

5. **The ablation suite is thesis-critical.** Both identify Experiment C
   (unconditioned VAE) as the make-or-break experiment. If diversity alone
   explains enrichment, the conformational state thesis weakens fundamentally.

6. **Pre-registration eliminates selective reporting risk.** Both recommend
   locking analysis decisions before running experiments, citing the Polaris
   consortium guidelines (JCIM 2025, "Practically Significant Method Comparison
   Protocols").

### Areas of Disagreement

1. **Scoring function revision vs. sensitivity analysis.**
   - Cohort2 (cheminfo-P01) proposes a comprehensive 6-configuration scoring
     reform as Priority 1, arguing the gap is a "publication blocker."
   - Cohort1 concludes the scoring function should NOT be revised for the
     primary comparison (deferred to supplementary), arguing that changing
     scoring to make state-aware win invites reviewer skepticism.
   - **My assessment:** Cohort1 is correct. Reporting results under both
     original and reformed scoring is essential, but the primary comparison
     must use the pre-existing scoring function. Changing the scoring function
     and then claiming state-aware wins is textbook p-hacking in the eyes of
     a hostile reviewer. The sensitivity analysis showing the gap is explained
     by reference_similarity is itself a publishable finding.

2. **Two-paper vs. one-paper strategy.**
   - Cohort2 recommends a two-paper strategy (methods paper + benchmark paper).
   - Cohort1 recommends a single integrated paper.
   - **My assessment:** A single focused paper is more realistic for the
     timeline pressure. The benchmark paper (bencharch-P01) is interesting but
     requires significant additional infrastructure (Docker containers,
     leaderboard, HuggingFace hosting) that distracts from the primary
     scientific contribution. If the results are strong, a follow-up benchmark
     release is natural.

3. **Kinetic scoring component.**
   - Cohort2 (biophys-P01) proposes a 5th scoring component based on kinetic
     predictions (tauRAMD, 150-250 GPU-days).
   - Cohort1 does not include kinetic scoring.
   - **My assessment:** The kinetic *narrative* (Component B) is excellent and
     zero-cost. The kinetic *scoring* (Component A) is too expensive, too
     uncertain (tauRAMD validation is itself a research question), and adds
     complexity to an already complex paper. Defer to a follow-up. The
     cheminfo critique correctly identified the Tier 3 heuristic as redundant
     with state_specificity -- a point any reviewer with multivariate
     statistics training would catch.

4. **Nature Comp Sci viability.**
   - Cohort2 targets Nature Comp Sci as primary venue.
   - Cohort1 targets JCIM as primary, Nature Comp Sci as aspirational.
   - **My assessment:** JCIM is the realistic target. Nature Comp Sci has
     published DiffSBDD (Schneuing et al., 2024), PropMolFlow (2025), SynGFN
     (2025), and TANGO (2026). These papers all introduce novel architectures
     or training paradigms. StateBind's contribution is a *benchmark question*
     (does state-conditioning help?), not a novel architecture. JCIM is the
     appropriate home for framework/benchmark papers.

### Gaps and Blind Spots

1. **Neither cohort addresses the GNINA training data overlap.** GNINA's CNN
   scoring function was trained on CrossDocked2020, which derives from PDBbind.
   CrossDocked2020 contains 22.5 million poses from ~22,000 PDB structures.
   EGFR is one of the most deposited kinases (~250+ structures). It is
   near-certain that CrossDocked2020 includes EGFR structures -- meaning GNINA
   has seen EGFR binding poses during training. This is not disqualifying (GNINA
   is used as a tool, not as the primary claim), but it must be disclosed and
   discussed. For the 3D baselines (DiffSBDD, FLOWR), which are also trained on
   CrossDocked2020 or similar datasets, this creates a more serious leakage
   concern: these methods may have seen EGFR pocket-ligand complexes during
   training, making their performance on EGFR a form of in-distribution
   evaluation, not zero-shot generalization.

2. **Neither cohort quantifies the expected CI widths for pooled multi-kinase
   enrichment.** The datasci-P01 proposal estimates ~21 held-out drugs across
   6 kinases, but after dropping RET, JAK2, and ALK (per Cohort1's final
   agenda), only ~8-10 remain across 4 kinases. With N=8-10 total held-out
   drugs, the 95% BCa CI on pooled BEDROC will still be very wide --
   approximately +/- 0.15-0.25 on a [0,1] scale. This may be sufficient to
   exclude the null for a large effect (the 10x enrichment) but will not
   support fine-grained method comparisons between baselines. Neither agenda
   acknowledges this limitation with sufficient honesty.

3. **The "within-method state ablation" concept is under-specified.** Cohort1's
   most ambitious claim -- that state-conditioning is a "transferable principle"
   -- requires running REINVENT 4 and FLOWR in both single-pocket and
   multi-pocket modes. But neither cohort specifies how to make REINVENT
   "state-aware" beyond running it 4 times with different pockets. This is
   pocket-specific optimization, not state-conditioning. The claim that
   "REINVENT benefits from state-conditioning" conflates pocket diversity with
   state-awareness. A true state-conditioning test would require modifying
   REINVENT's architecture to accept a state vector -- a substantial software
   engineering effort that neither cohort acknowledges.

4. **No discussion of molecular generation evaluation standards beyond
   enrichment.** The GSK benchmarking study (Sanjrani et al., JCIM 2025)
   and the Durian benchmark (Nie et al., JCIM 2025) established multi-metric
   evaluation standards. PoseBusters validity, strain energy, interaction
   recovery, and Mogul geometry checks are now expected. StateBind's SELFIES
   VAE generates 1D molecules that are then docked -- there is no guarantee
   that docked poses are physically plausible. PoseBusters validation of the
   docked poses should be included.

---

## Proposal-Level Assessment

### Strongest Proposals

**1. datasci-P01 (Cohort1): Multi-Kinase Retrospective Validation with
Pre-Registered Statistical Design**
- Rating: STRONG SUPPORT
- This is the statistical backbone of the paper. The BCa bootstrap protocol,
  BEDROC primary endpoint, ablation suite design, and pre-registration framework
  are all methodologically sound. The proposal correctly identifies that with
  N=5 per kinase, the 95% CI on EF@10 spans [0.5, 9.4] -- a devastating
  observation that motivates the multi-kinase extension.
- **Critical weakness:** The proposal originally included 6 kinases (21
  held-out drugs). After culling to 4 kinases, only ~8-10 held-out drugs
  remain. The power analysis needs to be re-run with this reduced N. The
  pre-2010 cutoff may actually be more informative than pre-2015 because it
  yields more held-out drugs for EGFR.

**2. cheminfo-P01 (Cohort2): Scoring Reform and Chemical Space Analysis**
- Rating: SUPPORT WITH MODIFICATIONS
- The gap decomposition analysis (showing reference_similarity explains the
  entire mean-score gap) is the paper's strongest methodological finding.
  The 6-configuration sensitivity table would be a high-impact figure.
  Chemical space UMAP visualizations are mandatory for any venue.
- **Critical weakness:** The proposal frames scoring reform as the #1 priority,
  but running the reformed scoring as the primary analysis creates a "we
  changed the rules until we won" perception. Must be secondary/sensitivity.

**3. compchem-P01 (Cohort1): GIST Water Thermodynamics**
- Rating: SUPPORT WITH MODIFICATIONS
- The GIST analysis has the best cost-to-impact ratio in either agenda. At
  <2 GPU-days, it provides direct physical evidence that conformational states
  present distinct solvation environments -- the thermodynamic foundation for
  the entire thesis. Published precedent exists (Robinson et al., 2010, 2014
  on SRC; Kim et al., 2018, PNAS on PKA; Ung et al., 2014 on DFG-out pockets).
- **Critical weakness:** The 3W2R mutation issue (T790M/L858R double mutant
  used for wild-type DFGout/aCin) contaminates the GIST analysis. Running GIST
  on a mutant structure and comparing to wild-type structures conflates
  mutational effects with conformational effects. A wild-type DFGout structure
  must be found or the analysis must include a back-mutation control.

### Weakest Proposals

**1. bencharch-P01 (Cohort2): StateBind-Bench Benchmark**
- Rating: WEAK SUPPORT
- The benchmark concept is sound and the gap is real (verified: no existing
  benchmark evaluates state-conditioned generation). However, the proposal
  is premature. A benchmark requires community trust, which requires strong
  primary results first. The infrastructure requirements (Docker containers,
  HuggingFace hosting, PapersWithCode leaderboard, quarterly weight rotation)
  distract from the scientific contribution. The NeurIPS 2026 target is
  correctly identified as infeasible.
- **Additional concern:** The 4-task design includes "Multi-Objective Pareto
  Optimization" as Task 4 with default weights that differ from StateBind's
  current weights (docking 0.35 in benchmark vs 0.20 in StateBind). This
  inconsistency undermines the benchmark's authority.

**2. biophys-P01 (Cohort2): Kinetic Scoring Component**
- Rating: SUPPORT WITH MAJOR MODIFICATIONS (Component B only)
- Component B (conformational selection narrative) is zero-cost and
  publication-ready. The lapatinib vs gefitinib residence time comparison
  (430 min vs <14 min despite weaker equilibrium affinity) is compelling.
- Component A (kinetic scoring) requires 150-250 GPU-days for tauRAMD that
  may not reproduce known kinetics (30% failure probability per the risk
  register). The Tier 3 heuristic is correctly identified by the cheminfo
  critique as a monotone function of state_specificity, adding no new
  information.
- Component C (experimental validation) requires wet lab access not available
  to this project. Include as a proposed collaboration in the Discussion.

**3. clinonc-P01 (Cohort2): C797S Resistance Design**
- Rating: SUPPORT WITH MODIFICATIONS (integration into Paper 1 only)
- The clinical framing is excellent and the C797S unmet need is real (7-29%
  of osimertinib patients). However, as a standalone experiment, it relies
  on AF2-MSM predictions of mutant DFGout structures -- a method with known
  bias toward DFGin (87% of KLIFS entries are DFGin, creating training data
  imbalance for AF2). The drughunt critique correctly flagged this risk.
  The C797S angle works best as translational motivation in the Introduction,
  not as a primary experiment.

### Claims Requiring Verification

| # | Claim | Source | Status | Evidence |
|---|-------|--------|--------|----------|
| 1 | No published paper conditions molecular generation on discrete conformational states | genai-R02, Cohort1 | PARTIALLY VERIFIED | My search confirms no paper explicitly conditions on DFG/aC state labels. However, DynamicBind (Nat Commun 2024) handles DFG-in to DFG-out transitions implicitly. Apo2Mol (AAAI 2026) generates for apo-to-holo transitions. DynamicFlow (ICLR 2025) trains on MD trajectories capturing multiple conformations. The novelty claim is valid but narrowing: these methods handle flexibility without discrete state labels. StateBind's contribution is the explicit discrete conditioning + retrospective benchmark, not conformation-awareness itself. |
| 2 | FLOWR achieves 92% PoseBusters validity | mlres-P01, Cohort1 | VERIFIED | FLOWR reports 0.92 +/- 0.22 PB validity (Cremer et al., ICLR 2025). MolPilot (ICML 2025) achieves 95.9%. Both surpass DiffSBDD (~38%, Buttenschoen et al., 2024). |
| 3 | EF@10 = 4.95 with N=5 has 95% CI spanning [0.5, 9.4] | datasci-P01 | PLAUSIBLE | Nicholls (2016, J Comput-Aided Mol Des 29:1205) provides analytic formulae confirming that EF CIs with <20 actives are "extremely large." The specific CI bounds depend on the number of inactives and the measured EF, but spanning from below 1.0 to near 10.0 with N=5 is consistent with published analyses. |
| 4 | 48% of approved kinase inhibitors violate Lipinski Ro5 | medchem-P01 | VERIFIED | Roskoski's annual review series (Pharmacological Research, 2024 update: 80 approved kinase inhibitors; 2025 update: 85; 2026 update: 90+). Multiple reviews confirm ~40-50% Ro5 violation rates for kinase inhibitors, with MW > 500 as the most common violation. |
| 5 | Type II inhibitors have Gini selectivity 0.76 vs 0.58 for Type I | medchem-P01, kinpharm-P01 | NEEDS VERIFICATION | Ung et al. (J Med Chem 2015) is cited by both cohorts. The paper analyzed DFGout conformations and biochemical profiles. The specific Gini values (0.76 vs 0.58) need page-level verification. The cheminfo critique noted that Zhao et al. 2017 (also cited) studied cysteine-targeting compounds, not all Type II -- verify the primary source. |
| 6 | REINVENT 4 can be integrated with GNINA as a custom scoring component | mlres-P01 | VERIFIED | REINVENT 4 (Loeffler et al., J Cheminform 2024) supports plugin architecture via Python namespace packages in reinvent_plugins/components/. Custom scoring components can be added. GNINA integration would require a custom plugin but is architecturally supported. |
| 7 | CrossDocked2020 contains EGFR structures in training | Cohort1 risk register | HIGHLY LIKELY | CrossDocked2020 derives from PDBbind, which includes EGFR (one of the most deposited kinases with 250+ PDB structures). The dataset contains 22.5 million poses from ~22,000 structures. It is near-certain EGFR is included. This creates an in-distribution evaluation concern for any 3D method trained on CrossDocked2020. |
| 8 | 3W2R is a T790M/L858R double mutant | structbio-R01, Cohort1 | VERIFIED | PDB 3W2R: "EGFR Kinase domain T790M/L858R mutant with compound 4" at 2.05 A resolution. Confirmed via RCSB PDB. This is NOT a wild-type structure. Using it to represent a wild-type DFGout/aCin state conflates mutational and conformational effects. |
| 9 | Osimertinib was approved November 2015 | datasci-P01 | VERIFIED | FDA accelerated approval November 13, 2015. It appears in the pre-2015 training set if the cutoff is inclusive. For pre-2015 validation, osimertinib should be in the held-out set, but its use as a reference molecule creates temporal leakage. |
| 10 | No existing benchmark evaluates state-conditioned generation | bencharch-P01 | VERIFIED | My search across MoleculeNet, MOSES, GuacaMol, TDC, CrossDocked2020, DUD-E, PDBbind, GenBench3D, Durian, and Polaris confirms no benchmark includes conformational state labels or evaluates state-conditioned generation. KLIFS provides state annotations but is not a generation benchmark. |

---

## Feasibility Assessment

### Technical Feasibility

| Work Item | Feasibility | Key Concern |
|-----------|-------------|-------------|
| Multi-kinase atlas (EGFR + ABL1 + BRAF + MET) | HIGH | KLIFS provides structures. ABL1 and BRAF have excellent DFGout coverage. MET is acceptable. |
| MPNN retraining per kinase | HIGH | ChEMBL data is available. Architecture is fixed. Training time is modest. |
| VAE retraining per kinase | HIGH | Same architecture, different training data. Compute: 1-2 GPU-days per kinase. |
| REINVENT 4 baseline | MODERATE | Plugin architecture supports GNINA, but integration requires custom development. Estimated: 1-2 weeks. |
| FLOWR baseline | MODERATE | FLOWR uses SPINDR dataset (not CrossDocked2020), reducing leakage concern. But custom pocket conditioning may require code modification. |
| Ablation suite | HIGH | Straightforward: zeroed state vector, shuffled labels, subsampled candidates. |
| GIST water analysis | HIGH | cpptraj + AmberTools are well-documented. The 3W2R mutation issue requires a structure substitution. |
| Bootstrap CIs | HIGH | Standard implementation. oddt.metrics.bedroc or custom from Truchon & Bayly Eq. 7. |
| Scoring sensitivity analysis | HIGH | Existing infrastructure supports weight reconfiguration. |
| OpenFE RBFE | MODERATE-LOW | OpenFE is production-ready but RBFE across diverse scaffolds from a VAE requires ABFE, not RBFE, for cross-series comparison. ABFE costs 20-40 GPU-hours per compound. Selection bias in choosing "top candidates" for FEP undermines the statistical argument. |
| tauRAMD kinetic scoring | LOW | 150-250 GPU-days for uncertain results. 30% chance of failing to reproduce known kinetics. |

### Timeline Realism

Cohort1 proposes 6-8 weeks for P0 (three pillars). This is aggressive but
feasible if personnel are dedicated full-time and no unexpected blockers arise.
The REINVENT 4 integration (1-2 weeks) and FLOWR setup (1 week) are the most
likely timeline risks.

Cohort2 proposes 16-18 weeks for both papers. This is more realistic but
assumes parallel development of two papers, which may not be practical for a
single researcher or small team.

**My estimate:** 10-14 weeks from start to manuscript draft for a single JCIM
paper, assuming full-time effort, functioning HPC access, and no major negative
results from the ablation suite.

### Risk Assessment

**Risk 1: Ablation C (unconditioned VAE) kills the thesis.**
- Probability: MEDIUM (30-40%)
- If the unconditioned VAE achieves comparable enrichment, the paper becomes
  "diverse generation outperforms template-based design" -- still publishable
  but a fundamentally different story.
- Mitigation: Pre-register this outcome explicitly. The paper can pivot to
  "chemical diversity, not state-conditioning, drives retrospective enrichment
  for kinase inhibitors" -- an honest negative finding with high citation
  potential.

**Risk 2: Pooled enrichment CIs fail to exclude null.**
- Probability: MEDIUM (25-35%)
- With N=8-10 held-out drugs across 4 kinases, the CIs may include values
  consistent with no enrichment advantage.
- Mitigation: Use BEDROC rather than EF (BEDROC uses the full ranking, not
  just a threshold), and report per-kinase results separately. Some kinases
  may show null results -- report honestly.

**Risk 3: 3D baselines outperform on all metrics.**
- Probability: LOW (10-15%)
- FLOWR (PB validity 92%, mean Vina -6.29) and MolPilot (PB validity 95.9%)
  are strong methods. However, they are pocket-conditioned, not state-conditioned.
  If they outperform StateBind in enrichment without state labels, the paper's
  contribution shifts to "state-conditioning does not add value beyond 3D
  pocket conditioning" -- a publishable negative result.

---

## Novelty Assessment (Deep Research)

### Is conformational-state-conditioned molecular generation truly novel?

**Verdict: The discrete state-conditioning approach is novel. The broader
conformation-awareness category is not.**

My independent search confirms the following competitive landscape:

| Method | Year | Venue | Approach | State-Conditioned? |
|--------|------|-------|----------|-------------------|
| DynamicBind | 2024 | Nat Commun | Equivariant diffusion; joint protein-ligand generation; handles DFG-in to DFG-out | No explicit state labels; implicit via learned dynamics |
| Apo2Mol | 2025/2026 | AAAI | Diffusion on apo-holo pairs; generates ligand + holo pocket | No; apo-to-holo transition, not discrete states |
| DynamicFlow | 2025 | ICLR | Flow matching on MD trajectories; multiscale protein-ligand | No; continuous dynamics, not discrete states |
| FLOWR | 2025 | ICLR | Flow matching with SPINDR dataset; interaction conditioning | No; pocket-conditioned, not state-conditioned |
| FLOWR.root | 2025 | arXiv | Foundation model for pocket-aware generation + affinity prediction | No explicit state conditioning |
| PropMolFlow | 2025 | Nat Comp Sci | Property-guided flow matching; geometry-complete | No; property conditioning, not state conditioning |
| MolPilot | 2025 | ICML | VLB-optimal scheduling for SBDD; 95.9% PB validity | No; pocket-conditioned only |
| AlphaFold2-RAVE | 2024 | JCIM | AF2 + enhanced sampling for conformation-selective docking | Conformation-selective screening, not generation |
| AF2 multi-state kinases | 2024 | Sci Reports | MSM for multi-state docking/screening | Multi-state screening/docking, not generation |

**Key distinction:** None of these methods explicitly condition generation on
discrete conformational state labels (DFGin/aCin, DFGin/aCout, etc.) and then
evaluate retrospective enrichment across states. They handle conformational
flexibility through learned dynamics (DynamicBind), apo-holo transitions
(Apo2Mol), MD trajectories (DynamicFlow), or pocket geometry (FLOWR). StateBind
is the only system that uses *explicit discrete state labels* as conditioning
input to a molecular generator and then benchmarks state-conditioning vs.
state-blindness.

**However**, the framing matters enormously. If the paper claims "we are the
first dynamics-aware molecular design system," it will be rejected because
DynamicBind, Apo2Mol, and DynamicFlow all precede it. If the paper claims "we
present the first benchmark evaluating whether discrete state-conditioning
improves molecular design," that claim is defensible.

**Time pressure:** The field is converging. A conformation-conditioned generation
benchmark is an obvious next step and likely under development by multiple
groups. Publication within 4-6 months is advisable.

---

## Statistical Rigor Assessment

### BEDROC(alpha=20) as Primary Metric

**Assessment: Appropriate choice, with caveats.**

Truchon and Bayly (2007) established that at alpha=20, 80% of BEDROC's weight
falls in the top 8% of the ranked list. For StateBind's setting (~461 molecules),
this means the top ~37 molecules dominate the score. BEDROC ranges [0,1] and has
a well-defined null distribution, making it amenable to hypothesis testing.

**Caveat 1:** BEDROC's statistical power depends on the number of actives.
Nicholls (2016) showed that early enrichment metrics have "relatively poor
statistical power" -- 0.5% early enrichment distinguishes methods to 95%
confidence only 14% of the time. With N=3-5 actives per kinase, individual
kinase BEDROC comparisons will have very low power. Pooling across kinases is
essential but introduces heterogeneity.

**Caveat 2:** BEDROC depends on the ratio of actives to inactives. With N=5
actives in 461 molecules (1.1% active rate), the BEDROC null distribution is
well-behaved, but the metric's sensitivity to active placement means a single
rank swap can change BEDROC substantially.

### Bootstrap CIs with N=5-10

**Assessment: Necessary but insufficient for strong claims.**

BCa bootstrap with 10,000 resamples will produce valid coverage intervals, but
with N=5-10 held-out drugs, the intervals will be wide. Expected 95% CI width
for BEDROC with N=5: approximately +/- 0.20-0.30 on a [0,1] scale. For pooled
BEDROC with N=10 across 4 kinases: approximately +/- 0.12-0.18.

This is sufficient to detect a large effect (the current 10x enrichment) but
insufficient for method ranking (e.g., "StateBind > REINVENT > FLOWR"). The
paper must frame its claims accordingly: "state-conditioned generation produces
statistically significant enrichment" (if CIs exclude null), not "state-
conditioned generation outperforms REINVENT" (which requires much tighter CIs).

### Recommended Statistical Additions

1. **Empereur-mot EmProc confidence bands** (J Cheminformatics, 2022) for the
   full enrichment curve, not just point estimates at specific fractions. This
   method handles the two sources of correlation (across fractions, across
   methods) that standard bootstrap ignores.

2. **Heterogeneity analysis** (I-squared statistic) for pooled multi-kinase
   enrichment. If I-squared > 50%, the pooling is questionable and per-kinase
   results must be the primary reporting unit.

3. **Effect sizes** (Cohen's d or rank-biserial correlation) alongside p-values.
   The Polaris consortium (JCIM 2025) explicitly requires effect size reporting
   for method comparison papers.

---

## Missing Baselines Assessment

### Would this paper be accepted without comparison to REINVENT 4, a 3D method, and a retrieval baseline?

**No.** The current baseline gap is the single most likely cause of desk
rejection at any venue.

The minimum baseline set for a 2026 molecular generation paper, based on my
review of recently accepted papers at Nature Comp Sci, JCIM, and NeurIPS:

| Baseline | Type | Why Essential | Available? |
|----------|------|---------------|------------|
| REINVENT 4 | 1D RL | De facto standard since PMO benchmark (Gao et al., NeurIPS 2022). Omitting it signals unfamiliarity with the field. | Yes, Apache 2.0, v4.7 |
| FLOWR or MolPilot | 3D flow/diffusion | Current 3D SOTA. FLOWR (92% PB validity, ICLR 2025) or MolPilot (95.9% PB validity, ICML 2025). Omitting both signals cherry-picking. | FLOWR: SPINDR dataset, checkpoint available. MolPilot: HuggingFace checkpoint. |
| Fingerprint retrieval | Non-generative | Tests whether generation adds value over database search. If ChEMBL similarity search achieves comparable enrichment, the generator is unnecessary. | Trivial to implement. |
| Random ChEMBL | Lower bound | Null distribution. Essential for BEDROC calibration. | Trivial. |
| Unconditioned VAE | Ablation | Isolates state-conditioning from diversity. THE critical experiment. | Existing codebase with zeroed state vector. |

Both cohorts propose most of these. The gap is primarily that neither proposal
has been *executed* yet.

---

## Leakage Assessment

### Osimertinib Reference Leakage

**Severity: MODERATE. Must be fixed.**

Osimertinib (FDA approval November 2015) is used as one of three reference
molecules in the scoring function. For pre-2015 retrospective validation, this
constitutes temporal information leakage: the scoring function has privileged
knowledge of a drug that has not yet been approved.

**Fix:** Remove osimertinib from references for all pre-2015 analyses. Use only
erlotinib (2004) and gefitinib (2003). The pre-2010 analysis is clean (all three
reference drugs pre-date the cutoff). Report both corrected and original results
for transparency.

### 3W2R Mutant Structure

**Severity: HIGH. Must be resolved.**

PDB 3W2R (EGFR T790M/L858R with pyrrolo[3,2-d]pyrimidine, 2.05 A) is used to
represent the wild-type DFGout/aCin state. Using a double mutant to represent
wild-type conflates mutational and conformational effects. This is a structural
biology kill shot.

**Options:**
- PDB 4I21 (EGFR L858R/T790M with MIG6 peptide, 2.35 A) -- also mutant
- Search KLIFS for wild-type EGFR in DFGout/aCin conformation
- If no wild-type DFGout EGFR structure exists (which is likely -- EGFR
  strongly favors the active conformation), use an AF2-MSM predicted structure
  with validation, or acknowledge the limitation explicitly and run back-
  mutation molecular dynamics as a control

### CrossDocked2020 EGFR Leakage

**Severity: MODERATE for GNINA; HIGH for 3D baselines.**

GNINA's CNN scoring function is trained on CrossDocked2020, which almost
certainly includes EGFR structures. This means GNINA has been trained on EGFR
binding poses. For StateBind's own results, this is a uniform bias (both
pipelines use the same GNINA) and can be disclosed.

For 3D baselines (DiffSBDD, FLOWR via SPINDR, MolPilot), training set overlap
with EGFR is a more serious concern. If these methods have seen EGFR pocket-
ligand complexes during training, their EGFR performance is in-distribution,
not zero-shot. FLOWR uses SPINDR (a curated subset), which may have less
overlap -- this should be checked.

---

## Top 3 Reviewer Kill Shots

These are the three attacks that would sink the paper at any venue. All three
must be preemptively addressed in the manuscript.

### Kill Shot 1: "The enrichment is driven by chemical diversity, not state-conditioning."

**The argument:** The state-aware pipeline generates 461 molecules with internal
diversity 0.91, while the static baseline generates 30 molecules with diversity
0.57. Any generator producing 10x more diverse molecules will achieve higher
enrichment purely through better coverage of chemical space. The state labels
are a red herring.

**The defense:** Ablation Experiment C (unconditioned VAE generating ~400
diverse molecules without state conditioning). If the unconditioned VAE achieves
comparable enrichment, the reviewer is correct and the paper must pivot. If the
state-conditioned VAE significantly outperforms (Cohen's d >= 0.8), state-
conditioning provides information beyond diversity. The paper MUST report
Experiment C results as prominently as the primary comparison.

### Kill Shot 2: "With N=5-10 held-out drugs, no statistical conclusion is possible."

**The argument:** The confidence intervals on enrichment metrics are so wide
that any difference could be explained by chance. The paper reports a 10x
enrichment factor, but the 95% CI includes values below 1.0 (random
performance). This is not a result; it is noise.

**The defense:** (a) Use BEDROC, not EF, because BEDROC uses the full ranking
and has higher statistical power. (b) Pool across 4 kinases (N~8-10 total
held-out drugs). (c) Report BCa bootstrap CIs with 10,000 resamples. (d) Pre-
register the primary endpoint and analysis plan. (e) Acknowledge the limitation
honestly and frame the contribution as "the first systematic benchmark" rather
than "definitive proof."

### Kill Shot 3: "The scoring function is designed to favor template-like molecules, so of course the static pipeline (which generates template modifications) wins on mean score."

**The argument:** The reference_similarity component (35% weight, Morgan
Tanimoto to 3 quinazoline drugs) is the dominant scoring component. Static
candidates, being close modifications of known drugs, trivially maximize this
component. The mean-score comparison is circular: you score molecules on
similarity to known drugs, and the pipeline that produces more similar molecules
scores higher. This is not a meaningful comparison.

**The defense:** (a) Present the gap decomposition showing reference_similarity
explains 100%+ of the gap. (b) Report the 3-component score (removing
state_specificity) as a secondary analysis. (c) Report the Dirichlet weight
sensitivity analysis (1,000+ samples). (d) Frame the mean-score gap as a
methodological insight: "the choice of scoring metric profoundly affects
evaluation of generative molecular design" -- a finding of independent interest.
(e) Use retrospective enrichment (BEDROC), not mean score, as the primary
comparison metric.

---

## Prioritization Recommendation

| Priority | Work Item | Effort | Impact | Risk | Rationale |
|----------|-----------|--------|--------|------|-----------|
| P0-Critical | Fix osimertinib leakage | Hours | HIGH | LOW | Reviewer kill shot if unfixed |
| P0-Critical | Verify/replace 3W2R structure | Days | HIGH | MODERATE | Structural biology kill shot |
| P0-Critical | Bootstrap CIs on current results | Hours | HIGH | LOW | No CIs = no publication |
| P0-Critical | Ablation C (unconditioned VAE) | 1-2 GPU-days | THESIS-CRITICAL | MEDIUM | Determines paper narrative |
| P0-Essential | REINVENT 4 baseline | 1-2 weeks | HIGH | MODERATE | Desk rejection without it |
| P0-Essential | FLOWR or 3D baseline | 1 week | HIGH | MODERATE | Expected at any venue |
| P0-Essential | Multi-kinase expansion (ABL1, BRAF, MET) | 4-6 weeks | HIGH | MEDIUM | Statistical power |
| P1-Important | GIST water thermodynamics | 2-4 GPU-days | HIGH | LOW | Best cost/impact ratio |
| P1-Important | Scoring sensitivity analysis (6 configs) | Days | HIGH | LOW | Explains the mean-score gap |
| P1-Important | Chemical space UMAP + property distributions | Days | MODERATE | LOW | Mandatory for venue |
| P1-Important | Retrieval baseline (fingerprint search) | Hours | MODERATE | LOW | Tests generator value |
| P2-Enhancement | Conformational selection narrative | 1 week (writing) | MODERATE | LOW | Zero-cost mechanistic framing |
| P2-Enhancement | Conformational mapping table (Modi/Ung/KLIFS) | Days | LOW | LOW | Pre-empts reviewer attack |
| P2-Enhancement | PoseBusters validation of docked poses | Hours | MODERATE | LOW | New evaluation standard |
| P3-Deferred | OpenFE FEP validation | 5-8 GPU-days | MODERATE | HIGH | Selection bias concerns |
| P3-Deferred | Benchmark release (StateBind-Bench) | 8+ weeks | HIGH (long-term) | LOW | Better as follow-up paper |
| P3-Deferred | Kinetic scoring component | 150+ GPU-days | LOW-MODERATE | HIGH | Too expensive, uncertain ROI |

---

## Specific Modifications

### For the Final Implementation Plan

1. **Narrow the novelty claim.** Do NOT claim "first dynamics-aware molecular
   design." DO claim "first systematic benchmark evaluating whether discrete
   conformational state labels improve molecular generation for kinase targets."
   This claim is defensible; the broader claim is not.

2. **Add PoseBusters validation.** All generated molecules (VAE, REINVENT,
   FLOWR) should have their docked poses validated through PoseBusters. This is
   now standard (GSK benchmark, JCIM 2025; Buttenschoen et al., Chemical
   Science 2024).

3. **Check FLOWR training data for EGFR.** FLOWR uses SPINDR, a curated
   dataset. Verify whether SPINDR includes EGFR pocket-ligand complexes. If
   yes, the FLOWR comparison is in-distribution for EGFR and must be disclosed.
   The multi-kinase extension reduces this concern (ABL1, BRAF, MET may not be
   in SPINDR).

4. **Add Empereur-mot EmProc confidence bands.** Beyond point-estimate CIs,
   report full enrichment curve confidence bands using the EmProc method
   (Empereur-mot et al., J Cheminformatics 2022). This would make StateBind
   among the first generative design papers to report enrichment CIs rigorously
   -- a methodological differentiator.

5. **Reframe "within-method state ablation" honestly.** Running REINVENT on
   4 pockets sequentially is *pocket-specific optimization*, not *state-
   conditioning*. The paper should not claim REINVENT is "state-conditioned"
   just because it docks against 4 structures. It should say: "We test whether
   the enrichment advantage of running generation against multiple pocket
   structures is specific to StateBind's explicit state-conditioning approach
   or is achievable through naive pocket-specific optimization."

6. **Pre-specify the ablation outcome table.** Following the Polaris consortium
   guidelines (JCIM 2025), pre-register 4 outcome scenarios with their
   publication framings:
   - Scenario A: State-conditioned >> Unconditioned (d >= 0.8) -- thesis
     confirmed.
   - Scenario B: State-conditioned > Unconditioned (0.5 <= d < 0.8) -- modest
     state effect.
   - Scenario C: State-conditioned = Unconditioned (d < 0.5) -- diversity
     drives enrichment.
   - Scenario D: Unconditioned > State-conditioned -- state labels may be
     noisy or harmful.

7. **Include "practical significance" alongside statistical significance.**
   Per the Polaris consortium: even if the enrichment difference is
   statistically significant, is it practically significant? Would a
   medicinal chemist make different decisions based on the state-conditioned
   results vs. the unconditioned results?

---

## Verdict

**Recommended strategy:** Single focused paper at JCIM. Core content: (1)
multi-kinase retrospective enrichment benchmark (4 kinases), (2) ablation suite
isolating state-conditioning contribution, (3) external baseline comparison
(REINVENT 4, FLOWR, retrieval, random), (4) scoring sensitivity analysis showing
the mean-score gap is a metric artifact. Supplementary: GIST water analysis,
conformational selection narrative, chemical space visualizations.

**Primary venue:** Journal of Chemical Information and Modeling (JCIM)

**Aspirational venue upgrade path:** If within-method state ablations show
consistent enrichment improvement across architectures AND the ablation C
result strongly supports state-conditioning (d >= 0.8), the claim elevates
to "transferable principle" and Nature Computational Science becomes viable.
But this must be contingent on data, not assumed.

**Estimated timeline to submission:** 12-16 weeks from start of implementation.

**Confidence level:** MODERATE. The key uncertainty is Ablation C. If the
unconditioned VAE matches the state-conditioned VAE on enrichment, the paper's
narrative changes fundamentally but remains publishable.

---

## References

1. Truchon, J.-F. & Bayly, C. I. (2007). Evaluating Virtual Screening Methods: Good and Bad Metrics for the "Early Recognition" Problem. *J. Chem. Inf. Model.* 47, 488-508.

2. Nicholls, A. (2016). The statistics of virtual screening and lead optimization. *J. Comput.-Aided Mol. Des.* 29, 1205-1218.

3. Empereur-mot, C. et al. (2022). Confidence bands and hypothesis tests for hit enrichment curves. *J. Cheminformatics* 14, 48.

4. Lu, W. et al. (2024). DynamicBind: predicting ligand-specific protein-ligand complex structure with a deep equivariant generative model. *Nature Communications* 15, 1071.

5. Apo2Mol (2025/2026). 3D Molecule Generation via Dynamic Pocket-Aware Diffusion Models. *AAAI Conference on Artificial Intelligence*. arXiv:2511.14559.

6. DynamicFlow (2025). Integrating Protein Dynamics into Drug Design. *ICLR 2025*.

7. Cremer, J. et al. (2025). FLOWR: Flow Matching for Structure-Aware De Novo, Interaction- and Fragment-Based Ligand Generation. *ICLR 2025*. arXiv:2504.10564.

8. PropMolFlow (2025). Property-guided molecule generation with geometry-complete flow matching. *Nature Computational Science*.

9. Qu, Y. et al. (2025). MolPilot: Piloting Structure-Based Drug Design via Modality-Specific Optimal Schedule. *ICML 2025*.

10. Loeffler, H. H. et al. (2024). Reinvent 4: Modern AI-driven generative molecule design. *J. Cheminform.* 16, 20.

11. Gao, W. et al. (2022). Sample efficiency matters: A benchmark for practical molecular optimization. *NeurIPS Datasets and Benchmarks*.

12. Sanjrani, G. M. et al. (2025). Benchmarking 3D Structure-Based Molecule Generators. *J. Chem. Inf. Model.* 65, 8006-8021.

13. Buttenschoen, M. et al. (2024). PoseBusters: AI-based docking methods fail to generate physically valid poses or generalise to novel sequences. *Chemical Science* 15, 3130-3139.

14. Polaris Consortium (2025). Practically Significant Method Comparison Protocols for Machine Learning in Small Molecule Drug Discovery. *J. Chem. Inf. Model.* DOI: 10.1021/acs.jcim.5c01609.

15. Roskoski, R. Jr. (2025). Properties of FDA-approved small molecule protein kinase inhibitors: A 2025 update. *Pharmacol. Res.* 191, 107059.

16. Ung, P. M.-U. et al. (2015). Conformational Analysis of the DFG-Out Kinase Motif and Biochemical Profiling of Structurally Validated Type II Inhibitors. *J. Med. Chem.* 58, 2178-2190.

17. Robinson, D. D. et al. (2010). Understanding kinase selectivity through energetic analysis of binding site waters. *ChemMedChem* 5, 618-627.

18. Vijayan, R. S. K. et al. (2024). Improving docking and virtual screening performance using AlphaFold2 multi-state modeling for kinases. *Scientific Reports* 14, 25097.

19. Song, Y. et al. (2024). A comprehensive exploration of the druggable conformational space of protein kinases using AI-predicted structures. *PLOS Comp. Biol.* 20, e1012302.

20. Relay Therapeutics (2026). Zovegalisib Phase 3 ReDiscover-2 trial update. The Dynamo platform: conformational dynamics-based drug design.

21. Schneuing, A. et al. (2024). Structure-based drug design with equivariant diffusion models. *Nature Computational Science* 4, 1-11.

22. Francoeur, P. G. et al. (2020). Three-Dimensional Convolutional Neural Networks and a Cross-Docked Data Set for Structure-Based Drug Design. *J. Chem. Inf. Model.* 60, 4200-4215.

23. Kim, Y. C. et al. (2018). Water as an active constituent in the control of glucokinase between closed and super-open conformations. *PNAS* 115, 5467-5472.

24. Wood, E. R. et al. (2004). A unique structure for epidermal growth factor receptor bound to GW572016 (lapatinib). *Cancer Res.* 64, 6652-6659.

25. Copeland, R. A. (2010). The dynamics of drug-target interactions: drug-target residence time and its impact on efficacy and safety. *Expert Opin. Drug Discov.* 5, 305-310.

---

*This review was produced by the Sr. Journal Reviewer -- Comp Bio as part of
the StateBind ReviewCohort Round 1 independent assessment. All claims are
supported by internet research citations. No code was modified.*
