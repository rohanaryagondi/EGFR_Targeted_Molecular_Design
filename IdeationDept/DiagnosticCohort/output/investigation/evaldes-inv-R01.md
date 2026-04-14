---
agent: Evaluation Design Expert
round: 1
date: 2026-04-14
type: research-note
---

# Investigation Report: H3 -- Was the Evaluation Structurally Unable to Detect the Conditioning Signal?

## 1. Executive Summary

The Gate G2 ablation returned a definitive NO_GO (Cohen's d = 0.059), but the
evaluation protocol contains three structural flaws that render it incapable of
detecting the very signal the thesis claims to produce. This report argues that
**H3 is the most probable root cause** (estimated probability: 55-65%) and that
the evaluation must be re-run with a state-matched docking protocol before any
conclusions about the thesis can be drawn.

The current evaluation asks: "Does knowing the conformational state help you make
generically good EGFR molecules?" The thesis asks: "Does knowing the conformational
state help you make molecules that are good FOR THAT SPECIFIC CONFORMATION?" These
are fundamentally different questions, and the G2 ablation tests only the former.

**Key recommendation:** Run a multi-pocket docking evaluation (20,400 GNINA runs,
~4-8 GPU-hours on H200) as the cheapest and most informative diagnostic. This can
be done in <1 day and definitively resolves whether H3 explains the null result.

---

## 2. The Three Structural Flaws in the G2 Evaluation

### 2.1 Flaw 1: state_specificity = 0 Removes the Thesis-Relevant Signal

The unified scoring function allocates 15% weight to `state_specificity`, which
measures whether a molecule is unique to its conditioned state. For the ablation,
this was forced to 0 for both arms by passing an empty `state_smiles_map`.

**Why this matters:** The `state_specificity` component (lines 193-234 of
`ranking/scoring.py`) rewards molecules that appear in only one state's generation
pool. If conditioning works, conditioned molecules should be MORE state-specific
than unconditioned ones. By zeroing this component, the evaluation removes the one
scoring dimension where conditioning could demonstrate its value.

**The fairness argument is flawed:** The rationale was that zeroing
`state_specificity` ensures "scoring fairness" since unconditioned molecules cannot
have state specificity. But this is equivalent to testing whether a compass helps
you navigate and then blindfolding the navigator -- you have ensured "visual
fairness" by removing the very channel through which the tool operates.

**The correct design:** Run the evaluation TWICE:
1. With `state_specificity = 0` (the existing test -- tests generic quality)
2. With `state_specificity` enabled for conditioned arm, using actual
   `state_smiles_map` (tests thesis-relevant quality)

The difference between these two evaluations is itself informative: if the
conditioned arm gains substantially when `state_specificity` is re-enabled, it
means conditioning IS producing state-specific molecules, even if they are not
generically "better."

### 2.2 Flaw 2: Fixed 1M17 Pocket Cannot Detect Multi-State Benefit

The `docking_proxy` component (weight 0.20) uses a cascading fallback that
ultimately docks against a fixed 1M17 pocket (DFGin/aCin). From `scoring.py`
lines 63-64:

```python
receptor_info = get_receptor_for_state("DFGin_aCin")
```

This means ALL molecules -- regardless of which state they were conditioned on --
are scored against the same DFGin/aCin pocket. A molecule conditioned on
DFGout_aCin that would dock excellently in the 3W2R pocket receives zero credit.
A molecule conditioned on DFGin_aCout that perfectly fits the 2GS7 pocket is
evaluated only against 1M17.

**The structural consequence:** 20% of the scoring signal is locked to a single
conformational state. For the 2/3 of conditioned molecules generated for non-DFGin
states, the docking score is actively misleading -- it measures fit to the WRONG
pocket.

**Why this biases AGAINST conditioning:** If conditioning works, it should produce:
- DFGin/aCin molecules that dock well in 1M17 (detected)
- DFGin/aCout molecules that dock well in 2GS7 (NOT detected)
- DFGout/aCin molecules that dock well in 3W2R (NOT detected)

Only 1/3 of the conditioning signal can be detected. The other 2/3 is invisible.

### 2.3 Flaw 3: Reference Similarity to Type I Drugs Penalizes State-Specific Generation

The `reference_similarity` component (weight 0.35 -- the LARGEST component) measures
Tanimoto similarity to erlotinib and gefitinib (lines 57-62 of `baselines/scoring.py`):

```python
_REFERENCE_BINDERS = [
    "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",  # Erlotinib
    "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",  # Gefitinib
]
```

Both erlotinib and gefitinib are **Type I inhibitors** that bind the DFGin/aCin
(active) conformation. Erlotinib has been crystallographically confirmed to bind
BOTH active and inactive EGFR conformations with similar affinity (Park et al.,
2012; PDB 4HJO shows erlotinib in the inactive state at 2.75 A resolution), but
its 4-anilinoquinazoline scaffold is characteristic of Type I binding.

**The bias:** If state conditioning successfully generates DFGout-specific scaffolds
(e.g., type II pharmacophores with amide/urea linkers and hydrophobic back-pocket
extensions, as documented by Lategahn et al., 2025, and Fang et al., 2014), these
molecules would have LOW similarity to erlotinib/gefitinib -- and would be PENALIZED
by the dominant scoring component.

The reference binder set structurally encodes a preference for DFGin chemistry.
A conditioned model that correctly generates DFGout scaffolds would score WORSE
on the 35%-weighted reference_similarity component, offsetting any gains from
docking or other components.

---

## 3. How Published Papers Evaluate Pocket-Conditioned Generation

### 3.1 Standard Evaluation Metrics in SBDD

The structure-based drug design (SBDD) literature has converged on a standard
evaluation protocol for pocket-conditioned generation. Based on extensive literature
review, the key metrics are:

**Binding affinity metrics:**
- Vina score (AutoDock Vina / GNINA) -- docked against the CONDITIONING pocket
- CNN affinity score (GNINA-specific)
- Top-10% Vina score (focuses on best generated molecules)

**Molecular quality metrics:**
- QED (quantitative estimate of drug-likeness)
- SA score (synthetic accessibility)
- Validity rate (fraction of valid SMILES)
- Diversity (internal Tanimoto diversity)

**Specificity metrics (emerging, critical for multi-pocket):**
- Delta Score (Gao et al., 2024) -- measures specificity to target pocket
- Cross-pocket docking preference matrix

### 3.2 DiffSBDD Evaluation Protocol

DiffSBDD (Schneuing et al., Nature Computational Science, 2024) evaluates
pocket-conditioned generation by:

1. Generating ~100 molecules per pocket from the CrossDocked2020 test set
2. Docking generated molecules BACK INTO THE CONDITIONING POCKET using AutoDock Vina
3. Reporting Vina score, QED, SA, and diversity
4. Comparing against ground-truth co-crystallized ligands

Critically, DiffSBDD docks molecules against the pocket they were conditioned on --
NOT against a fixed reference pocket. This is the fundamental design choice that
the G2 evaluation gets wrong.

### 3.3 The Delta Score: Measuring Pocket Specificity

Gao et al. (ICML 2024, "Rethinking Specificity in SBDD") introduced the Delta
Score to address a critical evaluation bias. Their key finding:

> "Out of 20 molecules with high docking scores against their targets, only 2 had
> the highest score for their true targets."

The Delta Score is defined as:

```
DeltaScore(p_i) = E[S(x_ij, p_i)] - E[S(x_ij, p_k)]  where k != i
```

This measures the DIFFERENCE between a molecule's affinity for its intended pocket
versus its affinity for random other pockets. Standard Vina scores miss this
entirely -- a molecule can score well against its target pocket while scoring
equally well (or better) against unrelated pockets.

**Relevance to StateBind:** The Delta Score framework is directly applicable.
For conditioned molecules, we should measure:

```
DeltaScore(state_i) = VinaDock(mol, pocket_i) - mean(VinaDock(mol, pocket_j))
                      where j != i
```

If conditioning works, the Delta Score should be significantly NEGATIVE (lower =
better in Vina convention) for conditioned molecules compared to unconditioned
molecules.

### 3.4 Multi-State Docking in Kinase Evaluation

Eguida and Schmidtke (Scientific Reports, 2024, "Improving docking and virtual
screening performance using AlphaFold2 multi-state modeling for kinases") provide
directly relevant methodology:

- They evaluated docking across 25 kinase targets from DUD-E
- Used multiple conformational states per kinase
- Found ensemble docking (multiple states) improved EF1% by 24% vs single state
  (8.2 vs 6.6)
- For diverse inhibitor sets (dissimilarity >= 0.7): EF1% improved from 4.6 to 6.4
- Used both AutoDock Best (ADB) and Boltzmann-weighted (BW) ensemble scores

Their key finding: **multi-state evaluation is essential for discovering chemically
diverse inhibitors.** Single-conformation evaluation systematically underestimates
the quality of diverse molecular sets -- exactly the bias present in the G2
evaluation.

### 3.5 Cross-Docking Benchmarks for Kinases

Backenkoehler et al. (JCIM, 2023, "Benchmarking Cross-Docking Strategies for
Structure-Informed Machine Learning in Kinase Drug Discovery") performed ~40,000
cross-docking runs across 589 kinase structures:

- Success rate with random structure selection: 33% (Posit method)
- Success rate with 20 structures: 83% -- docking into multiple conformations
  dramatically improved performance
- Larger conformational changes (DFGout vs DFGin) showed 96.9% conformation
  identification accuracy via Posit probability scores

This demonstrates that cross-docking between conformational states is both
technically feasible and diagnostically powerful for identifying conformation-
specific binding.

---

## 4. Proper Evaluation Design: The Multi-Pocket Docking Protocol

### 4.1 Overview

The proper evaluation requires docking EVERY generated molecule against ALL 3
conformational state pockets, then comparing whether conditioned molecules
preferentially dock well against their conditioning pocket.

**Existing infrastructure (confirmed):**

All 3 receptor structures are ALREADY PREPARED in the StateBind pipeline:
```
data/processed/docking/receptors/
    1m17.pdbqt    + 1m17_box.json    (DFGin/aCin)
    2gs7.pdbqt    + 2gs7_box.json    (DFGin/aCout)
    3w2r.pdbqt    + 3w2r_box.json    (DFGout/aCin)
```

The GNINA docking wrapper (`chemistry/docking.py`) already supports:
- Arbitrary receptor PDBQT input
- Per-receptor box center/size configuration
- Batch docking with parallelization (`dock_batch`, line 475)
- Result parsing with Vina score, CNN score, CNN affinity

### 4.2 Step-by-Step Protocol

**Step 1: Collect all generated SMILES**

Extract the ~6,800 SMILES from the 10-seed ablation (both conditioned and
unconditioned arms). For each molecule, record:
- SMILES string
- Source arm (conditioned / unconditioned)
- Conditioning state (DFGin_aCin / DFGin_aCout / DFGout_aCin / "none" for uncond)
- Seed ID

**Step 2: Multi-pocket docking (20,400 runs)**

For each of the ~6,800 molecules, dock against all 3 pockets:
- 1M17 (DFGin/aCin)
- 2GS7 (DFGin/aCout)
- 3W2R (DFGout/aCin)

This produces a 6,800 x 3 Vina score matrix.

**Step 3: Construct the pocket-preference matrix**

For each conditioned molecule, identify its "best pocket" (lowest Vina score).
Build a 3x3 confusion matrix:

```
                    Best-scoring pocket
                   1M17    2GS7    3W2R
Conditioned on:
  DFGin_aCin       [a]     [b]     [c]
  DFGin_aCout      [d]     [e]     [f]
  DFGout_aCin      [g]     [h]     [i]
```

**If conditioning works:** The diagonal (a, e, i) should dominate. Molecules
conditioned on DFGout_aCin should preferentially dock best in 3W2R.

**If conditioning has no effect:** The matrix should be approximately uniform
or dominated by whichever pocket is generically easiest to dock into.

**Step 4: Compute state-matched vs state-mismatched scores**

For conditioned molecules:
- `matched_score` = Vina score against the CONDITIONING pocket
- `mismatched_score` = mean Vina score against OTHER pockets

The key test statistic: `delta = matched_score - mismatched_score`

For unconditioned molecules, assign pseudo-states equally and compute the same
delta as a null baseline.

Cohen's d on `delta(conditioned) vs delta(unconditioned)` is the thesis-relevant
effect size.

**Step 5: Per-state enrichment analysis**

For each state separately, compute EF@10 using only the pocket-matched Vina
score. Compare conditioned vs unconditioned enrichment within each state.

**Step 6: Scaffold analysis**

For each pocket's top-scoring molecules, analyze Murcko scaffolds. Check whether:
- DFGin/aCin top molecules show 4-anilinoquinazoline scaffolds (Type I)
- DFGout/aCin top molecules show different scaffolds (Type II features:
  amide/urea linkers, hydrophobic tail groups)

### 4.3 Statistical Analysis

The multi-pocket evaluation produces several testable quantities:

1. **Primary:** Cohen's d on state-matched delta scores (conditioned vs uncond)
2. **Secondary:** Chi-squared test on the 3x3 pocket-preference matrix
   (H0: uniform distribution; H1: diagonal dominance)
3. **Tertiary:** Per-state paired t-test on EF@10 (conditioned vs uncond, n=10)
4. **Exploratory:** Scaffold diversity analysis per pocket

Pre-register success thresholds for the multi-pocket evaluation:
- STRONG GO: Cohen's d >= 0.8 on matched delta scores
- GO: d in [0.5, 0.8)
- PIVOT: d in [0.3, 0.5)
- NO-GO: d < 0.3 (confirms that conditioning truly provides no benefit, even
  when evaluated correctly)

---

## 5. What Would We Expect IF Conditioning Works But the Metric Is Blind?

### 5.1 Quantitative Predictions Under H3

If H3 is the root cause -- i.e., the conditioning mechanism works but the
evaluation misses it -- we would predict:

**In the current evaluation (G2):**
- Cohen's d ~ 0 on composite scores (OBSERVED: d = 0.059) -- consistent with H3
- No component shows d > 0.2 (OBSERVED: max d = 0.060) -- consistent with H3
- 5/10 seeds won by each arm (OBSERVED: exactly 5/5) -- consistent with H3
- Reference_similarity similar between arms (OBSERVED: 0.268 vs 0.260) --
  consistent with H3 (both arms generate similar Type I scaffolds for the
  reference_similarity component)

**In the multi-pocket evaluation (predicted):**
- Cohen's d >= 0.3-0.8 on state-matched delta scores
- Pocket-preference matrix shows diagonal enrichment (chi-squared p < 0.05)
- DFGout-conditioned molecules show 15-30% better Vina scores against 3W2R
  than against 1M17
- The magnitude depends on how strongly the conditioning mechanism operates,
  which intersects with H1

### 5.2 Signal Strength Estimation

The expected effect size depends on how much pocket-specific information the
conditioning mechanism conveys. Given:

- Centroid distances: 0.26-0.42 (weak but nonzero separation, ~6-10% of latent
  space scale)
- The model generates known EGFR drug scaffolds (erlotinib, gefitinib,
  osimertinib, lazertinib)
- 64/64 active latent dimensions (model is not collapsed)

A rough estimate: if conditioning produces even a 10% shift toward the correct
pocket's chemical preferences, and that pocket preference translates to a 1-2
kcal/mol differential in Vina scores, the normalized delta score difference
would be:

- Vina difference: 1-2 kcal/mol
- Sigmoid-normalized difference: ~0.05-0.10 (via normalize_vina_score with scale=3.0)
- SD of Vina scores across drug-like molecules: typically ~1.5-2.5 kcal/mol
- Expected Cohen's d on raw Vina delta: ~0.4-1.0

This puts the expected effect size in the GO to STRONG GO range, IF the
conditioning mechanism is working at the latent space level.

### 5.3 What If the Multi-Pocket Evaluation Also Shows d ~ 0?

If the multi-pocket evaluation confirms no effect, then H3 is eliminated and the
diagnosis shifts to H1 (weak conditioning) or H2 (uninformative data). This is
still a valuable result because:

1. It eliminates evaluation design as a confounder
2. It narrows the investigation to mechanism/data issues
3. It provides publishable evidence that the evaluation was properly designed

---

## 6. The EGFR Conformation-Chemistry Relationship

### 6.1 Do Different EGFR Conformations Prefer Different Chemistry?

This is a critical question because if all three EGFR states prefer the same
chemical matter, then state conditioning cannot produce state-specific molecules
(supporting H2 over H3). The literature provides a nuanced answer:

**Strong evidence for conformation-chemistry differences:**

**Type I vs Type II kinase inhibitors** represent fundamentally different binding
modes with distinct pharmacophores (Fang et al., ACS Chemical Biology, 2014):

- Type I (DFGin): Heterocyclic hinge-binder (e.g., 4-anilinoquinazoline),
  compact, forms 1-3 hydrogen bonds with hinge
- Type II (DFGout): Extended scaffold with amide/urea linker accessing the
  allosteric back pocket created by DFG flip, plus hinge-binding moiety

The pharmacophore model for Type II inhibitors has four distinct regions
(Fang et al., 2014):
1. Hinge-binding moiety (shared with Type I)
2. Flexible 3-5 bond linker traversing gatekeeper residue
3. Hydrogen-bonding moiety (amide/urea to C-helix and DFG motif)
4. Hydrophobic tail in the DFG-out pocket

**Complicating evidence for EGFR specifically:**

Park et al. (Biochemistry, 2012) showed that erlotinib binds BOTH active and
inactive EGFR conformations with similar affinity (Glide scores: -9.34 vs
-9.72 kcal/mol). PDB 4HJO confirms erlotinib in the inactive EGFR state at
2.75 A resolution. This suggests EGFR may be unusually promiscuous in its
ligand-conformation relationships.

However, lapatinib provides the counter-example: it binds specifically to the
inactive (DFGin/aCout) conformation with a slow off-rate, driven by a pendant
furan ring at the 6-position of the quinazoline core that inserts into a
hydrophobic pocket specific to the inactive state (Wood et al., Cancer Research,
2004; PDB 1XKK at 2.4 A). The 2GS7 structure (used as the DFGin/aCout
representative in StateBind) shows the Src-like inactive conformation with
the aC-helix displaced.

For the DFGout/aCin state, Lategahn et al. (JACS, 2025) describe trisubstituted
imidazole scaffolds with meta-aniline linkers and fluorinated phenyl back-pocket
groups that show sub-10 nM activity on the L858R/T790M mutant. These scaffolds
are structurally distinct from Type I 4-anilinoquinazolines.

**Assessment:** There IS genuine chemical diversity across EGFR conformational
states, but EGFR is less conformation-selective than other kinases (e.g., ABL,
where imatinib shows strong DFGout preference). The signal exists but may be
weaker than for a kinase with clearer conformation-chemistry separation.

### 6.2 Representative Structure Considerations

The three representative structures used in StateBind have important properties:

| Structure | State | Ligand | Mutations | Resolution |
|-----------|-------|--------|-----------|------------|
| 1M17 | DFGin/aCin | Erlotinib | Wild-type | 2.6 A |
| 2GS7 | DFGin/aCout | AMP-PNP | None | Not specified |
| 3W2R | DFGout/aCin | Compound 4 | T790M/L858R | Not specified |

The 2GS7 structure contains AMP-PNP (a non-hydrolyzable ATP analog), not a
drug-like ligand. This represents the Src-like inactive state. The 3W2R
structure carries the T790M/L858R double mutation, which alters the pocket
relative to wild-type EGFR. These structural differences will produce
conformation-specific docking preferences independent of the conditioning
mechanism, making them useful as a diagnostic.

---

## 7. The state_specificity Component: Include, Exclude, or Both?

### 7.1 The Dual-Evaluation Design

The correct approach is to run the evaluation TWICE:

**Evaluation A (Generic Quality -- existing G2 design):**
- `state_specificity = 0` for both arms
- Tests: "Does conditioning improve generic EGFR drug quality?"
- Result: NO_GO (d = 0.059) -- already established

**Evaluation B (Thesis-Relevant Quality -- new):**
- `state_specificity` enabled for conditioned arm (use actual `state_smiles_map`)
- `state_specificity = 0` for unconditioned arm (no states to be specific to)
- Tests: "Does conditioning produce molecules that are state-specific AND high-quality?"
- Expected result under H3: d >= 0.3

**Evaluation C (Multi-Pocket Docking -- new, primary diagnostic):**
- Replace fixed 1M17 docking with pocket-matched docking
- Score each molecule against its conditioning pocket (or all 3 pockets)
- Tests: "Does conditioning produce molecules that fit their target pocket better?"
- Expected result under H3: d >= 0.5

### 7.2 Why Evaluation C Is More Important Than Evaluation B

Evaluation B re-enables `state_specificity`, which measures whether a molecule
appears in only one state's generation pool. This is a necessary but not sufficient
condition -- a molecule could be state-specific (generated only for one state) but
not actually BETTER for that state's pocket.

Evaluation C directly tests pocket fit, which is the thesis claim. A molecule that
docks well against its conditioning pocket IS a success for state conditioning,
regardless of whether it also appears in other states' generation pools.

### 7.3 Recommended Implementation Order

1. **Evaluation C first** (multi-pocket docking) -- most informative, uses
   existing GNINA infrastructure, ~4-8 GPU-hours
2. **Evaluation B second** (re-enable state_specificity) -- cheap, requires only
   re-scoring existing molecules with modified weights
3. Compare results: If C shows a signal but B does not, the conditioning produces
   pocket-fit but not generation-exclusivity

---

## 8. Quick Diagnostic: Achievable in <1 Day

### 8.1 The 100-Molecule Pilot

Before committing to 20,400 GNINA runs, run a pilot with a small subset:

**Step 1: Sample 100 molecules (30 min)**
- Randomly select ~33 molecules from each conditioning state (DFGin/aCin,
  DFGin/aCout, DFGout/aCin)
- Select ~33 unconditioned molecules as control
- Use molecules from seed 42 (first seed)

**Step 2: Dock all 100 against all 3 pockets (1-3 hours)**
- 100 molecules x 3 pockets = 300 GNINA runs
- At ~30 seconds/molecule (GNINA 1.3, exhaustiveness=8, GPU): ~2.5 hours on CPU
  or ~30 minutes with GPU
- At exhaustiveness=4 (as used in the scoring cascade): ~1.5 hours on CPU

**Step 3: Construct the pilot pocket-preference matrix (15 min)**
- Build the 3x3 matrix from the 33 conditioned molecules
- Compute the diagonal dominance ratio
- If diagonal > 50%: strong evidence for H3
- If diagonal ~ 33%: evidence against H3 (conditioning has no pocket preference)

**Step 4: Compute pilot delta scores (15 min)**
- For each conditioned molecule: matched - mismatched Vina score
- For unconditioned molecules: assign pseudo-states, compute the same
- Quick t-test on delta scores

**Total time: 3-4 hours including analysis**

### 8.2 Even Faster: The Scaffold Fingerprint Diagnostic (30 min)

Without any docking, check whether conditioned molecules from different states
have different chemical properties:

1. Extract Murcko scaffolds for all ~6,800 molecules
2. For each state's conditioned molecules, compute the scaffold distribution
3. Compare scaffold distributions across states using Jensen-Shannon divergence
4. If JS divergence > 0 between states: conditioning IS producing state-specific
   chemistry (evidence for H3 -- the evaluation just cannot see it)
5. If JS divergence ~ 0: conditioning is NOT producing state-specific chemistry
   (evidence for H1/H2)

This test requires only RDKit (no docking) and can be done in <30 minutes.

### 8.3 The Property Fingerprint Diagnostic (30 min)

Compute basic molecular descriptors for each state's molecules:
- Molecular weight distribution
- LogP distribution
- Number of rotatable bonds (Type II inhibitors typically have more)
- Number of hydrogen bond donors/acceptors

If conditioned DFGout molecules show systematically different property
distributions (higher MW, more rotatable bonds, more HBDs for the amide/urea
linker), this is evidence that conditioning works at the chemical level.

---

## 9. Compute Cost Estimation for the Full Multi-Pocket Evaluation

### 9.1 GNINA Docking Throughput

Based on published benchmarks (McNutt et al., Journal of Cheminformatics, 2025):

- GNINA 1.3 default ensemble: ~30 sec/molecule on CPU, ~23 sec with fast model
- GNINA 1.3 with GPU (CNN rescore): approximately same wall time as CPU with
  marginal GPU overhead for the CNN component
- Knowledge-distilled fast model: ~16 sec/molecule on CPU
- At exhaustiveness=4 (as used in StateBind's scoring cascade): ~50-60% of
  exhaustiveness=8 cost, so ~10-18 sec/molecule

### 9.2 Total Run Estimates

**Full evaluation (20,400 runs):**

| Configuration | Time/mol | Total wall time | GPU-hours |
|---------------|----------|-----------------|-----------|
| Exh=8, CPU, 4 workers | 30s | ~42 hours | 0 |
| Exh=4, CPU, 4 workers | 18s | ~25 hours | 0 |
| Exh=8, CPU, 8 workers | 30s | ~21 hours | 0 |
| Exh=4, GPU rescore | 16s | ~5.5 hours | ~5.5 |

**Recommended: 3 SLURM array jobs**

Split by pocket (one job per receptor):
- Job 1: 6,800 mols x 1M17 (DFGin/aCin)
- Job 2: 6,800 mols x 2GS7 (DFGin/aCout)
- Job 3: 6,800 mols x 3W2R (DFGout/aCin)

Each job: ~6,800 molecules at 16-30 sec each = 1.8 - 3.4 hours per job.

**SLURM configuration per job:**
```bash
#SBATCH --job-name=multipocket_dock
#SBATCH -p gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=rtx_5000_ada:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH -t 06:00:00
```

With all 3 jobs running in parallel: **total wall time ~4-6 hours.**

**Pilot evaluation (300 runs):**
- 300 molecules at 20 sec = ~1.5 hours
- Single SLURM job, no GPU needed
- Can run on `devel` partition for fastest turnaround

### 9.3 Storage Requirements

Each GNINA output SDF: ~5-50 KB. Total for 20,400 runs: ~100 MB - 1 GB.
Box configs and scores: negligible. Well within home directory quotas;
scratch storage at `/nfs/roberts/scratch/pi_mg269/rag88/` available if needed.

---

## 10. The Pocket-Preference Matrix: Detailed Design

### 10.1 Matrix Construction

For each molecule `m` conditioned on state `s`:
1. Dock `m` against all 3 pockets: get Vina scores `V(m, 1M17)`, `V(m, 2GS7)`,
   `V(m, 3W2R)`
2. Identify best pocket: `best(m) = argmin_p V(m, p)` (most negative = best)
3. Increment matrix cell `[s, best(m)]`

**Expected matrix under H3 (conditioning works, evaluation misses it):**

```
                         Best pocket
                    1M17      2GS7      3W2R
Conditioned on:
  DFGin_aCin      [60%]      20%       20%
  DFGin_aCout      20%      [55%]      25%
  DFGout_aCin      15%       25%      [60%]
```

Diagonal dominance of ~55-60% (vs 33% expected under null).

**Expected matrix under null (conditioning has no effect):**

```
                         Best pocket
                    1M17      2GS7      3W2R
Conditioned on:
  DFGin_aCin       45%       30%       25%
  DFGin_aCout      43%       32%       25%
  DFGout_aCin      44%       31%       25%
```

Rows approximately identical; 1M17 may dominate because it is the most commonly
studied pocket (and molecules may be biased toward Type I scaffolds due to
training data composition).

### 10.2 Statistical Test

Chi-squared test of independence on the 3x3 matrix:
- H0: Conditioning state and best pocket are independent
- H1: Conditioning state and best pocket are associated (diagonal enrichment)
- df = (3-1)(3-1) = 4
- Power: With ~2,200 conditioned molecules per state and ~3,400 unconditioned,
  even modest diagonal enrichment (5-10% above uniform) should be detectable at
  p < 0.001

### 10.3 Effect Size for the Matrix

Cramer's V from the chi-squared statistic:
- V ~ 0: no association (conditioning has no effect on pocket preference)
- V ~ 0.1: small effect
- V ~ 0.3: medium effect
- V ~ 0.5+: large effect (strong pocket-conditioning association)

### 10.4 Augmented Matrix: Unconditioned Baseline

Build the same matrix for unconditioned molecules by assigning random pseudo-states:

```
                         Best pocket
                    1M17      2GS7      3W2R
Pseudo-state:
  "DFGin_aCin"     44%       31%       25%
  "DFGin_aCout"    45%       30%       25%
  "DFGout_aCin"    43%       32%       25%
```

This should show NO diagonal enrichment (Cramer's V ~ 0). The DIFFERENCE in
Cramer's V between conditioned and unconditioned matrices quantifies the
conditioning signal.

---

## 11. Analysis of Evaluation Biases in Molecular Generation Literature

### 11.1 The "Specification Game" in Molecular Generation Evaluation

Recent work has identified systematic biases in how molecular generation models
are evaluated:

**Gao et al. (ICML 2024):** Demonstrated that ~30% of randomly selected molecules
from a molecular library outperform reference ligands in standard Vina docking
scores. This means high Vina scores do NOT reliably indicate good drug candidates
-- and an evaluation relying solely on Vina scores against a single pocket can be
easily "gamed" by generating molecules that happen to have favorable electrostatic
profiles.

**MolGenBench (Chen et al., bioRxiv 2025):** Found that "individual actives may not
represent the full spectrum of functional interaction modes" -- evaluation using
a limited set of reference compounds or a single pocket biases the assessment
toward one chemical series.

**RediscMol benchmark (JCIM, 2024):** Showed that "findings from the RediscMol
benchmark differ from previous evaluations" -- different evaluation approaches
yield conflicting conclusions about the same model. This directly supports the
concern that the G2 evaluation's conclusion may not generalize to a properly
designed evaluation.

### 11.2 The Sensitivity-Power Tradeoff in BEDROC

Truchon and Bayly (JCIM, 2007) established the foundational metrics for virtual
screening evaluation. Key insight: there is a "seesaw effect" -- overemphasizing
early recognition (high alpha in BEDROC) reduces the statistical power to detect
true early enrichment.

The G2 evaluation uses BEDROC(alpha=20), which strongly emphasizes the top-ranked
molecules. With the current scoring biased toward Type I chemistry, BEDROC will
preferentially reward generation of erlotinib/gefitinib-like molecules. Any
diversification toward Type II chemistry (which H3 predicts conditioning should
produce for DFGout states) would be penalized.

### 11.3 The PMO Framework and Oracle Budget

The PMO benchmark (Gao et al., NeurIPS 2022) emphasizes a key principle:
**evaluation must use the same oracle that the model was optimized for.** In
StateBind, the conditioned model was trained with state labels but evaluated
with a state-blind scoring oracle. This is analogous to training a model on
Task A and evaluating it on Task B -- a mismatch that systematically
underestimates the model's true performance on Task A.

---

## 12. Assessment: Probability That H3 Is the Root Cause

### 12.1 Evidence FOR H3

1. **Structural analysis of the evaluation confirms 3 independent biases** that
   all push AGAINST detecting the conditioning signal (Sections 2.1-2.3)
2. **The G2 report itself acknowledges** (Section 6.2): "the ablation was
   structurally unable to detect the conditioning signal even if it existed"
3. **Published SBDD evaluation protocols** (DiffSBDD, TargetDiff, Pocket2Mol) all
   dock against the CONDITIONING pocket, not a fixed reference
4. **The Delta Score literature** shows that standard docking scores miss
   pocket-specificity in ~90% of cases (18/20 molecules, Gao et al., 2024)
5. **Ensemble docking literature** shows 24% improvement in EF1% when using
   multiple conformations vs single conformation (Eguida & Schmidtke, 2024)
6. **The reference binder set** (erlotinib, gefitinib -- both Type I) creates a
   35%-weighted bias toward DFGin chemistry
7. **Observed results are consistent** with H3 predictions: d ~ 0 on generic
   quality, 5/5 seed split, no component advantage

### 12.2 Evidence AGAINST H3

1. **Centroid distances are small** (0.26-0.42, ~6-10% of latent space scale) --
   conditioning may genuinely be weak (supporting H1)
2. **The model generates the same scaffolds regardless of state** (erlotinib,
   gefitinib, osimertinib, lazertinib appear in all states) -- suggesting the
   conditioning signal is not producing state-specific chemistry (supporting H2)
3. **EGFR may be unusually conformation-promiscuous** -- erlotinib binds both
   active and inactive with similar affinity (Park et al., 2012), so there may
   be less conformation-specific chemistry to discover than for other kinases

### 12.3 Probability Estimate

| Hypothesis | Probability | Rationale |
|------------|-------------|-----------|
| H3 (wrong evaluation) | **55-65%** | Three independent evaluation biases, all confirmed by literature precedent. Cheapest to test and eliminate. |
| H1 (weak conditioning) | 25-30% | Centroid distances are small. Prefix-token mechanism may be too weak for the Transformer to use. But H1 and H3 are not mutually exclusive -- even a weak conditioning signal would be invisible under the current evaluation. |
| H2 (uninformative data) | 10-20% | The 8,109 EGFR molecules may not span enough chemical diversity across states. But lapatinib (DFGin/aCout) and the Lategahn imidazoles (DFGout/aCin) prove distinct EGFR chemistry exists, so there IS some signal in the data. |

**Critical point:** H1, H2, and H3 are NOT mutually exclusive. The most likely
scenario is a combination: a moderately weak conditioning signal (H1 contributes)
applied to partially informative data (H2 contributes) evaluated with a
structurally blind metric (H3 contributes). The multi-pocket evaluation
disentangles H3 from H1/H2.

---

## 13. Decision Tree: What to Do Next

### 13.1 Immediate Actions (Week 1)

```
Day 1: Run scaffold fingerprint diagnostic (30 min)
       |
       +-- If JS divergence > 0.05 between states:
       |   Conditioning IS producing different chemistry.
       |   Strong evidence for H3. Proceed to multi-pocket docking.
       |
       +-- If JS divergence ~ 0:
           Conditioning is NOT producing different chemistry.
           H1/H2 more likely. Still run multi-pocket docking
           (to rule out H3), but invest more in H1/H2 investigation.

Day 1-2: Run 100-molecule pilot docking (3-4 hours)
         |
         +-- If diagonal > 40% in pocket-preference matrix:
         |   Evidence for H3. Run full 20,400-dock evaluation.
         |
         +-- If diagonal ~ 33%:
             H3 less likely. But small sample -- full evaluation
             still recommended for statistical power.

Day 2-3: Run full multi-pocket evaluation (4-8 GPU-hours)
         3 SLURM array jobs in parallel
```

### 13.2 Interpretation Gates

```
Full multi-pocket evaluation result:
|
+-- Cohen's d >= 0.5 on matched delta scores:
|   H3 CONFIRMED. Re-frame the project.
|   Publication: "State conditioning improves pocket-specific molecular
|   generation" (positive result, proper evaluation).
|   The original G2 NO_GO was a false negative due to evaluation design.
|
+-- Cohen's d in [0.2, 0.5):
|   H3 PARTIALLY CONFIRMED. Conditioning has a weak pocket effect.
|   Investigate H1 (stronger conditioning mechanism) while publishing
|   the evaluation design insight.
|
+-- Cohen's d < 0.2:
    H3 ELIMINATED. The evaluation design was not the problem.
    Focus on H1 (architecture) and H2 (data).
    The negative result on multi-pocket evaluation is itself publishable:
    "Even with proper multi-pocket evaluation, state conditioning shows
    no benefit for EGFR."
```

---

## 14. Comments on H1 and H2

### 14.1 H1: Weak Conditioning Mechanism

Even under H3, the conditioning signal appears weak (centroid distances 0.26-0.42).
The multi-pocket evaluation may reveal a small but real pocket preference, which
could be amplified by stronger conditioning:
- Cross-attention from learned state embeddings
- Separate decoder heads per state
- Adversarial state prediction from latent space (forces latent space to encode state)
- FiLM conditioning (Feature-wise Linear Modulation)

If multi-pocket evaluation shows d = 0.3 (weak), stronger conditioning might push
it to d = 0.8+ (strong).

### 14.2 H2: Insufficient State-Specific Data

The training data composition is critical. If 90% of the 8,109 molecules bind
DFGin/aCin and only 5% each bind the other states, the model has very little
state-specific chemistry to learn. The multi-pocket evaluation can indirectly
test this: if DFGin_aCin-conditioned molecules show pocket preference but
DFGout_aCin-conditioned molecules do not, H2 is likely for the minority states.

---

## 15. Conclusion: The Evaluation Must Be Fixed Before Declaring the Thesis Dead

The Gate G2 NO_GO is premature. The evaluation tested whether state conditioning
improves generic EGFR drug quality -- it did not test the thesis claim that state
conditioning improves state-specific molecular design.

Three structural flaws -- zeroed state_specificity, fixed 1M17 docking, and Type I
reference binders -- collectively ensure that any state-conditioning signal is
invisible to the evaluation. Published literature on SBDD evaluation (DiffSBDD,
Delta Score, multi-state docking) confirms that pocket-matched evaluation is the
standard approach.

The recommended multi-pocket docking evaluation is cheap (~4-8 GPU-hours), uses
existing GNINA infrastructure (all 3 receptors are already prepared), and
definitively resolves whether H3 explains the null result. It should be run
before any conclusions about the thesis are drawn.

If the multi-pocket evaluation confirms the null (d < 0.2), the thesis is
genuinely challenged and the focus shifts to H1/H2 or a negative-result
publication. If it reveals a pocket-preference signal (d >= 0.3), the project
has a clear positive-result publication path and the original G2 evaluation
design becomes an instructive methodological cautionary tale.

---

## References

1. Schneuing, A. et al. (2024). Structure-based drug design with equivariant
   diffusion models. *Nature Computational Science*, 4, 84-93.

2. Gao, W. et al. (2024). Rethinking Specificity in SBDD: Leveraging Delta
   Score and Energy-Guided Diffusion. *ICML 2024*, Proceedings of the 41st
   International Conference on Machine Learning.

3. Gao, W. et al. (2022). Sample Efficiency Matters: A Benchmark for
   Practical Molecular Optimization. *NeurIPS 2022 Datasets and Benchmarks*.

4. Park, J. H. et al. (2012). Erlotinib binds both inactive and active
   conformations of the EGFR tyrosine kinase domain. *Biochemical Journal*,
   448(3), 417-423. PDB: 4HJO.

5. Wood, E. R. et al. (2004). A unique structure for epidermal growth factor
   receptor bound to GW572016 (Lapatinib): Relationships among protein
   conformation, inhibitor off-rate, and receptor activity in tumor cells.
   *Cancer Research*, 64(18), 6652-6659. PDB: 1XKK.

6. Fang, Z. et al. (2014). Exploration of Type II Binding Mode: A Privileged
   Approach for Kinase Inhibitor Focused Drug Discovery? *ACS Chemical Biology*,
   9(6), 1271-1281.

7. Eguida, M. & Schmidtke, P. (2024). Improving docking and virtual screening
   performance using AlphaFold2 multi-state modeling for kinases. *Scientific
   Reports*, 14, 24498.

8. Backenkoehler, M. et al. (2023). Benchmarking Cross-Docking Strategies for
   Structure-Informed Machine Learning in Kinase Drug Discovery. *Journal of
   Chemical Information and Modeling*, 63(19), 6005-6013.

9. McNutt, A. T. et al. (2025). GNINA 1.3: the next increment in molecular
   docking with deep learning. *Journal of Cheminformatics*, 17, 22.

10. McNutt, A. T. et al. (2021). GNINA 1.0: Molecular docking with deep
    learning. *Journal of Cheminformatics*, 13, 43.

11. Truchon, J.-F. & Bayly, C. I. (2007). Evaluating Virtual Screening Methods:
    Good and Bad Metrics for the "Early Recognition" Problem. *Journal of
    Chemical Information and Modeling*, 47(2), 488-508.

12. Su, M. et al. (2019). Comparative Assessment of Scoring Functions: The
    CASF-2016 Update. *Journal of Chemical Information and Modeling*, 59(2),
    895-913.

13. Lategahn, J. et al. (2025). Structure-Activity Relationships of Inactive-
    Conformation Binding EGFR Inhibitors: Linking the ATP and Allosteric Pockets.
    *Angewandte Chemie International Edition*, 64(26).

14. Peng, X. et al. (2026). Unified modeling of 3D molecular generation via
    atomic interactions with PocketXMol. *Cell*, 189(1), 1-15.

15. Zhao, S. et al. (2024). A dual diffusion model enables 3D molecule generation
    and lead optimization based on target pockets. *Nature Communications*, 15,
    2654.

16. Chen, Y. et al. (2025). Benchmarking Real-World Applicability of Molecular
    Generative Models. *bioRxiv*, 2025.11.03.686215.

17. Weisberg, E. et al. (2005). Characterization of AMN107, a selective
    inhibitor of native and mutant Bcr-Abl. *Cancer Cell*, 7(2), 129-141.

18. Brooijmans, N. & Kuntz, I. D. (2003). Molecular recognition and docking
    algorithms. *Annual Review of Biophysics and Biomolecular Structure*, 32,
    335-373.

19. Cross, J. B. et al. (2009). Comparison of several molecular docking
    programs: pose prediction and virtual screening accuracy. *Journal of
    Chemical Information and Modeling*, 49(6), 1455-1474.

20. Sliwoski, G. et al. (2014). Computational methods in drug discovery.
    *Pharmacological Reviews*, 66(1), 334-395.

21. Zhao, H. & Bhatt, D. (2024). RediscMol: Benchmarking Molecular Generation
    Models in Biological Properties. *Journal of Medicinal Chemistry*, 67(3),
    1898-1910.

22. Jain, A. N. (2009). Effects of protein conformation in docking: improved
    pose prediction through protein pocket adaptation. *Journal of Computer-
    Aided Molecular Design*, 23(6), 355-374.

23. Wierbowski, S. D. et al. (2020). Cross-docking benchmark for automated
    pose and ranking prediction of ligand binding. *Protein Science*, 29(1),
    298-305.

24. Volkamer, A. et al. (2012). Analyzing the Topology of Active Sites: On
    the Prediction of Pockets and Subpockets. *Journal of Chemical Information
    and Modeling*, 52(2), 360-372.

25. Gao, W. et al. (2023). Delta Score: Improving the Binding Assessment of
    Structure-Based Drug Design Methods. *arXiv:2311.12035*.
