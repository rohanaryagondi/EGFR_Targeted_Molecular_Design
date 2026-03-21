# StateBind -- Development Roadmap

Last updated: 2026-03-21

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

- [ ] **`scripts/prepare_vae_data.py`** -- Query ChEMBL for EGFR actives (target CHEMBL203). Canonicalize SMILES via RDKit, filter MW 150-800, deduplicate, split 80/10/10. Output: `data/processed/egfr_smiles_{train,val,test}.json`. Target: 3,000-5,000 compounds.
- [ ] **`scripts/prepare_mpnn_data.py`** -- Extract IC50/Ki assays from ChEMBL EGFR, convert to pIC50, filter quality. Output: `data/processed/egfr_affinity.json` with SMILES + pIC50 + split labels.
- [ ] **`scripts/prepare_admet_data.py`** -- Download six TDC benchmarks (hERG, CYP3A4, Caco-2, solubility, clearance, lipophilicity). Merge into unified multi-task format. Output: `data/processed/admet_combined.json`.

### Model Training (after data preparation)

- [ ] **Conditional SMILES VAE** -- `python scripts/train_vae.py --config configs/vae.yaml`
  - Targets: reconstruction > 80%, validity >= 50%, uniqueness >= 80%
  - KL annealing: beta warmup over first 10 epochs
  - Estimated time: 2-4 hours on GPU
  - Checkpoint: `artifacts/models/vae/best_model.pt`

- [ ] **Affinity MPNN** -- `python scripts/train_mpnn.py --config configs/mpnn.yaml`
  - Targets: RMSE < 1.0 pIC50, R-squared > 0.5, Pearson r > 0.7
  - Must generalize to held-out SMILES (no memorization)
  - Estimated time: 1-2 hours on GPU
  - Checkpoint: `artifacts/models/mpnn/best_model.pt`

- [ ] **Multi-task ADMET** -- `python scripts/train_admet.py --config configs/admet.yaml`
  - Targets: hERG AUROC > 0.75, CYP3A4 AUROC > 0.70, Spearman > 0.5 on >= 4/6 endpoints
  - Multi-task must match or beat single-task baselines on average
  - Estimated time: 2-3 hours on GPU
  - Checkpoint: `artifacts/models/admet/best_model.pt`

---

## 3. Planned: Group A Workstreams (Parallel, No Dependencies)

These four workstreams have zero prerequisites and can execute simultaneously.

- [ ] **WS01: Chemistry Foundation** -- Replace all SMILES string heuristics with RDKit-backed operations: Morgan/ECFP4 fingerprints, canonical SMILES, molecular validation, synthetic accessibility scores. *Moderate complexity. High impact. Blocks WS02, WS04, WS08, WS09.* This is the most important unblocking task.

- [ ] **WS03: Statistical Testing** -- Add scipy-based significance tests to `evaluation/`: Mann-Whitney U, bootstrap confidence intervals, Cohen's d effect sizes, sensitivity analysis over scoring weights. *Low complexity. High impact. Blocks WS05.* Required to formally reject or retain the null hypothesis.

- [ ] **WS06: CI/CD** -- GitHub Actions workflow running `pytest`, `ruff check`, and type checking on every push and PR. Badge in README. *Low complexity. Moderate impact. Blocks nothing.* Prevents silent regressions.

- [ ] **WS07: Conditional VAE** -- End-to-end VAE pipeline: data prep, training loop, generation script, integration into `generation/` as a new strategy. Produces genuinely novel molecules from learned latent space, conditioned on conformational state. *High complexity. High impact. Blocks nothing directly (WS01 helpful but not required).*

---

## 4. Planned: Group B Workstreams (After WS01 Completes)

All four depend on `statebind.chemistry` from WS01. Within the scoring chain (WS02/WS04/WS08), execution must be **sequential** to avoid merge conflicts in `ranking/scoring.py`.

- [ ] **WS02: Scoring Integration** -- Wire RDKit chemistry into the unified scoring function. Replace n-gram Tanimoto with Morgan/ECFP4 similarity, replace heuristic druglikeness with QED + Lipinski + SA score. *Low complexity. High impact.* **Run FIRST in scoring chain.**

- [ ] **WS04: Docking Proxy** -- Build a small MLP discriminator on molecular descriptors as an intermediate docking proxy. Replaces the constant-0.5 stub with a model that at least discriminates between structures. *Moderate complexity. Critical impact.* **Run SECOND in scoring chain.**

- [ ] **WS08: MPNN Affinity** -- Integration adapter wiring the trained MPNN into `ranking/scoring.py`. Cascading fallback: MPNN -> docking proxy -> stub. Normalized pIC50 output. *High complexity. Critical impact.* **Run THIRD in scoring chain.**

- [ ] **WS09: ADMET Predictor** -- Integration adapter wiring the trained ADMET model into the filtering pipeline. Pass/fail gate for hERG liability (probability > 0.5) and CYP3A4 inhibition. Does NOT modify `ranking/scoring.py` -- no conflict with scoring chain. *High complexity. High impact.*

---

## 5. Planned: Group C (After WS03 Completes)

- [ ] **WS05: Visualization** -- Publication-quality matplotlib/seaborn figures: score distributions, chemical space UMAP, state atlas heatmaps, comparison bar charts with error bars. Requires statistical testing infrastructure from WS03 for confidence intervals and p-values on plots. *Low complexity. Moderate impact.*

---

## 6. Integration Tasks (After ML Training Complete)

These tasks connect trained models into the running pipeline and re-execute the central experiment.

- [ ] **Wire MPNN into scoring** -- Replace `_score_docking_stub()` in `ranking/scoring.py` with MPNN inference. Cascading fallback chain: MPNN (if checkpoint exists) -> docking proxy (if WS04 complete) -> constant 0.5 stub. Validate that `_validate_weights()` still passes.

- [ ] **Wire VAE into generation** -- VAE-sampled SMILES become `StateConditionedCandidate` objects with `source="ML_GENERATED"`, `strategy="VAE_GENERATED"`. Route through existing filtering -> ranking -> evaluation pipeline unchanged.

- [ ] **Wire ADMET into filtering** -- Add ADMET pass/fail gate between generation and ranking. Flag hERG liability, CYP3A4 inhibition, poor solubility. Candidates failing critical endpoints are excluded from ranking or tagged with penalty.

- [ ] **Re-run full comparison** -- Regenerate all candidates (VAE-generated replacing string-modified), re-score with the full cascade scoring function, re-run `scripts/compare_baseline_vs_state_aware.py`. Apply Mann-Whitney U test. Target: p < 0.05 on at least one primary metric (mean composite score, top-10 composition, or affinity distribution).

- [ ] **Update reports and artifacts** -- Regenerate all reports in `reports/` and artifacts in `artifacts/` with new results. Update README with current metrics. If null hypothesis is rejected, report the finding with effect size. If not rejected, report that with equal rigor.

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
| Pipeline (Phases 0-7) | Complete (12 modules, 359 tests) | Maintain |
| ML code | Written, untrained | Prepare training data |
| Scoring function | 20% dead weight (docking stub) | WS01 -> WS02 -> WS08 |
| Statistical testing | None (descriptive only) | WS03 |
| Null hypothesis | Not rejected | Pending real scoring + stats |
| Workstreams | 0 of 9 complete | Start Group A |
