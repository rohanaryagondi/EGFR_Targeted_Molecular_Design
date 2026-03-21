#!/usr/bin/env python3
"""Train an MPNN binding affinity predictor on EGFR bioactivity data.

Loads molecular graphs from a JSON dataset of SMILES/pIC50 records,
trains an :class:`~statebind.ml.mpnn.AffinityMPNN` model using PyTorch
Geometric, and evaluates on a held-out test set.

Outputs:
    artifacts/models/mpnn/best_model.pt   — best checkpoint (by val loss)
    artifacts/logs/mpnn/training_log.csv  — per-epoch metrics
    artifacts/evaluation/mpnn_metrics.json — test-set evaluation
    artifacts/models/mpnn/model_card.json — reproducibility metadata

Usage:
    python scripts/train_mpnn.py
    python scripts/train_mpnn.py --config configs/mpnn.yaml
    python scripts/train_mpnn.py --resume artifacts/models/mpnn/best_model.pt
    python scripts/train_mpnn.py --data-dir data/processed/
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from statebind.ml.affinity_dataset import (
    AffinityDatasetConfig,
    load_affinity_dataset,
    split_dataset,
)
from statebind.ml.models import ModelCard, TrainerConfig
from statebind.ml.mpnn import AffinityMPNN, MPNNConfig
from statebind.ml.utils import (
    EarlyStopper,
    count_parameters,
    get_device,
    save_model,
    set_seed,
)

# ---------------------------------------------------------------------------
# Optional rich progress bar
# ---------------------------------------------------------------------------

try:
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
    )

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------


def _load_config(config_path: str) -> dict[str, Any]:
    """Load YAML configuration and return raw dict.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def _build_model_config(raw: dict[str, Any]) -> MPNNConfig:
    """Build an MPNNConfig from the 'model' section of the YAML.

    Args:
        raw: Full parsed YAML dict.

    Returns:
        Validated :class:`MPNNConfig`.
    """
    model_section = raw.get("model", {})
    return MPNNConfig(**model_section)


def _build_trainer_config(raw: dict[str, Any]) -> TrainerConfig:
    """Build a TrainerConfig from the 'training' section of the YAML.

    Args:
        raw: Full parsed YAML dict.

    Returns:
        Validated :class:`TrainerConfig`.
    """
    training_section = raw.get("training", {})
    return TrainerConfig(**training_section)


def _build_data_config(
    raw: dict[str, Any], data_dir_override: str | None = None
) -> AffinityDatasetConfig:
    """Build an AffinityDatasetConfig from the 'data' section of the YAML.

    Args:
        raw: Full parsed YAML dict.
        data_dir_override: If provided, replaces the directory component
            of the configured data_path.

    Returns:
        Validated :class:`AffinityDatasetConfig`.
    """
    data_section = raw.get("data", {})

    if data_dir_override is not None:
        original_path = Path(data_section.get("data_path", ""))
        data_section["data_path"] = str(
            Path(data_dir_override) / original_path.name
        )

    return AffinityDatasetConfig(**data_section)


# ---------------------------------------------------------------------------
# Training loop (PyG-aware)
# ---------------------------------------------------------------------------


def _train_epoch(
    model: AffinityMPNN,
    loader: Any,
    loss_fn: Any,
    optimizer: Any,
    device: Any,
    gradient_clip: float,
    scaler: Any | None = None,
) -> float:
    """Run one training epoch over PyG batches.

    Args:
        model: The MPNN model.
        loader: PyG DataLoader yielding Batch objects.
        loss_fn: Loss function (e.g. MSELoss).
        optimizer: Torch optimizer.
        device: Target device.
        gradient_clip: Max gradient norm for clipping.
        scaler: Optional GradScaler for mixed precision.

    Returns:
        Mean training loss for this epoch.
    """
    import torch

    model.train()
    total_loss = 0.0
    n_batches = 0

    use_amp = scaler is not None

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()

        if use_amp:
            with torch.amp.autocast("cuda"):
                pred = model(batch)
                loss = loss_fn(pred.squeeze(), batch.y)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip)
            scaler.step(optimizer)
            scaler.update()
        else:
            pred = model(batch)
            loss = loss_fn(pred.squeeze(), batch.y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip)
            optimizer.step()

        total_loss += loss.item()
        n_batches += 1

    return total_loss / max(n_batches, 1)


