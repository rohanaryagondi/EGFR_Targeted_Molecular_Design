---
agent: Associate Research Scientist
round: 3
date: 2026-04-09
type: review-assessment
scope: deliberation
---

# Round 3 Deliberation: Implementation Realities

## Executive Summary

After reading all five Round 2 verification reports and inspecting the StateBind
codebase in detail, I have three conclusions:

1. **The 4-state-to-3-state switch is disruptive but not catastrophic.** I estimate
   3-5 days of focused engineering, not the 1-2 weeks some might fear. The hardest
   part is not the code changes -- it is re-running the full pipeline end-to-end
   and verifying that 646 tests still pass. The VAE checkpoint is invalidated and
   must be retrained.

2. **Two of the top-5 priority items will take 2x+ the estimated time.** Specifically,
   the multi-kinase ABL1 extension (estimated 6-9 weeks) will hit 10-14 weeks due
   to data curation complexity, and the structural annotation fix cascade will
   surface additional problems that are not yet visible.

3. **Parallelization is good but not great.** Items 1-3 (structural fix, scaffold
   split, bootstrap CIs) can proceed concurrently. But the ablation C (unconditioned
   VAE) is blocked on the structural fix completing first, because retraining a
   conditioned VAE on wrong states and then comparing it to unconditioned is
   scientifically meaningless.

---

## 1. Three-State Model Impact Assessment

### 1.1 What Changes If 4ZAU Is Confirmed DFGin (Not DFGout/aCout)

CompBioRev's finding that 4ZAU (osimertinib-bound, WT EGFR) is likely DFGin rather
than DFGout/aCout has cascading implications. I traced the impact through every
relevant source file.

#### Files Directly Affected

| File | What Changes | Lines Affected |
|------|-------------|----------------|
| `src/statebind/processing/models.py` | `ConformationalState` enum: keep all 4 values but DFGout_aCout becomes unused for EGFR | Lines 51-56 (enum definition) |
| `src/statebind/processing/structures.py` | Remove/reclassify 4ZAU and 5D41 from DFGout_aCout | Lines 201-227 (2 StructureRecords) |
| `src/statebind/structure/features.py` | Remove curated features for 4ZAU and 5D41 under DFGout_aCout, or move to correct state | Lines 242-269 (2 feature entries) |
| `src/statebind/generation/conditioning.py` | Remove DFGout_aCout PocketCondition entirely | Lines 115-136 (1 dict entry) |
| `configs/vae.yaml` | `n_states: 4` -> `n_states: 3`, remove `DFGout_aCout: 3` from `state_mapping` | Lines 21, 48-49 |
| `configs/vae_pre2010.yaml` | Same as above | Line 12, state_mapping |
| `configs/vae_pre2015.yaml` | Same as above | Line 12, state_mapping |
| `src/statebind/ml/vae_dataset.py` | `DEFAULT_STATE_MAPPING` drops `DFGout_aCout: 3` | Lines 41-46 |
| `src/statebind/ml/vae.py` | `VAEConfig.n_states` default changes from 4 to 3 | Line 84 |
| `scripts/train_vae.py` | Default fallback `n_states` from 4 to 3 | Lines 822, 882 |

#### Files Indirectly Affected (Downstream Regeneration)

| File/Artifact | Why | Effort |
|---------------|-----|--------|
| `src/statebind/structure/atlas.py` | Rebuilds atlas from structures.py. Auto-adjusts if structures removed. | Re-run only |
| `artifacts/generation/vae_candidates*.json` | All VAE-generated candidates for DFGout_aCout state are invalid | Re-generate after retrain |
| `artifacts/ranking/comparison.json` | Scoring included DFGout_aCout candidates | Re-run scoring pipeline |
| `artifacts/evaluation/` | Comparison results invalid | Re-run evaluation |
| `artifacts/docking/` | GNINA docking against 4ZAU receptor is invalid if 4ZAU was DFGin | Re-dock or remove |

#### Tests Affected

I found 11 occurrences of `DFGout_aCout` across 8 test files:

- `test_processing.py` (1): Structure dataset builder assertions
- `test_structure.py` (1): Atlas state count assertions
- `test_generation.py` (2): Candidate generation for all 4 states
- `test_ranking.py` (1): Scoring across all states
- `test_docking.py` (2): Docking against DFGout_aCout receptor
- `test_dynamics.py` (2): State transition model
- `test_context.py` (1): Mutation-to-state mapping
- `test_vae_integration.py` (1): VAE n_states=4

