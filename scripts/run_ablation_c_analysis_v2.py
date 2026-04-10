"""Ablation C v2 analysis: conditioned (3-seed) vs unconditioned (3-seed) VAE.

This is the corrected Ablation C analysis. The original used 4-state conditioned
candidates from a single obsolete model. This v2 uses the correct 3-state model
trained across 3 seeds (42, 123, 7) to match the unconditioned experiment design.

Pre-registration ref: commit 9e7cf96 (docs/pre-registration.md)

Usage:
    module load Python/3.12.3
    source envs/statebind/bin/activate
    cd repo/
    python scripts/run_ablation_c_analysis_v2.py
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
logger = logging.getLogger("ablation_c_v2")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEEDS = [42, 123, 7]
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
    - state_specificity = 0 for both conditions (empty state_smiles_map)
    - pipeline = STATIC for both (ensures identical treatment)

    This isolates the VAE's generation quality from the scoring system's
    state-specificity bonus.
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
    """Compute retrospective enrichment metrics with BCa bootstrap CIs."""
    future_drugs = get_future_drugs(RETROSPECTIVE_CUTOFF)
    future_smiles = [d["smiles"] for d in future_drugs]
    cand_smiles = extract_smiles(scored_candidates)

    logger.info("  Computing similarities to %d future drugs for %s (%d candidates)",
                len(future_drugs), label, len(cand_smiles))

    sims = compute_candidate_future_similarities(cand_smiles, future_smiles)

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

    ef50 = compute_enrichment_factor(sims, threshold=SIMILARITY_THRESHOLD, top_k=50)
    ef100 = compute_enrichment_factor(sims, threshold=SIMILARITY_THRESHOLD, top_k=100)

    novelty = compute_novelty(cand_smiles, training_smiles)

    drug_info = {}
    for drug in future_drugs:
        drug_sims_to_cands = [
            compute_candidate_future_similarities([cs], [drug["smiles"]])[0]
            for cs in cand_smiles[:50]
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
    diversity = compute_internal_diversity(
        generated_smiles, n_sample=min(1000, len(generated_smiles))
    )

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
    logger.info("Ablation C v2 Analysis: Conditioned (3-seed) vs Unconditioned (3-seed) VAE")
    logger.info("Pre-registration ref: commit 9e7cf96")
    logger.info("Corrected: uses 3-state model across 3 seeds for both conditions")
    logger.info("=" * 70)

    # ── Load training data ──────────────────────────────────────────────
    logger.info("Loading training data...")
    train_data = load_json(REPO_ROOT / "data" / "processed" / "egfr_smiles_train.json")
    training_smiles_list = [d["smiles"] for d in train_data]
    training_smiles_set = set(training_smiles_list)
    logger.info("  Training set: %d SMILES", len(training_smiles_list))

    # ── Load conditioned candidates (3 seeds) ──────────────────────────
    logger.info("Loading conditioned VAE candidates (3 seeds)...")
    cond_per_seed: dict[int, list[dict[str, Any]]] = {}
    cond_smiles_per_seed: dict[int, list[str]] = {}
    for seed in SEEDS:
        path = REPO_ROOT / "artifacts" / "generation" / f"vae_conditioned_seed{seed}.json"
        if not path.exists():
            logger.error("Missing conditioned candidates for seed %d: %s", seed, path)
            sys.exit(1)
        data = load_json(path)
        cond_per_seed[seed] = data["candidates"]
        cond_smiles_per_seed[seed] = extract_smiles(data["candidates"])
        logger.info("  Seed %d: %d candidates, states=%s",
                     seed, len(data["candidates"]), data.get("states", []))

    # Pooled conditioned (all seeds, deduplicated)
    cond_all_smiles = []
    cond_all_candidates = []
    seen_cond = set()
    for seed in SEEDS:
        for cand in cond_per_seed[seed]:
            if cand["smiles"] not in seen_cond:
                seen_cond.add(cand["smiles"])
                cond_all_candidates.append(cand)
                cond_all_smiles.append(cand["smiles"])
    logger.info("  Pooled conditioned: %d unique candidates from %d seeds",
                len(cond_all_candidates), len(SEEDS))

    # ── Load unconditioned candidates (3 seeds) ─────────────────────────
    logger.info("Loading unconditioned VAE candidates (3 seeds)...")
    uncond_per_seed: dict[int, list[dict[str, Any]]] = {}
    uncond_smiles_per_seed: dict[int, list[str]] = {}
    for seed in SEEDS:
        path = REPO_ROOT / "artifacts" / "generation" / f"vae_unconditioned_candidates_seed_{seed}.json"
        if not path.exists():
            logger.error("Missing unconditioned candidates for seed %d: %s", seed, path)
            sys.exit(1)
        data = load_json(path)
        uncond_per_seed[seed] = data["candidates"]
        uncond_smiles_per_seed[seed] = extract_smiles(data["candidates"])
        logger.info("  Seed %d: %d candidates", seed, len(data["candidates"]))

    # Pooled unconditioned (all seeds, deduplicated)
    uncond_all_smiles = []
    uncond_all_candidates = []
    seen_uncond = set()
    for seed in SEEDS:
        for cand in uncond_per_seed[seed]:
            if cand["smiles"] not in seen_uncond:
                seen_uncond.add(cand["smiles"])
                uncond_all_candidates.append(cand)
                uncond_all_smiles.append(cand["smiles"])
    logger.info("  Pooled unconditioned: %d unique candidates from %d seeds",
                len(uncond_all_candidates), len(SEEDS))

    # ── Score all candidates ────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 1: Scoring candidates with unified scoring")
    logger.info("=" * 50)

    # Score conditioned per seed
    scored_cond_per_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in SEEDS:
        logger.info("Scoring conditioned seed %d...", seed)
        scored_cond_per_seed[seed] = score_candidates(
            cond_per_seed[seed], f"conditioned_seed_{seed}"
        )
        logger.info("  Scored %d candidates for seed %d",
                     len(scored_cond_per_seed[seed]), seed)

    # Score conditioned pooled
    logger.info("Scoring pooled conditioned candidates...")
    scored_cond_pooled = score_candidates(cond_all_candidates, "conditioned_pooled")
    logger.info("  Scored %d pooled conditioned candidates", len(scored_cond_pooled))

    # Score unconditioned per seed
    scored_uncond_per_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in SEEDS:
        logger.info("Scoring unconditioned seed %d...", seed)
        scored_uncond_per_seed[seed] = score_candidates(
            uncond_per_seed[seed], f"unconditioned_seed_{seed}"
        )
        logger.info("  Scored %d candidates for seed %d",
                     len(scored_uncond_per_seed[seed]), seed)

    # Score unconditioned pooled
    logger.info("Scoring pooled unconditioned candidates...")
    scored_uncond_pooled = score_candidates(uncond_all_candidates, "unconditioned_pooled")
    logger.info("  Scored %d pooled unconditioned candidates", len(scored_uncond_pooled))

    # ── Compute retrospective enrichment ────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 2: Retrospective enrichment (cutoff=%d)", RETROSPECTIVE_CUTOFF)
    logger.info("=" * 50)

    # Conditioned per seed
    retro_cond_per_seed: dict[str, dict[str, Any]] = {}
    for seed in SEEDS:
        logger.info("Computing enrichment for conditioned seed %d...", seed)
        retro_cond_per_seed[str(seed)] = compute_retrospective(
            scored_cond_per_seed[seed], training_smiles_set,
            f"conditioned_seed_{seed}"
        )

    # Conditioned pooled
    logger.info("Computing enrichment for pooled conditioned...")
    retro_cond_pooled = compute_retrospective(
        scored_cond_pooled, training_smiles_set, "conditioned_pooled"
    )

    # Unconditioned per seed
    retro_uncond_per_seed: dict[str, dict[str, Any]] = {}
    for seed in SEEDS:
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

    # Per-seed EF@10 values (3 each -- proper paired comparison)
    cond_ef10_per_seed = [
        retro_cond_per_seed[str(s)]["ef_10"] for s in SEEDS
    ]
    uncond_ef10_per_seed = [
        retro_uncond_per_seed[str(s)]["ef_10"] for s in SEEDS
    ]

    logger.info("  Per-seed EF@10:")
    for seed in SEEDS:
        logger.info("    Seed %d: conditioned=%.4f, unconditioned=%.4f",
                     seed,
                     retro_cond_per_seed[str(seed)]["ef_10"],
                     retro_uncond_per_seed[str(seed)]["ef_10"])

    # Cohen's d on EF@10 distributions (3 values each)
    # Note: small sample size (n=3) -- interpret cautiously
    if len(set(cond_ef10_per_seed)) > 0 and len(set(uncond_ef10_per_seed)) > 0:
        d_ef10 = cohens_d(cond_ef10_per_seed, uncond_ef10_per_seed)
    else:
        d_ef10 = 0.0
    logger.info("  Cohen's d (EF@10, 3 seeds each): %.4f", d_ef10)

    # Per-molecule composite scores -- more robust with many observations
    cond_scores_pooled = [c["composite_score"] for c in scored_cond_pooled]
    uncond_scores_pooled = [c["composite_score"] for c in scored_uncond_pooled]

    d_composite = cohens_d(cond_scores_pooled, uncond_scores_pooled)
    logger.info("  Cohen's d (composite scores, pooled): %.4f", d_composite)

    # Cliff's delta (non-parametric robustness check)
    cliff_d = cliff_delta(cond_scores_pooled, uncond_scores_pooled)
    logger.info("  Cliff's delta (composite scores): %.4f", cliff_d)

    # Mann-Whitney U test
    mwu = mann_whitney_u(cond_scores_pooled, uncond_scores_pooled)
    logger.info("  Mann-Whitney U: stat=%.4f, p=%.4f", mwu.statistic, mwu.p_value)
    logger.info("  %s", mwu.interpretation)

    # Per-seed composite score Cohen's d (individual seeds)
    d_per_seed_composite: dict[str, float] = {}
    for seed in SEEDS:
        cond_s = [c["composite_score"] for c in scored_cond_per_seed[seed]]
        uncond_s = [c["composite_score"] for c in scored_uncond_per_seed[seed]]
        d_per_seed_composite[str(seed)] = round(cohens_d(cond_s, uncond_s), 4)
        logger.info("  Seed %d Cohen's d (composite): %.4f", seed, d_per_seed_composite[str(seed)])

    # Cohen's d on per-molecule similarities to future drugs
    future_drugs = get_future_drugs(RETROSPECTIVE_CUTOFF)
    future_smiles = [d["smiles"] for d in future_drugs]
    cond_sims_pooled = compute_candidate_future_similarities(
        extract_smiles(scored_cond_pooled), future_smiles
    )
    uncond_sims_pooled = compute_candidate_future_similarities(
        extract_smiles(scored_uncond_pooled), future_smiles
    )
    d_similarity = cohens_d(cond_sims_pooled, uncond_sims_pooled)
    logger.info("  Cohen's d (future drug similarity, pooled): %.4f", d_similarity)

    # BCa CI on composite score difference
    mean_uncond = float(np.mean(uncond_scores_pooled))
    ci_diff = bca_bootstrap_confidence_interval(
        cond_scores_pooled,
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

    vae_quality_cond_per_seed: dict[str, dict[str, Any]] = {}
    for seed in SEEDS:
        vae_quality_cond_per_seed[str(seed)] = compute_vae_quality(
            cond_smiles_per_seed[seed], training_smiles_list,
            f"conditioned_seed_{seed}"
        )

    vae_quality_cond_pooled = compute_vae_quality(
        cond_all_smiles, training_smiles_list, "conditioned_pooled"
    )

    vae_quality_uncond_per_seed: dict[str, dict[str, Any]] = {}
    for seed in SEEDS:
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
        cond_vals = [c["components"].get(comp_name, 0.0) for c in scored_cond_pooled]
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

    # Primary metric: Cohen's d on per-molecule composite scores (pooled)
    recommendation = make_gate_recommendation(d_composite)
    interpretation = interpret_gate(recommendation, d_composite)

    logger.info("  Primary Cohen's d (composite scores, pooled): %.4f", d_composite)
    logger.info("  Cohen's d (EF@10, 3 seeds): %.4f", d_ef10)
    logger.info("  Gate G2 recommendation: %s", recommendation)
    logger.info("  %s", interpretation)

    # ── Assemble results artifact ───────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()

    results: dict[str, Any] = {
        "generated_at": now,
        "task": "Ablation C v2: Corrected 3-seed conditioned vs 3-seed unconditioned",
        "pre_registration_ref": "commit 9e7cf96 (docs/pre-registration.md)",
        "version": "v2",
        "correction_note": (
            "v1 used obsolete 4-state conditioned VAE (1 seed). "
            "v2 uses correct 3-state model across 3 seeds (42, 123, 7), "
            "matching the unconditioned experiment design."
        ),
        "analysis_notes": {
            "conditioned_model": (
                "3-state model (DFGin_aCin, DFGin_aCout, DFGout_aCin). "
                "Trained with SELFIES representation across 3 seeds. "
                "100 candidates per state per seed = 300 per seed."
            ),
            "unconditioned_model": (
                "1-state model (unconditioned). "
                "Trained with SELFIES representation across 3 seeds. "
                "300 candidates per seed."
            ),
            "scoring_fairness": (
                "Both conditions scored with identical unified scoring. "
                "state_specificity = 0 for both (empty state_smiles_map). "
                "This isolates generation quality from scoring bonus."
            ),
            "effect_size_approach": (
                "Both conditions have 3 seeds. Primary metric is Cohen's d on "
                "per-molecule composite score distributions (pooled across seeds). "
                "Secondary metric is Cohen's d on per-seed EF@10 values (n=3 each). "
                "The per-molecule metric is more robust; the per-seed EF@10 metric "
                "has very low power (n=3) and should be interpreted cautiously."
            ),
        },

        # ── Conditioned per-seed results ──
        "conditioned_per_seed": {},

        # ── Conditioned pooled results ──
        "conditioned_pooled": {
            "n_candidates": len(scored_cond_pooled),
            "n_seeds": len(SEEDS),
            "seeds": SEEDS,
            "mean_composite_score": round(float(np.mean(cond_scores_pooled)), 4),
            "std_composite_score": round(float(np.std(cond_scores_pooled, ddof=1)), 4),
            "median_composite_score": round(float(np.median(cond_scores_pooled)), 4),
            "retrospective": retro_cond_pooled,
            "vae_quality": vae_quality_cond_pooled,
            "score_distribution": {
                "min": round(float(np.min(cond_scores_pooled)), 4),
                "p25": round(float(np.percentile(cond_scores_pooled, 25)), 4),
                "p50": round(float(np.percentile(cond_scores_pooled, 50)), 4),
                "p75": round(float(np.percentile(cond_scores_pooled, 75)), 4),
                "max": round(float(np.max(cond_scores_pooled)), 4),
            },
        },

        # ── Unconditioned per-seed results ──
        "unconditioned_per_seed": {},

        # ── Unconditioned pooled results ──
        "unconditioned_pooled": {
            "n_candidates": len(scored_uncond_pooled),
            "n_seeds": len(SEEDS),
            "seeds": SEEDS,
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
            "primary_metric": "cohens_d_composite_scores_pooled",
            "cohens_d_composite_pooled": round(d_composite, 4),
            "cohens_d_ef10_per_seed": round(d_ef10, 4),
            "cohens_d_future_drug_similarity_pooled": round(d_similarity, 4),
            "cliff_delta_composite_pooled": round(cliff_d, 4),
            "mann_whitney_u": {
                "statistic": mwu.statistic,
                "p_value": mwu.p_value,
                "interpretation": mwu.interpretation,
            },
            "mean_score_difference": {
                "point_estimate": round(
                    float(np.mean(cond_scores_pooled)) - float(np.mean(uncond_scores_pooled)), 4
                ),
                "ci_lower": ci_diff.ci_lower,
                "ci_upper": ci_diff.ci_upper,
                "method": "BCa bootstrap (10000 iterations)",
            },
            "per_seed_ef10": {
                "conditioned": {str(s): retro_cond_per_seed[str(s)]["ef_10"] for s in SEEDS},
                "unconditioned": {str(s): retro_uncond_per_seed[str(s)]["ef_10"] for s in SEEDS},
            },
            "per_seed_cohens_d_composite": d_per_seed_composite,
        },

        # ── Per-component breakdown ──
        "component_analysis": component_analysis,

        # ── Gate G2 ──
        "gate_g2": {
            "metric": "Cohen's d on per-molecule composite scores (pooled)",
            "observed_d_composite_pooled": round(d_composite, 4),
            "observed_d_ef10_per_seed": round(d_ef10, 4),
            "direction": "conditioned > unconditioned" if d_composite > 0 else "unconditioned >= conditioned",
            "thresholds": {
                "strong_go": f">= {THRESHOLD_STRONG_GO}",
                "go": f"[{THRESHOLD_GO}, {THRESHOLD_STRONG_GO})",
                "pivot": f"[{THRESHOLD_PIVOT}, {THRESHOLD_GO})",
                "no_go": f"< {THRESHOLD_PIVOT}",
            },
            "recommendation": recommendation,
            "interpretation": interpretation,
            "note": (
                "Gate G2 is a RECOMMENDATION -- human makes final decision. "
                "Per-seed EF@10 Cohen's d (n=3 per group) has very low power; "
                "the per-molecule composite score Cohen's d is more reliable."
            ),
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
                "Primary: Cohen's d with pooled SD on per-molecule composite "
                "score distributions (pooled across seeds). "
                "Secondary: Cohen's d on per-seed EF@10 (n=3 each, low power). "
                "Robustness checks: Cliff's delta, Mann-Whitney U, "
                "per-seed composite Cohen's d."
            ),
        },
    }

    # Fill per-seed conditioned results
    for seed in SEEDS:
        seed_scores = [c["composite_score"] for c in scored_cond_per_seed[seed]]
        results["conditioned_per_seed"][str(seed)] = {
            "n_candidates": len(scored_cond_per_seed[seed]),
            "mean_composite_score": round(float(np.mean(seed_scores)), 4),
            "std_composite_score": round(float(np.std(seed_scores, ddof=1)), 4) if len(seed_scores) > 1 else 0.0,
            "retrospective": retro_cond_per_seed[str(seed)],
            "vae_quality": vae_quality_cond_per_seed[str(seed)],
        }

    # Fill per-seed unconditioned results
    for seed in SEEDS:
        seed_scores = [c["composite_score"] for c in scored_uncond_per_seed[seed]]
        results["unconditioned_per_seed"][str(seed)] = {
            "n_candidates": len(scored_uncond_per_seed[seed]),
            "mean_composite_score": round(float(np.mean(seed_scores)), 4),
            "std_composite_score": round(float(np.std(seed_scores, ddof=1)), 4) if len(seed_scores) > 1 else 0.0,
            "retrospective": retro_uncond_per_seed[str(seed)],
            "vae_quality": vae_quality_uncond_per_seed[str(seed)],
        }

    # ── Save results ────────────────────────────────────────────────────
    output_path = REPO_ROOT / "artifacts" / "evaluation" / "ablation_c_results_v2.json"
    save_json(results, output_path)

    # ── Print summary ───────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info("ABLATION C v2 RESULTS SUMMARY")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Conditioned VAE (3-state, pooled from %d seeds, %d candidates):",
                len(SEEDS), len(scored_cond_pooled))
    logger.info("  Mean composite score: %.4f +/- %.4f",
                results["conditioned_pooled"]["mean_composite_score"],
                results["conditioned_pooled"]["std_composite_score"])
    logger.info("  EF@10 (pooled): %.4f [%.4f, %.4f]",
                retro_cond_pooled["ef_10"],
                retro_cond_pooled["ef_10_ci_lower"],
                retro_cond_pooled["ef_10_ci_upper"])
    if retro_cond_pooled["bedroc_20"] is not None:
        logger.info("  BEDROC(a=20): %.4f [%.4f, %.4f]",
                     retro_cond_pooled["bedroc_20"],
                     retro_cond_pooled["bedroc_20_ci_lower"],
                     retro_cond_pooled["bedroc_20_ci_upper"])
    logger.info("  Novelty: %.4f", vae_quality_cond_pooled["novelty"])
    if vae_quality_cond_pooled["internal_diversity"] is not None:
        logger.info("  Internal diversity: %.4f", vae_quality_cond_pooled["internal_diversity"])
    logger.info("")
    logger.info("Unconditioned VAE (pooled from %d seeds, %d candidates):",
                len(SEEDS), len(scored_uncond_pooled))
    logger.info("  Mean composite score: %.4f +/- %.4f",
                results["unconditioned_pooled"]["mean_composite_score"],
                results["unconditioned_pooled"]["std_composite_score"])
    logger.info("  EF@10 (pooled): %.4f [%.4f, %.4f]",
                retro_uncond_pooled["ef_10"],
                retro_uncond_pooled["ef_10_ci_lower"],
                retro_uncond_pooled["ef_10_ci_upper"])
    logger.info("")
    logger.info("Per-seed EF@10:")
    for seed in SEEDS:
        logger.info("  Seed %d: conditioned=%.4f, unconditioned=%.4f",
                     seed,
                     retro_cond_per_seed[str(seed)]["ef_10"],
                     retro_uncond_per_seed[str(seed)]["ef_10"])
    logger.info("")
    logger.info("Effect sizes:")
    logger.info("  Cohen's d (composite scores, pooled): %.4f", d_composite)
    logger.info("  Cohen's d (EF@10, per-seed, n=3):     %.4f", d_ef10)
    logger.info("  Cohen's d (future drug sim, pooled):   %.4f", d_similarity)
    logger.info("  Cliff's delta (composite, pooled):     %.4f", cliff_d)
    logger.info("  Mann-Whitney U p-value:                %.6f", mwu.p_value)
    logger.info("  Score difference CI:                   [%.4f, %.4f]",
                ci_diff.ci_lower, ci_diff.ci_upper)
    logger.info("  Per-seed composite Cohen's d:          %s",
                {str(s): d_per_seed_composite[str(s)] for s in SEEDS})
    logger.info("")
    logger.info("GATE G2: %s (d_composite=%.4f, d_ef10=%.4f)",
                recommendation, d_composite, d_ef10)
    logger.info("  %s", interpretation)
    logger.info("")
    logger.info("Results saved to: %s", output_path)


if __name__ == "__main__":
    main()
