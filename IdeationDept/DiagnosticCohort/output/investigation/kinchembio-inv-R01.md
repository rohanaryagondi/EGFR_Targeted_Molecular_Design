---
agent: Kinase Chemical Biology Expert
round: 1
date: 2026-04-14
type: research-note
---

# H2 Investigation: State-Specific Chemical Structure in EGFR Training Data

## Executive Summary

After extensive analysis of the StateBind codebase, training data pipeline, published
literature on EGFR conformational pharmacology, and cross-kinase comparisons, I assess
**H2 (insufficient state-specific structure in training data) as the primary root cause
of the G2 NO_GO result, with probability 0.75-0.85.**

The evidence is overwhelming and comes from multiple independent lines:

1. **The state labels are predominantly random.** The `prepare_vae_data.py` script
   assigns states to ChEMBL API molecules by calling `_assign_state_from_type("")`
   with an empty string, which triggers `rng.choice(_VALID_STATES)` -- uniform random
   assignment across 3 (or 4) states. The training data confirms this: the 8,109
   molecules distribute as DFGin_aCin=2017 (24.9%), DFGin_aCout=1993 (24.6%),
   DFGout_aCin=1985 (24.5%), DFGout_aCout=2114 (26.1%) -- almost perfectly uniform,
   which is the signature of random assignment with a seeded RNG.

2. **EGFR inhibitor chemical space is dominated by a single conformational type.**
   Over 90% of known EGFR inhibitors are type I (DFGin/aCin binders). All 14
   globally approved EGFR TKIs bind the DFGin conformation. Zero approved EGFR
   inhibitors are type II (DFGout). The chemical space is overwhelmingly
   4-anilinoquinazoline-based, and these scaffolds bind both active and inactive
   conformations indiscriminately.

3. **No conditioning mechanism can learn from noise.** If 75% of state labels are
   random, the conditional mutual information I(molecule; state) is near zero. The
   model correctly learns to ignore state labels -- this is the expected behavior
   of a well-trained model on noisy labels, not a failure of the architecture.

---

## 1. How Molecules Were Assigned to States

### 1.1 The Data Pipeline (Code Analysis)

The state assignment logic lives in `scripts/prepare_vae_data.py`. The pipeline has
a 3-tier fallback for data sourcing:

1. **Tier 1: Local ChEMBL file** (`data/raw/ligands/chembl_egfr.json`)
2. **Tier 2: ChEMBL REST API** (CHEMBL203, pchembl >= 5)
3. **Tier 3: Curated fallback** (~55 hand-annotated compounds)

The metadata file (`data/processed/egfr_smiles_metadata.json`) confirms the data
came from Tier 2 (`"source": "chembl_api"`) with n_train=8109, n_val=2027.

**The critical code path for Tier 2 (ChEMBL API):**

```python
def _fetch_chembl_api() -> list[dict[str, str]] | None:
    ...
    for act in all_activities:
        smiles = act.get("canonical_smiles", "")
        ...
        state = _assign_state_from_type("", rng)  # EMPTY STRING
        records.append({"smiles": smiles, "state": state})
```

The ChEMBL API does not return `inhibitor_type` for activity records, so an empty
string is always passed. The assignment function then falls through to random:

```python
def _assign_state_from_type(inhibitor_type: str, rng: random.Random) -> str:
    type_map = {"type_i": "DFGin_aCin", "type-ii": "DFGout_aCin", ...}
    key = inhibitor_type.strip().lower()
    if key in type_map:
        return type_map[key]
    # Unknown type -> random assignment (documented limitation)
    return rng.choice(_VALID_STATES)
```

### 1.2 Empirical Confirmation: State Distribution Is Uniform

The training data state distribution:

| State | Count | Percentage |
|-------|-------|-----------|
| DFGin_aCin | 2,017 | 24.9% |
| DFGin_aCout | 1,993 | 24.6% |
| DFGout_aCin | 1,985 | 24.5% |
| DFGout_aCout | 2,114 | 26.1% |
| **Total** | **8,109** | **100.0%** |

A uniform distribution across 4 categories with n=8109 and seed=42 produces exactly
this pattern. The expected count per state would be 2027.25 with standard deviation
~39. The observed values (1985-2114) are within 2 sigma of uniform random assignment.

