"""Learned EGFR binding proxy.

Architecture: hand-rolled MLP (same pattern as dynamics/world_model.py:81-160).
Features: top-variance Morgan fingerprint bits + molecular descriptors.
Training: SGD with gradient clipping on embedded EGFR SAR data.

LIMITATION: This is a discriminative model trained on 9 binders vs 25 decoys.
It measures "EGFR-likeness" not binding affinity.  It cannot rank binders
by potency.  Document this clearly in any downstream usage.

Contract reference: workstreams/INTERFACES.md Contract 2.
"""

from __future__ import annotations

import math
import threading
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    pass


# ── Feature extraction ────────────────────────────────────────────────────

# Descriptor keys extracted from chemistry.descriptors.compute_exact_properties().
# Order matters — must match between fit() and predict().
_DESCRIPTOR_KEYS: list[str] = [
    "estimated_mw",
    "logp",
    "tpsa",
    "estimated_hba",
    "estimated_hbd",
    "n_rings",
    "n_rotatable_bonds",
]
_N_DESCRIPTORS: int = len(_DESCRIPTOR_KEYS)  # 7


def _has_rdkit() -> bool:
    """Check if RDKit is available via the chemistry module."""
    try:
        from statebind.chemistry.fingerprints import HAS_RDKIT
        return HAS_RDKIT
    except ImportError:
        return False


def _morgan_to_array(smiles: str, n_bits: int = 2048) -> np.ndarray | None:
    """Convert SMILES to a dense numpy array of Morgan fingerprint bits.

    Returns None if SMILES is invalid or RDKit is unavailable.
    """
    try:
        from statebind.chemistry.fingerprints import compute_morgan_fingerprint
    except ImportError:
        return None

    fp = compute_morgan_fingerprint(smiles, radius=2, n_bits=n_bits)
    if fp is None:
        return None
    arr = np.zeros(n_bits, dtype=np.float64)
    for idx in fp.GetOnBits():
        arr[idx] = 1.0
    return arr


def _descriptors_to_array(smiles: str) -> np.ndarray | None:
    """Extract molecular descriptors as a numpy array.

    Returns None if any descriptor is None (invalid SMILES or no RDKit).
    """
    try:
        from statebind.chemistry.descriptors import compute_exact_properties
    except ImportError:
        return None

    props = compute_exact_properties(smiles)
    values = [props.get(k) for k in _DESCRIPTOR_KEYS]
    if any(v is None for v in values):
        return None
    return np.array(values, dtype=np.float64)


# ── Sigmoid / BCE helpers ─────────────────────────────────────────────────

_EPS = 1e-12


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


# ── DockingProxy MLP ─────────────────────────────────────────────────────


