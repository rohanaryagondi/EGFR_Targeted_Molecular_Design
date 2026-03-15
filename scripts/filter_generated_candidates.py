#!/usr/bin/env python3
"""Filter state-conditioned candidates with state-aware rules.

Type-I states (DFGin) get standard Lipinski-like filters.
Type-II states (DFGout) get relaxed MW/size limits.

Usage:
    python scripts/filter_generated_candidates.py
"""

import json
from pathlib import Path

from statebind.generation.diversity import analyze_cross_state_diversity
from statebind.generation.evaluation import (
    compare_with_static_baseline,
    evaluate_generation,
    evaluation_to_dict,
    save_evaluation,
)
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.baselines.pipeline import run_static_baseline
from statebind.utils.io import save_json

ARTIFACT_DIR = Path("artifacts/generation/filtered_v1")


def main() -> None:
    print("=" * 60)
    print("Filtering State-Conditioned Candidates")
    print("=" * 60)

    # Generate
    generation = generate_all_states()
    print(f"\nGenerated {generation.total_candidates} candidates across {len(generation.states)} states")

    # Filter
    filtered = filter_all_states(generation)
    print(f"After filtering: {filtered.total_passed} / {filtered.total_input} passed "
          f"({filtered.overall_pass_rate:.1%})")

    for lib in filtered.libraries:
        print(f"\n  {lib.state}:")
        print(f"    Input: {lib.n_input}, Passed: {lib.n_passed}, Rate: {lib.pass_rate:.1%}")
        if lib.property_stats.get("estimated_mw"):
            mw = lib.property_stats["estimated_mw"]
            print(f"    MW range: {mw.get('min', 0):.0f}–{mw.get('max', 0):.0f} "
                  f"(mean {mw.get('mean', 0):.0f})")

    # Diversity analysis
    diversity = analyze_cross_state_diversity(filtered)

    print(f"\n--- Diversity ---")
    for sd in diversity.per_state:
        print(f"  {sd.state}: diversity={sd.intra_diversity.diversity_score:.3f}, "
              f"state-unique={sd.n_state_unique} ({sd.unique_fraction:.1%})")

    print(f"\n  Global diversity: {diversity.global_diversity.diversity_score:.3f}")
    print(f"  Total unique across all states: {diversity.total_unique_across_all}")

    # Evaluation
    evaluation = evaluate_generation(generation, filtered, diversity)

    # Compare with static baseline
    print(f"\n--- Static Baseline Comparison ---")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        static_result = run_static_baseline(Path(tmpdir))
        static_smiles = {c.smiles for c in static_result.ranked.candidates}

    comparison = compare_with_static_baseline(filtered, static_smiles)
    print(f"  Static baseline: {comparison.static_n_candidates} candidates")
    print(f"  State-conditioned: {comparison.state_conditioned_n_candidates} unique candidates")
    print(f"  Overlap: {comparison.overlap_with_static}")
    print(f"  State-only (new): {comparison.state_only_candidates}")
    print(f"  Static-only (missed): {comparison.static_only_candidates}")
    print(f"  Diversity — static: {comparison.diversity_static:.3f}, "
          f"state-conditioned: {comparison.diversity_state_conditioned:.3f}")

    evaluation.baseline_comparison = {
        "static_n": comparison.static_n_candidates,
        "state_conditioned_n": comparison.state_conditioned_n_candidates,
        "overlap": comparison.overlap_with_static,
        "state_only_new": comparison.state_only_candidates,
        "diversity_static": round(comparison.diversity_static, 4),
        "diversity_state_conditioned": round(comparison.diversity_state_conditioned, 4),
    }

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    save_evaluation(evaluation, ARTIFACT_DIR / "evaluation.json")

    for lib in filtered.libraries:
        state_dir = ARTIFACT_DIR / lib.state
        state_dir.mkdir(parents=True, exist_ok=True)
        save_json(
            {
                "state": lib.state,
                "n_input": lib.n_input,
                "n_passed": lib.n_passed,
                "pass_rate": round(lib.pass_rate, 4),
                "property_stats": lib.property_stats,
                "candidates": [
                    {"id": c.candidate_id, "smiles": c.smiles,
                     "strategy": c.strategy.value}
                    for c in lib.candidates
                ],
            },
            state_dir / "filtered_candidates.json",
        )

    save_json(
        {
            "overlap_matrix": diversity.overlap_matrix,
            "per_state": [
                {
                    "state": sd.state,
                    "intra_diversity": round(sd.intra_diversity.diversity_score, 4),
                    "n_unique": sd.n_state_unique,
                    "unique_fraction": round(sd.unique_fraction, 4),
                }
                for sd in diversity.per_state
            ],
            "global_diversity": round(diversity.global_diversity.diversity_score, 4),
        },
        ARTIFACT_DIR / "diversity_report.json",
    )

    save_json(
        {
            "static_n": comparison.static_n_candidates,
            "state_conditioned_n": comparison.state_conditioned_n_candidates,
            "overlap": comparison.overlap_with_static,
            "state_only_new": comparison.state_only_candidates,
            "static_only_missed": comparison.static_only_candidates,
            "diversity_static": round(comparison.diversity_static, 4),
            "diversity_state_conditioned": round(comparison.diversity_state_conditioned, 4),
        },
        ARTIFACT_DIR / "baseline_comparison.json",
    )

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
