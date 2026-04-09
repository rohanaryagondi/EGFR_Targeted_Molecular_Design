---
agent: Senior Structural Biologist
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: datasci-P01
---

# Critique: Multi-Kinase Retrospective Validation with Pre-Registered Statistical Design

## Reviewing Agent

Dr. Senior Structural Biologist -- 20+ years in protein structure determination, kinase
conformational biology, KLIFS/KinCore database analysis, and structure-based drug design.
I bring a structure-first perspective: no statistical design survives contact with
structurally infeasible targets. This critique focuses on whether the proposed kinase set
can actually support the conformational state atlas that the statistical framework
requires.

## Proposal Summary

datasci-P01 proposes a pre-registered multi-kinase retrospective validation across 6
kinases (EGFR + ABL1, ALK, BRAF, RET, JAK2) with BEDROC(alpha=20) as the primary
endpoint, BCa bootstrap confidence intervals, a 6-experiment ablation suite, and
Benjamini-Hochberg correction for multiple comparisons. The target is ~21 held-out
drugs across the 6 kinases using a pre-2015 time-split cutoff.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The statistical framework is the strongest component of any proposal
in this round, but half the proposed kinase set is structurally infeasible for the
4-state model, and the proposal must be revised to avoid building a rigorous statistical
analysis on a crumbling structural foundation.

---

## Strengths

1. **The statistical framework is exactly what the publication needs.** BEDROC(alpha=20)
   as the primary endpoint, BCa bootstrap CIs, BH FDR correction, pre-registration on
   OSF -- this addresses every statistical weakness that reviewers would attack. The
   proposal correctly identifies that the current N=5 held-out drugs produce a 95% CI of
   approximately [0.5, 9.4] on EF@10, which spans random performance. No credible venue
   accepts this. The multi-kinase expansion is the only path to publishable statistical
   power.

