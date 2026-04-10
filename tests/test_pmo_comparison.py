"""Tests for PMO compute-matched comparison infrastructure.

Covers:
- OracleBudget: call tracking, budget exhaustion, remaining count
- PMOResult and OracleBudget: Pydantic serialization round-trips
- AUC curve accumulation and area computation
- prefilter_score: cheap scoring without GNINA
- run_pipeline_with_budget: end-to-end with mock docking
- compare_pmo: delta metrics and winner determination
- Edge cases: empty candidates, budget=1, tie detection
"""

from __future__ import annotations

import json

import pytest

from statebind.evaluation.pmo_comparison import (
    AUCPoint,
    OracleBudget,
    OracleCall,
    PMOComparison,
    PMOResult,
    _compute_auc_area,
    _compute_auc_curve,
    compare_pmo,
    format_comparison_table,
    prefilter_score,
    run_pipeline_with_budget,
)


# ═══════════════════════════════════════════════════════════════════════════
# OracleBudget tests
# ═══════════════════════════════════════════════════════════════════════════


class TestOracleBudget:
    """Tests for oracle budget tracking."""

    def test_initial_state(self) -> None:
        """Fresh budget has zero calls used and full remaining."""
        budget = OracleBudget(total_budget=10)
        assert budget.calls_used == 0
        assert budget.remaining == 10
        assert not budget.is_exhausted
        assert budget.results == []

    def test_record_call_tracks_correctly(self) -> None:
        """Each record_call increments calls_used and appends result."""
        budget = OracleBudget(total_budget=10)
        budget.record_call("CCO", 0.75)
        assert budget.calls_used == 1
        assert budget.remaining == 9
        assert len(budget.results) == 1
        assert budget.results[0].smiles == "CCO"
        assert budget.results[0].score == 0.75
        assert budget.results[0].rank_at_call == 1

    def test_multiple_calls(self) -> None:
        """Multiple calls track in order."""
        budget = OracleBudget(total_budget=5)
        budget.record_call("CCO", 0.5)
        budget.record_call("c1ccccc1", 0.8)
        budget.record_call("CC(=O)O", 0.3)
        assert budget.calls_used == 3
        assert budget.remaining == 2
        assert budget.results[2].rank_at_call == 3

    def test_budget_exhaustion_raises(self) -> None:
        """Recording a call after budget exhaustion raises RuntimeError."""
        budget = OracleBudget(total_budget=2)
        budget.record_call("CCO", 0.5)
        budget.record_call("c1ccccc1", 0.8)
        assert budget.is_exhausted
        assert budget.remaining == 0
        with pytest.raises(RuntimeError, match="Oracle budget exhausted"):
            budget.record_call("CC", 0.1)

    def test_budget_of_one(self) -> None:
        """Budget=1 allows exactly one call."""
        budget = OracleBudget(total_budget=1)
        budget.record_call("CCO", 0.5)
        assert budget.is_exhausted
        with pytest.raises(RuntimeError):
            budget.record_call("CC", 0.1)

    def test_score_rounding(self) -> None:
        """Scores are rounded to 4 decimal places."""
        budget = OracleBudget(total_budget=10)
        budget.record_call("CCO", 0.123456789)
        assert budget.results[0].score == 0.1235

    def test_serialization_roundtrip(self) -> None:
        """OracleBudget survives JSON serialization round-trip."""
        budget = OracleBudget(total_budget=5)
        budget.record_call("CCO", 0.75)
        budget.record_call("c1ccccc1", 0.82)

        data = budget.model_dump(mode="json")
        restored = OracleBudget.model_validate(data)
        assert restored.total_budget == 5
        assert restored.calls_used == 2
        assert len(restored.results) == 2
        assert restored.results[0].smiles == "CCO"


# ═══════════════════════════════════════════════════════════════════════════
# PMOResult serialization
# ═══════════════════════════════════════════════════════════════════════════


class TestPMOResultSerialization:
    """Tests for PMOResult Pydantic model."""

    def test_json_roundtrip(self) -> None:
        """PMOResult survives JSON dump and reload."""
        result = PMOResult(
            pipeline="static",
            budget=100,
            calls_used=50,
            top_10_avg_score=0.7234,
            auc_curve=[
                AUCPoint(oracle_calls=10, top_10_avg=0.5),
                AUCPoint(oracle_calls=20, top_10_avg=0.65),
            ],
            all_scores=[
                OracleCall(smiles="CCO", score=0.5, rank_at_call=1),
            ],
            generated_at="2025-01-01T00:00:00+00:00",
            notes="test",
        )
        json_str = json.dumps(result.model_dump(mode="json"), default=str)
        data = json.loads(json_str)
        restored = PMOResult.model_validate(data)
        assert restored.pipeline == "static"
        assert restored.budget == 100
        assert restored.calls_used == 50
        assert restored.top_10_avg_score == 0.7234
        assert len(restored.auc_curve) == 2
        assert restored.auc_curve[0].oracle_calls == 10

    def test_default_values(self) -> None:
        """PMOResult defaults are sensible."""
        result = PMOResult(
            pipeline="state_aware", budget=500, calls_used=0,
            top_10_avg_score=0.0,
        )
        assert result.ef_at_10 is None
        assert result.bedroc is None
        assert result.auc_curve == []
        assert result.prefilter_stats == {}


