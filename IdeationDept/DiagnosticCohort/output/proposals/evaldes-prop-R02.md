---
agent: Evaluation Design Expert
round: 2
date: 2026-04-14
type: proposal
---

# Evaluation Design Proposals: Revised After Random-Label Discovery

## 1. Reassessment Given the Random-Label Root Cause

My Round 1 assessment placed H3 (wrong evaluation metric) at 55-65% probability.
The discovery that `prepare_vae_data.py` assigns state labels via `rng.choice()`
for the vast majority of the 8,109 training molecules fundamentally changes the
evaluation design calculus.

**The mechanism:** In `_fetch_chembl_api()` (line 499), `inhibitor_type` is always
passed as `""` (empty string), which never matches any key in `_assign_state_from_type()`
(line 526), so every molecule falls through to `rng.choice(_VALID_STATES)`. In
`_load_chembl_local()` (line 434), the `inhibitor_type` field is read from the JSON
but ChEMBL activity records do not typically include this field, producing the same
fallback. Only the 55-molecule curated set (Tier 3) has correct state assignments.

**What this means for evaluation:** The model was trained on noise labels. No
evaluation protocol -- no matter how sophisticated -- can detect a conditioning
signal that was never learned. My three structural evaluation flaws (zeroed
state_specificity, fixed 1M17 pocket, Type I reference bias) are real, but they
are invisible behind the label problem. They could not have caused the null result
because the null result was caused upstream.

**Revised probability assessment:**
- H2 (random labels / no data signal): **75%** -- ROOT CAUSE
- H1 (weak conditioning mechanism): **15%** -- compounding factor, testable only after H2 is fixed
- H3 (wrong evaluation metric): **10%** -- real but masked; becomes relevant only after H2 and potentially H1 are addressed

---

## 2. Top 3 Proposals

### Proposal 1: Scaffold Overlap Diagnostic on Current Models (Negative Control)

**Rationale:** Before spending GPU hours on multi-pocket docking, confirm from the
evaluation side that random labels produce no pocket preference. This serves as a
negative control that validates the random-label diagnosis and establishes the
baseline against which fixed-label models will be compared.

**Protocol:**

**Step A: Scaffold divergence test (30 min, CPU only)**

Extract Murcko scaffolds from all ~6,800 generated molecules. Group conditioned
molecules by their conditioning state. Compute pairwise Jensen-Shannon divergence
on scaffold frequency distributions across the 3 states.

- If JS divergence ~ 0 between states: confirms random labels produce no chemical
  differentiation (expected result -- validates H2 diagnosis)
- If JS divergence > 0: surprising -- would suggest the prefix tokens found some
  signal despite noise labels (would require investigation)

**Step B: Property distribution test (30 min, CPU only)**

Compute MW, LogP, HBA, HBD, rotatable bonds, and ring count distributions for each
state's conditioned molecules. Two-sample Kolmogorov-Smirnov test between each pair
of states. Under random labels, all 3 property distributions should be
indistinguishable (KS p > 0.05 for all pairs).

**Step C: 100-molecule pilot docking (2-3 hours, 1 GPU)**

Sample ~33 molecules from each conditioning state plus ~33 unconditioned controls.
Dock all 132 molecules against all 3 pockets (396 GNINA runs). Construct the 3x3
pocket-preference matrix.

Expected result under random labels: matrix approximately uniform (diagonal ~ 33%).
This establishes the null-distribution baseline for the pocket-preference matrix
that we will compare against after retraining with proper labels.

**Step D: Document the negative control**

The negative control is itself a publication-quality result. It demonstrates that:
(a) the evaluation protocol CAN detect pocket preference if it exists, and (b) random
labels produce no pocket preference, confirming the diagnostic. This addresses a
potential reviewer objection: "maybe the evaluation is also broken, and you are
attributing the null to labels when the evaluation is the problem."