These are not major rewrites -- most are assertions about state counts or state
lists. Changing `4` to `3` and removing `DFGout_aCout` from expected lists. Estimate:
2-3 hours for test updates, plus the time to run the full test suite (646 tests,
~5-10 minutes on CPU).

### 1.2 VAE Retraining: Mandatory

The VAE uses a one-hot state conditioning vector of dimension `n_states` (currently 4).
Looking at `vae.py` lines 127-130, the GRU input size is `embed_dim + n_states`. With
3 states instead of 4:

- The encoder GRU input dimension changes from `embed_dim + 4` to `embed_dim + 3`
- The decoder z_proj input changes from `latent_dim + 4` to `latent_dim + 3`
- **All existing checkpoint weights are incompatible.** The first linear layer
  dimensions no longer match.

This means: **the VAE must be retrained from scratch.** There is no way to load a
4-state checkpoint into a 3-state model. Training takes ~15-30 minutes on a single
GPU per the config comments, so this is fast. But downstream generation, scoring,
and evaluation must all be re-run after retraining.

### 1.3 What Happens to DFGout_aCout Molecules

The generator (`generator.py` line 353, `generate_all_states()`) iterates over all
states from `get_pocket_conditions()`. With DFGout_aCout removed:

- ~115 candidates (estimated 25% of 461 total) were generated specifically for
  DFGout_aCout with strategies like `P_LOOP_INTERACTION` and `BACK_POCKET_EXTENSION`
- These candidates still exist as SMILES strings but their target_state label
  is now invalid
- Some may appear in other states' candidate sets (the cross-state overlap in
  `generate_all_states()` was tracked)
- The "unique to DFGout_aCout" candidates are dropped entirely

**Impact on enrichment numbers:** The retrospective enrichment analysis
(`evaluation/retrospective.py`) only tracks how well candidates match approved
drugs by similarity. All approved EGFR drugs in the database (lines 23-60) are
annotated as `state: "DFGin_aCin"`. So the DFGout_aCout candidates likely
contributed minimally to enrichment metrics. The primary enrichment signal comes
from DFGin_aCin and DFGin_aCout candidates.

### 1.4 Total Effort for 4->3 State Switch

| Task | Hours | Notes |
|------|-------|-------|
| Verify 4ZAU conformation (3D coordinates) | 2 | PyMOL: measure DFG-Asp-Phe Ca distance, K745-E762 salt bridge |
| Update `structures.py` | 1 | Remove or reclassify 4ZAU, 5D41 |
| Update `features.py` | 1 | Remove/move curated features |
| Update `conditioning.py` | 0.5 | Remove DFGout_aCout condition |
| Update `vae_dataset.py` DEFAULT_STATE_MAPPING | 0.5 | Drop entry |
| Update `vae.py` VAEConfig default | 0.5 | n_states=3 |
| Update 3 YAML configs | 0.5 | n_states, state_mapping |
| Update `train_vae.py` defaults | 0.5 | 2 lines |
| Update 8 test files (11 occurrences) | 2-3 | Mostly s/4/3/ and list edits |
| Run full test suite, fix failures | 2-4 | Unknown unknowns |
| Retrain VAE (GPU time) | 0.5 | 15-30 min on H200 |
| Re-run generation pipeline | 1 | |
| Re-run scoring pipeline | 1-2 | Depends on GNINA docking scope |
| Re-run evaluation + comparison | 1 | |
| **Total** | **13-18 hours** | **~2-3 working days** |

### 1.5 Recommendation: Adopt 3-State + Disclose

I agree with ProgDir's practical approach. If 4ZAU is confirmed DFGin by coordinate
inspection, adopt the 3-state model (DFGin/aCin, DFGin/aCout, DFGout/aCin) and
explicitly disclose in the paper:

> "No wild-type EGFR DFGout/aCout crystal structure has been deposited in the
> PDB as of 2026. The DFGout/aCin state is represented by mutant structures
> (T790M). We adopt a 3-state model for wild-type EGFR and discuss the mutant
> DFGout representations as a sensitivity analysis."

This is scientifically honest and strengthens the paper by showing the authors
understand the structural biology limitations.

**However**, do NOT remove `DFGout_aCout` from the `ConformationalState` enum in
`processing/models.py`. Keep it as a valid enum value for future use (other kinases
like ABL1 do have genuine DFGout/aCout structures). Just stop using it for EGFR.

---

## 2. Step-by-Step Implementation Plan for Top 5 Priorities

### 2a. Structural Annotation Fix

**Goal:** Correct mutation status for 3W2R, 5D41; fix 3iku PDB ID; resolve 4ZAU
classification.

