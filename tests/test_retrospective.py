"""Tests for Workstream 13: Retrospective Time-Split Validation.

Covers:
- Time-split data integrity and no-leakage guarantees
- Enrichment factor computation edge cases
- Similarity and novelty metric correctness
- Dataclass serialization and integration
"""

from __future__ import annotations

import json

import pytest

from statebind.evaluation.retrospective import (
    EGFR_DRUG_APPROVALS,
    RetrospectiveComparison,
    RetrospectiveResult,
    TimeSplitDataset,
    compute_candidate_future_similarities,
    compute_enrichment_factor,
    compute_novelty,
    compute_retrospective_metrics,
    generate_retrospective_summary,
    get_future_drugs,
    get_pre_cutoff_reference_binders,
    to_serializable,
    verify_no_leakage,
)

# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def erlotinib_smiles() -> str:
    return EGFR_DRUG_APPROVALS["erlotinib"]["smiles"]


@pytest.fixture()
def osimertinib_smiles() -> str:
    return EGFR_DRUG_APPROVALS["osimertinib"]["smiles"]


@pytest.fixture()
def future_drugs_2010() -> list[dict]:
    return get_future_drugs(2010)


@pytest.fixture()
def future_drugs_2015() -> list[dict]:
    return get_future_drugs(2015)


# ═══════════════════════════════════════════════════════════════════════════
# Time-split integrity tests
# ═══════════════════════════════════════════════════════════════════════════


class TestTimeSplitIntegrity:
    """Verify no temporal leakage in the time-split design."""

    def test_no_future_leakage_2010(self, future_drugs_2010: list[dict]) -> None:
        """No post-2010 approved drugs should pass the leakage check
        when present in training data -- verify_no_leakage catches them."""
        # Build a training set of pre-2010 drugs only
        pre_2010_smiles = {
            info["smiles"]
            for info in EGFR_DRUG_APPROVALS.values()
            if info["approved_year"] <= 2010
        }
        # Should pass -- no future drugs in this set
        assert verify_no_leakage(pre_2010_smiles, future_drugs_2010) is True

    def test_no_future_leakage_2015(self, future_drugs_2015: list[dict]) -> None:
        """No post-2015 approved drugs in pre-2015 training data."""
        pre_2015_smiles = {
            info["smiles"]
            for info in EGFR_DRUG_APPROVALS.values()
            if info["approved_year"] <= 2015
        }
        assert verify_no_leakage(pre_2015_smiles, future_drugs_2015) is True

    def test_future_drugs_excluded(self) -> None:
        """Osimertinib (2015) should be in future drugs for 2010 cutoff.
        Lazertinib (2021) should be in future drugs for 2015 cutoff."""
        future_2010 = get_future_drugs(2010)
        future_2015 = get_future_drugs(2015)

        future_2010_names = {d["name"] for d in future_2010}
        future_2015_names = {d["name"] for d in future_2015}

        assert "osimertinib" in future_2010_names
        assert "afatinib" in future_2010_names
        assert "lazertinib" in future_2015_names
        assert "mobocertinib" in future_2015_names

    def test_leakage_detected_when_future_drug_in_training(self) -> None:
        """verify_no_leakage should raise ValueError if future drug is in training."""
        future = get_future_drugs(2010)
        # Intentionally include osimertinib in training
        training = {EGFR_DRUG_APPROVALS["osimertinib"]["smiles"]}
        with pytest.raises(ValueError, match="Temporal leakage detected"):
            verify_no_leakage(training, future)

    def test_reference_binders_restricted_2010(self) -> None:
        """Pre-2010 refs should only be erlotinib (2004) and gefitinib (2003)."""
        refs = get_pre_cutoff_reference_binders(2010)
        ref_set = set(refs)

        # Erlotinib and gefitinib should be present
        assert EGFR_DRUG_APPROVALS["erlotinib"]["smiles"] in ref_set
        assert EGFR_DRUG_APPROVALS["gefitinib"]["smiles"] in ref_set

        # Osimertinib (2015) should NOT be present
        assert EGFR_DRUG_APPROVALS["osimertinib"]["smiles"] not in ref_set

        # Afatinib (2013) should NOT be present
        assert EGFR_DRUG_APPROVALS["afatinib"]["smiles"] not in ref_set

    def test_reference_binders_restricted_2015(self) -> None:
        """Pre-2015 refs should include 4 drugs (erlotinib, gefitinib,
        afatinib, osimertinib) but not lazertinib (2021)."""
        refs = get_pre_cutoff_reference_binders(2015)
        ref_set = set(refs)

        assert EGFR_DRUG_APPROVALS["erlotinib"]["smiles"] in ref_set
        assert EGFR_DRUG_APPROVALS["gefitinib"]["smiles"] in ref_set
        assert EGFR_DRUG_APPROVALS["afatinib"]["smiles"] in ref_set
        assert EGFR_DRUG_APPROVALS["osimertinib"]["smiles"] in ref_set
        assert EGFR_DRUG_APPROVALS["lazertinib"]["smiles"] not in ref_set