**Effort:** 3-4 hours total (CPU + 1 GPU job). No code changes required -- all
analyses use existing RDKit and GNINA infrastructure.

**Timeline:** Can be completed in 1 day. Should be run BEFORE retraining with
proper labels, as it provides the null baseline.

**Expected outcome:** Confirmation that current models show no pocket preference
(d ~ 0 on delta scores, diagonal ~ 33% on preference matrix). This is the
evaluation-side evidence for H2.

---

### Proposal 2: Multi-Pocket Evaluation Protocol for Retrained Models

**Rationale:** Once proper state labels are assigned (via KLIFS structural
annotations, as proposed by kinchembio) and the VAE is retrained, the evaluation
must actually test the thesis. My Round 1 design for multi-pocket docking remains
the correct evaluation protocol -- it just needs to be applied to properly-trained
models, not the current random-label models.

**The full evaluation has three tiers, run in sequence:**

**Tier 1: Pocket-Preference Matrix (primary, 4-8 GPU-hours)**

Dock all generated molecules against all 3 pocket conformers:
- 1M17 (DFGin/aCin) -- already prepared: `data/processed/docking/receptors/1m17.pdbqt`
- 2GS7 (DFGin/aCout) -- already prepared: `2gs7.pdbqt`
- 3W2R (DFGout/aCin) -- already prepared: `3w2r.pdbqt`

For each molecule, construct the Vina score vector [V_1M17, V_2GS7, V_3W2R].

Primary test statistic: **State-Matched Delta Score**
```
delta(mol_i) = Vina(mol_i, pocket_cond) - mean(Vina(mol_i, pocket_other))
```
Cohen's d comparing delta(conditioned) vs delta(unconditioned) is the thesis-relevant
effect size. Pre-register thresholds: d >= 0.5 = GO, d >= 0.3 = PIVOT, d < 0.3 = NO-GO.

Secondary test: Chi-squared on the 3x3 pocket-preference matrix (H0: uniform row
distribution; H1: diagonal dominance). Report Cramer's V as effect size.

**Tier 2: Dual-Evaluation with state_specificity (1 hour, CPU only)**

Re-score all molecules twice:
- Evaluation A: `state_specificity = 0` (replicates G2 design)
- Evaluation B: `state_specificity` enabled with actual `state_smiles_map`

The difference d_B - d_A measures the contribution of generation exclusivity to
the overall effect. If d_B >> d_A, conditioning produces molecules unique to their
target state. If d_B ~ d_A, conditioning does not produce state-exclusive molecules
even if it produces pocket-preferring molecules.

**Tier 3: Reference binder expansion (2 hours, CPU only)**

Expand the reference binder set beyond erlotinib/gefitinib to include state-
representative compounds:
- DFGin/aCin: erlotinib, gefitinib (existing) + osimertinib
- DFGin/aCout: lapatinib (PDB 1XKK, slow off-rate from inactive conformation)
- DFGout/aCin: a Type II EGFR inhibitor if one exists with confirmed DFGout binding

Compute reference_similarity against both the original (Type I only) and expanded
(multi-state) reference sets. If conditioned DFGout molecules show higher similarity
to Type II references, this is orthogonal evidence for state-specific generation.

**Implementation via SLURM:**

3 array jobs (one per receptor), each docking ~N molecules (N = number of unique
generated SMILES after retraining). Use `--gpus=rtx_5000_ada:1` on the `gpu`
partition, `-A pi_mg269`, with 4 CPUs and 16G memory per job.

```
#SBATCH --array=0-2
#SBATCH -p gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=rtx_5000_ada:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
```

**Effort:** 4-8 GPU-hours for Tier 1, 1-2 CPU-hours for Tiers 2-3. Total: 1-2
days including analysis.

**Timeline:** Run immediately after the first retrained model completes (should
follow the retraining step, which depends on KLIFS label assignment).

