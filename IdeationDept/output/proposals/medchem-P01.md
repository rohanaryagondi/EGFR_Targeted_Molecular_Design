---
agent: Senior Medicinal Chemist
round: 2
date: 2026-04-08
type: proposal
proposal_id: medchem-P01
title: "Scoring Function Revision with ADMET and Selectivity Integration"
---

# Proposal: Scoring Function Revision with ADMET and Selectivity Integration

## Proposing Agent

Dr. Senior Medicinal Chemist (medchem). 20+ years in kinase drug discovery, lead
optimization, multi-parameter optimization, and clinical candidate selection. This
proposal addresses the single most damaging methodological weakness in StateBind from
a drug design perspective: a scoring function that penalizes the very molecules it
should be rewarding.

## Problem Statement

StateBind's unified scoring function (0.35 reference similarity + 0.30 drug-likeness +
0.20 docking + 0.15 state specificity) has four fundamental problems that undermine
both scientific credibility and real-world relevance:

1. **Reference similarity at 35% rewards imitation, not innovation.** The largest single
   scoring component measures Morgan/ECFP4 Tanimoto similarity to erlotinib, gefitinib,
   and osimertinib. This penalizes novel scaffolds -- exactly the molecules a generative
   model should produce. Chen et al. (Front Bioinf 2025) showed that 60% of similarly
   bioactive ligand pairs have Tanimoto < 0.30. The static baseline wins on mean score
   (0.5437 vs 0.4378) primarily because its 30 template-based candidates are structural
   analogs of these three reference drugs.

2. **QED penalizes kinase inhibitors.** Osimertinib, the standard-of-care EGFR drug and
   a multi-billion-dollar molecule, scores QED = 0.31. Among all FDA-approved kinase
   inhibitors, 48% violate Lipinski's Rule of 5 (Roskoski 2026). The drug-likeness
   component (15% effective weight for QED alone) actively punishes molecules that
   resemble successful kinase drugs.

3. **ADMET is absent from scoring despite a trained model existing.** StateBind has a
   multi-task ADMET model (hERG AUROC 0.7745, CYP3A4 AUROC 0.7323) that is used only
   informationally. Hard hERG filtering at the standard 10 uM threshold rejects ALL
   kinase inhibitors -- including osimertinib (hERG IC50 = 0.57 uM), which is approved
   and clinically used with monitoring. The field has moved to ADMET-in-the-loop design
   (REINVENT 4, ADMETrix, PMMG, Chemistry42).

4. **Zero selectivity assessment.** No evaluation of off-target kinase binding exists.
   EGFR shares >30% ATP site identity with 50+ kinases. A molecule with high EGFR
   affinity and equally high ABL1/BRAF/SRC affinity is a toxicity liability, not a drug
   candidate.

These are not cosmetic issues. They are the problems reviewers at JCIM or Nature
Computational Science would attack first, and they directly confound the head-to-head
comparison that is the paper's core result.

## Vision

A revised 6-component scoring function that reflects real medicinal chemistry
multi-parameter optimization practice: binding affinity, state specificity, ADMET safety,
kinase selectivity, kinase-appropriate physicochemical properties, and a reduced
(but not eliminated) reference similarity anchor. Results reported under BOTH original
and revised scoring to maintain scientific integrity. The scoring revision itself
becomes a publishable contribution: "Conventional similarity-based scoring systematically
penalizes the exploration that generative models are designed to enable."

---

## Background and Evidence

### The Scoring Function Drives the Outcome -- And the Current Weights Are Indefensible

The weight sensitivity analysis already shows this: 56% of random Dirichlet weight
configurations favor static, 44% favor state-aware. The state-aware pipeline can ONLY
gain advantage from the state specificity component (15% of score). Yet 44% of random
configurations still favor it -- meaning state-aware candidates are competitive on
drug-likeness and docking while providing unique state information. When reference
similarity weight drops below 0.20, state-aware is favored in >60% of configurations
(medchem-R01, Finding 12). The scoring function is not measuring drug quality; it is
measuring resemblance to three known drugs.

### Key Evidence

1. **Tanimoto is a poor bioactivity proxy.** Chen et al. (Front Bioinf 2025) developed
   BSI (Bioactivity Similarity Index), a deep learning model trained on ChEMBL using
   leave-one-protein-out cross-validation. In a virtual screening scenario for ADRA2B,
   BSI achieved mean rank 3.9 for the next active compound vs Tanimoto's 45.2 -- a 12x
   improvement. BSI outperforms ChemBERTa and CLAMP cosine similarity. This demonstrates
   that structural similarity is not a reliable proxy for functional similarity.

