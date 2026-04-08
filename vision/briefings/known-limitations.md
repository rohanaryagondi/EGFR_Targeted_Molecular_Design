# Known Limitations

**Last updated:** 2026-04-07T20:00:00+00:00
**Briefing session:** 3

---

## Changes Since Last Briefing (Session 2)

Three limitations from the previous briefing have been **partially addressed:**

1. **Docking proxy (Section 1.1):** GNINA physics-based docking is now tier 0 in the
   cascade. The learned proxy (MPNN) is tier 1. The toy MLP is tier 2. The limitation
   is now about GNINA's GPU requirement and runtime cost, not about docking being fake.

2. **Scoring is a fixed weighted sum (Section 1.4):** Pareto multi-objective optimization
   is now implemented alongside the weighted sum. The limitation is now about the
   weighted sum still being the primary ranking method.

3. **No external validation (Section 3.2):** Retrospective time-split validation is now
   implemented at 2010 and 2015 cutoffs. The limitation is now about the small sample
   size (5-7 drugs) and the gap between retrospective and prospective validation.

**Two new limitations added:** GNINA runtime cost (Section 1.5) and retrospective
validation sample size (Section 3.3).

Every limitation below is real. Each one is followed by an **opportunity signal** --
what fixing it would unlock for the project.

---

## 1. Scoring Limitations

### 1.1 Docking is physics-based but environment-dependent

The docking component (20% of the unified score) now has a 4-tier cascade:

| Tier | Method | When Active | Limitation |
|------|--------|-------------|-----------|
| 0 | GNINA (Vina + CNN) | GPU node with GNINA binary | Requires GPU, slow (~minutes/molecule), GNINA v1.1 only (v1.3.2 needs GLIBC 2.29, cluster has 2.28) |
| 1 | MPNN affinity (12.7M params) | Trained checkpoint + PyTorch | Learned proxy, not physics-based. RMSE=0.7182. |
| 2 | DockingProxy MLP | Trained + RDKit | Toy model trained on 34 molecules. Overfits. |
| 3 | Constant 0.5 stub | Always | Zero discriminative power. |

On GPU compute nodes, tier 0 (GNINA) provides real Vina binding energies and CNN binding
predictions. On login nodes or CI, the cascade falls back to tier 1 (MPNN). This means
**scoring results depend on the execution environment.** A molecule scored on a GPU node
gets a physics-based docking score; the same molecule scored on a login node gets a
learned proxy score. The two scores are on different scales despite both being
sigmoid-normalized to [0, 1].

GNINA validation showed clear separation: known binders averaged -7.32 kcal/mol vs
non-binders at -4.16 kcal/mol (delta -3.16). But GNINA has not been run on the full
461-candidate comparison -- the current comparison results use MPNN (tier 1) scores.

> **Opportunity:** Running the full comparison with GNINA on GPU would provide
> physics-grounded docking scores for all candidates and might change the head-to-head
> result. GNINA scores across 4 conformational states would also provide direct evidence
> of state-specific binding -- strengthening the case for state-aware design. A fast
> GNINA-trained surrogate could provide rapid approximate scores for iterative workflows.

### 1.2 Reference similarity uses only 3 molecules

The reference similarity component (35% of the score -- the heaviest weight) computes
Morgan fingerprint Tanimoto similarity against exactly 3 approved EGFR drugs:
erlotinib, gefitinib, and osimertinib. This is a severe bias: it rewards candidates
that look like existing drugs and penalizes structurally novel chemotypes that might
bind EGFR through different interactions.

This bias is the primary driver of the static baseline's mean-score advantage. The 30
static candidates are string-modifications of known compounds and score high on
similarity. The 395 VAE-generated candidates explore diverse chemical space and score
low. The retrospective validation reveals this as misleading: the diverse VAE candidates
include molecules that resemble future drugs, giving the state-aware pipeline 10x
enrichment despite lower mean scores.

> **Opportunity:** Expanding the reference set to all known EGFR active compounds from
> ChEMBL (thousands with IC50 < 100 nM) would capture diverse binding modes. The
> retrospective validation framework already uses restricted reference sets (pre-cutoff
> drugs only) -- this machinery could be extended to use activity-based rather than
> approval-based reference sets.

### 1.3 ADMET is informational only, not a scoring or filtering component

