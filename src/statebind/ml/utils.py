"""ML training utilities.

All functions are gated behind optional torch dependency.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def _require_torch() -> None:
    """Raise RuntimeError if torch is not installed."""
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for this function but is not installed. "
            "Install it with: pip install torch"
        )


def get_device(preference: str = "auto") -> torch.device:
    """Get torch device based on preference.

    Args:
        preference: ``"auto"``, ``"cpu"``, ``"cuda"``, ``"cuda:0"``,
            ``"mps"``, etc.  ``"auto"`` picks CUDA if available, then
            MPS if available, then CPU.

    Returns:
        A :class:`torch.device` instance.

    Raises:
        RuntimeError: If torch is not installed.
    """
    _require_torch()

    if preference == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    return torch.device(preference)


def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility across random, numpy, torch.

    Sets seeds for:
    - :mod:`random`
    - :mod:`numpy`
    - :mod:`torch` (CPU and, if available, CUDA)

    Also enables deterministic cuDNN behaviour when torch is present.

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)

    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False


def save_model(
    model: torch.nn.Module,
    path: Path | str,
    config: dict | None = None,
    metrics: dict | None = None,
) -> Path:
    """Save model checkpoint with metadata.

    The checkpoint dictionary contains:

    - ``model_state_dict`` -- the model's :meth:`state_dict`
    - ``config``           -- optional configuration dict
    - ``metrics``          -- optional training metrics dict
    - ``timestamp``        -- ISO-8601 UTC timestamp of save time

    Args:
        model: The PyTorch model to save.
        path: Destination file path (parent dirs are created automatically).
        config: Optional configuration dictionary to store alongside weights.
        metrics: Optional metrics dictionary to store alongside weights.

    Returns:
        Resolved :class:`Path` to the saved checkpoint file.

    Raises:
        RuntimeError: If torch is not installed.
    """
    _require_torch()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint: dict = {
        "model_state_dict": model.state_dict(),
        "config": config,
        "metrics": metrics,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    torch.save(checkpoint, path)
    return path.resolve()


def load_model(
    model: torch.nn.Module,
    path: Path | str,
    device: torch.device | str = "cpu",
) -> dict:
    """Load model from checkpoint.

    The model is updated **in-place** via :meth:`load_state_dict`.

    Args:
        model: A model instance whose architecture matches the saved
            state dict.
        path: Path to the checkpoint file produced by :func:`save_model`.
        device: Device to map tensors to when loading.

    Returns:
        The full checkpoint dictionary (contains ``config``, ``metrics``,
        ``timestamp``, etc.).

    Raises:
        RuntimeError: If torch is not installed.
        FileNotFoundError: If *path* does not exist.
    """
    _require_torch()

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")

    checkpoint: dict = torch.load(path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    return checkpoint


def count_parameters(model: torch.nn.Module) -> tuple[int, int]:
    """Count total and trainable parameters in a model.

    Args:
        model: A PyTorch :class:`~torch.nn.Module`.

    Returns:
        A ``(total_params, trainable_params)`` tuple.

    Raises:
        RuntimeError: If torch is not installed.
    """
    _require_torch()

    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


@dataclass
class EarlyStopper:
    """Early stopping tracker.

    Monitors a validation loss and signals when training should stop
    because no improvement has been observed for *patience* consecutive
    epochs.

    Usage::

        stopper = EarlyStopper(patience=10)
        for epoch in range(n_epochs):
            val_loss = train_one_epoch()
            if stopper.step(val_loss, epoch):
                break  # no improvement for ``patience`` epochs
    """

    patience: int = 10
    min_delta: float = 0.0
    best_loss: float = float("inf")
    counter: int = 0
    best_epoch: int = 0

    def step(self, val_loss: float, epoch: int = 0) -> bool:
        """Record a validation loss and decide whether to stop.

        An improvement is registered when *val_loss* is at least
        ``min_delta`` lower than the current best loss.

        Args:
            val_loss: The validation loss for this epoch.
            epoch: The current epoch index (stored when a new best is
                found).

        Returns:
            ``True`` if training should stop (no improvement for
            *patience* steps), ``False`` otherwise.
        """
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            self.best_epoch = epoch
            return False

        self.counter += 1
        return self.counter >= self.patience

    def reset(self) -> None:
        """Reset the stopper to its initial state."""
        self.best_loss = float("inf")
        self.counter = 0
        self.best_epoch = 0