2. **Erlotinib is NOT conformationally selective.** Park et al. (2012) showed erlotinib
   binds both active and inactive EGFR with comparable affinity. Using erlotinib as a
   reference molecule in a scoring function designed to reward state-specific design is
   internally contradictory. The reference set conflates the very thing the pipeline is
   trying to resolve.

3. **48% of approved kinase inhibitors violate Ro5.** Roskoski's 2026 survey of 94
   FDA-approved small molecule kinase inhibitors found 45 (48%) violate at least one
   Lipinski rule. Most common violation: MW > 500 (28 compounds). The Lipinski/QED
   framework was calibrated on oral drugs broadly, not on kinase inhibitors specifically.
   Mean MW of approved kinase inhibitors is 472 Da (range 285-615), with a distribution
   centered above what QED considers optimal.

4. **Approved EGFR inhibitors have hERG IC50 values of 0.57-5.3 uM.** Osimertinib
   hERG IC50 = 0.57 uM in IonWorks assay, 2.21 uM in manual patch clamp (Zhong et al.,
   Front Pharmacol 2023). Gefitinib hERG IC50 = 1.91 uM (Wang et al., 2021). Lazertinib
   hERG IC50 = 5.3 uM. The standard 10 uM "safe" threshold used by most ADMET models
   rejects the entire approved EGFR drug class. Kinase-calibrated thresholds (>1 uM with
   safety margin monitoring) are clinically justified.

5. **Type II (DFG-out) inhibitors are significantly more selective.** Ung et al. (J Med
   Chem 2015) analyzed 257 DFG-out kinase crystal structures and found mean Gini
   selectivity coefficient of 0.76 for type II vs 0.58 for type I (p < 10^-4). The
   DFG-out pocket sequence is less conserved across kinases, providing a structural basis
   for this selectivity advantage. StateBind designs molecules for DFG-out states but
   never measures or claims the resulting selectivity benefit.

6. **ADMET-in-the-loop is now standard.** REINVENT 4 (Loeffler et al., J Cheminf 2024)
   supports weighted multi-component scoring including ADMET endpoints. ADMETrix (Mourdou
   et al., 2026) ranks 9th on TDC hERG leaderboard (AUROC 0.836) while integrated into
   the generative loop. PMMG (Advanced Science 2025) achieves 51.65% multi-objective
   success with simultaneous ADMET optimization. StateBind's post-hoc-only ADMET approach
   is increasingly out of step with the field.

7. **ADMETlab 3.0 provides 119 endpoints via free API.** Fu et al. (Nucleic Acids Res
   2024) describe 119 ADMET endpoints with classification AUC 0.72-0.99 and regression
   R^2 0.75-0.95. No model training required -- SMILES-in, predictions-out. This is the
   lowest-effort path to comprehensive ADMET profiling.

### Relationship to Existing Work

- **StateBind current state:** The unified scoring function lives in
  `ranking/scoring.py:125-130` with DEFAULT_WEIGHTS. The architecture already supports
  arbitrary weight configurations (weights must sum to 1.0, enforced at runtime). The
  ADMET model exists in `ml/admet.py`. GNINA docking infrastructure is validated for EGFR
  and could be extended to off-target kinases.

- **Vision System ideas:** This proposal builds on deferred idea **003 (Kinome-Wide
  Selectivity Panel)** by proposing a focused cross-docking selectivity proxy as a
  scoring component, and on deferred idea **006 (Learned Chemical Similarity)** by
  proposing BSI or pharmacophore fingerprints to replace Tanimoto. It does not duplicate
  either -- 003 proposed a full kinome-wide MPNN, and 006 proposed learned embeddings
  trained from scratch. This proposal is more pragmatic and focused.

- **Literature precedent:** Multi-parameter optimization is standard in pharma (Pfizer
  Mechanistic PK MPO achieves >0.95 AUCROC for clinical short-listing; Lombardo et al.
  2024). The PMMG algorithm (Advanced Science 2025) demonstrates simultaneous
  optimization of binding, ADMET, drug-likeness, and synthesizability. What is novel here
  is applying MPO principles to a conformational-state-aware pipeline, connecting state
  specificity to selectivity, and demonstrating that scoring function design critically
  determines whether state-aware or static design appears superior.

---

## Proposed Approach

### Overview

Replace the current 4-component scoring function with a 6-component function that
reflects real medicinal chemistry multi-parameter optimization. The two new components
are ADMET safety (using kinase-calibrated thresholds) and a computational selectivity
proxy (cross-docking against off-target kinases). Reference similarity weight is
reduced sharply. Drug-likeness is revised with kinase-specific desirability functions.
All results are reported under BOTH original and revised scoring to maintain scientific
honesty and to allow the data -- not the weight choice -- to determine which pipeline
is superior.

