---
agent: Associate Research Scientist
round: 1
date: 2026-04-09
type: review-assessment
---

# Independent Review Assessment: Implementation Reality Check

## Reviewer Identity

Associate Research Scientist -- 2-3 years post-PhD in computational chemistry and ML engineering. I am the person who will write the code, debug the CUDA errors at 2 AM, and explain to the PI why "1-2 weeks" actually means "5 weeks with 3 pivots." This review evaluates every proposal through the lens of what will actually happen when fingers hit keyboard.

---

## 1. Candidate Count Discrepancy -- A Red Flag Before We Start

Both agendas repeatedly cite "461 state-aware candidates." The actual comparison artifact on disk (`artifacts/ranking/comparison.json`) shows **431 state-aware candidates**, not 461. This is a 7% discrepancy. Every downstream compute estimate that uses 461 is slightly inflated. More importantly, if this number is wrong in the proposals, what else is off? Before any new work begins, reconcile the actual candidate counts from generation artifacts against what is reported.

---

## 2. Tool Installation Complexity Assessment

This is where proposals meet reality. I have rated each tool on a 5-point scale.

### Tool Complexity Matrix

| Tool | Complexity | Python 3.12? | GPU Required? | Est. Setup Time | Blocking Issues |
|------|-----------|-------------|--------------|----------------|-----------------|
| REINVENT 4 | **Medium-Hard** | Yes (>=3.10) | Recommended | 3-5 days | Custom GNINA scoring plugin, separate conda env |
| FLOWR | **Hard** | Unknown | Yes (40GB VRAM rec.) | 5-7 days | 40GB VRAM rec. rules out RTX 5000 Ada (16GB); repo deprecated in favor of FLOWR.root |
| FLOWR.root | **Hard** | Unknown | Yes | 5-7 days | Newer, less battle-tested; Google Drive checkpoint; Schrodinger-prepared complexes recommended |
| AiZynthFinder 4.4.1 | **Medium** | Yes (3.10-3.12) | No | 1-2 days | Requires stock DB download (Enamine/ZINC); ONNX model download |
| RAscore | **Nightmare** | **No** (Python 3.7-3.8 only) | No | Blocked | Requires TF 2.5.0, scikit-learn 0.22.1, Python 3.7. Completely incompatible with project's Python 3.12. Must retrain or use separate env. |
| ADMETlab 3.0 | **Easy** | N/A (API) | No | Hours | Rate limit 5 req/sec; 491 compounds = trivial. But API could go offline. |
| DrugCLIP | **Medium-Hard** | Unknown | Yes | 3-5 days | Checkpoint on Google Drive, not HuggingFace. Java-free but complex pipeline. |
| ProFSA | **Medium** | Unknown | Yes | 2-3 days | Checkpoint in GitHub repo data tarball. ICLR 2024 code. |
| PheSA | **Medium-Hard** | N/A (Java) | No | 3-5 days | Java dependency. OpenChemLib-based. Not native RDKit. Requires JVM in pipeline. |
| OpenFE | **Medium** | Yes | Yes (GPU for MD) | 2-3 days | conda install. OpenMM backend. ~3 hrs/transformation on GPU. |
| tauRAMD | **Hard** | Python script | Yes (GROMACS GPU) | 1-2 weeks | Requires GROMACS compiled with CUDA + RAMD plugin. System preparation is manual. |
| MAPIE (conformal prediction) | **Easy** | Yes | No | Hours | pip install. scikit-learn compatible. PyTorch wrapper available. |
| BEDROC | **Easy** | Yes | No | Hours | Implement from Truchon & Bayly formula or use rdkit.ML.Scoring. |
| Chemprop v2 | **Medium** | Yes | Recommended | 1-2 days | v1->v2 migration tool exists but architecture changes may break custom extensions. |
| Uni-Mol | **Hard** | Unknown | Yes | 3-5 days | Large pre-trained model (209M conformations). Custom inference pipeline. |

### Critical Blockers

**RAscore is a showstopper.** The synthbio-P01 proposal calls for RAscore as a Tier 0 screener and potentially a 5th scoring component. RAscore requires Python 3.7-3.8, TensorFlow 2.5.0, and scikit-learn 0.22.1. StateBind uses Python 3.12. These are fundamentally incompatible. The pickle serialization format used to save the RAscore models is version-specific. Options:

1. Run RAscore in a completely separate conda environment and call it via subprocess. Ugly but functional. Adds ~15 min of engineering.
2. Retrain the XGBoost model from scratch using modern dependencies. Requires the training data pipeline and AiZynthFinder results. 1-2 days.
3. Use only AiZynthFinder and skip RAscore entirely. Costs ~45 min per 50 molecules for retrosynthesis.

**Recommendation:** Option 3 (skip RAscore, use AiZynthFinder directly for top candidates). RAscore's value is as a fast filter, but with only 431 candidates, AiZynthFinder can process all of them in <6 hours. The engineering cost of maintaining a Python 3.7 environment is not worth it.

**FLOWR's 40GB VRAM recommendation.** The FLOWR README states: "CUDA-compatible GPU with at least 40GB VRAM recommended for training and generation." The RTX 5000 Ada has 16GB VRAM. The H200 has 141GB. FLOWR generation can only run on H200 nodes, not the more accessible RTX 5000 Ada partition. Furthermore, the original FLOWR repo is "no longer actively maintained" and directs users to FLOWR.root. The proposals reference FLOWR without acknowledging this deprecation. FLOWR.root checkpoints are on Google Drive (not Zenodo or HuggingFace), and it recommends Schrodinger-prepared complexes -- Schrodinger is proprietary software we do not have.

