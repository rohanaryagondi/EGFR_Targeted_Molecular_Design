"""State clustering for the EGFR structural atlas.

Clusters structures in feature space to discover/validate conformational
state groupings. Uses agglomerative clustering on standardized features.

The clustering serves two purposes:
1. Validation: do clusters match literature state labels?
2. Discovery: are there sub-states or intermediate conformations?
"""

from __future__ import annotations

from collections import Counter

import numpy as np

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from statebind.structure.models import (
    AtlasEntry,
    PairwiseSimilarity,
    StateCluster,
)


def cluster_structures(
    entries: list[AtlasEntry],
    n_clusters: int = 4,
    linkage: str = "ward",
) -> tuple[list[AtlasEntry], list[StateCluster]]:
    """Cluster atlas entries by structural features.

    Args:
        entries: Atlas entries with features.
        n_clusters: Number of clusters (default 4 = canonical states).
        linkage: Linkage criterion for agglomerative clustering.

    Returns:
        Tuple of (updated entries with cluster_id, cluster descriptions).
    """
    if not HAS_SKLEARN:
        raise ImportError(
            "scikit-learn is required for clustering. "
            "Install with: pip install statebind[science]"
        )
    if len(entries) < n_clusters:
        raise ValueError(
            f"Need at least {n_clusters} entries for {n_clusters} clusters, "
            f"got {len(entries)}"
        )

    # Build feature matrix
    X = np.array([e.features.to_vector() for e in entries])
    feature_names = entries[0].features.feature_names()

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Cluster
    model = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage=linkage,
    )
    labels = model.fit_predict(X_scaled)

    # Assign cluster IDs to entries
    for entry, label in zip(entries, labels):
        entry.cluster_id = int(label)

    # Build cluster descriptions
    clusters = _describe_clusters(entries, X, feature_names, n_clusters)

    return entries, clusters


def _describe_clusters(
    entries: list[AtlasEntry],
    X: np.ndarray,
    feature_names: list[str],
    n_clusters: int,
) -> list[StateCluster]:
    """Build human-readable cluster descriptions."""
    clusters = []

    for cid in range(n_clusters):
        members = [e for e in entries if e.cluster_id == cid]
        member_ids = [e.pdb_id for e in members]
        member_indices = [i for i, e in enumerate(entries) if e.cluster_id == cid]

        if not members:
            continue

        # Determine dominant state label
        state_counts = Counter(e.state_label for e in members)
        dominant_state = state_counts.most_common(1)[0][0]

        # Compute centroid
        centroid = X[member_indices].mean(axis=0).tolist()

        # Mean resolution
        resolutions = [e.resolution for e in members if e.resolution > 0]
        mean_res = sum(resolutions) / len(resolutions) if resolutions else 0.0

        # Check for mutant structures
        has_mutants = any(len(e.mutations_present) > 0 for e in members)

        # Generate label
        label = _generate_cluster_label(dominant_state, members)

        clusters.append(StateCluster(
            cluster_id=cid,
            label=label,
            dominant_state=dominant_state,
            member_pdb_ids=member_ids,
            centroid_features=centroid,
            n_members=len(members),
            mean_resolution=round(mean_res, 2),
            has_mutant_structures=has_mutants,
            notes=f"Dominant state: {dominant_state.value} "
                  f"({state_counts[dominant_state]}/{len(members)} members)",
        ))

    return clusters


def _generate_cluster_label(dominant_state, members) -> str:
    """Generate a human-readable cluster label."""
    from statebind.processing.models import ConformationalState

    labels = {
        ConformationalState.DFGIN_ACIN: "Active (DFGin/αCin)",
        ConformationalState.DFGIN_ACOUT: "Src-like inactive (DFGin/αCout)",
        ConformationalState.DFGOUT_ACIN: "DFGout intermediate (DFGout/αCin)",
        ConformationalState.UNCLASSIFIED: "Unclassified",
    }
    base = labels.get(dominant_state, "Unknown")
    n_mutants = sum(1 for e in members if e.mutations_present)
    if n_mutants > 0:
        base += f" [+{n_mutants} mutant(s)]"
    return base


def compute_pairwise_distances(
    entries: list[AtlasEntry],
) -> list[PairwiseSimilarity]:
    """Compute pairwise Euclidean distances in feature space.

    Args:
        entries: Atlas entries with features.

    Returns:
        List of PairwiseSimilarity for all pairs.
    """
    if not HAS_SKLEARN:
        raise ImportError(
            "scikit-learn is required for pairwise distances. "
            "Install with: pip install statebind[science]"
        )
    n = len(entries)
    X = np.array([e.features.to_vector() for e in entries])

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    similarities = []
    for i in range(n):
        for j in range(i + 1, n):
            dist = float(np.linalg.norm(X_scaled[i] - X_scaled[j]))
            similarities.append(PairwiseSimilarity(
                pdb_id_a=entries[i].pdb_id,
                pdb_id_b=entries[j].pdb_id,
                state_a=entries[i].state_label.value,
                state_b=entries[j].state_label.value,
                feature_distance=round(dist, 4),
                same_cluster=entries[i].cluster_id == entries[j].cluster_id,
            ))

    return similarities


def compute_cluster_quality(
    entries: list[AtlasEntry],
) -> dict[str, float]:
    """Compute clustering quality metrics.

    Returns:
    - label_agreement: fraction of entries where cluster matches state label
    - mean_intra_cluster_dist: mean distance within clusters
    - mean_inter_cluster_dist: mean distance between clusters
    - separation_ratio: inter/intra ratio (higher = better separation)
    """
    if not HAS_SKLEARN:
        raise ImportError(
            "scikit-learn is required for cluster quality metrics. "
            "Install with: pip install statebind[science]"
        )
    X = np.array([e.features.to_vector() for e in entries])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    labels = np.array([e.cluster_id for e in entries])
    [e.state_label.value for e in entries]

    # Label agreement: check if dominant state in each cluster matches entries
    clusters_by_id: dict[int, list] = {}
    for entry in entries:
        clusters_by_id.setdefault(entry.cluster_id, []).append(entry)

    n_agree = 0
    for cid, members in clusters_by_id.items():
        dominant = Counter(e.state_label for e in members).most_common(1)[0][0]
        n_agree += sum(1 for e in members if e.state_label == dominant)
    label_agreement = n_agree / len(entries) if entries else 0.0

    # Intra- and inter-cluster distances
    intra_dists = []
    inter_dists = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            d = float(np.linalg.norm(X_scaled[i] - X_scaled[j]))
            if labels[i] == labels[j]:
                intra_dists.append(d)
            else:
                inter_dists.append(d)

    mean_intra = sum(intra_dists) / len(intra_dists) if intra_dists else 0.0
    mean_inter = sum(inter_dists) / len(inter_dists) if inter_dists else 0.0
    ratio = mean_inter / mean_intra if mean_intra > 0 else 0.0

    return {
        "label_agreement": round(label_agreement, 4),
        "mean_intra_cluster_distance": round(mean_intra, 4),
        "mean_inter_cluster_distance": round(mean_inter, 4),
        "separation_ratio": round(ratio, 4),
    }
