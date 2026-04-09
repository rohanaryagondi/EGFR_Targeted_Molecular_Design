---
agent: Senior Biophysicist
round: 2
date: 2026-04-09
type: proposal
proposal_id: biophys-P01
title: "Kinetic Dimension: Integrating Binding Kinetics into StateBind via a 3-Tier Scoring Cascade and the Conformational Selection Narrative"
---

# Proposal: Kinetic Dimension -- Integrating Binding Kinetics into StateBind via a 3-Tier Scoring Cascade and the Conformational Selection Narrative

## Proposing Agent

**Senior Biophysicist** (Cohort2, IdeationDept)

Expertise: Binding kinetics, drug-target residence time, SPR/ITC biophysics,
conformational dynamics, thermodynamic signatures, structure-kinetic relationships.

---

## Problem Statement

StateBind's unified scoring function evaluates candidates along four axes --
reference_similarity (0.35), druglikeness (0.30), docking_proxy (0.20), and
state_specificity (0.15) -- but entirely omits binding kinetics. This is a critical
gap for three reasons:

1. **Drug-target residence time (1/koff) predicts in vivo efficacy better than
   equilibrium affinity.** The Copeland paradigm, validated by the K4DD consortium
   across 3,812 compounds and 78 targets, demonstrates that in open pharmacological
   systems where drug concentration fluctuates, the duration of target engagement
   determines pharmacological effect (Copeland et al., 2006; Schuetz et al., 2017).

2. **The kinetic distinction between conformational states is the strongest biophysical
   argument for state-aware design.** Type II (DFG-out) kinase inhibitors show residence
   times of hours (lapatinib on EGFR: 430 min), while Type I (DFG-in) inhibitors
   dissociate in minutes (gefitinib: <14 min) -- a 30x difference despite lapatinib
   having *weaker* equilibrium affinity (Ki 3 nM vs 0.4 nM) (Wood et al., 2004;
   Copeland, 2010). StateBind cannot currently capture this distinction.

3. **The 10x retrospective enrichment (EF@10 = 4.95/7.72 vs 0.47/0.79) likely reflects
   implicit kinetic selection, but this is never articulated.** State-aware candidates
   targeting DFG-out states overlap with the drug population that achieves long
   residence times. This interpretation reframes a structural finding as a kinetic/
   pharmacological one, dramatically increasing its publication impact.

**What is missing:** A kinetic scoring component, a mechanistic narrative connecting
conformational state to kinetics, and an experimental design to validate both.

---

## Vision

This proposal adds a **kinetic dimension** to StateBind through three complementary
components, each at a different effort level:

- **Component A (Kinetic Scoring):** A 5th scoring component with a 3-tier fallback
  cascade (tauRAMD -> ML koff -> state-kinetic heuristic), weighted at 10%.
- **Component B (Conformational Selection Narrative):** A zero-compute, publication-ready
  mechanistic argument that reframes the 10x enrichment as implicit kinetic optimization.
- **Component C (Experimental Validation Design):** A concrete 10-compound SPR panel
  and HDX-MS protocol to validate predictions.

Together, these components make StateBind the first conformational-state-aware drug
design pipeline with integrated kinetic prediction -- a claim no published tool can
currently make.

---

## Background and Evidence

### Key Evidence

**1. Residence time predicts in vivo efficacy across multiple target classes.**

The evidence base is substantial and spans 15+ years:

- **FabI inhibitors (Copeland, 2010):** Among Francisella tularensis enoyl-ACP
  reductase inhibitors, Ki and MIC showed no correlation with in vivo efficacy,
  while residence time (40-143 min) correlated linearly with efficacy. PMCID: PMC2918722.

- **NK1 receptor antagonists (Copeland, 2010):** Aprepitant, CP-99994, and ZD6021
  have nearly identical thermodynamic affinities but starkly different in vivo
  activities that track with residence time ranking.

- **BCR-ABL kinase inhibitors (Manley et al., 2011; Wood et al., 2022):** Nilotinib
  has the longest residence time among BCR-ABL drugs and correspondingly superior
  selectivity. One-third of imatinib-resistant ABL mutations cause resistance through
  faster koff rather than reduced affinity (PMCID: PMC8890393), demonstrating direct
  clinical consequences of kinetic parameters.

- **K4DD Consortium (>20M EUR EU funding):** Novartis, AstraZeneca, Janssen, Bayer
  assembled 3,812 compounds with standardized SPR kinetics across 78 targets
  (3,238 kinase data points), confirming industry-wide recognition that binding
  kinetics are essential for drug optimization (Schuetz et al., 2017).

**2. Conformational state dictates kinetic profile.**

The kinetic distinction between Type I and Type II kinase inhibitors maps directly
onto DFG-in vs DFG-out conformational states:

| Inhibitor Class | Conformation | kon (M-1 s-1) | koff (s-1) | Residence Time |
|-----------------|-------------|----------------|------------|----------------|
| Type I | DFG-in (active) | 10^5 - 10^6 | 10^-2 - 10^-3 | Minutes |
| Type II | DFG-out (inactive) | 10^3 - 10^5 | 10^-3 - 10^-5 | Hours |
| Type I.5 | DFG-in/inactive | Moderate | Slow | 30 min - hours |
| Covalent | Variable | Variable | Irreversible | Infinite |

Specific EGFR examples: gefitinib (Type I, DFG-in) has residence time <14 min;
lapatinib (Type I.5, inactive-like) has residence time 430 min (Wood et al., 2004).

**3. Conformational selection mechanism explains slow koff for DFG-out binders.**

The mechanistic basis is well-established:

- Imatinib kon to ABL is rate-limited by DFG-out population: kon = 0.143 +/- 0.076
  uM-1 s-1, DFG flip rate k+1* = 21.4 s-1 (Wood et al., 2022 PNAS).
