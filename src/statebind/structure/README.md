# statebind.structure

## Purpose

Conformational state atlas for the EGFR kinase domain (Phase 3). This module classifies crystal structures by DFG and aC-helix conformation, extracts geometric features per structure, clusters conformations in feature space, compares binding pockets across states, and produces the `StateAtlas` artifact -- the central structural data product that downstream modules (generation, ranking) depend on to understand how the pocket changes with conformational state.

## Public API

| Symbol | Type | Signature | Description |
|--------|------|-----------|-------------|
| `build_state_atlas` | function | `(n_clusters: int = 4, output_dir: Path \| None = None) -> StateAtlas` | Build the complete EGFR structural state atlas (load structures, extract features, cluster, compute pairwise distances) |
| `extract_features` | function | `(pdb_id: str) -> tuple[StructuralFeatures, PocketDescriptor]` | Extract structural features for a PDB structure (v1: literature-curated values) |
| `get_available_pdb_ids` | function | `() -> list[str]` | Return sorted list of PDB IDs with curated features available |
| `cluster_structures` | function | `(entries: list[AtlasEntry], n_clusters: int = 4, linkage: str = "ward") -> tuple[list[AtlasEntry], list[StateCluster]]` | Cluster atlas entries by structural features using agglomerative clustering |
| `compute_pairwise_distances` | function | `(entries: list[AtlasEntry]) -> list[PairwiseSimilarity]` | Compute pairwise Euclidean distances in standardized feature space |
| `compute_cluster_quality` | function | `(entries: list[AtlasEntry]) -> dict[str, float]` | Compute label agreement, intra/inter-cluster distances, and separation ratio |
| `compare_pockets_by_state` | function | `(entries: list[AtlasEntry]) -> dict[str, dict]` | Compare pocket descriptors grouped by conformational state label |
| `identify_pocket_differences` | function | `(comparison: dict[str, dict]) -> list[dict]` | Identify salient pocket differences between states, ordered by design relevance |
| `StructuralFeatures` | Pydantic model | -- | 9 geometric features per structure (DFG distances, aC-helix metrics, P-loop, hinge, A-loop, gatekeeper, pocket volume) |
| `PocketDescriptor` | Pydantic model | -- | Pocket-level descriptor (volume, back pocket accessibility, C797 exposure, gatekeeper clearance, hinge accessibility, P-loop conformation) |
| `AtlasEntry` | Pydantic model | -- | Single structure in the atlas with features, pocket, state label, cluster assignment |
| `StateCluster` | Pydantic model | -- | Cluster description with dominant state, member PDB IDs, centroid features |
| `PairwiseSimilarity` | Pydantic model | -- | Pairwise structural similarity between two atlas entries |
| `StateAtlas` | Pydantic model | -- | Complete atlas: entries, clusters, pairwise similarities, metadata |

## Internal Files

| File | Responsibility |
|------|---------------|
| `models.py` | Pydantic data models: `StructuralFeatures`, `PocketDescriptor`, `AtlasEntry`, `StateCluster`, `PairwiseSimilarity`, `StateAtlas` |
| `features.py` | Literature-curated structural features and pocket descriptors for 16 EGFR structures across 4 conformational states |
| `clustering.py` | Agglomerative clustering on standardized feature vectors; cluster description generation; pairwise distance computation; cluster quality metrics |
| `pocket_comparison.py` | Cross-state pocket comparison: per-state statistics, pocket difference identification with drug design implications |
| `atlas.py` | Atlas builder orchestration: loads structure dataset, extracts features, clusters, computes distances, writes 7 output artifacts |
| `__init__.py` | Package docstring |

## Dependencies

- **Imports from:** `statebind.processing.models` (ConformationalState, Provenance), `statebind.processing.structures` (build_structure_dataset)
- **External:** `numpy`, `scikit-learn` (AgglomerativeClustering, StandardScaler)
- **Imported by:** `statebind.generation` (uses PocketDescriptor)

## Data Flow

**Reads:**
- Structure dataset via `statebind.processing.structures.build_structure_dataset()`
- Curated feature values from the internal `_curated_features()` lookup table in `features.py`

**Produces (when output_dir is set):**
- `state_atlas.json` -- full atlas with all entries, clusters, pairwise similarities
- `atlas_table.csv` -- summary table of structures with key features
- `clusters.json` -- cluster descriptions
- `pocket_comparison.json` -- per-state pocket statistics
- `pocket_differences.json` -- salient pocket differences with design implications
- `clustering_quality.json` -- label agreement, intra/inter cluster distances, separation ratio
- `pairwise_distances.csv` -- all-pairs distance matrix

## Testing

- **Test file:** `tests/test_structure.py`
- **Run:** `pytest tests/test_structure.py -v`
- **Key fixtures:** `PROJECT_ROOT` constant for path resolution; tests cover project layout, feature extraction, clustering, pocket comparison, and full atlas build
- **Coverage:** Feature extraction for known PDB IDs, clustering with expected number of clusters, pairwise distance computation, pocket comparison by state, end-to-end atlas build

## Patterns to Follow

- All features carry a `feature_source` field ("literature", "computed", "predicted") so consumers know the provenance.
- Feature vectors are accessed via `StructuralFeatures.to_vector()` and names via `StructuralFeatures.feature_names()` to keep ordering consistent.
- Clustering always standardizes features with `StandardScaler` before computing distances.
- Pocket differences include a `design_implication` field to connect structural observations to drug design decisions.
- Atlas entries carry full `Provenance` metadata.

## Known Limitations

- **Literature-curated features only:** All 9 geometric features are hand-curated from published analyses, not computed from PDB coordinates. The curated set covers 16 structures.
- **No coordinate-based computation:** Feature extraction raises `KeyError` for PDB IDs not in the curated set. Future versions should compute features from PDB files using BioPython or MDAnalysis.
- **Fixed feature set:** The 9-feature representation is manually selected; no automated feature discovery.
- **Small structure set:** 16 structures across 4 states (7 DFGin_aCin, 5 DFGin_aCout, 2 DFGout_aCin, 2 DFGout_aCout).

## Planned Improvements

No currently planned workstream modifications. Future work would involve computing features directly from PDB coordinates and expanding the structure set.

## Current Status

Complete. 16 structures classified into 4 states. Literature-curated 9-D feature vectors. Agglomerative clustering with quality metrics.

## Remaining Work for AI Agents

No pending workstream work. Future: compute features from PDB coordinates via BioPython instead of literature curation.
