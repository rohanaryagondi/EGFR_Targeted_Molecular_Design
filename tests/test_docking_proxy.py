"""Tests for the learned EGFR docking proxy.

Covers:
- Training data validation (labels, SMILES, counts)
- Model behavior (output range, loss, discrimination, AUROC, batch)
- Singleton pattern (get_default_proxy)
- Fallback behavior (no RDKit)
- Performance (training time)
"""

from __future__ import annotations

import time
from unittest.mock import patch

import numpy as np
import pytest

from statebind.chemistry.docking_data import (
    DECOYS,
    EGFR_BINDERS,
    TrainingCompound,
    get_training_data,
)
from statebind.chemistry.docking_proxy import (
    DockingProxy,
    _has_rdkit,
    get_default_proxy,
)

_HAS_RDKIT = _has_rdkit()


# ── Helpers ───────────────────────────────────────────────────────────────


def _manual_auroc(labels: list[int], scores: list[float]) -> float:
    """Compute AUROC without sklearn.

    Uses the Wilcoxon–Mann–Whitney statistic: count concordant pairs.
    """
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0
    concordant = 0
    for s, l in zip(scores, labels):
        if l == 1:
            for s2, l2 in zip(scores, labels):
                if l2 == 0:
                    if s > s2:
                        concordant += 1
                    elif s == s2:
                        concordant += 0.5
    return concordant / (n_pos * n_neg)


def _train_fresh_proxy() -> tuple[DockingProxy, list[float]]:
    """Train a fresh proxy on embedded data. Returns (proxy, loss_history)."""
    smiles_list, labels = get_training_data()
    proxy = DockingProxy()
    loss_history = proxy.fit(smiles_list, labels)
    return proxy, loss_history


# ── Data tests ────────────────────────────────────────────────────────────


class TestTrainingData:
    def test_training_data_labels(self):
        """All binders have label=1, all decoys have label=0."""
        for compound in EGFR_BINDERS:
            assert compound.label == 1, f"{compound.name} should be label=1"
        for compound in DECOYS:
            assert compound.label == 0, f"{compound.name} should be label=0"

    @pytest.mark.skipif(not _HAS_RDKIT, reason="RDKit not installed")
    def test_training_data_valid_smiles(self):
        """All SMILES parse with RDKit."""
        from statebind.chemistry.validation import validate_smiles

        all_compounds = EGFR_BINDERS + DECOYS
        for compound in all_compounds:
            assert validate_smiles(compound.smiles), (
                f"{compound.name} has invalid SMILES: {compound.smiles}"
            )

    def test_training_data_sufficient_count(self):
        """At least 9 binders + 25 decoys = 34 total."""
        smiles_list, labels = get_training_data()
        assert len(EGFR_BINDERS) >= 9
        assert len(DECOYS) >= 25
        assert len(smiles_list) >= 34
        assert len(smiles_list) == len(labels)


# ── Model tests ───────────────────────────────────────────────────────────


@pytest.mark.skipif(not _HAS_RDKIT, reason="RDKit not installed")
class TestDockingProxyModel:
    def test_proxy_output_range(self):
        """All predictions on training SMILES in [0.0, 1.0]."""
        proxy, _ = _train_fresh_proxy()
        smiles_list, _ = get_training_data()
        for smi in smiles_list:
            score = proxy.predict(smi)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for {smi}"

    def test_proxy_training_loss_decreases(self):
        """Loss at epoch 0 > loss at final epoch."""
        _, loss_history = _train_fresh_proxy()
        assert len(loss_history) > 1
        assert loss_history[0] > loss_history[-1], (
            f"Loss did not decrease: {loss_history[0]:.4f} -> {loss_history[-1]:.4f}"
        )

    def test_proxy_binders_score_higher(self):
        """Mean binder score > mean decoy score."""
        proxy, _ = _train_fresh_proxy()
        smiles_list, labels = get_training_data()
        preds = proxy.predict_batch(smiles_list)
        binder_mean = np.mean([p for p, l in zip(preds, labels) if l == 1])
        decoy_mean = np.mean([p for p, l in zip(preds, labels) if l == 0])
        assert binder_mean > decoy_mean, (
            f"Binder mean {binder_mean:.4f} <= decoy mean {decoy_mean:.4f}"
        )

    def test_proxy_auroc_above_threshold(self):
        """AUROC > 0.7 on training data (sanity check)."""
        proxy, _ = _train_fresh_proxy()
        smiles_list, labels = get_training_data()
        preds = proxy.predict_batch(smiles_list)
        auroc = _manual_auroc(labels, preds)
        assert auroc > 0.7, f"AUROC {auroc:.4f} below threshold 0.7"

    def test_proxy_non_constant_output(self):
        """std(predictions) > 0.01 — unlike the 0.5 stub."""
        proxy, _ = _train_fresh_proxy()
        smiles_list, _ = get_training_data()
        preds = proxy.predict_batch(smiles_list)
        assert np.std(preds) > 0.01, (
            f"Predictions too constant: std={np.std(preds):.6f}"
        )

    def test_proxy_predict_batch_matches_individual(self):
        """predict_batch produces same values as individual predict calls."""
        proxy, _ = _train_fresh_proxy()
        smiles_list, _ = get_training_data()
        batch_preds = proxy.predict_batch(smiles_list)
        individual_preds = [proxy.predict(s) for s in smiles_list]
        np.testing.assert_array_almost_equal(batch_preds, individual_preds)

    def test_proxy_invalid_smiles_returns_default(self):
        """Invalid SMILES returns 0.5."""
        proxy, _ = _train_fresh_proxy()
        assert proxy.predict("not_a_smiles") == 0.5

    def test_proxy_empty_smiles_returns_default(self):
        """Empty string returns 0.5."""
        proxy, _ = _train_fresh_proxy()
        assert proxy.predict("") == 0.5


