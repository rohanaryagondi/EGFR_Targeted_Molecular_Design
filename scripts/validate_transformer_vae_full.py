#!/usr/bin/env python3
"""Full validation of Transformer VAE — reconstruction + generation quality.

Runs on GPU. For each of 3 trained seeds (conditioned), tests:
  1. Reconstruction accuracy (encode training mols → decode → Tanimoto)
  2. Aromatic ring counts in generated molecules
  3. Scaffold overlap between generated and training
  4. Nearest-neighbor similarity (generated → training)
  5. Drug proximity (generated → known EGFR drugs)
  6. Latent space statistics (active dims, state separation)

Also validates the unconditioned models (3 seeds) on the same metrics.

Usage:
    python scripts/validate_transformer_vae_full.py

Output:
    artifacts/evaluation/transformer_vae_validation.json
"""

from __future__ import annotations

import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tvae_validation")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEEDS = [42, 123, 7]
COND_CHECKPOINT_DIR = REPO_ROOT / "artifacts" / "models" / "transformer_vae"
UNCOND_CHECKPOINT_DIR = REPO_ROOT / "artifacts" / "models" / "transformer_vae_unconditioned"
GENERATION_DIR = REPO_ROOT / "artifacts" / "generation"
TRAIN_DATA_PATH = REPO_ROOT / "data" / "processed" / "egfr_smiles_train.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "evaluation" / "transformer_vae_validation.json"

FUTURE_DRUGS = {
    "erlotinib": "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
    "gefitinib": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
    "afatinib": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1",
    "osimertinib": "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
    "dacomitinib": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCCC1",
    "lazertinib": "C=CC(=O)Nc1cccc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c1OC",
    "mobocertinib": "C=CC(=O)Nc1cc(Nc2ncc(-c3cccnc3)c(-c3ccsc3)n2)c(OC)cc1N(C)CCN(C)C",
}

N_RECON_TEST = 500
MAX_LEN = 128
STATE_NAMES = ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin"]


def load_json(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Saved: %s", path)


# ---------------------------------------------------------------------------
# RDKit helpers
# ---------------------------------------------------------------------------

def get_fingerprint(smiles: str):
    """Morgan fingerprint (radius 2, 2048 bits)."""
    from rdkit import Chem
    from rdkit.Chem import AllChem
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)


def tanimoto(fp1, fp2) -> float:
    from rdkit import DataStructs
    if fp1 is None or fp2 is None:
        return 0.0
    return DataStructs.TanimotoSimilarity(fp1, fp2)


def count_aromatic_rings(smiles: str) -> int | None:
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return sum(1 for ring in mol.GetRingInfo().AtomRings()
               if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring))


def get_murcko_scaffold(smiles: str) -> str | None:
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        core = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(core)
    except Exception:
        return None


def num_rings(smiles: str) -> int | None:
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return mol.GetRingInfo().NumRings()


# ---------------------------------------------------------------------------
# Model loading + reconstruction
# ---------------------------------------------------------------------------

def load_model_and_vocab(checkpoint_dir: Path, device: str):
    """Load a Transformer VAE model + vocab from a seed directory."""
    import torch
    import yaml
    from statebind.ml.transformer_vae import (
        ConditionalTransformerVAE,
        TransformerVAEConfig,
    )
    from statebind.ml.vocabulary import Vocabulary

    # Load config
    config_path = checkpoint_dir / "config.yaml"
    with open(config_path) as f:
        raw_cfg = yaml.safe_load(f)
    model_cfg = raw_cfg.get("model", raw_cfg)
    config = TransformerVAEConfig(**model_cfg)

    # Load vocab
    vocab_path = checkpoint_dir / "vocabulary.json"
    with open(vocab_path) as f:
        vocab = Vocabulary.from_json(f.read())
    config.vocab_size = vocab.size

    # Load model
    model = ConditionalTransformerVAE(config)
    ckpt_path = checkpoint_dir / "best_model.pt"
    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return model, vocab, config