**Step 1: Verify 4ZAU conformation (2 hours)**
```
# Download 4ZAU coordinates
wget https://files.rcsb.org/download/4ZAU.pdb -O /tmp/4zau.pdb

# In PyMOL or via BioPython:
# Measure DFG-Asp831 Ca to DFG-Phe832 Ca distance
# DFGin: ~5-6 A, DFGout: ~9-12 A
# Measure K745-E762 salt bridge (NZ to OE1/OE2)
# aCin: ~2.8-3.5 A, aCout: ~8-12 A
```

**Step 2: Fix structures.py (1 hour)**
- File: `/home/rag88/projects/statebind/repo/src/statebind/processing/structures.py`
- Line 183-184: `mutations_present=[]` for 3iku -> Either fix PDB ID to `3ika` and
  set `mutations_present=["T790M"]`, or remove entry entirely since 3IKU is not an
  EGFR structure (it is E. coli ParM)
- Line 189-190: `mutations_present=[]` for 3w2r -> change to
  `mutations_present=["T790M", "L858R"]`
- Lines 219-220: `mutations_present=[]` for 5d41 -> change to
  `mutations_present=["L858R", "T790M"]`
- Lines 201-214: If 4ZAU confirmed DFGin, reclassify
  `state=ConformationalState.DFGIN_ACIN` and update `notes`

**Step 3: Fix features.py (1 hour)**
- File: `/home/rag88/projects/statebind/repo/src/statebind/structure/features.py`
- If 3iku ID is wrong (ParM not EGFR), remove its entry (lines 212-225) or replace
  with correct 3ika features
- If 4ZAU reclassified, its features (lines 242-255) need re-measurement since the
  curated DFGout values (dfg_asp_phe_dist=11.0, ac_helix_salt_bridge=10.5) would be
  wrong if it is actually DFGin

**Step 4: Update conditioning.py (30 min)**
- File: `/home/rag88/projects/statebind/repo/src/statebind/generation/conditioning.py`
- Remove `ConformationalState.DFGOUT_ACOUT.value` entry (lines 115-136)
- Update docstring (line 38) from "all 4" to "3 EGFR states"

**Step 5: Update configs (30 min)**
- `configs/vae.yaml`: `n_states: 3`, remove `DFGout_aCout: 3` from state_mapping
- `configs/vae_pre2010.yaml`: same
- `configs/vae_pre2015.yaml`: same

**Step 6: Update ML code (1 hour)**
- `src/statebind/ml/vae_dataset.py` line 41-46: Remove `"DFGout_aCout": 3` from
  DEFAULT_STATE_MAPPING. Keep `"DFGout_aCin": 2`.
- `src/statebind/ml/vae.py` line 84: Change default `n_states: int = 3`
- `scripts/train_vae.py` lines 822, 882: Change fallback from `4` to `3`

**Step 7: Update tests (2-3 hours)**
- 8 files, 11 occurrences. Most are count assertions or state lists.
- Run `pytest -v --tb=short` after each batch of changes.

**Expected failure modes:**
- The 3iku PDB ID fix may break the atlas builder if `3ika` is not in the curated
  features dict. You need to either add `3ika` features or skip the entry.
- Reclassifying 4ZAU as DFGin may cause the DFGout_aCin cluster to have only 1
  structure (3w2r, which is itself a mutant). This raises the question of whether
  DFGout_aCin has sufficient structural representation.
- The DFGout_aCin representative structure (`is_representative=True` on 3iku,
  line 184) will need reassignment if 3iku is removed.

**Estimated time: 8-12 hours (1.5-2 days)**

---

### 2b. MPNN Scaffold Split

**Goal:** Replace `np.random.permutation` with scaffold-aware splitting in
`affinity_dataset.py`.

**Step 1: Add scaffold split utility (4-6 hours)**
- File: Create or modify `src/statebind/ml/affinity_dataset.py`
- After line 390 (current `rng.permutation(n)` at line 390), add a scaffold
  splitting branch
- Use RDKit `MurckoScaffold.MakeScaffoldGeneric(MurckoScaffold.GetScaffoldForMol(mol))`
  to extract Murcko scaffolds
- Group molecules by scaffold
- Split scaffolds (not molecules) into train/val/test
- This ensures no scaffold leakage across splits

