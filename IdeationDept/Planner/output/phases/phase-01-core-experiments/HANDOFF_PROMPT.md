# Handoff Prompt for Next Claude Code Session

Copy everything below the line and paste it as your first message to a new Claude Code session
(same working directory: `IdeationDept/Planner/output/phases/phase-01-core-experiments/`).

---

Resume the VAE enrichment failure investigation for StateBind Phase 1.

**Context:** Gate G2 = NO-GO (confirmed). The SELFIES VAE generates valid but pharmacologically irrelevant molecules (EF@10=0, best Tanimoto to future drugs ~0.15). We submitted 15 diagnostic tests overnight to understand why.

**Your tasks:**

1. Check SLURM job status: `squeue -u rag88` and `sacct -j 7832708,7832709,7799914 --format=JobID,State,Elapsed,ExitCode`

2. If jobs completed, read all 15 JSON results from `artifacts/evaluation/vae_diagnostics/` (test_g1 through test_g8 and test_c1 through test_c7). Also check PMO results at `artifacts/evaluation/pmo_comparison.json`.

3. If any jobs failed, check `logs/vae_diag_gpu_<jobid>.err` and `logs/vae_diag_cpu_<jobid>.err` for errors. Fix and resubmit if needed.

4. Synthesize findings using the interpretation guide in `docs/vae-diagnostic-investigation.md`. The key question is: **Is the enrichment failure a data problem, a model problem, or a sampling problem?**

5. Write a synthesis report at `artifacts/evaluation/vae_diagnostics/synthesis.json` with:
   - Root cause diagnosis (which hypothesis is supported)
   - Evidence from each test
   - Implications for the project
   - Recommended next steps

6. Update `IdeationDept/Planner/output/logs/progress.md` with the diagnostic findings.

**Key files:**
- `docs/vae-diagnostic-investigation.md` — full investigation plan + interpretation guide
- `vae-diag-handoff.md` (this directory) — detailed context including SLURM job IDs
- `artifacts/evaluation/ablation_c_results_v2.json` — the G2 NO-GO results
- `artifacts/evaluation/scoring_ablation.json` — scoring component importance

**Early finding (CPU tests completed during setup):** The SELFIES VAE generates molecules with **0.0 aromatic rings** (training avg: 3.6). NN similarity to training = 0.125. Zero scaffold overlap between generated and training. The VAE is producing trivial aliphatic fragments, not drug-like molecules. This is a model/representation problem, not a data problem (training data itself achieves EF@10=1.32 in random subsets). The GPU tests (G1-G8) will tell you if this is also visible in reconstruction accuracy and latent space structure.

**Do not** modify code or submit new SLURM jobs without checking with me first. Focus on analysis and synthesis.
