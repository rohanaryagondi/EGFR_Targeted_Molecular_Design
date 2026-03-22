"""Synthetic accessibility (SA) scoring.

Uses the Ertl/Schuffenhauer SA_Score from RDKit's Contrib directory
when available.  Falls back to a simplified heuristic when the Contrib
module cannot be loaded, and to a neutral constant (5.0) when RDKit is
not installed at all.

SA scores range from 1 (easy to synthesize) to 10 (difficult).
"""

from __future__ import annotations

import logging

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency — RDKit core
# ---------------------------------------------------------------------------

HAS_RDKIT: bool

try:
    from rdkit import Chem as _Chem
    from rdkit.Chem import rdMolDescriptors as _rdMolDescriptors

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

# ---------------------------------------------------------------------------
# Optional dependency — RDKit Contrib SA_Score module
# ---------------------------------------------------------------------------

_sascorer: object | None = None
"""Reference to the ``sascorer`` module if it could be loaded."""

if HAS_RDKIT:
    try:
        import importlib.util
        import os
        import sys

        from rdkit import RDConfig as _RDConfig

        _sa_module_path = os.path.join(
            _RDConfig.RDContribDir, "SA_Score", "sascorer.py"
        )
        if os.path.isfile(_sa_module_path):
            _spec = importlib.util.spec_from_file_location("sascorer", _sa_module_path)
            if _spec is not None and _spec.loader is not None:
                _sascorer = importlib.util.module_from_spec(_spec)
                sys.modules["sascorer"] = _sascorer  # type: ignore[assignment]
                _spec.loader.exec_module(_sascorer)  # type: ignore[arg-type]
    except Exception:
        _log.debug("Could not load SA_Score from RDKit Contrib; using heuristic.", exc_info=True)
        _sascorer = None

_NEUTRAL_SA: float = 5.0
"""Returned when SA cannot be computed (no RDKit, invalid SMILES)."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _simplified_sa_score(mol: object) -> float:
    """Heuristic SA proxy when the Contrib ``sascorer`` is unavailable.

    Uses ring count, stereocentre count, heavy-atom count, and rotatable
    bond count to produce a rough score in [1, 10].  This is less
    accurate than the fragment-based Ertl approach but still provides
    a useful ordering.
    """
    n_heavy = mol.GetNumHeavyAtoms()  # type: ignore[union-attr]
    n_rings = _rdMolDescriptors.CalcNumRings(mol)
    n_stereo = len(_Chem.FindMolChiralCenters(mol, includeUnassigned=True))  # type: ignore[arg-type]
    n_rot = _rdMolDescriptors.CalcNumRotatableBonds(mol)

    # Size component — moderate molecules are easiest
    size_penalty = abs(n_heavy - 27.5) / 20.0

    # Complexity from rings and stereocentres
    complexity = n_rings * 0.5 + n_stereo * 0.5

    # Flexibility gives a small bonus (easier linker chemistry)
    flex_bonus = min(n_rot * 0.1, 0.5)

    raw = 2.0 + size_penalty + complexity - flex_bonus
    return max(1.0, min(10.0, round(raw, 4)))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_sa_score(smiles: str) -> float:
    """Synthetic accessibility score for *smiles*.

    Returns a value in ``[1.0, 10.0]`` where 1 is easy to synthesize
    and 10 is difficult.  Returns ``5.0`` (neutral) when RDKit is
    unavailable or *smiles* is invalid.

    Priority order:

    1. RDKit Contrib ``sascorer.calculateScore`` (Ertl fragment-based)
    2. Simplified RDKit heuristic (ring/stereo/size-based)
    3. Constant ``5.0`` (no RDKit)

    Args:
        smiles: SMILES string.

    Returns:
        SA score in ``[1.0, 10.0]``.
    """
    if not HAS_RDKIT:
        return _NEUTRAL_SA

    if not smiles:
        return _NEUTRAL_SA

    mol = _Chem.MolFromSmiles(smiles)
    if mol is None:
        return _NEUTRAL_SA

    # Priority 1: Contrib sascorer
    if _sascorer is not None:
        try:
            score = _sascorer.calculateScore(mol)  # type: ignore[union-attr]
            return float(max(1.0, min(10.0, round(score, 4))))
        except Exception:
            _log.debug("sascorer.calculateScore failed; falling back to heuristic.", exc_info=True)

    # Priority 2: simplified heuristic
    return _simplified_sa_score(mol)