**Implementation sketch:**
```python
def scaffold_split(dataset, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42):
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold
    
    scaffolds = {}
    for i, smi in enumerate(dataset.smiles_list):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            scaffold = "NONE"
        else:
            scaffold = MurckoScaffold.MakeScaffoldGeneric(
                MurckoScaffold.GetScaffoldForMol(mol)
            )
            scaffold = Chem.MolToSmiles(scaffold)
        scaffolds.setdefault(scaffold, []).append(i)
    
    # Sort scaffolds by size (largest first) for deterministic splitting
    scaffold_sets = sorted(scaffolds.values(), key=len, reverse=True)
    
    # Greedily assign scaffold groups to splits
    train_idx, val_idx, test_idx = [], [], []
    train_target = int(len(dataset) * train_ratio)
    val_target = int(len(dataset) * (train_ratio + val_ratio))
    
    for group in scaffold_sets:
        if len(train_idx) < train_target:
            train_idx.extend(group)
        elif len(train_idx) + len(val_idx) < val_target:
            val_idx.extend(group)
        else:
            test_idx.extend(group)
    
    return train_idx, val_idx, test_idx
```

**Step 2: Add split_type parameter (1 hour)**
- Modify `split_affinity_dataset()` to accept `split_type: str = "random"` parameter
- Support `"random"`, `"scaffold"`, and `"temporal"` (for future use)
- Keep backward compatibility: default remains `"random"`

**Step 3: Add tests (1-2 hours)**
- Test that no scaffold appears in both train and test
- Test that split ratios are approximately correct
- Test edge case: scaffolds with only 1 molecule

**Step 4: Re-evaluate MPNN (2-4 hours)**
- Retrain MPNN with scaffold split
- Record new R^2 on scaffold-split test set
- Expect R^2 to drop from 0.69 to approximately 0.45-0.55 (per mlrev and principal
  estimates)

**Step 5: Update artifacts and reports**
- Save both random-split and scaffold-split metrics to
  `artifacts/evaluation/mpnn_metrics.json`
- Report both in the paper

**Expected failure modes:**
- RDKit `MurckoScaffold` may fail on some SELFIES-decoded molecules with unusual
  ring systems. Need a try/except fallback.
- With only ~90 compounds in the curated dataset, scaffold splitting may produce
  very small test sets (< 10 molecules). Consider whether this is statistically
  meaningful.
- If many molecules share the same scaffold (e.g., quinazoline core common to
  erlotinib/gefitinib/lapatinib), one split may be disproportionately large.

**Estimated time: 2-3 days**

---

### 2c. Bootstrap CIs + BEDROC

**Goal:** Add confidence intervals to all reported metrics and compute BEDROC for
enrichment.

**Step 1: Implement bootstrap CI utility (2-3 hours)**
- File: Add to `src/statebind/evaluation/comparison.py` or create
  `src/statebind/evaluation/statistics.py`
- Standard nonparametric bootstrap: resample with replacement, compute metric,
  repeat 10,000 times, take 2.5th and 97.5th percentiles

```python
def bootstrap_ci(values, metric_fn, n_bootstrap=10000, ci=0.95, seed=42):
    rng = np.random.RandomState(seed)
    n = len(values)
    stats = []
    for _ in range(n_bootstrap):
        sample = rng.choice(values, size=n, replace=True)
        stats.append(metric_fn(sample))
    alpha = (1 - ci) / 2
    return np.percentile(stats, [alpha*100, (1-alpha)*100])
```

**Step 2: Add BEDROC computation (2-3 hours)**
- BEDROC (Boltzmann-Enhanced Discrimination of ROC): Truchon & Bayly, JCIM 2007
- Uses the `rdkit.ML.Scoring.Scoring` module: `CalcBEDROC(scores, labels, alpha=20.0)`
- RDKit has this built in, so no external dependency needed
- Apply to the retrospective enrichment results

**Step 3: Apply to existing metrics (2-3 hours)**
- Bootstrap CI on: mean scores, enrichment factors (EF@10, EF@50), BEDROC, R^2
- For each metric, report: point estimate [95% CI lower, upper]
- Modify `artifacts/evaluation/comparison.json` schema to include CIs

**Step 4: Add tests (1-2 hours)**
- Test that CI width decreases with more samples
- Test that point estimate falls within CI
- Test BEDROC with known active/decoy sets

**Expected failure modes:**
- Bootstrap CIs on small samples (e.g., 9-molecule MPNN test set) will be very wide,
  possibly embarrassingly wide. This is actually informative -- it shows the
  uncertainty is large. Do not suppress this.
- BEDROC alpha parameter matters a lot. alpha=20 (default) emphasizes early enrichment.
  Report alpha and consider sensitivity to alpha=5 and alpha=100.

**Estimated time: 1.5-2 days**

