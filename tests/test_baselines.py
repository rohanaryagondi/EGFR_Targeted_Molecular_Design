"""Tests for the static baseline pipeline.

Tests cover:
- Pocket definition
- Candidate library construction
- Property filtering
- Scoring and ranking
- Evaluation metrics
- End-to-end pipeline
"""

import pytest

from statebind.baselines.candidates import (
    build_candidate_library,
    build_reference_candidates,
)
from statebind.baselines.evaluation import evaluate_baseline
from statebind.baselines.filtering import (
    DEFAULT_FILTERS,
    apply_filters,
    compute_properties,
    _is_valid_smiles,
    _estimate_mw,
    _estimate_hba,
    _count_rings,
)
from statebind.baselines.models import (
    BaselineEvaluation,
    CandidateLibrary,
    CandidateSource,
    FilteredLibrary,
    PocketDefinition,
    RankedCandidates,
    ScoredCandidate,
)
from statebind.baselines.pipeline import run_static_baseline
from statebind.baselines.pocket import get_baseline_pocket, select_baseline_structure
from statebind.baselines.scoring import (
    _score_reference_similarity,
    _tanimoto_ngram,
    score_candidates,
)


# ── Pocket Tests ────────────────────────────────────────────────────────


class TestPocketDefinition:
    def test_baseline_pocket_returns_pocket(self):
        pocket = get_baseline_pocket()
        assert isinstance(pocket, PocketDefinition)
        assert pocket.pdb_id == "1m17"
        assert pocket.pocket_type == "ATP-binding"

    def test_pocket_has_residues(self):
        pocket = get_baseline_pocket()
        assert len(pocket.residues) >= 15, "Pocket should have ≥15 residues"

    def test_pocket_has_key_residues(self):
        pocket = get_baseline_pocket()
        positions = {r.residue_number for r in pocket.residues}
        # Gatekeeper
        assert 790 in positions, "Missing gatekeeper T790"
        # DFG motif
        assert 855 in positions or 856 in positions, "Missing DFG residues"
        # Hinge
        assert 791 in positions, "Missing hinge M791"
        # Covalent site
        assert 797 in positions, "Missing C797"

    def test_pocket_roles_present(self):
        pocket = get_baseline_pocket()
        roles = {r.role for r in pocket.residues}
        assert "gatekeeper" in roles
        assert "hinge" in roles
        assert "P-loop" in roles

    def test_pocket_custom_pdb_id(self):
        pocket = get_baseline_pocket(pdb_id="2jit", chain="B")
        assert pocket.pdb_id == "2jit"
        assert pocket.chain == "B"
        assert pocket.pocket_id == "2jit_B_ATP"

    def test_structure_selection(self):
        meta = select_baseline_structure()
        assert meta["pdb_id"] == "1m17"
        assert meta["state"] == "DFGin_aCin"
        assert len(meta["what_this_misses"]) > 0


# ── Candidate Library Tests ─────────────────────────────────────────────


class TestCandidateLibrary:
    def test_reference_candidates_not_empty(self):
        refs = build_reference_candidates()
        assert len(refs) > 0

    def test_reference_candidates_have_smiles(self):
        refs = build_reference_candidates()
        for c in refs:
            assert c.smiles, f"No SMILES for {c.candidate_id}"
            assert c.source == CandidateSource.REFERENCE

    def test_build_library_without_analogs(self):
        lib = build_candidate_library(enumerate_analogs=False)
        assert isinstance(lib, CandidateLibrary)
        assert lib.n_candidates > 0
        # All should be reference
        assert all(c.source == CandidateSource.REFERENCE for c in lib.candidates)

    def test_build_library_with_analogs(self):
        lib = build_candidate_library(enumerate_analogs=True)
        sources = {c.source for c in lib.candidates}
        assert CandidateSource.REFERENCE in sources
        assert CandidateSource.ENUMERATED in sources
        # Should have more candidates with analogs
        lib_no_analogs = build_candidate_library(enumerate_analogs=False)
        assert lib.n_candidates > lib_no_analogs.n_candidates

    def test_no_duplicate_smiles_in_library(self):
        lib = build_candidate_library(enumerate_analogs=True)
        smiles = [c.smiles for c in lib.candidates]
        assert len(smiles) == len(set(smiles)), "Duplicate SMILES in library"

    def test_library_has_metadata(self):
        lib = build_candidate_library()
        assert lib.target_pdb_id == "1m17"
        assert lib.pocket_id == "1m17_A_ATP"
        assert lib.generated_at


