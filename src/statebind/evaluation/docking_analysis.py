"""State-specific docking analysis: dock candidates into all 4 pockets.

Produces a candidate x state score matrix that measures whether
state-aware candidates bind preferentially to their target state
pocket.  This is the core 3D structural test of the state-aware
hypothesis.

Requires GNINA and prepared receptors.  Returns empty/stub results
when either is unavailable.

Contract reference: workstreams/INTERFACES.md Contract 8.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# The 4 EGFR conformational states
_STATES = ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin", "DFGout_aCout"]


# ── Data models ──────────────────────────────────────────────────────────


class StateSelectivityResult(BaseModel):
    """Docking selectivity analysis for one candidate across all states."""

    smiles: str
    target_state: str
    scores_by_state: dict[str, float] = Field(
        default_factory=dict,
        description="state -> normalized Vina score [0, 1]",
    )
    raw_vina_by_state: dict[str, float] = Field(
        default_factory=dict,
        description="state -> raw Vina score (kcal/mol)",
    )
    cnn_scores_by_state: dict[str, float] = Field(
        default_factory=dict,
        description="state -> CNN pose score [0, 1]",
    )
    best_state: str = ""
    selectivity_ratio: float = Field(
        default=0.0,
        description="target_score / mean(other_scores); >1 = selective",
    )
    target_rank: int = Field(
        default=0,
        description="Rank of target state among all states (1 = best)",
    )
    is_selective: bool = Field(
        default=False,
        description="True if target_state has the best docking score",
    )


class DockingAnalysisSummary(BaseModel):
    """Summary of state-specific docking analysis across candidates."""

    n_candidates: int = 0
    n_selective: int = 0
    selectivity_rate: float = Field(
        default=0.0,
        description="Fraction of candidates selective for target state",
    )
    mean_selectivity_ratio: float = 0.0
    per_state_means: dict[str, float] = Field(
        default_factory=dict,
        description="Mean normalized score per state",
    )
    results: list[StateSelectivityResult] = Field(default_factory=list)
    generated_at: str = ""
    notes: str = ""


# ── Analysis functions ───────────────────────────────────────────────────


def dock_candidate_all_states(
    smiles: str,
    target_state: str,
) -> StateSelectivityResult | None:
    """Dock one candidate into all 4 state receptors.

    Returns None if GNINA is unavailable or receptors are not prepared.

    Args:
        smiles: SMILES string.
        target_state: The intended conformational state.

    Returns:
        StateSelectivityResult with scores across states, or None.
    """
    try:
        from statebind.chemistry.docking import (
            dock_molecule,
            get_receptor_for_state,
            is_gnina_available,
            normalize_vina_score,
        )
    except ImportError:
        return None

    if not is_gnina_available():
        return None

    scores_by_state: dict[str, float] = {}
    raw_vina_by_state: dict[str, float] = {}
    cnn_scores_by_state: dict[str, float] = {}

    for state in _STATES:
        receptor_info = get_receptor_for_state(state)
        if receptor_info is None:
            continue

        pdbqt_path, box_center, box_size = receptor_info
        result = dock_molecule(smiles, pdbqt_path, box_center, box_size)

        if result.success:
            norm = normalize_vina_score(result.vina_score)
            scores_by_state[state] = round(norm, 4)
            raw_vina_by_state[state] = round(result.vina_score, 4)
            cnn_scores_by_state[state] = round(result.cnn_score, 4)

    if not scores_by_state:
        return None

    # Determine best state and selectivity
    best_state = max(scores_by_state, key=scores_by_state.get)  # type: ignore[arg-type]
    target_score = scores_by_state.get(target_state, 0.0)
    other_scores = [v for k, v in scores_by_state.items() if k != target_state]
    mean_other = sum(other_scores) / len(other_scores) if other_scores else 0.0
    selectivity_ratio = target_score / mean_other if mean_other > 0 else 0.0

    # Rank target state
    sorted_states = sorted(scores_by_state.items(), key=lambda x: x[1], reverse=True)
    target_rank = next(
        (i + 1 for i, (s, _) in enumerate(sorted_states) if s == target_state),
        len(sorted_states),
    )

    return StateSelectivityResult(
        smiles=smiles,
        target_state=target_state,
        scores_by_state=scores_by_state,
        raw_vina_by_state=raw_vina_by_state,
        cnn_scores_by_state=cnn_scores_by_state,
        best_state=best_state,
        selectivity_ratio=round(selectivity_ratio, 4),
        target_rank=target_rank,
        is_selective=(best_state == target_state),
    )


def run_docking_analysis(
    candidates: list[dict[str, str]],
    n_workers: int = 4,
) -> DockingAnalysisSummary:
    """Run state-specific docking analysis on a list of candidates.

    Each candidate dict must have ``smiles`` and ``target_state`` keys.

    Args:
        candidates: List of dicts with smiles and target_state.
        n_workers: Number of parallel workers (currently sequential).

    Returns:
        DockingAnalysisSummary with per-candidate results.
    """
    results: list[StateSelectivityResult] = []

    for cand in candidates:
        smiles = cand["smiles"]
        target_state = cand["target_state"]
        result = dock_candidate_all_states(smiles, target_state)
        if result is not None:
            results.append(result)

    n_selective = sum(1 for r in results if r.is_selective)
    ratios = [r.selectivity_ratio for r in results if r.selectivity_ratio > 0]
    mean_ratio = sum(ratios) / len(ratios) if ratios else 0.0

    # Per-state mean scores
    per_state_means: dict[str, float] = {}
    for state in _STATES:
        scores = [r.scores_by_state.get(state, 0.0) for r in results if state in r.scores_by_state]
        per_state_means[state] = round(sum(scores) / len(scores), 4) if scores else 0.0

    return DockingAnalysisSummary(
        n_candidates=len(results),
        n_selective=n_selective,
        selectivity_rate=round(n_selective / len(results), 4) if results else 0.0,
        mean_selectivity_ratio=round(mean_ratio, 4),
        per_state_means=per_state_means,
        results=results,
        generated_at=datetime.now(timezone.utc).isoformat(),
        notes=f"Docked {len(results)} candidates into {len(_STATES)} states.",
    )


def compute_score_heatmap(
    summary: DockingAnalysisSummary,
) -> dict[str, list[str] | list[list[float]]]:
    """Convert analysis results to a heatmap-ready data structure.

    Returns:
        Dict with keys: candidates (list[str]), states (list[str]),
        scores (list[list[float]] — candidates x states matrix).
    """
    candidates = [r.smiles for r in summary.results]
    states = list(_STATES)
    scores = [
        [r.scores_by_state.get(s, 0.0) for s in states]
        for r in summary.results
    ]
    return {
        "candidates": candidates,
        "states": states,
        "scores": scores,
    }


def save_docking_analysis(
    summary: DockingAnalysisSummary,
    output_dir: Path | None = None,
) -> Path:
    """Save docking analysis as JSON artifact.

    Args:
        summary: Analysis summary to save.
        output_dir: Output directory (default: artifacts/docking/).

    Returns:
        Path to the saved JSON file.
    """
    if output_dir is None:
        from statebind.data.paths import DataPaths
        output_dir = DataPaths().docking_results_dir

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "docking_analysis.json"

    with open(output_path, "w") as f:
        json.dump(summary.model_dump(mode="json"), f, indent=2)

    logger.info("Saved docking analysis to %s", output_path)
    return output_path