class TestPMOComparisonSerialization:
    """Tests for PMOComparison Pydantic model."""

    def test_json_roundtrip(self) -> None:
        """PMOComparison survives JSON serialization."""
        sr = PMOResult(
            pipeline="static", budget=100, calls_used=100,
            top_10_avg_score=0.6,
        )
        sar = PMOResult(
            pipeline="state_aware", budget=100, calls_used=100,
            top_10_avg_score=0.7,
        )
        comp = PMOComparison(
            static_result=sr,
            state_aware_result=sar,
            budget=100,
            top_10_delta=0.1,
            auc_delta=5.0,
            winner="state_aware",
        )
        data = comp.model_dump(mode="json")
        json_str = json.dumps(data, default=str)
        restored = PMOComparison.model_validate(json.loads(json_str))
        assert restored.winner == "state_aware"
        assert restored.budget == 100
        assert restored.top_10_delta == 0.1


# ═══════════════════════════════════════════════════════════════════════════
# AUC curve tests
# ═══════════════════════════════════════════════════════════════════════════


class TestAUCCurve:
    """Tests for AUC curve computation."""

    def test_empty_results(self) -> None:
        """Empty results produce empty curve."""
        curve = _compute_auc_curve([])
        assert curve == []

    def test_single_call(self) -> None:
        """Single call produces one AUC point."""
        results = [OracleCall(smiles="CCO", score=0.5, rank_at_call=1)]
        curve = _compute_auc_curve(results, sample_interval=1)
        assert len(curve) == 1
        assert curve[0].oracle_calls == 1
        assert curve[0].top_10_avg == 0.5

    def test_accumulation(self) -> None:
        """Top-10 avg improves as better molecules are found."""
        results = [
            OracleCall(smiles=f"C{'C' * i}", score=0.1 * (i + 1), rank_at_call=i + 1)
            for i in range(20)
        ]
        curve = _compute_auc_curve(results, sample_interval=5)
        # Should have points at 5, 10, 15, 20
        assert len(curve) == 4
        # Later points should have higher top-10 averages
        assert curve[-1].top_10_avg >= curve[0].top_10_avg

    def test_sample_interval(self) -> None:
        """Curve samples at correct intervals."""
        results = [
            OracleCall(smiles=f"C{'C' * i}", score=0.5, rank_at_call=i + 1)
            for i in range(25)
        ]
        curve = _compute_auc_curve(results, sample_interval=10)
        # Points at 10, 20, 25 (final)
        assert len(curve) == 3
        assert curve[0].oracle_calls == 10
        assert curve[1].oracle_calls == 20
        assert curve[2].oracle_calls == 25

    def test_auc_area_empty(self) -> None:
        """Empty or single-point curve has zero area."""
        assert _compute_auc_area([]) == 0.0
        assert _compute_auc_area([AUCPoint(oracle_calls=1, top_10_avg=0.5)]) == 0.0

    def test_auc_area_constant(self) -> None:
        """Constant curve: area = width * height."""
        curve = [
            AUCPoint(oracle_calls=0, top_10_avg=0.5),
            AUCPoint(oracle_calls=100, top_10_avg=0.5),
        ]
        area = _compute_auc_area(curve)
        assert area == 50.0  # 100 * 0.5

    def test_auc_area_increasing(self) -> None:
        """Increasing curve: area by trapezoidal rule."""
        curve = [
            AUCPoint(oracle_calls=0, top_10_avg=0.0),
            AUCPoint(oracle_calls=100, top_10_avg=1.0),
        ]
        area = _compute_auc_area(curve)
        assert area == 50.0  # trapezoid: (0 + 1) / 2 * 100


# ═══════════════════════════════════════════════════════════════════════════
# Pre-filter scoring
# ═══════════════════════════════════════════════════════════════════════════


