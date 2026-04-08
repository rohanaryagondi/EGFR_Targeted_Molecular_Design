# Pipeline, Config & Debug Reference

Reference doc for AI agents. Auto-loaded CLAUDE.md points here.

---

## Config System

All configuration is driven by YAML files in `configs/`. Scripts accept a `--config`
CLI argument (convention, not enforced by framework). Configs are loaded via
`statebind.utils.config.load_config()` which returns a plain dict.

### Config Files

| File | Purpose | Used By |
|------|---------|---------|
| `configs/default.yaml` | Project-level defaults: name, version, paths, logging | All scripts (base config) |
| `configs/structure.yaml` | Structure module: PDB references, classification thresholds, output dirs | `scripts/build_state_atlas.py`, `scripts/run_structure.py` |
| `configs/context.yaml` | Context module: target gene (EGFR), UniProt ID (P00533), mutation list, sources | `scripts/build_context_dataset.py`, `scripts/run_context.py` |
| `configs/vae.yaml` | VAE hyperparameters: vocab_size=150, embed_dim=128, hidden_dim=256, latent_dim=64, KL annealing (20 epoch warmup) | `scripts/train_vae.py` |
| `configs/mpnn.yaml` | MPNN hyperparameters: hidden_dim=128, 3 message-passing layers, mean_max readout | `scripts/train_mpnn.py` |
| `configs/admet.yaml` | ADMET hyperparameters: GIN backbone, 6 tasks, task weights (hERG=1.5x) | `scripts/train_admet.py` |
| `configs/retrospective.yaml` | Retrospective validation: cutoff years, enrichment K values, similarity thresholds, reference binders | `scripts/run_retrospective_validation.py` |
| `configs/mpnn_pre2010.yaml` | MPNN retrained on pre-2010 data | `scripts/train_mpnn.py` |
| `configs/mpnn_pre2015.yaml` | MPNN retrained on pre-2015 data | `scripts/train_mpnn.py` |
| `configs/vae_pre2010.yaml` | VAE retrained on pre-2010 data (SELFIES) | `scripts/train_vae.py` |
| `configs/vae_pre2015.yaml` | VAE retrained on pre-2015 data (SELFIES) | `scripts/train_vae.py` |

### Config Convention

YAML structure: `model:` (hyperparameters), `training:` (epochs, LR, device),
`data:` (paths, splits). `training.device: auto` means auto-detect GPU/CPU.
`training.seed: 42` is the default. Checkpoints: `artifacts/models/{name}/`.
Logs: `artifacts/logs/{name}/`.

---

## Data Flow Per Phase

