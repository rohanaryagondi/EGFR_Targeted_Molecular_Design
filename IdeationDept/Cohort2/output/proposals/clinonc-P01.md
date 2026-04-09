---
agent: Senior Clinical Oncologist
round: 2
date: 2026-04-09
type: proposal
proposal_id: clinonc-P01
title: "Conformational State-Conditioned Generation of DFGout EGFR Inhibitors for C797S Resistance: A Clinically Anchored Computational Methodology Study"
---

# Proposal: Conformational State-Conditioned Generation of DFGout EGFR Inhibitors for C797S Resistance: A Clinically Anchored Computational Methodology Study

## Proposing Agent

**Senior Clinical Oncologist (clinonc)** -- StateBind IdeationDept Cohort2

This proposal connects StateBind's conformational state-aware molecular generation to the
most pressing unmet need in EGFR-targeted therapy: the absence of any DFG-out inhibitor
for patients who develop C797S resistance after osimertinib. The proposal is grounded in
specific clinical trial data, validated structural biology, and an honest assessment of
what a computational methodology study can and cannot claim.

---

## Problem Statement

### The Clinical Gap

Every small-molecule EGFR inhibitor approved or in clinical development targets the DFG-in
(active) conformation. All eight approved EGFR TKIs (erlotinib, gefitinib, afatinib,
dacomitinib, osimertinib, lazertinib, zorifertinib, and amivantamab as a bispecific
antibody) bind EGFR in its active state. Every fourth-generation clinical candidate --
BDTX-1535, BLU-945, BBT-176, TQB3804, BPI-361175, JIN-A02, ES-072 -- also targets DFG-in.
Zero type II (DFG-out) EGFR inhibitors have entered clinical testing.

This monolithic therapeutic approach has a direct clinical consequence: **C797S resistance**.
The cysteine-to-serine substitution at position 797 eliminates the covalent bond anchor
used by all second- and third-generation EGFR TKIs. C797S occurs in 7% of first-line
osimertinib patients (FLAURA data; Ramalingam et al., 2023) and 15-29% of second-line
patients (AURA3 data; Chmielecki et al., 2023; Oxnard et al., 2018). When C797S occurs in
cis with T790M (on the same allele), no approved targeted therapy exists.

The DFG-out conformational state opens an extended hydrophobic pocket (~1913 A^3 vs ~1050
A^3 for the active state; Ung et al., 2019) that does not depend on residue 797. A type II
inhibitor occupying this pocket would bypass the C797S resistance mechanism entirely.

### The Computational Gap

StateBind has demonstrated that conformational state-conditioned molecular generation
produces 10x retrospective enrichment over static single-structure design (EF@10 = 4.95/7.72
vs 0.47/0.79). However, the pipeline currently has no resistance mutation context: all 17
mutations in the context model map to a single state (DFGin/aCin), rendering the mutation-to-
state prediction module uninformative. The pipeline has never been applied to a specific
clinical resistance scenario, which is exactly the translational experiment that would
elevate this work from a methods paper to a clinically significant methods paper.

---

## Vision

**A computational experiment demonstrating that StateBind's conformational state-conditioned
generation can produce novel molecular scaffolds predicted to bind the EGFR-C797S DFG-out
conformation, targeting the most urgent unmet need in EGFR-targeted therapy.**

This is NOT a drug discovery claim. It is a rigorous methodology demonstration with
clinical anchoring. The paper would show:

1. AlphaFold2 with MSA subsampling can predict EGFR mutant structures in multiple
   conformational states, including DFG-out
2. StateBind conditioned on these mutant-specific DFG-out structures generates molecules
   with distinct chemical properties from DFG-in-conditioned candidates
3. The generated DFG-out candidates pass a Target Product Profile (TPP) screen derived
   from real clinical requirements for fourth-generation EGFR inhibitors
4. The approach identifies chemotypes that occupy regions of chemical space unexplored by
   current clinical candidates

**Target venue**: Journal of Chemical Information and Modeling (JCIM) or Journal of
Medicinal Chemistry (JMC)

**Main paper claim**: "Conformational state-conditioned generative design, when applied to
resistance-mutant kinase structures predicted by AlphaFold2, identifies novel DFG-out
chemotypes for EGFR-C797S that are structurally distinct from all clinical-stage EGFR
inhibitors."

---

## Background and Evidence

### Key Evidence

