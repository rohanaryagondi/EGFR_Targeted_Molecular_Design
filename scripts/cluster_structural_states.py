#!/usr/bin/env python
"""Analyze state clustering quality and feature importance.

Usage:
    python scripts/cluster_structural_states.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.structure.atlas import build_state_atlas
from statebind.structure.clustering import compute_cluster_quality


def main() -> None:
    print("Building atlas for clustering analysis...")
    atlas = build_state_atlas(n_clusters=4)

    quality = compute_cluster_quality(atlas.entries)

    print()
    print("=" * 60)
    print("Clustering Quality Analysis")
    print("=" * 60)
    print(f"  Label agreement:        {quality['label_agreement']:.1%}")
    print(f"  Mean intra-cluster:     {quality['mean_intra_cluster_distance']:.4f}")
    print(f"  Mean inter-cluster:     {quality['mean_inter_cluster_distance']:.4f}")
    print(f"  Separation ratio:       {quality['separation_ratio']:.2f}x")
    print()

    if quality['label_agreement'] > 0.9:
        print("  ✓ Clusters agree strongly with literature state labels.")
    elif quality['label_agreement'] > 0.7:
        print("  ~ Clusters partially agree with literature labels.")
    else:
        print("  ✗ Clusters diverge from literature labels — investigate.")

    if quality['separation_ratio'] > 2.0:
        print("  ✓ Good separation between clusters.")
    else:
        print("  ~ Moderate separation — states may overlap in feature space.")

    # Feature statistics per cluster
    print()
    print("=" * 60)
    print("Key Feature Ranges by Cluster")
    print("=" * 60)

    import numpy as np
    feature_names = atlas.feature_names
    for c in atlas.clusters:
        members = [e for e in atlas.entries if e.cluster_id == c.cluster_id]
        vectors = np.array([e.features.to_vector() for e in members])
        print(f"\n  Cluster {c.cluster_id}: {c.label}")
        for i, fname in enumerate(feature_names):
            vals = vectors[:, i]
            print(f"    {fname:<25} {vals.mean():8.2f} ± {vals.std():6.2f}  "
                  f"[{vals.min():7.2f}, {vals.max():7.2f}]")


if __name__ == "__main__":
    main()
