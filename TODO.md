# StateBind -- Development Roadmap

Last updated: 2026-04-05

This document tracks every completed phase, active task, and planned workstream.
For success criteria and numeric targets, see `GOALS.md`.
For workstream briefs and interface contracts, see `workstreams/README.md`.

---

## 1. Completed

- [x] **Phase 0: Project scaffolding** -- `pyproject.toml`, `src/statebind/` layout, YAML configs, `DataPaths`, `ConfigLoader`. 12 subpackages wired into an acyclic dependency graph.
- [x] **Phase 1: Data processing** -- 18 EGFR mutations, 16 PDB structures, 9 reference ligands curated into `data/raw/`. `processing/` module validates, deduplicates, and writes `data/processed/` artifacts.
- [x] **Phase 2: Static baseline** -- Single-structure pipeline using PDB 1M17. 30 candidates generated, scored with 3-component function (reference similarity, druglikeness, docking stub). `baselines/` module.
- [x] **Phase 3: State atlas** -- 4-state conformational clustering (DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout). 9-dimensional structural features, state-specific pocket descriptors. `structure/` module.
- [x] **Phase 4: Context model** -- Mutation-to-state prediction. 33 features, 3 model tiers (logistic, random forest, gradient boosted), full ablation suite. `context/` module.
- [x] **Phase 5: World model** -- Markov state transition matrices, contrastive state embeddings, MLP transition predictor. `dynamics/` module.
- [x] **Phase 6: Generation** -- 7 state-conditioned strategies, type-I/II filtering, chemical diversity metrics. 49 novel candidates inaccessible to the static baseline. `generation/` module.
- [x] **Phase 7: Ranking + evaluation** -- Unified scoring function (4 weighted components), candidate merge, head-to-head comparison pipeline. `ranking/` + `evaluation/` modules.
- [x] **ML infrastructure** -- `Trainer` base class, `SMILESTokenizer`, `Vocabulary`, PyG graph construction utilities, `ModelCard`, `TrainerConfig`. `ml/` shared code.
- [x] **ML architectures** -- Conditional SMILES VAE (`ml/vae.py`), Affinity MPNN (`ml/mpnn.py`), Multi-task ADMET (`ml/admet.py`). Pydantic configs, YAML files (`configs/vae.yaml`, `configs/mpnn.yaml`, `configs/admet.yaml`), training scripts (`scripts/train_*.py`).
- [x] **Documentation** -- `CLAUDE.md`, `GOALS.md`, `CRITICAL.md`, 11 module READMEs, 9 workstream briefs, `INTERFACES.md`, `docs/` suite (23 files total).

---

## 2. In Progress: ML Training (Requires GPU)

### Data Preparation (no dependencies -- can start immediately)

- [x] **`scripts/prepare_vae_data.py`** -- Query ChEMBL for EGFR actives (target CHEMBL203). Canonicalize SMILES via RDKit, filter MW 150-800, deduplicate, split 80/20. Output: `data/processed/egfr_smiles_{train,val}.json`. **WS10 fix:** added pagination (40 pages). Result: 8,109 train / 2,027 val SMILES.
- [x] **`scripts/prepare_mpnn_data.py`** -- Extract IC50/Ki assays from ChEMBL EGFR, convert to pIC50, filter quality. Output: `data/processed/egfr_affinity.json` with SMILES + pIC50 + split labels. **WS10 fix:** expanded pagination from 5 to 40 pages. Result: 10,466 compounds.
- [x] **`scripts/prepare_admet_data.py`** -- Download six TDC benchmarks (hERG, CYP3A4, Caco-2, solubility, clearance, lipophilicity). Merge into unified multi-task format. Output: `data/processed/admet_combined.json`. **WS10 fix:** installed PyTDC. Result: 27,698 molecules (6 endpoints).

### Model Training (after data preparation)

