"""Ablation C analysis: conditioned vs unconditioned VAE.

Scores candidates with unified scoring, computes retrospective enrichment,
VAE quality metrics, and produces Gate G2 recommendation.

Pre-registration ref: commit 9e7cf96 (docs/pre-registration.md)

Usage:
    module load Python/3.12.3
    source envs/statebind/bin/activate
    cd repo/
    python scripts/run_ablation_c_analysis.py
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

# ---------------------------------------------------------------------------
# Imports from statebind
# ---------------------------------------------------------------------------

from statebind.evaluation.statistics import (
    bca_bootstrap_confidence_interval,
    cliff_delta,
    cohens_d,
    mann_whitney_u,
)
from statebind.evaluation.retrospective import (
    compute_bedroc,
    compute_candidate_future_similarities,
    compute_enrichment_factor,
    compute_enrichment_with_ci,
    compute_novelty,
    get_future_drugs,
)
from statebind.evaluation.vae_metrics import (
    compute_fcd,
    compute_internal_diversity,
    compute_novelty as vae_compute_novelty,
)
from statebind.ranking.models import PipelineLabel
from statebind.ranking.scoring import DEFAULT_WEIGHTS, score_unified

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ablation_c")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNCONDITIONED_SEEDS = [42, 123, 7]
RETROSPECTIVE_CUTOFF = 2010
SIMILARITY_THRESHOLD = 0.4
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 42

# Pre-registration thresholds (commit 9e7cf96)
THRESHOLD_STRONG_GO = 0.8
THRESHOLD_GO = 0.5
THRESHOLD_PIVOT = 0.3


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file."""
    with open(path) as f:
        return json.load(f)


