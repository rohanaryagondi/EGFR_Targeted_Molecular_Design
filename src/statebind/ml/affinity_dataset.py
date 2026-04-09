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

try:
    from rdkit import Chem as _Chem  # noqa: I001
    from rdkit.Chem.Scaffolds.MurckoScaffold import (
        GetScaffoldForMol as _GetScaffoldForMol,
        MakeScaffoldGeneric as _MakeScaffoldGeneric,
    )

    HAS_SCAFFOLD = True
except ImportError:
    HAS_SCAFFOLD = False

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
    split_type: str = Field(
        default="random",
        description=(
            "Split strategy: 'random' (seeded permutation), "
            "'scaffold' (Murcko scaffold grouping), or "
            "'temporal' (year-ordered chronological)."
        ),
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
        years: list[int] | None = None,
    ) -> None:
        _require_torch()
        super().__init__()
        self.graphs: list[Data] = graphs
        self.smiles_list: list[str] = smiles_list or [
            getattr(g, "smiles", "") for g in graphs
        ]
        self.years: list[int] | None = years

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


def _subset(
    dataset: AffinityDataset, idx: np.ndarray | list[int]
) -> AffinityDataset:
    """Create a subset of *dataset* from the given indices.

    Keeps ``graphs``, ``smiles_list``, and ``years`` aligned.
    """
    graphs = [dataset.graphs[i] for i in idx]
    smiles = [dataset.smiles_list[i] for i in idx]
    years = (
        [dataset.years[i] for i in idx]
        if dataset.years is not None
        else None
    )
    return AffinityDataset(graphs=graphs, smiles_list=smiles, years=years)


def split_dataset(
    dataset: AffinityDataset,
    config: AffinityDatasetConfig | None = None,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
    split_type: str = "random",
) -> tuple[AffinityDataset, AffinityDataset, AffinityDataset]:
    """Split an :class:`AffinityDataset` into train / validation / test sets.

    Supports three split strategies:

    - ``"random"`` -- seeded random permutation (original behavior).
    - ``"scaffold"`` -- group by Murcko scaffold so molecules sharing a
      scaffold never appear in different splits. Requires RDKit.
    - ``"temporal"`` -- chronological split by publication year. Requires
      ``dataset.years`` to be populated.

    Args:
        dataset: The full dataset to split.
        config: If provided, split ratios, seed, and split_type are taken
            from the config.  Explicit keyword arguments override config
            values when *config* is ``None``.
        train_ratio: Fraction for training (default 0.8).
        val_ratio: Fraction for validation (default 0.1).
        test_ratio: Fraction for test (default 0.1).
        seed: Random seed (default 42).
        split_type: ``"random"``, ``"scaffold"``, or ``"temporal"``.

    Returns:
        A tuple ``(train_dataset, val_dataset, test_dataset)``.

    Raises:
        ValueError: If ratios do not sum to approximately 1.0, or if
            *split_type* is not recognised.
        ImportError: If ``split_type="scaffold"`` and RDKit is not installed.
    """
    _require_torch()

    # Override defaults with config if provided
    if config is not None:
        train_ratio = config.train_ratio
        val_ratio = config.val_ratio
        test_ratio = config.test_ratio
        seed = config.seed
        split_type = config.split_type

    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"Split ratios must sum to 1.0, got "
            f"{train_ratio} + {val_ratio} + {test_ratio} = {total}"
        )

    if split_type == "scaffold":
        return scaffold_split(
            dataset,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            seed=seed,
        )
    if split_type == "temporal":
        return temporal_split(
            dataset,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
        )
    if split_type == "random":
        return _random_split(
            dataset,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            seed=seed,
        )

    raise ValueError(
        f"Unknown split_type '{split_type}'. "
        "Expected 'random', 'scaffold', or 'temporal'."
    )


# ---------------------------------------------------------------------------
# Split implementations
# ---------------------------------------------------------------------------


