"""Publication-quality matplotlib figures for pipeline comparison.

All figures are optional -- generated only when matplotlib is available.
Each function returns a Figure object and optionally saves to disk.
Uses Agg backend for non-interactive (server/CI) environments.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.figure import Figure

from statebind.evaluation.comparison import ComparativeResult
from statebind.ranking.models import MergedRanking, PipelineLabel

# ---------------------------------------------------------------------------
# Optional dependency -- matplotlib is in [science] extras
# ---------------------------------------------------------------------------

HAS_MATPLOTLIB: bool

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend, MUST precede pyplot
    import matplotlib.patches as mpatches  # noqa: I001 (Agg backend must precede pyplot)
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLOR_STATIC = "#1f77b4"       # blue
COLOR_STATE_AWARE = "#ff7f0e"  # orange

_DEFAULT_DPI = 150
_DEFAULT_FIGSIZE = (8, 6)
_FONT_TITLE = 14
_FONT_LABEL = 12
_FONT_TICK = 10

# Score component names in canonical order (matches sensitivity._COMPONENT_NAMES)
_COMPONENT_NAMES = [
    "reference_similarity",
    "druglikeness",
    "docking_proxy",
    "state_specificity",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _save_figure(fig: Figure, output_path: Path | None) -> None:
    """Save figure to disk if path is given. Does NOT close the figure."""
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=_DEFAULT_DPI, bbox_inches="tight")


def _apply_style() -> None:
    """Apply a clean publication-ready style."""
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        plt.rcParams.update({
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.facecolor": "#f8f8f8",
        })


# ---------------------------------------------------------------------------
# 1. Score distributions
# ---------------------------------------------------------------------------


def plot_score_distributions(
    result: ComparativeResult,
    output_path: Path | None = None,
) -> Figure | None:
    """Grouped bar chart of mean composite scores with std error bars.

    Annotates with Mann-Whitney p-value and Cohen's d when statistical
    tests are available in ``result.statistical_tests``.
    """
    if not HAS_MATPLOTLIB:
        return None

    static_stats = result.scores.static_stats
    state_stats = result.scores.state_aware_stats
    if not static_stats or not state_stats:
        return None

    _apply_style()
    fig, ax = plt.subplots(figsize=(6, 5))

    labels = ["Static Baseline", "State-Aware"]
    means = [static_stats.get("mean", 0.0), state_stats.get("mean", 0.0)]
    stds = [static_stats.get("std", 0.0), state_stats.get("std", 0.0)]
    colors = [COLOR_STATIC, COLOR_STATE_AWARE]

    ax.bar(labels, means, yerr=stds, capsize=6, color=colors,
           edgecolor="white", width=0.5, alpha=0.85)

    # Min/max markers
    for i, (stats, x) in enumerate(zip(
        [static_stats, state_stats], range(len(labels))
    )):
        lo, hi = stats.get("min", 0.0), stats.get("max", 0.0)
        ax.plot([x, x], [lo, hi], color="grey", linewidth=1, zorder=1)
        ax.scatter([x, x], [lo, hi], color="grey", s=20, zorder=2)

    # Statistical annotation
    if result.statistical_tests:
        test = result.statistical_tests[0]
        p_val = test.p_value
        effect = test.effect_size
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "n.s."
        ax.annotate(
            f"p={p_val:.4f} {sig}\nCohen's d={effect:+.3f}",
            xy=(0.5, max(means) + max(stds) * 1.2),
            ha="center", fontsize=9, style="italic",
        )

    ax.set_ylabel("Composite Score", fontsize=_FONT_LABEL)
    ax.set_title("Composite Score Distribution", fontsize=_FONT_TITLE)
    ax.tick_params(labelsize=_FONT_TICK)
    fig.tight_layout()
    _save_figure(fig, output_path)
    return fig


# ---------------------------------------------------------------------------
# 2. Score components heatmap
# ---------------------------------------------------------------------------


def plot_score_components_heatmap(
    merged: MergedRanking,
    top_n: int = 20,
    output_path: Path | None = None,
) -> Figure | None:
    """Heatmap of score components for the top-N globally ranked candidates.

    Rows = candidates, columns = 4 score components.
    A colour sidebar indicates pipeline origin.
    """
    if not HAS_MATPLOTLIB:
        return None

    candidates = merged.merged[:top_n]
    if not candidates:
        return None

    n = len(candidates)
    data = np.zeros((n, len(_COMPONENT_NAMES)))
    pipelines: list[str] = []
    y_labels: list[str] = []

    for i, c in enumerate(candidates):
        for j, comp in enumerate(_COMPONENT_NAMES):
            data[i, j] = c.get_score(comp) or 0.0
        pipelines.append(c.pipeline.value)
        y_labels.append(f"#{c.global_rank} {c.smiles[:20]}…")

    _apply_style()
    fig, (ax_side, ax_heat) = plt.subplots(
        1, 2, figsize=(10, max(4, n * 0.35)),
        gridspec_kw={"width_ratios": [0.04, 1]},
    )

    # Pipeline sidebar
    sidebar = np.array([
        0.0 if p == PipelineLabel.STATIC.value else 1.0
        for p in pipelines
    ]).reshape(-1, 1)
    from matplotlib.colors import ListedColormap
    side_cmap = ListedColormap([COLOR_STATIC, COLOR_STATE_AWARE])
    ax_side.imshow(sidebar, aspect="auto", cmap=side_cmap, vmin=0, vmax=1)
    ax_side.set_xticks([])
    ax_side.set_yticks(range(n))
    ax_side.set_yticklabels(y_labels, fontsize=8)
    ax_side.set_xlabel("Pipeline", fontsize=8)

    # Heatmap
    im = ax_heat.imshow(data, aspect="auto", cmap="YlOrRd")
    ax_heat.set_xticks(range(len(_COMPONENT_NAMES)))
    ax_heat.set_xticklabels(
        [c.replace("_", "\n") for c in _COMPONENT_NAMES],
        fontsize=_FONT_TICK, ha="center",
    )
    ax_heat.set_yticks([])

    # Annotate cells with values
    for i in range(n):
        for j in range(len(_COMPONENT_NAMES)):
            ax_heat.text(
                j, i, f"{data[i, j]:.2f}",
                ha="center", va="center", fontsize=7,
                color="white" if data[i, j] > 0.6 else "black",
            )

    fig.colorbar(im, ax=ax_heat, fraction=0.03, pad=0.02, label="Score")
    ax_heat.set_title(f"Top-{n} Candidates: Score Components", fontsize=_FONT_TITLE)

    # Legend for sidebar
    static_patch = mpatches.Patch(color=COLOR_STATIC, label="Static")
    state_patch = mpatches.Patch(color=COLOR_STATE_AWARE, label="State-Aware")
    fig.legend(handles=[static_patch, state_patch], loc="lower center",
               ncol=2, fontsize=9, frameon=True)

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _save_figure(fig, output_path)
    return fig


# ---------------------------------------------------------------------------
# 3. Diversity radar
# ---------------------------------------------------------------------------


def plot_diversity_radar(
    result: ComparativeResult,
    output_path: Path | None = None,
) -> Figure | None:
    """Radar chart comparing diversity metrics between pipelines."""
    if not HAS_MATPLOTLIB:
        return None

    s = result.diversity.static
    a = result.diversity.state_aware

    metric_names = [
        "n_candidates",
        "diversity_score",
        "n_unique_smiles",
        "mean_pairwise\ntanimoto",
    ]
    static_raw = [s.n_candidates, s.diversity_score, s.n_unique_smiles, s.mean_pairwise_tanimoto]
    state_raw = [a.n_candidates, a.diversity_score, a.n_unique_smiles, a.mean_pairwise_tanimoto]

    # Normalize to [0, 1]
    static_vals: list[float] = []
    state_vals: list[float] = []
    for sv, av in zip(static_raw, state_raw):
        mx = max(float(sv), float(av), 1e-9)
        static_vals.append(float(sv) / mx)
        state_vals.append(float(av) / mx)

    n_axes = len(metric_names)
    angles = [i / n_axes * 2 * np.pi for i in range(n_axes)]
    # Close the polygon
    static_vals.append(static_vals[0])
    state_vals.append(state_vals[0])
    angles.append(angles[0])

    _apply_style()
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})

    ax.plot(angles, static_vals, "o-", color=COLOR_STATIC, linewidth=2, label="Static")
    ax.fill(angles, static_vals, alpha=0.15, color=COLOR_STATIC)
    ax.plot(angles, state_vals, "o-", color=COLOR_STATE_AWARE, linewidth=2, label="State-Aware")
    ax.fill(angles, state_vals, alpha=0.15, color=COLOR_STATE_AWARE)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_names, fontsize=_FONT_TICK)
    ax.set_ylim(0, 1.1)
    ax.set_title("Diversity Comparison", fontsize=_FONT_TITLE, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=9)

    fig.tight_layout()
    _save_figure(fig, output_path)
    return fig


# ---------------------------------------------------------------------------
# 4. Sensitivity heatmap (diverging bar chart)
# ---------------------------------------------------------------------------


def plot_sensitivity_heatmap(
    summary: object | None,
    output_path: Path | None = None,
) -> Figure | None:
    """Diverging bar chart of weight-sensitivity deltas.

    Sorted by state_specificity weight. Green = state-aware wins,
    red = static wins.
    """
    if not HAS_MATPLOTLIB:
        return None

    try:
        from statebind.evaluation.sensitivity import SensitivitySummary
    except ImportError:
        return None

    if not isinstance(summary, SensitivitySummary) or not summary.results:
        return None

    # Sort by state_specificity weight
    sorted_results = sorted(
        summary.results,
        key=lambda r: r.weight_config.get("state_specificity", 0.0),
    )
    deltas = [r.delta for r in sorted_results]
    ss_weights = [r.weight_config.get("state_specificity", 0.0) for r in sorted_results]

    _apply_style()
    fig, ax = plt.subplots(figsize=(10, 5))

    colors = ["#2ca02c" if d >= 0 else "#d62728" for d in deltas]
    x = np.arange(len(deltas))
    ax.bar(x, deltas, color=colors, alpha=0.8, width=1.0, edgecolor="none")
    ax.axhline(0, color="black", linewidth=0.8)

    # X-axis: show state_specificity weight at a few tick positions
    n_ticks = min(10, len(sorted_results))
    tick_positions = np.linspace(0, len(deltas) - 1, n_ticks, dtype=int)
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(
        [f"{ss_weights[i]:.2f}" for i in tick_positions],
        fontsize=_FONT_TICK,
    )

    ax.set_xlabel("state_specificity weight", fontsize=_FONT_LABEL)
    ax.set_ylabel("Score Delta (state-aware − static)", fontsize=_FONT_LABEL)
    ax.set_title(
        f"Weight Sensitivity ({summary.n_configs} configs: "
        f"{summary.state_aware_wins} SA wins, "
        f"{summary.static_wins} static wins, "
        f"{summary.ties} ties)",
        fontsize=_FONT_TITLE,
    )
    ax.tick_params(labelsize=_FONT_TICK)
    fig.tight_layout()
    _save_figure(fig, output_path)
    return fig


# ---------------------------------------------------------------------------
# 5. Rank shift waterfall
# ---------------------------------------------------------------------------


def plot_rank_shift_waterfall(
    merged: MergedRanking,
    n: int = 20,
    output_path: Path | None = None,
) -> Figure | None:
    """Horizontal bar chart of the biggest rank shifts (promoted/demoted)."""
    if not HAS_MATPLOTLIB:
        return None

    from statebind.ranking.aggregation import compute_rank_shifts

    shifts = compute_rank_shifts(merged)
    if not shifts:
        return None

    # Sort by absolute shift, take top n
    top = sorted(shifts, key=lambda s: abs(s.shift), reverse=True)[:n]
    # Re-sort for visual: promoted at top, demoted at bottom
    top.sort(key=lambda s: s.shift, reverse=True)

    labels = [f"#{s.global_rank} ({s.pipeline.value[:5]})" for s in top]
    values = [s.shift for s in top]
    colors = ["#2ca02c" if v >= 0 else "#d62728" for v in values]

    _apply_style()
    fig_height = max(4, len(top) * 0.35)
    fig, ax = plt.subplots(figsize=(8, fig_height))

    y_pos = np.arange(len(top))
    ax.barh(y_pos, values, color=colors, alpha=0.85, edgecolor="white")
    ax.axvline(0, color="black", linewidth=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Rank Shift (positive = promoted)", fontsize=_FONT_LABEL)
    ax.set_title(f"Top-{len(top)} Rank Shifts: Pipeline-Local → Global", fontsize=_FONT_TITLE)
    ax.tick_params(labelsize=_FONT_TICK)

    promoted = mpatches.Patch(color="#2ca02c", label="Promoted")
    demoted = mpatches.Patch(color="#d62728", label="Demoted")
    ax.legend(handles=[promoted, demoted], fontsize=9)

    fig.tight_layout()
    _save_figure(fig, output_path)
    return fig


# ---------------------------------------------------------------------------
# 6. Strategy contribution
# ---------------------------------------------------------------------------


def plot_strategy_contribution(
    result: ComparativeResult,
    output_path: Path | None = None,
) -> Figure | None:
    """Bar charts of novel candidates by strategy and by state."""
    if not HAS_MATPLOTLIB:
        return None

    strategies = result.novelty.novel_strategies
    states = result.novelty.novel_states
    if not strategies and not states:
        return None

    _apply_style()
    n_panels = sum([bool(strategies), bool(states)])
    fig, axes = plt.subplots(1, n_panels, figsize=(5 * n_panels, 5))
    if n_panels == 1:
        axes = [axes]

    idx = 0

    if strategies:
        ax = axes[idx]
        sorted_strats = sorted(strategies.items(), key=lambda x: x[1], reverse=True)
        names = [s[0] for s in sorted_strats]
        counts = [s[1] for s in sorted_strats]
        ax.barh(range(len(names)), counts, color=COLOR_STATE_AWARE, alpha=0.85)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=9)
        ax.set_xlabel("Count", fontsize=_FONT_LABEL)
        ax.set_title("Novel Candidates by Strategy", fontsize=_FONT_TITLE)
        ax.tick_params(labelsize=_FONT_TICK)
        idx += 1

    if states:
        ax = axes[idx]
        sorted_states = sorted(states.items(), key=lambda x: x[1], reverse=True)
        names = [s[0].replace("_", "\n") for s in sorted_states]
        counts = [s[1] for s in sorted_states]
        ax.barh(range(len(names)), counts, color=COLOR_STATE_AWARE, alpha=0.85)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=9)
        ax.set_xlabel("Count", fontsize=_FONT_LABEL)
        ax.set_title("Novel Candidates by State", fontsize=_FONT_TITLE)
        ax.tick_params(labelsize=_FONT_TICK)

    fig.tight_layout()
    _save_figure(fig, output_path)
    return fig


# ---------------------------------------------------------------------------
# 7. SA score distribution
# ---------------------------------------------------------------------------


def plot_sa_score_distribution(
    merged: MergedRanking,
    output_path: Path | None = None,
) -> Figure | None:
    """Histogram of synthetic accessibility scores split by pipeline.

    Only generates when both matplotlib and RDKit are available.
    """
    if not HAS_MATPLOTLIB:
        return None

    try:
        from statebind.chemistry.sa_score import HAS_RDKIT, compute_sa_score
    except ImportError:
        return None

    if not HAS_RDKIT:
        return None

    static_sa = [compute_sa_score(c.smiles) for c in merged.static_pool.candidates]
    state_sa = [compute_sa_score(c.smiles) for c in merged.state_aware_pool.candidates]

    if not static_sa and not state_sa:
        return None

    _apply_style()
    fig, ax = plt.subplots(figsize=_DEFAULT_FIGSIZE)

    bins = np.linspace(1, 10, 25)
    if static_sa:
        ax.hist(static_sa, bins=bins, alpha=0.6, color=COLOR_STATIC,
                label=f"Static (n={len(static_sa)})", edgecolor="white")
    if state_sa:
        ax.hist(state_sa, bins=bins, alpha=0.6, color=COLOR_STATE_AWARE,
                label=f"State-Aware (n={len(state_sa)})", edgecolor="white")

    # Mean lines
    if static_sa:
        ax.axvline(np.mean(static_sa), color=COLOR_STATIC, linestyle="--", linewidth=1.5)
    if state_sa:
        ax.axvline(np.mean(state_sa), color=COLOR_STATE_AWARE, linestyle="--", linewidth=1.5)

    ax.set_xlabel("SA Score (1=easy, 10=hard)", fontsize=_FONT_LABEL)
    ax.set_ylabel("Count", fontsize=_FONT_LABEL)
    ax.set_title("Synthetic Accessibility Score Distribution", fontsize=_FONT_TITLE)
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=_FONT_TICK)
    fig.tight_layout()
    _save_figure(fig, output_path)
    return fig


# ---------------------------------------------------------------------------
# 8. Orchestrator
# ---------------------------------------------------------------------------


def generate_all_plots(
    result: ComparativeResult,
    merged: MergedRanking,
    output_dir: Path,
    sensitivity: object | None = None,
) -> dict[str, Path]:
    """Generate all available plots, save to *output_dir*.

    Returns dict mapping figure name to saved file path.
    Skips figures whose dependencies are not available.
    Keys are prefixed with ``plot_`` to avoid collision with ASCII
    figure keys in ``figures.generate_all_figures``.
    """
    if not HAS_MATPLOTLIB:
        return {}

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    plots: dict[str, Path] = {}

    _jobs: list[tuple[str, str]] = [
        ("plot_score_distributions", "score_distributions.png"),
        ("plot_score_components_heatmap", "score_components_heatmap.png"),
        ("plot_diversity_radar", "diversity_radar.png"),
        ("plot_rank_shift_waterfall", "rank_shift_waterfall.png"),
        ("plot_strategy_contribution", "strategy_contribution.png"),
        ("plot_sensitivity_heatmap", "sensitivity_heatmap.png"),
        ("plot_sa_score_distribution", "sa_score_distribution.png"),
    ]

    for key, filename in _jobs:
        path = output_dir / filename
        fig: Figure | None = None
        try:
            if key == "plot_score_distributions":
                fig = plot_score_distributions(result, output_path=path)
            elif key == "plot_score_components_heatmap":
                fig = plot_score_components_heatmap(merged, output_path=path)
            elif key == "plot_diversity_radar":
                fig = plot_diversity_radar(result, output_path=path)
            elif key == "plot_rank_shift_waterfall":
                fig = plot_rank_shift_waterfall(merged, output_path=path)
            elif key == "plot_strategy_contribution":
                fig = plot_strategy_contribution(result, output_path=path)
            elif key == "plot_sensitivity_heatmap":
                fig = plot_sensitivity_heatmap(sensitivity, output_path=path)
            elif key == "plot_sa_score_distribution":
                fig = plot_sa_score_distribution(merged, output_path=path)
        except Exception:
            fig = None

        if fig is not None:
            plots[key] = path
            plt.close(fig)

    return plots