2. **The ablation suite is essential and well-designed.** Experiment A (unconditioned VAE)
   is correctly identified as the thesis-killing ablation. The comparison hierarchy
   (F vs A, F vs D, A vs E) isolates the 4 confounded factors systematically. The
   quantitative thresholds (Cohen's d >= 0.8 for "large gap") provide objective
   decision criteria. This is the kind of rigor that distinguishes a methods paper from
   a pipeline demonstration.

3. **Pre-registration eliminates the selective reporting problem.** By specifying all
   analysis decisions before running experiments, every outcome becomes publishable.
   The 4-scenario handling (positive, thesis-killed, mixed, EGFR-only) shows mature
   thinking about the full space of possible results. This alone makes the paper
   competitive at JCIM regardless of the outcome.

4. **The per-kinase reference molecule design is careful.** Using only pre-cutoff drugs
   as references avoids temporal leakage. The identification of the osimertinib leakage
   in the pre-2015 EGFR validation is an important catch that must be addressed
   regardless of which kinases are included.

5. **The paired comparison across kinases is the right statistical approach.** Using a
   paired design (state-aware vs static within each kinase, then comparing differences
   across kinases) accounts for target-specific baseline difficulty and is more powerful
   than unpaired comparison.

## Weaknesses

1. **RET is structurally impossible for the state-aware model -- this is a critical flaw
   that invalidates one-sixth of the design.**
   - **Severity:** Critical
   - **Addressable?** Yes -- remove RET and replace with MET.

   My Round 2 research (structbio-R02) assessed every KinCore chain for RET. The result
   is unambiguous: **all 38 RET chains are BLAminus (DFGin active)**. Zero DFGout. Zero
   aCout. Not "limited" -- literally zero structures in any alternative conformational
   state.

   The proposal acknowledges RET has "less conformational diversity than ABL/BRAF" and
   lists it as having "2 (DFGin, some DFGout)" conformational states. This is incorrect.
   There are no RET DFGout structures in KinCore or KLIFS. The proposal may have been
   misled by cabozantinib's DFGout binding to MET (not RET) or by speculative modeling.
   No crystal structure of any compound bound to RET in a DFGout conformation has been
   deposited in the PDB.

   Without at least 2 structurally distinct conformational states, StateBind's state-aware
   pipeline cannot be applied to RET. You cannot build a conformational state atlas with
   one state. RET would collapse to a single-structure analysis identical to the static
   baseline, making the state-aware vs static comparison trivially uninformative.

   The proposal's structural atlas table (Step 1) lists RET with two structures --
   7JU6 (selpercatinib) and 7JU5 (pralsetinib) -- but both are DFGin/aCin. Two
   structures in the same conformational state do not constitute two states. This is a
   fundamental category error.

   **Specific evidence:**
   - KinCore RET page: 38/38 chains = BLAminus (100%)
   - KLIFS RET: All conformational annotations show DFG-in
   - PDB search for RET kinase domain DFGout: zero results
   - All 4 approved RET drugs (vandetanib, cabozantinib, selpercatinib, pralsetinib)
     bind DFGin conformations in their co-crystal structures (2IVU, 7JU6, 7JU5)
   - Cabozantinib binds MET in DFGout but there is no structural evidence it induces
     DFGout in RET

2. **JAK2 JH1 domain lacks the conformational diversity needed -- another kinase that
   cannot support the 4-state model.**
   - **Severity:** Critical
   - **Addressable?** Yes -- remove JAK2.

   The proposal lists JAK2 as having "2+ (DFGin variants)" conformational states and
   "60+ PDB structures." This is misleading because the 60+ structures are almost
   entirely the catalytic JH1 domain in one conformational state.

   My structbio-R02 assessment of KinCore data:
   - **JAK2 JH1 (the catalytic domain, the actual drug target): 61 chains, ALL classified
     as DFGin-None.** Not a single chain in DFGout. Not a single chain in aCout. The
     "None" classification means the dihedral angles do not cleanly map to any of the 8
     Modi/Dunbrack sub-states, suggesting unusual activation loop geometry.
   - JAK2 JH2 (the pseudokinase domain, NOT the drug target): 176 chains with more
     diversity including 3 DFGout structures. These are irrelevant because they describe
     a different domain with a different pocket.

   There is one JAK2 JH1 DFGout structure in the PDB (7TEU, resolution 1.45 A, with
   type II inhibitor YLIU-04-105-1), but it carries 2 mutations, and KinCore may not
   have classified it yet. Even if 7TEU is accepted, the JH1 conformational landscape
   remains: ~61 DFGin + 1 DFGout = 98.4% single-state.

   Furthermore, **all approved JAK2 drugs are type I inhibitors binding DFGin** --
   ruxolitinib, fedratinib, baricitinib, pacritinib. No approved drug binds JAK2 in
   DFGout. CHZ868 (type II) is experimental. The retrospective validation would test
   state-aware vs static for a kinase where every held-out drug binds the same state.
   This cannot produce evidence for or against the state-aware hypothesis.

   The proposal notes JAK2 provides 8+ held-out drugs (the largest set). This is
   numerically attractive but structurally meaningless. Eight type I drugs in one
   conformational state contribute noise, not signal, to a test of conformational
   state-awareness. Including JAK2 would dilute the mean BEDROC effect size by adding
   a kinase where state-aware and static pipelines produce identical results.

3. **ALK is marginal and should be downgraded to optional/stretch.**
   - **Severity:** Major
   - **Addressable?** Yes -- reclassify as optional.

   My structbio-R02 assessment:
   - 68 total chains, 85% ABAminus (an active-like conformation distinct from BLAminus)
   - Only 2 DFGout structures (5IUG at 1.93 A with 1 mutation; 4FNZ with resistance
     mutations)
   - Zero aCout structures
   - All 6 approved ALK drugs are type I, binding DFGin

   ALK fails the state-aware test for the same reason as JAK2: no conformational
   diversity among approved drugs. The difference is that ALK at least has 2 DFGout
   crystal structures, so a 2-state model (DFGin vs DFGout) is technically constructible.
   But with all held-out drugs binding DFGin, the retrospective validation tests nothing
   about state-conditioning.

   ALK's 85% ABAminus dominance also creates a mapping problem. StateBind's DFGin/aCin
   state conflates BLAminus and ABAminus, which are structurally distinct in the
   Modi/Dunbrack system. For EGFR this conflation is acceptable (most active structures
   are BLAminus). For ALK, the dominant conformation is ABAminus -- the 4-state model
   maps differently.

   ALK adds 4 held-out drugs (alectinib, brigatinib, lorlatinib, ensartinib) to the
   total count, which helps statistical power. But these 4 drugs all bind the same
   state, so they contribute to sample size without contributing to the test of
   state-awareness. Including ALK is defensible only for pipeline portability
   demonstration, not for hypothesis testing.

4. **MET is missing from the proposed set despite being structurally superior to RET,
   JAK2, and ALK.**
   - **Severity:** Major
   - **Addressable?** Yes -- add MET to replace RET.

   The proposal excludes MET because "only 2 approved drugs (capmatinib 2020, tepotinib
   2021), both post-2015. Zero training drugs for pre-2015 cutoff." This analysis is
   incomplete.

   My structbio-R02 assessment shows MET has:
   - 126 KinCore chains across 7 conformational states
   - 75 BLBplus (Src-like inactive, 60%) + 31 BBAminus (DFGout, 25%) + 5 BLAminus/
     ABAminus (active) = excellent 3-state coverage
   - One of only 2 kinases (with BRAF) observed in all 5 Ung conformational states
   - Approved drugs with conformational diversity: cabozantinib (type II, DFGout, 2012)
     vs capmatinib (type Ib, DFGin, 2020), tepotinib (type Ib, 2024), savolitinib
     (type Ib, 2021), glumetinib (type Ib, 2023)

   Using a 2011 cutoff (crizotinib approved for ALK 2011 but is a potent MET binder),
   MET holds out cabozantinib (2012, type II), capmatinib (2020), tepotinib (2024),
   savolitinib (2021), and glumetinib (2023) = 5 held-out drugs. Cabozantinib provides
   the critical type II (DFGout) vs type Ib (DFGin) contrast, which is exactly what
   the state-aware hypothesis needs.

   The proposal's exclusion reasoning (zero training drugs pre-2015) assumes the pre-2015
   cutoff is the only option. For MET, a pre-2012 cutoff with crizotinib as the sole
   reference molecule is viable. The per-kinase cutoff approach is more structurally
   honest than forcing all kinases into the same temporal window.

   Alternatively, MET has extensive ChEMBL bioactivity data (thousands of compounds with
   measured potency). A SELFIES VAE trained on pre-2012 ChEMBL MET-active compounds is
   feasible even if there is only one approved reference drug. The pre-cutoff training
   data is ChEMBL compounds, not just approved drugs.

