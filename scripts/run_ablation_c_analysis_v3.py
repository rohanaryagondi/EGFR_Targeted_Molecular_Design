"""Ablation C v3 analysis: Transformer VAE conditioned vs unconditioned.

Replaces v2 (SELFIES GRU VAE, which had 0% reconstruction).
Uses the same statistical methodology: unified scoring, retrospective
enrichment with BCa bootstrap CIs, Cohen's d for Gate G2.

Key change: Transformer VAE candidates (SMILES representation, Transformer
decoder) at new file paths.

Pre-registration ref: commit 9e7cf96 (docs/pre-registration.md)

Usage:
    python scripts/run_ablation_c_analysis_v3.py [--greedy]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

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
logger = logging.getLogger("ablation_c_v3")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEEDS_DEFAULT = [42, 123, 7]
ALL_SEEDS = [42, 123, 7, 13, 37, 99, 256, 314, 512, 777]
SEEDS = SEEDS_DEFAULT
RETROSPECTIVE_CUTOFF = 2010
SIMILARITY_THRESHOLD = 0.4
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 42

THRESHOLD_STRONG_GO = 0.8
THRESHOLD_GO = 0.5
THRESHOLD_PIVOT = 0.3


def load_json_file(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Saved: %s", path)


def extract_smiles(candidates: list[dict]) -> list[str]:
    return [c["smiles"] for c in candidates]


def score_candidates(candidates: list[dict], label: str) -> list[dict]:
    """Score candidates with unified scoring (state_specificity=0 for fairness)."""
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

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored


def compute_retrospective(scored: list[dict], training_smiles: set[str],
                          label: str) -> dict:
    future_drugs = get_future_drugs(RETROSPECTIVE_CUTOFF)
    future_smiles = [d["smiles"] for d in future_drugs]
    cand_smiles = extract_smiles(scored)

    logger.info("  Enrichment for %s (%d candidates, %d future drugs)...",
                label, len(cand_smiles), len(future_drugs))

    sims = compute_candidate_future_similarities(cand_smiles, future_smiles)
    enrichment_ci = compute_enrichment_with_ci(
        sims, threshold=SIMILARITY_THRESHOLD, top_k=10,
        alpha=0.05, n_bootstrap=BOOTSTRAP_N, seed=BOOTSTRAP_SEED,
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


def compute_vae_quality(generated: list[str], training: list[str],
                        label: str) -> dict:
    logger.info("  VAE quality for %s (%d mols)...", label, len(generated))
    fcd = compute_fcd(generated, training)
    novelty = vae_compute_novelty(generated, training)
    diversity = compute_internal_diversity(
        generated, n_sample=min(1000, len(generated))
    )
    return {
        "fcd_score": fcd,
        "novelty": novelty,
        "internal_diversity": diversity,
        "n_molecules": len(generated),
        "n_unique": len(set(generated)),
    }


def make_gate_recommendation(d: float) -> str:
    abs_d = abs(d)
    if abs_d >= THRESHOLD_STRONG_GO:
        return "STRONG_GO"
    elif abs_d >= THRESHOLD_GO:
        return "GO"
    elif abs_d >= THRESHOLD_PIVOT:
        return "PIVOT"
    else:
        return "NO_GO"


def interpret_gate(rec: str, d: float) -> str:
    direction = "conditioned > unconditioned" if d > 0 else "unconditioned > conditioned"
    msgs = {
        "STRONG_GO": (
            f"Large effect (d={d:.4f}, {direction}). State conditioning strongly benefits "
            "enrichment. Proceed with full manuscript + multi-kinase generalization."
        ),
        "GO": (
            f"Moderate effect (d={d:.4f}, {direction}). State conditioning meaningfully "
            "benefits enrichment. Publishable with tempered claims."
        ),
        "PIVOT": (
            f"Weak effect (d={d:.4f}, {direction}). State conditioning marginally benefits. "
            "Pivot framing to diversity + multi-pocket docking."
        ),
        "NO_GO": (
            f"Negligible effect (d={d:.4f}, {direction}). State conditioning provides no "
            "meaningful benefit. Consider negative-result or benchmark-only publication."
        ),
    }
    return msgs[rec]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--greedy", action="store_true",
                        help="Use greedy (T=0) generation instead of stochastic")
    parser.add_argument("--all-seeds", action="store_true",
                        help="Use all 10 seeds instead of original 3")
    args = parser.parse_args()

    global SEEDS
    SEEDS = ALL_SEEDS if args.all_seeds else SEEDS_DEFAULT

    suffix = "_greedy" if args.greedy else ""
    gen_label = "greedy (T=0)" if args.greedy else "stochastic (T=0.8)"

    logger.info("=" * 70)
    logger.info("Ablation C v3: Transformer VAE — Conditioned vs Unconditioned")
    logger.info("Generation mode: %s", gen_label)
    logger.info("Pre-registration ref: commit 9e7cf96")
    logger.info("=" * 70)

    # ── Load training data ─────────────────────────────────────────────
    train_data = load_json_file(REPO_ROOT / "data" / "processed" / "egfr_smiles_train.json")
    training_smiles_list = [d["smiles"] for d in train_data]
    training_smiles_set = set(training_smiles_list)
    logger.info("Training set: %d SMILES", len(training_smiles_list))

    # ── Load conditioned candidates (3 seeds) ──────────────────────────
    logger.info("Loading conditioned Transformer VAE candidates...")
    cond_per_seed: dict[int, list[dict]] = {}
    cond_smiles_per_seed: dict[int, list[str]] = {}
    for seed in SEEDS:
        path = REPO_ROOT / "artifacts" / "generation" / f"transformer_vae_conditioned_seed{seed}{suffix}.json"
        if not path.exists():
            logger.error("Missing: %s", path)
            sys.exit(1)
        data = load_json_file(path)
        # Filter to valid only
        valid_cands = [c for c in data["candidates"] if c.get("is_valid", True)]
        cond_per_seed[seed] = valid_cands
        cond_smiles_per_seed[seed] = extract_smiles(valid_cands)
        logger.info("  Seed %d: %d valid candidates (of %d total), states=%s",
                     seed, len(valid_cands), len(data["candidates"]),
                     data.get("states", []))

    # Pool conditioned (dedup)
    cond_all_cands = []
    cond_all_smiles = []
    seen = set()
    for seed in SEEDS:
        for c in cond_per_seed[seed]:
            if c["smiles"] not in seen:
                seen.add(c["smiles"])
                cond_all_cands.append(c)
                cond_all_smiles.append(c["smiles"])
    logger.info("  Pooled conditioned: %d unique valid", len(cond_all_cands))

    # ── Load unconditioned candidates (3 seeds) ────────────────────────
    logger.info("Loading unconditioned Transformer VAE candidates...")
    uncond_per_seed: dict[int, list[dict]] = {}
    uncond_smiles_per_seed: dict[int, list[str]] = {}
    for seed in SEEDS:
        path = REPO_ROOT / "artifacts" / "generation" / f"transformer_vae_unconditioned_seed{seed}{suffix}.json"
        if not path.exists():
            logger.error("Missing: %s", path)
            sys.exit(1)
        data = load_json_file(path)
        valid_cands = [c for c in data["candidates"] if c.get("is_valid", True)]
        uncond_per_seed[seed] = valid_cands
        uncond_smiles_per_seed[seed] = extract_smiles(valid_cands)
        logger.info("  Seed %d: %d valid candidates", seed, len(valid_cands))

    # Pool unconditioned (dedup)
    uncond_all_cands = []
    uncond_all_smiles = []
    seen_u = set()
    for seed in SEEDS:
        for c in uncond_per_seed[seed]:
            if c["smiles"] not in seen_u:
                seen_u.add(c["smiles"])
                uncond_all_cands.append(c)
                uncond_all_smiles.append(c["smiles"])
    logger.info("  Pooled unconditioned: %d unique valid", len(uncond_all_cands))

    # ── STEP 1: Score all candidates ───────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 1: Scoring with unified scoring function")
    logger.info("=" * 50)

    scored_cond_per_seed: dict[int, list[dict]] = {}
    for seed in SEEDS:
        logger.info("Scoring conditioned seed %d...", seed)
        scored_cond_per_seed[seed] = score_candidates(
            cond_per_seed[seed], f"cond_s{seed}")

    scored_cond_pooled = score_candidates(cond_all_cands, "cond_pooled")

    scored_uncond_per_seed: dict[int, list[dict]] = {}
    for seed in SEEDS:
        logger.info("Scoring unconditioned seed %d...", seed)
        scored_uncond_per_seed[seed] = score_candidates(
            uncond_per_seed[seed], f"uncond_s{seed}")

    scored_uncond_pooled = score_candidates(uncond_all_cands, "uncond_pooled")

    # ── STEP 2: Retrospective enrichment ───────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 2: Retrospective enrichment (cutoff=%d)", RETROSPECTIVE_CUTOFF)
    logger.info("=" * 50)

    retro_cond_ps: dict[str, dict] = {}
    for seed in SEEDS:
        retro_cond_ps[str(seed)] = compute_retrospective(
            scored_cond_per_seed[seed], training_smiles_set, f"cond_s{seed}")

    retro_cond_pooled = compute_retrospective(
        scored_cond_pooled, training_smiles_set, "cond_pooled")

    retro_uncond_ps: dict[str, dict] = {}
    for seed in SEEDS:
        retro_uncond_ps[str(seed)] = compute_retrospective(
            scored_uncond_per_seed[seed], training_smiles_set, f"uncond_s{seed}")

    retro_uncond_pooled = compute_retrospective(
        scored_uncond_pooled, training_smiles_set, "uncond_pooled")

    # ── STEP 3: Effect sizes ───────────────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 3: Effect size computation")
    logger.info("=" * 50)

    cond_ef10_ps = [retro_cond_ps[str(s)]["ef_10"] for s in SEEDS]
    uncond_ef10_ps = [retro_uncond_ps[str(s)]["ef_10"] for s in SEEDS]

    for seed in SEEDS:
        logger.info("  Seed %d: cond EF@10=%.4f, uncond EF@10=%.4f",
                     seed, retro_cond_ps[str(seed)]["ef_10"],
                     retro_uncond_ps[str(seed)]["ef_10"])

    d_ef10 = cohens_d(cond_ef10_ps, uncond_ef10_ps) if (
        len(set(cond_ef10_ps)) > 0 and len(set(uncond_ef10_ps)) > 0) else 0.0

    cond_scores = [c["composite_score"] for c in scored_cond_pooled]
    uncond_scores = [c["composite_score"] for c in scored_uncond_pooled]

    d_composite = cohens_d(cond_scores, uncond_scores)
    cliff_d = cliff_delta(cond_scores, uncond_scores)
    mwu = mann_whitney_u(cond_scores, uncond_scores)

    logger.info("  d(composite, pooled): %.4f", d_composite)
    logger.info("  d(EF@10, per-seed):   %.4f", d_ef10)
    logger.info("  Cliff's delta:        %.4f", cliff_d)
    logger.info("  MWU p-value:          %.6f", mwu.p_value)

    # Per-seed composite d
    d_ps_composite: dict[str, float] = {}
    for seed in SEEDS:
        cs = [c["composite_score"] for c in scored_cond_per_seed[seed]]
        us = [c["composite_score"] for c in scored_uncond_per_seed[seed]]
        d_ps_composite[str(seed)] = round(cohens_d(cs, us), 4)

    # Future drug similarity d
    future_drugs = get_future_drugs(RETROSPECTIVE_CUTOFF)
    future_smiles = [d["smiles"] for d in future_drugs]
    cond_sims = compute_candidate_future_similarities(
        extract_smiles(scored_cond_pooled), future_smiles)
    uncond_sims = compute_candidate_future_similarities(
        extract_smiles(scored_uncond_pooled), future_smiles)
    d_similarity = cohens_d(cond_sims, uncond_sims)

    # Bootstrap CI on score difference
    mean_uncond = float(np.mean(uncond_scores))
    ci_diff = bca_bootstrap_confidence_interval(
        cond_scores,
        lambda x: float(np.mean(x)) - mean_uncond,
        alpha=0.05, n_bootstrap=BOOTSTRAP_N, seed=BOOTSTRAP_SEED,
    )

    # ── STEP 4: VAE quality metrics ────────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 4: VAE quality metrics")
    logger.info("=" * 50)

    vq_cond_ps: dict[str, dict] = {}
    for seed in SEEDS:
        vq_cond_ps[str(seed)] = compute_vae_quality(
            cond_smiles_per_seed[seed], training_smiles_list, f"cond_s{seed}")

    vq_cond_pooled = compute_vae_quality(
        cond_all_smiles, training_smiles_list, "cond_pooled")

    vq_uncond_ps: dict[str, dict] = {}
    for seed in SEEDS:
        vq_uncond_ps[str(seed)] = compute_vae_quality(
            uncond_smiles_per_seed[seed], training_smiles_list, f"uncond_s{seed}")

    vq_uncond_pooled = compute_vae_quality(
        uncond_all_smiles, training_smiles_list, "uncond_pooled")

    # ── STEP 5: Per-component analysis ─────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 5: Per-component score analysis")
    logger.info("=" * 50)

    comp_names = ["reference_similarity", "druglikeness", "docking_proxy", "state_specificity"]
    comp_analysis = {}
    for cn in comp_names:
        cv = [c["components"].get(cn, 0.0) for c in scored_cond_pooled]
        uv = [c["components"].get(cn, 0.0) for c in scored_uncond_pooled]
        cd = cohens_d(cv, uv)
        comp_analysis[cn] = {
            "conditioned_mean": round(float(np.mean(cv)), 4),
            "conditioned_std": round(float(np.std(cv, ddof=1)), 4) if len(cv) > 1 else 0.0,
            "unconditioned_mean": round(float(np.mean(uv)), 4),
            "unconditioned_std": round(float(np.std(uv, ddof=1)), 4) if len(uv) > 1 else 0.0,
            "cohens_d": round(cd, 4),
            "cliff_delta": round(cliff_delta(cv, uv), 4),
        }
        logger.info("  %s: cond=%.4f, uncond=%.4f, d=%.4f", cn,
                     comp_analysis[cn]["conditioned_mean"],
                     comp_analysis[cn]["unconditioned_mean"], cd)

    # ── STEP 6: Gate G2 decision ───────────────────────────────────────
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 6: Gate G2 Decision (Transformer VAE)")
    logger.info("=" * 50)

    recommendation = make_gate_recommendation(d_composite)
    interpretation = interpret_gate(recommendation, d_composite)

    logger.info("  d(composite, pooled): %.4f", d_composite)
    logger.info("  d(EF@10, per-seed):   %.4f", d_ef10)
    logger.info("  GATE G2: %s", recommendation)
    logger.info("  %s", interpretation)

    # ── Assemble results ───────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()

    results: dict[str, Any] = {
        "generated_at": now,
        "task": "Ablation C v3: Transformer VAE conditioned vs unconditioned",
        "pre_registration_ref": "commit 9e7cf96 (docs/pre-registration.md)",
        "version": "v3",
        "generation_mode": gen_label,
        "model_note": (
            "v3 uses Transformer VAE (SMILES, Transformer decoder, kl_weight=1.0, "
            "word_dropout=0.1, free-bits KL). Replaces v2 which used broken SELFIES "
            "GRU VAE (0% reconstruction, 0 aromatic rings)."
        ),
        "analysis_notes": {
            "conditioned_model": (
                "3-state Transformer VAE (DFGin_aCin, DFGin_aCout, DFGout_aCin). "
                f"200 candidates/state/seed = 600/seed, 3 seeds. Mode: {gen_label}."
            ),
            "unconditioned_model": (
                "1-state Transformer VAE. "
                f"600 candidates/seed, 3 seeds. Mode: {gen_label}."
            ),
            "scoring_fairness": (
                "Both scored with identical unified scoring. "
                "state_specificity = 0 for both (empty state_smiles_map)."
            ),
        },
        "conditioned_per_seed": {},
        "conditioned_pooled": {
            "n_candidates": len(scored_cond_pooled),
            "n_seeds": len(SEEDS),
            "seeds": SEEDS,
            "mean_composite_score": round(float(np.mean(cond_scores)), 4),
            "std_composite_score": round(float(np.std(cond_scores, ddof=1)), 4),
            "median_composite_score": round(float(np.median(cond_scores)), 4),
            "retrospective": retro_cond_pooled,
            "vae_quality": vq_cond_pooled,
            "score_distribution": {
                "min": round(float(np.min(cond_scores)), 4),
                "p25": round(float(np.percentile(cond_scores, 25)), 4),
                "p50": round(float(np.percentile(cond_scores, 50)), 4),
                "p75": round(float(np.percentile(cond_scores, 75)), 4),
                "max": round(float(np.max(cond_scores)), 4),
            },
        },
        "unconditioned_per_seed": {},
        "unconditioned_pooled": {
            "n_candidates": len(scored_uncond_pooled),
            "n_seeds": len(SEEDS),
            "seeds": SEEDS,
            "mean_composite_score": round(float(np.mean(uncond_scores)), 4),
            "std_composite_score": round(float(np.std(uncond_scores, ddof=1)), 4),
            "median_composite_score": round(float(np.median(uncond_scores)), 4),
            "retrospective": retro_uncond_pooled,
            "vae_quality": vq_uncond_pooled,
            "score_distribution": {
                "min": round(float(np.min(uncond_scores)), 4),
                "p25": round(float(np.percentile(uncond_scores, 25)), 4),
                "p50": round(float(np.percentile(uncond_scores, 50)), 4),
                "p75": round(float(np.percentile(uncond_scores, 75)), 4),
                "max": round(float(np.max(uncond_scores)), 4),
            },
        },
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
                "point_estimate": round(float(np.mean(cond_scores)) - float(np.mean(uncond_scores)), 4),
                "ci_lower": ci_diff.ci_lower,
                "ci_upper": ci_diff.ci_upper,
                "method": "BCa bootstrap (10000 iterations)",
            },
            "per_seed_ef10": {
                "conditioned": {str(s): retro_cond_ps[str(s)]["ef_10"] for s in SEEDS},
                "unconditioned": {str(s): retro_uncond_ps[str(s)]["ef_10"] for s in SEEDS},
            },
            "per_seed_cohens_d_composite": d_ps_composite,
        },
        "component_analysis": comp_analysis,
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
        },
        "v2_comparison": {
            "note": "v2 (SELFIES GRU VAE) results for comparison",
            "v2_d_composite": -0.0385,
            "v2_d_ef10": 0.0,
            "v2_gate_g2": "NO_GO",
            "v2_ef10_all_seeds": 0.0,
            "v2_reason": "Total autoencoder failure (0% reconstruction, 0 aromatic rings)",
        },
    }

    # Per-seed details
    for seed in SEEDS:
        cs = [c["composite_score"] for c in scored_cond_per_seed[seed]]
        results["conditioned_per_seed"][str(seed)] = {
            "n_candidates": len(scored_cond_per_seed[seed]),
            "mean_composite_score": round(float(np.mean(cs)), 4),
            "std_composite_score": round(float(np.std(cs, ddof=1)), 4) if len(cs) > 1 else 0.0,
            "retrospective": retro_cond_ps[str(seed)],
            "vae_quality": vq_cond_ps[str(seed)],
        }
        us = [c["composite_score"] for c in scored_uncond_per_seed[seed]]
        results["unconditioned_per_seed"][str(seed)] = {
            "n_candidates": len(scored_uncond_per_seed[seed]),
            "mean_composite_score": round(float(np.mean(us)), 4),
            "std_composite_score": round(float(np.std(us, ddof=1)), 4) if len(us) > 1 else 0.0,
            "retrospective": retro_uncond_ps[str(seed)],
            "vae_quality": vq_uncond_ps[str(seed)],
        }

    # Save
    seed_tag = "_10seed" if args.all_seeds else ""
    out_name = f"ablation_c_results_v3{'_greedy' if args.greedy else ''}{seed_tag}.json"
    output_path = REPO_ROOT / "artifacts" / "evaluation" / out_name
    save_json(results, output_path)

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("ABLATION C v3 RESULTS SUMMARY (Transformer VAE, %s)", gen_label)
    logger.info("=" * 70)
    logger.info("")
    logger.info("Conditioned (3-state, %d seeds, %d candidates):",
                len(SEEDS), len(scored_cond_pooled))
    logger.info("  Mean score: %.4f +/- %.4f",
                results["conditioned_pooled"]["mean_composite_score"],
                results["conditioned_pooled"]["std_composite_score"])
    logger.info("  EF@10: %.4f [%.4f, %.4f]",
                retro_cond_pooled["ef_10"],
                retro_cond_pooled["ef_10_ci_lower"],
                retro_cond_pooled["ef_10_ci_upper"])
    logger.info("")
    logger.info("Unconditioned (%d seeds, %d candidates):",
                len(SEEDS), len(scored_uncond_pooled))
    logger.info("  Mean score: %.4f +/- %.4f",
                results["unconditioned_pooled"]["mean_composite_score"],
                results["unconditioned_pooled"]["std_composite_score"])
    logger.info("  EF@10: %.4f [%.4f, %.4f]",
                retro_uncond_pooled["ef_10"],
                retro_uncond_pooled["ef_10_ci_lower"],
                retro_uncond_pooled["ef_10_ci_upper"])
    logger.info("")
    logger.info("Per-seed EF@10:")
    for seed in SEEDS:
        logger.info("  Seed %d: cond=%.4f, uncond=%.4f", seed,
                     retro_cond_ps[str(seed)]["ef_10"],
                     retro_uncond_ps[str(seed)]["ef_10"])
    logger.info("")
    logger.info("Effect sizes:")
    logger.info("  d(composite):  %.4f (v2: -0.0385)", d_composite)
    logger.info("  d(EF@10):      %.4f (v2: 0.0)", d_ef10)
    logger.info("  d(drug sim):   %.4f", d_similarity)
    logger.info("  Cliff's delta: %.4f", cliff_d)
    logger.info("  MWU p-value:   %.6f", mwu.p_value)
    logger.info("  Score diff CI: [%.4f, %.4f]", ci_diff.ci_lower, ci_diff.ci_upper)
    logger.info("")
    logger.info("GATE G2 (Transformer VAE): %s (d=%.4f)  [v2 was NO_GO (d=-0.04)]",
                recommendation, d_composite)
    logger.info("  %s", interpretation)
    logger.info("")
    logger.info("Results: %s", output_path)


if __name__ == "__main__":
    main()