The ADMET predictor (hERG AUROC=0.7745, CYP3A4 AUROC=0.7323) was trained and
integrated, but hard filtering rejects ALL kinase inhibitors on hERG liability. This
is expected -- hERG inhibition is a known class liability for kinase inhibitors. As a
result, ADMET is used informational only: it flags candidates but does not filter or
contribute to the unified score.

> **Opportunity:** Kinase-specific ADMET thresholds (relative to known approved kinase
> inhibitors rather than absolute cutoffs) would make ADMET usable as a scoring
> component. Alternatively, a constrained optimization formulation (maximize affinity
> subject to ADMET being no worse than approved drugs) would integrate safety without
> rejecting the entire compound class.

### 1.4 Scoring is still primarily a fixed weighted sum

The unified score is `0.35*similarity + 0.30*druglikeness + 0.20*docking + 0.15*state`.
Pareto multi-objective optimization is now implemented and provides weight-free
hypervolume comparison, but the weighted sum remains the primary ranking method used
for the head-to-head comparison.

The weights are human-chosen, not optimized. Weight sensitivity analysis shows the
result is moderately sensitive: 44% of random weight combinations favor state-aware,
56% favor static. The linear sum also allows compensation -- a candidate with zero
docking affinity but high similarity to erlotinib still scores well.

> **Opportunity:** Using Pareto front dominance as the primary comparison metric (rather
> than a supplementary analysis) would eliminate weight dependence entirely. The Pareto
> infrastructure (hypervolume, non-dominated sorting, crowding distance) is already
> built -- it would need to become the main result rather than a secondary analysis.

### 1.5 GNINA runtime cost limits throughput

GNINA physics-based docking takes minutes per molecule on GPU. Docking 461 candidates
across 4 conformational states (1,844 docking runs) requires hours of GPU time. This
makes iterative pipeline runs expensive and precludes active learning loops that
require rapid scoring.

> **Opportunity:** GNINA's CNN-only scoring mode is faster than full Vina optimization.
> Alternatively, training a fast surrogate model on GNINA scores (using the existing
> MPNN architecture but with GNINA-generated labels instead of ChEMBL pIC50 values)
> would combine physics-based accuracy with inference-speed scoring.

---

## 2. Scientific Limitations

### 2.1 No experimental validation at any level

Zero wet-lab data. No binding assays, no cell viability tests, no animal models. Every
score is a computational prediction. The retrospective validation (10x enrichment)
provides the strongest evidence that the pipeline identifies real drug-like molecules,
but it is still computational -- it tests whether the pipeline would have ranked known
drugs highly, not whether novel candidates actually bind.

> **Opportunity:** Even a minimal experimental validation -- testing 5-10 top candidates
> in a fluorescence polarization binding assay -- would transform this from a purely
> computational exercise to a validated pipeline. The 10x retrospective enrichment makes
> the case for experimental follow-up compelling: the pipeline demonstrably identifies
> drug-like molecules.

### 2.2 Conformational states are discretized

The 4-state model (DFGin/out x aCin/out) treats kinase conformation as a categorical
variable. In reality, EGFR exists on a continuous conformational landscape with many
intermediate geometries. A molecule designed for "DFGout/aCout" might actually target a
state that is 70% DFGout and 30% DFGin.

The Head AI deferred the continuous conditioning idea (idea 001) because the null result
is not driven by discretization -- the 4-state model correctly separates the
conformational space. But discretization still limits the precision of state-specific
design.

> **Opportunity:** Continuous conformational representations from MD trajectories or
> learned protein structure embeddings would capture the full landscape. This would be
> genuinely novel -- most approaches in the literature also use discrete states.

### 2.3 All 17 mutations map to one state

The curated dataset of 17 EGFR resistance mutations all map to DFGin/aCin in the
context model. The mutation-to-state mapping is uninformative -- it cannot distinguish
between mutations that should shift state preference. The model correctly predicts
one class for all inputs, but this is vacuous.

> **Opportunity:** MD simulations of mutant EGFR structures would reveal actual state
> preferences per mutation. Alternatively, pulling structures of mutant EGFR from the
> PDB (many exist for T790M and L858R) would provide direct structural evidence.

### 2.4 No molecular dynamics