5. **The 3-state vs 4-state problem is not addressed.**
   - **Severity:** Major
   - **Addressable?** Yes -- specify per-kinase state definitions.

   The proposal implicitly assumes the 4-state model (DFGin/out x aCin/out) applies
   uniformly across all kinases. My R02 research shows this is structurally incorrect.

   The DFGout/aCout state is rare across the entire kinome. Ung et al. (2018) found
   that the CODO state (DFGout/aCout equivalent) comprises approximately 1% of all
   kinase structures. Only EGFR has a well-characterized DFGout/aCout representative
   (4ZAU). For ABL1, BRAF, and MET, the 4th state either does not exist in the PDB or
   has no clean representative structure.

   **The practical solution is a 3-state model for most kinases:** DFGin/aCin,
   DFGin/aCout, DFGout/aCin. This covers the three major conformational basins
   observed across the kinome. The 4th state (DFGout/aCout) should be optional, included
   only where structural data supports it (currently EGFR only).

   The publication narrative must address this. The claim cannot be "we applied the
   identical 4-state model to 6 kinases" when structurally that is impossible. Instead:
   "we applied a per-kinase conformational state atlas using 2-4 states based on
   available structural data, with 3 states (DFGin/aCin, DFGin/aCout, DFGout/aCin)
   as the core framework."

   This has statistical implications. If different kinases have different numbers of
   states, the state-conditioning signal differs across kinases. The ablation
   (Experiment A: unconditioned VAE) remains valid, but the interpretation of
   state-conditioning varies by kinase.