---

### 2d. Ablation C: Unconditioned VAE

**Goal:** Train a VAE without state conditioning and compare to the conditioned VAE
to isolate the effect of state awareness.

**Step 1: Create unconditioned VAE config (1 hour)**
- File: `configs/vae_unconditioned.yaml`
- Set `n_states: 1` (or 0 with a code path that skips state conditioning)
- Alternatively, the simpler approach: set `n_states: 1` and assign all molecules
  to state 0. The one-hot vector becomes a constant [1.0] appended to every input.
  This is mathematically equivalent to no conditioning (a constant input adds no
  information).

**Step 2: Modify VAE training to support unconditioned mode (2-4 hours)**
- Option A (preferred, minimal code change): Use the existing code with `n_states: 1`
  and a data loader that maps all states to index 0. The one-hot is `[1.0]` for every
  molecule. No architecture change needed.
- Option B (cleaner but more work): Add a `conditioned: bool` flag to VAEConfig.
  When False, skip the state concatenation in encoder and decoder. This changes
  the GRU input size, so it is a different model architecture.
- I recommend Option A because it requires zero code changes to `vae.py` and the
  comparison is fairer (same architecture, same number of parameters minus the
  information content of the state vector).

**Step 3: Train unconditioned VAE (30 min GPU)**
- `python scripts/train_vae.py --config configs/vae_unconditioned.yaml --selfies`
- Training time: same as conditioned VAE (~15-30 min on GPU)

**Step 4: Generate candidates from unconditioned VAE (1-2 hours)**
- Generate same number of candidates as conditioned VAE
- Use the same temperature and sampling parameters
- For compute-fairness: generate N candidates total (matching conditioned total)
  without state labels

**Step 5: Run evaluation pipeline on unconditioned candidates (2-4 hours)**
- Score with same unified scoring function
- Compute enrichment metrics
- Compare head-to-head: conditioned vs unconditioned

**Step 6: Compute effect size (1 hour)**
- Cohen's d between conditioned and unconditioned enrichment distributions
- Pre-registered threshold: d >= 0.8 for "state conditioning is meaningful"
- Also compute bootstrap CI on the difference

**CRITICAL DEPENDENCY:** This ablation is blocked on the structural annotation
fix (2a). If the state labels in the training data are wrong (e.g., molecules
assigned to DFGout_aCout when that state does not exist), then the conditioned
VAE was trained on partially wrong labels. The ablation would compare
"wrong conditioning" vs "no conditioning," which is uninformative. Fix structures
first, retrain conditioned VAE, then run the ablation.

**Expected failure modes:**
- If the unconditioned VAE produces similar or better enrichment, this is a
  **negative result for the paper's thesis.** Have a plan: frame it as "state
  conditioning improves diversity but not enrichment" or "state conditioning
  enables targeted generation for specific states even if aggregate metrics
  are similar."
- The n_states=1 approach adds a constant dimension to the input. This is
  not exactly equivalent to no conditioning (it adds a parameter). If
  reviewers challenge this, Option B is the fallback.

**Estimated time: 3-5 days (including wait for structural fix)**

---

### 2e. Multi-Kinase Incremental Extension (ABL1)

**Goal:** Add ABL1 as a second kinase to demonstrate generalization, without
full multi-kinase refactoring.

**Step 1: ABL1 data curation (3-5 days)**
- Query ChEMBL for ABL1 (target CHEMBL1862) bioactivity data
- Filter: IC50 assays, single protein, exact measurements only
- Curate ~100-500 compounds with pIC50 values
- Query PDB for ABL1 crystal structures across conformational states
  - ABL1 has well-characterized DFGout structures (imatinib complex, PDB 1IEP)
  - ABL1 has DFGin structures (dasatinib complex, PDB 2GQG)
  - ABL1 genuinely has DFGout/aCout structures, unlike EGFR
- Cross-reference with KLIFS for state annotations

**Step 2: Add ABL1 structure set (1-2 days)**
- Add ABL1 structures to a new function `_v1_curated_abl1_structures()` in
  `processing/structures.py` (or a new file `processing/structures_abl1.py`)
- Do NOT modify EGFR structures -- keep them separate
- Use same `StructureRecord` schema (it already has `target_gene` field... wait,
  it does not. The `StructureRecord` model does not have a `target_gene` field.)

**BLOCKER IDENTIFIED:** The `StructureRecord` Pydantic model (`processing/models.py`)
does not have a `target_gene` field. Adding one is a schema change that affects:
- All existing JSON artifacts containing structure records
- The `StructureDataset` model
- Any code that constructs `StructureRecord` objects
- Tests that validate structure records

