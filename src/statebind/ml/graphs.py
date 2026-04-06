"""Molecular graph construction from SMILES.

Converts SMILES strings into PyTorch Geometric Data objects for GNN models.
Requires: rdkit, torch, torch_geometric

Atom features (~40-dim):
- Element (one-hot, top 10 elements)
- Degree (one-hot, 0-6)
- Formal charge (one-hot, -2 to +2)
- Hybridization (one-hot, sp/sp2/sp3/sp3d/sp3d2)
- Aromaticity (binary)
- In ring (binary)
- Number of Hs (one-hot, 0-4)

Bond features (~10-dim):
- Bond type (one-hot: single/double/triple/aromatic)
- Conjugated (binary)
- In ring (binary)
- Stereo (one-hot: none/Z/E/CIS/TRANS)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from rdkit import Chem
    from rdkit.Chem import rdchem  # noqa: F401 (accessed via Chem.rdchem)
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

try:
    from torch_geometric.data import Data
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False

if TYPE_CHECKING:
    from rdkit.Chem import Atom, Bond

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature vocabulary constants
# ---------------------------------------------------------------------------

# Top 10 elements in drug-like molecules (plus "other")
_ELEMENTS = ["C", "N", "O", "S", "F", "Cl", "Br", "P", "I", "Si"]
_ELEMENT_SET = set(_ELEMENTS)

# Degree: 0-6
_MAX_DEGREE = 6

# Formal charge: -2, -1, 0, +1, +2
_CHARGES = [-2, -1, 0, 1, 2]

# Hybridization types
_HYBRIDIZATIONS = [
    Chem.rdchem.HybridizationType.SP if HAS_RDKIT else 0,
    Chem.rdchem.HybridizationType.SP2 if HAS_RDKIT else 1,
    Chem.rdchem.HybridizationType.SP3 if HAS_RDKIT else 2,
    Chem.rdchem.HybridizationType.SP3D if HAS_RDKIT else 3,
    Chem.rdchem.HybridizationType.SP3D2 if HAS_RDKIT else 4,
]

# Max explicit Hs: 0-4
_MAX_HS = 4

# Bond stereo types
_BOND_STEREO = [
    Chem.rdchem.BondStereo.STEREONONE if HAS_RDKIT else 0,
    Chem.rdchem.BondStereo.STEREOZ if HAS_RDKIT else 1,
    Chem.rdchem.BondStereo.STEREOE if HAS_RDKIT else 2,
    Chem.rdchem.BondStereo.STEREOCIS if HAS_RDKIT else 3,
    Chem.rdchem.BondStereo.STEREOTRANS if HAS_RDKIT else 4,
]

# Bond types
_BOND_TYPES = [
    Chem.rdchem.BondType.SINGLE if HAS_RDKIT else 0,
    Chem.rdchem.BondType.DOUBLE if HAS_RDKIT else 1,
    Chem.rdchem.BondType.TRIPLE if HAS_RDKIT else 2,
    Chem.rdchem.BondType.AROMATIC if HAS_RDKIT else 3,
]

# Precomputed feature dimensions
# Element: 11 (10 + other) | Degree: 7 | Charge: 5 | Hybridization: 5 |
# Aromatic: 1 | In ring: 1 | Num Hs: 5 => 35
ATOM_FEATURE_DIM: int = (
    len(_ELEMENTS) + 1 + (_MAX_DEGREE + 1) + len(_CHARGES)
    + len(_HYBRIDIZATIONS) + 1 + 1 + (_MAX_HS + 1)
)

# Bond type: 4 | Conjugated: 1 | In ring: 1 | Stereo: 5 => 11
BOND_FEATURE_DIM: int = len(_BOND_TYPES) + 1 + 1 + len(_BOND_STEREO)


# ---------------------------------------------------------------------------
# One-hot encoding helper
# ---------------------------------------------------------------------------

def _one_hot(value: object, choices: list) -> list[float]:
    """Return a one-hot vector for *value* within *choices*.

    If *value* is not in *choices*, all entries are 0.0.
    """
    return [1.0 if value == c else 0.0 for c in choices]


def _one_hot_with_other(value: object, choices: list) -> list[float]:
    """One-hot with a trailing 'other' bit.

    If *value* is not in *choices*, the last (other) bit is 1.
    """
    vec = [1.0 if value == c else 0.0 for c in choices]
    vec.append(0.0 if any(v == 1.0 for v in vec) else 1.0)
    return vec


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def atom_features(atom: Atom) -> list[float]:
    """Compute the feature vector for a single atom.

    Args:
        atom: An RDKit :class:`~rdkit.Chem.rdchem.Atom`.

    Returns:
        A list of floats of length :data:`ATOM_FEATURE_DIM`.
    """
    features: list[float] = []

    # Element — one-hot over top 10 elements + "other" (11)
    features.extend(_one_hot_with_other(atom.GetSymbol(), _ELEMENTS))

    # Degree — one-hot 0..6 (7)
    features.extend(_one_hot(atom.GetDegree(), list(range(_MAX_DEGREE + 1))))

    # Formal charge — one-hot -2..+2 (5)
    features.extend(_one_hot(atom.GetFormalCharge(), _CHARGES))

    # Hybridization — one-hot (5)
    features.extend(_one_hot(atom.GetHybridization(), _HYBRIDIZATIONS))

    # Aromaticity (1)
    features.append(1.0 if atom.GetIsAromatic() else 0.0)

    # In ring (1)
    features.append(1.0 if atom.IsInRing() else 0.0)

    # Number of Hs — one-hot 0..4 (5)
    features.extend(_one_hot(atom.GetTotalNumHs(), list(range(_MAX_HS + 1))))

    return features


def bond_features(bond: Bond) -> list[float]:
    """Compute the feature vector for a single bond.

    Args:
        bond: An RDKit :class:`~rdkit.Chem.rdchem.Bond`.

    Returns:
        A list of floats of length :data:`BOND_FEATURE_DIM`.
    """
    features: list[float] = []

    # Bond type — one-hot (4)
    features.extend(_one_hot(bond.GetBondType(), _BOND_TYPES))

    # Conjugated (1)
    features.append(1.0 if bond.GetIsConjugated() else 0.0)

    # In ring (1)
    features.append(1.0 if bond.IsInRing() else 0.0)

    # Stereo — one-hot (5)
    features.extend(_one_hot(bond.GetStereo(), _BOND_STEREO))

    return features


# ---------------------------------------------------------------------------
# SMILES -> PyG Data
# ---------------------------------------------------------------------------

def smiles_to_graph(smiles: str) -> Data | None:
    """Convert a single SMILES string to a PyTorch Geometric Data object.

    The returned :class:`~torch_geometric.data.Data` object contains:

    - ``x`` — atom feature matrix of shape ``(num_atoms, ATOM_FEATURE_DIM)``
    - ``edge_index`` — COO edge index of shape ``(2, num_edges)``
      (edges are undirected, i.e. each bond appears twice)
    - ``edge_attr`` — bond feature matrix of shape ``(num_edges, BOND_FEATURE_DIM)``
    - ``smiles`` — the original SMILES string

    Args:
        smiles: A SMILES string.

    Returns:
        A :class:`~torch_geometric.data.Data` object, or ``None`` if the
        SMILES is invalid or required dependencies are missing.
    """
    if not (HAS_RDKIT and HAS_TORCH and HAS_TORCH_GEOMETRIC):
        logger.warning(
            "smiles_to_graph requires rdkit, torch, and torch_geometric. "
            "Returning None."
        )
        return None

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.debug("Invalid SMILES: %s", smiles)
        return None

    # --- Atom features ---
    atom_feat_list: list[list[float]] = []
    for atom in mol.GetAtoms():
        atom_feat_list.append(atom_features(atom))

    x = torch.tensor(atom_feat_list, dtype=torch.float)

    # --- Edge index and edge features ---
    edge_indices: list[list[int]] = [[], []]
    edge_feat_list: list[list[float]] = []

    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        bf = bond_features(bond)

        # Undirected: add both directions
        edge_indices[0].extend([i, j])
        edge_indices[1].extend([j, i])
        edge_feat_list.append(bf)
        edge_feat_list.append(bf)

    if len(edge_feat_list) == 0:
        # Single-atom molecule — no bonds
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        edge_attr = torch.zeros((0, BOND_FEATURE_DIM), dtype=torch.float)
    else:
        edge_index = torch.tensor(edge_indices, dtype=torch.long)
        edge_attr = torch.tensor(edge_feat_list, dtype=torch.float)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        smiles=smiles,
    )
    return data


def smiles_to_graph_batch(smiles_list: list[str]) -> list[Data]:
    """Convert a list of SMILES strings to a list of PyG Data objects.

    Invalid SMILES (or those that fail conversion) are silently skipped.

    Args:
        smiles_list: A list of SMILES strings.

    Returns:
        A list of :class:`~torch_geometric.data.Data` objects. May be
        shorter than the input list if some SMILES were invalid.
    """
    results: list[Data] = []
    for smi in smiles_list:
        graph = smiles_to_graph(smi)
        if graph is not None:
            results.append(graph)
    return results
