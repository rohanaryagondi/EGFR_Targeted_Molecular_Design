#!/usr/bin/env python
"""Select the structure for the static baseline.

Usage:
    python scripts/select_baseline_structure.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.baselines.pocket import select_baseline_structure


def main() -> None:
    meta = select_baseline_structure()

    print("Static Baseline Structure Selection")
    print("=" * 50)
    print(f"PDB ID:      {meta['pdb_id']}")
    print(f"Chain:       {meta['chain']}")
    print(f"State:       {meta['state']}")
    print(f"Resolution:  {meta['resolution']} Å")
    print(f"Ligand:      {meta['ligand']}")
    print(f"Mutations:   {meta['mutations'] or 'Wild-type'}")
    print()
    print(f"Rationale: {meta['rationale']}")
    print()
    print("What this misses (by design):")
    for item in meta["what_this_misses"]:
        print(f"  ✗ {item}")


if __name__ == "__main__":
    main()
