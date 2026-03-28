"""Figure generation for the comparative evaluation.

Generates text-based (ASCII) figures for maximum portability.
These can be embedded directly in markdown reports without
requiring matplotlib or any graphics library.

If matplotlib is available, also generates PNG plots.
"""

from __future__ import annotations

from pathlib import Path

from statebind.evaluation.comparison import ComparativeResult
from statebind.ranking.models import MergedRanking, PipelineLabel


def _bar(value: float, max_value: float, width: int = 40) -> str:
    """Render a single ASCII bar."""
    if max_value <= 0:
        return ""
    filled = int(round(value / max_value * width))
    return "\u2588" * filled + "\u2591" * (width - filled)


def score_distribution_ascii(result: ComparativeResult) -> str:
    """ASCII histogram comparing score distributions."""
    lines = ["## Score Distribution Comparison", ""]

    static_stats = result.scores.static_stats
    state_stats = result.scores.state_aware_stats

    max_score = max(
        static_stats.get("max", 0),
        state_stats.get("max", 0),
        0.01,
    )

    lines.append(f"  Static baseline  mean={static_stats.get('mean', 0):.4f}  "
                 f"std={static_stats.get('std', 0):.4f}  "
                 f"[{static_stats.get('min', 0):.3f}, {static_stats.get('max', 0):.3f}]")
    lines.append(f"    Mean  {_bar(static_stats.get('mean', 0), max_score, 40)} {static_stats.get('mean', 0):.4f}")
    lines.append(f"    Max   {_bar(static_stats.get('max', 0), max_score, 40)} {static_stats.get('max', 0):.4f}")
    lines.append("")
    lines.append(f"  State-aware      mean={state_stats.get('mean', 0):.4f}  "
                 f"std={state_stats.get('std', 0):.4f}  "
                 f"[{state_stats.get('min', 0):.3f}, {state_stats.get('max', 0):.3f}]")
    lines.append(f"    Mean  {_bar(state_stats.get('mean', 0), max_score, 40)} {state_stats.get('mean', 0):.4f}")
    lines.append(f"    Max   {_bar(state_stats.get('max', 0), max_score, 40)} {state_stats.get('max', 0):.4f}")
    lines.append("")
    lines.append(f"  Delta mean: {result.scores.delta_mean:+.4f}")

    return "\n".join(lines)


def diversity_comparison_ascii(result: ComparativeResult) -> str:
    """ASCII bar chart comparing diversity."""
    lines = ["## Diversity Comparison", ""]

    s_div = result.diversity.static.diversity_score
    a_div = result.diversity.state_aware.diversity_score
    max_div = max(s_div, a_div, 0.01)

    lines.append(f"  Static     {_bar(s_div, max_div, 40)} {s_div:.4f}")
    lines.append(f"  State-aw.  {_bar(a_div, max_div, 40)} {a_div:.4f}")
    lines.append(f"  Delta: {result.diversity.delta_diversity:+.4f}")

    return "\n".join(lines)


def top_k_composition_ascii(result: ComparativeResult) -> str:
    """ASCII chart showing pipeline composition of top-K."""
    k = result.top_k.k
    s_count = result.top_k.static_count
    a_count = result.top_k.state_aware_count

    lines = [f"## Global Top-{k} Composition", ""]
    lines.append(f"  Static      {'S' * s_count}{'.' * (k - s_count)}  {s_count}/{k}")
    lines.append(f"  State-aware {'A' * a_count}{'.' * (k - a_count)}  {a_count}/{k}")

    return "\n".join(lines)


