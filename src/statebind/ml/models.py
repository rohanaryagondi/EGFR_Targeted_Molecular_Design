"""Pydantic v2 data models for ML training configuration, metrics, and model metadata.

All models are plain Pydantic ``BaseModel`` subclasses with no ML-library
dependencies so they can be imported, serialised, and validated even when
torch is not installed.

Models:
    TrainerConfig     — Hyperparameters and runtime settings for a training run.
    TrainingMetrics   — Per-epoch loss / LR snapshot.
    TrainingHistory   — Full training trajectory plus best-epoch bookkeeping.
    ModelCard         — Reproducibility metadata for a trained model artifact.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Training configuration
# ---------------------------------------------------------------------------


class TrainerConfig(BaseModel):
    """Hyperparameters and runtime settings for a single training run.

    ``device`` accepts ``"auto"`` (resolve to CUDA if available, else CPU),
    an explicit ``"cpu"`` / ``"cuda"`` string, or a device ordinal like
    ``"cuda:0"``.  Resolution is deferred to the trainer implementation so
    this model stays framework-free.
    """

    epochs: int = 100
    batch_size: int = 64
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    lr_scheduler: Literal["cosine", "plateau", "none"] = "cosine"
    patience: int = 15
    gradient_clip: float = 1.0
    device: str = "auto"
    checkpoint_dir: str = "artifacts/models/"
    log_dir: str = "artifacts/logs/"
    seed: int = 42
    num_workers: int = 0
    mixed_precision: bool = False


# ---------------------------------------------------------------------------
# Per-epoch metrics
# ---------------------------------------------------------------------------


class TrainingMetrics(BaseModel):
    """Snapshot of training metrics for a single epoch.

    ``extra`` can carry arbitrary per-epoch scalars (accuracy, AUROC, etc.)
    that are model-specific and not part of the common schema.
    """

    epoch: int
    train_loss: float
    val_loss: float | None = None
    learning_rate: float
    extra: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Training history (full run)
# ---------------------------------------------------------------------------


class TrainingHistory(BaseModel):
    """Complete record of a training run: config, per-epoch metrics, and timing.

    ``best_epoch`` and ``best_val_loss`` are updated by the trainer whenever a
    new validation-loss minimum is observed.  If no validation set is used,
    they retain their defaults (epoch 0, inf loss).
    """

    config: TrainerConfig
    metrics: list[TrainingMetrics] = Field(default_factory=list)
    best_epoch: int = 0
    best_val_loss: float = float("inf")
    total_time_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Model card (reproducibility metadata)
# ---------------------------------------------------------------------------


class ModelCard(BaseModel):
    """Metadata about a trained model for reproducibility.

    Captures enough context to understand what a model does, how it was
    trained, and where its limitations lie — without embedding the weights
    themselves.  Intended to be serialised alongside checkpoint files in
    ``artifacts/models/``.
    """

    model_name: str
    model_type: str  # "vae", "mpnn", "admet"
    description: str = ""
    input_format: str = ""   # e.g. "SMILES string" or "PyG Data object"
    output_format: str = ""  # e.g. "pIC50 float" or "dict[str, float]"
    training_data: str = ""  # e.g. "ChEMBL EGFR IC50, N=3421"
    n_parameters: int = 0
    performance: dict[str, float] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    version: str = "0.1.0"
