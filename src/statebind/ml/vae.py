"""Conditional SMILES VAE with GRU encoder and decoder.

Generates novel molecules conditioned on EGFR conformational states
(DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout).  The state
conditioning vector is concatenated to encoder inputs at every timestep
and to the latent code before projection to the decoder initial hidden
state.

Architecture::

    Input SMILES tokens -> Embedding(vocab_size, embed_dim)
                                    |
    Encoder: GRU(embed_dim + state_dim, hidden_dim, n_layers, bidirectional)
                                    |
    Latent: mu = Linear(2*hidden_dim, latent_dim)
            logvar = Linear(2*hidden_dim, latent_dim)
            z = mu + eps * exp(0.5 * logvar)   (reparameterization)
                                    |
    Decoder: z_proj = Linear(latent_dim + state_dim, hidden_dim * n_layers)
             GRU(embed_dim, hidden_dim, n_layers, teacher_forcing)
             Output: Linear(hidden_dim, vocab_size)

Classes:
    VAEConfig               -- Pydantic hyperparameter model (always available).
    SMILESEncoder           -- GRU encoder producing mu and logvar (requires torch).
    SMILESDecoder           -- GRU decoder with teacher forcing (requires torch).
    ConditionalSMILESVAE    -- Full model wrapping encoder + decoder (requires torch).

Functions:
    vae_loss                -- Reconstruction + KL divergence loss (requires torch).
"""

from __future__ import annotations

import logging
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
            "PyTorch is required for the VAE module but is not installed. "
            "Install it with: pip install torch"
        )


# ---------------------------------------------------------------------------
# Configuration (always available — no torch dependency)
# ---------------------------------------------------------------------------


class VAEConfig(BaseModel):
    """Hyperparameters for the Conditional SMILES VAE.

    All architectural and training-related hyperparameters are collected
    here so the model can be instantiated from a single config object and
    serialised alongside checkpoints for reproducibility.
    """

    vocab_size: int = 100
    embed_dim: int = 128
    hidden_dim: int = 256
    latent_dim: int = 64
    n_layers: int = 2
    dropout: float = 0.1
    n_states: int = Field(
        default=4,
        description="Number of conditioning states (EGFR conformations)",
    )
    kl_weight: float = Field(
        default=0.01,
        description="KL annealing target weight (beta)",
    )
    pad_idx: int = Field(
        default=0,
        description="Padding token index for masking",
    )


# ---------------------------------------------------------------------------
# Neural network components (only defined when torch is available)
# ---------------------------------------------------------------------------

