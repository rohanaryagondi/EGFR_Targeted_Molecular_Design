---
agent: Conditional Generation Expert
round: 2
date: 2026-04-14
type: proposal
---

# Round 2 Proposal: Conditioning Architecture Recovery Plan

## 1. Updated Hypothesis Assessment

The Round 1 synthesis, particularly kinchembio's discovery that `prepare_vae_data.py`
line 499 passes an empty string to `_assign_state_from_type()` for all ChEMBL API
compounds, fundamentally changes the diagnostic picture. My Round 1 assessment of
H1 at 70-80% was based on the assumption that state labels carried at least partial
chemical information. That assumption was wrong.

**Revised probabilities:**

| Hypothesis | Round 1 | Round 2 | Rationale |
|------------|---------|---------|-----------|
| H2: Random labels (root cause) | 25-35% | **75-85%** | `rng.choice()` for 99.5% of data is definitive. No mechanism can learn from noise. |
| H1: Weak conditioning (compounding) | 70-80% | **15-20%** | Still true that prefix tokens are weak, but irrelevant when labels are random. Downgraded from root cause to compounding factor. |
| H3: Wrong evaluation (compounding) | 20-30% | **10-15%** | Real concern, but moot until labels are fixed. |

**The critical insight:** My Round 1 conditioning strength ladder (Section 7) predicted
that if H2 is the root cause, all rungs would plateau at d ~ 0.06-0.10 regardless of
mechanism strength. That is exactly what we should expect with random labels. Running
the full ladder on random labels would waste 75 GPU-hours confirming what we already
know from the code. The ladder becomes valuable only AFTER labels are fixed.

### 1.1 Does the Random-Label Finding Change My Recommendations?

Yes, dramatically. My Round 1 ordering was:
1. Conditioning strength ladder (test H1)
2. Positive control with MW-tercile labels (disentangle H1 from H2)
3. Cross-pocket docking (test H3)

**New ordering:**
1. Confirm the damage (zero-GPU scaffold overlap check)
2. Fix the labels and retrain with existing prefix tokens first
3. Then test whether prefix tokens suffice or need replacement

The positive control (MW-tercile) is no longer my top recommendation because we
no longer need to disentangle H1 from H2 -- we know H2 is the root cause. However,
the positive control retains value as a **validation step** after label fixing: if
real labels still produce d ~ 0.06 but MW-tercile labels produce d > 0.3, then the
biological signal (state-specific chemotypes in EGFR) is too weak even with correct
labels, and we should pivot to ABL1.

### 1.2 Should We Use FiLM/adaLN-Zero from the Start, or Re-test Prefix Tokens First?

**Re-test prefix tokens first.** Here is the reasoning:

The current null result conflates two variables: random labels AND weak mechanism.
Scientific rigor demands changing one variable at a time. If we simultaneously fix
labels AND upgrade to adaLN-Zero, and then observe d > 0.3, we cannot attribute the
improvement to either fix individually. The pre-registration tested prefix-token
conditioning against a specific thesis. The cleanest recovery is:

1. Fix labels, retrain with prefix tokens, measure d. (Isolates H2.)
2. If d is still < 0.2, THEN upgrade mechanism and retrain. (Tests H1 given real labels.)

This sequential approach costs one extra training round (~7.5 GPU-hours for 10 seeds)
but produces a much stronger scientific narrative: "The null result was caused by
data labeling, not architecture. With correct labels, even the weakest viable
mechanism (prefix tokens) produces d = X."

**Exception:** If the scaffold overlap pre-check (Action 1) shows that EGFR
molecules are chemically indistinguishable across states even with CORRECT labels
from KLIFS/PDB, then prefix tokens are unlikely to extract a signal that barely
exists. In that case, go directly to adaLN-Zero + ABL1 data.

### 1.3 How Does the Information Shortcut Interact with Architectural Recommendations?

mldebug identified a critical architectural flaw: the decoder's `z_proj` receives
`[z; state_onehot]` directly (line 327 of `transformer_vae.py`), meaning the encoder
has no incentive to encode state into z. This is the "posterior collapse of
conditioning" from Nguyen et al. (2023).

**Impact on my recommendations:**

