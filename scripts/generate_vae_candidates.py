#!/usr/bin/env python3
"""Generate molecular candidates from the trained Conditional SMILES VAE.

For each of the 4 EGFR conformational states, samples N latent vectors
from the prior N(0, I), conditions on the state one-hot, and decodes to
SMILES.  Validates each SMILES with RDKit (if available) and writes a
JSON artifact at ``artifacts/generation/vae_candidates.json``.

This artifact is consumed by ``statebind.generation.vae_integration``
to create ``StateConditionedCandidate`` objects for the ranking pipeline.

Usage::

    python scripts/generate_vae_candidates.py [--config configs/vae.yaml]
        [--n-per-state 100] [--temperature 0.8]
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

# Conformational states and their one-hot indices
STATE_NAMES = ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin", "DFGout_aCout"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate VAE candidates")
    parser.add_argument(
        "--config",
        type=str,
        default="artifacts/models/vae/config.yaml",
        help="Path to VAE config YAML",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="artifacts/models/vae/best_model.pt",
        help="Path to VAE checkpoint",
    )
    parser.add_argument(
        "--vocab",
        type=str,
        default="artifacts/models/vae/vocabulary.json",
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
        default="artifacts/generation/vae_candidates.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    import torch
    import yaml

    from statebind.ml.vae import ConditionalSMILESVAE, VAEConfig
    from statebind.ml.vocabulary import Vocabulary
    from statebind.ml.utils import get_device

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

    # Detect SELFIES mode from checkpoint config
    ckpt_config = checkpoint.get("config", {})
    use_selfies = ckpt_config.get("representation", "smiles") == "selfies"
    selfies_tokenizer = None
    if use_selfies:
        from statebind.ml.tokenizer import SELFIESTokenizer
        selfies_tokenizer = SELFIESTokenizer()
        logger.info("SELFIES mode detected — will convert generated tokens to SMILES")

    # Reconstruct VAEConfig from checkpoint
    if "vae_config" in checkpoint and checkpoint["vae_config"]:
        vae_config = VAEConfig(**checkpoint["vae_config"])
    elif model_cfg:
        vae_config = VAEConfig(**model_cfg)
    else:
        vae_config = VAEConfig()

    logger.info("VAE config: vocab=%d, latent=%d, hidden=%d",
                vae_config.vocab_size, vae_config.latent_dim, vae_config.hidden_dim)

    # ── Load vocabulary ─────────────────────────────────────────────
    vocab_path = Path(args.vocab)
    if not vocab_path.exists():
        raise FileNotFoundError(f"Vocabulary not found: {vocab_path}")

    with open(vocab_path) as f:
        vocab = Vocabulary.from_json(f.read())
    logger.info("Vocabulary loaded: %d tokens", vocab.size)

    # ── Build and load model ────────────────────────────────────────
    model = ConditionalSMILESVAE(vae_config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    logger.info("Model loaded on %s (%d params)",
                device, sum(p.numel() for p in model.parameters()))

    # ── Try to import RDKit for validation ──────────────────────────
    try:
        from rdkit import Chem
        HAS_RDKIT = True
        logger.info("RDKit available — will validate generated SMILES")
    except ImportError:
        HAS_RDKIT = False
        logger.warning("RDKit not available — SMILES validity not checked")

    # ── Generate candidates ─────────────────────────────────────────
    n_per_state = args.n_per_state
    temperature = args.temperature
    max_len = 128
    n_states = vae_config.n_states

    all_candidates: list[dict] = []
    stats: dict[str, dict] = {}

    for state_idx, state_name in enumerate(STATE_NAMES):
        logger.info("Generating %d candidates for %s (temp=%.2f)...",
                     n_per_state, state_name, temperature)

        # Build state one-hot: (n_per_state, n_states)
        state_onehot = torch.zeros(n_per_state, n_states, device=device)
        state_onehot[:, state_idx] = 1.0

        # Sample from prior: z ~ N(0, I)
        z = torch.randn(n_per_state, vae_config.latent_dim, device=device)

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
            raw_str = "".join(tokens)

            if not raw_str:
                continue

            # Convert SELFIES to SMILES if in SELFIES mode
            if use_selfies and selfies_tokenizer is not None:
                smiles = selfies_tokenizer.selfies_to_smiles(raw_str)
                if smiles is None:
                    smiles = raw_str  # Keep raw for debugging
                    is_valid = False
                    is_novel = False
                    all_candidates.append({
                        "smiles": smiles,
                        "state": state_name,
                        "is_valid": False,
                        "is_novel": False,
                        "source": "conditional_smiles_vae",
                    })
                    continue
            else:
                smiles = raw_str

            is_valid = True
            is_novel = smiles not in seen_smiles

            if HAS_RDKIT:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    is_valid = False
                else:
                    # Canonicalize
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
                "source": "conditional_smiles_vae",
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

        logger.info("  %s: %d valid (%.1f%%), %d unique (%.1f%%)",
                     state_name, n_valid, validity_rate * 100,
                     n_unique, uniqueness_rate * 100)

    # ── Write artifact ──────────────────────────────────────────────
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "ConditionalSMILESVAE",
        "checkpoint": str(args.checkpoint),
        "temperature": temperature,
        "n_per_state": n_per_state,
        "states": STATE_NAMES,
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
    print("\n" + "=" * 60)
    print("VAE GENERATION SUMMARY")
    print("=" * 60)
    print(f"  Model:        ConditionalSMILESVAE ({sum(p.numel() for p in model.parameters()):,} params)")
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