def novelty_breakdown_ascii(result: ComparativeResult) -> str:
    """ASCII breakdown of novel candidates by strategy."""
    lines = ["## Novel Candidates by Strategy", ""]

    if not result.novelty.novel_strategies:
        lines.append("  No novel candidates.")
        return "\n".join(lines)

    max_count = max(result.novelty.novel_strategies.values())
    for strategy, count in sorted(
        result.novelty.novel_strategies.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        lines.append(f"  {strategy:<25} {_bar(count, max_count, 30)} {count}")

    lines.append(f"\n  Total novel: {result.novelty.n_novel}")

    return "\n".join(lines)


def overlap_venn_ascii(result: ComparativeResult) -> str:
    """Text-based Venn diagram of SMILES overlap."""
    o = result.overlap
    lines = ["## SMILES Overlap", ""]
    lines.append(f"  Static only: {o.static_only}")
    lines.append(f"  Shared:      {o.shared}")
    lines.append(f"  State only:  {o.state_aware_only}")
    lines.append(f"  Jaccard:     {o.jaccard:.4f}")
    lines.append("")
    lines.append(f"  [Static {o.static_only}]--({o.shared})--[State-aware {o.state_aware_only}]")

    return "\n".join(lines)


def statistical_summary_ascii(result: ComparativeResult) -> str:
    """ASCII visualization of statistical test results."""
    lines = ["## Statistical Tests", ""]

    if not result.statistical_tests:
        lines.append("  No statistical tests have been run.")
        return "\n".join(lines)

    for test in result.statistical_tests:
        lines.append(f"  {test.name}")
        # p-value bar (lower = more significant, invert for visual)
        p_bar = _bar(max(1.0 - test.p_value, 0.0), 1.0, 30)
        lines.append(f"    p-value:     {p_bar} {test.p_value:.4f}")
        lines.append(f"    Effect size: {test.effect_size:+.4f}")
        lines.append(f"    95% CI:      [{test.ci_lower:.4f}, {test.ci_upper:.4f}]")
        lines.append(f"    {test.interpretation}")
        lines.append("")

    return "\n".join(lines)


def sensitivity_heatmap_ascii(result: ComparativeResult) -> str:
    """ASCII visualization of weight sensitivity results."""
    from statebind.evaluation.sensitivity import SensitivitySummary

    lines = ["## Weight Sensitivity", ""]

    if not isinstance(result.sensitivity, SensitivitySummary):
        lines.append("  No sensitivity analysis has been run.")
        return "\n".join(lines)

    summary = result.sensitivity
    total = max(summary.n_configs, 1)

    lines.append(f"  {summary.n_configs} random weight configurations tested")
    lines.append("")
    lines.append(f"  State-aware wins  {_bar(summary.state_aware_wins, total, 30)} "
                 f"{summary.state_aware_wins}/{total} ({summary.state_aware_win_fraction:.1%})")
    lines.append(f"  Static wins       {_bar(summary.static_wins, total, 30)} "
                 f"{summary.static_wins}/{total} ({summary.static_wins / total:.1%})")
    lines.append(f"  Ties              {_bar(summary.ties, total, 30)} "
                 f"{summary.ties}/{total} ({summary.ties / total:.1%})")

    return "\n".join(lines)


def generate_all_figures(
    result: ComparativeResult,
    merged: MergedRanking,
    output_dir: Path | None = None,
    generate_plots: bool = False,
) -> dict[str, str | Path]:
    """Generate all ASCII figures. Optionally write to files.

    When *generate_plots* is True and *output_dir* is not None,
    also generates matplotlib PNG plots (if matplotlib is available)
    and includes their paths in the returned dict under ``plot_``
    prefixed keys.

    Returns:
        Dict mapping figure name to ASCII content (str) or plot
        file path (Path, only when *generate_plots* is True).
    """
    figures = {
        "score_distribution": score_distribution_ascii(result),
        "diversity_comparison": diversity_comparison_ascii(result),
        "top_k_composition": top_k_composition_ascii(result),
        "novelty_breakdown": novelty_breakdown_ascii(result),
        "overlap_venn": overlap_venn_ascii(result),
    }

    # Conditionally include statistical figures (preserves backward compat)
    if result.statistical_tests:
        figures["statistical_summary"] = statistical_summary_ascii(result)
    if result.sensitivity is not None:
        figures["sensitivity_heatmap"] = sensitivity_heatmap_ascii(result)

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in figures.items():
            with open(output_dir / f"{name}.txt", "w") as f:
                f.write(content)

    # Optionally generate matplotlib PNG plots alongside ASCII figures
    if generate_plots and output_dir is not None:
        try:
            from statebind.evaluation.plotting import HAS_MATPLOTLIB, generate_all_plots
            if HAS_MATPLOTLIB:
                plot_paths = generate_all_plots(
                    result, merged, Path(output_dir),
                    sensitivity=getattr(result, "sensitivity", None),
                )
                figures.update({k: str(v) for k, v in plot_paths.items()})
        except ImportError:
            pass

    return figures
