---
type: handoff
created: 2026-04-10T05:40:00Z
purpose: Continue VAE enrichment failure investigation after overnight SLURM jobs complete
---

# VAE Diagnostic Investigation — Handoff

## What happened

Phase 1 Gate G2 = **NO-GO** (confirmed with correct 3-state model, 3 seeds).
Cohen's d = -0.04, EF@10 = 0 for all seeds of both conditioned and unconditioned VAE.
The SELFIES VAE generates valid molecules (100%) but they are structurally irrelevant
to EGFR drugs (max Tanimoto to future drugs ~0.15, threshold is 0.4).

We launched 15 diagnostic tests across 2 SLURM jobs to understand WHY.

## SLURM Jobs to Check

| Job ID | Name | Partition | Script | Tests | Status |
|--------|------|-----------|--------|-------|--------|
| 7832708 | vae_diag_gpu | gpu_devel | `scripts/slurm_vae_diag_gpu.sh` | G1-G8 (8 tests) | submitted |
| 7832709 | vae_diag_cpu | day | `scripts/slurm_vae_diag_cpu.sh` | C1-C7 (7 tests) | submitted |
| 7799914 | pmo_comp | day | `scripts/slurm_pmo.sh` | PMO comparison (budget=500, real GNINA) | running ~3h |

Check status: `squeue -u rag88` and `sacct -j <jobid> --format=JobID,State,Elapsed,ExitCode`

## Where to find results

All diagnostic JSON artifacts in: `artifacts/evaluation/vae_diagnostics/`

```
test_g1_reconstruction.json      — Can VAE reconstruct training molecules?
test_g2_temperature_sweep.json   — Does lower temperature help drug similarity?
test_g3_greedy_decoding.json     — What does the model's "default" molecule look like?
test_g4_drug_seeding.json        — Can we get drug-like molecules by encoding real drugs?
test_g5_conditioning.json        — Does the state label actually change output?
test_g6_large_batch.json         — With 3000 molecules, do we get closer to drugs?
test_g7_latent_space.json        — Latent space structure (active dims, state separation)
test_g8_cross_seed.json          — KL and quality comparison across seeds 42/123/7
test_c1_training_proximity.json  — How close is training data to future drugs?
test_c2_scaffolds.json           — Scaffold overlap: training vs generated vs drugs
test_c3_distributions.json       — Descriptor distributions (MW, LogP, etc.)
test_c4_selfies_roundtrip.json   — Do EGFR drugs survive SMILES↔SELFIES conversion?
test_c5_random_baseline.json     — Is VAE better than random SELFIES?
test_c6_nearest_neighbor.json    — How far are generated molecules from training?
test_c7_per_state.json           — Per-state breakdown of candidate quality
```

PMO comparison result (if job completed): `artifacts/evaluation/pmo_comparison.json`

## Interpretation guide

Full interpretation logic is in `docs/vae-diagnostic-investigation.md`. Key decision tree:

1. **Read C1 first** — if training data itself has max Tanimoto < 0.4 to future drugs,
   the failure is a data coverage problem, not a model problem.
2. **Read G1** — if reconstruction accuracy is low (<30%), the VAE fundamentally doesn't
   work as a molecular autoencoder.
3. **Read G2** — if T=0 gives much higher drug sim than T=0.8, temperature is the issue.
4. **Read G4** — if encoding real drugs + decoding at noise=0 recovers them, the VAE has
   capacity but prior sampling misses the right regions.
5. **Read G5 + G7** — together these tell you if conditioning and latent structure work.
6. **Read C5** — if random SELFIES match VAE drug proximity, the VAE adds no value.
7. **Read C2** — if drug scaffolds aren't in training or generated sets, scaffold coverage
   is the bottleneck.

## What to do next

1. Read all 15 JSON files and synthesize a diagnosis
2. Check PMO job results (may have completed or timed out)
3. Based on diagnosis, decide:
   - **If data coverage problem**: The VAE can't generate what it never saw. Pivot framing.
   - **If model problem (reconstruction fails)**: Architecture/training issues. Could try
     SMILES-based VAE, different architecture, or larger model.
   - **If sampling problem (drugs encodable but not reached by prior)**: Could try targeted
     sampling, lower temperature, or latent space optimization.
   - **If SELFIES problem**: Switch to SMILES representation for next iteration.
4. Update `IdeationDept/Planner/output/logs/progress.md` with findings
5. Decide Phase 2 direction based on G2 NO-GO + diagnostic insights

## Key files

| File | Purpose |
|------|---------|
| `docs/vae-diagnostic-investigation.md` | Full investigation plan + interpretation guide |
| `scripts/vae_diagnostic_gpu.py` | GPU diagnostic tests (G1-G8) |
| `scripts/vae_diagnostic_cpu.py` | CPU diagnostic tests (C1-C7) |
| `scripts/slurm_vae_diag_gpu.sh` | SLURM submission for GPU tests |
| `scripts/slurm_vae_diag_cpu.sh` | SLURM submission for CPU tests |
| `artifacts/evaluation/ablation_c_results_v2.json` | Ablation C v2 results (G2 NO-GO) |
| `artifacts/evaluation/scoring_ablation.json` | Scoring ablation (state_specificity most important) |
| `IdeationDept/Planner/output/logs/progress.md` | Master progress tracker |

## Early Findings (CPU tests completed during session)

The CPU tests finished within minutes and the results are conclusive. The smoking gun:

**C3 (Distributions):** Generated molecules have **0.0 aromatic rings** (training: 3.6).
The VAE generates aliphatic chains with tiny 3-membered rings, not drug scaffolds.

**C6 (Nearest-neighbor):** Mean NN similarity to training = **0.125**. Max = 0.225.
**Zero** generated molecules above 0.5 Tanimoto to any training molecule.
The VAE generates in a COMPLETELY DIFFERENT chemical space from its own training data.

**C2 (Scaffolds):** Training has 1168 scaffolds, generated has 170. **Zero overlap.**
Top generated scaffolds are cyclopropane/cyclopropene (C1CC1, C1=CC1).
Drug scaffolds (quinazoline) present in training but absent from generated.

**C1 (Training proximity):** Training data IS close to future drugs (max sim=1.0 to
afatinib, 380/2000 above 0.4). Random training subsets achieve EF@10=1.32.
**This is NOT a data problem — it's a model problem.**

**Diagnosis: The SELFIES VAE decoder is fundamentally failing to generate aromatic
ring systems.** It produces valid molecules (SELFIES guarantees this) but they are
trivial aliphatic fragments. The autoregressive decoder likely struggles with the
long-range token dependencies needed for ring closure in SELFIES notation.

The GPU tests (G1-G8) will confirm whether this is also visible in reconstruction
(G1), temperature-independent (G2), and whether the latent space even encodes
aromatic information (G7).

## Context from training logs

**Seed 42**: val_loss=2.235, KL=0.66 (healthy — latent space is used)
**Seed 123**: val_loss=2.255, KL=0.04 (near-collapse — latent space barely used)
**Seed 7**: val_loss=2.254, KL=0.08 (near-collapse)

All seeds produce EF@10=0. So even healthy KL doesn't help enrichment.
