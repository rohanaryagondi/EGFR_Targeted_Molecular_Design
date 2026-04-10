# Generation Module Fix — Agent Prompt

**Directory**: `/home/rag88/projects/statebind/repo/`

Copy everything below the line and paste it as your first message to a new Claude Code
session. Working directory must be the repo root shown above.

---

## Mission

The SELFIES VAE in StateBind is a non-functional autoencoder (0% reconstruction, zero
aromatic rings generated, zero active latent dimensions). You will evaluate two
replacement approaches, build the better one, and integrate it so that Phase 1
experiments can be re-run with a working generative model.

## Your Constraints

- Read `CLAUDE.md` and `CRITICAL.md` at the repo root before writing any code.
- All code must follow StateBind conventions: typed Python, Pydantic v2 models,
  config-driven, tests required, artifacts on disk as JSON.
- You have full access to Yale Bouchet HPC (SLURM). Account: `pi_mg269`. See
  `CLAUDE.md` for partition details and GPU types.
- Existing tests (799+) must continue to pass. Run `pytest -x -q` before committing.
- Do not modify scoring, evaluation, or retrospective modules. Your changes are
  limited to `src/statebind/ml/`, `scripts/`, `configs/`, `tests/`, and
  the generation JSON artifact format (which must remain backward-compatible).

## Context Documents (READ THESE FIRST)

All in `IdeationDept/Planner/output/phases/phase-01-core-experiments/generation-fix/`:

1. **`context.md`** — Full diagnosis of the VAE failure, current architecture details,
   integration points, training data, evaluation targets. **Read this first.**
2. **`option-3-reinvent.md`** — REINVENT-style language model approach.
3. **`option-4-transformer-vae.md`** — Transformer VAE with SMILES approach.

Also read:
- `artifacts/evaluation/vae_diagnostics/synthesis.json` — the 15-test root cause analysis
- `src/statebind/ml/vae.py` — current (broken) VAE code
- `configs/vae.yaml` — current VAE config

## Phase 1: Deliberate (1-2 hours)

Evaluate both options against these criteria, then choose ONE to implement.

### Evaluation Criteria

| Criterion | Weight | Option 3 (REINVENT) | Option 4 (Transformer VAE) |
|-----------|--------|--------------------|-----------------------------|
| **Thesis alignment** | HIGH | State conditioning is indirect (via scoring). Tests "does state-aware scoring help generation?" | State conditioning is architectural. Tests "does state-aware generation help?" — the actual thesis. |
| **Ablation C compatibility** | HIGH | Needs redesign: conditioned = per-state agent, unconditioned = generic agent. Different paradigm. | Drop-in replacement: same API, same Ablation C design. Conditioned vs unconditioned uses same framework. |
| **Ring generation** | HIGH | SMILES LM naturally generates rings. Proven. | Transformer attention + SMILES fixes both root causes. Needs validation. |
| **Posterior collapse** | HIGH | N/A (no VAE bottleneck). | Fixed by free bits + word dropout. Well-studied solutions. |
| **Implementation effort** | MED | 3a (wrap REINVENT 4): days. 3b (in-house): ~1 week. | ~1 week. New decoder + training loop + tests. |
| **Publication novelty** | MED | REINVENT is established. Comparison baseline, not novel. | State-conditioned Transformer VAE for kinases is novel. |
| **Latent space analysis** | LOW | No latent space. Can't interpolate or analyze state separation. | Full latent space for analysis, interpolation, state visualization. |

### Decision Rule

- If the thesis is "state-aware GENERATION outperforms static" → Option 4 is required
  (state must be in the model, not just the scorer).
- If the thesis is "state-aware SCORING outperforms static" → Either works, Option 3
  is faster.
- StateBind's thesis (see `CLAUDE.md`) is: "conformational state-aware molecular
  design outperforms static single-structure design." This is about the full pipeline,
  not just scoring. **Option 4 is the stronger test of this thesis** because it puts
  state information into the generative model itself.

Write your deliberation to
`IdeationDept/Planner/output/phases/phase-01-core-experiments/generation-fix/deliberation.md`
with your reasoning and final choice.

## Phase 2: Quick Validation (2-3 hours)

Before building the full implementation, run a quick proof-of-concept:

### If you chose Option 4 (Transformer VAE):
1. Build a minimal `ConditionalTransformerVAE` class (~200 lines)
2. Verify: forward pass works, generate produces valid SMILES tokens
3. Train for 20 epochs on a 500-molecule subset (submit to SLURM, ~5 min on GPU)
4. Check: (a) reconstruction Tanimoto > 0.1? (b) generated molecules have aromatic rings?
5. If YES to both: proceed. If NO: debug, or reconsider Option 3.