The pipeline uses static crystal structures. Crystal structures are single snapshots --
they do not capture protein flexibility, water-mediated interactions, or the
thermodynamic ensemble of bound states.

> **Opportunity:** Even short MD simulations (10-100 ns) per state would provide an
> ensemble of pocket geometries for ensemble docking. The 4 prepared GNINA receptors
> could be augmented with MD-derived snapshots at modest computational cost.

### 2.5 No selectivity analysis

The pipeline scores binding to EGFR only. It does not check whether candidates also
bind kinases with similar ATP-binding pockets (ABL, BRAF, ALK, SRC, etc.). A molecule
that binds every kinase equally is not a useful drug.

> **Opportunity:** A multi-target MPNN (same architecture, trained on multiple kinases)
> or cross-docking with GNINA against homologous kinase structures would enable
> selectivity profiling. This is a major differentiator -- most generative pipelines
> optimize for a single target. Extending the retrospective validation to other kinases
> would also provide more statistical power for enrichment factor estimates.

---

## 3. ML Limitations

### 3.1 No pre-training on large chemical databases

The MPNN and ADMET models were trained from scratch on moderate datasets (10,466 and
27,698 molecules). Modern molecular property prediction benefits from pre-training on
millions of compounds. The Head AI deferred this (idea 010) because models already meet
target metrics, but generalization to truly novel chemotypes may be limited.

> **Opportunity:** Self-supervised pre-training (masked atom prediction, contrastive
> learning on augmented graphs) before fine-tuning on EGFR data. Existing pre-trained
> encoders (GEM, MolBERT, ChemBERTa) could be leveraged as feature extractors.

### 3.2 Retrospective validation is computational, not prospective

The retrospective time-split validation (WS13) is a significant advance: it
demonstrates 10x enrichment for identifying future approved drugs. But it tests against
known outcomes (drugs that were eventually approved), not against genuinely unknown
future drugs. The enrichment factors are computed against 5 (pre-2010) or 3 (pre-2015)
held-out drugs -- all the approved EGFR drugs that exist.

The pipeline correctly identified afatinib, dacomitinib, and osimertinib at high ranks.
It struggled with lazertinib and mobocertinib (structurally distinct 3rd-generation
compounds), finding them only via moderate Tanimoto similarity (0.46-0.54).

> **Opportunity:** Extending the retrospective validation to other kinase families
> with approved drugs (ALK: crizotinib, ceritinib, alectinib; RET: selpercatinib,
> pralsetinib; etc.) would provide more statistical power and test generalizability.
> The pipeline architecture is target-agnostic -- it needs only conformational state
> data and ChEMBL activity data for the new target.

### 3.3 Retrospective enrichment factors have wide confidence intervals

The enrichment factors (EF@10 = 4.95/7.72 for state-aware) are computed against very
small samples: 5 held-out drugs (pre-2010) and 3 held-out drugs (pre-2015). A single
drug ranked differently could swing the enrichment factor substantially. These are all
the approved EGFR drugs that exist, so the sample cannot be enlarged within EGFR.

> **Opportunity:** Bootstrap confidence intervals on enrichment factors would quantify
> this uncertainty. Multi-kinase validation (see 3.2) is the real solution -- more
> targets means more held-out drugs means tighter confidence intervals.

### 3.4 No uncertainty quantification

All models produce point predictions. The MPNN predicts pIC50 = 6.3, but how confident
is it? Without uncertainty estimates, the pipeline cannot distinguish between
high-confidence and low-confidence predictions.

> **Opportunity:** Ensembles (5-10 models), Monte Carlo dropout, or evidential deep
> learning would provide prediction intervals. The Head AI deferred this (idea 004)
> due to GPU cost; MC dropout would be a lightweight alternative.

### 3.5 VAE generates 1D representations, not 3D structures

The conditional VAE generates SELFIES/SMILES (1D text representations). It has no
concept of how the molecule fits in the EGFR pocket -- it only knows that certain
patterns are associated with active EGFR compounds.

> **Opportunity:** 3D-aware generative models (DiffSBDD, Pocket2Mol, TargetDiff) that
> generate atom coordinates directly in the binding pocket would produce candidates
> structurally optimized for binding. The GNINA infrastructure (prepared receptors,
> docking boxes) is already in place to support pose-aware generation.

