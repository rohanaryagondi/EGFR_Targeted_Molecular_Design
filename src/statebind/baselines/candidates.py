"""Candidate library construction for the static baseline.

The candidate library consists of:
1. Reference compounds: known EGFR binders from the curated dataset
2. Enumerated analogs: simple SMILES-based modifications of reference compounds

This is deliberately simple. The static baseline does not use generative models
or pocket-conditioned generation — it uses a conventional library of known
compounds and trivial analogs.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from statebind.baselines.models import (
    Candidate,
    CandidateLibrary,
    CandidateSource,
)
from statebind.processing.ligands import build_ligand_dataset


def _generate_candidate_id(smiles: str, source: str) -> str:
    """Generate a deterministic candidate ID from SMILES + source."""
    h = hashlib.md5(f"{source}:{smiles}".encode()).hexdigest()[:8]
    return f"{source}_{h}"


def build_reference_candidates() -> list[Candidate]:
    """Build candidates from the curated reference ligand dataset.

    Returns all ligands with valid SMILES as candidates.
    """
    ligands = build_ligand_dataset()
    candidates = []
    seen_smiles: set[str] = set()

    for lig in ligands.ligands:
        if not lig.canonical_smiles:
            continue
        if lig.canonical_smiles in seen_smiles:
            continue  # Deduplicate (e.g., erlotinib == AEE)

        seen_smiles.add(lig.canonical_smiles)
        candidates.append(Candidate(
            candidate_id=f"ref_{lig.ligand_id}",
            smiles=lig.canonical_smiles,
            source=CandidateSource.REFERENCE,
            parent_id="",
            notes=f"Reference: {lig.drug_name or lig.ligand_id}",
        ))

    return candidates


def _enumerate_simple_analogs(smiles: str, parent_id: str) -> list[Candidate]:
    """Generate simple SMILES-based analogs of a parent compound.

    Transformations applied:
    1. Halogen swaps (F↔Cl, F↔Br)
    2. Methyl/methoxy swaps
    3. Remove one substituent

    This is intentionally crude. It produces analogs that may or may not
    be synthetically accessible. The point is to have a larger candidate
    set for the scoring pipeline to differentiate.
    """
    analogs = []

    # 1. Halogen swaps
    halogen_swaps = [
        ("F", "Cl"), ("Cl", "F"),
        ("F", "Br"), ("Br", "F"),
        ("Cl", "Br"), ("Br", "Cl"),
    ]
    for old, new in halogen_swaps:
        if old in smiles:
            new_smiles = smiles.replace(old, new, 1)
            if new_smiles != smiles:
                cid = _generate_candidate_id(new_smiles, "enum")
                analogs.append(Candidate(
                    candidate_id=cid,
                    smiles=new_smiles,
                    source=CandidateSource.ENUMERATED,
                    parent_id=parent_id,
                    notes=f"Halogen swap {old}->{new} from {parent_id}",
                ))

    # 2. Methyl/methoxy swaps
    methyl_swaps = [
        ("OC", "OCC"),   # methoxy -> ethoxy
        ("OCC", "OC"),   # ethoxy -> methoxy
    ]
    for old, new in methyl_swaps:
        if old in smiles:
            new_smiles = smiles.replace(old, new, 1)
            if new_smiles != smiles:
                cid = _generate_candidate_id(new_smiles, "enum")
                analogs.append(Candidate(
                    candidate_id=cid,
                    smiles=new_smiles,
                    source=CandidateSource.ENUMERATED,
                    parent_id=parent_id,
                    notes=f"Alkyl swap from {parent_id}",
                ))

    # 3. N-demethylation (remove one N(C) → NH)
    if "N(C)" in smiles:
        new_smiles = smiles.replace("N(C)", "N", 1)
        if new_smiles != smiles:
            cid = _generate_candidate_id(new_smiles, "enum")
            analogs.append(Candidate(
                candidate_id=cid,
                smiles=new_smiles,
                source=CandidateSource.ENUMERATED,
                parent_id=parent_id,
                notes=f"N-demethylation from {parent_id}",
            ))

    return analogs


def build_candidate_library(
    target_pdb_id: str = "1m17",
    pocket_id: str = "1m17_A_ATP",
    enumerate_analogs: bool = True,
) -> CandidateLibrary:
    """Build the full candidate library for the static baseline.

    Args:
        target_pdb_id: PDB ID of the baseline structure.
        pocket_id: Pocket ID being targeted.
        enumerate_analogs: If True, generate simple analogs of reference compounds.

    Returns:
        CandidateLibrary with reference compounds and optional analogs.
    """
    candidates = build_reference_candidates()

    if enumerate_analogs:
        analog_candidates = []
        for ref in candidates:
            analogs = _enumerate_simple_analogs(ref.smiles, ref.candidate_id)
            analog_candidates.extend(analogs)

        # Deduplicate by SMILES
        seen_smiles = {c.smiles for c in candidates}
        for analog in analog_candidates:
            if analog.smiles not in seen_smiles:
                candidates.append(analog)
                seen_smiles.add(analog.smiles)

    now = datetime.now(timezone.utc).isoformat()

    return CandidateLibrary(
        library_id=f"static_baseline_{target_pdb_id}",
        target_pdb_id=target_pdb_id,
        pocket_id=pocket_id,
        candidates=candidates,
        generated_at=now,
    )
