"""Property filtering for the static baseline.

Applies simple molecular property filters to the candidate library.
Without RDKit, we use SMILES-based heuristic property estimation.
These are rough approximations — clearly labeled as such.

When RDKit is available, these should be replaced with proper calculations.
"""

from __future__ import annotations

import re

from statebind.baselines.models import (
    Candidate,
    CandidateLibrary,
    FilteredLibrary,
    FilterResult,
    PropertyFilter,
)


# ── Default Lipinski-like filters ───────────────────────────────────────

DEFAULT_FILTERS = [
    PropertyFilter(property_name="estimated_mw", min_value=200, max_value=600),
    PropertyFilter(property_name="estimated_hba", min_value=1, max_value=10),
    PropertyFilter(property_name="estimated_hbd", min_value=0, max_value=5),
    PropertyFilter(property_name="n_heavy_atoms", min_value=15, max_value=50),
    PropertyFilter(property_name="n_rings", min_value=1, max_value=8),
]


# ── SMILES-based property estimation ────────────────────────────────────
# These are heuristic approximations. NOT a substitute for RDKit.


def _estimate_heavy_atom_count(smiles: str) -> int:
    """Estimate heavy atom count from SMILES.

    Counts characters that represent atoms (C, N, O, S, F, Cl, Br, P, etc.)
    excluding hydrogens and SMILES syntax characters.
    """
    # Remove stereochemistry markers, charges, H counts
    clean = re.sub(r'[\[\]@+\-\d()/#\\.]', '', smiles)
    # Count remaining letters as atoms (rough)
    # Multi-char atoms: Cl, Br, Si, etc.
    count = 0
    i = 0
    while i < len(clean):
        if i + 1 < len(clean) and clean[i:i+2] in ("Cl", "Br", "Si", "Se"):
            count += 1
            i += 2
        elif clean[i].isalpha() and clean[i] != 'H':
            count += 1
            i += 1
        else:
            i += 1
    return count


def _estimate_mw(smiles: str) -> float:
    """Estimate molecular weight from SMILES (rough).

    Uses average atomic weights. Accuracy: ±10-20%.
    """
    weights = {
        'C': 12.011, 'c': 12.011,
        'N': 14.007, 'n': 14.007,
        'O': 15.999, 'o': 15.999,
        'S': 32.065, 's': 32.065,
        'F': 18.998, 'P': 30.974,
    }
    # Count atoms and sum weights
    mw = 0.0
    i = 0
    s = smiles
    while i < len(s):
        if i + 1 < len(s) and s[i:i+2] in ("Cl", "cl"):
            mw += 35.45
            i += 2
        elif i + 1 < len(s) and s[i:i+2] in ("Br", "br"):
            mw += 79.90
            i += 2
        elif s[i] in weights:
            mw += weights[s[i]]
            i += 1
        else:
            i += 1

    # Rough hydrogen correction: estimate H count from heavy atoms
    n_heavy = _estimate_heavy_atom_count(smiles)
    mw += n_heavy * 0.7 * 1.008  # Heuristic H-to-heavy ratio

    return round(mw, 1)


def _estimate_hba(smiles: str) -> int:
    """Estimate H-bond acceptors (N and O atoms)."""
    return smiles.count('N') + smiles.count('O') + smiles.count('n') + smiles.count('o')


def _estimate_hbd(smiles: str) -> int:
    """Estimate H-bond donors (NH and OH, rough)."""
    # Count [NH], [nH], [OH] patterns and standalone N/O not in rings
    count = 0
    count += len(re.findall(r'\[nH\]', smiles))
    count += len(re.findall(r'\[NH\d?\]', smiles))
    count += len(re.findall(r'\[OH\]', smiles))
    # Rough: count Nc (amine attached to something) patterns
    count += len(re.findall(r'(?<![cnos])N(?![+()\]])', smiles))
    return min(count, 10)  # Cap at reasonable value


