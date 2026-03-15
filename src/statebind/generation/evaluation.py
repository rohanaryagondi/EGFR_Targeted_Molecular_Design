"""Evaluation of state-conditioned generation quality.

Reports:
- Validity, uniqueness, diversity per state
- Generation yield by state
- Candidate overlap between states
- Comparison with static baseline
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from statebind.baselines.filtering import _is_valid_smiles
from statebind.baselines.scoring import _tanimoto_ngram
from statebind.generation.diversity import (
    CrossStateDiversityReport,
    analyze_cross_state_diversity,
    compute_diversity,
)
from statebind.generation.models import (
    FilteredStateLibrary,
    MultiStateFilterResult,
    MultiStateGenerationResult,
)


@dataclass
class StateEvaluation:
    """Evaluation metrics for a single state's candidates."""

    state: str
    n_generated: int = 0
    n_filtered: int = 0
    filter_pass_rate: float = 0.0
    validity_rate: float = 0.0
    uniqueness_rate: float = 0.0
    diversity_score: float = 0.0
    n_state_unique: int = 0
    unique_fraction: float = 0.0
    strategies_used: list[str] = field(default_factory=list)
    mean_mw: float = 0.0


@dataclass
class GenerationEvaluation:
    """Complete evaluation of multi-state generation."""

    per_state: list[StateEvaluation] = field(default_factory=list)
    total_generated: int = 0
    total_filtered: int = 0
    total_unique: int = 0
    global_diversity: float = 0.0
    cross_state_overlap: dict[str, int] = field(default_factory=dict)
    baseline_comparison: dict[str, object] = field(default_factory=dict)


@dataclass
class BaselineComparison:
    """Comparison between state-conditioned and static baseline."""

    static_n_candidates: int = 0
    state_conditioned_n_candidates: int = 0
    state_conditioned_unique: int = 0
    overlap_with_static: int = 0
    state_only_candidates: int = 0
    static_only_candidates: int = 0
    diversity_static: float = 0.0
    diversity_state_conditioned: float = 0.0


def evaluate_generation(
    generation: MultiStateGenerationResult,
    filtered: MultiStateFilterResult,
    diversity_report: CrossStateDiversityReport,
) -> GenerationEvaluation:
    """Evaluate multi-state generation results."""

    per_state: list[StateEvaluation] = []

    for gen_lib, filt_lib, div_report in zip(
        generation.libraries, filtered.libraries, diversity_report.per_state
    ):
        # Validity
        n_valid = sum(1 for c in gen_lib.candidates if _is_valid_smiles(c.smiles))
        validity = n_valid / max(gen_lib.n_candidates, 1)

        # Uniqueness
        unique_smiles = set(c.smiles for c in filt_lib.candidates)
        uniqueness = len(unique_smiles) / max(filt_lib.n_passed, 1)

        # Mean MW
        mean_mw = 0.0
        mw_stats = filt_lib.property_stats.get("estimated_mw", {})
        if "mean" in mw_stats:
            mean_mw = mw_stats["mean"]

        per_state.append(StateEvaluation(
            state=gen_lib.state,
            n_generated=gen_lib.n_candidates,
            n_filtered=filt_lib.n_passed,
            filter_pass_rate=filt_lib.pass_rate,
            validity_rate=validity,
            uniqueness_rate=uniqueness,
            diversity_score=div_report.intra_diversity.diversity_score,
            n_state_unique=div_report.n_state_unique,
            unique_fraction=div_report.unique_fraction,
            strategies_used=gen_lib.strategies_used,
            mean_mw=mean_mw,
        ))

    return GenerationEvaluation(
        per_state=per_state,
        total_generated=generation.total_candidates,
        total_filtered=filtered.total_passed,
        total_unique=generation.total_unique_smiles,
        global_diversity=diversity_report.global_diversity.diversity_score,
        cross_state_overlap=diversity_report.overlap_matrix,
    )


def compare_with_static_baseline(
    filtered: MultiStateFilterResult,
    static_smiles: set[str],
) -> BaselineComparison:
    """Compare state-conditioned candidates against static baseline.

    Args:
        filtered: Multi-state filtered results.
        static_smiles: Set of SMILES from the static baseline pipeline.

    Returns:
        BaselineComparison metrics.
    """
    state_smiles: set[str] = set()
    for lib in filtered.libraries:
        state_smiles.update(c.smiles for c in lib.candidates)

    overlap = state_smiles & static_smiles
    state_only = state_smiles - static_smiles
    static_only = static_smiles - state_smiles

    # Diversity of state-conditioned
    state_div = compute_diversity(list(state_smiles))
    static_div = compute_diversity(list(static_smiles))

    return BaselineComparison(
        static_n_candidates=len(static_smiles),
        state_conditioned_n_candidates=len(state_smiles),
        state_conditioned_unique=len(state_smiles),
        overlap_with_static=len(overlap),
        state_only_candidates=len(state_only),
        static_only_candidates=len(static_only),
        diversity_static=static_div.diversity_score,
        diversity_state_conditioned=state_div.diversity_score,
    )


def evaluation_to_dict(evl: GenerationEvaluation) -> dict:
    """Serialize evaluation to dict."""
    return {
        "total_generated": evl.total_generated,
        "total_filtered": evl.total_filtered,
        "total_unique": evl.total_unique,
        "global_diversity": round(evl.global_diversity, 4),
        "cross_state_overlap": evl.cross_state_overlap,
        "per_state": [
            {
                "state": s.state,
                "n_generated": s.n_generated,
                "n_filtered": s.n_filtered,
                "filter_pass_rate": round(s.filter_pass_rate, 4),
                "validity_rate": round(s.validity_rate, 4),
                "uniqueness_rate": round(s.uniqueness_rate, 4),
                "diversity_score": round(s.diversity_score, 4),
                "n_state_unique": s.n_state_unique,
                "unique_fraction": round(s.unique_fraction, 4),
                "strategies_used": s.strategies_used,
                "mean_mw": round(s.mean_mw, 1),
            }
            for s in evl.per_state
        ],
    }


def save_evaluation(evl: GenerationEvaluation, path: Path) -> None:
    """Save evaluation to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(evaluation_to_dict(evl), f, indent=2)
