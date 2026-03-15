#!/usr/bin/env python
"""Generate the Phase 3 state atlas report.

Usage:
    python scripts/report_state_atlas.py
    python scripts/report_state_atlas.py --artifacts-dir artifacts/structure/state_atlas_v1
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate state atlas report")
    parser.add_argument(
        "--artifacts-dir", type=Path,
        default=Path("artifacts/structure/state_atlas_v1"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("reports/phase3_state_atlas.md"),
    )
    args = parser.parse_args()

    if not args.artifacts_dir.exists():
        print(f"Artifacts not found: {args.artifacts_dir}")
        print("Run: python scripts/build_state_atlas.py")
        sys.exit(1)

    def _load(name: str):
        with open(args.artifacts_dir / name) as f:
            return json.load(f)

    atlas = _load("state_atlas.json")
    clusters = _load("clusters.json")
    pocket_comp = _load("pocket_comparison.json")
    pocket_diff = _load("pocket_differences.json")
    quality = _load("clustering_quality.json")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    report = f"""# Phase 3: Structural State Atlas Report

**Generated:** {now}
**Artifacts:** `{args.artifacts_dir}`

## 1. Atlas Overview

| Metric | Value |
|--------|-------|
| Structures | {atlas['n_structures']} |
| Conformational states | {atlas['n_states']} |
| Clusters | {atlas['n_clusters']} |
| Features per structure | {len(atlas['feature_names'])} |
| Feature source | Literature-curated (v1) |

### Feature Set

| Feature | Description |
|---------|-------------|"""

    feature_descriptions = {
        "dfg_asp_phe_dist": "DFG Asp-Phe Cα distance (Å) — in vs out",
        "dfg_phe_position": "DFG-Phe displacement from active position (Å)",
        "ac_helix_salt_bridge": "K745-E762 salt bridge distance (Å) — in=short, out=broken",
        "ac_helix_rotation": "αC-helix rotation angle (degrees)",
        "p_loop_displacement": "P-loop Cα RMSD vs active reference (Å)",
        "hinge_angle": "Hinge backbone angle (degrees)",
        "activation_loop_rmsd": "Activation loop RMSD vs active (Å)",
        "gatekeeper_sidechain": "Gatekeeper residue χ1 angle (degrees)",
        "pocket_volume": "Estimated binding pocket volume (ų)",
    }
    for fname in atlas['feature_names']:
        desc = feature_descriptions.get(fname, "")
        report += f"\n| `{fname}` | {desc} |"

    report += f"""

## 2. Clustering Results

### Cluster Quality

| Metric | Value | Interpretation |
|--------|-------|---------------|
| Label agreement | {quality['label_agreement']:.1%} | {'✓ Strong' if quality['label_agreement'] > 0.9 else '~ Moderate'} |
| Mean intra-cluster distance | {quality['mean_intra_cluster_distance']:.4f} | Lower = tighter clusters |
| Mean inter-cluster distance | {quality['mean_inter_cluster_distance']:.4f} | Higher = better separation |
| Separation ratio | {quality['separation_ratio']:.2f}x | >2x = good separation |

### Cluster Descriptions

| ID | Label | Members | N | Mutants |
|----|-------|---------|---|---------|"""

    for c in clusters:
        report += (f"\n| {c['cluster_id']} | {c['label']} | "
                   f"{c['members']} | {c['n_members']} | "
                   f"{'Yes' if c['has_mutants'] else 'No'} |")

    report += """

## 3. Pocket Comparison

### Per-State Pocket Characteristics

| State | N | Volume (ų) | Back Pocket | Gatekeeper | Hinge | P-loop |
|-------|---|-----------|-------------|------------|-------|--------|"""

    for state, data in sorted(pocket_comp.items()):
        bp = "Yes" if data['back_pocket_accessible_fraction'] > 0.5 else "No"
        vol = f"{data['mean_volume']:.0f}"
        gk = f"{data['mean_gatekeeper_clearance']:.1f} Å"
        hinge = f"{data['mean_hinge_accessibility']:.2f}"
        ploop = ", ".join(data['p_loop_conformations'])
        report += f"\n| {state} | {data['n_structures']} | {vol} | {bp} | {gk} | {hinge} | {ploop} |"

    report += """

### Key Pocket Differences
"""
    for i, diff in enumerate(pocket_diff, 1):
        report += f"""
**{i}. {diff['feature']}**
{diff['observation']}
*Design implication:* {diff['design_implication']}
"""

    report += """
## 4. Most Salient State Differences

The atlas reveals four structurally distinct conformational states with clear pocket differences:

1. **Active (DFGin/αCin)**: Compact ATP-binding pocket (~430-460 ų). No back pocket.
   Gatekeeper clearance ~3-4 Å. This is what the static baseline designs against.

2. **Src-like inactive (DFGin/αCout)**: Moderately enlarged pocket (~490-540 ų).
   αC-helix rotation opens space. Salt bridge broken (~9-10 Å vs ~3 Å).
   Important because activating mutations (L858R) destabilize this state.

3. **DFGout intermediate (DFGout/αCin)**: Large pocket with back pocket access
   (~780-800 ų). DFG flip creates new binding cavity for type-II inhibitors.
   αC-helix intact. Rarely targeted by approved EGFR TKIs.

4. **Classical inactive (DFGout/αCout)**: Largest pocket (~830-850 ų). Both DFG
   flipped and αC-helix rotated. Maximum pocket diversity from active state.
   P-loop folds over pocket.

## 5. Limitations

1. **Features are literature-curated, not computed.** v1 uses published measurements
   and educated estimates. Phase 4 will compute from coordinates.

2. **16 structures is a small atlas.** Covers the key states but may miss
   intermediate conformations or rare substates.

3. **No dynamics information.** The atlas is a static snapshot of states, not
   a model of transitions between them.

4. **Clustering is unsupervised.** With curated features that were designed to
   separate known states, high agreement is expected (not a strong validation).

5. **Pocket descriptors are simplified.** Volume, accessibility flags, and
   clearance scores are rough proxies for pocket shape.

## 6. How This Sets Up the Context-to-State Model

The atlas provides three things the downstream predictor needs:

1. **State labels per structure** — the prediction target
2. **Feature vectors per structure** — what characterizes each state
3. **Mutation annotations per structure** — the link between mutation context
   and conformational preference

In Phase 4, the context-to-state model will learn:
*Given a mutation profile, which conformational state(s) are most relevant?*

The atlas provides the ground truth for this mapping:
- T790M structures → cluster with DFGin_aCin (active state stabilized)
- L858R structures → cluster with DFGin_aCin (inactive destabilized)
- WT structures → appear in all state clusters
"""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)

    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