#### 1. Clinical Evidence for the C797S Unmet Need

The standard of care for EGFR-mutant advanced NSCLC is now osimertinib + platinum-pemetrexed
chemotherapy (FLAURA2: median OS 47.5 months, HR 0.77; Planchard et al., 2025) or
amivantamab + lazertinib (MARIPOSA: 3-year OS 60%, HR 0.75; Felip et al., 2025). After
progression on these regimens, C797S resistance leaves patients with no approved targeted
option.

The most promising fourth-generation candidate, BDTX-1535, achieved ORR of 42% (5/19) in
osimertinib-resistant patients with C797S or PACC mutations (Phase 2 data, August 2024 cutoff;
Black Diamond Therapeutics, 2024). Critically, BDTX-1535 is a DFG-in covalent inhibitor --
it does not exploit the DFG-out pocket. Other fourth-generation programs have failed: BBT-176
was terminated (1/18 PR), BLU-945 showed dose-limiting hepatotoxicity (2/18 PR).

The cis-configured triple mutant (L858R/T790M/C797S) is particularly intractable. Recent
preclinical work identified compound D18 as a non-covalent, brain-penetrant inhibitor with
IC50 = 1.3 nM against the triple mutant and >100-fold selectivity over wild-type EGFR
(2025; ScienceDirect). EAI045, the allosteric proof-of-concept, retains activity against
C797S (IC50 3 nM) but requires cetuximab co-treatment due to the asymmetric dimer
accessibility problem (Jia et al., 2016). Neither approach exploits DFG-out targeting as a
primary strategy.

**Bottom line**: 7-29% of osimertinib-treated patients develop C797S resistance. The only
promising clinical candidate (BDTX-1535, 42% ORR) still uses DFG-in binding. No DFG-out EGFR
inhibitor has ever been tested clinically. This is a genuine, quantifiable, unmet need.

#### 2. Structural Evidence: DFG-out Pocket Is Independent of C797

The C797S mutation replaces a cysteine thiol with a serine hydroxyl at the hinge region of the
ATP binding pocket. This eliminates covalent bonding but does NOT alter the DFG motif or the
allosteric pocket. The DFG-out conformation creates an extended hydrophobic pocket adjacent to
the ATP site by flipping Phe856 out of its standard position. Key structural anchors for a
type II inhibitor (contacts with the DFG phenylalanine, the alpha-C-helix, and the back
pocket hydrophobic residues) are structurally remote from position 797.

Available experimental structures:
- **PDB 5ZWJ**: EGFR T790M/C797S/V948R + EAI045, 2.90 A resolution (inactive-like conformation; 2018)
- **PDB 7VRE**: EGFR T790M/C797S + HCD2892, 2.51 A resolution (2022)
- **PDB 7VRA**: EGFR T790M/C797S + HC5476 (2022)
- **PDB 2GS7**: EGFR inactive (Src-like inactive), with AMP-PNP
- **PDB 4I21**: EGFR DFG-out inactive conformation

The V948R mutation in 5ZWJ was required to stabilize the inactive conformation for
crystallization -- illustrating the fundamental challenge: EGFR with activating mutations
strongly prefers the active conformation, making inactive-state crystallography difficult.
This is precisely why computational prediction of inactive conformations is valuable.

#### 3. AlphaFold2 Can Predict Kinase Conformational States

Recent methodological advances demonstrate that AlphaFold2 with MSA subsampling can predict
kinase conformational state populations with >80% accuracy when validated against NMR
experiments (Wayment-Steele et al., 2024, Nature Communications). The key methods:

- **MSA subsampling**: Standard AF2 consistently predicts the DFG-in (active) state for
  kinases. By subsampling the MSA (using fewer sequences), co-evolutionary constraints are
  relaxed, enabling prediction of alternative conformations including DFG-out.

- **AFsample2** (Bjorholm et al., 2025, Communications Biology): Uses random MSA column
  masking to reduce co-evolutionary signals, enhancing structural diversity. Achieved TM-score
  improvements to experimental alternative states exceeding 50% (from 0.58 to 0.98) and
  increased diversity of intermediate conformations by 70% compared to standard AF2.

- **AlphaFold2-RAVE**: Combines AF2 prediction with enhanced sampling to explore DFG loop
  conformational stability, mapping the energy landscape between DFG-in and DFG-out states
  (Herron et al., 2024, JCIM).

