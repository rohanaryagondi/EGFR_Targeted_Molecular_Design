"""Diversity analysis for state-conditioned candidate sets.

Computes:
- Intra-state diversity: how diverse candidates are WITHIN each state
- Cross-state overlap: how many candidates are shared between states
- State-unique candidates: candidates only generated for one state
- Diversity comparison vs static baseline
"""

from __future__ import annotations

from dataclasses import dataclass, field

from statebind.baselines.scoring import _tanimoto_ngram
from statebind.generation.models import (
    FilteredStateLibrary,
    MultiStateFilterResult,
    StateConditionedCandidate,
)


@dataclass
class DiversityMetrics:
    """Diversity metrics for a set of candidates."""

    n_candidates: int = 0
    n_unique_smiles: int = 0
    mean_pairwise_tanimoto: float = 0.0
    diversity_score: float = 0.0  # 1 - mean_pairwise_tanimoto
    min_tanimoto: float = 0.0
    max_tanimoto: float = 0.0


@dataclass
class StateDiversityReport:
    """Per-state diversity analysis."""

    state: str
    intra_diversity: DiversityMetrics = field(default_factory=DiversityMetrics)
    n_state_unique: int = 0      # candidates only in this state
    n_shared: int = 0            # candidates also in other states
    unique_fraction: float = 0.0  # n_state_unique / total


@dataclass
class CrossStateDiversityReport:
    """Cross-state diversity analysis."""

    per_state: list[StateDiversityReport] = field(default_factory=list)
    overlap_matrix: dict[str, int] = field(default_factory=dict)  # "s1|s2" -> count
    total_unique_across_all: int = 0
    total_candidates: int = 0
    global_diversity: DiversityMetrics = field(default_factory=DiversityMetrics)


def compute_diversity(smiles_list: list[str], max_pairs: int = 500) -> DiversityMetrics:
    """Compute diversity metrics for a list of SMILES.

    Samples up to max_pairs for efficiency.
    """
    unique = list(set(smiles_list))
    n = len(unique)

    if n < 2:
        return DiversityMetrics(
            n_candidates=len(smiles_list),
            n_unique_smiles=n,
            mean_pairwise_tanimoto=0.0,
            diversity_score=1.0,
        )

    # Sample pairs
    import random
    rng = random.Random(42)
    pairs = []
    if n * (n - 1) // 2 <= max_pairs:
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((i, j))
    else:
        for _ in range(max_pairs):
            i = rng.randint(0, n - 1)
            j = rng.randint(0, n - 2)
            if j >= i:
                j += 1
            pairs.append((i, j))

    tanimotos = [_tanimoto_ngram(unique[i], unique[j]) for i, j in pairs]

    mean_tan = sum(tanimotos) / len(tanimotos)

    return DiversityMetrics(
        n_candidates=len(smiles_list),
        n_unique_smiles=n,
        mean_pairwise_tanimoto=mean_tan,
        diversity_score=1.0 - mean_tan,
        min_tanimoto=min(tanimotos),
        max_tanimoto=max(tanimotos),
    )


def analyze_cross_state_diversity(
    filtered: MultiStateFilterResult,
) -> CrossStateDiversityReport:
    """Analyze diversity within and across states."""
    # Collect SMILES per state
    state_smiles: dict[str, set[str]] = {}
    all_smiles: list[str] = []

    for lib in filtered.libraries:
        smiles_set = {c.smiles for c in lib.candidates}
        state_smiles[lib.state] = smiles_set
        all_smiles.extend(c.smiles for c in lib.candidates)

    # Global unique count
    global_unique = set(all_smiles)

    # Per-state analysis
    per_state: list[StateDiversityReport] = []
    for lib in filtered.libraries:
        smiles_list = [c.smiles for c in lib.candidates]
        intra = compute_diversity(smiles_list)

        # State-unique: SMILES only in this state
        other_smiles = set()
        for other_lib in filtered.libraries:
            if other_lib.state != lib.state:
                other_smiles.update(c.smiles for c in other_lib.candidates)

        state_only = state_smiles[lib.state] - other_smiles
        shared = state_smiles[lib.state] & other_smiles

        unique_frac = len(state_only) / max(len(state_smiles[lib.state]), 1)

        per_state.append(StateDiversityReport(
            state=lib.state,
            intra_diversity=intra,
            n_state_unique=len(state_only),
            n_shared=len(shared),
            unique_fraction=unique_frac,
        ))

    # Overlap matrix
    overlap: dict[str, int] = {}
    states_list = sorted(state_smiles.keys())
    for i, s1 in enumerate(states_list):
        for j, s2 in enumerate(states_list):
            if i < j:
                shared = len(state_smiles[s1] & state_smiles[s2])
                overlap[f"{s1}|{s2}"] = shared

    # Global diversity
    global_div = compute_diversity(list(global_unique))

    return CrossStateDiversityReport(
        per_state=per_state,
        overlap_matrix=overlap,
        total_unique_across_all=len(global_unique),
        total_candidates=len(all_smiles),
        global_diversity=global_div,
    )
