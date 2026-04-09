"""Tests for Phase 6: state-conditioned generation.

Covers:
- Candidate schemas
- Filtering rules
- Generation metadata tracking
- Diversity computation
- Evaluation outputs
- Cross-state comparison
"""

from __future__ import annotations

import pytest

from statebind.baselines.models import CandidateSource
from statebind.generation.conditioning import (
    PocketCondition,
    get_pocket_conditions,
    select_strategies_for_pocket,
)
from statebind.generation.diversity import (
    analyze_cross_state_diversity,
    compute_diversity,
)
from statebind.generation.evaluation import (
    compare_with_static_baseline,
    evaluate_generation,
    evaluation_to_dict,
)
from statebind.generation.filtering import (
    filter_all_states,
    filter_state_library,
    get_filters_for_state,
)
from statebind.generation.generator import generate_all_states, generate_for_state
from statebind.generation.models import (
    FilteredStateLibrary,
    GenerationStrategy,
    MultiStateFilterResult,
    MultiStateGenerationResult,
    StateConditionedCandidate,
    StateConditionedLibrary,
)
from statebind.structure.models import PocketDescriptor


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def conditions():
    return get_pocket_conditions()


@pytest.fixture
def generation():
    return generate_all_states()


@pytest.fixture
def filtered(generation):
    return filter_all_states(generation)


# ── Candidate schema tests ───────────────────────────────────────────────

class TestCandidateSchema:
    def test_candidate_has_required_fields(self):
        c = StateConditionedCandidate(
            candidate_id="test_001",
            smiles="CCO",
            target_state="DFGin_aCin",
            strategy=GenerationStrategy.ANALOG,
        )
        assert c.candidate_id == "test_001"
        assert c.smiles == "CCO"
        assert c.target_state == "DFGin_aCin"
        assert c.strategy == GenerationStrategy.ANALOG

    def test_library_has_state(self):
        lib = StateConditionedLibrary(
            state="DFGin_aCin",
            candidates=[],
            n_candidates=0,
        )
        assert lib.state == "DFGin_aCin"

    def test_multi_state_result_has_states(self, generation):
        assert len(generation.states) == 3
        assert len(generation.libraries) == 3

    def test_all_candidates_have_state(self, generation):
        for lib in generation.libraries:
            for c in lib.candidates:
                assert c.target_state == lib.state

    def test_all_candidates_have_strategy(self, generation):
        for lib in generation.libraries:
            for c in lib.candidates:
                assert c.strategy in GenerationStrategy

    def test_all_candidates_have_smiles(self, generation):
        for lib in generation.libraries:
            for c in lib.candidates:
                assert len(c.smiles) > 0

    def test_candidates_have_pocket_metadata(self, generation):
        for lib in generation.libraries:
            for c in lib.candidates:
                assert c.pocket_volume > 0 or c.source == CandidateSource.ENUMERATED


# ── Conditioning tests ────────────────────────────────────────────────────

class TestConditioning:
    def test_three_states_covered(self, conditions):
        assert len(conditions) == 3

    def test_active_state_has_hinge_strategy(self, conditions):
        active = conditions["DFGin_aCin"]
        assert GenerationStrategy.HINGE_OPTIMIZED in active.strategies

    def test_dfgout_has_back_pocket_strategy(self, conditions):
        dfgout = conditions["DFGout_aCin"]
        assert GenerationStrategy.BACK_POCKET_EXTENSION in dfgout.strategies

    def test_active_has_gatekeeper_avoiding(self, conditions):
        active = conditions["DFGin_aCin"]
        assert GenerationStrategy.GATEKEEPER_AVOIDING in active.strategies

    def test_dynamic_strategy_selection(self):
        pocket = PocketDescriptor(
            pocket_volume=800.0,
            back_pocket_accessible=True,
            covalent_cys_exposed=True,
            gatekeeper_clearance=5.0,
            hinge_accessibility=0.9,
            p_loop_conformation="folded",
        )
        strategies = select_strategies_for_pocket(pocket)
        assert GenerationStrategy.BACK_POCKET_EXTENSION in strategies
        assert GenerationStrategy.VOLUME_FILLING in strategies
        assert GenerationStrategy.HINGE_OPTIMIZED in strategies
        assert GenerationStrategy.P_LOOP_INTERACTION in strategies


# ── Generation tests ──────────────────────────────────────────────────────

class TestGeneration:
    def test_generates_for_all_states(self, generation):
        assert all(lib.n_candidates > 0 for lib in generation.libraries)

    def test_total_candidates_positive(self, generation):
        assert generation.total_candidates > 0

    def test_unique_smiles_less_than_total(self, generation):
        assert generation.total_unique_smiles <= generation.total_candidates

    def test_cross_state_overlap_computed(self, generation):
        assert len(generation.cross_state_overlap) > 0

    def test_dfgout_has_back_pocket_candidates(self, generation):
        dfgout = next(l for l in generation.libraries if l.state == "DFGout_aCin")
        back_pocket = [c for c in dfgout.candidates
                       if c.strategy == GenerationStrategy.BACK_POCKET_EXTENSION]
        assert len(back_pocket) > 0

    def test_active_has_no_ploop_candidates(self, generation):
        active = next(l for l in generation.libraries if l.state == "DFGin_aCin")
        ploop = [c for c in active.candidates
                 if c.strategy == GenerationStrategy.P_LOOP_INTERACTION]
        assert len(ploop) == 0

    def test_deduplication_within_state(self, generation):
        for lib in generation.libraries:
            smiles = [c.smiles for c in lib.candidates]
            assert len(smiles) == len(set(smiles))

    def test_generation_deterministic(self):
        g1 = generate_all_states()
        g2 = generate_all_states()
        assert g1.total_candidates == g2.total_candidates
        for l1, l2 in zip(g1.libraries, g2.libraries):
            s1 = sorted(c.smiles for c in l1.candidates)
            s2 = sorted(c.smiles for c in l2.candidates)
            assert s1 == s2