| Phase | Script(s) | Input | Output Artifacts |
|-------|-----------|-------|-----------------|
| 0 - Data validation | `scripts/validate_data_layout.py`, `scripts/register_sources.py` | `data/raw/*.json` | `artifacts/data/manifest.json` |
| 1 - Processing | `scripts/build_context_dataset.py`, `scripts/build_structure_dataset.py`, `scripts/build_ligand_dataset.py`, `scripts/assemble_benchmark.py` | `data/raw/` | `data/processed/*.json`, `artifacts/processing/benchmark.json` |
| 2 - Static baseline | `scripts/run_static_baseline.py`, `scripts/extract_baseline_pocket.py`, `scripts/select_baseline_structure.py` | `data/processed/`, `configs/default.yaml` | `artifacts/baselines/static_candidates.json`, `artifacts/baselines/ranked.json` |
| 3 - Structure atlas | `scripts/build_state_atlas.py`, `scripts/cluster_structural_states.py`, `scripts/compare_pockets_across_states.py` | `data/processed/structures.json`, `configs/structure.yaml` | `artifacts/structure/state_atlas.json`, `artifacts/structure/pockets/` |
| 4 - Context model | `scripts/train_context_state_model.py`, `scripts/train_context_baseline.py`, `scripts/evaluate_context_state_model.py` | `data/processed/`, `configs/context.yaml` | `artifacts/context/mutation_atlas.json`, `artifacts/context/model_metrics.json` |
| 5 - World model | `scripts/train_world_model.py`, `scripts/build_state_sequences.py`, `scripts/train_transition_baseline.py`, `scripts/evaluate_world_model.py` | `artifacts/structure/`, `artifacts/context/` | `artifacts/dynamics/world_model.json`, `artifacts/dynamics/transitions.json` |
| ML - VAE training | `scripts/train_vae.py` | `data/processed/egfr_smiles_train.json`, `configs/vae.yaml` | `artifacts/models/vae/best_model.pt`, `artifacts/logs/vae/` |
| ML - MPNN training | `scripts/train_mpnn.py` | `data/processed/egfr_affinity.json`, `configs/mpnn.yaml` | `artifacts/models/mpnn/best_model.pt`, `artifacts/logs/mpnn/` |
| ML - ADMET training | `scripts/train_admet.py` | `data/processed/admet_combined.json`, `configs/admet.yaml` | `artifacts/models/admet/best_model.pt`, `artifacts/logs/admet/` |
| 6 - Generation | `scripts/generate_state_conditioned_candidates.py`, `scripts/filter_generated_candidates.py` | `artifacts/structure/`, `artifacts/context/` | `artifacts/generation/candidates.json`, `artifacts/generation/filtered.json` |
| 7a - Ranking | `scripts/rerank_candidates.py` | `artifacts/baselines/`, `artifacts/generation/` | `artifacts/ranking/merged.json` |
| 7b - Evaluation | `scripts/compare_baseline_vs_state_aware.py`, `scripts/report_comparative_results.py`, `scripts/generate_final_summary.py` | `artifacts/ranking/merged.json` | `artifacts/evaluation/comparison.json`, `reports/*.md` |
| Retro - Time-split data | `scripts/build_timesplit_datasets.py`, `scripts/build_timesplit_vae_data.py` | ChEMBL EGFR data + `configs/retrospective.yaml` | `data/processed/timesplit_{cutoff}_train.json`, `data/processed/egfr_smiles_pre{cutoff}_*.json` |
| Retro - Validation | `scripts/run_retrospective_validation.py` | Time-split data + `configs/retrospective.yaml` + pre-cutoff model checkpoints | `artifacts/evaluation/retrained/retrospective_{cutoff}_retrained.json` |

### Execution Order (abbreviated)

```bash
# Phase 0-1    validate_data_layout.py -> build_context_dataset.py -> build_structure_dataset.py -> assemble_benchmark.py
# Phase 2      run_static_baseline.py
# Phase 3-5    build_state_atlas.py -> train_context_state_model.py -> train_world_model.py
# ML (opt)     train_vae.py, train_mpnn.py, train_admet.py
# Phase 6-7    generate_state_conditioned_candidates.py -> filter_generated_candidates.py -> rerank_candidates.py -> compare_baseline_vs_state_aware.py -> report_comparative_results.py
```

---

## Debug Guide

| # | Problem | Solution |
|---|---------|----------|
| 1 | `ModuleNotFoundError: No module named 'statebind'` | Run `pip install -e ".[dev]"` from project root. |
| 2 | `ImportError: cannot import name 'AffinityMPNN'` | Install ML deps: `pip install -e ".[ml]"`. The class requires torch. |
| 3 | `ValueError: Scoring weights must sum to 1.0` | Check `DEFAULT_WEIGHTS` in `ranking/scoring.py:86`. Your custom weights dict must have all 4 keys summing to 1.0. |
| 4 | `FileNotFoundError` on any data path | Use `DataPaths()` for resolution. Check `data/raw/` exists. Run `scripts/validate_data_layout.py`. |
| 5 | Tests fail with `assert statebind.__version__ == "0.1.0"` | Version is pinned in both `pyproject.toml:7` and `src/statebind/__init__.py`. Keep them in sync. |
| 6 | `pydantic.ValidationError` on model construction | Check field types match Pydantic v2 expectations. Common: `float` vs `int`, missing required fields. |
| 7 | All docking scores are 0.5 | The MPNN cascade is active. If all scores are 0.5, the MPNN and DockingProxy MLP both failed to load and the fallback stub is being used. Check that `artifacts/models/mpnn/best_model.pt` exists and torch is installed. |
| 8 | State-aware scores barely beat static | Expected. The state_specificity component is only 15% weight. The MPNN cascade now provides real docking signal (20% weight), but the static baseline still wins on mean score because VAE-generated molecules have lower reference similarity. |
| 9 | `torch_geometric` import fails despite torch being installed | PyG requires matching CUDA/torch versions. Install via: `pip install torch-geometric -f https://data.pyg.org/whl/torch-{version}+{cuda}.html` |
| 10 | Circular import error between modules | You violated the dependency graph. The import direction must flow downward. |