**Recommendation:** Downgrade FLOWR to "documented fallback." Use DiffSBDD as the primary 3D baseline instead -- it has pre-trained checkpoints on Zenodo, runs on 16GB GPUs, and has been published in Nature Computational Science (making it a particularly relevant comparison). Accept the 38% PoseBusters validity as a known limitation and report it honestly.

---

## 3. Data Availability and Format Conversion Boundaries

### ChEMBL Data for New Kinases

| Kinase | ChEMBL ID | Est. Compounds (IC50/Ki/Kd, <= 100nM) | Est. All Actives | Pre-2010 Training | SMILES Failure Rate |
|--------|-----------|---------------------------------------|-------------------|-------------------|---------------------|
| EGFR | CHEMBL203 | ~3,500 | ~10,466 | ~7,800 | ~1-2% |
| ABL1 | CHEMBL1862 | ~2,500 | ~8,500 | ~5,500 | ~1-2% |
| BRAF | CHEMBL5145 | ~1,200 | ~3,625 | ~1,800 | ~1-3% |
| MET | CHEMBL3717 | ~800 | ~2,500 | ~1,200 | ~2-3% |

**Data flow from ChEMBL to pipeline:**

```
ChEMBL API (chembl_webresource_client)
    |-> JSON response with SMILES, pChEMBL, assay_type, year
    |-> Filter: assay_confidence >= 7, standard_type in (IC50, Ki, Kd)
    |-> RDKit MolStandardize: salt removal, neutralization, canonicalization
    |   (expect ~1-3% failure here: metallic compounds, boronics, large peptides)
    |-> Deduplicate by canonical SMILES, keep median pChEMBL
    |-> SELFIES encoding for VAE
    |   (expect ~0.1-0.5% SELFIES encoding failures: organometallics, very large MW)
    |-> Morgan fingerprint generation for MPNN graph features
    |   (expect ~0.5% failure: molecules with no heavy atoms after standardization)
    |-> Final filtered training set
```

**Error handling decisions needed:**

1. What to do with ChEMBL entries that have multiple activity types (IC50 and Ki for same compound-target pair)? Current EGFR pipeline uses median pChEMBL. Is this documented? Is it the right choice for multi-task?
2. Compounds appearing across multiple kinase targets: keep or deduplicate? For multi-task MPNN, you want them -- they are the signal for transfer learning. But they create non-independence between kinase-specific evaluations.
3. The ChEMBL API has rate limits and occasional downtime. Download all data once, save as local CSV/JSON, and version-stamp it.

### KLIFS Structure Data

**Access:** OpenCADD-KLIFS Python package (`pip install opencadd`). Alternatively, KLIFS REST API at klifs.net. Both return pandas DataFrames with DFG/aC-helix annotations.

**Format conversion chain:**

```
KLIFS API -> structure metadata (PDB ID, chain, DFG state, aC state, resolution)
    |-> Filter: resolution <= 3.0 A, R-free <= 0.30
    |-> PDB download from RCSB
    |-> Pocket extraction (6A around co-crystallized ligand)
    |-> PDBQT conversion for GNINA (via Open Babel or ADFR's prepare_receptor)
    |-> 9D feature computation (StateBind's structure/features.py)
    |-> Box center/size computation for docking
```

**Failure points:**

- Not all KLIFS structures have co-crystallized ligands. Apo structures need a different pocket definition strategy (e.g., use a reference ligand position from a holo structure).
- PDBQT conversion via Open Babel sometimes misassigns protonation states. The existing EGFR receptors were presumably hand-checked; new kinases need the same treatment.
- The 9D feature computation (`structure/features.py`) was designed for EGFR. Some features (e.g., "aC-Glu to catalytic Lys distance") require knowing the KLIFS-standardized residue numbering for each kinase. This is not a simple copy-paste; each kinase has different residue numbers for the catalytic Lys, the aC-Glu, the DFG-Asp, etc.

### REINVENT 4 Input/Output Format

**Input:** REINVENT 4 uses a TOML configuration file specifying the scoring components, their weights, and the generation mode (de novo, scaffold hopping, etc.). SMILES prior is built-in. Scoring components are Python plugins.