# ═══════════════════════════════════════════════════════════════════════════
# Enrichment factor tests
# ═══════════════════════════════════════════════════════════════════════════


class TestEnrichmentFactor:
    """Test enrichment factor computation edge cases."""

    def test_enrichment_perfect(self) -> None:
        """All hits concentrated in top-K should give maximum EF."""
        # 3 hits in top-3 out of 10 candidates, 3 total hits
        sims = [0.8, 0.6, 0.5, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        ef = compute_enrichment_factor(sims, threshold=0.4, top_k=3)
        # EF = (3/3) / (3/10) = 1.0 / 0.3 = 3.333...
        assert ef == pytest.approx(3.3333, abs=0.01)

    def test_enrichment_random(self) -> None:
        """Uniformly distributed hits should give EF close to 1.0."""
        # 10 hits evenly distributed across 100 candidates
        sims = []
        for i in range(100):
            sims.append(0.5 if i % 10 == 0 else 0.1)
        ef = compute_enrichment_factor(sims, threshold=0.4, top_k=10)
        # 1 hit in top 10, 10 total hits out of 100
        # EF = (1/10) / (10/100) = 0.1 / 0.1 = 1.0
        assert ef == pytest.approx(1.0, abs=0.01)

    def test_enrichment_zero_hits(self) -> None:
        """No hits anywhere should return EF = 0.0."""
        sims = [0.1, 0.2, 0.15, 0.05, 0.3]
        ef = compute_enrichment_factor(sims, threshold=0.4, top_k=3)
        assert ef == 0.0

    def test_enrichment_k_larger_than_n(self) -> None:
        """top_k > n_candidates should clamp gracefully."""
        sims = [0.8, 0.5, 0.1]  # 3 candidates, k=10
        ef = compute_enrichment_factor(sims, threshold=0.4, top_k=10)
        # effective_k = 3, 2 hits in top 3, 2 total hits
        # EF = (2/3) / (2/3) = 1.0
        assert ef == pytest.approx(1.0, abs=0.01)

    def test_enrichment_all_hits(self) -> None:
        """Every candidate is a hit -> EF = 1.0."""
        sims = [0.9, 0.8, 0.7, 0.6, 0.5]
        ef = compute_enrichment_factor(sims, threshold=0.4, top_k=2)
        # 2 hits in top 2, 5 total hits out of 5
        # EF = (2/2) / (5/5) = 1.0
        assert ef == pytest.approx(1.0, abs=0.01)

    def test_enrichment_empty_list(self) -> None:
        """Empty candidate list should return 0.0."""
        assert compute_enrichment_factor([], threshold=0.4, top_k=10) == 0.0

    def test_enrichment_k_zero(self) -> None:
        """top_k=0 should return 0.0."""
        assert compute_enrichment_factor([0.5, 0.6], threshold=0.4, top_k=0) == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# Similarity and novelty tests
# ═══════════════════════════════════════════════════════════════════════════


class TestSimilarityAndNovelty:
    """Test similarity computation and novelty metrics."""

    def test_max_similarity_known_drug(self, erlotinib_smiles: str) -> None:
        """Erlotinib should have perfect similarity to itself."""
        sims = compute_candidate_future_similarities(
            [erlotinib_smiles], [erlotinib_smiles],
        )
        assert len(sims) == 1
        assert sims[0] > 0.9  # Should be ~1.0

    def test_similarity_dissimilar_molecule(self) -> None:
        """Aspirin should have low similarity to erlotinib."""
        aspirin = "CC(=O)Oc1ccccc1C(O)=O"
        erlotinib = EGFR_DRUG_APPROVALS["erlotinib"]["smiles"]
        sims = compute_candidate_future_similarities(
            [aspirin], [erlotinib],
        )
        assert sims[0] < 0.3

    def test_novelty_computation(self) -> None:
        """3 of 5 candidates in training -> novelty = 0.4."""
        candidates = ["A", "B", "C", "D", "E"]
        training = {"A", "B", "C"}
        novelty = compute_novelty(candidates, training)
        assert novelty == pytest.approx(0.4, abs=0.001)

    def test_novelty_all_novel(self) -> None:
        """No candidates in training -> novelty = 1.0."""
        candidates = ["X", "Y", "Z"]
        training = {"A", "B", "C"}
        assert compute_novelty(candidates, training) == 1.0

    def test_novelty_none_novel(self) -> None:
        """All candidates in training -> novelty = 0.0."""
        candidates = ["A", "B"]
        training = {"A", "B"}
        assert compute_novelty(candidates, training) == 0.0

    def test_novelty_empty_candidates(self) -> None:
        """Empty candidate list -> novelty = 0.0."""
        assert compute_novelty([], {"A"}) == 0.0

    def test_future_drug_similarities_no_future(self) -> None:
        """No future drugs -> all similarities are 0.0."""
        sims = compute_candidate_future_similarities(["CCO", "CCC"], [])
        assert sims == [0.0, 0.0]


# ═══════════════════════════════════════════════════════════════════════════
# Integration and serialization tests
# ═══════════════════════════════════════════════════════════════════════════


class TestIntegration:
    """Integration tests for dataclass construction and serialization."""

    def test_retrospective_result_serialization(self) -> None:
        """RetrospectiveResult should serialize to JSON."""
        result = RetrospectiveResult(
            cutoff_year=2010,
            pipeline="static",
            enrichment_factors={10: 1.5, 50: 1.2},
            max_similarity_to_future=0.65,
            mean_similarity_to_future=0.32,
            n_candidates=100,
            n_future_drugs=4,
            future_drug_ranks={"osimertinib": 15, "afatinib": None},
            future_drug_similarities={"osimertinib": 0.45, "afatinib": 0.32},
            novelty_vs_training=0.85,
            top_k_hits={10: 3, 50: 8},
        )
        d = to_serializable(result)
        # Should be JSON-serializable (int keys converted to strings)
        json_str = json.dumps(d)
        assert '"cutoff_year": 2010' in json_str
        assert '"10":' in json_str  # int key -> string

    def test_retrospective_result_contract_properties(self) -> None:
        """Contract 10 compatibility properties should work."""
        result = RetrospectiveResult(
            enrichment_factors={10: 2.5, 50: 1.8, 100: 1.2},
        )
        assert result.enrichment_factor_10 == 2.5
        assert result.enrichment_factor_50 == 1.8

    def test_retrospective_result_missing_k(self) -> None:
        """Missing K values should return 0.0."""
        result = RetrospectiveResult(enrichment_factors={10: 1.5})
        assert result.enrichment_factor_50 == 0.0

    def test_retrospective_comparison_summary(self) -> None:
        """RetrospectiveComparison should produce a non-empty summary."""
        results = [
            RetrospectiveResult(
                cutoff_year=2010,
                pipeline="static",
                enrichment_factors={10: 1.5, 50: 1.2},
                n_future_drugs=4,
                future_drug_ranks={"osimertinib": 5},
                future_drug_similarities={"osimertinib": 0.55},
                max_similarity_to_future=0.55,
                novelty_vs_training=0.8,
            ),
            RetrospectiveResult(
                cutoff_year=2010,
                pipeline="state_aware",
                enrichment_factors={10: 2.0, 50: 1.5},
                n_future_drugs=4,
                future_drug_ranks={"osimertinib": 3},
                future_drug_similarities={"osimertinib": 0.62},
                max_similarity_to_future=0.62,
                novelty_vs_training=0.9,
            ),
        ]
        comparison = RetrospectiveComparison(
            results=results,
            cutoffs=[2010],
        )
        summary = generate_retrospective_summary(comparison)
        assert len(summary) > 0
        assert "2010" in summary
        assert "static" in summary

    def test_timesplit_dataset_valid(self) -> None:
        """TimeSplitDataset should have correct field types."""
        ds = TimeSplitDataset(
            cutoff_year=2010,
            train_smiles=["CCO", "CCC", "CCCC"],
            train_pIC50=[5.0, 6.0, 7.0],
            n_train=3,
            held_out_drugs=[{"name": "osimertinib", "smiles": "C", "approved_year": 2015}],
            n_held_out=1,
            pre_cutoff_reference_binders=["CCO"],
            source="test",
        )
        assert ds.cutoff_year == 2010
        assert ds.n_train == 3
        assert ds.n_held_out == 1
        assert len(ds.train_smiles) == len(ds.train_pIC50)

    def test_compute_retrospective_metrics_integration(self) -> None:
        """Full compute_retrospective_metrics with synthetic data."""
        erlotinib = EGFR_DRUG_APPROVALS["erlotinib"]["smiles"]
        osimertinib = EGFR_DRUG_APPROVALS["osimertinib"]["smiles"]

        candidates = [
            {"smiles": erlotinib, "composite_score": 0.8},
            {"smiles": "CCO", "composite_score": 0.6},
            {"smiles": "CCCC", "composite_score": 0.4},
        ]
        future_drugs = [
            {"name": "osimertinib", "smiles": osimertinib},
        ]
        training_smiles = {"CCO"}

        result = compute_retrospective_metrics(
            candidates=candidates,
            future_drugs=future_drugs,
            training_smiles=training_smiles,
            pipeline="static",
            cutoff_year=2010,
            k_values=[10],
            threshold=0.3,
        )

        assert result.cutoff_year == 2010
        assert result.pipeline == "static"
        assert result.n_candidates == 3
        assert result.n_future_drugs == 1
        assert 0.0 <= result.max_similarity_to_future <= 1.0
        assert 0.0 <= result.mean_similarity_to_future <= 1.0
        assert 0.0 <= result.novelty_vs_training <= 1.0
        assert "osimertinib" in result.future_drug_ranks
        assert "osimertinib" in result.future_drug_similarities

    def test_egfr_drug_approvals_complete(self) -> None:
        """EGFR_DRUG_APPROVALS should have all required drugs."""
        expected = {
            "erlotinib", "gefitinib", "afatinib", "osimertinib",
            "dacomitinib", "lazertinib", "mobocertinib",
        }
        assert set(EGFR_DRUG_APPROVALS.keys()) == expected

        for name, info in EGFR_DRUG_APPROVALS.items():
            assert "smiles" in info, f"{name} missing smiles"
            assert "approved_year" in info, f"{name} missing approved_year"
            assert "generation" in info, f"{name} missing generation"
            assert "state" in info, f"{name} missing state"
            assert isinstance(info["approved_year"], int)
            assert len(info["smiles"]) > 5

    def test_get_future_drugs_cutoff_boundary(self) -> None:
        """Drug approved in exactly the cutoff year should NOT be future."""
        # Osimertinib approved 2015 -> not in future for cutoff=2015
        future_2015 = get_future_drugs(2015)
        names = {d["name"] for d in future_2015}
        assert "osimertinib" not in names
        # But should be in future for cutoff=2014
        future_2014 = get_future_drugs(2014)
        names_2014 = {d["name"] for d in future_2014}
        assert "osimertinib" in names_2014
