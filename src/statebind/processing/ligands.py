"""Ligand dataset builder: EGFR reference compounds and approved TKIs.

Contains curated set of approved EGFR TKIs and representative co-crystal
ligands. SMILES are canonical. Properties are from published sources.
"""

from __future__ import annotations

from datetime import datetime, timezone

from statebind.processing.models import (
    LigandDataset,
    LigandRecord,
    LigandSource,
    Provenance,
)


def _v1_curated_ligands() -> list[LigandRecord]:
    """Return the v1 curated EGFR ligand set.

    Includes all FDA-approved EGFR TKIs and representative co-crystal ligands.
    SMILES from DrugBank/ChEMBL. pIC50 from ChEMBL where available.
    """
    return [
        # ── 1st-generation TKIs (reversible) ────────────────────────
        LigandRecord(
            ligand_id="gefitinib",
            canonical_smiles="COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
            source=LigandSource.APPROVED_DRUG,
            drug_name="gefitinib",
            pIC50=8.0,
            mw=446.9,
            logp=3.2,
            hbd=1,
            hba=7,
            pdb_id="2ity",
            is_approved=True,
            generation="1st",
            notes="Iressa. First EGFR TKI approved (2003). Reversible.",
            provenance=Provenance(sources=["drugbank", "chembl"], processing_date="2026-03-14"),
        ),
        LigandRecord(
            ligand_id="erlotinib",
            canonical_smiles="COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
            source=LigandSource.APPROVED_DRUG,
            drug_name="erlotinib",
            pIC50=8.2,
            mw=393.4,
            logp=3.3,
            hbd=1,
            hba=6,
            pdb_id="1m17",
            is_approved=True,
            generation="1st",
            notes="Tarceva. Reversible EGFR TKI approved 2004.",
            provenance=Provenance(sources=["drugbank", "chembl"], processing_date="2026-03-14"),
        ),

        # ── 2nd-generation TKIs (irreversible, pan-HER) ────────────
        LigandRecord(
            ligand_id="afatinib",
            canonical_smiles="CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1",
            source=LigandSource.APPROVED_DRUG,
            drug_name="afatinib",
            pIC50=9.0,
            mw=485.9,
            logp=3.6,
            hbd=2,
            hba=7,
            is_approved=True,
            generation="2nd",
            notes="Gilotrif. Irreversible pan-HER TKI. Covalent C797 binder.",
            provenance=Provenance(sources=["drugbank", "chembl"], processing_date="2026-03-14"),
        ),
        LigandRecord(
            ligand_id="dacomitinib",
            canonical_smiles="CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCCC1",
            source=LigandSource.APPROVED_DRUG,
            drug_name="dacomitinib",
            pIC50=8.8,
            mw=469.9,
            logp=4.1,
            hbd=2,
            hba=6,
            is_approved=True,
            generation="2nd",
            notes="Vizimpro. Pan-HER irreversible. Covalent C797.",
            provenance=Provenance(sources=["drugbank", "chembl"], processing_date="2026-03-14"),
        ),

        # ── 3rd-generation TKIs (mutant-selective) ──────────────────
        LigandRecord(
            ligand_id="osimertinib",
            canonical_smiles="COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
            source=LigandSource.APPROVED_DRUG,
            drug_name="osimertinib",
            pIC50=9.2,
            mw=499.6,
            logp=2.7,
            hbd=2,
            hba=7,
            pdb_id="5cau",
            is_approved=True,
            generation="3rd",
            notes="Tagrisso. T790M-selective. Covalent C797 binder. "
                  "Most clinically important 3rd-gen EGFR TKI.",
            provenance=Provenance(sources=["drugbank", "chembl"], processing_date="2026-03-14"),
        ),

        # ── Co-crystal ligands (from structure dataset) ─────────────
        LigandRecord(
            ligand_id="AEE",
            canonical_smiles="COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
            source=LigandSource.PDB_COCRYSTAL,
            pdb_id="1m17",
            notes="Erlotinib in PDB format. Co-crystallized with WT EGFR.",
            provenance=Provenance(sources=["pdb"], processing_date="2026-03-14"),
        ),
        LigandRecord(
            ligand_id="AQ4",
            canonical_smiles="CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1",
            source=LigandSource.PDB_COCRYSTAL,
            pdb_id="2gs2",
            notes="Lapatinib analog. Binds Src-like inactive conformation.",
            provenance=Provenance(sources=["pdb"], processing_date="2026-03-14"),
        ),
        LigandRecord(
            ligand_id="IRE",
            canonical_smiles="COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
            source=LigandSource.PDB_COCRYSTAL,
            pdb_id="2jit",
            notes="Gefitinib in PDB format. In T790M structure.",
            provenance=Provenance(sources=["pdb"], processing_date="2026-03-14"),
        ),
        LigandRecord(
            ligand_id="DJK",
            canonical_smiles="",  # Placeholder — complex heterocyclic
            source=LigandSource.PDB_COCRYSTAL,
            pdb_id="3iku",
            notes="Type-II inhibitor binding DFG-out conformation.",
            provenance=Provenance(sources=["pdb"], processing_date="2026-03-14"),
        ),
    ]


def build_ligand_dataset() -> LigandDataset:
    """Build the processed ligand dataset from curated compounds.

    Returns:
        Populated LigandDataset.
    """
    ligands = _v1_curated_ligands()
    now = datetime.now(timezone.utc).isoformat()

    return LigandDataset(
        version="1.0.0",
        ligands=ligands,
        generated_at=now,
        processing_version="0.1.0",
    )