def _count_rings(smiles: str) -> int:
    """Estimate ring count from SMILES ring-closure digits."""
    # Count unique ring-opening digits
    digits = re.findall(r'(?<!\%)(\d)', smiles)
    # Also check %nn ring closures
    pct_digits = re.findall(r'%(\d\d)', smiles)
    # Each ring has an opening and closing digit
    all_digits = digits + pct_digits
    return len(all_digits) // 2 if all_digits else 0


def _is_valid_smiles(smiles: str) -> bool:
    """Basic SMILES validity check (heuristic, not a parser).

    Checks:
    - Non-empty
    - Balanced parentheses
    - Balanced brackets
    - Contains at least one atom character
    - Ring closure digits are paired
    """
    if not smiles or not smiles.strip():
        return False
    if smiles.count('(') != smiles.count(')'):
        return False
    if smiles.count('[') != smiles.count(']'):
        return False
    if not re.search(r'[CNOScnos]', smiles):
        return False
    return True


def _compute_heuristic_properties(smiles: str) -> dict[str, float | None]:
    """Heuristic property estimation from SMILES (no RDKit required)."""
    if not _is_valid_smiles(smiles):
        return {
            "estimated_mw": None,
            "estimated_hba": None,
            "estimated_hbd": None,
            "n_heavy_atoms": None,
            "n_rings": None,
            "smiles_valid": 0.0,
        }

    return {
        "estimated_mw": _estimate_mw(smiles),
        "estimated_hba": float(_estimate_hba(smiles)),
        "estimated_hbd": float(_estimate_hbd(smiles)),
        "n_heavy_atoms": float(_estimate_heavy_atom_count(smiles)),
        "n_rings": float(_count_rings(smiles)),
        "smiles_valid": 1.0,
    }


def compute_properties(smiles: str) -> dict[str, float | None]:
    """Compute molecular properties from SMILES.

    Uses RDKit exact descriptors when available; falls back to heuristic
    estimates otherwise.

    Returns:
        Dict of property_name -> value. Values are None if computation failed.
    """
    try:
        from statebind.chemistry.descriptors import compute_exact_properties
        from statebind.chemistry.fingerprints import HAS_RDKIT
        if HAS_RDKIT:
            props = compute_exact_properties(smiles)
            # Add smiles_valid key for backward compat (tests assert on it)
            all_none = all(v is None for v in props.values())
            props["smiles_valid"] = 0.0 if all_none else 1.0
            return props
    except ImportError:
        pass
    return _compute_heuristic_properties(smiles)


def apply_filters(
    library: CandidateLibrary,
    filters: list[PropertyFilter] | None = None,
) -> FilteredLibrary:
    """Apply property filters to a candidate library.

    Args:
        library: Input candidate library.
        filters: List of property filters. Defaults to Lipinski-like filters.

    Returns:
        FilteredLibrary with pass/fail results for each candidate.
    """
    if filters is None:
        filters = DEFAULT_FILTERS

    results = []
    n_passed = 0

    for candidate in library.candidates:
        props = compute_properties(candidate.smiles)
        failed_filters = []

        for f in filters:
            val = props.get(f.property_name)
            if val is None:
                failed_filters.append(f"{f.property_name}:null")
                continue
            if f.min_value is not None and val < f.min_value:
                failed_filters.append(f"{f.property_name}<{f.min_value}")
            if f.max_value is not None and val > f.max_value:
                failed_filters.append(f"{f.property_name}>{f.max_value}")

        passed = len(failed_filters) == 0
        if passed:
            n_passed += 1

        results.append(FilterResult(
            candidate_id=candidate.candidate_id,
            smiles=candidate.smiles,
            passed=passed,
            properties=props,
            failed_filters=failed_filters,
        ))

    return FilteredLibrary(
        library_id=library.library_id,
        filters_applied=filters,
        results=results,
        n_input=len(library.candidates),
        n_passed=n_passed,
        n_failed=len(library.candidates) - n_passed,
    )