6. **The structural atlas table in Step 1 contains errors that could derail implementation.**
   - **Severity:** Major
   - **Addressable?** Yes -- cross-validate all PDB IDs against KLIFS/KinCore.

   Specific issues I identified:

   - **ABL1 table lists 6XR6, 6XR7, 6XRG.** These need KinCore/KLIFS verification. My
     recommended set is: 4WA9 (DFGin/aCin, WT, axitinib), 2G1T (DFGin/aCout, Src-like
     inactive), 2HYY (DFGout/aCin, WT, imatinib, 2.40 A). The 2HYY choice is critical
     because it is the gold-standard imatinib-DFGout structure with wild-type sequence.

   - **BRAF table lists 3OG7 as "DFGin/aCin."** This is incorrect. 3OG7 is the
     vemurafenib-V600E complex, which is DFGin/aCout (type I.5 binding) or DFGout/aCin
     depending on the classifier. BRAF active-state representatives should use 3Q4C
     (WT DFGin/aCin) or 6PP9 (BRAF:MEK1 complex). The DFGout representative should be
     5C9C (LY3009120, type II) or 6XFP (belvarafenib).

   - **RET table lists 7JU6 and 7JU5 as different states.** Both are DFGin/aCin. This is
     not a 2-state atlas; it is two structures of the same state.

   - **JAK2 table lists 3E62 as "DFGin/aCout."** This needs KinCore verification. If
     JAK2 JH1 truly has an aCout structure, this would partially address my concern --
     but KinCore classifies all 61 JH1 chains as DFGin-None, not DFGin/aCout.

   **Recommendation:** Before any implementation, every proposed PDB structure must be
   cross-validated against KinCore conformational classification AND KLIFS conformational
   annotation. Discrepancies between KinCore, KLIFS, and the proposal's assignments must
   be documented and resolved.

7. **The 3W2R mutation issue affects EGFR and should be addressed as a known limitation
   across all kinases.**
   - **Severity:** Minor
   - **Addressable?** Yes -- document systematically.

   The proposal correctly flags 3W2R (T790M/L858R double mutant) as needing verification.
   This issue generalizes: many kinase crystal structures carry mutations that may affect
   conformational state assignments. For each kinase, the structural atlas must document:
   (a) which structures are wild-type, (b) which carry clinically relevant mutations,
   (c) which carry crystallographic mutations (introduced for crystallization). Only WT
   or clinically relevant mutant structures should be used. Crystallographic mutations
   that alter the binding pocket must be excluded or flagged.

   For the proposed kinases:
   - **ABL1:** T315I gatekeeper mutant structures are common. Use WT for the atlas (2HYY
     is WT).
   - **BRAF:** V600E is the therapeutically relevant mutant. Using V600E structures is
     appropriate for the state atlas but must be documented.
   - **MET:** 3DKC (1.52 A, best resolution for DFGin/aCout) carries 3 mutations. A WT
     alternative may need to be identified.

---

## Feasibility Assessment

### Technical Feasibility

The statistical framework is technically straightforward -- BEDROC computation, BCa
bootstrap, BH correction are all well-established methods with available implementations
(oddt, scipy, statsmodels). The per-kinase pipeline (VAE retraining, MPNN retraining,
GNINA docking) reuses existing StateBind infrastructure. The major technical risk is
correctly preparing the conformational state atlas for each kinase, which requires
careful structure selection and KLIFS cross-validation.

**With the revised kinase set (EGFR + ABL1 + BRAF + MET), technical feasibility is
HIGH.** All four kinases have well-characterized 3-state conformational landscapes with
high-quality representative structures in the PDB.

### Scientific Feasibility

The scientific design is sound if the kinase set is corrected. The core question --
does state-conditioning improve retrospective enrichment across multiple kinases? --
is answerable with the revised set. ABL1 provides the richest test (type I vs type II
vs allosteric drugs spanning 3+ conformational states). BRAF provides the largest
structure count. MET provides an unusual conformational distribution (BLBplus-dominant)
that diversifies the test.

The ablation suite ensures scientific rigor regardless of outcome. Pre-registration
makes the study publishable regardless of whether the state-aware hypothesis holds.

**Scientific feasibility is HIGH with the revised kinase set.** The combination of EGFR
+ ABL1 + BRAF + MET covers 4 kinases with genuine conformational diversity among their
approved drugs, enabling a meaningful test of the state-aware hypothesis.

