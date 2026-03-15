"""Data models for the structural state atlas.

Every structure in the atlas carries geometric features, a state label,
a cluster assignment, and a pocket descriptor.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from statebind.processing.models import ConformationalState, Provenance


class StructuralFeatures(BaseModel):
    """Geometric features extracted from a single EGFR kinase structure.

    These features distinguish conformational states. Values are either
    computed from coordinates (future) or curated from literature (v1).

    Feature definitions:
    - dfg_asp_phe_dist: Cα distance between DFG-Asp (D855) and DFG-Phe (F856)
    - dfg_phe_position: DFG-Phe Cα z-displacement relative to aC-helix plane
    - ac_helix_salt_bridge: Distance K745-E762 salt bridge (in=short, out=broken)
    - ac_helix_rotation: Rotation angle of aC-helix relative to active reference
    - p_loop_displacement: P-loop Cα RMSD vs active reference
    - hinge_angle: Backbone angle at hinge region
    - activation_loop_rmsd: A-loop Cα RMSD vs active reference
    - gatekeeper_sidechain: Gatekeeper residue (790) sidechain χ1 angle
    - pocket_volume: Estimated binding pocket volume (Å³)
    """

    dfg_asp_phe_dist: float = Field(description="DFG Asp-Phe Cα distance (Å)")
    dfg_phe_position: float = Field(description="DFG-Phe displacement from active (Å)")
    ac_helix_salt_bridge: float = Field(description="K745-E762 salt bridge distance (Å)")
    ac_helix_rotation: float = Field(description="αC-helix rotation angle (degrees)")
    p_loop_displacement: float = Field(description="P-loop displacement RMSD (Å)")
    hinge_angle: float = Field(description="Hinge backbone angle (degrees)")
    activation_loop_rmsd: float = Field(description="A-loop RMSD vs active (Å)")
    gatekeeper_sidechain: float = Field(description="Gatekeeper χ1 angle (degrees)")
    pocket_volume: float = Field(description="Estimated pocket volume (ų)")

    def to_vector(self) -> list[float]:
        """Return features as a flat numeric vector for clustering."""
        return [
            self.dfg_asp_phe_dist,
            self.dfg_phe_position,
            self.ac_helix_salt_bridge,
            self.ac_helix_rotation,
            self.p_loop_displacement,
            self.hinge_angle,
            self.activation_loop_rmsd,
            self.gatekeeper_sidechain,
            self.pocket_volume,
        ]

    @staticmethod
    def feature_names() -> list[str]:
        return [
            "dfg_asp_phe_dist",
            "dfg_phe_position",
            "ac_helix_salt_bridge",
            "ac_helix_rotation",
            "p_loop_displacement",
            "hinge_angle",
            "activation_loop_rmsd",
            "gatekeeper_sidechain",
            "pocket_volume",
        ]


class PocketDescriptor(BaseModel):
    """Pocket-level descriptor for cross-state pocket comparison.

    Captures how the binding pocket differs across conformational states.
    """

    pocket_volume: float = Field(description="Estimated volume (ų)")
    back_pocket_accessible: bool = Field(
        default=False,
        description="Is the type-II back pocket accessible? (DFG-out opens it)",
    )
    covalent_cys_exposed: bool = Field(
        default=True,
        description="Is C797 solvent-exposed and accessible for covalent binding?",
    )
    gatekeeper_clearance: float = Field(
        default=0.0,
        description="Gatekeeper region clearance (Å). Larger = more permissive",
    )
    hinge_accessibility: float = Field(
        default=0.0,
        description="Hinge region H-bond accessibility score [0-1]",
    )
    p_loop_conformation: str = Field(
        default="extended",
        description="P-loop conformation: extended, folded, or intermediate",
    )


class AtlasEntry(BaseModel):
    """A single structure entry in the state atlas."""

    pdb_id: str
    chain: str = Field(default="A")
    resolution: float = Field(default=0.0)
    state_label: ConformationalState
    mutations_present: list[str] = Field(default_factory=list)
    ligand_id: str = Field(default="")
    ligand_bound: bool = Field(default=False)
    is_apo: bool = Field(default=False)
    is_representative: bool = Field(default=False)

    features: StructuralFeatures
    pocket: PocketDescriptor
    cluster_id: int = Field(default=-1, description="Assigned cluster from clustering")

    feature_source: str = Field(
        default="literature",
        description="How features were obtained: literature, computed, predicted",
    )
    notes: str = Field(default="")
    provenance: Provenance = Field(default_factory=lambda: Provenance(sources=["pdb"]))


class StateCluster(BaseModel):
    """A cluster of structurally similar conformations."""

    cluster_id: int
    label: str = Field(description="Human-readable cluster name")
    dominant_state: ConformationalState
    member_pdb_ids: list[str] = Field(default_factory=list)
    centroid_features: list[float] = Field(default_factory=list)
    n_members: int = Field(default=0)
    mean_resolution: float = Field(default=0.0)
    has_mutant_structures: bool = Field(default=False)
    notes: str = Field(default="")


class PairwiseSimilarity(BaseModel):
    """Pairwise structural similarity between two atlas entries."""

    pdb_id_a: str
    pdb_id_b: str
    state_a: str
    state_b: str
    feature_distance: float = Field(description="Euclidean distance in feature space")
    same_cluster: bool = Field(default=False)


class StateAtlas(BaseModel):
    """The complete structural state atlas.

    This is the central artifact of Phase 3. It contains:
    - All structures with features and state labels
    - Cluster assignments and descriptions
    - Pairwise similarities
    - Pocket comparison data
    """

    version: str = Field(default="1.0.0")
    target_gene: str = Field(default="EGFR")
    entries: list[AtlasEntry] = Field(default_factory=list)
    clusters: list[StateCluster] = Field(default_factory=list)
    pairwise_similarities: list[PairwiseSimilarity] = Field(default_factory=list)
    n_structures: int = Field(default=0)
    n_states: int = Field(default=0)
    n_clusters: int = Field(default=0)
    feature_names: list[str] = Field(default_factory=list)
    generated_at: str = Field(default="")
    processing_version: str = Field(default="0.1.0")
    notes: str = Field(default="")
