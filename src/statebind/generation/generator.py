"""State-conditioned candidate generator.

Generates molecular candidates tailored to each conformational state's
pocket geometry. Each strategy applies different SMILES transformations:

- HINGE_OPTIMIZED: add/optimize hinge-binding motifs
- BACK_POCKET_EXTENSION: append hydrophobic tails for type-II binding
- GATEKEEPER_AVOIDING: shrink substituents near gatekeeper position
- VOLUME_FILLING: add bulky groups for large pockets
- COVALENT_WARHEAD: append acrylamide warhead for C797
- P_LOOP_INTERACTION: add groups engaging folded P-loop
- ANALOG: baseline halogen/methyl swaps (same as Phase 2)

All transformations are SMILES-level. No 3D docking. The point is to
produce structurally distinct candidate sets per state, not to guarantee
binding. Chemical realism is approximate.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from statebind.baselines.candidates import (
    _enumerate_simple_analogs,
    build_reference_candidates,
)
from statebind.baselines.models import CandidateSource
from statebind.generation.conditioning import PocketCondition, get_pocket_conditions
from statebind.generation.models import (
    GenerationStrategy,
    MultiStateGenerationResult,
    StateConditionedCandidate,
    StateConditionedLibrary,
)


def _gen_id(smiles: str, state: str, strategy: str) -> str:
    """Generate a deterministic candidate ID."""
    key = f"{smiles}:{state}:{strategy}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


# ── Strategy-specific SMILES transformations ─────────────────────────────

def _hinge_optimized(smiles: str, parent_id: str, state: str) -> list[StateConditionedCandidate]:
    """Add or optimize hinge-binding motifs.

    Hinge H-bond donors/acceptors (aminopyrimidine, quinazoline).
    Transformations: add pyrimidine N, swap phenyl→pyridyl.
    """
    results = []

    # Phenyl → pyridyl swap (adds N for hinge H-bond)
    if "c1ccccc1" in smiles:
        new = smiles.replace("c1ccccc1", "c1ccncc1", 1)
        results.append(StateConditionedCandidate(
            candidate_id=_gen_id(new, state, "hinge_pyridyl"),
            smiles=new,
            source=CandidateSource.ENUMERATED,
            parent_id=parent_id,
            target_state=state,
            strategy=GenerationStrategy.HINGE_OPTIMIZED,
            notes="Phenyl→pyridyl swap for hinge H-bond",
        ))

    # Add amino group on heterocycle (for hinge NH)
    if "ncnc" in smiles.lower():
        new = smiles.replace("ncnc", "nc(N)nc", 1)
        if new != smiles:
            results.append(StateConditionedCandidate(
                candidate_id=_gen_id(new, state, "hinge_amino"),
                smiles=new,
                source=CandidateSource.ENUMERATED,
                parent_id=parent_id,
                target_state=state,
                strategy=GenerationStrategy.HINGE_OPTIMIZED,
                notes="Added amino group on pyrimidine for hinge contact",
            ))

    return results


def _back_pocket_extension(
    smiles: str, parent_id: str, state: str,
) -> list[StateConditionedCandidate]:
    """Extend molecule into DFG-out back pocket.

    Type-II inhibitor design: add hydrophobic tails that reach
    behind the DFG motif.
    """
    results = []

    # Append trifluoromethyl group (compact hydrophobic)
    new_cf3 = smiles + "C(F)(F)F"
    results.append(StateConditionedCandidate(
        candidate_id=_gen_id(new_cf3, state, "backpocket_cf3"),
        smiles=new_cf3,
        source=CandidateSource.ENUMERATED,
        parent_id=parent_id,
        target_state=state,
        strategy=GenerationStrategy.BACK_POCKET_EXTENSION,
        notes="CF3 tail for back pocket hydrophobic contact",
    ))

    # Append phenyl-amide linker (classic type-II extension)
    new_amide = smiles + "C(=O)Nc1ccccc1"
    results.append(StateConditionedCandidate(
        candidate_id=_gen_id(new_amide, state, "backpocket_amide"),
        smiles=new_amide,
        source=CandidateSource.ENUMERATED,
        parent_id=parent_id,
        target_state=state,
        strategy=GenerationStrategy.BACK_POCKET_EXTENSION,
        notes="Amide-phenyl tail for type-II back pocket binding",
    ))

    # Append methylpiperazine (solubilizing + back pocket fill)
    new_piperazine = smiles + "N1CCN(C)CC1"
    results.append(StateConditionedCandidate(
        candidate_id=_gen_id(new_piperazine, state, "backpocket_piperazine"),
        smiles=new_piperazine,
        source=CandidateSource.ENUMERATED,
        parent_id=parent_id,
        target_state=state,
        strategy=GenerationStrategy.BACK_POCKET_EXTENSION,
        notes="Methylpiperazine extension into back pocket",
    ))

    return results


def _gatekeeper_avoiding(
    smiles: str, parent_id: str, state: str,
) -> list[StateConditionedCandidate]:
    """Shrink substituents near the gatekeeper position.

    For tight gatekeeper clearance (< 4 Å), remove bulky groups
    that would clash with T790 (or M790 in T790M).
    """
    results = []

    # Remove methoxy → hydrogen (shrink)
    if "OC" in smiles:
        new = smiles.replace("OC", "O", 1)
        if new != smiles and len(new) > 10:
            results.append(StateConditionedCandidate(
                candidate_id=_gen_id(new, state, "gk_shrink_ome"),
                smiles=new,
                source=CandidateSource.ENUMERATED,
                parent_id=parent_id,
                target_state=state,
                strategy=GenerationStrategy.GATEKEEPER_AVOIDING,
                notes="Removed methoxy to reduce gatekeeper clash",
            ))

    # Cl → F swap (smaller halogen)
    if "Cl" in smiles:
        new = smiles.replace("Cl", "F", 1)
        results.append(StateConditionedCandidate(
            candidate_id=_gen_id(new, state, "gk_cl_to_f"),
            smiles=new,
            source=CandidateSource.ENUMERATED,
            parent_id=parent_id,
            target_state=state,
            strategy=GenerationStrategy.GATEKEEPER_AVOIDING,
            notes="Cl→F swap to reduce gatekeeper steric clash",
        ))

    return results


def _volume_filling(smiles: str, parent_id: str, state: str) -> list[StateConditionedCandidate]:
    """Add bulky groups to fill large pockets (> 600 Å³)."""
    results = []

    # Add cyclohexyl
    new_chex = smiles + "C1CCCCC1"
    results.append(StateConditionedCandidate(
        candidate_id=_gen_id(new_chex, state, "vol_cyclohexyl"),
        smiles=new_chex,
        source=CandidateSource.ENUMERATED,
        parent_id=parent_id,
        target_state=state,
        strategy=GenerationStrategy.VOLUME_FILLING,
        notes="Cyclohexyl for large pocket volume filling",
    ))

    # Add naphthyl
    new_naph = smiles + "c1ccc2ccccc2c1"
    results.append(StateConditionedCandidate(
        candidate_id=_gen_id(new_naph, state, "vol_naphthyl"),
        smiles=new_naph,
        source=CandidateSource.ENUMERATED,
        parent_id=parent_id,
        target_state=state,
        strategy=GenerationStrategy.VOLUME_FILLING,
        notes="Naphthyl for volume filling in DFG-out pocket",
    ))

    return results


def _covalent_warhead(smiles: str, parent_id: str, state: str) -> list[StateConditionedCandidate]:
    """Append covalent warhead motifs targeting C797."""
    results = []

    # Acrylamide warhead (osimertinib-like)
    new_acry = smiles + "C(=O)/C=C/C"
    results.append(StateConditionedCandidate(
        candidate_id=_gen_id(new_acry, state, "cov_acrylamide"),
        smiles=new_acry,
        source=CandidateSource.ENUMERATED,
        parent_id=parent_id,
        target_state=state,
        strategy=GenerationStrategy.COVALENT_WARHEAD,
        notes="Acrylamide warhead for C797 covalent binding",
    ))

    return results


def _p_loop_interaction(smiles: str, parent_id: str, state: str) -> list[StateConditionedCandidate]:
    """Add groups that engage the folded P-loop."""
    results = []

    # Add sulfonamide (P-loop H-bond)
    new_sulfonamide = smiles + "S(=O)(=O)N"
    results.append(StateConditionedCandidate(
        candidate_id=_gen_id(new_sulfonamide, state, "ploop_sulfonamide"),
        smiles=new_sulfonamide,
        source=CandidateSource.ENUMERATED,
        parent_id=parent_id,
        target_state=state,
        strategy=GenerationStrategy.P_LOOP_INTERACTION,
        notes="Sulfonamide for P-loop H-bond contact",
    ))

    return results


# Strategy dispatch
_STRATEGY_FN = {
    GenerationStrategy.HINGE_OPTIMIZED: _hinge_optimized,
    GenerationStrategy.BACK_POCKET_EXTENSION: _back_pocket_extension,
    GenerationStrategy.GATEKEEPER_AVOIDING: _gatekeeper_avoiding,
    GenerationStrategy.VOLUME_FILLING: _volume_filling,
    GenerationStrategy.COVALENT_WARHEAD: _covalent_warhead,
    GenerationStrategy.P_LOOP_INTERACTION: _p_loop_interaction,
}


def _generate_analogs(
    smiles: str, parent_id: str, state: str,
) -> list[StateConditionedCandidate]:
    """Generate simple analogs (halogen/methyl swaps) from Phase 2."""
    baseline_analogs = _enumerate_simple_analogs(smiles, parent_id)
    results = []
    for ba in baseline_analogs:
        results.append(StateConditionedCandidate(
            candidate_id=_gen_id(ba.smiles, state, "analog"),
            smiles=ba.smiles,
            source=CandidateSource.ENUMERATED,
            parent_id=parent_id,
            target_state=state,
            strategy=GenerationStrategy.ANALOG,
            notes=ba.notes,
        ))
    return results


def generate_for_state(
    condition: PocketCondition,
) -> StateConditionedLibrary:
    """Generate candidates conditioned on a single state's pocket.

    Steps:
    1. Start with reference compounds (approved EGFR TKIs)
    2. For each reference, apply state-specific strategies
    3. For each reference, also generate baseline analogs
    4. Deduplicate by SMILES within this state

    Returns:
        StateConditionedLibrary for this state.
    """
    references = build_reference_candidates()

    all_candidates: list[StateConditionedCandidate] = []
    strategies_used: set[str] = set()

    for ref in references:
        # Add reference as-is
        all_candidates.append(StateConditionedCandidate(
            candidate_id=_gen_id(ref.smiles, condition.state, "reference"),
            smiles=ref.smiles,
            source=CandidateSource.REFERENCE,
            parent_id=ref.candidate_id,
            target_state=condition.state,
            target_pdb_id=condition.representative_pdb,
            strategy=GenerationStrategy.REFERENCE,
            pocket_volume=condition.pocket.pocket_volume,
            back_pocket=condition.pocket.back_pocket_accessible,
            gatekeeper_clearance=condition.pocket.gatekeeper_clearance,
            notes=f"Reference compound for {condition.state}",
        ))
        strategies_used.add(GenerationStrategy.REFERENCE.value)

        # Apply state-specific strategies
        for strategy in condition.strategies:
            if strategy == GenerationStrategy.ANALOG:
                analogs = _generate_analogs(ref.smiles, ref.candidate_id, condition.state)
                for a in analogs:
                    a.target_pdb_id = condition.representative_pdb
                    a.pocket_volume = condition.pocket.pocket_volume
                    a.back_pocket = condition.pocket.back_pocket_accessible
                    a.gatekeeper_clearance = condition.pocket.gatekeeper_clearance
                all_candidates.extend(analogs)
                strategies_used.add(strategy.value)
            elif strategy in _STRATEGY_FN:
                fn = _STRATEGY_FN[strategy]
                mods = fn(ref.smiles, ref.candidate_id, condition.state)
                for m in mods:
                    m.target_pdb_id = condition.representative_pdb
                    m.pocket_volume = condition.pocket.pocket_volume
                    m.back_pocket = condition.pocket.back_pocket_accessible
                    m.gatekeeper_clearance = condition.pocket.gatekeeper_clearance
                all_candidates.extend(mods)
                strategies_used.add(strategy.value)

    # Deduplicate by SMILES within state
    seen: set[str] = set()
    unique: list[StateConditionedCandidate] = []
    for c in all_candidates:
        if c.smiles not in seen:
            seen.add(c.smiles)
            unique.append(c)

    return StateConditionedLibrary(
        state=condition.state,
        representative_pdb=condition.representative_pdb,
        pocket_volume=condition.pocket.pocket_volume,
        back_pocket_accessible=condition.pocket.back_pocket_accessible,
        candidates=unique,
        n_candidates=len(unique),
        strategies_used=sorted(strategies_used),
        generation_config={
            "strategies": [s.value for s in condition.strategies],
            "rationale": condition.rationale,
        },
    )


def generate_all_states() -> MultiStateGenerationResult:
    """Generate candidates for all 4 conformational states.

    Returns:
        MultiStateGenerationResult with per-state libraries.
    """
    conditions = get_pocket_conditions()
    libraries: list[StateConditionedLibrary] = []

    for state_name in sorted(conditions.keys()):
        cond = conditions[state_name]
        lib = generate_for_state(cond)
        libraries.append(lib)

    # Compute cross-state SMILES overlap
    state_smiles: dict[str, set[str]] = {}
    for lib in libraries:
        state_smiles[lib.state] = {c.smiles for c in lib.candidates}

    overlap: dict[str, int] = {}
    states_list = sorted(state_smiles.keys())
    for i, s1 in enumerate(states_list):
        for j, s2 in enumerate(states_list):
            if i < j:
                shared = len(state_smiles[s1] & state_smiles[s2])
                overlap[f"{s1}|{s2}"] = shared

    # Total unique
    all_smiles: set[str] = set()
    total = 0
    for lib in libraries:
        total += lib.n_candidates
        all_smiles.update(c.smiles for c in lib.candidates)

    now = datetime.now(timezone.utc).isoformat()

    return MultiStateGenerationResult(
        states=states_list,
        libraries=libraries,
        total_candidates=total,
        total_unique_smiles=len(all_smiles),
        cross_state_overlap=overlap,
        generated_at=now,
        notes="State-conditioned generation. Each state has different "
              "modification strategies driven by pocket geometry.",
    )
