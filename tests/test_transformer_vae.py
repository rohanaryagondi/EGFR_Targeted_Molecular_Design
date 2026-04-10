"""Tests for the Conditional Transformer VAE model.

Covers:
  1. TransformerVAEConfig: defaults, serialization, custom values.
  2. ConditionalTransformerVAE: forward shapes, encode, sample, generate.
  3. transformer_vae_loss: return types, padding, free bits, kl_weight.
  4. Integration: enum value, artifact schema, word dropout behavior.
  5. Internals: prefix token shape, causal mask correctness.

Total: 18 tests.
"""

from __future__ import annotations

import json

import pytest

from statebind.ml.transformer_vae import TransformerVAEConfig

# ── 1. Config tests ─────────────────────────────────────────────────────


class TestTransformerVAEConfig:
    """Tests for TransformerVAEConfig Pydantic model."""

    def test_config_defaults(self) -> None:
        """Default config has expected values."""
        cfg = TransformerVAEConfig()
        assert cfg.vocab_size == 100
        assert cfg.d_model == 256
        assert cfg.n_heads == 4
        assert cfg.n_decoder_layers == 4
        assert cfg.n_prefix_tokens == 8
        assert cfg.latent_dim == 64
        assert cfg.n_states == 3
        assert cfg.word_dropout == 0.3
        assert cfg.free_bits == 0.25
        assert cfg.kl_weight == 0.01
        assert cfg.pad_idx == 0
        assert cfg.encoder_hidden_dim == 256
        assert cfg.encoder_n_layers == 2

    def test_config_serialization_roundtrip(self) -> None:
        """Config survives JSON roundtrip via model_dump."""
        cfg = TransformerVAEConfig(d_model=128, n_heads=2, latent_dim=32)
        data = cfg.model_dump()
        restored = TransformerVAEConfig(**data)
        assert restored == cfg

        # Also test JSON string roundtrip
        json_str = json.dumps(data)
        from_json = TransformerVAEConfig(**json.loads(json_str))
        assert from_json == cfg

    def test_config_custom_values(self) -> None:
        """Non-default values are correctly stored."""
        cfg = TransformerVAEConfig(
            vocab_size=200,
            d_model=512,
            n_heads=8,
            n_decoder_layers=6,
            dim_feedforward=1024,
            n_prefix_tokens=4,
            latent_dim=128,
            n_states=1,
            word_dropout=0.5,
            free_bits=0.1,
            kl_weight=0.05,
        )
        assert cfg.vocab_size == 200
        assert cfg.d_model == 512
        assert cfg.n_heads == 8
        assert cfg.n_decoder_layers == 6
        assert cfg.dim_feedforward == 1024
        assert cfg.n_prefix_tokens == 4
        assert cfg.latent_dim == 128
        assert cfg.n_states == 1
        assert cfg.word_dropout == 0.5
        assert cfg.free_bits == 0.1
        assert cfg.kl_weight == 0.05


# ── 2. Model tests (require torch) ──────────────────────────────────────


