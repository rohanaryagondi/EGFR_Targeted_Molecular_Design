---
agent: Kinase Chemical Biology Expert
round: 2
date: 2026-04-14
type: proposal
---

# Round 2 Proposal: Fixing the Data Problem and Salvaging the Thesis

## Updated Hypothesis Probabilities

| Hypothesis | R1 Estimate | R2 Estimate | Rationale |
|------------|------------|------------|-----------|
| H2: Random labels | 75-85% | **80-85%** | Confirmed by code, distribution, and cross-agent corroboration |
| H1: Weak conditioning | 15-25% | **10-15%** | Real but irrelevant until labels fixed; see condgen response |
| H3: Wrong evaluation | 15-25% | **15-20%** | Real flaws, but moot under random labels; see evaldes response |

The Round 1 synthesis strengthened my assessment. mldebug independently corroborated
the random-label finding from metadata. condgen's own analysis shows prefix tokens
carry ~0.2 bits/token -- but with random labels, even 100 bits/token would carry no
signal. H2 is the root cause; everything else is downstream.

---

## Top 3 Actions (Ranked by Expected Value)

### Action 1: KLIFS/KinCoRe Cross-Reference to Properly Annotate EGFR Compounds

**Priority: HIGHEST. Do this first.**

**Problem.** The 8,109 EGFR molecules in the training set have random state labels
assigned by `rng.choice()`. The ChEMBL API returns no inhibitor type information.
We need a reliable method to assign conformational binding mode labels to these
molecules.

**Approach: Structure-based annotation via KLIFS.**

KLIFS (Kooistra et al., NAR 2016, updated weekly) contains 242 human EGFR structures,
all with ligands bound, each annotated with DFG conformation and aC-helix position:

| Conformation | EGFR Structures in KLIFS |
|-------------|-------------------------|
| DFGin / aCin | 162 |
| DFGin / aCout | 80 |
| DFGout | 2 (PDB 5HG7, 5HG5) |
| **Total** | **242** |

KLIFS provides SMILES for each co-crystallized ligand with its conformational state
annotation. The annotation pipeline would be:

1. **Extract KLIFS EGFR ligands with state labels** via the KLIFS API
   (`/api/structures_list?kinase_ID=406`). This yields ~242 structure-ligand pairs
   with gold-standard DFG/aC annotations. After deduplication by InChIKey, expect
   ~120-150 unique ligand chemotypes.

2. **Map KLIFS ligands to ChEMBL training compounds.** For each KLIFS ligand, compute
   ECFP4 Tanimoto similarity against all 8,109 training molecules. Assign the KLIFS
   conformational label to any training molecule with Tanimoto >= 0.7 to the KLIFS
   ligand (a threshold validated by Rodriguez-Perez & Bajorath, J Cheminform 2020,
   who showed balanced accuracy of 0.78-0.97 for binding mode classification using
   ECFP4). Molecules below this threshold remain "unknown."

3. **Augment with KinCoRe annotations.** KinCoRe (Dunbrack lab, NAR 2022) classifies
   kinase structures into 8 DFG sub-states and provides explicit inhibitor type labels
   (Type I, I.5, II, III, allosteric). Cross-reference KinCoRe's EGFR entries with
   KLIFS for consensus labels. KinCoRe reported 7,177 human kinase chains as of 2021;
   EGFR coverage includes many of the same PDB entries but with finer-grained
   classification.

4. **ML-based label propagation for remaining compounds.** For training molecules
   that cannot be matched to any KLIFS/KinCoRe ligand (expected majority), train a
   Random Forest classifier on the KLIFS-annotated subset using Morgan fingerprints
   (radius=2, 2048 bits). Rodriguez-Perez & Bajorath (J Med Chem 2019) demonstrated
   that such models achieve balanced accuracy of 0.78-0.97 on kinase inhibitor binding
   mode classification. Apply this classifier to propagate labels to the remaining
   compounds, retaining a confidence score.

**Expected outcome for EGFR.** This is where I must be honest: the annotation will
likely produce a severely imbalanced dataset.

| Expected State | Estimated % | Reasoning |
|---------------|------------|-----------|
| DFGin_aCin (Type I) | 85-92% | All 14 approved EGFR TKIs bind DFGin; 162/242 KLIFS structures |
| DFGin_aCout (Type I.5) | 5-10% | Lapatinib class; 80/242 KLIFS structures but many are same ligand |
| DFGout_aCin (Type II) | <2% | Only 2 KLIFS structures; no approved type II EGFR inhibitor exists |

