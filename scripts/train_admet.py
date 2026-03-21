#!/usr/bin/env python3
"""Train the multi-task ADMET predictor.

Loads molecular ADMET data, builds a GNN-based multi-task model, trains with
per-task loss weighting and NaN masking, evaluates on held-out test data, and
saves a model card with per-task performance metrics.

Usage:
    python scripts/train_admet.py
    python scripts/train_admet.py --config configs/admet.yaml
    python scripts/train_admet.py --resume artifacts/models/admet/best_model.pt
    python scripts/train_admet.py --data-dir data/processed/
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

# ---------------------------------------------------------------------------
# Optional rich progress bars
# ---------------------------------------------------------------------------

try:
    from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ---------------------------------------------------------------------------
# Optional sklearn for AUROC
# ---------------------------------------------------------------------------

try:
    from sklearn.metrics import roc_auc_score

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train multi-task ADMET predictor with shared GNN backbone.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/admet.yaml",
        help="Path to YAML config file (default: configs/admet.yaml)",
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
        help="Override data directory (replaces parent dir of data.data_path)",
    )
    return parser.parse_args()


def _load_config(path: str) -> dict[str, Any]:
    """Load and return YAML configuration.

    Args:
        path: Path to the YAML config file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# CSV logger
# ---------------------------------------------------------------------------


class _CSVLogger:
    """Minimal CSV logger for per-epoch training metrics."""

    def __init__(self, path: Path, task_names: list[str]) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.task_names = task_names
        # Write header
        header = ["epoch", "train_loss", "val_loss", "learning_rate"]
        header += [f"train_{t}" for t in task_names]
        header += [f"val_{t}" for t in task_names]
        with open(self.path, "w", newline="") as f:
            csv.writer(f).writerow(header)

    def log(
        self,
        epoch: int,
        train_loss: float,
        val_loss: float | None,
        lr: float,
        train_per_task: dict[str, float],
        val_per_task: dict[str, float],
    ) -> None:
        """Append one row of metrics."""
        row: list[Any] = [epoch, round(train_loss, 4)]
        row.append(round(val_loss, 4) if val_loss is not None else "")
        row.append(lr)
        for t in self.task_names:
            row.append(round(train_per_task.get(t, 0.0), 4))
        for t in self.task_names:
            row.append(round(val_per_task.get(t, 0.0), 4))
        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow(row)


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------


def _run_epoch(
    model: Any,
    loader: Any,
    task_names: list[str],
    task_types: dict[str, str],
    task_weights: dict[str, float],
    device: Any,
    optimizer: Any | None = None,
    gradient_clip: float = 1.0,
    scaler: Any | None = None,
) -> tuple[float, dict[str, float]]:
    """Run one training or validation epoch.

    Args:
        model: The MultiTaskADMET model.
        loader: PyG DataLoader yielding Batch objects.
        task_names: Ordered list of task endpoint names.
        task_types: Mapping of task name to 'regression' or 'classification'.
        task_weights: Per-task loss weights.
        device: Torch device.
        optimizer: Optimizer (None for validation — model runs in eval mode).
        gradient_clip: Max gradient norm for clipping.
        scaler: AMP GradScaler (None to disable mixed precision).

    Returns:
        Tuple of (mean_total_loss, per_task_mean_losses).
    """
    import torch

    from statebind.ml.admet import admet_loss

    is_train = optimizer is not None
    if is_train:
        model.train()
    else:
        model.eval()

    total_loss_accum = 0.0
    per_task_accum: dict[str, float] = {t: 0.0 for t in task_names}
    n_batches = 0

    context = torch.no_grad() if not is_train else _nullcontext()

    with context:
        for batch in loader:
            batch = batch.to(device)
            predictions = model(batch)

            # Build target tensor from batch.y — shape (batch_size, n_tasks)
            targets = batch.y
            if targets.dim() == 1:
                # Single task or flat — reshape
                targets = targets.view(-1, len(task_names))

            use_amp = scaler is not None
            if is_train:
                optimizer.zero_grad()

                if use_amp:
                    with torch.amp.autocast("cuda"):
                        loss, per_task = admet_loss(
                            predictions, targets, task_types, task_names, task_weights
                        )
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        model.parameters(), gradient_clip
                    )
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss, per_task = admet_loss(
                        predictions, targets, task_types, task_names, task_weights
                    )
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(
                        model.parameters(), gradient_clip
                    )
                    optimizer.step()
            else:
                loss, per_task = admet_loss(
                    predictions, targets, task_types, task_names, task_weights
                )

            total_loss_accum += loss.item()
            for t in task_names:
                if t in per_task:
                    per_task_accum[t] += per_task[t].item()
            n_batches += 1

    denom = max(n_batches, 1)
    mean_loss = total_loss_accum / denom
    per_task_mean = {t: per_task_accum[t] / denom for t in task_names}

    return mean_loss, per_task_mean


