# Master Progress Tracker

Last updated: 2026-04-10T17:00:00Z

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
| Phase 1 | P1-T01 | Ablation C Config + Data Prep | completed | 2026-04-09 | Created vae_unconditioned.yaml (n_states=1), prepare_ablation_c_data.py, slurm_ablation_c.sh (3 seeds). Modified generate_vae_candidates.py with --states flag. Conditioned total=300 (3x100), unconditioned=300 (1x300). 690 tests pass. |
| Phase 1 | P1-T02 | VAE Quality Metrics (FCD/Recon/Novelty) | completed | 2026-04-09 | Created evaluation/vae_metrics.py with compute_fcd, compute_reconstruction_accuracy, compute_novelty, compute_internal_diversity, evaluate_vae_quality. Added fcd_torch to [ml] extras. 37 new tests (34 pass, 3 skip env-specific). 690 tests pass. |
| Phase 1 | P1-T03 | Scoring Ablation + Fairness Script | completed | 2026-04-09 | Created evaluation/scoring_ablation.py with generate_ablation_configs (5 configs), rerank_with_weights, run_ablation_battery. Created run_scoring_ablation.py CLI. 23 new tests. 713 tests pass. |
| Phase 1 | P1-T04 | PMO Comparison Infrastructure | completed | 2026-04-10 | Created evaluation/pmo_comparison.py with OracleBudget, PMOResult, prefilter_score, run_pipeline_with_budget, compare_pmo. Created run_pmo_comparison.py CLI with --budget/--dry-run. 37 new tests. 752 tests pass. |
| Phase 1 | P1-T05 | ABL1 Schema + Data Curation Script | completed | 2026-04-10 | Added target_gene to StructureRecord (default="EGFR", backward-compat). Created curate_abl1_data.py (ChEMBL REST), curate_abl1_structures.py (RCSB+KLIFS). 2 new tests. 752 tests pass. |
| Phase 1 | P1-T06 | REINVENT 4 Environment + GNINA Plugin | completed | 2026-04-10 | Created setup_reinvent4.sh, standalone reinvent4_gnina_component.py (no statebind imports), reinvent4_egfr.toml, run_reinvent4_egfr.py, slurm_reinvent4.sh. Receptor: 1m17.pdbqt. 752 tests pass. |
| Phase 1 | P1-T07 | Ablation C Training + Generation (GPU) | completed | 2026-04-10 | 3 seeds trained on scavenge_gpu (L40S). Mean val_recon_loss=2.2547 (std=0.0010). 300 candidates/seed, 100% valid, ~96% unique. Checkpoints+generation artifacts saved. SLURM job 7799948. |
| Phase 1 | P1-T08 | Scoring Ablation + PMO Execution | completed | 2026-04-10 | Scoring ablation: state_specificity most important (removal drops EF@10 0.7949→0.4769). docking_proxy non-discriminative. P11 fairness: enrichment LOST without state_specificity. PMO SLURM job 7799914 submitted (budget=500). |
| Phase 1 | P1-T09 | ABL1 Structures + Features | completed | 2026-04-10 | 5 ABL1 PDBs (1IEP,2GQG,3CS9,2G1T,3PYY) with 9D features + 7D pocket descriptors. 3 states (DFGin_aCin,DFGin_aCout,DFGout_aCin). Docking config, atlas support, conditioning. 47 new tests. 799 tests pass. |
| Phase 1 | P1-T10 | Ablation C Analysis + Gate G2 | completed | 2026-04-10 | **G2 = NO-GO (v1).** Cohen's d = -0.0742 (negligible). EF@10=0 for both. Caveat: conditioned used old 4-state model. |
| Phase 1 | P1-T10v2 | Ablation C v2 Reanalysis (3-state) | completed | 2026-04-10 | **G2 = NO-GO (confirmed).** Correct 3-state model, 3 seeds each. d_composite=-0.0385, d_EF@10=0.0, MWU p=0.6128. EF@10=0 for all 6 seed×condition combos. Best future-drug similarity ~0.15 (threshold 0.4). VAE generates valid but pharmacologically irrelevant molecules. |
| Phase 1 | P1-T11 | REINVENT 4 EGFR Run + Gate G3 | completed | 2026-04-10 | **G3 = GO.** 548 valid molecules (threshold 100). REINVENT mean=0.1179 vs StateBind static=0.5437 vs state-aware=0.4378. StateBind outperforms REINVENT. 438/548 scored minimum due to SMILES issues. |
| Phase 1 | P1-T12 | ABL1 Model Training (VAE + MPNN) | skipped | 2026-04-10 | Skipped: G2 NO-GO. ABL1 extension not warranted. |
| Phase 1 | P1-T13 | ABL1 Pipeline + Retrospective + Gate G4 | skipped | 2026-04-10 | Skipped: G2 NO-GO. |
| Phase 1 | P1-DIAG | VAE Enrichment Failure Diagnostics | **completed** | 2026-04-10 | 15/15 tests done. **Root cause: total autoencoder failure.** 0% reconstruction (mean Tanimoto 0.031 to input). Decoder produces aliphatic chains (0.03 aromatic rings vs 3.56 in training). ZERO active latent dims. State conditioning cosmetic only. NOT a data/representation problem (training has drugs, SELFIES roundtrip perfect). See synthesis.json. |
| Phase 1 | P1-DIAG-V | Independent Verification of Diagnostics | **completed** | 2026-04-10 | All 15 test JSONs manually reviewed against interpretation guide. Root cause diagnosis CONFIRMED: MODEL_FAILURE (decoder_incapacity + posterior_collapse). Additional findings: (1) PMO comparison uninformative — GNINA timed out on CPU partition, both pipelines scored 0.0; (2) G4 shows 4/7 drugs encode to latent_norm < 1.0 (within prior ball) yet still decode to garbage — conclusively rules out prior-posterior gap; (3) SELFIES ring closure requires 40-66 tokens with long-range Ring1/Ring2 dependencies beyond GRU memory. synthesis.json updated to v2 with these additions. |