- [x] **Conditional SMILES VAE** -- `python scripts/train_vae.py --config configs/vae.yaml`
  - **v1 (original):** 2.6M params, 0% valid SMILES (teacher forcing from epoch 0).
  - **v2 (retrained 2026-04-06):** TF annealing, hidden_dim 512, 9.5M params, val_recon=1.92. **Still 0% valid at all temperatures (0.3, 0.8, 1.0).** Root cause: prior-posterior mismatch (kl_weight=0.001) + character-level SMILES fragility.
  - **v3 (SELFIES, trained 2026-04-06):** SELFIES representation (100% validity by construction) + kl_weight=0.01. 300 epochs on H200 (31 min), val_recon=2.26. Generation: **999/1000 valid (99.9%), 948 unique (94.8%)**. Checkpoint: `artifacts/models/vae/best_model.pt`.

- [x] **Affinity MPNN** -- `python scripts/train_mpnn.py --config configs/mpnn.yaml`
  - All targets exceeded: RMSE=0.7182 (<1.0 ✓), R²=0.6863 (>0.5 ✓), Pearson=0.8323 (>0.7 ✓)
  - 10,466 compounds, 12.7M params, best epoch 83/150, trained in 217s on H200
  - Checkpoint: `artifacts/models/mpnn/best_model.pt` (50MB)

- [x] **Multi-task ADMET** -- `python scripts/train_admet.py --config configs/admet.yaml`
  - Classification targets met: hERG AUROC=0.7745 (>0.75 ✓), CYP3A4 AUROC=0.7323 (>0.70 ✓)
  - Regression tasks: solubility R²=0.46, others weak (low per-task data coverage)
  - 27,698 molecules, 187K params, best epoch 40/150, trained in 197s on L40S
  - Checkpoint: `artifacts/models/admet/best_model.pt` (775KB)

---

## 3. Planned: Group A Workstreams (Parallel, No Dependencies)

These four workstreams have zero prerequisites and can execute simultaneously.

- [x] **WS01: Chemistry Foundation** -- Replace all SMILES string heuristics with RDKit-backed operations: Morgan/ECFP4 fingerprints, canonical SMILES, molecular validation, synthetic accessibility scores. *Moderate complexity. High impact. Blocks WS02, WS04, WS08, WS09.* **Complete.**

- [x] **WS03: Statistical Testing** -- Add scipy-based significance tests to `evaluation/`: Mann-Whitney U, bootstrap confidence intervals, Cohen's d effect sizes, sensitivity analysis over scoring weights. *Low complexity. High impact. Blocks WS05.* **Complete.**

- [x] **WS06: CI/CD** -- GitHub Actions workflow running `pytest`, `ruff check`, and type checking on every push and PR. Badge in README. *Low complexity. Moderate impact. Blocks nothing.* **Complete.**

- [x] **WS07: Conditional VAE** -- End-to-end VAE pipeline: data prep, training loop, generation script, integration into `generation/` as a new strategy. Produces genuinely novel molecules from learned latent space, conditioned on conformational state. *High complexity. High impact.* **Complete (data prep + integration; training on HPC).**

---

## 4. Planned: Group B Workstreams (After WS01 Completes)

All four depend on `statebind.chemistry` from WS01. Within the scoring chain (WS02/WS04/WS08), execution must be **sequential** to avoid merge conflicts in `ranking/scoring.py`.

- [x] **WS02: Scoring Integration** -- Wire RDKit chemistry into the unified scoring function. Replace n-gram Tanimoto with Morgan/ECFP4 similarity, replace heuristic druglikeness with QED + Lipinski + SA score. *Low complexity. High impact.* **Complete.**

- [x] **WS04: Docking Proxy** -- Build a small MLP discriminator on molecular descriptors as an intermediate docking proxy. Replaces the constant-0.5 stub with a model that at least discriminates between structures. *Moderate complexity. Critical impact.* **Complete.**

- [x] **WS08: MPNN Affinity** -- Integration adapter wiring the trained MPNN into `ranking/scoring.py`. Cascading fallback: MPNN -> docking proxy -> stub. Normalized pIC50 output. *High complexity. Critical impact.* **Complete (integration; training on HPC).**

