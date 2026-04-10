---
type: option-spec
created: 2026-04-10T06:00:00Z
option: 4
name: Transformer VAE with SMILES Representation
---

# Option 4: Transformer VAE with SMILES Representation

## Overview

Replace the GRU decoder with a Transformer decoder and switch from SELFIES to SMILES
representation. This is a direct architectural upgrade that preserves the VAE framework
(encoder, latent space, decoder, state conditioning) while fixing both root causes:

1. **Transformer attention solves ring closure**: Self-attention over all previously
   generated tokens means the model can directly attend to ring-opening positions
   when generating ring-closure tokens — no reliance on GRU hidden state memory.

2. **SMILES simplifies ring notation**: Benzene is `c1ccccc1` in SMILES vs
   `[C][=C][C][=C][C][=C][Ring1][=Branch1]` in SELFIES. The dependency distance
   for ring closure is much shorter.

3. **Posterior collapse is fixed orthogonally**: Add free bits + word dropout to the
   training procedure (independent of the decoder architecture).

## Architecture

```
Encoder:  Transformer encoder (or keep bidirectional GRU — encoder works fine)
          Input: SMILES tokens + state conditioning
          Output: mu, logvar (latent_dim=64 or 128)

Latent:   z ~ N(mu, sigma^2) with free-bits regularization
          Concatenate [z; state_onehot] before decoder

Decoder:  Transformer decoder with causal masking
          z injected via: (a) cross-attention to z, or (b) z prepended as prefix tokens,
          or (c) z projected to initial memory/bias
          Self-attention over generated tokens (solves ring closure)
          Output: Linear(d_model, vocab_size) per position

Loss:     CrossEntropy(recon) + beta * max(KL_per_dim, free_bits).sum()
          With word dropout (30-50% of decoder inputs replaced with <unk>)
```

### Specific Design Choices

**Encoder**: The bidirectional GRU encoder is fine — G7 showed the encoder does map
different molecules to different mu values (norm 0.16-1.9). The collapse is in the
decoder ignoring z, not in the encoder failing to encode. Options:
- Keep GRU encoder (simplest, encoder is not broken)
- Switch to Transformer encoder (cleaner but unnecessary)

**Decoder**: Small Transformer decoder.
- d_model = 256 or 512
- n_heads = 4 or 8
- n_layers = 4-6 (small — we only have ~6k training molecules)
- Causal self-attention mask (can only attend to earlier tokens)
- Positional encoding (sinusoidal or learned)

**z injection**: Three common approaches:
- **(a) Cross-attention**: Decoder cross-attends to z reshaped as a 1-step "memory."
  Clean but adds complexity.
- **(b) Prefix tokens**: Project z into d_model space, prepend as 4-8 "memory" tokens
  before SOS. Decoder attends to these via causal self-attention. Simple, effective,
  well-studied (Optimus, Li et al. 2020).
- **(c) Adaptive bias**: Add z-derived bias to attention layers. Less common.

Recommend **(b) prefix tokens** — simplest to implement, well-validated.

**State conditioning**: Concatenate state one-hot to z before projection to prefix
tokens (same as current approach). Alternatively, add state embedding to positional
encoding.

**Word dropout**: During training, randomly replace 30-50% of decoder input tokens
with a special `<unk>` token. This forces the decoder to rely on z (via prefix tokens)
for reconstruction, preventing posterior collapse. Critical fix.

**Free bits**: For each latent dimension j, compute:
`kl_j = max(KL_j, lambda)` where lambda=0.25
This guarantees minimum information flow through the latent bottleneck.

## Representation: SMILES (not SELFIES)

Switch from SELFIES to SMILES tokens. Rationale:

| Aspect | SELFIES | SMILES |
|--------|---------|--------|
| Validity guarantee | 100% | ~80-95% (post-filter) |
| Ring closure | `[Ring1][=Branch1]` (long-range) | `1` repeated (short-range) |
| Token vocabulary | ~70-100 bracket tokens | ~40-60 characters |
| Sequence length | Longer (40-66 for EGFR drugs) | Shorter (30-50 for EGFR drugs) |
| Decoder difficulty | Hard (long-range deps) | Moderate (familiar to LMs) |
| Literature support | Less common for VAEs | Standard (JT-VAE, CDDD, etc.) |

The `SMILESTokenizer` already exists in `src/statebind/ml/tokenizer.py` (character-level).
The `Vocabulary` class already handles SMILES tokens. The dataset pipeline
(`vae_dataset.py`) already uses `SMILESTokenizer` by default — SELFIES was an addition.

Validity can be checked with RDKit (`Chem.MolFromSmiles(s) is not None`) and invalid
molecules filtered. A well-trained SMILES model typically achieves 90-98% validity.

## Advantages

- **Direct VAE swap**: Same interface (encode, sample, generate), same latent space,
  same state conditioning. Ablation C can be re-run with minimal changes.
- **Solves both root causes**: Transformer attention for ring closure + free bits/word
  dropout for posterior collapse.
- **Interpretable latent space**: Can analyze state separation, interpolation, and
  latent traversals — valuable for the paper.
