# StateBind — Development Roadmap

## Current Status
All 7 pipeline phases are implemented. ML models (VAE, MPNN, ADMET) are coded
but require training. 6 independent workstreams are defined for parallel development.

## Priority 1: ML Model Training (New)
- [ ] Prepare ChEMBL EGFR bioactivity dataset for VAE/MPNN training
  - Query ChEMBL for EGFR IC50 data (target: CHEMBL203)
  - Convert to pIC50, filter quality, assign conformational states
  - Output: data/processed/egfr_smiles_train.json, egfr_affinity.json
- [ ] Prepare TDC ADMET benchmark data
  - Download Caco-2, hERG, CYP3A4, Clearance, Lipophilicity, Solubility from TDC
  - Merge into unified multi-task JSON
  - Output: data/processed/admet_combined.json
- [ ] Train Conditional SMILES VAE (Workstream 07)
  - `python scripts/train_vae.py --config configs/vae.yaml`
  - Validate: reconstruction accuracy > 80%, KL convergence, novel SMILES generation
- [ ] Train MPNN Binding Affinity Predictor (Workstream 08)
  - `python scripts/train_mpnn.py --config configs/mpnn.yaml`
  - Validate: test RMSE < 1.0 pIC50 units, R² > 0.5
- [ ] Train Multi-Task ADMET Predictor (Workstream 09)
  - `python scripts/train_admet.py --config configs/admet.yaml`
  - Validate: per-task metrics vs TDC leaderboard baselines

## Priority 2: Integration (After Training)
- [ ] Wire MPNN predictions into ranking/scoring.py to replace docking stub
  - Cascading fallback: MPNN → proxy → stub (constant 0.5)
  - Update scoring weights to reflect real discriminative signal
- [ ] Wire VAE-generated candidates into generation pipeline
  - VAE candidates → StateConditionedCandidate (source=ML_GENERATED, strategy=VAE_GENERATED)
  - Run through same filtering → ranking → evaluation pipeline
- [ ] Wire ADMET predictions into candidate filtering
  - Add ADMET pass/fail gate before scoring
  - Flag hERG liability and CYP3A4 inhibition

## Priority 3: Existing Workstreams (Parallel)
- [ ] Workstream 01: RDKit chemistry foundation (Morgan fingerprints, descriptors)
- [ ] Workstream 02: Wire chemistry into scoring (replace n-gram similarity)
- [ ] Workstream 03: Statistical testing (Mann-Whitney U, bootstrap CI)
- [ ] Workstream 04: Small MLP docking proxy (fallback for MPNN)
- [ ] Workstream 05: Visualization (Matplotlib figures)
- [ ] Workstream 06: CI/CD (GitHub Actions)

## Priority 4: Stretch Goals
- [ ] Transfer learning: pre-train MPNN on ChEMBL-wide, fine-tune on EGFR
- [ ] Active learning loop: VAE generates → MPNN scores → retrain VAE on top candidates
- [ ] Ensemble scoring: combine MPNN + docking proxy for robustness
- [ ] Multi-objective optimization: Pareto frontier over affinity + ADMET

## Dependency Graph
```
Workstream 01 (chemistry) ← Workstream 02 (scoring integration)
Workstream 07 (VAE)       ← Integration: VAE → generation pipeline
Workstream 08 (MPNN)      ← Integration: MPNN → ranking/scoring
Workstream 09 (ADMET)     ← Integration: ADMET → filtering
Workstreams 03-06: independent, can run in parallel
```

## Completed
- [x] Phase 0: Project scaffolding and data curation
- [x] Phase 1: Data processing pipeline
- [x] Phase 2: Static baseline pipeline
- [x] Phase 3: Conformational state atlas
- [x] Phase 4: Mutation-to-state prediction
- [x] Phase 5: State transition world model
- [x] Phase 6: State-conditioned generation
- [x] Phase 7: Unified ranking and evaluation
- [x] ML infrastructure (src/statebind/ml/) — shared trainer, tokenizer, vocabulary, graphs
- [x] VAE model architecture (src/statebind/ml/vae.py)
- [x] MPNN model architecture (src/statebind/ml/mpnn.py)
- [x] ADMET model architecture (src/statebind/ml/admet.py)
- [x] Training scripts and configs (scripts/train_*.py, configs/*.yaml)
- [x] Multi-AI workstream documentation (workstreams/, per-module READMEs)