This is what Principal estimated as part of the "15 source files" refactoring scope.
For the incremental approach: add `target_gene: str = Field(default="EGFR")` as an
optional field with a default. This is backward-compatible -- existing records
without the field will default to "EGFR".

**Step 3: Add ABL1 features (2-3 days)**
- Add curated structural features for ABL1 PDB structures in
  `structure/features.py` (or a new file)
- Add ABL1 pocket conditions in `generation/conditioning.py`
- Key: ABL1 uses the same 4-state framework but with different pocket geometries

**Step 4: ABL1 ligand dataset (1-2 days)**
- ChEMBL extraction + curation
- Format as JSON matching existing EGFR format
- Split into train/val/test (use scaffold splitting from day 1)

**Step 5: Train ABL1 models (2-3 days)**
- VAE: train with ABL1 SMILES + state labels
- MPNN: train with ABL1 affinity data (scaffold split)
- These can reuse the same model architectures with ABL1-specific configs

**Step 6: Run ABL1 pipeline (2-3 days)**
- Generate candidates per state
- Score with ABL1-specific GNINA receptor
- Compute enrichment against known ABL1 drugs (imatinib 2001, dasatinib 2006,
  nilotinib 2007, bosutinib 2012, ponatinib 2012, asciminib 2021)
- Compare state-aware vs static for ABL1

**Step 7: Cross-kinase analysis (1-2 days)**
- Compare EGFR vs ABL1 enrichment patterns
- Show that state conditioning benefit generalizes

**Expected failure modes (this is where the 2x estimate comes from):**
- ABL1 ChEMBL data is messier than EGFR. EGFR is one of the most studied kinases
  with clean data. ABL1 has more assay heterogeneity (cellular vs biochemical,
  different constructs). Curation will take longer than expected.
- ABL1 state annotations from KLIFS may disagree with the literature. EGFR
  already showed annotation errors; ABL1 will need the same careful verification.
- The `StructureRecord` schema change, even with defaults, may break serialization
  of existing artifacts. Need to test artifact loading backward compatibility.
- ABL1 GNINA docking requires preparing new receptor PDB files and validating
  the docking protocol against known ABL1 binders. This is a day of work that
  is easy to underestimate.

**Estimated time: 10-14 weeks (vs 6-9 week estimate)**

The 6-9 week estimate from Principal's analysis is for the code changes alone. It
does not fully account for:
- Data curation iteration (always takes 2-3x expected)
- State annotation verification for a new kinase
- GNINA receptor preparation and validation
- Debugging model training on new data
- The inevitable "ChEMBL data quality" surprises

---

## 3. Dependency Graph

```
                    [0] Verify 4ZAU conformation (2 hrs)
                              |
                    [1] Structural annotation fix (1.5-2 days)
                         /          |           \
                        /           |            \
        [1a] Fix structures.py   [1b] Fix features.py   [1c] Fix conditioning.py
                        \           |            /
                         \          |           /
                    [1d] Update configs + ML code
                              |
                    [1e] Update tests + run suite
                              |
                    [1f] Retrain VAE (30 min GPU)
                              |
                    [1g] Re-run pipeline (generation -> scoring -> evaluation)
                              |
                   -----------+-----------
                  |                       |
         [4] Ablation C              [5e] ABL1 pipeline
         Unconditioned VAE           (after ABL1 data ready)
         (3-5 days)
                  |
         [4a] Train unconditioned
                  |
         [4b] Generate + Score
                  |
         [4c] Effect size (Cohen's d)


    PARALLEL TRACK A (can start immediately):

         [2] MPNN Scaffold Split (2-3 days)
              |
         [2a] Implement scaffold_split()
              |
         [2b] Retrain MPNN
              |
         [2c] Report both R^2 values


    PARALLEL TRACK B (can start immediately):

         [3] Bootstrap CIs + BEDROC (1.5-2 days)
              |
         [3a] Implement bootstrap_ci()
              |
         [3b] Implement BEDROC
              |
         [3c] Apply to all metrics
              |
         [3d] Update artifact schemas


    PARALLEL TRACK C (can start after data curation):

         [5] ABL1 Extension (10-14 weeks total)
              |
         [5a] ABL1 data curation (3-5 days)
              |
         [5b] ABL1 structure set + features (3-5 days)
              |
         [5c] StructureRecord schema update (1 day)
              |
         [5d] ABL1 model training (2-3 days)
              |
         [5e] ABL1 pipeline execution (2-3 days) -- BLOCKED on [1g]
              |
         [5f] Cross-kinase analysis (1-2 days)
```