**Note:** The VAE training configuration (`configs/transformer_vae.yaml`) uses only
3 states (DFGin_aCin=0, DFGin_aCout=1, DFGout_aCin=2), but the training data
contains 4 states. The `SMILESDataset` class silently skips molecules with
"DFGout_aCout" labels (logged as warnings). This means approximately 2,114 molecules
(26%) are silently dropped during VAE training. The effective training set is
~6,000 molecules, not 8,109 -- and even these 6,000 have random state labels.

### 1.3 The ~55 Curated Compounds

Only Tier 3 (the curated fallback, ~55 compounds) has meaningful state assignments.
These include:
- 13 type I compounds assigned DFGin_aCin (erlotinib, gefitinib, icotinib, etc.)
- 10 type I.5 compounds assigned DFGin_aCout (lapatinib and analogs)
- 10 type II analogs assigned DFGout_aCin (sorafenib-like)
- 6 covalent compounds assigned DFGin_aCin
- Allosteric compounds assigned DFGout_aCin

But since the ChEMBL API returned ~10,000 compounds, the curated 55 are merged
with them -- representing only 0.5% of the dataset. Their correct labels are
drowned out by the randomly labeled majority.

### 1.4 Critical Assessment

**The state labels in the training data are noise.** They carry essentially zero
information about the actual conformational binding preference of each molecule.
This is not a subtle problem -- it is a fundamental data quality failure. The VAE
model was asked to learn a mapping from state labels to molecular structures, but
the labels are independent of the structures.

A model that learns to IGNORE random labels is behaving correctly. The centroid
distances of 0.26-0.42 in latent space likely reflect the trace amount of signal
from the 55 curated compounds, not learned state-structure relationships.

---

## 2. The EGFR Inhibitor Landscape: Why States Don't Produce Distinct Chemotypes

### 2.1 EGFR Is Dominated by Type I Inhibitors

The EGFR inhibitor landscape is one of the most heavily studied in oncology, and it
is overwhelmingly dominated by type I inhibitors that bind the active (DFGin/aCin)
conformation:

**Approved EGFR TKIs (all bind DFGin conformation):**

| Drug | Generation | Mechanism | Conformation | Year |
|------|-----------|-----------|-------------|------|
| Gefitinib | 1st | Reversible | DFGin/aCin | 2003 |
| Erlotinib | 1st | Reversible | DFGin/aCin | 2004 |
| Lapatinib | 1st | Reversible | DFGin/aCout | 2007 |
| Icotinib | 1st | Reversible | DFGin/aCin | 2011 |
| Afatinib | 2nd | Covalent | DFGin/aCin | 2013 |
| Neratinib | 2nd | Covalent | DFGin/aCin | 2017 |
| Osimertinib | 3rd | Covalent | DFGin/aCin | 2015 |
| Dacomitinib | 2nd | Covalent | DFGin/aCin | 2018 |
| Almonertinib | 3rd | Covalent | DFGin/aCin | 2020 |

(Yosaatmadja et al., J Biol Chem 2015; Dungo & Keating, Drugs 2013; PMC8587155)

**Zero** approved EGFR inhibitors are type II (DFGout). This is not an accident --
EGFR strongly prefers the active conformation, and the DFGout state is
thermodynamically disfavored for wild-type EGFR.

### 2.2 Why Are Type II EGFR Inhibitors Rare?

Several structural and thermodynamic factors explain why EGFR DFGout inhibitors
essentially do not exist:

1. **EGFR's conformational preference for DFGin.** MD simulations show that
   wild-type EGFR strongly favors the DFGin conformation. The DFG flip to DFGout
   requires protonation of Asp831, which only occurs at low local pH (Shan et al.,
   PNAS 2013). The free energy of the DFGout state is comparable but the kinetic
   barrier is substantial.

2. **No wild-type EGFR DFGout crystal structure exists.** The StateBind project
   itself acknowledges this: the DFGout_aCin representative is PDB 3W2R, which
   is a T790M/L858R double mutant -- not wild type. The `structures.py` source
   code explicitly states: "No wild-type EGFR DFGout structures exist in PDB."

3. **Small allosteric pocket.** When type II inhibitors bind DFGout conformations,
   they require a pocket formed by the flipped Phe of the DFG motif. In EGFR, this
   pocket is smaller than in kinases like ABL, making type II binding sterically
   unfavorable (Zhao et al., ACS Chem Biol 2014).

