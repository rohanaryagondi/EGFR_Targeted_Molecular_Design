"""Dataset for multi-task ADMET prediction.

Loads molecular SMILES with multi-task ADMET labels, converts each molecule
to a PyTorch Geometric graph (via :func:`statebind.ml.graphs.smiles_to_graph`),
and attaches a label vector with NaN-masking for missing endpoints.

Expected input format (JSON)::

    [
        {"smiles": "CCO", "caco2": -5.12, "herg": 0.0, "cyp3a4": null, ...},
        {"smiles": "c1ccccc1", "caco2": null, "herg": 1.0, ...},
        ...
    ]

Each item returns a PyG Data object augmented with:
    - ``y``:  FloatTensor of shape ``(n_tasks,)`` — labels (NaN for missing)
    - ``task_mask``: BoolTensor of shape ``(n_tasks,)`` — True for available labels

Optional dependencies:
    torch             — required for tensor construction
    torch_geometric   — required for PyG Data objects
    rdkit             — required for SMILES parsing (via graphs module)
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field, field_validator

try:
    import torch
    from torch.utils.data import Dataset

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from torch_geometric.data import Data

    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False

from statebind.ml.graphs import smiles_to_graph

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default task names (must match ADMETConfig defaults)
# ---------------------------------------------------------------------------

_DEFAULT_TASK_NAMES: list[str] = [
    "caco2",
    "herg",
    "cyp3a4",
    "clearance",
    "lipophilicity",
    "solubility",
]

# ---------------------------------------------------------------------------
# Pydantic configuration
# ---------------------------------------------------------------------------


class ADMETDatasetConfig(BaseModel):
    """Configuration for loading and splitting an ADMET dataset.

    Attributes:
        data_path: Path to the JSON file containing SMILES and labels.
        task_names: Ordered list of ADMET endpoint names to extract.
        train_frac: Fraction of data for the training split.
        val_frac: Fraction of data for the validation split.
        test_frac: Fraction of data for the test split.
        seed: Random seed for reproducible splitting.
        min_tasks: Minimum number of non-null labels a molecule must have
            to be included in the dataset.  Set to 0 to keep all molecules.
    """

    data_path: str = ""
    task_names: list[str] = Field(default_factory=lambda: list(_DEFAULT_TASK_NAMES))
    train_frac: float = 0.8
    val_frac: float = 0.1
    test_frac: float = 0.1
    seed: int = 42
    min_tasks: int = 1

    @field_validator("train_frac", "val_frac", "test_frac")
    @classmethod
    def _validate_fractions(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Split fraction must be in [0.0, 1.0], got {v}")
        return v


# ---------------------------------------------------------------------------
# Torch dependency guard
# ---------------------------------------------------------------------------


def _require_deps() -> None:
    """Raise RuntimeError if required dependencies are missing."""
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for ADMETDataset but is not installed. "
            "Install it with: pip install torch"
        )
    if not HAS_TORCH_GEOMETRIC:
        raise RuntimeError(
            "PyTorch Geometric is required for ADMETDataset but is not installed. "
            "Install it with: pip install torch_geometric"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_label(value: Any) -> float:
    """Convert a raw JSON label value to a float, using NaN for missing.

    Args:
        value: A numeric value, ``None``, or ``"null"`` / ``"nan"`` string.

    Returns:
        The numeric value as a float, or ``float('nan')`` if missing.
    """
    if value is None:
        return float("nan")
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ("null", "none", "nan", ""):
            return float("nan")
        try:
            return float(lower)
        except ValueError:
            return float("nan")
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return float("nan")
        return float(value)
    return float("nan")


def _records_from_json(path: Path) -> list[dict[str, Any]]:
    """Load a JSON file and return a list of record dicts.

    Handles both JSON arrays ``[{...}, ...]`` and newline-delimited JSON.

    Args:
        path: Path to the JSON file.

    Returns:
        List of record dictionaries.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file cannot be parsed as JSON records.
    """
    if not path.exists():
        raise FileNotFoundError(f"ADMET data file not found: {path}")

    text = path.read_text(encoding="utf-8").strip()

    # Try standard JSON array first
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        raise ValueError(
            f"Expected a JSON array at top level, got {type(data).__name__}"
        )
    except json.JSONDecodeError:
        pass

    # Fall back to newline-delimited JSON
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                records.append(obj)
            else:
                logger.warning(
                    "Line %d: expected dict, got %s — skipped",
                    line_no,
                    type(obj).__name__,
                )
        except json.JSONDecodeError:
            logger.warning("Line %d: invalid JSON — skipped", line_no)

    if not records:
        raise ValueError(f"No valid JSON records found in {path}")

    return records


# ---------------------------------------------------------------------------
# Dataset class
# ---------------------------------------------------------------------------

if HAS_TORCH and HAS_TORCH_GEOMETRIC:

    class ADMETDataset(Dataset):  # type: ignore[type-arg]
        """Dataset of molecular graphs with multi-task ADMET labels.

        Each item is a PyG :class:`~torch_geometric.data.Data` object containing:

        - ``x``: Atom feature matrix ``(num_atoms, atom_feature_dim)``
        - ``edge_index``: COO edge index ``(2, num_edges)``
        - ``edge_attr``: Bond feature matrix ``(num_edges, bond_feature_dim)``
        - ``smiles``: Original SMILES string
        - ``y``: FloatTensor of shape ``(n_tasks,)`` — labels (NaN for missing)
        - ``task_mask``: BoolTensor of shape ``(n_tasks,)`` — True where label
          is available

        Args:
            graphs: List of PyG Data objects (molecular graphs).
            labels: NumPy array of shape ``(n_molecules, n_tasks)`` with NaN
                for missing labels.
            task_names: Ordered list of task names.
        """

        def __init__(
            self,
            graphs: list[Data],
            labels: np.ndarray,
            task_names: list[str],
        ) -> None:
            super().__init__()
            if len(graphs) != len(labels):
                raise ValueError(
                    f"Number of graphs ({len(graphs)}) does not match number of "
                    f"label rows ({len(labels)})"
                )
            self.graphs = graphs
            self.labels = labels
            self.task_names = task_names

        def __len__(self) -> int:
            return len(self.graphs)

        def __getitem__(self, idx: int) -> Data:
            data = self.graphs[idx]

            label_row = self.labels[idx]
            y = torch.tensor(label_row, dtype=torch.float)
            task_mask = ~torch.isnan(y)

            # Attach labels to the Data object (clone to avoid mutation)
            data = data.clone()
            data.y = y
            data.task_mask = task_mask

            return data

        @property
        def n_tasks(self) -> int:
            """Number of ADMET endpoints."""
            return len(self.task_names)

        def label_coverage(self) -> dict[str, float]:
            """Fraction of non-NaN labels per task.

            Returns:
                Dictionary mapping task name to coverage fraction in [0, 1].
            """
            n = len(self.labels)
            if n == 0:
                return {name: 0.0 for name in self.task_names}
            coverage: dict[str, float] = {}
            for i, name in enumerate(self.task_names):
                valid = np.sum(~np.isnan(self.labels[:, i]))
                coverage[name] = round(float(valid) / n, 4)
            return coverage


# ---------------------------------------------------------------------------
# Loading and splitting
# ---------------------------------------------------------------------------


def load_admet_dataset(
    path: str | Path,
    config: ADMETDatasetConfig | None = None,
) -> ADMETDataset:
    """Load an ADMET dataset from a JSON file.

    Each record must have a ``"smiles"`` key.  Task labels are extracted by
    the names listed in ``config.task_names``; missing keys or ``null``
    values are stored as NaN.

    Records are filtered by ``config.min_tasks`` (molecules with fewer
    non-null labels are dropped).  Molecules whose SMILES cannot be
    converted to a graph are also dropped.

    Args:
        path: Path to the JSON file.
        config: Dataset configuration.  If ``None``, defaults are used.

    Returns:
        An :class:`ADMETDataset` instance.

    Raises:
        RuntimeError: If torch or torch_geometric are not installed.
        FileNotFoundError: If *path* does not exist.
        ValueError: If no valid molecules remain after filtering.
    """
    _require_deps()

    if config is None:
        config = ADMETDatasetConfig()

    path = Path(path)
    records = _records_from_json(path)
    logger.info("Loaded %d raw records from %s", len(records), path)

    task_names = config.task_names

    graphs: list[Data] = []
    label_rows: list[list[float]] = []
    skipped_smiles = 0
    skipped_min_tasks = 0

    for record in records:
        smiles = record.get("smiles")
        if not smiles or not isinstance(smiles, str):
            skipped_smiles += 1
            continue

        # Extract labels
        row = [_parse_label(record.get(name)) for name in task_names]
        n_valid = sum(1 for v in row if not math.isnan(v))

        if n_valid < config.min_tasks:
            skipped_min_tasks += 1
            continue

        # Convert SMILES to graph
        graph = smiles_to_graph(smiles)
        if graph is None:
            skipped_smiles += 1
            continue

        graphs.append(graph)
        label_rows.append(row)

    if skipped_smiles > 0:
        logger.info("Skipped %d records (invalid/missing SMILES)", skipped_smiles)
    if skipped_min_tasks > 0:
        logger.info(
            "Skipped %d records (fewer than %d valid labels)",
            skipped_min_tasks,
            config.min_tasks,
        )

    if len(graphs) == 0:
        raise ValueError(
            f"No valid molecules remaining after filtering from {path}. "
            f"Ensure the file contains records with 'smiles' and at least "
            f"{config.min_tasks} non-null task labels."
        )

    labels = np.array(label_rows, dtype=np.float64)
    logger.info(
        "ADMET dataset: %d molecules, %d tasks", len(graphs), len(task_names)
    )

    return ADMETDataset(graphs=graphs, labels=labels, task_names=task_names)


def split_admet_dataset(
    dataset: ADMETDataset,
    config: ADMETDatasetConfig | None = None,
) -> tuple[ADMETDataset, ADMETDataset, ADMETDataset]:
    """Split an ADMET dataset into train / validation / test subsets.

    Uses a seeded random permutation to ensure reproducibility.  The
    fractions in *config* (``train_frac``, ``val_frac``, ``test_frac``)
    control split sizes.  They need not sum to exactly 1.0 — any remainder
    is absorbed by the training set.

    Args:
        dataset: The full :class:`ADMETDataset` to split.
        config: Configuration with split fractions and seed.  If ``None``,
            defaults are used.

    Returns:
        A ``(train, val, test)`` tuple of :class:`ADMETDataset` instances.

    Raises:
        RuntimeError: If torch or torch_geometric are not installed.
        ValueError: If the dataset is too small to split (fewer than 3
            molecules).
    """
    _require_deps()

    if config is None:
        config = ADMETDatasetConfig()

    n = len(dataset)
    if n < 3:
        raise ValueError(
            f"Dataset has only {n} molecules — too small to split into "
            f"train/val/test."
        )

    rng = np.random.RandomState(config.seed)
    indices = rng.permutation(n)

    n_val = max(1, int(round(n * config.val_frac)))
    n_test = max(1, int(round(n * config.test_frac)))
    n_train = n - n_val - n_test

    if n_train < 1:
        # Ensure at least 1 training example
        n_train = 1
        remaining = n - 1
        n_val = remaining // 2
        n_test = remaining - n_val

    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    def _subset(idx: np.ndarray) -> ADMETDataset:
        sub_graphs = [dataset.graphs[i] for i in idx]
        sub_labels = dataset.labels[idx]
        return ADMETDataset(
            graphs=sub_graphs,
            labels=sub_labels,
            task_names=dataset.task_names,
        )

    train_ds = _subset(train_idx)
    val_ds = _subset(val_idx)
    test_ds = _subset(test_idx)

    logger.info(
        "Split: train=%d, val=%d, test=%d",
        len(train_ds),
        len(val_ds),
        len(test_ds),
    )

    return train_ds, val_ds, test_ds
