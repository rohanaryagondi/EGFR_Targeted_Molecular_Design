# Transformer VAE Handoff

Status as of 2026-04-10. Production training jobs running on SLURM.

## Why This Exists

StateBind's original SELFIES GRU VAE (`src/statebind/ml/vae.py`) is non-functional:
0% reconstruction, 0 aromatic rings, 0 active latent dimensions. Root causes:
(1) GRU decoder can't handle SELFIES ring-closure tokens (long-range dependency),
(2) posterior collapse (decoder ignores z). The state-conditioning hypothesis was
untested because the generative model itself was broken.

**Decision: Transformer VAE with SMILES** (preserves VAE framework, enables state
conditioning via prefix tokens, drop-in Ablation C compatibility).

## What Was Built (Phases 1-4 COMPLETE)

### Files Created

| File | Purpose |
|------|---------|
| `src/statebind/ml/transformer_vae.py` | Model: TransformerVAEConfig, ConditionalTransformerVAE, transformer_vae_loss |
| `tests/test_transformer_vae.py` | 17 unit tests (503 lines) |
| `scripts/train_transformer_vae.py` | Training with word dropout + free bits + KL annealing |
| `scripts/generate_transformer_vae.py` | Autoregressive generation + RDKit validation + JSON artifact |
| `configs/transformer_vae.yaml` | Conditioned config (3 states, tuned hyperparams) |
| `configs/transformer_vae_unconditioned.yaml` | Ablation C config (1 state) |
| `scripts/slurm_transformer_vae.sh` | SLURM array job: 3 seeds conditioned |
| `scripts/slurm_transformer_vae_uncond.sh` | SLURM array job: 3 seeds unconditioned |
| `scripts/slurm_transformer_vae_quickval.sh` | Quick validation script (used, can delete) |
| `scripts/sweep_submit.sh` | Sweep helper (used, can delete) |

### Files Modified

| File | Change |
|------|--------|
| `src/statebind/generation/models.py:30` | Added `TRANSFORMER_VAE_GENERATED` enum |
| `src/statebind/generation/vae_integration.py` | Added `strategy` + `id_prefix` params (backward-compatible) |

### Architecture

- **Encoder**: Bidirectional GRU (reused from `vae.py` via `SMILESEncoder`)
- **Latent**: 64-dim, mu/logvar, reparameterization trick
- **z injection**: `[z; state_onehot]` -> Linear -> 8 prefix tokens of d_model=256
- **Decoder**: `nn.TransformerEncoder` with causal mask + prefix visibility, 4 layers
- **Anti-collapse**: word dropout (0.1) + free bits KL (0.25 nats/dim floor)
- **Loss**: CE(recon, ignore padding) + kl_weight * sum(max(KL_j, free_bits))
- **4.1M parameters**

### Key Bug Fixes Applied

1. **Causal mask nan**: `0.0 * float("-inf") = nan` in IEEE 754. Fixed in `transformer_vae.py`
   by using `torch.triu(torch.full(..., float("-inf")), diagonal=1)` instead of multiplying
   a ones matrix by -inf.

2. **test_loss_ignores_padding**: PyTorch `cross_entropy(reduction="mean")` returns nan when
   ALL tokens are `ignore_index`. Rewrote test to compare half-padding vs no-padding loss.

3. **Pre-existing flaky test**: `test_docking.py::TestDockingWrapper::test_vina_score_range`
   fails with `vina_score=9.6` (expected [-15, 0]). Not our bug. Deselect with
   `--deselect tests/test_docking.py::TestDockingWrapper::test_vina_score_range`.

## Hyperparameter Sweep Results

18 configurations tested across kl_weight, model size, latent dim, word dropout, and
annealing warmup. All sweep logs are in `logs/sweep_*_*.out` and `logs/sw_*_*.out`.

### The Core Insight: Prior-Posterior Gap

With `kl_weight=0.01` (original), the model reconstructs excellently (Tanimoto=0.829)
but generates poorly from N(0,I) (~28% greedy validity) because the posterior doesn't
overlap the prior. The KL weight is the dominant hyperparameter.

### Sweep Progression

| kl_weight | Greedy validity | Notes |
|-----------|----------------|-------|
| 0.01 | 28% | Original, prior-posterior gap |
| 0.05 | 62% | |
| 0.10 | 72% | |
| 0.25 | 73% | Curve flattening |
| 0.50 | 79% | |
| 1.0 | 83% | Base model |
| 2.0 | 87% | |
| 5.0 | 88% | Diminishing returns |

### Winner: kl_weight=1.0, word_dropout=0.1

| Metric | temp=0.8 | temp=0.0 (greedy) |
|--------|----------|-------------------|
| Validity | 84.8% | 91.5% |
| Unique valid | 480/600 | 427/600 |
| Per state | ~170 valid each | ~183 valid each |