**Critical limitation**: Default AF2 predictions for kinases with activating mutations
overwhelmingly produce DFG-in structures. DFG-out predictions have lower confidence
(pLDDT ~75% vs >85% for DFG-in). This is a known bias that must be addressed through
MSA subsampling and validated against existing experimental structures.

#### 4. ProstT5 for Conformational State Discrimination

ESM-2, the widely used protein language model, is sequence-only and CANNOT distinguish
conformational states (identical sequences in different conformations produce identical
embeddings). ProstT5 (Heinzinger et al., 2024, NAR Genomics and Bioinformatics) is a
bilingual protein language model that encodes structure using Foldseek's 3Di alphabet
(20 structural tokens per residue). Because 3Di tokens encode local backbone geometry,
ProstT5 embeddings CAN discriminate between DFG-in and DFG-out conformations of the
same kinase sequence.

Recent work (ProtProfileMD, bioRxiv 2026) demonstrates that supervised fine-tuning of
ProstT5 can predict per-residue 3Di distributions from molecular dynamics, capturing
conformational flexibility. This is directly relevant to validating whether AF2-predicted
conformations cover the physiologically relevant ensemble.

#### 5. Type II Inhibitor Advantages

Type II (DFG-out) kinase inhibitors have established advantages for other targets:
- **Residence time**: 10-100x longer off-rates than type I inhibitors (Pargellis et al., 2002;
  Copeland et al., 2006)
- **Selectivity**: Imatinib binds 2000-3000x more strongly to Abl than to c-Src despite 54%
  sequence identity, because the DFG-out conformation is energetically unfavorable for c-Src
  (Seeliger et al., 2007)
- **Resistance**: Type II inhibitors can overcome gatekeeper mutations by accessing a pocket
  that does not rely on the gatekeeper position for binding (Shah et al., 2004)
- **Clinical success**: Imatinib (BCR-ABL), sorafenib (RAF/VEGFR), nilotinib (BCR-ABL),
  ponatinib (BCR-ABL), all are DFG-out binders with clinical approval

**No type II kinase inhibitor has been tested against EGFR clinically.** This gap is not
because the biology is unfavorable; it is because EGFR strongly favors the active conformation
in the presence of activating mutations, making structure-based design of type II EGFR
inhibitors challenging. Computational generation conditioned on predicted DFG-out structures
offers a path around this obstacle.

### Relationship to Existing Work

**Vision System Ideas**: This proposal builds on deferred ideas 003 (selectivity), 004
(retrosynthesis awareness), and 010 (uncertainty quantification) from the Vision System, but
introduces a fundamentally new element: resistance-mutation-conditioned generation using
predicted mutant structures. No existing Vision System idea proposes this.

**StateBind Current State**: The pipeline's 4-state atlas (DFGin_aCin, DFGin_aCout,
DFGout_aCin, DFGout_aCout) already provides the conditional generation framework. The
proposed experiment extends this by (a) replacing wild-type experimental structures with
mutant-predicted structures and (b) applying the generation to a specific clinical scenario.

**Literature Context**: Conditional generative models for molecular design are actively
published (CVAE with SELFIES, 2024; see PMC11525747). However, no publication has combined
conformational state-conditioned generation with resistance-mutant structures predicted by
AlphaFold2. This combination is genuinely novel.

---

## Proposed Approach

### Overview

A four-phase computational experiment that takes StateBind from a general-purpose
methodology demonstration to a clinically anchored proof-of-concept for DFG-out EGFR
inhibitor design against C797S resistance.

### Implementation Steps

#### Phase 1: Mutant Structure Prediction (Weeks 1-2)

**Objective**: Generate AlphaFold2 structural ensembles for EGFR-C797S in all four
conformational states.

**Protocol**:

1. **Input sequences**: EGFR kinase domain (residues 696-1022) with the following mutation
   combinations:
   - L858R/C797S (most common first-line resistance genotype)
   - L858R/T790M/C797S (cis triple mutant -- the undruggable genotype)
   - Exon19del/C797S
   - Exon19del/T790M/C797S

2. **AF2 with MSA subsampling** (Wayment-Steele et al., 2024 protocol):
   - Compile MSAs using JackHMMER against UniRef90/MGnify databases
   - Generate 160 models per mutant using subsampled MSAs (varying MSA depth from
     16 to full alignment)
   - Cluster output structures by DFG motif geometry: measure dihedral angles of
     Asp855-Phe856-Gly857 and alpha-C-helix position relative to N-lobe