if HAS_TORCH:

    class SMILESEncoder(nn.Module):
        """Bidirectional GRU encoder producing latent distribution parameters.

        At every timestep the state conditioning one-hot vector is
        concatenated to the token embedding, yielding input dimension
        ``embed_dim + n_states``.  The final hidden states from both
        directions are concatenated and projected to ``mu`` and ``logvar``.

        Parameters
        ----------
        config:
            A :class:`VAEConfig` with all architectural hyperparameters.
        """

        def __init__(self, config: VAEConfig) -> None:
            super().__init__()

            self.config = config

            self.embedding = nn.Embedding(
                config.vocab_size,
                config.embed_dim,
                padding_idx=config.pad_idx,
            )
            self.gru = nn.GRU(
                input_size=config.embed_dim + config.n_states,
                hidden_size=config.hidden_dim,
                num_layers=config.n_layers,
                batch_first=True,
                bidirectional=True,
                dropout=config.dropout if config.n_layers > 1 else 0.0,
            )
            # Bidirectional -> 2 * hidden_dim
            self.fc_mu = nn.Linear(
                2 * config.hidden_dim, config.latent_dim,
            )
            self.fc_logvar = nn.Linear(
                2 * config.hidden_dim, config.latent_dim,
            )

        def forward(
            self,
            x: torch.Tensor,
            lengths: torch.Tensor,
            state_onehot: torch.Tensor,
        ) -> tuple[torch.Tensor, torch.Tensor]:
            """Encode token sequences into latent distribution parameters.

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
            batch_size, seq_len = x.shape

            # Embed tokens: (batch, seq_len, embed_dim)
            embedded = self.embedding(x)

            # Expand state to every timestep: (batch, seq_len, n_states)
            state_expanded = state_onehot.unsqueeze(1).expand(
                -1, seq_len, -1,
            )

            # Concatenate: (batch, seq_len, embed_dim + n_states)
            gru_input = torch.cat([embedded, state_expanded], dim=-1)

            # Pack padded sequences for efficient GRU processing
            lengths_cpu = lengths.cpu().clamp(min=1)
            packed = nn.utils.rnn.pack_padded_sequence(
                gru_input,
                lengths_cpu,
                batch_first=True,
                enforce_sorted=False,
            )
            _, hidden = self.gru(packed)
            # hidden: (n_layers * 2, batch, hidden_dim)

            # Take final layer hidden states from both directions
            # Forward direction: hidden[-2], Backward direction: hidden[-1]
            hidden_cat = torch.cat(
                [hidden[-2], hidden[-1]], dim=-1,
            )
            # hidden_cat: (batch, 2 * hidden_dim)

            mu = self.fc_mu(hidden_cat)
            logvar = self.fc_logvar(hidden_cat)

            return mu, logvar

    class SMILESDecoder(nn.Module):
        """GRU decoder with teacher forcing and state conditioning.

        The latent code ``z`` is concatenated with the state one-hot
        vector and projected to produce the initial hidden state for all
        GRU layers.  During training, teacher forcing feeds ground-truth
        tokens as input with probability ``teacher_forcing_ratio``.

        Parameters
        ----------
        config:
            A :class:`VAEConfig` with all architectural hyperparameters.
        """

        def __init__(self, config: VAEConfig) -> None:
            super().__init__()

            self.config = config

            self.embedding = nn.Embedding(
                config.vocab_size,
                config.embed_dim,
                padding_idx=config.pad_idx,
            )
            self.gru = nn.GRU(
                input_size=config.embed_dim,
                hidden_size=config.hidden_dim,
                num_layers=config.n_layers,
                batch_first=True,
                dropout=config.dropout if config.n_layers > 1 else 0.0,
            )
            # Project (z + state) -> initial hidden for all layers
            self.z_proj = nn.Linear(
                config.latent_dim + config.n_states,
                config.hidden_dim * config.n_layers,
            )
            self.output_proj = nn.Linear(
                config.hidden_dim, config.vocab_size,
            )
            self.dropout = nn.Dropout(config.dropout)

        def forward(
            self,
            z: torch.Tensor,
            state_onehot: torch.Tensor,
            target: torch.Tensor,
            teacher_forcing_ratio: float = 0.5,
        ) -> torch.Tensor:
            """Decode latent code into token logits.

            Parameters
            ----------
            z:
                Latent code of shape ``(batch, latent_dim)``.
            state_onehot:
                Conditioning vector of shape ``(batch, n_states)``.
            target:
                Ground-truth token indices ``(batch, seq_len)`` used for
                teacher forcing.
            teacher_forcing_ratio:
                Probability of using the ground-truth token as the next
                input (1.0 = always teacher force, 0.0 = always
                autoregressive).

            Returns
            -------
            Tensor:
                Logits of shape ``(batch, seq_len, vocab_size)``.
            """
            batch_size, seq_len = target.shape

            # Project (z, state) -> initial hidden
            # -> (n_layers, batch, hidden_dim)
            z_state = torch.cat([z, state_onehot], dim=-1)
            hidden = self.z_proj(z_state)
            hidden = hidden.view(
                batch_size,
                self.config.n_layers,
                self.config.hidden_dim,
            )
            hidden = hidden.permute(1, 0, 2).contiguous()

            # Collect outputs
            outputs: list[torch.Tensor] = []

            # First input is the first token of target (should be SOS)
            input_token = target[:, 0].unsqueeze(1)  # (batch, 1)

            for t in range(seq_len):
                embedded = self.dropout(self.embedding(input_token))
                # embedded: (batch, 1, embed_dim)

                output, hidden = self.gru(embedded, hidden)
                # output: (batch, 1, hidden_dim)

                logits = self.output_proj(output)
                # logits: (batch, 1, vocab_size)
                outputs.append(logits)

                # Decide next input: teacher forcing or own prediction
                if t + 1 < seq_len:
                    use_teacher = (
                        torch.rand(1).item() < teacher_forcing_ratio
                    )
                    if use_teacher:
                        input_token = target[:, t + 1].unsqueeze(1)
                    else:
                        input_token = logits.argmax(dim=-1)
                        # input_token: (batch, 1)

            # (batch, seq_len, vocab_size)
            return torch.cat(outputs, dim=1)

    class ConditionalSMILESVAE(nn.Module):
        """Conditional SMILES VAE combining encoder and decoder.

        State conditioning (a one-hot vector over EGFR conformational
        states) is injected at two points:

        1. **Encoder** -- concatenated to token embeddings at every
           timestep.
        2. **Decoder** -- concatenated to the latent code ``z`` before
           projection to the initial GRU hidden state.

        Parameters
        ----------
        config:
            A :class:`VAEConfig` with all architectural hyperparameters.
        """

        def __init__(self, config: VAEConfig) -> None:
            super().__init__()

            self.config = config
            self.encoder = SMILESEncoder(config)
            self.decoder = SMILESDecoder(config)

        def forward(
            self,
            x: torch.Tensor,
            lengths: torch.Tensor,
            state_onehot: torch.Tensor,
            teacher_forcing_ratio: float = 0.5,
        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            """Full forward pass: encode, sample, decode.

            Parameters
            ----------
            x:
                Token indices of shape ``(batch, seq_len)``.
            lengths:
                Actual (unpadded) lengths of shape ``(batch,)``.
            state_onehot:
                Conditioning vector of shape ``(batch, n_states)``.
            teacher_forcing_ratio:
                Probability of teacher forcing during decoding.

            Returns
            -------
            tuple[Tensor, Tensor, Tensor]:
                ``(recon_logits, mu, logvar)`` where ``recon_logits``
                has shape ``(batch, seq_len, vocab_size)``.
            """
            mu, logvar = self.encode(x, lengths, state_onehot)
            z = self.sample(mu, logvar)
            recon_logits = self.decoder(
                z, state_onehot, x, teacher_forcing_ratio,
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
                Mean of the latent distribution, shape
                ``(batch, latent_dim)``.
            logvar:
                Log-variance of the latent distribution, shape
                ``(batch, latent_dim)``.

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

            Autoregressively decodes starting from the SOS token.  Stops
            at the EOS token or when ``max_len`` is reached.

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
                greedy (argmax) decoding.  Positive values scale logits
                before sampling from the categorical distribution.
            vocab:
                Optional vocabulary used to detect the SOS/EOS indices.
                If ``None``, SOS=1 and EOS=2 are assumed (matching
                :class:`statebind.ml.vocabulary.Vocabulary` defaults).

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

            # Project (z, state) -> initial hidden
            z_state = torch.cat([z, state_onehot], dim=-1)
            hidden = self.decoder.z_proj(z_state)
            hidden = hidden.view(
                batch_size,
                self.config.n_layers,
                self.config.hidden_dim,
            )
            hidden = hidden.permute(1, 0, 2).contiguous()

            # Start with SOS
            input_token = torch.full(
                (batch_size, 1),
                sos_idx,
                dtype=torch.long,
                device=device,
            )

            # Track generated sequences and completion
            sequences: list[list[int]] = [
                [] for _ in range(batch_size)
            ]
            finished = [False] * batch_size

            with torch.no_grad():
                for _ in range(max_len):
                    embedded = self.decoder.embedding(input_token)
                    # embedded: (batch, 1, embed_dim)

                    output, hidden = self.decoder.gru(
                        embedded, hidden,
                    )
                    # output: (batch, 1, hidden_dim)

                    logits = self.decoder.output_proj(
                        output,
                    ).squeeze(1)
                    # logits: (batch, vocab_size)

                    if temperature <= 0:
                        # Greedy decoding
                        next_token = logits.argmax(dim=-1)
                    else:
                        # Temperature-scaled sampling
                        scaled = logits / temperature
                        probs = functional.softmax(scaled, dim=-1)
                        next_token = torch.multinomial(
                            probs, num_samples=1,
                        ).squeeze(-1)

                    # next_token: (batch,)
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

                    input_token = next_token.unsqueeze(1)

            return sequences

    def vae_loss(
        recon_logits: torch.Tensor,
        target: torch.Tensor,
        mu: torch.Tensor,
        logvar: torch.Tensor,
        kl_weight: float = 0.01,
        pad_idx: int = 0,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Compute VAE loss: reconstruction CE + weighted KL divergence.

        The reconstruction loss is computed per-token using cross-entropy
        with padding tokens masked out.  The KL divergence is the
        closed-form KL between the learned posterior N(mu, sigma^2) and
        the standard normal prior N(0, I), averaged over the batch.

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
            Scalar multiplier for the KL term (beta in beta-VAE).
        pad_idx:
            Padding token index to ignore in reconstruction loss.

        Returns
        -------
        tuple[Tensor, Tensor, Tensor]:
            ``(total_loss, recon_loss, kl_loss)`` where
            ``total_loss = recon_loss + kl_weight * kl_loss``.
            All are scalar tensors.
        """
        # Reconstruction loss: cross-entropy, ignoring padding
        batch_size, seq_len, vocab_size = recon_logits.shape
        recon_flat = recon_logits.view(-1, vocab_size)
        target_flat = target.view(-1)
        recon_loss = functional.cross_entropy(
            recon_flat,
            target_flat,
            ignore_index=pad_idx,
            reduction="mean",
        )

        # KL divergence: -0.5 * sum(1 + logvar - mu^2 - exp(logvar))
        # Averaged over the batch
        kl_loss = -0.5 * torch.mean(
            torch.sum(
                1.0 + logvar - mu.pow(2) - logvar.exp(), dim=-1,
            )
        )

        total_loss = recon_loss + kl_weight * kl_loss

        return total_loss, recon_loss, kl_loss
