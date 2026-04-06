"""Unified world model combining transition and embedding components.

The world model provides a single interface for downstream consumers:
1. "Given current state X, what states might come next?"
2. "How far is state A from state B in transition space?"
3. "What is the equilibrium distribution over states?"
4. "Given a mutation context, what state trajectory is expected?"

Three model tiers:
- UniformBaseline: random walk (floor)
- MarkovModel: first-order transition matrix (interpretable)
- LearnedWorldModel: MLP on state embeddings (richer dynamics)
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from statebind.dynamics.embeddings import EmbeddingSpace, learn_embeddings
from statebind.dynamics.sequences import (
    StateTransition,
    TransitionDataset,
    build_transition_dataset,
)
from statebind.dynamics.transitions import (
    MarkovTransitionModel,
    TransitionMatrix,
    TransitionPrediction,
    UniformBaseline,
    estimate_transition_matrix,
)


@dataclass
class WorldModelConfig:
    """Configuration for the world model."""

    model_type: str = "markov"       # uniform, markov, learned
    embedding_dim: int = 4
    embedding_epochs: int = 200
    embedding_lr: float = 0.05
    mlp_hidden: int = 8
    mlp_epochs: int = 150
    mlp_lr: float = 0.01
    smoothing: float = 1.0
    random_seed: int = 42


@dataclass
class WorldModelOutput:
    """Complete output from the world model pipeline."""

    config: WorldModelConfig
    transition_dataset: TransitionDataset
    transition_matrix: TransitionMatrix
    embeddings: EmbeddingSpace | None
    stationary_distribution: dict[str, float]
    model_name: str = ""
    test_predictions: list[TransitionPrediction] = field(default_factory=list)
    train_log_likelihood: float = 0.0
    test_log_likelihood: float = 0.0


def _softmax(logits: list[float], temp: float = 1.0) -> list[float]:
    scaled = [x / temp for x in logits]
    mx = max(scaled)
    exps = [math.exp(x - mx) for x in scaled]
    total = sum(exps)
    return [e / total for e in exps]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class LearnedWorldModel:
    """MLP-based world model operating on state embeddings.

    Architecture:
        Embedding(state) -> Linear(hidden) -> ReLU -> Linear(n_states) -> Softmax

    The model learns to predict next-state from the embedding of the
    current state. This captures nonlinear transition patterns that
    the Markov model cannot (e.g., context-dependent transitions).
    """

    def __init__(self, states: list[str], config: WorldModelConfig):
        self.states = states
        self.config = config
        self.n_states = len(states)
        self.state_idx = {s: i for i, s in enumerate(states)}

        # Weights (initialized in fit)
        self.W1: list[list[float]] = []
        self.b1: list[float] = []
        self.W2: list[list[float]] = []
        self.b2: list[float] = []
        self.fitted = False

    def fit(
        self,
        transitions: list[StateTransition],
        embeddings: EmbeddingSpace,
    ) -> LearnedWorldModel:
        """Train MLP on transition data using state embeddings as input."""
        rng = random.Random(self.config.random_seed)
        hidden = self.config.mlp_hidden
        dim = embeddings.dim

        # Xavier init
        s1 = math.sqrt(2.0 / (dim + hidden))
        s2 = math.sqrt(2.0 / (hidden + self.n_states))

        self.W1 = [[rng.gauss(0, s1) for _ in range(dim)] for _ in range(hidden)]
        self.b1 = [0.0] * hidden
        self.W2 = [[rng.gauss(0, s2) for _ in range(hidden)] for _ in range(self.n_states)]
        self.b2 = [0.0] * self.n_states

        lr = self.config.mlp_lr

        # Build training pairs: (from_embedding, to_state_idx)
        pairs = []
        for t in transitions:
            if t.from_state in self.state_idx and t.to_state in self.state_idx:
                from_emb = embeddings.get_vector(t.from_state)
                to_idx = self.state_idx[t.to_state]
                pairs.append((from_emb, to_idx))

        for _epoch in range(self.config.mlp_epochs):
            rng.shuffle(pairs)
            for x, target in pairs:
                # Forward
                h = [max(0.0, _dot(self.W1[j], x) + self.b1[j]) for j in range(hidden)]
                logits = [_dot(self.W2[c], h) + self.b2[c] for c in range(self.n_states)]
                probs = _softmax(logits)

                # Backward
                d_logits = list(probs)
                d_logits[target] -= 1.0

                d_h = [0.0] * hidden
                for c in range(self.n_states):
                    for j in range(hidden):
                        self.W2[c][j] -= lr * d_logits[c] * h[j]
                        d_h[j] += d_logits[c] * self.W2[c][j]
                    self.b2[c] -= lr * d_logits[c]

                h_pre = [_dot(self.W1[j], x) + self.b1[j] for j in range(hidden)]
                for j in range(hidden):
                    if h_pre[j] > 0:
                        for k in range(len(x)):
                            self.W1[j][k] -= lr * d_h[j] * x[k]
                        self.b1[j] -= lr * d_h[j]

        self.fitted = True
        return self

    def predict(self, from_state: str, embeddings: EmbeddingSpace) -> TransitionPrediction:
        """Predict next state from embedding."""
        if not self.fitted:
            raise RuntimeError("Model not fitted.")

        x = embeddings.get_vector(from_state)
        hidden = len(self.b1)

        h = [max(0.0, _dot(self.W1[j], x) + self.b1[j]) for j in range(hidden)]
        logits = [_dot(self.W2[c], h) + self.b2[c] for c in range(self.n_states)]
        probs = _softmax(logits)

        prob_dict = dict(zip(self.states, probs))
        best_idx = max(range(self.n_states), key=lambda i: probs[i])

        return TransitionPrediction(
            from_state=from_state,
            predicted_state=self.states[best_idx],
            probabilities=prob_dict,
            confidence=probs[best_idx],
            model_name="learned_mlp",
        )

    def log_likelihood(
        self, transitions: list[StateTransition], embeddings: EmbeddingSpace
    ) -> float:
        """Compute average log-likelihood."""
        if not self.fitted:
            raise RuntimeError("Model not fitted.")
        if not transitions:
            return 0.0

        total = 0.0
        for t in transitions:
            pred = self.predict(t.from_state, embeddings)
            prob = pred.probabilities.get(t.to_state, 1e-15)
            total += math.log(max(prob, 1e-15))
        return total / len(transitions)


def build_world_model(config: WorldModelConfig | None = None) -> WorldModelOutput:
    """Build the complete world model pipeline.

    Steps:
    1. Construct transition dataset from literature
    2. Split into train/test transitions
    3. Estimate transition matrix (Markov model)
    4. Learn state embeddings
    5. Train learned model (if configured)
    6. Evaluate all models

    Returns:
        WorldModelOutput with all components.
    """
    if config is None:
        config = WorldModelConfig()

    rng = random.Random(config.random_seed)

    # 1. Build transition dataset
    dataset = build_transition_dataset()

    # 2. Split transitions: ~70% train, 30% test
    transitions = list(dataset.transitions)
    rng.shuffle(transitions)
    split_idx = int(0.7 * len(transitions))
    train_trans = transitions[:split_idx]
    test_trans = transitions[split_idx:]

    # 3. Estimate transition matrix from ALL data (for embeddings)
    full_matrix = estimate_transition_matrix(
        dataset.transitions, dataset.states, smoothing=config.smoothing
    )

    # Also estimate from train only (for evaluation)
    estimate_transition_matrix(
        train_trans, dataset.states, smoothing=config.smoothing
    )

    # 4. Learn embeddings
    embeddings = learn_embeddings(
        full_matrix,
        dim=config.embedding_dim,
        n_epochs=config.embedding_epochs,
        learning_rate=config.embedding_lr,
        seed=config.random_seed,
    )

    # 5. Train/evaluate models
    uniform = UniformBaseline(dataset.states)
    markov = MarkovTransitionModel(dataset.states, smoothing=config.smoothing)
    markov.fit(train_trans)

    # Evaluate on test transitions
    test_preds: list[TransitionPrediction] = []
    train_ll = 0.0
    test_ll = 0.0
    model_name = ""

    if config.model_type == "uniform":
        model_name = "uniform_baseline"
        test_preds = [uniform.predict(t.from_state) for t in test_trans]
        train_ll = uniform.log_likelihood(train_trans)
        test_ll = uniform.log_likelihood(test_trans)

    elif config.model_type == "markov":
        model_name = "markov"
        test_preds = [markov.predict(t.from_state) for t in test_trans]
        train_ll = markov.log_likelihood(train_trans)
        test_ll = markov.log_likelihood(test_trans)

    elif config.model_type == "learned":
        model_name = "learned_mlp"
        learned = LearnedWorldModel(dataset.states, config)
        learned.fit(train_trans, embeddings)
        test_preds = [learned.predict(t.from_state, embeddings) for t in test_trans]
        train_ll = learned.log_likelihood(train_trans, embeddings)
        test_ll = learned.log_likelihood(test_trans, embeddings)

    # Stationary distribution
    stationary = full_matrix.stationary_distribution()

    return WorldModelOutput(
        config=config,
        transition_dataset=dataset,
        transition_matrix=full_matrix,
        embeddings=embeddings,
        stationary_distribution=stationary,
        model_name=model_name,
        test_predictions=test_preds,
        train_log_likelihood=train_ll,
        test_log_likelihood=test_ll,
    )


def save_world_model(output: WorldModelOutput, artifact_dir: Path) -> list[Path]:
    """Save all world model artifacts to disk.

    Returns list of files written.
    """
    artifact_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []

    # Transition matrix
    tm_path = artifact_dir / "transition_matrix.json"
    with open(tm_path, "w") as f:
        json.dump({
            "states": output.transition_matrix.states,
            "matrix": output.transition_matrix.matrix,
            "counts": output.transition_matrix.counts,
        }, f, indent=2)
    files.append(tm_path)

    # Sequences
    seq_path = artifact_dir / "sequences.json"
    with open(seq_path, "w") as f:
        json.dump([
            {
                "id": s.sequence_id,
                "states": s.states,
                "description": s.description,
                "provenance": s.provenance,
                "context": s.context,
                "is_synthetic": s.is_synthetic,
            }
            for s in output.transition_dataset.sequences
        ], f, indent=2)
    files.append(seq_path)

    # Transition counts summary
    trans_path = artifact_dir / "transition_summary.json"
    states = output.transition_matrix.states
    summary: list[dict[str, object]] = []
    for i, si in enumerate(states):
        for j, sj in enumerate(states):
            count = output.transition_matrix.counts[i][j]
            prob = output.transition_matrix.matrix[i][j]
            summary.append({
                "from": si, "to": sj,
                "count": count, "probability": round(prob, 4),
            })
    with open(trans_path, "w") as f:
        json.dump(summary, f, indent=2)
    files.append(trans_path)

    # Embeddings
    if output.embeddings:
        emb_path = artifact_dir / "state_embeddings.json"
        with open(emb_path, "w") as f:
            json.dump({
                "dim": output.embeddings.dim,
                "embeddings": {
                    s: emb.vector
                    for s, emb in output.embeddings.embeddings.items()
                },
                "pairwise_distances": {
                    f"{k[0]}|{k[1]}": round(v, 4)
                    for k, v in output.embeddings.pairwise_distances().items()
                },
                "training_loss_final": (
                    output.embeddings.training_loss[-1]
                    if output.embeddings.training_loss else None
                ),
            }, f, indent=2)
        files.append(emb_path)

    # Stationary distribution
    stat_path = artifact_dir / "stationary_distribution.json"
    with open(stat_path, "w") as f:
        json.dump(
            {k: round(v, 4) for k, v in output.stationary_distribution.items()},
            f, indent=2,
        )
    files.append(stat_path)

    # Evaluation metrics
    eval_path = artifact_dir / "evaluation.json"
    with open(eval_path, "w") as f:
        json.dump({
            "model_name": output.model_name,
            "train_log_likelihood": round(output.train_log_likelihood, 4),
            "test_log_likelihood": round(output.test_log_likelihood, 4),
            "n_train_transitions": int(0.7 * output.transition_dataset.n_transitions),
            "n_test_transitions": (
                output.transition_dataset.n_transitions
                - int(0.7 * output.transition_dataset.n_transitions)
            ),
            "n_sequences": output.transition_dataset.n_sequences,
            "n_states": len(output.transition_matrix.states),
        }, f, indent=2)
    files.append(eval_path)

    # Config
    cfg_path = artifact_dir / "config.json"
    with open(cfg_path, "w") as f:
        json.dump({
            "model_type": output.config.model_type,
            "embedding_dim": output.config.embedding_dim,
            "embedding_epochs": output.config.embedding_epochs,
            "smoothing": output.config.smoothing,
            "random_seed": output.config.random_seed,
        }, f, indent=2)
    files.append(cfg_path)

    return files
