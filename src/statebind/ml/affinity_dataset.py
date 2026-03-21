"""Dataset for loading molecular graphs with pIC50 binding affinity labels.

Provides :class:`AffinityDataset`, a PyTorch Dataset that converts SMILES
strings to PyTorch Geometric :class:`~torch_geometric.data.Data` objects
(via :func:`~statebind.ml.graphs.smiles_to_graph`) and attaches a ``y``
attribute containing the pIC50 binding affinity as a :class:`~torch.FloatTensor`.

Expected JSON format::

    [
        {"smiles": "CCO", "pIC50": 5.2},
        {"smiles": "c1ccccc1", "pIC50": 6.1},
        ...
    ]

Optional dependencies:
    torch             -- tensor operations and Dataset base class
    torch_geometric   -- Data objects (via graphs.py)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, Field, field_validator

from statebind.ml.graphs import smiles_to_graph

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------

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

if TYPE_CHECKING:
    from torch_geometric.data import Data

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime guard helper
# ---------------------------------------------------------------------------

def _require_torch() -> None:
    """Raise RuntimeError if torch is not installed."""
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for AffinityDataset but is not installed. "
            "Install it with: pip install torch"
        )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class AffinityDatasetConfig(BaseModel):
    """Configuration for loading and splitting an affinity dataset.

    Attributes:
        data_path: Path to the JSON file containing SMILES/pIC50 records.
        smiles_column: Key name for the SMILES string in each JSON record.
        target_column: Key name for the pIC50 value in each JSON record.
        train_ratio: Fraction of data for the training split.
        val_ratio: Fraction of data for the validation split.
        test_ratio: Fraction of data for the test split (computed as the
            remainder if not explicitly set).
        seed: Random seed for reproducible splitting.
        max_samples: If set, cap the total number of samples loaded.
            Useful for debugging or quick experiments.
    """

    data_path: str = Field(
        description="Path to JSON file with SMILES and pIC50 records."
    )
    smiles_column: str = Field(
        default="smiles",
        description="Key name for SMILES in JSON records.",
    )
    target_column: str = Field(
        default="pIC50",
        description="Key name for binding affinity target in JSON records.",
    )
    train_ratio: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Training split fraction."
    )
    val_ratio: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Validation split fraction."
    )
    test_ratio: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Test split fraction."
    )
    seed: int = Field(default=42, description="Random seed for splitting.")
    max_samples: int | None = Field(
        default=None, description="Cap on total samples loaded (None = no cap)."
    )

    @field_validator("test_ratio")
    @classmethod
    def _ratios_sum_to_one(cls, v: float, info: object) -> float:
        """Validate that train + val + test ratios sum to approximately 1.0."""
        data = info.data if hasattr(info, "data") else {}
        train = data.get("train_ratio", 0.8)
        val = data.get("val_ratio", 0.1)
        total = train + val + v
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Split ratios must sum to 1.0, got "
                f"{train} + {val} + {v} = {total}"
            )
        return v


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

# Conditional base class: inherit from torch Dataset when available,
# otherwise from object to allow import without torch.
_BaseClass = Dataset if HAS_TORCH else object


class AffinityDataset(_BaseClass):
    """Dataset of molecular graphs with pIC50 binding affinity labels.

    Each item is a PyTorch Geometric :class:`~torch_geometric.data.Data`
    object with:

    - ``x`` — atom feature matrix ``(num_atoms, ATOM_FEATURE_DIM)``
    - ``edge_index`` — COO edge index ``(2, num_edges)``
    - ``edge_attr`` — bond feature matrix ``(num_edges, BOND_FEATURE_DIM)``
    - ``smiles`` — the original SMILES string
    - ``y`` — pIC50 value as a :class:`~torch.FloatTensor` of shape ``(1,)``

    Invalid SMILES (those where :func:`smiles_to_graph` returns ``None``)
    are silently filtered out during construction.

    Args:
        graphs: Pre-built list of PyG Data objects with ``y`` attributes.
        smiles_list: Corresponding SMILES strings (for provenance tracking).
    """

    def __init__(
        self,
        graphs: list[Data],
        smiles_list: list[str] | None = None,
    ) -> None:
        _require_torch()
        super().__init__()
        self.graphs: list[Data] = graphs
        self.smiles_list: list[str] = smiles_list or [
            getattr(g, "smiles", "") for g in graphs
        ]

    def __len__(self) -> int:
        """Return the number of valid molecular graphs in the dataset."""
        return len(self.graphs)

    def __getitem__(self, idx: int) -> Data:
        """Return the PyG Data object at the given index.

        Args:
            idx: Integer index.

        Returns:
            A :class:`~torch_geometric.data.Data` object with a ``y``
            attribute containing the pIC50 as a FloatTensor of shape ``(1,)``.
        """
        return self.graphs[idx]

    @property
    def targets(self) -> list[float]:
        """Return all pIC50 targets as a flat list of floats."""
        return [float(g.y.item()) for g in self.graphs]

    def summary(self) -> dict[str, float | int]:
        """Return summary statistics for the dataset.

        Returns:
            Dictionary with keys: ``n_samples``, ``mean_pIC50``,
            ``std_pIC50``, ``min_pIC50``, ``max_pIC50``.
        """
        if len(self.graphs) == 0:
            return {
                "n_samples": 0,
                "mean_pIC50": 0.0,
                "std_pIC50": 0.0,
                "min_pIC50": 0.0,
                "max_pIC50": 0.0,
            }
        values = np.array(self.targets)
        return {
            "n_samples": len(self.graphs),
            "mean_pIC50": round(float(np.mean(values)), 4),
            "std_pIC50": round(float(np.std(values)), 4),
            "min_pIC50": round(float(np.min(values)), 4),
            "max_pIC50": round(float(np.max(values)), 4),
        }


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------


def _build_graphs_from_records(
    records: list[dict],
    smiles_column: str,
    target_column: str,
    max_samples: int | None = None,
) -> tuple[list[Data], list[str], int]:
    """Convert raw JSON records to PyG Data objects with pIC50 labels.

    Args:
        records: List of dicts with SMILES and pIC50 keys.
        smiles_column: Key for SMILES in each record.
        target_column: Key for pIC50 in each record.
        max_samples: Maximum number of samples to process.

    Returns:
        Tuple of (graphs, smiles_list, n_skipped).
    """
    _require_torch()

    if max_samples is not None:
        records = records[:max_samples]

    graphs: list[Data] = []
    smiles_list: list[str] = []
    n_skipped = 0

    for record in records:
        smi = record.get(smiles_column)
        target = record.get(target_column)

        if smi is None or target is None:
            n_skipped += 1
            continue

        # Validate target is numeric
        try:
            pic50 = float(target)
        except (ValueError, TypeError):
            logger.debug("Non-numeric pIC50 for SMILES %s: %s", smi, target)
            n_skipped += 1
            continue

        # Convert SMILES to graph
        graph = smiles_to_graph(smi)
        if graph is None:
            logger.debug("Failed to convert SMILES to graph: %s", smi)
            n_skipped += 1
            continue

        # Attach target label
        graph.y = torch.tensor([pic50], dtype=torch.float)
        graphs.append(graph)
        smiles_list.append(smi)

    return graphs, smiles_list, n_skipped


def load_affinity_dataset(
    path: str | Path,
    config: AffinityDatasetConfig | None = None,
) -> AffinityDataset:
    """Load a dataset of molecular graphs with pIC50 labels from a JSON file.

    The JSON file should contain a list of objects, each with at least a
    SMILES field and a pIC50 field::

        [
            {"smiles": "CCO", "pIC50": 5.2},
            {"smiles": "c1ccccc1", "pIC50": 6.1}
        ]

    Invalid SMILES (where :func:`~statebind.ml.graphs.smiles_to_graph`
    returns ``None``) are silently filtered out.

    Args:
        path: Path to the JSON file.
        config: Optional configuration.  If ``None``, a default
            :class:`AffinityDatasetConfig` is created with the given path.

    Returns:
        An :class:`AffinityDataset` containing all valid molecular graphs.

    Raises:
        FileNotFoundError: If *path* does not exist.
        RuntimeError: If torch is not installed.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    _require_torch()

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    if config is None:
        config = AffinityDatasetConfig(data_path=str(path))

    with open(path) as f:
        records: list[dict] = json.load(f)

    if not isinstance(records, list):
        raise ValueError(
            f"Expected a JSON list of records, got {type(records).__name__}"
        )

    graphs, smiles_list, n_skipped = _build_graphs_from_records(
        records=records,
        smiles_column=config.smiles_column,
        target_column=config.target_column,
        max_samples=config.max_samples,
    )

    logger.info(
        "Loaded %d graphs from %s (%d records skipped)",
        len(graphs),
        path,
        n_skipped,
    )

    return AffinityDataset(graphs=graphs, smiles_list=smiles_list)