This imbalance is a biological reality, not a data curation failure. EGFR strongly
prefers the DFGin conformation (Shan et al., PNAS 2013). No wild-type EGFR DFGout
crystal structure exists (the 3W2R representative is a T790M/L858R double mutant).

**Effort:** 2-3 days scripting + 4-8 CPU-hours for fingerprint computation and
similarity mapping. No GPU needed for this step.

**SLURM spec:** 1 CPU job, 4 cores, 8 GB RAM, `day` partition, ~4 hours.

**Decision gate after annotation:** If the properly annotated dataset has <5% of
molecules in any non-DFGin_aCin state, EGFR cannot support meaningful state
conditioning with the current chemical space. Proceed to Action 3 (ABL1).

---

### Action 2: Diagnostic Battery to Confirm Labels Are Noise (Run in Parallel with Action 1)

**Priority: HIGH. Run immediately, costs almost nothing.**

This is a convergence of my Round 1 recommendation with mldebug's diagnostic battery.
The cheapest confirmations should happen before any expensive retraining.

**2a. State classifier on training data (my R1 proposal, 2 CPU-hours).**

Train a Random Forest on Morgan fingerprints (radius=2, 2048 bits) to predict state
from molecular structure in the current training data.

- **Expected result with random labels:** Accuracy ~25% (4 states) or ~33% (3 states),
  confirming labels carry zero chemical information.
- **Comparison benchmark:** Rodriguez-Perez & Bajorath (J Cheminform 2020) achieved
  balanced accuracy 0.78-0.97 on genuine Type I vs Type II classification across
  1,425 Type I, 394 Type I.5, and 190 Type II inhibitors with X-ray-confirmed
  binding modes. If our classifier hits chance level, the case is closed.

