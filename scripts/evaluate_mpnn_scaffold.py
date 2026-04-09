#!/usr/bin/env python3
"""Evaluate MPNN with scaffold split and produce Gate G1 artifact.

Trains the MPNN model twice -- once with scaffold split, once with random
split (for comparison) -- and writes a comprehensive metrics artifact to
``artifacts/evaluation/mpnn_scaffold_metrics.json``.

Gate G1 thresholds:
    >= 0.35 : GO
    [0.20, 0.35) : CONDITIONAL GO (reframe MPNN as supplementary)
    < 0.20 : NO-GO (drop MPNN from scoring)

Usage:
    python scripts/evaluate_mpnn_scaffold.py
    python scripts/evaluate_mpnn_scaffold.py --config configs/mpnn.yaml
    python scripts/evaluate_mpnn_scaffold.py --skip-random
"""
from __future__ import annotations

import argparse
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
    scaffold_split,
    split_dataset,
)
from statebind.ml.mpnn import AffinityMPNN, MPNNConfig
from statebind.ml.models import TrainerConfig
from statebind.ml.utils import (
    EarlyStopper,
    count_parameters,
    get_device,
    save_model,
    set_seed,
)

logger = logging.getLogger(__name__)

GATE_G1_GO = 0.35
GATE_G1_CONDITIONAL = 0.20


# ---------------------------------------------------------------------------
# Config loaders (reuse from train_mpnn.py logic)
# ---------------------------------------------------------------------------


def _load_config(config_path: str) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def _build_model_config(raw: dict[str, Any]) -> MPNNConfig:
    return MPNNConfig(**raw.get("model", {}))


def _build_trainer_config(raw: dict[str, Any]) -> TrainerConfig:
    return TrainerConfig(**raw.get("training", {}))


def _build_data_config(raw: dict[str, Any]) -> AffinityDatasetConfig:
    return AffinityDatasetConfig(**raw.get("data", {}))


# ---------------------------------------------------------------------------
# Training and evaluation helpers
# ---------------------------------------------------------------------------