- **Novel contribution**: "State-conditioned Transformer VAE for kinase-targeted
  generation" is a publishable architectural contribution. No existing work combines
  conformational state conditioning with Transformer VAE for kinases.
- **Moderate complexity**: 4-6 layer Transformer decoder is well within our data scale.
- **Self-contained**: No external dependencies beyond PyTorch.

## Disadvantages

- **Validity not 100%**: SMILES models produce ~5-15% invalid molecules. Must post-filter.
  This is standard practice and not a real limitation.
- **More code to write**: Transformer decoder + free bits + word dropout + prefix token
  injection. Estimated ~400-600 lines of new model code.
- **Training may need tuning**: Transformers can be finicky with small datasets (6k mols).
  May need careful learning rate warmup, dropout, and regularization.
- **Slightly larger model**: Transformer with 4 layers, d_model=256, 4 heads ≈ 3-5M params
  (comparable to current 9.5M GRU model, actually smaller).

## Implementation Outline

### New/Modified Files

```
src/statebind/ml/transformer_vae.py    — NEW: TransformerVAEConfig, TransformerEncoder (optional),
                                          TransformerDecoder, ConditionalTransformerVAE, transformer_vae_loss
src/statebind/ml/vae.py                — KEEP: VAEConfig, vae_loss still available for backward compat
scripts/train_transformer_vae.py       — NEW: Training script with free bits + word dropout + KL cycling
scripts/generate_transformer_vae.py    — NEW: Generation script (same output format as generate_vae_candidates.py)
configs/transformer_vae.yaml           — NEW: Config for Transformer VAE
configs/transformer_vae_unconditioned.yaml — NEW: For Ablation C unconditioned
tests/test_transformer_vae.py          — NEW: Unit tests (model creation, forward pass, generate, loss)
```

### Model Code Structure

```python
class TransformerVAEConfig(BaseModel):
    vocab_size: int = 100
    d_model: int = 256
    n_heads: int = 4
    n_enc_layers: int = 2        # encoder (GRU or Transformer)
    n_dec_layers: int = 4        # decoder (Transformer)
    latent_dim: int = 64
    n_prefix_tokens: int = 8     # z -> prefix tokens
    n_states: int = 3
    dropout: float = 0.2
    word_dropout: float = 0.3    # fraction of decoder inputs replaced with <unk>
    free_bits: float = 0.25      # minimum KL per dimension
    kl_weight: float = 0.01
    pad_idx: int = 0

class ConditionalTransformerVAE(nn.Module):
    # Same public API as ConditionalSMILESVAE:
    encode(x, lengths, state_onehot) -> (mu, logvar)
    sample(mu, logvar) -> z
    generate(z, state_onehot, max_len, temperature, vocab) -> list[list[int]]
    forward(x, lengths, state_onehot, word_dropout_rate) -> (recon_logits, mu, logvar)
```

The `generate()` method must match the current API signature so that
`generate_vae_candidates.py` works with minimal changes (just import swap).

### Training Pipeline

1. **Tokenize** SMILES with character-level `SMILESTokenizer` (already exists)
2. **Build vocabulary** from training data (already exists in `vocabulary.py`)
3. **Train** with:
   - Word dropout: 30% of decoder inputs -> `<unk>` token
   - Free bits: `KL_j = max(KL_j, 0.25)` per latent dim j
   - KL cycling: ramp beta 0->0.01 over 30 epochs, then cycle 4x
   - Cosine LR schedule with warmup
   - Gradient clipping at 1.0
4. **Early stopping** on val_recon_loss (same as current)
5. **Generate** candidates via sampling from prior z ~ N(0,I)
6. **Validate** with RDKit, filter invalids
7. **Write** JSON artifact in standard format

### Compute Estimate

- Training: ~30-60 min on H200 (300 epochs, 6k molecules, small transformer)
- Generation: seconds (just forward passes)
- Total: ~1-2 hours GPU time including experimentation

## Quick Validation Test (Before Full Training)

To validate the architecture works before committing to full training:

1. Build the model, verify forward pass and generate work
2. Train for 20 epochs on a 500-molecule subset
3. Check: does reconstruction Tanimoto exceed 0.1? (current GRU: 0.031)
4. Check: do generated molecules contain aromatic rings? (current GRU: 0.03 avg)
5. If both YES: proceed to full training. If NO: debug architecture.

This quick test takes ~5 minutes on a GPU.

## Integration with StateBind

Same as current VAE — the output JSON artifact has identical schema:
```json
{"smiles": "...", "state": "DFGin_aCin", "is_valid": true, "source": "transformer_vae_generated"}
```

`vae_integration.py` loads this unchanged. Add `TRANSFORMER_VAE_GENERATED` to
`GenerationStrategy` enum.

## Decision Criteria for This Option

This option is PREFERRED if:
- The thesis claims state conditioning improves the generative model itself
- Latent space analysis is important for the paper
- Novelty of the approach matters (state-conditioned Transformer VAE for kinases)
- Clean VAE interface swap is desired (same API, drop-in replacement)

This option is LESS PREFERRED if:
- Speed to results is the primary concern (more code to write than Option 3)
- Comparison with industry standard (REINVENT) is the main publication angle