3. **AFsample2 as complementary method** (Bjorholm et al., 2025):
   - Apply random MSA column masking (10-50% of columns) during AF2 inference
   - Generate 200 additional models per mutant
   - Increases conformational diversity by ~70% over standard AF2

4. **State classification**: Assign each predicted structure to one of 4 states using
   StateBind's existing 9D feature vector (structure/features.py):
   - DFG chi1/chi2 angles, alpha-C-helix RMSD, activation loop displacement,
     DFG-Phe position, Lys-Glu salt bridge distance, R-spine alignment,
     pocket volume, hinge angle

5. **Validation against experimental structures**:
   - Compare AF2-predicted DFG-out structures to PDB 5ZWJ (EGFR T790M/C797S/V948R + EAI045)
   and PDB 2GS7 (EGFR inactive)
   - Report binding pocket RMSD (target: median < 2.0 A based on Wayment-Steele benchmark
     of 1.3 A for kinase domains)
   - Report pLDDT scores for DFG-out vs DFG-in predictions (expect ~75% vs >85%)

**Estimated compute**: ~5 min per structure on H200 GPU x 360 models per mutant x 4 mutants
= ~120 GPU-hours. Well within Bouchet cluster capacity.

**Risk mitigation**: If AF2 fails to produce confident DFG-out structures for C797S mutants,
fall back to homology modeling using experimental DFG-out structures (PDB 5ZWJ, 4I21) as
templates with C797S mutations introduced by Rosetta or FoldX. Document this as a limitation.

#### Phase 2: State-Conditioned Generation (Weeks 2-3)

**Objective**: Generate molecules conditioned on C797S-mutant DFG-out structures using
StateBind's existing VAE + MPNN pipeline.

**Protocol**:

1. **Pocket extraction**: Extract binding pockets from Phase 1 DFG-out structures using
   StateBind's existing pocket detection (structure/atlas.py). Expect larger pockets
   (~1900 A^3) than DFG-in structures (~1050 A^3).

2. **Conditioning**: Use StateBind's SELFIES VAE (ml/vae.py; 99.9% validity rate) conditioned
   on:
   - **Experiment A**: C797S-mutant DFG-out pocket features (the proposed approach)
   - **Experiment B**: Wild-type DFG-out pocket features (current StateBind approach)
   - **Experiment C**: C797S-mutant DFG-in pocket features (active-state control)
   - **Experiment D**: Wild-type DFG-in pocket features (static baseline)

3. **Generation scale**: 5,000 molecules per condition (20,000 total). Use the same
   generation hyperparameters and sampling temperature across all conditions to ensure
   a fair comparison.

4. **MPNN scoring**: Score all generated molecules using StateBind's MPNN (ml/mpnn.py;
   R^2 = 0.69) for predicted binding affinity in each pocket context.

5. **ADMET filtering**: Apply StateBind's ADMET model (ml/admet.py; hERG AUROC = 0.77)
   to filter for drug-likeness.

#### Phase 3: Target Product Profile Screen (Weeks 3-4)

**Objective**: Evaluate generated candidates against a clinically derived TPP for a
fourth-generation EGFR inhibitor.

**TPP Criteria** (derived from clinical requirements and competitive landscape):

| Parameter | Threshold | Source/Rationale |
|-----------|-----------|------------------|
| **Predicted IC50 vs EGFR-C797S** | < 100 nM | BDTX-1535 comparator; EAI045 = 3 nM |
| **Selectivity vs WT-EGFR** | > 30-fold | Minimize skin toxicity (class effect) |
| **hERG IC50** | > 10 uM | ES-072 failed on QT prolongation (57.9%) |
| **MW** | 350-600 Da | Type II typically larger; DFG-out pocket accommodation |
| **cLogP** | 1.0-5.0 | Ro5 compliance with type II allowance |
| **TPSA** | < 140 A^2 | Oral bioavailability threshold |
| **HBD** | <= 4 | Oral bioavailability |
| **Rotatable bonds** | <= 10 | Oral bioavailability with flexibility allowance |
| **CNS MPO score** | >= 4.0 (tier 1) / >= 3.0 (tier 2) | Brain metastases filter |
| **Predicted P-gp substrate** | No (tier 1) | CNS penetration requirement |
| **SA score** | < 5.0 | Synthetic accessibility |

