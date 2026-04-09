"""Tests for statebind.chemistry — Morgan fingerprints, descriptors, validation, SA score.

Tests cover both RDKit-present paths (skipped when rdkit is not installed)
and fallback paths (exercised via mock patching of HAS_RDKIT flags).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from statebind.baselines.scoring import _REFERENCE_BINDERS, _tanimoto_ngram
from statebind.chemistry.descriptors import compute_exact_properties
from statebind.chemistry.fingerprints import (
    HAS_RDKIT,
    compute_max_reference_similarity,
    compute_morgan_fingerprint,
    compute_morgan_similarity,
)
from statebind.chemistry.sa_score import compute_sa_score
from statebind.chemistry.validation import canonicalize_smiles, validate_smiles

# Convenience aliases
_ERLOTINIB = _REFERENCE_BINDERS[0]
_GEFITINIB = _REFERENCE_BINDERS[1]
# Osimertinib SMILES defined directly (removed from _REFERENCE_BINDERS to fix
# temporal leakage -- approved 2015/2017, used as future drug in retrospective).
_OSIMERTINIB = "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1"


# ── Fingerprints ──────────────────────────────────────────────────────────


class TestFingerprints:
    """Morgan fingerprint computation and similarity."""

    def test_has_rdkit_flag_is_bool(self) -> None:
        assert isinstance(HAS_RDKIT, bool)

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_morgan_fingerprint_valid(self) -> None:
        fp = compute_morgan_fingerprint(_ERLOTINIB)
        assert fp is not None

    def test_morgan_fingerprint_invalid_smiles(self) -> None:
        assert compute_morgan_fingerprint("not_a_smiles") is None

    def test_morgan_fingerprint_empty_smiles(self) -> None:
        assert compute_morgan_fingerprint("") is None

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_morgan_similarity_self(self) -> None:
        sim = compute_morgan_similarity(_ERLOTINIB, _ERLOTINIB)
        assert sim == pytest.approx(1.0)

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_morgan_similarity_range(self) -> None:
        pairs = [
            (_ERLOTINIB, _GEFITINIB),
            (_ERLOTINIB, _OSIMERTINIB),
            (_GEFITINIB, _OSIMERTINIB),
            (_ERLOTINIB, "CCO"),
            (_ERLOTINIB, "c1ccccc1"),
        ]
        for a, b in pairs:
            sim = compute_morgan_similarity(a, b)
            assert 0.0 <= sim <= 1.0, f"sim({a[:20]}, {b[:20]}) = {sim}"

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_morgan_similarity_symmetric(self) -> None:
        sim_ab = compute_morgan_similarity(_ERLOTINIB, "CCO")
        sim_ba = compute_morgan_similarity("CCO", _ERLOTINIB)
        assert sim_ab == pytest.approx(sim_ba)

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_morgan_more_discriminative_than_ngram(self) -> None:
        """Morgan should spread scores more than n-gram across diverse molecules."""
        import numpy as np

        test_smiles = ["CCO", "c1ccccc1", "CC(=O)O", _ERLOTINIB]
        morgan_sims = [compute_morgan_similarity(s, _ERLOTINIB) for s in test_smiles]
        ngram_sims = [_tanimoto_ngram(s, _ERLOTINIB) for s in test_smiles]
        assert np.var(morgan_sims) > np.var(ngram_sims)

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_max_reference_similarity_known_binder(self) -> None:
        sim = compute_max_reference_similarity(_ERLOTINIB)
        assert sim == pytest.approx(1.0)

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_max_reference_similarity_custom_refs(self) -> None:
        sim = compute_max_reference_similarity("CCO", references=["CCO", "CCCO"])
        assert sim == pytest.approx(1.0)

    def test_max_reference_similarity_empty_smiles(self) -> None:
        assert compute_max_reference_similarity("") == 0.0

    def test_fingerprint_fallback_without_rdkit(self) -> None:
        with patch("statebind.chemistry.fingerprints.HAS_RDKIT", False):
            sim = compute_morgan_similarity("CCO", "CCCO")
            expected = _tanimoto_ngram("CCO", "CCCO")
            assert sim == pytest.approx(expected)


# ── Descriptors ───────────────────────────────────────────────────────────


class TestDescriptors:
    """Exact molecular property computation."""

    _REQUIRED_KEYS = {"estimated_mw", "estimated_hba", "estimated_hbd", "n_rings", "n_heavy_atoms"}
    _ADDITIONAL_KEYS = {"tpsa", "logp", "n_rotatable_bonds"}

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_exact_properties_erlotinib_mw(self) -> None:
        props = compute_exact_properties(_ERLOTINIB)
        mw = props["estimated_mw"]
        assert mw is not None
        assert mw == pytest.approx(393.44, rel=0.01)

    def test_exact_properties_backward_compat_keys(self) -> None:
        props = compute_exact_properties(_ERLOTINIB)
        for key in self._REQUIRED_KEYS:
            assert key in props, f"Missing required key: {key}"

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_exact_properties_additional_keys(self) -> None:
        props = compute_exact_properties(_ERLOTINIB)
        for key in self._ADDITIONAL_KEYS:
            assert key in props, f"Missing additional key: {key}"
            assert props[key] is not None

    def test_exact_properties_invalid_smiles(self) -> None:
        props = compute_exact_properties("not_a_smiles")
        for key in self._REQUIRED_KEYS | self._ADDITIONAL_KEYS:
            assert props[key] is None, f"Expected None for {key}"

    def test_exact_properties_empty_smiles(self) -> None:
        props = compute_exact_properties("")
        for key in self._REQUIRED_KEYS:
            assert props[key] is None

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_exact_properties_values_are_float(self) -> None:
        props = compute_exact_properties(_ERLOTINIB)
        for key, val in props.items():
            if val is not None:
                assert isinstance(val, float), f"{key} is {type(val)}, expected float"

    def test_exact_properties_no_rdkit_fallback(self) -> None:
        with patch("statebind.chemistry.descriptors.HAS_RDKIT", False):
            props = compute_exact_properties(_ERLOTINIB)
            for val in props.values():
                assert val is None


# ── Validation ────────────────────────────────────────────────────────────


class TestValidation:
    """SMILES validation and canonicalization."""

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    @pytest.mark.parametrize("smiles", [_ERLOTINIB, _GEFITINIB, _OSIMERTINIB, "CCO", "c1ccccc1"])
    def test_validate_valid_smiles(self, smiles: str) -> None:
        assert validate_smiles(smiles) is True

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    @pytest.mark.parametrize("smiles", ["", "not_a_smiles", "X", "[invalid"])
    def test_validate_invalid_smiles(self, smiles: str) -> None:
        assert validate_smiles(smiles) is False

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_canonicalize_returns_string(self) -> None:
        result = canonicalize_smiles("CCO")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_canonicalize_idempotent(self) -> None:
        canon1 = canonicalize_smiles(_ERLOTINIB)
        assert canon1 is not None
        canon2 = canonicalize_smiles(canon1)
        assert canon1 == canon2

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_canonicalize_invalid_returns_none(self) -> None:
        assert canonicalize_smiles("not_a_smiles") is None
        assert canonicalize_smiles("") is None

    def test_canonicalize_fallback_returns_original(self) -> None:
        with patch("statebind.chemistry.validation.HAS_RDKIT", False):
            result = canonicalize_smiles("CCO")
            assert result == "CCO"

    def test_validate_fallback_permissive(self) -> None:
        with patch("statebind.chemistry.validation.HAS_RDKIT", False):
            assert validate_smiles("anything") is True


# ── SA Score ──────────────────────────────────────────────────────────────


class TestSAScore:
    """Synthetic accessibility scoring."""

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    @pytest.mark.parametrize("smiles", [_ERLOTINIB, "CCO", "c1ccccc1", "CC(=O)O"])
    def test_sa_score_range(self, smiles: str) -> None:
        score = compute_sa_score(smiles)
        assert 1.0 <= score <= 10.0, f"SA({smiles}) = {score}"

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_sa_score_simple_molecule_low(self) -> None:
        score = compute_sa_score("c1ccccc1")  # benzene
        assert score < 5.0, f"Benzene SA = {score}, expected < 5"

    @pytest.mark.skipif(not HAS_RDKIT, reason="rdkit not installed")
    def test_sa_score_complex_higher_than_simple(self) -> None:
        simple = compute_sa_score("CCO")  # ethanol
        complex_ = compute_sa_score(_OSIMERTINIB)
        assert complex_ > simple, f"complex ({complex_}) should be > simple ({simple})"

    def test_sa_score_invalid_smiles(self) -> None:
        assert compute_sa_score("not_a_smiles") == 5.0

    def test_sa_score_empty_smiles(self) -> None:
        assert compute_sa_score("") == 5.0

    def test_sa_score_fallback_without_rdkit(self) -> None:
        with patch("statebind.chemistry.sa_score.HAS_RDKIT", False):
            assert compute_sa_score(_ERLOTINIB) == 5.0
