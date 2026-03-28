"""Affinity prediction adapter -- singleton inference wrapper.

Wraps the trained ``AffinityMPNN`` model for use in the ranking pipeline.
Provides ``predict_affinity()`` and ``predict_affinity_batch()`` with a
simple SMILES-in, float-out interface.

No torch dependency at import time -- all torch/PyG imports are deferred.
Public functions never raise; they return 0.5 (neutral) on any failure.

Normalization: MPNN predicts raw pIC50, then ``_normalize_pic50()`` maps
to [0, 1] via sigmoid((pIC50 - 5) / 2).  This centers at pIC50=5
(IC50 = 10 µM) and spreads across the pharmacologically relevant range:
    pIC50 = 3 (1 mM)   → 0.27
    pIC50 = 5 (10 µM)  → 0.50
    pIC50 = 7 (100 nM) → 0.73
    pIC50 = 9 (1 nM)   → 0.88
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

from statebind.data.paths import DataPaths

if TYPE_CHECKING:
    import torch  # noqa: I001

    from statebind.ml.mpnn import AffinityMPNN

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton (lazy-loaded on first predict call)
# ---------------------------------------------------------------------------

_MODEL: AffinityMPNN | None = None
_DEVICE: torch.device | None = None
_LOAD_ATTEMPTED: bool = False

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

_FALLBACK_SCORE: float = 0.5


def _normalize_pic50(pic50: float) -> float:
    """Normalize pIC50 to [0, 1] via sigmoid((pIC50 - 5) / 2).

    Centers at pIC50=5 (IC50 = 10 µM) and uses a scale factor of 2
    to spread the sigmoid across the pharmacologically relevant range
    (pIC50 3-9).

    Args:
        pic50: Raw pIC50 value from the MPNN.

    Returns:
        Float in (0, 1).  Higher = stronger predicted binder.
    """
    return 1.0 / (1.0 + math.exp(-(pic50 - 5.0) / 2.0))


# ---------------------------------------------------------------------------
# Singleton model loading
# ---------------------------------------------------------------------------


def _load_model(
    checkpoint_path: Path | str | None = None,
) -> tuple[Any, Any] | None:
    """Load the AffinityMPNN model from a checkpoint.

    All torch imports are deferred to this function body so the module
    remains importable without torch installed.

    Args:
        checkpoint_path: Path to the saved checkpoint.  Defaults to
            ``{project_root}/artifacts/models/mpnn/best_model.pt``.

    Returns:
        A ``(model, device)`` tuple on success, or ``None`` on any failure
        (missing checkpoint, missing dependencies, architecture mismatch,
        etc.).  Never raises.
    """
    try:
        import torch  # noqa: I001

        from statebind.ml.mpnn import AffinityMPNN, MPNNConfig
        from statebind.ml.utils import get_device
    except ImportError:
        logger.warning(
            "MPNN affinity predictor requires torch, torch_geometric, and "
            "rdkit. Returning None (predictions will fall back to 0.5)."
        )
        return None

    if checkpoint_path is None:
        checkpoint_path = (
            DataPaths().root / "artifacts" / "models" / "mpnn" / "best_model.pt"
        )
    checkpoint_path = Path(checkpoint_path)

    if not checkpoint_path.exists():
        logger.warning(
            "MPNN checkpoint not found at %s. "
            "Predictions will fall back to 0.5.",
            checkpoint_path,
        )
        return None

    try:
        device = get_device("auto")

        # Load checkpoint to inspect config
        checkpoint: dict[str, Any] = torch.load(
            checkpoint_path, map_location=device, weights_only=False
        )

        # Reconstruct config from checkpoint if available
        if "config" in checkpoint and checkpoint["config"] is not None:
            config = MPNNConfig(**checkpoint["config"])
        else:
            config = MPNNConfig()

        model = AffinityMPNN(config)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        model.eval()

        logger.info(
            "MPNN affinity model loaded from %s on device %s",
            checkpoint_path,
            device,
        )
        return (model, device)

    except Exception:
        logger.warning(
            "Failed to load MPNN model from %s. "
            "Predictions will fall back to 0.5.",
            checkpoint_path,
            exc_info=True,
        )
        return None


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def _model_loaded() -> bool:
    """Return True if the MPNN singleton was successfully loaded.

    This is used by ``ranking/scoring.py`` to distinguish "MPNN
    predicted 0.5" (a legitimate prediction for pIC50=5) from "MPNN
    failed to load" (where 0.5 is the fallback).
    """
    return _MODEL is not None


# ---------------------------------------------------------------------------
# Single-molecule prediction
# ---------------------------------------------------------------------------


def predict_affinity(
    smiles: str,
    checkpoint_path: Path | str | None = None,
) -> float:
    """Predict normalized binding affinity for a SMILES string.

    Uses a module-level singleton: the model is loaded once on the first
    call and reused for all subsequent calls.  If the model cannot be
    loaded (missing checkpoint, missing torch, etc.), returns 0.5
    (neutral fallback, same as the docking stub).

    Args:
        smiles: A SMILES string representing a molecule.
        checkpoint_path: Optional override for the model checkpoint path.
            Only used on the very first call (when the singleton is
            initialized).

    Returns:
        Float in [0.0, 1.0] where higher = stronger predicted binder.
        Returns 0.5 on any failure.
    """
    global _MODEL, _DEVICE, _LOAD_ATTEMPTED

    # Lazy singleton initialization
    if _MODEL is None and not _LOAD_ATTEMPTED:
        _LOAD_ATTEMPTED = True
        result = _load_model(checkpoint_path)
        if result is not None:
            _MODEL, _DEVICE = result

    if _MODEL is None:
        return _FALLBACK_SCORE

    try:
        import torch  # noqa: I001

        from statebind.ml.graphs import smiles_to_graph

        graph = smiles_to_graph(smiles)
        if graph is None:
            logger.debug("Failed to convert SMILES to graph: %s", smiles)
            return _FALLBACK_SCORE

        graph = graph.to(_DEVICE)

        with torch.no_grad():
            raw_pic50 = _MODEL(graph).squeeze().item()

        return round(_normalize_pic50(raw_pic50), 4)

    except Exception:
        logger.warning(
            "MPNN prediction failed for SMILES: %s",
            smiles,
            exc_info=True,
        )
        return _FALLBACK_SCORE


# ---------------------------------------------------------------------------
# Batch prediction
# ---------------------------------------------------------------------------

_BATCH_CHUNK_SIZE: int = 256


def predict_affinity_batch(
    smiles_list: list[str],
    checkpoint_path: Path | str | None = None,
) -> list[float]:
    """Predict normalized binding affinity for a list of SMILES strings.

    Uses batched inference via ``torch_geometric.data.Batch`` for
    efficiency.  Falls back to individual predictions if batching fails.

    Args:
        smiles_list: List of SMILES strings.
        checkpoint_path: Optional override for the model checkpoint path
            (only used on first call for singleton init).

    Returns:
        A list of floats, one per input SMILES.  Each value is in
        [0.0, 1.0].  Failed SMILES produce 0.5 (neutral fallback).
        The output list is always the same length as the input list.
    """
    global _MODEL, _DEVICE, _LOAD_ATTEMPTED

    if not smiles_list:
        return []

    # Lazy singleton initialization
    if _MODEL is None and not _LOAD_ATTEMPTED:
        _LOAD_ATTEMPTED = True
        result = _load_model(checkpoint_path)
        if result is not None:
            _MODEL, _DEVICE = result

    if _MODEL is None:
        return [_FALLBACK_SCORE for _ in smiles_list]

    # Try batched inference
    try:
        return _predict_batch_internal(smiles_list)
    except Exception:
        logger.warning(
            "Batch MPNN prediction failed, falling back to individual "
            "predictions.",
            exc_info=True,
        )
        return [predict_affinity(smi) for smi in smiles_list]


def _predict_batch_internal(
    smiles_list: list[str],
) -> list[float]:
    """Internal batched prediction using PyG Batch.

    Converts all SMILES to graphs, batches them in chunks of
    :data:`_BATCH_CHUNK_SIZE`, runs the model forward pass, and
    normalizes results via ``_normalize_pic50``.

    Args:
        smiles_list: List of SMILES strings.

    Returns:
        List of normalized affinity scores, same length as input.

    Raises:
        Any exception from torch or PyG (caller catches).
    """
    import torch
    from torch_geometric.data import Batch

    from statebind.ml.graphs import smiles_to_graph

    assert _MODEL is not None
    assert _DEVICE is not None

    # Convert all SMILES to graphs, tracking which indices succeeded
    results: list[float] = [_FALLBACK_SCORE for _ in smiles_list]
    graphs: list[Any] = []
    valid_indices: list[int] = []

    for idx, smi in enumerate(smiles_list):
        graph = smiles_to_graph(smi)
        if graph is not None:
            graphs.append(graph)
            valid_indices.append(idx)

    if not graphs:
        return results

    # Process in chunks to avoid OOM
    was_training = _MODEL.training
    _MODEL.eval()

    try:
        for chunk_start in range(0, len(graphs), _BATCH_CHUNK_SIZE):
            chunk_end = min(chunk_start + _BATCH_CHUNK_SIZE, len(graphs))
            chunk_graphs = graphs[chunk_start:chunk_end]
            chunk_valid_indices = valid_indices[chunk_start:chunk_end]

            batch = Batch.from_data_list(chunk_graphs).to(_DEVICE)

            with torch.no_grad():
                raw_predictions = _MODEL(batch)

            # Extract per-molecule pIC50 and normalize
            batch_size = len(chunk_graphs)
            for i in range(batch_size):
                original_idx = chunk_valid_indices[i]
                raw_pic50 = raw_predictions[i].squeeze().item()
                results[original_idx] = round(
                    _normalize_pic50(raw_pic50), 4
                )
    finally:
        if was_training:
            _MODEL.train()

    return results


# ---------------------------------------------------------------------------
# Testing / reset helpers
# ---------------------------------------------------------------------------


def reset_singleton() -> None:
    """Reset the module-level singleton state.

    Intended for testing only.  After calling this, the next
    :func:`predict_affinity` or :func:`predict_affinity_batch` call will
    attempt to reload the model.
    """
    global _MODEL, _DEVICE, _LOAD_ATTEMPTED
    _MODEL = None
    _DEVICE = None
    _LOAD_ATTEMPTED = False
