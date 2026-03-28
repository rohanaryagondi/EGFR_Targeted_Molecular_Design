"""Unified scoring: same function for both pipelines.

Scoring components (applied identically to static and state-aware candidates):
1. reference_similarity — Tanimoto-like similarity to known EGFR binders
2. druglikeness — property-based drug-likeness score
3. docking_proxy — MPNN affinity, docking proxy MLP, or stub (cascading fallback)
4. state_specificity — bonus for candidates unique to their target state
   (always 0 for static baseline; 0–1 for state-aware)

Using the SAME scoring function for both pipelines is critical for a fair
comparison. The only dimension where state-aware candidates can gain an
advantage is state_specificity — everything else is identical.
"""

from __future__ import annotations

from datetime import datetime, timezone

from statebind.baselines.scoring import (
    _has_rdkit,
    _score_druglikeness,
    _score_druglikeness_enhanced,
    _score_reference_similarity,
    _score_docking_stub,
    _tanimoto_ngram,
)


def _score_docking(smiles: str, pdb_id: str) -> tuple[float, bool, str]:
    """Score docking via learned models with stub fallback.

    Cascading fallback:
    1. MPNN affinity predictor (WS08) — if trained and torch available
    2. DockingProxy MLP (WS04) — if trained and RDKit available
    3. Constant 0.5 stub — always available

    Returns:
        (score, is_stub, method_string)
    """
    # Priority 1: MPNN affinity predictor
    try:
        from statebind.ml.affinity_predictor import _model_loaded, predict_affinity

        score = predict_affinity(smiles)
        if _model_loaded():
            return (
                score,
                False,
                "MPNN binding affinity predictor (pIC50, sigmoid-normalized)",
            )
    except (ImportError, Exception):
        pass

    # Priority 2: DockingProxy MLP (WS04)
    try:
        from statebind.chemistry.docking_proxy import get_default_proxy

        proxy = get_default_proxy()
        if proxy.fitted:
            score = proxy.predict(smiles)
            return (
                score,
                False,
                "Learned EGFR binding proxy (MLP on Morgan+descriptors)",
            )
    except (ImportError, Exception):
        pass

    # Priority 3: Stub
    return _score_docking_stub(smiles, pdb_id), True, "STUB: constant 0.5"
from statebind.baselines.filtering import compute_properties
from statebind.baselines.models import FilteredLibrary
from statebind.generation.models import (
    FilteredStateLibrary,
    MultiStateFilterResult,
)
from statebind.ranking.models import (
    MergedRanking,
    PipelineLabel,
    RankedPool,
    UnifiedScoreComponent,
    UnifiedScoredCandidate,
)


DEFAULT_WEIGHTS = {
    "reference_similarity": 0.35,
    "druglikeness": 0.30,
    "docking_proxy": 0.20,
    "state_specificity": 0.15,
}

SCORING_METHOD = (
    "Unified weighted sum: reference_similarity(0.35) + druglikeness(0.30) "
    "+ docking_proxy(0.20) + state_specificity(0.15). "
    "Use _get_scoring_method() for runtime-accurate version."
)


def _get_scoring_method() -> str:
    """Return scoring method string reflecting active backend.

    Checks MPNN, docking proxy, and RDKit availability at runtime.
    """
    # Check docking backend: MPNN > proxy > stub
    try:
        from statebind.ml.affinity_predictor import _model_loaded

        if _model_loaded():
            dock_desc = "MPNN_affinity(pIC50)"
        else:
            raise ImportError  # fall through to proxy check
    except (ImportError, Exception):
        try:
            from statebind.chemistry.docking_proxy import get_default_proxy
            proxy = get_default_proxy()
            dock_desc = "learned_proxy" if proxy.fitted else "STUB(0.5)"
        except (ImportError, Exception):
            dock_desc = "STUB(0.5)"

    try:
        from statebind.chemistry.fingerprints import HAS_RDKIT
        if HAS_RDKIT:
            return (
                "Unified weighted sum: reference_similarity(0.35, Morgan/ECFP4) + "
                f"druglikeness(0.30, QED+Lipinski+SA) + docking_proxy(0.20, {dock_desc}) + "
                "state_specificity(0.15). "
                "state_specificity is 0 for static baseline candidates."
            )
    except ImportError:
        pass
    return (
        "Unified weighted sum: reference_similarity(0.35) + druglikeness(0.30) "
        f"+ docking_proxy(0.20, {dock_desc}) + state_specificity(0.15). "
        "state_specificity is 0 for static baseline candidates."
    )


