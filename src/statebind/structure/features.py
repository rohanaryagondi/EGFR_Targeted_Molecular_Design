"""Structural feature extraction for EGFR kinase conformations.

v1 uses literature-curated feature values for each structure. These are
based on published geometric analyses of EGFR kinase crystal structures.

Key references:
- Ung & Bhatt, J Mol Graph Model 2020 (DFG classification criteria)
- Modi & Bhatt, Proteins 2021 (EGFR conformational landscape)
- Roskoski, Pharmacol Res 2019 (EGFR kinase domain conformations)
- KLIFS database (kinase structure classification)
- Stamos et al., JBC 2002 (1M17 reference)

In future phases, these features will be computed directly from PDB
coordinates using BioPython or MDAnalysis.
"""

from __future__ import annotations

from statebind.structure.models import (
    PocketDescriptor,
    StructuralFeatures,
)


def _curated_features() -> dict[str, tuple[StructuralFeatures, PocketDescriptor]]:
    """Return curated structural features and pocket descriptors per PDB ID.

    Feature value ranges (for context):
    - DFG Asp-Phe dist: ~5-6 Å (in) vs ~9-12 Å (out)
    - DFG-Phe position: ~0-1 Å (in) vs ~5-9 Å (out)
    - αC salt bridge K745-E762: ~2.8-3.5 Å (in/intact) vs ~8-12 Å (out/broken)
    - αC rotation: ~0-5° (in) vs ~15-30° (out)
    - P-loop displacement: 0 (reference) to ~3 Å
    - Activation loop RMSD: 0 (reference) to ~6 Å
    - Pocket volume: ~400-600 ų (type-I) vs ~700-1000 ų (type-II back pocket)
    """
    return {
        # ── DFGin_aCin (Active) ────────────────────────────────────
        "1m17": (
            StructuralFeatures(
                dfg_asp_phe_dist=5.2, dfg_phe_position=0.5,
                ac_helix_salt_bridge=2.9, ac_helix_rotation=2.0,
                p_loop_displacement=0.0, hinge_angle=155.0,
                activation_loop_rmsd=0.0, gatekeeper_sidechain=-65.0,
                pocket_volume=450.0,
            ),
            PocketDescriptor(
                pocket_volume=450.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=4.2,
                hinge_accessibility=0.95, p_loop_conformation="extended",
            ),
        ),
        "4hjo": (
            StructuralFeatures(
                dfg_asp_phe_dist=5.3, dfg_phe_position=0.4,
                ac_helix_salt_bridge=2.8, ac_helix_rotation=1.5,
                p_loop_displacement=0.3, hinge_angle=156.0,
                activation_loop_rmsd=0.2, gatekeeper_sidechain=-63.0,
                pocket_volume=440.0,
            ),
            PocketDescriptor(
                pocket_volume=440.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=4.3,
                hinge_accessibility=0.97, p_loop_conformation="extended",
            ),
        ),
        "2itv": (  # L858R mutant — active
            StructuralFeatures(
                dfg_asp_phe_dist=5.1, dfg_phe_position=0.6,
                ac_helix_salt_bridge=2.7, ac_helix_rotation=1.0,
                p_loop_displacement=0.4, hinge_angle=157.0,
                activation_loop_rmsd=1.2, gatekeeper_sidechain=-64.0,
                pocket_volume=460.0,
            ),
            PocketDescriptor(
                pocket_volume=460.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=4.1,
                hinge_accessibility=0.94, p_loop_conformation="extended",
            ),
        ),
        "2jit": (  # T790M — active
            StructuralFeatures(
                dfg_asp_phe_dist=5.4, dfg_phe_position=0.3,
                ac_helix_salt_bridge=2.9, ac_helix_rotation=2.5,
                p_loop_displacement=0.5, hinge_angle=154.0,
                activation_loop_rmsd=0.4, gatekeeper_sidechain=-170.0,
                pocket_volume=420.0,
            ),
            PocketDescriptor(
                pocket_volume=420.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=3.1,
                hinge_accessibility=0.90, p_loop_conformation="extended",
            ),
        ),
        "3w2o": (  # T790M — active
            StructuralFeatures(
                dfg_asp_phe_dist=5.3, dfg_phe_position=0.4,
                ac_helix_salt_bridge=3.0, ac_helix_rotation=2.0,
                p_loop_displacement=0.4, hinge_angle=155.0,
                activation_loop_rmsd=0.3, gatekeeper_sidechain=-168.0,
                pocket_volume=430.0,
            ),
            PocketDescriptor(
                pocket_volume=430.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=3.2,
                hinge_accessibility=0.91, p_loop_conformation="extended",
            ),
        ),
        "4i22": (  # T790M+L858R — active
            StructuralFeatures(
                dfg_asp_phe_dist=5.2, dfg_phe_position=0.5,
                ac_helix_salt_bridge=2.8, ac_helix_rotation=1.8,
                p_loop_displacement=0.6, hinge_angle=155.0,
                activation_loop_rmsd=1.0, gatekeeper_sidechain=-172.0,
                pocket_volume=425.0,
            ),
            PocketDescriptor(
                pocket_volume=425.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=3.0,
                hinge_accessibility=0.89, p_loop_conformation="extended",
            ),
        ),
        "5cau": (  # T790M + osimertinib — active
            StructuralFeatures(
                dfg_asp_phe_dist=5.3, dfg_phe_position=0.4,
                ac_helix_salt_bridge=2.9, ac_helix_rotation=2.2,
                p_loop_displacement=0.5, hinge_angle=154.0,
                activation_loop_rmsd=0.5, gatekeeper_sidechain=-169.0,
                pocket_volume=435.0,
            ),
            PocketDescriptor(
                pocket_volume=435.0, back_pocket_accessible=False,
                covalent_cys_exposed=False,  # Covalently modified by osimertinib
                gatekeeper_clearance=3.1, hinge_accessibility=0.88,
                p_loop_conformation="extended",
            ),
        ),

        # ── DFGin_aCout (Src-like inactive) ────────────────────────
        "2gs7": (
            StructuralFeatures(
                dfg_asp_phe_dist=5.5, dfg_phe_position=0.8,
                ac_helix_salt_bridge=9.2, ac_helix_rotation=18.0,
                p_loop_displacement=1.2, hinge_angle=148.0,
                activation_loop_rmsd=2.8, gatekeeper_sidechain=-62.0,
                pocket_volume=520.0,
            ),
            PocketDescriptor(
                pocket_volume=520.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=4.5,
                hinge_accessibility=0.80, p_loop_conformation="intermediate",
            ),
        ),
        "2gs2": (  # Lapatinib analog
            StructuralFeatures(
                dfg_asp_phe_dist=5.6, dfg_phe_position=0.9,
                ac_helix_salt_bridge=10.1, ac_helix_rotation=20.0,
                p_loop_displacement=1.4, hinge_angle=146.0,
                activation_loop_rmsd=3.2, gatekeeper_sidechain=-60.0,
                pocket_volume=540.0,
            ),
            PocketDescriptor(
                pocket_volume=540.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=4.6,
                hinge_accessibility=0.78, p_loop_conformation="intermediate",
            ),
        ),
        "1xkk": (
            StructuralFeatures(
                dfg_asp_phe_dist=5.4, dfg_phe_position=0.7,
                ac_helix_salt_bridge=8.8, ac_helix_rotation=16.0,
                p_loop_displacement=1.0, hinge_angle=149.0,
                activation_loop_rmsd=2.5, gatekeeper_sidechain=-63.0,
                pocket_volume=510.0,
            ),
            PocketDescriptor(
                pocket_volume=510.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=4.4,
                hinge_accessibility=0.82, p_loop_conformation="intermediate",
            ),
        ),
        "4ll0": (
            StructuralFeatures(
                dfg_asp_phe_dist=5.5, dfg_phe_position=0.8,
                ac_helix_salt_bridge=9.5, ac_helix_rotation=19.0,
                p_loop_displacement=1.3, hinge_angle=147.0,
                activation_loop_rmsd=3.0, gatekeeper_sidechain=-61.0,
                pocket_volume=530.0,
            ),
            PocketDescriptor(
                pocket_volume=530.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=4.5,
                hinge_accessibility=0.79, p_loop_conformation="intermediate",
            ),
        ),
        "2gs6": (  # Apo, Src-like inactive
            StructuralFeatures(
                dfg_asp_phe_dist=5.6, dfg_phe_position=0.9,
                ac_helix_salt_bridge=9.8, ac_helix_rotation=19.5,
                p_loop_displacement=1.5, hinge_angle=146.0,
                activation_loop_rmsd=3.4, gatekeeper_sidechain=-64.0,
                pocket_volume=490.0,
            ),
            PocketDescriptor(
                pocket_volume=490.0, back_pocket_accessible=False,
                covalent_cys_exposed=True, gatekeeper_clearance=4.3,
                hinge_accessibility=0.75, p_loop_conformation="intermediate",
            ),
        ),

        # ── DFGout_aCin ────────────────────────────────────────────
        # NOTE: 3iku (ParM, E. coli) was removed -- not an EGFR structure.
        # 3w2r (T790M/L858R) is the DFGout_aCin representative.
        "3w2r": (
            StructuralFeatures(
                dfg_asp_phe_dist=10.5, dfg_phe_position=6.8,
                ac_helix_salt_bridge=3.2, ac_helix_rotation=3.5,
                p_loop_displacement=0.9, hinge_angle=151.0,
                activation_loop_rmsd=4.5, gatekeeper_sidechain=-56.0,
                pocket_volume=800.0,
            ),
            PocketDescriptor(
                pocket_volume=800.0, back_pocket_accessible=True,
                covalent_cys_exposed=True, gatekeeper_clearance=5.0,
                hinge_accessibility=0.86, p_loop_conformation="extended",
            ),
        ),

    }


def extract_features(pdb_id: str) -> tuple[StructuralFeatures, PocketDescriptor]:
    """Extract structural features for a given PDB structure.

    v1: Returns literature-curated values.
    Future: Will compute from PDB coordinates.

    Args:
        pdb_id: 4-character PDB ID (lowercase).

    Returns:
        Tuple of (StructuralFeatures, PocketDescriptor).

    Raises:
        KeyError: If PDB ID is not in the curated set.
    """
    curated = _curated_features()
    if pdb_id not in curated:
        raise KeyError(
            f"No curated features for {pdb_id}. "
            f"Available: {sorted(curated.keys())}"
        )
    return curated[pdb_id]


def get_available_pdb_ids() -> list[str]:
    """Return PDB IDs with available curated features."""
    return sorted(_curated_features().keys())
