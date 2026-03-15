#!/usr/bin/env python3
"""Generate Phase 6 report: state-conditioned generation.

Usage:
    python scripts/report_generation_results.py
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from statebind.baselines.pipeline import run_static_baseline
from statebind.generation.diversity import analyze_cross_state_diversity
from statebind.generation.evaluation import (
    compare_with_static_baseline,
    evaluate_generation,
)
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states

REPORT_PATH = Path("reports/phase6_generation.md")


def main() -> None:
    print("Generating Phase 6 report...")

    generation = generate_all_states()
    filtered = filter_all_states(generation)
    diversity = analyze_cross_state_diversity(filtered)
    evaluation = evaluate_generation(generation, filtered, diversity)

    # Static baseline comparison
    with tempfile.TemporaryDirectory() as tmpdir:
        static_result = run_static_baseline(Path(tmpdir))
        static_smiles = {c.smiles for c in static_result.ranked.candidates}
    comparison = compare_with_static_baseline(filtered, static_smiles)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = []
    lines.append("# Phase 6: State-Conditioned Generation Report")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append("**Artifacts:** `artifacts/generation/candidates_v1`, `artifacts/generation/filtered_v1`")
    lines.append("")

    # 1. Overview
    lines.append("## 1. Overview")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| States | {len(generation.states)} |")
    lines.append(f"| Total generated | {generation.total_candidates} |")
    lines.append(f"| Total after filtering | {filtered.total_passed} |")
    lines.append(f"| Filter pass rate | {filtered.overall_pass_rate:.1%} |")
    lines.append(f"| Total unique SMILES | {generation.total_unique_smiles} |")
    lines.append(f"| Global diversity | {diversity.global_diversity.diversity_score:.3f} |")
    lines.append("")

    # 2. Per-state generation
    lines.append("## 2. Candidates Per State")
    lines.append("")
    lines.append("| State | PDB | Volume | Generated | Filtered | Pass Rate | Diversity | Unique |")
    lines.append("|-------|-----|--------|-----------|----------|-----------|-----------|--------|")
    for se, gl, fl, dr in zip(evaluation.per_state, generation.libraries,
                               filtered.libraries, diversity.per_state):
        lines.append(
            f"| {se.state} | {gl.representative_pdb} | {gl.pocket_volume:.0f} ų | "
            f"{se.n_generated} | {se.n_filtered} | {se.filter_pass_rate:.1%} | "
            f"{se.diversity_score:.3f} | {dr.n_state_unique} ({dr.unique_fraction:.0%}) |"
        )
    lines.append("")

    # 3. Strategies per state
    lines.append("## 3. Generation Strategies")
    lines.append("")
    for lib in generation.libraries:
        lines.append(f"### {lib.state}")
        lines.append(f"Pocket: {lib.pocket_volume:.0f} ų, "
                     f"back pocket: {'yes' if lib.back_pocket_accessible else 'no'}")
        lines.append(f"Strategies: {', '.join(lib.strategies_used)}")
        lines.append("")
        from collections import Counter
        strats: Counter[str] = Counter()
        for c in lib.candidates:
            strats[c.strategy.value] += 1
        for s, n in strats.most_common():
            lines.append(f"- {s}: {n} candidates")
        lines.append("")

    # 4. Filtering
    lines.append("## 4. Filtering Statistics")
    lines.append("")
    lines.append("DFGin states use standard Lipinski-like filters (MW 200-600).")
    lines.append("DFGout states use relaxed filters (MW 250-800) for type-II inhibitors.")
    lines.append("")
    for fl in filtered.libraries:
        lines.append(f"**{fl.state}**: {fl.n_passed}/{fl.n_input} passed ({fl.pass_rate:.1%})")
        mw = fl.property_stats.get("estimated_mw", {})
        if mw:
            lines.append(f"  MW: {mw.get('min',0):.0f}–{mw.get('max',0):.0f} (mean {mw.get('mean',0):.0f})")
        lines.append("")

    # 5. Diversity
    lines.append("## 5. Diversity Analysis")
    lines.append("")
    lines.append("### Intra-state diversity")
    lines.append("")
    lines.append("| State | Diversity (1-Tanimoto) | Unique to this state |")
    lines.append("|-------|-----------------------|---------------------|")
    for dr in diversity.per_state:
        lines.append(f"| {dr.state} | {dr.intra_diversity.diversity_score:.3f} | "
                     f"{dr.n_state_unique} ({dr.unique_fraction:.0%}) |")
    lines.append("")

    lines.append("### Cross-state overlap")
    lines.append("")
    lines.append("| State pair | Shared candidates |")
    lines.append("|-----------|-------------------|")
    for pair, count in sorted(diversity.overlap_matrix.items()):
        lines.append(f"| {pair.replace('|', ' ∩ ')} | {count} |")
    lines.append("")

    # 6. Static baseline comparison
    lines.append("## 6. Comparison with Static Baseline")
    lines.append("")
    lines.append("| Metric | Static (Phase 2) | State-Conditioned (Phase 6) |")
    lines.append("|--------|-----------------|---------------------------|")
    lines.append(f"| Total candidates | {comparison.static_n_candidates} | "
                 f"{comparison.state_conditioned_n_candidates} |")
    lines.append(f"| Diversity | {comparison.diversity_static:.3f} | "
                 f"{comparison.diversity_state_conditioned:.3f} |")
    lines.append(f"| Overlap | {comparison.overlap_with_static} shared |  |")
    lines.append(f"| Phase 6 only (new) | — | {comparison.state_only_candidates} |")
    lines.append(f"| Phase 2 only (missed) | {comparison.static_only_candidates} | — |")
    lines.append("")

    lines.append("### Interpretation")
    lines.append("")
    if comparison.state_only_candidates > 0:
        lines.append(f"State-conditioned generation produces **{comparison.state_only_candidates} "
                     f"new candidates** not found in the static baseline. These arise from "
                     f"pocket-specific strategies (back pocket extensions, volume filling, "
                     f"P-loop interactions) that are invisible to single-structure design.")
    lines.append("")
    if comparison.diversity_state_conditioned > comparison.diversity_static:
        lines.append(f"Chemical diversity increases from {comparison.diversity_static:.3f} "
                     f"to {comparison.diversity_state_conditioned:.3f}, confirming that "
                     f"multi-state generation explores a broader chemical space.")
    lines.append("")

    # 7. Qualitative notes
    lines.append("## 7. State Specificity Notes")
    lines.append("")
    lines.append("1. **DFGin_aCin (active)**: Hinge-optimized and gatekeeper-avoiding "
                 "modifications dominate. Compact molecules for the smallest pocket.")
    lines.append("2. **DFGin_aCout (Src-like)**: Volume-filling begins. Moderate extensions "
                 "to fill αC-helix cavity.")
    lines.append("3. **DFGout_aCin**: Back pocket extensions appear (CF3 tails, amide linkers). "
                 "These type-II motifs are unique to DFG-out states.")
    lines.append("4. **DFGout_aCout**: Largest and most diverse set. P-loop interaction "
                 "strategies appear. Back pocket + volume filling combine for the "
                 "largest candidate molecules.")
    lines.append("")

    # 8. Limitations
    lines.append("## 8. Limitations")
    lines.append("")
    lines.append("1. **SMILES-level modifications only.** No 3D docking or force-field evaluation.")
    lines.append("2. **Transformations are rule-based.** Back pocket extensions are appended, "
                 "not designed de novo for the specific pocket geometry.")
    lines.append("3. **No synthesizability check.** Some generated SMILES may be synthetically "
                 "challenging or chemically unstable.")
    lines.append("4. **Property estimation is approximate.** MW, HBA/HBD counts use SMILES "
                 "heuristics, not exact molecular calculations.")
    lines.append("5. **Small reference set.** Only 8 reference compounds seed the generation. "
                 "A larger seed set would produce more diverse candidates.")
    lines.append("")

    # Write
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"Report written to {REPORT_PATH}")
    print("Done.")


if __name__ == "__main__":
    main()