# ── Filtering Tests ─────────────────────────────────────────────────────


class TestFiltering:
    def test_smiles_validity_check(self):
        assert _is_valid_smiles("CCO")
        assert _is_valid_smiles("c1ccccc1")
        assert not _is_valid_smiles("")
        assert not _is_valid_smiles("(()")  # unbalanced

    def test_property_estimation_erlotinib(self):
        # Erlotinib SMILES
        smiles = "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC"
        props = compute_properties(smiles)
        assert props["smiles_valid"] == 1.0
        # MW should be in a reasonable range (actual: 393.4)
        assert 250 < props["estimated_mw"] < 550, f"MW estimate {props['estimated_mw']} seems wrong"
        assert props["estimated_hba"] > 0
        assert props["n_heavy_atoms"] > 10

    def test_property_estimation_invalid(self):
        props = compute_properties("")
        assert props["smiles_valid"] == 0.0
        assert props["estimated_mw"] is None

    def test_apply_filters_passes_known_drugs(self):
        lib = build_candidate_library(enumerate_analogs=False)
        filtered = apply_filters(lib)
        assert filtered.n_passed > 0, "No candidates passed filtering"
        # Most known drugs should pass Lipinski-like filters
        pass_rate = filtered.n_passed / filtered.n_input
        assert pass_rate > 0.5, f"Only {pass_rate:.0%} passed — too aggressive"

    def test_apply_filters_returns_correct_counts(self):
        lib = build_candidate_library(enumerate_analogs=False)
        filtered = apply_filters(lib)
        assert filtered.n_input == lib.n_candidates
        assert filtered.n_passed + filtered.n_failed == filtered.n_input

    def test_filter_results_have_properties(self):
        lib = build_candidate_library(enumerate_analogs=False)
        filtered = apply_filters(lib)
        for result in filtered.results:
            assert len(result.properties) > 0
            assert "estimated_mw" in result.properties

    def test_default_filters_exist(self):
        assert len(DEFAULT_FILTERS) >= 3
        names = {f.property_name for f in DEFAULT_FILTERS}
        assert "estimated_mw" in names

    def test_ring_count(self):
        # Benzene
        assert _count_rings("c1ccccc1") >= 1
        # Two rings
        assert _count_rings("c1ccc2ccccc2c1") >= 2


# ── Scoring Tests ───────────────────────────────────────────────────────


