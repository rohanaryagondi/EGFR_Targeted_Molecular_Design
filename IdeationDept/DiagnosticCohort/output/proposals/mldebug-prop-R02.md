---
agent: ML Diagnostics Expert
round: 2
date: 2026-04-14
type: proposal
---

# ML Diagnostics Proposal: Triage, Confirmation, and Monitoring Protocol

## 1. Updated Hypothesis Probabilities

Given the Round 1 synthesis and the random-label finding from kinchembio:

| Hypothesis | Round 1 | Round 2 | Rationale |
|------------|---------|---------|-----------|
| H2: Random labels | 45% | **80%** | Direct code evidence (`rng.choice()`), uniform distribution, corroborated independently |
| H1: Weak architecture | 35% | **15%** | Real but secondary. Prefix tokens are suboptimal, but irrelevant when labels are noise |
| H3: Wrong evaluation | 20% | **5%** | Real but tertiary. Cannot matter until model receives a signal to encode |

The random-label finding is decisive. A well-trained model on random labels SHOULD
ignore them. The observed Cohen's d = 0.059 and centroid distances of 6-10% of
latent scale are the *correct* behavior, not a failure. The diagnostic question
shifts from "where does the signal die?" to "can we confirm it was never there, and
what should we monitor when it is?"

---

## 2. Triage of the Round 1 Diagnostic Battery

### 2.1 Which of the 7 Diagnostics Are Still Informative?

| # | Diagnostic | Still Useful? | Why | Effort |
|---|-----------|--------------|-----|--------|
| D1 | Probing classifier on z | **YES -- as confirmation** | Expected ~33%. Running it takes 5 min and closes the loop definitively. If it shows >50%, our random-label theory is wrong. | 5 min GPU |
| D2 | Encoder hidden state probe | **SKIP** | If labels are random, the encoder hidden states will also show ~33%. This diagnostic distinguishes "encoder never captures state" from "bottleneck discards state," but that distinction is moot when labels are noise. | -- |
| D3 | Prefix attention analysis | **SKIP for now** | Informative only after retraining with real labels. On current model, prefix tokens carry no meaningful state signal regardless of attention pattern. | -- |
| D4 | State-swap experiment | **YES -- as confirmation** | Expected >95% identical outputs. If state-swapping changes outputs substantially, the model learned something from the labels despite their randomness, which would challenge the H2 theory. Fast and informative. | 15 min GPU |
| D5 | Scaffold overlap (training data) | **YES -- HIGHEST VALUE** | This is the one diagnostic that answers a question INDEPENDENT of the model: does the training data itself contain state-specific chemistry? If Jaccard overlap >0.85 across states in the training data, the labels are provably uninformative even if they were correctly assigned. This diagnostic is CPU-only and takes minutes. | 5 min CPU |
| D6 | Per-dimension KL analysis | **SKIP** | Same reasoning as D2. With random labels, no dimension will show state-dependent behavior. Revisit after retraining. | -- |
| D7 | Mutual information I(z; state) | **YES -- as confirmation** | Expected MI < 0.05 nats (< 5% of H(state)). Combined with D1, provides both a classifier-based and information-theoretic confirmation of the null. | 5 min GPU |

**Verdict:** Run D1, D4, D5, D7 from the original battery. Skip D2, D3, D6. Total
cost: ~30 minutes (25 min GPU + 5 min CPU). D5 is the most informative because it
tests the data directly, independent of the model.

### 2.2 The Critical Insight: D5 Answers a Different Question

D1/D4/D7 all ask: "did the model learn state information?" With random labels, the
answer is trivially no. But D5 asks: "does the training data CONTAIN state-specific
chemistry?" This question survives the random-label finding because it reveals
whether fixing labels would even help.

If D5 shows training-data scaffold overlap >0.85 between states, then even with
perfectly assigned labels, the chemical space is too homogeneous for conditioning to
work on EGFR. This would shift the recovery path toward ABL1 (where type I vs type
II scaffolds genuinely differ) rather than EGFR re-annotation.

**Important caveat:** With random labels, D5 on the training data will show high
overlap BY CONSTRUCTION (random assignment means each state gets a random sample of
the same pool). The informative version of D5 must be run on PROPERLY LABELED data --
either from KLIFS annotation or from kinchembio's proposed state classifier. This
means D5 is a diagnostic for AFTER label fixing, not before.