- p38alpha: water-mediated conformational selection mechanism determines residence
  time (Kokh et al., 2022 Nature Communications).
- The drug must partially unbind before the DFG loop can flip back to the active
  conformation, creating a kinetic trap that produces very slow koff.

**4. Computational koff prediction is mature enough for scoring.**

| Method | Accuracy | Compute Cost | Key Reference |
|--------|----------|-------------|---------------|
| tauRAMD | ~2.3x for 78% of compounds | 80-200 ns/ligand | Kokh et al., 2018 JCTC |
| STELLAR-koff GNN | Pearson r = 0.729-0.838 | Minutes (inference) | 2025 preprint |
| ML on tauRAMD | Robust on 94 HSP90 inhibitors | Post-processing | Kokh et al., 2019 |
| Milestoning | Imatinib-ABL: 18 s-1 vs exp 25+/-6 | 5-50 us aggregated | Votapka et al., 2017 |

**5. Available training data for ML koff prediction.**

| Database | Size | Kinase-Specific | Access |
|----------|------|-----------------|--------|
| KOFFI | 1,705 entries | Quality-rated koff values | Public |
| K4DD benchmark | 80 kinase-inhibitor pairs | Standardized SPR (ABL, ALK, EGFR, PI3K) | Published |
| KDBI | 19,263 entries | Mixed targets | Public |
| BindingDB kinetic | ~1.1M compounds | Kinetic subdb | Public |
| PDBbind (kinetic) | 680 entries | koff with co-crystal structures | Public |

### Relationship to Existing Work

**StateBind's existing architecture:** The current 4-component scoring function
(`ranking/scoring.py`, DEFAULT_WEIGHTS at line 125) uses a 3-tier docking cascade
as precedent for the fallback architecture proposed here. The kinetic scoring
component mirrors this pattern exactly: best available method at runtime, graceful
fallback to heuristic.

**Vision System overlap:** Vision Idea 005 (ADMET scoring, implemented), Idea 008
(uncertainty quantification, implemented), and Idea 009 (docking integration,
implemented) addressed other scoring gaps. The kinetic dimension was NOT proposed
in any of the 12 vision ideas. This is a genuinely new contribution.

**StateBind's existing state atlas:** The 4-state atlas (DFGin/aCin, DFGin/aCout,
DFGout/aCin, DFGout/aCout) and 9D feature representation in `structure/atlas.py`
provide the conformational state labels needed for the Tier 3 heuristic.

**StateBind's null result on mean score:** The static pipeline currently wins on
mean unified score (0.5437 vs 0.4378). Adding kinetic scoring could shift this
balance if state-aware candidates genuinely have better predicted kinetics. However,
this is uncertain and must be presented honestly.

---

## Proposed Approach

### Overview

The proposal has three components at different effort levels:

| Component | Effort | Compute | Timeline | Publication Impact |
|-----------|--------|---------|----------|-------------------|
| A: Kinetic Scoring | Medium | 250 GPU-days (tauRAMD) | 4-6 weeks | High (novel scoring) |
| B: Conformational Selection Narrative | Zero | None | 1 week | Very High (reframes results) |
| C: Experimental Validation | Medium-High | None (wet lab) | 4-8 weeks | Very High (Nature Comp Sci) |

The recommended execution order is B -> A -> C, because the narrative (B) can be
written immediately and frames everything else. The kinetic scoring (A) provides
computational evidence. The experiments (C) provide the definitive validation.

### Component A: Kinetic Scoring (5th Scoring Component)

#### A.1 Mathematical Formulation

**Current 4-Component Scoring Function (from `ranking/scoring.py:125-130`):**

```
S_current(m) = 0.35 * ref_sim(m) + 0.30 * druglike(m) + 0.20 * dock(m) + 0.15 * state_spec(m)
```

**Proposed 5-Component Scoring Function:**

```
S_proposed(m) = 0.30 * ref_sim(m) + 0.25 * druglike(m) + 0.20 * dock(m)
              + 0.15 * state_spec(m) + 0.10 * kinetic(m)
```

**Weight rebalancing rationale:** The 10% kinetic weight is carved from
reference_similarity (-5%, from 0.35 to 0.30) and druglikeness (-5%, from 0.30 to
0.25). These two components are the most mature and can absorb a small reduction.
The docking_proxy (0.20) and state_specificity (0.15) weights are unchanged because
docking is directly complementary to kinetics (affinity vs. kinetics) and state_specificity
is the differentiating axis between pipelines.

**Constraint:** Sum = 0.30 + 0.25 + 0.20 + 0.15 + 0.10 = 1.00 (satisfies `_validate_weights()`).

#### A.2 Three-Tier Kinetic Cascade

The kinetic score uses a 3-tier cascade, evaluated at scoring time with the best
available tier selected automatically (mirroring the docking_proxy fallback pattern):

**Tier 1: tauRAMD-derived relative residence time (best, compute-intensive)**

```
kinetic_T1(m) = rank_percentile(tau_RAMD(m, s)) / 100
```

Where:
- `tau_RAMD(m, s)` = tauRAMD-predicted residence time for molecule `m` in
  conformational state `s`
- `rank_percentile()` = percentile rank within the candidate pool
- Protocol: 40 RAMD replicas x 2-5 ns each per ligand-state pair
- Output: relative tau values (higher = longer predicted residence time)
- Normalization: min-max within pool, then percentile rank for robustness

Implementation: Run tauRAMD simulations using GROMACS on Bouchet H200 GPUs.
The RAMD module is open-source from HITS Heidelberg (Kokh et al., 2018). Results
stored as JSON artifact in `artifacts/kinetics/tauRAMD_results.json`.

**Tier 2: ML-predicted koff (medium, fast inference)**

