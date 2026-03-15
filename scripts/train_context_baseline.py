#!/usr/bin/env python3
"""Train the mutation-only baseline for context-to-state prediction.

This is the simplest model: nearest-centroid on mutation features only.
It establishes the floor that richer models must beat.

Usage:
    python scripts/train_context_baseline.py
"""

from pathlib import Path

from statebind.context.evaluation import evaluate_model, evaluation_to_dict
from statebind.context.models import ModelConfig
from statebind.context.training import (
    load_data,
    save_model_config,
    save_predictions,
    train_model,
)
from statebind.utils.io import save_json

ARTIFACT_DIR = Path("artifacts/context/baseline_v1")


def main() -> None:
    print("=" * 60)
    print("Context-to-State: Mutation-Only Baseline")
    print("=" * 60)

    # Load data
    context = load_data(split_seed=42)
    print(f"\nLoaded {len(context.mutations)} mutations")

    # Configure baseline
    config = ModelConfig(
        model_type="mutation_only",
        feature_set="mutation",
        random_seed=42,
    )

    # Train
    print("\nTraining nearest-centroid on mutation features...")
    trained = train_model(context, config)

    sd = trained.split_data
    print(f"  Train: {len(sd.train_X)} samples")
    print(f"  Val:   {len(sd.val_X)} samples")
    print(f"  Test:  {len(sd.test_X)} samples")
    print(f"  Features: {sd.n_features}")
    print(f"  Classes: {sd.class_labels}")

    # Evaluate
    print("\n--- Train Evaluation ---")
    train_eval = evaluate_model(trained, "train")
    print(f"  Accuracy: {train_eval.accuracy:.3f}")
    print(f"  Macro F1: {train_eval.macro_f1:.3f}")

    if sd.val_X:
        print("\n--- Val Evaluation ---")
        val_eval = evaluate_model(trained, "val")
        print(f"  Accuracy: {val_eval.accuracy:.3f}")
        print(f"  Macro F1: {val_eval.macro_f1:.3f}")

    print("\n--- Test Evaluation ---")
    test_eval = evaluate_model(trained, "test")
    print(f"  Accuracy: {test_eval.accuracy:.3f}")
    print(f"  Macro F1: {test_eval.macro_f1:.3f}")
    print(f"  Cross-entropy: {test_eval.cross_entropy:.3f}")
    print(f"  ECE: {test_eval.expected_calibration_error:.3f}")

    print("\n  Per-class:")
    for c in test_eval.per_class:
        if c.support > 0:
            print(f"    {c.label}: P={c.precision:.2f} R={c.recall:.2f} F1={c.f1:.2f} (n={c.support})")

    print("\n  Predictions:")
    for p in test_eval.predictions:
        top_prob = max(p.probabilities.values())
        print(f"    {p.mutation_id}: {p.predicted_label} (conf={p.confidence:.2f})")

    # Save artifacts
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    save_model_config(config, ARTIFACT_DIR / "config.json")
    save_predictions(trained.test_predictions, ARTIFACT_DIR / "test_predictions.json")
    save_json(evaluation_to_dict(test_eval), ARTIFACT_DIR / "test_evaluation.json")
    save_json(evaluation_to_dict(train_eval), ARTIFACT_DIR / "train_evaluation.json")

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
