# Structural State Atlas

## What the Atlas Represents

The state atlas is a structured collection of EGFR kinase domain crystal structures,
each annotated with:

1. **Conformational state label** (DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout)
2. **Structural feature vector** (9 geometric measurements characterizing the conformation)
3. **Cluster assignment** (unsupervised grouping in feature space)
4. **Pocket descriptor** (how the binding pocket differs in this conformation)
5. **Mutation annotations** (which mutations are present)

This is the structural foundation for state-aware design. It replaces the
single-structure worldview (Phase 2 baseline) with a multi-state ensemble view.

## How Structures Were Compared

### Feature Vector (9 dimensions)

| Feature | What it measures | DFGin_aCin | DFGout_aCout |
|---------|-----------------|------------|--------------|
| DFG Asp-Phe distance | DFG motif conformation | ~5 Å | ~11 Å |
| DFG-Phe position | Phenylalanine displacement | ~0.5 Å | ~7 Å |
| αC salt bridge | K745-E762 distance | ~3 Å | ~10 Å |
| αC rotation | Helix rotation angle | ~2° | ~22° |
| P-loop displacement | P-loop RMSD vs active | ~0 Å | ~1.8 Å |
| Hinge angle | Backbone angle at hinge | ~155° | ~143° |
| A-loop RMSD | Activation loop movement | ~0 Å | ~5.5 Å |
| Gatekeeper χ1 | Gatekeeper sidechain angle | ~-65° | ~-55° |
| Pocket volume | Binding site volume | ~450 ų | ~850 ų |

These features were chosen because they are:
- Physically interpretable
- Known to distinguish kinase conformational states
- Measurable from crystal structures (or literature)
- Relevant to drug binding

### Standardization and Distance

Features are standardized (z-scored) before comparison so that features
on different scales contribute equally. Pairwise distances are Euclidean
in standardized feature space.

## How State Clustering Was Performed

**Method:** Agglomerative clustering (Ward linkage) on standardized features.

**Number of clusters:** 4 (matching the 4 canonical kinase states).

**Validation:**
- Label agreement: do clusters match literature state labels?
- Separation ratio: is the inter-cluster distance much larger than intra-cluster?

This is a validation clustering, not a discovery clustering. We expect
4 well-separated clusters because the features were designed to capture
the known state distinctions. The value is in quantifying separation
and identifying structures that may be intermediate.

## How Pocket Differences Are Represented

Each atlas entry has a `PocketDescriptor` with:

| Property | What it captures |
|----------|-----------------|
| Volume | Overall pocket size (ų) |
| Back pocket accessible | Is the type-II back pocket open? (DFG-out) |
| Covalent C797 exposed | Is the covalent binding cysteine accessible? |
| Gatekeeper clearance | How much room past the gatekeeper? (T790M sensitive) |
| Hinge accessibility | Can inhibitors form hinge H-bonds? |
| P-loop conformation | Is the P-loop extended, intermediate, or folded? |

## Why This Matters for Downstream Design

1. **Different states = different pockets.** The active-state pocket is ~450 ų.
   The classical inactive pocket is ~850 ų. Designing only against 450 ų
   misses compounds that would fit the larger pocket.

2. **Resistance mutations shift state preference.** T790M stabilizes the active
   state. Designing against inactive states for T790M is pointless — the
   protein doesn't visit them. But for WT, targeting inactive states might
   find selective compounds.

3. **State-specific pocket features.** The back pocket is only accessible in
   DFG-out states. Type-II inhibitors need this pocket. The static baseline
   (active state) never sees it.

4. **Context-to-state prediction.** The atlas provides the structural ground
   truth that maps mutations to states. Phase 4 builds on this.

## How to Build the Atlas

```bash
python scripts/build_state_atlas.py
```

## Artifacts

```
artifacts/structure/state_atlas_v1/
├── state_atlas.json          # Full atlas with all entries, clusters, distances
├── atlas_table.csv           # Inspectable summary per structure
├── clusters.json             # Cluster descriptions
├── pocket_comparison.json    # Per-state pocket statistics
├── pocket_differences.json   # Ranked pocket differences with design implications
├── clustering_quality.json   # Clustering quality metrics
└── pairwise_distances.csv    # Full pairwise distance matrix
```
