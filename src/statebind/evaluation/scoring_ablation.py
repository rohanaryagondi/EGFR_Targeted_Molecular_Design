"""Scoring ablation analysis: systematic component removal.

Identifies which scoring components drive retrospective enrichment by
zeroing each component in turn (leave-one-out) and re-ranking with
renormalized weights.  Also provides the 3-component "fairness check"
(P11) that tests whether enrichment survives without state_specificity.

Key design:
- Does NOT re-compute per-component scores.  Each candidate already has
  reference_similarity, druglikeness, docking_proxy, and
  state_specificity values from the original scoring run.
- Only the composite score (weighted sum) is recomputed with new weights.
- All weight dicts sum to 1.0 (renormalized after zeroing).
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from statebind.ranking.models import (
    RankedPool,
    UnifiedScoredCandidate,
)

logger = logging.getLogger(__name__)


# ── Models ────────────────────────────────────────────────────────────────


class AblationConfig(BaseModel):
    """Weight configuration for one ablation experiment."""

    name: str
    weights: dict[str, float]
    zeroed_component: str | None = None


class AblationResult(BaseModel):
    """Metrics for one ablation configuration."""

    config: AblationConfig
    ef_at_10: float
    ef_ci_lower: float
    ef_ci_upper: float
    bedroc: float | None = None
    bedroc_ci_lower: float | None = None
    bedroc_ci_upper: float | None = None
    mean_score: float
    n_candidates: int


class AblationBattery(BaseModel):
    """Full ablation battery results."""

    results: list[AblationResult] = Field(default_factory=list)
    base_weights: dict[str, float]
    generated_at: str = Field(default="")
    notes: str = Field(default="")


# ── Config generation ─────────────────────────────────────────────────────


def generate_ablation_configs(
    base_weights: dict[str, float],
) -> list[AblationConfig]:
    """Generate leave-one-out ablation configs from base weights.

    Returns 5 configs: 1 baseline (original weights) + 4 ablations
    (one per component zeroed, remaining renormalized to sum=1.0).

    Args:
        base_weights: Original weight dict (must have exactly 4 keys that
            sum to 1.0).

    Returns:
        List of 5 ``AblationConfig`` objects.

    Raises:
        ValueError: If base_weights is empty or all weights are zero.
    """
    if not base_weights:
        raise ValueError("base_weights must not be empty")

    total = sum(base_weights.values())
    if abs(total) < 1e-8:
        raise ValueError(
            "All weights are zero -- cannot generate ablation configs"
        )

    configs: list[AblationConfig] = [
        AblationConfig(
            name="baseline",
            weights=dict(base_weights),
            zeroed_component=None,
        ),
    ]

    for component in sorted(base_weights.keys()):
        remaining_total = total - base_weights[component]
        if abs(remaining_total) < 1e-8:
            raise ValueError(
                f"Zeroing '{component}' leaves all remaining weights at zero "
                f"-- cannot renormalize"
            )
        renormalized = {}
        for k, v in base_weights.items():
            if k == component:
                renormalized[k] = 0.0
            else:
                renormalized[k] = round(v / remaining_total, 4)

        # Fix rounding: adjust the largest remaining weight so sum == 1.0
        rounding_error = 1.0 - sum(renormalized.values())
        if abs(rounding_error) > 1e-8:
            non_zero = [k for k, v in renormalized.items() if v > 0]
            if non_zero:
                largest = max(non_zero, key=lambda k: renormalized[k])
                renormalized[largest] = round(
                    renormalized[largest] + rounding_error, 4
                )

        configs.append(
            AblationConfig(
                name=f"no_{component}",
                weights=renormalized,
                zeroed_component=component,
            ),
        )

    return configs


# ── Reranking ─────────────────────────────────────────────────────────────


def rerank_with_weights(
    candidates: list[UnifiedScoredCandidate],
    weights: dict[str, float],
) -> list[UnifiedScoredCandidate]:
    """Recompute composite scores and re-rank using new weights.

    Takes existing scored candidates (with per-component scores already
    computed) and recomputes ONLY the composite score using the supplied
    weights.  Individual component scores are NOT recomputed.

    Args:
        candidates: Scored candidates with existing per-component scores.
        weights: New weight dict mapping component name to weight.

    Returns:
        New list of candidates (deep-copied) sorted by new composite score.

    Raises:
        ValueError: If candidates list is empty or weights are invalid.
    """
    if not candidates:
        raise ValueError("candidates list must not be empty")

    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 1e-3:
        raise ValueError(
            f"Weights must sum to 1.0, got {total_weight:.4f}"
        )

    reranked: list[UnifiedScoredCandidate] = []
    for c in candidates:
        # Deep copy via model_copy
        new_c = c.model_copy(deep=True)

        # Update weights on each component
        for sc in new_c.scores:
            if sc.name in weights:
                sc.weight = weights[sc.name]

        # Recompute composite
        new_c.composite_score = round(
            sum(sc.value * sc.weight for sc in new_c.scores), 4
        )
        reranked.append(new_c)

    # Sort descending by new composite
    reranked.sort(key=lambda x: x.composite_score, reverse=True)

    # Update ranks
    for i, c in enumerate(reranked):
        c.rank_in_pipeline = i + 1

    return reranked


# ── Ablation battery ──────────────────────────────────────────────────────


def _compute_similarities(
    candidates: list[UnifiedScoredCandidate],
    future_drug_smiles: list[str],
) -> list[float]:
    """Compute max Tanimoto similarity to any future drug for each candidate.

    Candidates must already be sorted by composite_score descending.
    Returns list in the same order as candidates.
    """
    from statebind.chemistry.fingerprints import compute_morgan_similarity

    sims: list[float] = []
    for c in candidates:
        max_sim = 0.0
        for drug_smi in future_drug_smiles:
            sim = compute_morgan_similarity(c.smiles, drug_smi)
            if sim > max_sim:
                max_sim = sim
        sims.append(round(max_sim, 4))
    return sims


def run_ablation_battery(
    candidates: list[UnifiedScoredCandidate],
    future_drugs: list[dict[str, Any]],
    base_weights: dict[str, float],
    threshold: float = 0.4,
    top_k: int = 10,
    n_bootstrap: int = 10000,
    seed: int = 42,
) -> list[AblationResult]:
    """Run the full ablation battery.

    For each config (baseline + 4 ablations):
    1. Rerank candidates with the config's weights
    2. Compute max-similarity-to-future-drug for each candidate
    3. Compute EF@K with BCa bootstrap CI
    4. Compute BEDROC with BCa bootstrap CI (if RDKit available)

    Args:
        candidates: Scored candidates from the state-aware pipeline.
        future_drugs: List of dicts with at least a 'smiles' key.
        base_weights: Original scoring weights (e.g., DEFAULT_WEIGHTS).
        threshold: Similarity threshold for EF "hit" definition.
        top_k: K for EF@K.
        n_bootstrap: Number of bootstrap resamples.
        seed: Random seed.

    Returns:
        List of ``AblationResult`` objects, one per config.
    """
    from statebind.evaluation.retrospective import (
        compute_bedroc,
        compute_enrichment_factor,
        compute_enrichment_with_ci,
    )

    configs = generate_ablation_configs(base_weights)
    future_drug_smiles = [d["smiles"] for d in future_drugs]

    results: list[AblationResult] = []

    for config in configs:
        logger.info("Running ablation: %s", config.name)

        # Rerank (baseline config uses original weights, so order may differ
        # only by float rounding -- that is expected)
        reranked = rerank_with_weights(candidates, config.weights)

        # Compute similarities in new rank order
        sims = _compute_similarities(reranked, future_drug_smiles)

        # EF + BEDROC with CI
        enrichment = compute_enrichment_with_ci(
            candidate_similarities=sims,
            threshold=threshold,
            top_k=top_k,
            n_bootstrap=n_bootstrap,
            seed=seed,
        )

        mean_score = round(
            sum(c.composite_score for c in reranked) / len(reranked), 4
        ) if reranked else 0.0

        results.append(
            AblationResult(
                config=config,
                ef_at_10=enrichment["ef_point"],
                ef_ci_lower=enrichment["ef_ci_lower"],
                ef_ci_upper=enrichment["ef_ci_upper"],
                bedroc=enrichment.get("bedroc_point"),
                bedroc_ci_lower=enrichment.get("bedroc_ci_lower"),
                bedroc_ci_upper=enrichment.get("bedroc_ci_upper"),
                mean_score=mean_score,
                n_candidates=len(reranked),
            )
        )

        logger.info(
            "  %s: EF@%d=%.4f [%.4f, %.4f]  mean_score=%.4f",
            config.name,
            top_k,
            enrichment["ef_point"],
            enrichment["ef_ci_lower"],
            enrichment["ef_ci_upper"],
            mean_score,
        )

    return results
