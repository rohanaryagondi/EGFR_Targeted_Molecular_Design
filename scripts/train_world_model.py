#!/usr/bin/env python3
"""Train the full world model (Markov + embeddings + learned MLP).

Builds all three model tiers, learns state embeddings, and compares.

Usage:
    python scripts/train_world_model.py
"""

import json
from pathlib import Path

from statebind.dynamics.evaluation import (
    compare_models,
    evaluate_embedding_quality,
    embedding_metrics_to_dict,
    metrics_to_dict,
)
from statebind.dynamics.world_model import (
    WorldModelConfig,
    build_world_model,
    save_world_model,
)

ARTIFACT_DIR = Path("artifacts/dynamics/world_model_v1")


def main() -> None:
    print("=" * 60)
    print("Training World Model: Full Pipeline")
    print("=" * 60)

    # Build the learned world model
    config = WorldModelConfig(
        model_type="learned",
        embedding_dim=4,
        embedding_epochs=200,
        embedding_lr=0.05,
        mlp_hidden=8,
        mlp_epochs=150,
        mlp_lr=0.01,
        smoothing=1.0,
        random_seed=42,
    )

    output = build_world_model(config)

    print(f"\nTransition dataset: {output.transition_dataset.n_sequences} sequences, "
          f"{output.transition_dataset.n_transitions} transitions")
    print(f"States: {output.transition_matrix.states}")

    # Transition matrix
    tm = output.transition_matrix
    print(f"\n--- Transition Matrix ---")
    header = f"  {'From \\ To':<18}" + "".join(f"{s.replace('DFG',''):>14}" for s in tm.states)
    print(header)
    for i, si in enumerate(tm.states):
        row = f"  {si.replace('DFG',''):<18}" + "".join(f"{tm.matrix[i][j]:>14.3f}" for j in range(len(tm.states)))
        print(row)

    # Stationary distribution
    print(f"\n--- Stationary Distribution ---")
    for s, p in output.stationary_distribution.items():
        bar = "█" * int(p * 40)
        print(f"  {s:<18} {p:.3f} {bar}")

    # Embeddings
    if output.embeddings:
        print(f"\n--- Learned Embeddings (dim={output.embeddings.dim}) ---")
        for s in output.embeddings.states:
            vec = output.embeddings.get_vector(s)
            vec_str = ", ".join(f"{v:+.3f}" for v in vec)
            print(f"  {s:<18} [{vec_str}]")

        dists = output.embeddings.pairwise_distances()
        print(f"\n  Pairwise embedding distances:")
        for (s1, s2), d in sorted(dists.items(), key=lambda x: x[1]):
            print(f"    {s1} ↔ {s2}: {d:.3f}")

        # Embedding quality
        emb_metrics = evaluate_embedding_quality(output.embeddings, tm)
        print(f"\n  Embedding quality:")
        print(f"    Mean distance: {emb_metrics.mean_distance:.3f}")
        print(f"    Distance-transition correlation: {emb_metrics.transition_correlation:+.3f}")
        print(f"    (Negative = good: closer embeddings ↔ higher transition probability)")

    # Training loss
    if output.embeddings and output.embeddings.training_loss:
        losses = output.embeddings.training_loss
        print(f"\n  Embedding training: loss {losses[0]:.4f} → {losses[-1]:.4f} "
              f"({len(losses)} epochs)")

    # Model comparison
    print(f"\n--- Model Comparison ---")
    comparison = compare_models(
        output.transition_dataset.transitions,
        output.transition_dataset.states,
        embeddings=output.embeddings,
        smoothing=1.0,
        seed=42,
    )

    print(f"  {'Model':<18} {'LL':>8} {'PPL':>8} {'Acc':>8}")
    print(f"  {'-'*42}")
    for m in comparison.models:
        print(f"  {m.model_name:<18} {m.log_likelihood:>8.4f} {m.perplexity:>8.2f} {m.accuracy:>8.3f}")
    print(f"\n  Best: {comparison.best_model}")

    # Save artifacts
    files = save_world_model(output, ARTIFACT_DIR)

    # Save comparison
    with open(ARTIFACT_DIR / "model_comparison.json", "w") as f:
        json.dump({
            "models": [metrics_to_dict(m) for m in comparison.models],
            "best_model": comparison.best_model,
            "best_log_likelihood": round(comparison.best_log_likelihood, 4),
        }, f, indent=2)

    if output.embeddings:
        emb_metrics = evaluate_embedding_quality(output.embeddings, tm)
        with open(ARTIFACT_DIR / "embedding_quality.json", "w") as f:
            json.dump(embedding_metrics_to_dict(emb_metrics), f, indent=2)

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/ ({len(files) + 2} files)")
    print("Done.")


if __name__ == "__main__":
    main()
