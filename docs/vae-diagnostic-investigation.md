# VAE Enrichment Failure — Diagnostic Investigation

**Date**: 2026-04-10
**Trigger**: Gate G2 NO-GO (confirmed v2). Ablation C shows Cohen's d = -0.04, EF@10 = 0 for all seeds/conditions.
**Question**: Why does the SELFIES VAE fail to generate molecules resembling future EGFR drugs?

## Background

The SELFIES VAE generates molecules that are:
- **Valid**: 100% validity (SELFIES guarantees this)
- **Novel**: 100% novelty vs training set (no exact matches)
- **Diverse**: Internal diversity ~0.92

But they are **structurally irrelevant**: best Tanimoto similarity to future drugs (afatinib, osimertinib, etc.) is ~0.15, well below the 0.4 threshold. EF@10 = 0 for both conditioned and unconditioned VAEs, across all 3 seeds.

The enrichment observed in the main StateBind pipeline (EF@10 = 4.95 static, 7.72 state-aware) comes entirely from analogue-based generation in `baselines/`, not from the VAE.

## Hypotheses

1. **VAE doesn't reconstruct** — The model can't even encode→decode its training set faithfully
2. **Training data doesn't cover drug space** — Future EGFR drugs may be distant from the training set in fingerprint space
3. **SELFIES destroys structural info** — The SELFIES→SMILES roundtrip may alter molecules
4. **Temperature too high** — T=0.8 sampling explores too far from the training manifold
5. **Posterior collapse** — Seeds 123/7 have near-zero KL (0.04/0.08), meaning the latent space is unused
6. **Conditioning has no effect** — The state label may not influence generation
7. **Prior-posterior gap** — Training from N(μ,σ²) but generating from N(0,I) creates a mismatch
8. **VAE generates generic druglike molecules** — Not EGFR-specific scaffolds

## Diagnostic Test Suite

### GPU Tests (scripts/vae_diagnostic_gpu.py, SLURM: slurm_vae_diag_gpu.sh)

| Test | Name | What It Measures | Key Output |
|------|------|-----------------|------------|
| G1 | Reconstruction accuracy | encode(train)→decode exact match rate & Tanimoto | `test_g1_reconstruction.json` |
| G2 | Temperature sweep | Generate at T={0,0.1,0.3,0.5,0.7,0.9,1.2}, measure drug proximity | `test_g2_temperature_sweep.json` |
| G3 | Greedy decoding | Argmax decode from z=0 for each state — the model's "default" molecule | `test_g3_greedy_decoding.json` |
| G4 | Drug seeding | Encode known EGFR drugs, add noise at 6 scales, decode neighbors | `test_g4_drug_seeding.json` |
| G5 | Conditioning check | Fix 50 z vectors, decode with each state label — do outputs differ? | `test_g5_conditioning.json` |
| G6 | Large batch (3000) | Generate 1000/state, measure max similarity to future drugs | `test_g6_large_batch.json` |
| G7 | Latent space stats | Encode 1000 training mols, analyze μ/σ per dimension, state separation | `test_g7_latent_space.json` |
| G8 | Cross-seed comparison | Compare KL and generation quality across seeds 42, 123, 7 | `test_g8_cross_seed.json` |

### CPU Tests (scripts/vae_diagnostic_cpu.py, SLURM: slurm_vae_diag_cpu.sh)

| Test | Name | What It Measures | Key Output |
|------|------|-----------------|------------|
| C1 | Training set drug proximity | Max Tanimoto from training molecules to each drug + random-subset EF@10 | `test_c1_training_proximity.json` |
| C2 | Scaffold analysis | Bemis-Murcko scaffolds in training, generated, and drugs — overlap matrix | `test_c2_scaffolds.json` |
| C3 | Descriptor distributions | MW, LogP, HBD, HBA, TPSA, rings: training vs generated vs drugs | `test_c3_distributions.json` |
| C4 | SELFIES roundtrip | SMILES→SELFIES→SMILES for all 7 EGFR drugs — identity preserved? | `test_c4_selfies_roundtrip.json` |
| C5 | Random SELFIES baseline | Generate 1000 random SELFIES molecules — drug proximity comparison | `test_c5_random_baseline.json` |
| C6 | Nearest-neighbor | For each generated mol, find NN in training — how far from training? | `test_c6_nearest_neighbor.json` |
| C7 | Per-state analysis | Drug proximity and NN stats broken down by conformational state | `test_c7_per_state.json` |

## How to Interpret Results

### If G1 (reconstruction) shows low accuracy (<30%):
→ The VAE hasn't learned to represent the training distribution. The encoder-decoder is broken.

### If C1 (training proximity) shows training set is also far from future drugs:
→ The training data itself doesn't cover future drug chemical space. Even perfect reconstruction wouldn't help. The enrichment failure is a data problem, not a model problem.

### If G2 (temperature) shows T=0 or T=0.1 gives much higher drug similarity:
→ The model has learned relevant structure but T=0.8 samples too far. Consider using lower temperature.

### If G4 (drug seeding) shows encode→decode recovers the drug at noise=0:
→ The drug is in the VAE's representational capacity. The issue is that prior sampling (z~N(0,I)) doesn't reach these regions.

### If G5 (conditioning) shows >50% identical outputs across states:
→ The state label is ignored. Conditioning doesn't work for this architecture/training regime.

### If G7 (latent space) shows few active dimensions and small state centroid distances:
→ Posterior collapse + no state separation. The latent space is a degenerate prior.

### If C5 (random baseline) shows similar drug proximity to VAE:
→ The VAE is not better than random SELFIES. It has learned validity but not chemical relevance.

### If C6 (nearest-neighbor) shows high NN similarity (>0.5):
→ Generated molecules are close to training, but training itself is far from drugs (see C1).

### If C6 shows low NN similarity (<0.3):
→ Generated molecules are in completely different chemical space from training. Mode collapse or sampling failure.

## Results Directory

All results saved to: `artifacts/evaluation/vae_diagnostics/`

```
test_g1_reconstruction.json      — Reconstruction accuracy
test_g2_temperature_sweep.json   — Temperature sweep
test_g3_greedy_decoding.json     — Greedy decoding
test_g4_drug_seeding.json        — Drug seeding
test_g5_conditioning.json        — Conditioning effectiveness
test_g6_large_batch.json         — Large batch generation
test_g7_latent_space.json        — Latent space statistics
test_g8_cross_seed.json          — Cross-seed comparison
test_c1_training_proximity.json  — Training set drug proximity
test_c2_scaffolds.json           — Scaffold analysis
test_c3_distributions.json       — Descriptor distributions
test_c4_selfies_roundtrip.json   — SELFIES roundtrip
test_c5_random_baseline.json     — Random SELFIES baseline
test_c6_nearest_neighbor.json    — Nearest-neighbor analysis
test_c7_per_state.json           — Per-state analysis
large_batch_smiles.json          — Raw SMILES from G6 (for further analysis)
```

## SLURM Jobs

```bash
# Submit both in parallel
cd $HOME/projects/statebind/repo
sbatch scripts/slurm_vae_diag_gpu.sh   # GPU: gpu_devel, 4h, H200
sbatch scripts/slurm_vae_diag_cpu.sh   # CPU: day, 2h
```

## Continuation

Once both jobs complete, read all 15 JSON artifacts and synthesize findings.
The handoff prompt for the next Claude Code session is in:
`IdeationDept/Planner/output/phases/phase-01-core-experiments/vae-diag-handoff.md`