### Implementation Steps

#### Step 1: Reference Similarity Revision (Days 1-3)

**Action:** Reduce weight from 0.35 to 0.10-0.15. Evaluate alternative similarity metrics.

*Option A (minimal, recommended):* Keep Morgan/ECFP4 Tanimoto but reduce weight to 0.10.
This is the simplest change and avoids introducing new dependencies. The 10% anchor
still rewards EGFR-relevant pharmacophores without overwhelming the score.

*Option B (moderate):* Replace Morgan Tanimoto with pharmacophore-based fingerprints
(e.g., FCFP4 or ErG fingerprints). These encode interaction patterns rather than exact
substructures, capturing functional equivalence that Tanimoto misses.

*Option C (aspirational):* Replace with BSI (Bioactivity Similarity Index; Chen et al.
2025). Requires running the pre-trained BSI model on all candidates. BSI achieved 12x
improvement over Tanimoto in mean active rank. However, this introduces a new model
dependency and the BSI model may not be publicly available as a ready-to-use tool.

**Recommendation:** Option A for the initial revision. Option B as a sensitivity analysis.
The weight reduction from 0.35 to 0.10 alone will eliminate the dominant bias toward
template-like molecules. Tanimoto's limitations are well-documented, but 10% weight
limits the damage.

**Erlotinib reference issue:** Erlotinib binds both active and inactive EGFR (Park et al.
2012), making it a poor reference for state-specific design. Consider replacing erlotinib
with lapatinib (which preferentially binds the inactive conformation) or simply accepting
that the reference set provides a general EGFR pharmacophore anchor, not a state-specific
one.

#### Step 2: Drug-Likeness Revision (Days 3-5)

**Action:** Replace QED with kinase-inhibitor-specific desirability functions.

The kinase inhibitor property space is distinct from the general oral drug space. Based
on the distribution of 94 FDA-approved kinase inhibitors (Roskoski 2026):

**Proposed kinase-specific desirability functions:**

| Property | Optimal Range | Decay | Basis |
|----------|--------------|-------|-------|
| MW | 350-550 Da | Linear to 0 at 250/700 | Mean approved KI: 472 Da |
| cLogP | 1.0-4.5 | Linear to 0 at -1/7 | Approved KI range, balances permeability/solubility |
| PSA | 50-130 A^2 | Linear to 0 at 20/200 | Approved KI range, oral absorption |
| Rotatable bonds | 3-12 | Linear to 0 at 0/18 | Approved KI range |
| HBD | 0-3 | Step to 0.5 at 4-5, 0 at >5 | Permeability constraint |

Composite score: weighted geometric mean of 5 desirability functions.

This replaces QED (50%) + Lipinski pass/fail (25%) within the drug-likeness component.
SA score (25%) is retained as-is within drug-likeness. The overall drug-likeness weight
is reduced from 0.30 to 0.15.

**Validation:** Apply the revised desirability functions to the 94 approved kinase
inhibitors. The revised score should rate >80% of them as "acceptable" (score > 0.5),
compared to QED which rates ~50% below 0.5.

#### Step 3: ADMET Integration (Days 5-10)

**Action:** Create a composite ADMET scoring component and integrate into the unified
scoring function at 0.15-0.20 weight.

**Approach A (recommended, lower effort):** Use StateBind's existing ADMET model with
kinase-calibrated thresholds.

The existing model predicts 6 endpoints. Map each to a continuous [0, 1] score using
kinase-calibrated sigmoid transforms:

| Endpoint | Transform | Calibration Basis |
|----------|-----------|-------------------|
| hERG | sigmoid((predicted_IC50 - 1.0) / 0.5) | Osimertinib approved at 0.57 uM; 1 uM center reflects class reality |
| CYP3A4 | 1.0 if non-inhibitor; 0.6 if inhibitor | CYP3A4 substrate status is class-typical for EGFR-TKIs, managed by DDI monitoring |
| Hepatic clearance | sigmoid((30 - predicted_CLint) / 10) | Reward stability > 30 min in HLM; approved TKIs have T1/2 of 36-48h |
| Caco-2 permeability | sigmoid((predicted_logPapp + 5.15) / 0.5) | Approved TKIs have oral F of 60-70% |
| Lipophilicity | 1.0 - abs(predicted_logD - 3.0) / 3.0, clipped [0,1] | Optimal ~3.0 for kinase inhibitors |
| Solubility | sigmoid((predicted_logS + 4.0) / 1.0) | Minimum solubility for oral formulation |

