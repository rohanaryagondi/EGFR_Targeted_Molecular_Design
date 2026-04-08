---
agent: Maverick Synth-Bio / DMPK Specialist
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: medchem-P01
---

# Critique: Scoring Function Revision with ADMET and Selectivity Integration

## Reviewing Agent

Dr. Maverick Synth-Bio / DMPK Specialist (synthbio). Expertise in retrosynthetic
planning, DMPK, ADMET profiling, PK/PD modeling, and translational drug design.
This review evaluates medchem-P01 from the perspective of practical translatability:
do the proposed ADMET scoring components reflect real DMPK decision-making, or do
they create a computational illusion of pharmacological rigor? The review pays
particular attention to the hERG threshold calibration, the ADMET composite
weighting scheme, the missing endpoint of metabolic stability, and the question
of whether ML-predicted ADMET scores can meaningfully discriminate among novel
generative chemistry scaffolds.

## Proposal Summary

medchem-P01 proposes replacing StateBind's current 4-component scoring function
(reference similarity 0.35, drug-likeness 0.30, docking 0.20, state specificity
0.15) with a 6-component function that adds ADMET safety (0.15-0.20 weight) and a
cross-docking selectivity proxy (0.10-0.15 weight). The ADMET composite score
aggregates 6 endpoints (hERG, CYP3A4, hepatic clearance, Caco-2, lipophilicity,
solubility) with sub-weights, using kinase-calibrated sigmoid transforms. Critically,
all results are reported under both original and revised scoring to prevent
accusations of p-hacking. Three weight configurations (MPO-Informed, Conservative,
Discovery Mode) are proposed.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The ADMET integration is directionally correct and long overdue,
but the composite design has specific DMPK problems -- the hERG calibration source
is underspecified, the endpoint selection omits the single most important DMPK
parameter (metabolic stability), the equal-ish sub-weighting ignores endpoint
criticality hierarchies, the CYP3A4 treatment is too permissive for a class where
DDI management is a real clinical burden, and the model's applicability domain for
novel scaffolds is unaddressed.

---

## Strengths

1. **Kinase-calibrated thresholds are the right approach.** The proposal correctly
   identifies that standard ADMET thresholds (hERG > 10 uM, MW < 500) reject the
   entire approved EGFR drug class. Calibrating to the ADMET profiles of approved
   EGFR-TKIs (erlotinib, gefitinib, osimertinib, afatinib, dacomitinib) is the
   defensible approach. The argument that "a reviewer cannot argue kinase-calibrated
   thresholds are too lenient without also arguing osimertinib should not have been
   approved" is logically sound and rhetorically strong. The ICH S9 guideline
   (oncology-specific regulatory relaxation) provides additional regulatory support.

2. **Dual reporting protocol is essential and well-designed.** Reporting results under
   both original and revised scoring is the single most important methodological
   decision in the proposal. It preempts the most damaging reviewer criticism
   ("you changed the scoring to make your pipeline win") and turns the scoring
   revision itself into a finding: the observation that scoring function design
   determines which pipeline appears superior is a genuine methodological contribution.
   The weight sensitivity analysis across 6 components using Dirichlet sampling is
   statistically sound.

3. **The selectivity-state connection is a strong publication claim.** Connecting
   DFG-out targeting to kinase selectivity via cross-docking, grounded in the
   Ung et al. (2015) Gini data (0.76 vs 0.58), elevates the paper from
   "we generated molecules" to "conformational state awareness inherently improves
   selectivity." This is the kind of mechanistic insight that JCIM and Nature
   Computational Science value.

4. **Practical integration path leverages existing infrastructure.** The proposal
   correctly identifies that StateBind's scoring architecture already supports
   arbitrary weight configurations and that adding new components requires only
   defining scoring functions, updating the enum, and adding weights. The GNINA
   cross-docking protocol for selectivity reuses the existing docking wrapper.
   This is architecturally disciplined.

5. **The component ablation analysis will be revealing.** Zeroing individual components
   and measuring the impact on the static-vs-state-aware comparison is excellent
   experimental design. If zeroing reference similarity flips the result, that
   alone is a publishable finding.

## Weaknesses