### 3.6 No active learning or iterative refinement

The pipeline is one-shot: generate -> score -> rank -> done. There is no mechanism to
learn from scoring results and generate better candidates in the next round.

> **Opportunity:** An active learning loop (generate -> score -> identify most
> promising/uncertain -> retrain -> generate again) would iteratively improve both
> model and candidate pool. The GNINA runtime cost (Section 1.5) is a barrier, but
> a fast surrogate model could enable rapid iteration.

---

## 4. Pipeline Limitations

### 4.1 No retrosynthetic analysis

The pipeline generates molecular structures but never checks whether they can be
synthesized. The SA score is a rough heuristic -- it does not propose actual synthesis
routes.

> **Opportunity:** Integrating a retrosynthetic planning tool (ASKCOS, IBM RXN) would
> filter candidates by synthesizability and provide proposed routes. This bridges
> computation and the wet lab.

### 4.2 No protein-ligand interaction fingerprints

The scoring function evaluates molecules in isolation -- it computes molecular
properties and similarity to known binders, but it never explicitly models how the
molecule interacts with the EGFR protein. GNINA provides binding poses but these are
not yet analyzed for specific interactions (hydrogen bonds, hydrophobic contacts,
pi-stacking).

> **Opportunity:** Extracting interaction fingerprints from GNINA binding poses would
> enable scoring by binding mode, not just binding energy. State-specific interaction
> patterns (e.g., contacts unique to DFGout pocket) could be a powerful discriminator
> for state-aware design.

### 4.3 No water or solvent modeling

The pipeline treats binding as a gas-phase interaction. Displacing water molecules is a
major thermodynamic driving force for binding, but this is not modeled.

> **Opportunity:** WaterMap-style analysis of crystallographic water positions, or
> implicit solvent corrections to GNINA docking scores, would add a thermodynamic
> dimension. Displaced high-energy waters correlate strongly with binding affinity.

---

## 5. What Peer Reviewers Would Attack

1. **"Where is the experimental validation?"** -- Every result is computational. The
   retrospective validation (10x enrichment) partially addresses this by showing the
   pipeline identifies real drugs, but reviewers will still ask why top candidates were
   not tested in a binding assay.

2. **"Why only 3 reference molecules for 35% of the score?"** -- The heaviest scoring
   component compares against 3 drugs. The retrospective validation exposes this bias:
   the reference similarity component penalizes the diverse VAE candidates that contain
   future-drug-like molecules.

3. **"Enrichment factors are based on 3-5 drugs."** -- The retrospective validation
   sample is small. Confidence intervals are wide. Reviewers will question whether the
   10x enrichment is robust.

4. **"4 discrete states is a gross oversimplification."** -- The conformational
   landscape is continuous. The 4-state model is standard in the kinase literature but
   still a simplification.

5. **"The state-aware advantage is only 15% of the score."** -- If the improvement
   comes entirely from 15% weight, reviewers will question whether the comparison
   is sufficiently powered or whether increasing the weight would change the result.

6. **"No comparison to existing generative models."** -- The pipeline should benchmark
   against published molecular generation methods (REINVENT, GraphAF, MolGPT) to
   contextualize its results.

---

## 6. What Drug Discovery Practitioners Would Find Naive

1. **No lead optimization cycle.** Real drug design is iterative: design -> synthesize ->
   test -> redesign. This pipeline is one-shot. The GNINA and Pareto infrastructure
   support iteration, but no active learning loop exists.

2. **No ADMET in scoring.** Safety should be a hard constraint, not a post-hoc
   annotation. The hERG problem (kinase inhibitors inherently fail) is a real challenge,
   but practitioners would expect a kinase-calibrated threshold, not a blanket exemption.

3. **No consideration of intellectual property.** Generated molecules may infringe
   existing patents. Freedom-to-operate analysis is standard in pharma.

4. **No formulation or delivery considerations.** A molecule that binds perfectly but
   cannot be formulated for oral delivery is not a drug candidate.

5. **Pocket shape not exploited in generation.** Pocket volumes range from 450 to 850
   cubic angstroms across states, but the VAE generates 1D strings without awareness
   of 3D pocket geometry. The GNINA receptors are prepared for all 4 states -- a
   3D-aware generator could use them.