**CNS Penetration Analysis** (additional filter for brain metastases relevance):

Given that 25-53% of EGFR-mutant NSCLC patients develop brain metastases (Rangachari
et al., 2015; Li et al., 2023), CNS penetration is a critical differentiator. The CNS
MPO score (Wager et al., 2010) integrates six physicochemical properties (ClogP, ClogD,
MW, TPSA, HBD, pKa), each scored 0-1.0, with a sum >= 4.0 indicating high probability
of BBB penetration.

- **Osimertinib**: MW 499.6, cLogP ~4.5, TPSA ~68 A^2, CSF:plasma 2.5-16%
- **Zorifertinib**: Specifically designed to evade P-gp/BCRP efflux, achieves ~100% CSF:plasma
- **Type II inhibitor challenge**: Larger molecular size (to reach DFG-out pocket) works against
  BBB penetration. This tension must be analyzed honestly.

Report: (a) proportion of candidates meeting each TPP threshold, (b) comparison across
four experimental conditions, (c) CNS MPO distribution stratified by condition, (d)
identification of candidates meeting all TPP criteria simultaneously.

#### Phase 4: Analysis and Publication (Weeks 4-6)

**Objective**: Comprehensive analysis framed for JCIM/JMC publication.

**Key analyses**:

1. **Chemical space comparison**: Visualize generated molecules (all 4 conditions) in UMAP/
   t-SNE space alongside approved EGFR TKIs and clinical candidates. Hypothesis: DFG-out
   conditioned molecules occupy distinct chemical space.

2. **Molecular property distributions**: Compare MW, cLogP, TPSA, HBD, rotatable bonds,
   and SA score across conditions. Hypothesis: DFG-out conditioning shifts properties
   toward higher MW and more rotatable bonds (to reach the extended pocket).

3. **Scaffold analysis**: Extract Murcko scaffolds and compare scaffold diversity across
   conditions. Hypothesis: DFG-out conditioning produces novel scaffolds not present in
   DFG-in conditioned sets.

4. **DFG-out pocket complementarity**: For top-scoring candidates from condition A, perform
   GNINA docking into experimental DFG-out structures (PDB 5ZWJ, 4I21) to validate
   predicted binding mode. Report docking scores and binding pose analysis.

5. **C797S independence analysis**: For top candidates, dock into both C797 (wild-type) and
   C797S (mutant) pockets. A true DFG-out binder should show minimal affinity change upon
   C797S mutation (since the binding mode does not depend on residue 797).

6. **Head-to-head with clinical candidates**: Compare generated DFG-out molecules to
   BDTX-1535, EAI045, and compound D18 on molecular properties (NOT on efficacy). Show
   that computational generation explores regions of chemical space that medicinal chemistry
   has not reached.

7. **Failure mode documentation**: Report honestly which conditions failed, which TPP
   criteria were hardest to satisfy, and what the limitations of AF2-predicted pockets
   are for downstream molecular generation.

### Technical Details

**Compute requirements**:
- Phase 1 (AF2 predictions): ~120 GPU-hours on H200 (Bouchet gpu_h200 partition)
- Phase 2 (VAE generation + MPNN scoring): ~10 GPU-hours
- Phase 3 (TPP filtering + ADMET): ~5 CPU-hours
- Phase 4 (GNINA docking + analysis): ~50 GPU-hours (GNINA on RTX 5000 Ada)
- **Total**: ~185 GPU-hours, approximately 8-10 SLURM jobs over 3-4 weeks

**Software dependencies** (all already available in StateBind):
- AlphaFold2 (requires separate installation; available on Bouchet via module)
- StateBind pipeline: SELFIES VAE, MPNN, ADMET, GNINA wrapper
- RDKit: descriptor calculation, CNS MPO scoring
- Additional: AFsample2 (open-source, GitHub)

**Data requirements**:
- EGFR sequences: UniProt P00533
- Experimental structures: PDB 5ZWJ, 7VRE, 7VRA, 2GS7, 4I21 (all publicly available)
- ChEMBL EGFR activity data (already in StateBind data pipeline)
- Clinical candidate structures: BDTX-1535 (from patent literature), EAI045 (from PDB 5ZWJ)

---

## Impact Assessment

### Publication Impact

**Target venue**: JCIM (primary) or JMC (secondary)

