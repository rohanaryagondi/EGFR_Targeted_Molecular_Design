---
agent: Conditional Generation Expert
round: 1
date: 2026-04-14
type: research-note
---

# Investigation Report: H1 -- Weak Conditioning Mechanism

## 1. Executive Summary

After deep analysis of the StateBind Transformer VAE architecture and extensive literature review of conditioning mechanisms in generative molecular design, I assess with **high confidence (70-80%)** that H1 -- the weak prefix-token conditioning mechanism -- is a primary contributor to the G2 null result. However, H1 alone is almost certainly insufficient to explain the full failure. The evidence points to a compounding interaction between H1 (weak mechanism), H2 (insufficient state-specific structure in training data), and H3 (evaluation metric blindness), with H1 being the most actionable and cheapest to test.

The prefix-token conditioning approach used in StateBind is the weakest viable mechanism in the modern conditioning hierarchy. Published work across vision (Peebles & Xie, 2023), NLP (Li & Liang, 2021), and molecular generation (Jin et al., 2025; SAFE-T, 2025) consistently demonstrates that stronger conditioning mechanisms yield dramatically better controllability. The specific quantitative signature -- centroid distances of only 6-10% of latent space scale, identical scaffold generation across states, and Cohen's d = 0.059 -- is exactly what the literature predicts when a conditioning signal is too weak to influence generation.

---

## 2. Architectural Diagnosis of the Current Conditioning Mechanism

### 2.1 How the StateBind Prefix-Token Conditioning Works

From direct inspection of `transformer_vae.py` (lines 217-388), the conditioning pathway is:

```
state_onehot (batch, 3)  -->  cat with z (batch, 64)  -->  [z; state] (batch, 67)
    -->  Linear(67, 8 * 256)  -->  reshape to (batch, 8, 256)  -->  prefix tokens
    -->  prepend to embedded SMILES tokens  -->  Transformer with causal mask
```

The state one-hot vector (3 dimensions) is concatenated with the latent code z (64 dimensions) and projected through a single linear layer to produce 8 prefix tokens of dimension 256 each. These prefix tokens are prepended to the decoder sequence and the causal attention mask allows all subsequent positions to attend to them.

### 2.2 Why This Is the Weakest Viable Mechanism

**Information-theoretic argument.** A 3-class one-hot vector carries at most log2(3) = 1.58 bits of information. This is distributed across 8 prefix tokens of dimension 256, yielding ~0.2 bits per token. Each SMILES molecule is 60-80 tokens long. The signal-to-noise ratio of the conditioning information relative to the molecule's own autoregressive signal is vanishingly small: 8 prefix tokens vs. 60-80 molecule tokens means the state signal occupies only ~10% of the total sequence.

**The attention sink problem.** Recent work on attention sinks in transformers (Xiao et al., 2024; Han et al., 2024) shows that early tokens in a sequence tend to attract disproportionate attention not because they carry semantic content, but because softmax normalization creates geometric anchoring. This means the prefix tokens may be attended to as attention sinks rather than as conditioning signals -- the model attends to them out of structural necessity rather than to extract state information. The prefix tokens in StateBind have no special architectural mechanism to prevent this degenerate attention pattern.

**Concatenation with z dominates.** The state one-hot (3 dims) is concatenated with z (64 dims) before projection. The linear layer that produces prefix tokens has input dimension 67, of which the state occupies only 3/67 = 4.5% of the input dimensions. Given that z already contains molecule-level information with ||mu|| ~ 4.3, the state signal is a tiny perturbation on a large latent vector. The linear projection can easily learn to route most of its capacity through the 64 z dimensions and treat the 3 state dimensions as near-irrelevant noise.

**No per-layer conditioning.** The prefix tokens influence the decoder only through attention. Unlike FiLM (Perez et al., 2018) or adaLN (Peebles & Xie, 2023), which modulate activations at every layer, the prefix tokens are processed once and their influence must propagate through 4 transformer layers entirely through the attention mechanism. As the network deepens, the prefix signal dilutes through residual connections and layer normalization.

### 2.3 Quantitative Evidence of Weak Conditioning

The G2 report provides direct evidence that the conditioning signal is nearly absent:

| Diagnostic | Value | Interpretation |
|------------|-------|----------------|
| State centroid distance (latent space) | 0.26-0.42 | Only 6-10% of mu norm (~4.3) |
| State centroid distance / std | ~0.06-0.10 | Well within 1 std of latent noise |
| Cohen's d (composite score) | 0.059 | Negligible effect |
| Scaffold overlap across states | Identical | erlotinib, gefitinib, osimertinib generated for all states |
| Component-level max d | 0.060 | No component shows conditioning benefit |

The centroid distance of 0.26-0.42 in a latent space with mu norm ~4.3 is particularly damning. For a well-conditioned model, we would expect centroid distances of at least 1.0-2.0 (20-50% of scale), as demonstrated by published CVAEs where conditioning on molecular properties creates clearly separated clusters in 2D UMAP projections (Lim et al., 2018; Romanelli et al., 2024).

