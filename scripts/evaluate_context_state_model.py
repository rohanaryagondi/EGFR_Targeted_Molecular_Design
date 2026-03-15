#!/usr/bin/env python3
"""Evaluate context-to-state models with detailed diagnostics.

Loads trained models (via re-training, since we don't persist weights),
runs evaluation on all splits, and produces detailed per-mutation
diagnostics and calibration analysis.

Usage:
    python scripts/evaluate_context_state_model.py
"""

import json
from pathlib import Path

from statebind.context.evaluation import (
    compare_ablations,
    evaluate_model,
    evaluation_to_dict,
)
from statebind.context.models import ModelConfig
from statebind.context.training import load_data, run_ablation_suite, train_model
from statebind.utils.io import save_json

ARTIFACT_DIR = Path("artifacts/context/evaluation_v1")


def main() -> None:
    print("=" * 60)
    print("Context-to-State: Detailed Evaluation")
    print("=" * 60)

    context = load_data(split_seed=42)

    # Re-train ablation suite (deterministic — same results)
    experiments = run_ablation_suite(context)
    comparison = compare_ablations(experiments, eval_split="test")

    # Find the best model
    best_name = comparison.best_model
    best_exp = next(e for e in experiments if e.name == best_name)
    assert best_exp.trained is not None

    print(f"\nBest model: {best_name}")
    print(f"Test accuracy: {comparison.best_accuracy:.3f}")

    # Detailed diagnostics for best model
    test_eval = evaluate_model(best_exp.trained, "test")

    print("\n--- Confusion Matrix ---")
    labels = best_exp.trained.split_data.class_labels
    # Print header
    print(f"{'True \\ Pred':<20}", end="")
    for label in labels:
        short = label.replace("DFG", "").replace("_", "")
        print(f"{short:>12}", end="")
    print()

    for true_label in labels:
        short_t = true_label.replace("DFG", "").replace("_", "")
        print(f"{short_t:<20}", end="")
        for pred_label in labels:
            count = next(
                (c.count for c in test_eval.confusion
                 if c.true_label == true_label and c.predicted_label == pred_label),
                0
            )
            print(f"{count:>12}", end="")
        print()

    print("\n--- Calibration Analysis ---")
    for b in test_eval.calibration_bins:
        if b.count > 0:
            print(
                f"  [{b.bin_lower:.1f}, {b.bin_upper:.1f}]: "
                f"conf={b.avg_confidence:.3f}, acc={b.avg_accuracy:.3f}, n={b.count}"
            )
    print(f"  ECE = {test_eval.expected_calibration_error:.3f}")

    print("\n--- Per-Mutation Diagnostics ---")
    for p in test_eval.predictions:
        true_label = next(
            (y for mid, y in zip(best_exp.trained.split_data.test_ids,
                                  best_exp.trained.split_data.test_y)
             if mid == p.mutation_id),
            "?"
        )
        status = "CORRECT" if p.predicted_label == true_label else "WRONG"
        print(f"  {p.mutation_id:<25} true={true_label:<16} "
              f"pred={p.predicted_label:<16} conf={p.confidence:.2f} [{status}]")

    # Ablation: what improved and what didn't
    print("\n--- Ablation Analysis ---")
    mutation_only_acc = next(
        (r["accuracy"] for r in comparison.rows if r["name"] == "mutation_only_centroid"),
        0.0,
    )
    for row in comparison.rows:
        delta = row["accuracy"] - mutation_only_acc  # type: ignore[operator]
        sign = "+" if delta > 0 else ""
        print(
            f"  {row['name']:<30} acc={row['accuracy']:.3f} "
            f"({sign}{delta:.3f} vs mutation-only baseline)"
        )

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    save_json(evaluation_to_dict(test_eval), ARTIFACT_DIR / "best_model_evaluation.json")
    save_json(
        {"rows": comparison.rows, "best_model": best_name,
         "best_accuracy": comparison.best_accuracy},
        ARTIFACT_DIR / "ablation_comparison.json",
    )

    # Per-mutation diagnostic table
    diagnostics = []
    for p in test_eval.predictions:
        true_label = next(
            (y for mid, y in zip(best_exp.trained.split_data.test_ids,
                                  best_exp.trained.split_data.test_y)
             if mid == p.mutation_id),
            "?",
        )
        diagnostics.append({
            "mutation_id": p.mutation_id,
            "true_label": true_label,
            "predicted_label": p.predicted_label,
            "confidence": p.confidence,
            "correct": p.predicted_label == true_label,
            "probabilities": p.probabilities,
        })
    save_json(diagnostics, ARTIFACT_DIR / "per_mutation_diagnostics.json")

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
