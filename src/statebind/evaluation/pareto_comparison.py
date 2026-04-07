"""Pareto front comparison between static and state-aware pipelines.

Loads scored candidates from MergedRanking, computes Pareto fronts for each
pipeline, and produces a ParetoComparison with hypervolume indicator, dominance
fraction, and per-objective analysis.

This module is ADDITIVE to the existing weighted-sum comparison -- it does not
replace any existing evaluation logic.
"""

from __future__ import annotations

from statebind.ranking.models import MergedRanking
from statebind.ranking.pareto import (
    OBJECTIVE_NAMES,
    ParetoComparison,
    compare_pareto_fronts,
    extract_score_matrix,
)


def run_pareto_comparison(
    merged: MergedRanking,
    objective_names: list[str] | None = None,
    reference_point: list[float] | None = None,
) -> ParetoComparison:
    """Run Pareto front comparison on both pipelines.

    Extracts per-objective scores from UnifiedScoredCandidate objects in
    both pools, computes Pareto fronts and hypervolume indicators, then
    compares the two fronts.

    Args:
        merged: MergedRanking containing both pipeline pools.
        objective_names: Score component names to use. Defaults to the
            4 standard objectives.
        reference_point: Reference point for hypervolume computation.
            Defaults to origin (all zeros).

    Returns:
        ParetoComparison with hypervolume ratio, dominance fraction,
        and per-objective winners.
    """
    if objective_names is None:
        objective_names = list(OBJECTIVE_NAMES)

    static_matrix = extract_score_matrix(
        merged.static_pool.candidates, objective_names
    )
    state_matrix = extract_score_matrix(
        merged.state_aware_pool.candidates, objective_names
    )

    return compare_pareto_fronts(
        static_scores=static_matrix,
        state_aware_scores=state_matrix,
        objective_names=objective_names,
        reference_point=reference_point,
    )


def format_pareto_summary(comparison: ParetoComparison) -> str:
    """Format a plain-text summary of the Pareto comparison.

    Returns a multi-line string suitable for embedding in markdown reports.
    """
    lines = []

    sr = comparison.static_result
    sar = comparison.state_aware_result

    lines.append(f"Static pipeline:      {sr.n_candidates} candidates, "
                 f"{len(sr.front_indices)} on Pareto front, "
                 f"hypervolume = {sr.hypervolume:.4f}")
    lines.append(f"State-aware pipeline: {sar.n_candidates} candidates, "
                 f"{len(sar.front_indices)} on Pareto front, "
                 f"hypervolume = {sar.hypervolume:.4f}")
    lines.append("")
    lines.append(f"Hypervolume ratio (state-aware / static): {comparison.hypervolume_ratio:.4f}")

    if comparison.hypervolume_ratio > 1.0:
        lines.append("  -> State-aware front covers MORE objective space")
    elif comparison.hypervolume_ratio < 1.0:
        lines.append("  -> Static front covers MORE objective space")
    else:
        lines.append("  -> Fronts cover EQUAL objective space")

    lines.append(f"Dominance fraction: {comparison.dominance_fraction:.4f} "
                 f"of static front dominated by state-aware")
    lines.append("")

    lines.append("Per-objective best extreme:")
    for name, winner in comparison.per_objective_winner.items():
        lines.append(f"  {name}: {winner}")

    return "\n".join(lines)
