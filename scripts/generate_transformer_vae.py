#!/usr/bin/env python3
"""Generate molecular candidates from the trained Conditional Transformer VAE.

For each EGFR conformational state, samples N latent vectors from the
prior N(0, I), conditions on the state one-hot, and decodes to SMILES
via autoregressive Transformer decoding.  Validates each SMILES with
RDKit (if available) and writes a JSON artifact.

This artifact is consumed by ``statebind.generation.vae_integration``
to create ``StateConditionedCandidate`` objects for the ranking pipeline.

Usage::

    python scripts/generate_transformer_vae.py \\
        --checkpoint artifacts/models/transformer_vae/best_model.pt \\
        --vocab artifacts/models/transformer_vae/vocabulary.json \\
        --n-per-state 100 --temperature 0.8
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_STATE_NAMES = ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin"]


def _resolve_state_names(
    cli_states: str | None,
    n_states: int,
) -> list[str]:
    """Determine the list of state names for generation."""
    if cli_states is not None:
        names = [s.strip() for s in cli_states.split(",") if s.strip()]
        if len(names) != n_states:
            logger.warning(
                "--states has %d names but model n_states=%d; using provided names",
                len(names),
                n_states,
            )
        return names

    if n_states == 1:
        return ["unconditioned"]
    if n_states == 3:
        return list(DEFAULT_STATE_NAMES)
    return [f"state_{i}" for i in range(n_states)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Transformer VAE candidates")
    parser.add_argument(
        "--config",
        type=str,
        default="artifacts/models/transformer_vae/config.yaml",
        help="Path to config YAML (optional, checkpoint config used as fallback)",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="artifacts/models/transformer_vae/best_model.pt",
        help="Path to Transformer VAE checkpoint",
    )
    parser.add_argument(
        "--vocab",
        type=str,
        default="artifacts/models/transformer_vae/vocabulary.json",
        help="Path to vocabulary JSON",
    )
    parser.add_argument(
        "--n-per-state",
        type=int,
        default=100,
        help="Number of samples per conformational state",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
        help="Sampling temperature (0 = greedy, >0 = stochastic)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/generation/transformer_vae_candidates.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--states",
        type=str,
        default=None,
        help=(
            "Comma-separated state names (e.g. 'unconditioned' or "
            "'DFGin_aCin,DFGin_aCout,DFGout_aCin'). "
            "If omitted, derived from checkpoint n_states."
        ),
    )
    args = parser.parse_args()

    import torch
    import yaml

    from statebind.ml.transformer_vae import (
        ConditionalTransformerVAE,
        TransformerVAEConfig,
    )
    from statebind.ml.utils import get_device
    from statebind.ml.vocabulary import Vocabulary

    # ── Load config ─────────────────────────────────────────────────
    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)
        model_cfg = raw_config.get("model", {})
    else:
        logger.warning("Config not found at %s, using checkpoint config", config_path)
        model_cfg = {}

    # ── Load checkpoint ─────────────────────────────────────────────
    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    device = get_device("auto")
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    # Reconstruct TransformerVAEConfig from checkpoint
    if "transformer_vae_config" in checkpoint and checkpoint["transformer_vae_config"]:
        tvae_config = TransformerVAEConfig(**checkpoint["transformer_vae_config"])
    elif model_cfg:
        tvae_config = TransformerVAEConfig(**model_cfg)
    else:
        tvae_config = TransformerVAEConfig()

    logger.info(
        "Transformer VAE config: vocab=%d, latent=%d, d_model=%d, layers=%d",
        tvae_config.vocab_size,
        tvae_config.latent_dim,
        tvae_config.d_model,
        tvae_config.n_decoder_layers,
    )

    # ── Load vocabulary ─────────────────────────────────────────────
    vocab_path = Path(args.vocab)
    if not vocab_path.exists():
        raise FileNotFoundError(f"Vocabulary not found: {vocab_path}")

    with open(vocab_path) as f:
        vocab = Vocabulary.from_json(f.read())
    logger.info("Vocabulary loaded: %d tokens", vocab.size)

    # ── Build and load model ────────────────────────────────────────
    model = ConditionalTransformerVAE(tvae_config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    logger.info(
        "Model loaded on %s (%d params)",
        device,
        sum(p.numel() for p in model.parameters()),
    )

    # ── Try to import RDKit for validation ──────────────────────────
    try:
        from rdkit import Chem
        HAS_RDKIT = True
        logger.info("RDKit available — will validate generated SMILES")
    except ImportError:
        HAS_RDKIT = False
        logger.warning("RDKit not available — SMILES validity not checked")

    # ── Resolve state names ────────────────────────────────────────
    state_names = _resolve_state_names(args.states, tvae_config.n_states)
    logger.info("State names: %s", state_names)

    # ── Generate candidates ─────────────────────────────────────────
    n_per_state = args.n_per_state
    temperature = args.temperature
    max_len = 128
    n_states = tvae_config.n_states

    all_candidates: list[dict] = []
    stats: dict[str, dict] = {}

    for state_idx, state_name in enumerate(state_names):
        logger.info(
            "Generating %d candidates for %s (temp=%.2f)...",
            n_per_state, state_name, temperature,
        )

        # Build state one-hot: (n_per_state, n_states)
        state_onehot = torch.zeros(n_per_state, n_states, device=device)
        state_onehot[:, state_idx] = 1.0

        # Sample from prior: z ~ N(0, I)
        z = torch.randn(n_per_state, tvae_config.latent_dim, device=device)

        # Decode
        token_sequences = model.generate(
            z, state_onehot, max_len=max_len,
            temperature=temperature, vocab=vocab,
        )

        # Convert token indices back to SMILES
        n_valid = 0
        n_unique = 0
        seen_smiles: set[str] = set()

        for seq_indices in token_sequences:
            tokens = vocab.decode(seq_indices, strip_special=True)
            smiles = "".join(tokens)

            if not smiles:
                all_candidates.append({
                    "smiles": "",
                    "state": state_name,
                    "is_valid": False,
                    "is_novel": False,
                    "source": "transformer_vae_generated",
                })
                continue

            is_valid = True
            is_novel = smiles not in seen_smiles

            if HAS_RDKIT:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    is_valid = False
                else:
                    smiles = Chem.MolToSmiles(mol)

            if is_valid:
                n_valid += 1
            if is_novel and is_valid:
                n_unique += 1
                seen_smiles.add(smiles)

            all_candidates.append({
                "smiles": smiles,
                "state": state_name,
                "is_valid": is_valid,
                "is_novel": is_novel and is_valid,
                "source": "transformer_vae_generated",
            })

        validity_rate = n_valid / max(n_per_state, 1)
        uniqueness_rate = n_unique / max(n_valid, 1) if n_valid > 0 else 0.0

        stats[state_name] = {
            "n_generated": n_per_state,
            "n_valid": n_valid,
            "n_unique": n_unique,
            "validity_rate": round(validity_rate, 4),
            "uniqueness_rate": round(uniqueness_rate, 4),
        }

        logger.info(
            "  %s: %d valid (%.1f%%), %d unique (%.1f%%)",
            state_name, n_valid, validity_rate * 100,
            n_unique, uniqueness_rate * 100,
        )

    # ── Write artifact ──────────────────────────────────────────────
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "ConditionalTransformerVAE",
        "checkpoint": str(args.checkpoint),
        "temperature": temperature,
        "n_per_state": n_per_state,
        "states": state_names,
        "stats": stats,
        "total_candidates": len(all_candidates),
        "total_valid": sum(1 for c in all_candidates if c["is_valid"]),
        "total_unique_valid": sum(s["n_unique"] for s in stats.values()),
        "candidates": all_candidates,
    }

    with open(output_path, "w") as f:
        json.dump(artifact, f, indent=2)

    logger.info("Wrote %d candidates to %s", len(all_candidates), output_path)

    # ── Summary ─────────────────────────────────────────────────────
    total_valid = artifact["total_valid"]
    total = artifact["total_candidates"]
    total_unique = artifact["total_unique_valid"]
    n_params = sum(p.numel() for p in model.parameters())
    print("\n" + "=" * 60)
    print("TRANSFORMER VAE GENERATION SUMMARY")
    print("=" * 60)
    print(f"  Model:        ConditionalTransformerVAE ({n_params:,} params)")
    print(f"  Temperature:  {temperature}")
    print(f"  Per state:    {n_per_state}")
    print(f"  Total:        {total}")
    print(f"  Valid:         {total_valid} ({total_valid / max(total, 1) * 100:.1f}%)")
    print(f"  Unique valid: {total_unique}")
    print(f"  Output:       {output_path}")
    for state_name, s in stats.items():
        print(f"    {state_name}: {s['n_valid']} valid, {s['n_unique']} unique")
    print("=" * 60)


if __name__ == "__main__":
    main()
