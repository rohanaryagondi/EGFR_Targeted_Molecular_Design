---
agent: ML Diagnostics Expert
round: 1
date: 2026-04-14
type: research-note
---

# ML Diagnostics Investigation Report: Where Does the Conditioning Signal Die?

## 1. Executive Summary

The StateBind Transformer VAE generates pharmacologically relevant EGFR molecules
(EF@10 = 5-8, drug scaffold recovery, 64/64 active latent dimensions) but state
conditioning provides zero measurable benefit (Cohen's d = 0.059). This report
designs a complete diagnostic battery of 7 experiments -- all executable on existing
checkpoints in under 1 GPU-hour total -- that can definitively localize WHERE the
conditioning signal is lost and distinguish between the three hypotheses (H1:
architecture, H2: data, H3: evaluation).

**Key architectural observation:** The model has a fundamental information-routing
asymmetry. State information enters the encoder at every timestep (concatenated to
embeddings) AND enters the decoder via prefix tokens projected from [z; state_onehot].
Yet centroid distances are only 6-10% of the latent space scale. This immediately
suggests the encoder is DISCARDING the state signal rather than encoding it -- which
is exactly what we would expect when the state labels carry minimal information about
molecular structure (H2) OR when the encoder has learned that discarding state is
optimal because the decoder receives it anyway via direct concatenation (an
information shortcut problem).

**Primary diagnostic recommendation:** Run the Probing Classifier (Diagnostic 1)
first. Its result determines the entire branching path of the investigation. If a
linear probe cannot predict state from z, the signal dies in the encoder. If it can,
the signal dies in the decoder or evaluation. This single experiment costs ~5 minutes
and resolves the top-level branch of the diagnostic tree.

---

## 2. Architectural Analysis: Where Conditioning Is Injected

Before designing diagnostics, we must precisely map the conditioning signal flow
through the model. From the source code (`transformer_vae.py` and `vae.py`):

### 2.1 Encoder Path

```
Input: SMILES tokens (batch, seq_len)
       + state_onehot (batch, n_states=3)

SMILESEncoder.forward():
  embedded = Embedding(x)               # (batch, seq_len, embed_dim=128)
  state_expanded = state_onehot.unsqueeze(1).expand(-1, seq_len, -1)
                                         # (batch, seq_len, 3)
  gru_input = cat([embedded, state_expanded], dim=-1)
                                         # (batch, seq_len, 131)
  _, hidden = GRU(gru_input)             # bidirectional, 2 layers
  hidden_cat = cat([hidden[-2], hidden[-1]], dim=-1)
                                         # (batch, 512)
  mu = fc_mu(hidden_cat)                 # (batch, 64)
  logvar = fc_logvar(hidden_cat)         # (batch, 64)
```

**Key:** State is concatenated at input. The 3-dim one-hot is appended to a 128-dim
embedding, making it only 2.3% of the encoder input dimensionality per timestep.
The GRU processes this through 2 bidirectional layers (hidden_dim=256 per direction).
The state information must survive through all GRU timesteps and be captured in the
final hidden state to influence mu/logvar.

### 2.2 Latent Sampling

```
z = mu + eps * exp(0.5 * logvar)   # during training
z = mu                              # during eval (deterministic)
```

Latent dim = 64. All 64 dimensions active (KL > 0.01/dim). Total KL ~14.1/sample.
Mean mu norm ~4.3. State centroid distances 0.26-0.42 (6-10% of mu norm).

### 2.3 Decoder Path (Transformer)

```
TransformerSMILESDecoder.forward():
  z_state = cat([z, state_onehot], dim=-1)  # (batch, 67)
  prefix = z_proj(z_state)                   # Linear(67, 8*256) -> (batch, 2048)
  prefix = prefix.view(batch, 8, 256)        # 8 prefix tokens of dim 256

  embedded = Embedding(target)               # (batch, seq_len, 256)
  embedded = pos_encoding(embedded)          # + sinusoidal PE
  combined = cat([prefix, embedded], dim=1)  # (batch, 8+seq_len, 256)

  # Causal mask: all positions can attend to prefix tokens
  # Sequence positions: standard causal masking
  output = Transformer(combined, mask=attn_mask)
  seq_output = output[:, 8:, :]              # skip prefix positions
  logits = output_proj(seq_output)           # (batch, seq_len, vocab_size)
```

**Key:** The decoder receives state through TWO channels:
1. Indirectly via z (which may or may not encode state)
2. Directly via [z; state_onehot] -> prefix projection

This means even if the encoder perfectly discards state from z, the decoder still
has access to state_onehot through the prefix projection. The z_proj linear layer
maps from (64 + 3) = 67 dimensions to 2048 dimensions (8 x 256). The 3 state dims
are 4.5% of the input to this projection.

### 2.4 Critical Observation: The Information Shortcut

The decoder's z_proj receives `[z; state_onehot]` directly. This means:

- The encoder has NO incentive to encode state into z, because the decoder receives
  state directly via concatenation to z before prefix projection.
- This is a well-known failure mode in conditional VAEs: when the decoder has direct
  access to the conditioning variable, the encoder learns to ignore it, and the
  latent code z becomes condition-independent (Sohn et al., 2015; Nguyen et al.,
  2023).
- The free-bits mechanism (0.25/dim) forces the encoder to use z for SOMETHING, but
  that something is molecular structure, not state. State information is redundant
  in z because it arrives at the decoder through a separate channel.

This shortcut is architecturally identical to the "posterior collapse of conditioning"
phenomenon analyzed by Nguyen et al. (2023): in conditional VAEs, when both the
encoder and decoder receive the condition, the encoder can learn to make q(z|x,c)
independent of c, while the decoder uses c directly. This is not a bug -- it is the
optimal information-theoretic solution when c contributes little to reconstructing x.

---

## 3. The Diagnostic Decision Tree

Before designing experiments, here is the complete diagnostic tree. Each branch
terminates in a hypothesis assignment:

```
D1: Can a linear probe predict state from z?
|
+-- Accuracy ~33% (chance) --> STATE NOT IN z
|   |
|   D2: Can a linear probe predict state from encoder hidden states
|       (before mu/logvar projection)?
|   |
|   +-- Accuracy ~33% --> STATE NOT IN ENCODER
|   |   |
|   |   Conclusion: Encoder discards state at input
|   |   --> H2 (state labels uninformative) OR
|   |       architectural shortcut (state redundant in encoder
|   |       because decoder gets it directly)
|   |
|   +-- Accuracy >50% --> STATE IN ENCODER, LOST AT BOTTLENECK
|       |
|       Conclusion: mu/logvar projection discards state
|       --> H1 (bottleneck too narrow for state)
|       Action: Increase latent_dim or add state-specific dims
|
+-- Accuracy >60% --> STATE IS IN z
    |
    D3: Average attention weight on prefix tokens per layer?
    |
    +-- Attention to prefix < 5% of total --> DECODER IGNORES PREFIX
    |   |
    |   Conclusion: Transformer routes around prefix tokens
    |   --> H1 (prefix mechanism too weak)
    |   Action: Replace with cross-attention or FiLM
    |
    +-- Attention to prefix > 10% --> DECODER USES PREFIX
        |
        D4: State-swap experiment changes output?
        |
        +-- Output identical across states --> STATE IN z BUT UNUSED
        |   |
        |   Conclusion: Prefix tokens carry z info, not state info
        |   --> H1 (state signal drowned by z)
        |
        +-- Output differs across states --> CONDITIONING WORKS
            |
            Conclusion: Model generates state-specific molecules
            --> H3 (evaluation metric blind to state-specific quality)
            Action: State-specific docking evaluation
```

---

## 4. The Diagnostic Battery: 7 Experiments

### Diagnostic 1: Probing Classifier on Latent z (HIGHEST PRIORITY)

**Purpose:** Determine whether the latent code z encodes state information.
This is the root node of the entire diagnostic tree.

**Method:** Train a logistic regression (linear probe) to predict the 3-class
state label from the latent mean vector mu. Use the validation set. If accuracy
is near chance (33%), state is not encoded. If accuracy exceeds 60%, state IS
encoded and the problem is downstream.

**Why a linear probe:** Following Alain & Bengio (2017) and Belinkov (2022),
linear probes test whether information is linearly accessible in the
representation. A nonlinear probe (MLP) would have higher accuracy but could
extract information that is not functionally used by the model. The linear
constraint ensures we measure what the model can straightforwardly access.

**Expected results under each hypothesis:**

| Hypothesis | Expected Accuracy | Reasoning |
|-----------|------------------|-----------|
| H1 (weak arch) | 35-50% | State partially encoded but not enough for decoder to use |
| H2 (bad data) | 33-40% | State labels uninformative -> nothing to encode |
| H3 (wrong metric) | 50-80% | Model encodes state well but evaluation misses it |

**Implementation:**

```python
import torch
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score

def diagnostic_1_probing_classifier(model, dataloader, device='cuda'):
    """Probe whether state is encoded in latent z.

    Returns:
        dict with accuracy, per-class accuracy, cross-val scores
    """
    model.eval()
    all_mu = []
    all_states = []

    with torch.no_grad():
        for batch in dataloader:
            x = batch['tokens'].to(device)
            lengths = batch['lengths'].to(device)
            state_onehot = batch['state_onehot'].to(device)
            state_idx = batch['state_idx']  # integer labels

            mu, logvar = model.encode(x, lengths, state_onehot)
            all_mu.append(mu.cpu().numpy())
            all_states.append(state_idx.numpy())

    mu_array = np.concatenate(all_mu, axis=0)      # (N, 64)
    state_array = np.concatenate(all_states, axis=0)  # (N,)

    # Linear probe with 5-fold cross-validation
    clf = LogisticRegression(max_iter=1000, multi_class='multinomial')
    cv_scores = cross_val_score(clf, mu_array, state_array, cv=5)

    # Full fit for per-class report
    clf.fit(mu_array, state_array)
    preds = clf.predict(mu_array)

    return {
        'cv_accuracy_mean': float(np.mean(cv_scores)),
        'cv_accuracy_std': float(np.std(cv_scores)),
        'per_class_report': classification_report(state_array, preds),
        'chance_level': 1.0 / len(np.unique(state_array)),
        'n_samples': len(state_array),
        'probe_coefficients_norm': float(np.linalg.norm(clf.coef_)),
    }
```

**Compute cost:** ~2-5 minutes per checkpoint (encode val set + sklearn fit).
For 10 conditioned checkpoints: ~30-50 minutes total.

**Decision:** If accuracy <= 40%, proceed to D2 (encoder hidden probe). If
accuracy >= 50%, skip to D3 (attention analysis).

---

### Diagnostic 2: Encoder Hidden State Probe

**Purpose:** If D1 shows state is NOT in z, determine whether the encoder
captures state at all before the mu/logvar bottleneck. This distinguishes
"encoder never captures state" (supports H2) from "encoder captures state but
bottleneck discards it" (supports H1).

**Method:** Extract the final hidden states from the GRU encoder BEFORE the
fc_mu/fc_logvar projections. Train a linear probe on this 512-dim vector to
predict state.

**Expected results:**

| Hypothesis | D1 Accuracy | D2 Accuracy | Interpretation |
|-----------|-------------|-------------|----------------|
| H2 | ~33% | ~33% | State never enters encoder meaningfully |
| H1 | ~33% | >50% | Encoder captures state but bottleneck loses it |
| Shortcut | ~33% | ~33-40% | Encoder ignores state because decoder gets it directly |

**Implementation:**

```python
def diagnostic_2_encoder_hidden_probe(model, dataloader, device='cuda'):
    """Probe whether state is encoded in GRU hidden states (pre-bottleneck).

    Requires hooking into the encoder to extract hidden states before
    fc_mu/fc_logvar projection.
    """
    model.eval()
    all_hidden = []
    all_states = []

    def hook_fn(module, input, output):
        # GRU output: (output_seq, hidden_state)
        # hidden_state: (n_layers*2, batch, hidden_dim)
        hidden = output[1]
        # Take final layer, both directions
        hidden_cat = torch.cat([hidden[-2], hidden[-1]], dim=-1)
        all_hidden.append(hidden_cat.detach().cpu().numpy())

    hook = model.encoder.gru.register_forward_hook(hook_fn)

    with torch.no_grad():
        for batch in dataloader:
            x = batch['tokens'].to(device)
            lengths = batch['lengths'].to(device)
            state_onehot = batch['state_onehot'].to(device)
            state_idx = batch['state_idx']
            all_states.append(state_idx.numpy())

            _ = model.encode(x, lengths, state_onehot)

    hook.remove()

    hidden_array = np.concatenate(all_hidden, axis=0)  # (N, 512)
    state_array = np.concatenate(all_states, axis=0)

    clf = LogisticRegression(max_iter=1000, multi_class='multinomial')
    cv_scores = cross_val_score(clf, hidden_array, state_array, cv=5)

    return {
        'hidden_dim': hidden_array.shape[1],
        'cv_accuracy_mean': float(np.mean(cv_scores)),
        'cv_accuracy_std': float(np.std(cv_scores)),
        'chance_level': 1.0 / len(np.unique(state_array)),
    }
```

**Compute cost:** Same as D1 (~2-5 minutes per checkpoint).

---

### Diagnostic 3: Prefix Token Attention Analysis

**Purpose:** Quantify how much attention the decoder pays to the 8 prefix
tokens (which carry the [z; state] signal) versus the sequence tokens. If the
decoder learns to ignore prefix tokens, the conditioning signal cannot
propagate regardless of how much state information the prefix contains.

**Method:** Extract attention weights from all 4 Transformer layers, all 4
heads. Compute the average attention weight assigned to prefix token positions
(positions 0-7) by sequence token positions (positions 8+).

**Connection to attention sink literature:** Recent work on attention sinks in
Transformers (Xiao et al., 2024; Gu et al., 2025) shows that prefix/initial
tokens often become attention sinks -- receiving high attention weight but
contributing little semantic information. The "sink" mechanism implements a
"no-op" channel that reduces unnecessary information mixing. If our prefix
tokens are functioning as sinks rather than information carriers, the attention
weights will be high but the VALUE vectors at prefix positions will have low
norms (the signature of attention sink behavior).

**Expected results:**

| Hypothesis | Mean Prefix Attention | Value Norm at Prefix | Interpretation |
|-----------|----------------------|---------------------|----------------|
| H1 (weak arch) | <5% per head | Any | Decoder bypasses prefix entirely |
| H1 (sink) | >15% per head | Low (< mean) | Prefix tokens are attention sinks, not info carriers |
| H3 (works) | 8-20% per head | Normal-High | Decoder genuinely uses prefix information |

**Threshold derivation:** With 8 prefix tokens and typical sequence lengths of
~50-80 tokens, uniform attention would give prefix tokens ~10-14% of total
attention weight. Significantly below this (< 5%) indicates active avoidance.
Significantly above (> 20%) with low value norms indicates sink behavior.

**Implementation:**

```python
def diagnostic_3_prefix_attention(model, dataloader, device='cuda',
                                   n_batches=20):
    """Analyze attention patterns on prefix tokens across layers and heads.

    Requires extracting attention weights from TransformerEncoderLayer.
    PyTorch's TransformerEncoder does not return attention weights by default,
    so we need to use hooks or modify the forward pass.
    """
    model.eval()
    n_layers = model.decoder.config.n_decoder_layers  # 4
    n_heads = model.decoder.config.n_heads             # 4
    n_prefix = model.decoder.config.n_prefix_tokens    # 8

    # Storage for attention weights per layer
    layer_attentions = {i: [] for i in range(n_layers)}

    # Register hooks on MultiheadAttention modules
    hooks = []
    for i, layer in enumerate(model.decoder.transformer.layers):
        def make_hook(layer_idx):
            def hook_fn(module, args, output):
                # MultiheadAttention returns (attn_output, attn_weights)
                # attn_weights shape: (batch, n_heads, tgt_len, src_len)
                # NOTE: need_weights must be True (default in PyTorch)
                if isinstance(output, tuple) and len(output) >= 2:
                    attn_weights = output[1]
                    if attn_weights is not None:
                        layer_attentions[layer_idx].append(
                            attn_weights.detach().cpu()
                        )
            return hook_fn
        hook = layer.self_attn.register_forward_hook(make_hook(i))
        hooks.append(hook)

    with torch.no_grad():
        for batch_idx, batch in enumerate(dataloader):
            if batch_idx >= n_batches:
                break
            x = batch['tokens'].to(device)
            lengths = batch['lengths'].to(device)
            state_onehot = batch['state_onehot'].to(device)
            _ = model(x, lengths, state_onehot)

    for hook in hooks:
        hook.remove()

    # Analyze attention to prefix positions
    results = {}
    for layer_idx in range(n_layers):
        attn_list = layer_attentions[layer_idx]
        if not attn_list:
            continue
        # Concatenate across batches: (total_samples, n_heads, total_len, total_len)
        all_attn = torch.cat(attn_list, dim=0)

        # Extract attention FROM sequence positions TO prefix positions
        # seq_to_prefix: attention weights from positions [n_prefix:] to [0:n_prefix]
        seq_to_prefix = all_attn[:, :, n_prefix:, :n_prefix]  # (..., seq_len, n_prefix)
        seq_to_seq = all_attn[:, :, n_prefix:, n_prefix:]     # (..., seq_len, seq_len)

        # Mean attention to prefix per head
        mean_prefix_attn = seq_to_prefix.sum(dim=-1).mean(dim=(0, 2))  # (n_heads,)
        # This gives the fraction of total attention going to prefix

        results[f'layer_{layer_idx}'] = {
            'mean_prefix_attention_per_head': mean_prefix_attn.tolist(),
            'mean_prefix_attention_overall': float(mean_prefix_attn.mean()),
        }

    return results
```

**Compute cost:** ~5-10 minutes per checkpoint (need to enable attention weight
output, may require modifying TransformerEncoder forward to pass
`need_weights=True`).

**Important implementation note:** PyTorch's `nn.TransformerEncoder` does not
return attention weights by default. To extract them, either:
(a) Use hooks on the `MultiheadAttention` submodules within each layer, OR
(b) Temporarily set `layer.self_attn.need_weights = True` before forward.
Option (b) is simpler but may change behavior due to dropout. Option (a) is
safer for diagnostic purposes.

---

### Diagnostic 4: State-Swap Experiment

**Purpose:** The definitive test of whether conditioning actually changes
generation output. Encode a molecule with one state, then decode it with ALL
three states. If the outputs are identical, conditioning is dead. If they
differ, conditioning works but the evaluation may not see it (H3).

**Method:** For each molecule in a sample of the validation set:
1. Encode with its true state to get mu.
2. Decode (greedy, T=0) with state=[1,0,0], [0,1,0], [0,0,1].
3. Compare: (a) Are the decoded SMILES identical? (b) If different, compute
   Tanimoto between the three outputs.

**Expected results:**

| Hypothesis | % Identical Across States | Mean Tanimoto Between States |
|-----------|--------------------------|------------------------------|
| H1 (dead conditioning) | >95% | >0.95 |
| H2 (uninformative data) | >90% | >0.90 |
| H3 (evaluation blind) | <70% | 0.5-0.8 |

**Implementation:**

```python
def diagnostic_4_state_swap(model, dataloader, vocab, device='cuda',
                             n_samples=200, max_len=128):
    """State-swap experiment: decode same z with different state labels.

    For each molecule, encode to mu, then decode with each state.
    Compare outputs across states.
    """
    model.eval()
    n_states = model.config.n_states

    results = {
        'n_samples': 0,
        'n_all_identical': 0,
        'n_at_least_one_different': 0,
        'pairwise_tanimoto': [],
        'per_state_smiles': [],
    }

    sample_count = 0
    with torch.no_grad():
        for batch in dataloader:
            if sample_count >= n_samples:
                break

            x = batch['tokens'].to(device)
            lengths = batch['lengths'].to(device)
            state_onehot = batch['state_onehot'].to(device)

            mu, logvar = model.encode(x, lengths, state_onehot)

            for i in range(min(x.shape[0], n_samples - sample_count)):
                z_i = mu[i:i+1]  # (1, 64)
                decoded_smiles = []

                for state_idx in range(n_states):
                    state_oh = torch.zeros(1, n_states, device=device)
                    state_oh[0, state_idx] = 1.0

                    token_sequences = model.generate(
                        z_i, state_oh, max_len=max_len,
                        temperature=0.0, vocab=vocab  # greedy
                    )
                    smiles = vocab.decode(token_sequences[0])
                    decoded_smiles.append(smiles)

                # Check if all identical
                all_same = len(set(decoded_smiles)) == 1
                results['n_all_identical'] += int(all_same)
                results['n_at_least_one_different'] += int(not all_same)
                results['per_state_smiles'].append(decoded_smiles)

                # Compute pairwise Tanimoto (if RDKit available)
                try:
                    from rdkit import Chem
                    from rdkit.Chem import AllChem
                    from rdkit import DataStructs

                    fps = []
                    for smi in decoded_smiles:
                        mol = Chem.MolFromSmiles(smi)
                        if mol:
                            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
                            fps.append(fp)
                        else:
                            fps.append(None)

                    for a in range(len(fps)):
                        for b in range(a+1, len(fps)):
                            if fps[a] is not None and fps[b] is not None:
                                tan = DataStructs.TanimotoSimilarity(fps[a], fps[b])
                                results['pairwise_tanimoto'].append(float(tan))
                except ImportError:
                    pass

                sample_count += 1

    results['n_samples'] = sample_count
    results['pct_all_identical'] = (
        results['n_all_identical'] / max(sample_count, 1) * 100
    )
    if results['pairwise_tanimoto']:
        results['mean_pairwise_tanimoto'] = float(
            np.mean(results['pairwise_tanimoto'])
        )
    return results
```

**Compute cost:** ~10-15 minutes per checkpoint (200 molecules x 3 states x
autoregressive decoding).

**Critical control:** Also run this on an UNCONDITIONED checkpoint. The
unconditioned model should show near-identical outputs across state labels
(since state was not used in training). Any difference in the conditioned model
above the unconditioned baseline is evidence that conditioning has some effect.

---

### Diagnostic 5: Per-State Scaffold Overlap Analysis

**Purpose:** Measure whether the model generates different Bemis-Murcko
scaffolds for different conditioning states. High overlap (>90%) supports H2
(same chemistry regardless of state) or dead conditioning. Low overlap (<60%)
supports H3 (model differentiates but evaluation misses it).

**Method:** Generate 500 molecules per state (using greedy decoding from
conditioned checkpoints). Extract Bemis-Murcko scaffolds. Compute the Jaccard
overlap between state-pair scaffold sets.

**Expected results:**

| Hypothesis | Mean Jaccard Overlap | Unique Scaffolds per State |
|-----------|---------------------|---------------------------|
| H1 (dead conditioning) | >0.85 | ~equal across states |
| H2 (uninformative data) | >0.80 | ~equal, reflects training distribution |
| H3 (evaluation blind) | <0.60 | significantly different per state |

**Also compare with training data:** Extract Bemis-Murcko scaffolds from the
8,109 training molecules grouped by state. If training data itself shows >90%
scaffold overlap across states, then H2 is strongly supported -- the model
cannot learn state-specific chemistry because the training data does not
contain state-specific chemistry.

**Implementation:**

```python
def diagnostic_5_scaffold_overlap(generated_smiles_by_state, training_data=None):
    """Compute Bemis-Murcko scaffold overlap between states.

    Args:
        generated_smiles_by_state: dict mapping state_name -> list of SMILES
        training_data: optional dict mapping state_name -> list of SMILES
            for comparison with training set overlap

    Returns:
        dict with Jaccard overlap, unique scaffold counts, shared scaffold counts
    """
    from rdkit import Chem
    from rdkit.Chem.Scaffolds.MurckoScaffold import (
        GetScaffoldForMol, MakeScaffoldGeneric
    )

    def extract_scaffolds(smiles_list):
        scaffolds = set()
        for smi in smiles_list:
            mol = Chem.MolFromSmiles(smi)
            if mol:
                try:
                    scaffold = GetScaffoldForMol(mol)
                    generic = MakeScaffoldGeneric(scaffold)
                    scaffolds.add(Chem.MolToSmiles(generic))
                except Exception:
                    pass
        return scaffolds

    states = list(generated_smiles_by_state.keys())
    scaffold_sets = {
        state: extract_scaffolds(smiles)
        for state, smiles in generated_smiles_by_state.items()
    }

    # Pairwise Jaccard overlap
    overlaps = {}
    for i, s1 in enumerate(states):
        for j, s2 in enumerate(states):
            if j <= i:
                continue
            intersection = scaffold_sets[s1] & scaffold_sets[s2]
            union = scaffold_sets[s1] | scaffold_sets[s2]
            jaccard = len(intersection) / max(len(union), 1)
            overlaps[f'{s1}_vs_{s2}'] = {
                'jaccard': round(jaccard, 4),
                'n_shared': len(intersection),
                'n_union': len(union),
                'n_s1_only': len(scaffold_sets[s1] - scaffold_sets[s2]),
                'n_s2_only': len(scaffold_sets[s2] - scaffold_sets[s1]),
            }

    # Per-state scaffold counts
    counts = {state: len(scaffs) for state, scaffs in scaffold_sets.items()}

    # All-state overlap (scaffolds in ALL states)
    if len(states) >= 2:
        universal = scaffold_sets[states[0]]
        for state in states[1:]:
            universal = universal & scaffold_sets[state]
        all_state_overlap_pct = len(universal) / max(
            max(len(s) for s in scaffold_sets.values()), 1
        ) * 100
    else:
        all_state_overlap_pct = 100.0

    result = {
        'pairwise_overlaps': overlaps,
        'per_state_scaffold_counts': counts,
        'universal_scaffold_count': len(universal) if len(states) >= 2 else 0,
        'universal_overlap_pct': round(all_state_overlap_pct, 2),
    }

    # Training data comparison
    if training_data:
        train_scaffolds = {
            state: extract_scaffolds(smiles)
            for state, smiles in training_data.items()
        }
        train_overlaps = {}
        for i, s1 in enumerate(states):
            for j, s2 in enumerate(states):
                if j <= i:
                    continue
                if s1 in train_scaffolds and s2 in train_scaffolds:
                    inter = train_scaffolds[s1] & train_scaffolds[s2]
                    union = train_scaffolds[s1] | train_scaffolds[s2]
                    train_overlaps[f'{s1}_vs_{s2}'] = round(
                        len(inter) / max(len(union), 1), 4
                    )
        result['training_data_scaffold_overlap'] = train_overlaps

    return result
```

**Compute cost:** ~5 minutes (generation already done in ablation, just need
scaffold extraction).

**Critical baseline:** The TRAINING DATA scaffold overlap between states is the
upper bound on what the model could ever learn. If the training data itself has
>90% scaffold overlap between DFGin_aCin and DFGin_aCout, then H2 is confirmed
and no architecture change can help.

---

### Diagnostic 6: Per-Dimension KL Analysis with State Conditioning

**Purpose:** Identify which latent dimensions encode state-related information.
If conditioning matters, some dimensions should have significantly different
KL divergence patterns between states. This goes beyond the aggregate "all 64
dims active" metric to look at state-conditional behavior.

**Method:** For each state, compute the distribution of per-dimension KL values.
Test whether any dimensions show state-dependent KL patterns using
Kruskal-Wallis tests. Also compute the per-dimension mu and sigma separately
for each state and identify dimensions with the largest between-state variance
in mu.

**Expected results:**

| Hypothesis | Dims with Significant State Effect | Between-State mu Variance |
|-----------|-----------------------------------|--------------------------|
| H1 (weak arch) | 0-3 dims | Low (< 0.1 per dim) |
| H2 (uninformative data) | 0-1 dims | Very low (< 0.05) |
| H3 (evaluation blind) | 5-15 dims | Moderate (0.1-0.5 per dim) |

**Implementation:**

```python
def diagnostic_6_per_dim_kl_analysis(model, dataloader, device='cuda'):
    """Analyze per-dimension KL divergence conditioned on state.

    Identifies dimensions that encode state-specific information.
    """
    from scipy import stats

    model.eval()
    state_mus = {0: [], 1: [], 2: []}      # per-state mu values
    state_logvars = {0: [], 1: [], 2: []}   # per-state logvar values

    with torch.no_grad():
        for batch in dataloader:
            x = batch['tokens'].to(device)
            lengths = batch['lengths'].to(device)
            state_onehot = batch['state_onehot'].to(device)
            state_idx = batch['state_idx'].numpy()

            mu, logvar = model.encode(x, lengths, state_onehot)
            mu_np = mu.cpu().numpy()
            logvar_np = logvar.cpu().numpy()

            for s in [0, 1, 2]:
                mask = state_idx == s
                if mask.sum() > 0:
                    state_mus[s].append(mu_np[mask])
                    state_logvars[s].append(logvar_np[mask])

    # Concatenate per state
    for s in [0, 1, 2]:
        state_mus[s] = np.concatenate(state_mus[s], axis=0)
        state_logvars[s] = np.concatenate(state_logvars[s], axis=0)

    latent_dim = state_mus[0].shape[1]
    results = {
        'per_dim_state_anova': [],
        'per_dim_between_state_mu_variance': [],
        'significant_dims_count': 0,
        'top_state_encoding_dims': [],
    }

    for d in range(latent_dim):
        # Kruskal-Wallis test across states for dimension d
        groups = [state_mus[s][:, d] for s in [0, 1, 2]]
        stat, p_value = stats.kruskal(*groups)

        # Between-state variance in mean mu for dimension d
        state_means = [state_mus[s][:, d].mean() for s in [0, 1, 2]]
        between_var = float(np.var(state_means))

        results['per_dim_state_anova'].append({
            'dim': d,
            'kruskal_stat': float(stat),
            'p_value': float(p_value),
            'state_means': [float(m) for m in state_means],
            'between_state_variance': between_var,
        })
        results['per_dim_between_state_mu_variance'].append(between_var)

    # Count significant dimensions (Bonferroni-corrected)
    alpha = 0.05 / latent_dim
    sig_count = sum(
        1 for d in results['per_dim_state_anova'] if d['p_value'] < alpha
    )
    results['significant_dims_count'] = sig_count
    results['bonferroni_alpha'] = alpha

    # Top 10 dimensions by between-state variance
    sorted_dims = sorted(
        results['per_dim_state_anova'],
        key=lambda x: x['between_state_variance'],
        reverse=True
    )[:10]
    results['top_state_encoding_dims'] = sorted_dims

    return results
```

**Compute cost:** ~2-5 minutes per checkpoint (same as D1, just different
analysis of the same mu/logvar data).

---

### Diagnostic 7: Mutual Information Estimation I(z; state)

**Purpose:** Directly estimate the mutual information between the latent code z
and the state label. This provides a single scalar quantifying how much
information about state is contained in z. Unlike the probing classifier (D1),
MI is independent of the probe's capacity and provides a bits/nats measure.

**Method:** Use the MINE (Mutual Information Neural Estimation) framework
(Belghazi et al., 2018) to estimate I(z; state). MINE trains a statistics
network T(z, state) to maximize a lower bound on MI. For our 3-class discrete
state variable, we can also use a simpler estimator: the classifier-based MI
lower bound (Poole et al., 2019), where I(z; state) >= H(state) - H(state|z),
and H(state|z) is estimated from the cross-entropy of the probing classifier
from D1.

**Expected results:**

| Hypothesis | I(z; state) nats | I(z; state) / H(state) | Interpretation |
|-----------|-----------------|------------------------|----------------|
| H1 | 0.05-0.3 | 5-25% | Some state info, not enough |
| H2 | <0.05 | <5% | Almost no state info in z |
| H3 | 0.3-0.8 | 25-75% | Substantial state info |

**Baseline:** H(state) for a 3-class uniform distribution = ln(3) = 1.099 nats.
If the state distribution is imbalanced (which it likely is for EGFR -- DFGin_aCin
dominates), H(state) will be lower.

**Implementation:**

```python
def diagnostic_7_mutual_information(model, dataloader, device='cuda'):
    """Estimate mutual information I(z; state) using classifier-based bound.

    Uses the result of the probing classifier to compute:
    I(z; state) >= H(state) - CE(state|z)

    where CE is the cross-entropy of the trained classifier.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict

    model.eval()
    all_mu = []
    all_states = []

    with torch.no_grad():
        for batch in dataloader:
            x = batch['tokens'].to(device)
            lengths = batch['lengths'].to(device)
            state_onehot = batch['state_onehot'].to(device)
            state_idx = batch['state_idx']

            mu, _ = model.encode(x, lengths, state_onehot)
            all_mu.append(mu.cpu().numpy())
            all_states.append(state_idx.numpy())

    mu_array = np.concatenate(all_mu, axis=0)
    state_array = np.concatenate(all_states, axis=0)

    # Empirical H(state)
    state_counts = np.bincount(state_array)
    state_probs = state_counts / state_counts.sum()
    H_state = -np.sum(state_probs * np.log(state_probs + 1e-10))

    # Cross-entropy of classifier = H(state|z) upper bound
    clf = LogisticRegression(max_iter=1000, multi_class='multinomial')
    # Cross-validated predictions for unbiased estimate
    cv_probs = cross_val_predict(
        clf, mu_array, state_array, cv=5, method='predict_proba'
    )

    # Cross-entropy: -mean(log(p(true_class|z)))
    true_probs = cv_probs[np.arange(len(state_array)), state_array]
    CE_state_given_z = -np.mean(np.log(true_probs + 1e-10))

    # MI lower bound
    MI_lower_bound = max(0, H_state - CE_state_given_z)

    return {
        'H_state_nats': float(H_state),
        'H_state_bits': float(H_state / np.log(2)),
        'CE_state_given_z': float(CE_state_given_z),
        'MI_lower_bound_nats': float(MI_lower_bound),
        'MI_lower_bound_bits': float(MI_lower_bound / np.log(2)),
        'MI_over_H_state_pct': float(MI_lower_bound / H_state * 100),
        'state_distribution': state_probs.tolist(),
        'n_samples': len(state_array),
    }
```

**Compute cost:** Same as D1 (~5 minutes, reuses probe infrastructure).

---

## 5. Disentanglement Metrics Assessment

### 5.1 Applicability to This Problem

Standard disentanglement metrics (beta-VAE metric, DCI, SAP) were designed for
settings with multiple independent generative factors (e.g., dSprites with shape,
scale, rotation, position). Our setting has a single discrete factor (state) and
the question is whether it is encoded at all, not whether it is disentangled from
other factors.

However, a modified DCI analysis is informative:

**DCI (Disentanglement, Completeness, Informativeness)** (Eastwood & Williams, 2018):
- **Informativeness:** Can latent dims predict state? (equivalent to D1)
- **Disentanglement:** Is state encoded in a few dims or spread across many?
- **Completeness:** Is each dim used for only one factor?

Since we have only one discrete factor (state) and one continuous "factor"
(molecular identity), DCI reduces to: how many latent dims encode state (D6
answers this), and how predictive are they (D1/D7 answers this).

**MIG (Mutual Information Gap)** (Chen et al., 2018): The gap between the
highest and second-highest MI between latent dims and factors. With only one
factor, MIG is not applicable.

**SAP (Separated Attribute Predictability)** (Kumar et al., 2018): The
difference in accuracy between the two most predictive latent dimensions for
each factor. We can compute this as a refinement of D6: which single latent
dimension best predicts state?

### 5.2 Expected Disentanglement Under Each Hypothesis

| Metric | H1 (weak arch) | H2 (bad data) | H3 (works) |
|--------|----------------|---------------|------------|
| DCI-Informativeness | Low (0.0-0.2) | Very low (0.0-0.1) | Moderate (0.2-0.5) |
| DCI-Disentanglement | N/A (too few dims) | N/A | Moderate (0.3-0.6) |
| SAP (single-dim probe) | ~33% (chance) | ~33% | >40% |

### 5.3 Practical Recommendation

Skip formal DCI/SAP computation. D1 (probing classifier), D6 (per-dim KL),
and D7 (MI) collectively provide more diagnostic information than DCI/SAP for
this specific problem.

---

## 6. The Information Shortcut Problem: A Deeper Analysis

### 6.1 Why the Encoder Rationally Ignores State

The model architecture creates what I call a "conditioning shortcut" -- a
well-documented phenomenon in conditional VAEs (Sohn et al., 2015; Zhao et al.,
2017; Nguyen et al., 2023).

**The mathematical argument:** The ELBO objective for a conditional VAE is:

```
ELBO = E_q(z|x,c)[log p(x|z,c)] - beta * KL[q(z|x,c) || p(z)]
```

where c is the condition (state). The encoder q(z|x,c) and decoder p(x|z,c)
both receive c. The encoder can choose to encode c into z or not. If it does
NOT encode c, the decoder still has access to c directly (through the prefix
projection of [z; state_onehot]). So the decoder can reconstruct x equally well
with or without c in z.

Meanwhile, encoding c in z increases KL[q(z|x,c) || p(z)], because the
state-conditional posteriors q(z|x, c=0), q(z|x, c=1), q(z|x, c=2) would
have different means, increasing KL. Since the KL term is penalized (weighted
by beta=1.0 with free-bits), the optimizer actively pushes AGAINST encoding
state in z.

**The result:** The optimal encoder under this architecture is one where z
encodes molecular structure but NOT state. The state arrives at the decoder
through the direct concatenation path [z; state_onehot] -> prefix tokens.

### 6.2 But Does the Decoder USE the State from Prefix Tokens?

Even though state_onehot reaches the decoder via prefix tokens, the decoder
may not use it meaningfully. Here is why:

1. **Prefix token projection:** The z_proj linear layer maps (64+3) -> 2048.
   The 3 state dimensions account for 4.5% of the input. The projection maps
   this to 8 tokens of 256 dims each. The contribution of the 3 state bits
   is diluted across 2048 output dimensions.

2. **Attention dynamics:** The 8 prefix tokens compete with ~50-80 sequence
   tokens for attention. Positional encoding is NOT applied to prefix tokens
   (they are prepended BEFORE pos_encoding is added to the sequence). This
   means prefix tokens lack positional information, which can cause the
   Transformer to treat them differently.

3. **No positional encoding on prefix:** Looking at the code:
   ```python
   embedded = self.pos_encoding(embedded)  # only applied to seq tokens
   combined = torch.cat([prefix, embedded], dim=1)  # prefix has no PE
   ```
   The prefix tokens are raw linear projections without positional encoding.
   The sequence tokens have sinusoidal positional encoding. This asymmetry
   means the Transformer may learn to distinguish prefix from sequence tokens
   based on their encoding pattern, but it also means the 8 prefix tokens are
   positionally interchangeable, which may reduce their information capacity.

4. **Attention sink risk:** Per Xiao et al. (2024) and Gu et al. (2025),
   initial tokens in Transformer sequences often become "attention sinks" --
   they receive high attention weight but their value vectors are actively
   suppressed (low norm) to implement a "no-op" channel. If the 8 prefix
   tokens become sinks, they absorb attention but contribute no information.

### 6.3 Testable Prediction

If the information shortcut hypothesis is correct:
- D1 (probing z) will show ~33-40% accuracy (state NOT in z)
- D3 (attention) will show moderate attention to prefix (~10-15%) but low
  value norms at prefix positions (sink behavior)
- D4 (state-swap) will show >90% identical outputs (state has no effect)
- D5 (scaffold overlap) will show >85% Jaccard overlap across states

If the model actually works but evaluation misses it (H3):
- D1 will show 50-70% accuracy (state IS in z)
- D3 will show genuine attention to prefix with normal value norms
- D4 will show <70% identical outputs and Tanimoto <0.8 between states
- D5 will show <60% Jaccard overlap

---

## 7. Training Data Analysis: The H2 Pre-Check

### 7.1 Critical Metadata Observation

The training data metadata (`egfr_smiles_metadata.json`) contains a critical note:

```
"notes": "State assignments use inhibitor-type heuristics. Compounds without
 known type are assigned randomly."
```

This is a major red flag. If state assignments are based on inhibitor-type
heuristics with random assignment for unknowns, the state labels may be noisy
or uninformative. Specifically:

1. **"Inhibitor-type heuristics"** likely classifies type I inhibitors
   (erlotinib-like 4-anilinoquinazolines) as DFGin_aCin and type II inhibitors
   as DFGout_aCin. But most EGFR inhibitors in ChEMBL are type I (binding the
   active DFGin conformation), so DFGin_aCin would dominate.

2. **"Compounds without known type are assigned randomly"** means a substantial
   fraction of the 8,109 molecules have noise labels. If 30%+ are randomly
   assigned, the signal-to-noise ratio for state conditioning drops
   dramatically.

3. The metadata shows 4 states including DFGout_aCout, but the model config
   uses only 3 states (n_states=3, mapping DFGin_aCin:0, DFGin_aCout:1,
   DFGout_aCin:2). Molecules with DFGout_aCout state in the training data
   are either filtered out or mapped to one of the 3 states.

### 7.2 State Distribution Analysis (Critical Pre-Check)

Before running any GPU-based diagnostics, compute the state distribution in
the training data:

```python
import json
from collections import Counter

with open('data/processed/egfr_smiles_train.json') as f:
    train_data = json.load(f)

state_counts = Counter(item['state'] for item in train_data)
print(state_counts)
# Expected: DFGin_aCin dominates, DFGout_aCin is rare
```

If DFGin_aCin has >60% of molecules and DFGout_aCin has <15%, the class
imbalance alone makes state conditioning difficult. The model sees mostly
DFGin_aCin molecules and learns to generate "generic EGFR molecules" that
happen to also be good DFGin_aCin molecules.

### 7.3 Scaffold Overlap in Training Data

This is the CHEAPEST and MOST INFORMATIVE diagnostic of all. No GPU needed.
Just compute Bemis-Murcko scaffold overlap between states in the training data:

```python
from rdkit import Chem
from rdkit.Chem.Scaffolds.MurckoScaffold import GetScaffoldForMol, MakeScaffoldGeneric
from collections import defaultdict

scaffolds_by_state = defaultdict(set)
for item in train_data:
    mol = Chem.MolFromSmiles(item['smiles'])
    if mol:
        try:
            scaffold = GetScaffoldForMol(mol)
            generic = MakeScaffoldGeneric(scaffold)
            scaffolds_by_state[item['state']].add(Chem.MolToSmiles(generic))
        except:
            pass

# Compute pairwise Jaccard overlap
states = list(scaffolds_by_state.keys())
for i, s1 in enumerate(states):
    for j, s2 in enumerate(states):
        if j <= i:
            continue
        inter = scaffolds_by_state[s1] & scaffolds_by_state[s2]
        union = scaffolds_by_state[s1] | scaffolds_by_state[s2]
        print(f"{s1} vs {s2}: Jaccard={len(inter)/len(union):.3f}")
```

**If Jaccard > 0.7 for all state pairs:** H2 is confirmed. The training data
does not contain state-specific chemistry. No architecture change will help.

**If Jaccard < 0.4 for at least one state pair:** State-specific chemistry
EXISTS in the data but the model fails to learn it. H1 or H1+H3.

---

## 8. Recommended Diagnostic Execution Order

The diagnostics should be executed in this specific order to maximize
information gain per GPU-hour:

### Phase 0: CPU-Only Pre-Check (0 GPU-hours, ~10 minutes)

**0a. Training data state distribution.** Count molecules per state. If one
state has >70% of molecules, class imbalance is a major factor.

**0b. Training data scaffold overlap.** Compute Bemis-Murcko overlap between
states. If Jaccard > 0.7 for all pairs, H2 is strongly supported before
touching a GPU.

### Phase 1: Root Diagnostic (< 0.1 GPU-hours)

**1. D1: Probing Classifier.** Run on 1 checkpoint first, then all 10 if
results are ambiguous. This resolves the top-level branch.

**2. D7: Mutual Information.** Computed from the same mu/logvar data as D1.
Free once D1 data is collected.

### Phase 2: Branching Diagnostics (< 0.3 GPU-hours)

If D1 accuracy <= 40% (state NOT in z):
- **D2: Encoder Hidden Probe.** Determine if state dies in encoder or bottleneck.
- **D6: Per-Dim KL Analysis.** Identify if any dimensions even attempt to
  encode state.

If D1 accuracy >= 50% (state IS in z):
- **D3: Prefix Attention Analysis.** Determine if decoder uses prefix info.
- **D4: State-Swap Experiment.** Determine if generation output changes with state.

### Phase 3: Scaffold Analysis (< 0.2 GPU-hours)

**D5: Per-State Scaffold Overlap.** Run on generated molecules (already
available from the ablation). Compare with training data overlap.

### Total Estimated Compute Budget

| Diagnostic | GPU-Hours | Depends On |
|-----------|-----------|-----------|
| Phase 0 (CPU) | 0 | Nothing |
| D1 (10 checkpoints) | 0.05 | Nothing |
| D7 (from D1 data) | 0.01 | D1 |
| D2 (if D1 < 40%) | 0.05 | D1 |
| D3 (if D1 > 50%) | 0.10 | D1 |
| D4 (state-swap) | 0.15 | D3 |
| D5 (scaffold) | 0.02 | Nothing |
| D6 (per-dim KL) | 0.05 | D1 |
| **Total (all)** | **< 0.5 GPU-hours** | |

This entire battery can run on a single RTX 5000 Ada or H200 in under
30 minutes wall time.

---

## 9. Gradient-Based Diagnostics (Advanced, If Needed)

If the above diagnostics are ambiguous, the following gradient-based experiments
provide additional signal:

### 9.1 d(output)/d(state) Gradient Analysis

Compute the gradient of the decoder output logits with respect to the state_onehot
input. If this gradient is near zero, the state has no causal effect on the output.

```python
def gradient_wrt_state(model, batch, device='cuda'):
    """Compute gradient of output logits w.r.t. state conditioning input."""
    model.eval()
    x = batch['tokens'].to(device)
    lengths = batch['lengths'].to(device)

    # Make state_onehot a leaf tensor requiring grad
    state_onehot = batch['state_onehot'].to(device).requires_grad_(True)

    mu, logvar = model.encode(x, lengths, state_onehot)
    z = mu  # eval mode

    decoder_input = x[:, :-1]
    logits = model.decoder(z, state_onehot, decoder_input)

    # Compute gradient of sum of logits w.r.t. state
    logits.sum().backward()

    grad_norm = state_onehot.grad.norm(dim=-1).mean().item()
    return {'grad_norm_state': grad_norm}
```

**Interpretation:** If grad_norm is < 0.01 (relative to typical gradient norms
in the model), the state signal has effectively zero causal influence on the
output. Note that this gradient includes BOTH the encoder path (state -> GRU ->
mu -> z) and the direct decoder path (state -> [z;state] -> prefix).

### 9.2 State-Counterfactual Gradient

More informative than D4: instead of generating full molecules, compute the
KL divergence between the output distributions (logits) under different state
labels:

```python
def state_counterfactual_kl(model, batch, device='cuda'):
    """Compute KL between output distributions under different states."""
    model.eval()
    x = batch['tokens'].to(device)
    lengths = batch['lengths'].to(device)
    state_onehot = batch['state_onehot'].to(device)

    with torch.no_grad():
        mu, _ = model.encode(x, lengths, state_onehot)
        decoder_input = x[:, :-1]

        logits_by_state = []
        for s in range(3):
            state_oh = torch.zeros_like(state_onehot)
            state_oh[:, s] = 1.0
            logits = model.decoder(mu, state_oh, decoder_input)
            logits_by_state.append(logits)

        # Pairwise KL between state-conditioned output distributions
        kl_pairs = {}
        for i in range(3):
            for j in range(i+1, 3):
                p = torch.softmax(logits_by_state[i], dim=-1)
                q = torch.softmax(logits_by_state[j], dim=-1)
                kl = (p * (p.log() - q.log())).sum(dim=-1).mean()
                kl_pairs[f'state_{i}_vs_{j}'] = kl.item()

        return kl_pairs
```

**Expected:** If KL between state-conditioned outputs is < 0.01 nats per token,
the state conditioning has no meaningful effect on the output distribution.

---

## 10. Hypothesis Assessment Based on Available Evidence

Before running the diagnostic battery, here is my assessment of each hypothesis
based on the available evidence:

### 10.1 H1: Weak Conditioning Mechanism

**Evidence for:**
- Centroid distances 0.26-0.42 are only 6-10% of latent space scale
- Prefix token mechanism is a relatively weak form of conditioning compared to
  cross-attention or FiLM (Perez et al., 2018)
- State one-hot is only 3 dimensions concatenated to 128-dim embedding (2.3%)
  in encoder and 64-dim z (4.5%) in decoder
- No positional encoding on prefix tokens (potential sink behavior)

**Evidence against:**
- The architecture successfully uses z (centroid distances may be small but KL
  is healthy at 14.1/sample)
- Prefix token mechanisms work well in other contexts (prompt tuning, soft
  prompts)
- Even weak conditioning should produce SOME measurable effect (d > 0.1) if
  the data has state-specific structure

**Prior probability:** 35%

### 10.2 H2: Insufficient State-Specific Data

**Evidence for:**
- Metadata explicitly states: "Compounds without known type are assigned
  randomly" -- noisy labels
- Most EGFR inhibitors are type I (DFGin_aCin), so class imbalance is likely
- Model generates same drug scaffolds (erlotinib, gefitinib, osimertinib)
  regardless of state -- these are ALL type I DFGin_aCin inhibitors
- EGFR has relatively few structurally characterized type II inhibitors compared
  to kinases like ABL (imatinib), BRAF (vemurafenib), or MEK
- The 4-anilinoquinazoline scaffold dominates EGFR medicinal chemistry and
  appears across all binding modes
- The information shortcut in the architecture (decoder gets state directly)
  means the encoder has no incentive to encode state in z, which is ONLY a
  problem if state is uninformative (if state were informative, the decoder
  would use it through the prefix tokens)

**Evidence against:**
- 8,109 molecules is not tiny
- Type I vs Type II inhibitors DO have scaffold differences (4-anilinoquinazoline
  vs. phenylaminopyrimidine; Roskoski, 2016)
- Lapatinib, neratinib bind DFGin_aCout (inactive) vs. erlotinib, gefitinib
  bind DFGin_aCin (active) -- chemically distinct

**Prior probability:** 45%

### 10.3 H3: Wrong Evaluation Metric

**Evidence for:**
- Docking_proxy uses fixed 1M17 (DFGin_aCin) pocket -- structurally cannot
  reward DFGin_aCout or DFGout_aCin-specific molecules
- state_specificity is zeroed in the ablation
- The evaluation tests "does conditioning improve generic EGFR quality" not
  "does conditioning improve state-specific quality"
- Section 6.2 of the G2 report explicitly acknowledges this limitation

**Evidence against:**
- Even with a generic evaluation, if conditioning produces genuinely different
  molecules, SOME scoring components should show differences (reference_similarity,
  druglikeness)
- No component shows d > 0.17 -- not even the state-agnostic components
- If the model generates state-specific molecules, we would expect lower
  SIMILARITY to the reference set (which is dominated by DFGin_aCin drugs) for
  DFGin_aCout-conditioned molecules, producing a NEGATIVE effect on
  reference_similarity. We see d = 0.06, not negative.

**Prior probability:** 20%

### 10.4 Combined Assessment

**Most likely scenario (probability ~55%):** H2 is the primary cause, with H1
as a contributing factor. The training data does not contain sufficient state-
specific chemical structure for the model to learn meaningful state-condition
mappings. The architecture's information shortcut (decoder gets state directly)
means the encoder rationally ignores state, and the decoder has no incentive to
use state because the state labels do not predict molecular structure.

**Second most likely (probability ~25%):** H1 is the primary cause. The data
does contain some state-specific structure, but the prefix token mechanism is
too weak to force the decoder to use it. Cross-attention or FiLM conditioning
would show a stronger signal.

**Third most likely (probability ~15%):** H3 contributes meaningfully. The
model generates somewhat different molecules per state, but the fixed-pocket
evaluation cannot detect this.

**Least likely (probability ~5%):** All three hypotheses are false. Conditioning
works, the data has state-specific structure, and the evaluation is correct.
The thesis is simply wrong -- conformational state does not help molecular
design for EGFR.

---

## 11. What Should the Project Do Next?

### 11.1 Immediate Actions (This Week)

1. **Run Phase 0 (CPU, 10 minutes):** Training data state distribution +
   scaffold overlap. This alone may resolve the investigation.

2. **Run Phase 1 (D1 + D7, <5 minutes GPU):** Probing classifier on one
   checkpoint. If accuracy is ~33%, the signal dies in the encoder and H2 is
   strongly supported. If >50%, proceed to attention and state-swap diagnostics.

3. **Run Phase 2 (branching, <20 minutes GPU):** Follow the diagnostic tree
   based on D1 results.

### 11.2 Decision Rules After Diagnostics

**If D1 < 40% AND training scaffold Jaccard > 0.7:**
- H2 confirmed. The data is the problem.
- Option A: Switch to a kinase with clearer type I/II scaffold separation
  (ABL, BRAF, CDK4/6). ABL is ideal: imatinib (DFGout, type II) vs. dasatinib
  (DFGin, type I) represent genuinely different chemotypes.
- Option B: Re-label molecules using structural docking (dock each molecule
  against 3 pocket conformers, assign to state with best docking score). This
  creates structure-based labels instead of heuristic labels.
- Option C: Publication as negative result -- "Conformational state labels
  derived from inhibitor-type heuristics do not carry enough structural
  information for conditional molecular generation."

**If D1 > 50% AND D4 shows <70% identical outputs:**
- H3 supported. Conditioning works but evaluation misses it.
- Action: State-specific docking evaluation (~20,400 GNINA runs, 3 GPU jobs).
  Dock conditioned molecules against their target state's pocket and compare
  docking scores to unconditioned molecules.

**If D1 < 40% AND training scaffold Jaccard < 0.5:**
- H1 supported (data has structure, architecture loses it).
- Action: Replace prefix tokens with cross-attention conditioning. Specifically:
  - Add a learned state embedding matrix (3 x d_model)
  - Replace prefix projection with cross-attention layers in the decoder
  - Or add FiLM conditioning (gamma, beta from state embedding) at each layer
  - Retrain and repeat diagnostics

### 11.3 Compute Budget for Recovery

| Action | GPU-Hours | SLURM Jobs | Priority |
|--------|-----------|-----------|----------|
| Full diagnostic battery | 0.5 | 1 | Highest |
| State-specific docking (if H3) | ~20 | 3-5 | High |
| Cross-attention VAE (if H1) | ~40 | 20 | Medium |
| New kinase data (if H2, ABL) | ~10 | 5-10 | Medium |
| Relabeling via docking (if H2) | ~30 | 5-10 | Medium |

---

## 12. References

1. Alain, G. & Bengio, Y. (2017). Understanding intermediate layers using linear
   classifier probes. *ICLR Workshop*.

2. Belinkov, Y. (2022). Probing classifiers: Promises, shortcomings, and advances.
   *Computational Linguistics*, 48(1), 207-219.

3. Belghazi, M.I., et al. (2018). MINE: Mutual Information Neural Estimation.
   *ICML 2018*.

4. Bemis, G.W. & Murcko, M.A. (1996). The properties of known drugs. 1. Molecular
   frameworks. *Journal of Medicinal Chemistry*, 39(15), 2887-2893.

5. Chen, R.T., Li, X., Grosse, R.B., & Duvenaud, D.K. (2018). Isolating sources of
   disentanglement in variational autoencoders. *NeurIPS 2018*.

6. Chefer, H., Gur, S., & Wolf, L. (2021). Transformer interpretability beyond
   attention visualization. *CVPR 2021*.

7. Eastwood, C. & Williams, C.K.I. (2018). A framework for the quantitative
   evaluation of disentangled representations. *ICLR 2018*.

8. Gu, X. et al. (2025). Attention sink in Transformers. *Presentation at Hunyuan*.

9. Kumar, A., Sattigeri, P., & Balakrishnan, A. (2018). Variational inference of
   disentangled latent concepts from unlabeled observations. *ICLR 2018*.

10. Li, X. & Liang, P. (2021). Prefix-tuning: Optimizing continuous prompts for
    generation. *ACL 2021*.

11. Lester, B., Al-Rfou, R., & Constant, N. (2021). The power of scale for
    parameter-efficient prompt tuning. *EMNLP 2021*.

12. Nguyen, T.M., et al. (2023). Beyond vanilla variational autoencoders:
    Detecting posterior collapse in conditional and hierarchical variational
    autoencoders. *arXiv:2306.05023*. Published at a major venue, establishing
    that input-output correlation in CVAEs causes posterior collapse.

13. Perez, E., Strub, F., de Vries, H., Dumoulin, V., & Bengio, A. (2018). FiLM:
    Visual reasoning with a general conditioning layer. *AAAI 2018*.

14. Poole, B., Ozair, S., Van Den Oord, A., Alemi, A., & Tucker, G. (2019). On
    variational bounds of mutual information. *ICML 2019*.

15. Roskoski, R. Jr. (2016). Classification of small molecule protein kinase
    inhibitors based upon the structures of their drug-enzyme complexes. *Pharmacological
    Research*, 103, 26-48.

16. Sohn, K., Lee, H., & Yan, X. (2015). Learning structured output representation
    using deep conditional generative models. *NeurIPS 2015*.

17. Xiao, G., et al. (2024). Efficient streaming language models with attention
    sinks. *ICLR 2024*.

18. Zhao, S., Song, J., & Ermon, S. (2017). InfoVAE: Information maximizing
    variational autoencoders. *arXiv:1706.02262*.

19. Bhadwal, A.S., Kumari, M. & Kumar, A. (2025). PCF-VAE: posterior collapse free
    variational autoencoder for de novo drug design. *Scientific Reports*, 15.

20. Peng, X. et al. (2026). PocketXMol: Unified modeling of 3D molecular generation
    via atomic interactions. *Cell*.

21. Abnar, S. & Zuidema, W. (2020). Quantifying attention flow in transformers.
    *ACL 2020*.

22. Roskoski, R. Jr. (2019). Small molecule inhibitors targeting the EGFR/ErbB family
    of protein-tyrosine kinases in human cancers. *Pharmacological Research*, 139, 395-411.

23. Schimunek, J. et al. (2023). Context-enriched molecule representations improve
    few-shot drug discovery. *ICLR 2023*.

24. van den Oord, A. et al. (2017). Neural discrete representation learning (VQ-VAE).
    *NeurIPS 2017*.

25. Dumoulin, V., Shlens, J., & Kudlur, M. (2017). A learned representation for
    artistic style (AdaIN). *ICLR 2017*.

---

## 13. Appendix: Complete Diagnostic Script

Below is a self-contained script that runs all diagnostics on a single checkpoint.
It can be submitted as a SLURM job with <1 GPU-hour.

```python
#!/usr/bin/env python3
"""StateBind G2 Diagnostic Battery -- All 7 diagnostics on one checkpoint.

Usage:
    python run_diagnostics.py --checkpoint_dir artifacts/models/transformer_vae/seed_42_cond/
    
Submit via SLURM:
    sbatch -p gpu_devel -A pi_mg269 --gpus=rtx_5000_ada:1 --cpus-per-task=4 \
           --mem=16G -t 00:30:00 --wrap="python run_diagnostics.py ..."
"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint_dir', type=str, required=True)
    parser.add_argument('--data_path', type=str,
                        default='data/processed/egfr_smiles_val.json')
    parser.add_argument('--output_path', type=str,
                        default='artifacts/evaluation/diagnostics/')
    parser.add_argument('--device', type=str, default='auto')
    args = parser.parse_args()

    # Import torch and model modules
    import torch
    from statebind.ml.transformer_vae import ConditionalTransformerVAE, TransformerVAEConfig

    # 1. Load checkpoint
    logger.info("Loading checkpoint from %s", args.checkpoint_dir)
    # ... (checkpoint loading logic)

    # 2. Load validation data
    logger.info("Loading validation data from %s", args.data_path)
    # ... (data loading logic)

    # 3. Run Phase 0: CPU diagnostics
    logger.info("=== Phase 0: Training Data Analysis ===")
    # ... (state distribution, scaffold overlap)

    # 4. Run D1: Probing Classifier
    logger.info("=== D1: Probing Classifier ===")
    d1_results = diagnostic_1_probing_classifier(model, val_loader, device)
    logger.info("D1 Accuracy: %.4f +/- %.4f (chance: %.4f)",
                d1_results['cv_accuracy_mean'],
                d1_results['cv_accuracy_std'],
                d1_results['chance_level'])

    # 5. Branch based on D1
    if d1_results['cv_accuracy_mean'] < 0.40:
        logger.info("State NOT in z (accuracy < 40%). Running D2, D6.")
        # D2: Encoder hidden probe
        d2_results = diagnostic_2_encoder_hidden_probe(model, val_loader, device)
        # D6: Per-dim KL
        d6_results = diagnostic_6_per_dim_kl_analysis(model, val_loader, device)
    else:
        logger.info("State MAY be in z (accuracy >= 40%). Running D3, D4.")
        # D3: Attention analysis
        d3_results = diagnostic_3_prefix_attention(model, val_loader, device)
        # D4: State-swap
        d4_results = diagnostic_4_state_swap(model, val_loader, vocab, device)

    # 6. D5: Scaffold overlap (always run)
    logger.info("=== D5: Scaffold Overlap ===")
    # ... (scaffold analysis)

    # 7. D7: Mutual information (always run, from D1 data)
    logger.info("=== D7: Mutual Information ===")
    d7_results = diagnostic_7_mutual_information(model, val_loader, device)

    # 8. Save results
    output_dir = Path(args.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    # ... (save JSON)

    logger.info("Diagnostics complete. Results saved to %s", output_dir)


if __name__ == '__main__':
    main()
```

---

## 14. Summary Table: What Each Diagnostic Tells Us

| # | Diagnostic | What It Measures | GPU Cost | Resolves |
|---|-----------|-----------------|---------|---------|
| D1 | Probing Classifier | Is state encoded in z? | 5 min | H1 vs H2 vs H3 (root branch) |
| D2 | Encoder Hidden Probe | Is state in pre-bottleneck hidden? | 5 min | Encoder vs bottleneck problem |
| D3 | Prefix Attention | Does decoder attend to prefix? | 10 min | H1 subtype (bypass vs sink) |
| D4 | State-Swap | Does state change generation? | 15 min | H1 vs H3 (definitive) |
| D5 | Scaffold Overlap | Same scaffolds across states? | 2 min | H2 (data structure) |
| D6 | Per-Dim KL | Which dims encode state? | 5 min | H1 refinement |
| D7 | Mutual Information | How many bits of state in z? | 5 min | Quantifies H1 vs H2 severity |

**Total GPU time: < 30 minutes on a single GPU.**

The most valuable experiment per GPU-minute is D1 (probing classifier). If forced
to run exactly one diagnostic, run D1. Its result determines every subsequent step.