---

## 3. Literature Review: Conditioning Mechanisms Ranked by Strength

### 3.1 Comparative Table of Conditioning Mechanisms

| Mechanism | Where Applied | Strength | Compute Overhead | Implementation Effort | Key Paper |
|-----------|--------------|----------|------------------|-----------------------|-----------|
| **Prefix tokens** (current) | Input sequence only | Weakest | None | Already implemented | Li & Liang (2021) |
| **Concatenation to z** (also current) | Latent projection | Weak | None | Already implemented | Lim et al. (2018) |
| **FiLM** (feature-wise linear modulation) | Per-layer affine transform | Moderate | ~2% params | Low (1-2 days) | Perez et al. (2018) |
| **Cross-attention** | Separate K/V from condition | Strong | ~15% Gflops | Moderate (3-5 days) | Vaswani et al. (2017); Rombach et al. (2022) |
| **adaLN** (adaptive layer norm) | Replaces LayerNorm params | Strong | ~0% Gflops | Moderate (3-5 days) | Peebles & Xie (2023) |
| **adaLN-Zero** | adaLN + zero-init residual gates | Strongest | ~0% Gflops | Moderate (3-5 days) | Peebles & Xie (2023) |
| **Classifier-free guidance** | Inference-time amplification | Amplifier (stacks on any) | 2x forward pass | Low (1 day) | Ho & Salimans (2022) |
| **Separate decoder heads** | Independent decoders per class | Strongest (brute force) | 3x params/compute | High (1-2 weeks) | Various |

### 3.2 DiT Conditioning Mechanism Comparison (Peebles & Xie, 2023)

The most rigorous published comparison of conditioning mechanisms comes from DiT (Peebles & Xie, 2023, ICCV 2023). They compared four mechanisms on class-conditional ImageNet 256x256 at the DiT-XL/2 scale after 400K training steps:

| Mechanism | Gflops | FID-50K | Relative to adaLN-Zero |
|-----------|--------|---------|------------------------|
| In-context (prefix tokens) | 119.4 | ~35 | 1.8x worse |
| Cross-attention | 137.6 | ~26 | 1.3x worse |
| adaLN | 118.6 | ~25 | 1.3x worse |
| **adaLN-Zero** | 118.6 | **~19.5** | **Best** |

