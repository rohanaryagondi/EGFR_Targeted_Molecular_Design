"""Tests for VAE quality metrics (FCD, reconstruction, novelty, diversity).

Covers:
- Novelty computation with known overlaps
- Internal diversity with identical and diverse molecules
- FCD with mock/skip when fcd_torch is unavailable
- Reconstruction accuracy with mock/skip when torch is unavailable
- VaeMetricsResult serialization
- Edge cases: empty lists, single molecule, all duplicates
"""

from __future__ import annotations

import pytest

from statebind.evaluation.vae_metrics import (
    HAS_FCD,
    HAS_RDKIT,
    HAS_TORCH,
    VaeMetricsResult,
    _canonicalize,
    compute_fcd,
    compute_internal_diversity,
    compute_novelty,
    compute_reconstruction_accuracy,
    evaluate_vae_quality,
)


# ── Novelty tests ───────────────────────────────────────────────────────


class TestComputeNovelty:
    """Test novelty metric."""

    def test_half_overlap(self):
        generated = ["CCO", "CCN"]
        training = ["CCO"]
        result = compute_novelty(generated, training)
        assert result == 0.5

    def test_full_overlap(self):
        generated = ["CCO", "CCN"]
        training = ["CCO", "CCN"]
        assert compute_novelty(generated, training) == 0.0

    def test_no_overlap(self):
        generated = ["CCO", "CCN"]
        training = ["CCC", "CCCC"]
        assert compute_novelty(generated, training) == 1.0

    def test_empty_generated(self):
        assert compute_novelty([], ["CCO"]) == 0.0

    def test_empty_training(self):
        # Everything is novel when training set is empty
        assert compute_novelty(["CCO", "CCN"], []) == 1.0

    def test_both_empty(self):
        assert compute_novelty([], []) == 0.0

    def test_single_molecule_novel(self):
        assert compute_novelty(["CCO"], ["CCN"]) == 1.0

    def test_single_molecule_not_novel(self):
        assert compute_novelty(["CCO"], ["CCO"]) == 0.0

    def test_all_duplicates_in_generated(self):
        generated = ["CCO", "CCO", "CCO"]
        training = ["CCO"]
        assert compute_novelty(generated, training) == 0.0

    def test_novelty_rounded_to_4dp(self):
        # 1 out of 3 = 0.3333...
        generated = ["CCO", "CCN", "CCC"]
        training = ["CCO", "CCN"]
        result = compute_novelty(generated, training)
        assert result == round(1 / 3, 4)


# ── Internal diversity tests ────────────────────────────────────────────


class TestComputeInternalDiversity:
    """Test internal diversity metric."""

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_identical_molecules_zero_diversity(self):
        result = compute_internal_diversity(["CCO"] * 10)
        assert result is not None
        assert result == 0.0

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_diverse_molecules_positive_diversity(self):
        diverse = [
            "c1ccccc1",      # benzene
            "CCO",           # ethanol
            "CC(=O)O",       # acetic acid
            "CCCCCCCCCC",    # decane
            "C1CCCCC1",      # cyclohexane
        ]
        result = compute_internal_diversity(diverse)
        assert result is not None
        assert result > 0.0

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_diversity_range(self):
        smiles = ["CCO", "CCCO", "CCCCO", "c1ccccc1", "CC(=O)O"]
        result = compute_internal_diversity(smiles)
        assert result is not None
        assert 0.0 <= result <= 1.0

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_single_molecule_zero(self):
        assert compute_internal_diversity(["CCO"]) == 0.0

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_empty_list(self):
        assert compute_internal_diversity([]) == 0.0

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_subsampling(self):
        # With n_sample=3, only 3 molecules are compared
        smiles = ["CCO", "CCN", "CCC", "CCCC", "CCCCC"]
        result = compute_internal_diversity(smiles, n_sample=3)
        assert result is not None
        assert 0.0 <= result <= 1.0

    def test_no_rdkit_returns_none(self):
        if HAS_RDKIT:
            pytest.skip("RDKit is installed -- cannot test fallback")
        result = compute_internal_diversity(["CCO", "CCN"])
        assert result is None

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_invalid_smiles_skipped(self):
        # Invalid SMILES should be skipped, remaining evaluated
        smiles = ["CCO", "INVALID_SMILES_XYZ", "CCN"]
        result = compute_internal_diversity(smiles)
        assert result is not None
        # Only 2 valid molecules, should still compute
        assert 0.0 <= result <= 1.0

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_all_invalid_returns_zero(self):
        smiles = ["INVALID1", "INVALID2"]
        result = compute_internal_diversity(smiles)
        assert result == 0.0