**2b. Scaffold overlap between states (mldebug's proposal, 30 min CPU).**

Compute Bemis-Murcko scaffolds for all training molecules. Calculate Jaccard overlap
between states. If Jaccard > 0.7, the same scaffolds appear in all states -- another
confirmation of random assignment.

**2c. condgen's positive control: MW-tercile conditioning (2-3 GPU-hours).**

This is the single most informative experiment for the architecture question. Assign
molecules to terciles by molecular weight (MW < 350, 350-450, > 450). Train the same
Transformer VAE with prefix-token conditioning on MW labels instead of state labels.

- **If MW conditioning works (generates correct MW range): H2 confirmed.**
  The architecture can condition on informative labels; state labels are the problem.
- **If MW conditioning fails: H1 also confirmed.** Architecture needs fixing too.

This experiment costs 2-3 GPU-hours and answers the most important outstanding
question: is the architecture fundamentally broken (H1), or is it just receiving
noise (H2)?

**SLURM specs:**
- 2a + 2b: 1 CPU job, 4 cores, 8 GB, `day`, ~3 hours
- 2c: 1 GPU job, `gpu_devel`, 1x H200, 4 cores, 16 GB, ~3 hours

**Total for diagnostic battery: <1 day, <5 GPU-hours.**

---

### Action 3: ABL1 Data Curation as Positive Control Kinase

**Priority: MEDIUM-HIGH. Start after EGFR annotation reveals class imbalance.**

If EGFR annotation (Action 1) confirms that >90% of compounds are Type I binders,
the thesis cannot be tested on EGFR alone. ABL1 is the optimal alternative because
it has genuine conformational-state-specific chemotypes that are structurally distinct.

**Why ABL1 is the ideal positive control.**

KLIFS data for ABL1 (kinase_ID=392) shows a dramatically different conformational
landscape than EGFR:

| Metric | EGFR | ABL1 |
|--------|------|------|
| Total KLIFS structures | 242 | 309 |
| DFGin structures | 240 (99%) | 75 (24%) |
| DFGout structures | 2 (0.8%) | 115 (37%) |
| DFGout-like structures | 0 | 119 (39%) |
| Structures with ligands | 242 (100%) | 268 (87%) |

ABL1 has a near-even DFGin/DFGout split. The chemical space is genuinely separated:
- **Type I (DFGin):** Dasatinib (2-aminothiazole), bosutinib (quinoline). Compact,
  ATP-competitive.
- **Type II (DFGout):** Imatinib (2-phenylaminopyrimidine), nilotinib (optimized
  imatinib), ponatinib. Extended scaffolds with urea/amide linkers reaching the
  allosteric pocket behind the DFG motif.

Dasatinib vs imatinib have Morgan FP Tanimoto similarity well below 0.3 -- they are
structurally distinct chemotypes that a VAE should be able to distinguish.

**Concrete ABL1 curation plan.**

1. **Query ChEMBL for ABL1 compounds.** Target: CHEMBL1862 (Homo sapiens ABL1).
   Filter: pchembl_value >= 5 (IC50 <= 10 uM), confidence_score >= 8. Based on
   published estimates (Miljkovic et al., J Cheminform 2020 reported >2,000 kinase
   inhibitors with binding mode annotations across all kinases; ABL1 is among the
   most studied), expect 3,000-6,000 unique compounds.

2. **Annotate binding modes via KLIFS cross-reference.** Use the same pipeline as
   Action 1: extract KLIFS ABL1 ligands (268 with ligands, ~100-150 unique after
   deduplication), compute Tanimoto against ChEMBL compounds, propagate labels.
   ABL1 annotation quality will be far superior to EGFR because:
   - 115 DFGout structures provide diverse type II ligand templates
   - Imatinib resistance is extensively characterized with structural data
   - KinCoRe explicitly classifies ABL1 inhibitor types

3. **Validate annotations.** Use known drug binding modes as ground truth:
   - Imatinib: must be Type II (DFGout) -- PDB 1IEP
   - Nilotinib: must be Type II (DFGout) -- PDB 3CS9
   - Dasatinib: must be Type I (DFGin) -- PDB 2GQG
   - Bosutinib: must be Type I (DFGin) -- PDB 3UE4
   - Ponatinib: must be Type II (DFGout) -- PDB 3OXZ
   - Asciminib: must be Type III (allosteric) -- PDB 5MO4

4. **Quality control.** Run the same Random Forest classifier diagnostic (Action 2a)
   on the annotated ABL1 data. Expected accuracy with real labels: >0.75 (given
   published benchmarks). If accuracy is near chance, something is wrong with the
   annotation.

5. **Prepare training data.** Format as the existing VAE expects:
   `[{"smiles": "...", "state": "DFGin_aCin"}, ...]`

**Expected class distribution for ABL1:**

| State | Estimated % | Reasoning |
|-------|------------|-----------|
| DFGin (Type I) | 40-55% | Dasatinib-like, bosutinib-like compounds |
| DFGout (Type II) | 30-40% | Imatinib-like, nilotinib-like, ponatinib-like |
| Allosteric (Type III) | 5-10% | Asciminib class, GNF-2/5 series |
| Unknown/ambiguous | 10-20% | Cannot confidently assign |

This distribution would provide a genuine test of the state-conditioning thesis.
A 40/35/15/10 split is far more balanced than EGFR's expected 90/7/2/1.

**Effort:** 1-2 weeks (data curation: 3-4 days; annotation pipeline: 2-3 days;
validation and QC: 2-3 days). Reuses much of the Action 1 annotation code.

**SLURM specs:** CPU-only for curation. 1 GPU job for retraining VAE on ABL1 data
(same architecture, new data): `gpu_devel`, 1x H200, ~6 hours.

**Decision gate:** If the ABL1-trained VAE with real state labels shows Cohen's
d > 0.3 on multi-pocket evaluation, the thesis is rescued for a different kinase.
If d remains ~0, the thesis is dead (or requires architectural fixes per condgen).

---

## Responses to Other Agents

### Response to condgen: MW-Tercile Positive Control

**I strongly support this experiment.** It is the single cheapest way to disentangle
H1 from H2. MW terciles provide clean, unambiguous labels that the model must be able
to learn if the architecture works at all. Expected MW separation between terciles is
large (~100-150 Da), and the molecular features that determine MW (atom count,
ring count, chain length) are directly encoded in SMILES.

However, I want to add a nuance: **even if MW conditioning works, it does not
guarantee that conformational state conditioning will work with real labels.** MW
is a global molecular property directly encoded in every SMILES token. Conformational
binding preference is an emergent property of 3D shape, electrostatics, and
protein-ligand complementarity -- it is NOT directly encoded in SMILES. A model
can learn MW from SMILES because MW is a trivial function of the string. It cannot
learn binding mode from SMILES as easily because binding mode requires 3D reasoning
that a sequence model does not natively perform.

So the MW control proves the architecture is not broken. It does NOT prove the
architecture is sufficient for the much harder task of conformational conditioning.
If MW works but state conditioning does not (with real labels), we learn that
conformational labels require a stronger conditioning mechanism or 3D-aware
representations -- which connects back to condgen's FiLM/adaLN proposals.

**Recommendation:** Run MW positive control immediately (Action 2c). Regardless of
outcome, also run condgen's conditioning strength ladder when testing real state
labels.

### Response to evaldes: Multi-Pocket Docking Timing

**Do NOT run multi-pocket docking on the current random-label models.**

evaldes proposes 20,400 GNINA runs (6,800 molecules x 3 pockets, 4-8 GPU-hours) to
test whether H3 explains the null result. While the protocol design is sound, running
it on current models is wasteful:

1. The current models were trained on random labels. They never learned
   state-specific generation. Running docking on 3 pockets will produce 3 sets of
   essentially identical scores because the molecules were not generated with any
   state awareness.

2. The experiment cannot distinguish "H3 is the problem" from "the model never
   learned state-specific generation because of H2." You would observe no pocket-
   preference signal, but you would not know whether this is because:
   - (a) The model generates state-agnostic molecules (H2 caused this), or
   - (b) The evaluation is blind even to state-specific molecules (H3)

3. Multi-pocket docking becomes informative AFTER retraining with real labels. If a
   model trained on properly annotated data (Action 1 or Action 3) generates
   molecules that dock better to their target pocket than to other pockets, the
   thesis is supported. This is the correct time to run evaldes's protocol.

**Exception:** A small 100-molecule pilot (as evaldes proposes, 300 runs, ~3-4 hours)
could establish a baseline for pocket preference in RANDOMLY generated molecules. This
would tell us the expected null distribution, against which we later compare properly
conditioned molecules. This is useful and cheap enough to run now.

**Recommendation:** Run 100-molecule pilot now as a null baseline. Save the full
20,400-run evaluation for after retraining with proper labels.

### Response to mldebug: Diagnostic Priorities

mldebug's 7-experiment battery is well-designed, but given that we now have strong
evidence for H2, some experiments are more informative than others:

**Still highly informative (run these):**
- Scaffold overlap (Exp 5): Confirms H2 cheaply. CPU-only, 30 min.
- Probing classifier on z (Exp 1): Tells us whether the model learned any
  state structure at all. If accuracy >33%, some signal leaked through despite
  random labels (possibly from the 55 curated compounds).

**Informative only after real labels (defer these):**
- Prefix token attention analysis (Exp 3): Only meaningful if labels carry signal.
- State-swap experiment (Exp 4): Only meaningful if model learned state-specific
  generation.
- Per-dimension KL analysis (Exp 6): Only meaningful with informative labels.

**Run the diagnostic battery in two phases:** cheap confirmations now (Exps 1, 5, 7),
then re-run the full battery after retraining with proper labels (all 7 experiments).

---

## Is EGFR Salvageable?

This is the hardest question, and I owe the team an honest answer.

**Partially, but not as originally conceived.**

The original thesis tests 4 conformational states (DFGin_aCin, DFGin_aCout,
DFGout_aCin, DFGout_aCout). For EGFR:

- **DFGin_aCin vs DFGin_aCout** is testable. KLIFS shows 162 vs 80 structures in
  these two states. Lapatinib (aCout) is structurally distinct from erlotinib
  (aCin) due to its bulky 3-fluorobenzyloxy group that exploits the displaced
  aC-helix. With proper annotation, a 2-class conditioning task (active vs
  inactive aC-helix) may show a signal.

- **DFGout states** are not testable for EGFR. Only 2 KLIFS structures, no approved
  type II inhibitors, no wild-type DFGout crystal structure. The chemical space
  is empty.

**Minimum class balance requirement.** For conditional generation to learn
meaningfully different distributions, published work suggests the minority class
needs at least 10-15% of the training data. Rodriguez-Perez & Bajorath (J Cheminform
2020) showed that active learning reached near-maximal classifier performance with
~25% of available training data; for generative models, the requirement is likely
higher because the model must learn a distribution, not just a boundary.

With proper EGFR annotation, the DFGin_aCout class might reach 5-10% of the dataset.
This is marginal but potentially viable with oversampling or weighted training. The
DFGout class at <2% is not viable.

**My recommendation:** Test EGFR as a 2-class problem (aCin vs aCout) with proper
labels. If this shows signal (d > 0.2), it partially rescues the thesis for EGFR.
Simultaneously develop ABL1 (Action 3) as the stronger test case. The publication
becomes: "State conditioning works when states correspond to chemically distinct
populations (ABL1), but not when chemical space is homogeneous (EGFR) -- and we show
how to diagnose this before training."

---

## Timeline

| Week | Action | Deliverable | Decision Gate |
|------|--------|-------------|---------------|
| 1 (Days 1-3) | Diagnostic battery (2a, 2b, 2c) | Classifier accuracy, scaffold overlap, MW control | If classifier ~25%: H2 confirmed |
| 1 (Days 1-5) | EGFR KLIFS annotation (Action 1) | Annotated EGFR dataset with state labels | If <5% non-aCin: EGFR 4-state dead |
| 2 (Days 6-10) | ABL1 ChEMBL curation (Action 3, steps 1-2) | ABL1 compound set with KLIFS annotations | If <1000 annotatable: reconsider |
| 2-3 (Days 8-14) | ABL1 annotation QC + VAE training data prep | Validated ABL1 training set | If classifier >75%: labels good |
| 3 (Days 12-16) | Retrain VAE on properly labeled EGFR (2-class) | Trained model + diagnostics | If d > 0.2: EGFR partially rescued |
| 3-4 (Days 14-20) | Retrain VAE on ABL1 data | Trained model + diagnostics | If d > 0.3: thesis rescued |
| 4 (Days 18-22) | Multi-pocket docking on retrained models | evaldes's full 20,400-run protocol | Final assessment of thesis |
| 5 (Days 22-28) | Analysis + manuscript outline | Recovery report or negative-result paper | Publication strategy decision |

**Total estimated time: 4-5 weeks.**
**Total GPU-hours: ~20-30 (training + docking).**
**Total CPU-hours: ~20-40 (annotation + fingerprints).**

---

## References

1. Kooistra AJ, et al. KLIFS: a structural kinase-ligand interaction database. *Nucleic Acids Research*. 2016;44(D1):D365-D371.
2. Kanev GK, et al. KLIFS: an overhaul after the first 5 years of supporting kinase research. *Nucleic Acids Research*. 2021;49(D1):D562-D569.
3. Modi V, Dunbrack RL. Kincore: a web resource for structural classification of protein kinases and their inhibitors. *Nucleic Acids Research*. 2022;50(D1):D654-D664.
4. Rodriguez-Perez R, Bajorath J. Assessing the information content of structural and protein-ligand interaction representations for the classification of kinase inhibitor binding modes. *J Cheminformatics*. 2020;12:36.
5. Miljkovic F, Rodriguez-Perez R, Bajorath J. Machine learning models for accurate prediction of kinase inhibitors with different binding modes. *J Med Chem*. 2020;63(16):8738-8748.
6. Shan Y, et al. How does a drug molecule find its target binding site? *JACS*. 2011;133(24):9181-9183.
7. Wood ER, et al. A unique structure for epidermal growth factor receptor bound to GW572016 (lapatinib). *Cancer Res*. 2004;64(18):6652-6659.
8. Roskoski R. Properties of FDA-approved small molecule protein kinase inhibitors. *Pharmacol Res*. 2019;144:68-86.
9. Peebles W, Xie S. Scalable diffusion models with transformers. *ICCV*. 2023.
10. Reveguk ZV, et al. Classifying protein kinase conformations with machine learning. *Protein Sci*. 2024;33(3):e4918.
11. Xerxa E, Miljkovic F, Bajorath J. Data sets of human and mouse protein kinase inhibitors with curated activity data including covalent inhibitors. *Future Sci OA*. 2023;9(9):FSO088.
12. Zhao Z, et al. Exploration of type II binding mode: a privileged approach for kinase inhibitor focused drug discovery? *ACS Chem Biol*. 2014;9(6):1230-1241.
