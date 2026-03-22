"""SMILES validation and canonicalization via RDKit.

Provides proper SMILES parsing when RDKit is available. Falls back to
permissive behavior (assume valid) when RDKit is not installed, so the
pipeline is never blocked by a missing optional dependency.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Optional dependency
# ---------------------------------------------------------------------------

HAS_RDKIT: bool

try:
    from rdkit import Chem as _Chem  # noqa: F401

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_smiles(smiles: str) -> bool:
    """Check whether *smiles* encodes a valid molecule.

    Returns ``True`` when RDKit is **not** installed (permissive fallback)
    so that the pipeline does not reject candidates it cannot parse.

    Args:
        smiles: SMILES string to validate.

    Returns:
        ``True`` if valid (or if RDKit unavailable), ``False`` otherwise.
    """
    if not HAS_RDKIT:
        return True
    if not smiles:
        return False
    mol = _Chem.MolFromSmiles(smiles)
    return mol is not None


def canonicalize_smiles(smiles: str) -> str | None:
    """Return the canonical form of *smiles*.

    - **RDKit available:** returns canonical SMILES, or ``None`` if the
      input is invalid.
    - **RDKit unavailable:** returns the original string unchanged.

    Args:
        smiles: SMILES string to canonicalize.

    Returns:
        Canonical SMILES, the original string (no RDKit), or ``None``
        (invalid + RDKit present).
    """
    if not HAS_RDKIT:
        return smiles
    if not smiles:
        return None
    mol = _Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return _Chem.MolToSmiles(mol)
