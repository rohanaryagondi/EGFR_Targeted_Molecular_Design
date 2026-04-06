"""Pocket definition for the static baseline.

The EGFR ATP-binding pocket is well-characterized in literature. For the
static baseline, we define the pocket by its known key residues rather than
running geometric detection (which requires coordinate files).

This is the pocket the static baseline designs against — one pocket,
one structure, no conformational state awareness.

Key references:
- Stamos et al., JBC 2002 (1M17 structure, erlotinib binding mode)
- Wood et al., Cancer Res 2004 (EGFR binding site characterization)
- Yun et al., Cancer Cell 2007 (T790M gatekeeper analysis)
"""

from __future__ import annotations

from statebind.baselines.models import PocketDefinition, PocketResidue

# EGFR kinase domain ATP-binding site residues (canonical numbering)
# Based on 1M17 (WT EGFR + erlotinib) crystal structure analysis
_EGFR_ATP_POCKET_RESIDUES = [
    # P-loop (glycine-rich loop)
    PocketResidue(residue_number=719, residue_name="GLY", role="P-loop"),
    PocketResidue(residue_number=720, residue_name="SER", role="P-loop"),
    PocketResidue(residue_number=721, residue_name="GLY", role="P-loop"),
    PocketResidue(residue_number=723, residue_name="PHE", role="P-loop"),

    # aC-helix
    PocketResidue(residue_number=744, residue_name="LYS", role="aC-helix/catalytic"),
    PocketResidue(residue_number=762, residue_name="GLU", role="aC-helix/salt-bridge"),

    # Hinge region (critical for TKI binding)
    PocketResidue(residue_number=788, residue_name="THR", role="hinge"),
    PocketResidue(residue_number=789, residue_name="GLN", role="hinge"),
    PocketResidue(residue_number=790, residue_name="THR", role="gatekeeper"),
    PocketResidue(residue_number=791, residue_name="MET", role="hinge"),

    # Catalytic loop
    PocketResidue(residue_number=792, residue_name="LEU", role="hinge-adjacent"),
    PocketResidue(residue_number=793, residue_name="GLY", role="hinge-adjacent"),

    # Back pocket / hydrophobic region
    PocketResidue(residue_number=797, residue_name="CYS", role="covalent-binding"),
    PocketResidue(residue_number=854, residue_name="THR", role="back-pocket"),
    PocketResidue(residue_number=855, residue_name="ASP", role="catalytic"),

    # DFG motif
    PocketResidue(residue_number=855, residue_name="ASP", role="DFG-Asp"),
    PocketResidue(residue_number=856, residue_name="PHE", role="DFG-Phe"),
    PocketResidue(residue_number=857, residue_name="GLY", role="DFG-Gly"),

    # Activation loop
    PocketResidue(residue_number=858, residue_name="LEU", role="activation-loop"),
]


def get_baseline_pocket(
    pdb_id: str = "1m17",
    chain: str = "A",
) -> PocketDefinition:
    """Return the literature-defined EGFR ATP-binding pocket.

    This is the canonical pocket used by the static baseline. It is defined
    by residue list, not by geometric detection. The same pocket definition
    is used regardless of conformational state — this is the deliberate
    limitation that state-aware design addresses.

    Args:
        pdb_id: PDB ID of the baseline structure.
        chain: Chain ID.

    Returns:
        PocketDefinition with EGFR ATP-binding site residues.
    """
    residues = [
        PocketResidue(
            chain=chain,
            residue_number=r.residue_number,
            residue_name=r.residue_name,
            role=r.role,
        )
        for r in _EGFR_ATP_POCKET_RESIDUES
    ]

    return PocketDefinition(
        pocket_id=f"{pdb_id}_{chain}_ATP",
        pdb_id=pdb_id,
        chain=chain,
        pocket_type="ATP-binding",
        residues=residues,
        volume_A3=None,  # Would require coordinate analysis
        source="literature",
        notes=(
            "Literature-derived EGFR ATP-binding site. "
            "Residues based on 1M17 crystal structure (Stamos et al., 2002). "
            "This pocket definition is state-independent — it does NOT change "
            "based on DFG or aC-helix conformation. This is the key limitation "
            "the state-aware pipeline addresses."
        ),
    )


def select_baseline_structure() -> dict:
    """Select the structure for the static baseline.

    Decision: 1M17 (WT EGFR + erlotinib, DFGin_aCin, 2.6 Å)

    Rationale:
    - Wild-type: no mutation bias
    - Active conformation (DFGin_aCin): most commonly targeted
    - Ligand-bound: pocket well-defined
    - Erlotinib complex: well-studied reference
    - Reasonable resolution (2.6 Å)
    - Representative of "typical" structure-based design starting point

    Returns:
        Structure selection metadata.
    """
    return {
        "pdb_id": "1m17",
        "chain": "A",
        "state": "DFGin_aCin",
        "resolution": 2.6,
        "ligand": "AEE (erlotinib)",
        "mutations": [],
        "rationale": (
            "WT EGFR in active conformation, co-crystallized with erlotinib. "
            "This represents the 'default' starting point for traditional "
            "structure-based design: pick the best available WT co-crystal "
            "structure and design against that single pocket."
        ),
        "what_this_misses": [
            "Inactive conformations (DFGout, aCout) that resistance mutations may stabilize",
            "Mutation-induced pocket shape changes",
            "State-selective binding opportunities",
            "Conformational dynamics between states",
        ],
    }
