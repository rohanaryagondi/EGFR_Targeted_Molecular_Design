"""Pocket-to-modification mapping: how pocket context drives generation.

Each conformational state has distinct pocket geometry. This module maps
pocket features to generation strategies:

- DFGin_aCin (active): compact pocket → hinge optimization, gatekeeper avoidance
- DFGin_aCout (Src-like): moderate pocket, broken salt bridge → aC-helix interactions
- DFGout_aCin: large pocket + back pocket → type-II extensions
- DFGout_aCout: largest pocket, folded P-loop → volume-filling, P-loop contacts

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

def get_pocket_conditions() -> dict[str, PocketCondition]:
    """Return pocket conditions for all 4 canonical EGFR states.

    Each condition maps a pocket geometry to generation strategies.

    Pocket volumes are literature-curated estimates:
    - DFGin_aCin (~450 Å³): Stamos et al., JBC 2002 (PDB 1M17)
    - DFGin_aCout (~520 Å³): Zhang et al., Nature 2006 (PDB 2GS7)
    - DFGout_aCin (~790 Å³): Yun et al., PNAS 2008 (PDB 3IKA/3IKU)
    - DFGout_aCout (~850 Å³): Park et al., JACS 2015 (PDB 4ZAU)

    Exact volumes vary by detection method. Values represent approximate
    magnitude and relative ordering across states.
    """
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
            representative_pdb="3iku",
            pocket=PocketDescriptor(
                pocket_volume=790.0,
                back_pocket_accessible=True,
                covalent_cys_exposed=True,
                gatekeeper_clearance=4.9,
                hinge_accessibility=0.85,
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
        ConformationalState.DFGOUT_ACOUT.value: PocketCondition(
            state=ConformationalState.DFGOUT_ACOUT.value,
            representative_pdb="4zau",
            pocket=PocketDescriptor(
                pocket_volume=850.0,
                back_pocket_accessible=True,
                covalent_cys_exposed=True,
                gatekeeper_clearance=5.1,
                hinge_accessibility=0.71,
                p_loop_conformation="folded",
            ),
            strategies=[
                GenerationStrategy.BACK_POCKET_EXTENSION,
                GenerationStrategy.VOLUME_FILLING,
                GenerationStrategy.P_LOOP_INTERACTION,
                GenerationStrategy.ANALOG,
            ],
            rationale="Largest pocket (850 Å³). Both DFG flipped and αC rotated. "
                      "Back pocket accessible. P-loop folded over pocket — "
                      "design for P-loop contacts. Reduced hinge access (0.71).",
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