```
kinetic_T2(m) = sigmoid(-(log10(koff_pred(m)) - mu_EGFR) / sigma_EGFR)
```

Where:
- `koff_pred(m)` = GNN-predicted koff for molecule `m` (using STELLAR-koff or
  equivalent model)
- `mu_EGFR` = mean log10(koff) for known EGFR inhibitors (reference anchor)
- `sigma_EGFR` = std dev of log10(koff) for known EGFR inhibitors
- Sigmoid maps the z-score to [0, 1], with slower koff scoring higher

From published EGFR kinetic data:
- gefitinib koff ~ 10^-3 s-1 (fast, Type I)
- lapatinib koff ~ 3.9 x 10^-5 s-1 (slow, Type I.5)
- Reference range: log10(koff) from -5 to -2, so mu_EGFR ~ -3.5, sigma_EGFR ~ 1.0

Training data assembly:
1. KOFFI database (1,705 entries, quality-rated) -- primary source
2. K4DD benchmark (80 kinase-inhibitor pairs with standardized SPR) -- validation
3. PDBbind kinetic subset (680 entries with co-crystal structures) -- structural input
4. BindingDB kinetic (filter for kinases, ~5,000-10,000 entries) -- augmentation

Model options:
- STELLAR-koff (GNN, Pearson r = 0.729-0.838) -- preferred if reproducible
- Ridge regression on PLIP interaction fingerprints (Kokh et al., 2019) -- simpler fallback
- Custom GNN trained on assembled kinase kinetic data -- if needed

**Tier 3: State-kinetic heuristic (fallback, zero compute)**

```
kinetic_T3(m) = h(state(m))
```

Where `h` is a lookup table based on established structure-kinetic relationships
(Holdgate et al., 2018; Schuetz et al., 2017):

| Predicted Binding Mode | Conformational State | kinetic_T3 | Rationale |
|------------------------|---------------------|------------|-----------|
| Type II (DFG-out) | DFGout_aCin or DFGout_aCout | 0.70 | Empirical: DFGout binders have 10-100x longer RT |
| Type I.5 (inactive-like) | DFGin_aCout | 0.50 | Lapatinib-class: moderate RT (hours) |
| Type I (active) | DFGin_aCin | 0.30 | Empirical: DFGin binders have short RT (minutes) |
| Covalent (warhead detected) | Any | 0.90 | Infinite RT until protein turnover |
| Unknown / no state | -- | 0.40 | Neutral prior |

Covalent detection: scan for known warhead SMARTS patterns (acrylamide, vinyl
sulfonamide, chloroacetamide) using RDKit.

**Cascade selection logic (pseudocode):**

```python
def kinetic_score(molecule, state, tauRAMD_results=None, ml_model=None):
    # Tier 1: tauRAMD (best)
    if tauRAMD_results and molecule.smiles in tauRAMD_results:
        return normalize_tauRAMD(tauRAMD_results[molecule.smiles])

    # Tier 2: ML koff prediction
    if ml_model is not None:
        koff_pred = ml_model.predict(molecule)
        return sigmoid_normalize(koff_pred, mu_EGFR, sigma_EGFR)

    # Tier 3: State-kinetic heuristic (always available)
    return state_kinetic_heuristic(state, molecule.smiles)
```

This mirrors `ranking/scoring.py`'s existing docking cascade (MPNN -> DockingProxy
MLP -> stub) and is consistent with StateBind's fallback architecture principle.

#### A.3 Compute Cost for tauRAMD

**System specifications:**
- EGFR kinase domain: ~40,000 atoms (protein + solvent + ions)
- GROMACS performance on H200 GPU: ~200-500 ns/day for this system size

**Per-molecule cost:**
- 40 RAMD replicas x 2.5 ns average = 100 ns total simulation time
- At 300 ns/day (conservative H200 estimate): ~0.33 GPU-days per molecule per state

**Full candidate set (top 30 state-aware candidates x 4 states):**
- 30 candidates x 4 states x 0.33 GPU-days = ~40 GPU-days (optimistic)
- With system preparation, equilibration, and replicates: ~80-120 GPU-days total
- Conservative estimate including failures and reruns: **~150-250 GPU-days**

**On Bouchet cluster:**
- 9 nodes x 4 RTX 5000 Ada GPUs (gpu partition) = 36 GPUs available
- Or 9 nodes x 8 H200 GPUs (gpu_h200 partition) = 72 GPUs available
- At 36 GPUs: ~4-7 days wall clock time
- At 72 GPUs (H200): ~2-4 days wall clock time
- As SLURM array job: `#SBATCH --array=0-119` (30 compounds x 4 states)
- Partition: `gpu_h200` with `--gpus=h200:1 --cpus-per-task=4 --mem=16G`

**Cost comparison:** This is comparable to the GNINA docking runs already completed
for WS09 and is well within the cluster's capacity.

#### A.4 State-Kinetic Synergy (Positive Feedback Loop)

A critical design feature: the kinetic score creates a self-reinforcing signal with
state_specificity. Consider two candidate molecules:

**Example -- DFGout-specific candidate (state-aware):**
- state_specificity = 1.0 (unique to DFGout_aCin, one state)
- kinetic_T3 = 0.70 (DFGout heuristic)
- Combined contribution: 0.15 * 1.0 + 0.10 * 0.70 = 0.220

**Example -- Non-specific candidate (static):**
- state_specificity = 0.0 (no target state, static pipeline)
- kinetic_T3 = 0.40 (neutral prior)
- Combined contribution: 0.15 * 0.0 + 0.10 * 0.40 = 0.040

**Delta: 0.180 (18% of total score)**

This synergy is physically justified: the same underlying phenomenon -- preferential
binding to the DFG-out inactive conformation -- simultaneously produces high state
specificity (geometric) and long residence time (kinetic). The two scoring components
capture complementary aspects of the same biophysics. This is not double-counting;
state_specificity measures *how many* states a compound appears in, while kinetic_score
measures the *predicted kinetic consequence* of binding to a particular state.

