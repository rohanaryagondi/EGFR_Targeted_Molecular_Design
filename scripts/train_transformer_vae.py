#!/usr/bin/env python3
"""Train the Conditional Transformer VAE for state-conditioned molecular generation.

Implements a custom training loop with KL annealing, word dropout,
free-bits KL regularization, early stopping, checkpoint saving, and
CSV metric logging.

Key differences from train_vae.py:
  - Transformer decoder (not GRU) — no teacher forcing needed
  - Word dropout forces decoder to rely on latent z (anti-collapse)
  - Free-bits KL prevents per-dimension posterior collapse
  - LR warmup before cosine decay (Transformer stability)

Usage:
    python scripts/train_transformer_vae.py --config configs/transformer_vae.yaml
    python scripts/train_transformer_vae.py --config configs/transformer_vae.yaml \\
        --resume artifacts/models/transformer_vae/best_model.pt
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("train_transformer_vae")


# ---------------------------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------------------------


def load_config(config_path: str) -> dict[str, Any]:
    """Load YAML config and return as nested dict."""
    path = Path(config_path)
    if not path.exists():
        logger.error("Config file not found: %s", path)
        sys.exit(1)
    with open(path) as f:
        config: dict[str, Any] = yaml.safe_load(f)
    return config


def resolve_data_paths(
    config: dict[str, Any],
    data_dir: str | None,
) -> tuple[Path, Path]:
    """Resolve training and validation data file paths."""
    data_cfg = config.get("data", {})
    train_path = Path(data_cfg.get("train_path", "data/processed/egfr_smiles_train.json"))
    val_path = Path(data_cfg.get("val_path", "data/processed/egfr_smiles_val.json"))

    if data_dir is not None:
        data_dir_path = Path(data_dir)
        train_path = data_dir_path / train_path.name
        val_path = data_dir_path / val_path.name

    return train_path, val_path


def validate_data_files(train_path: Path, val_path: Path) -> bool:
    """Check that required data files exist."""
    missing: list[str] = []
    if not train_path.exists():
        missing.append(str(train_path))
    if not val_path.exists():
        missing.append(str(val_path))

    if missing:
        print("\n[ERROR] Required data files not found:")
        for p in missing:
            print(f"  - {p}")
        print(
            "\nTo prepare the training data, run:\n"
            "  python scripts/prepare_vae_data.py\n"
        )
        return False
    return True


# ---------------------------------------------------------------------------
# KL annealing
# ---------------------------------------------------------------------------


def compute_kl_weight(
    epoch: int,
    target_weight: float,
    warmup_epochs: int,
    strategy: str = "linear",
) -> float:
    """Compute the KL weight for the current epoch based on annealing schedule."""
    if warmup_epochs <= 0:
        return target_weight

    if strategy == "cyclical":
        cycle_pos = epoch % warmup_epochs
        weight = target_weight * (cycle_pos / warmup_epochs)
    else:
        if epoch >= warmup_epochs:
            weight = target_weight
        else:
            weight = target_weight * (epoch / warmup_epochs)

    return round(weight, 6)


# ---------------------------------------------------------------------------
# Training and validation steps
# ---------------------------------------------------------------------------


def train_one_epoch(
    model: Any,
    loader: Any,
    optimizer: Any,
    kl_weight: float,
    device: Any,
    gradient_clip: float,
    word_dropout: float = 0.3,
    free_bits: float = 0.25,
    scaler: Any | None = None,
) -> dict[str, float]:
    """Run one training epoch and return aggregated losses.

    Parameters
    ----------
    model:
        The :class:`ConditionalTransformerVAE` model.
    loader:
        Training DataLoader yielding ``(tokens, lengths, state_onehots)``.
    optimizer:
        The optimizer.
    kl_weight:
        Current KL weight (from annealing schedule).
    device:
        Torch device.
    gradient_clip:
        Maximum gradient norm for clipping.
    word_dropout:
        Fraction of decoder inputs replaced with ``<unk>`` during training.
    free_bits:
        Minimum KL per latent dimension.
    scaler:
        Optional GradScaler for mixed precision.

    Returns
    -------
    dict[str, float]:
        ``{"total_loss", "recon_loss", "kl_loss"}`` averaged over batches.
    """
    import torch

    from statebind.ml.transformer_vae import transformer_vae_loss

    model.train()
    total_loss_sum = 0.0
    recon_loss_sum = 0.0
    kl_loss_sum = 0.0
    n_batches = 0

    use_amp = scaler is not None

    for tokens, lengths, state_onehots in loader:
        tokens = tokens.to(device)
        lengths = lengths.to(device)
        state_onehots = state_onehots.to(device)

        optimizer.zero_grad()

        if use_amp:
            with torch.amp.autocast("cuda"):
                recon_logits, mu, logvar = model(
                    tokens, lengths, state_onehots,
                    word_dropout=word_dropout,
                )
                # Target is tokens shifted by 1 (next-token prediction)
                target = tokens[:, 1:]
                total, recon, kl = transformer_vae_loss(
                    recon_logits, target, mu, logvar,
                    kl_weight=kl_weight,
                    pad_idx=model.config.pad_idx,
                    free_bits=free_bits,
                )
            scaler.scale(total).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip)
            scaler.step(optimizer)
            scaler.update()
        else:
            recon_logits, mu, logvar = model(
                tokens, lengths, state_onehots,
                word_dropout=word_dropout,
            )
            target = tokens[:, 1:]
            total, recon, kl = transformer_vae_loss(
                recon_logits, target, mu, logvar,
                kl_weight=kl_weight,
                pad_idx=model.config.pad_idx,
                free_bits=free_bits,
            )
            total.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip)
            optimizer.step()

        total_loss_sum += total.item()
        recon_loss_sum += recon.item()
        kl_loss_sum += kl.item()
        n_batches += 1

    denom = max(n_batches, 1)
    return {
        "total_loss": round(total_loss_sum / denom, 4),
        "recon_loss": round(recon_loss_sum / denom, 4),
        "kl_loss": round(kl_loss_sum / denom, 4),
    }


def validate_one_epoch(
    model: Any,
    loader: Any,
    kl_weight: float,
    device: Any,
    free_bits: float = 0.25,
) -> dict[str, float]:
    """Run one validation epoch and return aggregated losses.

    Word dropout is always 0.0 during validation.
    """
    import torch

    from statebind.ml.transformer_vae import transformer_vae_loss

    model.eval()
    total_loss_sum = 0.0
    recon_loss_sum = 0.0
    kl_loss_sum = 0.0
    n_batches = 0

    with torch.no_grad():
        for tokens, lengths, state_onehots in loader:
            tokens = tokens.to(device)
            lengths = lengths.to(device)
            state_onehots = state_onehots.to(device)

            # No word dropout during validation
            recon_logits, mu, logvar = model(
                tokens, lengths, state_onehots, word_dropout=0.0,
            )
            target = tokens[:, 1:]
            total, recon, kl = transformer_vae_loss(
                recon_logits, target, mu, logvar,
                kl_weight=kl_weight,
                pad_idx=model.config.pad_idx,
                free_bits=free_bits,
            )

            total_loss_sum += total.item()
            recon_loss_sum += recon.item()
            kl_loss_sum += kl.item()
            n_batches += 1

    denom = max(n_batches, 1)
    return {
        "total_loss": round(total_loss_sum / denom, 4),
        "recon_loss": round(recon_loss_sum / denom, 4),
        "kl_loss": round(kl_loss_sum / denom, 4),
    }


# ---------------------------------------------------------------------------
# CSV logging
# ---------------------------------------------------------------------------

CSV_HEADER: list[str] = [
    "epoch",
    "kl_weight",
    "train_total_loss",
    "train_recon_loss",
    "train_kl_loss",
    "val_total_loss",
    "val_recon_loss",
    "val_kl_loss",
    "learning_rate",
    "elapsed_seconds",
]


def init_csv_log(path: Path) -> None:
    """Create the CSV log file with headers if it does not already exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)


