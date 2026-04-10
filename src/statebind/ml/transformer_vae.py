"""Conditional Transformer VAE with GRU encoder and Transformer decoder.

Replaces the broken GRU decoder from :mod:`statebind.ml.vae` with a
Transformer decoder that uses self-attention to handle ring-closure
dependencies in SMILES notation.  Posterior collapse is addressed with
free-bits KL regularization and word dropout.

Architecture::

    Input SMILES tokens -> Embedding(vocab_size, embed_dim)
                                    |
    Encoder: Bidirectional GRU (reused from vae.py)
             -> mu, logvar (latent_dim)
                                    |
    Latent: z = mu + eps * exp(0.5 * logvar)
            [z; state_onehot] -> Linear -> n_prefix_tokens of d_model
                                    |
    Decoder: [prefix_tokens; embedded_input] -> TransformerEncoder (causal)
             -> Linear(d_model, vocab_size) per position

Classes:
    TransformerVAEConfig        -- Pydantic config (always importable).
    SinusoidalPositionalEncoding -- Standard positional encoding.
    TransformerSMILESDecoder    -- Transformer decoder with prefix z injection.
    ConditionalTransformerVAE   -- Full model (requires torch).

Functions:
    transformer_vae_loss        -- Reconstruction + free-bits KL (requires torch).
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as functional

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

if TYPE_CHECKING:
    from statebind.ml.vocabulary import Vocabulary

logger = logging.getLogger(__name__)


def _require_torch() -> None:
    """Raise RuntimeError if torch is not installed."""
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for the Transformer VAE module but is not "
            "installed. Install it with: pip install torch"
        )


# ---------------------------------------------------------------------------
# Configuration (always available — no torch dependency)
# ---------------------------------------------------------------------------


class TransformerVAEConfig(BaseModel):
    """Hyperparameters for the Conditional Transformer VAE.

    All architectural and training-related hyperparameters are collected
    here so the model can be instantiated from a single config object and
    serialised alongside checkpoints for reproducibility.
    """

    vocab_size: int = 100
    embed_dim: int = 128
    latent_dim: int = 64
    n_states: int = Field(
        default=3,
        description="Number of conditioning states (EGFR conformations)",
    )
    pad_idx: int = Field(
        default=0,
        description="Padding token index for masking",
    )

    # Encoder (bidirectional GRU — reused from vae.py)
    encoder_hidden_dim: int = 256
    encoder_n_layers: int = 2
    encoder_dropout: float = 0.1

    # Decoder (Transformer)
    d_model: int = 256
    n_heads: int = 4
    n_decoder_layers: int = 4
    dim_feedforward: int = 512
    decoder_dropout: float = 0.1

    # z injection
    n_prefix_tokens: int = Field(
        default=8,
        description="Number of prefix tokens projected from latent z",
    )

    # Anti-collapse
    word_dropout: float = Field(
        default=0.3,
        description="Fraction of decoder inputs replaced with <unk> during training",
    )
    free_bits: float = Field(
        default=0.25,
        description="Minimum KL per latent dimension (lambda in free-bits)",
    )

    # KL
    kl_weight: float = Field(
        default=0.01,
        description="KL annealing target weight (beta)",
    )


# ---------------------------------------------------------------------------
# Neural network components (only defined when torch is available)
# ---------------------------------------------------------------------------

if HAS_TORCH:
    from statebind.ml.vae import SMILESEncoder, VAEConfig

    class SinusoidalPositionalEncoding(nn.Module):
        """Standard sinusoidal positional encoding.

        Precomputes a positional encoding matrix and adds it to the
        input embeddings.  Dropout is applied after addition.

        Parameters
        ----------
        d_model:
            Embedding / model dimension.
        max_len:
            Maximum sequence length to precompute.
        dropout:
            Dropout probability applied after PE addition.
        """

        def __init__(
            self,
            d_model: int,
            max_len: int = 512,
            dropout: float = 0.1,
        ) -> None:
            super().__init__()
            self.dropout = nn.Dropout(p=dropout)

            pe = torch.zeros(max_len, d_model)
            position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div_term = torch.exp(
                torch.arange(0, d_model, 2, dtype=torch.float)
                * (-math.log(10000.0) / d_model)
            )
            pe[:, 0::2] = torch.sin(position * div_term)
            pe[:, 1::2] = torch.cos(position * div_term)
            # (1, max_len, d_model) for broadcasting over batch
            pe = pe.unsqueeze(0)
            self.register_buffer("pe", pe)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Add positional encoding to input embeddings.

            Parameters
            ----------
            x:
                Input tensor of shape ``(batch, seq_len, d_model)``.

            Returns
            -------
            Tensor:
                ``x + PE[:seq_len]`` with dropout, same shape as input.
            """
            x = x + self.pe[:, : x.size(1)]
            return self.dropout(x)

    class TransformerSMILESDecoder(nn.Module):
        """Transformer decoder with prefix-token z injection.

        The latent code ``z`` concatenated with the state one-hot is
        projected into ``n_prefix_tokens`` vectors of size ``d_model``,
        which are prepended to the embedded input sequence.  A causal
        attention mask allows all positions to attend to prefix tokens
        and earlier sequence positions.

        Word dropout randomly replaces input embeddings with the
        ``<unk>`` token embedding during training to force the decoder
        to rely on information from the prefix (latent) tokens.

        Parameters
        ----------
        config:
            A :class:`TransformerVAEConfig` with all hyperparameters.
        """

        def __init__(self, config: TransformerVAEConfig) -> None:
            super().__init__()
            self.config = config

            self.embedding = nn.Embedding(
                config.vocab_size,
                config.d_model,
                padding_idx=config.pad_idx,
            )
            self.pos_encoding = SinusoidalPositionalEncoding(
                config.d_model,
                max_len=512,
                dropout=config.decoder_dropout,
            )

            # Project [z; state_onehot] -> prefix tokens
            self.z_proj = nn.Linear(
                config.latent_dim + config.n_states,
                config.n_prefix_tokens * config.d_model,
            )

            # Self-attention transformer layers (causal)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=config.d_model,
                nhead=config.n_heads,
                dim_feedforward=config.dim_feedforward,
                dropout=config.decoder_dropout,
                batch_first=True,
                norm_first=True,
            )
            self.transformer = nn.TransformerEncoder(
                encoder_layer,
                num_layers=config.n_decoder_layers,
            )

            self.output_proj = nn.Linear(config.d_model, config.vocab_size)

            # UNK index for word dropout
            self._unk_idx = 3

        def _make_prefix_causal_mask(
            self,
            n_prefix: int,
            seq_len: int,
            device: torch.device,
        ) -> torch.Tensor:
            """Create a causal mask that allows attending to all prefix tokens.

            Returns a float mask of shape ``(total, total)`` where
            ``total = n_prefix + seq_len``.  Positions with ``-inf`` are
            blocked from attention.

            - All positions can attend to any prefix token.
            - Sequence positions use standard causal masking among
              themselves (can attend to earlier or same position).

            Parameters
            ----------
            n_prefix:
                Number of prefix tokens.
            seq_len:
                Number of sequence tokens (after prefix).
            device:
                Device for the mask tensor.

            Returns
            -------
            Tensor:
                Float attention mask ``(total, total)``.
            """
            total = n_prefix + seq_len

            # Start with all blocked
            mask = torch.full(
                (total, total), float("-inf"), device=device,
            )

            # Prefix tokens can attend to all prefix tokens
            mask[:n_prefix, :n_prefix] = 0.0

            # All positions can attend to prefix tokens
            mask[:, :n_prefix] = 0.0

            # Sequence positions: causal within sequence block
            seq_mask = torch.triu(
                torch.full((seq_len, seq_len), float("-inf"), device=device),
                diagonal=1,
            )
            mask[n_prefix:, n_prefix:] = seq_mask

            return mask

        def forward(
            self,
            z: torch.Tensor,
            state_onehot: torch.Tensor,
            target: torch.Tensor,
            word_dropout: float = 0.0,
        ) -> torch.Tensor:
            """Decode latent code into token logits.

            Parameters
            ----------
            z:
                Latent code of shape ``(batch, latent_dim)``.
            state_onehot:
                Conditioning vector of shape ``(batch, n_states)``.
            target:
                Decoder input token indices ``(batch, seq_len)``.
                Typically ``tokens[:, :-1]`` (everything except last).
            word_dropout:
                Probability of replacing each input token embedding
                with ``<unk>`` embedding.  SOS (position 0) is never
                dropped.  Set to 0.0 during validation/generation.

            Returns
            -------
            Tensor:
                Logits of shape ``(batch, seq_len, vocab_size)``.
            """
            batch_size, seq_len = target.shape
            device = target.device
            n_prefix = self.config.n_prefix_tokens

            # --- Prefix tokens from z ---
            z_state = torch.cat([z, state_onehot], dim=-1)
            prefix = self.z_proj(z_state)  # (batch, n_prefix * d_model)
            prefix = prefix.view(
                batch_size, n_prefix, self.config.d_model,
            )

            # --- Embed and optionally corrupt input tokens ---
            embedded = self.embedding(target)  # (batch, seq_len, d_model)

            if word_dropout > 0.0 and self.training:
                # Create dropout mask — never drop position 0 (SOS)
                drop_mask = (
                    torch.rand(batch_size, seq_len, device=device)
                    < word_dropout
                )
                drop_mask[:, 0] = False

                unk_tensor = torch.full(
                    (batch_size, seq_len),
                    self._unk_idx,
                    dtype=torch.long,
                    device=device,
                )
                unk_embedded = self.embedding(unk_tensor)
                embedded = torch.where(
                    drop_mask.unsqueeze(-1), unk_embedded, embedded,
                )

            # --- Add positional encoding to sequence tokens ---
            embedded = self.pos_encoding(embedded)

            # --- Concatenate [prefix; sequence] ---
            combined = torch.cat([prefix, embedded], dim=1)
            # (batch, n_prefix + seq_len, d_model)

            # --- Create causal mask ---
            attn_mask = self._make_prefix_causal_mask(
                n_prefix, seq_len, device,
            )

            # --- Padding mask ---
            # Prefix tokens are never padded
            prefix_pad = torch.zeros(
                batch_size, n_prefix, dtype=torch.bool, device=device,
            )
            seq_pad = target == self.config.pad_idx
            src_key_padding_mask = torch.cat(
                [prefix_pad, seq_pad], dim=1,
            )

            # --- Transformer forward ---
            output = self.transformer(
                combined,
                mask=attn_mask,
                src_key_padding_mask=src_key_padding_mask,
            )

            # --- Extract sequence positions, project to vocab ---
            seq_output = output[:, n_prefix:, :]  # (batch, seq_len, d_model)
            logits = self.output_proj(seq_output)  # (batch, seq_len, vocab_size)

            return logits

    class ConditionalTransformerVAE(nn.Module):
        """Conditional Transformer VAE combining GRU encoder and Transformer decoder.

        State conditioning (a one-hot vector over EGFR conformational
        states) is injected at two points:

        1. **Encoder** -- concatenated to token embeddings at every
           timestep (via the reused :class:`SMILESEncoder`).
        2. **Decoder** -- concatenated to the latent code ``z`` before
           projection to prefix tokens for the Transformer.

        Parameters
        ----------
        config:
            A :class:`TransformerVAEConfig` with all hyperparameters.
        """

        def __init__(self, config: TransformerVAEConfig) -> None:
            super().__init__()
            self.config = config

            # Build a VAEConfig for the GRU encoder (reuse proven encoder)
            encoder_config = VAEConfig(
                vocab_size=config.vocab_size,
                embed_dim=config.embed_dim,
                hidden_dim=config.encoder_hidden_dim,
                latent_dim=config.latent_dim,
                n_layers=config.encoder_n_layers,
                dropout=config.encoder_dropout,
                n_states=config.n_states,
                kl_weight=config.kl_weight,
                pad_idx=config.pad_idx,
            )
            self.encoder = SMILESEncoder(encoder_config)
            self.decoder = TransformerSMILESDecoder(config)

        def forward(
            self,
            x: torch.Tensor,
            lengths: torch.Tensor,
            state_onehot: torch.Tensor,
            word_dropout: float = 0.0,
        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            """Full forward pass: encode, sample, decode.

            The input ``x`` is expected to contain the full sequence
            including SOS and EOS tokens.  The method internally shifts
            the sequence: ``x[:, :-1]`` is fed to the decoder as input,
            and the returned logits are aligned with ``x[:, 1:]``
            (next-token prediction targets).

            Parameters
            ----------
            x:
                Token indices of shape ``(batch, seq_len)`` including
                SOS at position 0 and EOS at the end.
            lengths:
                Actual (unpadded) lengths of shape ``(batch,)``.
            state_onehot:
                Conditioning vector of shape ``(batch, n_states)``.
            word_dropout:
                Word dropout rate for the decoder (training only).

            Returns
            -------
            tuple[Tensor, Tensor, Tensor]:
                ``(recon_logits, mu, logvar)`` where ``recon_logits``
                has shape ``(batch, seq_len - 1, vocab_size)``,
                aligned with ``x[:, 1:]``.
            """
            mu, logvar = self.encode(x, lengths, state_onehot)
            z = self.sample(mu, logvar)

            # Decoder input: everything except last token
            decoder_input = x[:, :-1]
            recon_logits = self.decoder(
                z, state_onehot, decoder_input, word_dropout,
            )
            return recon_logits, mu, logvar

        def encode(
            self,
            x: torch.Tensor,
            lengths: torch.Tensor,
            state_onehot: torch.Tensor,
        ) -> tuple[torch.Tensor, torch.Tensor]:
            """Encode input tokens to latent distribution parameters.

            Parameters
            ----------
            x:
                Token indices of shape ``(batch, seq_len)``.
            lengths:
                Actual (unpadded) lengths of shape ``(batch,)``.
            state_onehot:
                Conditioning vector of shape ``(batch, n_states)``.

            Returns
            -------
            tuple[Tensor, Tensor]:
                ``(mu, logvar)`` each of shape ``(batch, latent_dim)``.
            """
            return self.encoder(x, lengths, state_onehot)

        def sample(
            self,
            mu: torch.Tensor,
            logvar: torch.Tensor,
        ) -> torch.Tensor:
            """Reparameterization trick: sample z from N(mu, sigma^2).

            During evaluation (``model.eval()``), returns ``mu`` directly
            without sampling to ensure deterministic outputs.

            Parameters
            ----------
            mu:
                Mean of shape ``(batch, latent_dim)``.
            logvar:
                Log-variance of shape ``(batch, latent_dim)``.

            Returns
            -------
            Tensor:
                Sampled latent code of shape ``(batch, latent_dim)``.
            """
            if self.training:
                std = torch.exp(0.5 * logvar)
                eps = torch.randn_like(std)
                return mu + eps * std
            return mu

        def generate(
            self,
            z: torch.Tensor,
            state_onehot: torch.Tensor,
            max_len: int,
            temperature: float = 1.0,
            vocab: Vocabulary | None = None,
        ) -> list[list[int]]:
            """Generate token sequences from latent codes.

            Autoregressively decodes starting from the SOS token,
            using the Transformer decoder with prefix-token z injection.
            Stops at EOS or when ``max_len`` is reached.

            Parameters
            ----------
            z:
                Latent codes of shape ``(batch, latent_dim)``.
            state_onehot:
                Conditioning vector of shape ``(batch, n_states)``.
            max_len:
                Maximum number of tokens to generate per sequence.
            temperature:
                Sampling temperature.  ``0`` or negative values trigger
                greedy (argmax) decoding.
            vocab:
                Optional vocabulary for SOS/EOS indices.  If ``None``,
                SOS=1 and EOS=2 are assumed.

            Returns
            -------
            list[list[int]]:
                A list of ``batch`` token-index sequences (excluding
                SOS, including up to but not including EOS).
            """
            sos_idx = vocab.sos_idx if vocab is not None else 1
            eos_idx = vocab.eos_idx if vocab is not None else 2

            batch_size = z.shape[0]
            device = z.device
            n_prefix = self.config.n_prefix_tokens

            # --- Build prefix tokens (constant throughout generation) ---
            z_state = torch.cat([z, state_onehot], dim=-1)
            prefix = self.decoder.z_proj(z_state)
            prefix = prefix.view(
                batch_size, n_prefix, self.config.d_model,
            )

            # --- Start with SOS ---
            generated = torch.full(
                (batch_size, 1),
                sos_idx,
                dtype=torch.long,
                device=device,
            )
            sequences: list[list[int]] = [[] for _ in range(batch_size)]
            finished = [False] * batch_size

            with torch.no_grad():
                for _ in range(max_len):
                    cur_len = generated.size(1)

                    # Embed current sequence
                    embedded = self.decoder.embedding(generated)
                    embedded = self.decoder.pos_encoding(embedded)

                    # Concatenate prefix + current sequence
                    combined = torch.cat([prefix, embedded], dim=1)

                    # Causal mask
                    attn_mask = self.decoder._make_prefix_causal_mask(
                        n_prefix, cur_len, device,
                    )

                    # No padding during generation
                    output = self.decoder.transformer(
                        combined, mask=attn_mask,
                    )

                    # Logits at the last sequence position
                    last_output = output[:, n_prefix + cur_len - 1, :]
                    logits = self.decoder.output_proj(last_output)

                    # Sample or greedy
                    if temperature <= 0:
                        next_token = logits.argmax(dim=-1)
                    else:
                        scaled = logits / temperature
                        probs = functional.softmax(scaled, dim=-1)
                        next_token = torch.multinomial(
                            probs, num_samples=1,
                        ).squeeze(-1)

                    # Append to sequences, check for EOS
                    for i in range(batch_size):
                        if finished[i]:
                            continue
                        tok = next_token[i].item()
                        if tok == eos_idx:
                            finished[i] = True
                        else:
                            sequences[i].append(tok)

                    if all(finished):
                        break

                    # Append next token to generated for next iteration
                    generated = torch.cat(
                        [generated, next_token.unsqueeze(1)], dim=1,
                    )

            return sequences

    def transformer_vae_loss(
        recon_logits: torch.Tensor,
        target: torch.Tensor,
        mu: torch.Tensor,
        logvar: torch.Tensor,
        kl_weight: float = 0.01,
        pad_idx: int = 0,
        free_bits: float = 0.25,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Compute VAE loss with free-bits KL regularization.

        The reconstruction loss is cross-entropy with padding masked.
        The KL divergence uses per-dimension free bits to prevent
        posterior collapse: each latent dimension contributes at least
        ``free_bits`` nats to the KL term.

        Parameters
        ----------
        recon_logits:
            Decoder output logits ``(batch, seq_len, vocab_size)``.
        target:
            Ground-truth token indices ``(batch, seq_len)``.
        mu:
            Latent mean ``(batch, latent_dim)``.
        logvar:
            Latent log-variance ``(batch, latent_dim)``.
        kl_weight:
            Scalar multiplier for the KL term (beta).
        pad_idx:
            Padding token index to ignore in reconstruction loss.
        free_bits:
            Minimum KL per latent dimension (lambda).

        Returns
        -------
        tuple[Tensor, Tensor, Tensor]:
            ``(total_loss, recon_loss, kl_loss)`` where
            ``total_loss = recon_loss + kl_weight * kl_loss``.
        """
        # --- Reconstruction loss ---
        batch_size, seq_len, vocab_size = recon_logits.shape
        recon_flat = recon_logits.reshape(-1, vocab_size)
        target_flat = target.reshape(-1)
        recon_loss = functional.cross_entropy(
            recon_flat,
            target_flat,
            ignore_index=pad_idx,
            reduction="mean",
        )

        # --- KL divergence with free bits ---
        # Per-dimension KL: 0.5 * (mu^2 + exp(logvar) - 1 - logvar)
        kl_per_dim = 0.5 * (
            mu.pow(2) + logvar.exp() - 1.0 - logvar
        )  # (batch, latent_dim)

        # Clamp each dimension to at least free_bits
        kl_clamped = torch.clamp(kl_per_dim, min=free_bits)

        # Sum over dimensions, mean over batch
        kl_loss = kl_clamped.sum(dim=-1).mean()

        total_loss = recon_loss + kl_weight * kl_loss

        return total_loss, recon_loss, kl_loss