# ── Filtering tests ──────────────────────────────────────────────────────

class TestFiltering:
    def test_dfgin_uses_type1_filters(self):
        filters = get_filters_for_state("DFGin_aCin")
        mw_filter = next(f for f in filters if f.property_name == "estimated_mw")
        assert mw_filter.max_value == 600

    def test_dfgout_uses_type2_filters(self):
        filters = get_filters_for_state("DFGout_aCin")
        mw_filter = next(f for f in filters if f.property_name == "estimated_mw")
        assert mw_filter.max_value == 800

    def test_filter_produces_results(self, filtered):
        assert filtered.total_passed > 0

    def test_filter_pass_rate_in_range(self, filtered):
        assert 0.0 <= filtered.overall_pass_rate <= 1.0

    def test_filtered_candidates_have_valid_smiles(self, filtered):
        from statebind.baselines.filtering import _is_valid_smiles
        for lib in filtered.libraries:
            for c in lib.candidates:
                assert _is_valid_smiles(c.smiles)

    def test_dfgout_allows_larger_molecules(self, filtered):
        """DFGout states should pass larger molecules that DFGin would reject."""
        dfgout_lib = next(l for l in filtered.libraries if l.state == "DFGout_aCin")
        mw_stats = dfgout_lib.property_stats.get("estimated_mw", {})
        if mw_stats and "max" in mw_stats:
            # Some DFGout candidates should have MW > 600 (type-I limit)
            # This test checks the filter threshold is different
            dfgout_filters = get_filters_for_state("DFGout_aCin")
            mw_filter = next(f for f in dfgout_filters if f.property_name == "estimated_mw")
            assert mw_filter.max_value > 600


# ── Diversity tests ──────────────────────────────────────────────────────

class TestDiversity:
    def test_compute_diversity_single(self):
        d = compute_diversity(["CCO"])
        assert d.diversity_score == 1.0  # single molecule = max diversity

    def test_compute_diversity_identical(self):
        d = compute_diversity(["CCO", "CCO", "CCO"])
        # All same SMILES → 1 unique → diversity = 1.0 (only 1 unique)
        assert d.n_unique_smiles == 1

    def test_compute_diversity_different(self):
        d = compute_diversity(["CCO", "c1ccccc1", "CC(=O)O"])
        assert d.diversity_score > 0

    def test_cross_state_diversity(self, filtered):
        report = analyze_cross_state_diversity(filtered)
        assert len(report.per_state) == 3
        assert report.total_unique_across_all > 0

    def test_state_unique_candidates_exist(self, filtered):
        report = analyze_cross_state_diversity(filtered)
        # At least some states should have unique candidates
        total_unique = sum(sd.n_state_unique for sd in report.per_state)
        assert total_unique > 0


# ── Evaluation tests ─────────────────────────────────────────────────────

class TestEvaluation:
    def test_evaluation_has_per_state(self, generation, filtered):
        diversity = analyze_cross_state_diversity(filtered)
        evl = evaluate_generation(generation, filtered, diversity)
        assert len(evl.per_state) == 3

    def test_evaluation_to_dict(self, generation, filtered):
        diversity = analyze_cross_state_diversity(filtered)
        evl = evaluate_generation(generation, filtered, diversity)
        d = evaluation_to_dict(evl)
        assert "total_generated" in d
        assert "per_state" in d
        assert len(d["per_state"]) == 3

    def test_baseline_comparison(self, filtered):
        static_smiles = {"CCO", "c1ccccc1"}  # dummy static set
        comp = compare_with_static_baseline(filtered, static_smiles)
        assert comp.state_conditioned_n_candidates > 0


# ── Metadata tracking tests ──────────────────────────────────────────────

class TestMetadataTracking:
    def test_generation_has_timestamp(self, generation):
        assert generation.generated_at != ""

    def test_library_has_config(self, generation):
        for lib in generation.libraries:
            assert "strategies" in lib.generation_config
            assert "rationale" in lib.generation_config

    def test_candidates_track_parent(self, generation):
        for lib in generation.libraries:
            for c in lib.candidates:
                if c.source == CandidateSource.ENUMERATED:
                    assert c.parent_id != ""

    def test_candidates_track_pocket_volume(self, generation):
        for lib in generation.libraries:
            assert lib.pocket_volume > 0
            for c in lib.candidates:
                if c.source == CandidateSource.REFERENCE:
                    assert c.pocket_volume > 0
