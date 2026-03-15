"""Cross-state pocket comparison.

Compares how the EGFR binding pocket differs across conformational states.
This is the structural basis for why state-aware design matters:
different states present different pockets.
"""

from __future__ import annotations

from collections import defaultdict

from statebind.processing.models import ConformationalState
from statebind.structure.models import AtlasEntry, PocketDescriptor


def compare_pockets_by_state(
    entries: list[AtlasEntry],
) -> dict[str, dict]:
    """Compare pocket descriptors across conformational states.

    Groups entries by state label and computes per-state pocket statistics.

    Returns:
        Dict mapping state label → pocket summary statistics.
    """
    by_state: dict[str, list[AtlasEntry]] = defaultdict(list)
    for e in entries:
        by_state[e.state_label.value].append(e)

    comparison = {}
    for state, members in sorted(by_state.items()):
        volumes = [e.pocket.pocket_volume for e in members]
        clearances = [e.pocket.gatekeeper_clearance for e in members]
        hinge_scores = [e.pocket.hinge_accessibility for e in members]
        n_back_pocket = sum(1 for e in members if e.pocket.back_pocket_accessible)
        n_covalent = sum(1 for e in members if e.pocket.covalent_cys_exposed)
        p_loop_types = [e.pocket.p_loop_conformation for e in members]

        comparison[state] = {
            "n_structures": len(members),
            "mean_volume": round(_mean(volumes), 1),
            "volume_range": [round(min(volumes), 1), round(max(volumes), 1)],
            "mean_gatekeeper_clearance": round(_mean(clearances), 2),
            "mean_hinge_accessibility": round(_mean(hinge_scores), 2),
            "back_pocket_accessible_fraction": round(n_back_pocket / len(members), 2),
            "covalent_cys_exposed_fraction": round(n_covalent / len(members), 2),
            "p_loop_conformations": list(set(p_loop_types)),
            "representative_pdb": next(
                (e.pdb_id for e in members if e.is_representative),
                members[0].pdb_id,
            ),
        }

    return comparison


def identify_pocket_differences(
    comparison: dict[str, dict],
) -> list[dict]:
    """Identify the most salient pocket differences between states.

    Returns a list of observations about what changes between states,
    ordered by relevance to drug design.
    """
    differences = []

    states = sorted(comparison.keys())
    if len(states) < 2:
        return [{"observation": "Only one state — no comparison possible"}]

    # 1. Volume differences
    volumes = {s: d["mean_volume"] for s, d in comparison.items()}
    vol_range = max(volumes.values()) - min(volumes.values())
    if vol_range > 100:
        smallest = min(volumes, key=volumes.get)
        largest = max(volumes, key=volumes.get)
        differences.append({
            "feature": "pocket_volume",
            "observation": (
                f"Pocket volume varies {vol_range:.0f} ų across states. "
                f"Smallest: {smallest} ({volumes[smallest]:.0f} ų), "
                f"largest: {largest} ({volumes[largest]:.0f} ų)."
            ),
            "design_implication": (
                "Larger pockets (DFG-out states) accommodate type-II inhibitors. "
                "Designing only against the smaller active-state pocket misses "
                "these opportunities."
            ),
            "magnitude": vol_range,
        })

    # 2. Back pocket accessibility
    back_pocket = {s: d["back_pocket_accessible_fraction"] for s, d in comparison.items()}
    if any(v > 0 for v in back_pocket.values()) and any(v == 0 for v in back_pocket.values()):
        open_states = [s for s, v in back_pocket.items() if v > 0.5]
        closed_states = [s for s, v in back_pocket.items() if v < 0.5]
        differences.append({
            "feature": "back_pocket",
            "observation": (
                f"Back pocket accessible in {', '.join(open_states)} "
                f"but not in {', '.join(closed_states)}."
            ),
            "design_implication": (
                "Type-II inhibitors require the DFG-out back pocket. "
                "Static design against an active-state structure would never "
                "find type-II binding opportunities."
            ),
            "magnitude": 1.0,
        })

    # 3. Gatekeeper clearance
    clearances = {s: d["mean_gatekeeper_clearance"] for s, d in comparison.items()}
    clearance_range = max(clearances.values()) - min(clearances.values())
    if clearance_range > 0.5:
        differences.append({
            "feature": "gatekeeper_clearance",
            "observation": (
                f"Gatekeeper clearance varies by {clearance_range:.1f} Å. "
                f"Critical for T790M gatekeeper mutation."
            ),
            "design_implication": (
                "T790M reduces gatekeeper clearance. State-aware design can "
                "target states where the mutation has less impact on pocket access."
            ),
            "magnitude": clearance_range,
        })

    # 4. Hinge accessibility
    hinge = {s: d["mean_hinge_accessibility"] for s, d in comparison.items()}
    hinge_range = max(hinge.values()) - min(hinge.values())
    if hinge_range > 0.1:
        differences.append({
            "feature": "hinge_accessibility",
            "observation": (
                f"Hinge accessibility varies from "
                f"{min(hinge.values()):.2f} to {max(hinge.values()):.2f}."
            ),
            "design_implication": (
                "Hinge H-bonds are critical for TKI binding. States with "
                "reduced hinge access may require different binding strategies."
            ),
            "magnitude": hinge_range,
        })

    # Sort by magnitude
    differences.sort(key=lambda d: d.get("magnitude", 0), reverse=True)

    return differences


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