def smiles_to_tensor(smiles_list: list[str], vocab, max_len: int, device: str):
    """Tokenize and encode SMILES to padded tensor."""
    import torch
    from statebind.ml.tokenizer import SMILESTokenizer

    tokenizer = SMILESTokenizer()
    all_indices = []
    all_lengths = []

    for smi in smiles_list:
        tokens = tokenizer.tokenize(smi)
        indices = vocab.encode(tokens, add_sos=True, add_eos=True)
        if len(indices) > max_len:
            indices = indices[:max_len]
        all_lengths.append(len(indices))
        all_indices.append(indices)

    # Pad
    max_actual = max(all_lengths)
    padded = []
    for indices in all_indices:
        padded.append(indices + [vocab.pad_idx] * (max_actual - len(indices)))

    x = torch.tensor(padded, dtype=torch.long, device=device)
    lengths = torch.tensor(all_lengths, dtype=torch.long, device=device)
    return x, lengths


def reconstruction_test(model, vocab, config, training_smiles: list[str],
                        n_test: int, device: str) -> dict[str, Any]:
    """Encode training molecules → decode (greedy) → measure similarity."""
    import torch
    from statebind.ml.tokenizer import SMILESTokenizer
    from rdkit import Chem

    tokenizer = SMILESTokenizer()
    test_smiles = training_smiles[:n_test]

    # Default state for reconstruction (use state 0)
    n_states = config.n_states
    state_onehot = torch.zeros(len(test_smiles), n_states, device=device)
    state_onehot[:, 0] = 1.0

    # Encode
    x, lengths = smiles_to_tensor(test_smiles, vocab, MAX_LEN, device)
    with torch.no_grad():
        mu, logvar = model.encode(x, lengths, state_onehot)
        # Use mu directly (deterministic)
        z = mu

    # Decode (greedy)
    with torch.no_grad():
        # Process in batches of 50 to avoid OOM
        all_token_seqs = []
        batch_size = 50
        for i in range(0, len(test_smiles), batch_size):
            z_batch = z[i:i+batch_size]
            state_batch = state_onehot[i:i+batch_size]
            token_seqs = model.generate(
                z_batch, state_batch, max_len=MAX_LEN,
                temperature=0.0, vocab=vocab,
            )
            all_token_seqs.extend(token_seqs)

    # Convert token indices back to SMILES
    reconstructed = []
    for token_seq in all_token_seqs:
        tokens = vocab.decode(token_seq, strip_special=True)
        smiles = tokenizer.detokenize(tokens)
        reconstructed.append(smiles)

    # Compute Tanimoto similarities
    exact_matches = 0
    tanimoto_scores = []
    valid_recon = 0
    for orig, recon in zip(test_smiles, reconstructed):
        mol_r = Chem.MolFromSmiles(recon)
        if mol_r is None:
            tanimoto_scores.append(0.0)
            continue
        valid_recon += 1
        can_orig = Chem.CanonSmiles(orig)
        can_recon = Chem.CanonSmiles(recon)
        if can_orig == can_recon:
            exact_matches += 1
            tanimoto_scores.append(1.0)
        else:
            fp_o = get_fingerprint(orig)
            fp_r = get_fingerprint(recon)
            sim = tanimoto(fp_o, fp_r)
            tanimoto_scores.append(sim)

    return {
        "n_tested": n_test,
        "exact_match_rate": round(exact_matches / n_test, 4),
        "exact_matches": exact_matches,
        "valid_reconstruction_rate": round(valid_recon / n_test, 4),
        "mean_tanimoto_to_input": round(float(np.mean(tanimoto_scores)), 4),
        "median_tanimoto_to_input": round(float(np.median(tanimoto_scores)), 4),
        "p25_tanimoto": round(float(np.percentile(tanimoto_scores, 25)), 4),
        "p75_tanimoto": round(float(np.percentile(tanimoto_scores, 75)), 4),
        "tanimoto_above_0.5": sum(1 for s in tanimoto_scores if s >= 0.5),
        "tanimoto_above_0.7": sum(1 for s in tanimoto_scores if s >= 0.7),
        "tanimoto_above_0.9": sum(1 for s in tanimoto_scores if s >= 0.9),
    }