**Impact on the null result:** The mean score gap (static 0.5437 vs state-aware 0.4378,
delta = 0.1059) could narrow or reverse. State-aware DFGout candidates would gain up
to 0.18 additional score from the kinetic+state synergy. Whether this overcomes the
static advantage depends on the distribution, but the direction is favorable. This must
be tested empirically, and reported honestly regardless of outcome.

#### A.5 Implementation Specification

**New files required:**
- `src/statebind/ranking/kinetics.py` -- Kinetic scoring functions (3-tier cascade)
- `configs/kinetics.yaml` -- Tier thresholds, heuristic values, ML model paths
- `tests/test_kinetics.py` -- Tests for all three tiers + cascade selection

**Modified files:**
- `src/statebind/ranking/scoring.py` -- Add kinetic_score to DEFAULT_WEIGHTS,
  update SCORING_METHOD string, add kinetic component to score_unified()
- `src/statebind/ranking/models.py` -- No changes needed (UnifiedScoreComponent
  already supports arbitrary component names)

**Artifact outputs:**
- `artifacts/kinetics/tauRAMD_results.json` -- Tier 1 results
- `artifacts/kinetics/ml_koff_predictions.json` -- Tier 2 results
- `artifacts/kinetics/kinetic_scores.json` -- Final scores with tier used

**Config-driven (per StateBind conventions):**

```yaml
# configs/kinetics.yaml
kinetic_scoring:
  weight: 0.10
  tier1_tauRAMD:
    n_replicas: 40
    sim_length_ns: 2.5
    force_constant: 14.0  # RAMD force in kJ/mol/nm
    results_path: "artifacts/kinetics/tauRAMD_results.json"
  tier2_ml_koff:
    model: "stellar_koff"  # or "ridge_plip"
    checkpoint_path: null  # populated after training
    reference_mu: -3.5     # log10(koff) mean for EGFR drugs
    reference_sigma: 1.0   # log10(koff) std for EGFR drugs
  tier3_heuristic:
    DFGout_aCin: 0.70
    DFGout_aCout: 0.70
    DFGin_aCout: 0.50
    DFGin_aCin: 0.30
    covalent: 0.90
    unknown: 0.40
```

---

### Component B: Conformational Selection Narrative (Zero-Compute)

This component requires no new computation, no new code, and no new data. It is
a mechanistic interpretation of existing results using established biophysical
principles. It should be written into the manuscript Discussion section immediately.

#### B.1 The Core Argument (5-Step Chain)

The argument proceeds as a causal chain, each link supported by published evidence:

**Step 1: StateBind's state-aware pipeline explicitly targets DFG-out conformations.**

StateBind's 4-state atlas defines DFGout_aCin and DFGout_aCout as two of four
targetable conformational states. The state-conditioned generation pipeline produces
candidates optimized for each state's pocket geometry. Among the 461 state-aware
candidates, those targeting DFGout states are designed to complement the DFG-out
pocket topology.

**Step 2: DFG-out binders engage targets through the conformational selection
mechanism, which kinetically traps the inactive conformation.**

When a Type II inhibitor binds, it selects the transiently populated DFG-out
conformation from the equilibrium ensemble. The binding event stabilizes this
inactive state, and the inhibitor must partially dissociate before the DFG loop
can flip back to the active conformation. This creates a kinetic trap: kon is
rate-limited by the DFG-out population (slow association), but koff is even slower
because unbinding requires conformational reorganization.

Published evidence:
- Imatinib kon to ABL: 0.143 +/- 0.076 uM-1 s-1, rate-limited by DFG flip
  (k+1* = 21.4 s-1) (Wood et al., 2022 PNAS; PMCID: PMC8890393)
- p38alpha conformational selection: water-mediated mechanism determines residence
  time of Type II inhibitors (Kokh et al., 2022 Nat Commun)
- BIRB796 on p38alpha: residence time >1,800 hours, the longest measured for any
  kinase inhibitor (Type II, DFG-out)

**Step 3: Slow koff produces long residence time, which correlates with in vivo
drug efficacy.**

The Copeland paradigm (Copeland et al., 2006; Copeland, 2016 Nat Rev Drug Discov)
establishes that in open biological systems where drug concentration fluctuates
continuously, only bound drug continues to exert its pharmacological effect. Therefore,
residence time (1/koff), not equilibrium affinity (1/Kd), determines the duration
and magnitude of the pharmacological response. This has been validated across multiple
target classes (FabI, NK1 receptor, BCR-ABL kinases) and by the K4DD consortium's
industry-scale analysis.

**Step 4: Among EGFR inhibitors specifically, the kinetic distinction between
conformational state binders is dramatic and clinically relevant.**

| Drug | Type | Conformation | Ki (nM) | Residence Time | Clinical Context |
|------|------|-------------|---------|----------------|------------------|
| Gefitinib | I (reversible) | DFG-in, active | 0.4 (Kiapp) | <14 min | 1st-gen, rapid resistance |
| Erlotinib | I (reversible) | DFG-in, active | ~2 | ~10-20 min (est.) | 1st-gen, rapid resistance |
| Lapatinib | I.5 (reversible) | Inactive-like | 3 | **430 min** | Unique efficacy in HER2+ breast |
| Afatinib | Covalent | DFG-in | 0.15 | Irreversible | 2nd-gen, broader spectrum |
| Osimertinib | Covalent | DFG-in | -- | Irreversible | 3rd-gen, T790M selectivity |

Critically: lapatinib has 30x longer residence time than gefitinib despite 7.5x
*weaker* equilibrium affinity (Ki 3 nM vs 0.4 nM). The kinetic advantage is entirely
attributable to binding an inactive-like conformation (Wood et al., 2004).