class _nullcontext:
    """Minimal no-op context manager (avoids 3.6 compat issues)."""

    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Test evaluation
# ---------------------------------------------------------------------------


def _evaluate_test(
    model: Any,
    loader: Any,
    task_names: list[str],
    task_types: dict[str, str],
    device: Any,
) -> dict[str, dict[str, float]]:
    """Evaluate the model on the test set and compute per-task metrics.

    Regression tasks: RMSE, MAE, R-squared.
    Classification tasks: accuracy, AUROC (if sklearn is available).

    Args:
        model: Trained MultiTaskADMET model.
        loader: PyG DataLoader for the test split.
        task_names: Ordered list of task endpoint names.
        task_types: Mapping of task name to type.
        device: Torch device.

    Returns:
        Dictionary mapping task name to a dict of metric name -> value.
    """
    import torch

    model.eval()

    # Collect predictions and targets per task
    all_preds: dict[str, list[float]] = {t: [] for t in task_names}
    all_targets: dict[str, list[float]] = {t: [] for t in task_names}

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            predictions = model(batch)

            targets = batch.y
            if targets.dim() == 1:
                targets = targets.view(-1, len(task_names))

            for i, name in enumerate(task_names):
                if name not in predictions:
                    continue

                pred = predictions[name].squeeze(-1).cpu()
                target_col = targets[:, i].cpu()

                # Only keep non-NaN entries
                valid_mask = ~torch.isnan(target_col)
                if valid_mask.sum() == 0:
                    continue

                pred_valid = pred[valid_mask].numpy()
                target_valid = target_col[valid_mask].numpy()

                # For classification, apply sigmoid to raw logits
                if task_types.get(name) == "classification":
                    pred_probs = 1.0 / (1.0 + np.exp(-pred_valid))
                    all_preds[name].extend(pred_probs.tolist())
                else:
                    all_preds[name].extend(pred_valid.tolist())
                all_targets[name].extend(target_valid.tolist())

    # Compute metrics
    results: dict[str, dict[str, float]] = {}

    for name in task_names:
        preds = np.array(all_preds[name])
        targets_arr = np.array(all_targets[name])

        if len(preds) == 0:
            results[name] = {"n_samples": 0}
            continue

        metrics: dict[str, float] = {"n_samples": float(len(preds))}

        if task_types.get(name) == "regression":
            # RMSE
            mse = float(np.mean((preds - targets_arr) ** 2))
            metrics["rmse"] = round(math.sqrt(mse), 4)
            # MAE
            metrics["mae"] = round(float(np.mean(np.abs(preds - targets_arr))), 4)
            # R-squared
            ss_res = float(np.sum((targets_arr - preds) ** 2))
            ss_tot = float(np.sum((targets_arr - np.mean(targets_arr)) ** 2))
            if ss_tot > 0:
                metrics["r2"] = round(1.0 - ss_res / ss_tot, 4)
            else:
                metrics["r2"] = 0.0
        else:
            # Classification
            pred_binary = (preds >= 0.5).astype(float)
            metrics["accuracy"] = round(
                float(np.mean(pred_binary == targets_arr)), 4
            )

            if HAS_SKLEARN:
                try:
                    # AUROC requires both classes present
                    if len(np.unique(targets_arr)) > 1:
                        metrics["auroc"] = round(
                            float(roc_auc_score(targets_arr, preds)), 4
                        )
                    else:
                        metrics["auroc"] = float("nan")
                except ValueError:
                    metrics["auroc"] = float("nan")
            else:
                metrics["auroc_note"] = "sklearn not installed — AUROC skipped"

        results[name] = metrics

    return results


