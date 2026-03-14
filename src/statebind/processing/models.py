"""Pydantic models for processed benchmark datasets.

These models define the exact schema for every processed table.
All downstream modules consume these schemas.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── Enums ───────────────────────────────────────────────────────────────


class ResistanceGeneration(str, Enum):
    FIRST = "1st"
    SECOND = "2nd"
    THIRD = "3rd"
    FOURTH = "4th"
    ACTIVATING = "activating"
    UNKNOWN = "unknown"


class MechanismCategory(str, Enum):
    GATEKEEPER = "gatekeeper"
    COVALENT_SITE = "covalent_site"
    HINGE = "hinge"
    HYDROPHOBIC_SPINE = "hydrophobic_spine"
    P_LOOP = "p_loop"
    ACTIVATION_LOOP = "activation_loop"
    SOLVENT_FRONT = "solvent_front"
    AC_HELIX = "ac_helix"
    ALLOSTERIC = "allosteric"
    ACTIVATING_MUTATION = "activating_mutation"
    OTHER = "other"
    UNKNOWN = "unknown"


class ConformationalEffect(str, Enum):
    STABILIZES_DFGIN = "stabilizes_DFGin"
    STABILIZES_DFGOUT = "stabilizes_DFGout"
    STABILIZES_ACTIVE = "stabilizes_active"
    DESTABILIZES_INACTIVE = "destabilizes_inactive"
    STERIC_CLASH = "steric_clash"
    NO_DIRECT_CONFORMATIONAL = "no_direct_conformational"
    UNKNOWN = "unknown"


class ConformationalState(str, Enum):
    DFGIN_ACIN = "DFGin_aCin"
    DFGIN_ACOUT = "DFGin_aCout"
    DFGOUT_ACIN = "DFGout_aCin"
    DFGOUT_ACOUT = "DFGout_aCout"
    UNCLASSIFIED = "unclassified"


class LigandSource(str, Enum):
    PDB_COCRYSTAL = "pdb_cocrystal"
    CHEMBL = "chembl"
    APPROVED_DRUG = "approved_drug"
    MANUAL = "manual"


# ── Provenance ──────────────────────────────────────────────────────────


class Provenance(BaseModel):
    """Provenance record attached to every processed entity."""

    sources: list[str] = Field(description="Source database names")
    processing_version: str = Field(default="0.1.0")
    processing_date: str = Field(default="")
    notes: str = Field(default="")


# ── Context Records ────────────────────────────────────────────────────


class MutationRecord(BaseModel):
    """A single EGFR mutation with resistance and conformational annotations."""

    mutation_id: str = Field(description="e.g., T790M")
    gene: str = Field(default="EGFR")
    uniprot_id: str = Field(default="P00533")
    position: int = Field(description="Residue position in canonical sequence")
    wild_type: str = Field(description="Single-letter wild-type amino acid")
    mutant: str = Field(description="Single-letter mutant amino acid")
    domain: str = Field(default="kinase")
    resistance_generation: ResistanceGeneration = Field(default=ResistanceGeneration.UNKNOWN)
    mechanism_category: MechanismCategory = Field(default=MechanismCategory.UNKNOWN)
    conformational_effect: ConformationalEffect = Field(default=ConformationalEffect.UNKNOWN)
    preferred_states: list[ConformationalState] = Field(
        default_factory=list,
        description="Conformational states this mutation is expected to favor",
    )
    known_drugs_affected: list[str] = Field(default_factory=list)
    known_drugs_effective: list[str] = Field(default_factory=list)
    pdb_structures: list[str] = Field(
        default_factory=list,
        description="PDB IDs of structures containing this mutation",
    )
    references: list[str] = Field(default_factory=list, description="PMIDs or DOIs")
    notes: str = Field(default="")
    split: Literal["train", "val", "test", "unassigned"] = Field(default="unassigned")
    provenance: Provenance = Field(default_factory=lambda: Provenance(sources=["manual"]))


class ContextDataset(BaseModel):
    """The full processed context dataset."""

    version: str = Field(default="1.0.0")
    gene: str = Field(default="EGFR")
    uniprot_id: str = Field(default="P00533")
    kinase_domain_start: int = Field(default=696)
    kinase_domain_end: int = Field(default=1022)
    mutations: list[MutationRecord] = Field(default_factory=list)
    generated_at: str = Field(default="")
    processing_version: str = Field(default="0.1.0")


# ── Structure Records ──────────────────────────────────────────────────


class StructureRecord(BaseModel):
    """A single EGFR structure entry."""

    pdb_id: str = Field(description="4-char PDB ID, lowercase")
    resolution: float = Field(default=0.0, description="Resolution in Angstroms")
    experimental_method: str = Field(default="X-ray diffraction")
    is_predicted: bool = Field(default=False, description="AlphaFold or other prediction")
    chain: str = Field(default="A")
    state: ConformationalState = Field(default=ConformationalState.UNCLASSIFIED)
    dfg_distance: float | None = Field(default=None, description="DFG Asp-Phe Ca distance (A)")
    ac_helix_metric: float | None = Field(default=None, description="aC-helix classification metric")
    mutations_present: list[str] = Field(
        default_factory=list,
        description="Mutations in this structure relative to WT",
    )
    ligand_id: str = Field(default="", description="PDB hetero-atom code of bound ligand")
    ligand_bound: bool = Field(default=False)
    is_apo: bool = Field(default=False, description="No bound ligand in active site")
    is_representative: bool = Field(default=False)
    deposition_date: str = Field(default="")
    organism: str = Field(default="Homo sapiens")
    notes: str = Field(default="")
    provenance: Provenance = Field(default_factory=lambda: Provenance(sources=["pdb"]))


class StructureDataset(BaseModel):
    """The full processed structure dataset."""

    version: str = Field(default="1.0.0")
    target_gene: str = Field(default="EGFR")
    structures: list[StructureRecord] = Field(default_factory=list)
    generated_at: str = Field(default="")
    processing_version: str = Field(default="0.1.0")


# ── Ligand Records ─────────────────────────────────────────────────────


class LigandRecord(BaseModel):
    """A single ligand/compound entry."""

    ligand_id: str = Field(description="Canonical ID (ChEMBL ID, PDB code, or drug name)")
    canonical_smiles: str = Field(default="", description="RDKit-canonicalized SMILES")
    source: LigandSource = Field(default=LigandSource.MANUAL)
    drug_name: str = Field(default="", description="Common/generic name if approved drug")
    pIC50: float | None = Field(default=None, description="-log10(IC50 in M)")
    assay_type: str = Field(default="", description="binding, functional, cell-based")
    mw: float | None = Field(default=None, description="Molecular weight")
    logp: float | None = Field(default=None, description="Calculated logP")
    hbd: int | None = Field(default=None, description="H-bond donors")
    hba: int | None = Field(default=None, description="H-bond acceptors")
    pdb_id: str = Field(default="", description="PDB ID if co-crystal ligand")
    target_gene: str = Field(default="EGFR")
    is_approved: bool = Field(default=False)
    generation: str = Field(default="", description="TKI generation (1st, 2nd, 3rd)")
    notes: str = Field(default="")
    provenance: Provenance = Field(default_factory=lambda: Provenance(sources=["manual"]))


class LigandDataset(BaseModel):
    """The full processed ligand dataset."""

    version: str = Field(default="1.0.0")
    target_gene: str = Field(default="EGFR")
    ligands: list[LigandRecord] = Field(default_factory=list)
    generated_at: str = Field(default="")
    processing_version: str = Field(default="0.1.0")


# ── Mapping Records ────────────────────────────────────────────────────


class MutationStructureMapping(BaseModel):
    """Maps a mutation to structures where it appears."""

    mutation_id: str
    pdb_id: str
    chain: str = Field(default="A")
    state: ConformationalState = Field(default=ConformationalState.UNCLASSIFIED)
    ligand_id: str = Field(default="")


class StructureLigandMapping(BaseModel):
    """Maps a structure to its co-crystallized ligand."""

    pdb_id: str
    ligand_id: str
    chain: str = Field(default="A")


class MappingTables(BaseModel):
    """Cross-reference tables connecting contexts, structures, and ligands."""

    version: str = Field(default="1.0.0")
    mutation_structure: list[MutationStructureMapping] = Field(default_factory=list)
    structure_ligand: list[StructureLigandMapping] = Field(default_factory=list)
    generated_at: str = Field(default="")


# ── Benchmark Card ──────────────────────────────────────────────────────


class BenchmarkSummary(BaseModel):
    """Summary statistics for the assembled benchmark."""

    version: str = Field(default="1.0.0")
    n_mutations: int = Field(default=0)
    n_structures: int = Field(default=0)
    n_ligands: int = Field(default=0)
    n_mutation_structure_mappings: int = Field(default=0)
    n_structure_ligand_mappings: int = Field(default=0)
    states_represented: list[str] = Field(default_factory=list)
    resistance_generations: list[str] = Field(default_factory=list)
    mechanism_categories: list[str] = Field(default_factory=list)
    split_counts: dict[str, int] = Field(default_factory=dict)
    generated_at: str = Field(default="")
    processing_version: str = Field(default="0.1.0")
