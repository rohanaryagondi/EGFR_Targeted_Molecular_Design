"""Transition matrix estimation and Markov model.

Computes state-to-state transition probabilities from observed transitions.
Implements:
1. UniformBaseline: equal probability to all states (random walk)
2. MarkovTransitionModel: maximum-likelihood transition matrix from counts
   with Laplace smoothing

The Markov model is the first useful dynamics model: it captures which
transitions are common (e.g., active ↔ Src-like) vs rare (active → DFGout).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from statebind.dynamics.sequences import StateTransition


@dataclass
class TransitionMatrix:
    """Row-stochastic transition matrix P(to | from).

    matrix[i][j] = P(state_j | state_i)
    """

    states: list[str]
    matrix: list[list[float]] = field(default_factory=list)
    counts: list[list[int]] = field(default_factory=list)

    def get_prob(self, from_state: str, to_state: str) -> float:
        """Get P(to_state | from_state)."""
        i = self.states.index(from_state)
        j = self.states.index(to_state)
        return self.matrix[i][j]

    def get_row(self, from_state: str) -> dict[str, float]:
        """Get full transition distribution from a state."""
        i = self.states.index(from_state)
        return dict(zip(self.states, self.matrix[i]))

    def stationary_distribution(self, max_iter: int = 1000, tol: float = 1e-8) -> dict[str, float]:
        """Compute stationary distribution by power iteration.

        π = π @ P, iteratively.
        """
        n = len(self.states)
        pi = [1.0 / n] * n  # uniform initial

        for _ in range(max_iter):
            pi_new = [0.0] * n
            for j in range(n):
                for i in range(n):
                    pi_new[j] += pi[i] * self.matrix[i][j]

            # Check convergence
            diff = sum(abs(a - b) for a, b in zip(pi, pi_new))
            pi = pi_new
            if diff < tol:
                break

        return dict(zip(self.states, pi))


@dataclass
class TransitionPrediction:
    """Prediction for the next state given current state."""

    from_state: str
    predicted_state: str
    probabilities: dict[str, float]
    confidence: float  # max probability
    model_name: str = ""


def estimate_transition_matrix(
    transitions: list[StateTransition],
    states: list[str],
    smoothing: float = 1.0,
) -> TransitionMatrix:
    """Estimate transition matrix from observed transitions.

    Uses Laplace smoothing to avoid zero probabilities.
    P(j|i) = (count(i→j) + smoothing) / (sum_k count(i→k) + n * smoothing)

    Args:
        transitions: Observed state transitions.
        states: List of all possible states.
        smoothing: Laplace smoothing parameter (1.0 = add-one).

    Returns:
        TransitionMatrix with row-stochastic probabilities.
    """
    n = len(states)
    state_idx = {s: i for i, s in enumerate(states)}

    # Count transitions
    counts = [[0] * n for _ in range(n)]
    for t in transitions:
        if t.from_state in state_idx and t.to_state in state_idx:
            i = state_idx[t.from_state]
            j = state_idx[t.to_state]
            counts[i][j] += 1

    # Normalize with smoothing
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        row_total = sum(counts[i]) + n * smoothing
        for j in range(n):
            matrix[i][j] = (counts[i][j] + smoothing) / row_total

    return TransitionMatrix(states=states, matrix=matrix, counts=counts)


class UniformBaseline:
    """Baseline model: uniform random transition to any state.

    Always predicts equal probability for all states.
    This is the floor — any useful model must beat it.
    """

    def __init__(self, states: list[str]):
        self.states = states
        self.n_states = len(states)

    def predict(self, from_state: str) -> TransitionPrediction:
        """Predict next state (uniform)."""
        prob = 1.0 / self.n_states
        return TransitionPrediction(
            from_state=from_state,
            predicted_state=self.states[0],  # arbitrary
            probabilities={s: prob for s in self.states},
            confidence=prob,
            model_name="uniform_baseline",
        )

    def predict_sequence(self, states: list[str]) -> list[TransitionPrediction]:
        """Predict next state for each position in a sequence."""
        return [self.predict(s) for s in states[:-1]]

    def log_likelihood(self, transitions: list[StateTransition]) -> float:
        """Compute average log-likelihood of transitions."""
        if not transitions:
            return 0.0
        prob = 1.0 / self.n_states
        return math.log(max(prob, 1e-15))  # same for all transitions


class MarkovTransitionModel:
    """First-order Markov model with Laplace-smoothed transition matrix.

    P(next_state | current_state) from empirical transition counts.
    """

    def __init__(self, states: list[str], smoothing: float = 1.0):
        self.states = states
        self.smoothing = smoothing
        self.trans_matrix: TransitionMatrix | None = None
        self.fitted = False

    def fit(self, transitions: list[StateTransition]) -> "MarkovTransitionModel":
        """Estimate transition matrix from data."""
        self.trans_matrix = estimate_transition_matrix(
            transitions, self.states, smoothing=self.smoothing
        )
        self.fitted = True
        return self

    def predict(self, from_state: str) -> TransitionPrediction:
        """Predict next state from transition matrix."""
        if not self.fitted or self.trans_matrix is None:
            raise RuntimeError("Model not fitted.")

        probs = self.trans_matrix.get_row(from_state)
        best = max(probs, key=probs.get)  # type: ignore[arg-type]

        return TransitionPrediction(
            from_state=from_state,
            predicted_state=best,
            probabilities=probs,
            confidence=probs[best],
            model_name="markov",
        )

    def predict_sequence(self, states: list[str]) -> list[TransitionPrediction]:
        """Predict next state for each step in a sequence."""
        return [self.predict(s) for s in states[:-1]]

    def log_likelihood(self, transitions: list[StateTransition]) -> float:
        """Compute average log-likelihood of transitions under the model."""
        if not self.fitted or self.trans_matrix is None:
            raise RuntimeError("Model not fitted.")
        if not transitions:
            return 0.0

        total = 0.0
        for t in transitions:
            prob = self.trans_matrix.get_prob(t.from_state, t.to_state)
            total += math.log(max(prob, 1e-15))
        return total / len(transitions)

    def get_stationary(self) -> dict[str, float]:
        """Return stationary distribution."""
        if not self.fitted or self.trans_matrix is None:
            raise RuntimeError("Model not fitted.")
        return self.trans_matrix.stationary_distribution()