4. **Erlotinib binds BOTH active and inactive conformations.** Park et al.
   (Biochem J 2012, PDB 4HJO) demonstrated that erlotinib binds the inactive
   EGFR conformation with similar affinity (Glide score -9.72 kcal/mol) as
   the active conformation (-9.34 kcal/mol). This means that even type I
   inhibitors are not conformationally selective for EGFR -- they bind whatever
   conformation is present.

### 2.3 The 4-Anilinoquinazoline Problem

The overwhelming majority of EGFR inhibitors share the 4-anilinoquinazoline
scaffold or closely related heterocyclic cores:

- **Quinazoline-based (7 approved):** gefitinib, erlotinib, lapatinib, icotinib,
  afatinib, dacomitinib, vandetanib
- **Pyrrolopyrimidine-based (3 approved):** osimertinib, almonertinib, lazertinib
- **Pyridine-based:** neratinib

All of these scaffolds bind the ATP-site hinge region via a conserved hydrogen bond
to Met793 (EGFR numbering). The hinge-binding motif is the same regardless of
conformational state. The back-pocket extending groups (which would distinguish
type I from type II) are rare in EGFR inhibitor chemical space.

This means that scaffold analysis of the 8,109 training molecules would show
massive overlap -- the same quinazoline, pyrimidine, and pyrrolopyrimidine
scaffolds appearing in all states (since states were randomly assigned).

### 2.4 Lapatinib as the Exception That Proves the Rule

Lapatinib is the ONLY approved EGFR inhibitor that preferentially binds an
inactive conformation (DFGin/aCout, type I.5). Its selectivity comes from a
bulky 3-fluorobenzyloxy substituent that extends into the space opened by
the displaced aC-helix. This gives it:
- Ki = 3 nM for EGFR
- Slow off-rate (t1/2 ~ 300 min)
- Selectivity for inactive conformation

(Wood et al., Cancer Res 2004; Qiu et al., J Biol Chem 2009)

But lapatinib represents ~1 compound in a sea of >8,000. Even if perfectly
labeled, the DFGin_aCout state would contain mostly randomly assigned type I
compounds plus lapatinib and a handful of analogs.

---

## 3. Quantifying the Problem: Expected Signal Strength

### 3.1 What Fraction of EGFR Inhibitors Are Genuinely State-Specific?

Based on published literature and database analysis:

| Binding Mode | EGFR Coverage | Estimated % of ChEMBL EGFR |
|-------------|---------------|---------------------------|
| Type I (DFGin/aCin) | Dominant | ~85-90% |
| Type I.5 (DFGin/aCout) | Lapatinib class | ~5-10% |
| Type II (DFGout/aCin) | Essentially none | <1% |
| Covalent (DFGin) | 3rd-gen | ~5% |
| Allosteric | Experimental | <1% |

(Zhao et al., ACS Chem Biol 2014; Roskoski, Pharmacol Res 2019; PMC8838133)

For the ~10,000 EGFR compounds in ChEMBL (CHEMBL203, pchembl >= 5), the vast
majority are type I binders tested against wild-type EGFR in the active conformation.
ChEMBL bioactivity records do not include inhibitor type annotations for the vast
majority of entries. A 2024 study (PMC11647682) curating ChEMBL EGFR data found
35,310 bioactivity records corresponding to 11,634 unique compounds, with 4,884
classified as active (IC50 <= 1 uM). Inhibitor type information was not part of
the curation.

### 3.2 The State Classifier Experiment

If the state labels carry real chemical information, a simple classifier should
be able to predict state from molecular structure. I propose the following
diagnostic experiment:

**Experiment: State Classifier from Morgan Fingerprints**

1. Compute Morgan fingerprints (radius=2, 2048 bits) for all 8,109 training molecules
2. Train a Random Forest classifier to predict state from fingerprint
3. Evaluate with 5-fold cross-validation
4. Compare accuracy to chance baseline (33% for 3 states, 25% for 4 states)

**Expected outcome:** Classification accuracy will be at or near chance level
(~25% for 4 states, ~33% for 3 states), confirming that state labels carry no
chemical information.

**Supporting evidence from literature:** Published work on kinase inhibitor binding
mode classification shows that Random Forests with ECFP4 fingerprints achieve
balanced accuracy of 0.78-0.97 when classifying real type I vs type II inhibitors
(Rodriguéz-Pérez & Bajorath, J Cheminform 2020). Morgan fingerprints achieve
mean AUC of 0.751 for kinase profiling prediction (Wu et al., J Cheminform 2023).
If the state labels were real, we would expect similar performance. Accuracy at
chance level would definitively confirm that labels are noise.