**Novelty claim**: This would be the first publication combining:
- Conformational state-conditioned molecular generation
- Resistance-mutant structures predicted by AlphaFold2
- Clinical TPP-based evaluation of computationally generated candidates
- Direct application to the DFG-out EGFR gap in clinical oncology

**Competitive landscape**: No published work has applied generative molecular design
specifically conditioned on predicted DFG-out EGFR-C797S structures. The closest work is
Chitnis et al. (2025) on SAR for inactive-conformation EGFR inhibitors, but this is
traditional medicinal chemistry, not generative design.

**Expected reviewer reception**: JCIM reviewers will value the methodology rigor (controlled
experiments, multiple conditions, failure mode analysis). JMC reviewers will value the
clinical grounding (specific resistance mutation, specific patient population, specific
competitive landscape). Both will demand honest framing about computational limitations.

**Citation potential**: High. The intersection of AlphaFold2, generative design, and clinical
resistance is a rapidly growing area. The DFG-out EGFR angle is unique and timely.

### Effort Estimate

| Phase | Duration | Personnel | Compute |
|-------|----------|-----------|---------|
| 1. AF2 mutant prediction | 2 weeks | 1 computational scientist | 120 GPU-hours (H200) |
| 2. Conditioned generation | 1 week | 1 computational scientist | 10 GPU-hours |
| 3. TPP screening | 1 week | 1 computational scientist | 5 CPU-hours |
| 4. Analysis + writing | 2-3 weeks | 1 computational + 1 domain expert | 50 GPU-hours |
| **Total** | **6-8 weeks** | | **~185 GPU-hours** |

This is achievable within the Bouchet cluster allocation and does not require external
collaborators, proprietary data, or wet-lab access.

### Risk Assessment

#### Risk 1: AF2 Fails to Produce Confident DFG-out Structures for C797S Mutants

**Likelihood**: Moderate-High. Default AF2 strongly biases toward DFG-in for EGFR with
activating mutations. Even with MSA subsampling, pLDDT for DFG-out predictions may be
low (~75%).

**Mitigation**: (a) Use AFsample2 column masking, which increased conformational diversity
by 70% in benchmarks. (b) Fall back to homology modeling using PDB 5ZWJ/4I21 as templates
with C797S introduced computationally. (c) Report the AF2 limitation honestly as a finding
-- "the difficulty of predicting EGFR DFG-out computationally mirrors the experimental
difficulty of crystallizing this state." This is itself a publishable result.

**Residual impact if risk materializes**: The study proceeds with homology-modeled structures,
which reduces the AF2 novelty but preserves the clinical framing and generation experiment.
The paper becomes more about state-conditioned generation methodology than about AF2
prediction.

#### Risk 2: Generated DFG-out Molecules Fail TPP Criteria

**Likelihood**: Moderate. Type II inhibitors tend to be larger (MW > 500), which conflicts
with BBB penetration requirements. The CNS MPO filter may eliminate most DFG-out candidates.

**Mitigation**: (a) Report this as a genuine finding -- the MW-BBB tension for DFG-out EGFR
inhibitors is a real pharmaceutical challenge that has not been systematically characterized.
(b) Separate the TPP into "systemic" and "CNS-penetrant" tiers, acknowledging that not all
C797S patients have brain metastases. (c) Analyze whether allosteric pocket extension
(DFGout_aCout, which provides the largest pocket) produces even larger molecules than
DFGout_aCin, documenting the structure-property tradeoff.

**Residual impact**: Even negative results (DFG-out molecules are too large for CNS) are
publishable if characterized rigorously. This would be the first systematic computational
analysis of the MW-BBB tradeoff for DFG-out EGFR inhibitors.

#### Risk 3: No Meaningful Difference Between Conditions

**Likelihood**: Low-Moderate. If the VAE does not meaningfully condition on pocket features,
all four conditions may produce similar molecules.

**Mitigation**: (a) StateBind's existing 10x enrichment differential between state-aware
and static generation suggests the conditioning is effective. (b) If differences are small,
this is a finding about the VAE's conditioning capacity, not a failure of the experimental
design. (c) Compare pocket feature vectors between conditions to confirm they are
sufficiently different to expect different molecular outputs.

#### Risk 4: Reviewers Demand Experimental Validation

**Likelihood**: High (near certain for JMC; moderate for JCIM).

