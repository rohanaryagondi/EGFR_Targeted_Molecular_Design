"""Tests for MPNN data preparation, affinity predictor adapter, and scoring integration.

Groups:
  1. Data preparation (4): validate curated compounds, pIC50 range, deduplication
  2. Normalization (4): sigmoid behavior, monotonicity, bounds, known values
  3. Adapter interface (6): predict_affinity fallback, batch, edge cases
  4. Scoring integration (5): cascading fallback, method string, stub fallback
  5. Edge cases (3): long SMILES, disconnected, reset
  6. Dataset splits (6): scaffold, temporal, backward compat, invalid type, no rdkit

Total: ~28 tests.
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


# ── Group 6: Dataset Split Tests ──────────────────────────────────────────


def _make_toy_dataset(n: int = 50, years: list[int] | None = None) -> object:
    """Build a tiny AffinityDataset with *n* molecules for split tests.

    Uses ``pytest.importorskip`` for torch / torch_geometric so the tests
    are cleanly skipped when GPU dependencies are absent.

    Returns an :class:`AffinityDataset` instance (typed as ``object`` so the
    helper itself does not need torch at import time).
    """
    torch = pytest.importorskip("torch")
    pytest.importorskip("torch_geometric")

    from statebind.ml.affinity_dataset import AffinityDataset
    from statebind.ml.graphs import smiles_to_graph

    # A pool of small, parseable SMILES covering diverse scaffolds
    _smiles_pool = [
        "c1ccccc1",          # benzene
        "c1ccc(O)cc1",       # phenol
        "c1ccc(N)cc1",       # aniline
        "c1ccc2ccccc2c1",    # naphthalene
        "C1CCCCC1",          # cyclohexane
        "c1ccncc1",          # pyridine
        "c1ccc(CC)cc1",      # ethylbenzene
        "c1ccoc1",           # furan
        "c1ccsc1",           # thiophene
        "c1cc[nH]c1",        # pyrrole
        "CCO",               # ethanol
        "CCCC",              # butane
        "CC(=O)O",           # acetic acid
        "CC(=O)N",           # acetamide
        "c1ccc(-c2ccccc2)cc1",  # biphenyl
    ]

    graphs = []
    smiles_list = []
    for i in range(n):
        smi = _smiles_pool[i % len(_smiles_pool)]
        g = smiles_to_graph(smi)
        if g is None:
            continue
        g.y = torch.tensor([5.0 + (i % 10) * 0.3], dtype=torch.float)
        graphs.append(g)
        smiles_list.append(smi)

    return AffinityDataset(
        graphs=graphs,
        smiles_list=smiles_list,
        years=years,
    )


class TestDatasetSplits:
    """Tests for scaffold_split, temporal_split, and split_dataset dispatch."""

    # -- a. scaffold_split: non-overlapping scaffolds between splits ----------

    def test_scaffold_split_no_scaffold_overlap(self) -> None:
        """Train and test sets must not share any Murcko scaffold."""
        pytest.importorskip("torch")
        pytest.importorskip("torch_geometric")
        rdkit_chem = pytest.importorskip("rdkit.Chem")

        from rdkit.Chem.Scaffolds.MurckoScaffold import (  # noqa: E402
            GetScaffoldForMol,
            MakeScaffoldGeneric,
        )

        from statebind.ml.affinity_dataset import scaffold_split

        ds = _make_toy_dataset(50)
        train_ds, val_ds, test_ds = scaffold_split(ds, seed=42)

        def _scaffolds(smiles_list: list[str]) -> set[str]:
            scaffolds: set[str] = set()
            for smi in smiles_list:
                mol = rdkit_chem.MolFromSmiles(smi)
                if mol is None:
                    continue
                core = GetScaffoldForMol(mol)
                generic = MakeScaffoldGeneric(core)
                scaffolds.add(rdkit_chem.MolToSmiles(generic))
            return scaffolds

        train_scaff = _scaffolds(train_ds.smiles_list)
        test_scaff = _scaffolds(test_ds.smiles_list)
        overlap = train_scaff & test_scaff
        assert overlap == set(), (
            f"Scaffold overlap between train and test: {overlap}"
        )

    # -- b. scaffold_split: approximate ratios (within 20%) ------------------

    def test_scaffold_split_approximate_ratios(self) -> None:
        """Split sizes should be within 20% of the target ratios."""
        pytest.importorskip("torch")
        pytest.importorskip("torch_geometric")
        pytest.importorskip("rdkit")

        from statebind.ml.affinity_dataset import scaffold_split

        ds = _make_toy_dataset(100)
        n = len(ds)
        train_ds, val_ds, test_ds = scaffold_split(
            ds, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42,
        )

        # All molecules must be accounted for
        assert len(train_ds) + len(val_ds) + len(test_ds) == n

        # Ratios within 20% of target
        assert abs(len(train_ds) / n - 0.8) < 0.20, (
            f"Train ratio {len(train_ds)/n:.2f} too far from 0.8"
        )
        assert abs(len(val_ds) / n - 0.1) < 0.20, (
            f"Val ratio {len(val_ds)/n:.2f} too far from 0.1"
        )
        assert abs(len(test_ds) / n - 0.1) < 0.20, (
            f"Test ratio {len(test_ds)/n:.2f} too far from 0.1"
        )

    # -- c. temporal_split: test set has latest years ------------------------

    def test_temporal_split_order(self) -> None:
        """Test set must contain the latest years."""
        pytest.importorskip("torch")
        pytest.importorskip("torch_geometric")

        from statebind.ml.affinity_dataset import temporal_split

        years = [2000 + i for i in range(50)]  # 2000..2049
        ds = _make_toy_dataset(50, years=years)
        train_ds, val_ds, test_ds = temporal_split(ds)

        # Test set years should all be >= max(train years)
        if train_ds.years and test_ds.years:
            assert min(test_ds.years) >= max(train_ds.years), (
                "Test set contains years older than training set"
            )
        # Val years should be between train and test
        if val_ds.years and train_ds.years:
            assert min(val_ds.years) >= max(train_ds.years), (
                "Val set contains years older than training set"
            )

    # -- d. backward compat: random split unchanged --------------------------

    def test_random_split_backward_compat(self) -> None:
        """split_dataset(ds, split_type='random') matches old behaviour."""
        pytest.importorskip("torch")
        pytest.importorskip("torch_geometric")

        from statebind.ml.affinity_dataset import split_dataset

        ds = _make_toy_dataset(50)
        train_a, val_a, test_a = split_dataset(ds, seed=42)
        train_b, val_b, test_b = split_dataset(
            ds, seed=42, split_type="random",
        )

        assert train_a.smiles_list == train_b.smiles_list
        assert val_a.smiles_list == val_b.smiles_list
        assert test_a.smiles_list == test_b.smiles_list

    # -- e. invalid split_type raises ValueError -----------------------------

    def test_invalid_split_type_raises(self) -> None:
        """Unknown split_type must raise ValueError."""
        pytest.importorskip("torch")
        pytest.importorskip("torch_geometric")

        from statebind.ml.affinity_dataset import split_dataset

        ds = _make_toy_dataset(20)
        with pytest.raises(ValueError, match="Unknown split_type"):
            split_dataset(ds, split_type="nonexistent")

    # -- f. scaffold_split without RDKit raises ImportError -------------------

    def test_scaffold_split_no_rdkit_raises(self) -> None:
        """scaffold_split must raise ImportError when RDKit is missing."""
        pytest.importorskip("torch")
        pytest.importorskip("torch_geometric")

        import statebind.ml.affinity_dataset as ad_mod
        from statebind.ml.affinity_dataset import scaffold_split

        ds = _make_toy_dataset(20)
        original = ad_mod.HAS_SCAFFOLD
        try:
            ad_mod.HAS_SCAFFOLD = False
            with pytest.raises(ImportError, match="scaffold_split requires RDKit"):
                scaffold_split(ds, seed=42)
        finally:
            ad_mod.HAS_SCAFFOLD = original

    # -- g. temporal_split without years raises ValueError -------------------

    def test_temporal_split_no_years_raises(self) -> None:
        """temporal_split must raise ValueError when years is None."""
        pytest.importorskip("torch")
        pytest.importorskip("torch_geometric")

        from statebind.ml.affinity_dataset import temporal_split

        ds = _make_toy_dataset(20)  # no years
        with pytest.raises(ValueError, match="dataset.years"):
            temporal_split(ds)
