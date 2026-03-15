#!/usr/bin/env python3
"""Generate state-conditioned molecular candidates.

Produces candidate libraries for all 4 EGFR conformational states,
with pocket-aware modification strategies.

Usage:
    python scripts/generate_state_conditioned_candidates.py
"""

import json
from pathlib import Path

from statebind.generation.generator import generate_all_states
from statebind.utils.io import save_json

ARTIFACT_DIR = Path("artifacts/generation/candidates_v1")


def main() -> None:
    print("=" * 60)
    print("State-Conditioned Candidate Generation")
    print("=" * 60)

    result = generate_all_states()

    print(f"\nStates: {result.states}")
    print(f"Total candidates: {result.total_candidates}")
    print(f"Total unique SMILES: {result.total_unique_smiles}")

    for lib in result.libraries:
        print(f"\n--- {lib.state} ---")
        print(f"  Representative PDB: {lib.representative_pdb}")
        print(f"  Pocket volume: {lib.pocket_volume:.0f} ų")
        print(f"  Back pocket: {'Yes' if lib.back_pocket_accessible else 'No'}")
        print(f"  Candidates: {lib.n_candidates}")
        print(f"  Strategies: {', '.join(lib.strategies_used)}")

        # Strategy breakdown
        from collections import Counter
        strat_counts: Counter[str] = Counter()
        for c in lib.candidates:
            strat_counts[c.strategy.value] += 1
        for strat, count in strat_counts.most_common():
            print(f"    {strat}: {count}")

    print(f"\n--- Cross-State Overlap ---")
    for pair, count in sorted(result.cross_state_overlap.items()):
        s1, s2 = pair.split("|")
        s1_short = s1.replace("DFG", "")
        s2_short = s2.replace("DFG", "")
        print(f"  {s1_short} ∩ {s2_short}: {count} shared")

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    # Per-state candidate lists
    for lib in result.libraries:
        state_dir = ARTIFACT_DIR / lib.state
        state_dir.mkdir(parents=True, exist_ok=True)
        save_json(
            {
                "state": lib.state,
                "representative_pdb": lib.representative_pdb,
                "pocket_volume": lib.pocket_volume,
                "back_pocket": lib.back_pocket_accessible,
                "n_candidates": lib.n_candidates,
                "strategies": lib.strategies_used,
                "candidates": [
                    {
                        "id": c.candidate_id,
                        "smiles": c.smiles,
                        "strategy": c.strategy.value,
                        "parent_id": c.parent_id,
                        "notes": c.notes,
                    }
                    for c in lib.candidates
                ],
            },
            state_dir / "candidates.json",
        )

    # Summary
    save_json(
        {
            "states": result.states,
            "total_candidates": result.total_candidates,
            "total_unique_smiles": result.total_unique_smiles,
            "cross_state_overlap": result.cross_state_overlap,
            "per_state": [
                {
                    "state": lib.state,
                    "n_candidates": lib.n_candidates,
                    "strategies": lib.strategies_used,
                }
                for lib in result.libraries
            ],
        },
        ARTIFACT_DIR / "generation_summary.json",
    )

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