# ---------------------------------------------------------------------------
# Model card
# ---------------------------------------------------------------------------


def _build_model_card(
    config: dict[str, Any],
    n_parameters: int,
    test_metrics: dict[str, dict[str, float]],
) -> dict[str, Any]:
    """Build a model card dictionary for the trained ADMET model.

    Args:
        config: Full YAML configuration dict.
        n_parameters: Total number of model parameters.
        test_metrics: Per-task test set evaluation results.

    Returns:
        Serializable model card dictionary.
    """
    # Flatten performance into a single dict
    performance: dict[str, float] = {}
    for task_name, metrics in test_metrics.items():
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and not math.isnan(value):
                performance[f"{task_name}_{metric_name}"] = round(value, 4)

    return {
        "model_name": "MultiTaskADMET",
        "model_type": "admet",
        "description": (
            "Multi-task ADMET predictor with shared GIN backbone and "
            "task-specific heads. Predicts Caco-2 permeability, hERG inhibition, "
            "CYP3A4 inhibition, hepatic clearance, lipophilicity, and solubility."
        ),
        "input_format": "PyG Data object (molecular graph from SMILES)",
        "output_format": "dict[str, float] — per-task predictions",
        "training_data": config.get("data", {}).get("data_path", "unknown"),
        "n_parameters": n_parameters,
        "performance": performance,
        "limitations": [
            "Docking-based validation not yet performed",
            "Multi-task labels may be sparse — NaN-masked loss used",
            "No external validation set beyond random split",
        ],
        "version": "0.1.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
    }


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------


