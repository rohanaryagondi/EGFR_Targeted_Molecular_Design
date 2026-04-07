#!/usr/bin/env python3
"""Phase 7 — Full comparison pipeline with ML integration.

Runs both pipelines (static baseline and state-aware), optionally
incorporates VAE-generated candidates and ADMET safety filtering, scores
with the full MPNN cascade, and runs statistical tests.

Outputs:
  artifacts/ranking/comparison.json
  artifacts/ranking/figures/*.txt

Usage::

    # Minimal (template candidates only, no ADMET, no VAE):
    python scripts/compare_baseline_vs_state_aware.py

    # Full ML pipeline:
    python scripts/compare_baseline_vs_state_aware.py \
        --vae-candidates artifacts/generation/vae_candidates.json \
        --admet-filter \
        --statistics
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from statebind.baselines.pipeline import run_static_baseline
from statebind.evaluation.comparison import run_full_comparison
from statebind.evaluation.figures import generate_all_figures
from statebind.evaluation.tables import (
    novelty_by_state_table,
    novelty_by_strategy_table,
    rank_shift_table,
    summary_table,
    top_candidates_table,
)
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.generation.models import (
    MultiStateGenerationResult,
    StateConditionedLibrary,
)
from statebind.ranking.scoring import (
    merge_rankings,
    rank_state_aware,
    rank_static_baseline,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _merge_vae_into_generation(
    generation: MultiStateGenerationResult,
    vae_path: str,
) -> MultiStateGenerationResult:
    """Load VAE candidates and merge into the generation result.

    VAE candidates are added to the matching state library (or create
    new libraries for states not covered by template generation).
    Deduplication happens downstream in filter_all_states.
    """
    from statebind.generation.vae_integration import (
        build_vae_libraries,
        load_vae_candidates,
    )

    candidates = load_vae_candidates(vae_path)
    vae_libraries = build_vae_libraries(candidates)

    if not vae_libraries:
        logger.warning("No valid VAE candidates loaded from %s", vae_path)
        return generation

    logger.info(
        "Loaded %d VAE candidates across %d states",
        len(candidates),
        len(vae_libraries),
    )

    # Build lookup of existing libraries by state
    existing: dict[str, StateConditionedLibrary] = {
        lib.state: lib for lib in generation.libraries
    }

    merged_libraries: list[StateConditionedLibrary] = []
    all_smiles: set[str] = set()
    total = 0

    for lib in generation.libraries:
        merged_libraries.append(lib)
        total += lib.n_candidates
        all_smiles.update(c.smiles for c in lib.candidates)

    for vae_lib in vae_libraries:
        if vae_lib.state in existing:
            # Merge VAE candidates into existing library
            target = existing[vae_lib.state]
            # Find the merged library (same object since we appended it)
            for mlib in merged_libraries:
                if mlib.state == vae_lib.state:
                    combined = list(mlib.candidates) + list(vae_lib.candidates)
                    strategies = list(set(mlib.strategies_used + vae_lib.strategies_used))
                    # Create updated library
                    idx = merged_libraries.index(mlib)
                    merged_libraries[idx] = StateConditionedLibrary(
                        state=mlib.state,
                        representative_pdb=mlib.representative_pdb,
                        pocket_volume=mlib.pocket_volume,
                        back_pocket_accessible=mlib.back_pocket_accessible,
                        candidates=combined,
                        n_candidates=len(combined),
                        strategies_used=strategies,
                        generation_config=mlib.generation_config,
                    )
                    total += vae_lib.n_candidates
                    all_smiles.update(c.smiles for c in vae_lib.candidates)
                    break
        else:
            # New state from VAE — add as new library
            merged_libraries.append(vae_lib)
            total += vae_lib.n_candidates
            all_smiles.update(c.smiles for c in vae_lib.candidates)

    # Recompute cross-state overlap
    state_smiles: dict[str, set[str]] = {}
    for lib in merged_libraries:
        state_smiles[lib.state] = {c.smiles for c in lib.candidates}

    overlap: dict[str, int] = {}
    states_list = sorted(state_smiles.keys())
    for i, s1 in enumerate(states_list):
        for j, s2 in enumerate(states_list):
            if i < j:
                shared = len(state_smiles[s1] & state_smiles[s2])
                overlap[f"{s1}|{s2}"] = shared

    now = datetime.now(timezone.utc).isoformat()

    return MultiStateGenerationResult(
        states=states_list,
        libraries=merged_libraries,
        total_candidates=total,
        total_unique_smiles=len(all_smiles),
        cross_state_overlap=overlap,
        generated_at=now,
        notes=(
            f"Merged template + VAE generation. "
            f"{len(candidates)} VAE candidates added."
        ),
    )


def _apply_admet_filter(
    filtered_libraries: list,
) -> tuple[list, dict]:
    """Apply ADMET safety filtering to already-filtered candidates.

    Returns the filtered libraries (with ADMET-failing candidates removed)
    and a summary dict of ADMET statistics.
    """
    try:
        from statebind.ml.admet_predictor import (
            check_admet_pass,
            predict_admet,
        )
    except ImportError:
        logger.warning("ADMET predictor not available — skipping ADMET filtering")
        return filtered_libraries, {"available": False}

    admet_stats: dict[str, int] = {
        "total_checked": 0,
        "total_passed": 0,
        "total_failed": 0,
        "failures_by_endpoint": {},
    }

    for lib in filtered_libraries:
        passed_candidates = []
        for candidate in lib.candidates:
            admet_stats["total_checked"] += 1

            predictions = predict_admet(candidate.smiles)
            if not predictions:
                # No model available or failed — permissive pass
                passed_candidates.append(candidate)
                admet_stats["total_passed"] += 1
                continue

            passed, failures = check_admet_pass(predictions)
            if passed:
                passed_candidates.append(candidate)
                admet_stats["total_passed"] += 1
            else:
                admet_stats["total_failed"] += 1
                for endpoint in failures:
                    admet_stats["failures_by_endpoint"][endpoint] = (
                        admet_stats["failures_by_endpoint"].get(endpoint, 0) + 1
                    )

        lib.candidates = passed_candidates
        lib.n_passed = len(passed_candidates)
        lib.pass_rate = lib.n_passed / max(lib.n_input, 1)

    admet_stats["available"] = True
    return filtered_libraries, admet_stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare static baseline vs state-aware pipeline"
    )
    parser.add_argument(
        "--vae-candidates",
        type=str,
        default=None,
        help="Path to VAE candidates JSON (from generate_vae_candidates.py)",
    )
    parser.add_argument(
        "--admet-filter",
        action="store_true",
        help="Apply ADMET safety filtering",
    )
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Run Mann-Whitney U and sensitivity analysis",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts/ranking",
        help="Output directory for comparison artifacts",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Run static baseline ─────────────────────────────────
    print("=" * 60)
    print("STEP 1: Running static baseline pipeline...")
    print("=" * 60)
    baseline = run_static_baseline()
    print(f"  Static baseline: {len(baseline.filtered.results)} candidates after filtering")

    # ── Step 2: Generate state-aware candidates ─────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Generating state-aware candidates...")
    print("=" * 60)
    generation = generate_all_states()
    print(f"  Template generation: {generation.total_candidates} total, "
          f"{generation.total_unique_smiles} unique")

    # ── Step 2b: Merge VAE candidates if available ──────────────────
    if args.vae_candidates:
        vae_path = Path(args.vae_candidates)
        if vae_path.exists():
            print(f"\n  Merging VAE candidates from {vae_path}...")
            generation = _merge_vae_into_generation(generation, str(vae_path))
            print(f"  After VAE merge: {generation.total_candidates} total, "
                  f"{generation.total_unique_smiles} unique")
        else:
            print(f"  WARNING: VAE candidates file not found: {vae_path}")

    # ── Step 3: Filter ───���──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: Applying chemistry filters...")
    print("=" * 60)
    filtered = filter_all_states(generation)
    print(f"  Chemistry filter: {filtered.total_input} → {filtered.total_passed} "
          f"({filtered.overall_pass_rate:.1%})")

    # ── Step 3b: ADMET filtering ────────────────────────────────────
    admet_stats: dict = {"available": False}
    if args.admet_filter:
        print("\n  Applying ADMET safety filtering...")
        filtered.libraries, admet_stats = _apply_admet_filter(filtered.libraries)
        # Recompute totals
        filtered.total_passed = sum(lib.n_passed for lib in filtered.libraries)
        filtered.overall_pass_rate = filtered.total_passed / max(filtered.total_input, 1)
        if admet_stats.get("available"):
            print(f"  ADMET filter: {admet_stats['total_checked']} checked, "
                  f"{admet_stats['total_passed']} passed, "
                  f"{admet_stats['total_failed']} failed")
            if admet_stats.get("failures_by_endpoint"):
                for ep, count in sorted(admet_stats["failures_by_endpoint"].items()):
                    print(f"    {ep}: {count} failures")
        else:
            print("  ADMET model not available — skipped")

    # ── Step 4: Score and rank ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Scoring with unified function (MPNN cascade)...")
    print("=" * 60)
    static_pool = rank_static_baseline(baseline.filtered)
    state_pool = rank_state_aware(filtered)
    merged = merge_rankings(static_pool, state_pool)

    print(f"  Static pool:      {static_pool.n_ranked} candidates scored")
    print(f"  State-aware pool: {state_pool.n_ranked} candidates scored")
    print(f"  Merged:           {len(merged.merged)} unique candidates")
    print(f"  Scoring method:   {static_pool.scoring_method[:80]}...")

    # ── Step 5: Comparison + statistics ─────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: Running comparison suite...")
    print("=" * 60)
    result = run_full_comparison(
        merged, top_k=10, run_statistics=args.statistics,
    )

    # ── Generate tables ─────────────────────────────────────────────
    tables = {
        "summary": summary_table(result),
        "top_10_global": top_candidates_table(merged, k=10),
        "rank_shifts": rank_shift_table(merged, top_n=10),
        "novelty_by_strategy": novelty_by_strategy_table(result),
        "novelty_by_state": novelty_by_state_table(result),
    }

    # ── Generate figures ────────────────────────────────────────────
    figures = generate_all_figures(result, merged, output_dir=fig_dir)

    # ── Write comparison artifact ───────────────────────────────────
    comparison_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_config": {
            "vae_candidates": args.vae_candidates,
            "admet_filter": args.admet_filter,
            "statistics": args.statistics,
        },
        "overlap": {
            "static_total": result.overlap.static_total,
            "state_aware_total": result.overlap.state_aware_total,
            "shared": result.overlap.shared,
            "static_only": result.overlap.static_only,
            "state_aware_only": result.overlap.state_aware_only,
            "jaccard": result.overlap.jaccard,
        },
        "diversity": {
            "static": round(result.diversity.static.diversity_score, 4),
            "state_aware": round(result.diversity.state_aware.diversity_score, 4),
            "delta": result.diversity.delta_diversity,
        },
        "scores": {
            "static": result.scores.static_stats,
            "state_aware": result.scores.state_aware_stats,
            "delta_mean": result.scores.delta_mean,
        },
        "top_k": {
            "k": result.top_k.k,
            "static_count": result.top_k.static_count,
            "state_aware_count": result.top_k.state_aware_count,
        },
        "novelty": {
            "n_novel": result.novelty.n_novel,
            "by_strategy": result.novelty.novel_strategies,
            "by_state": result.novelty.novel_states,
        },
        "mean_ranks": result.mean_ranks,
        "admet": admet_stats,
        "tables": tables,
    }

    # Add statistical test results if available
    if result.statistical_tests:
        comparison_data["statistical_tests"] = []
        for test in result.statistical_tests:
            if hasattr(test, "__dict__"):
                comparison_data["statistical_tests"].append(
                    {k: v for k, v in test.__dict__.items()
                     if not k.startswith("_")}
                )
            else:
                comparison_data["statistical_tests"].append(str(test))

    if result.sensitivity is not None:
        try:
            comparison_data["sensitivity"] = {
                "results": [
                    {k: v for k, v in r.__dict__.items() if not k.startswith("_")}
                    for r in result.sensitivity.results
                ] if hasattr(result.sensitivity, "results") else str(result.sensitivity),
            }
        except Exception:
            comparison_data["sensitivity"] = str(result.sensitivity)

    path = output_dir / "comparison.json"
    with open(path, "w") as f:
        json.dump(comparison_data, f, indent=2, default=str)
    print(f"\nWrote {path}")

    # ── Print summary ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("COMPARISON RESULTS")
    print("=" * 60)

    print("\n── Head-to-Head ──")
    for row in tables["summary"]:
        print(f"  {row['metric']:<40} Static={row['static_baseline']:<10} "
              f"State={row['state_aware']:<10} Delta={row['delta']}")

    print(f"\n── Scoring Method ──")
    print(f"  {static_pool.scoring_method}")

    # Print statistical test results
    if result.statistical_tests:
        print(f"\n── Statistical Tests ──")
        for test in result.statistical_tests:
            if hasattr(test, "test_name"):
                p_val = getattr(test, "p_value", "N/A")
                sig = getattr(test, "significant", "N/A")
                stat = getattr(test, "statistic", "N/A")
                effect = getattr(test, "effect_size", "N/A")
                print(f"  {test.test_name}:")
                print(f"    Statistic: {stat}")
                print(f"    p-value:   {p_val}")
                print(f"    Significant (p<0.05): {sig}")
                if effect != "N/A":
                    print(f"    Effect size: {effect}")
            else:
                print(f"  {test}")

    # Print figures
    for name, fig in figures.items():
        print(f"\n{fig}")

    # ── Null hypothesis verdict ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("NULL HYPOTHESIS STATUS")
    print("=" * 60)

    if result.statistical_tests:
        # Check for significant difference (p < 0.05) AND correct direction
        # (state-aware mean > static mean).  Both conditions are required to
        # reject H0: "state-aware does NOT produce superior candidates."
        any_significant = any(t.p_value < 0.05 for t in result.statistical_tests)
        delta = result.scores.delta_mean
        state_aware_better = delta > 0

        if any_significant and state_aware_better:
            print("  REJECTED: State-aware pipeline shows statistically significant")
            print(f"  advantage (p < 0.05, delta mean = {delta:+.4f}).")
        elif any_significant and not state_aware_better:
            print("  NOT REJECTED: Statistically significant difference found,")
            print(f"  but static pipeline scores higher (delta mean = {delta:+.4f}).")
        else:
            print("  NOT REJECTED: No statistically significant difference found")
            print("  between state-aware and static pipelines (p >= 0.05).")
    else:
        print("  PENDING: Statistical tests not run. Use --statistics flag.")

    print(f"\nArtifacts in {output_dir}/")
    print(f"Figures in {fig_dir}/")


if __name__ == "__main__":
    main()