# ── FCD tests ───────────────────────────────────────────────────────────


class TestComputeFcd:
    """Test FCD computation."""

    def test_no_fcd_torch_returns_none(self):
        if HAS_FCD:
            pytest.skip("fcd_torch is installed -- cannot test fallback")
        result = compute_fcd(["CCO", "CCN"], ["CCO", "CCN"])
        assert result is None

    @pytest.mark.skipif(not HAS_FCD, reason="fcd_torch not installed")
    def test_fcd_identical_sets(self):
        smiles = ["CCO", "CCN", "CCC", "CCCC", "c1ccccc1"] * 20
        result = compute_fcd(smiles, smiles)
        assert result is not None
        assert isinstance(result, float)

    def test_fcd_empty_generated(self):
        result = compute_fcd([], ["CCO"])
        assert result is None

    def test_fcd_empty_reference(self):
        result = compute_fcd(["CCO"], [])
        assert result is None


# ── Reconstruction accuracy tests ───────────────────────────────────────


class TestComputeReconstructionAccuracy:
    """Test reconstruction accuracy."""

    def test_no_torch_returns_none(self):
        if HAS_TORCH:
            pytest.skip("torch is installed -- cannot test fallback")
        # Pass None for model/dataset/vocab since torch is not available
        result = compute_reconstruction_accuracy(
            None, None, None,  # type: ignore[arg-type]
        )
        assert result is None

    @pytest.mark.skipif(not HAS_TORCH, reason="torch not installed")
    def test_perfect_reconstruction_mock(self):
        """Mock a perfect-reconstruction VAE."""
        import torch

        from statebind.ml.vocabulary import Vocabulary

        vocab = Vocabulary()
        for tok in ["C", "=", "O", "N", "(", ")"]:
            vocab.add_token(tok)

        # Build a mock model that returns its input
        class _MockVAE:
            def to(self, device):
                return self

            def eval(self):
                pass

            def encode(self, x, lengths, state):
                return torch.zeros(1, 16), torch.zeros(1, 16)

            def generate(self, z, state, max_len, temperature, vocab):
                # Return pre-stored sequence
                return [self._target_body]

            _target_body: list[int] = []

        mock_model = _MockVAE()

        # Build a minimal dataset-like object
        # Two molecules: "C=O" and "CCN"
        smiles_tokens = [
            [vocab.token_to_idx["C"], vocab.token_to_idx["="],
             vocab.token_to_idx["O"]],
            [vocab.token_to_idx["C"], vocab.token_to_idx["C"],
             vocab.token_to_idx["N"]],
        ]

        class _MockDataset:
            def __len__(self):
                return 2

            def __getitem__(self, idx):
                body = smiles_tokens[idx]
                full = [vocab.sos_idx] + body + [vocab.eos_idx]
                return (
                    torch.tensor(full, dtype=torch.long),
                    len(full),
                    torch.tensor([1.0, 0.0, 0.0, 0.0]),
                )

        mock_dataset = _MockDataset()

        # Hook: mock generate returns the correct body each time
        original_generate = mock_model.generate

        call_count = [0]

        def generate_side_effect(z, state, max_len, temperature, vocab):
            idx = call_count[0]
            call_count[0] += 1
            return [smiles_tokens[idx]]

        mock_model.generate = generate_side_effect  # type: ignore[assignment]

        result = compute_reconstruction_accuracy(
            mock_model, mock_dataset, vocab,  # type: ignore[arg-type]
        )
        assert result is not None
        assert result == 1.0

    @pytest.mark.skipif(not HAS_TORCH, reason="torch not installed")
    def test_zero_reconstruction_mock(self):
        """Mock a VAE that always generates wrong output."""
        import torch

        from statebind.ml.vocabulary import Vocabulary

        vocab = Vocabulary()
        for tok in ["C", "=", "O", "N"]:
            vocab.add_token(tok)

        class _MockVAE:
            def to(self, device):
                return self

            def eval(self):
                pass

            def encode(self, x, lengths, state):
                return torch.zeros(1, 16), torch.zeros(1, 16)

            def generate(self, z, state, max_len, temperature, vocab):
                # Always return wrong tokens
                return [[999, 998, 997]]

        mock_model = _MockVAE()

        class _MockDataset:
            def __len__(self):
                return 2

            def __getitem__(self, idx):
                body = [vocab.token_to_idx["C"], vocab.token_to_idx["O"]]
                full = [vocab.sos_idx] + body + [vocab.eos_idx]
                return (
                    torch.tensor(full, dtype=torch.long),
                    len(full),
                    torch.tensor([1.0, 0.0, 0.0, 0.0]),
                )

        result = compute_reconstruction_accuracy(
            mock_model, _MockDataset(), vocab,  # type: ignore[arg-type]
        )
        assert result is not None
        assert result == 0.0