def _compute_state_specificity(
    smiles: str,
    target_state: str,
    state_smiles_map: dict[str, set[str]],
) -> float:
    """Reward candidates unique to their target state.

    Uses geometric decay (1/2^(n-1)) because a candidate appearing in 2
    states is substantially less specific than one in 1 state, while the
    difference between 3 and 4 states is negligible. Linear decay would
    overweight moderately-shared candidates.

    Returns:
        1.0 if candidate appears only in target_state
        0.5 if candidate appears in 2 states
        0.25 if candidate appears in 3 states
        0.0 if candidate appears in all 4 states or has no target state
    """
    if not target_state or not state_smiles_map:
        return 0.0

    n_states_present = sum(
        1 for ss in state_smiles_map.values() if smiles in ss
    )

    if n_states_present <= 1:
        return 1.0
    elif n_states_present == 2:
        return 0.5
    elif n_states_present == 3:
        return 0.25
    return 0.0


def _validate_weights(weights: dict[str, float]) -> None:
    """Verify scoring weights sum to 1.0 and all required keys present."""
    required = {"reference_similarity", "druglikeness", "docking_proxy", "state_specificity"}
    missing = required - set(weights.keys())
    if missing:
        raise ValueError(f"Missing scoring weight keys: {missing}")
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-4:
        raise ValueError(f"Scoring weights must sum to 1.0, got {total:.4f}")


