"""ML infrastructure: shared training utilities, model cards, and optional deep-learning backends.

Provides framework-agnostic Pydantic configuration models (TrainerConfig,
TrainingMetrics, TrainingHistory, ModelCard) that work without any ML library
installed.  When PyTorch and/or PyTorch-Geometric are available, higher-level
helpers (trainers, GNN layers, etc.) are re-exported from submodules.

Optional dependencies:
    torch             — needed for any neural-network training
    torch_geometric   — needed for graph neural network (MPNN) models

The flags ``HAS_TORCH`` and ``HAS_TORCH_GEOMETRIC`` let callers check
availability at runtime without catching ImportError themselves.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Optional dependency flags
# ---------------------------------------------------------------------------

HAS_TORCH: bool
"""True when ``torch`` is importable in the current environment."""

try:
    import torch as _torch  # noqa: F401

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

HAS_TORCH_GEOMETRIC: bool
"""True when ``torch_geometric`` is importable in the current environment."""

try:
    import torch_geometric as _pyg  # noqa: F401

    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False

# ---------------------------------------------------------------------------
# Always-available Pydantic models (no ML deps required)
# ---------------------------------------------------------------------------

from statebind.ml.models import (  # noqa: E402
    ModelCard,
    TrainerConfig,
    TrainingHistory,
    TrainingMetrics,
)

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    # Dependency flags
    "HAS_TORCH",
    "HAS_TORCH_GEOMETRIC",
    # Pydantic config / data models
    "TrainerConfig",
    "TrainingMetrics",
    "TrainingHistory",
    "ModelCard",
    # Version
    "__version__",
]
