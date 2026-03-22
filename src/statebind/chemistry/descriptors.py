"""Exact molecular property computation via RDKit.

Computes the same property keys used by ``baselines.filtering`` so that
downstream consumers can swap in exact values without code changes.
When RDKit is unavailable, returns ``None`` for every property.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Optional dependency
# ---------------------------------------------------------------------------

HAS_RDKIT: bool

try:
    from rdkit import Chem as _Chem
    from rdkit.Chem import Descriptors as _Descriptors
    from rdkit.Chem import rdMolDescriptors as _rdMolDescriptors

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

# Keys that MUST appear in the returned dict (backward compat with
# baselines/filtering.py:147-170 and DEFAULT_FILTERS at :25-31).
_REQUIRED_KEYS: list[str] = [
    "estimated_mw",
    "estimated_hba",
    "estimated_hbd",
    "n_rings",
    "n_heavy_atoms",
]

_ADDITIONAL_KEYS: list[str] = [
    "tpsa",
    "logp",
    "n_rotatable_bonds",
]

_ALL_KEYS: list[str] = _REQUIRED_KEYS + _ADDITIONAL_KEYS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_exact_properties(smiles: str) -> dict[str, float | None]:
    """Compute molecular properties for *smiles* via RDKit.

    Returns a dict whose keys are a superset of those produced by
    ``baselines.filtering.compute_properties`` so that downstream code
    (filters, scoring) can use exact values as drop-in replacements.

    Required keys (backward compat with ``baselines/filtering.py``):
        ``estimated_mw``, ``estimated_hba``, ``estimated_hbd``,
        ``n_rings``, ``n_heavy_atoms``

    Additional keys (when RDKit is available):
        ``tpsa``, ``logp``, ``n_rotatable_bonds``

    All values are ``None`` when RDKit is unavailable or *smiles* is
    invalid.

    Args:
        smiles: SMILES string.

    Returns:
        Property dict.  Values are ``float`` or ``None``.
    """
    none_result: dict[str, float | None] = {k: None for k in _ALL_KEYS}

    if not HAS_RDKIT:
        return none_result

    if not smiles:
        return none_result

    mol = _Chem.MolFromSmiles(smiles)
    if mol is None:
        return none_result

    return {
        # Required keys — names match baselines/filtering.py
        "estimated_mw": float(_Descriptors.MolWt(mol)),
        "estimated_hba": float(_Descriptors.NumHAcceptors(mol)),
        "estimated_hbd": float(_Descriptors.NumHDonors(mol)),
        "n_rings": float(_rdMolDescriptors.CalcNumRings(mol)),
        "n_heavy_atoms": float(mol.GetNumHeavyAtoms()),
        # Additional descriptors
        "tpsa": float(_Descriptors.TPSA(mol)),
        "logp": float(_Descriptors.MolLogP(mol)),
        "n_rotatable_bonds": float(_rdMolDescriptors.CalcNumRotatableBonds(mol)),
    }
