#!/usr/bin/env python3
"""Build the state transition dataset from literature-curated sequences.

Constructs pseudo-trajectories encoding expert knowledge about EGFR
conformational dynamics. NOT MD simulation data.

Usage:
    python scripts/build_state_sequences.py
"""

import json
from pathlib import Path

from statebind.dynamics.sequences import build_transition_dataset

ARTIFACT_DIR = Path("artifacts/dynamics/sequences_v1")


def main() -> None:
    print("=" * 60)
    print("Building State Transition Dataset")
    print("=" * 60)

    dataset = build_transition_dataset()

    print(f"\nSequences: {dataset.n_sequences}")
    print(f"Transitions: {dataset.n_transitions}")
    print(f"States: {dataset.states}")

    print("\n--- Sequences ---")
    for seq in dataset.sequences:
        syn_tag = " [SYNTHETIC]" if seq.is_synthetic else ""
        print(f"  {seq.sequence_id}{syn_tag}")
        print(f"    {' → '.join(seq.states)}")
        print(f"    {seq.description}")

    # Transition counts
    from collections import Counter
    counts: Counter[tuple[str, str]] = Counter()
    for t in dataset.transitions:
        counts[(t.from_state, t.to_state)] += 1

    print("\n--- Transition Counts ---")
    for (f, t), c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {f} → {t}: {c}")

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    with open(ARTIFACT_DIR / "sequences.json", "w") as f:
        json.dump([
            {
                "id": s.sequence_id,
                "states": s.states,
                "description": s.description,
                "provenance": s.provenance,
                "context": s.context,
                "is_synthetic": s.is_synthetic,
            }
            for s in dataset.sequences
        ], f, indent=2)

    with open(ARTIFACT_DIR / "transitions.json", "w") as f:
        json.dump([
            {
                "from": t.from_state,
                "to": t.to_state,
                "context": t.context,
                "evidence_type": t.evidence_type,
            }
            for t in dataset.transitions
        ], f, indent=2)

    with open(ARTIFACT_DIR / "transition_counts.json", "w") as f:
        json.dump({f"{k[0]}|{k[1]}": v for k, v in counts.items()}, f, indent=2)

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
