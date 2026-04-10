# Master Progress Tracker

Last updated: 2026-04-09T22:15:00Z

## Progress Table

| Phase | Task ID | Task Name | Status | Completed Date | Notes |
|-------|---------|-----------|--------|---------------|-------|
| Phase 0 | P0-T01 | Verify 4ZAU DFG Conformation | completed | 2026-04-09 | 4ZAU=DFGin_aCin, 5D41=DFGin_aCout. Both are DFGin, confirming no genuine DFGout EGFR structures. Project should switch to 3-state model. |
| Phase 0 | P0-T02 | Fix Osimertinib Reference Leakage | completed | 2026-04-09 | Removed osimertinib from _REFERENCE_BINDERS; updated test_chemistry.py and fingerprints.py docstring; 646/646 tests pass |
| Phase 0 | P0-T03 | MPNN Scaffold + Temporal Split (Code) | completed | 2026-04-09 | 7 new tests added (scaffold, temporal, backward compat, invalid type, no-rdkit, no-years) |
| Phase 0 | P0-T04 | Bootstrap CIs + BEDROC | completed | 2026-04-09 | BCa bootstrap (10k iters) + BEDROC via RDKit; 19 new tests (7 BCa, 8 BEDROC, 3 enrichment+CI, 1 integration); 658 pass |
| Phase 0 | P0-T05 | MPNN Scaffold Split Evaluation (GPU) | completed | 2026-04-09 | Gate G1 = GO; scaffold R^2 = 0.5153 (random R^2 = 0.7016, degradation = 0.1863); 0 scaffold overlap between train/test; MPNN remains credible scoring component |
| Phase 0 | P0-T06 | Fix Structural Annotations (Common) | completed | 2026-04-09 | Removed 3iku (ParM, not EGFR) from atlas; promoted 3w2r to DFGout_aCin representative with mutations=["T790M","L858R"]; fixed 5d41 mutations to ["L858R","T790M"]; updated conditioning.py, ligands.py, docking.yaml, tests; 658 tests pass |
| Phase 0 | P0-T07 | Remove DFGout_aCout (3-State Switch) | completed | 2026-04-09 | Removed DFGOUT_ACOUT from ConformationalState enum, structures.py, features.py, conditioning.py, docking.py, vae.py, vae_dataset.py, docking_analysis.py, sequences.py, clustering.py, context/features.py. Updated 3 VAE configs + docking.yaml. Updated 10 test files + 6 scripts. State specificity scoring now uses enum count. 656 tests pass, 13 skipped. |
| Phase 0 | P0-T08 | VAE Retrain (3-State) | completed | 2026-04-09 | SELFIES VAE retrained with n_states=3 on scavenge_gpu (H200). 300 epochs in 21.4 min. Best epoch 295: val_recon_loss=2.235, val_total_loss=2.2415, val_kl=0.6475. Train: 5995 samples, Val: 1542 samples (DFGout_aCout filtered). 9.5M params. Checkpoint verified loading with n_states=3. Old 4-state checkpoint backed up. |
| Phase 0 | P0-T09 | Pre-Registration Document | completed | 2026-04-09 | Commit 9e7cf96. Pre-registered Ablation C hypothesis (Cohen's d >= 0.5), 3-state model, analysis plan (Mann-Whitney U + BCa bootstrap CIs + BEDROC). |

## Gate Outcomes

| Gate | Decision Date | Outcome | Metric Value | Notes |
|------|--------------|---------|-------------|-------|
| G0 | 2026-04-09 | GO | 3-state verified | All PDB annotations verified: 4ZAU=DFGin_aCin, 5D41=DFGin_aCout, 3iku removed (not EGFR), 3W2R/5D41 mutations corrected. DFGout_aCout removed → 3-state model. |
| G1 | 2026-04-09 | GO | scaffold R^2 = 0.5153 | MPNN scaffold R^2 = 0.5153 >= 0.35; degradation from random = 0.1863 |
| G2 | -- | pending | -- | Ablation C Cohen's d >= 0.5 |
| G3 | -- | pending | -- | REINVENT 4 integration |
| G4 | -- | pending | -- | ABL1 enrichment > 1.0 |
| G5 | -- | pending | -- | Cross-kinase consistency |

## Phase Summary

| Phase | Status | Tasks Total | Completed | Remaining |
|-------|--------|-------------|-----------|-----------|
| Phase 0: Structural & Methodological Fixes | completed | 9 | 9 | 0 |
| Phase 1: Core Experiments | planned | 13 | 0 | 13 |
| Phase 2: Multi-Kinase & Strengthening | not started | -- | -- | -- |
| Phase 3: Writing & Submission | not started | -- | -- | -- |
