"""Practical Molecular Optimization (PMO) compute-matched comparison.

Implements the framework from Gao et al. 2022 for fair comparison of
molecular design pipelines under an equal oracle (GNINA docking) budget.

The core problem: static pipeline docks ~30 candidates while state-aware
docks ~461 (15:1 oracle call imbalance).  PMO fixes this by giving each
pipeline the same budget of N GNINA docking calls, then comparing the
best molecules found within that budget.

Key design:
- Pre-filter scoring uses ONLY cheap descriptors (Tanimoto, QED,
  Lipinski, property ranges) -- no GNINA calls.
- Equal budget means equal GNINA calls, not equal candidates generated.
- AUC curve tracks how top-10 average improves as oracle calls accumulate.
- State-aware may use multiple receptors; budget is per-pipeline total.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from pydantic import BaseModel, Field

from statebind.baselines.filtering import compute_properties
from statebind.baselines.scoring import (
    _has_rdkit,
    _score_druglikeness,
    _score_druglikeness_enhanced,
    _score_reference_similarity,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════


class OracleCall(BaseModel):
    """Record of a single oracle (docking) call."""

    smiles: str
    score: float
    rank_at_call: int = Field(
        default=0, description="Which call number this was (1-indexed)"
    )


class OracleBudget(BaseModel):
    """Tracks oracle (GNINA docking) calls against a fixed budget.

    The budget enforces compute-matched comparison: both pipelines
    get exactly N docking calls, no more.
    """

    total_budget: int = Field(default=500, ge=1)
    calls_used: int = Field(default=0, ge=0)
    results: list[OracleCall] = Field(default_factory=list)

    @property
    def remaining(self) -> int:
        """Number of oracle calls still available."""
        return max(0, self.total_budget - self.calls_used)

    @property
    def is_exhausted(self) -> bool:
        """Whether the budget has been fully consumed."""
        return self.calls_used >= self.total_budget

    def record_call(self, smiles: str, score: float) -> None:
        """Record one oracle call, consuming one unit of budget.

        Args:
            smiles: SMILES string that was docked.
            score: Normalized docking score in [0, 1].

        Raises:
            RuntimeError: If the budget is exhausted.
        """
        if self.is_exhausted:
            raise RuntimeError(
                f"Oracle budget exhausted: {self.calls_used}/{self.total_budget} "
                f"calls used. Cannot record additional call for {smiles!r}."
            )
        self.calls_used += 1
        self.results.append(
            OracleCall(
                smiles=smiles,
                score=round(score, 4),
                rank_at_call=self.calls_used,
            )
        )


class AUCPoint(BaseModel):
    """Single point on the AUC curve: top-10 avg vs oracle calls used."""

    oracle_calls: int
    top_10_avg: float


class PMOResult(BaseModel):
    """Result of running one pipeline under a fixed oracle budget."""

    pipeline: str = Field(description="'static' or 'state_aware'")
    budget: int
    calls_used: int
    top_10_avg_score: float = Field(
        description="Average score of the top 10 molecules found"
    )
    ef_at_10: float | None = Field(
        default=None,
        description="Enrichment factor at 10 (if reference actives available)",
    )
    ef_ci_lower: float | None = Field(default=None)
    ef_ci_upper: float | None = Field(default=None)
    bedroc: float | None = Field(
        default=None,
        description="BEDROC early enrichment (if reference actives available)",
    )
    auc_curve: list[AUCPoint] = Field(
        default_factory=list,
        description="Top-10 avg score vs oracle calls used",
    )
    all_scores: list[OracleCall] = Field(
        default_factory=list,
        description="All oracle call results in order",
    )
    prefilter_stats: dict[str, Any] = Field(
        default_factory=dict,
        description="Statistics from the pre-filter stage",
    )
    generated_at: str = Field(default="")
    notes: str = Field(default="")


class PMOComparison(BaseModel):
    """Head-to-head comparison of two pipelines under equal oracle budgets."""

    static_result: PMOResult
    state_aware_result: PMOResult
    budget: int
    auc_delta: float = Field(
        default=0.0,
        description="State-aware AUC minus static AUC (positive = SA better)",
    )
    top_10_delta: float = Field(
        default=0.0,
        description="State-aware top-10 avg minus static top-10 avg",
    )
    winner: str = Field(
        default="",
        description="'static', 'state_aware', or 'tie'",
    )
    generated_at: str = Field(default="")
    notes: str = Field(default="")


# ═══════════════════════════════════════════════════════════════════════════
# Pre-filter scoring (cheap — no GNINA)
# ═══════════════════════════════════════════════════════════════════════════


def prefilter_score(smiles: str) -> float:
    """Score a candidate using ONLY cheap descriptors (no GNINA).

    Combines:
    - Reference similarity (Tanimoto to erlotinib/gefitinib): weight 0.5
    - Druglikeness (QED+Lipinski or heuristic): weight 0.5

    This is used to prioritize which candidates receive scarce oracle
    (docking) calls.  Higher score = dock first.

    Args:
        smiles: SMILES string.

    Returns:
        Score in [0, 1].
    """
    if not smiles:
        return 0.0

    sim = _score_reference_similarity(smiles)

    if _has_rdkit():
        drug = _score_druglikeness_enhanced(smiles)
    else:
        props = compute_properties(smiles)
        drug = _score_druglikeness(props)

    # Equal weight to similarity and druglikeness
    return round(0.5 * sim + 0.5 * drug, 4)


# ═══════════════════════════════════════════════════════════════════════════
# AUC curve computation
# ═══════════════════════════════════════════════════════════════════════════


def _compute_auc_curve(
    results: list[OracleCall],
    sample_interval: int = 10,
) -> list[AUCPoint]:
    """Compute the AUC curve: top-10 avg score vs oracle calls used.

    Samples at every ``sample_interval`` calls plus the final call count.

    Args:
        results: Ordered list of oracle call results.
        sample_interval: How often to record a point (every N calls).

    Returns:
        List of AUCPoint in order of increasing oracle_calls.
    """
    if not results:
        return []

    curve: list[AUCPoint] = []
    scores_so_far: list[float] = []

    for i, call in enumerate(results, 1):
        scores_so_far.append(call.score)
        if i % sample_interval == 0 or i == len(results):
            # Top-10 average of best scores seen so far
            top_10 = sorted(scores_so_far, reverse=True)[:10]
            avg = round(sum(top_10) / len(top_10), 4)
            curve.append(AUCPoint(oracle_calls=i, top_10_avg=avg))

    return curve


def _compute_auc_area(curve: list[AUCPoint]) -> float:
    """Compute area under the AUC curve via trapezoidal rule.

    Args:
        curve: List of AUCPoint sorted by oracle_calls.

    Returns:
        Area under the curve.  Higher = better (found good molecules sooner).
    """
    if len(curve) < 2:
        return 0.0

    area = 0.0
    for i in range(1, len(curve)):
        dx = curve[i].oracle_calls - curve[i - 1].oracle_calls
        avg_y = (curve[i].top_10_avg + curve[i - 1].top_10_avg) / 2.0
        area += dx * avg_y

    return round(area, 4)


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline execution under budget
# ═══════════════════════════════════════════════════════════════════════════


def run_pipeline_with_budget(
    pipeline_label: str,
    budget: int,
    candidates: list[str],
    dock_fn: Callable[[str], float],
    sample_interval: int = 10,
) -> PMOResult:
    """Run a pipeline under a fixed oracle budget.

    Steps:
    1. Pre-filter all candidates by cheap descriptors (no GNINA).
    2. Sort by pre-filter score descending.
    3. Dock the top-N candidates where N = budget.
    4. Track AUC: top-10 avg score vs oracle calls used.

    Args:
        pipeline_label: "static" or "state_aware".
        budget: Maximum number of oracle (GNINA) calls.
        candidates: List of SMILES strings (typically many more than budget).
        dock_fn: Callable that takes a SMILES string and returns a
            normalized docking score in [0, 1].  This is the oracle.
        sample_interval: How often to sample AUC curve points.

    Returns:
        PMOResult with scores, AUC curve, and statistics.
    """
    if budget < 1:
        raise ValueError(f"Budget must be >= 1, got {budget}")
    if not candidates:
        raise ValueError("No candidates provided")

    # Deduplicate candidates
    unique_candidates = list(dict.fromkeys(candidates))
    n_before_dedup = len(candidates)
    n_after_dedup = len(unique_candidates)

    # Step 1: Pre-filter score (cheap)
    logger.info(
        "Pre-filtering %d unique candidates for %s pipeline",
        n_after_dedup,
        pipeline_label,
    )
    scored_candidates: list[tuple[str, float]] = []
    for smi in unique_candidates:
        pf_score = prefilter_score(smi)
        scored_candidates.append((smi, pf_score))

    # Step 2: Sort by pre-filter score descending
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    # Step 3: Dock the top-N by pre-filter (N = budget)
    n_to_dock = min(budget, len(scored_candidates))
    oracle = OracleBudget(total_budget=budget)

    logger.info(
        "Docking top %d candidates (budget=%d) for %s",
        n_to_dock,
        budget,
        pipeline_label,
    )

    for smiles, _pf_score in scored_candidates[:n_to_dock]:
        try:
            dock_score = dock_fn(smiles)
            oracle.record_call(smiles, dock_score)
        except RuntimeError:
            # Budget exhausted (should not happen given n_to_dock logic)
            logger.warning("Budget exhausted unexpectedly")
            break
        except Exception as exc:
            logger.warning("Docking failed for %s: %s", smiles, exc)
            # Record a score of 0 for failed docking
            oracle.record_call(smiles, 0.0)

    # Step 4: AUC curve
    auc_curve = _compute_auc_curve(oracle.results, sample_interval)

    # Top-10 average
    all_scores = sorted(
        [r.score for r in oracle.results], reverse=True
    )
    top_10 = all_scores[:10]
    top_10_avg = round(sum(top_10) / len(top_10), 4) if top_10 else 0.0

    now = datetime.now(timezone.utc).isoformat()

    prefilter_stats = {
        "n_candidates_input": n_before_dedup,
        "n_candidates_unique": n_after_dedup,
        "n_docked": oracle.calls_used,
        "prefilter_score_max": round(scored_candidates[0][1], 4)
        if scored_candidates
        else 0.0,
        "prefilter_score_min_docked": round(
            scored_candidates[min(n_to_dock, len(scored_candidates)) - 1][1], 4
        )
        if scored_candidates
        else 0.0,
    }

    return PMOResult(
        pipeline=pipeline_label,
        budget=budget,
        calls_used=oracle.calls_used,
        top_10_avg_score=top_10_avg,
        auc_curve=auc_curve,
        all_scores=oracle.results,
        prefilter_stats=prefilter_stats,
        generated_at=now,
        notes=(
            f"{pipeline_label} pipeline: docked {oracle.calls_used}/{budget} "
            f"candidates from {n_after_dedup} unique pre-filtered."
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Comparison
# ═══════════════════════════════════════════════════════════════════════════


def compare_pmo(
    static_result: PMOResult,
    state_aware_result: PMOResult,
) -> PMOComparison:
    """Compare two pipeline results under equal oracle budgets.

    Computes:
    - AUC difference (state_aware - static)
    - Top-10 average difference
    - Winner determination

    Args:
        static_result: PMOResult from the static pipeline.
        state_aware_result: PMOResult from the state-aware pipeline.

    Returns:
        PMOComparison with delta metrics and winner.
    """
    static_auc = _compute_auc_area(static_result.auc_curve)
    sa_auc = _compute_auc_area(state_aware_result.auc_curve)
    auc_delta = round(sa_auc - static_auc, 4)

    top_10_delta = round(
        state_aware_result.top_10_avg_score - static_result.top_10_avg_score, 4
    )

    # Winner: higher top-10 avg wins; tie if within 0.001
    if abs(top_10_delta) < 0.001:
        winner = "tie"
    elif top_10_delta > 0:
        winner = "state_aware"
    else:
        winner = "static"

    now = datetime.now(timezone.utc).isoformat()

    return PMOComparison(
        static_result=static_result,
        state_aware_result=state_aware_result,
        budget=static_result.budget,
        auc_delta=auc_delta,
        top_10_delta=top_10_delta,
        winner=winner,
        generated_at=now,
        notes=(
            f"PMO comparison: budget={static_result.budget}, "
            f"static top-10={static_result.top_10_avg_score:.4f}, "
            f"state_aware top-10={state_aware_result.top_10_avg_score:.4f}, "
            f"winner={winner}"
        ),
    )


def format_comparison_table(comparison: PMOComparison) -> str:
    """Format a human-readable comparison table.

    Args:
        comparison: PMOComparison result.

    Returns:
        Multi-line string table.
    """
    sr = comparison.static_result
    sar = comparison.state_aware_result

    static_auc = _compute_auc_area(sr.auc_curve)
    sa_auc = _compute_auc_area(sar.auc_curve)

    lines = [
        "",
        "=" * 65,
        "PMO Compute-Matched Comparison",
        "=" * 65,
        f"  Oracle budget:          {comparison.budget} GNINA calls per pipeline",
        "",
        f"  {'Metric':<30} {'Static':>12} {'State-Aware':>12}",
        f"  {'-' * 30} {'-' * 12} {'-' * 12}",
        f"  {'Oracle calls used':<30} {sr.calls_used:>12} {sar.calls_used:>12}",
        f"  {'Top-10 avg score':<30} {sr.top_10_avg_score:>12.4f} {sar.top_10_avg_score:>12.4f}",
        f"  {'AUC (area under curve)':<30} {static_auc:>12.4f} {sa_auc:>12.4f}",
    ]

    if sr.prefilter_stats and sar.prefilter_stats:
        lines.append(
            f"  {'Candidates (unique)':<30} "
            f"{sr.prefilter_stats.get('n_candidates_unique', '?'):>12} "
            f"{sar.prefilter_stats.get('n_candidates_unique', '?'):>12}"
        )

    lines.extend([
        "",
        f"  Top-10 delta (SA - static):  {comparison.top_10_delta:+.4f}",
        f"  AUC delta (SA - static):     {comparison.auc_delta:+.4f}",
        f"  Winner:                      {comparison.winner}",
        "=" * 65,
        "",
    ])

    return "\n".join(lines)