The exception: run D5 on the ~55 curated compounds (Tier 3) as a proof-of-concept.
If even the curated compounds show high scaffold overlap, EGFR may be fundamentally
unsuitable.

---

## 3. Top 3 Proposed Actions

### Action 1: Confirmation Battery (D1 + D4 + D5-curated + D7)

**Priority: IMMEDIATE (run in parallel with kinchembio's state classifier)**

**What:** Run the 4 retained diagnostics on the existing conditioned checkpoint (seed 0).

**Why:** Confirmation is cheap and necessary. The random-label finding is from code
inspection and metadata analysis. Running diagnostics on the trained model provides
independent empirical confirmation. If any diagnostic contradicts the prediction
(e.g., D1 shows >50% accuracy), we need to reassess.

**Specific predictions (pre-registered before running):**

| Diagnostic | Predicted Result | If Violated |
|-----------|-----------------|-------------|
| D1: Probing classifier | 33-37% accuracy (chance) | Model learned something from random labels; investigate overfitting to the 55 curated compounds |
| D4: State-swap | >95% identical outputs | Conditioning has some effect; check if decoder uses state_onehot directly through the shortcut |
| D7: MI estimate | < 0.05 nats (< 5% of H(state)) | Same as D1 violation |
| D5: Curated scaffold overlap | Jaccard 0.3-0.6 between type I/type II curated compounds | If >0.8, even curated compounds are chemically similar across states |

**SLURM spec:**
```bash
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 00:30:00
```

**Effort:** 0.5 GPU-hours, 1 person-hour to write the script.

**Deliverable:** JSON artifact `artifacts/diagnostics/confirmation_battery_results.json`
with all 4 diagnostic outputs and pass/fail against predictions.

---

### Action 2: Loss-Curve Diagnostic (NEW -- Not in Round 1)

**Priority: HIGH (run concurrently with Action 1)**

**What:** Compare training loss convergence curves between conditioned and
unconditioned model runs. If labels carry no information, the conditioned model's
loss curve should be statistically indistinguishable from the unconditioned model's
loss curve. This is the simplest possible test of "do labels add information?"

**Why this is informative beyond the state classifier (kinchembio):**

The state classifier answers: "can a downstream model distinguish states from
molecular fingerprints?" This tests the DATA. The loss-curve diagnostic answers:
"did the VAE benefit from having state labels during training?" This tests the
MODEL'S LEARNING PROCESS.

Specifically, for a conditional VAE, the ELBO decomposes as:

```
ELBO = E_q[log p(x|z,c)] - KL(q(z|x,c) || p(z|c))
```

If c (state) carries information about x (molecule), then:
- The reconstruction loss `E_q[log p(x|z,c)]` should be LOWER for the conditioned
  model (state helps reconstruct molecules)
- The KL term should show state-dependent structure

If c is random noise:
- Reconstruction loss should be IDENTICAL between conditioned and unconditioned
- KL term should be identical (encoder learns to ignore c)

**Implementation:**

```python
def loss_curve_diagnostic(conditioned_log, unconditioned_log):
    """Compare training loss trajectories.

    Args:
        conditioned_log: path to training log with per-epoch losses
        unconditioned_log: path to unconditioned training log

    Returns:
        dict with:
          - final_recon_loss_diff: should be ~0 if labels uninformative
          - final_kl_diff: should be ~0 if labels uninformative
          - convergence_epoch_diff: should be ~0
          - paired_t_test on final 10 epochs of recon loss
    """
    import json
    import numpy as np
    from scipy.stats import ttest_ind

    with open(conditioned_log) as f:
        cond = json.load(f)
    with open(unconditioned_log) as f:
        uncond = json.load(f)

    # Extract per-epoch reconstruction and KL losses
    cond_recon = [e['val_recon_loss'] for e in cond['epochs']]
    uncond_recon = [e['val_recon_loss'] for e in uncond['epochs']]
    cond_kl = [e['val_kl_loss'] for e in cond['epochs']]
    uncond_kl = [e['val_kl_loss'] for e in uncond['epochs']]

    # Compare final 10 epochs
    n_final = 10
    t_stat_recon, p_recon = ttest_ind(
        cond_recon[-n_final:], uncond_recon[-n_final:]
    )
    t_stat_kl, p_kl = ttest_ind(
        cond_kl[-n_final:], uncond_kl[-n_final:]
    )

    return {
        'final_recon_loss_conditioned': float(np.mean(cond_recon[-n_final:])),
        'final_recon_loss_unconditioned': float(np.mean(uncond_recon[-n_final:])),
        'recon_loss_diff': float(
            np.mean(cond_recon[-n_final:]) - np.mean(uncond_recon[-n_final:])
        ),
        'recon_loss_p_value': float(p_recon),
        'final_kl_conditioned': float(np.mean(cond_kl[-n_final:])),
        'final_kl_unconditioned': float(np.mean(uncond_kl[-n_final:])),
        'kl_diff': float(
            np.mean(cond_kl[-n_final:]) - np.mean(uncond_kl[-n_final:])
        ),
        'kl_p_value': float(p_kl),
        'interpretation': (
            'LABELS_UNINFORMATIVE' if p_recon > 0.05
            else 'LABELS_PROVIDE_SIGNAL'
        ),
    }
```

**What counts as confirmation:**
- Recon loss difference < 0.5% AND p > 0.05: labels are noise (confirms H2)
- Recon loss difference > 2% AND p < 0.01: labels somehow help (challenges H2)
- KL difference significant: encoder is using labels differentially (challenges H2)

**Effort:** If training logs exist: 10 minutes CPU, 0 GPU. If we need to extract
from checkpoints: re-run 1 epoch of validation on each checkpoint, ~15 min GPU.

**Note:** The 10-seed ablation produced both conditioned and unconditioned checkpoints
(seeds 0-9 each). We already have 20 trained models. Comparing their final validation
losses is essentially free.

**SLURM spec:** CPU-only, or share the Action 1 GPU job.

---

### Action 3: Post-Fix Monitoring Protocol (For After Labels Are Fixed)

**Priority: DESIGN NOW, EXECUTE AFTER DATA FIX**

**What:** A comprehensive monitoring protocol to run during and after retraining with
properly annotated data. This ensures we can detect whether the conditioning signal
propagates correctly through the fixed pipeline.

**Why:** Fixing labels is necessary but not sufficient. The architecture has a known
shortcut (decoder receives state directly via prefix projection), and the evaluation
has known flaws (single pocket, zeroed state_specificity). We need to monitor the
full chain: data -> encoder -> latent -> decoder -> output -> evaluation.

**The monitoring protocol has 4 checkpoints:**

#### Checkpoint A: Training-Time Monitoring (during retraining)

Run at every epoch (or every 5 epochs for compute efficiency):

1. **Per-state validation loss divergence.** Track `val_recon_loss` separately per
   state. If labels are informative, losses should diverge across states (the model
   learns different reconstruction targets per state). If losses remain identical
   across states, the model is ignoring the labels even when they are correct.

   ```python
   # Add to training loop
   for state_idx in range(n_states):
       state_mask = (batch['state_idx'] == state_idx)
       if state_mask.sum() > 0:
           state_recon = recon_loss[state_mask].mean()
           log(f'val_recon_state_{state_idx}', state_recon)
   ```

2. **Probing classifier accuracy on z (D1) at epoch boundaries.** Track how
   quickly the encoder learns to encode state. Expect: accuracy rises from ~33%
   (random init) to >50% within first 10 epochs if labels are informative.

3. **Centroid distance growth.** Track inter-state centroid distances in latent
   space at each epoch. Expect: distances grow from 0 (random init) to >1.0 (if
   conditioning works). The Round 1 value of 0.26-0.42 should be the MINIMUM
   we achieve with proper labels.

#### Checkpoint B: Post-Training Diagnostics (after retraining completes)

Run the full confirmation battery (D1 + D4 + D5 + D7) from Action 1 on the
newly trained model. Expected results with proper labels:

| Diagnostic | Expected (if fix works) | Expected (if fix fails) |
|-----------|------------------------|------------------------|
| D1: Probing accuracy | >55% | 33-40% |
| D4: State-swap identity | <70% | >90% |
| D5: Generated scaffold Jaccard | <0.65 | >0.85 |
| D7: MI I(z;state) | >0.15 nats (>15% H(state)) | <0.05 nats |

**Go/No-Go gate:** If D1 accuracy < 45% after retraining with proper labels, the
problem is NOT just the data. Proceed to architecture fix (FiLM/adaLN-Zero). If
D1 accuracy > 55%, data fix worked and we can evaluate the thesis.

#### Checkpoint C: Architecture Decision Point

If Checkpoint B fails (D1 < 45% with proper labels), the information shortcut
is the likely culprit. The decoder receives `[z; state_onehot]` directly via
`z_proj`, so the encoder has no incentive to encode state into z even when state
labels are informative.

**Diagnosis of the shortcut:**

To confirm the shortcut is active, run D1 on z alone, then on `[z; state_onehot]`
(the decoder's actual input). If the latter is much more predictive than the
former, the decoder uses state through the direct path, not through z.

**Resolution options (ranked by implementation effort):**

1. **Remove the shortcut (easiest, 2 hours).** Change `z_proj` input from
   `[z; state_onehot]` to `z` alone. Force ALL state information to pass through
   z. Risk: may destabilize training if the decoder relied on the direct path.

   ```python
   # Current: z_proj = Linear(latent_dim + n_states, n_prefix * d_model)
   # Fixed:   z_proj = Linear(latent_dim, n_prefix * d_model)
   # Decoder must extract state from z, forcing encoder to encode it.
   ```

2. **Separate state and content prefix tokens (moderate, 1 day).** Use separate
   projections: `z -> content_prefix` (6 tokens) and `state -> state_prefix`
   (2 tokens). This preserves the direct state path but makes it structurally
   distinct from z, preventing the encoder from offloading state encoding.

3. **FiLM conditioning (moderate, 1-2 days).** Replace prefix-token conditioning
   with FiLM layers as condgen proposes. This eliminates the shortcut entirely by
   conditioning at every layer through affine transforms rather than through
   concatenation to z.

4. **adaLN-Zero (higher effort, 3-5 days).** The strongest mechanism per DiT.
   Replaces LayerNorm parameters with condition-predicted values. Best performance
   but requires more architectural changes.

**My recommendation:** Try option 1 first (remove shortcut, 2 hours). If training
destabilizes, fall back to option 2 (separate prefixes, 1 day). Only escalate to
FiLM/adaLN-Zero if prefix-based approaches fail with proper labels. This follows
the cheapest-test-first principle.

#### Checkpoint D: Evaluation Calibration

After model retraining succeeds (Checkpoint B pass), run evaldes's multi-pocket
docking protocol. But ALSO run the single-pocket evaluation as a control. The
difference between multi-pocket and single-pocket Cohen's d quantifies the
contribution of H3 to the original null result.

---

## 4. Response to condgen's MW-Tercile Positive Control

### 4.1 Is It a Valid Diagnostic?

**Yes, with caveats.** The MW-tercile experiment (condition on molecular weight bins
instead of conformational state) is an excellent positive control for the conditioning
MECHANISM. The logic is sound:

- MW terciles are objectively determinable from SMILES (no annotation ambiguity)
- MW distribution in training data is continuous, so tercile bins create genuinely
  distinct chemical subpopulations (light fragments vs heavy multi-ring compounds)
- If MW conditioning works but state conditioning does not, the mechanism is functional
  and the data (state labels) is the problem

### 4.2 What the Probing Classifier Would Show for MW-Conditioned Models

For a MW-conditioned model:
- **D1 (probe on z):** Expected accuracy 70-90%. MW is strongly correlated with
  molecular structure (atom count, ring count, chain length). The encoder would
  encode MW-related features into z even without explicit conditioning because MW is
  an intrinsic property of the molecule. The probe should easily extract this.
- **D4 (state-swap):** Expected <50% identical outputs. Swapping MW condition from
  "light" to "heavy" should produce visibly different molecules (shorter vs longer
  SMILES, different ring counts).
- **D7 (MI):** Expected >0.5 nats (>45% of H(MW_tercile)). Strong mutual information.

### 4.3 The Caveat: MW Is Too Easy

MW is essentially a function of SMILES length. The encoder's GRU naturally encodes
sequence length into its hidden state. MW conditioning may succeed trivially because
the encoder cannot AVOID encoding MW. This does not prove the mechanism works for
ARBITRARY conditioning variables -- only for variables correlated with sequence
structure.

A better positive control would be **ring count terciles** or **heteroatom fraction
terciles** -- properties that are informative about chemical structure but not as
trivially encoded as MW. If ring-count conditioning also works, the mechanism is
genuinely functional for structural properties.

**Recommendation:** Run MW-tercile first (cheapest confirmation), then ring-count
as a harder test if MW succeeds.

---

## 5. Timeline

| Week | Action | Gate | Effort |
|------|--------|------|--------|
| W1 (days 1-2) | **Action 1:** Confirmation battery (D1+D4+D5+D7) | All confirm H2 | 0.5 GPU-hr, 1 person-hr |
| W1 (days 1-2) | **Action 2:** Loss-curve diagnostic | Losses indistinguishable | 0.25 GPU-hr |
| W1 (days 2-3) | kinchembio's state classifier on Morgan FPs | Accuracy ~33% | 2 hr CPU |
| W1 (day 3) | condgen's MW-tercile positive control (retrain VAE with MW labels) | MW probe accuracy >70% | 3 GPU-hr |
| W1 (day 4) | **Go/No-Go Gate 1:** If all confirm H2 AND MW control works -> proceed to data fix | | |
| W2-3 | Fix labels via KLIFS/KinCoRe annotation (kinchembio leads) | >60% of compounds annotated | 2 person-weeks |
| W3 | Retrain VAE with fixed labels + **Action 3 Checkpoint A** monitoring | Per-state loss diverges | 4 GPU-hr |
| W3 | **Action 3 Checkpoint B:** Post-training diagnostics | D1 >55%, D4 <70% identity | 1 GPU-hr |
| W3-4 | **Go/No-Go Gate 2:** If Checkpoint B passes -> evaluate thesis. If fails -> architecture fix | | |
| W4 (if needed) | Remove shortcut (Checkpoint C option 1) + retrain | D1 improves >10pp | 6 GPU-hr |
| W4-5 | Multi-pocket docking evaluation (evaldes leads) + **Checkpoint D** | Multi-pocket d > 0.3 | 8 GPU-hr |

**Total compute through Gate 1:** ~4 GPU-hours, 1-2 days.
**Total compute through Gate 2:** ~12 GPU-hours, 3 weeks.
**Total compute through full recovery:** ~20 GPU-hours, 5 weeks.

---

## 6. Key Risks and Contingencies

### Risk 1: Confirmation battery contradicts H2

**Probability:** 5-10%. **Signal:** D1 accuracy > 50%.

**Contingency:** The 55 curated compounds may dominate the latent space despite
being 0.5% of the data. Check whether the probing classifier's accuracy is driven
entirely by these 55 compounds (remove them from the validation set and re-probe).

### Risk 2: MW-tercile control fails

**Probability:** 10-15%. **Signal:** MW probe accuracy < 50%.

**Contingency:** The architecture itself is broken, not just the data. Escalate
directly to FiLM/adaLN-Zero before fixing labels. No point in fixing data for an
architecture that cannot condition on anything.

### Risk 3: Labels fixed but model still shows no conditioning

**Probability:** 25-30%. **Signal:** Checkpoint B fails (D1 < 45%).

**Contingency:** This confirms the information shortcut is active. Apply Checkpoint C
option 1 (remove shortcut) and retrain. If still fails, the chemical space truly
lacks state-specific structure for EGFR, and the ABL1 pivot becomes necessary.

### Risk 4: EGFR labels cannot be fixed adequately

**Probability:** 30-40%. **Signal:** KLIFS/KinCoRe annotation covers <40% of compounds.

**Contingency:** Switch to ABL1 (kinchembio's recommendation). ABL1 has genuine
type I/type II distinction with published crystal structures for both. Timeline cost:
+4-6 weeks.

---

## 7. Summary

The diagnostic question has fundamentally shifted. We are no longer asking "where does
the conditioning signal die?" -- we know it was never alive because the labels are
random noise. The three actions proposed here form a cascade:

1. **Confirm** the diagnosis empirically (0.5 days, 4 diagnostics)
2. **Validate** the confirmation via an independent channel (loss curves, 0.25 days)
3. **Monitor** the recovery (multi-checkpoint protocol for when labels are fixed)

The most important single experiment is the MW-tercile positive control (condgen's
proposal). If MW conditioning works with the current architecture, the mechanism is
functional and the recovery path is clear: fix the data, retrain, evaluate with
multi-pocket docking. If MW conditioning also fails, the architecture needs
replacement before data fixing can even be tested.

Every diagnostic is designed to produce a binary go/no-go gate. There are no
ambiguous outcomes. At each gate, the next action is determined by the result,
not by judgment calls. This is by design: the project needs FAST ANSWERS, not
exploratory science.