1. **The hERG sigmoid center of 1 uM is derived from the wrong assay format, and
   the proposal does not specify which assay format should calibrate the threshold.**

   The proposal states that osimertinib has hERG IC50 = 0.57 uM (IonWorks) and
   2.21 uM (manual patch clamp), citing Zhong et al. (2023). The proposed sigmoid
   is centered at 1 uM. But which measurement should anchor the calibration?

   This matters enormously. Cross-platform variability for hERG IC50 is well-documented:
   Kramer et al. (Sci Rep, 2020) found 10.4-fold variability for dofetilide across
   automated patch clamp platforms, and averaged automated IC50s were 7x higher than
   manual patch clamp values. IonWorks Quattro consistently produces lower IC50
   estimates than manual patch clamp due to incomplete voltage control and shorter
   drug equilibration times (often < 3 minutes vs the 5-10 minutes needed for
   equilibrium). For terfenadine, the discrepancy reaches 10 nM (manual) vs 77 nM
   (IonWorks) -- a nearly 8-fold shift.

   Osimertinib's 0.57 uM (IonWorks) vs 2.21 uM (manual patch clamp) is a 3.9-fold
   difference, consistent with the known platform bias. The manual patch clamp value
   (2.21 uM) is the regulatory gold standard per ICH S7B Q&A 2.1 best practices
   (Nature Sci Rep, 2025). The IonWorks value (0.57 uM) overestimates potency.

   A sigmoid centered at 1 uM, calibrated against the IonWorks-derived 0.57 uM,
   would give osimertinib a score of ~0.27 -- meaning the scoring function assigns
   a poor safety score to the best drug in the class. But centering at 2.0 uM
   (manual patch clamp reference) gives osimertinib a score of ~0.60, which more
   accurately reflects its real-world risk-benefit status: approved with QTc
   monitoring, not clinically unacceptable.

   The proposal acknowledges this ambiguity (Open Question 3) but does not resolve it.
   It needs to specify: **calibrate to manual patch clamp values**, which are the
   regulatory standard. StateBind's ADMET model was trained on TDC hERG data, which
   itself is a mixture of assay formats (ChEMBL bioactivity data includes IonWorks,
   QPatch, manual patch, and thallium flux assays). The model's predictions thus
   inherit this assay heterogeneity. The sigmoid calibration must account for this.

   - **Severity:** Major
   - **Addressable?** Yes -- specify manual patch clamp as the reference format.
     Center the sigmoid at 2.0 uM (where osimertinib scores ~0.60) or at 1.5 uM
     as a compromise. Test both centers as a sensitivity analysis. Document which
     assay format the TDC training data uses and acknowledge the assay-mixing
     limitation.