**Mitigation**: (a) Frame explicitly as a computational methodology paper, not a drug
discovery paper. (b) Include a "Limitations and Future Directions" section that honestly
states: "Experimental validation of binding affinity, cellular activity, and selectivity
is required before any clinical relevance claim can be made." (c) JCIM is the better
venue because it is specifically for computational methodology; JMC would require at
minimum docking validation, which Phase 4 provides. (d) Cite Insilico Medicine's
ISM001-055 as a precedent for the multi-year timeline from computational hit to clinic,
calibrating expectations.

#### Risk 5: AF2-Predicted Pockets Are Unreliable for Downstream Docking

**Likelihood**: Moderate. AF2 structures are predictions, not experimental structures.
Pocket geometries may have subtle errors that affect docking scores.

**Mitigation**: (a) Validate AF2 pockets against experimental structures first (Phase 1,
step 5). (b) Report GNINA docking scores for both AF2-predicted and experimental pockets,
documenting any discrepancy. (c) Use ensemble docking across multiple predicted conformations
rather than relying on a single structure. (d) This is a known limitation of all
AF2-based drug design and is accepted in the field as long as it is reported honestly
(Hekkelman et al., 2023).

---

## Evaluation Criteria

### Primary Success Criteria

1. **Structural prediction success**: AF2 produces at least 2 conformational states
   (including DFG-out) for at least 2 of the 4 mutant sequences, with binding pocket
   RMSD < 2.5 A to experimental reference structures.

2. **Chemical space differentiation**: DFG-out conditioned molecules (Condition A) are
   statistically distinguishable from DFG-in conditioned molecules (Condition C) in at
   least 3 of the following: MW, cLogP, TPSA, scaffold diversity, docking score distribution
   (p < 0.05, Kolmogorov-Smirnov test).

3. **TPP passage rate**: At least 5% of Condition A molecules pass all systemic TPP criteria
   (excluding CNS filter). At least 1% pass the full TPP including CNS MPO >= 4.0.

4. **C797S independence**: Top-scoring DFG-out candidates show < 2-fold change in predicted
   binding affinity upon C797S mutation, compared to > 10-fold change for DFG-in covalent
   reference inhibitors (osimertinib, afatinib).

### Secondary Success Criteria

5. **Scaffold novelty**: At least 50% of DFG-out Murcko scaffolds are not present in the
   ChEMBL EGFR activity dataset.

6. **Clinical candidate differentiation**: Generated DFG-out molecules occupy a distinct
   region of chemical space from BDTX-1535, EAI045, and approved EGFR TKIs (measured by
   Tanimoto distance > 0.7 from nearest clinical compound).

7. **Honest null reporting**: If any condition fails to produce meaningful results, this
   is documented as a finding, not hidden.

---

## Open Questions

1. **Should the study include ESMFold alongside AF2?** ESMFold is faster (~10 sec per
   structure vs ~5 min for AF2) but may have worse conformational diversity. Including
   both could strengthen the methods comparison, but adds scope.

2. **Which GNINA scoring function version?** StateBind uses GNINA v1.1. The default CNN
   scoring function may not be well-calibrated for DFG-out pockets, which are
   underrepresented in the PDBbind training set. Consider using Vinardo as a complementary
   scoring function.

3. **How to handle the asymmetric dimer problem?** EAI045 requires cetuximab because the
   allosteric pocket is accessible only in one subunit of the EGFR asymmetric dimer.
   Should the study model monomeric or dimeric EGFR? Monomeric is simpler and standard
   for type II inhibitor design; dimeric is more physiologically relevant but
   computationally expensive.

4. **Should ProstT5 be integrated for state classification?** ProstT5's 3Di embeddings
   could replace or supplement the 9D feature vector for conformational state
   classification, but this adds a dependency and scope. A comparison of ProstT5-based
   vs. geometric-feature-based state classification could be a separate contribution.

5. **Pre-registration?** Given the experimental design with defined success criteria,
   consider pre-registering the computational experiment on OSF to signal methodological
   rigor. This is unusual for computational chemistry but increasingly valued.

6. **How to model the triple mutant (L858R/T790M/C797S)?** The T790M gatekeeper mutation
   alters the pocket near the hinge, potentially affecting both DFG-in and DFG-out binding.
   AF2 predictions for triple mutants may be less reliable than for double mutants. Consider
   focusing primarily on L858R/C797S (the most common clinical genotype) and including the
   triple mutant as a secondary analysis.