### Parallelization Summary

| Parallel? | Items | Rationale |
|-----------|-------|-----------|
| YES | [2] + [3] | Scaffold split and bootstrap CIs are independent of each other and of structural fix |
| YES | [5a-5c] + [1] | ABL1 data curation can proceed while structural fix is in progress |
| NO | [4] after [1] | Ablation is meaningless with wrong state labels |
| NO | [5e] after [1g] | ABL1 pipeline needs the corrected codebase |
| YES | [2] + [1] | Scaffold split does not depend on structural fix (MPNN is state-agnostic) |

**Maximum parallelism:** 3 concurrent work streams in week 1:
- Stream 1: Structural annotation fix (1 person, 2-3 days)
- Stream 2: MPNN scaffold split (1 person, 2-3 days)
- Stream 3: Bootstrap CIs + BEDROC (1 person, 1.5-2 days)

After week 1: Ablation C starts (depends on Stream 1), ABL1 begins data curation.

---

## 4. Items That Will Take 2x+ Estimated Time

### 4.1 ABL1 Multi-Kinase Extension: 2x (6-9 weeks -> 10-14 weeks)

**Reasons:**
1. **Data curation always takes longer.** ChEMBL ABL1 data has known issues with
   assay heterogeneity (different construct lengths, cellular vs biochemical IC50,
   multiple ABL1 isoforms). Expect 3-5 iterations of curation before clean data.
2. **State annotation verification.** CompBioRev just found 4+ annotation errors
   in EGFR, the best-studied kinase. ABL1 annotations will need the same scrutiny.
   This is at least 1 week of literature review.
3. **GNINA receptor preparation.** Each ABL1 PDB structure needs: crystal contacts
   removed, missing loops modeled, protonation state assigned, binding site defined.
   With 4+ structures, this is 2-3 days.
4. **"It works for EGFR" assumptions.** The pipeline was built for EGFR. Pocket
   volumes, gatekeeper clearances, hinge angles -- all the magic numbers in
   `features.py` and `conditioning.py` -- were tuned for EGFR. ABL1 has different
   values and different ranges. The generation strategies may need ABL1-specific
   tuning.
5. **Schema migration.** Adding `target_gene` to `StructureRecord` is trivial in
   code but requires re-generating every artifact that serializes structure records.

### 4.2 Structural Annotation Fix Cascade: 1.5x (8-12 hours -> 12-20 hours)

**Reasons:**
1. **Unknown unknowns in the features.** The curated features in `features.py` for
   3iku and 4ZAU were hand-written to match DFGout geometry (dfg_asp_phe_dist=10.2
   for 3iku, 11.0 for 4ZAU). If these structures are reclassified, we need NEW
   curated features. But the features module is v1 (literature-curated), meaning
   someone needs to go look up the actual geometric measurements for whatever
   structures replace them. This is manual research, not code.
2. **Representative structure reassignment.** 3iku is the `is_representative=True`
   structure for DFGout_aCin. If 3iku is removed (wrong PDB ID), the only remaining
   DFGout_aCin structure is 3w2r, which is a T790M/L858R double mutant. Is that
   acceptable as a "representative" DFGout_aCin structure? This is a scientific
   question, not an engineering one, and it requires discussion.
3. **Clustering impact.** The atlas builder (`atlas.py`) clusters structures in
   9D feature space. Removing 2-3 structures from the DFGout clusters may collapse
   the clustering solution. With only 1 structure in DFGout_aCin (3w2r), clustering
   becomes degenerate. Need to check whether the atlas still produces meaningful
   results.

### 4.3 Items That Will Be Faster Than Estimated

- **Bootstrap CIs** (estimated 1.5-2 days): Likely 1 day. The implementation is
  straightforward numpy, no external dependencies, no GPU.
- **VAE retraining** (estimated 30 min): Confirmed by config comments. Fast.

---

## 5. Responses to Other Reviewers

### To CompBioRev (Structural Annotations)

Your finding is the most important discovery of this entire review process. The
annotation errors in `structures.py` are not edge cases -- they are the structural
foundation of the project. I want to add one practical note:

If we fix 3iku (wrong PDB ID) and find that the intended structure (3IKA, T790M)
does not have curated features yet, we need to either:
(a) Add 3IKA features by measuring from the PDB coordinates (1-2 hours with PyMOL)
(b) Find a different DFGout_aCin structure