# ── VaeMetricsResult serialization tests ────────────────────────────────


class TestVaeMetricsResult:
    """Test Pydantic model serialization."""

    def test_roundtrip_json(self):
        result = VaeMetricsResult(
            fcd_score=12.345,
            reconstruction_accuracy=0.8765,
            novelty=0.5,
            internal_diversity=0.7,
            n_generated=100,
            n_valid=100,
            n_novel=50,
        )
        data = result.model_dump_json()
        restored = VaeMetricsResult.model_validate_json(data)
        assert restored.fcd_score == 12.345
        assert restored.novelty == 0.5
        assert restored.n_novel == 50

    def test_none_fields(self):
        result = VaeMetricsResult(
            fcd_score=None,
            reconstruction_accuracy=None,
            novelty=1.0,
            internal_diversity=None,
            n_generated=10,
            n_valid=10,
            n_novel=10,
        )
        data = result.model_dump()
        assert data["fcd_score"] is None
        assert data["reconstruction_accuracy"] is None
        assert data["internal_diversity"] is None
        assert data["novelty"] == 1.0

    def test_dict_roundtrip(self):
        result = VaeMetricsResult(
            novelty=0.42,
            n_generated=200,
            n_valid=200,
            n_novel=84,
        )
        d = result.model_dump()
        restored = VaeMetricsResult(**d)
        assert restored.novelty == 0.42
        assert restored.n_novel == 84


# ── Orchestrator tests ──────────────────────────────────────────────────


class TestEvaluateVaeQuality:
    """Test the top-level orchestrator."""

    def test_basic_evaluation(self):
        generated = ["CCO", "CCN", "CCC"]
        training = ["CCO"]
        result = evaluate_vae_quality(generated, training)
        assert isinstance(result, VaeMetricsResult)
        assert result.n_generated == 3
        assert result.n_valid == 3
        assert result.n_novel == 2
        assert result.novelty == round(2 / 3, 4)

    def test_empty_generated(self):
        result = evaluate_vae_quality([], ["CCO"])
        assert result.n_generated == 0
        assert result.novelty == 0.0
        assert result.n_novel == 0

    def test_empty_training(self):
        result = evaluate_vae_quality(["CCO", "CCN"], [])
        assert result.novelty == 1.0
        assert result.n_novel == 2

    def test_no_model_skips_reconstruction(self):
        result = evaluate_vae_quality(
            ["CCO", "CCN"], ["CCO"],
            model=None, dataset=None, vocab=None,
        )
        assert result.reconstruction_accuracy is None

    def test_result_is_serializable(self):
        result = evaluate_vae_quality(["CCO", "CCN"], ["CCO"])
        json_str = result.model_dump_json()
        assert "novelty" in json_str


# ── Canonicalization tests ──────────────────────────────────────────────


class TestCanonicalize:
    """Test SMILES canonicalization helper."""

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_canonical_with_rdkit(self):
        # Different notations for ethanol
        c1 = _canonicalize("OCC")
        c2 = _canonicalize("CCO")
        assert c1 == c2

    def test_strips_whitespace(self):
        # Fallback path should at least strip whitespace
        if not HAS_RDKIT:
            assert _canonicalize("  CCO  ") == "CCO"

    @pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
    def test_invalid_smiles_returns_stripped(self):
        # Invalid SMILES with RDKit should return stripped string
        result = _canonicalize("INVALID_XYZ")
        assert result == "INVALID_XYZ"
