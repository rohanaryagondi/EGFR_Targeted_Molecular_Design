"""Data models for the static baseline pipeline.

Every intermediate and output artifact has a typed schema.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── Pocket ──────────────────────────────────────────────────────────────


class PocketResidue(BaseModel):
    """A single residue contributing to the binding pocket."""

    chain: str = Field(default="A")
    residue_number: int
    residue_name: str = Field(description="3-letter amino acid code")
    role: str = Field(default="", description="hinge, gatekeeper, DFG, P-loop, etc.")


class PocketDefinition(BaseModel):
    """Definition of a binding pocket on a specific structure.

    For the static baseline, this is a literature-derived pocket definition
    based on known EGFR ATP-binding site residues. In later phases, this
    will be replaced by geometric pocket detection from coordinates.
    """

    pocket_id: str = Field(description="Unique identifier")
    pdb_id: str = Field(description="Structure this pocket belongs to")
    chain: str = Field(default="A")
    pocket_type: str = Field(default="ATP-binding", description="ATP-binding, allosteric, etc.")
    residues: list[PocketResidue] = Field(default_factory=list)
    volume_A3: float | None = Field(default=None, description="Pocket volume (Angstrom^3)")
    center_of_mass: list[float] | None = Field(
        default=None, description="Approximate center [x, y, z]"
    )
    source: str = Field(
        default="literature",
        description="How this pocket was defined: literature, fpocket, sitemap, etc.",
    )
    notes: str = Field(default="")


# ── Candidate ───────────────────────────────────────────────────────────


class CandidateSource(str, Enum):
    REFERENCE = "reference"        # From curated ligand dataset
    ENUMERATED = "enumerated"      # Simple SMILES enumeration
    EXTERNAL = "external"          # External library


class Candidate(BaseModel):
    """A candidate molecule for evaluation."""

    candidate_id: str
    smiles: str
    source: CandidateSource = Field(default=CandidateSource.REFERENCE)
    parent_id: str = Field(default="", description="ID of parent compound if enumerated")
    notes: str = Field(default="")


class CandidateLibrary(BaseModel):
    """A collection of candidates for a baseline run."""

    library_id: str
    target_pdb_id: str
    pocket_id: str
    candidates: list[Candidate] = Field(default_factory=list)
    generated_at: str = Field(default="")

    @property
    def n_candidates(self) -> int:
        return len(self.candidates)


# ── Filtering ───────────────────────────────────────────────────────────


class PropertyFilter(BaseModel):
    """A single property filter criterion."""

    property_name: str
    min_value: float | None = None
    max_value: float | None = None


class FilterResult(BaseModel):
    """Result of applying property filters to a candidate."""

    candidate_id: str
    smiles: str
    passed: bool
    properties: dict[str, float | None] = Field(default_factory=dict)
    failed_filters: list[str] = Field(default_factory=list)


class FilteredLibrary(BaseModel):
    """Candidates that passed property filtering."""

    library_id: str
    filters_applied: list[PropertyFilter] = Field(default_factory=list)
    results: list[FilterResult] = Field(default_factory=list)
    n_input: int = Field(default=0)
    n_passed: int = Field(default=0)
    n_failed: int = Field(default=0)


# ── Scoring ─────────────────────────────────────────────────────────────


class ScoreComponent(BaseModel):
    """A single scoring component for a candidate."""

    name: str
    value: float
    weight: float = Field(default=1.0)
    method: str = Field(default="", description="How this score was computed")
    is_stub: bool = Field(default=False, description="True if score is placeholder")


class ScoredCandidate(BaseModel):
    """A candidate with computed scores."""

    candidate_id: str
    smiles: str
    scores: list[ScoreComponent] = Field(default_factory=list)
    composite_score: float = Field(default=0.0)
    rank: int = Field(default=0)

    def get_score(self, name: str) -> float | None:
        for s in self.scores:
            if s.name == name:
                return s.value
        return None


class RankedCandidates(BaseModel):
    """Final ranked output from the baseline pipeline."""

    run_id: str
    pipeline: str = Field(default="static_baseline")
    target_pdb_id: str
    pocket_id: str
    scoring_method: str = Field(default="")
    candidates: list[ScoredCandidate] = Field(default_factory=list)
    generated_at: str = Field(default="")
    notes: str = Field(default="")

    @property
    def n_ranked(self) -> int:
        return len(self.candidates)


# ── Evaluation ──────────────────────────────────────────────────────────


class BaselineEvaluation(BaseModel):
    """Evaluation metrics for a baseline run."""

    run_id: str
    n_candidates_input: int = Field(default=0)
    n_candidates_filtered: int = Field(default=0)
    n_candidates_ranked: int = Field(default=0)
    validity_rate: float = Field(default=0.0, description="Fraction with valid SMILES")
    uniqueness_rate: float = Field(default=0.0, description="Fraction of unique SMILES")
    diversity_score: float = Field(default=0.0, description="Intra-set Tanimoto diversity")
    property_stats: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Per-property mean/std/min/max"
    )
    score_stats: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Per-score-component mean/std/min/max"
    )
    top_k_candidates: list[str] = Field(
        default_factory=list, description="Top-K candidate IDs"
    )
    notes: str = Field(default="")