# ── Singleton tests ───────────────────────────────────────────────────────


class TestDefaultProxy:
    def test_default_proxy_returns_instance(self):
        """get_default_proxy() returns a DockingProxy instance."""
        import statebind.chemistry.docking_proxy as mod

        mod._DEFAULT_PROXY = None  # reset singleton
        proxy = get_default_proxy()
        assert isinstance(proxy, DockingProxy)
        mod._DEFAULT_PROXY = None  # cleanup

    def test_default_proxy_singleton(self):
        """get_default_proxy() returns same instance on repeated calls."""
        import statebind.chemistry.docking_proxy as mod

        mod._DEFAULT_PROXY = None  # reset singleton
        p1 = get_default_proxy()
        p2 = get_default_proxy()
        assert p1 is p2
        mod._DEFAULT_PROXY = None  # cleanup

    @pytest.mark.skipif(not _HAS_RDKIT, reason="RDKit not installed")
    def test_default_proxy_trained_predictions_differ(self):
        """Trained proxy predictions differ from 0.5."""
        import statebind.chemistry.docking_proxy as mod

        mod._DEFAULT_PROXY = None  # reset singleton
        proxy = get_default_proxy()
        # Erlotinib — known EGFR binder
        score = proxy.predict(
            "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC"
        )
        assert score != 0.5, f"Expected non-0.5, got {score}"
        mod._DEFAULT_PROXY = None  # cleanup


# ── Fallback tests ────────────────────────────────────────────────────────


class TestDockingProxyFallback:
    def test_proxy_without_rdkit_returns_default(self):
        """When RDKit unavailable, predict returns 0.5."""
        proxy = DockingProxy()
        # Force fitted=True but no RDKit
        proxy.fitted = True
        proxy.W1 = np.zeros((16, 20))
        proxy.b1 = np.zeros(16)
        proxy.W2 = np.zeros((1, 16))
        proxy.b2 = np.zeros(1)
        with patch(
            "statebind.chemistry.docking_proxy._has_rdkit", return_value=False
        ):
            score = proxy.predict("CCO")
            assert score == 0.5

    def test_featurize_returns_none_without_rdkit(self):
        """_featurize returns None when RDKit is unavailable."""
        proxy = DockingProxy()
        with patch(
            "statebind.chemistry.docking_proxy._has_rdkit", return_value=False
        ):
            result = proxy._featurize("CCO")
            assert result is None


# ── Additional tests ──────────────────────────────────────────────────────


@pytest.mark.skipif(not _HAS_RDKIT, reason="RDKit not installed")
class TestDockingProxySpecific:
    def test_erlotinib_scores_high(self):
        """Erlotinib (known binder) should score > 0.7."""
        proxy, _ = _train_fresh_proxy()
        score = proxy.predict(
            "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC"
        )
        assert score > 0.7, f"Erlotinib scored {score}, expected > 0.7"

    def test_caffeine_scores_low(self):
        """Caffeine (non-binder) should score < 0.4."""
        proxy, _ = _train_fresh_proxy()
        score = proxy.predict("Cn1c(=O)c2c(ncn2C)n(C)c1=O")
        assert score < 0.4, f"Caffeine scored {score}, expected < 0.4"

    def test_training_completes_under_five_seconds(self):
        """Training must complete in < 5 seconds."""
        smiles_list, labels = get_training_data()
        proxy = DockingProxy()
        t0 = time.time()
        proxy.fit(smiles_list, labels)
        elapsed = time.time() - t0
        assert elapsed < 5.0, f"Training took {elapsed:.2f}s, expected < 5s"