**Effort estimate:** 2 hours of compute on a single CPU node. This should be the
FIRST experiment run before any architectural changes.

### 3.3 Mutual Information Analysis

A more formal diagnostic: compute I(X; Y) where X is the molecular fingerprint
and Y is the state label. For randomly assigned labels, I(X; Y) should be
approximately zero (within estimation error). For genuinely informative labels
(as in ABL1 type I vs type II), I(X; Y) should be substantially positive.

---

## 4. Cross-Kinase Comparison: Where State Labels Would Work

### 4.1 ABL1: The Positive Control

ABL1 (BCR-ABL) is the paradigmatic example of a kinase with genuinely distinct
conformational-state-specific inhibitor chemotypes:

**Type I (DFGin) inhibitors:**
- Dasatinib (2-aminothiazole scaffold, IC50 ~0.6 nM)
- Bosutinib (quinoline scaffold)
- Bind both active and inactive conformations
- Characterized by compact structures occupying the ATP site

**Type II (DFGout) inhibitors:**
- Imatinib (2-phenylaminopyrimidine scaffold, IC50 ~25 nM)
- Nilotinib (optimized imatinib scaffold)
- Ponatinib (multi-kinase, extended scaffold)
- Require the DFG-out allosteric pocket
- Characterized by extended structures with urea/amide linkers

(Manley et al., Biochim Biophys Acta 2005; Nagar et al., Cancer Res 2002;
Tokarski et al., Cancer Res 2006)

**Chemical space separation in ABL1:**

The dasatinib scaffold (2-aminothiazole-5-carboxamide) is structurally
distinct from the imatinib scaffold (2-phenylaminopyrimidine) at the Tanimoto
level. A Morgan fingerprint comparison between dasatinib and imatinib would
yield a Tanimoto similarity well below 0.3. This structural difference is
directly linked to the different conformational requirements.

In the PDB, ABL1 has extensive structural coverage:
- DFGin structures: PDB 2GQG (dasatinib), many others
- DFGin/aCout: PDB 2G1T (Src-like inactive, apo)
- DFGout structures: PDB 1IEP (imatinib), 3CS9 (nilotinib), 3PYY (DPH)

The StateBind atlas for ABL1 (in `structure/atlas.py`) already includes these
structures. ABL1 would provide a genuine test of the state-conditioning thesis
because:

1. The DFGin vs DFGout chemical space is genuinely separated
2. Multiple PDB structures exist for each state
3. ChEMBL has ~5,000 ABL1 bioactivity records
4. Inhibitor type annotations are more available (imatinib resistance is
   extensively characterized)

### 4.2 BRAF: Another Potential Positive Control

BRAF presents an interesting case with clear conformational selectivity:

- **Type I.5 (DFGin/aCout):** Vemurafenib, dabrafenib, encorafenib bind
  the monomeric BRAFV600E-specific conformation with aC-helix displaced
- **Type II (DFGout):** BI 882370, LY3009120 bind the DFGout conformation
  and are pan-RAF inhibitors

(Hatzivassiliou et al., Nature 2010; Karoulia et al., Nat Rev Cancer 2017;
Peng et al., Mol Cancer Ther 2015)

The BRAF V600E mutation shifts the conformational equilibrium, creating a
genuine conformational niche that selective inhibitors exploit. The chemical
distinction between type I.5 (7-azaindole core, sulfonamide) and type II
(urea-based, extended scaffolds) inhibitors is substantial.

### 4.3 Quantitative Comparison: EGFR vs ABL vs BRAF

| Feature | EGFR | ABL1 | BRAF |
|---------|------|------|------|
| DFGout structures in PDB | 1 (mutant only) | 3+ (WT and mutant) | Multiple |
| Approved type II drugs | 0 | 3 (imatinib, nilotinib, ponatinib) | 1+ |
| Type I vs II scaffold distinction | Minimal | Large | Moderate |
| ChEMBL compounds (pchembl >= 5) | ~10,000 | ~5,000 | ~3,000 |
| Expected classifier accuracy | ~33% (chance) | ~70-85% | ~60-75% |
| State label informativeness | Near zero | High | Moderate |

---

## 5. Comments on H1 (Architecture) and H3 (Evaluation)

### 5.1 H1: Architecture Is a Secondary Concern