- **For prefix tokens:** The shortcut means the decoder CAN access state information
  through the prefix projection, but only via the weak prefix-token pathway. The
  encoder correctly ignores state because it is redundant. This is suboptimal but
  not necessarily fatal -- the decoder's prefix projection does receive the full
  state one-hot. The question is whether 8 prefix tokens can transmit 1.58 bits
  effectively.

- **For FiLM/adaLN-Zero:** These mechanisms would receive state at every layer,
  making the encoder shortcut less relevant. The decoder would have strong
  per-layer access to state regardless of what the encoder does with it.

- **The fix:** If we upgrade to adaLN-Zero, we should ALSO remove the state
  concatenation from the encoder input. The encoder should produce a
  state-agnostic z, and ALL conditioning should flow through the decoder's
  adaLN layers. This eliminates the shortcut and creates a clean separation:
  z encodes molecular structure, adaLN modulates generation by state.

- **For the prefix-token retest:** Keep the current architecture as-is (including
  the shortcut) to isolate the effect of label fixing. The shortcut is a known
  weakness but not the primary failure mode when labels are random.

---

## 2. Top 3 Actions, Ranked by Effort/Impact

### Action 1: Scaffold Overlap Pre-Check with Real Labels (HIGHEST PRIORITY)

**What:** Before any retraining, determine whether EGFR molecules WITH CORRECT
state labels are chemically distinguishable across conformational states.

**Why this is first:** This is a zero-GPU, 2-hour analysis that determines whether
the EGFR thesis is even testable. If molecules assigned to different states via
KLIFS/PDB share >90% of their Murcko scaffolds, then no conditioning mechanism
on any architecture can produce state-specific generation for EGFR. This
would redirect us to ABL1 (where DFGin/DFGout distinction is chemically real)
before spending 50+ GPU-hours on retraining.

**Method:**

1. Query KLIFS for all EGFR structures with ligands, grouped by DFG/aC state.
   KLIFS (klifs.net) annotates every kinase-ligand co-crystal with its DFG and
   aC-helix conformation. This gives us ground-truth state labels for ~200-400
   EGFR-ligand complexes.

2. Extract Murcko scaffolds (RDKit `MurckoScaffold.MakeScaffoldGeneric()`) for
   ligands in each state.

3. Compute pairwise Tanimoto similarity (ECFP4) between state-specific ligand sets.

4. Calculate scaffold overlap: fraction of scaffolds appearing in 2+ states.

**Decision thresholds:**

