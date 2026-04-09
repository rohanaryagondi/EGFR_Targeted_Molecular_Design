#!/usr/bin/env python3
"""Train the Conditional SMILES VAE for state-conditioned molecular generation.

Implements a custom training loop with KL annealing, early stopping,
checkpoint saving, and CSV metric logging.  The generic Trainer is
intentionally *not* used because the VAE requires per-step KL weight
scheduling and a composite loss function (reconstruction + KL divergence).

Usage:
    python scripts/train_vae.py --config configs/vae.yaml
    python scripts/train_vae.py --config configs/vae.yaml \\
        --resume artifacts/models/vae/best_model.pt
    python scripts/train_vae.py --config configs/vae.yaml --data-dir /scratch/egfr/
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

# ---------------------------------------------------------------------------
# Optional rich progress bars — fall back to plain logging
# ---------------------------------------------------------------------------

try:
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
    )

    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None  # type: ignore[assignment]

logger = logging.getLogger("train_vae")


# ---------------------------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------------------------


def load_config(config_path: str) -> dict[str, Any]:
    """Load YAML config and return as nested dict.

    Parameters
    ----------
    config_path:
        Path to the YAML configuration file.

    Returns
    -------
    dict[str, Any]:
        Parsed configuration dictionary.
    """
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
    """Resolve training and validation data file paths.

    If *data_dir* is provided, it overrides the directory portion of the
    paths specified in the config while keeping the filenames.

    Parameters
    ----------
    config:
        The full parsed YAML config.
    data_dir:
        Optional override for the data directory.

    Returns
    -------
    tuple[Path, Path]:
        ``(train_path, val_path)`` resolved and ready to open.
    """
    data_cfg = config.get("data", {})
    train_path = Path(data_cfg.get("train_path", "data/processed/egfr_smiles_train.json"))
    val_path = Path(data_cfg.get("val_path", "data/processed/egfr_smiles_val.json"))

    if data_dir is not None:
        data_dir_path = Path(data_dir)
        train_path = data_dir_path / train_path.name
        val_path = data_dir_path / val_path.name

    return train_path, val_path


def validate_data_files(train_path: Path, val_path: Path) -> bool:
    """Check that required data files exist and print helpful messages if not.

    Parameters
    ----------
    train_path:
        Path to the training data JSON.
    val_path:
        Path to the validation data JSON.

    Returns
    -------
    bool:
        ``True`` if both files exist, ``False`` otherwise.
    """
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
            "\nTo prepare the training data, run the data processing pipeline first:\n"
            "  1. python scripts/build_context_dataset.py\n"
            "  2. python scripts/build_structure_dataset.py\n"
            "  3. python scripts/assemble_benchmark.py\n"
            "\n"
            "The pipeline produces JSON files with the format:\n"
            '  [{"smiles": "CCO", "state": "DFGin_aCin"}, ...]\n'
            "\n"
            "You can also use --data-dir to point to an alternative directory\n"
            "containing egfr_smiles_train.json and egfr_smiles_val.json."
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
    """Compute the KL weight for the current epoch based on annealing schedule.

    Parameters
    ----------
    epoch:
        Current epoch (0-indexed).
    target_weight:
        Final KL weight after warmup completes.
    warmup_epochs:
        Number of epochs over which to anneal from 0 to *target_weight*.
    strategy:
        Annealing strategy: ``"linear"`` (ramp from 0 to target) or
        ``"cyclical"`` (periodic linear ramps).

    Returns
    -------
    float:
        The KL weight for this epoch, rounded to 6 decimal places.
    """
    if warmup_epochs <= 0:
        return target_weight

    if strategy == "cyclical":
        # Cyclical: repeat the linear ramp every warmup_epochs
        cycle_pos = epoch % warmup_epochs
        weight = target_weight * (cycle_pos / warmup_epochs)
    else:
        # Linear: ramp from 0 to target_weight over warmup_epochs
        if epoch >= warmup_epochs:
            weight = target_weight
        else:
            weight = target_weight * (epoch / warmup_epochs)

    return round(weight, 6)


# ---------------------------------------------------------------------------
# Training and validation steps
# ---------------------------------------------------------------------------


def compute_teacher_forcing_ratio(
    epoch: int,
    total_epochs: int,
    start_ratio: float = 1.0,
    end_ratio: float = 0.0,
    warmup_epochs: int = 10,
) -> float:
    """Compute scheduled sampling teacher forcing ratio.

    Holds at *start_ratio* for *warmup_epochs*, then linearly decays to
    *end_ratio* over the remaining epochs.

    Parameters
    ----------
    epoch:
        Current epoch (0-indexed).
    total_epochs:
        Total number of training epochs.
    start_ratio:
        Teacher forcing ratio during warmup.
    end_ratio:
        Minimum teacher forcing ratio.
    warmup_epochs:
        Number of epochs to hold at *start_ratio* before annealing.

    Returns
    -------
    float:
        Teacher forcing ratio for this epoch, rounded to 4 decimal places.
    """
    if epoch < warmup_epochs:
        return start_ratio
    decay_epochs = max(total_epochs - warmup_epochs, 1)
    progress = (epoch - warmup_epochs) / decay_epochs
    ratio = start_ratio - (start_ratio - end_ratio) * min(progress, 1.0)
    return round(max(ratio, end_ratio), 4)


def train_one_epoch(
    model: Any,
    loader: Any,
    optimizer: Any,
    kl_weight: float,
    device: Any,
    gradient_clip: float,
    teacher_forcing_ratio: float = 0.5,
    scaler: Any | None = None,
) -> dict[str, float]:
    """Run one training epoch and return aggregated losses.

    Parameters
    ----------
    model:
        The :class:`ConditionalSMILESVAE` model.
    loader:
        Training DataLoader yielding ``(tokens, lengths, state_onehots)`` batches.
    optimizer:
        The optimizer.
    kl_weight:
        Current KL weight (from annealing schedule).
    device:
        Torch device to use.
    gradient_clip:
        Maximum gradient norm for clipping.
    teacher_forcing_ratio:
        Probability of teacher forcing for this epoch (scheduled sampling).
    scaler:
        Optional GradScaler for mixed precision.

    Returns
    -------
    dict[str, float]:
        ``{"total_loss", "recon_loss", "kl_loss"}`` averaged over all batches.
    """
    import torch  # noqa: I001
    from statebind.ml.vae import vae_loss

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
                    teacher_forcing_ratio=teacher_forcing_ratio,
                )
                total, recon, kl = vae_loss(
                    recon_logits, tokens, mu, logvar,
                    kl_weight=kl_weight, pad_idx=model.config.pad_idx,
                )
            scaler.scale(total).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip)
            scaler.step(optimizer)
            scaler.update()
        else:
            recon_logits, mu, logvar = model(
                tokens, lengths, state_onehots,
                teacher_forcing_ratio=teacher_forcing_ratio,
            )
            total, recon, kl = vae_loss(
                recon_logits, tokens, mu, logvar,
                kl_weight=kl_weight, pad_idx=model.config.pad_idx,
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
) -> dict[str, float]:
    """Run one validation epoch and return aggregated losses.

    Parameters
    ----------
    model:
        The :class:`ConditionalSMILESVAE` model.
    loader:
        Validation DataLoader.
    kl_weight:
        Current KL weight.
    device:
        Torch device.

    Returns
    -------
    dict[str, float]:
        ``{"total_loss", "recon_loss", "kl_loss"}`` averaged over all batches.
    """
    import torch  # noqa: I001
    from statebind.ml.vae import vae_loss

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

            recon_logits, mu, logvar = model(
                tokens, lengths, state_onehots, teacher_forcing_ratio=0.0,
            )
            total, recon, kl = vae_loss(
                recon_logits, tokens, mu, logvar,
                kl_weight=kl_weight, pad_idx=model.config.pad_idx,
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
    """Create the CSV log file with headers if it does not already exist.

    Parameters
    ----------
    path:
        Path to the CSV file.
    """
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
    """Append one row of metrics to the CSV log.

    Parameters
    ----------
    path:
        Path to the CSV file.
    epoch:
        Current epoch number.
    kl_weight:
        KL weight used this epoch.
    train_metrics:
        Training losses dict.
    val_metrics:
        Validation losses dict.
    lr:
        Current learning rate.
    elapsed:
        Total elapsed seconds since training start.
    """
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
    """Save a full training checkpoint.

    Parameters
    ----------
    model:
        The model to save.
    optimizer:
        The optimizer (state saved for resume).
    epoch:
        Current epoch number.
    metrics:
        Dict of metrics to store.
    config:
        The full training config dict.
    path:
        Destination file path.
    """
    import torch

    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "epoch": epoch,
        "metrics": metrics,
        "config": config,
        "vae_config": model.config.model_dump(),
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
    """Save a model card JSON alongside the checkpoint.

    Parameters
    ----------
    config:
        The full training config dict.
    vocab_size:
        Actual vocabulary size used.
    n_parameters:
        Total number of model parameters.
    best_epoch:
        Epoch with the best validation loss.
    best_val_loss:
        Best validation loss achieved.
    train_size:
        Number of training samples.
    val_size:
        Number of validation samples.
    checkpoint_dir:
        Directory to write the model card to.
    """
    from statebind.ml.models import ModelCard

    card = ModelCard(
        model_name="ConditionalSMILESVAE",
        model_type="vae",
        description=(
            "Conditional SMILES VAE for EGFR state-conditioned molecular generation. "
            "GRU encoder/decoder with state-conditioning at encoder input and decoder "
            "initial hidden state. Trained with KL annealing."
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
            "Docking scores are not used during training (stub)",
            "Validity of generated SMILES is not guaranteed without post-filtering",
            "Trained on EGFR-specific data only — not a general-purpose generator",
            "KL collapse risk if annealing schedule is too aggressive",
        ],
        version="0.1.0",
    )

    card_path = checkpoint_dir / "model_card.json"
    with open(card_path, "w") as f:
        f.write(card.model_dump_json(indent=2))

    logger.info("Model card saved to %s", card_path)


def save_vocabulary(vocab: Any, checkpoint_dir: Path) -> None:
    """Save the vocabulary JSON to the checkpoint directory.

    Parameters
    ----------
    vocab:
        The :class:`Vocabulary` instance.
    checkpoint_dir:
        Directory to write the vocabulary to.
    """
    vocab_path = checkpoint_dir / "vocabulary.json"
    with open(vocab_path, "w") as f:
        f.write(vocab.to_json())
    logger.info("Vocabulary saved to %s (%d tokens)", vocab_path, vocab.size)


def save_final_config(config: dict[str, Any], checkpoint_dir: Path) -> None:
    """Save the final resolved config to the checkpoint directory.

    Parameters
    ----------
    config:
        The full training config dict (with any runtime overrides applied).
    checkpoint_dir:
        Directory to write the config to.
    """
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
        description="Train the Conditional SMILES VAE for state-conditioned molecular generation.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/vae.yaml",
        help="Path to YAML configuration file (default: configs/vae.yaml)",
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
    parser.add_argument(
        "--selfies",
        action="store_true",
        default=False,
        help="Use SELFIES representation instead of SMILES (guarantees valid molecules)",
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
    config["representation"] = "selfies" if args.selfies else "smiles"
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
            "See https://pytorch.org/get-started/locally/ for platform-specific instructions."
        )
        sys.exit(1)

    from statebind.ml.tokenizer import SMILESTokenizer
    from statebind.ml.utils import (
        EarlyStopper,
        count_parameters,
        get_device,
        set_seed,
    )
    from statebind.ml.vae import ConditionalSMILESVAE, VAEConfig
    from statebind.ml.vae_dataset import (
        SMILESDatasetConfig,
        collate_smiles,
        load_smiles_dataset,
    )
    from statebind.ml.vocabulary import build_vocabulary

    use_selfies = args.selfies
    selfies_tokenizer = None
    if use_selfies:
        from statebind.ml.tokenizer import SELFIESTokenizer
        selfies_tokenizer = SELFIESTokenizer()
        logger.info("SELFIES mode enabled — converting SMILES to SELFIES")

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
    print("  Conditional SMILES VAE — Training Pipeline")
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

    # Convert to SELFIES if requested
    if use_selfies:
        assert selfies_tokenizer is not None
        logger.info("Converting training data to SELFIES...")
        train_selfies = []
        train_records_filtered = []
        for smi, rec in zip(train_smiles, train_records):
            sel = selfies_tokenizer.smiles_to_selfies(smi)
            if sel is not None:
                train_selfies.append(sel)
                rec_copy = dict(rec)
                rec_copy["smiles"] = sel  # Replace SMILES with SELFIES
                train_records_filtered.append(rec_copy)
        val_selfies = []
        val_records_filtered = []
        for smi, rec in zip(val_smiles, val_records):
            sel = selfies_tokenizer.smiles_to_selfies(smi)
            if sel is not None:
                val_selfies.append(sel)
                rec_copy = dict(rec)
                rec_copy["smiles"] = sel
                val_records_filtered.append(rec_copy)
        logger.info(
            "SELFIES conversion: train %d/%d, val %d/%d",
            len(train_selfies), len(train_smiles),
            len(val_selfies), len(val_smiles),
        )
        train_smiles = train_selfies
        val_smiles = val_selfies
        train_records = train_records_filtered
        val_records = val_records_filtered
        tokenizer = selfies_tokenizer  # type: ignore[assignment]
    else:
        tokenizer = SMILESTokenizer()  # type: ignore[assignment]

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

    # For SELFIES mode, write converted data to temp files so
    # load_smiles_dataset can read them
    if use_selfies:
        import tempfile
        selfies_dir = Path(tempfile.mkdtemp(prefix="selfies_"))
        selfies_train_path = selfies_dir / "train.json"
        selfies_val_path = selfies_dir / "val.json"
        with open(selfies_train_path, "w") as f:
            json.dump(train_records, f)
        with open(selfies_val_path, "w") as f:
            json.dump(val_records, f)
        logger.info("SELFIES data written to %s", selfies_dir)
        train_dataset = load_smiles_dataset(selfies_train_path, tokenizer, vocab, ds_config)
        val_dataset = load_smiles_dataset(selfies_val_path, tokenizer, vocab, ds_config)
    else:
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

    vae_config = VAEConfig(
        vocab_size=actual_vocab_size,
        embed_dim=model_cfg.get("embed_dim", 128),
        hidden_dim=model_cfg.get("hidden_dim", 256),
        latent_dim=model_cfg.get("latent_dim", 64),
        n_layers=model_cfg.get("n_layers", 2),
        dropout=model_cfg.get("dropout", 0.1),
        n_states=model_cfg.get("n_states", 3),
        kl_weight=model_cfg.get("kl_weight", 0.01),
        pad_idx=vocab.pad_idx,
    )

    model = ConditionalSMILESVAE(vae_config).to(device)

    total_params, trainable_params = count_parameters(model)
    print("  Architecture:  GRU encoder (bidirectional) + GRU decoder")
    print(f"  Latent dim:    {vae_config.latent_dim}")
    print(f"  Hidden dim:    {vae_config.hidden_dim}")
    print(f"  Parameters:    {total_params:,} total, {trainable_params:,} trainable")

    # ------------------------------------------------------------------
    # Optimizer and scheduler
    # ------------------------------------------------------------------
    lr = train_cfg.get("learning_rate", 0.001)
    weight_decay = train_cfg.get("weight_decay", 0.00001)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=lr, weight_decay=weight_decay,
    )

    scheduler_name = train_cfg.get("lr_scheduler", "cosine")
    epochs = train_cfg.get("epochs", 200)

    scheduler: torch.optim.lr_scheduler.LRScheduler | None = None
    if scheduler_name == "cosine":
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs, eta_min=1e-7,
        )
    elif scheduler_name == "plateau":
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5,
            patience=max(train_cfg.get("patience", 20) // 3, 3),
            min_lr=1e-7,
        )

    # Mixed precision scaler (CUDA only)
    use_amp = train_cfg.get("mixed_precision", False) and device.type == "cuda"
    scaler: torch.amp.GradScaler | None = None
    if use_amp:
        scaler = torch.amp.GradScaler("cuda")
        logger.info("Mixed precision training enabled")

    # Early stopping
    patience = train_cfg.get("patience", 20)
    stopper = EarlyStopper(patience=patience)

    # KL annealing parameters
    kl_target_weight = model_cfg.get("kl_weight", 0.01)
    kl_warmup_epochs = kl_cfg.get("warmup_epochs", 20)
    kl_strategy = kl_cfg.get("strategy", "linear")

    # Teacher forcing annealing parameters
    tf_cfg = config.get("teacher_forcing", {})
    tf_start = tf_cfg.get("start_ratio", 1.0)
    tf_end = tf_cfg.get("end_ratio", 0.0)
    tf_warmup = tf_cfg.get("warmup_epochs", 10)

    # Early stopping target: use recon_loss to avoid KL annealing artifacts
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
        if "val_total_loss" in stored_metrics:
            best_val_loss = stored_metrics["val_total_loss"]
            best_epoch = checkpoint.get("epoch", 0)
        print(f"  Resumed at epoch {start_epoch}, best val loss: {round(best_val_loss, 4)}")

    # ------------------------------------------------------------------
    # Prepare logging directories
    # ------------------------------------------------------------------
    checkpoint_dir = Path(train_cfg.get("checkpoint_dir", "artifacts/models/vae/"))
    log_dir = Path(train_cfg.get("log_dir", "artifacts/logs/vae/"))
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
    print(f"  TF annealing: {tf_start} -> {tf_end}, warmup={tf_warmup} epochs")
    print(f"  Early stop on: {early_stop_metric}")
    print(f"  LR scheduler: {scheduler_name}")
    print()

    training_start = time.monotonic()

    # Set up rich progress bar or plain output
    epoch_range = range(start_epoch, epochs)

    if HAS_RICH:
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        task = progress.add_task("Training", total=epochs - start_epoch)
        progress.start()
    else:
        progress = None  # type: ignore[assignment]

    try:
        for epoch in epoch_range:
            epoch_start = time.monotonic()

            # Compute KL weight for this epoch
            kl_weight = compute_kl_weight(
                epoch, kl_target_weight, kl_warmup_epochs, kl_strategy,
            )

            # Compute teacher forcing ratio for this epoch
            tf_ratio = compute_teacher_forcing_ratio(
                epoch, epochs, tf_start, tf_end, tf_warmup,
            )

            # Train
            train_metrics = train_one_epoch(
                model, train_loader, optimizer, kl_weight, device,
                gradient_clip, tf_ratio, scaler,
            )

            # Validate
            val_metrics = validate_one_epoch(
                model, val_loader, kl_weight, device,
            )

            # Current learning rate
            current_lr = optimizer.param_groups[0]["lr"]

            # Step scheduler
            if scheduler is not None:
                if scheduler_name == "plateau":
                    scheduler.step(val_metrics["total_loss"])
                elif scheduler_name == "cosine":
                    scheduler.step()

            # Elapsed time
            elapsed = time.monotonic() - training_start

            # Log to CSV
            append_csv_log(
                csv_path, epoch, kl_weight,
                train_metrics, val_metrics, current_lr, elapsed,
            )

            # Check for best model (track recon_loss to avoid KL annealing artifacts)
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
            train_detail = f"(recon={t_recon:.4f}, kl={t_kl:.4f})"
            val_detail = f"(recon={v_recon:.4f}, kl={v_kl:.4f})"

            line = (
                f"  Epoch {epoch:>3d}/{epochs}  |  "
                f"train: {train_metrics['total_loss']:.4f} "
                f"{train_detail}  |  "
                f"val: {val_metrics['total_loss']:.4f} "
                f"{val_detail}  |  "
                f"kl_w={kl_weight:.4f}  tf={tf_ratio:.2f}  "
                f"lr={current_lr:.6f}  "
                f"({epoch_time:.1f}s){best_marker}"
            )

            if HAS_RICH:
                console.print(line)
                progress.advance(task)
            else:
                print(line)

            # Early stopping on same metric as best model tracking
            if stopper.step(track_loss, epoch):
                print(f"\n  Early stopping at epoch {epoch} (no improvement for {patience} epochs)")
                break

    finally:
        if HAS_RICH and progress is not None:
            progress.stop()

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
    print(f"  Model card:      {checkpoint_dir / 'model_card.json'}")
    print(f"  Vocabulary:      {checkpoint_dir / 'vocabulary.json'}")
    print("=" * 64)


if __name__ == "__main__":
    main()