The prefix-token conditioning mechanism (8 tokens projected from [z; state_onehot])
is architecturally adequate for conveying 3 bits of information (3 states). Published
work on conditional VAEs shows that even simple concatenation conditioning can
effectively control generation when the conditioning signal is informative
(Lim et al., J Cheminform 2018).

The weak centroid separation (0.26-0.42) is not evidence of a weak mechanism.
It is evidence that the mechanism correctly learned the amount of signal present
in the labels -- approximately zero. A stronger conditioning mechanism (cross-
attention, adversarial state prediction) would also fail on random labels; it
would just fail differently (by overfitting to the noise or learning spurious
correlations).

**That said,** if the data labels are fixed, it would be worth testing a stronger
mechanism as a secondary experiment. The architecture should not be changed before
the data problem is addressed.

### 5.2 H3: Evaluation Metric Is a Compounding Factor

The evaluation design (H3) is a legitimate concern but secondary to H2:

1. **The docking_proxy uses a fixed 1M17 (DFGin/aCin) pocket.** This means even
   if a conditioned model generated molecules optimized for DFGin/aCout or DFGout
   pockets, they would not be rewarded in the scoring function.

2. **state_specificity is zeroed.** The 15% weight on state_specificity was set
   to 0 for "fairness," which removes the only component that could directly
   measure state-specific behavior.

3. **reference_similarity (35% weight) compares to erlotinib/gefitinib/osimertinib.**
   These are all type I (DFGin/aCin) inhibitors. A molecule optimized for DFGout
   binding (e.g., a type II urea-based scaffold) would score LOW on reference
   similarity because it would look nothing like erlotinib.

The evaluation design systematically penalizes any molecule that deviates from
type I EGFR inhibitor chemical space. This compounds the data problem: even if
H2 were fixed and the model learned to generate genuinely state-specific molecules,
the current evaluation would still show no benefit.

However, H3 is moot if H2 is not fixed first. You cannot evaluate state-specific
generation if the model never learned state-specific patterns.

---

## 6. What Should the Project Do Next?

### 6.1 Immediate Diagnostic (1-2 days)

**Run the state classifier experiment.** This is the cheapest possible diagnostic
and will definitively confirm or refute H2.

```
1. Load egfr_smiles_train.json (8,109 molecules)
2. Compute Morgan fingerprints (radius=2, 2048 bits) via RDKit
3. Map state labels to integers (3 or 4 classes)
4. Train RandomForestClassifier(n_estimators=500)
5. 5-fold cross-validation
6. Report accuracy, balanced accuracy, per-class F1
7. Compare to chance baseline
```

**Expected result:** Accuracy ~25-33% (chance), confirming labels are noise.

**If accuracy is significantly above chance (>45%):** This would partially refute
H2 and suggest the ChEMBL data has some latent type information (e.g., from the
55 curated compounds leaking into the random labels). Further investigation of
which compounds drive the signal would be warranted.

### 6.2 Data Fix (1-2 weeks)

If the classifier confirms random labels (expected), the project has two paths:

**Path A: Proper EGFR state annotation**

1. Use KLIFS database to annotate compounds by binding mode. KLIFS provides
   automated DFG conformation assignment with >99% accuracy (Kooistra et al.,
   Nucleic Acids Res 2016). For ~500 EGFR co-crystal structures, KLIFS provides
   conformation labels for the protein. Cross-referencing the bound ligands to
   ChEMBL would provide ~500 properly annotated molecules.

2. Use inhibitor type prediction models. Published ML models achieve MCC 0.67-0.95
   for predicting kinase inhibitor binding mode from molecular structure alone
   (Rodriguéz-Pérez & Bajorath, J Cheminform 2020; Volkamer et al., Sci Rep 2021).
   Train on KLIFS-annotated data, predict on ChEMBL compounds.

3. Use pharmacological knowledge. Literature curation of type I vs type I.5
   vs type II binding for the ~100 best-characterized EGFR inhibitors would
   provide a gold-standard validation set.

**Problem with Path A:** Even with perfect annotation, EGFR will show ~90% type I,
~8% type I.5, ~2% type II/allosteric. The class imbalance is extreme, and the
chemical space overlap between type I and type I.5 is substantial (same quinazoline
cores, differing only in back-pocket extensions). A conditional VAE would likely
still struggle to learn meaningful state-specific generation.

**Path B: Switch to ABL1 as primary kinase (recommended)**

1. Use ABL1 (CHEMBL1862) as the primary test kinase for the state-conditioning
   thesis. ABL1 has genuine DFGin vs DFGout chemotype separation.