def score_unified(
    smiles: str,
    target_state: str,
    pipeline: PipelineLabel,
    state_smiles_map: dict[str, set[str]],
    weights: dict[str, float] | None = None,
) -> tuple[list[UnifiedScoreComponent], float]:
    """Score a single candidate under the unified scheme.

    Returns:
        (components, composite_score)
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    _validate_weights(weights)

    props = compute_properties(smiles)
    sim = _score_reference_similarity(smiles)
    _rdkit = _has_rdkit()
    if _rdkit:
        drug = _score_druglikeness_enhanced(smiles)
    else:
        drug = _score_druglikeness(props)
    dock, dock_is_stub, dock_method = _score_docking(smiles, "unified")
    spec = _compute_state_specificity(smiles, target_state, state_smiles_map)

    _sim_method = (
        "Morgan/ECFP4 Tanimoto (radius=2, 2048 bits) vs erlotinib/gefitinib/osimertinib"
        if _rdkit else "SMILES 3-gram Tanimoto vs erlotinib/gefitinib/osimertinib"
    )
    _drug_method = (
        "QED(0.5) + Lipinski(0.25) + SA_score(0.25) via RDKit"
        if _rdkit else "Property-based linear scoring (MW, HBA, HBD, rings)"
    )

    components = [
        UnifiedScoreComponent(
            name="reference_similarity",
            value=round(sim, 4),
            weight=weights["reference_similarity"],
            method=_sim_method,
        ),
        UnifiedScoreComponent(
            name="druglikeness",
            value=round(drug, 4),
            weight=weights["druglikeness"],
            method=_drug_method,
        ),
        UnifiedScoreComponent(
            name="docking_proxy",
            value=round(dock, 4),
            weight=weights["docking_proxy"],
            method=dock_method,
            is_stub=dock_is_stub,
        ),
        UnifiedScoreComponent(
            name="state_specificity",
            value=round(spec, 4),
            weight=weights["state_specificity"],
            method="Fraction of states candidate is unique to (0 for static)",
        ),
    ]

    composite = sum(c.value * c.weight for c in components)
    return components, round(composite, 4)


def rank_static_baseline(
    filtered: FilteredLibrary,
    weights: dict[str, float] | None = None,
) -> RankedPool:
    """Score and rank static baseline candidates under unified scoring."""
    scored: list[UnifiedScoredCandidate] = []
    empty_map: dict[str, set[str]] = {}

    for result in filtered.results:
        if not result.passed:
            continue
        components, composite = score_unified(
            result.smiles, "", PipelineLabel.STATIC, empty_map, weights,
        )
        scored.append(UnifiedScoredCandidate(
            candidate_id=result.candidate_id,
            smiles=result.smiles,
            pipeline=PipelineLabel.STATIC,
            strategy="static",
            scores=components,
            composite_score=composite,
        ))

    scored.sort(key=lambda x: x.composite_score, reverse=True)
    for i, c in enumerate(scored):
        c.rank_in_pipeline = i + 1

    now = datetime.now(timezone.utc).isoformat()
    return RankedPool(
        pipeline=PipelineLabel.STATIC,
        scoring_method=_get_scoring_method(),
        candidates=scored,
        generated_at=now,
        notes="Static baseline scored under unified scheme. state_specificity=0 for all.",
    )


def rank_state_aware(
    filtered: MultiStateFilterResult,
    weights: dict[str, float] | None = None,
) -> RankedPool:
    """Score and rank state-conditioned candidates under unified scoring."""
    # Build state→SMILES map for specificity scoring
    state_smiles_map: dict[str, set[str]] = {}
    for lib in filtered.libraries:
        state_smiles_map[lib.state] = {c.smiles for c in lib.candidates}

    scored: list[UnifiedScoredCandidate] = []
    seen_smiles: set[str] = set()

    for lib in filtered.libraries:
        for candidate in lib.candidates:
            # Deduplicate across states — keep first occurrence
            if candidate.smiles in seen_smiles:
                continue
            seen_smiles.add(candidate.smiles)

            components, composite = score_unified(
                candidate.smiles,
                candidate.target_state,
                PipelineLabel.STATE_AWARE,
                state_smiles_map,
                weights,
            )
            scored.append(UnifiedScoredCandidate(
                candidate_id=candidate.candidate_id,
                smiles=candidate.smiles,
                pipeline=PipelineLabel.STATE_AWARE,
                target_state=candidate.target_state,
                strategy=candidate.strategy.value if hasattr(candidate.strategy, "value") else str(candidate.strategy),
                scores=components,
                composite_score=composite,
            ))

    scored.sort(key=lambda x: x.composite_score, reverse=True)
    for i, c in enumerate(scored):
        c.rank_in_pipeline = i + 1

    now = datetime.now(timezone.utc).isoformat()
    return RankedPool(
        pipeline=PipelineLabel.STATE_AWARE,
        scoring_method=_get_scoring_method(),
        candidates=scored,
        generated_at=now,
        notes="State-conditioned candidates scored under unified scheme.",
    )


def merge_rankings(
    static_pool: RankedPool,
    state_aware_pool: RankedPool,
) -> MergedRanking:
    """Merge both pools into a single global ranking.

    Deduplicates by SMILES — if same SMILES appears in both pipelines,
    keeps the higher-scoring version and labels it with its origin pipeline.
    """
    best_by_smiles: dict[str, UnifiedScoredCandidate] = {}

    for c in static_pool.candidates:
        if c.smiles not in best_by_smiles or c.composite_score > best_by_smiles[c.smiles].composite_score:
            best_by_smiles[c.smiles] = c.model_copy()

    for c in state_aware_pool.candidates:
        if c.smiles not in best_by_smiles or c.composite_score > best_by_smiles[c.smiles].composite_score:
            best_by_smiles[c.smiles] = c.model_copy()

    merged = sorted(best_by_smiles.values(), key=lambda x: x.composite_score, reverse=True)
    for i, c in enumerate(merged):
        c.global_rank = i + 1

    now = datetime.now(timezone.utc).isoformat()
    return MergedRanking(
        static_pool=static_pool,
        state_aware_pool=state_aware_pool,
        merged=merged,
        generated_at=now,
        notes=(
            f"Merged {static_pool.n_ranked} static + {state_aware_pool.n_ranked} "
            f"state-aware → {len(merged)} unique SMILES."
        ),
    )
