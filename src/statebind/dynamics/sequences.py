"""State sequence construction from literature-curated transition knowledge.

EGFR kinase domain transitions between conformational states are well-documented
in the structural biology literature. This module constructs plausible state
sequences (pseudo-trajectories) from three sources:

1. **Canonical pathways**: Known activation/inactivation routes
2. **Drug-induced transitions**: Conformational shifts caused by inhibitor binding
3. **Mutation-induced bias**: How mutations alter state equilibria

These are NOT MD simulation trajectories. They are literature-curated transition
sequences that encode expert knowledge about EGFR conformational dynamics.
Every sequence has a provenance field documenting its source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from statebind.processing.models import ConformationalState

# Short aliases for readability (3-state model: DFGout_aCout removed)
_ACT = ConformationalState.DFGIN_ACIN       # Active
_SRC = ConformationalState.DFGIN_ACOUT      # Src-like inactive
_OUT = ConformationalState.DFGOUT_ACIN      # DFGout intermediate (deepest inactive)


@dataclass
class StateTransition:
    """A single observed or inferred state-to-state transition."""

    from_state: str
    to_state: str
    context: str = ""          # what triggered this transition
    evidence_type: str = ""    # "crystallographic", "kinetic", "inferred"
    reference: str = ""        # PMID or source
    weight: float = 1.0        # confidence weight


@dataclass
class StateSequence:
    """An ordered sequence of conformational state visits.

    Represents a trajectory through state space — either a known
    biological pathway or a constructed pseudo-trajectory.
    """

    sequence_id: str
    states: list[str]
    description: str = ""
    provenance: str = ""       # how this sequence was constructed
    context: str = ""          # mutation/drug context
    is_synthetic: bool = False # True if algorithmically generated


@dataclass
class TransitionDataset:
    """Collection of state sequences and pairwise transitions."""

    sequences: list[StateSequence] = field(default_factory=list)
    transitions: list[StateTransition] = field(default_factory=list)
    n_sequences: int = 0
    n_transitions: int = 0
    states: list[str] = field(default_factory=list)
    generated_at: str = ""
    version: str = "1.0.0"
    notes: str = ""


def _canonical_sequences() -> list[StateSequence]:
    """Literature-curated canonical EGFR state transition sequences.

    Sources:
    - Shan et al., PNAS 2013 (EGFR activation mechanism)
    - Ruan & Bhatt, PNAS 2012 (conformational transitions)
    - Sutto & Bhatt, PNAS 2014 (DFG dynamics)
    - Yosaatmadja et al., Structure 2015 (EGFR states)
    """
    return [
        # ── Activation pathways ─────────────────────────────
        StateSequence(
            sequence_id="canonical_activation_1",
            states=[_OUT.value, _OUT.value, _SRC.value, _ACT.value],
            description="DFGout inactive → active via DFG flip then αC rotation",
            provenance="Shan et al., PNAS 2013; Ruan & Bhatt, PNAS 2012",
            context="WT EGFR activation",
        ),
        StateSequence(
            sequence_id="canonical_activation_2",
            states=[_SRC.value, _ACT.value],
            description="Direct Src-like → active (αC-helix rotation only)",
            provenance="Shan et al., PNAS 2013",
            context="WT EGFR, no DFG flip needed",
        ),
        StateSequence(
            sequence_id="canonical_activation_3",
            states=[_OUT.value, _SRC.value, _ACT.value],
            description="DFGout inactive → Src-like → active (αC moves first)",
            provenance="Sutto & Bhatt, PNAS 2014",
            context="Alternative activation route",
        ),

        # ── Inactivation pathways ───────────────────────────
        StateSequence(
            sequence_id="canonical_inactivation_1",
            states=[_ACT.value, _SRC.value, _OUT.value],
            description="Active → Src-like → DFGout inactive",
            provenance="Shan et al., PNAS 2013",
            context="WT EGFR autoinhibition",
        ),
        StateSequence(
            sequence_id="canonical_inactivation_2",
            states=[_ACT.value, _SRC.value],
            description="Active → Src-like (αC-helix rotation only)",
            provenance="Yosaatmadja et al., Structure 2015",
            context="Partial inactivation",
        ),
        StateSequence(
            sequence_id="canonical_inactivation_3",
            states=[_ACT.value, _OUT.value, _OUT.value],
            description="Active → DFGout intermediate → DFGout inactive",
            provenance="Sutto & Bhatt, PNAS 2014",
            context="DFG-first inactivation route",
        ),

        # ── Drug-induced transitions ────────────────────────
        StateSequence(
            sequence_id="type1_inhibitor_binding",
            states=[_ACT.value, _ACT.value],
            description="Type-I inhibitor locks active conformation",
            provenance="KLIFS database; gefitinib/erlotinib co-crystals",
            context="Gefitinib, erlotinib, osimertinib binding",
        ),
        StateSequence(
            sequence_id="type2_inhibitor_binding",
            states=[_ACT.value, _OUT.value],
            description="Type-II inhibitor induces DFG flip to DFGout",
            provenance="KLIFS database",
            context="Type-II inhibitor binding (e.g., lapatinib-like)",
        ),
        StateSequence(
            sequence_id="allosteric_inhibitor_binding",
            states=[_ACT.value, _SRC.value],
            description="Allosteric inhibitor stabilizes Src-like inactive",
            provenance="Jia et al., Structure 2016",
            context="Allosteric EGFR inhibition",
        ),

        # ── Mutation-biased transitions ─────────────────────
        StateSequence(
            sequence_id="l858r_bias",
            states=[_SRC.value, _ACT.value, _ACT.value, _ACT.value],
            description="L858R destabilizes inactive, shifts equilibrium to active",
            provenance="Sordella et al., Science 2004; Red Brewer et al., PNAS 2009",
            context="L858R activating mutation",
        ),
        StateSequence(
            sequence_id="t790m_bias",
            states=[_SRC.value, _ACT.value, _ACT.value],
            description="T790M stabilizes hydrophobic spine, favors active state",
            provenance="Yun et al., PNAS 2008",
            context="T790M gatekeeper mutation",
        ),
        StateSequence(
            sequence_id="t790m_resistance",
            states=[_ACT.value, _ACT.value, _ACT.value],
            description="T790M locks active conformation, resists 1st-gen TKI-induced inactivation",
            provenance="Yun et al., PNAS 2008",
            context="T790M + gefitinib/erlotinib",
        ),
        StateSequence(
            sequence_id="c797s_mechanism",
            states=[_ACT.value, _ACT.value],
            description="C797S retains active state, blocks covalent binding only",
            provenance="Thress et al., Nat Med 2015",
            context="C797S resistance to osimertinib",
        ),

        # ── Equilibrium fluctuations ────────────────────────
        StateSequence(
            sequence_id="wt_equilibrium_1",
            states=[_ACT.value, _SRC.value, _ACT.value, _SRC.value, _ACT.value],
            description="WT EGFR fluctuates between active and Src-like",
            provenance="Shan et al., PNAS 2013 (computed equilibrium)",
            context="WT EGFR, no ligand",
        ),
        StateSequence(
            sequence_id="wt_equilibrium_2",
            states=[_SRC.value, _OUT.value, _SRC.value, _OUT.value, _OUT.value],
            description="WT EGFR samples inactive states",
            provenance="Sutto & Bhatt, PNAS 2014 (computed equilibrium)",
            context="WT EGFR, no ligand, deeper inactive sampling",
        ),
        StateSequence(
            sequence_id="wt_equilibrium_3",
            states=[_ACT.value, _SRC.value, _OUT.value, _OUT.value, _ACT.value],
            description="WT EGFR full cycle through all states",
            provenance="Composite from MD literature",
            context="WT EGFR, illustrative full cycle",
            is_synthetic=True,
        ),
    ]


def extract_transitions(sequences: list[StateSequence]) -> list[StateTransition]:
    """Extract all pairwise transitions from state sequences.

    Each consecutive pair (state[i], state[i+1]) in a sequence becomes
    a StateTransition record.
    """
    transitions: list[StateTransition] = []
    for seq in sequences:
        for i in range(len(seq.states) - 1):
            transitions.append(StateTransition(
                from_state=seq.states[i],
                to_state=seq.states[i + 1],
                context=seq.context,
                evidence_type="inferred" if seq.is_synthetic else "literature",
                reference=seq.provenance,
            ))
    return transitions


def build_transition_dataset() -> TransitionDataset:
    """Build the complete transition dataset from curated sequences.

    Returns:
        TransitionDataset with sequences and extracted transitions.
    """
    sequences = _canonical_sequences()
    transitions = extract_transitions(sequences)

    all_states = sorted(set(
        s for seq in sequences for s in seq.states
    ))

    now = datetime.now(timezone.utc).isoformat()

    return TransitionDataset(
        sequences=sequences,
        transitions=transitions,
        n_sequences=len(sequences),
        n_transitions=len(transitions),
        states=all_states,
        generated_at=now,
        notes="Literature-curated EGFR state sequences. "
              "NOT MD trajectories. See provenance on each sequence.",
    )