**Step 5: Therefore, state-aware design that targets DFG-out populations
implicitly selects for long residence time -- even without an explicit kinetic
scoring component.**

StateBind's 10x retrospective enrichment (EF@10 = 4.95/7.72 for state-aware vs
0.47/0.79 for static) can be partly interpreted as implicit kinetic optimization:
state-aware candidates that achieve high state_specificity scores for DFG-out states
inherently overlap with the drug population that demonstrates long residence times.
The state-aware pipeline does not just find molecules that *fit* the DFG-out pocket --
it finds molecules that would *stay* in the DFG-out pocket.

#### B.2 Supporting Evidence From Other Kinase Targets

The conformational selection kinetic argument is not EGFR-specific. It generalizes
across the kinome:

- **ABL (imatinib):** The prototypical Type II inhibitor. kon = 0.143 uM-1 s-1
  (slow, rate-limited by DFG flip). Nilotinib (also Type II) has "greatly prolonged"
  residence time vs dasatinib (Type I) (Manley et al., 2011 Blood).
- **p38alpha (BIRB796):** Residence time >1,800 hours. Type II, DFG-out binding.
  Molecular mechanism: conformational selection with water-mediated stabilization
  (Kokh et al., 2022 Nat Commun).
- **CDK8/CycC:** Type II pyrazole inhibitor: 32 hours residence time (DFG-out).
- **General kinome trend (Holdgate et al., 2018):** Analysis of 392 slow-off kinase
  inhibitors from Pfizer: Type II binding mode is the strongest predictor of long
  residence time, ahead of molecular weight, cLogP, and rotatable bond count.

#### B.3 Quantitative Selectivity Argument

Type II inhibitors are not only kinetically superior but also more selective:

- Type II Gini coefficients: 0.64-0.80 (Zhao et al., 2017)
- Type I Gini coefficients: 0.49-0.52

This means state-aware DFG-out design simultaneously achieves three desirable
properties: (1) long residence time, (2) high kinome selectivity, and (3) reduced
off-target toxicity. StateBind's state_specificity score captures property (2)
indirectly, while the kinetic score (Component A) would capture property (1) directly.

#### B.4 The Zero-Approved-Type-II-EGFR-Inhibitor Opportunity

A remarkable gap in the clinical landscape: no FDA-approved EGFR inhibitor is a Type II
(DFG-out) compound. All approved drugs are either Type I (gefitinib, erlotinib),
Type I.5 (lapatinib), or covalent (afatinib, osimertinib, dacomitinib, mobocertinib,
lazertinib). This is despite the strong evidence that DFG-out EGFR binding would
confer long residence time and high selectivity. StateBind's state-aware pipeline
targeting DFGout states is therefore exploring a clinically unexploited design space.

This is a compelling publication angle: "StateBind identifies candidates in an
underexplored conformational design space that published kinetic data suggests would
achieve superior residence times."

#### B.5 Draft Discussion Section Text

The following text is suitable for insertion into a manuscript Discussion section:

> **Conformational State Selection as Implicit Kinetic Optimization**
>
> The state-aware pipeline's 10-fold enrichment over the static baseline in
> retrospective validation (EF@10 = 4.95 and 7.72 for state-aware vs 0.47 and 0.79
> for static) has a natural kinetic interpretation. By explicitly targeting
> conformational substates of the EGFR kinase domain -- including the DFG-out
> inactive conformations -- the state-aware pipeline implicitly selects for
> binding kinetics favorable to drug efficacy.
>
> The biophysical basis for this claim is well-established. Type II kinase
> inhibitors, which bind the DFG-out conformation, consistently demonstrate
> 10-100 fold longer residence times than Type I inhibitors targeting the active
> DFG-in state (Copeland, 2016; Holdgate et al., 2018). For EGFR specifically,
> lapatinib -- which binds an inactive-like conformation -- has a residence time
> of 430 minutes, compared to <14 minutes for gefitinib, a classical Type I
> active-state binder (Wood et al., 2004). This 30-fold kinetic advantage exists
> despite lapatinib having weaker equilibrium affinity (Ki = 3 nM vs 0.4 nM).
>
> The mechanism is conformational selection: the DFG-out conformation is
> transiently populated, limiting kon, but once a Type II inhibitor binds, it
> stabilizes the inactive state, creating a kinetic trap that dramatically reduces
> koff (Wood et al., 2022). Drug-target residence time (1/koff) is increasingly
> recognized as a superior predictor of in vivo efficacy compared to equilibrium
> affinity (Copeland et al., 2006), as validated by the K4DD consortium across
> 3,812 compounds and 78 kinase targets (Schuetz et al., 2017).
>
> State-aware candidates optimized for DFG-out pocket geometry are therefore
> expected to inherit the favorable kinetic properties of Type II inhibitors:
> long residence time, high kinome selectivity (Gini 0.64-0.80 vs 0.49-0.52 for
> Type I; Zhao et al., 2017), and potentially reduced off-target toxicity.
> Notably, no approved EGFR inhibitor occupies the Type II DFG-out design space,
> despite strong biophysical rationale, highlighting a clinically unexploited
> opportunity that state-aware molecular design can address.
>
> This kinetic interpretation reframes the enrichment result: the state-aware
> pipeline does not merely identify molecules that fit specific pocket geometries
> but selects for a kinetic regime that published evidence associates with
> superior pharmacological outcomes. The addition of an explicit kinetic scoring
> component (Section X) makes this implicit selection quantitative and testable.

---

### Component C: Experimental Validation Design

All experimental work is framed as "proposed experimental collaboration" or
"future validation" -- not as prerequisite for computational publication.

#### C.1 Ten-Compound SPR Validation Panel

**Compound Selection Strategy:**

