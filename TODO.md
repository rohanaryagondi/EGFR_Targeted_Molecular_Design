# StateBind Roadmap

## Phase 0: Scaffold
- [x] Repository structure
- [x] pyproject.toml
- [x] Documentation (Charter, Architecture, Phase Plan, Decisions, Runbook)
- [x] Module placeholders with `__init__.py`
- [x] Utility modules (config, io)
- [x] CLI entrypoint
- [x] Test suite (imports, structure, utils, CLI)
- [x] .gitignore
- [x] Push to GitHub

## Phase 1: Context & Data
- [ ] EGFR mutation data model (Pydantic)
- [ ] Mutation atlas curation script
- [ ] Data loaders for COSMIC/ClinVar
- [ ] Mutation → resistance mechanism mapping
- [ ] Context query API
- [ ] Unit tests
- [ ] Phase 1 report

## Phase 2: Structure Atlas
- [ ] PDB downloader for EGFR structures
- [ ] DFG-in/out geometric classifier
- [ ] αC-helix position classifier
- [ ] State atlas builder
- [ ] Pocket extraction
- [ ] Visualization
- [ ] Unit tests
- [ ] Phase 2 report

## Phase 3: Dynamics & State Prediction
- [ ] Mutation → state preference lookup table
- [ ] Simple ML predictor (if data supports)
- [ ] Validation against known associations
- [ ] Unit tests
- [ ] Phase 3 report

## Phase 4: Molecular Generation
- [ ] Pocket representation for generation
- [ ] Fragment-based or SMILES-based generator
- [ ] Static baseline generation
- [ ] State-aware generation
- [ ] Unit tests
- [ ] Phase 4 report

## Phase 5: Ranking & Benchmarking
- [ ] Scoring functions (docking proxy, shape)
- [ ] Baseline comparison pipeline
- [ ] Statistical analysis
- [ ] Unit tests
- [ ] Phase 5 report

## Phase 6: Integration & Demo
- [ ] End-to-end pipeline script
- [ ] Demo notebook
- [ ] Final report with figures
- [ ] README polish
- [ ] Repository cleanup
