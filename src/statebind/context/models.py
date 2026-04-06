"""Model definitions for context-to-state prediction.

Three model tiers:
1. MutationOnlyBaseline — nearest-centroid classifier on mutation features
2. CombinedLogistic — logistic regression on mutation + pathway features
3. EmbeddingMLP — small feed-forward net with learned mutation embedding

All models share a common interface: fit(X, y) -> self, predict(X) -> predictions,
predict_proba(X) -> probability distributions.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class Prediction:
    """Single prediction with label and probability distribution."""

    mutation_id: str
    predicted_label: str
    probabilities: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0  # max probability


@dataclass
class ModelConfig:
    """Configuration for context-to-state models."""

    model_type: str = "mutation_only"  # mutation_only, combined_logistic, embedding_mlp
    feature_set: str = "mutation"  # mutation, pathway, all
    learning_rate: float = 0.01
    n_epochs: int = 100
    hidden_dim: int = 16
    dropout: float = 0.1
    l2_reg: float = 0.01
    random_seed: int = 42
    temperature: float = 1.0  # calibration temperature


def _softmax(logits: list[float], temperature: float = 1.0) -> list[float]:
    """Numerically stable softmax with temperature scaling."""
    scaled = [x / temperature for x in logits]
    max_val = max(scaled)
    exps = [math.exp(x - max_val) for x in scaled]
    total = sum(exps)
    return [e / total for e in exps]


def _dot(a: list[float], b: list[float]) -> float:
    """Dot product of two vectors."""
    return sum(x * y for x, y in zip(a, b))


def _euclidean(a: list[float], b: list[float]) -> float:
    """Euclidean distance between two vectors."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


class MutationOnlyBaseline:
    """Nearest-centroid classifier using mutation features.

    Computes class centroids from training data, then assigns test
    points to the nearest centroid. Probabilities are inverse-distance
    weighted across centroids.

    This is the simplest possible model — the one to beat.
    """

    def __init__(self, config: ModelConfig | None = None):
        self.config = config or ModelConfig(model_type="mutation_only")
        self.centroids: dict[str, list[float]] = {}
        self.class_labels: list[str] = []
        self.fitted = False

    def fit(
        self, X: list[list[float]], y: list[str]
    ) -> MutationOnlyBaseline:
        """Compute class centroids from training data."""
        # Group by label
        groups: dict[str, list[list[float]]] = {}
        for features, label in zip(X, y):
            groups.setdefault(label, []).append(features)

        self.class_labels = sorted(groups.keys())

        # Compute centroids
        for label, members in groups.items():
            n = len(members)
            dim = len(members[0])
            centroid = [0.0] * dim
            for vec in members:
                for i, v in enumerate(vec):
                    centroid[i] += v
            self.centroids[label] = [c / n for c in centroid]

        self.fitted = True
        return self

    def predict(self, X: list[list[float]]) -> list[str]:
        """Predict class labels for feature vectors."""
        return [p.predicted_label for p in self.predict_proba(X)]

    def predict_proba(self, X: list[list[float]], ids: list[str] | None = None) -> list[Prediction]:
        """Predict with probability distributions."""
        if not self.fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        if ids is None:
            ids = [f"sample_{i}" for i in range(len(X))]

        predictions = []
        for features, mid in zip(X, ids):
            # Compute distances to each centroid
            distances = {}
            for label, centroid in self.centroids.items():
                distances[label] = _euclidean(features, centroid)

            # Inverse-distance weighting for probabilities
            inv_dists = {
                label: 1.0 / (d + 1e-8) for label, d in distances.items()
            }
            total = sum(inv_dists.values())
            probs = {label: inv / total for label, inv in inv_dists.items()}

            best_label = min(distances, key=distances.get)  # type: ignore[arg-type]
            predictions.append(Prediction(
                mutation_id=mid,
                predicted_label=best_label,
                probabilities=probs,
                confidence=probs[best_label],
            ))

        return predictions


