---
type: deliberation
created: 2026-04-10T12:00:00Z
decision: Option 4 — Transformer VAE with SMILES Representation
---

# Generation Module Fix — Deliberation

## Decision

**Option 4: Transformer VAE with SMILES** is selected for implementation.

## Evaluation

| Criterion | Weight | Option 3 (REINVENT) | Option 4 (Transformer VAE) | Winner |
|-----------|--------|---------------------|---------------------------|--------|
| Thesis alignment | HIGH | State conditioning is indirect (via scoring function only). Tests "does state-aware scoring help generation?" | State conditioning is architectural (in the model). Tests "does state-aware generation help?" — the actual thesis. | **Option 4** |
| Ablation C compatibility | HIGH | Requires paradigm redesign: conditioned = per-state agent, unconditioned = generic agent. Different model instances. | Drop-in replacement: same API, same Ablation C design (n_states=3 vs n_states=1). Same framework. | **Option 4** |
| Ring generation | HIGH | SMILES LM naturally generates rings. Proven at scale (AstraZeneca, Merck). | Transformer attention + SMILES fixes both root causes. Needs validation but mechanism is sound. | Tie |
| Posterior collapse | HIGH | N/A — no VAE bottleneck, no KL divergence. | Fixed by free bits (lambda=0.25/dim) + word dropout (30%). Well-studied solutions (Kingma et al. 2016, Bowman et al. 2016). | Tie |
| Implementation effort | MED | 3a (wrap REINVENT 4): days. 3b (in-house): ~1 week. | ~1 week. New decoder + training loop + tests. | Option 3 |
| Publication novelty | MED | REINVENT is established. Comparison baseline, not novel. | State-conditioned Transformer VAE for kinases is novel. No existing work combines conformational state conditioning with Transformer VAE for kinase-targeted generation. | **Option 4** |
| Latent space analysis | LOW | No latent space. Cannot interpolate, visualize state separation, or do latent traversals. | Full latent space for analysis, interpolation, state visualization. Valuable for publication figures. | **Option 4** |

## Reasoning

### The thesis requires Option 4

StateBind's thesis (from CLAUDE.md): "conformational state-aware molecular design outperforms static single-structure design." This is about the full design pipeline, not just scoring.

- **Option 3** would test: "Does state-aware *scoring* during generation improve outcomes?" The generative model itself has no state awareness — it's an unconditional SMILES language model guided by a reward signal.
- **Option 4** would test: "Does state-aware *generation* improve outcomes?" The generative model directly conditions on conformational state via architectural design (state one-hot concatenated to latent code, injected as prefix tokens into the Transformer decoder).

Option 4 is the stronger test of the thesis because state information is embedded in the model architecture, not just the external scoring function.

### Ablation C is simpler with Option 4

The existing Ablation C infrastructure (3-seed conditioned vs 3-seed unconditioned, same architecture except n_states) works directly with Option 4:
- Conditioned: `TransformerVAEConfig(n_states=3)` with state-specific one-hots
- Unconditioned: `TransformerVAEConfig(n_states=1)` with constant "unconditioned" label

With Option 3, Ablation C would require a different experimental design (per-state RL agents vs generic agent), making the comparison less clean.

### Risk assessment

Option 4's main risk is that the Transformer decoder might not train well on 6K molecules. Mitigations:
1. Small architecture (d_model=256, 4 layers, ~3-5M params) — smaller than the failed 9.5M GRU model
2. Free bits + word dropout are well-validated anti-collapse techniques
3. SMILES representation eliminates the ring-closure difficulty that killed the GRU decoder
4. Quick validation (20 epochs, 500 molecules) will catch fundamental issues before full training

### What we sacrifice

- No comparison with industry standard (REINVENT). This could be added later as a baseline if needed for publication.
- RL-based exploration of chemical space (REINVENT's strength). The VAE explores via latent space sampling instead.
- 100% validity guarantee (SELFIES). SMILES validity is typically 80-95% with post-filtering.

These tradeoffs are acceptable given thesis alignment and publication novelty.

## Implementation Plan

See the plan file for full details. Summary:
1. Transformer VAE with GRU encoder (reused from existing code) + Transformer decoder
2. z injection via 8 prefix tokens (project [z; state_onehot] to d_model space)
3. Free bits (lambda=0.25) + word dropout (30%) to prevent posterior collapse
4. SMILES representation with existing SMILESTokenizer
5. Same JSON artifact format for pipeline compatibility