- [x] **WS09: ADMET Predictor** -- Integration adapter wiring the trained ADMET model into the filtering pipeline. Pass/fail gate for hERG liability (probability > 0.5) and CYP3A4 inhibition. Does NOT modify `ranking/scoring.py` -- no conflict with scoring chain. *High complexity. High impact.* **Complete.**

---

## 5. Planned: Group C (After WS03 Completes)

- [x] **WS05: Visualization** -- Publication-quality matplotlib/seaborn figures: score distributions, chemical space UMAP, state atlas heatmaps, comparison bar charts with error bars. Requires statistical testing infrastructure from WS03 for confidence intervals and p-values on plots. *Low complexity. Moderate impact.* **Complete.**

---

## 6. Integration Tasks (After ML Training Complete)

These tasks connect trained models into the running pipeline and re-execute the central experiment.

- [x] **Wire MPNN into scoring** -- MPNN loads automatically via cascading fallback in `ranking/scoring.py`. Verified: osimertinib scores 0.75, ethanol 0.34, fallback 0.50 for invalid SMILES. Scoring method string reports `MPNN_affinity(pIC50)`.

- [x] **Wire VAE into generation** -- VAE v3 (SELFIES) trained: 300 epochs, val_recon=2.26, 9.5M params. Generation: **999/1000 valid (99.9%), 948 unique (94.8%)**. SELFIES representation guarantees validity by construction. 1000 candidates generated (250 per state). Comparison re-run with VAE candidates: state-aware mean=0.4378 vs static=0.5437. VAE candidates expand chemical space (431 novel) but score lower on average due to low reference similarity.

- [x] **Wire ADMET into filtering** -- ADMET predictions work (hERG AUROC=0.77, CYP3A4=0.73). Hard pass/fail filtering too aggressive for kinase inhibitors (100% hERG failure — kinase inhibitors are inherently hERG-liable). ADMET best used as informational annotation, not pre-ranking gate. Documented as limitation.

- [x] **Re-run full comparison** -- Re-run with SELFIES VAE candidates (1000 generated, 999 valid). State-aware=461 candidates (395 VAE + 36 template + 30 shared), static=30. Mean: static=0.5437, state-aware=0.4378 (delta=-0.1059). Mann-Whitney U: p<0.001, Cohen's d=1.36 (large, static favored). Max: state-aware=0.7794 vs static=0.7288. Diversity: state-aware=0.9056 vs static=0.5684. 431 novel candidates. Weight sensitivity: 44% state-aware wins, 56% static. **Null hypothesis formally retained.**

- [x] **Update reports and artifacts** -- Comparison artifact at `artifacts/ranking/comparison.json`. GOALS.md, TODO.md, CRITICAL.md, HANDOFF.md all updated with VAE v3 results and final comparison.

---

## 7. Stretch Goals

These extend beyond v1 scope. Recorded for directional planning, not as commitments.

- [ ] **Transfer learning** -- Pre-train MPNN on ChEMBL-wide bioactivity data (~2M compounds), fine-tune on EGFR subset. Expected benefit: better generalization on novel scaffolds outside the EGFR training distribution.

- [ ] **Active learning loop** -- VAE generates candidates -> MPNN scores them -> top candidates added to MPNN training set -> MPNN retrained -> updated scores guide next VAE generation round. Closes the generation-evaluation loop.

- [ ] **Real docking** -- AutoDock Vina or GNINA integration. Dock candidates against all 4 state-specific receptor structures (prepared as PDBQT). Provides pose-level binding mode information that ML proxies cannot capture. Estimated: 2-3 days for receptor prep + compute.

- [ ] **Multi-objective optimization** -- Replace weighted linear scoring with Pareto frontier optimization over affinity, druglikeness, selectivity, and ADMET. Produces a diverse candidate set optimized along different tradeoff axes rather than a single composite number.

- [ ] **Multi-target expansion** -- Replicate the pipeline for ABL (imatinib, DFG-out preference), ALK (G1202R resistance), and BRAF (V600E). Tests whether state-aware advantage generalizes beyond EGFR.