**Expected outcome under correct labels + working conditioning:**
- Delta Score Cohen's d >= 0.3 (PIVOT or better)
- Pocket-preference matrix diagonal > 50% (chi-squared p < 0.05)
- DFGout-conditioned molecules show 1-2 kcal/mol better Vina scores against 3W2R
  than against 1M17

**Expected outcome under correct labels + broken conditioning (H1):**
- Delta Score Cohen's d < 0.3 (same as random-label result)
- Pocket-preference matrix uniform (diagonal ~ 33%)
- This outcome would confirm H1 as the remaining problem

---

### Proposal 3: Delta Score Framework as Standalone Publication Contribution

**Rationale:** Regardless of whether StateBind's conditioning succeeds or fails,
the evaluation methodology itself is a contribution. The pocket-preference matrix
and state-matched Delta Score adapted for multi-conformation kinase evaluation
do not currently exist as a standardized protocol. Gao et al. (ICML 2024) introduced
the Delta Score for cross-target specificity, but no one has applied it to
intra-target conformational specificity.

**The contribution:**

Define a standardized evaluation protocol for state-conditioned molecular generation:

1. **The Pocket-Preference Matrix:** A 3x3 (or NxN for N conformational states)
   contingency table showing which pocket each conditioned molecule scores best
   against. Accompanied by chi-squared test and Cramer's V effect size.

2. **The Conformational Delta Score:** Adaptation of Gao et al.'s Delta Score to
   intra-target conformational specificity:
   ```
   ConfDelta(mol, state_i) = Dock(mol, pocket_i) - (1/(N-1)) * sum_j(Dock(mol, pocket_j))
   ```
   Where j ranges over all states except i. Lower (more negative) is better in
   Vina convention.

3. **The Dual-Evaluation Protocol:** Run every state-conditioned evaluation twice
   (with and without state_specificity) to disentangle generation exclusivity from
   pocket fit quality.

4. **Benchmark Baselines:**
   - Random-label negative control (from Proposal 1)
   - Unconditioned model (existing G2 data)
   - Properly-conditioned model (after retraining)
   - Positive control: known Type I vs Type II inhibitors docked against all pockets

**Why this is publishable independently:**

The field of structure-based drug design is rapidly adopting pocket-conditioned
generation (DiffSBDD, TargetDiff, PocketXMol), but evaluation protocols are
inconsistent. Most papers report only Vina score against the conditioning pocket
without testing cross-pocket specificity. A standardized evaluation protocol with
the Conformational Delta Score, pocket-preference matrix, and dual-evaluation
design would be immediately useful to the community.

**Target venue:** JCIM (methods/evaluation focus) or a workshop paper at NeurIPS
(ML for Drug Discovery).

**Effort:** The framework itself is developed through the analysis in Proposals 1
and 2. The standalone contribution requires writing up the methodology, running the
positive control (known inhibitors docked against all 3 EGFR pockets), and
comparing against the Gao et al. Delta Score.

**Timeline:** 1-2 weeks for the full benchmark, overlapping with the retraining
timeline.

---

## 3. Response to Other Agents' Findings

### 3.1 Response to kinchembio: ABL1 Evaluation Protocol

kinchembio proposes ABL1 as a positive control kinase because it has genuine DFGin/DFGout
chemical distinction (imatinib = Type II, dasatinib = Type I). I strongly support
this and provide the evaluation protocol:

**ABL1 pocket structures for evaluation:**

| State | PDB ID | Ligand | Resolution | Notes |
|-------|--------|--------|------------|-------|
| DFGin (active) | 2GQG | Dasatinib | 2.4 A | Type I binding mode |
| DFGout (inactive) | 1IEP | Imatinib | 2.1 A | Type II with DFG flip |

These two structures represent the clearest conformational distinction among all
kinase systems. The binding pockets differ dramatically:
- 1IEP (DFGout): large hydrophobic back pocket accessible only when DFG is out
- 2GQG (DFGin): compact ATP-competitive pocket, DFG loop blocks back pocket