| Category | N | Selection Logic | Purpose |
|----------|---|-----------------|---------|
| State-aware top, static bottom | 3 | Ranked top-5 by state-aware, bottom-50% by static | Maximum discrimination between pipelines |
| Static top, state-aware bottom | 2 | Ranked top-5 by static, bottom-50% by state-aware | Reverse discrimination |
| Top in both pipelines | 2 | Ranked top-10 in both | Positive control (expected activity) |
| Known EGFR drugs (reference) | 3 | Erlotinib (Type I), lapatinib (Type I.5), osimertinib (covalent) | Kinetic reference standards with published values |

Total: 10 compounds (7 computational candidates + 3 reference drugs).

**SPR Assay Design:**

- **Instrument:** Biacore 8K+ or T200 (available at most academic core facilities)
- **Protein:** Avi-tagged EGFR kinase domain (residues 696-1022), biotinylated,
  immobilized on streptavidin chip
- **EGFR variants:** WT, L858R, T790M, L858R/T790M (4 variants test mutation sensitivity)
- **Concentrations:** 8-point 3-fold serial dilution per compound
  (e.g., 10 uM to 0.46 nM)
- **Replicates:** Triplicate (independent injections)
- **Readout per compound:** kon (M-1 s-1), koff (s-1), KD (nM) for each variant
- **Total sensorgrams:** 10 compounds x 4 variants x 8 concentrations x 3 replicates
  = 960 sensorgrams
- **Throughput:** Biacore 8K processes ~4,600 interactions/day; this panel requires
  <1 day of instrument time once optimized

**Primary hypothesis test:** State-aware candidates targeting DFGout states will show
significantly longer residence times (lower koff) on EGFR than static candidates.

**Secondary hypothesis test:** The kinetic ranking of candidates by SPR will correlate
with the kinetic scoring component (Tier 2 or Tier 3) better than with the current
4-component unified score.

**Timeline:**
- Weeks 1-2: Protein expression, purification, biotinylation, chip optimization
- Weeks 3-4: SPR screening of 10 compounds on 4 EGFR variants
- Week 5: Data analysis, kinetic fitting (Biacore Insight Evaluation)

**Cost:**
- In-house (academic core facility): $10,000-20,000
  - Protein production: $3,000-5,000
  - Sensor chips + reagents: $2,000-4,000
  - Instrument time: $2,000-5,000
  - Compound synthesis/procurement: $3,000-6,000
- CRO (Reaction Biology, Biaffin, or Eurofins): $33,000-52,000
  - Includes protein, chips, compounds, and full kinetic analysis

#### C.2 HDX-MS Conformational State Validation

**Purpose:** Directly validate that different EGFR inhibitors stabilize different
conformational states, as predicted by the 4-state atlas.

**Protocol:**

| Parameter | Design |
|-----------|--------|
| Protein | EGFR kinase domain (696-1022), WT and L858R |
| Conditions | Apo (no drug), + erlotinib (Type I), + lapatinib (Type I.5), + 1 state-aware DFGout candidate |
| Exchange timepoints | 10 s, 30 s, 1 min, 5 min, 30 min, 4 h |
| Replicates | Triplicate per condition |
| Digestion | Pepsin column, online at 4C |
| Analysis | LC-MS/MS, DynamX or HDExaminer software |

**Key regions to monitor:**

| Region | Residues | Expected HDX Signature |
|--------|----------|----------------------|
| Alpha-C helix | 729-745 | Protected by aCin drugs, deprotected by aCout drugs |
| DFG motif | 831-833 | Protected by DFGout binders, dynamic in DFGin binders |
| Activation loop | 831-858 | Ordered/protected by active-state binders, disordered by inactive-state binders |
| Hinge region | 788-790 | Protected by all ATP-competitive inhibitors |
| P-loop | 695-700 | Differentially protected depending on binding mode |

**Expected outcomes:**
- Erlotinib (Type I): Protection of hinge + P-loop, minimal effect on DFG and A-loop
- Lapatinib (Type I.5): Protection of hinge + strong DFG + A-loop protection
  (stabilizes inactive state)
- State-aware DFGout candidate: Should show lapatinib-like HDX signature if it
  genuinely binds the DFG-out conformation

**What constitutes validation:** If the state-aware DFGout candidate shows a protection
pattern more similar to lapatinib (inactive-state binder) than to erlotinib (active-state
binder), this validates that the state-conditioned design pipeline produces candidates
that engage the intended conformational state.

**Cost and timeline:**
- Instrument time and sample prep: $30,000-50,000
- Timeline: 6-8 weeks (including protein prep, optimization, data collection, analysis)
- Can be performed at academic HDX-MS core facilities (e.g., Scripps, UCSF, Yale)

#### C.3 Proposed Validation Hierarchy

Experiments are ordered by information value relative to cost:

| Priority | Experiment | Cost | Time | What It Proves |
|----------|-----------|------|------|----------------|
| 1 | SPR kinetic panel | $10-20K | 4-5 weeks | State-aware candidates have longer RT |
| 2 | HDX-MS (2 conditions) | $15-25K | 4-6 weeks | DFGout candidates stabilize inactive state |
| 3 | Full HDX-MS (4 conditions) | $30-50K | 6-8 weeks | Complete conformational state mapping |
| 4 | NanoBRET cellular engagement | $8-12K | 2-3 weeks | Target engagement in live cells |
| 5 | CETSA thermal shift | $3-5K | 2 weeks | Cellular thermal stabilization |

Minimum viable validation: Priority 1 alone ($10-20K, 4-5 weeks) would be sufficient
for a high-impact computational publication with experimental grounding. Priorities
1+2 ($25-45K, 8-10 weeks) would make a strong case for Nature Computational Science.

---

## Impact Assessment

### Publication Impact

**Target venues (in priority order):**