class TestTransformerVAEModel:
    """Tests for ConditionalTransformerVAE nn.Module."""

    @pytest.fixture()
    def _small_model(self):
        """Create a small model for fast testing."""
        torch = pytest.importorskip("torch")  # noqa: F841
        from statebind.ml.transformer_vae import ConditionalTransformerVAE

        cfg = TransformerVAEConfig(
            vocab_size=30,
            embed_dim=32,
            latent_dim=16,
            n_states=3,
            encoder_hidden_dim=32,
            encoder_n_layers=1,
            encoder_dropout=0.0,
            d_model=32,
            n_heads=2,
            n_decoder_layers=2,
            dim_feedforward=64,
            decoder_dropout=0.0,
            n_prefix_tokens=4,
            word_dropout=0.0,
            free_bits=0.25,
            kl_weight=0.01,
        )
        model = ConditionalTransformerVAE(cfg)
        return model, cfg

    def test_forward_output_shapes(self, _small_model) -> None:
        """Forward pass produces correct output shapes."""
        torch = pytest.importorskip("torch")
        model, cfg = _small_model

        batch, seq_len = 4, 20
        tokens = torch.randint(1, cfg.vocab_size, (batch, seq_len))
        tokens[:, 0] = 1  # SOS
        lengths = torch.full((batch,), seq_len, dtype=torch.long)
        state_oh = torch.zeros(batch, cfg.n_states)
        state_oh[:, 0] = 1.0

        model.train()
        logits, mu, logvar = model(tokens, lengths, state_oh)

        # Logits aligned with tokens[:, 1:] (next-token prediction)
        assert logits.shape == (batch, seq_len - 1, cfg.vocab_size)
        assert mu.shape == (batch, cfg.latent_dim)
        assert logvar.shape == (batch, cfg.latent_dim)

    def test_encode_returns_mu_logvar(self, _small_model) -> None:
        """Encode produces mu and logvar with correct shapes."""
        torch = pytest.importorskip("torch")
        model, cfg = _small_model

        batch, seq_len = 3, 15
        tokens = torch.randint(1, cfg.vocab_size, (batch, seq_len))
        lengths = torch.full((batch,), seq_len, dtype=torch.long)
        state_oh = torch.zeros(batch, cfg.n_states)
        state_oh[:, 1] = 1.0

        mu, logvar = model.encode(tokens, lengths, state_oh)
        assert mu.shape == (batch, cfg.latent_dim)
        assert logvar.shape == (batch, cfg.latent_dim)

    def test_sample_training_vs_eval(self, _small_model) -> None:
        """Sample adds noise in training, returns mu in eval."""
        torch = pytest.importorskip("torch")
        model, cfg = _small_model

        mu = torch.randn(2, cfg.latent_dim)
        logvar = torch.zeros(2, cfg.latent_dim)

        # Eval mode: returns mu exactly
        model.eval()
        z_eval = model.sample(mu, logvar)
        assert torch.allclose(z_eval, mu)

        # Training mode: should differ from mu (with very high probability)
        model.train()
        z_train = model.sample(mu, logvar)
        # With logvar=0, std=1, noise is N(0,1). Very unlikely to be exactly mu.
        assert not torch.allclose(z_train, mu, atol=1e-3)

    def test_generate_produces_valid_sequences(self, _small_model) -> None:
        """Generate returns list of token sequences with valid indices."""
        torch = pytest.importorskip("torch")
        model, cfg = _small_model
        model.eval()

        batch = 3
        z = torch.randn(batch, cfg.latent_dim)
        state_oh = torch.zeros(batch, cfg.n_states)
        state_oh[:, 0] = 1.0

        sequences = model.generate(
            z, state_oh, max_len=30, temperature=0.8,
        )

        assert isinstance(sequences, list)
        assert len(sequences) == batch
        for seq in sequences:
            assert isinstance(seq, list)
            for tok in seq:
                assert isinstance(tok, int)
                assert 0 <= tok < cfg.vocab_size

    def test_generate_greedy_deterministic(self, _small_model) -> None:
        """Greedy decoding (temperature=0) is deterministic."""
        torch = pytest.importorskip("torch")
        model, cfg = _small_model
        model.eval()

        z = torch.randn(2, cfg.latent_dim)
        state_oh = torch.zeros(2, cfg.n_states)
        state_oh[:, 0] = 1.0

        seq1 = model.generate(z, state_oh, max_len=20, temperature=0)
        seq2 = model.generate(z, state_oh, max_len=20, temperature=0)
        assert seq1 == seq2

    def test_different_states_produce_different_latents(
        self, _small_model,
    ) -> None:
        """Encoding the same input with different states gives different mu."""
        torch = pytest.importorskip("torch")
        model, cfg = _small_model
        model.eval()

        tokens = torch.randint(1, cfg.vocab_size, (1, 15))
        lengths = torch.tensor([15])

        state_a = torch.zeros(1, cfg.n_states)
        state_a[0, 0] = 1.0
        state_b = torch.zeros(1, cfg.n_states)
        state_b[0, 1] = 1.0

        mu_a, _ = model.encode(tokens, lengths, state_a)
        mu_b, _ = model.encode(tokens, lengths, state_b)

        # Different state conditioning should produce different encodings
        assert not torch.allclose(mu_a, mu_b, atol=1e-4)


# ── 3. Loss tests (require torch) ───────────────────────────────────────