**ABL1 evaluation uses the same protocol as EGFR (Proposal 2):**
- Dock all ABL1-generated molecules against both DFGin and DFGout pockets
- Construct 2x2 pocket-preference matrix
- Compute Conformational Delta Score
- Compare conditioned vs unconditioned

**Key advantage:** ABL1 is a stronger positive control because Type I and Type II
ABL inhibitors are structurally much more distinct than EGFR inhibitors. If
conditioning fails on ABL1, the architecture is definitively broken (H1 confirmed).
If conditioning works on ABL1 but not EGFR, the problem is EGFR-specific data (H2
partially confirmed -- EGFR may not have enough conformation-chemistry separation).

### 3.2 Response to condgen: MW-Tercile Positive Control

condgen proposes a positive control using molecular weight terciles instead of
conformational states. This is an evaluation-relevant idea:

**How to evaluate the MW-tercile positive control:**
- Train a 3-class conditioned model on {low MW, medium MW, high MW}
- Generate 200 molecules per class
- Measure: mean MW per conditioned class vs unconditioned
- The Delta Score analog: MW(mol) - median_MW(conditioned_class)
- Cohen's d on this difference should be large (d > 1.0) if the prefix-token
  mechanism works at all

This is a pure architecture test that removes biology entirely. If d ~ 0 on the
MW-tercile control, the prefix-token mechanism is provably unable to convey
conditioning information regardless of data quality.

**Evaluation effort:** Minimal -- compute MW for all generated molecules and compare
distributions. No docking required.

### 3.3 Response to mldebug: 7-Diagnostic Battery

mldebug proposes 7 diagnostics including conditional generation fidelity (generate
per-state, check property distributions) and latent space analysis. From the
evaluation perspective:

**Which diagnostics are informative on current (random-label) models:**
- Latent space analysis: YES -- can confirm centroids are near-identical (expected)
- Conditional generation fidelity: YES -- can confirm no property shift per state
- Reconstruction accuracy: NOT informative for conditioning (tests general model quality)

**Which require retrained models:**
- All docking-based diagnostics
- Pocket-preference matrix
- Delta Score analysis

---

## 4. Quick Diagnostic on Current Models: What Is Still Informative?

Despite random labels, two evaluation-side diagnostics ARE informative on the
current models:

### 4.1 Confirming Unconditioned = Conditioned (Evaluation-Side H2 Evidence)

Compare the distributions of generated molecules from each conditioning state.
Under random labels, ALL three state-conditioned generation pools should be
statistically indistinguishable from each other AND from the unconditioned pool.

**Test:** For all 10 seeds, compute per-state distributions of:
- MW, LogP, QED, SA, number of aromatic rings, rotatable bonds
- Murcko scaffold frequencies
- Morgan fingerprint centroids

Run pairwise two-sample KS tests. Under H2 (random labels), expect p > 0.1 for
all comparisons. If any comparison shows p < 0.01, the conditioning mechanism
found SOME signal despite noise -- which would be surprising and worth investigating.

**Effort:** 1 hour, CPU only. Uses existing generated molecules.

### 4.2 Null-Distribution Baseline for Future Comparison

The 100-molecule pilot docking from Proposal 1 (Step C) establishes the null
distribution for the pocket-preference matrix. Record:
- Diagonal fraction under random labels
- Delta Score distribution under random labels
- Mean and SD of Vina scores per pocket

These become the statistical baselines against which retrained models are compared.
Without this null baseline, we cannot quantify the improvement from proper labels.

---

## 5. The Evaluation Cascade: Ordered Decision Tree

**Phase 0: Negative control on current models (Proposal 1)**
- Effort: 3-4 hours
- Decision: If current models show NO pocket preference -> proceed (expected)
  If current models show pocket preference -> investigate (unexpected, important)

