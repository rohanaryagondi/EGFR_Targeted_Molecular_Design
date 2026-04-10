# Continuation Prompt for Next AI Session

Copy everything below the line and paste it as your first message.

---

We are replacing StateBind's broken SELFIES GRU VAE with a Transformer VAE. The model code, tests, configs, training scripts, generation scripts, and SLURM scripts are all written and tested. A hyperparameter sweep found the optimal config (kl_weight=1.0, word_dropout=0.1). Production training was submitted on 2026-04-10 as two SLURM array jobs:

- **Job 7880395**: Conditioned 3-state model, 3 seeds (42, 123, 7)
- **Job 7880397**: Unconditioned model (Ablation C), 3 seeds (42, 123, 7)

Read `docs/transformer-vae-handoff.md` for the full context -- it has the sweep results table, all file paths, architecture details, known bugs, and what to do next.

Check whether those jobs have completed (`squeue -u rag88`). If they have:

1. **Extract results** from the logs (`logs/tfm_vae_3s_7880395_*.out` and `logs/tfm_vae_uc_7880397_*.out`). Check early stopping epoch, best val loss, validity rates, unique counts. Expected: >90% greedy validity, >80% stochastic validity.

2. **Verify outputs exist**: checkpoints at `artifacts/models/transformer_vae/seed_*/best_model.pt` and generation JSON at `artifacts/generation/transformer_vae_*.json`.

3. **Run validation checks** (on SLURM, not login node): reconstruction Tanimoto, aromatic ring count, scaffold overlap, nearest-neighbor similarity, drug proximity. Targets are in the handoff doc. These require loading the trained models, so submit as a GPU job.

4. **Write training results** documenting per-seed metrics and cross-seed variance.

5. **Proceed to integration handoff**: the generation artifacts are already compatible with `statebind.generation.vae_integration.load_vae_candidates()`. Document what's ready for the Phase 1 experiment re-run (Ablation C: conditioned vs unconditioned).

If jobs are still running, tell me and wait. If any failed, check `.err` files and diagnose. The user has said compute is not an issue -- up to 15 concurrent SLURM jobs are fine, and quality should not be compromised.

Important context:
- Always run compute (pytest, training, generation) on SLURM, not the login node
- The user prefers the `priority` queue (`-p priority -A prio_gerstein`) for fast scheduling
- There is a pre-existing flaky test to deselect: `--deselect tests/test_docking.py::TestDockingWrapper::test_vina_score_range`
- Read `CLAUDE.md` and `CRITICAL.md` in the repo root for project rules
