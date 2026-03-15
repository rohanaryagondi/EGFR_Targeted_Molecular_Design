"""Evaluation module for baseline outputs.

Computes validity, uniqueness, diversity, and property distribution
statistics for a baseline run. These same metrics will be applied
to the state-aware pipeline for fair comparison.
"""

from __future__ import annotations

import statistics

from statebind.baselines.filtering import _is_valid_smiles
from statebind.baselines.models import BaselineEvaluation, RankedCandidates
from statebind.baselines.scoring import _tanimoto_ngram


def evaluate_baseline(
    ranked: RankedCandidates,
    top_k: int = 10,
) -> BaselineEvaluation:
    """Evaluate a baseline run's output quality.

    Metrics:
    - Validity: fraction of candidates with parseable SMILES
    - Uniqueness: fraction of unique SMILES strings
    - Diversity: 1 - mean pairwise Tanimoto similarity (intra-set)
    - Property stats: per-score-component mean/std/min/max
    - Top-K: identifiers of top-ranked candidates

    Args:
        ranked: Ranked candidates from the scoring pipeline.
        top_k: Number of top candidates to highlight.

    Returns:
        BaselineEvaluation with all metrics.
    """
    candidates = ranked.candidates
    n = len(candidates)

    if n == 0:
        return BaselineEvaluation(
            run_id=ranked.run_id,
            notes="No candidates to evaluate.",
        )

    # ── Validity ────────────────────────────────────────────────────
    n_valid = sum(1 for c in candidates if _is_valid_smiles(c.smiles))
    validity_rate = n_valid / n

    # ── Uniqueness ──────────────────────────────────────────────────
    unique_smiles = set(c.smiles for c in candidates)
    uniqueness_rate = len(unique_smiles) / n

    # ── Diversity ───────────────────────────────────────────────────
    # Mean pairwise distance = 1 - mean pairwise similarity
    diversity_score = _compute_diversity(candidates)

    # ── Score statistics ────────────────────────────────────────────
    score_stats = _compute_score_stats(candidates)

    # ── Top-K ───────────────────────────────────────────────────────
    top_k_ids = [c.candidate_id for c in candidates[:min(top_k, n)]]

    return BaselineEvaluation(
        run_id=ranked.run_id,
        n_candidates_input=n,
        n_candidates_filtered=n,  # These are post-filtering
        n_candidates_ranked=n,
        validity_rate=round(validity_rate, 4),
        uniqueness_rate=round(uniqueness_rate, 4),
        diversity_score=round(diversity_score, 4),
        score_stats=score_stats,
        top_k_candidates=top_k_ids,
        notes=(
            f"Evaluated {n} candidates. "
            f"Diversity computed via SMILES 3-gram Tanimoto (heuristic). "
            f"Score component 'docking_proxy' is a STUB (constant 0.5)."
        ),
    )


def _compute_diversity(candidates: list) -> float:
    """Compute intra-set diversity as 1 - mean pairwise similarity.

    For large sets, samples pairs to keep runtime manageable.
    """
    smiles_list = [c.smiles for c in candidates if c.smiles]
    n = len(smiles_list)
    if n < 2:
        return 0.0

    # For small sets, compute all pairs
    max_pairs = 500
    similarities = []

    if n * (n - 1) // 2 <= max_pairs:
        for i in range(n):
            for j in range(i + 1, n):
                sim = _tanimoto_ngram(smiles_list[i], smiles_list[j])
                similarities.append(sim)
    else:
        # Sample pairs deterministically
        import hashlib
        for idx in range(max_pairs):
            h = int(hashlib.md5(str(idx).encode()).hexdigest(), 16)
            i = h % n
            j = (h // n) % n
            if i == j:
                j = (j + 1) % n
            sim = _tanimoto_ngram(smiles_list[i], smiles_list[j])
            similarities.append(sim)

    mean_sim = statistics.mean(similarities) if similarities else 0.0
    return 1.0 - mean_sim


def _compute_score_stats(candidates: list) -> dict[str, dict[str, float]]:
    """Compute per-score-component statistics."""
    stats = {}

    # Composite score
    composites = [c.composite_score for c in candidates]
    stats["composite_score"] = _basic_stats(composites)

    # Individual components
    component_names = set()
    for c in candidates:
        for s in c.scores:
            component_names.add(s.name)

    for name in sorted(component_names):
        values = []
        for c in candidates:
            val = c.get_score(name)
            if val is not None:
                values.append(val)
        if values:
            stats[name] = _basic_stats(values)

    return stats


def _basic_stats(values: list[float]) -> dict[str, float]:
    """Compute mean, std, min, max for a list of values."""
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "n": 0}

    mean = statistics.mean(values)
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "n": len(values),
    }