2. Annotate ABL1 compounds using KLIFS + KinCoRe (Dunbrack lab) databases.
   KinCoRe provides automated conformational classification with 8 DFG subtypes
   (Modi & Bhatt, Nucleic Acids Res 2022).

3. Cross-reference PDB ABL1 structures with ChEMBL bioactivity to create
   properly annotated training data with ~5,000 compounds.

4. Run the state classifier to confirm signal (expected accuracy 70-85% for
   type I vs type II).

5. Train the conditional Transformer VAE on properly labeled ABL1 data.

6. Re-run Ablation C with ABL1 data.

**If ABL1 shows a positive signal:** This validates the state-conditioning thesis
(just not for EGFR) and opens a strong publication story about when state-
conditioning works and when it doesn't.

**If ABL1 also shows null:** This would suggest the conditioning mechanism (H1)
is indeed too weak, independent of data quality.

### 6.3 Evaluation Fix (1 week, can be parallel)

Regardless of the data fix, update the evaluation:

1. **Multi-pocket docking:** Dock against 3 pocket conformers (1M17 DFGin/aCin,
   2GS7 DFGin/aCout, 3W2R DFGout/aCin) using GNINA. Score each molecule
   against its target state's pocket.

2. **State-specific reference compounds:** Replace the fixed reference set
   (erlotinib, gefitinib, osimertinib -- all type I) with state-specific
   reference sets. For DFGin/aCout, use lapatinib-like compounds. For DFGout,
   use type II scaffolds.

3. **Re-enable state_specificity scoring** with proper state-aware evaluation.

### 6.4 Decision Tree

```
Day 1-2: Run state classifier on current data
  |
  +--> Accuracy ~25-33% (expected): Labels are noise. H2 confirmed.
  |     |
  |     +--> Week 1-2: Prepare ABL1 dataset with proper annotations
  |     |     |
  |     |     +--> Run state classifier on ABL1 data
  |     |           |
  |     |           +--> Accuracy >60%: ABL1 has real signal. Proceed.
  |     |           |     |
  |     |           |     +--> Week 3-4: Train conditional VAE on ABL1
  |     |           |     |
  |     |           |     +--> Week 5: Re-run Ablation C with ABL1
  |     |           |           |
  |     |           |           +--> GO: State conditioning works for ABL1.
  |     |           |           |    Publication: "State conditioning works
  |     |           |           |    when states are chemically distinct."
  |     |           |           |
  |     |           |           +--> NO_GO: Architecture problem (H1).
  |     |           |                Test stronger conditioning mechanism.
  |     |           |
  |     |           +--> Accuracy <45%: ABL1 also lacks signal.
  |     |                 The problem is deeper. Consider negative-result paper.
  |     |
  |     +--> Parallel: Fix EGFR annotation via KLIFS/KinCoRe
  |     |
  |     +--> Parallel: Fix evaluation (multi-pocket docking)
  |
  +--> Accuracy >45%: Unexpected. Some signal exists.
        |
        +--> Investigate which molecules drive the signal.
        +--> The 55 curated compounds may be leaking in.
        +--> Proceed more cautiously with architecture investigation.
```

---

## 7. Probability Assessment of Root Causes

| Hypothesis | Probability | Evidence |
|-----------|------------|---------|
| **H2: Data labels are noise** | **0.75-0.85** | Random assignment confirmed in code; uniform distribution in data; EGFR lacks type II inhibitors; same scaffolds dominate all states |
| H3: Wrong evaluation metric | 0.50-0.60 | Fixed pocket (1M17) cannot detect multi-state benefit; reference compounds are all type I; state_specificity zeroed. BUT this is compounding, not root cause. |
| H1: Weak conditioning | 0.10-0.20 | Prefix-token mechanism is adequate for 3 bits of information; weak centroids reflect weak signal, not weak mechanism. Would need to be tested AFTER fixing H2. |

**These probabilities are not independent.** H2 is almost certainly the primary
cause. H3 would compound the problem even if H2 were fixed. H1 is unlikely to
be the bottleneck but cannot be ruled out until H2 is addressed.

---

## 8. The Broader Scientific Lesson

This investigation reveals a general trap in conditional molecular generation:
**if the conditioning labels do not reflect genuine structure-activity relationships,
a well-trained model will correctly learn to ignore them.**