class TestPrefilterScore:
    """Tests for cheap pre-filter scoring (no GNINA)."""

    def test_empty_smiles(self) -> None:
        """Empty SMILES returns 0."""
        assert prefilter_score("") == 0.0

    def test_valid_molecule(self) -> None:
        """Valid molecule produces a score in [0, 1]."""
        score = prefilter_score("c1ccccc1")  # benzene
        assert 0.0 <= score <= 1.0

    def test_known_binder_scores_high(self) -> None:
        """Erlotinib (reference binder) should score high."""
        erlotinib = "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC"
        score = prefilter_score(erlotinib)
        # Should be high because similarity to itself is 1.0
        assert score > 0.5

    def test_deterministic(self) -> None:
        """Same input always produces same score."""
        s1 = prefilter_score("CCO")
        s2 = prefilter_score("CCO")
        assert s1 == s2

    def test_score_rounded(self) -> None:
        """Score is rounded to 4 decimal places."""
        score = prefilter_score("c1ccccc1")
        assert score == round(score, 4)


# ═══════════════════════════════════════════════════════════════════════════
# run_pipeline_with_budget
# ═══════════════════════════════════════════════════════════════════════════


def _mock_dock_fn(smiles: str) -> float:
    """Deterministic mock docking: longer SMILES score higher."""
    return round(min(len(smiles) / 50.0, 1.0), 4)


