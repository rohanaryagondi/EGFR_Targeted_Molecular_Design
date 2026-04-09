"""Feature extraction from mutation records for context-to-state prediction.

Three feature sets are available:
1. Mutation-only: position, amino acid properties, mechanism, resistance gen
2. Expression/pathway proxy: simulated pathway activation scores (v1 proxy)
3. Combined: mutation + expression features

All features are numeric or one-hot encoded. No raw strings reach the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from statebind.processing.models import (
    ConformationalState,
    MechanismCategory,
    MutationRecord,
    ResistanceGeneration,
)

# ── Amino acid property tables ───────────────────────────────────────────

# Kyte-Doolittle hydrophobicity scale (normalized to [0, 1])
_HYDROPHOBICITY: dict[str, float] = {
    "I": 1.00, "V": 0.97, "L": 0.92, "F": 0.72, "C": 0.64,
    "M": 0.48, "A": 0.47, "G": 0.00, "T": 0.19, "S": 0.17,
    "W": 0.40, "Y": 0.36, "P": 0.39, "D": 0.11, "E": 0.11,
    "N": 0.11, "Q": 0.11, "H": 0.17, "K": 0.08, "R": 0.00,
}

# Residue molecular weight (daltons, approximate)
_RESIDUE_MW: dict[str, float] = {
    "G": 57.05, "A": 71.08, "V": 99.13, "L": 113.16, "I": 113.16,
    "P": 97.12, "F": 147.18, "W": 186.21, "M": 131.20, "S": 87.08,
    "T": 101.10, "C": 103.14, "Y": 163.18, "H": 137.14, "D": 115.09,
    "E": 129.12, "N": 114.10, "Q": 128.13, "K": 128.17, "R": 156.19,
}

# Residue volume (Å³, from Zamyatnin)
_RESIDUE_VOLUME: dict[str, float] = {
    "G": 60.1, "A": 88.6, "V": 140.0, "L": 166.7, "I": 166.7,
    "P": 122.7, "F": 189.9, "W": 227.8, "M": 162.9, "S": 89.0,
    "T": 116.1, "C": 108.5, "Y": 193.6, "H": 153.2, "D": 111.1,
    "E": 138.4, "N": 114.1, "Q": 143.8, "K": 168.6, "R": 173.4,
}

# Charge at pH 7 (simplified)
_CHARGE: dict[str, float] = {
    "G": 0.0, "A": 0.0, "V": 0.0, "L": 0.0, "I": 0.0,
    "P": 0.0, "F": 0.0, "W": 0.0, "M": 0.0, "S": 0.0,
    "T": 0.0, "C": 0.0, "Y": 0.0, "H": 0.5, "D": -1.0,
    "E": -1.0, "N": 0.0, "Q": 0.0, "K": 1.0, "R": 1.0,
}

# EGFR kinase domain boundaries
_KINASE_START = 696
_KINASE_END = 1022

# Mechanism category to one-hot index
_MECHANISM_INDEX: dict[str, int] = {
    cat.value: i for i, cat in enumerate(MechanismCategory)
}

# Resistance generation to ordinal
_GENERATION_ORDINAL: dict[str, float] = {
    ResistanceGeneration.ACTIVATING.value: 0.0,
    ResistanceGeneration.FIRST.value: 1.0,
    ResistanceGeneration.SECOND.value: 2.0,
    ResistanceGeneration.THIRD.value: 3.0,
    ResistanceGeneration.FOURTH.value: 4.0,
    ResistanceGeneration.UNKNOWN.value: 2.0,  # neutral default
}

# ── Expression/pathway proxy features ────────────────────────────────────
# v1: These are deterministic proxies based on mutation properties, standing
# in for actual expression/pathway data. Documented as proxies, not real data.

_PATHWAY_SCORES: dict[str, dict[str, float]] = {
    # mutation_id -> {pathway: activation_score}
    # Scores are on [0, 1]. Curated from published functional studies.
    "L858R":   {"mapk": 0.85, "pi3k": 0.80, "stat3": 0.70, "src": 0.30},
    "G719S":   {"mapk": 0.65, "pi3k": 0.55, "stat3": 0.40, "src": 0.25},
    "L861Q":   {"mapk": 0.60, "pi3k": 0.50, "stat3": 0.35, "src": 0.20},
    "S768I":   {"mapk": 0.50, "pi3k": 0.45, "stat3": 0.30, "src": 0.20},
    "T790M":   {"mapk": 0.75, "pi3k": 0.70, "stat3": 0.55, "src": 0.40},
    "D761Y":   {"mapk": 0.45, "pi3k": 0.40, "stat3": 0.25, "src": 0.20},
    "T854A":   {"mapk": 0.40, "pi3k": 0.35, "stat3": 0.20, "src": 0.15},
    "L747S":   {"mapk": 0.50, "pi3k": 0.45, "stat3": 0.30, "src": 0.20},
    "C797S":   {"mapk": 0.80, "pi3k": 0.75, "stat3": 0.60, "src": 0.35},
    "G796D":   {"mapk": 0.55, "pi3k": 0.50, "stat3": 0.35, "src": 0.25},
    "L792H":   {"mapk": 0.50, "pi3k": 0.45, "stat3": 0.30, "src": 0.20},
    "G724S":   {"mapk": 0.55, "pi3k": 0.50, "stat3": 0.35, "src": 0.25},
    "G796S":   {"mapk": 0.50, "pi3k": 0.45, "stat3": 0.30, "src": 0.20},
    "G796R":   {"mapk": 0.50, "pi3k": 0.45, "stat3": 0.30, "src": 0.25},
    "L718Q":   {"mapk": 0.55, "pi3k": 0.50, "stat3": 0.35, "src": 0.25},
    "L718V":   {"mapk": 0.55, "pi3k": 0.50, "stat3": 0.35, "src": 0.25},
    "L858R+T790M+C797S": {"mapk": 0.90, "pi3k": 0.85, "stat3": 0.75, "src": 0.50},
}

PATHWAY_NAMES = ["mapk", "pi3k", "stat3", "src"]


@dataclass
class FeatureSet:
    """Container for extracted features from a single mutation."""

    mutation_id: str
    feature_names: list[str] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    label: str = ""  # target state label
    label_distribution: dict[str, float] = field(default_factory=dict)
    split: str = "unassigned"


def mutation_feature_names() -> list[str]:
    """Return ordered list of mutation-only feature names."""
    names = [
        "relative_position",       # position within kinase domain [0,1]
        "wt_hydrophobicity",       # wild-type residue hydrophobicity
        "mut_hydrophobicity",      # mutant residue hydrophobicity
        "delta_hydrophobicity",    # change in hydrophobicity
        "wt_volume",               # wild-type residue volume
        "mut_volume",              # mutant residue volume
        "delta_volume",            # change in volume
        "wt_charge",               # wild-type charge
        "mut_charge",              # mutant charge
        "delta_charge",            # change in charge
        "wt_mw",                   # wild-type molecular weight
        "mut_mw",                  # mutant molecular weight
        "delta_mw",                # change in molecular weight
        "generation_ordinal",      # resistance generation as ordinal
        "n_drugs_affected",        # number of drugs made ineffective
        "n_drugs_effective",       # number of drugs still effective
        "has_known_structures",    # whether PDB structures exist
    ]
    # One-hot mechanism category (12 categories)
    for cat in MechanismCategory:
        names.append(f"mechanism_{cat.value}")
    return names


def pathway_feature_names() -> list[str]:
    """Return ordered list of pathway proxy feature names."""
    return [f"pathway_{p}" for p in PATHWAY_NAMES]


def all_feature_names() -> list[str]:
    """Return ordered list of all feature names (mutation + pathway)."""
    return mutation_feature_names() + pathway_feature_names()


def extract_mutation_features(m: MutationRecord) -> list[float]:
    """Extract mutation-only numeric features from a MutationRecord.

    Returns a fixed-length vector of floats. Order matches mutation_feature_names().
    """
    # Position features
    rel_pos = (m.position - _KINASE_START) / (_KINASE_END - _KINASE_START)
    rel_pos = max(0.0, min(1.0, rel_pos))

    # Amino acid property deltas
    wt_hydro = _HYDROPHOBICITY.get(m.wild_type, 0.5)
    mut_hydro = _HYDROPHOBICITY.get(m.mutant, 0.5)
    wt_vol = _RESIDUE_VOLUME.get(m.wild_type, 130.0)
    mut_vol = _RESIDUE_VOLUME.get(m.mutant, 130.0)
    wt_chg = _CHARGE.get(m.wild_type, 0.0)
    mut_chg = _CHARGE.get(m.mutant, 0.0)
    wt_mw = _RESIDUE_MW.get(m.wild_type, 110.0)
    mut_mw = _RESIDUE_MW.get(m.mutant, 110.0)

    # Resistance generation ordinal
    gen_ord = _GENERATION_ORDINAL.get(m.resistance_generation.value, 2.0)

    # Drug counts
    n_affected = float(len(m.known_drugs_affected))
    n_effective = float(len(m.known_drugs_effective))

    # Has structures
    has_structs = 1.0 if len(m.pdb_structures) > 0 else 0.0

    # Mechanism one-hot
    mech_onehot = [0.0] * len(MechanismCategory)
    idx = _MECHANISM_INDEX.get(m.mechanism_category.value)
    if idx is not None:
        mech_onehot[idx] = 1.0

    values = [
        rel_pos,
        wt_hydro, mut_hydro, wt_hydro - mut_hydro,
        wt_vol, mut_vol, wt_vol - mut_vol,
        wt_chg, mut_chg, wt_chg - mut_chg,
        wt_mw, mut_mw, wt_mw - mut_mw,
        gen_ord,
        n_affected, n_effective,
        has_structs,
    ] + mech_onehot

    return values


def extract_pathway_features(m: MutationRecord) -> list[float]:
    """Extract pathway proxy features for a mutation.

    v1: Uses curated proxy scores. Not real expression data.
    Returns zeros for unknown mutations.
    """
    scores = _PATHWAY_SCORES.get(m.mutation_id, {})
    return [scores.get(p, 0.0) for p in PATHWAY_NAMES]


def extract_all_features(m: MutationRecord) -> list[float]:
    """Extract combined mutation + pathway feature vector."""
    return extract_mutation_features(m) + extract_pathway_features(m)


def assign_state_label(m: MutationRecord) -> tuple[str, dict[str, float]]:
    """Assign a conformational state label to a mutation.

    Label assignment strategy (documented assumptions):
    1. If preferred_states is non-empty, use the first as primary label.
    2. If preferred_states is empty, assign "DFGin_aCin" as default
       (most mutations retain some active-state binding).

    Also returns a soft label distribution across all 3 states.
    The distribution is:
    - 0.7 for the primary state
    - 0.15 distributed among other states
    - If multiple preferred_states, distribute 0.7 proportionally

    Returns:
        (primary_label, {state: probability})
    """
    all_states = [
        ConformationalState.DFGIN_ACIN,
        ConformationalState.DFGIN_ACOUT,
        ConformationalState.DFGOUT_ACIN,
    ]

    preferred = m.preferred_states
    if not preferred:
        # Default assumption: mutations without known preference
        # are assigned to active state with low confidence
        primary = ConformationalState.DFGIN_ACIN.value
        n = len(all_states)
        p = 1.0 / n
        dist = {s.value: p for s in all_states}  # uniform = uncertain
        return primary, dist

    primary = preferred[0].value

    # Build soft distribution
    n_preferred = len(preferred)
    preferred_set = {s.value for s in preferred}

    dist: dict[str, float] = {}
    remaining_mass = 0.3  # 30% spread to non-preferred
    preferred_mass = 0.7  # 70% to preferred states
    n_non_preferred = len(all_states) - n_preferred

    for s in all_states:
        if s.value in preferred_set:
            dist[s.value] = preferred_mass / n_preferred
        else:
            dist[s.value] = remaining_mass / max(n_non_preferred, 1)

    return primary, dist


def build_feature_matrix(
    mutations: list[MutationRecord],
    feature_set: str = "all",
) -> list[FeatureSet]:
    """Build feature matrix from a list of mutations.

    Args:
        mutations: List of mutation records.
        feature_set: One of "mutation", "pathway", "all".

    Returns:
        List of FeatureSet objects, one per mutation.
    """
    extractors = {
        "mutation": (extract_mutation_features, mutation_feature_names),
        "pathway": (extract_pathway_features, pathway_feature_names),
        "all": (extract_all_features, all_feature_names),
    }

    if feature_set not in extractors:
        raise ValueError(f"Unknown feature_set: {feature_set}. Use: {list(extractors)}")

    extract_fn, name_fn = extractors[feature_set]
    names = name_fn()

    results = []
    for m in mutations:
        label, dist = assign_state_label(m)
        fs = FeatureSet(
            mutation_id=m.mutation_id,
            feature_names=names,
            values=extract_fn(m),
            label=label,
            label_distribution=dist,
            split=m.split,
        )
        results.append(fs)

    return results