The field of conditional molecular generation has mostly demonstrated conditioning
on continuous properties (logP, QED, molecular weight) that are computable from
structure and therefore carry perfect label quality. Conditioning on categorical
labels (conformational state, selectivity profile, binding mode) requires that
these labels be assigned through experimental evidence or validated computational
prediction, not random assignment.

For kinase conformational state conditioning specifically, the approach can only
work for kinases where:
1. Multiple conformational states are structurally characterized
2. Distinct chemotype populations exist for each state
3. Enough annotated compounds exist per state for training
4. The chemical space difference between states is large enough to learn

EGFR fails criteria 2 and 3 decisively. ABL1 meets all four criteria. This
kinase-dependent feasibility assessment should have been performed before
training the conditional model.

---

## References

1. Zhao Z, Wu H, Wang L, et al. "Exploration of Type II Binding Mode: A Privileged
   Approach for Kinase Inhibitor Focused Drug Discovery?" ACS Chem Biol. 2014;
   9(6):1230-1241. doi:10.1021/cb500129t

2. Zuccotto F, Ardini E, Casale E, Angiolini M. "Through the 'gatekeeper door':
   exploiting the active kinase conformation." J Med Chem. 2010;53(7):2681-2694.

3. Shan Y, Arkhipov A, Kim ET, et al. "Transitions to catalytically inactive
   conformations in EGFR kinase." PNAS. 2013;110(18):7270-7275.

4. Park JH, Liu Y, Lemmon MA, Bhatt RN. "Erlotinib binds both inactive and active
   conformations of the EGFR tyrosine kinase domain." Biochem J. 2012;448(3):417-423.
   PDB: 4HJO.

5. Kooistra AJ, Kanev GK, van Linden OPJ, et al. "KLIFS: a structural kinase-
   ligand interaction database." Nucleic Acids Res. 2016;44(D1):D365-D371.

6. Modi V, Dunbrack RL Jr. "Kincore: a web resource for structural classification
   of protein kinases and their inhibitors." Nucleic Acids Res. 2022;50(D1):D654-D664.

7. Rodriguéz-Pérez R, Bajorath J. "Assessing the information content of structural
   and protein-ligand interaction representations for the classification of kinase
   inhibitor binding modes via machine learning and active learning." J Cheminform.
   2020;12(1):36.

8. Volkamer A, Eid S, Turk S, et al. "Prediction of kinase inhibitors binding modes
   with machine learning and reduced descriptor sets." Sci Rep. 2021;11(1):706.

9. Nagar B, Bornmann WG, Pellicena P, et al. "Crystal structures of the kinase
   domain of c-Abl in complex with the small molecule inhibitors PD173955 and
   imatinib (STI-571)." Cancer Res. 2002;62(15):4236-4243.

10. Tokarski JS, Newitt JA, Chang CYJ, et al. "The structure of dasatinib (BMS-
    354825) bound to activated ABL kinase domain elucidates its inhibitory activity
    against imatinib-resistant ABL mutants." Cancer Res. 2006;66(11):5790-5797.

11. Wood ER, Truesdale AT, McDonald OB, et al. "A unique structure for EGFR
    kinase defines a mechanism for type I inhibitor selectivity." Cancer Res.
    2004;64:6652-6659.

12. Roskoski R Jr. "Properties of FDA-approved small molecule protein kinase
    inhibitors: A 2024 update." Pharmacol Res. 2024;200:107059.

13. Lim J, Ryu S, Park K, et al. "Molecular generative model based on conditional
    variational autoencoder for de novo molecular design." J Cheminform. 2018;10(1):31.

14. Wu Z, Zhu M, Kang Y, et al. "Large-scale comparison of machine learning methods
    for profiling prediction of kinase inhibitors." J Cheminform. 2023;15(1):105.

15. Hatzivassiliou G, Song K, Yen I, et al. "RAF inhibitors prime wild-type RAF to
    activate the MAPK pathway and enhance growth." Nature. 2010;464:431-435.

16. Karoulia Z, Gavathiotis E, Poulikakos PI. "New perspectives for targeting RAF
    kinase in human cancer." Nat Rev Cancer. 2017;17:676-691.

17. Peng SB, Henry JR, Kaufman MD, et al. "A Novel RAF Kinase Inhibitor with
    DFG-Out-Binding Mode: High Efficacy in BRAF-Mutant Tumor Xenograft Models."
    Mol Cancer Ther. 2015;14(3):354-363.

