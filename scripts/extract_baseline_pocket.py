#!/usr/bin/env python
"""Extract the pocket definition for the static baseline.

Usage:
    python scripts/extract_baseline_pocket.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.baselines.pocket import get_baseline_pocket


def main() -> None:
    pocket = get_baseline_pocket()

    print("Static Baseline Pocket Definition")
    print("=" * 50)
    print(f"Pocket ID:   {pocket.pocket_id}")
    print(f"PDB ID:      {pocket.pdb_id}")
    print(f"Chain:       {pocket.chain}")
    print(f"Type:        {pocket.pocket_type}")
    print(f"Source:      {pocket.source}")
    print(f"Residues:    {len(pocket.residues)}")
    print()

    # Group by role
    roles: dict[str, list] = {}
    for r in pocket.residues:
        roles.setdefault(r.role, []).append(r)

    print("Residues by structural role:")
    for role, residues in sorted(roles.items()):
        res_str = ", ".join(f"{r.residue_name}{r.residue_number}" for r in residues)
        print(f"  {role:<25} {res_str}")

    print()
    print(f"Notes: {pocket.notes}")


if __name__ == "__main__":
    main()
