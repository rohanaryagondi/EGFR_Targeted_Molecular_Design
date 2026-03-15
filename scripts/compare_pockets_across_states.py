#!/usr/bin/env python
"""Compare binding pockets across conformational states.

Usage:
    python scripts/compare_pockets_across_states.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.structure.atlas import build_state_atlas
from statebind.structure.pocket_comparison import (
    compare_pockets_by_state,
    identify_pocket_differences,
)


def main() -> None:
    print("Building atlas for pocket comparison...")
    atlas = build_state_atlas(n_clusters=4)

    comparison = compare_pockets_by_state(atlas.entries)
    differences = identify_pocket_differences(comparison)

    print()
    print("=" * 60)
    print("Pocket Comparison Across Conformational States")
    print("=" * 60)

    for state, data in sorted(comparison.items()):
        print(f"\n  {state} (n={data['n_structures']})")
        print(f"    Volume:           {data['mean_volume']:.0f} ų "
              f"[{data['volume_range'][0]:.0f}–{data['volume_range'][1]:.0f}]")
        print(f"    Back pocket:      {'Yes' if data['back_pocket_accessible_fraction'] > 0.5 else 'No'}")
        print(f"    Gatekeeper gap:   {data['mean_gatekeeper_clearance']:.1f} Å")
        print(f"    Hinge access:     {data['mean_hinge_accessibility']:.2f}")
        print(f"    Covalent C797:    {'Exposed' if data['covalent_cys_exposed_fraction'] > 0.5 else 'Variable'}")
        print(f"    P-loop:           {', '.join(data['p_loop_conformations'])}")
        print(f"    Representative:   {data['representative_pdb']}")

    print()
    print("=" * 60)
    print("Key Pocket Differences (Drug Design Implications)")
    print("=" * 60)

    for i, diff in enumerate(differences, 1):
        print(f"\n  {i}. {diff['feature']}")
        print(f"     {diff['observation']}")
        print(f"     → {diff['design_implication']}")


if __name__ == "__main__":
    main()