def _train_and_evaluate(
    model_config: MPNNConfig,
    trainer_config: TrainerConfig,
    train_ds: Any,
    val_ds: Any,
    test_ds: Any,
    device: Any,
    tag: str,
    metrics_list: list[str],
) -> dict[str, Any]:
    """Train an MPNN from scratch on the given splits and return metrics.

    Args:
        model_config: MPNN architecture config.
        trainer_config: Training hyperparameters.
        train_ds: Training dataset.
        val_ds: Validation dataset.
        test_ds: Test dataset.
        device: Torch device.
        tag: Label for this run (e.g. "scaffold" or "random").
        metrics_list: Metrics to compute on the test set.

    Returns:
        Dictionary with train/test metrics and timing.
    """
    import torch
    from torch_geometric.loader import DataLoader

    print(f"\n{'=' * 70}")
    print(f"  Training MPNN ({tag} split)")
    print(f"  train={len(train_ds)}, val={len(val_ds)}, test={len(test_ds)}")
    print(f"{'=' * 70}")

    # DataLoaders
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

    # Fresh model
    model = AffinityMPNN(config=model_config).to(device)
    total_params, trainable_params = count_parameters(model)
    print(f"  Model: {total_params:,} params ({trainable_params:,} trainable)")

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=trainer_config.learning_rate,
        weight_decay=trainer_config.weight_decay,
    )
    loss_fn = torch.nn.MSELoss()

    scheduler = None
    if trainer_config.lr_scheduler == "cosine":
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=trainer_config.epochs, eta_min=1e-7
        )
    elif trainer_config.lr_scheduler == "plateau":
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5,
            patience=max(trainer_config.patience // 3, 3), min_lr=1e-7,
        )

    stopper = EarlyStopper(patience=trainer_config.patience)

    # Checkpoint dir (split-specific)
    ckpt_dir = Path(trainer_config.checkpoint_dir.rstrip("/") + f"_{tag}")
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_val_loss = float("inf")
    best_epoch = 0
    start_time = time.monotonic()

    for epoch in range(trainer_config.epochs):
        # --- Train ---
        model.train()
        train_loss_sum = 0.0
        n_batches = 0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            pred = model(batch)
            loss = loss_fn(pred.squeeze(), batch.y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), trainer_config.gradient_clip
            )
            optimizer.step()
            train_loss_sum += loss.item()
            n_batches += 1
        train_loss = train_loss_sum / max(n_batches, 1)

        # --- Validate ---
        model.eval()
        val_loss_sum = 0.0
        n_val_batches = 0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                pred = model(batch)
                loss = loss_fn(pred.squeeze(), batch.y)
                val_loss_sum += loss.item()
                n_val_batches += 1
        val_loss = val_loss_sum / max(n_val_batches, 1)

        # Scheduler step
        if scheduler is not None:
            if trainer_config.lr_scheduler == "plateau":
                scheduler.step(val_loss)
            else:
                scheduler.step()

        # Print every 10 epochs
        if epoch % 10 == 0 or epoch == trainer_config.epochs - 1:
            print(f"  [{tag}] Epoch {epoch:>4d}/{trainer_config.epochs}  "
                  f"train={train_loss:.4f}  val={val_loss:.4f}")

        # Track best
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            save_model(
                model,
                ckpt_dir / "best_model.pt",
                config=model_config.model_dump(),
                metrics={
                    "epoch": epoch,
                    "train_loss": round(train_loss, 4),
                    "val_loss": round(val_loss, 4),
                },
            )

        # Early stopping
        if stopper.step(val_loss, epoch):
            print(f"  [{tag}] Early stopping at epoch {epoch} "
                  f"(no improvement for {trainer_config.patience} epochs)")
            break

    elapsed = time.monotonic() - start_time
    print(f"  [{tag}] Training complete in {elapsed:.1f}s (best epoch: {best_epoch})")

    # --- Load best model and evaluate ---
    best_ckpt = ckpt_dir / "best_model.pt"
    if best_ckpt.exists():
        checkpoint = torch.load(best_ckpt, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])

    model.eval()
    all_preds: list[float] = []
    all_targets: list[float] = []
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            pred = model(batch)
            all_preds.extend(pred.squeeze().cpu().tolist())
            all_targets.extend(batch.y.cpu().tolist())

    preds = np.array(all_preds)
    targets = np.array(all_targets)

    results: dict[str, float] = {}
    mse = float(np.mean((preds - targets) ** 2))
    results["rmse"] = round(math.sqrt(mse), 4)
    results["mse"] = round(mse, 4)
    results["mae"] = round(float(np.mean(np.abs(preds - targets))), 4)

    ss_res = float(np.sum((targets - preds) ** 2))
    ss_tot = float(np.sum((targets - np.mean(targets)) ** 2))
    r2 = 1.0 - (ss_res / max(ss_tot, 1e-12))
    results["r2"] = round(r2, 4)

    try:
        from scipy import stats as scipy_stats
        if len(preds) > 1:
            corr, _ = scipy_stats.pearsonr(preds, targets)
            results["pearson"] = round(float(corr), 4)
        else:
            results["pearson"] = 0.0
    except ImportError:
        results["pearson"] = 0.0

    # Also compute train R^2
    train_preds_list: list[float] = []
    train_targets_list: list[float] = []
    with torch.no_grad():
        for batch in train_loader:
            batch = batch.to(device)
            pred = model(batch)
            train_preds_list.extend(pred.squeeze().cpu().tolist())
            train_targets_list.extend(batch.y.cpu().tolist())
    train_preds = np.array(train_preds_list)
    train_targets = np.array(train_targets_list)
    ss_res_train = float(np.sum((train_targets - train_preds) ** 2))
    ss_tot_train = float(np.sum((train_targets - np.mean(train_targets)) ** 2))
    train_r2 = 1.0 - (ss_res_train / max(ss_tot_train, 1e-12))
    results["train_r2"] = round(train_r2, 4)

    print(f"\n  [{tag}] Test metrics:")
    for name, value in results.items():
        print(f"    {name}: {value}")

    return {
        "test_metrics": results,
        "best_epoch": best_epoch,
        "best_val_loss": round(best_val_loss, 4),
        "training_time_seconds": round(elapsed, 2),
        "n_train": len(train_ds),
        "n_val": len(val_ds),
        "n_test": len(test_ds),
    }


# ---------------------------------------------------------------------------
# Gate G1 logic
# ---------------------------------------------------------------------------


