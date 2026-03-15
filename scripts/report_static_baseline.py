#!/usr/bin/env python
"""Generate the Phase 2 static baseline report.

Reads artifacts from a baseline run and writes reports/phase2_static_baseline.md.

Usage:
    python scripts/report_static_baseline.py
    python scripts/report_static_baseline.py --artifacts-dir artifacts/baselines/static_v1
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static baseline report")
    parser.add_argument(
        "--artifacts-dir", type=Path,
        default=Path("artifacts/baselines/static_v1"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("reports/phase2_static_baseline.md"),
    )
    args = parser.parse_args()

    if not args.artifacts_dir.exists():
        print(f"Artifacts not found: {args.artifacts_dir}")
        print("Run: python scripts/run_static_baseline.py")
        sys.exit(1)

    # Load artifacts
    def _load(name: str) -> dict:
        with open(args.artifacts_dir / name) as f:
            return json.load(f)

    structure = _load("structure_selection.json")
    pocket = _load("pocket_definition.json")
    library = _load("candidate_library.json")
    filtered = _load("filtered_library.json")
    ranked = _load("ranked_candidates.json")
    evaluation = _load("evaluation.json")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    report = f"""# Phase 2: Static Baseline Report

**Generated:** {now}
**Pipeline:** static_baseline
**Artifacts:** `{args.artifacts_dir}`

## 1. Structure Selected

| Property | Value |
|----------|-------|
| PDB ID | {structure['pdb_id']} |
| Chain | {structure['chain']} |
| Conformational State | {structure['state']} |
| Resolution | {structure['resolution']} Å |
| Co-crystal Ligand | {structure['ligand']} |
| Mutations | {', '.join(structure['mutations']) or 'Wild-type'} |

**Rationale:** {structure['rationale']}

## 2. Pocket Definition

| Property | Value |
|----------|-------|
| Pocket ID | {pocket['pocket_id']} |
| Type | {pocket['pocket_type']} |
| Source | {pocket['source']} |
| Residues | {len(pocket['residues'])} |

The pocket is defined by known EGFR ATP-binding site residues from literature.
It is NOT derived from geometric pocket detection or conformational analysis.

## 3. Candidate Library

| Metric | Count |
|--------|-------|
| Total candidates | {library.get('candidates', []).__len__() if isinstance(library.get('candidates'), list) else len(library.get('candidates', []))} |
| Reference compounds | {sum(1 for c in library.get('candidates', []) if c.get('source') == 'reference')} |
| Enumerated analogs | {sum(1 for c in library.get('candidates', []) if c.get('source') == 'enumerated')} |

## 4. Filtering Summary

| Metric | Count |
|--------|-------|
| Input candidates | {filtered['n_input']} |
| Passed filters | {filtered['n_passed']} |
| Failed filters | {filtered['n_failed']} |
| Pass rate | {filtered['n_passed']/max(filtered['n_input'],1)*100:.1f}% |

### Filters applied:
"""
    for f in filtered.get("filters_applied", []):
        min_v = f.get("min_value", "—")
        max_v = f.get("max_value", "—")
        report += f"- **{f['property_name']}**: [{min_v}, {max_v}]\n"

    report += f"""
## 5. Ranking Summary

| Metric | Value |
|--------|-------|
| Candidates ranked | {ranked.get('candidates', []).__len__()} |
| Scoring method | {ranked.get('scoring_method', '').split('.')[0]} |

### Top 10 Candidates

| Rank | ID | Composite Score | Similarity | Drug-likeness | Docking |
|------|----|----------------|------------|---------------|---------|"""

    for c in ranked.get("candidates", [])[:10]:
        scores = {s["name"]: s["value"] for s in c.get("scores", [])}
        report += (
            f"\n| {c['rank']} | {c['candidate_id'][:20]} | "
            f"{c['composite_score']:.4f} | "
            f"{scores.get('reference_similarity', 0):.4f} | "
            f"{scores.get('druglikeness', 0):.4f} | "
            f"{scores.get('docking_proxy', 0):.4f} |"
        )

    report += f"""

## 6. Evaluation Metrics

| Metric | Value |
|--------|-------|
| Validity rate | {evaluation.get('validity_rate', 0):.1%} |
| Uniqueness rate | {evaluation.get('uniqueness_rate', 0):.1%} |
| Diversity score | {evaluation.get('diversity_score', 0):.4f} |

### Score Distributions
"""
    for name, stats in evaluation.get("score_stats", {}).items():
        report += (
            f"- **{name}**: mean={stats['mean']:.4f}, "
            f"std={stats['std']:.4f}, "
            f"range=[{stats['min']:.4f}, {stats['max']:.4f}]\n"
        )

    report += """
## 7. Limitations

This baseline has **deliberate limitations** that define what state-aware design addresses:

1. **Single structure.** Uses only 1M17 (WT, active conformation). Does not consider
   inactive states that resistance mutations may stabilize.

2. **Static pocket.** Literature-derived residue list. Does not adapt to conformational
   changes in DFG motif, αC-helix, or P-loop.

3. **No mutation awareness.** The same pocket and scoring applies regardless of which
   EGFR mutation is present.

4. **Stub docking.** The docking score is a constant placeholder (0.5). It provides
   NO discriminative power. Must be replaced with Vina/GNINA for real benchmarking.

5. **Heuristic properties.** MW, HBA, HBD estimated from SMILES patterns, not
   computed with RDKit.

6. **SMILES-based similarity.** Uses character n-grams, not molecular fingerprints.
   Captures surface-level similarity only.

## 8. What This Does NOT Capture

| What's Missing | Why It Matters |
|----------------|---------------|
| Conformational state awareness | T790M stabilizes DFGin; designing only against DFGin misses DFGout opportunities |
| Mutation-specific pocket changes | C797S eliminates covalent binding; pocket shape differs in mutant structures |
| State-selective scoring | A compound may score well against active state but poorly against the state a resistant mutant actually occupies |
| Ensemble-based evaluation | Real targets exist in multiple states; single-structure scoring is overconfident |

## 9. What This Baseline CAN Prove

- That the pipeline infrastructure works end-to-end
- That scoring, filtering, and ranking produce sensible outputs
- That known drugs rank near the top (sanity check)
- That there IS a baseline number the state-aware system must exceed

## 10. Next Steps

1. **Replace docking stub** with AutoDock Vina or GNINA
2. **Replace SMILES similarity** with Morgan/ECFP fingerprints via RDKit
3. **Build state-aware pipeline** that uses the conformational state atlas
4. **Compare** state-aware vs. static baseline on the same candidate set
"""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)

    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
