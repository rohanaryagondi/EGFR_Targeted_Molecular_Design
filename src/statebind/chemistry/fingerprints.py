"""Morgan fingerprint computation and Tanimoto similarity.

When RDKit is available, uses Morgan/ECFP4 fingerprints (radius=2,
2048 bits) for proper molecular similarity.  Falls back to SMILES
character 3-gram Tanimoto from ``baselines.scoring`` when RDKit is
not installed.
"""

from __future__ import annotations

from typing import Any

from statebind.baselines.scoring import _REFERENCE_BINDERS, _tanimoto_ngram

# ---------------------------------------------------------------------------
# Optional dependency
# ---------------------------------------------------------------------------

HAS_RDKIT: bool
"""``True`` when ``rdkit`` is importable in the current environment."""

try:
    from rdkit import Chem as _Chem
    from rdkit import DataStructs as _DataStructs
    from rdkit.Chem import AllChem as _AllChem

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_morgan_fingerprint(
    smiles: str,
    radius: int = 2,
    n_bits: int = 2048,
) -> Any | None:
    """Compute a Morgan fingerprint for *smiles*.

    Args:
        smiles: SMILES string.
        radius: Morgan radius (default 2 ≈ ECFP4).
        n_bits: Bit-vector length.

    Returns:
        RDKit ``ExplicitBitVect``, or ``None`` if the SMILES is invalid
        or RDKit is unavailable.
    """
    if not HAS_RDKIT:
        return None
    if not smiles:
        return None
    mol = _Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return _AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)


def compute_morgan_similarity(
    smiles_a: str,
    smiles_b: str,
    radius: int = 2,
    n_bits: int = 2048,
) -> float:
    """Tanimoto similarity between Morgan fingerprints of two molecules.

    Falls back to SMILES character 3-gram Tanimoto when RDKit is not
    available.

    Args:
        smiles_a: First SMILES string.
        smiles_b: Second SMILES string.
        radius: Morgan radius.
        n_bits: Bit-vector length.

    Returns:
        Similarity in ``[0.0, 1.0]``.
    """
    if not HAS_RDKIT:
        return _tanimoto_ngram(smiles_a, smiles_b)
    fp_a = compute_morgan_fingerprint(smiles_a, radius, n_bits)
    fp_b = compute_morgan_fingerprint(smiles_b, radius, n_bits)
    if fp_a is None or fp_b is None:
        return 0.0
    return float(_DataStructs.TanimotoSimilarity(fp_a, fp_b))


def compute_max_reference_similarity(
    smiles: str,
    references: list[str] | None = None,
) -> float:
    """Maximum Morgan similarity to reference EGFR binders.

    Uses the two canonical reference binders (erlotinib, gefitinib)
    from ``baselines.scoring._REFERENCE_BINDERS`` when *references*
    is ``None``.

    Falls back to n-gram Tanimoto when RDKit is unavailable (the
    fallback is handled transparently by :func:`compute_morgan_similarity`).

    Args:
        smiles: Query SMILES string.
        references: Optional list of reference SMILES.  Defaults to
            ``_REFERENCE_BINDERS``.

    Returns:
        Maximum similarity in ``[0.0, 1.0]``.
    """
    if not smiles:
        return 0.0
    refs = references if references is not None else _REFERENCE_BINDERS
    if not refs:
        return 0.0
    similarities = [compute_morgan_similarity(smiles, ref) for ref in refs]
    return max(similarities)