class TestScoring:
    def test_tanimoto_identical(self):
        smiles = "CCO"
        assert _tanimoto_ngram(smiles, smiles) == 1.0

    def test_tanimoto_different(self):
        sim = _tanimoto_ngram("CCO", "c1ccccc1NC(=O)CCCCCC")
        assert 0.0 <= sim < 1.0

    def test_reference_similarity_known_drug(self):
        # Erlotinib should be very similar to reference (it IS the reference)
        erlotinib = "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC"
        sim = _score_reference_similarity(erlotinib)
        assert sim > 0.8, f"Erlotinib similarity {sim} too low"

    def test_reference_similarity_empty(self):
        assert _score_reference_similarity("") == 0.0

    def test_score_candidates_returns_ranked(self):
        lib = build_candidate_library(enumerate_analogs=True)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        assert isinstance(ranked, RankedCandidates)
        assert ranked.n_ranked > 0

    def test_scores_are_sorted_descending(self):
        lib = build_candidate_library(enumerate_analogs=True)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        scores = [c.composite_score for c in ranked.candidates]
        assert scores == sorted(scores, reverse=True), "Not sorted descending"

    def test_ranks_are_sequential(self):
        lib = build_candidate_library(enumerate_analogs=True)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        ranks = [c.rank for c in ranked.candidates]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_scored_candidates_have_components(self):
        lib = build_candidate_library(enumerate_analogs=False)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        for c in ranked.candidates:
            assert len(c.scores) == 3
            names = {s.name for s in c.scores}
            assert "reference_similarity" in names
            assert "druglikeness" in names
            assert "docking_proxy" in names

    def test_docking_stub_is_labeled(self):
        lib = build_candidate_library(enumerate_analogs=False)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        for c in ranked.candidates:
            dock = next(s for s in c.scores if s.name == "docking_proxy")
            assert dock.is_stub, "Docking stub should be marked as stub"
            assert dock.value == 0.5, "Docking stub should return 0.5"

    def test_known_drugs_rank_high(self):
        """Known EGFR drugs should rank in top half (sanity check)."""
        lib = build_candidate_library(enumerate_analogs=True)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        n = ranked.n_ranked
        top_half_ids = {c.candidate_id for c in ranked.candidates[:n // 2 + 1]}
        # At least one reference compound should be in top half
        ref_in_top = [cid for cid in top_half_ids if cid.startswith("ref_")]
        assert len(ref_in_top) > 0, "No reference compounds in top half of ranking"


# ── Evaluation Tests ────────────────────────────────────────────────────


class TestEvaluation:
    def test_evaluate_returns_metrics(self):
        lib = build_candidate_library(enumerate_analogs=True)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        ev = evaluate_baseline(ranked)
        assert isinstance(ev, BaselineEvaluation)
        assert ev.validity_rate > 0
        assert ev.uniqueness_rate > 0
        assert ev.diversity_score >= 0

    def test_evaluate_empty(self):
        ranked = RankedCandidates(
            run_id="empty", target_pdb_id="1m17", pocket_id="test",
        )
        ev = evaluate_baseline(ranked)
        assert ev.n_candidates_ranked == 0

    def test_top_k_populated(self):
        lib = build_candidate_library(enumerate_analogs=True)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        ev = evaluate_baseline(ranked, top_k=5)
        assert len(ev.top_k_candidates) <= 5
        assert len(ev.top_k_candidates) > 0

    def test_score_stats_present(self):
        lib = build_candidate_library(enumerate_analogs=True)
        filtered = apply_filters(lib)
        ranked = score_candidates(filtered)
        ev = evaluate_baseline(ranked)
        assert "composite_score" in ev.score_stats
        assert "reference_similarity" in ev.score_stats


# ── End-to-End Pipeline Test ────────────────────────────────────────────


class TestPipeline:
    def test_full_pipeline_runs(self, tmp_path):
        result = run_static_baseline(
            output_dir=tmp_path,
            enumerate_analogs=True,
            top_k=5,
        )
        assert result.ranked.n_ranked > 0
        assert result.evaluation.validity_rate > 0

        # Check artifacts written
        expected_files = [
            "structure_selection.json",
            "pocket_definition.json",
            "candidate_library.json",
            "filtered_library.json",
            "ranked_candidates.json",
            "evaluation.json",
            "ranking_table.csv",
        ]
        for fname in expected_files:
            assert (tmp_path / fname).exists(), f"Missing artifact: {fname}"

    def test_pipeline_without_analogs(self, tmp_path):
        result = run_static_baseline(
            output_dir=tmp_path,
            enumerate_analogs=False,
        )
        assert result.ranked.n_ranked > 0
        # All candidates should be references
        for c in result.library.candidates:
            assert c.source == CandidateSource.REFERENCE

    def test_pipeline_metadata_consistent(self, tmp_path):
        result = run_static_baseline(output_dir=tmp_path)
        assert result.structure_metadata["pdb_id"] == "1m17"
        assert result.pocket.pdb_id == "1m17"
        assert result.library.target_pdb_id == "1m17"
        assert result.ranked.target_pdb_id == "1m17"
        assert result.ranked.pipeline == "static_baseline"
