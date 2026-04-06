"""Chemistry module: RDKit-backed molecular computations with graceful fallbacks.

Provides Morgan fingerprints, exact molecular descriptors, SMILES
validation/canonicalization, and synthetic accessibility scoring.  Every
function falls back to a safe default when RDKit is not installed.

Optional dependencies:
    rdkit — needed for all chemistry computations

The flag ``HAS_RDKIT`` lets callers check availability at runtime
without catching ImportError themselves.
"""

from __future__ import annotations

from statebind.chemistry.descriptors import compute_exact_properties
from statebind.chemistry.docking_proxy import DockingProxy, get_default_proxy
from statebind.chemistry.fingerprints import (
    HAS_RDKIT,
    compute_max_reference_similarity,
    compute_morgan_fingerprint,
    compute_morgan_similarity,
)
from statebind.chemistry.sa_score import compute_sa_score
from statebind.chemistry.validation import canonicalize_smiles, validate_smiles

__all__ = [
    "compute_morgan_fingerprint",
    "compute_morgan_similarity",
    "compute_max_reference_similarity",
    "compute_exact_properties",
    "validate_smiles",
    "canonicalize_smiles",
    "compute_sa_score",
    "HAS_RDKIT",
    "DockingProxy",
    "get_default_proxy",
]