### If you chose Option 3 (REINVENT in-house):
1. Build a minimal SMILES language model (~150 lines)
2. Verify: forward pass works, sampling produces valid SMILES
3. Pre-train for 10 epochs on training data (submit to SLURM, ~5 min on GPU)
4. Check: (a) perplexity decreasing? (b) sampled molecules have aromatic rings?
5. If YES to both: proceed. If NO: debug architecture.

Write results to `generation-fix/validation-results.md`.

## Phase 3: Full Implementation (4-8 hours)

Build the complete module. Follow these requirements exactly:

### Code Requirements

1. **Config model** (Pydantic BaseModel): All hyperparameters in a config class.
   Corresponding YAML config in `configs/`.

2. **Model class** with this public API (must match or extend current VAE API):
   ```python
   model.encode(x, lengths, state_onehot) -> (mu, logvar)  # if VAE
   model.sample(mu, logvar) -> z                            # if VAE
   model.generate(z_or_none, state_onehot, max_len, temperature, vocab) -> list[list[int]]
   model.forward(...) -> (logits_or_recon, ...)
   ```

3. **Training script** in `scripts/`:
   - Reads config YAML
   - Handles SLURM (device auto-detection, logging, checkpointing)
   - Saves checkpoint compatible with generation script
   - Logs to stderr for SLURM capture

4. **Generation script** in `scripts/`:
   - Loads checkpoint
   - Generates N candidates per state
   - Validates with RDKit
   - Writes JSON artifact with schema:
     ```json
     {
       "model_config": {...},
       "temperature": 0.8,
       "n_per_state": 100,
       "candidates": [
         {"smiles": "...", "state": "DFGin_aCin", "is_valid": true, "source": "..."}
       ]
     }
     ```

5. **Tests** in `tests/`:
   - Model instantiation from config
   - Forward pass shape correctness
   - Generate produces list of token sequences
   - Loss computation (if VAE: reconstruction + KL with free bits)
   - Config serialization round-trip
   - At least 15 tests

6. **SLURM scripts** in `scripts/`:
   - Training: GPU partition, appropriate resources
   - Generation: Can be CPU or GPU

### Training Requirements

- Train the model on the full EGFR dataset (5995 train / 1542 val)
- 3 seeds (42, 123, 7) for reproducibility
- Save best checkpoint per seed (by val loss)
- Log training curves to stderr

### Validation After Training

After training completes, run these sanity checks (you can adapt the existing
diagnostic scripts in `scripts/vae_diagnostic_gpu.py` and `scripts/vae_diagnostic_cpu.py`):

1. **Reconstruction**: Encode 500 training molecules, decode — mean Tanimoto > 0.3 (if VAE)
2. **Aromatic rings**: Generated molecules should have mean aromatic rings > 1.0
3. **Scaffold overlap**: Some overlap between generated and training scaffolds
4. **NN to training**: Mean nearest-neighbor similarity to training > 0.3
5. **Drug proximity**: Max Tanimoto to any future drug > 0.3 from 300 generated molecules
6. **Validity**: > 80% valid SMILES (if SMILES-based)

If ANY of these fail, debug before proceeding. Do not just accept poor results.

Write validation results to `generation-fix/training-results.md`.

## Phase 4: Integration + Ablation Prep (1-2 hours)

1. Update `src/statebind/generation/vae_integration.py` to also handle the new
   model's output format (should be backward-compatible if JSON schema matches).

2. Add the new `GenerationStrategy` enum member to `generation/models.py`.

3. Create unconditioned config (n_states=1) for Ablation C.

4. Create SLURM scripts for Ablation C training (3 seeds x 2 conditions = 6 runs).

5. Run `pytest -x -q` — all existing tests must pass, plus your new tests.

6. Write a handoff document at `generation-fix/HANDOFF.md` for the human operator
   that summarizes:
   - Which option was chosen and why
   - Training results (per-seed metrics)
   - Validation results (the 6 sanity checks)
   - What's ready for Phase 1 re-run
   - Any known issues or limitations

## Important Notes

- **Do not modify** `src/statebind/ranking/`, `src/statebind/evaluation/`,
  `src/statebind/baselines/`, or `src/statebind/processing/`.
- **Do not delete** the old VAE code (`src/statebind/ml/vae.py`). Keep it for
  reference and backward compatibility. Add the new model alongside it.
- **Config-driven**: No hard-coded hyperparameters. Everything in YAML.
- **Checkpoint format**: Save as PyTorch `.pt` file with `model_state_dict`,
  `config`, `vocab`, `tokenizer_type`, and `epoch`.
- **SLURM**: Use `scavenge_gpu` partition for training (preemptable but fast scheduling).
  Use `--requeue` flag. Fallback to `gpu_devel` if scavenge is unreliable.
  Account: `-A pi_mg269`.
- **Max 3 parallel SLURM jobs** at a time (user preference).