def _val_epoch(
    model: AffinityMPNN,
    loader: Any,
    loss_fn: Any,
    device: Any,
) -> float:
    """Run one validation epoch over PyG batches.

    Args:
        model: The MPNN model.
        loader: PyG DataLoader yielding Batch objects.
        loss_fn: Loss function.
        device: Target device.

    Returns:
        Mean validation loss for this epoch.
    """
    import torch

    model.eval()
    total_loss = 0.0
    n_batches = 0

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            pred = model(batch)
            loss = loss_fn(pred.squeeze(), batch.y)
            total_loss += loss.item()
            n_batches += 1

    return total_loss / max(n_batches, 1)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _evaluate_test_set(
    model: AffinityMPNN,
    loader: Any,
    device: Any,
    metrics_list: list[str],
) -> dict[str, float]:
    """Evaluate the model on the test set and compute requested metrics.

    Supported metrics: rmse, mae, r2, pearson.

    Args:
        model: Trained MPNN model (set to eval mode internally).
        loader: PyG DataLoader for the test set.
        device: Target device.
        metrics_list: List of metric names to compute.

    Returns:
        Dictionary mapping metric name to rounded float value.
    """
    import torch
    from scipy import stats as scipy_stats

    model.eval()
    all_preds: list[float] = []
    all_targets: list[float] = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            pred = model(batch)
            all_preds.extend(pred.squeeze().cpu().tolist())
            all_targets.extend(batch.y.cpu().tolist())

    preds = np.array(all_preds)
    targets = np.array(all_targets)

    results: dict[str, float] = {}

    if "rmse" in metrics_list:
        mse = float(np.mean((preds - targets) ** 2))
        results["rmse"] = round(math.sqrt(mse), 4)

    if "mae" in metrics_list:
        results["mae"] = round(float(np.mean(np.abs(preds - targets))), 4)

    if "r2" in metrics_list:
        ss_res = float(np.sum((targets - preds) ** 2))
        ss_tot = float(np.sum((targets - np.mean(targets)) ** 2))
        r2 = 1.0 - (ss_res / max(ss_tot, 1e-12))
        results["r2"] = round(r2, 4)

    if "pearson" in metrics_list:
        if len(preds) > 1:
            corr, _ = scipy_stats.pearsonr(preds, targets)
            results["pearson"] = round(float(corr), 4)
        else:
            results["pearson"] = 0.0

    return results


# ---------------------------------------------------------------------------
# CSV logging
# ---------------------------------------------------------------------------


def _init_csv(csv_path: Path) -> None:
    """Write CSV header if the log file does not exist yet.

    Args:
        csv_path: Path to the CSV log file.
    """
    if not csv_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["epoch", "train_loss", "val_loss", "learning_rate"])


def _log_csv(
    csv_path: Path,
    epoch: int,
    train_loss: float,
    val_loss: float | None,
    lr: float,
) -> None:
    """Append one row of epoch metrics to the CSV log.

    Args:
        csv_path: Path to the CSV log file.
        epoch: Current epoch number.
        train_loss: Training loss for this epoch.
        val_loss: Validation loss (or None).
        lr: Current learning rate.
    """
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            epoch,
            round(train_loss, 4),
            round(val_loss, 4) if val_loss is not None else "",
            lr,
        ])


# ---------------------------------------------------------------------------
# Model card
# ---------------------------------------------------------------------------