**Composite ADMET score:** 0.40 * hERG + 0.20 * CYP3A4 + 0.15 * clearance + 0.10 *
Caco-2 + 0.10 * lipophilicity + 0.05 * solubility.

hERG gets the highest sub-weight because it is the primary safety concern for kinase
inhibitors and the endpoint most likely to cause clinical failure. The 0.40 hERG
sub-weight reflects the reality that QT prolongation was the dose-limiting toxicity
that constrained nilotinib, was a labeling concern for osimertinib, and contributed to
mobocertinib's withdrawal.

**Approach B (higher effort, better coverage):** Augment with ADMETlab 3.0 API
predictions (119 endpoints). Script the API calls for all 461 + 30 candidates. Select
the 10-15 most clinically relevant endpoints. Use the same kinase-calibrated sigmoid
transforms. This provides broader coverage but introduces an external API dependency.

**Kinase-calibrated thresholds vs standard thresholds -- the key argument:**

| Property | Standard Threshold | Kinase-Calibrated | Approved Drug Evidence |
|----------|-------------------|-------------------|----------------------|
| hERG IC50 | > 10 uM | > 1 uM | Osimertinib: 0.57 uM (approved) |
| CYP3A4 | Non-inhibitor | Substrate status acceptable | All 1st/3rd gen EGFR-TKIs are CYP3A4 substrates |
| Oral F | > 30% | > 30% | Erlotinib/Gefitinib/Osimertinib: 60-70% |
| MW | < 500 | < 600 | Mean approved KI: 472 Da; range to 615 |

This calibration is defensible because oncology drug development explicitly accepts
higher safety risks in exchange for efficacy (ICH S9 guideline). A reviewer cannot argue
that kinase-calibrated thresholds are too lenient without also arguing that osimertinib
should not have been approved.

#### Step 4: Selectivity Proxy via Cross-Docking (Days 8-14)

**Action:** Add a selectivity component using GNINA cross-docking against 5 off-target
kinases.

**Off-target panel selection:**

| Kinase | PDB ID | Justification |
|--------|--------|---------------|
| ERBB2/HER2 | 3PP0 (DFGin/aCin) | Most closely related; off-target HER2 inhibition causes cardiotoxicity |
| ABL1 | 2HYY (DFGout) | Paradigmatic kinase; imatinib off-target effects well-characterized |
| SRC | 2SRC (DFGin/aCin) | Proto-oncogene kinase; dasatinib cross-reactivity well-studied |
| BRAF | 1UWH (DFGin/aCin) | Critical in melanoma; cross-reactivity with EGFR inhibitors documented |
| MET | 2WGJ (DFGin/aCin) | EGFR-MET cross-talk drives resistance; selectivity clinically relevant |

**Scoring:**
- Dock each candidate against all 5 off-target kinases using GNINA (same protocol as EGFR)
- Normalize each off-target docking score to [0, 1] using the same sigmoid transform
- Selectivity score = 1.0 - max(off_target_normalized_scores)
- A molecule that binds strongly to any off-target kinase gets a low selectivity score
- A molecule that binds EGFR strongly but off-targets weakly gets a high selectivity score

**Compute cost:** 491 candidates x 5 off-targets = 2,455 docking runs. At GNINA's rate
of ~minutes per molecule on GPU, this requires approximately 40-80 GPU-hours on H200.
Feasible within a single day on Bouchet (1 node, 8 H200 GPUs) or spread across multiple
scavenge_gpu jobs.

**The state-selectivity argument this enables:** If state-aware candidates targeting
DFG-out conformations show higher selectivity scores than active-state binders (as the
type II Gini data predicts: 0.76 vs 0.58), this provides direct evidence that
conformational state awareness improves selectivity. This transforms the paper from
"state-aware improves retrospective enrichment" to "state-aware inherently selects for
more selective, more drug-like molecules."

**Quantifying the selectivity advantage:** Partition state-aware candidates by their
target state. Compute mean selectivity score for DFGin/aCin, DFGin/aCout, DFGout/aCin,
DFGout/aCout candidates. Test whether DFG-out candidates have significantly higher
selectivity scores (expected: yes, based on Ung et al. 2015 Gini data). Report the
distribution, not just the mean.

#### Step 5: Assemble the Revised Scoring Function (Days 12-16)

**Proposed weight configurations:**

