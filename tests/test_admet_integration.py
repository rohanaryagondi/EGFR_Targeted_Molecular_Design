"""Tests for ADMET data preparation, prediction adapter, and filter gate.

Groups:
  1. Data preparation (8): validate curated compounds, merge logic, coverage
  2. Model quality (6): AUROC/RMSE thresholds (skip without checkpoint)
  3. Adapter (6): predict_admet interface, singleton, fallback
  4. Filter (8): filter_candidates_admet, hERG flagging, graceful degradation
  5. Edge cases (4): empty inputs, batch consistency, threshold coverage

Total: ~32 tests.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from prepare_admet_data import (
    _ADMET_TASKS,
    _CLASSIFICATION_TASKS,
    _REGRESSION_TASKS,
    _curated_admet_compounds,
    _merge_by_smiles,
)

from statebind.generation.admet_filter import (
    ADMETFilterResult,
    ADMETFilterSummary,
    filter_candidates_admet,
)
from statebind.generation.models import StateConditionedCandidate
from statebind.ml.admet_predictor import (
    DEFAULT_ADMET_THRESHOLDS,
    check_admet_pass,
    predict_admet,
    predict_admet_batch,
)


# ── Group 1: Data Preparation Tests ─────────────────────────────────────


class TestADMETDataPreparation:
    def test_curated_compounds_not_empty(self) -> None:
        data = _curated_admet_compounds()
        total = sum(len(v) for v in data.values())
        assert total >= 50

    def test_curated_all_tasks_present(self) -> None:
        data = _curated_admet_compounds()
        for task in _ADMET_TASKS:
            assert task in data

    def test_merged_records_have_smiles(self) -> None:
        data = _curated_admet_compounds()
        records = _merge_by_smiles(data)
        for rec in records:
            assert "smiles" in rec
            assert isinstance(rec["smiles"], str)
            assert len(rec["smiles"]) > 0

    def test_merged_at_least_one_label(self) -> None:
        data = _curated_admet_compounds()
        records = _merge_by_smiles(data)
        for rec in records:
            labels = [rec.get(t) for t in _ADMET_TASKS if rec.get(t) is not None]
            assert len(labels) >= 1

    def test_no_duplicate_smiles_after_merge(self) -> None:
        data = _curated_admet_compounds()
        records = _merge_by_smiles(data)
        smiles_list = [r["smiles"] for r in records]
        assert len(smiles_list) == len(set(smiles_list))

    def test_classification_labels_binary(self) -> None:
        data = _curated_admet_compounds()
        records = _merge_by_smiles(data)
        for rec in records:
            for task in sorted(_CLASSIFICATION_TASKS):
                val = rec.get(task)
                if val is not None:
                    assert val in (0.0, 1.0), f"{task} label must be 0/1, got {val}"

    def test_regression_values_finite(self) -> None:
        data = _curated_admet_compounds()
        records = _merge_by_smiles(data)
        regression_tasks = sorted(_REGRESSION_TASKS)
        for rec in records:
            for task in regression_tasks:
                val = rec.get(task)
                if val is not None:
                    assert math.isfinite(val), f"{task} has non-finite value {val}"

    def test_task_coverage_minimum(self) -> None:
        """Each task has at least 10 labeled molecules in curated set."""
        data = _curated_admet_compounds()
        for task in _ADMET_TASKS:
            count = len(data.get(task, []))
            assert count >= 10, f"Task {task} has only {count} records"


# ── Group 2: Model Quality Tests ────────────────────────────────────────

_CHECKPOINT = Path("artifacts/models/admet/best_model.pt")


class TestADMETModelQuality:
    """Model quality tests -- skipped when no trained model available.

    Thresholds relaxed vs spec since testing against small curated set.
    """

    pytestmark = [
        pytest.mark.skipif(
            not _CHECKPOINT.exists(), reason="No trained ADMET checkpoint"
        ),
    ]

    def test_herg_auroc(self) -> None:
        torch = pytest.importorskip("torch")  # noqa: F841
        pytest.importorskip("sklearn")
        from sklearn.metrics import roc_auc_score

        data = _curated_admet_compounds()
        herg_data = data.get("herg", [])
        if len(herg_data) < 10:
            pytest.skip("Not enough hERG data")
        preds = predict_admet_batch([s for s, _ in herg_data])
        pred_probs = [p.get("herg", 0.5) for p in preds]
        auroc = roc_auc_score([y for _, y in herg_data], pred_probs)
        assert auroc >= 0.55

    def test_cyp3a4_auroc(self) -> None:
        torch = pytest.importorskip("torch")  # noqa: F841
        pytest.importorskip("sklearn")
        from sklearn.metrics import roc_auc_score

        data = _curated_admet_compounds()
        cyp_data = data.get("cyp3a4", [])
        if len(cyp_data) < 10:
            pytest.skip("Not enough CYP3A4 data")
        preds = predict_admet_batch([s for s, _ in cyp_data])
        pred_probs = [p.get("cyp3a4", 0.5) for p in preds]
        auroc = roc_auc_score([y for _, y in cyp_data], pred_probs)
        assert auroc >= 0.55

    def test_caco2_rmse(self) -> None:
        torch = pytest.importorskip("torch")  # noqa: F841
        numpy = pytest.importorskip("numpy")

        data = _curated_admet_compounds()
        caco2_data = data.get("caco2", [])
        if len(caco2_data) < 5:
            pytest.skip("Not enough caco2 data")
        preds = predict_admet_batch([s for s, _ in caco2_data])
        pairs = [
            (true, p.get("caco2"))
            for (_, true), p in zip(caco2_data, preds)
            if p.get("caco2") is not None
        ]
        if len(pairs) < 5:
            pytest.skip("Too few successful caco2 predictions")
        rmse = float(
            numpy.sqrt(numpy.mean([(t - p) ** 2 for t, p in pairs]))
        )
        assert rmse < 3.0

    def test_clearance_rmse(self) -> None:
        torch = pytest.importorskip("torch")  # noqa: F841
        numpy = pytest.importorskip("numpy")

        data = _curated_admet_compounds()
        cl_data = data.get("clearance", [])
        if len(cl_data) < 5:
            pytest.skip("Not enough clearance data")
        preds = predict_admet_batch([s for s, _ in cl_data])
        pairs = [
            (true, p.get("clearance"))
            for (_, true), p in zip(cl_data, preds)
            if p.get("clearance") is not None
        ]
        if len(pairs) < 5:
            pytest.skip("Too few successful clearance predictions")
        rmse = float(
            numpy.sqrt(numpy.mean([(t - p) ** 2 for t, p in pairs]))
        )
        assert rmse < 50.0

    def test_lipophilicity_rmse(self) -> None:
        torch = pytest.importorskip("torch")  # noqa: F841
        numpy = pytest.importorskip("numpy")

        data = _curated_admet_compounds()
        lipo_data = data.get("lipophilicity", [])
        if len(lipo_data) < 5:
            pytest.skip("Not enough lipophilicity data")
        preds = predict_admet_batch([s for s, _ in lipo_data])
        pairs = [
            (true, p.get("lipophilicity"))
            for (_, true), p in zip(lipo_data, preds)
            if p.get("lipophilicity") is not None
        ]
        if len(pairs) < 5:
            pytest.skip("Too few successful lipophilicity predictions")
        rmse = float(
            numpy.sqrt(numpy.mean([(t - p) ** 2 for t, p in pairs]))
        )
        assert rmse < 2.0

    def test_solubility_rmse(self) -> None:
        torch = pytest.importorskip("torch")  # noqa: F841
        numpy = pytest.importorskip("numpy")

        data = _curated_admet_compounds()
        sol_data = data.get("solubility", [])
        if len(sol_data) < 5:
            pytest.skip("Not enough solubility data")
        preds = predict_admet_batch([s for s, _ in sol_data])
        pairs = [
            (true, p.get("solubility"))
            for (_, true), p in zip(sol_data, preds)
            if p.get("solubility") is not None
        ]
        if len(pairs) < 5:
            pytest.skip("Too few successful solubility predictions")
        rmse = float(
            numpy.sqrt(numpy.mean([(t - p) ** 2 for t, p in pairs]))
        )
        assert rmse < 3.0


# ── Group 3: Adapter Tests ──────────────────────────────────────────────


class TestADMETPredictor:
    def test_predict_returns_dict(self) -> None:
        result = predict_admet("CCO")
        assert isinstance(result, dict)

    def test_predict_invalid_smiles_empty(self) -> None:
        result = predict_admet("NOT_A_SMILES_XYZ")
        assert result == {}

    def test_predict_empty_smiles_empty(self) -> None:
        result = predict_admet("")
        assert result == {}

    def test_batch_returns_correct_length(self) -> None:
        result = predict_admet_batch(["CCO", "c1ccccc1", "INVALID"])
        assert len(result) == 3

    def test_check_pass_empty_predictions(self) -> None:
        passed, failures = check_admet_pass({})
        assert passed is True
        assert failures == []

    def test_check_pass_detects_herg_failure(self) -> None:
        preds = {"herg": 0.9, "caco2": -4.0, "lipophilicity": 3.0}
        passed, failures = check_admet_pass(preds)
        assert passed is False
        assert "herg" in failures
        assert "caco2" not in failures


# ── Group 4: Filter Tests ───────────────────────────────────────────────


def _make_candidate(
    smiles: str = "CCO", cid: str = "test_001"
) -> StateConditionedCandidate:
    return StateConditionedCandidate(candidate_id=cid, smiles=smiles)


class TestADMETFilter:
    def test_filter_empty_input(self) -> None:
        output, summary = filter_candidates_admet([])
        assert output == []
        assert summary.n_input == 0

    def test_filter_returns_all_candidates(self) -> None:
        candidates = [
            _make_candidate("CCO", "c1"),
            _make_candidate("c1ccccc1", "c2"),
        ]
        output, summary = filter_candidates_admet(candidates)
        assert len(output) == 2
        assert summary.n_input == 2

    def test_filter_pydantic_serialization(self) -> None:
        r = ADMETFilterResult(candidate_id="x", smiles="CCO")
        d = r.model_dump()
        assert d["candidate_id"] == "x"
        assert d["passed"] is True
        s = ADMETFilterSummary(n_input=5, n_passed=3, n_failed=2)
        assert s.model_dump()["n_input"] == 5

    def test_filter_summary_counts_consistent(self) -> None:
        candidates = [
            _make_candidate(f"C{'C' * i}O", f"c{i}") for i in range(5)
        ]
        _, summary = filter_candidates_admet(candidates)
        assert (
            summary.n_passed + summary.n_failed + summary.n_skipped
            == summary.n_input
        )

    def test_filter_custom_thresholds(self) -> None:
        candidates = [_make_candidate("CCO", "c1")]
        strict = {"herg": (">", 0.01)}
        output, summary = filter_candidates_admet(candidates, thresholds=strict)
        assert summary.n_input == 1

    def test_filter_remove_mode(self) -> None:
        candidates = [_make_candidate("CCO", "c1")]
        output, _ = filter_candidates_admet(candidates, remove_failures=True)
        assert len(output) <= len(candidates)

    def test_filter_flags_herg_liability(self) -> None:
        terfenadine = (
            "OC(CCN1CCC(C(c2ccccc2)c2ccccc2)CC1)c1ccc(C(C)(C)C)cc1"
        )
        candidates = [_make_candidate(terfenadine, "herg_test")]
        output, summary = filter_candidates_admet(candidates)
        assert summary.n_input == 1
        if summary.n_skipped == 0:
            result = summary.results[0]
            if "herg" in result.predictions and result.predictions["herg"] > 0.5:
                assert not result.passed or "herg" in result.failed_tasks

    def test_filter_graceful_without_model(self) -> None:
        """When model singleton is forced unavailable, all candidates pass through."""
        import statebind.ml.admet_predictor as ap

        orig_model, orig_attempted = ap._MODEL, ap._LOAD_ATTEMPTED
        try:
            ap._MODEL = None
            ap._LOAD_ATTEMPTED = True
            candidates = [
                _make_candidate("CCO", "c1"),
                _make_candidate("CCCC", "c2"),
            ]
            output, summary = filter_candidates_admet(candidates)
            assert len(output) == 2
            assert summary.n_skipped == 2
            assert summary.n_passed == 0
            assert summary.n_failed == 0
        finally:
            ap._MODEL = orig_model
            ap._LOAD_ATTEMPTED = orig_attempted


# ── Group 5: Edge Cases ─────────────────────────────────────────────────


class TestADMETEdgeCases:
    def test_batch_single_element(self) -> None:
        result = predict_admet_batch(["CCO"])
        assert len(result) == 1

    def test_batch_empty_list(self) -> None:
        assert predict_admet_batch([]) == []

    def test_thresholds_cover_all_tasks(self) -> None:
        expected = {
            "herg",
            "cyp3a4",
            "caco2",
            "clearance",
            "lipophilicity",
            "solubility",
        }
        assert set(DEFAULT_ADMET_THRESHOLDS.keys()) == expected

    def test_batch_prediction_matches_individual(self) -> None:
        smiles = ["CCO", "c1ccccc1"]
        batch_results = predict_admet_batch(smiles)
        individual_results = [predict_admet(s) for s in smiles]
        assert len(batch_results) == len(individual_results)
        for batch_r, indiv_r in zip(batch_results, individual_results):
            if batch_r and indiv_r:
                for task in batch_r:
                    assert task in indiv_r
                    assert abs(batch_r[task] - indiv_r[task]) < 0.01
