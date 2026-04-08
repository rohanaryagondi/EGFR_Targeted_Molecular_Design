"""Retrospective time-split validation metrics.

Validates the pipeline by training on pre-cutoff EGFR data and testing
whether it identifies molecules resembling drugs approved after the cutoff.
This is the strongest validation strategy available to a purely computational
project -- it demonstrates real predictive power without wet lab work.

See ``workstreams/13-retrospective-validation.md`` for the full design.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from statebind.chemistry.fingerprints import compute_morgan_similarity

# ── EGFR Drug Approval Database ────────────────────────────────────────────
#
# Canonical SMILES sourced from prepare_mpnn_data.py curated set and
# public ChEMBL/DrugBank records.  Approval years from FDA.

EGFR_DRUG_APPROVALS: dict[str, dict[str, Any]] = {
    "erlotinib": {
        "smiles": "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
        "approved_year": 2004,
        "generation": "1st",
        "state": "DFGin_aCin",
    },
    "gefitinib": {
        "smiles": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
        "approved_year": 2003,
        "generation": "1st",
        "state": "DFGin_aCin",
    },
    "afatinib": {
        "smiles": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1",
        "approved_year": 2013,
        "generation": "2nd",
        "state": "DFGin_aCin",
    },
    "osimertinib": {
        "smiles": (
            "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)"
            "cc1Nc1nccc(-c2cn(C)c3ccccc23)n1"
        ),
        "approved_year": 2015,
        "generation": "3rd",
        "state": "DFGin_aCin",
    },
    "dacomitinib": {
        "smiles": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCCC1",
        "approved_year": 2018,
        "generation": "2nd",
        "state": "DFGin_aCin",
    },
    "lazertinib": {
        "smiles": "C=CC(=O)Nc1cccc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c1OC",
        "approved_year": 2021,
        "generation": "3rd",
        "state": "DFGin_aCin",
    },
    "mobocertinib": {
        "smiles": (
            "C=CC(=O)Nc1cc(Nc2ncc(-c3cccnc3)c(-c3ccsc3)n2)"
            "c(OC)cc1N(C)CCN(C)C"
        ),
        "approved_year": 2021,
        "generation": "3rd",
        "state": "DFGin_aCin",
    },
}


# ── Dataclasses ────────────────────────────────────────────────────────────


@dataclass
class TimeSplitDataset:
    """Training and validation data for one time-split cutoff."""

    cutoff_year: int = 0
    train_smiles: list[str] = field(default_factory=list)
    train_pIC50: list[float] = field(default_factory=list)
    n_train: int = 0
    held_out_drugs: list[dict[str, Any]] = field(default_factory=list)
    n_held_out: int = 0
    pre_cutoff_reference_binders: list[str] = field(default_factory=list)
    source: str = ""


@dataclass
class RetrospectiveResult:
    """Validation result for one cutoff + one pipeline."""

    cutoff_year: int = 0
    pipeline: str = ""  # "static" or "state_aware"
    enrichment_factors: dict[int, float] = field(default_factory=dict)
    max_similarity_to_future: float = 0.0
    mean_similarity_to_future: float = 0.0
    n_candidates: int = 0
    n_future_drugs: int = 0
    future_drug_ranks: dict[str, int | None] = field(default_factory=dict)
    future_drug_similarities: dict[str, float] = field(default_factory=dict)
    novelty_vs_training: float = 0.0
    top_k_hits: dict[int, int] = field(default_factory=dict)

    @property
    def enrichment_factor_10(self) -> float:
        """EF at top 10 (Contract 10 compatibility)."""
        return self.enrichment_factors.get(10, 0.0)

    @property
    def enrichment_factor_50(self) -> float:
        """EF at top 50 (Contract 10 compatibility)."""
        return self.enrichment_factors.get(50, 0.0)


@dataclass
class RetrospectiveComparison:
    """Comparison across cutoffs and pipelines."""

    results: list[RetrospectiveResult] = field(default_factory=list)
    cutoffs: list[int] = field(default_factory=list)
    summary: str = ""


# ── Drug timeline helpers ──────────────────────────────────────────────────


def get_future_drugs(cutoff_year: int) -> list[dict[str, Any]]:
    """Return EGFR drugs approved *after* ``cutoff_year``.

    Each dict has keys: name, smiles, approved_year, generation, state.
    """
    future: list[dict[str, Any]] = []
    for name, info in EGFR_DRUG_APPROVALS.items():
        if info["approved_year"] > cutoff_year:
            future.append({"name": name, **info})
    return future


def get_pre_cutoff_reference_binders(cutoff_year: int) -> list[str]:
    """Return SMILES of reference binders approved on or before ``cutoff_year``.

    These replace ``_REFERENCE_BINDERS`` from ``baselines/scoring.py``
    during retrospective evaluation to prevent temporal leakage.
    """
    return [
        info["smiles"]
        for info in EGFR_DRUG_APPROVALS.values()
        if info["approved_year"] <= cutoff_year
    ]


# ── Enrichment factor ─────────────────────────────────────────────────────


def compute_enrichment_factor(
    candidate_similarities: list[float],
    threshold: float = 0.4,
    top_k: int = 10,
) -> float:
    """Enrichment factor: hits in top-K relative to random expectation.

    EF = (hits_in_top_k / top_k) / (total_hits / total_candidates)

    A value > 1.0 means the pipeline enriches similar-to-future-drug
    molecules in its top-ranked candidates compared to random ranking.

    Args:
        candidate_similarities: Ordered list (by composite score descending)
            of each candidate's max Tanimoto similarity to any future drug.
        threshold: Minimum similarity to count as a "hit".
        top_k: Number of top candidates to consider.

    Returns:
        Enrichment factor. 0.0 if no hits exist anywhere in the list.
    """
    n = len(candidate_similarities)
    if n == 0 or top_k <= 0:
        return 0.0

    effective_k = min(top_k, n)
    total_hits = sum(1 for s in candidate_similarities if s >= threshold)

    if total_hits == 0:
        return 0.0

    hits_in_top_k = sum(
        1 for s in candidate_similarities[:effective_k] if s >= threshold
    )

    hit_rate_top_k = hits_in_top_k / effective_k
    hit_rate_overall = total_hits / n

    return round(hit_rate_top_k / hit_rate_overall, 4)


# ── Similarity computation ─────────────────────────────────────────────────


def compute_candidate_future_similarities(
    candidate_smiles: list[str],
    future_drug_smiles: list[str],
) -> list[float]:
    """Max Tanimoto similarity of each candidate to any future drug.

    Uses Morgan/ECFP4 fingerprints via ``chemistry.fingerprints``.

    Args:
        candidate_smiles: List of candidate SMILES (ordered by score).
        future_drug_smiles: List of future drug SMILES.

    Returns:
        List parallel to ``candidate_smiles`` with max similarities.
    """
    if not future_drug_smiles:
        return [0.0] * len(candidate_smiles)

    similarities: list[float] = []
    for cand in candidate_smiles:
        max_sim = max(
            compute_morgan_similarity(cand, drug)
            for drug in future_drug_smiles
        )
        similarities.append(round(max_sim, 4))
    return similarities


def compute_future_drug_ranks(
    candidate_smiles: list[str],
    future_drugs: list[dict[str, Any]],
    threshold: float = 0.4,
) -> dict[str, int | None]:
    """For each future drug, find rank of first candidate with sim >= threshold.

    Candidates must be ordered by composite score descending (rank 1 = best).

    Args:
        candidate_smiles: Ordered candidate SMILES.
        future_drugs: List of dicts with at least "name" and "smiles" keys.
        threshold: Minimum Tanimoto similarity for a "match".

    Returns:
        Dict mapping drug name to 1-based rank, or None if no match found.
    """
    ranks: dict[str, int | None] = {}
    for drug in future_drugs:
        drug_name = drug["name"]
        drug_smiles = drug["smiles"]
        found_rank: int | None = None
        for rank, cand in enumerate(candidate_smiles, start=1):
            sim = compute_morgan_similarity(cand, drug_smiles)
            if sim >= threshold:
                found_rank = rank
                break
        ranks[drug_name] = found_rank
    return ranks


# ── Novelty computation ────────────────────────────────────────────────────


def compute_novelty(
    candidate_smiles: list[str],
    training_smiles: set[str],
) -> float:
    """Fraction of candidates not present in the training set.

    Args:
        candidate_smiles: Generated candidate SMILES.
        training_smiles: Set of SMILES from the pre-cutoff training data.

    Returns:
        Novelty fraction in [0.0, 1.0].
    """
    if not candidate_smiles:
        return 0.0
    novel = sum(1 for s in candidate_smiles if s not in training_smiles)
    return round(novel / len(candidate_smiles), 4)


# ── Leakage verification ──────────────────────────────────────────────────


def verify_no_leakage(
    training_smiles: set[str],
    future_drugs: list[dict[str, Any]],
) -> bool:
    """Assert no future drug SMILES appears in the training set.

    Args:
        training_smiles: Set of canonical SMILES in the training data.
        future_drugs: List of future drug dicts with "smiles" key.

    Returns:
        True if no leakage detected.

    Raises:
        ValueError: If any future drug is found in the training set.
    """
    for drug in future_drugs:
        if drug["smiles"] in training_smiles:
            msg = (
                f"Temporal leakage detected: {drug['name']} "
                f"(approved {drug.get('approved_year', '?')}) "
                f"found in training data"
            )
            raise ValueError(msg)
    return True


# ── Orchestrator ───────────────────────────────────────────────────────────


def compute_retrospective_metrics(
    candidates: list[dict[str, Any]],
    future_drugs: list[dict[str, Any]],
    training_smiles: set[str],
    pipeline: str = "static",
    cutoff_year: int = 2010,
    k_values: list[int] | None = None,
    threshold: float = 0.4,
) -> RetrospectiveResult:
    """Compute all retrospective validation metrics for one pipeline run.

    Args:
        candidates: Sorted by composite_score descending.  Each dict must
            have "smiles" and "composite_score" keys.
        future_drugs: Held-out drugs with "name" and "smiles" keys.
        training_smiles: Set of pre-cutoff SMILES for novelty computation.
        pipeline: "static" or "state_aware".
        cutoff_year: The time-split cutoff year.
        k_values: List of K values for enrichment (default [10, 50, 100]).
        threshold: Tanimoto similarity threshold for "hit".

    Returns:
        Populated ``RetrospectiveResult``.
    """
    if k_values is None:
        k_values = [10, 50, 100]

    cand_smiles = [c["smiles"] for c in candidates]
    future_smiles = [d["smiles"] for d in future_drugs]

    # Similarity of each candidate to future drugs
    sims = compute_candidate_future_similarities(cand_smiles, future_smiles)

    # Enrichment factors at each K
    enrichment_factors: dict[int, float] = {}
    top_k_hits: dict[int, int] = {}
    for k in k_values:
        enrichment_factors[k] = compute_enrichment_factor(sims, threshold, k)
        effective_k = min(k, len(sims))
        top_k_hits[k] = sum(
            1 for s in sims[:effective_k] if s >= threshold
        )

    # Per-drug similarities (max sim from any candidate to each drug)
    drug_sims: dict[str, float] = {}
    for drug in future_drugs:
        best = 0.0
        for cs in cand_smiles:
            s = compute_morgan_similarity(cs, drug["smiles"])
            if s > best:
                best = s
        drug_sims[drug["name"]] = round(best, 4)

    # Future drug ranks
    drug_ranks = compute_future_drug_ranks(cand_smiles, future_drugs, threshold)

    # Novelty
    novelty = compute_novelty(cand_smiles, training_smiles)

    # Aggregate similarity stats
    max_sim = round(max(sims), 4) if sims else 0.0
    mean_sim = round(sum(sims) / len(sims), 4) if sims else 0.0

    return RetrospectiveResult(
        cutoff_year=cutoff_year,
        pipeline=pipeline,
        enrichment_factors=enrichment_factors,
        max_similarity_to_future=max_sim,
        mean_similarity_to_future=mean_sim,
        n_candidates=len(candidates),
        n_future_drugs=len(future_drugs),
        future_drug_ranks=drug_ranks,
        future_drug_similarities=drug_sims,
        novelty_vs_training=novelty,
        top_k_hits=top_k_hits,
    )


# ── Summary generation ─────────────────────────────────────────────────────


def generate_retrospective_summary(
    comparison: RetrospectiveComparison,
) -> str:
    """Generate a natural-language summary of retrospective findings.

    Reports enrichment factors, pipeline comparison at each cutoff,
    and which future drugs were "found" (had a close analog in top-K).
    """
    lines: list[str] = [
        "Retrospective Time-Split Validation Summary",
        "=" * 50,
        "",
    ]

    for cutoff in comparison.cutoffs:
        cutoff_results = [
            r for r in comparison.results if r.cutoff_year == cutoff
        ]
        lines.append(f"Cutoff year: {cutoff}")
        lines.append("-" * 30)

        for r in cutoff_results:
            ef10 = r.enrichment_factor_10
            ef50 = r.enrichment_factor_50
            found = sum(1 for rank in r.future_drug_ranks.values() if rank is not None)
            lines.append(
                f"  {r.pipeline:12s}  EF@10={ef10:.2f}  EF@50={ef50:.2f}  "
                f"max_sim={r.max_similarity_to_future:.3f}  "
                f"novelty={r.novelty_vs_training:.2f}  "
                f"drugs_found={found}/{r.n_future_drugs}"
            )

            # List found drugs
            for drug_name, rank in r.future_drug_ranks.items():
                sim = r.future_drug_similarities.get(drug_name, 0.0)
                if rank is not None:
                    lines.append(
                        f"    -> {drug_name}: rank {rank}, sim {sim:.3f}"
                    )
                else:
                    lines.append(
                        f"    -> {drug_name}: not found (best sim {sim:.3f})"
                    )

        lines.append("")

    # Overall assessment
    static_results = [r for r in comparison.results if r.pipeline == "static"]
    sa_results = [r for r in comparison.results if r.pipeline == "state_aware"]

    if static_results and sa_results:
        static_ef = sum(r.enrichment_factor_10 for r in static_results) / len(
            static_results
        )
        sa_ef = sum(r.enrichment_factor_10 for r in sa_results) / len(
            sa_results
        )
        if sa_ef > static_ef:
            lines.append(
                f"State-aware pipeline shows higher mean EF@10 "
                f"({sa_ef:.2f} vs {static_ef:.2f})."
            )
        elif static_ef > sa_ef:
            lines.append(
                f"Static pipeline shows higher mean EF@10 "
                f"({static_ef:.2f} vs {sa_ef:.2f})."
            )
        else:
            lines.append(f"Both pipelines show equal mean EF@10 ({sa_ef:.2f}).")

    return "\n".join(lines)


def to_serializable(obj: RetrospectiveResult | RetrospectiveComparison) -> dict[str, Any]:
    """Convert a retrospective dataclass to a JSON-serializable dict.

    Converts integer dict keys to strings for JSON compatibility.
    """
    d = asdict(obj)

    def _fix_int_keys(data: Any) -> Any:
        if isinstance(data, dict):
            return {str(k): _fix_int_keys(v) for k, v in data.items()}
        if isinstance(data, list):
            return [_fix_int_keys(item) for item in data]
        return data

    return _fix_int_keys(d)
