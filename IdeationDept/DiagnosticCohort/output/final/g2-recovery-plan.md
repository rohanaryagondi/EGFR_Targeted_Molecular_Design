---
agent: Orchestrator (Investigation Lead)
round: 3
date: 2026-04-14
type: directive
scope: final-recovery-plan
---

# G2 Recovery Plan: From Random Labels to Publication

## 0. Document Purpose

This is the final output of the DiagnosticCohort investigation into the Gate G2
(Ablation C) NO_GO result (Cohen's d = 0.059, 10 seeds, ~6,800 molecules). It
synthesizes the findings of 5 specialist agents across 2 rounds of independent
investigation and cross-analysis. It provides the root cause assessment, a decision-
tree recovery plan with go/no-go gates, resource estimates, and publication strategy.

**Audience:** The human operator (rag88) and any future AI agents tasked with
executing the recovery.

---

## 1. Root Cause Assessment

### 1.1 The Smoking Gun: Random State Labels

The root cause of the G2 NO_GO is that **state labels in the training data are
randomly assigned** for the vast majority of the 8,109 EGFR molecules.

**Direct evidence:**

1. **Code inspection (kinchembio, mldebug):** `prepare_vae_data.py` assigns states
   via `rng.choice(_VALID_STATES)` for all ChEMBL API compounds. The function
   `_assign_state_from_type("")` receives an empty string (ChEMBL API does not return
   inhibitor type), which triggers uniform random assignment. Only ~55 hand-curated
   compounds (0.5% of dataset) have meaningful state labels.

2. **Distribution analysis (kinchembio):** The state distribution is near-perfectly
   uniform (24.5-26.1% per state), consistent with random assignment. For a real
   biological distribution of EGFR inhibitors, >90% should be Type I (DFGin).

3. **Silent data loss (kinchembio):** The VAE config uses `n_states=3` but the data
   contains 4 states. ~2,114 DFGout_aCout molecules (26%) are silently dropped during
   training.

4. **Model behavior is correct (mldebug):** A model trained on random labels SHOULD
   ignore them. Cohen's d = 0.059 and centroid distances of 6-10% of latent scale are
   the correct outcome, not a failure. The null result is the expected result.

### 1.2 Final Probability Estimates

Integrating all 5 specialists' Round 2 assessments:

| Hypothesis | Probability | Role | Agent Consensus |
|------------|------------|------|-----------------|
| **H2: Random state labels** | **75-85%** | **ROOT CAUSE** | 5/5 agree (condgen 80%, kinchembio 80%, evaldes 75%, mldebug 80%, pubstrat 80%) |
| H1: Weak conditioning mechanism | 15-20% | Compounding factor | 5/5 agree secondary. Prefix tokens are weakest viable mechanism but irrelevant when labels are noise |
| H3: Wrong evaluation metric | 5-15% | Compounding factor | 5/5 agree tertiary. Three structural flaws confirmed but masked by H2 |

**The failure chain:**

```
Random labels (H2)
  -> Model correctly learns to ignore labels
    -> Near-identical latent centroids (d = 0.059)
      -> No state-specific molecular generation
        -> Evaluation confirms no benefit
           (which it couldn't detect even if there were benefit, due to H3 flaws)
```

All three hypotheses must be addressed for a positive result. They must be fixed
**in order**: H2 (data) first, then H1 (architecture, if needed), then H3 (evaluation).

### 1.3 Compounding Factors

Even after fixing H2, two compounding issues remain:

**H1 -- Weak conditioning mechanism:**
- Prefix-token conditioning is the weakest in the modern hierarchy: prefix < FiLM <
  cross-attention < adaLN < adaLN-Zero (Peebles & Xie, 2023)
- The state one-hot (3 dims) occupies only 4.5% of the 67-dim z-projection input
- 1.58 bits of state information spread across 8 prefix tokens yields ~0.2 bits/token,
  easily overwhelmed by the 60-80 molecule tokens
- The decoder receives `[z; state_onehot]` directly via `z_proj`, creating an
  information shortcut where the encoder has no incentive to encode state into z

**H3 -- Wrong evaluation:**
- `state_specificity = 0`: Zeroes the only component that could detect state-specific
  generation (15% weight removed)
- Fixed 1M17 pocket: 2/3 of conditioned molecules scored against the wrong pocket
- Type I reference molecules (35% weight): Erlotinib/gefitinib references penalize
  generation of DFGout-specific chemistry

---

## 2. Decision Tree

The recovery follows a branching decision tree, not a linear plan. At each gate,
the next action is determined by the result.

```
                        DAY 1: DIAGNOSTIC BATTERY
                        (scaffold overlap, probing classifier,
                         state-swap, MI estimate, loss curves)
                                    |
                    ________________|________________
                   |                                 |
            All confirm H2                   ANY contradicts H2
            (expected)                       (D1 accuracy >50%)
                   |                                 |
                   v                          Investigate: are the
         DAY 1-2: MW-TERCILE                  55 curated compounds
         POSITIVE CONTROL                     dominating the latent
         (same architecture,                  space? Re-probe without
          MW labels instead                   curated set.
          of state labels)                          |
                   |                                 v
          _________|_________               Reassess H2 probability.
         |                   |              If still >50%, continue.
    d > 0.5 on MW       d < 0.3 on MW      If <50%, pivot to
    (architecture        (architecture      architecture-first path.
     works)               broken)
         |                   |
         v                   v
    WEEK 1-3:           WEEK 1-2:
    FIX EGFR LABELS     ARCHITECTURE FIX
    via KLIFS/KinCoRe   (FiLM or adaLN-Zero)
    (parallel: start    BEFORE fixing labels.
     ABL1 curation)     Then fix labels.
         |                   |
         v                   v
    WEEK 3-5: RETRAIN WITH FIXED LABELS
    Same architecture (prefix tokens) if MW worked.
    New architecture (FiLM/adaLN) if MW failed.
    10 seeds, conditioned + unconditioned.
                        |
              __________|__________
             |          |          |
         d > 0.5    d 0.15-0.30   d < 0.15
         (GO)       (PIVOT)       (NO_GO)
             |          |          |
             v          v          v
         Evaluate    Upgrade to   Check MW-tercile
         with multi- adaLN-Zero   result:
         pocket      + CFG +       - If MW worked:
         docking.    multi-pocket    EGFR biology
         Write       evaluation.     is the problem.
         paper       Retrain.        Pivot to ABL1.
         (Framing F) If still null:  - If MW failed:
             |       pivot to ABL1.   Architecture
             v          |             is broken.
         ABL1          v              Try adaLN-Zero.
         validation  ABL1 result         |
         (if ready)  determines          v
             |       publication      ABL1 is the
             v       strategy.        last chance.
         WEEK 6-8:                        |
         PREPRINT                         v
         (ChemRxiv)                   ALL NULL:
                                      Write rigorous
                                      negative result
                                      paper (Framing B+E)
```

---

## 3. Phased Execution Plan

### Phase 0: Diagnostic Confirmation (Day 1)

**Goal:** Empirically confirm the random-label root cause and test the conditioning
mechanism independently.

| # | Diagnostic | Method | Predicted Result | If Violated | Effort |
|---|-----------|--------|-----------------|-------------|--------|
| D0 | Scaffold overlap (training data) | Bemis-Murcko Jaccard between state-labeled groups | Jaccard > 0.85 (random assignment -> same scaffolds per state) | Jaccard < 0.7 would suggest some real structure in labels | 5 min CPU |
| D1 | Probing classifier on z | Logistic regression on latent z from seed-0 checkpoint | 33-37% accuracy (chance) | >50% suggests model found signal despite noise | 5 min GPU |
| D4 | State-swap experiment | Generate with state A labels, then swap to state B | >95% identical outputs | <80% identical suggests conditioning has some effect | 15 min GPU |
| D5 | Scaffold overlap (curated 55) | Bemis-Murcko Jaccard on the 55 hand-curated compounds only | Jaccard 0.3-0.6 (curated set has real type I/II distinction) | >0.8 suggests even curated compounds are chemically homogeneous | 5 min CPU |
| D7 | Mutual information I(z; state) | Non-parametric MI estimate on latent z | < 0.05 nats (< 5% of H(state)) | > 0.15 nats challenges H2 | 5 min GPU |
| D8 | Loss-curve comparison | Compare final validation loss (conditioned vs unconditioned) across 10 seeds | Recon loss difference < 0.5%, p > 0.05 | Difference > 2%, p < 0.01 means labels somehow help | 10 min CPU |
| D9 | Property distributions (generated) | KS test on MW/LogP/QED between state-conditioned generation pools | p > 0.1 for all pairwise comparisons | p < 0.01 for any pair suggests conditioning differentiated output | 30 min CPU |

**SLURM spec (GPU diagnostics D1, D4, D7):**
```bash
#SBATCH --job-name=g2_diag_confirm
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 00:30:00
```

**SLURM spec (CPU diagnostics D0, D5, D8, D9):**
```bash
#SBATCH --job-name=g2_diag_cpu
#SBATCH -p day
#SBATCH -A pi_mg269
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH -t 01:00:00
```

**Total Phase 0 effort:** ~1 GPU-hour, ~2 CPU-hours. Completable in 1 day.

**Deliverable:** `artifacts/diagnostics/confirmation_battery_results.json`

**Gate G0:** All diagnostics confirm H2? If yes -> Phase 1. If any contradicts ->
investigate before proceeding (see decision tree).

---

### Phase 1: MW-Tercile Positive Control (Days 1-2)

**Goal:** Determine whether the prefix-token conditioning mechanism can convey ANY
meaningful conditioning signal, independent of state labels.

**Protocol:**
1. Assign MW tercile labels (low/medium/high) to training data based on molecular
   weight. These labels are objectively determinable from SMILES with zero ambiguity.
2. Train the Transformer VAE with MW-tercile labels using the EXACT same architecture
   (prefix tokens, same hyperparameters, same training schedule).
3. Generate 200 molecules per MW class + 200 unconditioned.
4. Measure: mean MW per conditioned class, Cohen's d on MW difference.
5. Run probing classifier (D1) on latent z for MW terciles.

**Expected results:**
- If mechanism works: d > 1.0 on MW difference, probe accuracy > 70%
- If mechanism broken: d < 0.3, probe accuracy < 50%

**Why MW is the right first test (but not the only test):**
MW is correlated with SMILES length, making it an "easy" conditioning target. If MW
fails, the mechanism is definitively broken. If MW succeeds, run a harder test
(ring-count terciles) to confirm the mechanism works for non-trivial properties
(mldebug's recommendation).

**SLURM spec:**
```bash
#SBATCH --job-name=g2_mw_control
#SBATCH -p gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=rtx_5000_ada:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
```

**Total Phase 1 effort:** 2-3 GPU-hours, 1 day.

**Gate G1:** MW conditioning d > 0.5?
- YES -> Architecture works. Proceed to Phase 2 (fix data).
- NO -> Architecture broken. Proceed to Phase 2-ALT (fix architecture first).

---

### Phase 2: Fix EGFR Labels (Week 1-3)

**Goal:** Replace random state assignments with biologically meaningful labels using
structural data from KLIFS and KinCoRe.

**Method (kinchembio's protocol):**

1. **KLIFS structural annotation (primary, 2-3 days):**
   - Query KLIFS for all EGFR structures with ligand-bound conformational state
     annotations (DFG conformation + alphaC-helix position)
   - Map ChEMBL compound IDs to KLIFS ligand IDs via InChIKey/SMILES matching
   - For compounds with co-crystal structures: assign state from the structure
   - Expected coverage: 500-2,000 compounds with confident labels

2. **KinCoRe cross-validation (1 day):**
   - Use KinCoRe (Modi & Bhatt, 2023) kinase inhibitor classification as independent
     validation of KLIFS assignments
   - Compounds classified as type I -> DFGin, type II -> DFGout

3. **Reduce to 2-class problem (kinchembio's recommendation):**
   - EGFR biology is type I-dominated (>90% of inhibitors are DFGin)
   - No WT EGFR DFGout structures exist (3W2R is T790M/L858R double mutant)
   - Reduce from 4-state to 2-state: **aCin vs aCout** (both within DFGin)
   - This is the biologically meaningful distinction for EGFR: active (aCin) vs
     inactive (aCout) conformations both accessible to type I inhibitors

4. **State classifier validation (2 hours, CPU):**
   - Train Random Forest on Morgan fingerprints with KLIFS-assigned labels
   - If accuracy >> 50% (for 2-class): labels carry chemical signal
   - If accuracy ~ 50%: even properly labeled EGFR may lack chemical distinction
   - This is the go/no-go for EGFR viability

**Risk -- EGFR may not be salvageable:**
- If KLIFS annotation covers < 40% of compounds AND the state classifier shows ~50%
  accuracy, EGFR lacks sufficient chemical diversity across states
- In this case, the ABL1 parallel path (Phase 2-PAR) becomes the primary path

**Total Phase 2 effort:** 2-3 days for annotation, 2 hours for classifier. CPU-only.

**Gate G2-data:** State classifier accuracy on KLIFS-labeled EGFR > 60% (2-class)?
- YES -> Labels carry signal. Proceed to Phase 3 (retrain).
- NO -> EGFR may be fundamentally unsuitable. Check ABL1 progress (Phase 2-PAR).

---

### Phase 2-PAR: ABL1 Dataset Construction (Week 1-3, parallel)

**Goal:** Build a properly labeled ABL1 training dataset as a positive control kinase
with genuine chemotype distinction across conformational states.

**Why ABL1 (kinchembio, pubstrat):**
- Genuine DFGin vs DFGout chemotype distinction: imatinib/nilotinib/ponatinib (type II,
  DFGout) vs dasatinib/bosutinib (type I, DFGin). Tanimoto < 0.3 between classes.
- KLIFS has 309 ABL1 structures with near-even DFGin/DFGout split
- ChEMBL has ~15,000 ABL1 compounds
- If conditioning works anywhere for kinases, it should work for ABL1

**Protocol:**
1. Query ChEMBL for ABL1 bioactivity data (IC50 < 1 uM)
2. Map to KLIFS structures for DFG state assignment
3. Assign type I/type II classification from KinCoRe
4. Validate with scaffold analysis: confirm type I and type II scaffolds are distinct
5. Prepare SELFIES-encoded training set matching EGFR pipeline format

**Effort:** 1-2 weeks person-time, CPU-only for data curation.

**This runs in parallel with Phase 2.** The ABL1 dataset does not depend on EGFR
label fixing, and starting it now saves 3-4 weeks of calendar time if EGFR proves
unsuitable.

---

### Phase 2-ALT: Architecture Fix (Only if Gate G1 fails)

**Goal:** Replace the prefix-token conditioning mechanism with a stronger alternative.

**This phase is triggered ONLY if the MW-tercile positive control fails (Gate G1 = NO).**

**Options ranked by implementation effort (mldebug's ranking):**

| Option | Effort | Description | When to Use |
|--------|--------|-------------|-------------|
| 1. Remove shortcut | 2 hours | Change `z_proj` input from `[z; state_onehot]` to `z` alone. Forces state through z. | First attempt |
| 2. Separate prefix tokens | 1 day | Separate `z -> content_prefix` (6 tokens) and `state -> state_prefix` (2 tokens) | If option 1 destabilizes training |
| 3. FiLM conditioning | 1-2 days | Replace prefix conditioning with FiLM layers (affine transform at every decoder layer) | If prefix-based approaches fail |
| 4. adaLN-Zero | 3-5 days | Replace LayerNorm with condition-predicted parameters (strongest mechanism per DiT) | Nuclear option |

**Strategy:** Try option 1 first (cheapest test first). If MW-tercile succeeds with
option 1, the shortcut was the problem. If it doesn't, escalate through options 2-4.

**SLURM spec:** Same as Phase 1 (single GPU training job).

---

### Phase 3: Retrain VAE with Fixed Labels (Week 3-5)

**Goal:** Retrain the Transformer VAE using properly annotated EGFR labels (and/or
ABL1 data) and run the G2 ablation again.

**Critical design decision (condgen, mldebug consensus):** Retrain with the SAME
architecture (prefix tokens) first, unless Gate G1 failed. This isolates the data
effect. If real labels produce d > 0.3 with the same architecture, the story is
clean: "the data was the problem, not the model."

**Training protocol:**
- 10 seeds (matching original G2 pre-registration)
- Conditioned + unconditioned for each seed
- Same hyperparameters, same training schedule
- NEW: Per-state validation loss tracking (mldebug's Checkpoint A monitoring)
- NEW: Probing classifier at epoch boundaries to track state encoding
- NEW: Centroid distance tracking across epochs

**Monitoring during training (mldebug's protocol):**

| Metric | Tracked At | Expected (if fix works) | Expected (if fix fails) |
|--------|-----------|------------------------|------------------------|
| Per-state val loss | Every 5 epochs | Diverges across states | Identical across states |
| Probing accuracy on z | Every 10 epochs | Rises from ~33% to >50% | Stays at ~33% |
| Centroid distance | Every 10 epochs | Grows from 0 to >1.0 | Stays at 0.26-0.42 |

**SLURM spec (per seed):**
```bash
#SBATCH --job-name=g2_retrain
#SBATCH -p gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=rtx_5000_ada:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
```

Use `--array=0-9` for 10-seed parallelism. Consider `-p priority -A prio_gerstein`
for faster turnaround.

**Total Phase 3 effort:** 7.5-15 GPU-hours (10 seeds x 0.75-1.5 hrs each). 2-3 days
wall time with array jobs.

**Post-training diagnostics (mldebug's Checkpoint B):**

| Diagnostic | Expected (fix works) | Expected (fix fails) | Threshold |
|-----------|---------------------|---------------------|-----------|
| D1: Probing accuracy | >55% | 33-40% | GO if >45% |
| D4: State-swap identity | <70% | >90% | GO if <80% |
| D5: Generated scaffold Jaccard | <0.65 | >0.85 | GO if <0.75 |
| D7: MI I(z;state) | >0.15 nats | <0.05 nats | GO if >0.10 nats |

**Gate G2b (thesis retest):** Cohen's d on conditioned vs unconditioned, 10 seeds.

| Result | Interpretation | Next Step |
|--------|---------------|-----------|
| d >= 0.5 | **GO.** Data fix resolved the problem. | Phase 4 (multi-pocket evaluation) |
| d in [0.3, 0.5) | **PIVOT.** Weak signal. Data helped but architecture limits remain. | Phase 3-ALT (upgrade to adaLN-Zero) + Phase 4 |
| d in [0.15, 0.30) | **Conditional NO_GO.** Some improvement but insufficient. | Check MW-tercile result. If MW worked: EGFR biology is the limit. Pivot to ABL1. If MW failed: try architecture fix. |
| d < 0.15 | **NO_GO.** Data fix alone insufficient. | Check diagnostics. If D1 < 45%: architecture shortcut is active (Phase 3-ALT). If D1 > 55% but d still low: chemical space lacks state structure. ABL1 is the path. |

---

### Phase 3-ALT: Architecture Upgrade (Only if Gate G2b < 0.3 and D1 < 45%)

**Goal:** Fix the information shortcut and/or upgrade the conditioning mechanism.

**Step 1: Remove shortcut (2 hours)**
```python
# Current:  z_proj = Linear(latent_dim + n_states, n_prefix * d_model)
# Fixed:    z_proj = Linear(latent_dim, n_prefix * d_model)
# State information must flow through z, forcing encoder to encode it.
```
Retrain 1 seed, check D1 accuracy. If >55% improvement, retrain all 10 seeds.

**Step 2: FiLM conditioning (1-2 days, if shortcut removal insufficient)**
Replace prefix-token conditioning with FiLM layers at every Transformer decoder layer.
Affine transform: `h_out = gamma(state) * h + beta(state)`.

**Step 3: adaLN-Zero (3-5 days, if FiLM insufficient)**
Replace LayerNorm with adaptive LayerNorm (Peebles & Xie, 2023). State and z jointly
predict scale, shift, and gate parameters for each layer.

**Step 4: Classifier-free guidance at inference (1 day, additive)**
Add CFG with guidance weight w=2.0-3.0 at generation time. This amplifies whatever
conditioning signal exists without architectural changes.

**Total Phase 3-ALT effort:** 2-20 GPU-hours depending on how far up the ladder.

---

### Phase 4: Multi-Pocket Evaluation (Week 5-6)

**Goal:** Evaluate retrained models using the proper multi-pocket docking protocol
that can actually detect state-specific generation benefit.

**Protocol (evaldes):**

**Tier 1: Pocket-Preference Matrix (primary)**
- Dock all generated molecules against 3 pocket conformers:
  - 1M17 (DFGin/aCin) -- receptor PDBQT already prepared
  - 2GS7 (DFGin/aCout) -- receptor PDBQT already prepared
  - 3W2R (DFGout/aCin) -- receptor PDBQT already prepared
- Construct 3x3 pocket-preference matrix
- Primary test statistic: **Conformational Delta Score**
  ```
  ConfDelta(mol, state_i) = Vina(mol, pocket_i) - mean(Vina(mol, pocket_other))
  ```
- Cohen's d comparing delta(conditioned) vs delta(unconditioned)

**Tier 2: Dual-Evaluation (re-score with state_specificity)**
- Evaluation A: `state_specificity = 0` (replicates original G2)
- Evaluation B: `state_specificity` enabled with proper `state_smiles_map`
- Difference d_B - d_A measures contribution of generation exclusivity

**Tier 3: Reference binder expansion**
- Expand beyond erlotinib/gefitinib to include state-representative compounds:
  - DFGin/aCin: erlotinib, gefitinib, osimertinib
  - DFGin/aCout: lapatinib (PDB 1XKK)
  - DFGout: type II if available

**Negative control baseline (evaldes's Proposal 1):**
Run 100-molecule pilot docking on CURRENT (random-label) models FIRST to establish
the null distribution. This becomes the before/after comparison for the paper.

**SLURM spec:**
```bash
#SBATCH --job-name=g2_multipocket
#SBATCH --array=0-2
#SBATCH -p gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=rtx_5000_ada:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
```

**Total Phase 4 effort:** 4-8 GPU-hours for full docking, 2-3 hours for pilot.

**Gate G2c (multi-pocket thesis test):**

| Delta Score d | Pocket-Preference Diagonal | Interpretation |
|--------------|---------------------------|----------------|
| >= 0.5 | > 50%, chi-sq p < 0.05 | **GO.** Thesis supported. |
| 0.3-0.5 | 40-50% | **PIVOT.** Weak but real signal. |
| < 0.3 | ~33% (uniform) | **NO_GO.** No pocket preference. |

---

### Phase 5: ABL1 Validation (Week 4-7, overlapping)

**Goal:** Train and evaluate a state-conditioned VAE on ABL1 as a positive control.

If the ABL1 dataset is ready (Phase 2-PAR), train with the same protocol as EGFR:
- 10 seeds, conditioned (DFGin vs DFGout) + unconditioned
- Same architecture (or upgraded, if Phase 3-ALT was needed for EGFR)
- Multi-pocket evaluation against DFGin pocket (2GQG, dasatinib) and DFGout pocket
  (1IEP, imatinib)

**Expected:** ABL1 conditioning should produce STRONGER signal than EGFR because:
- Genuine chemotype distinction (Tanimoto < 0.3 between type I and type II)
- Near-even DFGin/DFGout split in KLIFS structures
- Well-characterized biology with multiple approved drugs in each class

**Effort:** 10-15 GPU-hours training, 4-8 GPU-hours docking.

---

### Phase 6: Paper Writing and Preprint (Week 6-9)

See Section 5 (Publication Strategy) below.

---

## 4. Resource Requirements

### 4.1 Compute Budget

| Phase | GPU-Hours | CPU-Hours | Wall Time | Partition |
|-------|-----------|-----------|-----------|-----------|
| 0: Diagnostics | 1 | 2 | 1 day | gpu_devel + day |
| 1: MW positive control | 2-3 | 0.5 | 1 day | gpu |
| 2: EGFR label fix | 0 | 20-40 | 2-3 days | day |
| 2-PAR: ABL1 curation | 0 | 40-80 | 1-2 weeks | day |
| 3: Retrain (EGFR) | 7.5-15 | 2 | 2-3 days | gpu (array) |
| 3: Retrain (ABL1) | 7.5-15 | 2 | 2-3 days | gpu (array) |
| 3-ALT: Architecture fix | 2-20 | 1 | 1-5 days | gpu |
| 4: Multi-pocket docking | 4-8 | 4 | 1-2 days | gpu (array) |
| **Total (expected path)** | **25-45** | **70-130** | **5-7 weeks** | |
| **Total (worst case)** | **50-80** | **70-130** | **8-10 weeks** | |

### 4.2 Person-Time

| Activity | Person-Days | Skills |
|----------|------------|--------|
| Write diagnostic scripts | 1-2 | Python, PyTorch |
| KLIFS/KinCoRe annotation pipeline | 3-5 | ChEMBL API, KLIFS API, cheminformatics |
| ABL1 dataset construction | 5-10 | ChEMBL API, KLIFS API, SELFIES |
| Architecture modification (if needed) | 2-5 | PyTorch, Transformer architecture |
| Multi-pocket docking pipeline | 1-2 | GNINA, SLURM |
| Analysis and visualization | 3-5 | Matplotlib, statistical analysis |
| Paper writing | 10-15 | Scientific writing |
| **Total:** | **25-44** | |

### 4.3 Key Dependencies

```
Phase 0 (diagnostics)       Phase 1 (MW control)     Phase 2-PAR (ABL1)
   |                            |                         |
   |--- no dependency ----------|                         |
   |                            |                         |
   v                            v                         |
Phase 2 (EGFR labels)     Gate G1 (MW works?)            |
   |                       /         \                    |
   v                  YES              NO                 |
Gate G2-data          |            Phase 2-ALT            |
   |                  |            (fix arch)             |
   v                  v                |                  |
Phase 3 (retrain) <---|----------------|                  |
   |                                                      |
   v                                                      v
Gate G2b (thesis retest)              Phase 5 (ABL1 train/eval)
   |                                       |
   v                                       v
Phase 4 (multi-pocket)               Gate G2-ABL1
   |                                       |
   v                                       v
Phase 6 (paper) <--------------------------+
```

**Critical path:** Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 6
**Parallel path:** Phase 2-PAR -> Phase 5 (merges at Phase 6)

---

## 5. Publication Strategy

### 5.1 Recommended Framing: "The Diagnostic Journey" (Framing F)

**Title template:** "When Conditional Generation Fails: Diagnosing Random Labels,
Evaluation Blindness, and Weak Conditioning in State-Aware Molecular Design"

**Main claim:** We pre-registered a hypothesis that conformational state conditioning
improves EGFR molecular generation. The result was a definitive null (d=0.059, 10
seeds). Systematic investigation revealed three compounding failure modes: (1) training
data labels were randomly assigned, (2) the evaluation was structurally blind to
state-specific quality, and (3) the conditioning mechanism was the weakest viable
option. After fixing all three, we report [updated result]. The diagnostic framework
generalizes to any conditional molecular generation system.

**Why this is the strongest framing (pubstrat):**
- Story structure mirrors the scientific method: hypothesis -> test -> null ->
  investigation -> root cause -> fix -> retest
- Three independent failure modes are each independently citable contributions
- Pre-registration anchors credibility (null was committed before investigation)
- Subsumes all other framings (A-E from Round 1)
- The 10-seed false alarm (d=0.71 on 3 seeds -> d=-0.02 on 10 seeds) with RANDOM
  labels is a concrete demonstration of small-sample evaluation risk

**Expected value:** 5.5 (highest of all framings). Expected citations: 60-150 over
3 years.

### 5.2 Paper Structure

| Section | Content | Key Figures |
|---------|---------|-------------|
| 1. Introduction | State-conditioned generation thesis, prior work | -- |
| 2. Methods | VAE architecture, training protocol, pre-registration | Architecture diagram |
| 3. The Null Result | G2 Ablation C: d=0.059, 10 seeds | Effect size distribution, false alarm analysis |
| 4. Investigation | Three failure modes discovered | (a) Random label distribution, (b) Scaffold overlap, (c) Pocket-preference null |
| 5. The Fix | KLIFS annotation, evaluation redesign, architecture upgrade | Before/after label distributions, MW positive control |
| 6. Results After Fix | Retrained model, multi-pocket evaluation | Delta Score distributions, pocket-preference matrix |
| 7. Generalization | ABL1 validation (if available) | Two-kinase comparison |
| 8. Discussion | When does conditioning work? Guidelines for practitioners | Decision flowchart |

**Estimated length:** 6,000-8,000 words, 5-6 figures.

### 5.3 Outcome-Dependent Venue Targeting

| EGFR Result | ABL1 Result | Best Framing | Target Venue | Expected Citations |
|-------------|-------------|-------------|-------------|-------------------|
| Positive (d>0.5) | Positive | F: Full diagnostic journey, two kinases | Nature Comp Sci / JCIM | 100-200 |
| Positive | Null | F: EGFR diagnostic journey | JCIM | 60-100 |
| Positive | Not run | F: EGFR-only journey | JCIM | 50-80 |
| Null EGFR | Positive ABL1 | F: Kinase-dependent conditioning | JCIM | 70-120 |
| Null EGFR | Null ABL1 | B+E: Pre-registered negative + evaluation | J Cheminformatics | 30-60 |
| Weak (0.3-0.5) | Positive | F: Conditioning works when chemistry allows | JCIM | 80-130 |

**There is no unpublishable outcome.** Every terminal node produces a paper. The
worst case (all null) is a J Cheminformatics full article; the best case is a Nature
Computational Science candidate.

### 5.4 Timeline to Preprint

- **Week 0:** Start writing introduction and methods (can proceed while experiments run)
- **Week 3-5:** Results from retrained models available
- **Week 5-6:** Multi-pocket docking results available
- **Week 6-8:** Draft complete with all results
- **Week 7-9:** ChemRxiv preprint to establish priority

**Scooping risk (pubstrat):** 15-20% within 6 months (mainly Volkamer group). The
7-9 week preprint timeline is well within this window. The diagnostic journey framing
is unique to this project -- no competitor has pre-registered a conditional generation
hypothesis and then systematically diagnosed the failure.

### 5.5 Standalone Publication Contributions

Even independent of the main paper, the investigation produces publishable components:

1. **Conformational Delta Score framework (evaldes):** Standardized evaluation protocol
   for state-conditioned molecular generation. Pocket-preference matrix + Delta Score
   adapted for intra-target conformational specificity. No comparable protocol exists.
   Target: JCIM methods paper or NeurIPS ML4DD workshop.

2. **10-seed false alarm analysis:** d=0.71 (3 seeds) to d=-0.02 (10 seeds) on random
   labels. Concrete quantitative demonstration of small-sample evaluation risk. Could
   standalone as a J Cheminformatics communication.

---

## 6. Week-by-Week Timeline

| Week | Day | Activity | Gate | Owner |
|------|-----|----------|------|-------|
| **W0** | 1 | Phase 0: Run diagnostic battery (D0, D1, D4, D5, D7, D8, D9) | G0: All confirm H2? | mldebug |
| | 1 | Phase 0: Run 100-molecule pilot docking (negative control baseline) | -- | evaldes |
| | 1-2 | Phase 1: MW-tercile positive control training + evaluation | G1: MW d > 0.5? | condgen |
| | 1 | Phase 2: Begin KLIFS/KinCoRe annotation for EGFR | -- | kinchembio |
| | 1 | Phase 2-PAR: Begin ABL1 dataset construction | -- | kinchembio |
| **W1** | 3-5 | Phase 2: Complete EGFR annotation + state classifier | G2-data: Classifier acc > 60%? | kinchembio |
| | 3-5 | Phase 1 (if MW failed): Phase 2-ALT shortcut removal | -- | mldebug |
| **W2** | 6-10 | Phase 2: Finalize EGFR training set with proper labels | -- | kinchembio |
| | 6-10 | Phase 2-PAR: Continue ABL1 curation | -- | kinchembio |
| | 8-10 | Begin paper writing (intro, methods, investigation sections) | -- | pubstrat |
| **W3** | 11-15 | Phase 3: Retrain EGFR VAE, 10 seeds (array job) | -- | condgen/mldebug |
| | 11-15 | Phase 3: Monitor training (Checkpoint A: per-state loss, probes) | -- | mldebug |
| **W4** | 16-18 | Phase 3: Post-training diagnostics (Checkpoint B) | G2b: d > 0.3? | mldebug |
| | 16-18 | Phase 3-ALT (if G2b < 0.3 and D1 < 45%): Architecture fix | -- | condgen |
| | 16-20 | Phase 5: Begin ABL1 VAE training (if dataset ready) | -- | condgen |
| **W5** | 21-25 | Phase 4: Multi-pocket docking on retrained EGFR models | G2c: Delta d > 0.3? | evaldes |
| | 21-25 | Phase 5: ABL1 training + evaluation | G2-ABL1: d > 0.3? | condgen/evaldes |
| **W6** | 26-30 | Compile all results. Update paper draft with results sections. | -- | pubstrat |
| | 26-30 | Phase 4 on ABL1 (multi-pocket docking if ABL1 trained) | -- | evaldes |
| **W7-8** | 31-40 | Finalize manuscript. Internal review. | -- | all |
| **W8-9** | -- | **ChemRxiv preprint submission** | -- | pubstrat |
| **W10-14** | -- | Journal submission (JCIM or appropriate venue per outcome matrix) | -- | pubstrat |

---

## 7. Risk Register

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Diagnostics contradict H2 | 5-10% | HIGH: Invalidates recovery plan | Investigate curated-compound dominance in latent space. Re-assess. | mldebug |
| MW-tercile control fails | 10-15% | MEDIUM: Architecture needs fixing before data fix | Escalate to shortcut removal -> FiLM -> adaLN-Zero ladder | condgen |
| KLIFS annotation covers <40% of compounds | 30-40% | MEDIUM: Insufficient coverage for retraining | Use classifier trained on KLIFS-labeled subset to predict rest. Accept lower confidence. | kinchembio |
| EGFR state classifier ~50% (no chemical distinction) | 25-35% | HIGH: EGFR fundamentally unsuitable | Pivot to ABL1 as primary kinase. EGFR becomes negative control. | kinchembio |
| Fixed labels + same architecture still d < 0.3 | 25-30% | MEDIUM: H1 confirmed as compounding factor | Apply Phase 3-ALT (architecture fix ladder). | condgen/mldebug |
| ABL1 also shows null result | 15-20% | HIGH: Thesis may be false | Publish rigorous negative result (Framing B+E). Still publishable. | pubstrat |
| Scooping by Volkamer group or PocketXMol team | 15-20% (6 months) | HIGH: Priority loss | Accelerate to preprint. Diagnostic journey framing is unique. | pubstrat |

---

## 8. Success Criteria

### 8.1 Minimum Viable Outcome

The minimum outcome that justifies the recovery effort is **one of:**
- EGFR retrained with proper labels shows d > 0.3 (PIVOT or better)
- ABL1 shows d > 0.3 with state conditioning
- MW-tercile positive control demonstrates the mechanism works, providing the
  architecture validation even if EGFR biology limits the thesis

Any of these produces a publishable JCIM paper with the diagnostic journey framing.

### 8.2 Best-Case Outcome

- EGFR: d > 0.5 after data fix (GO)
- ABL1: d > 0.5 with genuine DFGin/DFGout distinction
- Multi-pocket Delta Score confirms pocket-preference (diagonal > 50%)
- Two-kinase comparison shows conditioning scales with biological distinctness

This produces a Nature Computational Science candidate.

### 8.3 Worst-Case Outcome (Still Publishable)

- EGFR: d < 0.15 even after data fix and architecture upgrade
- ABL1: d < 0.15 despite genuine chemotype distinction
- Thesis conclusively negative

This produces a J Cheminformatics full article with:
- Pre-registered negative result
- Systematic diagnostic investigation of three failure modes
- Evaluation protocol contribution (Conformational Delta Score)
- False alarm analysis (d=0.71 on 3 seeds -> null on 10 seeds)

Expected citations: 30-60. This is the floor, not zero.

---

## 9. Immediate Next Steps

The following actions should be taken immediately (Day 1):

1. **Write and submit the diagnostic battery script** (Phase 0). This is 1 GPU-hour
   and 2 CPU-hours. Submit to `gpu_devel` and `day` partitions.

2. **Write and submit the MW-tercile positive control** (Phase 1). Relabel training
   data with MW terciles, train 1 seed. Submit to `gpu` partition.

3. **Begin KLIFS API queries** for EGFR structural annotations (Phase 2). This is
   CPU-only scripting work.

4. **Begin ChEMBL queries** for ABL1 bioactivity data (Phase 2-PAR). This is
   CPU-only scripting work.

5. **Start writing the paper introduction and methods sections.** These do not depend
   on experimental results.

All 5 actions are independent and can proceed in parallel.

---

## Appendix A: Key Input Documents

| Document | Path | Purpose |
|----------|------|---------|
| G2 Report | `reports/gate-g2-ablation-c-report.md` | Primary failure analysis |
| Pre-registration | `docs/pre-registration.md` | Thresholds and commitments |
| Implementation Plan | `IdeationDept/ReviewCohort/output/final/implementation-plan.md` | Original G2 design |
| Project Briefing | `IdeationDept/context/project-briefing.md` | Full project context |
| VAE Code | `src/statebind/ml/transformer_vae.py` | Conditioning mechanism |
| Scoring Code | `src/statebind/ranking/scoring.py` | Evaluation weights |
| 10-seed Results | `artifacts/evaluation/ablation_c_results_v3_10seed.json` | Raw data |

## Appendix B: Round 2 Agent Proposals

| Agent | File | Key Contribution |
|-------|------|-----------------|
| condgen | `output/proposals/condgen-prop-R02.md` | Scaffold overlap pre-check, one-variable-at-a-time retraining, conditioning ladder |
| kinchembio | `output/proposals/kinchembio-prop-R02.md` | KLIFS/KinCoRe annotation protocol, EGFR 2-class reduction, ABL1 curation plan |
| evaldes | `output/proposals/evaldes-prop-R02.md` | Negative control baseline, multi-pocket protocol, Delta Score framework |
| mldebug | `output/proposals/mldebug-prop-R02.md` | Diagnostic triage (4/7 retained), loss-curve diagnostic, monitoring protocol, shortcut fix ladder |
| pubstrat | `output/proposals/pubstrat-prop-R02.md` | Framing F (diagnostic journey), outcome matrix, citation analysis, parallel ABL1 recommendation |

## Appendix C: Round 1 Investigation Reports

| Agent | File | Key Finding |
|-------|------|-------------|
| condgen | `output/investigation/condgen-inv-R01.md` | Prefix tokens are weakest mechanism; DiT showed 1.8x worse FID vs adaLN-Zero |
| kinchembio | `output/investigation/kinchembio-inv-R01.md` | **SMOKING GUN:** `rng.choice()` in `prepare_vae_data.py` assigns random labels |
| evaldes | `output/investigation/evaldes-inv-R01.md` | Three structural evaluation flaws: zeroed state_specificity, fixed pocket, type I references |
| mldebug | `output/investigation/mldebug-inv-R01.md` | Information shortcut: decoder receives state directly, encoder ignores it |
| pubstrat | `output/investigation/pubstrat-inv-R01.md` | 5 narrative framings, all outcomes publishable, ChemRxiv in 4-6 weeks |
| Synthesis | `output/investigation/round01-synthesis.md` | H2=70-80% root cause, H1=15-25% compounding, H3=15-25% compounding |
