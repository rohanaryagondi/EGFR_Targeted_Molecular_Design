# Context-to-State Model

## Overview

The context-to-state model predicts which EGFR conformational state(s) are most
relevant for a given biological context (mutation profile + optional pathway features).

This connects the mutation biology (Phase 1) to the structural state atlas (Phase 3),
enabling state-aware molecular design in Phase 5.

## Inputs

### Mutation features (29 dimensions)
- **Position**: Relative position within the kinase domain [0, 1]
- **Amino acid properties**: Hydrophobicity, volume, charge, molecular weight
  for wild-type and mutant residues, plus delta (change)
- **Resistance generation**: Ordinal encoding (activating=0, 1st=1, ..., 4th=4)
- **Drug counts**: Number of drugs affected and effective
- **Structure availability**: Binary flag for PDB structure existence
- **Mechanism category**: One-hot encoding (12 categories)

### Pathway proxy features (4 dimensions)
- `pathway_mapk`: MAPK pathway activation score [0, 1]
- `pathway_pi3k`: PI3K/AKT pathway activation score [0, 1]
- `pathway_stat3`: STAT3 pathway activation score [0, 1]
- `pathway_src`: Src kinase pathway activation score [0, 1]

**Note:** v1 pathway features are literature-curated proxies, not measured data.
They represent estimated relative pathway activation based on published functional
studies of each mutation.

## Outputs

1. **Predicted state label**: One of {DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout}
2. **Probability distribution**: P(state | mutation) for all 4 states
3. **Confidence score**: Max probability (higher = more certain)
4. **Soft label distribution**: Ground-truth uncertainty encoding

## Label Assumptions

State labels are derived from the `preferred_states` field on each MutationRecord:

| Scenario | Primary label | Distribution |
|----------|--------------|--------------|
| preferred_states = [DFGin_aCin] | DFGin_aCin | 70% to preferred, 10% each to others |
| preferred_states = [A, B] | First entry (A) | 35% each to A and B, 15% each to others |
| preferred_states = [] | DFGin_aCin (default) | Uniform 25% each (maximum uncertainty) |

**Known bias:** Many mutations default to DFGin_aCin because their conformational
preference is not well characterized. The model should learn to assign low
confidence to these cases.

## Split Strategy

- **Test set (forced):** T790M, L858R, C797S — the 3 most clinically important mutations
- **Remaining:** Hash-based assignment (~60% train, ~20% val, ~20% test)
- **Guarantee:** At least 1 train and 1 val sample among non-key mutations
- **Reproducibility:** Deterministic hash with seed=42

## Baselines

1. **Nearest centroid (mutation-only)** — simplest baseline, class centroids
2. **Nearest centroid (pathway-only)** — tests pathway signal alone
3. **Nearest centroid (combined)** — tests whether adding pathways helps
4. **Logistic regression (mutation-only)** — learned decision boundary
5. **Logistic regression (combined)** — learned boundary with all features
6. **Embedding MLP (combined)** — nonlinear feature combinations

## Limitations

1. Dataset size (n=17) is far below what's needed for reliable ML. Results are
   directional evidence, not statistical guarantees.
2. Pathway features are proxies. Real expression/proteomics data would be needed
   for a production model.
3. Label assignment assumes known conformational preference. Mutations with
   unknown preference get a default label, introducing noise.
4. No cross-validation due to small sample size. Single split provides one estimate.
5. Models are intentionally simple. Complex architectures are not appropriate
   for n=17.
