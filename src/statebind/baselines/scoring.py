"""Scoring and ranking for the static baseline.

Scoring components:
1. Reference similarity: Tanimoto-like similarity to known binders
2. Property score: how drug-like the candidate is
3. Docking score: STUB — placeholder for future docking integration

The composite score is a weighted sum. Weights are configurable.

IMPORTANT: This scoring pipeline does NOT use conformational state information.
It treats the target as a single static structure. This is the deliberate
limitation that makes this a baseline.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from statebind.baselines.models import (
    FilteredLibrary,
    RankedCandidates,
    ScoreComponent,
    ScoredCandidate,
)


# ── SMILES fingerprint (simple character n-gram approach) ───────────────


def _smiles_ngrams(smiles: str, n: int = 3) -> set[str]:
    """Extract character n-grams from SMILES as a simple fingerprint.

    This is NOT a proper molecular fingerprint (ECFP, Morgan, etc.).
    It is a crude proxy that captures some structural similarity.
    With RDKit, this should be replaced by Morgan/ECFP4 fingerprints.
    """
    if len(smiles) < n:
        return {smiles}
    return {smiles[i:i+n] for i in range(len(smiles) - n + 1)}


def _tanimoto_ngram(smiles_a: str, smiles_b: str, n: int = 3) -> float:
    """Compute Tanimoto similarity between SMILES n-gram sets.

    Returns value in [0, 1]. Higher = more similar.
    """
    ngrams_a = _smiles_ngrams(smiles_a, n)
    ngrams_b = _smiles_ngrams(smiles_b, n)
    if not ngrams_a or not ngrams_b:
        return 0.0
    intersection = len(ngrams_a & ngrams_b)
    union = len(ngrams_a | ngrams_b)
    return intersection / union if union > 0 else 0.0


# ── Reference SMILES for similarity scoring ─────────────────────────────

_REFERENCE_BINDERS = [
    # Erlotinib
    "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
    # Gefitinib
    "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
    # Osimertinib
    "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
]


def _has_rdkit() -> bool:
    """Check if RDKit is available via the chemistry module."""
    try:
        from statebind.chemistry.fingerprints import HAS_RDKIT
        return HAS_RDKIT
    except ImportError:
        return False


def _score_reference_similarity(smiles: str) -> float:
    """Score candidate by max Tanimoto similarity to reference binders.

    Uses Morgan/ECFP4 fingerprints when RDKit is available; falls back to
    SMILES character 3-gram Tanimoto otherwise.

    Returns value in [0, 1]. Higher = more similar to known binders.
    """
    if not smiles:
        return 0.0
    try:
        from statebind.chemistry.fingerprints import compute_max_reference_similarity
        return compute_max_reference_similarity(smiles, _REFERENCE_BINDERS)
    except ImportError:
        pass
    # Fallback: n-gram Tanimoto
    similarities = [_tanimoto_ngram(smiles, ref) for ref in _REFERENCE_BINDERS]
    return max(similarities) if similarities else 0.0


# ── Property score ──────────────────────────────────────────────────────


def _score_druglikeness(properties: dict[str, float | None]) -> float:
    """Score how drug-like a candidate is based on estimated properties.

    Simple linear scoring:
    - MW in [300, 500] → 1.0, penalty outside
    - HBA in [3, 7] → 1.0
    - HBD in [1, 3] → 1.0
    - Rings in [2, 5] → 1.0

    Returns value in [0, 1]. Higher = more drug-like.
    """
    score = 0.0
    n_components = 0

    mw = properties.get("estimated_mw")
    if mw is not None:
        if 300 <= mw <= 500:
            score += 1.0
        elif 200 <= mw <= 600:
            score += 0.5
        n_components += 1

    hba = properties.get("estimated_hba")
    if hba is not None:
        if 3 <= hba <= 7:
            score += 1.0
        elif 1 <= hba <= 10:
            score += 0.5
        n_components += 1

    hbd = properties.get("estimated_hbd")
    if hbd is not None:
        if 1 <= hbd <= 3:
            score += 1.0
        elif 0 <= hbd <= 5:
            score += 0.5
        n_components += 1

    rings = properties.get("n_rings")
    if rings is not None:
        if 2 <= rings <= 5:
            score += 1.0
        elif 1 <= rings <= 7:
            score += 0.5
        n_components += 1

    return score / n_components if n_components > 0 else 0.0


def _score_druglikeness_enhanced(smiles: str) -> float:
    """Enhanced drug-likeness: QED(0.5) + Lipinski(0.25) + SA(0.25).

    Requires RDKit. Returns value in [0, 1]. Higher = more drug-like.

    Components:
    - QED: Bickerton et al. quantitative estimate of drug-likeness [0, 1]
    - Lipinski: (4 - n_violations) / 4 based on Rule-of-5 [0, 1]
    - SA: normalized synthetic accessibility (10 - SA) / 9 [0, 1]
    """
    from rdkit import Chem
    from rdkit.Chem import QED as _QED

    from statebind.chemistry.descriptors import compute_exact_properties
    from statebind.chemistry.sa_score import compute_sa_score

    if not smiles:
        return 0.0
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or mol.GetNumAtoms() == 0:
        return 0.0

    # QED: comprehensive drug-likeness [0, 1]
    qed_score = _QED.qed(mol)

    # Lipinski Rule-of-5: count violations, normalize to [0, 1]
    props = compute_exact_properties(smiles)
    violations = 0
    mw = props.get("estimated_mw")
    if mw is not None and mw > 500:
        violations += 1
    hba = props.get("estimated_hba")
    if hba is not None and hba > 10:
        violations += 1
    hbd = props.get("estimated_hbd")
    if hbd is not None and hbd > 5:
        violations += 1
    logp = props.get("logp")
    if logp is not None and logp > 5:
        violations += 1
    lipinski_score = (4 - violations) / 4

    # SA: [1, 10] → [0, 1] where lower SA = better
    sa_raw = compute_sa_score(smiles)
    sa_normalized = (10.0 - sa_raw) / 9.0

    return round(0.5 * qed_score + 0.25 * lipinski_score + 0.25 * sa_normalized, 4)


# ── Docking score stub ──────────────────────────────────────────────────


def _score_docking_stub(smiles: str, pdb_id: str) -> float:
    """STUB: Placeholder docking score.

    Returns a constant score. This MUST be replaced with actual docking
    (AutoDock Vina, GNINA, etc.) in a future phase for the benchmark
    to have real discriminative power.

    Current implementation: returns 0.5 for all candidates.

    TODO: Replace with:
    - AutoDock Vina (open source, well-validated)
    - GNINA (ML-based, faster)
    - Smina (Vina fork with better scoring)
    """
    return 0.5


# ── Composite scoring ──────────────────────────────────────────────────


def score_candidates(
    filtered: FilteredLibrary,
    target_pdb_id: str = "1m17",
    weights: dict[str, float] | None = None,
) -> RankedCandidates:
    """Score and rank filtered candidates.

    Scoring components:
    1. reference_similarity (weight=0.4): Tanimoto to known binders
    2. druglikeness (weight=0.3): property-based drug-likeness
    3. docking_proxy (weight=0.3): STUB — placeholder

    Args:
        filtered: Filtered candidate library.
        target_pdb_id: PDB ID used for docking stub.
        weights: Optional weight overrides. Keys: similarity, druglikeness, docking.

    Returns:
        RankedCandidates sorted by composite score (descending).
    """
    if weights is None:
        weights = {
            "reference_similarity": 0.4,
            "druglikeness": 0.3,
            "docking_proxy": 0.3,
        }

    _rdkit = _has_rdkit()
    _sim_method = (
        "Morgan/ECFP4 Tanimoto (radius=2, 2048 bits) vs erlotinib/gefitinib/osimertinib"
        if _rdkit else "SMILES 3-gram Tanimoto vs erlotinib/gefitinib/osimertinib"
    )
    _drug_method = (
        "QED(0.5) + Lipinski(0.25) + SA_score(0.25) via RDKit"
        if _rdkit else "Property-based linear scoring (MW, HBA, HBD, rings)"
    )

    scored = []

    for result in filtered.results:
        if not result.passed:
            continue

        # Compute score components
        sim_score = _score_reference_similarity(result.smiles)
        if _rdkit:
            drug_score = _score_druglikeness_enhanced(result.smiles)
        else:
            drug_score = _score_druglikeness(result.properties)
        dock_score = _score_docking_stub(result.smiles, target_pdb_id)

        components = [
            ScoreComponent(
                name="reference_similarity",
                value=sim_score,
                weight=weights.get("reference_similarity", 0.4),
                method=_sim_method,
                is_stub=False,
            ),
            ScoreComponent(
                name="druglikeness",
                value=drug_score,
                weight=weights.get("druglikeness", 0.3),
                method=_drug_method,
                is_stub=False,
            ),
            ScoreComponent(
                name="docking_proxy",
                value=dock_score,
                weight=weights.get("docking_proxy", 0.3),
                method="STUB: constant 0.5 — replace with Vina/GNINA",
                is_stub=True,
            ),
        ]

        composite = sum(c.value * c.weight for c in components)

        scored.append(ScoredCandidate(
            candidate_id=result.candidate_id,
            smiles=result.smiles,
            scores=components,
            composite_score=round(composite, 4),
        ))

    # Sort by composite score descending
    scored.sort(key=lambda x: x.composite_score, reverse=True)

    # Assign ranks
    for i, candidate in enumerate(scored):
        candidate.rank = i + 1

    now = datetime.now(timezone.utc).isoformat()

    return RankedCandidates(
        run_id=f"static_baseline_{target_pdb_id}_{now[:10]}",
        pipeline="static_baseline",
        target_pdb_id=target_pdb_id,
        pocket_id=f"{target_pdb_id}_A_ATP",
        scoring_method=(
            f"Weighted sum: reference_similarity(0.4, {'Morgan/ECFP4' if _rdkit else 'n-gram'}) + "
            f"druglikeness(0.3, {'QED+Lipinski+SA' if _rdkit else 'heuristic'}) + "
            f"docking_proxy(0.3). NOTE: docking_proxy is a STUB returning constant 0.5."
        ),
        candidates=scored,
        generated_at=now,
        notes=(
            "Static baseline scoring. Uses ONE structure (1M17), ONE pocket definition, "
            "and NO conformational state information. The docking component is a placeholder. "
            "This is the baseline that state-aware design must beat."
        ),
    )
