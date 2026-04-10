"""Pocket-to-modification mapping: how pocket context drives generation.

Each conformational state has distinct pocket geometry. This module maps
pocket features to generation strategies:

EGFR (3 states):
- DFGin_aCin (active): compact pocket -> hinge optimization, gatekeeper avoidance
- DFGin_aCout (Src-like): moderate pocket, broken salt bridge -> aC-helix interactions
- DFGout_aCin: large pocket + back pocket -> type-II extensions
  (DFGout_aCout removed: no genuine EGFR DFGout/aCout structures exist)

ABL1 (3 states):
- DFGin_aCin (active): compact pocket -> hinge optimization for type-I inhibitors
- DFGin_aCout (Src-like): broken K271-E286 -> volume filling, aC interactions
- DFGout_aCin: large back pocket -> type-II inhibitor extensions (imatinib-like)

These mappings are literature-informed and determine WHICH chemical
modifications are applied during state-conditioned generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from statebind.generation.models import GenerationStrategy
from statebind.processing.models import ConformationalState
from statebind.structure.models import PocketDescriptor


@dataclass
class PocketCondition:
    """Pocket-derived generation condition for a single state."""

    state: str
    representative_pdb: str
    pocket: PocketDescriptor
    strategies: list[GenerationStrategy] = field(default_factory=list)
    rationale: str = ""


# ── State-specific pocket conditions ────────────────────────────────────

def get_pocket_conditions(target_gene: str = "EGFR") -> dict[str, PocketCondition]:
    """Return pocket conditions for canonical states of the specified kinase.

    Args:
        target_gene: Target kinase gene symbol ("EGFR" or "ABL1").

    Returns:
        Dict mapping ConformationalState value -> PocketCondition.

    Each condition maps a pocket geometry to generation strategies.

    EGFR pocket volumes (literature-curated estimates):
    - DFGin_aCin (~450 Å³): Stamos et al., JBC 2002 (PDB 1M17)
    - DFGin_aCout (~520 Å³): Zhang et al., Nature 2006 (PDB 2GS7)
    - DFGout_aCin (~790 Å³): Yun et al., PNAS 2008 (PDB 3IKA/3IKU)
    DFGout_aCout removed: no genuine EGFR DFGout/aCout structures in PDB.

    ABL1 pocket volumes (literature-curated estimates):
    - DFGin_aCin (~460 Å³): Das et al., J Mol Biol 2006 (PDB 2GQG)
    - DFGin_aCout (~510 Å³): Levinson et al., PLoS Biol 2006 (PDB 2G1T)
    - DFGout_aCin (~820 Å³): Nagar et al., Cancer Res 2002 (PDB 1IEP)
    """
    if target_gene.upper() == "ABL1":
        return _abl1_pocket_conditions()
    return _egfr_pocket_conditions()


def _egfr_pocket_conditions() -> dict[str, PocketCondition]:
    """Return EGFR pocket conditions for all 3 canonical states."""
    return {
        ConformationalState.DFGIN_ACIN.value: PocketCondition(
            state=ConformationalState.DFGIN_ACIN.value,
            representative_pdb="1m17",
            pocket=PocketDescriptor(
                pocket_volume=450.0,
                back_pocket_accessible=False,
                covalent_cys_exposed=True,
                gatekeeper_clearance=3.6,
                hinge_accessibility=0.92,
                p_loop_conformation="extended",
            ),
            strategies=[
                GenerationStrategy.HINGE_OPTIMIZED,
                GenerationStrategy.GATEKEEPER_AVOIDING,
                GenerationStrategy.COVALENT_WARHEAD,
                GenerationStrategy.ANALOG,
            ],
            rationale="Compact active-state pocket. Prioritize hinge H-bonds "
                      "(accessibility 0.92), avoid gatekeeper clash (clearance "
                      "3.6 Å), exploit C797 for covalent binding.",
        ),
        ConformationalState.DFGIN_ACOUT.value: PocketCondition(
            state=ConformationalState.DFGIN_ACOUT.value,
            representative_pdb="2gs7",
            pocket=PocketDescriptor(
                pocket_volume=520.0,
                back_pocket_accessible=False,
                covalent_cys_exposed=True,
                gatekeeper_clearance=4.5,
                hinge_accessibility=0.79,
                p_loop_conformation="intermediate",
            ),
            strategies=[
                GenerationStrategy.VOLUME_FILLING,
                GenerationStrategy.HINGE_OPTIMIZED,
                GenerationStrategy.COVALENT_WARHEAD,
                GenerationStrategy.ANALOG,
            ],
            rationale="Src-like pocket with αC-helix rotated out. Moderately "
                      "larger volume (520 Å³). Hinge less accessible (0.79). "
                      "Fill extra space from αC rotation.",
        ),
        ConformationalState.DFGOUT_ACIN.value: PocketCondition(
            state=ConformationalState.DFGOUT_ACIN.value,
            representative_pdb="3w2r",
            pocket=PocketDescriptor(
                pocket_volume=800.0,
                back_pocket_accessible=True,
                covalent_cys_exposed=True,
                gatekeeper_clearance=5.0,
                hinge_accessibility=0.86,
                p_loop_conformation="extended",
            ),
            strategies=[
                GenerationStrategy.BACK_POCKET_EXTENSION,
                GenerationStrategy.VOLUME_FILLING,
                GenerationStrategy.HINGE_OPTIMIZED,
                GenerationStrategy.ANALOG,
            ],
            rationale="DFG-out opens back pocket (790 Å³). Type-II inhibitor "
                      "opportunity. Extend into allosteric back pocket behind "
                      "the DFG motif. Larger gatekeeper clearance (4.9 Å).",
        ),
    }


def _abl1_pocket_conditions() -> dict[str, PocketCondition]:
    """Return ABL1 pocket conditions for all 3 canonical states.

    ABL1 has genuine DFGout structures (unlike EGFR), making it a stronger
    test case for state conditioning. ABL1 also has a clear Src-like
    inactive (DFGin_aCout) state (PDB 2G1T, Levinson et al. 2006).

    Key differences from EGFR:
    - ABL1 lacks the C797 covalent cysteine -> no COVALENT_WARHEAD strategy
    - ABL1 T315 gatekeeper is smaller (Thr vs EGFR T790 Thr) -> similar
      gatekeeper considerations but different resistance mutation (T315I)
    - ABL1 DFGout is clinically validated (imatinib, nilotinib)

    Sources:
    - DFGin_aCin: Das et al., J Mol Biol 2006 (2GQG + dasatinib)
    - DFGin_aCout: Levinson et al., PLoS Biol 2006 (2G1T, Src-like)
    - DFGout_aCin: Nagar et al., Cancer Res 2002 (1IEP + imatinib)
    """
    return {
        ConformationalState.DFGIN_ACIN.value: PocketCondition(
            state=ConformationalState.DFGIN_ACIN.value,
            representative_pdb="2gqg",
            pocket=PocketDescriptor(
                pocket_volume=460.0,
                back_pocket_accessible=False,
                covalent_cys_exposed=False,   # ABL1 has no C797 equivalent
                gatekeeper_clearance=4.3,
                hinge_accessibility=0.94,
                p_loop_conformation="extended",
            ),
            strategies=[
                GenerationStrategy.HINGE_OPTIMIZED,
                GenerationStrategy.GATEKEEPER_AVOIDING,
                GenerationStrategy.ANALOG,
            ],
            rationale="Active ABL1 pocket. Type-I inhibitors (dasatinib-like). "
                      "Prioritize hinge H-bonds (accessibility 0.94). ABL1 lacks "
                      "EGFR C797 so no covalent strategy. Gatekeeper T315 provides "
                      "moderate clearance (4.3 Å) -- avoid clash for T315I resistance.",
        ),
        ConformationalState.DFGIN_ACOUT.value: PocketCondition(
            state=ConformationalState.DFGIN_ACOUT.value,
            representative_pdb="2g1t",
            pocket=PocketDescriptor(
                pocket_volume=510.0,
                back_pocket_accessible=False,
                covalent_cys_exposed=False,
                gatekeeper_clearance=4.5,
                hinge_accessibility=0.78,
                p_loop_conformation="intermediate",
            ),
            strategies=[
                GenerationStrategy.VOLUME_FILLING,
                GenerationStrategy.HINGE_OPTIMIZED,
                GenerationStrategy.ANALOG,
            ],
            rationale="Src-like inactive ABL1 (2G1T). K271-E286 salt bridge broken, "
                      "αC-helix rotated out. Moderately larger pocket (510 Å³). "
                      "Reduced hinge accessibility (0.78). Fill extra volume from "
                      "αC rotation.",
        ),
        ConformationalState.DFGOUT_ACIN.value: PocketCondition(
            state=ConformationalState.DFGOUT_ACIN.value,
            representative_pdb="1iep",
            pocket=PocketDescriptor(
                pocket_volume=820.0,
                back_pocket_accessible=True,
                covalent_cys_exposed=False,
                gatekeeper_clearance=5.1,
                hinge_accessibility=0.85,
                p_loop_conformation="extended",
            ),
            strategies=[
                GenerationStrategy.BACK_POCKET_EXTENSION,
                GenerationStrategy.VOLUME_FILLING,
                GenerationStrategy.HINGE_OPTIMIZED,
                GenerationStrategy.ANALOG,
            ],
            rationale="DFG-out ABL1 (imatinib-bound 1IEP). Large pocket (820 Å³) "
                      "with back pocket accessible. Classic type-II inhibitor "
                      "opportunity. Extend into allosteric back pocket behind the "
                      "DFG motif. Clinically validated by imatinib and nilotinib.",
        ),
    }


def select_strategies_for_pocket(
    pocket: PocketDescriptor,
) -> list[GenerationStrategy]:
    """Dynamically select strategies based on pocket features.

    This generalizes beyond the 4 curated states to handle
    any pocket descriptor.
    """
    strategies = [GenerationStrategy.ANALOG]  # always include baseline

    if pocket.hinge_accessibility > 0.8:
        strategies.append(GenerationStrategy.HINGE_OPTIMIZED)

    if pocket.back_pocket_accessible:
        strategies.append(GenerationStrategy.BACK_POCKET_EXTENSION)

    if pocket.pocket_volume > 600:
        strategies.append(GenerationStrategy.VOLUME_FILLING)

    if pocket.gatekeeper_clearance < 4.0:
        strategies.append(GenerationStrategy.GATEKEEPER_AVOIDING)

    if pocket.covalent_cys_exposed:
        strategies.append(GenerationStrategy.COVALENT_WARHEAD)

    if pocket.p_loop_conformation == "folded":
        strategies.append(GenerationStrategy.P_LOOP_INTERACTION)

    return strategies
