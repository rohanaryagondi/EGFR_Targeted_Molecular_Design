"""Latent state embedding learning.

Learns compact vector representations of conformational states that
respect transition geometry: states connected by frequent transitions
should be closer in embedding space than states with rare transitions.

Uses the structural feature centroids from the atlas as initialization,
then adjusts based on transition co-occurrence.

Implements a contrastive-style objective:
- Pull together states that frequently transition to each other
- Push apart states that rarely transition
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from statebind.dynamics.transitions import TransitionMatrix


@dataclass
class StateEmbedding:
    """Embedding vector for a single conformational state."""

    state: str
    vector: list[float]
    dim: int = 0

    def __post_init__(self) -> None:
        self.dim = len(self.vector)


@dataclass
class EmbeddingSpace:
    """Collection of state embeddings with metadata."""

    embeddings: dict[str, StateEmbedding] = field(default_factory=dict)
    dim: int = 0
    training_loss: list[float] = field(default_factory=list)
    states: list[str] = field(default_factory=list)

    def get_vector(self, state: str) -> list[float]:
        """Get embedding vector for a state."""
        return self.embeddings[state].vector

    def pairwise_distances(self) -> dict[tuple[str, str], float]:
        """Compute all pairwise Euclidean distances."""
        dists: dict[tuple[str, str], float] = {}
        for i, s1 in enumerate(self.states):
            for j, s2 in enumerate(self.states):
                if i < j:
                    v1 = self.embeddings[s1].vector
                    v2 = self.embeddings[s2].vector
                    d = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
                    dists[(s1, s2)] = d
        return dists

    def nearest_state(self, state: str) -> str:
        """Find the nearest other state in embedding space."""
        v = self.embeddings[state].vector
        best_d = float("inf")
        best_s = ""
        for s, emb in self.embeddings.items():
            if s == state:
                continue
            d = math.sqrt(sum((a - b) ** 2 for a, b in zip(v, emb.vector)))
            if d < best_d:
                best_d = d
                best_s = s
        return best_s


def _initialize_embeddings(
    states: list[str],
    dim: int,
    seed: int = 42,
    feature_centroids: dict[str, list[float]] | None = None,
) -> dict[str, list[float]]:
    """Initialize embedding vectors.

    If feature_centroids are provided, project them to target dim via
    random projection. Otherwise, use random initialization.
    """
    rng = random.Random(seed)

    if feature_centroids and all(s in feature_centroids for s in states):
        # Random projection from feature space to embedding space
        src_dim = len(next(iter(feature_centroids.values())))
        proj = [[rng.gauss(0, 1.0 / math.sqrt(dim)) for _ in range(src_dim)]
                for _ in range(dim)]

        embeddings = {}
        for state in states:
            vec = feature_centroids[state]
            projected = [sum(p[k] * vec[k] for k in range(src_dim)) for p in proj]
            embeddings[state] = projected
        return embeddings

    # Random initialization
    return {
        s: [rng.gauss(0, 0.1) for _ in range(dim)]
        for s in states
    }


def learn_embeddings(
    trans_matrix: TransitionMatrix,
    dim: int = 4,
    n_epochs: int = 200,
    learning_rate: float = 0.05,
    seed: int = 42,
    feature_centroids: dict[str, list[float]] | None = None,
) -> EmbeddingSpace:
    """Learn state embeddings that respect transition geometry.

    Objective: for each state pair (i, j), push embedding distance to
    be inversely proportional to transition probability P(j|i) + P(i|j).

    Loss = sum_{i,j} (||e_i - e_j||^2 - target_dist(i,j))^2

    Where target_dist is derived from transition probability:
    target = -log(P(j|i) + P(i|j) + eps), normalized.

    Args:
        trans_matrix: Fitted transition matrix.
        dim: Embedding dimensionality.
        n_epochs: Training iterations.
        learning_rate: SGD step size.
        seed: Random seed.
        feature_centroids: Optional structural feature centroids per state.

    Returns:
        EmbeddingSpace with learned embeddings.
    """
    states = trans_matrix.states
    n = len(states)

    # Initialize
    vecs = _initialize_embeddings(states, dim, seed, feature_centroids)

    # Compute target distances from transition matrix
    targets: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j in range(i + 1, n):
            # Symmetrized transition probability
            p_ij = trans_matrix.matrix[i][j]
            p_ji = trans_matrix.matrix[j][i]
            sym = (p_ij + p_ji) / 2.0

            # Convert to target distance: high probability = low distance
            target_d = -math.log(max(sym, 1e-8))
            targets[(i, j)] = target_d

    # Normalize targets to [0.5, 3.0] range
    if targets:
        t_min = min(targets.values())
        t_max = max(targets.values())
        t_range = max(t_max - t_min, 1e-8)
        for key in targets:
            targets[key] = 0.5 + 2.5 * (targets[key] - t_min) / t_range

    # SGD training
    losses = []
    rng = random.Random(seed + 1)

    for epoch in range(n_epochs):
        total_loss = 0.0

        # Iterate over all pairs
        pairs = list(targets.keys())
        rng.shuffle(pairs)

        for i, j in pairs:
            si, sj = states[i], states[j]
            vi, vj = vecs[si], vecs[sj]

            # Current distance
            dist_sq = sum((a - b) ** 2 for a, b in zip(vi, vj))
            dist = math.sqrt(dist_sq + 1e-10)

            target_d = targets[(i, j)]

            # Loss: (dist - target)^2
            loss = (dist - target_d) ** 2
            total_loss += loss

            # Gradient: d/dvi = 2 * (dist - target) * (vi - vj) / dist
            grad_scale = 2.0 * (dist - target_d) / (dist + 1e-10) * learning_rate

            for k in range(dim):
                diff = vi[k] - vj[k]
                vecs[si][k] -= grad_scale * diff
                vecs[sj][k] += grad_scale * diff

        avg_loss = total_loss / max(len(pairs), 1)
        losses.append(avg_loss)

    # Build result
    embeddings = {
        s: StateEmbedding(state=s, vector=vecs[s])
        for s in states
    }

    return EmbeddingSpace(
        embeddings=embeddings,
        dim=dim,
        training_loss=losses,
        states=states,
    )
