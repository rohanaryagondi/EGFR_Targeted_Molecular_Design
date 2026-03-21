"""Generic PyTorch training loop with checkpointing, early stopping, and logging.

Provides a reusable Trainer class that handles:
- Training loop with gradient clipping
- Validation loop
- LR scheduling (cosine annealing, reduce-on-plateau)
- Early stopping
- Checkpoint saving/loading (best + periodic)
- CSV logging of metrics
- Seed management
- Resume from checkpoint support
- Mixed precision training (optional)
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from statebind.ml.models import TrainerConfig, TrainingHistory, TrainingMetrics
from statebind.ml.utils import EarlyStopper, get_device, save_model, set_seed


def _require_torch() -> None:
    """Raise RuntimeError if torch is not installed."""
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for the Trainer but is not installed. "
            "Install it with: pip install torch"
        )


class Trainer:
    """Generic PyTorch model trainer.

    Handles the full training lifecycle: optimizer setup, LR scheduling,
    gradient clipping, early stopping, checkpoint management, mixed-precision
    training, and CSV metric logging.

    Usage::

        config = TrainerConfig(epochs=100, learning_rate=1e-3)
        trainer = Trainer(config)
        history = trainer.fit(model, train_loader, val_loader, loss_fn)

    The trainer does **not** own the model or data — it orchestrates the
    loop and returns a :class:`TrainingHistory` record of everything that
    happened.
    """

    def __init__(self, config: TrainerConfig) -> None:
        _require_torch()
        self.config = config
        self.device: torch.device = get_device(config.device)
        self.history = TrainingHistory(config=config)
        self._csv_path: Path | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader | None = None,
        loss_fn: nn.Module | None = None,
        optimizer: torch.optim.Optimizer | None = None,
    ) -> TrainingHistory:
        """Train the model.

        If *optimizer* is ``None``, uses AdamW with ``config.learning_rate``
        and ``config.weight_decay``.  If *loss_fn* is ``None``, uses
        ``nn.MSELoss()``.

        Args:
            model: The PyTorch model to train (moved to ``self.device``).
            train_loader: Training data loader.
            val_loader: Optional validation data loader.
            loss_fn: Loss function (default: ``nn.MSELoss()``).
            optimizer: Optimizer (default: AdamW).

        Returns:
            :class:`TrainingHistory` with per-epoch metrics and timing.
        """
        _require_torch()

        # --- Setup --------------------------------------------------------
        set_seed(self.config.seed)
        model = model.to(self.device)

        if loss_fn is None:
            loss_fn = nn.MSELoss()

        if optimizer is None:
            optimizer = torch.optim.AdamW(
                model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay,
            )

        scheduler = self._get_scheduler(optimizer)
        stopper = EarlyStopper(patience=self.config.patience)

        # Mixed precision scaler (only for CUDA)
        use_amp = self.config.mixed_precision and self.device.type == "cuda"
        scaler: torch.amp.GradScaler | None = None
        if use_amp:
            scaler = torch.amp.GradScaler("cuda")

        # Prepare log directory and CSV file
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        self._csv_path = log_dir / "training_log.csv"
        self._init_csv()

        # Prepare checkpoint directory
        ckpt_dir = Path(self.config.checkpoint_dir)
        ckpt_dir.mkdir(parents=True, exist_ok=True)

        # --- Training loop ------------------------------------------------
        start_time = time.monotonic()
        start_epoch = 0

        # If history already has metrics (from resume), start from there
        if self.history.metrics:
            start_epoch = self.history.metrics[-1].epoch + 1

        for epoch in range(start_epoch, self.config.epochs):
            train_loss = self._train_epoch(
                model, train_loader, loss_fn, optimizer, scaler
            )

            val_loss: float | None = None
            if val_loader is not None:
                val_loss = self._val_epoch(model, val_loader, loss_fn)

            # Current learning rate
            current_lr = optimizer.param_groups[0]["lr"]

            # Step scheduler
            if scheduler is not None:
                if self.config.lr_scheduler == "plateau" and val_loss is not None:
                    scheduler.step(val_loss)
                elif self.config.lr_scheduler == "cosine":
                    scheduler.step()

            # Record metrics
            metrics = TrainingMetrics(
                epoch=epoch,
                train_loss=round(train_loss, 4),
                val_loss=round(val_loss, 4) if val_loss is not None else None,
                learning_rate=current_lr,
            )
            self.history.metrics.append(metrics)
            self._log_metrics(metrics)

            # Track best model (by val_loss, or train_loss if no val set)
            monitor_loss = val_loss if val_loss is not None else train_loss
            if monitor_loss < self.history.best_val_loss:
                self.history.best_val_loss = round(monitor_loss, 4)
                self.history.best_epoch = epoch
                # Save best checkpoint
                save_model(
                    model,
                    ckpt_dir / "best_model.pt",
                    config=self.config.model_dump(),
                    metrics=metrics.model_dump(),
                )

            # Early stopping
            if val_loss is not None and stopper.step(val_loss, epoch):
                break

        elapsed = time.monotonic() - start_time
        self.history.total_time_seconds = round(elapsed, 2)

        return self.history

    def resume(self, model: nn.Module, checkpoint_path: Path | str) -> int:
        """Resume training from a checkpoint.

        Loads the model state dict and restores the training history from
        the checkpoint's stored metrics.  The caller should then call
        :meth:`fit` which will continue from the next epoch.

        Args:
            model: A model instance whose architecture matches the saved
                state dict.
            checkpoint_path: Path to a checkpoint produced by :func:`save_model`.

        Returns:
            The epoch number to resume from (i.e. ``last_epoch + 1``).

        Raises:
            FileNotFoundError: If *checkpoint_path* does not exist.
            RuntimeError: If torch is not installed.
        """
        _require_torch()

        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        checkpoint = torch.load(
            checkpoint_path, map_location=self.device, weights_only=False
        )
        model.load_state_dict(checkpoint["model_state_dict"])

        # Restore history from checkpoint metrics if available
        if checkpoint.get("metrics"):
            stored = checkpoint["metrics"]
            epoch = stored.get("epoch", 0)
            restored = TrainingMetrics(
                epoch=epoch,
                train_loss=stored.get("train_loss", 0.0),
                val_loss=stored.get("val_loss"),
                learning_rate=stored.get("learning_rate", self.config.learning_rate),
            )
            self.history.metrics = [restored]
            self.history.best_epoch = epoch
            if restored.val_loss is not None:
                self.history.best_val_loss = restored.val_loss
            return epoch + 1

        return 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _train_epoch(
        self,
        model: nn.Module,
        loader: DataLoader,
        loss_fn: nn.Module,
        optimizer: torch.optim.Optimizer,
        scaler: torch.amp.GradScaler | None,
    ) -> float:
        """Run one training epoch. Returns mean loss."""
        model.train()
        total_loss = 0.0
        n_batches = 0

        use_amp = scaler is not None

        for batch in loader:
            # Support both (x, y) tuples and single tensors
            if isinstance(batch, (list, tuple)) and len(batch) >= 2:
                x, y = batch[0], batch[1]
                x = x.to(self.device)
                y = y.to(self.device)
            else:
                x = batch.to(self.device) if hasattr(batch, "to") else batch
                y = x  # autoencoder / reconstruction mode

            optimizer.zero_grad()

            if use_amp:
                with torch.amp.autocast("cuda"):
                    pred = model(x)
                    loss = loss_fn(pred, y)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), self.config.gradient_clip
                )
                scaler.step(optimizer)
                scaler.update()
            else:
                pred = model(x)
                loss = loss_fn(pred, y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), self.config.gradient_clip
                )
                optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        return total_loss / max(n_batches, 1)

    def _val_epoch(
        self,
        model: nn.Module,
        loader: DataLoader,
        loss_fn: nn.Module,
    ) -> float:
        """Run one validation epoch. Returns mean loss."""
        model.eval()
        total_loss = 0.0
        n_batches = 0

        with torch.no_grad():
            for batch in loader:
                if isinstance(batch, (list, tuple)) and len(batch) >= 2:
                    x, y = batch[0], batch[1]
                    x = x.to(self.device)
                    y = y.to(self.device)
                else:
                    x = batch.to(self.device) if hasattr(batch, "to") else batch
                    y = x

                pred = model(x)
                loss = loss_fn(pred, y)
                total_loss += loss.item()
                n_batches += 1

        return total_loss / max(n_batches, 1)

    def _get_scheduler(
        self, optimizer: torch.optim.Optimizer
    ) -> torch.optim.lr_scheduler.LRScheduler | None:
        """Create LR scheduler based on config.

        Returns ``None`` if ``config.lr_scheduler`` is ``"none"``.
        """
        if self.config.lr_scheduler == "cosine":
            return torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=self.config.epochs, eta_min=1e-7
            )
        if self.config.lr_scheduler == "plateau":
            return torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer,
                mode="min",
                factor=0.5,
                patience=max(self.config.patience // 3, 3),
                min_lr=1e-7,
            )
        return None

    def _init_csv(self) -> None:
        """Write CSV header if the log file doesn't exist yet."""
        if self._csv_path is None:
            return
        if not self._csv_path.exists():
            with open(self._csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["epoch", "train_loss", "val_loss", "learning_rate"])

    def _log_metrics(self, metrics: TrainingMetrics) -> None:
        """Append metrics to CSV log."""
        if self._csv_path is None:
            return
        with open(self._csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                metrics.epoch,
                metrics.train_loss,
                metrics.val_loss if metrics.val_loss is not None else "",
                metrics.learning_rate,
            ])