2. **The ADMET composite uses quasi-equal sub-weights that do not reflect endpoint
   criticality in real drug programs.**

   The proposed sub-weights are: hERG 0.40, CYP3A4 0.20, clearance 0.15, Caco-2
   0.10, lipophilicity 0.10, solubility 0.05. The proposal argues hERG gets the
   highest weight because "it is the primary safety concern for kinase inhibitors."
   This is correct in direction. But the rest of the weighting is questionable.

   In real pharma DMPK decision-making, endpoints fall into three tiers:

   **Tier 1 -- Program killers (abort the series):**
   - hERG liability below therapeutic margin (kills the program)
   - Metabolic instability / unacceptable clearance (no drug exposure)
   - Hepatotoxicity (DILI is the #1 reason for post-market withdrawals)

   **Tier 2 -- Optimization targets (modify the molecule):**
   - CYP inhibition (DDI management, formulation changes)
   - Caco-2 permeability (formulation engineering, prodrug strategies)
   - Solubility (salt/polymorph/amorphous solid dispersion work)

   **Tier 3 -- Descriptors (track but rarely gate decisions):**
   - Lipophilicity (informational, correlated with multiple other endpoints)
   - Plasma protein binding (relevant for dose projection, not gating)

   Under this framework, the current sub-weights undervalue clearance (0.15 for a
   Tier 1 endpoint) and overvalue lipophilicity (0.10 for what is essentially a
   physicochemical descriptor, not an independent ADMET measurement). Lipophilicity
   is already captured implicitly by the drug-likeness component (cLogP desirability
   function) and by its correlation with hERG, solubility, and metabolic clearance.
   Including it as a separate ADMET sub-component double-counts its contribution.

   - **Severity:** Major
   - **Addressable?** Yes -- restructure sub-weights into a tier-based scheme:
     hERG 0.35, clearance/metabolic stability 0.30, CYP3A4 0.15, Caco-2 0.10,
     solubility 0.10. Remove lipophilicity from the ADMET composite entirely
     (it belongs in drug-likeness) and replace it with metabolic stability
     (see Weakness 6).

3. **ADMETlab 3.0 vs StateBind's trained ADMET model: the proposal defaults to the
   in-house model without adequately weighing the tradeoffs.**

   The proposal recommends Approach A (StateBind's existing model) as lower effort,
   with ADMETlab 3.0 as Approach B. This deserves more careful analysis.

   StateBind's model: 6 endpoints, trained on TDC data (~2,000-8,000 compounds per
   endpoint), hERG AUROC 0.7745, CYP3A4 AUROC 0.7323. These are below TDC leaderboard
   SOTA (hERG: 0.880, CYP3A4: varies by substrate/inhibitor). The model was trained
   on known chemotypes from ChEMBL -- predominantly drug-like molecules from medicinal
   chemistry programs. Its applicability domain for genuinely novel scaffolds from
   a generative model is unknown.

   ADMETlab 3.0: 119 endpoints, trained on >400,000 compounds (1.5x larger than
   ADMETlab 2.0), free API with no registration, batch processing up to 1000 SMILES,
   uncertainty estimates included in predictions. Classification AUC 0.72-0.99 across
   60 endpoints, regression R^2 0.75-0.95 across 18 endpoints. Critically, ADMETlab 3.0
   includes metabolic stability (human liver microsomal stability) -- the endpoint
   StateBind's model lacks entirely (see Weakness 6). It also includes half-life and
   microsomal clearance endpoints.

   The case for ADMETlab 3.0 is stronger than the proposal acknowledges:
   - Broader endpoint coverage (119 vs 6)
   - Uncertainty estimates (StateBind's model provides none)
   - Larger and more diverse training set
   - No training/maintenance burden
   - Includes metabolic stability, half-life, VDss, PPBR

   The case against is real but manageable:
   - External API dependency (but batch processing of 491 SMILES takes minutes)
   - Results are not reproducible if the API changes (but version 3.0 is published
     and stable)
   - Introduces a heterogeneous modeling approach (external predictions for some
     endpoints, internal for others)

   My recommendation: **use both**. Run ADMETlab 3.0 on all candidates for
   comprehensive profiling (119 endpoints, used in the drug-ability assessment and
   as supplementary data). Use StateBind's internal model for the scoring-integrated
   6 endpoints (consistency within the scoring function). Report the correlation
   between the two models' predictions as a concordance check. This avoids the
   "one model rules all" trap and provides the reader with both breadth (ADMETlab)
   and integration (internal model).

   - **Severity:** Minor
   - **Addressable?** Yes -- run both models, use internal for scoring integration,
     ADMETlab for comprehensive profiling and concordance validation.

4. **Threshold calibration uses only approved drugs -- survivorship bias.**

   The proposal calibrates all thresholds to the ADMET profiles of approved EGFR
   drugs. This is reasonable as a lower bound ("approved drugs must pass"), but it
   is circular: approved drugs survived ADMET by definition. The thresholds tell you
   what "good enough to get approved" looks like, but not what "failed in clinic due
   to ADMET" looks like.

   The missing reference class is **failed EGFR-TKI clinical candidates**. Consider:
   - Mobocertinib (EXKIVITY): FDA license withdrawn July 2024. QTc prolongation
     occurred in 11% of patients (grade >=3: 3%), cardiac failure led to 1
     treatment-related death (Takeda, 2023). While withdrawal was primarily due to
     Phase 3 EXCLAIM-2 failing its primary endpoint, the cardiac safety signal was
     a significant clinical liability. Mobocertinib is the cautionary example of
     an EGFR-TKI that was approved (accelerated) despite hERG concerns and
     subsequently withdrawn.
   - Neratinib: Severe diarrhea (gastrointestinal toxicity) was dose-limiting.
   - Poziotinib: Clinical holds due to toxicity.
   - Multiple preclinical EGFR-TKI candidates abandoned due to metabolic instability,
     CYP-mediated DDIs, or hepatotoxicity.

   DICTrank (Cai et al., Drug Discov Today, 2023) provides the largest reference list
   of 1,318 human drugs ranked by drug-induced cardiotoxicity risk using FDA labeling,
   categorized as Most-DICT-Concern (n=341), Less-DICT-Concern (n=528),
   No-DICT-Concern (n=343), and Ambiguous (n=106). Cross-referencing kinase
   inhibitors in DICTrank against the proposed thresholds would provide a more
   balanced calibration that includes both successes and failures.

   The sigmoid calibration should incorporate the ADMET profiles of failed candidates
   as the "penalty zone" boundary, not just the approved drugs as the "acceptable"
   boundary. A threshold calibrated only on survivors will be systematically too
   permissive.

   - **Severity:** Major
   - **Addressable?** Yes -- augment the calibration set with (a) failed EGFR-TKI
     clinical candidates' ADMET profiles where available, (b) DICTrank
     Most-DICT-Concern kinase inhibitors as negative calibrants, and (c)
     mobocertinib as an explicit cautionary reference point for the hERG sigmoid.
     The sigmoid should transition from "acceptable" to "concerning" in the zone
     where failed candidates cluster, not just below the worst approved drug.

5. **CYP3A4 scoring is too permissive and misses the clinical reality of DDI burden.**

   The proposal assigns CYP3A4 inhibitor status a score of 0.6 (vs 1.0 for
   non-inhibitor), with the argument that "CYP3A4 substrate status is class-typical
   for EGFR-TKIs, managed by DDI monitoring." This conflates two distinct issues.

   Being a CYP3A4 **substrate** is indeed class-typical and manageable. All first-
   and third-generation EGFR-TKIs are CYP3A4 substrates: erlotinib (CYP3A4 + CYP1A2),
   gefitinib (CYP3A4/3A5), osimertinib (CYP3A4/3A5), dacomitinib (CYP2D6 -- the
   exception). This means their exposure changes with CYP3A4 inducers/inhibitors. For
   osimertinib, co-administration with a strong CYP3A4 inducer requires doubling the
   dose from 80 mg to 160 mg daily (PMC12008127). This is manageable in oncology.

   Being a CYP3A4 **inhibitor** is a different and more serious concern. A CYP3A4
   inhibitor increases the exposure of co-administered CYP3A4 substrates, potentially
   causing toxicity of other medications the patient is taking. Osimertinib is a weak
   CYP3A inducer (not inhibitor) but does inhibit BCRP. In the real world, NSCLC
   patients take multiple medications simultaneously -- anticoagulants, antiemetics,
   corticosteroids, analgesics -- many of which are CYP3A4 substrates. A potent
   CYP3A4 inhibitor in this setting creates polypharmacy risk.

   A binary score (1.0 non-inhibitor, 0.6 inhibitor) with no gradient is too coarse.
   CYP3A4 inhibition potency varies by orders of magnitude: weak inhibitors
   (2-5 fold AUC change) are manageable; strong inhibitors (>5-fold AUC change)
   are genuinely problematic. The scoring should distinguish at least three levels:
   non-inhibitor (1.0), weak inhibitor (0.7), strong inhibitor (0.3).

   Furthermore, the proposal scores only CYP3A4 and ignores CYP2D6 and CYP2C9,
   which are the other two most clinically relevant CYPs. Dacomitinib is primarily
   metabolized by CYP2D6. Erlotinib involves CYP1A2. A single-CYP scoring component
   captures at most one-third of the DDI liability landscape.

   - **Severity:** Major
   - **Addressable?** Yes -- (a) replace binary with a graded CYP3A4 inhibition
     score based on predicted inhibition potency (weak/moderate/strong), (b) note
     that TDC provides benchmarks for CYP2D6 and CYP2C9 inhibition and substrate
     status (6 CYP datasets total), and StateBind should score at least the top 3
     CYPs (3A4, 2D6, 2C9) if not all 6. ADMETlab 3.0 covers all major CYP isoforms.

6. **Metabolic stability -- the missing endpoint that matters most after hERG.**

   The proposal includes hepatic clearance but omits metabolic stability (human liver
   microsomal half-life, HLM t1/2). These are related but distinct:

   - **Hepatic clearance** (CLint): measured in hepatocyte assays, captures Phase I
     + Phase II metabolism. More physiologically relevant but harder to predict.
   - **Microsomal stability** (HLM t1/2): measured in liver microsomes, captures
     primarily CYP-mediated oxidative metabolism. More standardized, more data
     available, the most commonly used early DMPK screen in pharma.

   In real drug programs, HLM t1/2 is the first metabolic stability measurement
   obtained, typically at the hit-to-lead stage. Compounds with HLM t1/2 < 15
   minutes (high clearance) are deprioritized or fast-tracked for metabolic
   soft-spot analysis. This is arguably a more gating decision than Caco-2
   permeability, which has workarounds (formulation, prodrug).

   TDC includes both CL-Hepa (hepatocyte clearance, 1,020 samples) and CL-Micro
   (microsomal clearance, 1,102 samples) as benchmark datasets. ADMETlab 3.0
   includes HLM stability predictions. The data and models exist.

   The approved EGFR-TKIs have excellent metabolic stability: erlotinib T1/2 >36h,
   gefitinib T1/2 ~52h, osimertinib T1/2 ~48h, dacomitinib T1/2 ~70h
   (PMC6921037). These are all low-clearance compounds (erlotinib CL/F = 4.5 L/h,
   osimertinib CL/F = 14.3 L/h). A generated molecule with high clearance
   (short HLM t1/2) would require impractically high doses and frequent dosing,
   making it clinically non-viable regardless of its binding affinity.

   Omitting metabolic stability while including lipophilicity and solubility as
   separate ADMET sub-components is a misallocation of scoring budget. Lipophilicity
   is a physicochemical descriptor already captured in drug-likeness (cLogP
   desirability function). Metabolic stability is a functional endpoint with direct
   clinical consequences.

   - **Severity:** Critical
   - **Addressable?** Yes -- replace lipophilicity with metabolic stability
     (microsomal clearance) in the ADMET composite. Use either StateBind's
     existing clearance prediction (if it correlates with microsomal data) or
     ADMETlab 3.0's HLM stability prediction. Calibrate the sigmoid to approved
     EGFR-TKI clearance values: penalize molecules with predicted CLint > 50
     uL/min/mg (high clearance), reward those with CLint < 20 uL/min/mg (low
     clearance, consistent with the long half-lives of approved EGFR-TKIs).

7. **The ADMET model's applicability domain for novel scaffolds is unaddressed.**

   This is perhaps the most fundamental concern from a DMPK perspective. The entire
   point of a generative model is to produce novel chemistry. StateBind's ADMET model
   was trained on TDC data derived from ChEMBL -- curated bioactivity data from
   medicinal chemistry literature, heavily biased toward known drug-like chemotypes.

   When the model encounters a genuinely novel scaffold from the SELFIES VAE, its
   predictions may be unreliable. Li et al. (JCIM, 2024) developed conformalized
   fusion regression (CFR) specifically to address this: a GNN model combined with
   conformal prediction to produce calibrated prediction intervals. Their key finding:
   uncertainty quantification is essential for out-of-distribution molecules, and
   standard GNN predictions without UQ are overconfident on novel chemistry.

   StateBind's ADMET model provides point predictions with no uncertainty estimates.
   If a novel scaffold gets an hERG prediction of "0.8 uM" with unknown confidence,
   is that more or less reliable than a well-known quinazoline scaffold getting the
   same prediction? The scoring function treats them identically.

   This creates a systematic bias: the ADMET component will reward molecules that
   look like the training data (known chemotypes with confident predictions) and may
   penalize or give meaningless scores to genuinely novel molecules. This partially
   counteracts the reduction in reference similarity weight -- you remove the
   explicit novelty penalty but introduce an implicit one through ADMET prediction
   confidence bias.

   The severity is difficult to quantify without knowing the chemical diversity of
   StateBind's generated candidates relative to the TDC training set. If the SELFIES
   VAE produces molecules within the training distribution (likely, given SELFIES
   validity constraints), the concern is minor. If it produces substantially
   out-of-distribution molecules, the concern is major.

   ADMETlab 3.0 addresses this partially -- it provides uncertainty estimates in its
   predictions, flagging low-confidence outputs. This is another argument for using
   ADMETlab 3.0 at least as a validation layer.

   - **Severity:** Major
   - **Addressable?** Yes -- (a) compute Tanimoto similarity between generated
     candidates and the nearest neighbor in the TDC training set to assess
     applicability domain coverage, (b) flag candidates with low AD coverage
     in the scoring output, (c) use ADMETlab 3.0 uncertainty estimates as a
     secondary check, (d) report ADMET score distributions stratified by
     novelty (Tanimoto to training set) to show whether ADMET scores correlate
     with chemical similarity to known compounds. If they do, this is evidence
     of AD limitation; if they do not, the model generalizes acceptably.

---

## Feasibility Assessment

### Technical Feasibility

High. The proposal leverages existing StateBind infrastructure (scoring architecture,
ADMET model, GNINA wrapper) and freely available data (PDB structures, ChEMBL reference
sets). The GNINA cross-docking for selectivity is the most compute-intensive step
(~200 GPU-hours) but well within Bouchet cluster capacity. All proposed modifications
are architecturally straightforward given StateBind's extensible scoring design.

### Scientific Feasibility

Moderate-high. The core thesis -- that scoring function design determines which pipeline
appears superior -- is almost certainly true and is already partially demonstrated by
the Dirichlet weight sensitivity analysis. The selectivity signal for DFG-out
candidates is well-grounded in literature (Ung et al., 2015) but may not be
detectable through GNINA cross-docking, which lacks the resolution of FEP or even
MM-GBSA for selectivity discrimination. The ADMET component will produce
differentiable scores, but whether those scores meaningfully discriminate among
candidates depends on the model's accuracy and applicability domain.

### Timeline Feasibility

The 2-3 week estimate is realistic for a minimal implementation (Steps 1-3 and
Step 5 with Config A). The cross-docking selectivity component (Step 4) may extend
to 3-4 weeks if receptor preparation for 5 off-target kinases requires per-target
calibration with ChEMBL reference compounds, which it should. The dual reporting
and ablation analysis (Step 6) is CPU-bound and adds 2-3 days. Total realistic
timeline: 3-4 weeks.

---

## Suggested Modifications

1. **Specify manual patch clamp as the hERG calibration standard.** Center the sigmoid
   at 1.5-2.0 uM (manual patch clamp range for osimertinib), not 1.0 uM (which
   splits the IonWorks/manual range and would give osimertinib a poor score). Test
   both centers as sensitivity analysis. Document the TDC training data's assay
   heterogeneity as a limitation.

2. **Replace lipophilicity with metabolic stability (microsomal clearance) in the
   ADMET composite.** Lipophilicity is a physicochemical descriptor already captured
   by drug-likeness. Metabolic stability is a functional DMPK endpoint that directly
   determines clinical viability (drug exposure, half-life, dosing frequency). Use
   CL-Micro from TDC or ADMETlab 3.0's HLM stability prediction. Calibrate to
   approved EGFR-TKI clearance values.

3. **Restructure ADMET sub-weights by endpoint criticality tier.** Proposed revision:
   hERG 0.35, metabolic stability 0.25, CYP inhibition (multi-CYP) 0.15, Caco-2
   0.15, solubility 0.10. This reflects the DMPK decision hierarchy: safety-critical
   endpoints (hERG, metabolic stability) dominate; optimization-addressable endpoints
   (CYP, Caco-2, solubility) inform but do not gate.

4. **Expand CYP scoring to at least 3 isoforms (3A4, 2D6, 2C9) with graded inhibition
   potency.** Use TDC's 6 CYP benchmark datasets or ADMETlab 3.0's CYP predictions.
   Replace binary scoring (inhibitor/non-inhibitor) with a 3-level gradient
   (non-inhibitor, weak, strong). Average across the 3 CYPs for a composite DDI
   liability score.

5. **Augment calibration with failed clinical candidates.** Add mobocertinib and other
   failed/withdrawn EGFR-TKIs to the calibration set. Use DICTrank
   Most-DICT-Concern kinase inhibitors as negative reference points. The sigmoid
   should penalize molecules that fall in the ADMET zone where clinical failures
   cluster, not just below the worst approved drug.

6. **Add applicability domain assessment for ADMET predictions on novel scaffolds.**
   Compute nearest-neighbor Tanimoto to TDC training set for each candidate. Report
   ADMET score distributions stratified by this distance. Use ADMETlab 3.0 uncertainty
   estimates as a secondary validation layer. Flag candidates where ADMET predictions
   may be unreliable due to out-of-distribution novelty.

7. **Coordinate ADMET sub-component design with synthbio-P01.** My own proposal
   (synthbio-P01) includes ADMETlab 3.0 comprehensive profiling and RAscore
   integration. The ADMET component in medchem-P01 and the ADMET profiling in
   synthbio-P01 should share infrastructure: run ADMETlab 3.0 once for all candidates,
   use the 6 scoring-integrated endpoints for medchem's composite, and use the full
   119-endpoint profile for synthbio's drug-ability assessment.

---

## Alternative Approaches

**Multi-objective Pareto ADMET instead of weighted composite.** Rather than collapsing
6 ADMET endpoints into a single weighted score, an alternative is to use the ADMET
endpoints as Pareto dimensions alongside docking and state specificity. This avoids
the sub-weighting problem entirely: a molecule is Pareto-optimal in ADMET-space if
no other molecule dominates it on ALL ADMET endpoints simultaneously. StateBind
already has Pareto optimization infrastructure in `ranking/pareto.py`. The downside
is that Pareto analysis with 6+ dimensions becomes difficult to interpret and
visualize. A compromise: use 3 aggregated "ADMET pillars" (safety = hERG, metabolic
= clearance + metabolic stability, permeability = Caco-2 + solubility) as Pareto
dimensions alongside docking and state specificity.

**DICTrank-based cardiotoxicity scoring.** Instead of predicting hERG IC50 and
applying a sigmoid, use the DICTrank framework (Cai et al., 2023) to directly classify
cardiotoxicity risk. DICTrank classifiers (JCIM, 2024) use protein targets, electro-
topological state descriptors, and peak plasma concentration to predict risk
categories. This captures the multi-mechanistic nature of cardiotoxicity (not just
hERG) and is calibrated on FDA labeling outcomes, not just in vitro IC50 values.
However, DICTrank requires plasma concentration estimates, which StateBind does not
currently produce (but PKSmart from synthbio-P01 could provide these).

---

## Impact on Publication Narrative

The scoring revision is **essential** for publication credibility. Without it, the
paper's core claim (state-aware > static) rests on a scoring function that assigns
35% weight to resembling three known drugs -- an indefensible design choice that any
reviewer in drug discovery will attack. The revision transforms this weakness into a
strength: the scoring function design itself becomes a finding.

However, the ADMET integration must be done carefully. A poorly calibrated ADMET
component (wrong hERG threshold, missing metabolic stability, applicability domain
issues) could introduce a different set of reviewer criticisms. The proposal is
directionally right but needs the modifications above to withstand DMPK scrutiny at
a venue like JCIM, where reviewers include practicing DMPK scientists.

The coordination with synthbio-P01 is critical: medchem-P01 puts ADMET in the scoring
function; synthbio-P01 provides the comprehensive drug-ability assessment. Together,
they tell the story of "scored molecules that are actually translatable." Separately,
each is incomplete. The publication narrative should present the scoring revision
(medchem-P01) as the quantitative framework and the drug-ability assessment
(synthbio-P01) as the translational validation.

The CYP3A4 scoring in particular needs careful framing. Osimertinib IS a CYP3A4
substrate and weak CYP3A inducer. Penalizing CYP3A4 substrate status would penalize
the best drug in the class. The scoring must distinguish substrate status (neutral)
from inhibitor status (penalized), and this distinction must be explicit in the
methods section. Reviewers familiar with EGFR-TKI pharmacology will check this.

---

## References

1. Kramer J, et al. (2020). Cross-site and cross-platform variability of automated
   patch clamp assessments of drug effects on human cardiac currents in recombinant
   cells. *Scientific Reports*, 10:5627. DOI: 10.1038/s41598-020-62344-w -- 10.4-fold
   hERG IC50 variability across automated platforms; 7x averaged automated vs manual.

2. Multi-laboratory comparisons of manual patch clamp hERG data. (2025). *Scientific
   Reports*. DOI: 10.1038/s41598-025-15761-8 -- Five-laboratory standardized protocol
   comparison; Lab 2 IC50s 5.8-11.3x larger than group averages.

3. Cai C, et al. (2023). DICTrank: The largest reference list of 1318 human drugs
   ranked by risk of drug-induced cardiotoxicity using FDA labeling. *Drug Discovery
   Today*, 28(12):103805. DOI: 10.1016/j.drudis.2023.103805

4. Takeda (2023). Update on EXKIVITY (mobocertinib). October 2, 2023. -- Voluntary
   withdrawal initiated; FDA license withdrawn July 15, 2024. QTc prolongation in
   11% of patients.

5. Li P, et al. (2024). Conformalized Graph Learning for Molecular ADMET Property
   Prediction and Reliable Uncertainty Quantification. *Journal of Chemical Information
   and Modeling*. DOI: 10.1021/acs.jcim.4c01139 -- CFR model for calibrated prediction
   intervals on out-of-distribution molecules.

6. Fu L, et al. (2024). ADMETlab 3.0: an updated comprehensive online ADMET prediction
   platform. *Nucleic Acids Research*, 52(W1):W422-W431. DOI: 10.1093/nar/gkae236 --
   119 endpoints, uncertainty estimates, free API, HLM stability included.

7. Redfern WS, et al. (2003). Relationships between preclinical cardiac
   electrophysiology, clinical QT interval prolongation and torsade de pointes.
   *Cardiovascular Research*, 58:32-45. -- 30-fold hERG safety margin proposal.

8. Abrantes JA, et al. (2023). Safety and efficacy of osimertinib 160 mg daily given
   concurrently with a strong CYP3A4 inducer. *CPT: Pharmacometrics & Systems
   Pharmacology*. PMC12008127 -- Dose-doubling required with CYP3A4 inducers.

9. Thakkar A, et al. (2024). AiZynthFinder 4.0. *Journal of Cheminformatics*, 16:56.
   DOI: 10.1186/s13321-024-00860-x -- RAscore proxy for synthesis feasibility.

10. Ducci M, et al. (2019). FDA- and EMA-Approved Tyrosine Kinase Inhibitors in
    Advanced EGFR-Mutated Non-Small Cell Lung Cancer: Safety, Tolerability, Plasma
    Concentration Monitoring, and Management. *Frontiers in Oncology*, 9:1430.
    PMC6921037. -- Pharmacokinetic comparison table: erlotinib T1/2 >36h CL 4.5 L/h,
    gefitinib T1/2 52h CL 46 L/h, osimertinib T1/2 48.6h CL 17.7 L/h.

11. ICH E14/S7B Q&As. (2022). Clinical and Nonclinical Evaluation of QT/QTc Interval
    Prolongation. FDA. -- Regulatory standard for hERG assessment including recommended
    use of manual patch clamp per Q&A 2.1 best practices.

12. Critical Assessment of ML models for ADMET Prediction in TDC leaderboards. (2026).
    *bioRxiv*. DOI: 10.64898/2026.02.26.708193v1 -- Reproducibility, robustness
    against data leakage, test-set overfitting concerns in TDC benchmarks.

13. TDC ADMET Benchmark Group. 22 datasets including CL-Hepa (1,020 samples),
    CL-Micro (1,102 samples), Half-Life (667 samples), VDss (1,130 samples).
    https://tdcommons.ai/benchmark/admet_group/overview/

14. Zhong Y, et al. (2023). Acute osimertinib exposure induces electrocardiac changes.
    *Frontiers in Pharmacology*, 14:1177003. -- hERG IC50 2.21 uM (HEK293 manual patch
    clamp) vs 0.57 uM (IonWorks Quattro automated).