### Timeline Feasibility

The 6-week timeline is ambitious but achievable if the structural atlas is prepared
correctly upfront. The EGFR-first ablation gate (Weeks 2-3) is a good decision point.
However, the structural atlas construction for 3 new kinases (Step 1) requires more
attention than the 1-2 weeks allocated. I recommend 2 full weeks for structure
selection, KLIFS cross-validation, GNINA receptor preparation, and re-docking
validation. This pushes the total to 7-8 weeks, which remains feasible.

---

## Suggested Modifications

1. **Replace the kinase set.** Remove RET and JAK2. Add MET. The revised set is:
   **EGFR + ABL1 + BRAF + MET** (4 kinases, core set) with **ALK as optional** (5th
   kinase, for pipeline portability demonstration only, not for hypothesis testing).

   **Revised held-out drug count with 4 core kinases:**

   | Kinase | Cutoff | Held-Out Drugs | Conformational Diversity |
   |--------|--------|---------------|------------------------|
   | EGFR | 2010 | 5 | Mostly type I |
   | ABL1 | 2005 | 5 (dasatinib, nilotinib, bosutinib, ponatinib, asciminib) | Type I + II + allosteric |
   | BRAF | 2010 | 3 (vemurafenib, dabrafenib, encorafenib) | Type I.5 |
   | MET | 2011 | 5 (cabozantinib, capmatinib, tepotinib, savolitinib, glumetinib) | Type Ib + II |
   | **Total** | | **~18** | |

   18 held-out drugs across 4 kinases. My R02 analysis estimated this yields a 95% CI
   of approximately [2.8, 7.0] on pooled EF@10, which excludes 1.0 (random performance)
   and is publishable.

   Adding ALK (optional): 5 more drugs (all type I), total ~23. Wider CI due to diluted
   conformational signal.

2. **Adopt a per-kinase state model (3 or 4 states) rather than forcing 4 states on all
   kinases.** Specify:
   - EGFR: 4 states (1M17, 2GS7, 3W2R or WT alternative, 4ZAU)
   - ABL1: 3 states (4WA9, 2G1T, 2HYY) + optional DFGinter
   - BRAF: 3 states (3Q4C, 7M0X, 5C9C) -- note V600E issue
   - MET: 3 states (3R7O, 3DKC, 4EEV)

   Document the per-kinase state count as a feature, not a limitation. The publication
   framing becomes: "we adapt the conformational atlas to each kinase's structural
   landscape" -- which is more structurally honest than "we force 4 states on everything."

3. **Cross-validate every proposed PDB structure against KinCore and KLIFS before
   implementation.** Create a verification table with columns: PDB ID, resolution,
   WT/mutant status, KinCore classification, KLIFS classification, proposed StateBind
   state assignment, and any discrepancies. Resolve all discrepancies before proceeding
   to docking.

4. **Use per-kinase time-split cutoffs rather than a uniform pre-2015 cutoff.** The
   kinase drug approval timelines differ substantially. ABL1's first drug was 2001
   (imatinib); BRAF's was 2011 (vemurafenib). A uniform pre-2015 cutoff leaves some
   kinases with 4 training drugs and others with 1. Per-kinase cutoffs maximize both
   training data and held-out drug count. This is more complex to pre-register but more
   structurally and pharmacologically appropriate.

5. **Recompute the power analysis for K=4 kinases (not K=6).** With K=4, the paired
   t-test loses degrees of freedom. The minimum detectable BEDROC difference at 80%
   power with K=4 will be larger than with K=6. The proposal should report the revised
   power analysis to confirm that the study remains adequately powered. My estimate:
   with K=4 and SD=0.08, detecting a mean BEDROC difference of 0.10 requires approximately
   85-90% power -- still feasible, but the margin is thinner.

6. **If ALK is included, explicitly label it as "pipeline portability" rather than
   "hypothesis testing."** ALK cannot test the state-aware hypothesis (all drugs bind
   DFGin). It can demonstrate that the pipeline runs on a kinase with limited
   conformational diversity. This is useful for the paper but should not be pooled into
   the primary BEDROC test, as it would dilute the effect.

---

## Alternative Approaches