def save_json(data: dict[str, Any], path: Path) -> None:
    """Save a JSON file with pretty-printing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Saved: %s", path)


def extract_smiles(candidates: list[dict[str, Any]]) -> list[str]:
    """Extract SMILES from candidate list."""
    return [c["smiles"] for c in candidates]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_candidates(
    candidates: list[dict[str, Any]],
    label: str,
) -> list[dict[str, Any]]:
    """Score candidates with unified scoring function.

    For ablation C, all candidates are scored identically:
    - state_specificity = 0 for both conditions (unconditioned has no state,
      and we use empty state_smiles_map to make the comparison fair)
    - pipeline = STATIC for both (ensures identical treatment)

    This isolates the VAE's generation quality from the scoring system's
    state-specificity bonus.

    Args:
        candidates: List of dicts with at least 'smiles' key.
        label: Description for logging.

    Returns:
        List of scored candidate dicts sorted by composite_score descending.
    """
    scored = []
    empty_map: dict[str, set[str]] = {}
    n_total = len(candidates)

    for i, cand in enumerate(candidates):
        smiles = cand["smiles"]
        if (i + 1) % 50 == 0 or i == 0:
            logger.info("  Scoring %s [%d/%d]", label, i + 1, n_total)

        try:
            components, composite = score_unified(
                smiles=smiles,
                target_state="",
                pipeline=PipelineLabel.STATIC,
                state_smiles_map=empty_map,
                weights=DEFAULT_WEIGHTS,
            )

            scored.append({
                "smiles": smiles,
                "composite_score": composite,
                "state": cand.get("state", ""),
                "components": {c.name: c.value for c in components},
                "candidate_id": str(uuid.uuid4())[:8],
            })
        except Exception as e:
            logger.warning("  Failed to score %s: %s", smiles[:40], e)
            continue

    # Sort descending by composite_score
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Retrospective enrichment
# ---------------------------------------------------------------------------


def compute_retrospective(
    scored_candidates: list[dict[str, Any]],
    training_smiles: set[str],
    label: str,
) -> dict[str, Any]:
    """Compute retrospective enrichment metrics with BCa bootstrap CIs.

    Args:
        scored_candidates: Scored and sorted (desc) candidate dicts.
        training_smiles: Set of training SMILES for novelty.
        label: Description for logging.

    Returns:
        Dict with EF@10, BEDROC, CIs, novelty, etc.
    """
    future_drugs = get_future_drugs(RETROSPECTIVE_CUTOFF)
    future_smiles = [d["smiles"] for d in future_drugs]
    cand_smiles = extract_smiles(scored_candidates)

    logger.info("  Computing similarities to %d future drugs for %s (%d candidates)",
                len(future_drugs), label, len(cand_smiles))

    # Max similarity of each candidate to any future drug
    sims = compute_candidate_future_similarities(cand_smiles, future_smiles)

    # EF@10 and BEDROC with BCa bootstrap CIs
    logger.info("  Computing enrichment with %d bootstrap iterations for %s",
                BOOTSTRAP_N, label)
    enrichment_ci = compute_enrichment_with_ci(
        sims,
        threshold=SIMILARITY_THRESHOLD,
        top_k=10,
        alpha=0.05,
        n_bootstrap=BOOTSTRAP_N,
        seed=BOOTSTRAP_SEED,
    )

    # Also compute EF@50 and EF@100
    ef50 = compute_enrichment_factor(sims, threshold=SIMILARITY_THRESHOLD, top_k=50)
    ef100 = compute_enrichment_factor(sims, threshold=SIMILARITY_THRESHOLD, top_k=100)

    # Novelty
    novelty = compute_novelty(cand_smiles, training_smiles)

    # Per-drug info
    drug_info = {}
    for drug in future_drugs:
        drug_sims_to_cands = [
            compute_candidate_future_similarities([cs], [drug["smiles"]])[0]
            for cs in cand_smiles[:50]  # check top-50 for per-drug
        ]
        best_sim = max(drug_sims_to_cands) if drug_sims_to_cands else 0.0
        drug_info[drug["name"]] = round(best_sim, 4)

    return {
        "ef_10": enrichment_ci["ef_point"],
        "ef_10_ci_lower": enrichment_ci["ef_ci_lower"],
        "ef_10_ci_upper": enrichment_ci["ef_ci_upper"],
        "ef_50": ef50,
        "ef_100": ef100,
        "bedroc_20": enrichment_ci["bedroc_point"],
        "bedroc_20_ci_lower": enrichment_ci["bedroc_ci_lower"],
        "bedroc_20_ci_upper": enrichment_ci["bedroc_ci_upper"],
        "n_bootstrap": BOOTSTRAP_N,
        "novelty_vs_training": novelty,
        "n_candidates": len(cand_smiles),
        "future_drug_best_sims": drug_info,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "cutoff_year": RETROSPECTIVE_CUTOFF,
    }


# ---------------------------------------------------------------------------
# VAE quality metrics
# ---------------------------------------------------------------------------


def compute_vae_quality(
    generated_smiles: list[str],
    training_smiles: list[str],
    label: str,
) -> dict[str, Any]:
    """Compute VAE quality metrics (FCD, novelty, diversity)."""
    logger.info("  Computing VAE quality metrics for %s (%d molecules)",
                label, len(generated_smiles))

    fcd = compute_fcd(generated_smiles, training_smiles)
    novelty = vae_compute_novelty(generated_smiles, training_smiles)
    diversity = compute_internal_diversity(generated_smiles, n_sample=min(1000, len(generated_smiles)))

    return {
        "fcd_score": fcd,
        "novelty": novelty,
        "internal_diversity": diversity,
        "n_molecules": len(generated_smiles),
        "n_unique": len(set(generated_smiles)),
    }


# ---------------------------------------------------------------------------
# Gate G2 decision
# ---------------------------------------------------------------------------


def make_gate_recommendation(d: float) -> str:
    """Return gate recommendation based on pre-registered thresholds."""
    abs_d = abs(d)
    if abs_d >= THRESHOLD_STRONG_GO:
        return "STRONG_GO"
    elif abs_d >= THRESHOLD_GO:
        return "GO"
    elif abs_d >= THRESHOLD_PIVOT:
        return "PIVOT"
    else:
        return "NO_GO"


def interpret_gate(recommendation: str, d: float) -> str:
    """Return plain-language interpretation of gate outcome."""
    direction = "conditioned > unconditioned" if d > 0 else "unconditioned > conditioned"
    interpretations = {
        "STRONG_GO": (
            f"Large effect size (d={d:.4f}, {direction}). "
            "State conditioning provides robust benefit for retrospective enrichment. "
            "Proceed with full manuscript preparation and multi-kinase generalization."
        ),
        "GO": (
            f"Moderate effect size (d={d:.4f}, {direction}). "
            "State conditioning provides meaningful benefit. "
            "Publishable with appropriately tempered claims."
        ),
        "PIVOT": (
            f"Weak effect size (d={d:.4f}, {direction}). "
            "State conditioning provides marginal benefit. "
            "Pivot framing to 'diversity + multi-pocket docking' rather than "
            "'state conditioning drives enrichment.'"
        ),
        "NO_GO": (
            f"Negligible effect size (d={d:.4f}, {direction}). "
            "State conditioning provides no meaningful benefit over unconditioned baseline. "
            "Consider pivoting to negative-result publication or benchmark-only contribution."
        ),
    }
    return interpretations[recommendation]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    logger.info("=" * 70)
    logger.info("Ablation C Analysis: Conditioned vs Unconditioned VAE")
    logger.info("Pre-registration ref: commit 9e7cf96")
    logger.info("=" * 70)

    # ── Load training data ──────────────────────────────────────────────
    logger.info("Loading training data...")
    train_data = load_json(REPO_ROOT / "data" / "processed" / "egfr_smiles_train.json")
    training_smiles_list = [d["smiles"] for d in train_data]
    training_smiles_set = set(training_smiles_list)
    logger.info("  Training set: %d SMILES", len(training_smiles_list))

    # ── Load conditioned candidates ─────────────────────────────────────
    logger.info("Loading conditioned VAE candidates...")
    cond_data = load_json(REPO_ROOT / "artifacts" / "generation" / "vae_candidates.json")
    cond_candidates = cond_data["candidates"]
    cond_smiles_all = extract_smiles(cond_candidates)
    logger.info("  Conditioned: %d candidates across states %s",
                len(cond_candidates), cond_data["states"])

    # Note: conditioned VAE was trained with 4 states (pre 3-state fix).
    # Document this honestly in the results.
    cond_n_states = len(cond_data["states"])

    # ── Load unconditioned candidates (3 seeds) ─────────────────────────
    logger.info("Loading unconditioned VAE candidates...")
    uncond_per_seed: dict[int, list[dict[str, Any]]] = {}
    uncond_smiles_per_seed: dict[int, list[str]] = {}
    for seed in UNCONDITIONED_SEEDS:
        path = REPO_ROOT / "artifacts" / "generation" / f"vae_unconditioned_candidates_seed_{seed}.json"
        data = load_json(path)
        uncond_per_seed[seed] = data["candidates"]
        uncond_smiles_per_seed[seed] = extract_smiles(data["candidates"])
        logger.info("  Seed %d: %d candidates", seed, len(data["candidates"]))

    # Pooled unconditioned (all seeds combined, deduplicated)
    uncond_all_smiles = []
    uncond_all_candidates = []
    seen = set()
    for seed in UNCONDITIONED_SEEDS:
        for cand in uncond_per_seed[seed]:
            if cand["smiles"] not in seen:
                seen.add(cand["smiles"])
                uncond_all_candidates.append(cand)
                uncond_all_smiles.append(cand["smiles"])

    logger.info("  Pooled unconditioned: %d unique candidates from %d seeds",
                len(uncond_all_candidates), len(UNCONDITIONED_SEEDS))

    # ── Score all candidates ────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 1: Scoring candidates with unified scoring")
    logger.info("=" * 50)

    # Score conditioned
    logger.info("Scoring conditioned candidates...")
    scored_cond = score_candidates(cond_candidates, "conditioned")
    logger.info("  Scored %d conditioned candidates", len(scored_cond))

    # Score unconditioned per seed
    scored_uncond_per_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in UNCONDITIONED_SEEDS:
        logger.info("Scoring unconditioned seed %d...", seed)
        scored_uncond_per_seed[seed] = score_candidates(
            uncond_per_seed[seed], f"unconditioned_seed_{seed}"
        )
        logger.info("  Scored %d candidates for seed %d",
                     len(scored_uncond_per_seed[seed]), seed)

    # Score pooled unconditioned
    logger.info("Scoring pooled unconditioned candidates...")
    scored_uncond_pooled = score_candidates(uncond_all_candidates, "unconditioned_pooled")
    logger.info("  Scored %d pooled unconditioned candidates", len(scored_uncond_pooled))

    # ── Compute retrospective enrichment ────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 2: Retrospective enrichment (cutoff=%d)", RETROSPECTIVE_CUTOFF)
    logger.info("=" * 50)

    # Conditioned
    logger.info("Computing enrichment for conditioned...")
    retro_cond = compute_retrospective(scored_cond, training_smiles_set, "conditioned")

    # Unconditioned per seed
    retro_uncond_per_seed: dict[str, dict[str, Any]] = {}
    for seed in UNCONDITIONED_SEEDS:
        logger.info("Computing enrichment for unconditioned seed %d...", seed)
        retro_uncond_per_seed[str(seed)] = compute_retrospective(
            scored_uncond_per_seed[seed], training_smiles_set,
            f"unconditioned_seed_{seed}"
        )

    # Unconditioned pooled
    logger.info("Computing enrichment for pooled unconditioned...")
    retro_uncond_pooled = compute_retrospective(
        scored_uncond_pooled, training_smiles_set, "unconditioned_pooled"
    )

    # ── Compute effect sizes ────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 3: Effect size computation")
    logger.info("=" * 50)

    # Per-seed EF@10 values
    uncond_ef10_per_seed = [
        retro_uncond_per_seed[str(s)]["ef_10"] for s in UNCONDITIONED_SEEDS
    ]
    cond_ef10 = retro_cond["ef_10"]

    logger.info("  Conditioned EF@10: %.4f", cond_ef10)
    for seed in UNCONDITIONED_SEEDS:
        logger.info("  Unconditioned seed %d EF@10: %.4f",
                     seed, retro_uncond_per_seed[str(seed)]["ef_10"])

    # Since conditioned has only 1 seed, we use per-molecule composite score
    # distributions for effect size (as specified in task spec).
    cond_scores = [c["composite_score"] for c in scored_cond]
    uncond_scores_pooled = [c["composite_score"] for c in scored_uncond_pooled]

    # Cohen's d on per-molecule composite scores
    d_composite = cohens_d(cond_scores, uncond_scores_pooled)
    logger.info("  Cohen's d (composite scores, conditioned vs pooled unconditioned): %.4f", d_composite)

    # Cliff's delta (non-parametric robustness check)
    cliff_d = cliff_delta(cond_scores, uncond_scores_pooled)
    logger.info("  Cliff's delta: %.4f", cliff_d)

    # Mann-Whitney U test
    mwu = mann_whitney_u(cond_scores, uncond_scores_pooled)
    logger.info("  Mann-Whitney U: stat=%.4f, p=%.4f", mwu.statistic, mwu.p_value)
    logger.info("  %s", mwu.interpretation)

    # Also compute Cohen's d on per-molecule similarities to future drugs
    # (more directly tied to retrospective enrichment)
    cond_sims = compute_candidate_future_similarities(
        extract_smiles(scored_cond),
        [d["smiles"] for d in get_future_drugs(RETROSPECTIVE_CUTOFF)]
    )
    uncond_sims_pooled = compute_candidate_future_similarities(
        extract_smiles(scored_uncond_pooled),
        [d["smiles"] for d in get_future_drugs(RETROSPECTIVE_CUTOFF)]
    )
    d_similarity = cohens_d(cond_sims, uncond_sims_pooled)
    logger.info("  Cohen's d (future drug similarity): %.4f", d_similarity)

    # BCa CI on composite score difference
    mean_uncond = float(np.mean(uncond_scores_pooled))
    ci_diff = bca_bootstrap_confidence_interval(
        cond_scores,
        lambda x: float(np.mean(x)) - mean_uncond,
        alpha=0.05,
        n_bootstrap=BOOTSTRAP_N,
        seed=BOOTSTRAP_SEED,
    )
    logger.info("  Mean score difference CI: [%.4f, %.4f]",
                ci_diff.ci_lower, ci_diff.ci_upper)

    # ── VAE quality metrics ─────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 4: VAE quality metrics")
    logger.info("=" * 50)

    vae_quality_cond = compute_vae_quality(
        cond_smiles_all, training_smiles_list, "conditioned"
    )

    vae_quality_uncond_per_seed: dict[str, dict[str, Any]] = {}
    for seed in UNCONDITIONED_SEEDS:
        vae_quality_uncond_per_seed[str(seed)] = compute_vae_quality(
            uncond_smiles_per_seed[seed], training_smiles_list,
            f"unconditioned_seed_{seed}"
        )

    vae_quality_uncond_pooled = compute_vae_quality(
        uncond_all_smiles, training_smiles_list, "unconditioned_pooled"
    )

    # ── Per-component scoring breakdown ─────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 5: Per-component score analysis")
    logger.info("=" * 50)

    component_names = ["reference_similarity", "druglikeness", "docking_proxy", "state_specificity"]
    component_analysis = {}
    for comp_name in component_names:
        cond_vals = [c["components"].get(comp_name, 0.0) for c in scored_cond]
        uncond_vals = [c["components"].get(comp_name, 0.0) for c in scored_uncond_pooled]
        comp_d = cohens_d(cond_vals, uncond_vals)
        comp_cliff = cliff_delta(cond_vals, uncond_vals)
        component_analysis[comp_name] = {
            "conditioned_mean": round(float(np.mean(cond_vals)), 4),
            "conditioned_std": round(float(np.std(cond_vals, ddof=1)), 4) if len(cond_vals) > 1 else 0.0,
            "unconditioned_mean": round(float(np.mean(uncond_vals)), 4),
            "unconditioned_std": round(float(np.std(uncond_vals, ddof=1)), 4) if len(uncond_vals) > 1 else 0.0,
            "cohens_d": round(comp_d, 4),
            "cliff_delta": round(comp_cliff, 4),
        }
        logger.info("  %s: cond=%.4f +/- %.4f, uncond=%.4f +/- %.4f, d=%.4f",
                     comp_name,
                     component_analysis[comp_name]["conditioned_mean"],
                     component_analysis[comp_name]["conditioned_std"],
                     component_analysis[comp_name]["unconditioned_mean"],
                     component_analysis[comp_name]["unconditioned_std"],
                     comp_d)

    # ── Gate G2 decision ────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 6: Gate G2 Decision")
    logger.info("=" * 50)

    # Primary metric: Cohen's d on composite scores
    recommendation = make_gate_recommendation(d_composite)
    interpretation = interpret_gate(recommendation, d_composite)

    logger.info("  Primary Cohen's d (composite scores): %.4f", d_composite)
    logger.info("  Gate G2 recommendation: %s", recommendation)
    logger.info("  %s", interpretation)

    # ── Assemble results artifact ───────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()

    results = {
        "generated_at": now,
        "task": "P1-T10: Ablation C Analysis + Gate G2",
        "pre_registration_ref": "commit 9e7cf96 (docs/pre-registration.md)",
        "pre_registration_date": "2026-04-09T23:30:00+00:00",
        "analysis_notes": {
            "conditioned_model": (
                f"4-state model (pre 3-state fix). States: {cond_data['states']}. "
                "This is documented honestly -- the conditioned VAE used 4 states "
                "including DFGout_aCout, which was later removed from the enum. "
                "The unconditioned VAE uses n_states=1 as pre-registered."
            ),
            "scoring_fairness": (
                "Both conditions scored with identical unified scoring. "
                "state_specificity = 0 for both (empty state_smiles_map). "
                "This isolates generation quality from scoring bonus."
            ),
            "effect_size_approach": (
                "Conditioned has 1 seed, unconditioned has 3 seeds. "
                "Per pre-registration, using per-molecule composite score distributions "
                "for Cohen's d since conditioned has only 1 seed."
            ),
        },

        # ── Conditioned results ──
        "conditioned": {
            "n_candidates": len(scored_cond),
            "n_states": cond_n_states,
            "states": cond_data["states"],
            "model_checkpoint": cond_data.get("checkpoint", ""),
            "mean_composite_score": round(float(np.mean(cond_scores)), 4),
            "std_composite_score": round(float(np.std(cond_scores, ddof=1)), 4),
            "median_composite_score": round(float(np.median(cond_scores)), 4),
            "retrospective": retro_cond,
            "vae_quality": vae_quality_cond,
            "score_distribution": {
                "min": round(float(np.min(cond_scores)), 4),
                "p25": round(float(np.percentile(cond_scores, 25)), 4),
                "p50": round(float(np.percentile(cond_scores, 50)), 4),
                "p75": round(float(np.percentile(cond_scores, 75)), 4),
                "max": round(float(np.max(cond_scores)), 4),
            },
        },

        # ── Unconditioned per-seed results ──
        "unconditioned_per_seed": {},

        # ── Unconditioned pooled results ──
        "unconditioned_pooled": {
            "n_candidates": len(scored_uncond_pooled),
            "n_seeds": len(UNCONDITIONED_SEEDS),
            "seeds": UNCONDITIONED_SEEDS,
            "mean_composite_score": round(float(np.mean(uncond_scores_pooled)), 4),
            "std_composite_score": round(float(np.std(uncond_scores_pooled, ddof=1)), 4),
            "median_composite_score": round(float(np.median(uncond_scores_pooled)), 4),
            "retrospective": retro_uncond_pooled,
            "vae_quality": vae_quality_uncond_pooled,
            "score_distribution": {
                "min": round(float(np.min(uncond_scores_pooled)), 4),
                "p25": round(float(np.percentile(uncond_scores_pooled, 25)), 4),
                "p50": round(float(np.percentile(uncond_scores_pooled, 50)), 4),
                "p75": round(float(np.percentile(uncond_scores_pooled, 75)), 4),
                "max": round(float(np.max(uncond_scores_pooled)), 4),
            },
        },

        # ── Effect sizes ──
        "effect_sizes": {
            "primary_metric": "cohens_d_composite_scores",
            "cohens_d_composite": round(d_composite, 4),
            "cohens_d_future_drug_similarity": round(d_similarity, 4),
            "cliff_delta_composite": round(cliff_d, 4),
            "mann_whitney_u": {
                "statistic": mwu.statistic,
                "p_value": mwu.p_value,
                "interpretation": mwu.interpretation,
            },
            "mean_score_difference": {
                "point_estimate": round(float(np.mean(cond_scores)) - float(np.mean(uncond_scores_pooled)), 4),
                "ci_lower": ci_diff.ci_lower,
                "ci_upper": ci_diff.ci_upper,
                "method": "BCa bootstrap (10000 iterations)",
            },
            "per_seed_ef10": {
                "conditioned": cond_ef10,
                "unconditioned": {str(s): retro_uncond_per_seed[str(s)]["ef_10"] for s in UNCONDITIONED_SEEDS},
            },
        },

        # ── Per-component breakdown ──
        "component_analysis": component_analysis,

        # ── Gate G2 ──
        "gate_g2": {
            "metric": "Cohen's d on per-molecule composite scores",
            "observed_d": round(d_composite, 4),
            "direction": "conditioned > unconditioned" if d_composite > 0 else "unconditioned >= conditioned",
            "thresholds": {
                "strong_go": f">= {THRESHOLD_STRONG_GO}",
                "go": f"[{THRESHOLD_GO}, {THRESHOLD_STRONG_GO})",
                "pivot": f"[{THRESHOLD_PIVOT}, {THRESHOLD_GO})",
                "no_go": f"< {THRESHOLD_PIVOT}",
            },
            "recommendation": recommendation,
            "interpretation": interpretation,
            "note": "Gate G2 is a RECOMMENDATION -- human makes final decision.",
        },

        "methodology": {
            "scoring": (
                "Unified scoring with DEFAULT_WEIGHTS: "
                "reference_similarity=0.35, druglikeness=0.30, "
                "docking_proxy=0.20, state_specificity=0.15. "
                "state_specificity forced to 0 for both conditions "
                "(empty state_smiles_map) to ensure fair comparison."
            ),
            "retrospective": (
                f"Time-split cutoff {RETROSPECTIVE_CUTOFF}. "
                f"Similarity threshold {SIMILARITY_THRESHOLD}. "
                f"BCa bootstrap CIs with {BOOTSTRAP_N} iterations."
            ),
            "effect_size": (
                "Cohen's d with pooled standard deviation on per-molecule "
                "composite score distributions. Cliff's delta as non-parametric "
                "robustness check. Mann-Whitney U two-sided test."
            ),
        },
    }

    # Fill per-seed unconditioned results
    for seed in UNCONDITIONED_SEEDS:
        seed_scores = [c["composite_score"] for c in scored_uncond_per_seed[seed]]
        results["unconditioned_per_seed"][str(seed)] = {
            "n_candidates": len(scored_uncond_per_seed[seed]),
            "mean_composite_score": round(float(np.mean(seed_scores)), 4),
            "std_composite_score": round(float(np.std(seed_scores, ddof=1)), 4) if len(seed_scores) > 1 else 0.0,
            "retrospective": retro_uncond_per_seed[str(seed)],
            "vae_quality": vae_quality_uncond_per_seed[str(seed)],
        }

    # ── Save results ────────────────────────────────────────────────────
    output_path = REPO_ROOT / "artifacts" / "evaluation" / "ablation_c_results.json"
    save_json(results, output_path)

    # ── Print summary ───────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info("ABLATION C RESULTS SUMMARY")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Conditioned VAE (%d states, %d candidates):",
                cond_n_states, len(scored_cond))
    logger.info("  Mean composite score: %.4f +/- %.4f",
                results["conditioned"]["mean_composite_score"],
                results["conditioned"]["std_composite_score"])
    logger.info("  EF@10: %.4f [%.4f, %.4f]",
                retro_cond["ef_10"], retro_cond["ef_10_ci_lower"], retro_cond["ef_10_ci_upper"])
    if retro_cond["bedroc_20"] is not None:
        logger.info("  BEDROC(a=20): %.4f [%.4f, %.4f]",
                     retro_cond["bedroc_20"], retro_cond["bedroc_20_ci_lower"],
                     retro_cond["bedroc_20_ci_upper"])
    logger.info("  Novelty: %.4f", vae_quality_cond["novelty"])
    if vae_quality_cond["internal_diversity"] is not None:
        logger.info("  Internal diversity: %.4f", vae_quality_cond["internal_diversity"])
    logger.info("")
    logger.info("Unconditioned VAE (pooled, %d candidates from %d seeds):",
                len(scored_uncond_pooled), len(UNCONDITIONED_SEEDS))
    logger.info("  Mean composite score: %.4f +/- %.4f",
                results["unconditioned_pooled"]["mean_composite_score"],
                results["unconditioned_pooled"]["std_composite_score"])
    logger.info("  EF@10: %.4f [%.4f, %.4f]",
                retro_uncond_pooled["ef_10"],
                retro_uncond_pooled["ef_10_ci_lower"],
                retro_uncond_pooled["ef_10_ci_upper"])
    logger.info("")
    for seed in UNCONDITIONED_SEEDS:
        logger.info("  Seed %d EF@10: %.4f", seed, retro_uncond_per_seed[str(seed)]["ef_10"])
    logger.info("")
    logger.info("Effect sizes:")
    logger.info("  Cohen's d (composite scores): %.4f", d_composite)
    logger.info("  Cohen's d (future drug sim):  %.4f", d_similarity)
    logger.info("  Cliff's delta:                %.4f", cliff_d)
    logger.info("  Mann-Whitney U p-value:       %.4f", mwu.p_value)
    logger.info("  Score difference CI:          [%.4f, %.4f]", ci_diff.ci_lower, ci_diff.ci_upper)
    logger.info("")
    logger.info("GATE G2: %s (d=%.4f)", recommendation, d_composite)
    logger.info("  %s", interpretation)
    logger.info("")
    logger.info("Results saved to: %s", output_path)


if __name__ == "__main__":
    main()