18. Manley PW, Cowan-Jacob SW, Mestan J. "Advances in the structural biology,
    design and clinical development of Bcr-Abl kinase inhibitors for the treatment
    of chronic myeloid leukaemia." Biochim Biophys Acta. 2005;1754(1-2):3-13.

19. Qiu C, Tarrant MK, Choi SH, et al. "Mechanism of activation and inhibition of
    the HER4/ErbB4 kinase." Structure. 2008;16(3):460-467.

20. Yosaatmadja Y, Silva S, Rosber JA, et al. "Binding mode of the breakthrough
    inhibitor AZD9291 to EGFR revealed." J Struct Biol. 2015;192(3):539-544.

21. Peng X, Wen Y, Liang S, et al. "Atom-level generative foundation model for
    molecular interaction with pockets." Cell. 2026; PocketXMol.

22. Dungo RT, Keating GM. "Afatinib: first global approval." Drugs. 2013;73(13):
    1503-1515.

23. Smaill JB, Rewcastle GW, Loo JA, et al. "Tyrosine kinase inhibitors. 17.
    Irreversible inhibitors of the epidermal growth factor receptor." J Med Chem.
    2000;43(7):1380-1397.

24. Abdeldayem A, Raouf YS, Constantinescu SN, et al. "The Ins and Outs of Bcr-Abl
    Inhibition." Genes Cancer. 2012;3(5-6):423-434.

25. Minami Y, Shimamura T, Shah K, et al. "The major lung cancer-derived mutants of
    ERBB2 are oncogenic and are associated with sensitivity to the irreversible EGFR/
    ERBB2 inhibitor HKI-272." Oncogene. 2007;26(34):5023-5027.

---

## Appendix A: The Metadata Smoking Gun

The metadata file at `data/processed/egfr_smiles_metadata.json` explicitly documents
the problem:

```json
{
  "source": "chembl_api",
  "notes": "State assignments use inhibitor-type heuristics. Compounds without
            known type are assigned randomly. Data source: chembl_api."
}
```

"Compounds without known type are assigned randomly" -- this is the root cause
documented in plain text. Since the ChEMBL API does not return inhibitor type
for activity records, ALL compounds from the API path are assigned randomly.

## Appendix B: The DFGout_aCout Ghost State

The training data contains a 4th state "DFGout_aCout" that does not exist in the
VAE configuration. The `transformer_vae.yaml` config maps only 3 states:

```yaml
state_mapping:
  DFGin_aCin: 0
  DFGin_aCout: 1
  DFGout_aCin: 2
```

The `SMILESDataset` class silently skips molecules whose state label is not in the
state_mapping. This means ~2,114 molecules (26% of the dataset) labeled "DFGout_aCout"
are dropped during training. The effective training set is ~6,000 molecules with
random 3-state labels, further reducing the already-nonexistent signal.

## Appendix C: Proposed State Classifier Script

```python
"""Diagnostic: Can a classifier predict conformational state from molecule?

If accuracy ~ chance (33%), state labels are noise.
If accuracy >> chance, state labels carry chemical information.

This should be the FIRST experiment before any VAE changes.
"""
import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import balanced_accuracy_score, classification_report

# 1. Load data
with open("data/processed/egfr_smiles_train.json") as f:
    data = json.load(f)

# 2. Morgan fingerprints
from rdkit import Chem
from rdkit.Chem import AllChem

fps, labels = [], []
state_map = {"DFGin_aCin": 0, "DFGin_aCout": 1, "DFGout_aCin": 2}
for rec in data:
    if rec["state"] not in state_map:
        continue  # skip DFGout_aCout
    mol = Chem.MolFromSmiles(rec["smiles"])
    if mol is None:
        continue
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
    fps.append(np.array(fp))
    labels.append(state_map[rec["state"]])

X = np.array(fps)
y = np.array(labels)

# 3. Cross-validate
clf = RandomForestClassifier(n_estimators=500, random_state=42, n_jobs=-1)
scores = cross_val_score(clf, X, y, cv=5, scoring="balanced_accuracy")

print(f"Balanced accuracy: {scores.mean():.3f} +/- {scores.std():.3f}")
print(f"Chance baseline: {1.0/len(set(y)):.3f}")

# 4. Full report
clf.fit(X, y)
from sklearn.model_selection import cross_val_predict
y_pred = cross_val_predict(clf, X, y, cv=5)
print(classification_report(y, y_pred, target_names=list(state_map.keys())))
```
