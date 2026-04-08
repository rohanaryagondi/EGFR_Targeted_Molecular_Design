"""Figure generation for the comparative evaluation.

Generates text-based (ASCII) figures for maximum portability.
These can be embedded directly in markdown reports without
requiring matplotlib or any graphics library.

If matplotlib is available, also generates PNG plots.
"""

from __future__ import annotations

from pathlib import Path

from statebind.evaluation.comparison import ComparativeResult
from statebind.ranking.models import MergedRanking


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
    st_mean = static_stats.get('mean', 0)
    st_max = static_stats.get('max', 0)
    sa_mean = state_stats.get('mean', 0)
    sa_max = state_stats.get('max', 0)
    lines.append(f"    Mean  {_bar(st_mean, max_score, 40)} {st_mean:.4f}")
    lines.append(f"    Max   {_bar(st_max, max_score, 40)} {st_max:.4f}")
    lines.append("")
    lines.append(
        f"  State-aware      mean={sa_mean:.4f}  "
        f"std={state_stats.get('std', 0):.4f}  "
        f"[{state_stats.get('min', 0):.3f}, {sa_max:.3f}]"
    )
    lines.append(f"    Mean  {_bar(sa_mean, max_score, 40)} {sa_mean:.4f}")
    lines.append(f"    Max   {_bar(sa_max, max_score, 40)} {sa_max:.4f}")
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


def pareto_summary_ascii(result: ComparativeResult) -> str:
    """ASCII visualization of Pareto front comparison results."""
    from statebind.ranking.pareto import ParetoComparison

    lines = ["## Pareto Front Analysis", ""]

    pareto = getattr(result, "pareto", None)
    if not isinstance(pareto, ParetoComparison):
        lines.append("  No Pareto analysis has been run.")
        return "\n".join(lines)

    sr = pareto.static_result
    sar = pareto.state_aware_result

    lines.append("  Pareto Front Sizes:")
    max_front = max(len(sr.front_indices), len(sar.front_indices), 1)
    lines.append(f"    Static      {_bar(len(sr.front_indices), max_front, 30)} "
                 f"{len(sr.front_indices)}/{sr.n_candidates}")
    lines.append(f"    State-aw.   {_bar(len(sar.front_indices), max_front, 30)} "
                 f"{len(sar.front_indices)}/{sar.n_candidates}")
    lines.append("")

    lines.append("  Hypervolume Indicators:")
    max_hv = max(sr.hypervolume, sar.hypervolume, 0.0001)
    lines.append(f"    Static      {_bar(sr.hypervolume, max_hv, 30)} {sr.hypervolume:.4f}")
    lines.append(f"    State-aw.   {_bar(sar.hypervolume, max_hv, 30)} {sar.hypervolume:.4f}")
    lines.append(f"    Ratio (SA/S): {pareto.hypervolume_ratio:.4f}")
    lines.append("")

    lines.append(f"  Dominance: {pareto.dominance_fraction:.1%} of static front "
                 f"dominated by state-aware")
    lines.append("")

    lines.append("  Per-objective best extreme:")
    for name, winner in pareto.per_objective_winner.items():
        marker = "SA" if winner == "state_aware" else ("S" if winner == "static" else "=")
        lines.append(f"    [{marker}] {name}")

    return "\n".join(lines)


def retrospective_enrichment_ascii(result: ComparativeResult) -> str:
    """ASCII bar chart of enrichment factors per cutoff and pipeline."""
    from statebind.evaluation.retrospective import RetrospectiveComparison

    lines = ["## Retrospective Enrichment Factors", ""]

    retro = getattr(result, "retrospective", None)
    if not isinstance(retro, RetrospectiveComparison):
        lines.append("  No retrospective validation has been run.")
        return "\n".join(lines)

    for cutoff in retro.cutoffs:
        cutoff_results = [
            r for r in retro.results if r.cutoff_year == cutoff
        ]
        if not cutoff_results:
            continue

        lines.append(f"  Cutoff {cutoff}:")

        for k in [10, 50]:
            max_ef = max(
                (r.enrichment_factors.get(k, 0.0) for r in cutoff_results),
                default=1.0,
            )
            max_ef = max(max_ef, 1.0)  # At least 1.0 for scale

            for r in cutoff_results:
                label = "Static   " if r.pipeline == "static" else "State-aw."
                ef = r.enrichment_factors.get(k, 0.0)
                lines.append(
                    f"    {label} EF@{k:<3d} {_bar(ef, max_ef, 25)} {ef:.2f}"
                )
            lines.append("")

    return "\n".join(lines)