class CombinedLogistic:
    """Multinomial logistic regression on combined features.

    Implements gradient descent with L2 regularization.
    No external ML library dependencies.
    """

    def __init__(self, config: ModelConfig | None = None):
        self.config = config or ModelConfig(
            model_type="combined_logistic", feature_set="all"
        )
        self.weights: dict[str, list[float]] = {}  # class -> weight vector
        self.biases: dict[str, float] = {}
        self.class_labels: list[str] = []
        self.fitted = False

    def fit(
        self, X: list[list[float]], y: list[str]
    ) -> CombinedLogistic:
        """Train logistic regression with gradient descent."""
        rng = random.Random(self.config.random_seed)

        self.class_labels = sorted(set(y))
        len(self.class_labels)
        n_features = len(X[0]) if X else 0
        n_samples = len(X)

        if n_samples == 0:
            self.fitted = True
            return self

        # Initialize weights
        scale = 0.01
        for label in self.class_labels:
            self.weights[label] = [rng.gauss(0, scale) for _ in range(n_features)]
            self.biases[label] = 0.0

        # Label to index
        {label: i for i, label in enumerate(self.class_labels)}

        lr = self.config.learning_rate
        l2 = self.config.l2_reg

        for _epoch in range(self.config.n_epochs):
            # Forward pass: compute logits for all samples
            for xi, yi in zip(X, y):
                logits = [
                    _dot(self.weights[label], xi) + self.biases[label]
                    for label in self.class_labels
                ]
                probs = _softmax(logits, temperature=1.0)

                # Gradient: prob - target
                for c, label in enumerate(self.class_labels):
                    target = 1.0 if label == yi else 0.0
                    grad = probs[c] - target

                    # Update weights
                    for j in range(n_features):
                        self.weights[label][j] -= lr * (
                            grad * xi[j] + l2 * self.weights[label][j]
                        )
                    self.biases[label] -= lr * grad

        self.fitted = True
        return self

    def predict(self, X: list[list[float]]) -> list[str]:
        """Predict class labels."""
        return [p.predicted_label for p in self.predict_proba(X)]

    def predict_proba(self, X: list[list[float]], ids: list[str] | None = None) -> list[Prediction]:
        """Predict with calibrated probability distributions."""
        if not self.fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        if ids is None:
            ids = [f"sample_{i}" for i in range(len(X))]

        temp = self.config.temperature

        predictions = []
        for features, mid in zip(X, ids):
            logits = [
                _dot(self.weights[label], features) + self.biases[label]
                for label in self.class_labels
            ]
            probs = _softmax(logits, temperature=temp)
            prob_dict = dict(zip(self.class_labels, probs))

            best_idx = max(range(len(probs)), key=lambda i: probs[i])
            predictions.append(Prediction(
                mutation_id=mid,
                predicted_label=self.class_labels[best_idx],
                probabilities=prob_dict,
                confidence=probs[best_idx],
            ))

        return predictions