- [ ] **FEP+ validation** -- For top 10-20 re-scored candidates, compute binding free energies via free energy perturbation. Closest computational analog to experimental IC50. Requires commercial software (Schrodinger) or collaboration.

---

## 8. Dependency Graph

```
                    +-----------+
                    | Start     |
                    +-----+-----+
                          |
          +---------------+---------------+---------------+
          |               |               |               |
     +----v----+     +----v----+     +----v----+     +----v----+
     |  WS01   |     |  WS03   |     |  WS06   |     |  WS07   |
     |Chemistry|     |  Stats  |     |  CI/CD  |     |   VAE   |
     | Found.  |     | Testing |     |         |     | Training|
     +----+----+     +----+----+     +---------+     +---------+
          |               |
    +-----+-----+        +----v----+
    |     |     |         |  WS05   |
    |     |     |         |  Viz    |
    v     v     v         +---------+
  +---+ +---+ +---+
  |W02| |W04| |W08|   <-- CONFLICT ZONE: all modify ranking/scoring.py
  +---+ +---+ +---+       Must execute sequentially: WS02 -> WS04 -> WS08
  Score  Dock  MPNN
  Integ  Proxy Affin
    |     |     |
    +-----+-----+----+
          |           |
     +----v----+ +----v----+
     |  WS09   | |  ML     |
     |  ADMET  | | Training|
     |  Integ  | | (Sec 2) |
     +---------+ +----+----+
                      |
               +------v------+
               | Integration |
               |  Tasks      |
               |  (Sec 6)    |
               +------+------+
                      |
               +------v------+
               | Re-run full |
               | comparison  |
               +------+------+
                      |
               +------v------+
               | Stretch     |
               | Goals       |
               +-------------+
```

### Conflict Zone Detail

Workstreams WS02, WS04, and WS08 all modify `ranking/scoring.py`. They must NOT run in parallel. Each builds a fallback layer on top of the previous:

1. **WS02** (Scoring Integration): replaces n-gram similarity with Morgan/ECFP4, heuristic druglikeness with QED. Establishes the RDKit-backed scoring baseline.
2. **WS04** (Docking Proxy): replaces constant-0.5 stub with an MLP discriminator. First real signal in the docking weight.
3. **WS08** (MPNN Affinity): replaces docking proxy with trained MPNN. Cascading fallback preserves WS04 as backup.

WS09 (ADMET) modifies the filtering pipeline in `generation/`, not `ranking/scoring.py`, so it can run in parallel with the scoring chain.

### Critical Path

The shortest path to rejecting the null hypothesis:

```
WS01 -> WS02 -> WS08 -> Integration -> Re-run comparison -> Statistical test
         |                                                         |
         +--- WS03 (parallel) -------- WS05 (optional) -----------+
```

ML training (Section 2) runs in parallel with all workstreams and feeds into Integration.

---

## Quick Reference: Current State

| Area | Status | Next Action |
|------|--------|-------------|
| Pipeline (Phases 0-7) | Complete (12 modules, 618 tests) | Maintain |
| MPNN | Trained: RMSE=0.72, R²=0.69, Pearson=0.83 | Integrated into scoring cascade |
| ADMET | Trained: hERG AUROC=0.77, CYP3A4=0.73 | Informational annotation (not hard filter) |
| VAE | SELFIES v3 trained (9.5M params, val_recon=2.26, 99.9% valid) | **Complete** |
| Scoring function | 4-tier cascade: GNINA -> MPNN -> proxy -> stub | Complete |
| GNINA docking | Integrated as tier 0, validated on GPU (binders -7.32 vs non-binders -4.16) | **Complete** (WS11) |
| Pareto optimization | Hypervolume comparison + Pareto front plots | **Complete** (WS12) |
| Statistical testing | Mann-Whitney U: p<0.001, d=1.36 (static favored) | Null hypothesis NOT rejected |
| Null hypothesis | **Not rejected** (static favored on mean composite) | Formally retained with VAE |
| Workstreams | 11 of 12 complete (618 tests passing) | WS13 remaining |