**Config A -- MPO-Informed (recommended primary):**

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Reference similarity | 0.10 | Reduced from 0.35; provides EGFR pharmacophore anchor without dominating |
| Drug-likeness (kinase-specific) | 0.15 | Reduced from 0.30; kinase desirability replaces QED/Lipinski |
| Docking affinity | 0.20 | Unchanged; primary binding assessment |
| State specificity | 0.20 | Increased from 0.15; the thesis variable |
| ADMET composite | 0.20 | NEW; kinase-calibrated safety assessment |
| Selectivity proxy | 0.15 | NEW; off-target kinase binding assessment |

Rationale: Mirrors the weight distribution of a real pharma MPO (25-30% potency, 15-20%
selectivity, 15-20% ADMET, 10-15% properties, 5-10% novelty). The state specificity
component (0.20) is justified as a "selectivity predictor" given the type II selectivity
evidence.

**Config B -- Conservative:**

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Reference similarity | 0.20 | Moderate reduction; preserves comparability to original |
| Drug-likeness (kinase-specific) | 0.20 | Slight reduction |
| Docking affinity | 0.20 | Unchanged |
| State specificity | 0.15 | Unchanged |
| ADMET composite | 0.15 | NEW; lower weight limits impact |
| Selectivity proxy | 0.10 | NEW; lower weight limits impact |

Rationale: Minimizes the change from original scoring while still incorporating the
missing components. If the enrichment result holds under this conservative revision,
it is robust to scoring function design.

**Config C -- Discovery Mode:**

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Reference similarity | 0.05 | Near-elimination; maximum novelty exploration |
| Drug-likeness (kinase-specific) | 0.10 | Minimal constraint |
| Docking affinity | 0.25 | Highest single weight; binding is primary |
| State specificity | 0.20 | Strong thesis signal |
| ADMET composite | 0.20 | Strong safety signal |
| Selectivity proxy | 0.20 | Strong selectivity signal |

Rationale: Maximally rewards binding, safety, and selectivity while minimizing the
penalty on novelty. This is the "what would a medicinal chemist actually optimize?"
configuration.

#### Step 6: Dual Reporting and Sensitivity Analysis (Days 14-20)

**Critical constraint: dual reporting protocol.**

datasci's warning in the Round 1 synthesis is correct: changing the scoring function
to make state-aware win is scientifically questionable. The proposal MUST:

1. **Report all results under BOTH original and revised scoring.** Present the
   head-to-head comparison twice: once with original weights (0.35/0.30/0.20/0.15),
   once with revised weights (Config A/B/C). If state-aware wins under revised scoring
   but loses under original, the reader sees both and draws their own conclusions.

2. **Re-run the retrospective enrichment under both regimes.** The 10x enrichment
   (EF@10 = 4.95/7.72) was computed under original scoring. Compute it under revised
   scoring. If the enrichment improves, state-aware design benefits from better scoring.
   If it degrades, that is informative too. Report both.

3. **Run weight sensitivity analysis under revised scoring.** Repeat the 100 random
   Dirichlet weight configurations, now sampling over 6 components instead of 4. Report
   the fraction favoring state-aware under the expanded configuration space. The
   prediction: with ADMET and selectivity added, >60% of configurations favor state-aware
   (because state-aware candidates targeting DFG-out states should score higher on both
   ADMET and selectivity).

4. **Component-ablation analysis.** Run the comparison with each of the 6 components
   individually zeroed out. This shows the marginal contribution of each component to
   the static vs state-aware outcome. If zeroing reference similarity flips the result,
   that demonstrates the scoring function -- not the pipeline -- determines the winner.

5. **Let the data speak.** If revised scoring does not change the enrichment result,
   that itself is informative: it means the enrichment advantage is robust to scoring
   function design, which strengthens the publication claim.

### Technical Details

**Architecture compatibility:** StateBind's `ranking/scoring.py` already supports
arbitrary weight configurations via `DEFAULT_WEIGHTS` (a dict that must sum to 1.0).
Adding new components requires: (a) defining a new scoring function for each component,
(b) adding the component name to `DEFAULT_WEIGHTS`, (c) updating the `UnifiedScoreComponent`
enum in `ranking/models.py`, and (d) updating all downstream consumers. The architecture
was designed for this extensibility.

**GNINA cross-docking:** The GNINA wrapper in `chemistry/docking.py` already handles
receptor preparation and docking execution. Extending to off-target kinases requires
preparing 5 new PDBQT receptor files and box coordinates. The docking protocol
(exhaustiveness, scoring function, output parsing) is identical to EGFR docking.

**ADMET model integration:** The existing model in `ml/admet.py` returns continuous
predictions for 6 endpoints. Currently used only for post-hoc annotation. Integration
into scoring requires: (a) defining sigmoid transforms for each endpoint, (b) computing
a composite score, (c) adding this as a scoring component. No model retraining needed.