def retrospective_summary_ascii(result: ComparativeResult) -> str:
    """ASCII table summarizing retrospective validation results."""
    from statebind.evaluation.retrospective import RetrospectiveComparison

    lines = ["## Retrospective Validation Summary", ""]

    retro = getattr(result, "retrospective", None)
    if not isinstance(retro, RetrospectiveComparison):
        lines.append("  No retrospective validation has been run.")
        return "\n".join(lines)

    header = (
        f"  {'Cutoff':<8} {'Pipeline':<14} {'EF@10':>7} {'EF@50':>7} "
        f"{'Max Sim':>8} {'Novelty':>8} {'Found':>8}"
    )
    lines.append(header)
    lines.append("  " + "\u2500" * (len(header) - 2))

    for r in retro.results:
        found = sum(1 for rank in r.future_drug_ranks.values() if rank is not None)
        total = r.n_future_drugs
        lines.append(
            f"  {r.cutoff_year:<8} {r.pipeline:<14} "
            f"{r.enrichment_factor_10:>7.2f} {r.enrichment_factor_50:>7.2f} "
            f"{r.max_similarity_to_future:>8.3f} "
            f"{r.novelty_vs_training:>8.2f} "
            f"{found:>3}/{total:<3}"
        )

    if retro.summary:
        lines.append("")
        # Include just the last line (overall assessment) from summary
        summary_lines = retro.summary.strip().split("\n")
        if summary_lines:
            lines.append(f"  {summary_lines[-1].strip()}")

    return "\n".join(lines)


def plot_pareto_projections(
    pareto: object,
    save_dir: str | Path | None = None,
) -> list[Path]:
    """Plot 2D Pareto front projections for all pairs of objectives.

    Args:
        pareto: ParetoComparison object.
        save_dir: Directory to save PNG files. If None, uses tempdir.

    Returns:
        List of saved figure paths (one per objective pair).
    """
    import itertools
    import tempfile

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    from statebind.ranking.pareto import ParetoComparison

    if not isinstance(pareto, ParetoComparison):
        return []

    if save_dir is None:
        save_dir = Path(tempfile.mkdtemp())
    else:
        save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    names = pareto.static_result.objective_names
    pairs = list(itertools.combinations(range(len(names)), 2))
    paths: list[Path] = []

    for i, j in pairs:
        fig, ax = plt.subplots(1, 1, figsize=(7, 5))

        # Static front
        sf = pareto.static_result.front_scores
        if sf.shape[0] > 0:
            ax.scatter(sf[:, i], sf[:, j], c="steelblue", alpha=0.7,
                       label=f"Static front ({sf.shape[0]})", zorder=3, s=50)

        # State-aware front
        saf = pareto.state_aware_result.front_scores
        if saf.shape[0] > 0:
            ax.scatter(saf[:, i], saf[:, j], c="darkorange", alpha=0.7,
                       label=f"State-aware front ({saf.shape[0]})", zorder=3,
                       marker="^", s=50)

        ax.set_xlabel(names[i])
        ax.set_ylabel(names[j])
        ax.set_title(f"Pareto Front: {names[i]} vs {names[j]}")
        ax.legend(loc="best", fontsize=8)
        ax.grid(True, alpha=0.3)

        fname = f"pareto_{names[i]}_vs_{names[j]}.png"
        fpath = save_dir / fname
        fig.savefig(fpath, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(fpath)

    return paths


def plot_parallel_coordinates(
    pareto: object,
    save_path: str | Path | None = None,
) -> Path | None:
    """Parallel coordinates plot showing all objectives simultaneously.

    Each line is a Pareto-optimal candidate. Blue = static, orange = state-aware.
    """
    import tempfile

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    from statebind.ranking.pareto import ParetoComparison

    if not isinstance(pareto, ParetoComparison):
        return None

    if save_path is None:
        save_path = Path(tempfile.mkdtemp()) / "pareto_parallel_coordinates.png"
    else:
        save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    names = pareto.static_result.objective_names
    n_obj = len(names)
    x_ticks = list(range(n_obj))

    fig, ax = plt.subplots(1, 1, figsize=(8, 5))

    # Plot static front
    sf = pareto.static_result.front_scores
    for row in sf:
        ax.plot(x_ticks, row, c="steelblue", alpha=0.4, linewidth=1.2)

    # Plot state-aware front
    saf = pareto.state_aware_result.front_scores
    for row in saf:
        ax.plot(x_ticks, row, c="darkorange", alpha=0.4, linewidth=1.2)

    # Dummy lines for legend
    ax.plot([], [], c="steelblue", linewidth=2,
            label=f"Static ({sf.shape[0]} on front)")
    ax.plot([], [], c="darkorange", linewidth=2,
            label=f"State-aware ({saf.shape[0]} on front)")

    ax.set_xticks(x_ticks)
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_ylabel("Score")
    ax.set_title("Pareto Front: Parallel Coordinates")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_ylim(0, 1.05)

    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return save_path


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

    # WS12: Pareto analysis figure
    if getattr(result, "pareto", None) is not None:
        figures["pareto_summary"] = pareto_summary_ascii(result)

    # WS13: Retrospective validation figures
    if getattr(result, "retrospective", None) is not None:
        figures["retrospective_enrichment"] = retrospective_enrichment_ascii(result)
        figures["retrospective_summary"] = retrospective_summary_ascii(result)

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

        # WS12: Pareto plots
        pareto = getattr(result, "pareto", None)
        if pareto is not None:
            proj_paths = plot_pareto_projections(pareto, save_dir=output_dir)
            for p in proj_paths:
                figures[f"plot_pareto_{p.stem}"] = p
            pc_path = plot_parallel_coordinates(
                pareto,
                save_path=output_dir / "pareto_parallel_coordinates.png",
            )
            if pc_path is not None:
                figures["plot_pareto_parallel_coordinates"] = pc_path

    return figures
