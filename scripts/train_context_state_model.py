#!/usr/bin/env python3
"""Train all context-to-state models and run ablation suite.

Trains 6 model variants:
1. Mutation-only + nearest centroid
2. Pathway-only + nearest centroid
3. Combined + nearest centroid
4. Mutation-only + logistic regression
5. Combined + logistic regression
6. Combined + embedding MLP

Saves all predictions, evaluations, and ablation comparison.

Usage:
    python scripts/train_context_state_model.py
"""

import json
from pathlib import Path

from statebind.context.evaluation import (
    compare_ablations,
    evaluate_model,
    evaluation_to_dict,
)
from statebind.context.training import (
    load_data,
    run_ablation_suite,
    save_model_config,
    save_predictions,
)
from statebind.utils.io import save_json

ARTIFACT_DIR = Path("artifacts/context/ablation_v1")


def main() -> None:
    print("=" * 60)
    print("Context-to-State: Full Ablation Suite")
    print("=" * 60)

    # Load data
    context = load_data(split_seed=42)
    print(f"\nLoaded {len(context.mutations)} mutations")

    # Run ablation suite
    print("\nTraining 6 model variants...")
    experiments = run_ablation_suite(context)

    # Evaluate each
    all_evals = {}
    for exp in experiments:
        if exp.trained is None:
            continue

        print(f"\n--- {exp.name} ---")
        print(f"  Features: {exp.feature_set}, Model: {exp.model_type}")

        for split in ["train", "test"]:
            result = evaluate_model(exp.trained, split)
            all_evals[f"{exp.name}_{split}"] = result
            if split == "test":
                print(f"  Test accuracy: {result.accuracy:.3f}")
                print(f"  Test macro F1: {result.macro_f1:.3f}")
                print(f"  Test CE: {result.cross_entropy:.3f}")
                print(f"  Test ECE: {result.expected_calibration_error:.3f}")

    # Compare
    comparison = compare_ablations(experiments, eval_split="test")

    print("\n" + "=" * 60)
    print("ABLATION COMPARISON (Test Set)")
    print("=" * 60)
    print(f"{'Model':<30} {'Features':<12} {'Acc':>6} {'F1':>6} {'CE':>6} {'ECE':>6}")
    print("-" * 72)
    for row in comparison.rows:
        print(
            f"{row['name']:<30} {row['feature_set']:<12} "
            f"{row['accuracy']:>6.3f} {row['macro_f1']:>6.3f} "
            f"{row['cross_entropy']:>6.3f} {row['ece']:>6.3f}"
        )
    print("-" * 72)
    print(f"Best: {comparison.best_model} (accuracy={comparison.best_accuracy:.3f})")

    # Save artifacts
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    for exp in experiments:
        if exp.trained is None:
            continue
        exp_dir = ARTIFACT_DIR / exp.name
        exp_dir.mkdir(parents=True, exist_ok=True)

        save_model_config(exp.config, exp_dir / "config.json")
        save_predictions(exp.trained.test_predictions, exp_dir / "test_predictions.json")

        test_eval = evaluate_model(exp.trained, "test")
        save_json(evaluation_to_dict(test_eval), exp_dir / "test_evaluation.json")

        train_eval = evaluate_model(exp.trained, "train")
        save_json(evaluation_to_dict(train_eval), exp_dir / "train_evaluation.json")

    # Save comparison
    save_json(
        {"rows": comparison.rows, "best_model": comparison.best_model,
         "best_accuracy": comparison.best_accuracy},
        ARTIFACT_DIR / "ablation_comparison.json",
    )

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