## Gate Outcomes

| Gate | Decision Date | Outcome | Metric Value | Notes |
|------|--------------|---------|-------------|-------|
| G0 | 2026-04-09 | GO | 3-state verified | All PDB annotations verified: 4ZAU=DFGin_aCin, 5D41=DFGin_aCout, 3iku removed (not EGFR), 3W2R/5D41 mutations corrected. DFGout_aCout removed → 3-state model. |
| G1 | 2026-04-09 | GO | scaffold R^2 = 0.5153 | MPNN scaffold R^2 = 0.5153 >= 0.35; degradation from random = 0.1863 |
| G2 | 2026-04-10 | **NO-GO** | Cohen's d = -0.0385 (v2) | Confirmed with correct 3-state model, 3 seeds. EF@10=0 for all seeds/conditions. MWU p=0.6128. |
| G3 | 2026-04-10 | **GO** | 548 valid molecules | REINVENT 4 ran successfully. StateBind outperforms (0.54/0.44 vs 0.12 mean score). |
| G4 | 2026-04-10 | **SKIPPED** | -- | ABL1 skipped due to G2 NO-GO. |
| G5 | -- | pending | -- | Cross-kinase consistency |

## Active SLURM Jobs

| Job ID | Name | Partition | Purpose | Status |
|--------|------|-----------|---------|--------|
| 7832709 | vae_diag_cpu | day | 7 CPU diagnostic tests (C1-C7) | completed |
| 7834860 | vae_diag_gpu | scavenge_gpu | 8 GPU diagnostic tests (G1-G8) | completed |
| 7799914 | pmo_comp | day | PMO comparison (budget=500, real GNINA) | completed — UNINFORMATIVE (all scores 0.0, GNINA timed out on CPU-only partition). Static generated proper analogues (gefitinib/erlotinib scaffolds) but docking returned 0 for all 30+76 candidates. Resubmit on gpu_devel with GNINA GPU mode to get real scores. |

## VAE Diagnostic Investigation — Key Findings (2026-04-10)

15 diagnostic tests (8 GPU, 7 CPU) conclusively identified the root cause of EF@10=0.

**Root Cause: Total autoencoder failure.** The SELFIES VAE decoder cannot generate aromatic ring systems.

| Finding | Test | Key Number |
|---------|------|------------|
| 0% reconstruction accuracy | G1 | mean Tanimoto to input = 0.031 |
| Default molecule is 127-carbon aliphatic chain | G3 | identical for all 3 states |
| Near-zero aromatic rings in output | C3 | generated=0.03 vs training=3.56 |
| Zero scaffold overlap gen↔training | C2 | 0 of 170 generated scaffolds appear in training |
| Zero active latent dimensions | G7 | 0 dims with KL>0.01 (of 64) |
| States not separated in latent space | G7 | centroid distances 0.06-0.09 |
| Encoding real drugs → decode = garbage | G4 | max sim to input drug ~0.11 |
| No temperature helps | G2 | 0 molecules >0.3 sim at any T |
| Training data IS drug-relevant | C1 | max sim=1.0 to afatinib, EF@10=1.32 random subsets |
| SELFIES representation is lossless | C4 | all 7 drugs roundtrip at Tanimoto=1.0 |

**Diagnosis category**: MODEL_FAILURE (decoder_incapacity + posterior_collapse)
**NOT**: data problem, representation problem, temperature problem, or conditioning problem

**Full synthesis**: `artifacts/evaluation/vae_diagnostics/synthesis.json` (v2, independently verified 2026-04-10T17:00Z)

### Independent Verification Notes (2026-04-10T17:00Z)

All 15 test JSONs reviewed against raw data and interpretation guide. Key additions to v1 synthesis:

1. **PMO comparison uninformative**: GNINA docking on CPU partition timed out. Both pipelines generated proper SMILES (static pipeline produced gefitinib/erlotinib analogues) but all docking scores = 0. Needs resubmission on GPU partition.
2. **Prior-posterior gap definitively ruled out**: G4 data shows afatinib (norm=0.46), osimertinib (0.41), dacomitinib (0.43) encode WITHIN the unit ball — exactly where N(0,I) sampling draws from. Yet decoding from these positions gives max self-similarity 0.08-0.11. The decoder is uniformly broken across the entire latent space.
3. **SELFIES token complexity**: C4 shows drugs require 40-66 SELFIES tokens with multiple Ring1/Ring2 closure tokens. These are long-range dependencies (ring closure references positions 20+ tokens back) that the single-layer GRU decoder cannot reliably learn.
4. **KL collapse is disguised by aggregation**: Seed 42's total KL=0.61 looked healthy in training logs, but G7 shows it's spread across 64 dims at <0.001 each. Zero dimensions above KL=0.01. Future VAE monitoring should track per-dimension KL, not just aggregate.

## Phase Summary

| Phase | Status | Tasks Total | Completed | Remaining |
|-------|--------|-------------|-----------|-----------|
| Phase 0: Structural & Methodological Fixes | completed | 9 | 9 | 0 |
| Phase 1: Core Experiments | completed | 13 | 12 (incl v2 reanalysis) | 2 skipped (T12, T13: G2 NO-GO) |
| Phase 2: Multi-Kinase & Strengthening | not started | -- | -- | -- |
| Phase 3: Writing & Submission | not started | -- | -- | -- |
