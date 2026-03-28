"""ADMET prediction adapter -- singleton inference wrapper.

Provides ``predict_admet()`` and ``predict_admet_batch()`` for running the
trained MultiTaskADMET model on SMILES strings, plus ``check_admet_pass()``
for threshold-based safety filtering.

No torch dependency at import time -- all torch/PyG imports are deferred.
Public functions never raise; they return empty dicts or permissive defaults
on any failure.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from statebind.data.paths import DataPaths

if TYPE_CHECKING:
    import torch  # noqa: I001

    from statebind.ml.admet import MultiTaskADMET

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton (lazy-loaded on first predict call)
# ---------------------------------------------------------------------------

_MODEL: MultiTaskADMET | None = None
_DEVICE: torch.device | None = None
_LOAD_ATTEMPTED: bool = False

# ---------------------------------------------------------------------------
# Default ADMET thresholds for safety filtering
# ---------------------------------------------------------------------------

# Each entry: task_name -> (operator, threshold)
# ">" means FAIL if prediction exceeds threshold (unsafe above)
# "<" means FAIL if prediction is below threshold (unsafe below)
DEFAULT_ADMET_THRESHOLDS: dict[str, tuple[str, float]] = {
    "herg": (">", 0.5),
    "cyp3a4": (">", 0.7),
    "caco2": ("<", -6.0),
    "clearance": (">", 50.0),
    "lipophilicity": (">", 5.0),
    "solubility": ("<", -5.0),
}


# ---------------------------------------------------------------------------
# Threshold-based safety check (no torch needed)
# ---------------------------------------------------------------------------


def check_admet_pass(
    predictions: dict[str, float],
    thresholds: dict[str, tuple[str, float]] | None = None,
) -> tuple[bool, list[str]]:
    """Check whether ADMET predictions pass safety thresholds.

    Pure Python -- no torch dependency.  Returns a permissive pass when
    *predictions* is empty (graceful fallback when no model is available).

    Args:
        predictions: Dictionary mapping task name to predicted value.
            Typically the output of :func:`predict_admet`.
        thresholds: Per-task thresholds.  Each value is a ``(operator,
            limit)`` tuple where *operator* is ``">"`` (fail if prediction
            exceeds *limit*) or ``"<"`` (fail if prediction is below
            *limit*).  Defaults to :data:`DEFAULT_ADMET_THRESHOLDS`.

    Returns:
        A ``(passed, failures)`` tuple.  *passed* is ``True`` when all
        checked endpoints are within safe limits.  *failures* is a list
        of task names that violated their threshold.
    """
    if not predictions:
        return (True, [])

    if thresholds is None:
        thresholds = DEFAULT_ADMET_THRESHOLDS

    failures: list[str] = []
    for task_name, (operator, limit) in thresholds.items():
        if task_name not in predictions:
            continue
        value = predictions[task_name]
        if operator == ">" and value > limit:
            failures.append(task_name)
        elif operator == "<" and value < limit:
            failures.append(task_name)

    passed = len(failures) == 0
    return (passed, failures)


# ---------------------------------------------------------------------------
# Singleton model loading
# ---------------------------------------------------------------------------


def _load_model(
    checkpoint_path: Path | str | None = None,
) -> tuple[Any, Any] | None:
    """Load the MultiTaskADMET model from a checkpoint.

    All torch imports are deferred to this function body so the module
    remains importable without torch installed.

    Args:
        checkpoint_path: Path to the saved checkpoint.  Defaults to
            ``{project_root}/artifacts/models/admet/best_model.pt``.

    Returns:
        A ``(model, device)`` tuple on success, or ``None`` on any failure
        (missing checkpoint, missing dependencies, architecture mismatch,
        etc.).  Never raises.
    """
    try:
        import torch  # noqa: I001

        from statebind.ml.admet import ADMETConfig, MultiTaskADMET
        from statebind.ml.utils import get_device
    except ImportError:
        logger.warning(
            "ADMET predictor requires torch, torch_geometric, and rdkit. "
            "Returning None (predictions will fall back to empty dict)."
        )
        return None

    if checkpoint_path is None:
        checkpoint_path = (
            DataPaths().root / "artifacts" / "models" / "admet" / "best_model.pt"
        )
    checkpoint_path = Path(checkpoint_path)

    if not checkpoint_path.exists():
        logger.warning(
            "ADMET checkpoint not found at %s. "
            "Predictions will fall back to empty dict.",
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
            config = ADMETConfig(**checkpoint["config"])
        else:
            config = ADMETConfig()

        model = MultiTaskADMET(config)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        model.eval()

        logger.info(
            "ADMET model loaded from %s on device %s",
            checkpoint_path,
            device,
        )
        return (model, device)

    except Exception:
        logger.warning(
            "Failed to load ADMET model from %s. "
            "Predictions will fall back to empty dict.",
            checkpoint_path,
            exc_info=True,
        )
        return None


# ---------------------------------------------------------------------------
# Single-molecule prediction
# ---------------------------------------------------------------------------


def predict_admet(
    smiles: str,
    checkpoint_path: Path | str | None = None,
) -> dict[str, float]:
    """Predict ADMET properties for a single SMILES string.

    Uses a module-level singleton: the model is loaded once on the first
    call and reused for all subsequent calls.  If the model cannot be
    loaded (missing checkpoint, missing torch, etc.), returns an empty
    dictionary.

    Args:
        smiles: A SMILES string representing a molecule.
        checkpoint_path: Optional override for the model checkpoint path.
            Only used on the very first call (when the singleton is
            initialized).

    Returns:
        Dictionary mapping task name to predicted float value (rounded to
        4 decimal places).  Classification tasks have sigmoid applied.
        Returns ``{}`` on any failure.
    """
    global _MODEL, _DEVICE, _LOAD_ATTEMPTED

    # Lazy singleton initialization
    if _MODEL is None and not _LOAD_ATTEMPTED:
        _LOAD_ATTEMPTED = True
        result = _load_model(checkpoint_path)
        if result is not None:
            _MODEL, _DEVICE = result

    if _MODEL is None:
        return {}

    try:
        from statebind.ml.graphs import smiles_to_graph

        graph = smiles_to_graph(smiles)
        if graph is None:
            logger.debug("Failed to convert SMILES to graph: %s", smiles)
            return {}

        graph = graph.to(_DEVICE)
        return _MODEL.predict(graph)

    except Exception:
        logger.warning(
            "ADMET prediction failed for SMILES: %s",
            smiles,
            exc_info=True,
        )
        return {}


# ---------------------------------------------------------------------------
# Batch prediction
# ---------------------------------------------------------------------------

_BATCH_CHUNK_SIZE: int = 256


def predict_admet_batch(
    smiles_list: list[str],
    checkpoint_path: Path | str | None = None,
) -> list[dict[str, float]]:
    """Predict ADMET properties for a list of SMILES strings.

    Uses batched inference via ``torch_geometric.data.Batch`` for
    efficiency.  Falls back to individual predictions if batching fails.

    Args:
        smiles_list: List of SMILES strings.
        checkpoint_path: Optional override for the model checkpoint path
            (only used on first call for singleton init).

    Returns:
        A list of dictionaries, one per input SMILES.  Each dictionary
        maps task name to predicted float (rounded to 4 dp).  Failed
        SMILES produce empty dicts.  The output list is always the same
        length as the input list.
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
        return [{} for _ in smiles_list]

    # Try batched inference
    try:
        return _predict_batch_internal(smiles_list)
    except Exception:
        logger.warning(
            "Batch ADMET prediction failed, falling back to individual predictions.",
            exc_info=True,
        )
        # Fall back to individual predictions
        return [predict_admet(smi) for smi in smiles_list]


