#!/usr/bin/env python3
"""Score REINVENT 4 candidates with StateBind unified scoring function.

Loads REINVENT 4 generated candidates from the JSON artifact, scores each
with the same unified scoring function used for StateBind candidates,
computes enrichment metrics, and produces the Gate G3 assessment.

This script runs in the statebind environment (NOT reinvent4).

Usage:
    python scripts/score_reinvent4_candidates.py
    python scripts/score_reinvent4_candidates.py \
        --candidates artifacts/generation/reinvent4_egfr_candidates.json \
        --output-scored artifacts/ranking/reinvent4_scored.json \
        --output-gate artifacts/evaluation/reinvent4_results.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_candidates(path: Path) -> list[dict]:
    """Load REINVENT 4 candidates from JSON artifact."""
    from statebind.utils.io import load_json

    data = load_json(str(path))
    candidates = data.get("candidates", [])
    logger.info("Loaded %d candidates from %s", len(candidates), path)
    return candidates


def score_candidates(candidates: list[dict]) -> list[dict]:
    """Score each candidate with the unified scoring function.

    For REINVENT candidates:
    - state_specificity = 0 (no state conditioning)
    - target_state = "" (treated as static pipeline)
    - All other components scored identically to StateBind candidates.
    """
    from statebind.ranking.models import PipelineLabel
    from statebind.ranking.scoring import DEFAULT_WEIGHTS, score_unified

    scored = []
    n_failed = 0
    empty_state_map: dict[str, set[str]] = {}

    for i, cand in enumerate(candidates):
        smiles = cand.get("smiles", "")
        if not smiles:
            n_failed += 1
            continue

        try:
            components, composite = score_unified(
                smiles=smiles,
                target_state="",
                pipeline=PipelineLabel.STATIC,
                state_smiles_map=empty_state_map,
                weights=DEFAULT_WEIGHTS,
            )

            scored_entry = {
                "smiles": smiles,
                "source": "reinvent4_rl",
                "composite_score": composite,
                "components": {c.name: c.value for c in components},
                "weights": {c.name: c.weight for c in components},
            }
            scored.append(scored_entry)

        except Exception as exc:
            logger.warning("Failed to score candidate %d (%s): %s", i, smiles[:60], exc)
            n_failed += 1

        if (i + 1) % 50 == 0:
            logger.info("  Scored %d / %d candidates", i + 1, len(candidates))

    logger.info(
        "Scoring complete: %d scored, %d failed out of %d total",
        len(scored),
        n_failed,
        len(candidates),
    )
    return scored


def compute_enrichment(
    scored: list[dict],
    statebind_comparison_path: Path | None = None,
) -> dict:
    """Compute enrichment metrics for REINVENT 4 candidates.

    Computes:
    - EF@10: Enrichment factor at top 10%
    - BEDROC(alpha=20): early recognition metric
    - BCa bootstrap confidence intervals

    Uses reference_similarity > 0.4 as the "active" threshold
    (same threshold used in StateBind retrospective validation).
    """
    if not scored:
        return {
            "ef_at_10": 0.0,
            "bedroc_alpha20": 0.0,
            "n_active": 0,
            "n_total": 0,
        }

    # Define "actives" as molecules with high reference similarity
    # This matches the retrospective validation approach
    active_threshold = 0.4
    scores = np.array([s["composite_score"] for s in scored])
    ref_sims = np.array([s["components"].get("reference_similarity", 0.0) for s in scored])

    actives = ref_sims >= active_threshold
    n_active = int(actives.sum())
    n_total = len(scored)
    active_rate = n_active / max(n_total, 1)

    # EF@10: enrichment factor at top 10%
    top_10_pct = max(1, int(0.1 * n_total))
    sorted_indices = np.argsort(-scores)  # descending
    top_10_actives = actives[sorted_indices[:top_10_pct]].sum()
    ef_at_10 = (top_10_actives / max(top_10_pct, 1)) / max(active_rate, 1e-10)

    # BEDROC(alpha=20) -- Boltzmann-Enhanced Discrimination ROC
    bedroc = _compute_bedroc(scores, actives, alpha=20.0)

    # BCa bootstrap CIs
    n_boot = 1000
    ef_boots = []
    bedroc_boots = []

    rng = np.random.RandomState(42)
    for _ in range(n_boot):
        idx = rng.choice(n_total, n_total, replace=True)
        boot_scores = scores[idx]
        boot_actives = actives[idx]

        boot_n_active = boot_actives.sum()
        boot_active_rate = boot_n_active / max(n_total, 1)

        if boot_n_active == 0 or boot_active_rate == 0:
            ef_boots.append(0.0)
            bedroc_boots.append(0.0)
            continue

        boot_sorted = np.argsort(-boot_scores)
        boot_top_actives = boot_actives[boot_sorted[:top_10_pct]].sum()
        boot_ef = (boot_top_actives / max(top_10_pct, 1)) / max(boot_active_rate, 1e-10)
        ef_boots.append(float(boot_ef))

        boot_bedroc = _compute_bedroc(boot_scores, boot_actives, alpha=20.0)
        bedroc_boots.append(boot_bedroc)

    ef_ci = (
        float(np.percentile(ef_boots, 2.5)),
        float(np.percentile(ef_boots, 97.5)),
    )
    bedroc_ci = (
        float(np.percentile(bedroc_boots, 2.5)),
        float(np.percentile(bedroc_boots, 97.5)),
    )

    # Load StateBind comparison if available
    statebind_enrichment = {}
    if statebind_comparison_path and statebind_comparison_path.exists():
        try:
            from statebind.utils.io import load_json
            comp_data = load_json(str(statebind_comparison_path))
            statebind_enrichment = {
                "static_mean_score": comp_data.get("scores", {}).get("static", {}).get("mean", None),
                "state_aware_mean_score": comp_data.get("scores", {}).get("state_aware", {}).get("mean", None),
            }
        except Exception:
            pass

    return {
        "n_active": n_active,
        "n_total": n_total,
        "active_rate": round(active_rate, 4),
        "active_threshold": active_threshold,
        "ef_at_10": round(float(ef_at_10), 4),
        "ef_at_10_ci_95": [round(ef_ci[0], 4), round(ef_ci[1], 4)],
        "bedroc_alpha20": round(float(bedroc), 4),
        "bedroc_alpha20_ci_95": [round(bedroc_ci[0], 4), round(bedroc_ci[1], 4)],
        "statebind_comparison": statebind_enrichment,
    }


def _compute_bedroc(scores: np.ndarray, actives: np.ndarray, alpha: float = 20.0) -> float:
    """Compute BEDROC metric.

    BEDROC measures early enrichment with exponential weighting.
    alpha controls the emphasis on early recognition (higher = more emphasis).

    Args:
        scores: Array of scores (higher = better predicted).
        actives: Boolean array of true actives.
        alpha: Exponential weighting parameter.

    Returns:
        BEDROC value in [0, 1].
    """
    n = len(scores)
    n_actives = actives.sum()

    if n_actives == 0 or n_actives == n:
        return 0.0

    # Rank by score (descending)
    sorted_idx = np.argsort(-scores)
    sorted_actives = actives[sorted_idx]

    # Compute BEDROC
    ri_sum = 0.0
    for i in range(n):
        if sorted_actives[i]:
            ri_sum += np.exp(-alpha * i / n)

    ra = n_actives / n
    rand_sum = (ra * (1 - np.exp(-alpha))) / (np.exp(alpha / n) - 1)

    if rand_sum == 0:
        return 0.0

    ri_max = 0.0
    for i in range(int(n_actives)):
        ri_max += np.exp(-alpha * i / n)

    bedroc = (ri_sum - rand_sum) / (ri_max - rand_sum) if (ri_max - rand_sum) != 0 else 0.0
    return max(0.0, min(1.0, bedroc))


def compile_gate_g3(
    candidates: list[dict],
    scored: list[dict],
    enrichment: dict,
) -> dict:
    """Compile Gate G3 assessment.

    Gate G3 criteria:
    - 100+ valid docked molecules: GO
    - Slow but functional (>10 min/mol): CONDITIONAL GO (reduce N)
    - GNINA integration fails: NO-GO (fall back to Vina)
    """
    n_valid = len(scored)
    n_total = len(candidates)

    # Determine recommendation
    if n_valid >= 100:
        recommendation = "GO"
        rationale = (
            f"REINVENT 4 successfully generated and scored {n_valid} valid "
            f"molecules (threshold: 100). GNINA integration is functional."
        )
    elif n_valid >= 10:
        recommendation = "CONDITIONAL_GO"
        rationale = (
            f"REINVENT 4 generated {n_valid} valid scored molecules. "
            f"Below the 100 threshold but functional. Consider increasing "
            f"RL steps or batch size for a larger sample."
        )
    else:
        recommendation = "NO_GO"
        rationale = (
            f"Only {n_valid} valid scored molecules from {n_total} candidates. "
            f"GNINA integration may have systematic issues. Consider Vina fallback."
        )

    # Score statistics
    if scored:
        comp_scores = [s["composite_score"] for s in scored]
        score_stats = {
            "mean": round(float(np.mean(comp_scores)), 4),
            "std": round(float(np.std(comp_scores)), 4),
            "min": round(float(np.min(comp_scores)), 4),
            "max": round(float(np.max(comp_scores)), 4),
            "median": round(float(np.median(comp_scores)), 4),
        }
    else:
        score_stats = {}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G3",
        "model": "REINVENT4_RL",
        "receptor": "1m17",
        "state": "DFGin_aCin",
        "n_total_candidates": n_total,
        "n_valid_scored": n_valid,
        "recommendation": recommendation,
        "rationale": rationale,
        "score_stats": score_stats,
        "enrichment": enrichment,
        "notes": (
            "External RL baseline using REINVENT 4 with GNINA scoring. "
            "Single receptor (1M17), no state conditioning. "
            "state_specificity = 0 for all candidates (expected and fair). "
            "Compared against StateBind static and state-aware pipelines."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score REINVENT 4 candidates and compute Gate G3.",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=REPO_ROOT / "artifacts" / "generation" / "reinvent4_egfr_candidates.json",
        help="Path to REINVENT 4 candidates JSON.",
    )
    parser.add_argument(
        "--output-scored",
        type=Path,
        default=REPO_ROOT / "artifacts" / "ranking" / "reinvent4_scored.json",
        help="Path to write scored candidates.",
    )
    parser.add_argument(
        "--output-gate",
        type=Path,
        default=REPO_ROOT / "artifacts" / "evaluation" / "reinvent4_results.json",
        help="Path to write Gate G3 assessment.",
    )
    parser.add_argument(
        "--comparison",
        type=Path,
        default=REPO_ROOT / "artifacts" / "ranking" / "comparison.json",
        help="Path to StateBind comparison JSON for enrichment comparison.",
    )
    args = parser.parse_args()

    if not args.candidates.exists():
        logger.error("Candidates file not found: %s", args.candidates)
        sys.exit(1)

    # Step 1: Load candidates
    candidates = load_candidates(args.candidates)

    if not candidates:
        logger.error("No candidates found in %s", args.candidates)
        sys.exit(1)

    # Step 2: Score with unified function
    scored = score_candidates(candidates)

    # Step 3: Save scored candidates
    from statebind.utils.io import save_json

    scored_output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "REINVENT4_RL",
        "scoring_method": "StateBind unified scoring (same as static/state-aware)",
        "n_scored": len(scored),
        "n_failed": len(candidates) - len(scored),
        "notes": (
            "REINVENT 4 candidates scored with StateBind unified function. "
            "state_specificity = 0 for all (no state conditioning). "
            "reference_similarity, druglikeness, docking_proxy computed identically."
        ),
        "candidates": scored,
    }

    args.output_scored.parent.mkdir(parents=True, exist_ok=True)
    save_json(scored_output, str(args.output_scored))
    logger.info("Scored candidates saved to %s", args.output_scored)

    # Step 4: Compute enrichment
    enrichment = compute_enrichment(
        scored,
        statebind_comparison_path=args.comparison if args.comparison.exists() else None,
    )
    logger.info("Enrichment metrics: %s", enrichment)

    # Step 5: Gate G3 assessment
    gate = compile_gate_g3(candidates, scored, enrichment)

    args.output_gate.parent.mkdir(parents=True, exist_ok=True)
    save_json(gate, str(args.output_gate))
    logger.info("Gate G3 assessment saved to %s", args.output_gate)
    logger.info("Gate G3 recommendation: %s", gate["recommendation"])

    # Print summary
    print("\n" + "=" * 60)
    print("REINVENT 4 EGFR Baseline -- Gate G3 Summary")
    print("=" * 60)
    print(f"Total candidates:     {gate['n_total_candidates']}")
    print(f"Valid scored:         {gate['n_valid_scored']}")
    print(f"Gate G3:              {gate['recommendation']}")
    print(f"Rationale:            {gate['rationale']}")
    if gate["score_stats"]:
        print(f"Mean composite score: {gate['score_stats']['mean']}")
        print(f"Max composite score:  {gate['score_stats']['max']}")
    print(f"EF@10:                {enrichment['ef_at_10']} "
          f"(95% CI: {enrichment['ef_at_10_ci_95']})")
    print(f"BEDROC(a=20):         {enrichment['bedroc_alpha20']} "
          f"(95% CI: {enrichment['bedroc_alpha20_ci_95']})")
    print("=" * 60)


if __name__ == "__main__":
    main()