The proposal's core statistical framework (BEDROC + BCa + ablation + pre-registration)
is the right approach. The main alternative is in kinase selection:

**Maximum statistical power approach:** Include all structurally feasible kinases (EGFR
+ ABL1 + BRAF + MET) plus ALK and any others with even 2 conformational states, to
maximize total held-out drugs. Risk: dilutes the conformational signal with kinases
where state-awareness is untestable.

**Maximum structural rigor approach:** Include only kinases with 3+ conformational
states AND drugs spanning multiple binding modes (EGFR + ABL1 + MET, possibly BRAF).
This tests the state-aware hypothesis most stringently but with K=3-4 kinases and
reduced statistical power.

I recommend the middle ground: K=4 core kinases (EGFR, ABL1, BRAF, MET) for the
primary analysis, with ALK as a documented extension. This balances structural
feasibility with statistical power.

---

## Impact on Publication Narrative

This proposal is the statistical backbone of the publication. Without it, the 10x
enrichment claim rests on N=5 drugs from one kinase -- unpublishable at a credible
venue. With it (corrected to 4 structurally feasible kinases), the paper transforms
from a case study to a multi-target validation study.

The key narrative impact: **the kinase set must be selected on structural grounds, not
purely on drug count.** Including RET and JAK2 because they have many held-out drugs --
when those drugs all bind the same conformational state -- would produce a study that
appears rigorous (6 kinases! 21 drugs!) but is structurally hollow. Four kinases with
genuine conformational diversity is more scientifically credible than 6 kinases where
half cannot test the hypothesis.

The 3-state vs 4-state issue also shapes the narrative. If the paper claims "4-state
model" but applies it to kinases with only 3 or 2 states, reviewers will attack the
inconsistency. Better to claim "per-kinase conformational state atlas (2-4 states based
on structural data)" from the outset.

---

## References

1. Modi V, Dunbrack RL. (2019). Defining a new nomenclature for the structures of active
   and inactive kinases. PNAS 116:6818-6827.

2. Ung PMU, Rahman R, Schlessinger A. (2018). Redefining the Protein Kinase
   Conformational Space with Machine Learning. Cell Chemical Biology 25:916-924.

3. Fang Z, et al. (2022). KinCore: a web resource for structural classification of
   protein kinases and their inhibitors. Nucleic Acids Research 50:D654-D664.

4. Kanev GK, et al. (2021). KLIFS: an overhaul after the first 5 years of supporting
   kinase research. Nucleic Acids Research 49:D562-D569.

5. Zhao Z, et al. (2014). Conformational Analysis of the DFG-Out Kinase Motif and
   Biochemical Profiling of Structurally Validated Type II Inhibitors. J Med Chem
   58:466-479.

6. Herrington N, et al. (2024). A comprehensive exploration of the druggable
   conformational space of protein kinases using AI-predicted structures. PLOS
   Computational Biology 20:e1012302.

7. Wylie AA, et al. (2017). The allosteric inhibitor ABL001 enables dual targeting of
   BCR-ABL1. Nature 543:733-737.

8. Levinson NM, et al. (2006). A Src-like inactive conformation in the abl tyrosine
   kinase domain. PLoS Biology 4:e144.

9. Grover P, et al. (2024). Next-Generation JAK2 Inhibitors for the Treatment of
   Myeloproliferative Neoplasms. Blood Cancer Discovery 4:352-369.

10. Dang CV, et al. (2025). Molecular Basis of c-MET Inhibition by Approved Small
    Molecule Drugs. ACS Med Chem Lett (2025).

11. Li Y, et al. (2022). Hidden intermediates in the DFG-flip process of c-Met kinase.
    J Chem Inf Model 62:4025-4037.

12. Roskoski R. (2025). Properties of FDA-approved small molecule protein kinase
    inhibitors: A 2025 update. Pharmacological Research 204:107083.

13. Drilon A, et al. (2020). Structural basis of acquired resistance to selpercatinib
    and pralsetinib mediated by non-gatekeeper RET mutations. Annals of Oncology
    32:261-268.

14. Shen Y, et al. (2021). Structural insights into JAK2 inhibition by ruxolitinib,
    fedratinib, and derivatives thereof. J Med Chem 64:2228-2241.