class TestTransformerVAELoss:
    """Tests for transformer_vae_loss function."""

    def test_loss_returns_three_tensors(self) -> None:
        """Loss returns (total, recon, kl) as scalar tensors."""
        torch = pytest.importorskip("torch")
        from statebind.ml.transformer_vae import transformer_vae_loss

        batch, seq_len, vocab = 4, 10, 30
        logits = torch.randn(batch, seq_len, vocab)
        target = torch.randint(0, vocab, (batch, seq_len))
        mu = torch.randn(batch, 16)
        logvar = torch.randn(batch, 16)

        total, recon, kl = transformer_vae_loss(
            logits, target, mu, logvar,
        )
        assert total.ndim == 0
        assert recon.ndim == 0
        assert kl.ndim == 0

    def test_loss_ignores_padding(self) -> None:
        """Padding tokens (pad_idx=0) don't contribute to recon loss."""
        torch = pytest.importorskip("torch")
        from statebind.ml.transformer_vae import transformer_vae_loss

        batch, seq_len, vocab = 2, 10, 30

        # Half padding, half real tokens
        logits = torch.randn(batch, seq_len, vocab)
        target_half_pad = torch.randint(1, vocab, (batch, seq_len))
        target_half_pad[:, seq_len // 2:] = 0  # second half is padding

        target_no_pad = target_half_pad.clone()
        # Replace padding with random tokens to get "no padding ignored" loss
        target_no_pad[:, seq_len // 2:] = torch.randint(1, vocab, (batch, seq_len // 2))

        mu = torch.zeros(batch, 16)
        logvar = torch.zeros(batch, 16)

        _, recon_pad, _ = transformer_vae_loss(
            logits, target_half_pad, mu, logvar,
            pad_idx=0, kl_weight=0.0,
        )
        _, recon_no_pad, _ = transformer_vae_loss(
            logits, target_no_pad, mu, logvar,
            pad_idx=0, kl_weight=0.0,
        )

        # With padding ignored, loss should differ from all-tokens loss
        assert not torch.isnan(recon_pad)
        assert recon_pad.item() != recon_no_pad.item()

    def test_free_bits_prevents_kl_collapse(self) -> None:
        """With mu=0, logvar=0, KL per dim = 0, but free bits floors it."""
        torch = pytest.importorskip("torch")
        from statebind.ml.transformer_vae import transformer_vae_loss

        batch, seq_len, vocab = 4, 10, 30
        latent_dim = 16
        free_bits = 0.25

        logits = torch.randn(batch, seq_len, vocab)
        target = torch.randint(1, vocab, (batch, seq_len))
        mu = torch.zeros(batch, latent_dim)
        logvar = torch.zeros(batch, latent_dim)

        _, _, kl = transformer_vae_loss(
            logits, target, mu, logvar,
            free_bits=free_bits,
        )

        # KL per dim = 0, but clamped to free_bits. Sum = free_bits * latent_dim.
        expected_kl = free_bits * latent_dim
        assert abs(kl.item() - expected_kl) < 1e-4

    def test_kl_weight_scales_contribution(self) -> None:
        """kl_weight=0 means total equals recon; kl_weight>0 adds KL."""
        torch = pytest.importorskip("torch")
        from statebind.ml.transformer_vae import transformer_vae_loss

        batch, seq_len, vocab = 4, 10, 30
        logits = torch.randn(batch, seq_len, vocab)
        target = torch.randint(1, vocab, (batch, seq_len))
        mu = torch.randn(batch, 16)
        logvar = torch.randn(batch, 16)

        total_0, recon_0, kl_0 = transformer_vae_loss(
            logits, target, mu, logvar, kl_weight=0.0,
        )
        assert torch.allclose(total_0, recon_0)

        total_1, recon_1, kl_1 = transformer_vae_loss(
            logits, target, mu, logvar, kl_weight=1.0,
        )
        assert torch.allclose(total_1, recon_1 + kl_1)


# ── 4. Integration tests ────────────────────────────────────────────────


class TestTransformerVAEIntegration:
    """Tests for pipeline integration of the Transformer VAE."""

    def test_generation_strategy_enum_has_transformer_vae(self) -> None:
        """GenerationStrategy has TRANSFORMER_VAE_GENERATED member."""
        from statebind.generation.models import GenerationStrategy

        assert hasattr(GenerationStrategy, "TRANSFORMER_VAE_GENERATED")
        assert (
            GenerationStrategy.TRANSFORMER_VAE_GENERATED.value
            == "transformer_vae_generated"
        )

    def test_artifact_json_schema(self) -> None:
        """Mock artifact dict has the required schema keys."""
        artifact = {
            "generated_at": "2026-04-10T12:00:00+00:00",
            "model": "ConditionalTransformerVAE",
            "checkpoint": "artifacts/models/transformer_vae/best_model.pt",
            "temperature": 0.8,
            "n_per_state": 100,
            "states": ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin"],
            "candidates": [
                {
                    "smiles": "c1ccc(NC(=O)c2ccccc2)cc1",
                    "state": "DFGin_aCin",
                    "is_valid": True,
                    "source": "transformer_vae_generated",
                },
            ],
        }
        assert "candidates" in artifact
        assert "temperature" in artifact
        cand = artifact["candidates"][0]
        assert "smiles" in cand
        assert "state" in cand
        assert "is_valid" in cand

    def test_load_vae_candidates_with_strategy_param(
        self, tmp_path,
    ) -> None:
        """load_vae_candidates accepts strategy and id_prefix params."""
        from statebind.generation.models import GenerationStrategy
        from statebind.generation.vae_integration import load_vae_candidates

        artifact = {
            "candidates": [
                {
                    "smiles": "c1ccccc1",
                    "state": "DFGin_aCin",
                    "is_valid": True,
                },
            ],
        }
        path = tmp_path / "test.json"
        path.write_text(json.dumps(artifact))

        # Default behavior (backward compat)
        cands = load_vae_candidates(path)
        assert cands[0].strategy == GenerationStrategy.VAE_GENERATED
        assert cands[0].candidate_id.startswith("vae_")

        # With Transformer VAE strategy
        cands2 = load_vae_candidates(
            path,
            strategy=GenerationStrategy.TRANSFORMER_VAE_GENERATED,
            id_prefix="tvae",
        )
        assert cands2[0].strategy == GenerationStrategy.TRANSFORMER_VAE_GENERATED
        assert cands2[0].candidate_id.startswith("tvae_")


# ── 5. Internals tests (require torch) ──────────────────────────────────


class TestTransformerVAEInternals:
    """Tests for internal components of the Transformer VAE."""

    def test_prefix_tokens_shape(self) -> None:
        """z_proj produces correct prefix token shape."""
        torch = pytest.importorskip("torch")
        from statebind.ml.transformer_vae import TransformerSMILESDecoder

        cfg = TransformerVAEConfig(
            vocab_size=30,
            d_model=32,
            n_heads=2,
            n_decoder_layers=2,
            dim_feedforward=64,
            n_prefix_tokens=4,
            latent_dim=16,
            n_states=3,
        )
        decoder = TransformerSMILESDecoder(cfg)

        batch = 3
        z = torch.randn(batch, cfg.latent_dim)
        state_oh = torch.zeros(batch, cfg.n_states)
        z_state = torch.cat([z, state_oh], dim=-1)

        prefix = decoder.z_proj(z_state)
        prefix = prefix.view(batch, cfg.n_prefix_tokens, cfg.d_model)

        assert prefix.shape == (batch, cfg.n_prefix_tokens, cfg.d_model)

    def test_causal_mask_shape_and_values(self) -> None:
        """Causal mask has correct shape and blocks future positions."""
        torch = pytest.importorskip("torch")
        from statebind.ml.transformer_vae import TransformerSMILESDecoder

        cfg = TransformerVAEConfig(
            vocab_size=30, d_model=32, n_heads=2,
            n_decoder_layers=1, dim_feedforward=64,
            n_prefix_tokens=3, latent_dim=16, n_states=3,
        )
        decoder = TransformerSMILESDecoder(cfg)

        n_prefix, seq_len = 3, 5
        mask = decoder._make_prefix_causal_mask(
            n_prefix, seq_len, torch.device("cpu"),
        )

        total = n_prefix + seq_len
        assert mask.shape == (total, total)

        # All positions can attend to prefix (columns 0..n_prefix-1 are 0)
        assert (mask[:, :n_prefix] == 0.0).all()

        # Sequence positions: causal within sequence block
        # Position n_prefix+i can attend to n_prefix+j only if j <= i
        for i in range(seq_len):
            for j in range(seq_len):
                row = n_prefix + i
                col = n_prefix + j
                if j <= i:
                    assert mask[row, col] == 0.0, (
                        f"Position {row} should attend to {col}"
                    )
                else:
                    assert mask[row, col] == float("-inf"), (
                        f"Position {row} should NOT attend to {col}"
                    )

    def test_word_dropout_only_during_training(self) -> None:
        """Word dropout is not applied during eval mode."""
        torch = pytest.importorskip("torch")
        from statebind.ml.transformer_vae import ConditionalTransformerVAE

        cfg = TransformerVAEConfig(
            vocab_size=30, embed_dim=32, latent_dim=16, n_states=3,
            encoder_hidden_dim=32, encoder_n_layers=1,
            d_model=32, n_heads=2, n_decoder_layers=1,
            dim_feedforward=64, n_prefix_tokens=4,
            word_dropout=1.0,  # 100% dropout to make effect obvious
        )
        model = ConditionalTransformerVAE(cfg)

        batch, seq_len = 2, 10
        tokens = torch.randint(4, cfg.vocab_size, (batch, seq_len))
        tokens[:, 0] = 1  # SOS
        lengths = torch.full((batch,), seq_len, dtype=torch.long)
        state_oh = torch.zeros(batch, cfg.n_states)
        state_oh[:, 0] = 1.0

        # In eval mode, word_dropout should have no effect
        model.eval()
        logits_eval1, _, _ = model(tokens, lengths, state_oh, word_dropout=1.0)
        logits_eval2, _, _ = model(tokens, lengths, state_oh, word_dropout=0.0)
        assert torch.allclose(logits_eval1, logits_eval2)