def _gate_g1(scaffold_r2: float) -> dict[str, Any]:
    """Evaluate Gate G1 criterion.

    Args:
        scaffold_r2: The scaffold-split test R^2 value.

    Returns:
        Dictionary with gate outcome, criterion, and notes.
    """
    if scaffold_r2 >= GATE_G1_GO:
        outcome = "GO"
        notes = (
            f"Scaffold R^2 = {scaffold_r2:.4f} >= {GATE_G1_GO}. "
            "The MPNN remains a credible scoring component under "
            "structurally challenging evaluation."
        )
    elif scaffold_r2 >= GATE_G1_CONDITIONAL:
        outcome = "CONDITIONAL_GO"
        notes = (
            f"Scaffold R^2 = {scaffold_r2:.4f} is in [{GATE_G1_CONDITIONAL}, "
            f"{GATE_G1_GO}). The MPNN should be reframed as a supplementary "
            "scoring signal rather than a primary component."
        )
    else:
        outcome = "NO_GO"
        notes = (
            f"Scaffold R^2 = {scaffold_r2:.4f} < {GATE_G1_CONDITIONAL}. "
            "The MPNN does not generalize to novel scaffolds and should "
            "be dropped from the scoring pipeline."
        )
    return {
        "criterion": f"scaffold R^2 >= {GATE_G1_GO}",
        "value": round(scaffold_r2, 4),
        "outcome": outcome,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(
    config_path: str = "configs/mpnn.yaml",
    skip_random: bool = False,
) -> None:
    """Run scaffold split evaluation and produce Gate G1 artifact."""
    import torch

    raw_config = _load_config(config_path)
    model_config = _build_model_config(raw_config)
    trainer_config = _build_trainer_config(raw_config)
    data_config = _build_data_config(raw_config)
    eval_config = raw_config.get("evaluation", {})
    metrics_list: list[str] = eval_config.get(
        "metrics", ["rmse", "mae", "r2", "pearson"]
    )

    seed = data_config.seed
    set_seed(seed)
    device = get_device(trainer_config.device)

    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        vram = getattr(props, "total_memory", 0)
        print(f"VRAM: {vram / 1e9:.1f} GB")

    # Load dataset
    data_path = Path(data_config.data_path)
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        sys.exit(1)

    print(f"\nLoading dataset from: {data_path}")
    dataset = load_affinity_dataset(data_path, config=data_config)
    summary = dataset.summary()
    print(f"  {summary['n_samples']} valid graphs")
    print(f"  pIC50: [{summary['min_pIC50']}, {summary['max_pIC50']}] "
          f"(mean={summary['mean_pIC50']}, std={summary['std_pIC50']})")

    if summary["n_samples"] == 0:
        print("ERROR: No valid graphs. Exiting.")
        sys.exit(1)

    # ── Scaffold split ────────────────────────────────────────────────
    print("\n--- Scaffold split ---")
    scaffold_config = data_config.model_copy(update={"split_type": "scaffold"})
    train_ds_s, val_ds_s, test_ds_s = split_dataset(dataset, config=scaffold_config)

    # Count scaffolds for metadata
    scaffold_info: dict[str, int] = {}
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds.MurckoScaffold import (
            GetScaffoldForMol,
            MakeScaffoldGeneric,
        )
        all_scaffolds = set()
        train_scaffolds = set()
        test_scaffolds = set()
        for smi in dataset.smiles_list:
            mol = Chem.MolFromSmiles(smi)
            if mol:
                core = GetScaffoldForMol(mol)
                generic = MakeScaffoldGeneric(core)
                all_scaffolds.add(Chem.MolToSmiles(generic))
        for smi in train_ds_s.smiles_list:
            mol = Chem.MolFromSmiles(smi)
            if mol:
                core = GetScaffoldForMol(mol)
                generic = MakeScaffoldGeneric(core)
                train_scaffolds.add(Chem.MolToSmiles(generic))
        for smi in test_ds_s.smiles_list:
            mol = Chem.MolFromSmiles(smi)
            if mol:
                core = GetScaffoldForMol(mol)
                generic = MakeScaffoldGeneric(core)
                test_scaffolds.add(Chem.MolToSmiles(generic))
        scaffold_info = {
            "n_unique_scaffolds": len(all_scaffolds),
            "n_train_scaffolds": len(train_scaffolds),
            "n_test_scaffolds": len(test_scaffolds),
            "scaffold_overlap": len(train_scaffolds & test_scaffolds),
        }
        print(f"  Scaffolds: {len(all_scaffolds)} unique, "
              f"{len(train_scaffolds)} train, {len(test_scaffolds)} test, "
              f"{len(train_scaffolds & test_scaffolds)} overlap")
    except ImportError:
        scaffold_info = {}

    scaffold_results = _train_and_evaluate(
        model_config=model_config,
        trainer_config=trainer_config,
        train_ds=train_ds_s,
        val_ds=val_ds_s,
        test_ds=test_ds_s,
        device=device,
        tag="scaffold",
        metrics_list=metrics_list,
    )

    # ── Random split (for comparison) ─────────────────────────────────
    random_results: dict[str, Any] | None = None
    random_r2: float = 0.69  # default from existing artifact

    if not skip_random:
        print("\n--- Random split ---")
        set_seed(seed)  # reset seed for fair comparison
        random_config = data_config.model_copy(update={"split_type": "random"})
        train_ds_r, val_ds_r, test_ds_r = split_dataset(dataset, config=random_config)

        random_results = _train_and_evaluate(
            model_config=model_config,
            trainer_config=trainer_config,
            train_ds=train_ds_r,
            val_ds=val_ds_r,
            test_ds=test_ds_r,
            device=device,
            tag="random",
            metrics_list=metrics_list,
        )
        random_r2 = random_results["test_metrics"]["r2"]
    else:
        # Use the value from the existing artifact if available
        existing_path = Path("artifacts/evaluation/mpnn_metrics.json")
        if existing_path.exists():
            with open(existing_path) as f:
                existing = json.load(f)
            random_r2 = existing.get("test_metrics", {}).get("r2", 0.69)
            print(f"\n[Skipping random re-train; using existing R^2={random_r2}]")

    # ── Gate G1 ───────────────────────────────────────────────────────
    scaffold_r2 = scaffold_results["test_metrics"]["r2"]
    gate = _gate_g1(scaffold_r2)

    degradation = round(random_r2 - scaffold_r2, 4)

    # ── Write artifact ────────────────────────────────────────────────
    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "split_type": "scaffold",
        "seed": seed,
        "metrics": {
            "test_r2": scaffold_results["test_metrics"]["r2"],
            "test_mse": scaffold_results["test_metrics"]["mse"],
            "test_mae": scaffold_results["test_metrics"]["mae"],
            "test_rmse": scaffold_results["test_metrics"]["rmse"],
            "test_pearson": scaffold_results["test_metrics"].get("pearson", 0.0),
            "train_r2": scaffold_results["test_metrics"]["train_r2"],
            "n_train": scaffold_results["n_train"],
            "n_val": scaffold_results["n_val"],
            "n_test": scaffold_results["n_test"],
            **scaffold_info,
        },
        "gate_g1": gate,
        "comparison": {
            "random_split_r2": random_r2,
            "scaffold_split_r2": scaffold_r2,
            "degradation": degradation,
        },
        "scaffold_training": {
            "best_epoch": scaffold_results["best_epoch"],
            "best_val_loss": scaffold_results["best_val_loss"],
            "training_time_seconds": scaffold_results["training_time_seconds"],
        },
        "notes": (
            "Scaffold split ensures no Murcko scaffold is shared between "
            "train and test sets, providing a harder and more realistic "
            "generalization test than random split."
        ),
    }

    if random_results is not None:
        artifact["random_training"] = {
            "test_metrics": random_results["test_metrics"],
            "best_epoch": random_results["best_epoch"],
            "best_val_loss": random_results["best_val_loss"],
            "training_time_seconds": random_results["training_time_seconds"],
            "n_train": random_results["n_train"],
            "n_val": random_results["n_val"],
            "n_test": random_results["n_test"],
        }

    output_path = Path("artifacts/evaluation/mpnn_scaffold_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(artifact, f, indent=2)

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("MPNN Scaffold Split Evaluation -- SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Scaffold R^2:  {scaffold_r2}")
    print(f"  Random R^2:    {random_r2}")
    print(f"  Degradation:   {degradation}")
    print(f"  Gate G1:       {gate['outcome']}")
    print(f"  Criterion:     {gate['criterion']}")
    print(f"  Notes:         {gate['notes']}")
    print(f"\n  Artifact: {output_path}")
    print(f"{'=' * 70}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate MPNN with scaffold split for Gate G1.",
    )
    parser.add_argument(
        "--config", type=str, default="configs/mpnn.yaml",
        help="Path to YAML config (default: configs/mpnn.yaml)",
    )
    parser.add_argument(
        "--skip-random", action="store_true",
        help="Skip random-split re-training (use existing metrics for comparison)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = _parse_args()
    main(config_path=args.config, skip_random=args.skip_random)
