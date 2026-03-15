#!/usr/bin/env python3
"""Train the baseline transition models (uniform + Markov).

These are the interpretable baselines. The Markov model provides
the first useful transition probabilities.

Usage:
    python scripts/train_transition_baseline.py
"""

import json
from pathlib import Path

from statebind.dynamics.evaluation import (
    compute_transition_accuracy,
    evaluate_transition_model,
    metrics_to_dict,
)
from statebind.dynamics.sequences import build_transition_dataset
from statebind.dynamics.transitions import (
    MarkovTransitionModel,
    UniformBaseline,
    estimate_transition_matrix,
)

ARTIFACT_DIR = Path("artifacts/dynamics/baseline_v1")


def main() -> None:
    print("=" * 60)
    print("Transition Model: Baselines (Uniform + Markov)")
    print("=" * 60)

    dataset = build_transition_dataset()
    states = dataset.states

    # Split
    import random
    rng = random.Random(42)
    transitions = list(dataset.transitions)
    rng.shuffle(transitions)
    split = int(0.7 * len(transitions))
    train = transitions[:split]
    test = transitions[split:]

    print(f"\nTransitions: {len(transitions)} total, {len(train)} train, {len(test)} test")
    print(f"States: {states}")

    # 1. Uniform baseline
    uniform = UniformBaseline(states)
    uni_preds = [uniform.predict(t.from_state) for t in test]
    uni_ll = uniform.log_likelihood(test)
    uni_metrics = evaluate_transition_model("uniform", uni_preds, test, uni_ll)

    print(f"\n--- Uniform Baseline ---")
    print(f"  Log-likelihood: {uni_metrics.log_likelihood:.4f}")
    print(f"  Perplexity: {uni_metrics.perplexity:.4f}")
    print(f"  Accuracy: {uni_metrics.accuracy:.4f}")

    # 2. Markov model
    markov = MarkovTransitionModel(states, smoothing=1.0)
    markov.fit(train)
    mk_preds = [markov.predict(t.from_state) for t in test]
    mk_ll = markov.log_likelihood(test)
    mk_metrics = evaluate_transition_model("markov", mk_preds, test, mk_ll)

    print(f"\n--- Markov Model ---")
    print(f"  Log-likelihood: {mk_metrics.log_likelihood:.4f}")
    print(f"  Perplexity: {mk_metrics.perplexity:.4f}")
    print(f"  Accuracy: {mk_metrics.accuracy:.4f}")

    # Transition matrix
    matrix = markov.trans_matrix
    assert matrix is not None
    print(f"\n  Transition Matrix P(to | from):")
    header = "  " + f"{'From \\ To':<20}" + "".join(f"{s.replace('DFG',''):>12}" for s in states)
    print(header)
    for i, si in enumerate(states):
        row = f"  {si.replace('DFG',''):<20}" + "".join(f"{matrix.matrix[i][j]:>12.3f}" for j in range(len(states)))
        print(row)

    # Stationary distribution
    stationary = markov.get_stationary()
    print(f"\n  Stationary distribution:")
    for s, p in stationary.items():
        print(f"    {s}: {p:.3f}")

    # Improvement
    ll_improvement = mk_metrics.log_likelihood - uni_metrics.log_likelihood
    print(f"\n--- Comparison ---")
    print(f"  Markov vs Uniform: {ll_improvement:+.4f} log-likelihood")
    print(f"  Perplexity reduction: {uni_metrics.perplexity:.2f} → {mk_metrics.perplexity:.2f}")

    # Save
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    with open(ARTIFACT_DIR / "baseline_comparison.json", "w") as f:
        json.dump({
            "uniform": metrics_to_dict(uni_metrics),
            "markov": metrics_to_dict(mk_metrics),
            "ll_improvement": round(ll_improvement, 4),
        }, f, indent=2)

    with open(ARTIFACT_DIR / "transition_matrix.json", "w") as f:
        json.dump({
            "states": states,
            "matrix": matrix.matrix,
            "counts": matrix.counts,
        }, f, indent=2)

    with open(ARTIFACT_DIR / "stationary_distribution.json", "w") as f:
        json.dump({k: round(v, 4) for k, v in stationary.items()}, f, indent=2)

    print(f"\nArtifacts saved to {ARTIFACT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