class EmbeddingMLP:
    """Small feed-forward network with a learned mutation embedding layer.

    Architecture:
        Input(n_features) -> Linear(hidden) -> ReLU -> Linear(n_classes) -> Softmax

    The "embedding" is the hidden layer representation, which learns to
    map diverse mutation features into a compact space that separates states.
    """

    def __init__(self, config: ModelConfig | None = None):
        self.config = config or ModelConfig(
            model_type="embedding_mlp", feature_set="all",
            hidden_dim=16, n_epochs=200, learning_rate=0.005,
        )
        self.W1: list[list[float]] = []  # hidden_dim x n_features
        self.b1: list[float] = []
        self.W2: list[list[float]] = []  # n_classes x hidden_dim
        self.b2: list[float] = []
        self.class_labels: list[str] = []
        self.fitted = False

    def _relu(self, x: list[float]) -> list[float]:
        return [max(0.0, v) for v in x]

    def _forward(self, x: list[float]) -> tuple[list[float], list[float]]:
        """Forward pass. Returns (hidden_activations, logits)."""
        # Hidden layer
        h = [_dot(self.W1[i], x) + self.b1[i] for i in range(len(self.b1))]
        h = self._relu(h)

        # Apply dropout during training (zeroing out units)
        # Not applied during inference

        # Output layer
        logits = [_dot(self.W2[i], h) + self.b2[i] for i in range(len(self.b2))]
        return h, logits

    def fit(
        self, X: list[list[float]], y: list[str]
    ) -> EmbeddingMLP:
        """Train MLP with SGD."""
        rng = random.Random(self.config.random_seed)

        self.class_labels = sorted(set(y))
        n_classes = len(self.class_labels)
        n_features = len(X[0]) if X else 0
        hidden = self.config.hidden_dim

        if not X:
            self.fitted = True
            return self

        # Xavier initialization
        scale1 = math.sqrt(2.0 / (n_features + hidden))
        scale2 = math.sqrt(2.0 / (hidden + n_classes))

        self.W1 = [[rng.gauss(0, scale1) for _ in range(n_features)] for _ in range(hidden)]
        self.b1 = [0.0] * hidden
        self.W2 = [[rng.gauss(0, scale2) for _ in range(hidden)] for _ in range(n_classes)]
        self.b2 = [0.0] * n_classes

        lr = self.config.learning_rate
        l2 = self.config.l2_reg

        for _epoch in range(self.config.n_epochs):
            # Shuffle training order
            indices = list(range(len(X)))
            rng.shuffle(indices)

            for idx in indices:
                xi = X[idx]
                yi = y[idx]

                # Forward
                h_pre = [_dot(self.W1[i], xi) + self.b1[i] for i in range(hidden)]
                h = [max(0.0, v) for v in h_pre]
                logits = [_dot(self.W2[c], h) + self.b2[c] for c in range(n_classes)]
                probs = _softmax(logits)

                # Backward: output layer
                d_logits = list(probs)
                target_idx = self.class_labels.index(yi)
                d_logits[target_idx] -= 1.0

                # Gradients for W2, b2
                d_h = [0.0] * hidden
                for c in range(n_classes):
                    for j in range(hidden):
                        self.W2[c][j] -= lr * (d_logits[c] * h[j] + l2 * self.W2[c][j])
                        d_h[j] += d_logits[c] * self.W2[c][j]
                    self.b2[c] -= lr * d_logits[c]

                # ReLU backward
                d_h_pre = [d_h[j] if h_pre[j] > 0 else 0.0 for j in range(hidden)]

                # Gradients for W1, b1
                for j in range(hidden):
                    for k in range(n_features):
                        self.W1[j][k] -= lr * (d_h_pre[j] * xi[k] + l2 * self.W1[j][k])
                    self.b1[j] -= lr * d_h_pre[j]

        self.fitted = True
        return self

    def predict(self, X: list[list[float]]) -> list[str]:
        """Predict class labels."""
        return [p.predicted_label for p in self.predict_proba(X)]

    def predict_proba(self, X: list[list[float]], ids: list[str] | None = None) -> list[Prediction]:
        """Predict with probability distributions."""
        if not self.fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        if ids is None:
            ids = [f"sample_{i}" for i in range(len(X))]

        temp = self.config.temperature

        predictions = []
        for features, mid in zip(X, ids):
            _h, logits = self._forward(features)
            probs = _softmax(logits, temperature=temp)
            prob_dict = dict(zip(self.class_labels, probs))

            best_idx = max(range(len(probs)), key=lambda i: probs[i])
            predictions.append(Prediction(
                mutation_id=mid,
                predicted_label=self.class_labels[best_idx],
                probabilities=prob_dict,
                confidence=probs[best_idx],
            ))

        return predictions

    def get_embeddings(self, X: list[list[float]]) -> list[list[float]]:
        """Extract hidden layer embeddings for visualization."""
        embeddings = []
        for features in X:
            h, _logits = self._forward(features)
            embeddings.append(h)
        return embeddings


def create_model(config: ModelConfig) -> MutationOnlyBaseline | CombinedLogistic | EmbeddingMLP:
    """Factory function to create a model from config."""
    if config.model_type == "mutation_only":
        return MutationOnlyBaseline(config)
    elif config.model_type == "combined_logistic":
        return CombinedLogistic(config)
    elif config.model_type == "embedding_mlp":
        return EmbeddingMLP(config)
    else:
        raise ValueError(f"Unknown model_type: {config.model_type}")
