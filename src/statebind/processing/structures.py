"""Structure dataset builder: EGFR kinase domain PDB structures with state annotations.

This module contains v1 curated structural metadata for representative
EGFR kinase domain structures across conformational states. Structure
classification is based on published geometric criteria and KLIFS annotations.
"""

from __future__ import annotations

from datetime import datetime, timezone

from statebind.processing.models import (
    ConformationalState,
    Provenance,
    StructureDataset,
    StructureRecord,
)


def _v1_curated_structures() -> list[StructureRecord]:
    """Return the v1 curated EGFR structure set.

    Selection criteria:
    - Human EGFR kinase domain
    - Resolution <= 3.0 A
    - Representative coverage across conformational states
    - Includes WT and key mutant structures

    State classifications based on:
    - KLIFS database annotations
    - Ung & Bhatt, J Mol Graph Model 2020 (geometric criteria)
    - Visual inspection of DFG motif and aC-helix
    """
    return [
        # ── DFGin_aCin (Active) ─────────────────────────────────────
        StructureRecord(
            pdb_id="1m17",
            resolution=2.6,
            chain="A",
            state=ConformationalState.DFGIN_ACIN,
            ligand_id="AEE",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            is_representative=True,
            deposition_date="2002-06-28",
            notes="WT EGFR bound to erlotinib. Classic active-state reference.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="4hjo",
            resolution=1.8,
            chain="A",
            state=ConformationalState.DFGIN_ACIN,
            ligand_id="0WM",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            notes="High-resolution WT EGFR in active conformation.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="2itv",
            resolution=2.47,
            chain="A",
            state=ConformationalState.DFGIN_ACIN,
            ligand_id="AEE",
            ligand_bound=True,
            is_apo=False,
            mutations_present=["L858R"],
            notes="L858R mutant bound to erlotinib. Active conformation.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="2jit",
            resolution=3.0,
            chain="A",
            state=ConformationalState.DFGIN_ACIN,
            ligand_id="IRE",
            ligand_bound=True,
            is_apo=False,
            mutations_present=["T790M"],
            notes="T790M mutant bound to Iressa (gefitinib). Gatekeeper structure.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="3w2o",
            resolution=2.05,
            chain="A",
            state=ConformationalState.DFGIN_ACIN,
            ligand_id="W2O",
            ligand_bound=True,
            is_apo=False,
            mutations_present=["T790M"],
            notes="T790M with WZ4002 (preclinical 3rd-gen compound).",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="4i22",
            resolution=2.8,
            chain="A",
            state=ConformationalState.DFGIN_ACIN,
            ligand_id="0PN",
            ligand_bound=True,
            is_apo=False,
            mutations_present=["T790M", "L858R"],
            notes="Double mutant T790M/L858R. Active conformation.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="5cau",
            resolution=2.8,
            chain="A",
            state=ConformationalState.DFGIN_ACIN,
            ligand_id="5Q0",
            ligand_bound=True,
            is_apo=False,
            mutations_present=["T790M"],
            notes="T790M with osimertinib. Clinically relevant complex.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),

        # ── DFGin_aCout (Src-like inactive) ─────────────────────────
        StructureRecord(
            pdb_id="2gs7",
            resolution=2.6,
            chain="A",
            state=ConformationalState.DFGIN_ACOUT,
            ligand_id="AEE",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            is_representative=True,
            notes="WT EGFR Src-like inactive conformation. aC-helix rotated out.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="2gs2",
            resolution=2.8,
            chain="A",
            state=ConformationalState.DFGIN_ACOUT,
            ligand_id="AQ4",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            notes="WT EGFR Src-like inactive with lapatinib.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="1xkk",
            resolution=2.4,
            chain="A",
            state=ConformationalState.DFGIN_ACOUT,
            ligand_id="FMM",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            notes="WT EGFR Src-like inactive conformation.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="4ll0",
            resolution=2.8,
            chain="A",
            state=ConformationalState.DFGIN_ACOUT,
            ligand_id="2JI",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            notes="WT EGFR aC-helix out, bound to type-I 1/2 inhibitor.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),

        # ── DFGout_aCin ─────────────────────────────────────────────
        StructureRecord(
            pdb_id="3iku",
            resolution=2.75,
            chain="A",
            state=ConformationalState.DFGOUT_ACIN,
            ligand_id="DJK",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            is_representative=True,
            notes="WT EGFR with DFG-out and aC-helix in. Type-II inhibitor bound.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="3w2r",
            resolution=2.35,
            chain="A",
            state=ConformationalState.DFGOUT_ACIN,
            ligand_id="W2R",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            notes="DFG-out with type-II inhibitor.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),

        # ── DFGout_aCout (Classical inactive) ───────────────────────
        StructureRecord(
            pdb_id="4zau",
            resolution=2.9,
            chain="A",
            state=ConformationalState.DFGOUT_ACOUT,
            ligand_id="4ZA",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            is_representative=True,
            notes="WT EGFR classical inactive. Both DFG-out and aC-helix-out.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),
        StructureRecord(
            pdb_id="5d41",
            resolution=2.85,
            chain="A",
            state=ConformationalState.DFGOUT_ACOUT,
            ligand_id="5IA",
            ligand_bound=True,
            is_apo=False,
            mutations_present=[],
            notes="Inactive EGFR conformation.",
            provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
        ),

        # ── Apo structures ──────────────────────────────────────────
        StructureRecord(
            pdb_id="2gs6",
            resolution=2.6,
            chain="A",
            state=ConformationalState.DFGIN_ACOUT,
            ligand_id="",
            ligand_bound=False,
            is_apo=True,
            mutations_present=[],
            notes="Apo WT EGFR kinase domain, Src-like inactive.",
            provenance=Provenance(sources=["pdb"], processing_date="2026-03-14"),
        ),
    ]


def build_structure_dataset() -> StructureDataset:
    """Build the processed structure dataset from curated metadata.

    Returns:
        Populated StructureDataset.
    """
    structures = _v1_curated_structures()
    now = datetime.now(timezone.utc).isoformat()

    return StructureDataset(
        version="1.0.0",
        structures=structures,
        generated_at=now,
        processing_version="0.1.0",
    )