def _random_split(
    dataset: AffinityDataset,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[AffinityDataset, AffinityDataset, AffinityDataset]:
    """Random permutation split (original default behaviour)."""
    n = len(dataset)
    rng = np.random.RandomState(seed)
    indices = rng.permutation(n)

    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    # Remainder goes to test to avoid off-by-one rounding
    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    train_ds = _subset(dataset, train_idx)
    val_ds = _subset(dataset, val_idx)
    test_ds = _subset(dataset, test_idx)

    logger.info(
        "Random split: train=%d, val=%d, test=%d (seed=%d)",
        len(train_ds),
        len(val_ds),
        len(test_ds),
        seed,
    )

    return train_ds, val_ds, test_ds


def scaffold_split(
    dataset: AffinityDataset,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[AffinityDataset, AffinityDataset, AffinityDataset]:
    """Split *dataset* so molecules sharing a Murcko scaffold stay together.

    Scaffolds are shuffled (seeded) and greedily assigned to train / val /
    test to approximate the requested ratios.  Molecules whose SMILES cannot
    be parsed by RDKit are placed in the training set with a warning.

    Args:
        dataset: Full :class:`AffinityDataset`.
        train_ratio: Target fraction for training.
        val_ratio: Target fraction for validation.
        test_ratio: Target fraction for test.
        seed: Random seed for scaffold shuffling.

    Returns:
        ``(train, val, test)`` :class:`AffinityDataset` tuple.

    Raises:
        ImportError: If RDKit is not installed.
    """
    if not HAS_SCAFFOLD:
        raise ImportError(
            "scaffold_split requires RDKit. Install with: "
            "pip install rdkit-pypi"
        )

    n = len(dataset)

    # --- group indices by generic Murcko scaffold ---
    scaffold_to_indices: dict[str, list[int]] = {}
    unparseable_indices: list[int] = []

    for i, smi in enumerate(dataset.smiles_list):
        mol = _Chem.MolFromSmiles(smi)
        if mol is None:
            logger.warning(
                "scaffold_split: could not parse SMILES '%s' "
                "(index %d); assigning to training set.",
                smi,
                i,
            )
            unparseable_indices.append(i)
            continue

        core = _GetScaffoldForMol(mol)
        generic = _MakeScaffoldGeneric(core)
        scaffold_smi = _Chem.MolToSmiles(generic)

        scaffold_to_indices.setdefault(scaffold_smi, []).append(i)

    # --- shuffle scaffolds (not individual molecules) ---
    rng = np.random.RandomState(seed)
    scaffolds = list(scaffold_to_indices.keys())
    rng.shuffle(scaffolds)

    # --- greedy assignment to approximate target ratios ---
    train_indices: list[int] = list(unparseable_indices)
    val_indices: list[int] = []
    test_indices: list[int] = []

    train_target = train_ratio * n
    val_target = val_ratio * n
    test_target = test_ratio * n

    for scaffold_key in scaffolds:
        members = scaffold_to_indices[scaffold_key]

        # Compute how far each bucket is from its target
        train_gap = train_target - len(train_indices)
        val_gap = val_target - len(val_indices)
        test_gap = test_target - len(test_indices)

        # Assign to the bucket that is furthest below its target
        max_gap = max(train_gap, val_gap, test_gap)
        if max_gap == train_gap:
            train_indices.extend(members)
        elif max_gap == val_gap:
            val_indices.extend(members)
        else:
            test_indices.extend(members)

    train_ds = _subset(dataset, train_indices)
    val_ds = _subset(dataset, val_indices)
    test_ds = _subset(dataset, test_indices)

    logger.info(
        "Scaffold split: train=%d, val=%d, test=%d "
        "(%d scaffolds, %d unparseable -> train, seed=%d)",
        len(train_ds),
        len(val_ds),
        len(test_ds),
        len(scaffolds),
        len(unparseable_indices),
        seed,
    )

    return train_ds, val_ds, test_ds


def temporal_split(
    dataset: AffinityDataset,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    year_column: str = "year",
) -> tuple[AffinityDataset, AffinityDataset, AffinityDataset]:
    """Split *dataset* chronologically so the test set contains the newest data.

    Molecules are sorted by year (earliest first). The first
    ``train_ratio`` fraction becomes train, the next ``val_ratio``
    fraction becomes validation, and the remainder becomes test.

    Args:
        dataset: Full :class:`AffinityDataset` with ``years`` populated.
        train_ratio: Target fraction for training.
        val_ratio: Target fraction for validation.
        test_ratio: Target fraction for test.
        year_column: Unused (kept for API symmetry with config keys).

    Returns:
        ``(train, val, test)`` :class:`AffinityDataset` tuple.

    Raises:
        ValueError: If ``dataset.years`` is ``None`` or empty.
    """
    if dataset.years is None or len(dataset.years) == 0:
        raise ValueError(
            "temporal_split requires dataset.years to be populated. "
            "Provide a list of integer years when constructing AffinityDataset."
        )

    if len(dataset.years) != len(dataset):
        raise ValueError(
            f"dataset.years length ({len(dataset.years)}) does not match "
            f"dataset length ({len(dataset)})."
        )

    n = len(dataset)
    # Sort indices by year (ascending -- earliest first)
    sorted_indices = np.argsort(dataset.years).tolist()

    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train_idx = sorted_indices[:n_train]
    val_idx = sorted_indices[n_train : n_train + n_val]
    test_idx = sorted_indices[n_train + n_val :]

    train_ds = _subset(dataset, train_idx)
    val_ds = _subset(dataset, val_idx)
    test_ds = _subset(dataset, test_idx)

    logger.info(
        "Temporal split: train=%d (years <=%s), val=%d, test=%d (years >=%s)",
        len(train_ds),
        max(dataset.years[i] for i in train_idx) if train_idx else "?",
        len(val_ds),
        len(test_ds),
        min(dataset.years[i] for i in test_idx) if test_idx else "?",
    )

    return train_ds, val_ds, test_ds