def _save_model_card(
    model: AffinityMPNN,
    model_config: MPNNConfig,
    trainer_config: TrainerConfig,
    data_config: AffinityDatasetConfig,
    test_metrics: dict[str, float],
    n_train: int,
    n_val: int,
    n_test: int,
    best_epoch: int,
    output_dir: Path,
) -> Path:
    """Save a ModelCard JSON alongside the checkpoint.

    Args:
        model: The trained model (used for parameter count).
        model_config: MPNN architecture config.
        trainer_config: Training hyperparameters.
        data_config: Dataset config.
        test_metrics: Evaluation metrics on the test set.
        n_train: Number of training samples.
        n_val: Number of validation samples.
        n_test: Number of test samples.
        best_epoch: Epoch with the best validation loss.
        output_dir: Directory to write the model card JSON.

    Returns:
        Path to the saved model card file.
    """
    total_params, trainable_params = count_parameters(model)

    card = ModelCard(
        model_name="AffinityMPNN",
        model_type="mpnn",
        description=(
            "Message Passing Neural Network for EGFR binding affinity "
            "prediction (pIC50). Trained on ChEMBL bioactivity data to "
            "replace the docking_proxy stub in the ranking pipeline."
        ),
        input_format="PyG Data object (molecular graph from smiles_to_graph)",
        output_format="pIC50 float (predicted binding affinity)",
        training_data=(
            f"ChEMBL EGFR pIC50, N={n_train + n_val + n_test} "
            f"(train={n_train}, val={n_val}, test={n_test})"
        ),
        n_parameters=total_params,
        performance=test_metrics,
        limitations=[
            "Trained on EGFR data only; may not generalise to other targets.",
            "pIC50 predictions are estimates; no experimental validation.",
            f"Best epoch: {best_epoch} (early stopping with patience "
            f"{trainer_config.patience}).",
            f"Architecture: {model_config.n_message_passing_layers} MP layers, "
            f"hidden_dim={model_config.hidden_dim}, "
            f"readout={model_config.readout}.",
        ],
        version="0.1.0",
    )

    card_path = output_dir / "model_card.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    with open(card_path, "w") as f:
        json.dump(card.model_dump(), f, indent=2)

    return card_path


# ---------------------------------------------------------------------------
# Main training pipeline
# ---------------------------------------------------------------------------