**Data dependencies:** All data needed (PDB structures for off-target kinases, ADMET
model checkpoints, docking infrastructure) is either already available in StateBind or
freely downloadable from PDB/RCSB.

---

## Impact Assessment

### Publication Impact

- **Target venue:** JCIM (primary) / Nature Computational Science (aspirational)

- **Main claim this enables:** "Conventional known-drug-similarity scoring systematically
  penalizes the chemical exploration that generative models are designed to enable. Under
  pharmacologically-principled scoring that includes ADMET safety and kinase selectivity,
  conformational state-aware design demonstrates both higher retrospective enrichment
  and improved predicted selectivity profiles."

- **Secondary claim:** "Conformational state-aware design inherently generates molecules
  with higher kinase selectivity, consistent with the known selectivity advantage of
  type II (DFG-out) binding (Gini 0.76 vs 0.58)."

- **Reviewer concerns this addresses:**
  - Concern #2 ("Why only 3 reference molecules for 35% of score?"): Weight reduced to
    10%, limitation acknowledged, alternative metrics tested.
  - Concern #3 from drug discovery practitioners ("No ADMET in scoring"): Now a scoring
    component with kinase-calibrated thresholds.
  - Concern #5 from practitioners ("No selectivity"): Cross-docking selectivity proxy
    added.
  - Implicit concern ("The scoring function was designed to make state-aware win"):
    Dual reporting under both original and revised scoring eliminates this.

- **The scoring revision AS a publishable insight:** The observation that QED penalizes
  48% of approved kinase inhibitors (Roskoski 2026), that Tanimoto misses 60% of
  bioactive pairs (Chen et al. 2025), and that the scoring function design -- not the
  pipeline design -- determines which approach appears superior is itself a methodological
  contribution. This could be a standalone figure or supplementary analysis: "Figure S3:
  Impact of scoring function design on head-to-head comparison outcomes."

### Effort Estimate

- **Compute:**
  - Selectivity cross-docking: 2,455 runs x ~5 min/run = ~200 GPU-hours. Feasible in
    1 day on 1 Bouchet gpu_h200 node (8 GPUs) or 2-3 days on scavenge_gpu.
  - ADMET scoring: Minutes (existing model, batch inference on 491 SMILES).
  - Weight sensitivity re-analysis: Hours on CPU (Monte Carlo sampling).
  - Retrospective re-run: Hours on GPU (re-scoring with new weights).

- **Data:**
  - Off-target kinase PDB structures: 5 files from RCSB (free, minutes to download).
  - ADMET model checkpoint: Already exists in StateBind.
  - ADMETlab 3.0 API (optional): Free, no registration.
  - Approved kinase inhibitor property data: Published in Roskoski reviews.

- **Implementation:** 2-3 weeks total.
  - Week 1: Reference similarity weight change, kinase desirability functions, ADMET
    sigmoid transforms and composite score. Re-run comparison.
  - Week 2: GNINA cross-docking for selectivity. Prepare 5 off-target receptors,
    submit docking jobs, parse results, compute selectivity scores.
  - Week 3: Dual reporting, weight sensitivity, retrospective re-run, ablation analysis.

- **Dependencies:**
  - GNINA binary and GPU access (already available).
  - PDB structures for off-target kinases (freely available).
  - No new model training required.

### Risk Assessment

- **Technical risks:**
  - GNINA cross-docking scores for off-target kinases may not be well-calibrated. Docking
    score magnitudes differ across targets due to pocket size and scoring artifacts.
    *Mitigation:* Normalize per-target scores using a set of known binders/non-binders for
    each off-target kinase (available from ChEMBL).
  - ADMETlab 3.0 API may have rate limits or availability issues.
    *Mitigation:* Fall back to StateBind's existing 6-endpoint ADMET model. The proposal
    is designed to work with either.

- **Scientific risks:**
  - Revised scoring may NOT change the enrichment result. If the 10x enrichment holds
    under both original and revised scoring, that is scientifically GOOD (robustness) but
    reduces the narrative impact of the scoring revision.
    *Mitigation:* Frame as robustness evidence. "The enrichment advantage persists across
    scoring function designs, from similarity-focused to MPO-focused."
  - Revised scoring may cause state-aware to win on mean score, inviting accusations of
    p-hacking the scoring function.
    *Mitigation:* Dual reporting is mandatory. Present both results. Let the weight
    sensitivity analysis (hundreds of configurations) speak to robustness.
  - DFG-out candidates may NOT show higher selectivity than active-state candidates.
    *Mitigation:* Report the result regardless. If the selectivity advantage does not
    materialize in silico, discuss whether the docking proxy has sufficient resolution to
    detect it. The literature evidence (Gini 0.76 vs 0.58) sets expectations, but docking
    is not kinase selectivity profiling.