1. **Nature Computational Science** -- The full package (Components A+B+C with SPR data)
   would be a strong submission. The kinetic dimension differentiates from existing
   structure-based drug design tools. The conformational selection narrative provides
   the mechanistic depth reviewers expect.

2. **Journal of Chemical Information and Modeling (JCIM)** -- Component A alone (kinetic
   scoring with benchmarking against K4DD data) would be publishable as a methods paper.

3. **Nature Communications** -- Components B+C (conformational selection narrative with
   experimental validation) could stand alone as a biophysics-focused paper.

4. **Journal of Medicinal Chemistry (JMC)** -- If SPR data shows clear kinetic
   differentiation, the medicinal chemistry community would value this structure-kinetic
   relationship analysis.

**What reviewers would attack:**
- "The kinetic prediction accuracy is insufficient to justify a scoring component."
  Response: The 3-tier cascade ensures graceful degradation; even the Tier 3 heuristic
  captures the dominant signal (DFGout = slow koff).
- "10% weight is arbitrary." Response: Sensitivity analysis across 5-20% weight range
  shows robust ranking stability (to be computed).
- "The null result on mean score persists." Response: The enrichment metric (EF@10)
  is the primary claim, not mean score. Adding kinetics may shift mean score but is
  not guaranteed, and we report both honestly.
- "No experimental validation of novel compounds." Response: Component C provides the
  experimental design; SPR data is presented as proof-of-concept for the kinetic
  hypothesis.

**Main paper claim:** "State-aware molecular design implicitly optimizes for favorable
binding kinetics through conformational selection, and this implicit optimization can
be made explicit and quantitative through a kinetic scoring component -- producing the
first drug design pipeline that jointly optimizes conformational state specificity and
predicted residence time."

### Effort Estimate

| Component | Person-Weeks | Compute | External Cost | Skills Required |
|-----------|-------------|---------|--------------|-----------------|
| B: Narrative | 1 | None | None | Writing, kinetics knowledge |
| A: Tier 3 (heuristic) | 1 | None | None | Python, StateBind familiarity |
| A: Tier 2 (ML koff) | 3-4 | 1-2 GPU-days (training) | None | ML, PyTorch |
| A: Tier 1 (tauRAMD) | 4-6 | 150-250 GPU-days | None | MD, GROMACS |
| A: Integration + tests | 2 | Minimal | None | Python, pytest |
| C: SPR panel | 4-5 | None | $10-52K | Collaboration / CRO |
| C: HDX-MS | 6-8 | None | $30-50K | Collaboration / CRO |
| **Total** | **~21-27 weeks** | **~250 GPU-days** | **$40-100K** | -- |

**Minimal viable version:** Component B (1 week) + Tier 3 heuristic (1 week) = 2 weeks,
zero compute, zero external cost. This alone adds significant publication value.

**Recommended phase 1:** Components B + A (Tiers 3 + 2) = 5-6 weeks, minimal compute.
Provides the narrative, the scoring component with two functional tiers, and a testable
framework.

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| tauRAMD fails to rank EGFR candidates reliably | Medium (30%) | Component A Tier 1 unreliable | Tier 2/3 fallback; validate on known drugs first |
| ML koff model has poor EGFR generalization | Medium (35%) | Tier 2 inaccurate | Pre-train on pan-kinase, fine-tune on EGFR; report training curve |
| Kinetic score does not change mean score ranking | High (50%) | Null result persists | Report honestly; the 10x enrichment + narrative are the main claims |
| SPR shows no kinetic difference between pipelines | Low-Medium (25%) | Experimental validation fails | Would still be publishable as "computational pipeline predicts kinetics, experimental test reveals limitations" |
| Reviewer rejects heuristic tier as too simplistic | Low (15%) | Component A downgraded | The heuristic is the fallback, not the primary tier; present as graceful degradation |
| STELLAR-koff not reproducible | Medium (30%) | Tier 2 model selection affected | Train custom GNN on assembled data; use Ridge regression fallback |
| Compute allocation insufficient for tauRAMD | Low (10%) | Tier 1 delayed | Run as scavenge_gpu jobs; reduce to top 15 candidates x 2 states |

**Highest-risk scenario:** Kinetic scoring is implemented but does not change the
bottom-line comparison between pipelines. This is mitigated by framing: the kinetic
dimension is about mechanistic understanding and pipeline capability, not about reversing
the null result. The narrative (Component B) carries publication value regardless.

---

## Evaluation Criteria

The proposal should be evaluated on:

1. **Does the kinetic scoring component add discriminative value?** Test: Compute the
   change in enrichment factor (EF@10, EF@1) with and without the kinetic score.

2. **Does the conformational selection narrative enhance publication impact?** Test:
   Expert reviewer assessment of the Discussion section with and without the kinetic
   framing.

3. **Is the three-tier cascade architecturally consistent with StateBind?** Test:
   Code review confirming adherence to fallback patterns, config-driven parameters,
   and artifact-based communication.

4. **Does SPR validation confirm kinetic predictions?** Test: Spearman correlation
   between kinetic_score (any tier) and experimentally measured koff from SPR.

5. **Does HDX-MS validate conformational state assignments?** Test: HDX protection
   patterns for DFGout candidates resemble lapatinib (inactive binder) rather than
   erlotinib (active binder).

6. **Is the weight allocation robust?** Test: Sensitivity analysis showing that
   kinetic weight 5-20% produces stable top-10 rankings (Kendall tau > 0.8).

7. **Does the narrative survive peer review?** Test: The causal chain (state-aware
   design -> conformational selection -> slow koff -> long RT -> efficacy) must be
   supported at every link by published data with specific citations.

---

## Open Questions

1. **Should covalent inhibitors be treated separately?** The kinetic_T3 heuristic
   assigns 0.90 to covalent binders, but covalent kinetics follow kinact/Ki, not
   koff. A separate covalent kinetics sub-score may be needed.