class DockingProxy:
    """Learned EGFR binding discriminator.

    Architecture: Linear(input_dim -> hidden_dim) -> ReLU
                  -> Linear(hidden_dim -> 1) -> Sigmoid

    Features (computed in _featurize):
        - Top-N Morgan fingerprint bits by variance (N = input_dim - 7)
        - 7 molecular descriptors: MW, LogP, TPSA, HBA, HBD, rings, rot bonds

    The model is trained via ``fit()`` and cached via ``get_default_proxy()``.
    """

    def __init__(self, input_dim: int = 20, hidden_dim: int = 16) -> None:
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.n_fp_bits = input_dim - _N_DESCRIPTORS  # top FP bits to keep

        # Weights — set during fit()
        self.W1: np.ndarray | None = None
        self.b1: np.ndarray | None = None
        self.W2: np.ndarray | None = None
        self.b2: np.ndarray | None = None

        # Feature selection / normalization — set during fit()
        self._fp_indices: np.ndarray | None = None  # which FP bits to keep
        self._desc_min: np.ndarray | None = None
        self._desc_max: np.ndarray | None = None

        self.fitted: bool = False
        self._rng = np.random.RandomState(42)

    # ── Feature extraction ────────────────────────────────────────────

    def _featurize(self, smiles: str) -> np.ndarray | None:
        """Convert SMILES to feature vector.

        Returns None if featurization fails (invalid SMILES, no RDKit).
        """
        if not _has_rdkit():
            return None

        fp_arr = _morgan_to_array(smiles)
        if fp_arr is None:
            return None

        desc_arr = _descriptors_to_array(smiles)
        if desc_arr is None:
            return None

        # Select top-variance FP bits (set during fit)
        if self._fp_indices is not None:
            fp_selected = fp_arr[self._fp_indices]
        else:
            # Before fit — use first N bits (should not happen in practice)
            fp_selected = fp_arr[: self.n_fp_bits]

        # Normalize descriptors using training-set statistics
        if self._desc_min is not None and self._desc_max is not None:
            desc_range = self._desc_max - self._desc_min + _EPS
            desc_norm = (desc_arr - self._desc_min) / desc_range
        else:
            desc_norm = desc_arr

        return np.concatenate([fp_selected, desc_norm])

    # ── Training ──────────────────────────────────────────────────────

    def fit(
        self,
        smiles_list: list[str],
        labels: list[int],
        n_epochs: int = 200,
        lr: float = 0.01,
    ) -> list[float]:
        """Train on (SMILES, label) pairs.  Returns loss history.

        Steps:
        1. Featurize all valid training SMILES (full 2048-bit FP + descriptors).
        2. Select top-variance FP bits and compute descriptor normalization.
        3. Build final feature matrix.
        4. Train MLP via SGD with gradient clipping.
        """
        if not _has_rdkit():
            return []

        # Step 1 — raw features for all valid samples
        raw_fps: list[np.ndarray] = []
        raw_descs: list[np.ndarray] = []
        valid_labels: list[int] = []

        for smi, lbl in zip(smiles_list, labels):
            fp = _morgan_to_array(smi)
            desc = _descriptors_to_array(smi)
            if fp is not None and desc is not None:
                raw_fps.append(fp)
                raw_descs.append(desc)
                valid_labels.append(lbl)

        if len(valid_labels) < 2:
            return []

        fp_matrix = np.array(raw_fps)       # (N, 2048)
        desc_matrix = np.array(raw_descs)    # (N, 7)
        y = np.array(valid_labels, dtype=np.float64)  # (N,)

        # Step 2 — feature selection and normalization stats
        fp_var = fp_matrix.var(axis=0)
        top_indices = np.argsort(fp_var)[-self.n_fp_bits:]
        self._fp_indices = np.sort(top_indices)

        self._desc_min = desc_matrix.min(axis=0)
        self._desc_max = desc_matrix.max(axis=0)

        # Step 3 — build final feature matrix
        fp_selected = fp_matrix[:, self._fp_indices]    # (N, n_fp_bits)
        desc_range = self._desc_max - self._desc_min + _EPS
        desc_norm = (desc_matrix - self._desc_min) / desc_range  # (N, 7)
        X = np.concatenate([fp_selected, desc_norm], axis=1)     # (N, input_dim)

        # Step 4 — Xavier init (following dynamics/world_model.py:115-122)
        s1 = np.sqrt(2.0 / (self.input_dim + self.hidden_dim))
        s2 = np.sqrt(2.0 / (self.hidden_dim + 1))
        self.W1 = self._rng.randn(self.hidden_dim, self.input_dim) * s1
        self.b1 = np.zeros(self.hidden_dim)
        self.W2 = self._rng.randn(1, self.hidden_dim) * s2
        self.b2 = np.zeros(1)

        # Step 5 — SGD training loop
        n = len(y)
        indices = np.arange(n)
        loss_history: list[float] = []

        for _epoch in range(n_epochs):
            self._rng.shuffle(indices)
            epoch_loss = 0.0

            for i in indices:
                x = X[i]       # (input_dim,)
                target = y[i]  # scalar

                # Forward
                z = self.W1 @ x + self.b1              # (hidden,)
                h = np.maximum(0.0, z)                  # ReLU
                logit = float((self.W2 @ h + self.b2).item())  # scalar
                pred = _sigmoid(logit)

                # Binary cross-entropy loss
                loss = -(
                    target * math.log(pred + _EPS)
                    + (1.0 - target) * math.log(1.0 - pred + _EPS)
                )
                epoch_loss += loss

                # Backward
                d_logit = pred - target  # sigmoid + BCE gradient

                # W2, b2 gradients
                d_W2 = d_logit * h       # (hidden,)
                d_b2 = d_logit

                # Hidden layer gradients
                d_h = self.W2[0] * d_logit            # (hidden,)
                d_z = d_h * (z > 0).astype(np.float64)  # ReLU gradient

                # W1, b1 gradients
                d_W1 = d_z[:, None] @ x[None, :]     # (hidden, input_dim)
                d_b1 = d_z                            # (hidden,)

                # Gradient clipping
                d_W1 = np.clip(d_W1, -1.0, 1.0)
                d_b1 = np.clip(d_b1, -1.0, 1.0)
                d_W2 = np.clip(d_W2, -1.0, 1.0)

                # Update weights
                self.W1 -= lr * d_W1
                self.b1 -= lr * d_b1
                self.W2[0] -= lr * d_W2
                self.b2[0] -= lr * d_b2

            loss_history.append(epoch_loss / n)

        self.fitted = True
        return loss_history

    # ── Inference ─────────────────────────────────────────────────────

    def predict(self, smiles: str) -> float:
        """Predict EGFR-likeness score in [0, 1].

        Returns 0.5 if the model is not fitted or featurization fails.
        """
        if not self.fitted:
            return 0.5

        x = self._featurize(smiles)
        if x is None:
            return 0.5

        z = self.W1 @ x + self.b1
        h = np.maximum(0.0, z)
        logit = float((self.W2 @ h + self.b2).item())
        return round(_sigmoid(logit), 4)

    def predict_batch(self, smiles_list: list[str]) -> list[float]:
        """Batch prediction.  Same semantics as predict()."""
        return [self.predict(s) for s in smiles_list]


# ── Singleton ─────────────────────────────────────────────────────────────

_DEFAULT_PROXY: DockingProxy | None = None
_PROXY_LOCK = threading.Lock()


def get_default_proxy() -> DockingProxy:
    """Get or create the default trained proxy.

    Trains on first call using embedded EGFR SAR data from docking_data.py.
    Thread-safe via double-checked locking.
    """
    global _DEFAULT_PROXY
    if _DEFAULT_PROXY is not None:
        return _DEFAULT_PROXY
    with _PROXY_LOCK:
        if _DEFAULT_PROXY is not None:
            return _DEFAULT_PROXY
        proxy = DockingProxy()
        try:
            from statebind.chemistry.docking_data import get_training_data

            smiles_list, labels = get_training_data()
            proxy.fit(smiles_list, labels)
        except Exception:
            pass  # proxy stays unfitted — predict() returns 0.5
        _DEFAULT_PROXY = proxy
        return proxy