**GNINA integration challenge:** REINVENT 4 calls scoring components synchronously during RL training. Each scoring call must return a float within seconds. GNINA docking takes 30-120 seconds per molecule (StateBind's config: `timeout_per_molecule: 120`). This means REINVENT RL training with GNINA scoring will be extremely slow: 500 RL steps x 250 molecules/step x 60 seconds/dock = ~208 GPU-hours per kinase-state combination.

**Workaround options:**
1. Use a pre-trained MPNN as REINVENT's scoring oracle instead of GNINA. Much faster (~0.1s per molecule) but introduces the same model biases we are trying to compare against.
2. Pre-dock a large library and use nearest-neighbor lookup as scoring. Loses the generative optimization loop.
3. Accept the slow speed and run on H200 nodes with `--gpus=h200:1`. Budget 10-15 GPU-days for REINVENT alone across 4 states.

**Output:** REINVENT produces SMILES strings with per-step scores. These need to be re-scored with StateBind's unified scoring function for fair comparison. This is straightforward but adds ~2-4 hours of GNINA docking per state.

### FLOWR Input/Output Format

**Input:** PDB/CIF protein structure + reference ligand SDF for pocket definition. FLOWR extracts pocket atoms within a configurable radius (default 6A).

**Output:** SDF files containing 3D molecules with coordinates. These need:
1. SMILES extraction (RDKit `MolToSmiles`)
2. GNINA re-docking for fair scoring (cannot use FLOWR's internal scores for comparison)
3. Property computation for unified scoring

**Format conversion issues:** FLOWR generates 3D molecules. GNINA docking also produces 3D poses. These are different 3D conformations of the same molecule. For fair comparison, we should re-dock FLOWR molecules from SMILES (ignoring FLOWR's pose) to match how StateBind VAE candidates are scored.

---

## 4. Compute Resource Estimates (Corrected)

### Docking Scale

The proposals estimate docking load but inconsistently. Let me trace it properly:

**Current EGFR pipeline:**
- 431 state-aware candidates x 4 states = 1,724 docking runs
- 30 static candidates x 1 state = 30 docking runs
- At ~60-120 sec/dock: ~28-57 GPU-hours for existing EGFR docking

**Multi-kinase extension (3 new kinases):**
- Assume ~400 state-aware candidates per kinase x 3-4 states x 3 kinases = ~3,600-4,800 docking runs
- At ~90 sec/dock average: ~90-120 GPU-hours
- Plus REINVENT candidates: ~1,000 per kinase x 4 states x 4 kinases = ~16,000 docking runs = ~400 GPU-hours
- Plus FLOWR/DiffSBDD candidates: ~1,000 per kinase x 4 states x 4 kinases = ~16,000 docking runs = ~400 GPU-hours

**Total docking estimate: ~900-1,000 GPU-hours** (much higher than the "2-3 GPU-days" in Cohort1's P0 baseline estimate). The baseline proposals drastically underestimate docking time because they assume scoring without GNINA re-docking, which defeats the purpose of fair comparison.

### GPU Memory Budget

| Task | GPU | Memory Req. | Feasible? |
|------|-----|-------------|-----------|
| VAE training (batch=64) | RTX 5000 Ada (16GB) | ~2-4 GB | Yes |
| VAE training (batch=64) | H200 (141GB) | ~2-4 GB | Yes (overkill) |
| MPNN training (batch=64) | RTX 5000 Ada (16GB) | ~4-8 GB | Yes |
| GNINA docking (single mol) | RTX 5000 Ada (16GB) | ~2-4 GB | Yes |
| FLOWR generation | RTX 5000 Ada (16GB) | ~16GB (tight) | Marginal -- 40GB recommended |
| FLOWR generation | H200 (141GB) | ~16GB | Yes |
| DiffSBDD generation | RTX 5000 Ada (16GB) | ~8-12 GB | Yes |
| REINVENT 4 RL | RTX 5000 Ada (16GB) | ~8 GB | Yes |
| OpenFE FEP | RTX 5000 Ada (16GB) | ~4-8 GB | Yes |
| tauRAMD (GROMACS) | H200 (141GB) | ~4-8 GB | Yes |
| Uni-Mol inference | RTX 5000 Ada (16GB) | ~8-12 GB | Marginal |

### Disk Space

| Data | Est. Size | Location |
|------|----------|----------|
| Current artifacts | 160 MB | `artifacts/` |
| ChEMBL data (4 kinases) | ~200 MB | `data/processed/` |
| KLIFS structures + receptors | ~500 MB | `data/processed/docking/` |
| GNINA docking results (all methods, 4 kinases) | ~5-10 GB | scratch |
| REINVENT 4 installation + models | ~2-3 GB | conda env |
| DiffSBDD installation + checkpoints | ~3-5 GB | conda env |
| OpenFE RBFE trajectories (if P3) | ~50-100 GB | scratch |
| GROMACS/tauRAMD trajectories (if pursued) | ~200-500 GB | scratch |

**Home directory (~33 TB available):** Sufficient for code and processed data.
**Scratch (~8.9 TB available):** Sufficient for MD trajectories and docking results.
No disk space blockers.

---

## 5. Error Handling Decision Matrix

Every proposal assumes a happy path. Here is where things will go wrong, and what decision must be made in advance:

| Failure Mode | Expected Rate | Decision Needed | Recommendation |
|-------------|---------------|----------------|----------------|
| ChEMBL SMILES fail RDKit parsing | 1-3% | Skip silently, log and skip, or fix manually? | Log and skip. Manually inspect any with pIC50 > 8. |
| SELFIES encoding fails | 0.1-0.5% | Skip or try canonical SMILES? | Log and skip. These are typically organometallics or very large MW. |
| GNINA segfaults on a molecule | ~0.5-1% | Retry, skip, or assign score 0? | Try once with timeout. If fail, assign NaN and exclude from ranking. Do NOT assign 0 (confounds with low affinity). |
| GNINA produces no valid pose | ~2-5% | Assign what score? | Assign NaN, exclude from enrichment calculation. Report fraction with valid poses per method. |
| MPNN predicts extreme values (>12 or <2 pIC50) | ~1-2% | Clip, flag, or exclude? | Clip to [2.0, 12.0] range. Flag clipped values in output. |
| REINVENT RL does not converge | ~10-20% of runs | Restart with different seed, change hyperparameters? | Pre-define: 3 seeds, keep best. If 0/3 converge, report as failure. |
| AiZynthFinder finds no route | ~20-30% | Binary fail or continuous score? | Report binary (route found/not found) and number of steps. |
| ADMETlab 3.0 API timeout | Variable | Retry or local model? | 3 retries with exponential backoff. Save all results locally. Version-stamp. |
| KLIFS has no DFGout structure for a kinase-state | Common for sparse kinases | AF2-MSM or skip state? | AF2-MSM with quality threshold (docking AUC >= 0.70). If fails, reduce to 2-3 state model. |
| Multi-task MPNN shows negative transfer | ~20-30% chance | Revert to single-task? | Pre-plan ablation: multi-task vs single-task per kinase. Report honestly. |

---

## 6. Step-by-Step Implementation Sketches for Top 3 Priorities

### Priority Item 1: Pre-Publication Fixes (Critical Path)

**Estimated time: 3-5 days (not "hours" as claimed)**

**Step 1: Osimertinib Reference Leakage Fix (Day 1)**
1. Edit `baselines/scoring.py` lines 57-64: remove osimertinib from `_REFERENCE_BINDERS` list for pre-2015 validation
2. But wait -- osimertinib is also in `evaluation/retrospective.py` as a held-out drug (approved_year: 2015). Is it in the pre-2015 held-out set or the reference set? Need to trace data flow through `scripts/` to find the actual retrospective validation script.
3. Create two reference sets: pre-2010 refs (erlotinib, gefitinib only) and pre-2015 refs (erlotinib, gefitinib only -- osimertinib is the held-out drug).
4. Re-run unified scoring with new reference sets. This requires re-running the GNINA docking? No -- docking scores do not depend on reference set. Only `reference_similarity` changes.
5. Re-compute enrichment metrics (EF@10, and add BEDROC).
6. **Failure point:** The `DEFAULT_WEIGHTS` in `ranking/scoring.py` have `SCORING_METHOD` as a string constant (line 131-135). CLAUDE.md says "Do not change DEFAULT_WEIGHTS without updating SCORING_METHOD." So changing the reference set also requires updating the method documentation string. And CLAUDE.md says "Do not modify _REFERENCE_BINDERS without re-running the full pipeline." This means re-running everything, not just re-scoring.
7. **True effort:** 1-2 days including re-running the pipeline and validating results.

**Step 2: Structure Verification -- 3W2R and 4ZAU (Days 2-3)**
1. Verify 3W2R: Download PDB file, check mutation annotations. 3W2R IS a T790M/L858R double mutant (this is stated in the PDB header). This is NOT wild-type EGFR.
2. Search KLIFS for wild-type EGFR DFGout structures. Candidates: PDB 4I21 (EGFR DFGout), PDB 2JIU, others.
3. If a clean WT DFGout structure exists, prepare it as a new receptor (PDBQT conversion, box definition).
4. Re-dock all candidates against the new structure and the old 3W2R. Compare results.
5. **Failure point:** Wild-type EGFR rarely crystallizes in DFGout. The mutation may be necessary for the structure to exist. If no WT DFGout structure exists, the paper must disclose the mutation and discuss its implications.
6. Similarly verify 4ZAU: Check ligand assignment (is it osimertinib or EAI045?), check DFGout_aCout classification against KLIFS annotations.
7. **True effort:** 2-3 days including literature search, KLIFS queries, potential receptor re-preparation.

**Step 3: Bootstrap CIs and BEDROC (Day 4-5)**
1. Implement BCa bootstrap (10,000 resamples) for EF@10. scipy.stats.bootstrap or manual implementation.
2. Implement BEDROC(alpha=20). Formula from Truchon & Bayly (2007). RDKit has `rdkit.ML.Scoring.Scoring.CalcBEDROC`.
3. Apply to existing retrospective results.
4. Generate confidence interval table.
5. **Failure point:** With N=5 held-out drugs, the BCa bootstrap CIs will be VERY wide. The CI might include 1.0 (random performance). This is the honest result, and it is exactly why multi-kinase extension is essential.
6. **True effort:** 1-2 days.

**Total realistic estimate for pre-publication fixes: 5-8 days, not "hours"**

### Priority Item 2: Ablation Suite -- Experiment C (Unconditioned VAE)

**Estimated time: 1-2 weeks**

**Step 1: Architecture Modification (Days 1-2)**
1. Read `ml/vae.py` carefully. The state conditioning vector is concatenated at two points: (a) encoder input at every timestep (`embed_dim + state_dim`), and (b) latent-to-decoder projection (`latent_dim + state_dim`).
2. The "zeroed out" ablation means: keep the architecture identical, but pass a zero vector of dimension `n_states` (=4) instead of the one-hot state vector. This preserves parameter count and architecture.
3. Implementation: Add a flag `zero_state=True` to `VAEConfig`. When set, replace state vector with zeros in both the encoder and decoder.
4. **Failure point:** The GRU encoder input size is `embed_dim + state_dim`. With zeroed state, the input is still the same size but with 4 constant-zero features. This is mathematically correct but may cause different training dynamics (the GRU has learned to use those features; zeroing them could cause initially worse reconstruction loss).
5. Alternative: Remove the state dimensions entirely (`embed_dim` only). This is a different architecture and confounds the comparison. Stick with zeroing.

**Step 2: Training (Days 3-5)**
1. Train unconditioned VAE on the same EGFR data with the same hyperparameters (`configs/vae.yaml`).
2. Use 3 random seeds for error bars.
3. Monitor training: reconstruction loss + KL divergence. The unconditioned model should converge faster (easier task -- no state conditioning to learn).
4. **GPU time:** ~1-2 hours per training run on RTX 5000 Ada. 3 seeds = 3-6 hours.
5. **Checkpoint management:** Save to `artifacts/models/vae_unconditioned_seed{N}/`.

**Step 3: Generation and Scoring (Days 6-7)**
1. Generate ~400 molecules from the unconditioned VAE (matching state-aware count).
2. Score with unified scoring function (including GNINA docking for all 4 states).
3. **Failure point:** How do you assign state labels to unconditioned molecules for the state_specificity component? The unconditioned VAE has no target state. Options: (a) assign 0 for state_specificity (penalizes unconditioned); (b) compute state_specificity as if targeting the best-scoring state (generous); (c) score under 3-component scoring (no state_specificity).
4. **Decision required BEFORE running:** This is a pre-registration-level decision. I recommend: score under BOTH 4-component (with state_specificity=0, matching static baseline) AND 3-component scoring. Report both.

**Step 4: Statistical Comparison (Day 8)**
1. Compute EF@10, BEDROC for unconditioned VAE.
2. Compute Cohen's d for state-aware vs unconditioned enrichment.
3. If Cohen's d < 0.5, the state-awareness claim weakens.
4. If Cohen's d >= 0.8, the state-awareness claim is supported.

**Total realistic estimate: 8-10 days**

### Priority Item 3: REINVENT 4 External Baseline

**Estimated time: 2-3 weeks (not "1-2 weeks" as claimed)**

**Step 1: Environment Setup (Days 1-3)**
1. Create separate conda environment: `conda create -n reinvent4 python=3.10` (not 3.12 -- REINVENT targets 3.10+, safer to use 3.10).
2. Install REINVENT 4: `python install.py cu126` (match cluster CUDA version).
3. Verify: run tutorial examples from `tutorials/` directory.
4. **Failure point:** REINVENT's conda env will have its own PyTorch version, potentially conflicting with StateBind's. Keep environments completely separate.

**Step 2: GNINA Scoring Plugin (Days 4-7)**
1. Write a custom REINVENT scoring component in `reinvent_plugins/components/comp_gnina_docking.py`.
2. The plugin must: (a) convert SMILES to 3D conformer, (b) call GNINA binary as subprocess, (c) parse docking score, (d) handle timeouts and failures gracefully, (e) return normalized score.
3. **This is the hardest part.** REINVENT's RL loop calls scoring synchronously. Each GNINA call takes 30-120 seconds. With 64 molecules per RL batch, each batch takes 32-128 minutes. This is 10-100x slower than typical REINVENT usage with fast scoring functions.
4. **Workaround:** Use REINVENT's `ExternalProcess` component type, which supports batch scoring via subprocess. Write a wrapper script that accepts SMILES list, docks them in parallel (using StateBind's existing `ProcessPoolExecutor` docking infra), and returns scores.
5. **Alternative workaround:** Train REINVENT with StateBind's MPNN as the scoring oracle (fast, ~0.1s/mol). Then re-dock the final REINVENT candidates with GNINA for the fair comparison. This is faster but introduces a two-stage evaluation that may confuse reviewers.

**Step 3: Configuration per State (Days 8-9)**
1. Write 4 TOML config files, one per EGFR state.
2. Each config specifies: receptor PDBQT path, box center, box size, scoring weights.
3. REINVENT's scoring must mirror StateBind's unified scoring: reference_similarity (0.35), drug-likeness (0.30), docking (0.20), state_specificity (0.15).
4. **Problem:** State_specificity for REINVENT. REINVENT generates molecules per-state (one RL run per state). State_specificity requires knowing which molecules appear across multiple states. This is only computable AFTER all 4 runs complete, not during RL. Options: (a) drop state_specificity from REINVENT's scoring during RL, add it post-hoc; (b) approximate with docking-score-ratio as proxy.

**Step 4: Generation Runs (Days 10-14)**
1. Run REINVENT de novo on each of 4 EGFR states.
2. 3 random seeds per state = 12 runs.
3. 500 RL steps per run, 250 final molecules per run.
4. Expected wall time: 2-5 GPU-days (depends on GNINA scoring speed).
5. **Monitor for:** RL not converging (reward plateau), mode collapse (all molecules similar), SMILES validity dropping.

**Step 5: Re-scoring and Comparison (Days 15-17)**
1. Collect all REINVENT molecules (up to 1,000 per seed, 3,000 total).
2. Deduplicate. Run through StateBind's unified scoring function.
3. GNINA re-docking against all 4 states.
4. Compute EF@10, BEDROC, property distributions.

**Total realistic estimate: 17-21 days**

---

## 7. Cohort-Specific Critique

### Cohort 1 Final Agenda

**Strengths:**
- Pre-registration framework is excellent and genuinely differentiating.
- Ablation suite design (Experiments A-G) is comprehensive and well-specified.
- The "harmonized specification" for unconditioned VAE (zeroed state vector, not removed) is the correct approach.
- Risk register is honest.
- Timeline is aggressive but not delusional.

**Implementation Concerns:**

1. **"FLOWR replaces MolCRAFT as primary 3D baseline"** -- FLOWR requires 40GB VRAM, is deprecated in favor of FLOWR.root, and the original repo recommends Schrodinger-prepared complexes. DiffSBDD is a safer choice (Zenodo checkpoints, 16GB compatible, published in Nat. Comp. Sci.).

2. **"~30-42 GPU-days" for multi-kinase** -- This estimate is for VAE + MPNN training only. It does not include GNINA docking for all candidates across all states and kinases. True docking cost alone is ~40-50 GPU-days. Total P0 compute is more like 80-100 GPU-days.

3. **"CrossDocked2020 contains EGFR (3D leakage)" risk rated as "High probability, Medium impact"** -- This is a bigger deal than acknowledged. If EGFR structures are in the 3D method's training data, the "zero-shot" claim for FLOWR/DiffSBDD is invalid. Must check before running experiments, not after.

4. **Within-method state ablations** (REINVENT 4-pocket vs 1-pocket, FLOWR 4-pocket vs 1-pocket) are described as the "Nature Comp Sci upgrade." Agreed -- this is the key differentiating experiment. But the engineering cost is substantial: it doubles the number of external baseline runs (from 2 methods x 1 config to 2 methods x 2 configs = 4 setups). Budget at least 2 additional weeks.

### Cohort 2 Final Agenda

**Strengths:**
- The two-paper strategy is pragmatic and well-reasoned.
- The scoring reform (Priority 1) correctly identifies the #1 publication blocker.
- The conformational selection narrative (Priority 3) at zero compute cost is brilliant prioritization.
- Kinase panel revision (dropping JAK2, leading with EGFR) is correct.
- The kinetic scoring deferral (Priority 4, Option A: post-hoc analysis) is the right call.

**Implementation Concerns:**

1. **"Expand reference set: 3 drugs -> 100-300 ChEMBL EGFR scaffold centroids"** -- The ChEMBL query for EGFR IC50 <= 100 nM will return ~3,000-3,500 compounds. Bemis-Murcko decomposition, clustering, and centroid selection is straightforward in RDKit (~2-3 hours of code). But the potency-weighted scoring formula (top-K centroids, potency-weighted mean) needs careful implementation and validation. Expected effort: 2-3 days, not "1-2 weeks."

2. **PheSA** requires Java (OpenChemLib). This adds a JVM dependency to the pipeline. On HPC, this means `module load Java`. PheSA is not RDKit-native. Every scoring call would need to cross the Python-Java boundary (via subprocess, py4j, or pre-computing all similarities). This is annoying but feasible. Alternative: use ROSHAMBO (Python/RDKit-native, shape+pharmacophore scores). ROSHAMBO uses RDKit 2023.03 and computes shape/color scores with RDKit definitions. Much easier integration. I recommend ROSHAMBO over PheSA for the 6-configuration sensitivity analysis.

3. **DrugCLIP pocket-ligand scoring** -- The NeurIPS 2023 DrugCLIP model checkpoint is on Google Drive. The 2026 Science version is at drugclip.com. Neither is on HuggingFace or PyPI. Integration requires: (a) downloading checkpoint, (b) understanding input format (pocket + ligand 3D), (c) writing inference script, (d) handling 431+ molecules. Expected effort: 3-5 days. This is Medium-Hard.

4. **"~5 person-weeks, ~8 GPU-hours" for scoring reform** -- The GPU-hours estimate is wildly low if GNINA re-docking is included. Re-scoring all candidates under 6 configurations does NOT require re-docking (docking scores are cached). But Tversky and PheSA/ROSHAMBO scores need to be computed from scratch. True compute: ~8-16 GPU-hours for any needed re-docking, plus ~1-2 days CPU for fingerprint/similarity computation.

5. **tauRAMD: 150-250 GPU-days** -- This is correctly identified as expensive. The cheminfo critique's recommendation to pilot-validate on 3 known drugs first (3 GPU-days) is essential. But even the pilot requires GROMACS compiled with the RAMD plugin and GPU support. GROMACS compilation on HPC is a 1-2 day affair. The RAMD plugin (from HITS-MCM/tauRAMD GitHub) requires patching GROMACS source code. This is not a `pip install` operation.

---

## 8. Unknown Unknowns

Things the proposals have not thought about:

### 8.1 GNINA v1.1 vs v1.3

The cluster has GNINA v1.1 (built Dec 2023). GNINA v1.3 was released March 2025 with a PyTorch backend (replacing Caffe) and improved scoring. Should we upgrade? Upgrading would mean ALL existing docking scores become non-comparable. If we upgrade mid-project, we need to re-dock everything. If we do not upgrade, we are using a 2+ year old binary. **Decision: Do NOT upgrade. Keep v1.1 for consistency. Document the version in the paper.**

### 8.2 GLIBC 2.28 Compatibility

The Bouchet cluster runs GLIBC 2.28 (RHEL 8). Some newer tool binaries may require GLIBC 2.29+. This was a common issue with early GNINA builds. We need to verify each new tool's binary compatibility before assuming it works. FLOWR.root, DiffSBDD, and REINVENT 4 are all Python-based and should be fine. But any tool with compiled C++ components (OpenFE uses OpenMM, GROMACS) needs verification.

### 8.3 Conda Environment Conflicts

StateBind uses `pip install -e ".[ml]"` with Python 3.12. REINVENT 4 needs its own conda env (Python 3.10). DiffSBDD likely needs another env. AiZynthFinder needs another. Managing 4-5 conda environments on an HPC cluster with SLURM is operational overhead. Each SLURM script must activate the correct environment. Suggestion: create a `envs/` directory with one-line activation scripts per tool, and a master script that dispatches to the correct env.

### 8.4 Random Seeds and Reproducibility

Proposals mention "3 random seeds" for error bars but do not specify HOW seeds are set. PyTorch, NumPy, Python `random`, and CUDA all have separate RNG states. True reproducibility requires:
```python
import torch, numpy, random
torch.manual_seed(seed)
numpy.random.seed(seed)
random.seed(seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
```
StateBind's existing code does not appear to have a unified seed-setting utility. One should be created before running any comparative experiments.

### 8.5 Time Zone of ChEMBL Document Dates

The temporal split uses drug approval years. But ChEMBL's `document_year` field is the publication year of the assay, not the compound synthesis date. A compound tested in 2009 and published in 2011 with `document_year=2011` would be in the pre-2015 training set but represents pre-2010 knowledge. This is a known issue in temporal split validation (Wallach & Heifets, 2018). The proposals do not address this. For the held-out drugs, we use FDA approval year, which is clean. For training compounds, we use ChEMBL document_year, which has this lag. This is acceptable but should be disclosed.

### 8.6 Multi-Task MPNN Input Dimensionality

The kinpharm-P01 proposal appends a 5D kinase embedding + 9D state vector to the molecular representation. The current MPNN (`ml/mpnn.py`) uses NNConv with atom features (35D) and bond features. The state conditioning is NOT part of the current MPNN architecture -- it is only in the VAE. Adding state conditioning to the MPNN requires architecture changes to the readout head (not the message passing layers). This is ~1-2 days of engineering but is not as simple as "concatenate and train."

### 8.7 Pareto Optimization with Missing Components

If GNINA fails for a molecule (no valid pose), the docking_proxy score is NaN. The unified scoring function has a fallback cascade (GNINA -> MPNN -> proxy -> stub 0.5). But for Pareto analysis, a stub score of 0.5 is misleading -- it places the molecule in the middle of the docking distribution. Molecules with failed docking should be excluded from Pareto analysis entirely, not given a default value. This needs to be handled explicitly.

### 8.8 EGFR-Specific Reference Binders for Other Kinases

The `_REFERENCE_BINDERS` list in `baselines/scoring.py` contains erlotinib, gefitinib, and osimertinib -- all EGFR drugs. For multi-kinase extension, each kinase needs its own reference binder list. ABL1 needs imatinib, dasatinib, nilotinib. BRAF needs vemurafenib, dabrafenib. This is not just a data entry task; the reference binders define the similarity anchor for `reference_similarity`. The choice of references for each kinase should be pre-registered. This is mentioned in the Cohort1 agenda but not in the implementation details.

### 8.9 ADMETlab 3.0 API Stability

The proposals treat ADMETlab 3.0 as reliable infrastructure. It is a free academic web service hosted by SCBDD in China. Free academic APIs can go offline, change endpoints, or rate-limit without notice. **Mitigation:** Download results once, save locally with version stamps and access dates. Use local ADMET model (StateBind already has one with hERG AUROC 0.77) as fallback. Do NOT build any critical pipeline component that requires live API access.

### 8.10 CrossDocked2020 EGFR Leakage

Both agendas mention this risk but neither proposes a concrete check. Here is the check: CrossDocked2020 is based on PDBbind v2016. Download the PDB ID list from CrossDocked2020. Grep for EGFR-related PDB IDs (1M17, 2GS7, 3W2R, 4ZAU, and any other EGFR structures). If any StateBind representative structures appear in CrossDocked2020's training set, DiffSBDD/FLOWR are not "zero-shot" for EGFR. This check takes 30 minutes and should be done BEFORE deciding on the 3D baseline. I would be very surprised if 1M17 is NOT in CrossDocked2020.

---

## 9. Prioritization Recommendation

From an implementation perspective, here is what I would do in what order:

### Phase 0: Foundation (Week 0-1)
1. Reconcile candidate counts (431 vs 461?)
2. Fix osimertinib reference leakage
3. Verify 3W2R/4ZAU structures
4. Implement BEDROC + bootstrap CIs
5. Create unified seed-setting utility
6. Check CrossDocked2020 for EGFR structures
7. Set up kinase-specific reference binder lists for ABL1, BRAF, MET

### Phase 1: Critical Ablation (Week 1-3)
8. Train unconditioned VAE (Experiment C)
9. Run ablation suite on EGFR (Experiments C, E, F, G)
10. If Cohen's d < 0.5 for state effect: STOP and re-evaluate thesis

### Phase 2: External Baselines (Week 2-5)
11. Set up REINVENT 4 in separate conda env
12. Write GNINA scoring plugin for REINVENT
13. Run REINVENT on 4 EGFR states (3 seeds)
14. Set up DiffSBDD (NOT FLOWR) as 3D baseline
15. Run DiffSBDD on 4 EGFR pockets
16. Re-score all external candidates with unified scoring

### Phase 3: Scoring Reform (Week 2-4, parallel with Phase 2)
17. ChEMBL EGFR centroid reference set
18. 6-configuration sensitivity analysis (use ROSHAMBO, not PheSA)
19. UMAP + property distribution figures
20. Conformal prediction wrapping for MPNN (MAPIE, easy)

### Phase 4: Multi-Kinase (Week 4-10)
21. ChEMBL data curation for ABL1, BRAF, MET
22. KLIFS structure retrieval + atlas construction
23. Receptor preparation (PDBQT) for all states
24. Train kinase-specific VAEs (or multi-task)
25. Train kinase-specific MPNNs (or multi-task)
26. Run full pipeline per kinase
27. Retrospective enrichment with bootstrap CIs

### Phase 5: Strengthening (Week 8-12)
28. GIST water analysis on EGFR (if Phase 1 results positive)
29. Survival funnel: ADMETlab 3.0 profiling + AiZynthFinder for top 50
30. Within-method state ablations (REINVENT 4-pocket vs 1-pocket)
31. Conformational selection narrative (writing, zero compute)

### Phase 6: Writing (Week 10-14)
32. Compile all results
33. Generate publication figures
34. Write manuscript

**My personal timeline estimate for one person: 14-18 weeks, not 6-8 weeks.**

The Cohort1 estimate of "6-8 weeks" and the Cohort2 estimate of "20-26 person-weeks" are realistic only if multiple people are working in parallel. For a single researcher (which is what "associate research scientist" implies), 14-18 weeks is honest.

---

## 10. Summary Verdict

Both cohorts produced strong research agendas. The core thesis is sound and the proposed experiments are scientifically appropriate. My concerns are almost entirely about implementation feasibility and timeline:

1. **Tool installation complexity is systematically underestimated.** RAscore is incompatible with Python 3.12. FLOWR requires 40GB VRAM and is deprecated. PheSA requires Java. Each external tool needs its own conda environment.

2. **Compute budgets are 2-3x underestimated** when GNINA re-docking is properly accounted for across all methods, states, and kinases.

3. **Timeline estimates are 1.5-2x optimistic** for a single researcher. "Hours" tasks are actually "days." "1-2 weeks" tasks are actually "3-4 weeks."

4. **Error handling decisions are not pre-specified.** Every format conversion boundary (SMILES -> SELFIES, SMILES -> 3D, 3D -> GNINA, ChEMBL -> filtered set) needs an explicit failure mode specification.

5. **The 431 vs 461 discrepancy** needs to be resolved before any new work begins.

Despite these concerns, the work is feasible on Yale Bouchet with H200/RTX 5000 Ada GPUs. The scratch filesystem has ample space. The key risk is timeline, not capability. If the pre-publication fixes and ablation suite are done first (Phases 0-1), the go/no-go decision point at Week 3 is well-defined and de-risks the remaining 12-15 weeks of work.

---

## References

1. Loeffler et al. (2024). REINVENT 4: Modern AI-Driven Generative Molecule Design. J Cheminformatics.
2. Cremer et al. (2025). FLOWR: Flow Matching for Structure-Aware De Novo, Interaction- and Fragment-Based Ligand Generation. arXiv:2504.10564.
3. Schneuing et al. (2024). Structure-based drug design with equivariant diffusion models. Nature Computational Science.
4. Thakkar et al. (2024). AiZynthFinder 4. MIT License. GitHub: MolecularAI/aizynthfinder.
5. Thakkar et al. (2021). Retrosynthetic accessibility score (RAscore). Chemical Science, 12(9), 3339-3349.
6. Fu et al. (2024). ADMETlab 3.0. Nucleic Acids Research, 52(W1), W422-W431.
7. McNutt et al. (2021). GNINA 1.0: molecular docking with deep learning. J Cheminformatics, 13, 43.
8. Sunseri & Koes (2025). GNINA 1.3: the next increment in molecular docking with deep learning. J Cheminformatics.
9. Gao et al. (2023). SELFIES and the future of molecular string representations. Patterns, 3(10), 100588.
10. Truchon & Bayly (2007). Evaluating virtual screening methods: good and bad metrics for the "early recognition" problem. JCIM, 47, 488-508.
11. Heid et al. (2024). Chemprop: A Machine Learning Package for Chemical Property Prediction. JCIM.
12. Gao et al. (2024). Round-trip retrosynthesis verification of 3D-generated molecules. arXiv:2411.08306.
13. Li et al. (2024). Conformalized GNN fusion for ADMET prediction. JCIM.
14. Wahler et al. (2024). PheSA: An Open-Source Tool for Pharmacophore-Enhanced Shape Alignment. JCIM.
15. Gao et al. (2023). DrugCLIP: Contrastive Protein-Molecule Representation Learning for Virtual Screening. NeurIPS 2023.
16. Kokh et al. (2018). Estimation of Drug-Target Residence Times by tauRAMD. JCTC, 14(7), 3859-3869.
17. Gapsys et al. (2025). OpenFE consortium benchmark for relative free energy perturbation.
18. OpenCADD-KLIFS Python package. opencadd.readthedocs.io.
19. Van Tilborg et al. (2022). MAPIE: Model Agnostic Prediction Interval Estimator. scikit-learn-contrib.
20. Qu et al. (2024). MolCRAFT: Structure-Based Drug Design with Bayesian Flow Networks. ICML 2024.

---

*This review was produced by the Associate Research Scientist (associate) for the StateBind ReviewCohort, Round 1. All tool assessments are based on published documentation and direct verification of project artifacts. No code was modified.*