def latent_space_analysis(model, vocab, config, training_smiles: list[str],
                          training_data: list[dict], device: str) -> dict[str, Any]:
    """Analyze latent space: active dims, state separation, KL per dim."""
    import torch

    n_encode = min(1000, len(training_smiles))
    smiles_subset = training_smiles[:n_encode]
    data_subset = training_data[:n_encode]

    # Group by state
    state_to_idx = {"DFGin_aCin": 0, "DFGin_aCout": 1, "DFGout_aCin": 2}
    n_states = config.n_states

    state_onehots = []
    for d in data_subset:
        oh = [0.0] * n_states
        s = d.get("state", "DFGin_aCin")
        oh[state_to_idx.get(s, 0)] = 1.0
        state_onehots.append(oh)

    state_tensor = torch.tensor(state_onehots, device=device)
    x, lengths = smiles_to_tensor(smiles_subset, vocab, MAX_LEN, device)

    with torch.no_grad():
        mu, logvar = model.encode(x, lengths, state_tensor)

    mu_np = mu.cpu().numpy()
    logvar_np = logvar.cpu().numpy()

    # Per-dimension KL divergence: KL(q||p) = -0.5 * (1 + logvar - mu^2 - exp(logvar))
    kl_per_dim = -0.5 * (1 + logvar_np - mu_np**2 - np.exp(logvar_np))
    mean_kl_per_dim = kl_per_dim.mean(axis=0)  # shape (latent_dim,)

    active_dims_001 = int(np.sum(mean_kl_per_dim > 0.01))
    active_dims_01 = int(np.sum(mean_kl_per_dim > 0.1))

    # State centroid distances
    state_mus = {}
    for state_name, state_idx in state_to_idx.items():
        mask = [d.get("state", "") == state_name for d in data_subset]
        if any(mask):
            state_mus[state_name] = mu_np[mask].mean(axis=0)

    centroid_dists = {}
    state_names_present = sorted(state_mus.keys())
    for i, s1 in enumerate(state_names_present):
        for s2 in state_names_present[i+1:]:
            dist = float(np.linalg.norm(state_mus[s1] - state_mus[s2]))
            centroid_dists[f"{s1}_vs_{s2}"] = round(dist, 4)

    top_kl_indices = np.argsort(mean_kl_per_dim)[::-1][:10]

    return {
        "n_encoded": n_encode,
        "latent_dim": int(config.latent_dim),
        "active_dims_kl_gt_0.01": active_dims_001,
        "active_dims_kl_gt_0.1": active_dims_01,
        "total_kl_per_sample": round(float(mean_kl_per_dim.sum()), 4),
        "mean_mu_norm": round(float(np.linalg.norm(mu_np, axis=1).mean()), 4),
        "mean_sigma": round(float(np.exp(0.5 * logvar_np).mean()), 4),
        "top_10_kl_dims": top_kl_indices.tolist(),
        "top_10_kl_values": [round(float(mean_kl_per_dim[i]), 4) for i in top_kl_indices],
        "state_centroid_distances": centroid_dists,
    }


# ---------------------------------------------------------------------------
# Generation quality analysis (from JSON artifacts)
# ---------------------------------------------------------------------------