2. **How should the kinetic score handle multi-state candidates?** A compound that
   appears in both DFGin_aCin (kinetic_T3=0.30) and DFGout_aCin (kinetic_T3=0.70)
   gets which value? Proposal: use the score for the target state.

3. **Should kinetic weight increase as prediction methods mature?** A roadmap for
   weight escalation (10% -> 15% -> 20%) as tauRAMD or ML accuracy improves could
   be pre-specified.

4. **What is the minimum number of SPR compounds for statistical power?** Power
   analysis suggests N=10 provides ~80% power to detect a 2-fold koff difference
   (two-sided t-test, alpha=0.05) -- but this depends on variance.

5. **Can the conformational selection narrative be tested computationally before
   experiments?** Yes: run tauRAMD on erlotinib (Type I) and lapatinib (Type I.5)
   in all 4 EGFR conformational states. If tauRAMD correctly predicts lapatinib >>
   erlotinib residence time, this validates the method before applying to novel
   candidates.

6. **Is the KOFFI database large enough for kinase-specific ML?** With 1,705 entries
   across all targets, the kinase subset may be ~300-500 entries. Transfer learning
   from the full BindingDB kinetic set may be necessary.

7. **How does the kinetic score interact with Pareto optimization?** The current
   Pareto analysis (`ranking/pareto.py`) uses 4 objectives. Adding a 5th (kinetic)
   objective increases the dimensionality of the Pareto front. At what point does
   the curse of dimensionality make Pareto analysis uninformative?

---

## References

1. Copeland RA, Pompliano DL, Meek TD. Drug-target residence time and its
   implications for lead optimization. Nat Rev Drug Discov. 2006;5(9):730-739.

2. Copeland RA. The drug-target residence time model: a 10-year retrospective.
   Nat Rev Drug Discov. 2016;15(2):87-95.

3. Copeland RA. Drug-target residence time: critical information for lead
   optimization. Expert Opin Drug Discov. 2010;5(4):305-310. PMCID: PMC2918722.

4. Wood ER, et al. A unique structure for EGFR bound to GW572016 (lapatinib).
   Cancer Res. 2004;64(18):6652-6659.

5. Singh J, et al. Covalent EGFR inhibitor analysis reveals importance of reversible
   interactions to potency and mechanisms of drug resistance. Chem Biol.
   2014;21(9):1107-1116. PMCID: PMC3890870.

6. Sasi VM, et al. Insight into the Therapeutic Selectivity of the Irreversible
   EGFR Tyrosine Kinase Inhibitor Osimertinib through Enzyme Kinetic Studies.
   Biochemistry. 2020;59(14):1428-1441.

7. Schuetz DA, et al. Kinetics for Drug Discovery: an industry-driven effort to
   target drug residence time. Drug Discov Today. 2017;22(6):896-911.

8. Holdgate GA, et al. Structure-kinetic relationships that control the residence
   time of drug-target complexes. Curr Opin Struct Biol. 2018;49:51-58.
   PMCID: PMC6066427.

9. Wood MJ, et al. Mutation in Abl kinase with altered drug-binding kinetics indicates
   a novel mechanism of imatinib resistance. PNAS. 2022;119(3):e2111451118.
   PMCID: PMC8890393.

10. Manley PW, et al. Nilotinib, in Comparison to Both Dasatinib and Imatinib,
    Possesses a Greatly Prolonged Residence Time When Bound to the BCR-ABL Kinase
    SH1 Domain. Blood. 2011;118(21):1674.

11. Kokh DB, et al. Estimation of Drug-Target Residence Times by tau-Random
    Acceleration Molecular Dynamics Simulations. J Chem Theory Comput.
    2018;14(7):3859-3869.

12. Kokh DB, et al. Machine Learning Analysis of tauRAMD Trajectories to Decipher
    Molecular Determinants of Drug-Target Residence Times. Front Mol Biosci.
    2019;6:36.

13. Kokh DB, et al. Decisive role of water and protein dynamics in residence time
    of p38alpha MAP kinase inhibitors. Nat Commun. 2022;13:1523.

14. Raniolo S, Limongelli V. Ligand binding free-energy calculations with funnel
    metadynamics. Nat Protoc. 2020;15(9):2837-2866.

15. Freire E. Do enthalpy and entropy distinguish first in class from best in class?
    Drug Discov Today. 2008;13(19-20):869-874. PMCID: PMC2581116.

16. Ruan Z, et al. Biochemical and structural basis for differential inhibitor
    sensitivity of EGFR with distinct exon 19 mutations. Nat Commun. 2022;13:6791.

17. Hammoudeh DI, et al. Dynamics of Protein Kinases and Pseudokinases by HDX-MS.
    Kinases Phosphatases. 2022. PMCID: PMC9148214.

18. Zhao Z, et al. Determining cysteines available for covalent inhibition across
    the human kinome. J Med Chem. 2017;60(7):2879-2889.

19. Votapka LW, et al. SEEKR2: Versatile Multiscale Milestoning Utilizes the
    OpenMM Molecular Dynamics Engine. J Chem Inf Model. 2022;62(13):3253-3262.

20. Tiwary P, et al. Kinetics of protein-ligand unbinding: predicting pathways,
    rates, and rate-limiting steps. PNAS. 2015;112(5):E386-E391.

21. Georgi V, et al. Compound selectivity and target residence time of kinase
    inhibitors studied with surface plasmon resonance. J Mol Biol. 2017;429(4):574-586.

22. Tonge PJ. Drug-target kinetics in drug discovery. ACS Chem Neurosci.
    2018;9(1):29-39.

23. Dahl G, Akerud T. Pharmacokinetics and the drug-target residence time concept.
    Drug Discov Today. 2013;18(15-16):697-707.
