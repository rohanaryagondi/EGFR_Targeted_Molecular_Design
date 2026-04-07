"""Tests for Workstream 12: Pareto Multi-Objective Optimization.

Covers:
- Pareto front computation (non-dominated sorting)
- Hypervolume indicator calculation
- Crowding distance
- Pipeline comparison (ParetoComparison)
- Visualization functions
- Integration with ComparativeResult
- Serialization
- Graceful degradation without pymoo
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from statebind.ranking.pareto import (
    HAS_PYMOO,
    OBJECTIVE_NAMES,
    ParetoComparison,
    _crowding_distance,
    _is_dominated,
    compare_pareto_fronts,
    compute_pareto_front,
    extract_score_matrix,
)

# ══════════════════════════════════════════════════════════════════════
# 1. Pareto front computation
# ══════════════════════════════════════════════════════════════════════


class TestParetoFrontComputation:
    """Tests for non-dominated sorting and Pareto front extraction."""

    def test_pareto_single_dominated(self):
        """One candidate dominates all others -> front = [that candidate]."""
        scores = np.array([
            [0.9, 0.9],
            [0.1, 0.1],
            [0.2, 0.2],
            [0.3, 0.3],
        ])
        result = compute_pareto_front(scores)
        assert result.front_indices == [0]
        assert result.front_scores.shape == (1, 2)

    def test_pareto_all_nondominated(self):
        """When no candidate dominates another, all are on the front."""
        scores = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [0.5, 0.5],
        ])
        result = compute_pareto_front(scores)
        # All three form a Pareto front (none dominates any other)
        assert sorted(result.front_indices) == [0, 1, 2]

    def test_pareto_two_objectives(self):
        """Known 2D example with expected front."""
        scores = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [0.5, 0.5],
            [0.3, 0.3],  # dominated by (0.5, 0.5)
            [0.1, 0.1],  # dominated by many
        ])
        result = compute_pareto_front(scores)
        assert sorted(result.front_indices) == [0, 1, 2]

    def test_pareto_four_objectives(self):
        """Works with 4 objectives (project's actual setup)."""
        rng = np.random.default_rng(42)
        scores = rng.uniform(0, 1, size=(20, 4))
        result = compute_pareto_front(
            scores,
            objective_names=OBJECTIVE_NAMES,
        )
        assert result.n_objectives == 4
        assert len(result.front_indices) > 0
        assert len(result.front_indices) <= 20
        assert result.objective_names == OBJECTIVE_NAMES
        assert result.front_scores.shape[1] == 4

    def test_pareto_empty_input(self):
        """Empty array returns empty front."""
        scores = np.empty((0, 3))
        result = compute_pareto_front(scores)
        assert result.front_indices == []
        assert result.front_scores.shape == (0, 3)
        assert result.hypervolume == 0.0
        assert result.crowding_distances == []
        assert result.n_candidates == 0

    def test_pareto_single_candidate(self):
        """Single candidate is always on the front."""
        scores = np.array([[0.5, 0.6, 0.7]])
        result = compute_pareto_front(scores)
        assert result.front_indices == [0]

    def test_pareto_invalid_dimensions(self):
        """1D input raises ValueError."""
        with pytest.raises(ValueError, match="2D"):
            compute_pareto_front(np.array([1.0, 2.0, 3.0]))

    def test_pareto_objective_names_mismatch(self):
        """Mismatched objective_names length raises ValueError."""
        scores = np.array([[0.5, 0.6]])
        with pytest.raises(ValueError, match="objective_names length"):
            compute_pareto_front(scores, objective_names=["a", "b", "c"])


# ══════════════════════════════════════════════════════════════════════
# 2. Hypervolume computation
# ══════════════════════════════════════════════════════════════════════


class TestHypervolume:
    """Tests for hypervolume indicator."""

    def test_hypervolume_monotone(self):
        """Adding a non-dominated point never decreases hypervolume."""
        base_scores = np.array([
            [0.8, 0.2],
            [0.2, 0.8],
        ])
        extended_scores = np.array([
            [0.8, 0.2],
            [0.2, 0.8],
            [0.6, 0.6],  # non-dominated addition
        ])
        ref = [0.0, 0.0]
        r1 = compute_pareto_front(base_scores, reference_point=ref)
        r2 = compute_pareto_front(extended_scores, reference_point=ref)
        assert r2.hypervolume >= r1.hypervolume

    def test_hypervolume_single_point(self):
        """Single point hypervolume = product of (point - ref) for 2D."""
        scores = np.array([[0.8, 0.6]])
        ref = [0.0, 0.0]
        result = compute_pareto_front(scores, reference_point=ref)
        expected = 0.8 * 0.6  # = 0.48
        assert abs(result.hypervolume - expected) < 0.01

    def test_hypervolume_known_value(self):
        """2D example with analytically computable hypervolume."""
        # Two points: (0.8, 0.2) and (0.2, 0.8), ref = (0, 0)
        # HV = 0.8*0.8 - 0.6*0.6 = 0.64 - 0.36 = 0.28 ... actually
        # For 2D Pareto: the dominated area below the staircase
        # Points sorted by x: (0.2, 0.8), (0.8, 0.2)
        # Area = 0.2*0.8 + (0.8-0.2)*0.2 = 0.16 + 0.12 = 0.28
        # With pymoo: rect(0.2, 0.8) + rect(0.6, 0.2) = 0.16 + 0.12 = 0.28
        scores = np.array([
            [0.8, 0.2],
            [0.2, 0.8],
        ])
        ref = [0.0, 0.0]
        result = compute_pareto_front(scores, reference_point=ref)
        assert abs(result.hypervolume - 0.28) < 0.02

    def test_hypervolume_reference_point(self):
        """Different reference points give different hypervolumes."""
        scores = np.array([
            [0.8, 0.6],
            [0.6, 0.8],
        ])
        r1 = compute_pareto_front(scores, reference_point=[0.0, 0.0])
        r2 = compute_pareto_front(scores, reference_point=[0.5, 0.5])
        # Tighter reference point -> smaller hypervolume
        assert r2.hypervolume < r1.hypervolume

    def test_hypervolume_nonnegative(self):
        """Hypervolume is always non-negative."""
        rng = np.random.default_rng(123)
        scores = rng.uniform(0, 1, size=(15, 4))
        result = compute_pareto_front(scores, reference_point=[0.0] * 4)
        assert result.hypervolume >= 0.0


# ══════════════════════════════════════════════════════════════════════
# 3. Crowding distance
# ══════════════════════════════════════════════════════════════════════


class TestCrowdingDistance:
    """Tests for crowding distance computation."""

    def test_crowding_boundary_points(self):
        """Boundary points get infinite distance."""
        front = np.array([
            [0.0, 1.0],
            [0.5, 0.5],
            [1.0, 0.0],
        ])
        distances = _crowding_distance(front)
        assert distances[0] == float("inf")
        assert distances[2] == float("inf")

    def test_crowding_two_points(self):
        """Two points both get infinity."""
        front = np.array([
            [0.3, 0.7],
            [0.7, 0.3],
        ])
        distances = _crowding_distance(front)
        assert all(d == float("inf") for d in distances)

    def test_crowding_interior_finite(self):
        """Interior points have finite positive distance."""
        front = np.array([
            [0.0, 1.0],
            [0.3, 0.7],
            [0.5, 0.5],
            [0.7, 0.3],
            [1.0, 0.0],
        ])
        distances = _crowding_distance(front)
        # Boundary points are inf
        assert distances[0] == float("inf")
        assert distances[4] == float("inf")
        # Interior points are finite and positive
        for d in distances[1:4]:
            assert 0 < d < float("inf")


# ══════════════════════════════════════════════════════════════════════
# 4. Comparison tests
# ══════════════════════════════════════════════════════════════════════


class TestParetoComparison:
    """Tests for compare_pareto_fronts."""

    def test_comparison_basic(self):
        """Basic comparison runs without error."""
        static = np.array([[0.8, 0.2], [0.2, 0.8], [0.5, 0.5]])
        state_aware = np.array([[0.9, 0.3], [0.3, 0.9], [0.6, 0.6]])
        comp = compare_pareto_fronts(static, state_aware)
        assert isinstance(comp, ParetoComparison)
        assert comp.hypervolume_ratio > 0

    def test_comparison_symmetric(self):
        """Swapping pipelines inverts the ratio."""
        a = np.array([[0.8, 0.2], [0.2, 0.8]])
        b = np.array([[0.7, 0.3], [0.3, 0.7]])
        comp_ab = compare_pareto_fronts(a, b)
        comp_ba = compare_pareto_fronts(b, a)
        # ratio_ab * ratio_ba should be ~1
        if comp_ab.hypervolume_ratio != float("inf") and comp_ba.hypervolume_ratio != float("inf"):
            assert abs(comp_ab.hypervolume_ratio * comp_ba.hypervolume_ratio - 1.0) < 0.1

    def test_dominance_fraction_range(self):
        """Dominance fraction is in [0, 1]."""
        rng = np.random.default_rng(42)
        static = rng.uniform(0, 1, size=(10, 3))
        state_aware = rng.uniform(0, 1, size=(10, 3))
        comp = compare_pareto_fronts(static, state_aware)
        assert 0.0 <= comp.dominance_fraction <= 1.0

    def test_per_objective_winner(self):
        """Correctly identifies best-extreme pipeline per objective."""
        static = np.array([[1.0, 0.1]])
        state_aware = np.array([[0.1, 1.0]])
        comp = compare_pareto_fronts(
            static, state_aware,
            objective_names=["obj_a", "obj_b"],
        )
        assert comp.per_objective_winner["obj_a"] == "static"
        assert comp.per_objective_winner["obj_b"] == "state_aware"

    def test_dominance_fraction_fully_dominated(self):
        """When state-aware dominates all static front points."""
        static = np.array([[0.3, 0.3], [0.2, 0.4]])
        state_aware = np.array([[0.9, 0.9]])
        comp = compare_pareto_fronts(static, state_aware)
        assert comp.dominance_fraction == 1.0

    def test_dominance_fraction_none_dominated(self):
        """When static front is not dominated at all."""
        static = np.array([[0.9, 0.9]])
        state_aware = np.array([[0.3, 0.3]])
        comp = compare_pareto_fronts(static, state_aware)
        assert comp.dominance_fraction == 0.0


# ══════════════════════════════════════════════════════════════════════
# 5. Visualization tests
# ══════════════════════════════════════════════════════════════════════


class TestVisualization:
    """Tests for Pareto visualization functions."""

    @pytest.fixture
    def sample_comparison(self):
        """Create a sample ParetoComparison for plotting."""
        static = np.random.default_rng(42).uniform(0, 1, size=(15, 4))
        state_aware = np.random.default_rng(43).uniform(0, 1, size=(20, 4))
        return compare_pareto_fronts(
            static, state_aware, objective_names=OBJECTIVE_NAMES,
        )

    def test_pareto_projection_creates_files(self, sample_comparison):
        """6 PNG files created for C(4,2) objective pairs."""
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            pytest.skip("matplotlib not installed")

        from statebind.evaluation.figures import plot_pareto_projections

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = plot_pareto_projections(sample_comparison, save_dir=tmpdir)
            assert len(paths) == 6  # C(4,2) = 6
            for p in paths:
                assert p.exists()
                assert p.suffix == ".png"

    def test_parallel_coordinates_creates_file(self, sample_comparison):
        """One PNG file created."""
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            pytest.skip("matplotlib not installed")

        from statebind.evaluation.figures import plot_parallel_coordinates

        with tempfile.TemporaryDirectory() as tmpdir:
            path = plot_parallel_coordinates(
                sample_comparison,
                save_path=Path(tmpdir) / "pc.png",
            )
            assert path is not None
            assert path.exists()
            assert path.suffix == ".png"

    def test_plots_headless(self, sample_comparison):
        """Works with Agg backend, no display needed."""
        try:
            import matplotlib
            matplotlib.use("Agg")
        except ImportError:
            pytest.skip("matplotlib not installed")

        from statebind.evaluation.figures import (
            plot_parallel_coordinates,
            plot_pareto_projections,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = plot_pareto_projections(sample_comparison, save_dir=tmpdir)
            assert len(paths) > 0
            pc = plot_parallel_coordinates(
                sample_comparison,
                save_path=Path(tmpdir) / "pc.png",
            )
            assert pc is not None

    def test_pareto_summary_ascii(self, sample_comparison):
        """ASCII summary renders without errors."""
        from statebind.evaluation.comparison import ComparativeResult
        from statebind.evaluation.figures import pareto_summary_ascii

        result = ComparativeResult()
        result.pareto = sample_comparison
        text = pareto_summary_ascii(result)
        assert "Pareto Front Analysis" in text
        assert "Hypervolume" in text

    def test_pareto_summary_ascii_no_pareto(self):
        """ASCII summary handles missing Pareto gracefully."""
        from statebind.evaluation.comparison import ComparativeResult
        from statebind.evaluation.figures import pareto_summary_ascii

        result = ComparativeResult()
        text = pareto_summary_ascii(result)
        assert "No Pareto analysis" in text


# ══════════════════════════════════════════════════════════════════════
# 6. Integration tests
# ══════════════════════════════════════════════════════════════════════


class TestIntegration:
    """Integration tests with the broader evaluation pipeline."""

    def test_pareto_in_comparison_result(self):
        """ComparativeResult includes pareto field."""
        from statebind.evaluation.comparison import ComparativeResult

        result = ComparativeResult()
        assert hasattr(result, "pareto")
        assert result.pareto is None

    def test_pareto_serialization(self):
        """ParetoResult and ParetoComparison serialize to JSON."""
        static = np.array([[0.8, 0.2], [0.2, 0.8]])
        state_aware = np.array([[0.9, 0.3], [0.3, 0.9]])
        comp = compare_pareto_fronts(
            static, state_aware,
            objective_names=["sim", "drug"],
        )
        d = comp.to_dict()
        # Must be JSON-serializable
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert "hypervolume_ratio" in parsed
        assert "static_result" in parsed
        assert "state_aware_result" in parsed
        assert isinstance(parsed["static_result"]["front_scores"], list)

    def test_extract_score_matrix(self):
        """extract_score_matrix works with UnifiedScoredCandidate objects."""
        from statebind.ranking.models import (
            PipelineLabel,
            UnifiedScoreComponent,
            UnifiedScoredCandidate,
        )

        candidates = [
            UnifiedScoredCandidate(
                candidate_id="c1",
                smiles="CCO",
                pipeline=PipelineLabel.STATIC,
                scores=[
                    UnifiedScoreComponent(name="reference_similarity", value=0.8),
                    UnifiedScoreComponent(name="druglikeness", value=0.6),
                    UnifiedScoreComponent(name="docking_proxy", value=0.5),
                    UnifiedScoreComponent(name="state_specificity", value=0.0),
                ],
            ),
            UnifiedScoredCandidate(
                candidate_id="c2",
                smiles="CCCO",
                pipeline=PipelineLabel.STATIC,
                scores=[
                    UnifiedScoreComponent(name="reference_similarity", value=0.7),
                    UnifiedScoreComponent(name="druglikeness", value=0.5),
                    UnifiedScoreComponent(name="docking_proxy", value=0.4),
                    UnifiedScoreComponent(name="state_specificity", value=0.0),
                ],
            ),
        ]
        matrix = extract_score_matrix(candidates)
        assert matrix.shape == (2, 4)
        assert matrix[0, 0] == 0.8  # reference_similarity
        assert matrix[1, 2] == 0.4  # docking_proxy

    def test_extract_score_matrix_empty(self):
        """Empty candidate list returns empty matrix."""
        matrix = extract_score_matrix([])
        assert matrix.shape == (0, 4)

    @pytest.mark.skipif(not HAS_PYMOO, reason="pymoo not installed")
    def test_pymoo_hypervolume_consistency(self):
        """pymoo hypervolume matches for simple 2D case."""
        scores = np.array([[0.8, 0.6]])
        ref = [0.0, 0.0]
        result = compute_pareto_front(scores, reference_point=ref)
        expected = 0.8 * 0.6
        assert abs(result.hypervolume - expected) < 0.01

    def test_graceful_without_pymoo(self):
        """Falls back when pymoo is not importable."""
        with patch("statebind.ranking.pareto.HAS_PYMOO", False):
            from statebind.ranking.pareto import _compute_hypervolume

            front = np.array([[0.8, 0.6]])
            ref = np.array([0.0, 0.0])
            hv = _compute_hypervolume(front, ref)
            # Should still compute (via 2D exact or MC)
            assert hv > 0

    def test_pareto_comparison_module(self):
        """evaluation/pareto_comparison.py runs end-to-end with mock data."""
        from statebind.evaluation.pareto_comparison import (
            format_pareto_summary,
            run_pareto_comparison,
        )
        from statebind.ranking.models import (
            MergedRanking,
            PipelineLabel,
            RankedPool,
            UnifiedScoreComponent,
            UnifiedScoredCandidate,
        )

        def _make_candidate(cid, smiles, pipeline, sim, drug, dock, spec):
            return UnifiedScoredCandidate(
                candidate_id=cid,
                smiles=smiles,
                pipeline=pipeline,
                scores=[
                    UnifiedScoreComponent(name="reference_similarity", value=sim),
                    UnifiedScoreComponent(name="druglikeness", value=drug),
                    UnifiedScoreComponent(name="docking_proxy", value=dock),
                    UnifiedScoreComponent(name="state_specificity", value=spec),
                ],
                composite_score=sim * 0.35 + drug * 0.30 + dock * 0.20 + spec * 0.15,
            )

        static_cands = [
            _make_candidate("s1", "CCO", PipelineLabel.STATIC, 0.9, 0.7, 0.5, 0.0),
            _make_candidate("s2", "CCCO", PipelineLabel.STATIC, 0.8, 0.6, 0.4, 0.0),
        ]
        state_cands = [
            _make_candidate("a1", "CCCCO", PipelineLabel.STATE_AWARE, 0.7, 0.8, 0.6, 0.5),
            _make_candidate("a2", "CCCCCO", PipelineLabel.STATE_AWARE, 0.6, 0.7, 0.7, 0.8),
        ]

        merged = MergedRanking(
            static_pool=RankedPool(
                pipeline=PipelineLabel.STATIC, candidates=static_cands,
            ),
            state_aware_pool=RankedPool(
                pipeline=PipelineLabel.STATE_AWARE, candidates=state_cands,
            ),
        )

        comp = run_pareto_comparison(merged)
        assert isinstance(comp, ParetoComparison)
        assert comp.hypervolume_ratio > 0

        summary = format_pareto_summary(comp)
        assert "hypervolume" in summary.lower()
        assert "Static pipeline" in summary

    def test_is_dominated_basic(self):
        """Test basic domination check."""
        a = np.array([0.5, 0.5])
        b = np.array([0.6, 0.6])
        assert _is_dominated(a, b, maximize=True)
        assert not _is_dominated(b, a, maximize=True)

    def test_is_dominated_not_dominated(self):
        """Neither dominates when each is better on one objective."""
        a = np.array([0.8, 0.2])
        b = np.array([0.2, 0.8])
        assert not _is_dominated(a, b, maximize=True)
        assert not _is_dominated(b, a, maximize=True)