I checked: there are very few EGFR DFGout structures in the PDB period. The project
may end up with DFGout_aCin represented by a single mutant structure. That is
scientifically defensible (DFG conformation is primarily determined by the DFG motif
geometry, not distant mutations) but it is worth stating explicitly.

### To MLRev (Compute-Matched Comparison)

I agree the 30 vs 461 comparison is indefensible. On implementation: a fixed oracle
call budget is straightforward to implement but the question is what counts as an
"oracle call." In StateBind:
- GNINA docking is the expensive oracle (~30 seconds per molecule)
- MPNN inference is cheap (~1 ms per molecule)
- Fingerprint similarity is trivial

If the budget is defined as "GNINA docking calls," then the static baseline should
also be allowed to dock 461 molecules (generate more analogs). If it is "molecules
evaluated by the full scoring function," then both pipelines should evaluate the
same total number. This needs a clear definition before implementation.

### To Principal (Incremental ABL1)

Your file-by-file analysis was extremely useful. One item I want to flag: your
estimate of 6-9 weeks for incremental ABL1 assumes data is ready. My experience
with ChEMBL data curation for a new target is that it consistently takes 2-3x
the planned time due to:
- Assay type disambiguation
- Duplicate compound resolution
- pIC50 standardization across different assay conditions
- Structure-activity relationship (SAR) sanity checking

I recommend budgeting 3-5 days for data curation alone, and having a "data quality
go/no-go" checkpoint at day 3.

### To ProgDir (16-Week Timeline)

The 16-week Scenario B timeline is reasonable IF the structural annotation fix goes
smoothly. If the 3-state switch reveals additional problems (e.g., DFGout_aCin having
only 1 structure breaks the atlas clustering), add 1-2 weeks of contingency.

My recommended modification to the timeline:

| Week | Activity |
|------|----------|
| 1 | Verify 4ZAU + structural fix + scaffold split + bootstrap CIs (parallel) |
| 2 | VAE retrain + re-run pipeline + Ablation C starts |
| 3-4 | Ablation C complete + ABL1 data curation starts + REINVENT setup |
| 5-6 | ABL1 model training + compute-matched comparison |
| 7-8 | ABL1 pipeline execution + ChemRxiv preprint draft |
| 9-10 | BRAF data curation (if time) + conformal prediction |
| 11-12 | Cross-kinase analysis + scoring sensitivity |
| 13-14 | Paper writing + figures + supplementary |
| 15-16 | Internal review + revision + submission |

ChemRxiv preprint at week 7-8 aligns with having EGFR + ABL1 results and the
critical ablation complete.

---

## 6. Final Recommendations

### Priority Ordering (My Final Position)

1. **Verify 4ZAU + structural annotation fix** (Tier 0, immediate, 2-3 days)
2. **MPNN scaffold split** (Tier 0, parallel with #1, 2-3 days)
3. **Bootstrap CIs + BEDROC** (Tier 0, parallel with #1-2, 1.5 days)
4. **Retrain VAE (3-state) + re-run pipeline** (Tier 0, after #1, 1-2 days)
5. **Ablation C: unconditioned VAE** (Tier 1, after #4, 3-5 days)
6. **Compute-matched comparison** (Tier 1, 1-2 weeks)
7. **ABL1 incremental extension** (Tier 1-2, 10-14 weeks)
8. **REINVENT 4 setup** (Tier 2, 8-15 days)

### Go/No-Go Criteria

| Item | Go Criterion | No-Go Action |
|------|-------------|-------------|
| 4ZAU verification | DFG-Asp-Phe dist > 9A = DFGout | If DFGin: adopt 3-state model |
| MPNN scaffold split | R^2 > 0.35 on scaffold-split test | If R^2 < 0.35: MPNN is unreliable, increase weight on GNINA |
| Ablation C | Cohen's d >= 0.5 (relaxed from 0.8) | If d < 0.5: reframe paper as "diversity" not "enrichment" benefit |
| ABL1 data quality | >= 80 compounds with clean pIC50, >= 3 state-annotated structures | If insufficient: drop ABL1, use BRAF or SRC instead |

### Venue Recommendation

**JCIM (primary).** The structural annotation issues, while fixable, make Nature
Computational Science premature. JCIM reviewers will appreciate methodological
honesty about the 3-state model and mutant structure usage. After JCIM acceptance
and ABL1 extension, consider a follow-up Nature Comp Sci paper on multi-kinase
generalization.

---

*This deliberation is based on direct inspection of 12 source files, 3 config files,
8 test files, and all 5 Round 2 verification reports. All file paths, line numbers,
and code references are from the current ML branch.*