| Scaffold Overlap | Interpretation | Next Step |
|-----------------|----------------|-----------|
| < 50% | States have distinct chemotypes | Fix labels, retrain (Action 2) |
| 50-75% | Partial distinction, may be enough | Fix labels, retrain, monitor d |
| > 75% | States chemically indistinguishable for EGFR | Pivot to ABL1 (kinchembio's recommendation) |

**Effort:** 2-4 hours of analysis. No GPU. No retraining. Can be done on the
login node or a `devel` partition CPU job.

**SLURM spec:** Not needed (CPU-only, runs in minutes).

**Expected outcome:** Based on kinchembio's analysis that >90% of EGFR inhibitors
are Type I, I expect scaffold overlap to be 60-80% for DFGin_aCin vs DFGin_aCout
(both bound by the same Type I scaffolds) but lower (30-50%) for DFGin vs DFGout
states. This would suggest a 2-state (DFGin vs DFGout) model rather than 3-state.

**Responding to kinchembio:** I agree that ABL1 is the stronger biological test
case. The question is whether we can salvage EGFR first (cheaper: same data
pipeline) or should jump directly to ABL1 (more work: new data pipeline, new
docking pockets). This pre-check answers that question in 2 hours.

---

### Action 2: Fix Labels and Retrain with Existing Architecture (CORE ACTION)

**What:** Replace random state assignment with real labels from KLIFS/PDB, retrain
the Transformer VAE with prefix-token conditioning, and re-run the 10-seed ablation.

**Why:** This is the minimum-change experiment that isolates H2. If d > 0.2 with
fixed labels and the same architecture, we know the null result was caused by
random labels. If d is still ~0.06, the architecture needs upgrading (proceed to
Action 3).

**Label-fixing strategy (two tiers):**

**Tier 1 -- KLIFS-matched labels (~200-400 molecules):**
- Query KLIFS API for EGFR structures with ligands
- Each structure has a DFG/aC-helix annotation
- Extract ligand SMILES from PDB
- Match to ChEMBL molecules by Tanimoto similarity (threshold 0.9)
- These are ground-truth labels

**Tier 2 -- Classifier-propagated labels (~2,000-4,000 molecules):**
- Train a Random Forest classifier on Tier 1 molecules (ECFP4 fingerprints ->
  state label) as proposed by kinchembio
- Apply to remaining ChEMBL EGFR molecules with pchembl >= 5
- Keep only predictions with probability > 0.7 (high-confidence labels)
- Discard molecules where the classifier is uncertain

**Why not keep all 8,109 molecules:** Quality over quantity. A 2,000-molecule
dataset with 80%+ correct labels will train a better conditional model than
8,109 molecules with random labels. The VAE already handles small datasets well
(EF@10 = 5-8 with the current training set).

**Training protocol:**
- Same config: `configs/transformer_vae.yaml` (2000 epochs, patience 300,
  batch 128, LR 3e-4, cosine schedule, free_bits 0.25)
- Same 10 seeds: 42, 123, 7, 13, 37, 99, 256, 314, 512, 777
- Same evaluation: Ablation C protocol with state_specificity = 0
- Additionally run with state_specificity enabled (evaldes's recommendation)
- 2-state variant (DFGin vs DFGout) if scaffold overlap pre-check suggests
  3 states are not distinguishable

**SLURM spec:**

```bash
#!/bin/bash
#SBATCH --job-name=vae_fixed_labels
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH -p gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=rtx_5000_ada:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH --array=0-9
```

- 10 array jobs (one per seed), ~45 min each
- Total GPU-hours: ~7.5 hours
- Wall time: ~1.5 hours (all seeds in parallel)

**Decision thresholds on the retrained model:**

| Result | Interpretation | Next Step |
|--------|----------------|-----------|
| d > 0.3 | Labels were the root cause. Prefix tokens sufficient. | Publish recovery. Add CFG for amplification. |
| d = 0.15-0.30 | Labels partially explain null. Mechanism also weak. | Proceed to Action 3 (adaLN-Zero). |
| d < 0.15 | Labels help but not enough. Either EGFR states are too similar or mechanism is too weak. | Run MW-tercile positive control to distinguish. If positive control works: pivot to ABL1. If not: mechanism is broken, proceed to Action 3. |

**Timeline:** 1-2 days for label fixing, 0.5 day for retraining, 0.5 day for evaluation.
Total: 2-3 days.

---

### Action 3: adaLN-Zero Upgrade (CONDITIONAL -- only if Action 2 shows d < 0.30)

**What:** Replace prefix-token conditioning with adaLN-Zero in the Transformer
decoder, retrain, and re-run the ablation. Simultaneously remove state
concatenation from the encoder to eliminate the information shortcut.

**Why adaLN-Zero over FiLM:** My Round 1 research showed that in the DiT
comparison (Peebles & Xie, 2023), adaLN-Zero achieved FID ~19.5 vs ~35 for
in-context conditioning (1.8x better) at identical compute cost. FiLM is a
reasonable intermediate step but adaLN-Zero is definitively better and not
significantly harder to implement. Given time pressure (competitive landscape
closing, per pubstrat), we should go directly to the strongest mechanism.

**Architecture changes (specific to `transformer_vae.py`):**

1. **New module: `AdaLNZeroTransformerLayer`**
   - Replace `nn.TransformerEncoderLayer` with a custom layer
   - Conditioning embedding: `state_embed = MLP(state_onehot)` producing a
     d_model-dimensional vector
   - Each layer: regress (gamma1, beta1, alpha1, gamma2, beta2, alpha2) from
     state_embed via a single Linear(d_model, 6 * d_model)
   - gamma1/beta1 modulate the pre-attention LayerNorm
   - alpha1 gates the attention residual (initialized to zero)
   - gamma2/beta2 modulate the pre-FFN LayerNorm
   - alpha2 gates the FFN residual (initialized to zero)

2. **Remove prefix tokens entirely**
   - Delete `z_proj` (saves 67 * 2048 = 137K parameters)
   - z is injected ONLY through a new cross-attention mechanism or through a
     learned z-to-memory projection that creates 8 key-value pairs for
     cross-attention

3. **Remove state from encoder input**
   - Change encoder input dim from `embed_dim + n_states` to `embed_dim`
   - This eliminates the shortcut: z is now state-agnostic
   - All conditioning flows through the decoder's adaLN layers

4. **Add condition dropout for CFG**
   - During training, replace state_onehot with zeros 15% of the time
   - At inference, use guidance scale w=2.0:
     `logits = logits_uncond + w * (logits_cond - logits_uncond)`

**Implementation pseudocode:**

```python
class AdaLNZeroBlock(nn.Module):
    def __init__(self, d_model, n_heads, dim_ff, cond_dim):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model, elementwise_affine=False)
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.norm2 = nn.LayerNorm(d_model, elementwise_affine=False)
        self.ff = nn.Sequential(
            nn.Linear(d_model, dim_ff), nn.GELU(),
            nn.Linear(dim_ff, d_model),
        )
        # Regress 6 modulation vectors from condition
        self.adaLN_modulation = nn.Sequential(
            nn.SiLU(),
            nn.Linear(cond_dim, 6 * d_model),
        )
        # Zero-init the modulation output
        nn.init.zeros_(self.adaLN_modulation[-1].weight)
        nn.init.zeros_(self.adaLN_modulation[-1].bias)

    def forward(self, x, cond, mask=None):
        # cond: (batch, cond_dim) -- state embedding
        shift_msa, scale_msa, gate_msa, shift_mlp, scale_mlp, gate_mlp = (
            self.adaLN_modulation(cond).chunk(6, dim=-1)
        )
        # Each is (batch, d_model) -> unsqueeze to (batch, 1, d_model)
        h = self.norm1(x) * (1 + scale_msa.unsqueeze(1)) + shift_msa.unsqueeze(1)
        h = self.attn(h, h, h, attn_mask=mask)[0]
        x = x + gate_msa.unsqueeze(1) * h

        h = self.norm2(x) * (1 + scale_mlp.unsqueeze(1)) + shift_mlp.unsqueeze(1)
        h = self.ff(h)
        x = x + gate_mlp.unsqueeze(1) * h
        return x
```

**Addressing the shortcut (mldebug's finding):**

With adaLN-Zero, we explicitly separate the roles:
- **z** encodes molecular identity (structure, scaffold, functional groups)
- **state** modulates generation style via adaLN at every layer
- The encoder sees ONLY the molecule (no state concatenation)
- The decoder sees z through cross-attention (or prefix, but now z-only)
  and state through adaLN modulation

This architecture eliminates the shortcut because:
- The encoder cannot see state, so z is guaranteed state-agnostic
- The decoder receives state ONLY through adaLN, which modulates every
  layer's activations with per-layer gating (6 modulation vectors per layer)
- There is no pathway for state to be "accidentally" ignored

**SLURM spec:**

```bash
#!/bin/bash
#SBATCH --job-name=vae_adaln_zero
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH -p gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=rtx_5000_ada:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH --array=0-9
```

- Same 10 seeds, same evaluation protocol
- Training time per seed: ~50-60 min (slightly longer due to adaLN compute)
- Total GPU-hours: ~10 hours
- Wall time: ~2 hours

**Timeline:** 3-5 days for implementation + 0.5 day for training + 0.5 day for
evaluation. Total: 4-6 days.

**Expected outcomes:**

| Scenario | d with prefix (Action 2) | d with adaLN-Zero | Interpretation |
|----------|-------------------------|-------------------|----------------|
| A | 0.20-0.30 | 0.40-0.80 | Both labels and mechanism mattered. adaLN-Zero amplifies the biological signal. Publish. |
| B | < 0.15 | 0.30-0.60 | Mechanism was the main remaining bottleneck after label fix. Publish with architectural comparison. |
| C | < 0.15 | < 0.15 | EGFR states are not chemically distinguishable. Pivot to ABL1 or publish as negative result. |
| D | > 0.30 | > 0.30 | Labels were sufficient. adaLN-Zero is better but prefix tokens work. Simplest narrative. |

---

## 3. Responding to Other Agents

### 3.1 kinchembio -- ABL1 pivot

I strongly support having an ABL1 contingency plan. ABL1 has genuine DFGin/DFGout
chemotype distinction: imatinib/nilotinib are Type II (DFGout), while dasatinib/
bosutinib are Type I (DFGin). The Tanimoto similarity between these classes is
likely < 0.3. However, building a full ABL1 pipeline (data preparation, docking
pocket preparation, scoring calibration) is 2-3 weeks of work. I recommend:

- Run the EGFR recovery first (Actions 1-2, 3-5 days total)
- In parallel, start ABL1 data preparation (kinchembio's 2-hour classifier)
- If EGFR Actions 1-2 show d < 0.15 with correct labels, pivot to ABL1

### 3.2 evaldes -- Multi-pocket docking

I agree that the single-pocket evaluation is a structural flaw, but it is a
lower-priority fix than the random labels. The evaluation flaw can only matter
if the model IS generating state-specific molecules that the metric cannot
detect. With random labels, the model cannot generate state-specific molecules.
Therefore: fix labels first, then fix evaluation.

That said, I recommend running evaldes's multi-pocket docking as a PARALLEL
track once Action 2 (retrained model) produces molecules. It adds 4-8 GPU-hours
but provides the definitive answer on whether state-specific docking quality
improves.

### 3.3 mldebug -- Diagnostic battery

mldebug's 7-experiment battery (especially D1: probing classifier, D3: attention
analysis, D5: state swap) should run on the RETRAINED model (after Action 2),
not on the current model trained with random labels. Running diagnostics on the
current model will confirm that the model ignores state labels -- which we already
know because the labels are random. The diagnostics become valuable as a health
check on the retrained model.

**Exception:** The scaffold overlap pre-check (my Action 1) incorporates mldebug's
spirit of "cheapest diagnostic first" but operates on the DATA rather than the
MODEL. This should run immediately.

### 3.4 pubstrat -- Sequential testing cascade

I fully agree with pubstrat's sequential cascade approach. The decision tree I
propose below aligns with their framework: cheapest tests first, go/no-go gates
at each stage, every outcome publishable.

---

## 4. Integrated Timeline and Decision Tree

### Week 1 (Days 1-3): Foundation

| Day | Action | GPU-hours | Output |
|-----|--------|-----------|--------|
| 1 | Scaffold overlap pre-check (Action 1) | 0 | GO/NO-GO for EGFR |
| 1-2 | Fix labels using KLIFS/PDB + classifier | 0 | New training data |
| 2-3 | Retrain 10 seeds with prefix tokens (Action 2) | 7.5 | 10 checkpoints |
| 3 | Evaluate: 10-seed ablation | 1 | Cohen's d |

**Gate G2b:** d from retrained prefix-token model with real labels.

```
d > 0.30 --> GO. Prefix tokens sufficient. Add CFG, publish recovery.
d = 0.15-0.30 --> CONDITIONAL GO. Labels helped but mechanism is weak. Week 2: adaLN-Zero.
d < 0.15 --> INVESTIGATE. Run MW-tercile positive control.
  MW-tercile d > 0.30 --> Architecture works, EGFR states too similar. Pivot to ABL1.
  MW-tercile d < 0.15 --> Architecture is also broken. Week 2: adaLN-Zero + ABL1.
```

### Week 2 (Days 4-9): Architecture Upgrade (conditional on d < 0.30)

| Day | Action | GPU-hours | Output |
|-----|--------|-----------|--------|
| 4-7 | Implement adaLN-Zero decoder (Action 3) | 0 | New code |
| 8 | Retrain 10 seeds with adaLN-Zero | 10 | 10 checkpoints |
| 9 | Evaluate + mldebug diagnostic battery | 2 | Cohen's d + diagnostics |

**Gate G2c:** d from adaLN-Zero model with real labels.

```
d > 0.30 --> GO. Stronger mechanism was needed. Publish with DiT comparison.
d < 0.15 --> NO-GO for EGFR. Pivot to ABL1 or negative-result paper.
```

### Week 3 (Days 10-14): Parallel Tracks

Two parallel efforts based on Week 2 results:
- **Track A (if d > 0.30):** Multi-pocket docking evaluation (evaldes), CFG
  optimization, prepare publication figures
- **Track B (if d < 0.15 on EGFR):** ABL1 data pipeline + retraining with
  adaLN-Zero

### Total Resource Estimate

| Phase | GPU-hours | Person-days | SLURM jobs |
|-------|-----------|-------------|------------|
| Action 1 (scaffold check) | 0 | 0.5 | 0 |
| Action 2 (label fix + retrain) | 8.5 | 2 | 11 |
| Action 3 (adaLN-Zero, conditional) | 12 | 5 | 11 |
| MW-tercile positive control (conditional) | 7.5 | 1 | 10 |
| Multi-pocket docking (parallel) | 6 | 1 | 10 |
| **Total (worst case)** | **34** | **9.5** | **42** |
| **Total (best case: labels fix it)** | **8.5** | **2.5** | **11** |

---

## 5. What Does Not Change from Round 1

Despite the revised hypothesis ordering, several Round 1 findings remain directly
relevant:

1. **The conditioning strength ladder retains value** -- but should run AFTER
   labels are fixed. With real labels, comparing prefix tokens vs FiLM vs
   adaLN-Zero on the same data would make an excellent ablation study for
   publication. The ladder transforms from "diagnostic" to "publication content."

2. **CFG remains the cheapest amplifier.** Once we have ANY working conditioning
   mechanism, adding CFG (1 day of code + retraining with 15% condition dropout)
   provides inference-time amplification. MolGuidance (Jin et al., 2025) showed
   CFG with w=2.0-3.0 improves controllability metrics by 25-50%.

3. **The DiT comparison data is still the strongest evidence** that prefix tokens
   are suboptimal. Peebles & Xie (2023) showed a 1.8x FID gap between in-context
   and adaLN-Zero conditioning. This motivates Action 3 if Action 2 shows d < 0.30.

4. **The positive control experiment remains the ultimate H2 test.** If we
   condition on MW-tercile labels (which are trivially correct) and still get
   d ~ 0.06, then the architecture itself is broken (H1). If MW-tercile gives
   d > 0.3 but state labels give d ~ 0.06, then the state labels carry no
   chemical information (H2 for EGFR specifically, not for the thesis in general).

---

## 6. Key Risks and Mitigations

| Risk | Probability | Mitigation |
|------|-------------|------------|
| KLIFS has too few EGFR structures for reliable labels | 20% | Use PDB directly; cross-reference with literature Type I/II annotations |
| Classifier propagation introduces label noise | 30% | Use strict probability threshold (>0.7); validate with cross-validation |
| adaLN-Zero implementation introduces bugs | 15% | Unit test each component; compare reconstruction loss to baseline |
| EGFR truly has no state-specific chemotype signal | 40% | ABL1 contingency; negative result publication |
| Retraining takes longer than estimated | 10% | Use priority queue (`-p priority -A prio_gerstein`) for faster scheduling |

---

## References

- Peebles, W., & Xie, S. (2023). Scalable diffusion models with transformers. ICCV 2023.
- Perez, E., Strub, F., De Vries, H., Dumoulin, V., & Bengio, Y. (2018). FiLM: Visual reasoning with a general conditioning layer. AAAI 2018.
- Ho, J., & Salimans, T. (2022). Classifier-free diffusion guidance. NeurIPS 2021 Workshop.
- Jin, W., et al. (2025). MolGuidance: Classifier-free guidance for molecular generation with flow matching.
- Nguyen, A., et al. (2023). On the posterior collapse of conditional VAEs. ICLR 2023.
- Li, X. L., & Liang, P. (2021). Prefix-tuning: Optimizing continuous prompts for generation. ACL 2021.
- Sohn, K., Lee, H., & Yan, X. (2015). Learning structured output representation using deep conditional generative models. NeurIPS 2015.
- Alain, G., & Bengio, Y. (2017). Understanding intermediate layers using linear classifier probes. ICLR 2017 Workshop.
- Xiao, G., et al. (2024). Efficient streaming language models with attention sinks. ICLR 2024.