def split_dataset(
    dataset: AffinityDataset,
    config: AffinityDatasetConfig | None = None,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[AffinityDataset, AffinityDataset, AffinityDataset]:
    """Split an :class:`AffinityDataset` into train / validation / test sets.

    Uses a seeded random permutation to ensure reproducibility.

    Args:
        dataset: The full dataset to split.
        config: If provided, split ratios and seed are taken from the config.
            Explicit keyword arguments override config values.
        train_ratio: Fraction for training (default 0.8).
        val_ratio: Fraction for validation (default 0.1).
        test_ratio: Fraction for test (default 0.1).
        seed: Random seed (default 42).

    Returns:
        A tuple ``(train_dataset, val_dataset, test_dataset)``.

    Raises:
        ValueError: If ratios do not sum to approximately 1.0.
    """
    _require_torch()

    # Override defaults with config if provided
    if config is not None:
        train_ratio = config.train_ratio
        val_ratio = config.val_ratio
        test_ratio = config.test_ratio
        seed = config.seed

    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"Split ratios must sum to 1.0, got "
            f"{train_ratio} + {val_ratio} + {test_ratio} = {total}"
        )

    n = len(dataset)
    rng = np.random.RandomState(seed)
    indices = rng.permutation(n)

    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    # Remainder goes to test to avoid off-by-one rounding
    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    def _subset(idx: np.ndarray) -> AffinityDataset:
        graphs = [dataset.graphs[i] for i in idx]
        smiles = [dataset.smiles_list[i] for i in idx]
        return AffinityDataset(graphs=graphs, smiles_list=smiles)

    train_ds = _subset(train_idx)
    val_ds = _subset(val_idx)
    test_ds = _subset(test_idx)

    logger.info(
        "Split dataset: train=%d, val=%d, test=%d (seed=%d)",
        len(train_ds),
        len(val_ds),
        len(test_ds),
        seed,
    )

    return train_ds, val_ds, test_ds
