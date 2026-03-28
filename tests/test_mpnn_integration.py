"""Tests for MPNN data preparation, affinity predictor adapter, and scoring integration.

Groups:
  1. Data preparation (4): validate curated compounds, pIC50 range, deduplication
  2. Normalization (4): sigmoid behavior, monotonicity, bounds, known values
  3. Adapter interface (6): predict_affinity fallback, batch, edge cases
  4. Scoring integration (5): cascading fallback, method string, stub fallback
  5. Edge cases (3): long SMILES, disconnected, reset

Total: ~22 tests.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from prepare_mpnn_data import (  # noqa: E402, I001
    _curated_egfr_affinity_compounds,
)

from statebind.ml.affinity_predictor import (  # noqa: E402
    _FALLBACK_SCORE,
    _normalize_pic50,
    predict_affinity,
    predict_affinity_batch,
    reset_singleton,
)
from statebind.ranking.models import PipelineLabel  # noqa: E402
from statebind.ranking.scoring import (  # noqa: E402
    DEFAULT_WEIGHTS,
    score_unified,
)


# ── Group 1: Data Preparation Tests ─────────────────────────────────────


class TestMPNNDataPreparation:
    def test_curated_compounds_not_empty(self) -> None:
        records = _curated_egfr_affinity_compounds()
        assert len(records) >= 50

    def test_data_has_smiles_and_pic50(self) -> None:
        records = _curated_egfr_affinity_compounds()
        for rec in records:
            assert "smiles" in rec, "Record missing 'smiles' key"
            assert "pIC50" in rec, "Record missing 'pIC50' key"
            assert isinstance(rec["smiles"], str)
            assert isinstance(rec["pIC50"], (int, float))
            assert len(rec["smiles"]) > 0

    def test_pic50_range(self) -> None:
        records = _curated_egfr_affinity_compounds()
        for rec in records:
            assert 2.0 <= float(rec["pIC50"]) <= 12.0, (
                f"pIC50 {rec['pIC50']} out of range for {rec['smiles']}"
            )

    def test_no_duplicate_smiles(self) -> None:
        records = _curated_egfr_affinity_compounds()
        smiles_list = [r["smiles"] for r in records]
        assert len(smiles_list) == len(set(smiles_list)), (
            "Duplicate SMILES found in curated dataset"
        )


# ── Group 2: Normalization Tests ────────────────────────────────────────


class TestNormalizePIC50:
    def test_normalize_pic50_at_5(self) -> None:
        result = _normalize_pic50(5.0)
        assert abs(result - 0.5) < 1e-10

    def test_normalize_pic50_monotonic(self) -> None:
        low = _normalize_pic50(3.0)
        mid = _normalize_pic50(5.0)
        high = _normalize_pic50(7.0)
        very_high = _normalize_pic50(9.0)
        assert low < mid < high < very_high

    def test_normalize_pic50_bounded(self) -> None:
        for val in [-10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0]:
            result = _normalize_pic50(val)
            assert 0.0 < result < 1.0, (
                f"_normalize_pic50({val}) = {result}, not in (0, 1)"
            )

    def test_normalize_pic50_known_values(self) -> None:
        # pIC50=7 (100 nM) -> ~0.731
        val7 = _normalize_pic50(7.0)
        expected7 = 1.0 / (1.0 + math.exp(-(7.0 - 5.0) / 2.0))
        assert abs(val7 - expected7) < 1e-10
        assert abs(val7 - 0.7310585786) < 1e-4

        # pIC50=9 (1 nM) -> ~0.881
        val9 = _normalize_pic50(9.0)
        expected9 = 1.0 / (1.0 + math.exp(-(9.0 - 5.0) / 2.0))
        assert abs(val9 - expected9) < 1e-10
        assert abs(val9 - 0.8807970780) < 1e-4


# ── Group 3: Adapter Interface Tests ────────────────────────────────────


class TestAffinityPredictorAdapter:
    """Test predict_affinity fallback behavior (no trained model needed)."""

    def setup_method(self) -> None:
        reset_singleton()

    def teardown_method(self) -> None:
        reset_singleton()

    def test_predict_affinity_returns_float(self) -> None:
        result = predict_affinity("CCO")
        assert isinstance(result, float)

    def test_predict_affinity_range(self) -> None:
        result = predict_affinity("CCO")
        assert 0.0 <= result <= 1.0

    def test_predict_affinity_invalid_smiles(self) -> None:
        result = predict_affinity("NOT_A_VALID_SMILES_STRING")
        assert result == _FALLBACK_SCORE

    def test_predict_affinity_empty_string(self) -> None:
        result = predict_affinity("")
        assert result == _FALLBACK_SCORE

    def test_batch_returns_correct_length(self) -> None:
        smiles_list = ["CCO", "c1ccccc1", "CC(=O)O"]
        results = predict_affinity_batch(smiles_list)
        assert len(results) == 3
        for r in results:
            assert isinstance(r, float)
            assert 0.0 <= r <= 1.0

    def test_batch_empty_list(self) -> None:
        results = predict_affinity_batch([])
        assert results == []


# ── Group 4: Scoring Integration Tests ──────────────────────────────────


class TestScoringIntegration:
    def test_scoring_produces_docking_component(self) -> None:
        components, composite = score_unified(
            "CCO", "", PipelineLabel.STATIC, {}
        )
        docking = [c for c in components if c.name == "docking_proxy"]
        assert len(docking) == 1
        assert 0.0 <= docking[0].value <= 1.0

    def test_scoring_method_string_reflects_backend(self) -> None:
        components, _ = score_unified(
            "CCO", "", PipelineLabel.STATIC, {}
        )
        docking = [c for c in components if c.name == "docking_proxy"][0]
        # Method string should describe what backend is active
        assert isinstance(docking.method, str)
        assert len(docking.method) > 0

    def test_scoring_fallback_to_stub(self) -> None:
        """Verify stub fallback when MPNN is unavailable.

        Monkey-patches the affinity_predictor singleton to simulate
        a failed model load, then checks that scoring falls through
        to DockingProxy or stub.
        """
        import statebind.ml.affinity_predictor as ap

        orig = (ap._MODEL, ap._DEVICE, ap._LOAD_ATTEMPTED)
        try:
            ap._MODEL = None
            ap._DEVICE = None
            ap._LOAD_ATTEMPTED = True  # prevent reload attempts

            components, _ = score_unified(
                "CCO", "", PipelineLabel.STATIC, {}
            )
            docking = [c for c in components if c.name == "docking_proxy"][0]

            # Without MPNN, should fall through to proxy or stub
            # If RDKit is available, DockingProxy handles it (is_stub=False)
            # If no RDKit, falls to stub (is_stub=True, value=0.5)
            from statebind.baselines.scoring import _has_rdkit

            if _has_rdkit():
                assert docking.is_stub is False
            else:
                assert docking.is_stub is True
                assert docking.value == 0.5
        finally:
            ap._MODEL, ap._DEVICE, ap._LOAD_ATTEMPTED = orig

    def test_docking_component_weight(self) -> None:
        components, _ = score_unified(
            "CCO", "", PipelineLabel.STATIC, {}
        )
        docking = [c for c in components if c.name == "docking_proxy"][0]
        assert docking.weight == DEFAULT_WEIGHTS["docking_proxy"]

    def test_batch_prediction_consistent(self) -> None:
        """Batch prediction should match individual predictions."""
        reset_singleton()
        smiles_list = ["CCO", "c1ccccc1", "CC(=O)O"]
        batch_results = predict_affinity_batch(smiles_list)

        reset_singleton()
        individual_results = [predict_affinity(s) for s in smiles_list]

        for batch_val, ind_val in zip(batch_results, individual_results):
            assert abs(batch_val - ind_val) < 1e-6


# ── Group 5: Edge Cases ─────────────────────────────────────────────────


class TestEdgeCases:
    def setup_method(self) -> None:
        reset_singleton()

    def teardown_method(self) -> None:
        reset_singleton()

    def test_predict_affinity_very_long_smiles(self) -> None:
        # Polymer-like SMILES > 500 chars
        long_smiles = "C" * 600
        result = predict_affinity(long_smiles)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_predict_affinity_disconnected(self) -> None:
        # Salt: disconnected SMILES
        result = predict_affinity("[Na+].[Cl-]")
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_reset_singleton(self) -> None:
        import statebind.ml.affinity_predictor as ap

        # Force a load attempt
        predict_affinity("CCO")
        assert ap._LOAD_ATTEMPTED is True

        # Reset
        reset_singleton()
        assert ap._MODEL is None
        assert ap._DEVICE is None
        assert ap._LOAD_ATTEMPTED is False
