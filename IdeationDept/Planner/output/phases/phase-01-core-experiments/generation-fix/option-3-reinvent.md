---
type: option-spec
created: 2026-04-10T06:00:00Z
option: 3
name: REINVENT-style State-Conditioned Generation
---

# Option 3: REINVENT-Style State-Conditioned Generation

## Overview

Replace the VAE with a REINVENT-style autoregressive language model. REINVENT
(AstraZeneca, 2017–2024) is the industry-standard approach for de novo molecular
design. It uses a pre-trained SMILES language model fine-tuned via reinforcement
learning toward a scoring function.

**Key difference from VAE**: No encoder, no latent space, no reconstruction.
The model is a pure decoder (RNN or Transformer LM) that learns the distribution
of drug-like SMILES. State conditioning happens through the scoring/reward function,
not through the model architecture.

## Architecture

```
Prior:    Pretrained SMILES language model (RNN/LSTM/Transformer)
          Trained on ChEMBL drug-like molecules (~2M SMILES)

Agent:    Copy of Prior, fine-tuned via RL on EGFR-specific scoring

Scoring:  StateBind's existing scoring function (ranking/scoring.py)
          with state_specificity component providing state conditioning

Training: REINFORCE / augmented likelihood
          reward = scoring_fn(smiles, target_state)
          loss = -reward * log_prob(smiles | agent) + sigma * (log_prob(prior) - log_prob(agent))
```

### Two Sub-Approaches

**3a: Wrap existing REINVENT 4 installation.**
We already have REINVENT 4 integrated (Phase 1 Task T06, Gate G3 = GO). It ran
successfully and generated 548 valid EGFR molecules. The infrastructure exists:
- `scripts/setup_reinvent4.sh` — environment setup
- `configs/reinvent4_egfr.toml` — REINVENT config
- `scripts/reinvent4_gnina_component.py` — GNINA scoring plugin
- `scripts/run_reinvent4_egfr.py` — runner

This approach uses REINVENT 4 as a black box and wraps its output into our
candidate JSON format.

**3b: Build a lightweight REINVENT-style model in-house.**
Train a SMILES language model from scratch on our EGFR data, then fine-tune with
our scoring function. Smaller, faster, more controllable. Uses our existing
`ml/trainer.py` infrastructure.

## How State Conditioning Works

REINVENT doesn't have explicit state conditioning in its architecture. Instead:

1. **Per-state fine-tuning**: Train 3 separate agents, one per state. Each agent's
   reward function uses the full scoring function with `target_state = X`.
   The state_specificity scoring component (the most important, per scoring ablation)
   rewards molecules that dock well in state X's pocket.

2. **Scoring-based conditioning**: A single agent generates molecules, but the reward
   function includes state_specificity for the target state. The agent learns to
   generate molecules that score well for that state.

3. **Post-hoc assignment**: Generate a large pool, score against all states, assign
   each molecule to its best-scoring state.

For Ablation C (conditioned vs unconditioned):
- **Conditioned**: 3 agents, each targeting one state's pocket
- **Unconditioned**: 1 agent with a generic scoring function (no state_specificity)

## Advantages

- **Proven at scale**: REINVENT is used by AstraZeneca, Merck, Novartis in production
- **No ring generation problem**: SMILES language models naturally produce aromatic rings
  because ring notation in SMILES is simple (`c1ccccc1`)
- **No posterior collapse**: No VAE bottleneck, no KL divergence issue
- **Already integrated**: REINVENT 4 ran successfully in Phase 1 (G3 = GO)
- **Strong priors**: Pre-training on ChEMBL gives the model knowledge of drug-like space
- **Publication angle**: Direct comparison with industry standard

## Disadvantages

- **No explicit latent space**: Cannot interpolate between molecules or do latent
  space optimization. Less interpretable than a VAE.
- **State conditioning is indirect**: Through the scoring function, not the model.
  This means Ablation C tests "does state-aware scoring during generation help?"
  not "does state-aware architecture help?" — a subtly different question.
- **RL training instability**: REINFORCE has high variance. Needs careful tuning
  of sigma (prior regularization), learning rate, and reward shaping.
- **External dependency (3a)**: REINVENT 4 is a separate codebase with its own
  environment and configuration. Harder to modify internals.
- **Validity ~90-95%**: SMILES models produce some invalid molecules (vs 100% for SELFIES).
  Easily handled by post-filtering but worth noting.

## Implementation Outline (3b — in-house)

### New Files
```
src/statebind/ml/smiles_lm.py         — SMILES language model (LSTM or Transformer LM)
src/statebind/ml/reinvent_trainer.py   — RL fine-tuning loop (REINFORCE + augmented likelihood)
scripts/pretrain_smiles_lm.py          — Pre-train on ChEMBL SMILES
scripts/finetune_reinvent.py           — Fine-tune with state scoring
configs/reinvent_statebind.yaml        — Config for in-house REINVENT
tests/test_smiles_lm.py               — Unit tests
```

### Training Pipeline
1. **Pre-train** SMILES LM on ChEMBL drug-like subset (~1-2M SMILES), 50-100 epochs
2. **Fine-tune** per-state agents using StateBind scoring as reward
3. **Generate** candidates: sample from each agent, validate, write JSON artifact
4. **Evaluate** using existing retrospective pipeline

### Compute Estimate
- Pre-training: ~2-4 hours on H200 (one-time)
- Fine-tuning per state: ~30-60 min on H200
- Generation: minutes (just sampling from the model)
- Total: ~6 hours GPU time

## Integration with StateBind

The output JSON artifact has the same schema as the current VAE output:
```json
{"smiles": "...", "state": "DFGin_aCin", "is_valid": true, "source": "reinvent_generated"}
```

`vae_integration.py` (or a renamed `ml_integration.py`) loads this and creates
`StateConditionedCandidate` objects. The scoring pipeline is unchanged.

The `GenerationStrategy` enum in `generation/models.py` would need a new member:
`REINVENT_GENERATED = "reinvent_generated"`.

## Decision Criteria for This Option

This option is PREFERRED if:
- Speed matters most (already partially integrated)
- The publication framing emphasizes comparison with industry standard
- Explicit latent space is not needed for the thesis

This option is LESS PREFERRED if:
- The thesis requires demonstrating that state information improves the generative
  model itself (not just the scoring/selection)
- Latent space analysis is important for the paper
- Novelty of the approach matters for publication venue