- **Scope risk:**
  - Full selectivity cross-docking is compute-intensive. If Bouchet GPU queues are
    congested, the selectivity component may delay the timeline.
    *Mitigation:* Use scavenge_gpu partition for cost-free preemptable jobs. Alternatively,
    use MPNN-predicted affinities for off-target kinases as a faster proxy (retrain MPNN
    on ABL/SRC/BRAF ChEMBL data, or use the existing EGFR MPNN as a cross-target proxy
    with the understanding that this is approximate).

---

## Evaluation Criteria

1. **Kinase inhibitor property calibration:** >80% of 94 FDA-approved kinase inhibitors
   should score > 0.5 on the revised drug-likeness component (vs ~50% on QED). If the
   revised function penalizes approved drugs, it is miscalibrated.

2. **Dual reporting completeness:** All 9 existing comparison metrics (overlap, diversity,
   score distributions, top-K dominance, novelty, statistical testing, weight sensitivity,
   Pareto, retrospective) must be reported under BOTH original and revised scoring.

3. **Retrospective enrichment under revised scoring:** EF@10 should remain > 1.0 for
   state-aware (demonstrating the pipeline adds value regardless of scoring design). The
   absolute EF@10 may change; the direction (state-aware > static) is the key test.

4. **Selectivity signal:** Mean selectivity score for DFG-out-targeting candidates should
   be significantly higher than for DFGin/aCin candidates (one-sided Mann-Whitney U,
   p < 0.05), consistent with the Gini 0.76 vs 0.58 literature finding.

5. **Weight sensitivity improvement:** Under revised 6-component scoring, >55% of random
   Dirichlet configurations should favor state-aware (up from 44% under original scoring),
   demonstrating that the revised function is more robust.

6. **Component ablation insight:** Zeroing reference similarity should shift the comparison
   toward state-aware by at least 0.05 in mean score delta, confirming that reference
   similarity is the dominant confound.

---

## Open Questions

1. **How to normalize cross-docking scores across different kinase targets?** GNINA
   scores are target-dependent (different pocket sizes, different score distributions).
   Options: per-target z-score normalization using known binder/non-binder distributions,
   or per-target sigmoid calibration. This requires small reference datasets for each
   off-target kinase (100-200 compounds from ChEMBL, easily obtainable).

2. **Should the ADMET composite include ADMETlab 3.0 predictions in addition to or
   instead of StateBind's internal model?** The internal model provides consistency
   (same model for all candidates) but lower accuracy (hERG AUROC 0.7745 vs ADMETlab's
   0.72-0.99 range). Using external predictions introduces a dependency but provides
   broader endpoint coverage (119 vs 6 endpoints).

3. **What is the correct hERG calibration center -- 1.0 uM or 0.5 uM?** The sigmoid
   center determines where the hERG score transitions from "acceptable" to "concerning."
   Centering at 1.0 uM is conservative (osimertinib at 0.57 uM would score ~0.27).
   Centering at 0.5 uM is permissive (osimertinib would score ~0.50). The choice depends
   on whether we calibrate to "acceptable for oncology" (0.5 uM) or "preferred for new
   drugs" (1.0 uM). Both options should be tested.

4. **Should the erlotinib reference molecule be replaced?** Given that erlotinib is not
   conformationally selective (Park et al. 2012), should it be replaced with a
   state-specific reference such as lapatinib (inactive-state binder) or afatinib
   (covalent, active-state)? This changes the reference set's meaning from "known EGFR
   drugs" to "state-representative EGFR drugs."

5. **How to handle the dual-reporting framing editorially?** Presenting all results
   twice (original + revised scoring) could confuse readers or feel like hedging.
   Recommendation: present revised scoring as the primary analysis with original scoring
   in supplementary materials, with explicit justification for why the revision better
   reflects drug design practice.

---

## References

1. Chen Y, et al. (2025). Beyond Tanimoto: a learned bioactivity similarity index
   enhances ligand discovery. *Frontiers in Bioinformatics*, 5:1695353.
   DOI: 10.3389/fbinf.2025.1695353

2. Ung PMU, Rahman R, Schlessinger A. (2015). Redefining the protein kinase
   conformational space with machine learning. *Cell Chemical Biology / J Med Chem*.
   PMC4326797. -- Type II selectivity Gini 0.76 vs 0.58.

3. Roskoski R. (2026). Properties of FDA-approved small molecule protein kinase
   inhibitors: A 2026 update. *Pharmacological Research*. -- 94 approved KIs, 48% Ro5
   violations.

