#!/usr/bin/env python
"""Build the EGFR conformational state atlas.

Usage:
    python scripts/build_state_atlas.py
    python scripts/build_state_atlas.py --output-dir artifacts/structure/state_atlas_v1
    python scripts/build_state_atlas.py --n-clusters 4
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.structure.atlas import build_state_atlas


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EGFR state atlas")
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/structure/state_atlas_v1"),
    )
    parser.add_argument("--n-clusters", type=int, default=4)
    args = parser.parse_args()

    print("=" * 60)
    print("StateBind — EGFR Conformational State Atlas")
    print("=" * 60)
    print()

    atlas = build_state_atlas(
        n_clusters=args.n_clusters,
        output_dir=args.output_dir,
    )

    print()
    print("=" * 60)
    print("Atlas Summary")
    print("=" * 60)
    print(f"  Structures:  {atlas.n_structures}")
    print(f"  States:      {atlas.n_states}")
    print(f"  Clusters:    {atlas.n_clusters}")
    print()

    print("Clusters:")
    for c in atlas.clusters:
        print(f"  [{c.cluster_id}] {c.label}")
        print(f"      Members: {', '.join(c.member_pdb_ids)}")
        print(f"      Size: {c.n_members}, Mutants: {c.has_mutant_structures}")
    print()


if __name__ == "__main__":
    main()
