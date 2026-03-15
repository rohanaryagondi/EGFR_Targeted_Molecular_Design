#!/usr/bin/env python3
"""Evaluate world model with detailed diagnostics.

Runs all models, compares predictions, analyzes transition matrix
structure, and checks embedding geometry.

Usage:
    python scripts/evaluate_world_model.py
"""

import json
from pathlib import Path

from statebind.dynamics.evaluation import (
    compare_models,
    evaluate_embedding_quality,
    evaluate_transition_model,
    embedding_metrics_to_dict,
    metrics_to_dict,
)
from statebind.dynamics.world_model import WorldModelConfig, build_world_model
from statebind.utils.io import save_json

ARTIFACT_DIR = Path("artifacts/dynamics/evaluation_v1")


def main() -> None:
    print("=" * 60)
    print("World Model: Detailed Evaluation")
    print("=" * 60)

    # Build all models
    configs = [
        ("uniform", WorldModelConfig(model_type="uniform")),
        ("markov", WorldModelConfig(model_type="markov")),
        ("learned", WorldModelConfig(
            model_type="learned", embedding_dim=4,
            mlp_hidden=8, mlp_epochs=150,
        )),
    ]

    results = {}
    for name, cfg in configs:
        output = build_world_model(cfg)
        results[name] = output

    # Compare
    print("\n--- Model Comparison ---")
    print(f"  {'Model':<18} {'Train LL':>10} {'Test LL':>10}")
    print(f"  {'-'*38}")
    for name, out in results.items():
        print(f"  {name:<18} {out.train_log_likelihood:>10.4f} {out.test_log_likelihood:>10.4f}")

    # Detailed Markov analysis
    markov_out = results["markov"]
    tm = markov_out.transition_matrix

    print(f"\n--- Transition Matrix Analysis ---")

    # Most and least likely transitions
    transitions_ranked = []
    for i, si in enumerate(tm.states):
        for j, sj in enumerate(tm.states):
            transitions_ranked.append((si, sj, tm.matrix[i][j], tm.counts[i][j]))

    transitions_ranked.sort(key=lambda x: -x[2])

    print(f"\n  Most likely transitions:")
    for si, sj, prob, count in transitions_ranked[:5]:
        print(f"    {si} → {sj}: P={prob:.3f} (n={count})")

    print(f"\n  Least likely transitions:")
    for si, sj, prob, count in transitions_ranked[-3:]:
        print(f"    {si} → {sj}: P={prob:.3f} (n={count})")

    # Self-transition rates
    print(f"\n  Self-transition rates (state stability):")
    for i, s in enumerate(tm.states):
        print(f"    {s}: P(stay) = {tm.matrix[i][i]:.3f}")

    # Embedding analysis
    learned_out = results["learned"]
    if learned_out.embeddings:
        emb = learned_out.embeddings
        print(f"\n--- Embedding Analysis ---")

        # Nearest neighbors in embedding space
        print(f"\n  Nearest state in embedding space:")
        for s in emb.states:
            nearest = emb.nearest_state(s)
            dists = emb.pairwise_distances()
            d = next(v for k, v in dists.items() if s in k and nearest in k)
            print(f"    {s} → {nearest} (d={d:.3f})")

        # Quality
        emb_q = evaluate_embedding_quality(emb, tm)
        print(f"\n  Transition-distance correlation: {emb_q.transition_correlation:+.3f}")
        if emb_q.transition_correlation < -0.3:
            print(f"    → Good: closer embeddings = higher transition probability")
        elif emb_q.transition_correlation > 0.3:
            print(f"    → Unexpected: closer embeddings ≠ higher transition probability")
        else:
            print(f"    → Weak correlation: embeddings partially capture transition geometry")

    # Stationary distribution comparison
    print(f"\n--- Stationary Distribution ---")
    stat = markov_out.stationary_distribution
    print(f"  Equilibrium state occupancy (Markov model):")
    for s, p in sorted(stat.items(), key=lambda x: -x[1]):
        bar = "█" * int(p * 50)
        print(f"    {s:<18} {p:.3f} {bar}")

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    all_metrics = {}
    for name, out in results.items():
        all_metrics[name] = {
            "train_ll": round(out.train_log_likelihood, 4),
            "test_ll": round(out.test_log_likelihood, 4),
            "model_name": out.model_name,
        }
    save_json(all_metrics, ARTIFACT_DIR / "model_metrics.json")

    save_json(
        [
            {"from": si, "to": sj, "probability": round(prob, 4), "count": count}
            for si, sj, prob, count in transitions_ranked[:10]
        ],
        ARTIFACT_DIR / "top_transitions.json",
    )

    # Full evaluation
    eval_data = {
        "models": all_metrics,
        "stationary": {k: round(v, 4) for k, v in stat.items()},
        "self_transitions": {
            s: round(tm.matrix[i][i], 4) for i, s in enumerate(tm.states)
        },
    }
    if learned_out.embeddings:
        emb_q = evaluate_embedding_quality(learned_out.embeddings, tm)
        eval_data["embedding_quality"] = embedding_metrics_to_dict(emb_q)

    save_json(eval_data, ARTIFACT_DIR / "full_evaluation.json")

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