4. Roskoski R. (2025). Properties of FDA-approved small molecule protein kinase
   inhibitors: A 2025 update. *Pharmacological Research*. -- 85 approved, 46% Ro5
   violations.

5. Roskoski R. (2024). Properties of FDA-approved small molecule protein kinase
   inhibitors: A 2024 update. *Pharmacological Research*, 200:107059. -- 80 approved
   KIs.

6. Zhong Y, et al. (2023). Acute osimertinib exposure induces electrocardiac changes
   by synchronously inhibiting the currents of cardiac ion channels. *Frontiers in
   Pharmacology*, 14:1177003. DOI: 10.3389/fphar.2023.1177003 -- hERG IC50 2.21 uM
   (HEK293), 0.57 uM (IWQ).

7. Wang Z, et al. (2021). Mechanisms of gefitinib-induced QT prolongation. *European
   Journal of Pharmacology*, 910:174467. -- Gefitinib hERG IC50 1.91 uM.

8. Park JH, et al. (2012). Erlotinib binds both active and inactive conformations of
   EGFR kinase. -- Erlotinib non-selectivity for conformational states.

9. Zhao Z, et al. (2014). Exploration of type II binding mode: A privileged approach
   for kinase inhibitor focused drug discovery? *ACS Chemical Biology*, 9(6):1230-1241.
   PMC4068218. -- Type II selectivity argument, structural basis.

10. Loeffler H, et al. (2024). Reinvent 4: Modern AI-driven generative molecule
    design. *Journal of Cheminformatics*, 16:20. DOI: 10.1186/s13321-024-00812-5 --
    Multi-component ADMET-integrated scoring.

11. Mourdou N, et al. (2026). ADMETrix: ADMET-Driven De Novo Molecular Generation.
    *ICANN 2025 Workshop*. ChemRxiv. DOI: 10.26434/chemrxiv-2025-3x5nq-v3 -- hERG
    AUROC 0.836 in generative loop.

12. Fu L, et al. (2024). ADMETlab 3.0: an updated comprehensive online ADMET prediction
    platform. *Nucleic Acids Research*, 52(W1):W422-W431. DOI: 10.1093/nar/gkae236 --
    119 endpoints, free API.

13. Lombardo F, et al. (2024). Application of mechanistic multiparameter optimization
    and large-scale in vitro to in vivo pharmacokinetics correlations. -- Mechanistic PK
    MPO AUCROC >0.95.

14. Bickerton GR, et al. (2012). Quantifying the chemical beauty of drugs. *Nature
    Chemistry*, 4:90-98. PMC3524573. -- QED definition (osimertinib scores 0.31).

15. Redfern WS, et al. (2003). Relationships between preclinical cardiac
    electrophysiology, clinical QT interval prolongation and torsade de pointes.
    *Cardiovascular Research*, 58:32-45. -- 30-fold hERG safety margin guideline.

16. PMMG: Pareto MCTS Molecular Generation. (2025). *Advanced Science*. -- 51.65%
    multi-objective success with simultaneous binding/ADMET/synthesizability optimization.

17. Sato T, Honma T. (2010). Combining machine learning and pharmacophore-based
    interaction fingerprints for in silico screening. *JCIM*, 50(1):170-185. --
    Pharm-IF EF@10 5.7 vs GLIDE 4.2.

18. Zangl PA, et al. (2021). Cardiac safety of osimertinib: a review. *Journal of
    Clinical Oncology*, 39(suppl). PMC8078322. -- LVEF 3.1-5.5%, risk ratio 2.62 for
    QT prolongation.

19. Thakkar A, et al. (2024). AiZynthFinder 4.0. *Journal of Cheminformatics*, 16:56.
    DOI: 10.1186/s13321-024-00860-x -- RAscore proxy for synthesis feasibility.

20. Activity cliff-aware reinforcement learning for de novo drug design. (2025).
    *Journal of Cheminformatics*, 17. PMC12013064. -- ACRL framework addressing
    Tanimoto limitations.

21. Dunn TB, et al. (2023). Exploring activity landscapes with extended similarity.
    *Molecular Informatics*, 42(6):e2300056. -- Alternatives to Tanimoto.

22. DrugMetric. (2024). *Briefings in Bioinformatics*. -- Drug-likeness based on
    chemical space distance, outperforms QED.

23. Abdulkarim MA, et al. (2023). Machine learning-based approach to developing potent
    EGFR inhibitors. *ACS Omega*, 8(26):23790-23801. -- 9,019 EGFR compounds, scaffold
    distribution.