def train_mpnn(
    config_path: str = "configs/mpnn.yaml",
    resume_path: str | None = None,
    data_dir: str | None = None,
) -> None:
    """End-to-end MPNN training pipeline.

    Loads config, prepares data, trains the model with early stopping,
    evaluates on the test set, and saves all artifacts.

    Args:
        config_path: Path to the YAML configuration file.
        resume_path: Optional path to a checkpoint to resume from.
        data_dir: Optional override for the data directory.
    """
    import torch
    from torch_geometric.loader import DataLoader

    # ── Load configuration ────────────────────────────────────────────
    raw_config = _load_config(config_path)
    model_config = _build_model_config(raw_config)
    trainer_config = _build_trainer_config(raw_config)
    data_config = _build_data_config(raw_config, data_dir_override=data_dir)
    eval_config = raw_config.get("evaluation", {})
    metrics_list: list[str] = eval_config.get("metrics", ["rmse", "mae", "r2", "pearson"])
    eval_output_path = Path(eval_config.get(
        "output_path", "artifacts/evaluation/mpnn_metrics.json"
    ))

    print(f"Config loaded from: {config_path}")
    print(f"  Model: hidden_dim={model_config.hidden_dim}, "
          f"layers={model_config.n_message_passing_layers}, "
          f"readout={model_config.readout}")
    print(f"  Training: epochs={trainer_config.epochs}, "
          f"lr={trainer_config.learning_rate}, "
          f"batch_size={trainer_config.batch_size}")

    # ── Seed and device ───────────────────────────────────────────────
    set_seed(trainer_config.seed)
    device = get_device(trainer_config.device)
    print(f"  Device: {device}")

    # ── Load and split dataset ────────────────────────────────────────
    data_path = Path(data_config.data_path)
    if not data_path.exists():
        print(f"\nERROR: Data file not found: {data_path}")
        print("Run the data preparation pipeline first, or provide "
              "--data-dir pointing to the correct location.")
        sys.exit(1)

    print(f"\nLoading dataset from: {data_path}")
    dataset = load_affinity_dataset(data_path, config=data_config)
    summary = dataset.summary()
    print(f"  Loaded {summary['n_samples']} valid graphs")
    print(f"  pIC50 range: [{summary['min_pIC50']}, {summary['max_pIC50']}] "
          f"(mean={summary['mean_pIC50']}, std={summary['std_pIC50']})")

    if summary["n_samples"] == 0:
        print("\nERROR: No valid graphs in dataset. Check your data file.")
        sys.exit(1)

    train_ds, val_ds, test_ds = split_dataset(dataset, config=data_config)
    print(f"  Splits: train={len(train_ds)}, val={len(val_ds)}, test={len(test_ds)}")

    # ── Create DataLoaders ────────────────────────────────────────────
    train_loader = DataLoader(
        train_ds,
        batch_size=trainer_config.batch_size,
        shuffle=True,
        num_workers=trainer_config.num_workers,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=trainer_config.batch_size,
        shuffle=False,
        num_workers=trainer_config.num_workers,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=trainer_config.batch_size,
        shuffle=False,
        num_workers=trainer_config.num_workers,
    )

    # ── Initialize model ──────────────────────────────────────────────
    model = AffinityMPNN(config=model_config)
    model = model.to(device)

    total_params, trainable_params = count_parameters(model)
    print(f"\nModel initialized: {total_params:,} total params "
          f"({trainable_params:,} trainable)")

    # ── Optimizer, loss, scheduler ────────────────────────────────────
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=trainer_config.learning_rate,
        weight_decay=trainer_config.weight_decay,
    )
    loss_fn = torch.nn.MSELoss()

    scheduler: torch.optim.lr_scheduler.LRScheduler | None = None
    if trainer_config.lr_scheduler == "cosine":
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=trainer_config.epochs, eta_min=1e-7
        )
    elif trainer_config.lr_scheduler == "plateau":
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=0.5,
            patience=max(trainer_config.patience // 3, 3),
            min_lr=1e-7,
        )

    stopper = EarlyStopper(patience=trainer_config.patience)

    # Mixed precision scaler (CUDA only)
    use_amp = trainer_config.mixed_precision and device.type == "cuda"
    scaler: torch.amp.GradScaler | None = None
    if use_amp:
        scaler = torch.amp.GradScaler("cuda")
        print("  Mixed precision: enabled")

    # ── Resume from checkpoint ────────────────────────────────────────
    start_epoch = 0
    if resume_path is not None:
        resume_file = Path(resume_path)
        if not resume_file.exists():
            print(f"\nERROR: Checkpoint not found: {resume_file}")
            sys.exit(1)
        checkpoint = torch.load(resume_file, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        if checkpoint.get("metrics") and checkpoint["metrics"].get("epoch") is not None:
            start_epoch = checkpoint["metrics"]["epoch"] + 1
        print(f"\nResumed from checkpoint: {resume_file} (starting at epoch {start_epoch})")

    # ── Prepare logging ───────────────────────────────────────────────
    ckpt_dir = Path(trainer_config.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path(trainer_config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    csv_path = log_dir / "training_log.csv"
    _init_csv(csv_path)

    # ── Training loop ─────────────────────────────────────────────────
    print(f"\nTraining for up to {trainer_config.epochs} epochs "
          f"(patience={trainer_config.patience})...")
    print("-" * 70)

    best_val_loss = float("inf")
    best_epoch = 0
    start_time = time.monotonic()

    epoch_range = range(start_epoch, trainer_config.epochs)

    if HAS_RICH:
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
        )
        task = progress.add_task("Training", total=trainer_config.epochs - start_epoch)
        progress.start()
    else:
        progress = None

    try:
        for epoch in epoch_range:
            # Train
            train_loss = _train_epoch(
                model, train_loader, loss_fn, optimizer, device,
                trainer_config.gradient_clip, scaler,
            )

            # Validate
            val_loss = _val_epoch(model, val_loader, loss_fn, device)

            # Current LR
            current_lr = optimizer.param_groups[0]["lr"]

            # Step scheduler
            if scheduler is not None:
                if trainer_config.lr_scheduler == "plateau":
                    scheduler.step(val_loss)
                elif trainer_config.lr_scheduler == "cosine":
                    scheduler.step()

            # Log to CSV
            _log_csv(csv_path, epoch, train_loss, val_loss, current_lr)

            # Print progress
            if not HAS_RICH:
                print(
                    f"  Epoch {epoch:>4d}/{trainer_config.epochs}  "
                    f"train_loss={round(train_loss, 4):.4f}  "
                    f"val_loss={round(val_loss, 4):.4f}  "
                    f"lr={current_lr:.2e}"
                )
            else:
                progress.update(task, advance=1, description=(
                    f"Epoch {epoch + 1}/{trainer_config.epochs} | "
                    f"train={round(train_loss, 4):.4f} val={round(val_loss, 4):.4f}"
                ))

            # Track best model
            if val_loss < best_val_loss:
                best_val_loss = round(val_loss, 4)
                best_epoch = epoch
                save_model(
                    model,
                    ckpt_dir / "best_model.pt",
                    config=model_config.model_dump(),
                    metrics={
                        "epoch": epoch,
                        "train_loss": round(train_loss, 4),
                        "val_loss": round(val_loss, 4),
                        "learning_rate": current_lr,
                    },
                )

            # Early stopping
            if stopper.step(val_loss, epoch):
                print(f"\nEarly stopping at epoch {epoch} "
                      f"(no improvement for {trainer_config.patience} epochs)")
                break

    finally:
        if HAS_RICH and progress is not None:
            progress.stop()

    elapsed = time.monotonic() - start_time
    print("-" * 70)
    print(f"Training complete in {elapsed:.1f}s")
    print(f"  Best epoch: {best_epoch} (val_loss={best_val_loss})")

    # ── Load best model for evaluation ────────────────────────────────
    best_ckpt = ckpt_dir / "best_model.pt"
    if best_ckpt.exists():
        checkpoint = torch.load(best_ckpt, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        print(f"  Loaded best checkpoint from: {best_ckpt}")

    # ── Evaluate on test set ──────────────────────────────────────────
    print(f"\nEvaluating on test set ({len(test_ds)} samples)...")
    test_metrics = _evaluate_test_set(model, test_loader, device, metrics_list)

    print("  Test metrics:")
    for name, value in test_metrics.items():
        print(f"    {name}: {value}")

    # Save evaluation metrics
    eval_output_path.parent.mkdir(parents=True, exist_ok=True)
    eval_result = {
        "model": "AffinityMPNN",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "model": model_config.model_dump(),
            "training": trainer_config.model_dump(),
            "data": data_config.model_dump(),
        },
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "test_metrics": test_metrics,
        "dataset_summary": {
            "n_train": len(train_ds),
            "n_val": len(val_ds),
            "n_test": len(test_ds),
        },
        "training_time_seconds": round(elapsed, 2),
    }
    with open(eval_output_path, "w") as f:
        json.dump(eval_result, f, indent=2)
    print(f"\n  Evaluation saved to: {eval_output_path}")

    # ── Save model card ───────────────────────────────────────────────
    card_path = _save_model_card(
        model=model,
        model_config=model_config,
        trainer_config=trainer_config,
        data_config=data_config,
        test_metrics=test_metrics,
        n_train=len(train_ds),
        n_val=len(val_ds),
        n_test=len(test_ds),
        best_epoch=best_epoch,
        output_dir=ckpt_dir,
    )
    print(f"  Model card saved to: {card_path}")

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("MPNN Training Summary")
    print("=" * 70)
    print(f"  Model:       AffinityMPNN ({total_params:,} params)")
    print(f"  Dataset:     {summary['n_samples']} molecules "
          f"(train={len(train_ds)}, val={len(val_ds)}, test={len(test_ds)})")
    print(f"  Best epoch:  {best_epoch} / {trainer_config.epochs}")
    print(f"  Val loss:    {best_val_loss}")
    for name, value in test_metrics.items():
        print(f"  Test {name:>8s}: {value}")
    print(f"  Time:        {elapsed:.1f}s")
    print(f"  Checkpoint:  {ckpt_dir / 'best_model.pt'}")
    print(f"  Log:         {csv_path}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace with config, resume, and data_dir fields.
    """
    parser = argparse.ArgumentParser(
        description="Train an MPNN binding affinity predictor on EGFR data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/train_mpnn.py\n"
            "  python scripts/train_mpnn.py --config configs/mpnn.yaml\n"
            "  python scripts/train_mpnn.py --resume artifacts/models/mpnn/best_model.pt\n"
            "  python scripts/train_mpnn.py --data-dir /scratch/data/\n"
        ),
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/mpnn.yaml",
        help="Path to YAML config file (default: configs/mpnn.yaml)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to checkpoint to resume training from",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Override data directory (replaces dir in config data_path)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    args = _parse_args()
    train_mpnn(
        config_path=args.config,
        resume_path=args.resume,
        data_dir=args.data_dir,
    )
