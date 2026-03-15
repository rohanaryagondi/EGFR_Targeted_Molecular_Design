"""State atlas builder: orchestrates atlas construction.

Takes the processed structure dataset, extracts features for each
structure, clusters them, computes pairwise similarities, and
produces the complete StateAtlas artifact.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from statebind.processing.models import Provenance
from statebind.processing.structures import build_structure_dataset
from statebind.structure.clustering import (
    cluster_structures,
    compute_cluster_quality,
    compute_pairwise_distances,
)
from statebind.structure.features import extract_features, get_available_pdb_ids
from statebind.structure.models import AtlasEntry, StateAtlas, StructuralFeatures
from statebind.structure.pocket_comparison import (
    compare_pockets_by_state,
    identify_pocket_differences,
)


def build_state_atlas(
    n_clusters: int = 4,
    output_dir: Path | None = None,
) -> StateAtlas:
    """Build the complete EGFR structural state atlas.

    Steps:
    1. Load structure dataset
    2. Extract features for each structure
    3. Build atlas entries
    4. Cluster in feature space
    5. Compute pairwise distances
    6. Optionally write artifacts

    Args:
        n_clusters: Number of clusters for state grouping.
        output_dir: If provided, write all artifacts here.

    Returns:
        Complete StateAtlas.
    """
    struct_ds = build_structure_dataset()
    available = set(get_available_pdb_ids())

    # Build atlas entries
    entries = []
    skipped = []
    for s in struct_ds.structures:
        if s.pdb_id not in available:
            skipped.append(s.pdb_id)
            continue

        features, pocket = extract_features(s.pdb_id)

        entry = AtlasEntry(
            pdb_id=s.pdb_id,
            chain=s.chain,
            resolution=s.resolution,
            state_label=s.state,
            mutations_present=s.mutations_present,
            ligand_id=s.ligand_id,
            ligand_bound=s.ligand_bound,
            is_apo=s.is_apo,
            is_representative=s.is_representative,
            features=features,
            pocket=pocket,
            feature_source="literature",
            notes=s.notes,
            provenance=Provenance(
                sources=["pdb", "literature"],
                processing_version="0.1.0",
                processing_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            ),
        )
        entries.append(entry)

    if skipped:
        print(f"Skipped {len(skipped)} structures without features: {skipped}")

    print(f"Built {len(entries)} atlas entries")

    # Cluster
    entries, clusters = cluster_structures(entries, n_clusters=n_clusters)
    print(f"Clustered into {len(clusters)} groups")

    # Pairwise distances
    pairwise = compute_pairwise_distances(entries)

    # Count distinct states
    states = {e.state_label for e in entries}

    now = datetime.now(timezone.utc).isoformat()

    atlas = StateAtlas(
        version="1.0.0",
        entries=entries,
        clusters=clusters,
        pairwise_similarities=pairwise,
        n_structures=len(entries),
        n_states=len(states),
        n_clusters=len(clusters),
        feature_names=StructuralFeatures.feature_names(),
        generated_at=now,
        processing_version="0.1.0",
        notes=(
            f"EGFR kinase domain state atlas. {len(entries)} structures, "
            f"{len(states)} states, {len(clusters)} clusters. "
            f"Features: literature-curated (v1)."
        ),
    )

    if output_dir is not None:
        _write_atlas_artifacts(atlas, entries, output_dir)

    return atlas


def _write_atlas_artifacts(
    atlas: StateAtlas,
    entries: list[AtlasEntry],
    output_dir: Path,
) -> None:
    """Write atlas artifacts to disk."""
    import csv

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Full atlas JSON
    with open(output_dir / "state_atlas.json", "w") as f:
        json.dump(atlas.model_dump(mode="json"), f, indent=2, default=str)

    # 2. Atlas summary table CSV
    fields = [
        "pdb_id", "state_label", "cluster_id", "resolution",
        "mutations_present", "ligand_id", "is_representative",
        "dfg_asp_phe_dist", "ac_helix_salt_bridge", "ac_helix_rotation",
        "pocket_volume", "back_pocket_accessible",
    ]
    with open(output_dir / "atlas_table.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for e in entries:
            writer.writerow({
                "pdb_id": e.pdb_id,
                "state_label": e.state_label.value,
                "cluster_id": e.cluster_id,
                "resolution": e.resolution,
                "mutations_present": ";".join(e.mutations_present),
                "ligand_id": e.ligand_id,
                "is_representative": e.is_representative,
                "dfg_asp_phe_dist": e.features.dfg_asp_phe_dist,
                "ac_helix_salt_bridge": e.features.ac_helix_salt_bridge,
                "ac_helix_rotation": e.features.ac_helix_rotation,
                "pocket_volume": e.pocket.pocket_volume,
                "back_pocket_accessible": e.pocket.back_pocket_accessible,
            })

    # 3. Cluster summary
    cluster_data = []
    for c in atlas.clusters:
        cluster_data.append({
            "cluster_id": c.cluster_id,
            "label": c.label,
            "dominant_state": c.dominant_state.value,
            "n_members": c.n_members,
            "members": ", ".join(c.member_pdb_ids),
            "mean_resolution": c.mean_resolution,
            "has_mutants": c.has_mutant_structures,
        })
    with open(output_dir / "clusters.json", "w") as f:
        json.dump(cluster_data, f, indent=2)

    # 4. Pocket comparison
    pocket_comp = compare_pockets_by_state(entries)
    with open(output_dir / "pocket_comparison.json", "w") as f:
        json.dump(pocket_comp, f, indent=2)

    # 5. Pocket differences
    differences = identify_pocket_differences(pocket_comp)
    with open(output_dir / "pocket_differences.json", "w") as f:
        json.dump(differences, f, indent=2)

    # 6. Clustering quality
    quality = compute_cluster_quality(entries)
    with open(output_dir / "clustering_quality.json", "w") as f:
        json.dump(quality, f, indent=2)

    # 7. Pairwise distance matrix as CSV
    with open(output_dir / "pairwise_distances.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["pdb_a", "pdb_b", "state_a", "state_b", "distance", "same_cluster"]
        )
        writer.writeheader()
        for p in atlas.pairwise_similarities:
            writer.writerow({
                "pdb_a": p.pdb_id_a,
                "pdb_b": p.pdb_id_b,
                "state_a": p.state_a,
                "state_b": p.state_b,
                "distance": p.feature_distance,
                "same_cluster": p.same_cluster,
            })

    print(f"\nAtlas artifacts written to {output_dir}/")
    for fp in sorted(output_dir.iterdir()):
        if fp.name != ".gitkeep":
            print(f"  {fp.name:<35} {fp.stat().st_size:>8} bytes")