---

## References

1. Bjorholm T, Kryshtafovych A, et al. AFsample2 predicts multiple conformations and
   ensembles with AlphaFold2. Commun Biol. 2025;8:332.

2. Black Diamond Therapeutics. Phase 2 data: BDTX-1535 in recurrent EGFRm NSCLC. Press
   release, November 2024. NCT05256290.

3. Chitnis SS, et al. Structure-Activity Relationships of Inactive-Conformation Binding
   EGFR Inhibitors: Linking the ATP and Allosteric Pockets. Arch Pharm (Weinheim).
   2025;358:e70027.

4. Chmielecki J, et al. Analysis of acquired resistance mechanisms to osimertinib in
   patients with EGFR-mutated advanced NSCLC from the AURA3 trial. Nat Commun.
   2023;14(1):1071.

5. Copeland RA, Pompliano DL, Meek TD. Drug-target residence time and its implications
   for lead optimization. Nat Rev Drug Discov. 2006;5(9):730-739.

6. Felip E, et al. Overall survival with amivantamab-lazertinib in EGFR-mutated advanced
   NSCLC. N Engl J Med. 2025;393(1):49-61.

7. Hekkelman ML, de Vries I, Wierenga RP, Borsa M, Leigh D, Guskov A. AlphaFill:
   enriching AlphaFold models with ligands and cofactors. Nat Methods. 2023;20:205-213.

8. Heinzinger M, Weissenow K, Gor Sichert J, Steinegger M, Rost B. Bilingual language
   model for protein sequence and structure. NAR Genomics Bioinf. 2024;6(4):lqae150.

9. Herron L, Mondal TK, Bhatt D. Exploring kinase Asp-Phe-Gly (DFG) loop conformational
   stability with AlphaFold2-RAVE. J Chem Inf Model. 2024;64(7):2789-2797.

10. Jia Y, et al. Overcoming EGFR(T790M) and EGFR(C797S) resistance with mutant-selective
    allosteric inhibitors. Nature. 2016;534(7605):129-132.

11. Li L, et al. Brain metastases in patients with EGFR-mutated NSCLC: outcomes and
    prognostic factors. Sci Rep. 2023;13:19123.

12. Oxnard GR, et al. Assessment of resistance mechanisms and clinical implications in
    patients with EGFR T790M-positive lung cancer and acquired resistance to osimertinib.
    JAMA Oncol. 2018;4(11):1527-1534.

13. Pargellis C, et al. Inhibition of p38 MAP kinase by utilizing a novel allosteric binding
    site. Nat Struct Biol. 2002;9:268-272.

14. Planchard D, et al. Survival with osimertinib plus chemotherapy in EGFR-mutated advanced
    NSCLC. N Engl J Med. 2025;393(17):1615-1626.

15. Ramalingam SS, et al. Candidate mechanisms of acquired resistance to first-line
    osimertinib in EGFR-mutated advanced NSCLC. Nat Commun. 2023;14(1):1070.

16. Rangachari D, et al. Brain metastases in patients with EGFR-mutated or ALK-rearranged
    non-small-cell lung cancers. Lung Cancer. 2015;88(1):108-111.

17. Seeliger MA, et al. c-Src binds to the cancer drug imatinib with an inactive Abl/c-Kit
    conformation and a distributed thermodynamic penalty. Structure. 2007;15(3):299-311.

18. Shah NP, et al. Overriding imatinib resistance with a novel ABL kinase inhibitor.
    Science. 2004;305(5682):399-401.

19. Ung PMU, et al. Structural insights into characterizing binding sites in EGFR kinase
    mutants. J Chem Inf Model. 2019;59(1):544-556.

20. Wager TT, et al. Moving beyond rules: the development of a central nervous system
    multiparameter optimization (CNS MPO) approach to enable alignment of druglike
    properties. ACS Chem Neurosci. 2010;1(6):435-449.

21. Wayment-Steele HK, Ojoawo A, Otten R, Wiber JM, Allber A, Colwell L. High-throughput
    prediction of protein conformational distributions with subsampled AlphaFold2. Nat
    Commun. 2024;15:2464.

22. ProtProfileMD: Protein Language Modeling beyond static folds reveals sequence-encoded
    flexibility. bioRxiv 2026. doi:10.64898/2026.01.21.700698v1.