def _print_summary(
    task_names: list[str],
    task_types: dict[str, str],
    test_metrics: dict[str, dict[str, float]],
    best_epoch: int,
    best_val_loss: float,
    total_time: float,
) -> None:
    """Print a human-readable summary table of training results."""
    print("\n" + "=" * 70)
    print("ADMET Training Summary")
    print("=" * 70)
    print(f"  Best epoch:     {best_epoch}")
    print(f"  Best val loss:  {round(best_val_loss, 4)}")
    print(f"  Training time:  {total_time:.1f}s ({total_time / 60:.1f}m)")

    print(f"\n  {'Task':<16} {'Type':<16} ", end="")
    # Determine columns based on task types
    print(f"{'Metric 1':>12} {'Metric 2':>12} {'Metric 3':>12} {'N':>8}")
    print("  " + "-" * 76)

    for name in task_names:
        ttype = task_types.get(name, "regression")
        metrics = test_metrics.get(name, {})
        n_samples = int(metrics.get("n_samples", 0))

        if ttype == "regression":
            rmse = metrics.get("rmse", float("nan"))
            mae = metrics.get("mae", float("nan"))
            r2 = metrics.get("r2", float("nan"))
            print(
                f"  {name:<16} {ttype:<16} "
                f"{'RMSE=' + str(rmse):>12} "
                f"{'MAE=' + str(mae):>12} "
                f"{'R2=' + str(r2):>12} "
                f"{n_samples:>8}"
            )
        else:
            acc = metrics.get("accuracy", float("nan"))
            auroc = metrics.get("auroc", float("nan"))
            auroc_str = str(auroc) if not math.isnan(auroc) else "n/a"
            print(
                f"  {name:<16} {ttype:<16} "
                f"{'Acc=' + str(acc):>12} "
                f"{'AUROC=' + auroc_str:>12} "
                f"{'':>12} "
                f"{n_samples:>8}"
            )

    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for ADMET training pipeline."""
    args = _parse_args()

    # ------------------------------------------------------------------
    # 1. Load config
    # ------------------------------------------------------------------
    config = _load_config(args.config)
    model_cfg = config.get("model", {})
    train_cfg = config.get("training", {})
    data_cfg = config.get("data", {})
    eval_cfg = config.get("evaluation", {})
    weight_cfg = config.get("task_weights", {})

    task_names: list[str] = model_cfg.get("task_names", [])
    task_types: dict[str, str] = model_cfg.get("task_types", {})
    task_weights: dict[str, float] = {
        t: float(weight_cfg.get(t, 1.0)) for t in task_names
    }

    seed = train_cfg.get("seed", 42)
    epochs = train_cfg.get("epochs", 150)
    batch_size = train_cfg.get("batch_size", 64)
    learning_rate = train_cfg.get("learning_rate", 0.001)
    weight_decay = train_cfg.get("weight_decay", 1e-5)
    patience = train_cfg.get("patience", 20)
    gradient_clip = train_cfg.get("gradient_clip", 1.0)
    device_pref = train_cfg.get("device", "auto")
    checkpoint_dir = Path(train_cfg.get("checkpoint_dir", "artifacts/models/admet/"))
    log_dir = Path(train_cfg.get("log_dir", "artifacts/logs/admet/"))
    num_workers = train_cfg.get("num_workers", 4)
    mixed_precision = train_cfg.get("mixed_precision", False)
    lr_scheduler_type = train_cfg.get("lr_scheduler", "cosine")

    # Override data path if --data-dir provided
    data_path = data_cfg.get("data_path", "data/processed/admet_combined.json")
    if args.data_dir is not None:
        data_path = str(Path(args.data_dir) / Path(data_path).name)

    print("=" * 60)
    print("Multi-Task ADMET Predictor — Training Pipeline")
    print("=" * 60)
    print(f"  Config:      {args.config}")
    print(f"  Data:        {data_path}")
    print(f"  Tasks:       {', '.join(task_names)}")
    print(f"  Epochs:      {epochs}")
    print(f"  Batch size:  {batch_size}")
    print(f"  LR:          {learning_rate}")
    print(f"  Scheduler:   {lr_scheduler_type}")
    print(f"  Patience:    {patience}")
    if args.resume:
        print(f"  Resume from: {args.resume}")

    # ------------------------------------------------------------------
    # 2. Import torch dependencies (late import for graceful failure)
    # ------------------------------------------------------------------
    try:
        import torch
        from torch_geometric.loader import DataLoader
    except ImportError as e:
        print(f"\nERROR: Missing required dependency: {e}")
        print("Install with: pip install torch torch_geometric")
        sys.exit(1)

    from statebind.ml.admet import ADMETConfig, MultiTaskADMET
    from statebind.ml.admet_dataset import (
        ADMETDatasetConfig,
        load_admet_dataset,
        split_admet_dataset,
    )
    from statebind.ml.utils import (
        EarlyStopper,
        count_parameters,
        get_device,
        save_model,
        set_seed,
    )

    # ------------------------------------------------------------------
    # 3. Setup
    # ------------------------------------------------------------------
    set_seed(seed)
    device = get_device(device_pref)
    print(f"  Device:      {device}")

    # ------------------------------------------------------------------
    # 4. Load and split dataset
    # ------------------------------------------------------------------
    data_file = Path(data_path)
    if not data_file.exists():
        print(f"\nERROR: Data file not found: {data_file}")
        print(
            "Run the data preparation pipeline first, or provide a valid "
            "--data-dir path."
        )
        sys.exit(1)

    ds_config = ADMETDatasetConfig(
        data_path=str(data_file),
        task_names=task_names,
        train_frac=float(data_cfg.get("train_ratio", 0.8)),
        val_frac=float(data_cfg.get("val_ratio", 0.1)),
        test_frac=float(data_cfg.get("test_ratio", 0.1)),
        seed=seed,
        min_tasks=int(data_cfg.get("min_tasks", 1)),
    )

    print("\nLoading dataset...")
    dataset = load_admet_dataset(data_file, ds_config)
    train_ds, val_ds, test_ds = split_admet_dataset(dataset, ds_config)
    print(f"  Train: {len(train_ds)}  Val: {len(val_ds)}  Test: {len(test_ds)}")

    # Label coverage
    coverage = dataset.label_coverage()
    for t, cov in coverage.items():
        print(f"    {t:<16} coverage: {cov:.1%}")

    # ------------------------------------------------------------------
    # 5. Create DataLoaders
    # ------------------------------------------------------------------
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        drop_last=False,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        drop_last=False,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        drop_last=False,
    )

    # ------------------------------------------------------------------
    # 6. Initialize model
    # ------------------------------------------------------------------
    admet_config = ADMETConfig(
        atom_feature_dim=model_cfg.get("atom_feature_dim", 35),
        bond_feature_dim=model_cfg.get("bond_feature_dim", 11),
        hidden_dim=model_cfg.get("hidden_dim", 128),
        n_gnn_layers=model_cfg.get("n_gnn_layers", 3),
        dropout=model_cfg.get("dropout", 0.2),
        gnn_type=model_cfg.get("gnn_type", "gin"),
        task_names=task_names,
        task_types=task_types,
    )

    model = MultiTaskADMET(admet_config).to(device)
    total_params, trainable_params = count_parameters(model)
    print(f"\nModel: {total_params:,} parameters ({trainable_params:,} trainable)")

    # ------------------------------------------------------------------
    # 7. Optimizer, scheduler, early stopping
    # ------------------------------------------------------------------
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )

    scheduler: torch.optim.lr_scheduler.LRScheduler | None = None
    if lr_scheduler_type == "cosine":
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs, eta_min=1e-7
        )
    elif lr_scheduler_type == "plateau":
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=0.5,
            patience=max(patience // 3, 3),
            min_lr=1e-7,
        )

    stopper = EarlyStopper(patience=patience)

    # AMP scaler (CUDA only)
    scaler: torch.amp.GradScaler | None = None
    if mixed_precision and device.type == "cuda":
        scaler = torch.amp.GradScaler("cuda")

    # Resume from checkpoint
    start_epoch = 0
    if args.resume:
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"\nWARNING: Checkpoint not found: {resume_path} — training from scratch")
        else:
            checkpoint = torch.load(
                resume_path, map_location=device, weights_only=False
            )
            model.load_state_dict(checkpoint["model_state_dict"])
            if checkpoint.get("metrics") and checkpoint["metrics"].get("epoch") is not None:
                start_epoch = checkpoint["metrics"]["epoch"] + 1
            print(f"  Resumed from epoch {start_epoch}")

    # ------------------------------------------------------------------
    # 8. Logging
    # ------------------------------------------------------------------
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    csv_logger = _CSVLogger(log_dir / "training_log.csv", task_names)

    # ------------------------------------------------------------------
    # 9. Training loop
    # ------------------------------------------------------------------
    print(f"\nTraining for up to {epochs} epochs (patience={patience})...\n")

    best_val_loss = float("inf")
    best_epoch = 0
    start_time = time.monotonic()

    # Choose progress display
    epoch_iter: Any
    if HAS_RICH:
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        progress.start()
        task_id = progress.add_task("Training", total=epochs - start_epoch)
        epoch_iter = range(start_epoch, epochs)
    else:
        progress = None
        task_id = None
        epoch_iter = range(start_epoch, epochs)

    try:
        for epoch in epoch_iter:
            # --- Train ---
            train_loss, train_per_task = _run_epoch(
                model=model,
                loader=train_loader,
                task_names=task_names,
                task_types=task_types,
                task_weights=task_weights,
                device=device,
                optimizer=optimizer,
                gradient_clip=gradient_clip,
                scaler=scaler,
            )

            # --- Validate ---
            val_loss, val_per_task = _run_epoch(
                model=model,
                loader=val_loader,
                task_names=task_names,
                task_types=task_types,
                task_weights=task_weights,
                device=device,
                optimizer=None,
            )

            # --- LR scheduling ---
            current_lr = optimizer.param_groups[0]["lr"]
            if scheduler is not None:
                if lr_scheduler_type == "plateau":
                    scheduler.step(val_loss)
                elif lr_scheduler_type == "cosine":
                    scheduler.step()

            # --- Logging ---
            csv_logger.log(
                epoch=epoch,
                train_loss=train_loss,
                val_loss=val_loss,
                lr=current_lr,
                train_per_task={t: v for t, v in train_per_task.items()},
                val_per_task={t: v for t, v in val_per_task.items()},
            )

            # Console output (every 10 epochs or first/last)
            if epoch % 10 == 0 or epoch == start_epoch or epoch == epochs - 1:
                if not HAS_RICH:
                    print(
                        f"  Epoch {epoch:>4d}/{epochs}  "
                        f"train={round(train_loss, 4):<8}  "
                        f"val={round(val_loss, 4):<8}  "
                        f"lr={current_lr:.2e}"
                    )

            # --- Best model checkpoint ---
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch
                save_model(
                    model,
                    checkpoint_dir / "best_model.pt",
                    config=config,
                    metrics={
                        "epoch": epoch,
                        "train_loss": round(train_loss, 4),
                        "val_loss": round(val_loss, 4),
                        "learning_rate": current_lr,
                    },
                )

            # --- Early stopping ---
            if stopper.step(val_loss, epoch):
                print(f"\n  Early stopping at epoch {epoch} "
                      f"(no improvement for {patience} epochs)")
                break

            # Update rich progress
            if progress is not None and task_id is not None:
                progress.update(
                    task_id,
                    advance=1,
                    description=(
                        f"Epoch {epoch + 1}/{epochs} | "
                        f"train={round(train_loss, 4)} val={round(val_loss, 4)}"
                    ),
                )
    finally:
        if progress is not None:
            progress.stop()

    total_time = time.monotonic() - start_time

    # Save final checkpoint
    save_model(
        model,
        checkpoint_dir / "final_model.pt",
        config=config,
        metrics={
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "val_loss": round(val_loss, 4),
            "best_epoch": best_epoch,
            "best_val_loss": round(best_val_loss, 4),
            "total_time_seconds": round(total_time, 2),
        },
    )

    print(f"\n  Best model saved at epoch {best_epoch} "
          f"(val_loss={round(best_val_loss, 4)})")

    # ------------------------------------------------------------------
    # 10. Test evaluation
    # ------------------------------------------------------------------
    print("\nEvaluating on test set...")

    # Load best model for evaluation
    best_ckpt = checkpoint_dir / "best_model.pt"
    if best_ckpt.exists():
        checkpoint = torch.load(best_ckpt, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])

    test_metrics = _evaluate_test(
        model=model,
        loader=test_loader,
        task_names=task_names,
        task_types=task_types,
        device=device,
    )

    # Save evaluation metrics
    eval_output_path = Path(eval_cfg.get("output_path", "artifacts/evaluation/admet_metrics.json"))
    eval_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(eval_output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "best_epoch": best_epoch,
                "best_val_loss": round(best_val_loss, 4),
                "total_time_seconds": round(total_time, 2),
                "per_task_metrics": test_metrics,
            },
            f,
            indent=2,
        )
    print(f"  Metrics saved to {eval_output_path}")

    # ------------------------------------------------------------------
    # 11. Model card
    # ------------------------------------------------------------------
    model_card = _build_model_card(config, total_params, test_metrics)
    card_path = checkpoint_dir / "model_card.json"
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(model_card, f, indent=2)
    print(f"  Model card saved to {card_path}")

    # ------------------------------------------------------------------
    # 12. Print summary table
    # ------------------------------------------------------------------
    _print_summary(
        task_names=task_names,
        task_types=task_types,
        test_metrics=test_metrics,
        best_epoch=best_epoch,
        best_val_loss=best_val_loss,
        total_time=total_time,
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