def _predict_batch_internal(
    smiles_list: list[str],
) -> list[dict[str, float]]:
    """Internal batched prediction using PyG Batch.

    Converts all SMILES to graphs, batches them in chunks of
    :data:`_BATCH_CHUNK_SIZE`, runs the model forward pass, and
    post-processes results (sigmoid for classification, rounding).

    Args:
        smiles_list: List of SMILES strings.

    Returns:
        List of prediction dicts, same length as input.

    Raises:
        Any exception from torch or PyG (caller catches).
    """
    import torch
    from torch_geometric.data import Batch

    from statebind.ml.graphs import smiles_to_graph

    assert _MODEL is not None
    assert _DEVICE is not None

    # Convert all SMILES to graphs, tracking which indices succeeded
    results: list[dict[str, float]] = [{} for _ in smiles_list]
    graphs: list[Any] = []
    valid_indices: list[int] = []

    for idx, smi in enumerate(smiles_list):
        graph = smiles_to_graph(smi)
        if graph is not None:
            graphs.append(graph)
            valid_indices.append(idx)

    if not graphs:
        return results

    # Get task types for post-processing
    task_types = _MODEL.config.task_types

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
                raw_predictions = _MODEL.forward(batch)

            # Post-process: extract per-molecule results
            batch_size = len(chunk_graphs)
            for i in range(batch_size):
                original_idx = chunk_valid_indices[i]
                prediction: dict[str, float] = {}

                for task_name, tensor in raw_predictions.items():
                    value = tensor[i].squeeze().item()
                    # Apply sigmoid for classification tasks
                    if task_types.get(task_name) == "classification":
                        value = torch.sigmoid(torch.tensor(value)).item()
                    prediction[task_name] = round(value, 4)

                results[original_idx] = prediction
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
    :func:`predict_admet` or :func:`predict_admet_batch` call will
    attempt to reload the model.
    """
    global _MODEL, _DEVICE, _LOAD_ATTEMPTED
    _MODEL = None
    _DEVICE = None
    _LOAD_ATTEMPTED = False