def append_csv_log(
    path: Path,
    epoch: int,
    kl_weight: float,
    train_metrics: dict[str, float],
    val_metrics: dict[str, float],
    lr: float,
    elapsed: float,
) -> None:
    """Append one row of metrics to the CSV log."""
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            epoch,
            round(kl_weight, 6),
            train_metrics["total_loss"],
            train_metrics["recon_loss"],
            train_metrics["kl_loss"],
            val_metrics["total_loss"],
            val_metrics["recon_loss"],
            val_metrics["kl_loss"],
            round(lr, 8),
            round(elapsed, 2),
        ])


# ---------------------------------------------------------------------------
# Checkpoint and artifact saving
# ---------------------------------------------------------------------------


def save_checkpoint(
    model: Any,
    optimizer: Any,
    epoch: int,
    metrics: dict[str, Any],
    config: dict[str, Any],
    path: Path,
) -> None:
    """Save a full training checkpoint."""
    import torch

    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "epoch": epoch,
        "metrics": metrics,
        "config": config,
        "transformer_vae_config": model.config.model_dump(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    torch.save(checkpoint, path)


def save_model_card(
    config: dict[str, Any],
    vocab_size: int,
    n_parameters: int,
    best_epoch: int,
    best_val_loss: float,
    train_size: int,
    val_size: int,
    checkpoint_dir: Path,
) -> None:
    """Save a model card JSON alongside the checkpoint."""
    from statebind.ml.models import ModelCard

    model_cfg = config.get("model", {})
    card = ModelCard(
        model_name="ConditionalTransformerVAE",
        model_type="transformer_vae",
        description=(
            "Conditional Transformer VAE for EGFR state-conditioned molecular generation. "
            "GRU encoder + Transformer decoder with prefix-token z injection, word dropout, "
            "and free-bits KL regularization. Uses SMILES representation."
        ),
        input_format="SMILES string + EGFR conformational state label",
        output_format="Generated SMILES string",
        training_data=(
            f"ChEMBL EGFR bioactivity (IC50 < 10uM) + known binders, "
            f"N_train={train_size}, N_val={val_size}"
        ),
        n_parameters=n_parameters,
        performance={
            "best_epoch": best_epoch,
            "best_val_loss": round(best_val_loss, 4),
        },
        limitations=[
            "SMILES validity not guaranteed — requires post-filtering with RDKit",
            "Trained on EGFR-specific data only — not a general-purpose generator",
            f"Word dropout={model_cfg.get('word_dropout', 0.3)}, "
            f"free_bits={model_cfg.get('free_bits', 0.25)}",
        ],
        version="0.1.0",
    )

    card_path = checkpoint_dir / "model_card.json"
    with open(card_path, "w") as f:
        f.write(card.model_dump_json(indent=2))

    logger.info("Model card saved to %s", card_path)


def save_vocabulary(vocab: Any, checkpoint_dir: Path) -> None:
    """Save the vocabulary JSON to the checkpoint directory."""
    vocab_path = checkpoint_dir / "vocabulary.json"
    with open(vocab_path, "w") as f:
        f.write(vocab.to_json())
    logger.info("Vocabulary saved to %s (%d tokens)", vocab_path, vocab.size)


def save_final_config(config: dict[str, Any], checkpoint_dir: Path) -> None:
    """Save the final resolved config to the checkpoint directory."""
    config_path = checkpoint_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    logger.info("Final config saved to %s", config_path)


# ---------------------------------------------------------------------------
# Main training pipeline
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: parse args, build components, train, save artifacts."""
    parser = argparse.ArgumentParser(
        description="Train the Conditional Transformer VAE.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/transformer_vae.yaml",
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to checkpoint file to resume training from",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Override data directory (uses filenames from config)",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Setup logging
    # ------------------------------------------------------------------
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ------------------------------------------------------------------
    # Load config
    # ------------------------------------------------------------------
    config = load_config(args.config)
    model_cfg = config.get("model", {})
    train_cfg = config.get("training", {})
    data_cfg = config.get("data", {})
    kl_cfg = config.get("kl_annealing", {})

    # ------------------------------------------------------------------
    # Validate data files exist
    # ------------------------------------------------------------------
    train_path, val_path = resolve_data_paths(config, args.data_dir)
    if not validate_data_files(train_path, val_path):
        sys.exit(1)

    # ------------------------------------------------------------------
    # Check torch availability
    # ------------------------------------------------------------------
    try:
        import torch
        from torch.utils.data import DataLoader
    except ImportError:
        print(
            "\n[ERROR] PyTorch is required but not installed.\n"
            "Install it with: pip install torch\n"
        )
        sys.exit(1)

    from statebind.ml.tokenizer import SMILESTokenizer
    from statebind.ml.transformer_vae import (
        ConditionalTransformerVAE,
        TransformerVAEConfig,
    )
    from statebind.ml.utils import (
        EarlyStopper,
        count_parameters,
        get_device,
        set_seed,
    )
    from statebind.ml.vae_dataset import (
        SMILESDatasetConfig,
        collate_smiles,
        load_smiles_dataset,
    )
    from statebind.ml.vocabulary import build_vocabulary

    # ------------------------------------------------------------------
    # Seed and device
    # ------------------------------------------------------------------
    seed = train_cfg.get("seed", 42)
    set_seed(seed)

    device = get_device(train_cfg.get("device", "auto"))
    logger.info("Using device: %s", device)

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    print("=" * 64)
    print("  Conditional Transformer VAE — Training Pipeline")
    print("=" * 64)
    print(f"  Config:    {args.config}")
    print(f"  Device:    {device}")
    print(f"  Seed:      {seed}")
    print(f"  Train:     {train_path}")
    print(f"  Val:       {val_path}")
    if args.resume:
        print(f"  Resume:    {args.resume}")
    print("=" * 64)

    # ------------------------------------------------------------------
    # Load training data and build vocabulary
    # ------------------------------------------------------------------
    print("\n[1/5] Loading data and building vocabulary...")

    with open(train_path) as f:
        train_records: list[dict[str, str]] = json.load(f)
    with open(val_path) as f:
        val_records: list[dict[str, str]] = json.load(f)

    train_smiles = [r["smiles"] for r in train_records]
    val_smiles = [r["smiles"] for r in val_records]

    tokenizer = SMILESTokenizer()
    all_smiles = train_smiles + val_smiles
    vocab = build_vocabulary(all_smiles, tokenizer)

    actual_vocab_size = vocab.size
    logger.info(
        "Vocabulary built: %d tokens (config specified %d, using actual)",
        actual_vocab_size,
        model_cfg.get("vocab_size", 150),
    )

    # Update config with actual vocab size
    model_cfg["vocab_size"] = actual_vocab_size

    print(f"  Train samples: {len(train_records)}")
    print(f"  Val samples:   {len(val_records)}")
    print(f"  Vocab size:    {actual_vocab_size}")

    # ------------------------------------------------------------------
    # Create datasets and dataloaders
    # ------------------------------------------------------------------
    print("\n[2/5] Building datasets and dataloaders...")

    state_mapping = data_cfg.get("state_mapping", {
        "DFGin_aCin": 0,
        "DFGin_aCout": 1,
        "DFGout_aCin": 2,
    })

    ds_config = SMILESDatasetConfig(
        max_len=data_cfg.get("max_len", 128),
        n_states=model_cfg.get("n_states", 3),
        state_mapping=state_mapping,
    )

    train_dataset = load_smiles_dataset(train_path, tokenizer, vocab, ds_config)
    val_dataset = load_smiles_dataset(val_path, tokenizer, vocab, ds_config)

    batch_size = train_cfg.get("batch_size", 128)
    num_workers = train_cfg.get("num_workers", 4)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        collate_fn=collate_smiles,
        pin_memory=(device.type == "cuda"),
        drop_last=False,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        collate_fn=collate_smiles,
        pin_memory=(device.type == "cuda"),
        drop_last=False,
    )

    print(f"  Train batches: {len(train_loader)}")
    print(f"  Val batches:   {len(val_loader)}")

    # ------------------------------------------------------------------
    # Initialize model
    # ------------------------------------------------------------------
    print("\n[3/5] Initializing model...")

    tvae_config = TransformerVAEConfig(
        vocab_size=actual_vocab_size,
        embed_dim=model_cfg.get("embed_dim", 128),
        latent_dim=model_cfg.get("latent_dim", 64),
        n_states=model_cfg.get("n_states", 3),
        pad_idx=vocab.pad_idx,
        encoder_hidden_dim=model_cfg.get("encoder_hidden_dim", 256),
        encoder_n_layers=model_cfg.get("encoder_n_layers", 2),
        encoder_dropout=model_cfg.get("encoder_dropout", 0.1),
        d_model=model_cfg.get("d_model", 256),
        n_heads=model_cfg.get("n_heads", 4),
        n_decoder_layers=model_cfg.get("n_decoder_layers", 4),
        dim_feedforward=model_cfg.get("dim_feedforward", 512),
        decoder_dropout=model_cfg.get("decoder_dropout", 0.1),
        n_prefix_tokens=model_cfg.get("n_prefix_tokens", 8),
        word_dropout=model_cfg.get("word_dropout", 0.3),
        free_bits=model_cfg.get("free_bits", 0.25),
        kl_weight=model_cfg.get("kl_weight", 0.01),
    )

    model = ConditionalTransformerVAE(tvae_config).to(device)

    total_params, trainable_params = count_parameters(model)
    print(f"  Architecture:  GRU encoder + Transformer decoder (d={tvae_config.d_model})")
    print(f"  Latent dim:    {tvae_config.latent_dim}")
    print(f"  Prefix tokens: {tvae_config.n_prefix_tokens}")
    print(f"  Decoder:       {tvae_config.n_decoder_layers} layers, {tvae_config.n_heads} heads")
    print(f"  Word dropout:  {tvae_config.word_dropout}")
    print(f"  Free bits:     {tvae_config.free_bits}")
    print(f"  Parameters:    {total_params:,} total, {trainable_params:,} trainable")

    # ------------------------------------------------------------------
    # Optimizer and scheduler (with warmup)
    # ------------------------------------------------------------------
    lr = train_cfg.get("learning_rate", 0.0003)
    weight_decay = train_cfg.get("weight_decay", 0.00001)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=lr, weight_decay=weight_decay,
    )

    scheduler_name = train_cfg.get("lr_scheduler", "cosine")
    epochs = train_cfg.get("epochs", 300)
    warmup_epochs = train_cfg.get("lr_warmup_epochs", 10)

    # Linear warmup then cosine decay
    def lr_lambda(epoch: int) -> float:
        if epoch < warmup_epochs:
            return (epoch + 1) / warmup_epochs
        progress = (epoch - warmup_epochs) / max(epochs - warmup_epochs, 1)
        return max(0.5 * (1 + __import__("math").cos(progress * __import__("math").pi)), 1e-7 / lr)

    scheduler: torch.optim.lr_scheduler.LRScheduler
    if scheduler_name == "cosine":
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    elif scheduler_name == "plateau":
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5,
            patience=max(train_cfg.get("patience", 20) // 3, 3),
            min_lr=1e-7,
        )
    else:
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.0)

    # Mixed precision scaler (CUDA only)
    use_amp = train_cfg.get("mixed_precision", False) and device.type == "cuda"
    scaler: torch.amp.GradScaler | None = None
    if use_amp:
        scaler = torch.amp.GradScaler("cuda")
        logger.info("Mixed precision training enabled")

    # Early stopping
    patience = train_cfg.get("patience", 40)
    stopper = EarlyStopper(patience=patience)

    # KL annealing parameters
    kl_target_weight = model_cfg.get("kl_weight", 0.01)
    kl_warmup_epochs = kl_cfg.get("warmup_epochs", 50)
    kl_strategy = kl_cfg.get("strategy", "linear")

    # Anti-collapse parameters
    word_dropout = model_cfg.get("word_dropout", 0.3)
    free_bits = model_cfg.get("free_bits", 0.25)

    # Early stopping target
    early_stop_metric = config.get("early_stop_metric", "val_recon_loss")

    # ------------------------------------------------------------------
    # Resume from checkpoint
    # ------------------------------------------------------------------
    start_epoch = 0
    best_val_loss = float("inf")
    best_epoch = 0

    if args.resume:
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"\n[ERROR] Checkpoint not found: {resume_path}")
            sys.exit(1)

        print(f"\n  Resuming from {resume_path}...")
        checkpoint = torch.load(resume_path, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        start_epoch = checkpoint.get("epoch", 0) + 1
        stored_metrics = checkpoint.get("metrics", {})
        if "val_recon_loss" in stored_metrics:
            best_val_loss = stored_metrics["val_recon_loss"]
            best_epoch = checkpoint.get("epoch", 0)
        elif "val_total_loss" in stored_metrics:
            best_val_loss = stored_metrics["val_total_loss"]
            best_epoch = checkpoint.get("epoch", 0)
        print(f"  Resumed at epoch {start_epoch}, best val loss: {round(best_val_loss, 4)}")

    # ------------------------------------------------------------------
    # Prepare logging directories
    # ------------------------------------------------------------------
    checkpoint_dir = Path(train_cfg.get("checkpoint_dir", "artifacts/models/transformer_vae/"))
    log_dir = Path(train_cfg.get("log_dir", "artifacts/logs/transformer_vae/"))
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    csv_path = log_dir / "training_log.csv"
    init_csv_log(csv_path)

    gradient_clip = train_cfg.get("gradient_clip", 1.0)

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------
    print(f"\n[4/5] Training for up to {epochs} epochs (patience={patience})...")
    print(f"  KL annealing: {kl_strategy}, warmup={kl_warmup_epochs} epochs")
    print(f"  Word dropout: {word_dropout}")
    print(f"  Free bits:    {free_bits}")
    print(f"  LR warmup:    {warmup_epochs} epochs")
    print(f"  Early stop on: {early_stop_metric}")
    print()

    training_start = time.monotonic()

    for epoch in range(start_epoch, epochs):
        epoch_start = time.monotonic()

        # Compute KL weight for this epoch
        kl_weight = compute_kl_weight(
            epoch, kl_target_weight, kl_warmup_epochs, kl_strategy,
        )

        # Train
        train_metrics = train_one_epoch(
            model, train_loader, optimizer, kl_weight, device,
            gradient_clip, word_dropout, free_bits, scaler,
        )

        # Validate
        val_metrics = validate_one_epoch(
            model, val_loader, kl_weight, device, free_bits,
        )

        # Current learning rate
        current_lr = optimizer.param_groups[0]["lr"]

        # Step scheduler
        if scheduler_name == "plateau":
            scheduler.step(val_metrics["total_loss"])
        else:
            scheduler.step()

        # Elapsed time
        elapsed = time.monotonic() - training_start

        # Log to CSV
        append_csv_log(
            csv_path, epoch, kl_weight,
            train_metrics, val_metrics, current_lr, elapsed,
        )

        # Check for best model
        is_best = False
        track_loss = (
            val_metrics["recon_loss"]
            if early_stop_metric == "val_recon_loss"
            else val_metrics["total_loss"]
        )
        if track_loss < best_val_loss:
            best_val_loss = track_loss
            best_epoch = epoch
            is_best = True

            save_checkpoint(
                model, optimizer, epoch,
                {
                    "val_total_loss": val_metrics["total_loss"],
                    "val_recon_loss": val_metrics["recon_loss"],
                    "val_kl_loss": val_metrics["kl_loss"],
                    "train_total_loss": train_metrics["total_loss"],
                },
                config,
                checkpoint_dir / "best_model.pt",
            )

        # Print epoch summary
        epoch_time = time.monotonic() - epoch_start
        best_marker = " *" if is_best else ""

        t_recon = train_metrics['recon_loss']
        t_kl = train_metrics['kl_loss']
        v_recon = val_metrics['recon_loss']
        v_kl = val_metrics['kl_loss']

        print(
            f"  Epoch {epoch:>3d}/{epochs}  |  "
            f"train: {train_metrics['total_loss']:.4f} "
            f"(recon={t_recon:.4f}, kl={t_kl:.4f})  |  "
            f"val: {val_metrics['total_loss']:.4f} "
            f"(recon={v_recon:.4f}, kl={v_kl:.4f})  |  "
            f"kl_w={kl_weight:.4f}  lr={current_lr:.6f}  "
            f"({epoch_time:.1f}s){best_marker}",
            flush=True,
        )

        # Early stopping
        if stopper.step(track_loss, epoch):
            print(f"\n  Early stopping at epoch {epoch} (no improvement for {patience} epochs)")
            break

    total_time = time.monotonic() - training_start

    # ------------------------------------------------------------------
    # Save final artifacts
    # ------------------------------------------------------------------
    print(f"\n[5/5] Saving artifacts to {checkpoint_dir}/...")

    save_vocabulary(vocab, checkpoint_dir)
    save_model_card(
        config=config,
        vocab_size=actual_vocab_size,
        n_parameters=total_params,
        best_epoch=best_epoch,
        best_val_loss=best_val_loss,
        train_size=len(train_dataset),
        val_size=len(val_dataset),
        checkpoint_dir=checkpoint_dir,
    )
    save_final_config(config, checkpoint_dir)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 64)
    print("  Training Complete")
    print("=" * 64)
    print(f"  Total time:      {total_time:.1f}s ({total_time / 60:.1f} min)")
    print(f"  Best epoch:      {best_epoch}")
    print(f"  Best val loss:   {round(best_val_loss, 4)}")
    print(f"  Vocab size:      {actual_vocab_size}")
    print(f"  Parameters:      {total_params:,}")
    print(f"  Checkpoint:      {checkpoint_dir / 'best_model.pt'}")
    print(f"  Training log:    {csv_path}")
    print("=" * 64)


if __name__ == "__main__":
    main()