The key finding: **in-context conditioning (analogous to StateBind's prefix tokens) yielded FID nearly double that of adaLN-Zero** while using identical compute. The adaLN-Zero mechanism was simultaneously the cheapest and the most effective. This is the single most important quantitative datapoint for this investigation: the exact mechanism class used by StateBind has been shown to be the weakest in a controlled comparison.

The authors note: "The adaLN-Zero block yields lower FID than both cross-attention and in-context conditioning while being the most compute-efficient." The mechanism works by regressing scale (gamma), shift (beta), and dimensionwise gating (alpha) parameters from the conditioning embedding, with alpha initialized to zero so that each transformer block starts as the identity function.

### 3.3 FiLM Conditioning (Perez et al., 2018)

FiLM applies a conditioned affine transformation to feature maps: FiLM(F) = gamma * F + beta, where gamma and beta are predicted from the conditioning signal. On the CLEVR visual reasoning benchmark, FiLM halved the state-of-the-art error rate. Ablation studies showed that even a single FiLM layer produced meaningful conditioning, and the learned gamma values frequently went to near-zero, demonstrating the model's ability to selectively gate features based on the condition.

FiLM's advantage for StateBind is its simplicity and per-layer application. Unlike prefix tokens that must propagate through attention, FiLM directly modulates every layer's activations.

**Implementation for StateBind (pseudocode):**
```python
class FiLMConditionedTransformerLayer(nn.Module):
    def __init__(self, d_model, n_states, n_heads, dim_ff):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads)
        self.ff = nn.Sequential(
            nn.Linear(d_model, dim_ff), nn.GELU(),
            nn.Linear(dim_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        # FiLM generators: state_embed -> gamma, beta for each sub-layer
        self.film_attn = nn.Linear(n_states, 2 * d_model)  # gamma + beta
        self.film_ff = nn.Linear(n_states, 2 * d_model)

    def forward(self, x, state_onehot, mask=None):
        # Attention sub-layer with FiLM
        gamma1, beta1 = self.film_attn(state_onehot).chunk(2, dim=-1)
        h = self.norm1(x)
        h = h * (1 + gamma1.unsqueeze(1)) + beta1.unsqueeze(1)
        h = self.attn(h, h, h, attn_mask=mask)[0]
        x = x + h

        # FF sub-layer with FiLM
        gamma2, beta2 = self.film_ff(state_onehot).chunk(2, dim=-1)
        h = self.norm2(x)
        h = h * (1 + gamma2.unsqueeze(1)) + beta2.unsqueeze(1)
        h = self.ff(h)
        x = x + h
        return x
```

This adds ~2 * d_model * n_states * 2 * n_layers = 2 * 256 * 3 * 2 * 4 = 12,288 parameters. Negligible overhead.

### 3.4 adaLN-Zero Conditioning (Peebles & Xie, 2023)

adaLN-Zero is the state-of-the-art conditioning mechanism for class-conditional transformer generation. It replaces standard LayerNorm parameters with dynamically predicted parameters from the conditioning signal, plus a learnable gating parameter alpha that is zero-initialized so each block starts as the identity function.

**Implementation for StateBind (pseudocode):**
```python
class AdaLNZeroTransformerLayer(nn.Module):
    def __init__(self, d_model, n_states, n_heads, dim_ff):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads)
        self.ff = nn.Sequential(
            nn.Linear(d_model, dim_ff), nn.GELU(),
            nn.Linear(dim_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model, elementwise_affine=False)
        self.norm2 = nn.LayerNorm(d_model, elementwise_affine=False)
        # adaLN-Zero: condition -> gamma, beta, alpha for each sub-layer
        self.adaLN_modulation = nn.Sequential(
            nn.SiLU(),
            nn.Linear(d_model, 6 * d_model)  # 6 params: gamma1, beta1, alpha1, gamma2, beta2, alpha2
        )
        # Conditioning embedding
        self.cond_embed = nn.Linear(n_states, d_model)
        # Zero-initialize the final linear layer
        nn.init.zeros_(self.adaLN_modulation[-1].weight)
        nn.init.zeros_(self.adaLN_modulation[-1].bias)

    def forward(self, x, state_onehot, mask=None):
        c = self.cond_embed(state_onehot)
        gamma1, beta1, alpha1, gamma2, beta2, alpha2 = \
            self.adaLN_modulation(c).chunk(6, dim=-1)

        # Attention with adaLN-Zero
        h = self.norm1(x) * (1 + gamma1.unsqueeze(1)) + beta1.unsqueeze(1)
        h = self.attn(h, h, h, attn_mask=mask)[0]
        x = x + alpha1.unsqueeze(1) * h  # alpha gates the residual

        # FF with adaLN-Zero
        h = self.norm2(x) * (1 + gamma2.unsqueeze(1)) + beta2.unsqueeze(1)
        h = self.ff(h)
        x = x + alpha2.unsqueeze(1) * h
        return x
```

The zero-initialization is critical: it means the model initially ignores the conditioning and learns to gradually incorporate it during training, preventing early-training interference between reconstruction and conditioning objectives.

### 3.5 Classifier-Free Guidance for VAEs (Ho & Salimans, 2022)

Classifier-free guidance (CFG) is an inference-time technique that amplifies the conditioning signal. During training, the condition is randomly dropped (replaced with a null token) with probability p_uncond (typically 10-20%). At inference, two forward passes are computed -- one conditional and one unconditional -- and the final prediction is:

```
output = (1 + w) * conditional_output - w * unconditional_output
```

where w is the guidance scale (typically 1.0-7.5, with 2.0-3.0 being numerically stable for molecular generation per MolGuidance; Jin et al., 2025).

**Critical finding from MolGuidance (Jin et al., 2025; ICML 2025):** This work provides the first comprehensive comparison of guidance strategies for conditional molecular generation using SE(3)-equivariant flow matching. Key results:

- CFG achieved superior property alignment on 4 of 6 properties tested
- Optimal CFG weights: w_continuous = 2.71, w_discrete = 1.91
- CFG showed 2-3.4% decline in molecule stability versus unguided generation
- Discrete-only guidance outperformed continuous-only guidance
- Autoguidance matched or exceeded JODO baseline on 5 properties
- Model guidance underperformed across all properties

**CFG applicability to StateBind.** CFG is designed for diffusion models and flow matching, not directly for VAE decoders. However, adaptations exist. For autoregressive decoders (like the StateBind Transformer decoder), CFG can be applied at the logit level:

```python
# During generation:
logits_cond = decoder(z, state_onehot, generated_so_far)
logits_uncond = decoder(z, null_state, generated_so_far)
logits_guided = logits_uncond + w * (logits_cond - logits_uncond)
next_token = sample(logits_guided)
```

This requires training the model with state dropout (10-20% of the time, replace state_onehot with zeros). Implementation effort: ~1 day of code changes + retraining.

---

## 4. Published Effect Sizes for Conditional Molecular Generation

### 4.1 When Conditioning Works: Quantitative Benchmarks

| Paper | Architecture | Conditioning Type | Key Improvement | Dataset |
|-------|-------------|-------------------|-----------------|---------|
| Richards & Groener (2022) | Conditional beta-VAE | Latent prior conditioning | pLogP: 6.53 -> 104.29 (16x) | ZINC-250k |
| STAR-VAE (IBM, AAAI 2026) | Transformer VAE + LoRA | Property-conditioned prior + classifier guidance | Docking: -5.0 -> -6.3 (1SYH), p<0.0001 | PubChem 79M |
| CVAE (Romanelli et al., 2024) | CVAE with property vectors | Concatenation to latent | 4.8x more drug-like molecules than REINVENT4 | ChEMBL filtered |
| DiffSBDD (Schneuing et al., 2024) | SE(3) equivariant diffusion | Pocket inpainting | Vina: -5.69 -> -8.10 (scaffold elaboration) | CrossDocked2020 |
| MolGuidance (Jin et al., 2025) | Flow matching + CFG | Classifier-free guidance | Polarizability MAE: 1.97 -> 1.27 Bohr^3 | QM9 |
| SAFE-T (2025) | Chemical language model | Biological context conditioning | Activity cliff ROC-AUC: 0.541 -> 0.947 | MoAT-DB, ACNet |
| Lim et al. (2018) | CVAE (GRU encoder/decoder) | Concatenation to encoder+decoder | Clear latent clustering by properties | ZINC |

The critical observation: **when conditioning works, the improvements are dramatic and easily detectable**. pLogP jumps from 6.5 to 104 (Richards & Groener, 2022). Docking scores improve by 2+ kcal/mol (DiffSBDD, STAR-VAE). These are not subtle effects requiring careful statistical analysis -- they are order-of-magnitude improvements.

StateBind's Cohen's d = 0.059 is not what "weak but real conditioning" looks like. It is what "no conditioning signal" looks like. Published conditional generation papers show d >> 1.0 when the conditioning mechanism is adequate and the conditioning labels carry real information.

### 4.2 When Conditioning Fails: Known Failure Modes

From the literature, conditioning fails in specific, predictable circumstances:

1. **Labels carry no information about the output.** If the conditioning labels do not correspond to meaningfully different subpopulations in the training data, no mechanism can create a signal from nothing. This is H2.

2. **Conditioning signal is too weak relative to the autoregressive signal.** The decoder's own next-token prediction overwhelms the conditioning input. This is what happens with prefix tokens when the condition is a low-entropy discrete label.

3. **KL collapse absorbs the conditioning.** If the VAE's KL term is too loose, the model may encode the conditioning information into z rather than using the explicit conditioning pathway. StateBind uses free-bits (0.25/dim) and achieves total KL ~14.1/sample, so this is less likely here.

4. **Evaluation metric is orthogonal to the conditioning axis.** Even perfect conditioning on state X will show d = 0 if the evaluation scores molecules using a metric blind to state X. This is H3.

---

## 5. Disentangling H1 from H2 and H3

### 5.1 The Critical Diagnostic Question

The central challenge is: **is the null result because the conditioning mechanism fails to transmit the signal (H1), because there is no signal to transmit (H2), or because we are measuring the wrong thing (H3)?**

These hypotheses are not mutually exclusive. My assessment of their probabilities:

| Hypothesis | Probability | Evidence |
|------------|------------|---------|
| H1: Weak conditioning mechanism | 40-50% | Prefix tokens are weakest mechanism; centroid distances 6-10% of scale; DiT comparison shows 1.8x FID penalty for in-context vs adaLN-Zero |
| H2: No state-specific structure in data | 25-35% | Same scaffolds (anilinoquinazolines) dominate all 3 EGFR states; only 8,109 molecules; Type I inhibitors (DFGin) vastly outnumber Type II (DFGout) in public data |
| H3: Wrong evaluation metric | 20-30% | Single-pocket (1M17) docking cannot detect multi-state benefit; state_specificity zeroed; no cross-pocket comparison |
| Interaction (H1 x H2) | High | A weak mechanism will fail to extract even a weak signal that a strong mechanism might detect |

### 5.2 How to Disentangle Empirically

**Test H1 in isolation:** Strengthen the conditioning mechanism (FiLM or adaLN-Zero) while keeping the same training data and evaluation. If d increases substantially (>0.3), H1 was the bottleneck.

**Test H2 in isolation:** Keep the prefix-token mechanism but provide a "positive control" conditioning signal that IS known to be informative. For example:
- Condition on molecular weight bins (light/medium/heavy) instead of conformational states
- Condition on logP bins (hydrophilic/neutral/hydrophobic)
- Condition on scaffold class (quinazoline/pyrimidine/other)

If prefix-token conditioning on MW or logP produces d > 0.3 but conditioning on conformational state does not, then the state labels carry no information (H2 confirmed).

**Test H3 in isolation:** Take the existing ~6,800 molecules and dock them against ALL three pocket conformers (1M17, 4HJO, 3W2S). Compare: do conditioned-for-state-X molecules dock better in pocket-X than unconditioned molecules? This requires no retraining, only GNINA docking runs.

### 5.3 The "Positive Control" Experiment

The single most informative experiment is a positive control for the conditioning mechanism. Train the same Transformer VAE with the same prefix-token conditioning, but condition on a label that is KNOWN to be chemically informative. If we condition on molecular weight tercile (MW < 350, 350-450, > 450) using the same architecture:

- If conditioned generation produces molecules in the correct MW range: the mechanism works, and the problem is with state labels (H2) or evaluation (H3).
- If conditioned generation produces similar MW distributions regardless of the label: the mechanism is truly broken (H1 confirmed).

This experiment requires no code changes to the conditioning pathway -- only a change in the label assignment during data preparation. Cost: 2-3 GPU training runs, ~2 hours total.

---

## 6. Concrete Architectural Recommendations

### 6.1 Recommendation 1: FiLM Conditioning (Cheapest, Moderate Strength)

**What:** Replace prefix-token conditioning with FiLM layers applied at every transformer decoder layer.

**Why:** FiLM is the minimum viable upgrade. It applies the conditioning signal at every layer rather than only at the input, prevents the dilution problem, and adds negligible parameters (~12K vs. current model's ~2M+).

**Effort:** 1-2 days of code changes. Modify `TransformerSMILESDecoder` to replace `nn.TransformerEncoderLayer` with custom FiLM-conditioned layers. Keep the GRU encoder unchanged.

**Expected effect if H1 is the bottleneck:** Centroid distances should increase from 0.3-0.4 to 1.0-2.0. If state labels carry real information, d should increase to 0.3-0.8.

### 6.2 Recommendation 2: adaLN-Zero Conditioning (Moderate Cost, Strongest)

**What:** Replace LayerNorm in the Transformer decoder with adaptive LayerNorm where scale, shift, and residual gating parameters are predicted from the state embedding.

**Why:** This is the SOTA mechanism from DiT (Peebles & Xie, 2023), proven to be the best conditioning approach for class-conditional transformer generation. It achieved FID nearly half that of in-context conditioning. It modulates every layer and every sub-layer, and the zero-initialization provides a clean training signal.

**Effort:** 3-5 days. Requires replacing `nn.TransformerEncoderLayer` with custom layers. More invasive than FiLM but not fundamentally harder.

**Expected effect:** If state labels carry real information, this should produce the strongest possible conditioning signal. If d is still ~0 with adaLN-Zero, we can rule out H1 with high confidence.

### 6.3 Recommendation 3: Classifier-Free Guidance (Cheapest Amplifier)

**What:** Add CFG as an inference-time technique on top of any conditioning mechanism.

**Training change:** During training, replace state_onehot with zeros for 10-15% of batches. This teaches the model to generate both conditionally and unconditionally.

**Inference change:** Run two forward passes per generation step:
```python
logits_guided = logits_uncond + w * (logits_cond - logits_uncond)
```

**Why:** CFG amplifies whatever conditioning signal exists. If the signal is zero, CFG does nothing. If there is a weak signal that prefix tokens partially transmit, CFG can boost it. Optimal w for molecular generation is 2.0-3.0 (MolGuidance, Jin et al., 2025).

**Effort:** 1 day of code changes + retraining (~6 hours with 10 seeds).

**Risk:** CFG can reduce validity and diversity. MolGuidance reports 2-3.4% decline in molecule stability with CFG. However, since StateBind's Transformer VAE already achieves 93-97% validity, there is margin.

### 6.4 Recommendation 4: Separate Decoders Per State (Most Expensive, Definitive)

**What:** Train 3 independent Transformer VAE decoders, one per conformational state. Share the encoder.

**Why:** This eliminates the conditioning mechanism entirely. If 3 separate decoders trained on state-specific data still produce identical molecules, then H2 is definitively confirmed -- the states simply do not correspond to chemically distinct populations. If separate decoders produce meaningfully different molecules, then the problem was purely H1.

**Effort:** 1-2 weeks. Requires significant code refactoring and 3x training compute.

**Expected effect:** This is the nuclear option. It sacrifices all parameter sharing for maximum state specificity. The data is split: ~6,000 DFGin/aCin molecules, ~1,500 DFGin/aCout, ~600 DFGout/aCin. The small state populations (especially DFGout/aCin) may produce poor models, which itself would be evidence for H2.

---

## 7. Conditioning Strength Ladder Experiment

### 7.1 Design

A systematic experiment to isolate H1 by testing increasingly strong conditioning mechanisms on the same data, same seeds, same evaluation. This is the primary experiment I recommend.

**Ladder rungs (in order of increasing conditioning strength):**

| Rung | Mechanism | Additional Technique | Expected Behavior if H1 | Expected Behavior if H2 |
|------|-----------|---------------------|------------------------|------------------------|
| 0 | No conditioning (current unconditioned) | -- | d = 0 (baseline) | d = 0 (baseline) |
| 1 | Prefix tokens (current conditioned) | -- | d ~ 0.06 (observed) | d ~ 0.06 |
| 2 | Prefix tokens + CFG (w=2.0) | Condition dropout 15% | d = 0.1-0.3 | d ~ 0.06 |
| 3 | FiLM per-layer | -- | d = 0.3-0.6 | d ~ 0.1 |
| 4 | FiLM + CFG (w=2.0) | Condition dropout 15% | d = 0.5-0.8 | d ~ 0.1 |
| 5 | adaLN-Zero | -- | d = 0.5-1.0 | d ~ 0.1 |
| 6 | adaLN-Zero + CFG (w=2.0) | Condition dropout 15% | d = 0.8-1.5 | d ~ 0.1 |
| 7 | Separate decoders (3 independent) | -- | d > 1.0 | d ~ 0.1 |

**Interpretation key:**
- If d monotonically increases up the ladder: **H1 confirmed.** The conditioning mechanism was the bottleneck.
- If d plateaus at ~0.06 regardless of mechanism: **H2 confirmed.** There is no state-specific signal in the data.
- If d increases slightly (to ~0.2) but does not reach GO threshold: **H1 + H2 interaction.** The mechanism was weak AND the signal is weak. Need both stronger mechanism and better data.
- If d is high for positive controls (MW, logP) but low for state labels across all mechanisms: **H2 definitively confirmed.** State labels carry no chemical information.

### 7.2 Implementation Specification

**Seeds:** Use the same 10 seeds (42, 123, 7, 13, 37, 99, 256, 314, 512, 777) for all rungs.

**Training:** Same hyperparameters as current config (configs/transformer_vae.yaml): 2000 epochs, patience 300, batch 128, LR 3e-4, cosine schedule, free_bits=0.25.

**Evaluation:** Identical to Ablation C: reference_similarity=0.35, druglikeness=0.30, docking_proxy=0.20, state_specificity=0 (zeroed). Report Cohen's d on composite score (pooled molecules) and EF@10 (per-seed).

**Positive control (run alongside):** Rung 1 and Rung 3 trained with MW tercile labels instead of conformational state labels. Same architecture, same data, different labels.

**SLURM estimate for full ladder:**
- Rung 0: Already done (unconditioned models)
- Rung 1: Already done (current conditioned models)
- Rung 2: 10 retraining runs (need condition dropout) x ~45 min = ~7.5 hours
- Rung 3: 10 runs x ~45 min = ~7.5 hours
- Rung 4: 10 runs x ~45 min = ~7.5 hours
- Rung 5: 10 runs x ~45 min = ~7.5 hours
- Rung 6: 10 runs x ~45 min = ~7.5 hours
- Rung 7: 30 runs (10 seeds x 3 states) x ~45 min = ~22.5 hours
- Positive control: 20 runs x ~45 min = ~15 hours
- Total: ~75 GPU-hours on H200 or RTX 5000 Ada
- Can be parallelized: 10 SLURM array jobs per rung, ~7-8 hours wall time total

### 7.3 Decision Tree Based on Ladder Results

```
Rung 2 (prefix + CFG): d > 0.15?
  YES -> CFG amplifies existing signal. Run full ladder.
    Rung 5 (adaLN-Zero): d > 0.3?
      YES -> H1 was the primary bottleneck. Publish with stronger mechanism.
      NO  -> H1 + H2 interaction. Try positive control.
        Positive control d > 0.3?
          YES -> H2 confirmed. State labels are uninformative.
          NO  -> Mechanism still too weak? Unlikely. Check data quality.
  NO  -> No signal to amplify. Go directly to positive control.
    Positive control d > 0.3?
      YES -> H2 confirmed for state labels.
      NO  -> Something else is wrong. Check reconstruction quality.

In parallel (can run immediately):
  H3 test (cross-pocket docking): Conditioned molecules dock better in target pocket?
    YES -> H3 was masking the signal. Reframe thesis around docking specificity.
    NO  -> Conditioning truly produces no benefit. Negative result.
```

---

## 8. Key Evidence from Adjacent Fields

### 8.1 Type I vs Type II Kinase Inhibitors and State Specificity

The question of whether EGFR conformational states correspond to chemically distinct ligand populations has a known answer from the kinase pharmacology literature:

**Type I inhibitors** (bind DFGin) are typically 4-anilinoquinazolines (gefitinib, erlotinib, lapatinib) or 2-aminopyrimidines (osimertinib). They occupy the ATP-binding site in the active conformation.

**Type II inhibitors** (bind DFGout) feature a characteristic three-part structure: a hinge-binding head group, an amide/urea linker crossing the gatekeeper, and a hydrophobic tail occupying the allosteric pocket exposed by DFG flipping (Blanc et al., 2013; PMC4326797). Only 149 structurally validated Type II inhibitors exist in the PDB across all kinases.

**For EGFR specifically:** The overwhelming majority of EGFR inhibitors in ChEMBL are Type I (DFGin binders). Type II EGFR inhibitors are rare -- most DFGout binders in the kinase field target ABL (imatinib), KIT, or BRAF. This means StateBind's 3-state training data is likely dominated by DFGin/aCin molecules with very few true DFGout-selective compounds.

This is directly relevant to H2: if 90%+ of the 8,109 training molecules are Type I inhibitors that bind the DFGin conformation regardless of their state label assignment, then state labels are almost meaningless -- the model correctly learns to ignore them.

**Implication:** The choice of EGFR may be unfortunate for testing the state-conditioning thesis. A kinase with more balanced Type I/Type II inhibitor populations (e.g., ABL, where imatinib/nilotinib are DFGout and dasatinib/ponatinib are DFGin) would provide a much stronger test. However, this is an H2 concern.

### 8.2 PocketXMol and SBDD Conditioning

PocketXMol (Peng et al., Cell 2026) demonstrates that pocket-conditioned molecular generation produces real, experimentally validated improvements. Their model achieves strong performance on 11 of 13 computational benchmarks and generated caspase-9-inhibiting small molecules with efficacy comparable to commercial inhibitors, and PD-L1-binding peptides validated experimentally. This confirms that pocket conditioning CAN work when the conditioning mechanism (atom-level prompting) is strong and the pocket differences are chemically meaningful.

### 8.3 SAFE-T Conditional Chemical Language Model

SAFE-T (2025) provides a striking example of how conditioning mechanism design matters. Their three-stage training (chemical pretraining, biological context fine-tuning, preference optimization) with SAFE fragment-based representation achieves activity cliff prediction ROC-AUC of 0.947, up from 0.541 without preference tuning. The conditioning is applied through the language model's context window rather than through prefix tokens, and the model maintains >99% validity. The improvement from 0.541 to 0.947 is a massive effect size -- proof that conditioning on biological context CAN produce dramatic improvements when the mechanism and data are adequate.

---

## 9. Assessment of Root Cause Probability

### 9.1 My Assessment: H1 is Necessary but Not Sufficient

After extensive research, my assessment is:

**H1 probability: 70-80% that replacing the prefix-token mechanism with a stronger alternative would measurably increase the conditioning effect.** The evidence is strong:
- DiT comparison shows prefix/in-context conditioning is 1.8x worse than adaLN-Zero
- Information-theoretic argument: 1.58 bits across 8 tokens is vanishingly sparse
- Centroid distances of 6-10% of scale are consistent with "mechanism ignoring the label"
- The z-concatenation pathway puts state signal at 4.5% of input dimensions

**However, I estimate only 30-40% probability that strengthening the mechanism ALONE will produce d > 0.3 (GO threshold).** This is because:
- H2 likely also contributes: EGFR inhibitor populations may not be chemically differentiated by state
- H3 likely also contributes: single-pocket scoring cannot detect multi-state benefit
- The interaction H1 x H2 means even a strong mechanism cannot extract a signal that does not exist in the data

### 9.2 What the Project Should Do Next

**Immediate (Week 1, ~2 person-days, ~10 GPU-hours):**
1. Run the H3 test: dock all ~6,800 molecules against 3 pocket conformers. Cheapest test, requires no code changes, tests the evaluation hypothesis directly.
2. Run the positive control: retrain with MW-tercile labels using existing prefix-token architecture. Tests whether the mechanism can transmit ANY discrete label.

**Short-term (Weeks 2-3, ~5 person-days, ~40 GPU-hours):**
3. Implement FiLM conditioning in the Transformer decoder. Train 10 seeds.
4. Implement CFG (condition dropout during training, guided sampling during generation). Compatible with prefix tokens, FiLM, or adaLN.

**Medium-term (Weeks 3-5, ~7 person-days, ~25 GPU-hours):**
5. If FiLM shows improvement: implement adaLN-Zero for maximum conditioning strength.
6. Full conditioning strength ladder with all mechanisms.

**Decision point (Week 5):**
- If any mechanism produces d > 0.3 on existing data with existing scoring: **thesis is alive.** Strengthen mechanism, prepare positive-result publication.
- If no mechanism produces d > 0.3 but positive control works: **H2 confirmed.** Consider switching to ABL or using a kinase with better state-differentiated data.
- If no mechanism produces d > 0.3 and positive control also fails: **re-examine data pipeline.** Something is fundamentally wrong with the training data or the evaluation.
- If H3 test (cross-pocket docking) shows state-conditioned molecules dock better in their target pocket: **reframe the thesis** around pocket-specific docking improvement rather than generic quality improvement. This is a valid and publishable finding even without a stronger mechanism.

---

## 10. Publication Implications

### 10.1 Positive Outcome (Stronger Mechanism Works)

If adaLN-Zero or FiLM + CFG produces d > 0.5 on existing data:

**Paper narrative:** "Conditioning mechanism design is the critical bottleneck for state-conditioned molecular generation. Prefix-token conditioning fails (d=0.06), while adaLN-Zero/FiLM achieves d=X. This demonstrates that the thesis is architecturally dependent."

**Target venues:** JCIM, NeurIPS workshop, Nature Computational Science (if d > 0.8 with experimental validation).

### 10.2 Mixed Outcome (Mechanism Helps but Not Enough)

If d increases to 0.2-0.3 with stronger mechanisms:

**Paper narrative:** "State-conditioned molecular generation requires both strong conditioning mechanisms AND chemically differentiated training populations. We demonstrate a conditioning strength hierarchy for molecular VAEs."

**Target venues:** JCIM, Bioinformatics, ICML workshop.

### 10.3 Negative Outcome (Nothing Works)

If d remains ~0 across all mechanisms and positive controls work:

**Paper narrative:** "EGFR conformational states do not correspond to chemically distinct ligand populations in public bioactivity databases. State-conditioned generation requires kinases with structurally differentiated binding site pharmacophores."

**Target venues:** JCIM (negative result), J Med Chem (perspective on state-based design).

---

## 11. Technical Appendix: Attention Analysis Diagnostic

Before implementing new mechanisms, a cheap diagnostic can confirm whether prefix tokens are being used:

**Experiment:** Extract attention weights from all 4 transformer decoder layers. For each layer, compute the mean attention weight from molecule token positions to prefix token positions. Compare:
- Do molecule tokens attend heavily to prefix tokens (>0.1 average weight per prefix token)?
- Do the attention patterns differ by state label?
- Does attention to prefix tokens decrease in deeper layers (dilution)?

**Implementation:** Add a hook to `TransformerSMILESDecoder.forward()` that captures `self.transformer` attention weights. Can be done with `register_forward_hook`. No retraining needed.

**Cost:** ~1 hour of code + ~10 minutes of inference on existing models.

If attention to prefix tokens is negligible or state-independent, this provides direct evidence that the mechanism is being ignored. If attention is strong but state-independent, the prefix tokens are acting as attention sinks rather than conditioning signals.

---

## References

1. Blanc, J. et al. (2013). "Conformational analysis of the DFG-out kinase motif and biochemical profiling of structurally validated type II inhibitors." J. Med. Chem. 56(18), 7382-7399.

2. Ho, J. & Salimans, T. (2022). "Classifier-free diffusion guidance." arXiv:2207.12598. NeurIPS 2021 Workshop on Deep Generative Models and Downstream Applications.

3. Jin, J. et al. (2025). "MolGuidance: Advanced guidance strategies for conditional molecular generation with flow matching." arXiv:2512.12198. ICML 2025.

4. Li, X.L. & Liang, P. (2021). "Prefix-tuning: Optimizing continuous prompts for generation." ACL 2021.

5. Lim, J. et al. (2018). "Molecular generative model based on conditional variational autoencoder for de novo molecular design." J. Cheminformatics, 10(31).

6. Peebles, W. & Xie, S. (2023). "Scalable diffusion models with transformers." ICCV 2023.

7. Peng, X. et al. (2026). "Unified modeling of 3D molecular generation via atomic interactions with PocketXMol." Cell.

8. Perez, E. et al. (2018). "FiLM: Visual reasoning with a general conditioning layer." AAAI 2018.

9. Richards, W. & Groener, O. (2022). "Conditional beta-VAE for de novo molecular generation." arXiv:2205.01592.

10. Rombach, R. et al. (2022). "High-resolution image synthesis with latent diffusion models." CVPR 2022.

11. Romanelli, V. et al. (2024). "Enhancing de novo drug design across multiple therapeutic targets with CVAE generative models." ACS Omega, 9(43), 43561-43578.

12. Schneuing, A. et al. (2024). "Structure-based drug design with equivariant diffusion models." Nature Computational Science, 4, 899-909.

13. Vaswani, A. et al. (2017). "Attention is all you need." NeurIPS 2017.

14. Xiao, G. et al. (2024). "Efficient streaming language models with attention sinks." ICLR 2024.

15. Han, C. et al. (2024). "Prefixing attention sinks can mitigate activation outliers for large language model quantization." EMNLP 2024.

16. SAFE-T (2025). "Conditional chemical language models are versatile tools in drug discovery." arXiv:2507.10273.

17. VFMol (2026). "A discrete flow matching variational autoencoder for molecular graph generation." J. Chem. Inf. Model.

18. STAR-VAE (2025). "Latent variable transformers for scalable and controllable molecular generation." AAAI 2026.

19. Dumoulin, V. et al. (2018). "Feature-wise transformations." Distill.

20. KdaiP (2024). "1D Condition method pytorch: FiLM, Conditional Layer Norm and AdaIN." GitHub repository.

21. Kowalski, K. et al. (2015). "DFG-1 residue controls inhibitor binding mode and affinity." J. Med. Chem. 63(8), 4372-4383.

22. van Linden, O.P.J. et al. (2014). "KLIFS: A structural kinase-ligand interaction database." Nucleic Acids Research, 44(D1), D365-D371.

23. Dhillon, S. (2019). "Globally approved EGFR inhibitors: Insights into their syntheses, target kinases, biological activities, receptor interactions, and metabolism." Molecules, 24(11), 2166.

24. Controlled Generation with Equivariant Variational Flow Matching. ICML 2025. arXiv:2506.18340.

25. Leveraging tree-transformer VAE with fragment tokenization for high-performance large chemical model generation. Communications Chemistry (2025).