def analyze_generation(candidates: list[dict], training_smiles: list[str],
                       label: str) -> dict[str, Any]:
    """Analyze generated molecule quality from a candidate list."""
    logger.info("  Analyzing %d candidates for %s...", len(candidates), label)

    valid_smiles = [c["smiles"] for c in candidates
                    if c.get("is_valid", True)]

    # Aromatic rings
    arom_counts = []
    ring_counts = []
    for smi in valid_smiles:
        ar = count_aromatic_rings(smi)
        if ar is not None:
            arom_counts.append(ar)
        nr = num_rings(smi)
        if nr is not None:
            ring_counts.append(nr)

    # Scaffolds
    gen_scaffolds = Counter()
    for smi in valid_smiles:
        scaf = get_murcko_scaffold(smi)
        if scaf:
            gen_scaffolds[scaf] += 1

    train_scaffolds = Counter()
    for smi in training_smiles[:2000]:
        scaf = get_murcko_scaffold(smi)
        if scaf:
            train_scaffolds[scaf] += 1

    scaffold_overlap = len(set(gen_scaffolds.keys()) & set(train_scaffolds.keys()))

    # Drug scaffolds in generated
    drug_scaffolds_found = {}
    for drug_name, drug_smi in FUTURE_DRUGS.items():
        drug_scaf = get_murcko_scaffold(drug_smi)
        drug_scaffolds_found[drug_name] = drug_scaf in gen_scaffolds if drug_scaf else False

    # NN similarity to training
    logger.info("    Computing NN similarity to training...")
    train_fps = []
    for smi in training_smiles[:2000]:
        fp = get_fingerprint(smi)
        if fp is not None:
            train_fps.append(fp)

    nn_sims = []
    for smi in valid_smiles[:500]:  # cap at 500 for speed
        fp_g = get_fingerprint(smi)
        if fp_g is None:
            continue
        best_sim = max(tanimoto(fp_g, fp_t) for fp_t in train_fps)
        nn_sims.append(best_sim)

    # Drug proximity
    logger.info("    Computing drug proximity...")
    drug_fps = {}
    for name, smi in FUTURE_DRUGS.items():
        fp = get_fingerprint(smi)
        if fp is not None:
            drug_fps[name] = fp

    per_drug_max_sim = {}
    per_drug_mean_sim = {}
    overall_drug_sims = []
    for drug_name, drug_fp in drug_fps.items():
        sims = []
        for smi in valid_smiles:
            fp_g = get_fingerprint(smi)
            sim = tanimoto(fp_g, drug_fp)
            sims.append(sim)
        per_drug_max_sim[drug_name] = round(max(sims), 4) if sims else 0.0
        per_drug_mean_sim[drug_name] = round(float(np.mean(sims)), 4) if sims else 0.0
        overall_drug_sims.extend(sims)

    n_above_03 = sum(1 for s in overall_drug_sims if s >= 0.3)
    n_above_04 = sum(1 for s in overall_drug_sims if s >= 0.4)

    return {
        "label": label,
        "n_candidates": len(candidates),
        "n_valid": len(valid_smiles),
        "n_unique_valid": len(set(valid_smiles)),
        "validity_rate": round(len(valid_smiles) / max(len(candidates), 1), 4),
        "aromatic_rings": {
            "mean": round(float(np.mean(arom_counts)), 4) if arom_counts else 0.0,
            "std": round(float(np.std(arom_counts)), 4) if arom_counts else 0.0,
            "median": round(float(np.median(arom_counts)), 4) if arom_counts else 0.0,
            "pct_with_aromatic": round(sum(1 for a in arom_counts if a > 0) / max(len(arom_counts), 1), 4),
        },
        "total_rings": {
            "mean": round(float(np.mean(ring_counts)), 4) if ring_counts else 0.0,
        },
        "scaffolds": {
            "n_unique_generated": len(gen_scaffolds),
            "n_unique_training": len(train_scaffolds),
            "overlap": scaffold_overlap,
            "overlap_rate": round(scaffold_overlap / max(len(gen_scaffolds), 1), 4),
            "top_5_generated": dict(gen_scaffolds.most_common(5)),
            "drug_scaffolds_in_generated": drug_scaffolds_found,
        },
        "nn_to_training": {
            "mean": round(float(np.mean(nn_sims)), 4) if nn_sims else 0.0,
            "median": round(float(np.median(nn_sims)), 4) if nn_sims else 0.0,
            "max": round(float(np.max(nn_sims)), 4) if nn_sims else 0.0,
            "n_above_0.3": sum(1 for s in nn_sims if s >= 0.3),
            "n_above_0.5": sum(1 for s in nn_sims if s >= 0.5),
            "n_tested": len(nn_sims),
        },
        "drug_proximity": {
            "per_drug_max_sim": per_drug_max_sim,
            "per_drug_mean_sim": per_drug_mean_sim,
            "overall_max": round(max(overall_drug_sims), 4) if overall_drug_sims else 0.0,
            "overall_mean": round(float(np.mean(overall_drug_sims)), 4) if overall_drug_sims else 0.0,
            "n_above_0.3": n_above_03,
            "n_above_0.4": n_above_04,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Device: %s", device)

    # Load training data
    logger.info("Loading training data...")
    train_data = load_json(TRAIN_DATA_PATH)
    training_smiles = [d["smiles"] for d in train_data]
    logger.info("  Training set: %d molecules", len(training_smiles))

    results: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "device": device,
        "n_training": len(training_smiles),
    }

    # ── Conditioned models (3 seeds) ──────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("CONDITIONED MODELS (3-state)")
    logger.info("=" * 60)

    cond_results = {}
    for seed in SEEDS:
        logger.info("")
        logger.info("--- Seed %d ---", seed)
        ckpt_dir = COND_CHECKPOINT_DIR / f"seed_{seed}"

        # Load model
        logger.info("  Loading model from %s", ckpt_dir)
        model, vocab, config = load_model_and_vocab(ckpt_dir, device)
        logger.info("  Model: %d params, vocab=%d, latent=%d, states=%d",
                     sum(p.numel() for p in model.parameters()),
                     config.vocab_size, config.latent_dim, config.n_states)

        # Reconstruction test
        logger.info("  Running reconstruction test (%d molecules)...", N_RECON_TEST)
        recon = reconstruction_test(model, vocab, config, training_smiles,
                                    N_RECON_TEST, device)
        logger.info("  Reconstruction: exact=%.1f%%, mean Tanimoto=%.4f",
                     recon["exact_match_rate"] * 100, recon["mean_tanimoto_to_input"])

        # Latent space analysis
        logger.info("  Latent space analysis...")
        latent = latent_space_analysis(model, vocab, config, training_smiles,
                                       train_data, device)
        logger.info("  Active dims (KL>0.01): %d, total KL/sample: %.4f",
                     latent["active_dims_kl_gt_0.01"], latent["total_kl_per_sample"])
        logger.info("  State centroid distances: %s", latent["state_centroid_distances"])

        # Generation analysis (from JSON artifacts)
        # Stochastic
        stoch_path = GENERATION_DIR / f"transformer_vae_conditioned_seed{seed}.json"
        stoch_data = load_json(stoch_path)
        stoch_cands = [c for c in stoch_data["candidates"] if c.get("is_valid", True)]
        logger.info("  Analyzing stochastic generation (%d valid)...", len(stoch_cands))
        gen_stoch = analyze_generation(stoch_cands, training_smiles,
                                       f"conditioned_seed{seed}_stochastic")

        # Greedy
        greedy_path = GENERATION_DIR / f"transformer_vae_conditioned_seed{seed}_greedy.json"
        greedy_data = load_json(greedy_path)
        greedy_cands = [c for c in greedy_data["candidates"] if c.get("is_valid", True)]
        logger.info("  Analyzing greedy generation (%d valid)...", len(greedy_cands))
        gen_greedy = analyze_generation(greedy_cands, training_smiles,
                                        f"conditioned_seed{seed}_greedy")

        cond_results[str(seed)] = {
            "reconstruction": recon,
            "latent_space": latent,
            "generation_stochastic": gen_stoch,
            "generation_greedy": gen_greedy,
        }

        # Free GPU memory
        del model
        torch.cuda.empty_cache()

    results["conditioned"] = cond_results

    # ── Unconditioned models (3 seeds) ─────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("UNCONDITIONED MODELS")
    logger.info("=" * 60)

    uncond_results = {}
    for seed in SEEDS:
        logger.info("")
        logger.info("--- Seed %d (unconditioned) ---", seed)
        ckpt_dir = UNCOND_CHECKPOINT_DIR / f"seed_{seed}"

        if not (ckpt_dir / "best_model.pt").exists():
            logger.warning("  Checkpoint not found at %s, skipping", ckpt_dir)
            continue

        model, vocab, config = load_model_and_vocab(ckpt_dir, device)

        # Reconstruction
        logger.info("  Running reconstruction test...")
        recon = reconstruction_test(model, vocab, config, training_smiles,
                                    N_RECON_TEST, device)
        logger.info("  Reconstruction: exact=%.1f%%, mean Tanimoto=%.4f",
                     recon["exact_match_rate"] * 100, recon["mean_tanimoto_to_input"])

        # Generation analysis
        stoch_path = GENERATION_DIR / f"transformer_vae_unconditioned_seed{seed}.json"
        stoch_data = load_json(stoch_path)
        stoch_cands = [c for c in stoch_data["candidates"] if c.get("is_valid", True)]
        gen_stoch = analyze_generation(stoch_cands, training_smiles,
                                       f"unconditioned_seed{seed}_stochastic")

        greedy_path = GENERATION_DIR / f"transformer_vae_unconditioned_seed{seed}_greedy.json"
        greedy_data = load_json(greedy_path)
        greedy_cands = [c for c in greedy_data["candidates"] if c.get("is_valid", True)]
        gen_greedy = analyze_generation(greedy_cands, training_smiles,
                                        f"unconditioned_seed{seed}_greedy")

        uncond_results[str(seed)] = {
            "reconstruction": recon,
            "generation_stochastic": gen_stoch,
            "generation_greedy": gen_greedy,
        }

        del model
        torch.cuda.empty_cache()

    results["unconditioned"] = uncond_results

    # ── GRU VAE comparison numbers (from diagnostics) ──────────────────
    results["gru_vae_comparison"] = {
        "note": "Numbers from artifacts/evaluation/vae_diagnostics/synthesis.json for comparison",
        "gru_reconstruction_exact_match": 0.0,
        "gru_reconstruction_mean_tanimoto": 0.031,
        "gru_aromatic_rings_mean": 0.03,
        "gru_nn_to_training_mean": 0.125,
        "gru_scaffold_overlap": 0,
        "gru_max_future_drug_sim": 0.167,
        "gru_active_latent_dims": 0,
    }

    # ── Summary ────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    for seed in SEEDS:
        sr = cond_results[str(seed)]
        logger.info("Seed %d (conditioned):", seed)
        logger.info("  Recon exact match: %.1f%% (GRU: 0.0%%)",
                     sr["reconstruction"]["exact_match_rate"] * 100)
        logger.info("  Recon mean Tanimoto: %.4f (GRU: 0.031)",
                     sr["reconstruction"]["mean_tanimoto_to_input"])
        logger.info("  Aromatic rings (greedy): %.2f (GRU: 0.03)",
                     sr["generation_greedy"]["aromatic_rings"]["mean"])
        logger.info("  Scaffold overlap (greedy): %d (GRU: 0)",
                     sr["generation_greedy"]["scaffolds"]["overlap"])
        logger.info("  NN to training (greedy): %.4f (GRU: 0.125)",
                     sr["generation_greedy"]["nn_to_training"]["mean"])
        logger.info("  Max drug sim (greedy): %.4f (GRU: 0.167)",
                     sr["generation_greedy"]["drug_proximity"]["overall_max"])
        logger.info("  Active dims KL>0.01: %d (GRU: 0)",
                     sr["latent_space"]["active_dims_kl_gt_0.01"])

    save_json(results, OUTPUT_PATH)
    logger.info("Done. Results at: %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