**Phase 1: Fix labels (kinchembio's KLIFS assignment)**
- Effort: 2-4 hours
- Decision: Are >50% of molecules assigned to states from structural data?
  If yes -> proceed to retraining
  If no -> need alternative data strategy

**Phase 2: MW-tercile positive control (condgen's proposal)**
- Effort: 4 GPU-hours training + 30 min evaluation
- Decision: If d > 1.0 on MW difference -> prefix tokens CAN condition, proceed
  If d < 0.3 -> prefix tokens broken, need architecture change (H1 confirmed)

**Phase 3: Retrain with proper EGFR labels**
- Effort: 10-20 GPU-hours (10 seeds, conditioned + unconditioned)
- Decision: Proceed to Phase 4

**Phase 4: Multi-pocket evaluation (Proposal 2)**
- Effort: 4-8 GPU-hours docking + analysis
- Decision:
  - d >= 0.5 on Delta Score -> GO (thesis supported)
  - d in [0.3, 0.5) -> PIVOT (weak signal, may need architecture upgrade)
  - d < 0.3 -> If MW-tercile worked, the problem is EGFR biology (H2 residual)
               If MW-tercile also failed, the problem is architecture (H1)

**Phase 5: ABL1 validation (if EGFR shows signal)**
- Effort: 4-8 GPU-hours training + 4-8 GPU-hours docking
- Decision: ABL1 signal should be STRONGER than EGFR
  If ABL1 d > EGFR d -> confirms state-conditioning scales with biology
  If ABL1 d < EGFR d -> unexpected, investigate

**Total timeline:** 2-3 weeks for the full cascade, with go/no-go decisions at
each phase.

---

## 6. Summary

| Proposal | Action | Effort | When | Primary Value |
|----------|--------|--------|------|---------------|
| 1 | Scaffold + pilot docking negative control | 3-4 hrs | Immediately | Null baseline + H2 confirmation |
| 2 | Multi-pocket evaluation protocol (post-retraining) | 4-8 GPU-hrs | After retraining | Thesis-relevant test |
| 3 | Delta Score framework as standalone contribution | 1-2 weeks | Overlapping | Publication-ready methodology |

**My revised probability assessment:**
- H2 (random labels): **75%** -- fix labels first, everything else is secondary
- H1 (weak conditioning): **15%** -- testable via MW-tercile control
- H3 (wrong evaluation): **10%** -- real but masked; becomes the key question only
  after H2 is resolved and H1 is ruled out

The evaluation flaws I identified in Round 1 are genuine design problems that WILL
need to be addressed. But they are not the cause of the current null result -- random
labels are. The priority is: fix labels, confirm the architecture works (MW-tercile),
then deploy the multi-pocket evaluation to test the actual thesis.

---

## References

- Gao, W., et al. (2024). "Rethinking Specificity in SBDD." ICML 2024.
- Schneuing, A., et al. (2024). "Structure-based drug design with equivariant diffusion models." Nature Computational Science.
- Eguida, M. & Schmidtke, P. (2024). "Improving docking and virtual screening performance using AlphaFold2 multi-state modeling for kinases." Scientific Reports.
- Backenkoehler, M., et al. (2023). "Benchmarking Cross-Docking Strategies for Structure-Informed ML in Kinase Drug Discovery." JCIM.
- Park, J.H., et al. (2012). "Erlotinib binds both inactive and active conformations of the EGFR tyrosine kinase domain." Biochemistry.
- Fang, Z., et al. (2014). "Discovery of inter-domain stabilizers -- a novel assay system for allosteric akt inhibitors." ACS Chemical Biology.
- Lategahn, J., et al. (2025). "Trisubstituted imidazoles as EGFR inhibitors." JACS.
- Wood, E.R., et al. (2004). "A unique structure for epidermal growth factor receptor bound to GW572016 (Lapatinib)." Cancer Research.
- McNutt, A.T., et al. (2025). "GNINA 1.3: Fast and accurate molecular docking with deep learning." Journal of Cheminformatics.