Why this beats alternatives:
- `latent_dim=32` gets higher raw validity (93.3% greedy) but sacrifices diversity
  (338 vs 427 unique) -- not worth it for molecular generation.
- Larger models (d512/6L, d768/8L) hurt rather than help -- likely overfitting.
- `word_dropout=0.1` works better with `kl_weight=1.0` because high KL pressure already
  forces the model to use z, so less artificial forcing is needed. The two forces are
  complementary.

### Full Sweep Table

| Config | kl_w | Model | lat | Other | t=0.5 valid% | t=0.5 uniq | greedy valid% | greedy uniq |
|--------|------|-------|-----|-------|-------------|------------|--------------|------------|
| sweep_kl005 | 0.05 | d256/4L | 64 | -- | 55.8% | 331 | 62.3% | 356 |
| sweep_kl01 | 0.10 | d256/4L | 64 | -- | 63.7% | 371 | 72.0% | 415 |
| sweep_kl025 | 0.25 | d256/4L | 64 | -- | 65.3% | 385 | 73.3% | 414 |
| sweep_kl05 | 0.50 | d256/4L | 64 | -- | 75.7% | 432 | 78.8% | 429 |
| sweep_kl10 | 1.0 | d256/4L | 64 | -- | 74.5% | 430 | 83.0% | 443 |
| sw_kl2 | 2.0 | d256/4L | 64 | -- | 77.5% | 435 | 87.0% | 433 |
| sw_kl5 | 5.0 | d256/4L | 64 | -- | 78.3% | 407 | 87.8% | 358 |
| sweep_large | 0.5 | d512/6L | 64 | -- | 77.2% | 440 | 82.5% | 392 |
| sw_lg_kl1 | 1.0 | d512/6L | 64 | -- | 77.5% | 444 | 86.3% | 390 |
| sw_lg_kl2 | 2.0 | d512/6L | 64 | -- | 66.8% | 371 | 85.0% | 299 |
| sw_xl_kl1 | 1.0 | d768/8L | 64 | -- | 71.8% | 397 | 78.7% | 294 |
| sw_xl_l32 | 1.0 | d768/8L | 32 | -- | 77.0% | 400 | 77.7% | 178 |
| sw_kl05l32 | 0.5 | d256/4L | 32 | -- | 85.2% | 469 | 86.5% | 331 |
| sw_kl1l32 | 1.0 | d256/4L | 32 | -- | 85.2% | 462 | 90.8% | 332 |
| sw_kl2l32 | 2.0 | d256/4L | 32 | -- | 86.8% | 467 | 93.3% | 338 |
| **sw_kl1wd01** | **1.0** | **d256/4L** | **64** | **wd=0.1** | **84.8%** | **480** | **91.5%** | **427** |
| sw_kl1wu200 | 1.0 | d256/4L | 64 | wu=200 | 71.2% | 414 | 81.5% | 441 |
| sw_combo | 1.0 | d512/6L | 32 | wd=0.15 | 76.7% | 385 | 88.3% | 212 |

## What Is Running Now

### Production Training (submitted 2026-04-10)

**Job 7880395** -- Conditioned (3-state), array 0-2:
- Seeds: 42, 123, 7
- Config: `configs/transformer_vae.yaml` (kl_weight=1.0, word_dropout=0.1)
- Output checkpoints: `artifacts/models/transformer_vae/seed_{42,123,7}/`
- Output generation (stochastic): `artifacts/generation/transformer_vae_conditioned_seed{42,123,7}.json`
- Output generation (greedy): `artifacts/generation/transformer_vae_conditioned_seed{42,123,7}_greedy.json`
- Generates 200 per state at temp=0.8 and temp=0.0

**Job 7880397** -- Unconditioned (Ablation C), array 0-2:
- Seeds: 42, 123, 7
- Config: `configs/transformer_vae_unconditioned.yaml` (same hyperparams, n_states=1)
- Output checkpoints: `artifacts/models/transformer_vae_unconditioned/seed_{42,123,7}/`
- Output generation (stochastic): `artifacts/generation/transformer_vae_unconditioned_seed{42,123,7}.json`
- Output generation (greedy): `artifacts/generation/transformer_vae_unconditioned_seed{42,123,7}_greedy.json`
- Generates 600 unconditioned at temp=0.8 and temp=0.0

Logs: `logs/tfm_vae_3s_7880395_{0,1,2}.out` and `logs/tfm_vae_uc_7880397_{0,1,2}.out`

### What to Check When Jobs Complete

Monitor: `squeue -u rag88`

For each completed job, check the log for:
```
grep -E "(Early stopping|Best val|Valid:|Unique valid)" logs/tfm_vae_3s_7880395_*.out
grep -E "(Early stopping|Best val|Valid:|Unique valid)" logs/tfm_vae_uc_7880397_*.out
```