class TestRunPipelineWithBudget:
    """Tests for budget-limited pipeline execution."""

    def test_basic_execution(self) -> None:
        """Pipeline runs and returns a valid PMOResult."""
        candidates = ["CCO", "c1ccccc1", "CC(=O)O", "CCCCCC", "c1ccncc1"]
        result = run_pipeline_with_budget(
            pipeline_label="static",
            budget=3,
            candidates=candidates,
            dock_fn=_mock_dock_fn,
            sample_interval=1,
        )
        assert result.pipeline == "static"
        assert result.budget == 3
        assert result.calls_used == 3
        assert 0.0 <= result.top_10_avg_score <= 1.0
        assert len(result.auc_curve) > 0
        assert len(result.all_scores) == 3

    def test_budget_respected(self) -> None:
        """No more than budget calls are made."""
        candidates = [f"C{'C' * i}" for i in range(100)]
        result = run_pipeline_with_budget(
            pipeline_label="test",
            budget=10,
            candidates=candidates,
            dock_fn=_mock_dock_fn,
        )
        assert result.calls_used <= 10

    def test_fewer_candidates_than_budget(self) -> None:
        """When candidates < budget, dock all candidates."""
        candidates = ["CCO", "c1ccccc1"]
        result = run_pipeline_with_budget(
            pipeline_label="test",
            budget=100,
            candidates=candidates,
            dock_fn=_mock_dock_fn,
        )
        assert result.calls_used == 2

    def test_duplicate_candidates_deduplicated(self) -> None:
        """Duplicate SMILES are removed before docking."""
        candidates = ["CCO", "CCO", "CCO", "c1ccccc1"]
        result = run_pipeline_with_budget(
            pipeline_label="test",
            budget=10,
            candidates=candidates,
            dock_fn=_mock_dock_fn,
        )
        # Only 2 unique candidates
        assert result.calls_used == 2
        assert result.prefilter_stats["n_candidates_input"] == 4
        assert result.prefilter_stats["n_candidates_unique"] == 2

    def test_invalid_budget_raises(self) -> None:
        """Budget < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Budget must be >= 1"):
            run_pipeline_with_budget(
                pipeline_label="test",
                budget=0,
                candidates=["CCO"],
                dock_fn=_mock_dock_fn,
            )

    def test_empty_candidates_raises(self) -> None:
        """Empty candidate list raises ValueError."""
        with pytest.raises(ValueError, match="No candidates"):
            run_pipeline_with_budget(
                pipeline_label="test",
                budget=10,
                candidates=[],
                dock_fn=_mock_dock_fn,
            )

    def test_prefilter_stats_populated(self) -> None:
        """Pre-filter statistics are present in result."""
        candidates = ["CCO", "c1ccccc1", "CC(=O)O"]
        result = run_pipeline_with_budget(
            pipeline_label="test",
            budget=2,
            candidates=candidates,
            dock_fn=_mock_dock_fn,
        )
        stats = result.prefilter_stats
        assert "n_candidates_input" in stats
        assert "n_candidates_unique" in stats
        assert "n_docked" in stats
        assert stats["n_docked"] == 2

    def test_failed_dock_records_zero(self) -> None:
        """A docking function that raises records score=0."""
        call_count = 0

        def failing_dock(smiles: str) -> float:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Simulated docking failure")
            return 0.5

        candidates = ["CCO", "c1ccccc1", "CC(=O)O"]
        result = run_pipeline_with_budget(
            pipeline_label="test",
            budget=3,
            candidates=candidates,
            dock_fn=failing_dock,
        )
        # All 3 should be recorded (failed one gets 0.0)
        assert result.calls_used == 3
        scores = [r.score for r in result.all_scores]
        assert 0.0 in scores


# ═══════════════════════════════════════════════════════════════════════════
# compare_pmo
# ═══════════════════════════════════════════════════════════════════════════


class TestComparePMO:
    """Tests for PMO comparison logic."""

    @pytest.fixture()
    def static_result(self) -> PMOResult:
        return PMOResult(
            pipeline="static",
            budget=100,
            calls_used=100,
            top_10_avg_score=0.6,
            auc_curve=[
                AUCPoint(oracle_calls=0, top_10_avg=0.3),
                AUCPoint(oracle_calls=50, top_10_avg=0.5),
                AUCPoint(oracle_calls=100, top_10_avg=0.6),
            ],
        )

    @pytest.fixture()
    def sa_result(self) -> PMOResult:
        return PMOResult(
            pipeline="state_aware",
            budget=100,
            calls_used=100,
            top_10_avg_score=0.75,
            auc_curve=[
                AUCPoint(oracle_calls=0, top_10_avg=0.4),
                AUCPoint(oracle_calls=50, top_10_avg=0.65),
                AUCPoint(oracle_calls=100, top_10_avg=0.75),
            ],
        )

    def test_state_aware_wins(
        self, static_result: PMOResult, sa_result: PMOResult,
    ) -> None:
        """State-aware with higher top-10 wins."""
        comp = compare_pmo(static_result, sa_result)
        assert comp.winner == "state_aware"
        assert comp.top_10_delta > 0
        assert comp.budget == 100

    def test_static_wins(self, sa_result: PMOResult) -> None:
        """Static with higher top-10 wins."""
        static_better = PMOResult(
            pipeline="static",
            budget=100,
            calls_used=100,
            top_10_avg_score=0.9,
            auc_curve=[
                AUCPoint(oracle_calls=0, top_10_avg=0.5),
                AUCPoint(oracle_calls=100, top_10_avg=0.9),
            ],
        )
        comp = compare_pmo(static_better, sa_result)
        assert comp.winner == "static"
        assert comp.top_10_delta < 0

    def test_tie_detection(self) -> None:
        """Nearly equal top-10 scores produce a tie."""
        sr = PMOResult(
            pipeline="static", budget=100, calls_used=100,
            top_10_avg_score=0.7000,
        )
        sar = PMOResult(
            pipeline="state_aware", budget=100, calls_used=100,
            top_10_avg_score=0.7005,  # within 0.001 tolerance
        )
        comp = compare_pmo(sr, sar)
        assert comp.winner == "tie"

    def test_auc_delta_computed(
        self, static_result: PMOResult, sa_result: PMOResult,
    ) -> None:
        """AUC delta is state_aware - static."""
        comp = compare_pmo(static_result, sa_result)
        # sa_result has higher AUC, so delta should be positive
        assert comp.auc_delta > 0

    def test_comparison_serialization(
        self, static_result: PMOResult, sa_result: PMOResult,
    ) -> None:
        """Comparison result survives JSON round-trip."""
        comp = compare_pmo(static_result, sa_result)
        data = comp.model_dump(mode="json")
        json_str = json.dumps(data, default=str)
        restored = PMOComparison.model_validate(json.loads(json_str))
        assert restored.winner == comp.winner
        assert restored.top_10_delta == comp.top_10_delta


# ═══════════════════════════════════════════════════════════════════════════
# Format comparison table
# ═══════════════════════════════════════════════════════════════════════════


class TestFormatComparisonTable:
    """Tests for human-readable output formatting."""

    def test_produces_string(self) -> None:
        """format_comparison_table returns a non-empty string."""
        sr = PMOResult(
            pipeline="static", budget=100, calls_used=100,
            top_10_avg_score=0.6,
            prefilter_stats={"n_candidates_unique": 30},
        )
        sar = PMOResult(
            pipeline="state_aware", budget=100, calls_used=100,
            top_10_avg_score=0.7,
            prefilter_stats={"n_candidates_unique": 200},
        )
        comp = compare_pmo(sr, sar)
        table = format_comparison_table(comp)
        assert isinstance(table, str)
        assert "PMO" in table
        assert "Static" in table
        assert "State-Aware" in table

    def test_contains_budget(self) -> None:
        """Table mentions the oracle budget."""
        sr = PMOResult(
            pipeline="static", budget=500, calls_used=500,
            top_10_avg_score=0.5,
        )
        sar = PMOResult(
            pipeline="state_aware", budget=500, calls_used=500,
            top_10_avg_score=0.5,
        )
        comp = compare_pmo(sr, sar)
        table = format_comparison_table(comp)
        assert "500" in table
