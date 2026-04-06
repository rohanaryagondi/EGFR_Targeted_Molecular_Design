"""Chemistry filtering with state-aware rules.

Extends baseline filtering with pocket-aware constraints:
- Active state: standard Lipinski-like rules (type-I inhibitor range)
- DFG-out states: relaxed MW limits (type-II inhibitors are larger)
- All states: validity, ring count, heavy atom count checks
"""

from __future__ import annotations

from datetime import datetime, timezone

from statebind.baselines.filtering import (
    _is_valid_smiles,
    compute_properties,
)
from statebind.baselines.models import PropertyFilter
from statebind.generation.models import (
    FilteredStateLibrary,
    MultiStateFilterResult,
    MultiStateGenerationResult,
    StateConditionedCandidate,
    StateConditionedLibrary,
)

# ── State-specific filter sets ──────────────────────────────────────────

def _type1_filters() -> list[PropertyFilter]:
    """Filters for type-I inhibitor candidates (active/Src-like states)."""
    return [
        PropertyFilter(property_name="estimated_mw", min_value=200, max_value=600),
        PropertyFilter(property_name="estimated_hba", min_value=1, max_value=10),
        PropertyFilter(property_name="estimated_hbd", min_value=0, max_value=5),
        PropertyFilter(property_name="n_heavy_atoms", min_value=15, max_value=50),
        PropertyFilter(property_name="n_rings", min_value=1, max_value=8),
    ]


def _type2_filters() -> list[PropertyFilter]:
    """Relaxed filters for type-II candidates (DFG-out states).

    Type-II inhibitors (e.g., imatinib, sorafenib) are typically larger
    than type-I because they extend into the back pocket.
    """
    return [
        PropertyFilter(property_name="estimated_mw", min_value=250, max_value=800),
        PropertyFilter(property_name="estimated_hba", min_value=1, max_value=12),
        PropertyFilter(property_name="estimated_hbd", min_value=0, max_value=6),
        PropertyFilter(property_name="n_heavy_atoms", min_value=18, max_value=60),
        PropertyFilter(property_name="n_rings", min_value=2, max_value=10),
    ]


def get_filters_for_state(state: str) -> list[PropertyFilter]:
    """Return appropriate filters based on conformational state."""
    if "DFGout" in state:
        return _type2_filters()
    return _type1_filters()


def filter_state_library(
    library: StateConditionedLibrary,
    filters: list[PropertyFilter] | None = None,
) -> FilteredStateLibrary:
    """Filter candidates for a single state.

    Args:
        library: State-conditioned candidate library.
        filters: Optional custom filters. If None, uses state-appropriate defaults.

    Returns:
        FilteredStateLibrary with passed candidates and statistics.
    """
    if filters is None:
        filters = get_filters_for_state(library.state)

    passed: list[StateConditionedCandidate] = []
    all_props: dict[str, list[float]] = {}

    for candidate in library.candidates:
        # Compute properties
        props = compute_properties(candidate.smiles)

        # Check validity
        if not _is_valid_smiles(candidate.smiles):
            continue

        # Check filters
        pass_all = True
        for f in filters:
            val = props.get(f.property_name)
            if val is None:
                pass_all = False
                break
            if f.min_value is not None and val < f.min_value:
                pass_all = False
                break
            if f.max_value is not None and val > f.max_value:
                pass_all = False
                break

        if pass_all:
            passed.append(candidate)
            for pname, pval in props.items():
                if pval is not None:
                    all_props.setdefault(pname, []).append(pval)

    # Compute property statistics
    prop_stats: dict[str, dict[str, float]] = {}
    for pname, vals in all_props.items():
        if vals:
            prop_stats[pname] = {
                "mean": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
                "n": float(len(vals)),
            }

    n_input = library.n_candidates
    n_passed = len(passed)
    pass_rate = n_passed / max(n_input, 1)

    return FilteredStateLibrary(
        state=library.state,
        n_input=n_input,
        n_passed=n_passed,
        n_failed=n_input - n_passed,
        pass_rate=pass_rate,
        candidates=passed,
        property_stats=prop_stats,
    )


def filter_all_states(
    generation: MultiStateGenerationResult,
) -> MultiStateFilterResult:
    """Filter candidates across all states.

    Each state gets appropriate filters (type-I vs type-II).
    """
    libraries: list[FilteredStateLibrary] = []
    total_input = 0
    total_passed = 0

    for lib in generation.libraries:
        filtered = filter_state_library(lib)
        libraries.append(filtered)
        total_input += filtered.n_input
        total_passed += filtered.n_passed

    now = datetime.now(timezone.utc).isoformat()

    return MultiStateFilterResult(
        states=generation.states,
        libraries=libraries,
        total_input=total_input,
        total_passed=total_passed,
        overall_pass_rate=total_passed / max(total_input, 1),
        generated_at=now,
    )