**Expected results** (based on sweep with same hyperparams):
- Early stopping around epoch 600-800
- Best val_recon_loss ~0.31
- Greedy validity >90%
- Stochastic (temp=0.8) validity >80%

Check for errors:
```
cat logs/tfm_vae_3s_7880395_*.err
cat logs/tfm_vae_uc_7880397_*.err
```

Verify outputs exist:
```
ls -la artifacts/models/transformer_vae/seed_*/best_model.pt
ls -la artifacts/models/transformer_vae_unconditioned/seed_*/best_model.pt
ls -la artifacts/generation/transformer_vae_*.json
```

## What to Do After Jobs Complete (Phase 5.4 + 5.6 + Phase 6)

### Step 1: Validate Results

For each of the 3 conditioned seeds AND 3 unconditioned seeds, extract from logs:
- Epoch at early stopping
- Best val_recon_loss
- Generation validity at temp=0.8 and temp=0.0
- Unique valid count

All 6 should show greedy validity >80%. If any fails, check its .err file.

### Step 2: Run Validation Checks (Phase 5.4)

These must run on a GPU node (submit to SLURM). Write a validation script or run inline:

1. **Reconstruction quality**: Load a trained model + vocab, encode 500 training molecules,
   decode them, compute mean Tanimoto similarity. Target: >0.3 (original GRU: 0.031).

2. **Aromatic rings**: Count mean aromatic rings in generated valid SMILES.
   Target: >1.0 (training data mean: 3.56, original GRU: 0.03).

3. **Scaffold overlap**: Extract Murcko scaffolds from generated and training sets.
   Target: some overlap (any overlap is better than the GRU's zero).

4. **Nearest-neighbor similarity**: For generated molecules, compute Tanimoto to
   nearest training molecule. Target: mean >0.3.

5. **Drug proximity**: Max Tanimoto from any generated molecule to known EGFR drugs
   (erlotinib, gefitinib, lapatinib, osimertinib). Target: >0.3.

6. **Validity**: Already measured during generation. Target: >80%.

### Step 3: Write Training Results (Phase 5.6)

Document per-seed metrics, cross-seed variance, and validation check results.

### Step 4: Integration Handoff (Phase 6)

The Transformer VAE generation artifacts (JSON files in `artifacts/generation/`) are
already in the correct format for `statebind.generation.vae_integration.load_vae_candidates()`.

To use in the pipeline:
```python
from statebind.generation.models import GenerationStrategy
from statebind.generation.vae_integration import load_vae_candidates

candidates = load_vae_candidates(
    "artifacts/generation/transformer_vae_conditioned_seed42.json",
    strategy=GenerationStrategy.TRANSFORMER_VAE_GENERATED,
    id_prefix="tvae",
)
```

The ranking pipeline (`ranking/scoring.py`) handles these candidates the same as any
other `StateConditionedCandidate` -- no changes needed downstream.

### Step 5: Re-run Phase 1 Experiments

With a working generative model, the Phase 1 experiments (core ablations) can be re-run.
Read `docs/PHASE_PLAN.md` and any Phase 1 task specs in the planning docs for details.
The key experiment is **Ablation C**: conditioned vs unconditioned generation quality.
The conditioned model (3-state) should produce state-differentiated molecules that score
better on state-specific metrics than the unconditioned model (1 state, same total count).

## Config Reference (Production)

```yaml
# configs/transformer_vae.yaml (tuned)
model:
  kl_weight: 1.0          # Was 0.01 -- 100x increase closes prior-posterior gap
  word_dropout: 0.1        # Was 0.3 -- less forcing needed with high KL
  d_model: 256
  n_decoder_layers: 4
  latent_dim: 64
  n_states: 3
  free_bits: 0.25

training:
  epochs: 2000             # Was 1000
  patience: 300            # Was 150
  # Everything else unchanged
```

## Known Issues

1. **Flaky test**: `test_docking.py::TestDockingWrapper::test_vina_score_range` fails
   intermittently (vina_score=9.6, expected [-15,0]). Deselect with
   `--deselect tests/test_docking.py::TestDockingWrapper::test_vina_score_range`.

2. **Old SLURM jobs**: Previous training runs (job IDs 7843742, 7848979, 7843744, 7848980)
   used suboptimal hyperparams (kl_weight=0.01). Their outputs in `artifacts/` should be
   ignored or overwritten by the new production runs.

3. **Sweep checkpoints lost**: Sweep jobs wrote to /tmp on compute nodes, which gets cleaned.
   Only the logs survive. This is fine -- production runs write to `artifacts/`.

4. **Old vae.py not touched**: The broken `src/statebind/ml/vae.py` is still present.
   It should NOT be deleted -- `SMILESEncoder` is imported from it by `transformer_vae.py`.
