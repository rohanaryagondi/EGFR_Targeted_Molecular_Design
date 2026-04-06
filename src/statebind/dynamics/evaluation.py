"""Evaluation metrics for world model / transition prediction.

Computes:
- Transition prediction accuracy
- Log-likelihood comparison (vs uniform baseline)
- Perplexity
- Embedding geometry quality
- Transition matrix analysis
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from statebind.dynamics.embeddings import EmbeddingSpace
from statebind.dynamics.sequences import StateTransition
from statebind.dynamics.transitions import (
    MarkovTransitionModel,
    TransitionMatrix,
    TransitionPrediction,
    UniformBaseline,
)


@dataclass
class TransitionMetrics:
    """Evaluation metrics for transition prediction."""

    model_name: str
    accuracy: float = 0.0
    log_likelihood: float = 0.0
    perplexity: float = 0.0
    n_samples: int = 0


@dataclass
class EmbeddingMetrics:
    """Quality metrics for learned embeddings."""

    mean_distance: float = 0.0
    min_distance: float = 0.0
    max_distance: float = 0.0
    transition_correlation: float = 0.0
    # Does embedding distance correlate with transition probability?


@dataclass
class ModelComparison:
    """Comparison of multiple world model variants."""

    models: list[TransitionMetrics] = field(default_factory=list)
    best_model: str = ""
    best_log_likelihood: float = float("-inf")


def compute_transition_accuracy(
    predictions: list[TransitionPrediction],
    true_transitions: list[StateTransition],
) -> float:
    """Fraction of transitions where predicted_state matches actual next state."""
    if not predictions:
        return 0.0
    correct = sum(
        1 for p, t in zip(predictions, true_transitions)
        if p.predicted_state == t.to_state
    )
    return correct / len(predictions)


def compute_perplexity(log_likelihood: float) -> float:
    """Perplexity = exp(-avg_log_likelihood). Lower is better."""
    return math.exp(-log_likelihood)


def evaluate_transition_model(
    model_name: str,
    predictions: list[TransitionPrediction],
    true_transitions: list[StateTransition],
    log_likelihood: float,
) -> TransitionMetrics:
    """Evaluate a transition model."""
    accuracy = compute_transition_accuracy(predictions, true_transitions)
    perplexity = compute_perplexity(log_likelihood)

    return TransitionMetrics(
        model_name=model_name,
        accuracy=accuracy,
        log_likelihood=log_likelihood,
        perplexity=perplexity,
        n_samples=len(predictions),
    )


def evaluate_embedding_quality(
    embeddings: EmbeddingSpace,
    trans_matrix: TransitionMatrix,
) -> EmbeddingMetrics:
    """Evaluate how well embeddings reflect transition geometry.

    Checks whether embedding distance is negatively correlated with
    transition probability: frequent transitions → close in embedding space.
    """
    dists = embeddings.pairwise_distances()
    states = embeddings.states

    if not dists:
        return EmbeddingMetrics()

    dist_values = list(dists.values())
    mean_d = sum(dist_values) / len(dist_values)
    min_d = min(dist_values)
    max_d = max(dist_values)

    # Compute correlation between distance and transition probability
    # For each pair, get distance and symmetrized transition prob
    pairs_dist = []
    pairs_prob = []
    state_idx = {s: i for i, s in enumerate(states)}

    for (s1, s2), dist in dists.items():
        i, j = state_idx[s1], state_idx[s2]
        sym_prob = (trans_matrix.matrix[i][j] + trans_matrix.matrix[j][i]) / 2.0
        pairs_dist.append(dist)
        pairs_prob.append(sym_prob)

    # Pearson correlation
    n = len(pairs_dist)
    if n < 2:
        return EmbeddingMetrics(mean_distance=mean_d, min_distance=min_d, max_distance=max_d)

    mean_dist = sum(pairs_dist) / n
    mean_prob = sum(pairs_prob) / n

    cov = sum((d - mean_dist) * (p - mean_prob) for d, p in zip(pairs_dist, pairs_prob)) / n
    std_dist = math.sqrt(sum((d - mean_dist) ** 2 for d in pairs_dist) / n)
    std_prob = math.sqrt(sum((p - mean_prob) ** 2 for p in pairs_prob) / n)

    correlation = cov / (std_dist * std_prob + 1e-10)

    return EmbeddingMetrics(
        mean_distance=mean_d,
        min_distance=min_d,
        max_distance=max_d,
        transition_correlation=correlation,
    )


def compare_models(
    dataset_transitions: list[StateTransition],
    states: list[str],
    embeddings: EmbeddingSpace | None = None,
    smoothing: float = 1.0,
    seed: int = 42,
) -> ModelComparison:
    """Compare uniform, Markov, and learned models.

    Performs train/test split and evaluates all models.
    """
    import random as stdlib_random
    rng = stdlib_random.Random(seed)

    transitions = list(dataset_transitions)
    rng.shuffle(transitions)
    split = int(0.7 * len(transitions))
    train = transitions[:split]
    test = transitions[split:]

    results: list[TransitionMetrics] = []

    # 1. Uniform baseline
    uniform = UniformBaseline(states)
    uni_preds = [uniform.predict(t.from_state) for t in test]
    uni_ll = uniform.log_likelihood(test)
    results.append(evaluate_transition_model("uniform", uni_preds, test, uni_ll))

    # 2. Markov model
    markov = MarkovTransitionModel(states, smoothing=smoothing)
    markov.fit(train)
    mk_preds = [markov.predict(t.from_state) for t in test]
    mk_ll = markov.log_likelihood(test)
    results.append(evaluate_transition_model("markov", mk_preds, test, mk_ll))

    # 3. Learned model (if embeddings available)
    if embeddings is not None:
        from statebind.dynamics.world_model import LearnedWorldModel, WorldModelConfig

        config = WorldModelConfig(
            model_type="learned", random_seed=seed,
            mlp_hidden=8, mlp_epochs=150, mlp_lr=0.01,
        )
        learned = LearnedWorldModel(states, config)
        learned.fit(train, embeddings)
        lm_preds = [learned.predict(t.from_state, embeddings) for t in test]
        lm_ll = learned.log_likelihood(test, embeddings)
        results.append(evaluate_transition_model("learned_mlp", lm_preds, test, lm_ll))

    # Find best
    best = max(results, key=lambda m: m.log_likelihood)

    return ModelComparison(
        models=results,
        best_model=best.model_name,
        best_log_likelihood=best.log_likelihood,
    )


def metrics_to_dict(metrics: TransitionMetrics) -> dict:
    """Serialize transition metrics."""
    return {
        "model_name": metrics.model_name,
        "accuracy": round(metrics.accuracy, 4),
        "log_likelihood": round(metrics.log_likelihood, 4),
        "perplexity": round(metrics.perplexity, 4),
        "n_samples": metrics.n_samples,
    }


def embedding_metrics_to_dict(metrics: EmbeddingMetrics) -> dict:
    """Serialize embedding metrics."""
    return {
        "mean_distance": round(metrics.mean_distance, 4),
        "min_distance": round(metrics.min_distance, 4),
        "max_distance": round(metrics.max_distance, 4),
        "transition_correlation": round(metrics.transition_correlation, 4),
    }
