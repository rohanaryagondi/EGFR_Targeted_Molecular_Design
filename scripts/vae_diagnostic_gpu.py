"""VAE enrichment failure diagnostics — GPU tests (model inference).

Runs 8 diagnostic tests that require the trained VAE model:

  TEST-G1: Reconstruction accuracy (encode training set → decode → match rate)
  TEST-G2: Temperature sweep (generate at 7 temperatures, measure drug proximity)
  TEST-G3: Greedy decoding (temp=0 argmax, maximum-likelihood generation)
  TEST-G4: Drug seeding (encode known EGFR drugs, add noise, decode)
  TEST-G5: Conditioning effectiveness (fixed z, vary state label)
  TEST-G6: Large-batch generation (3000 molecules for statistical power)
  TEST-G7: Latent space statistics (encode training set, analyze μ/σ structure)
  TEST-G8: KL per-dimension analysis (forward pass on training batch)

Each test writes a JSON artifact to artifacts/evaluation/vae_diagnostics/.
Uses seed 42 checkpoint (healthy KL=0.66) as the primary model.

Usage:
    python scripts/vae_diagnostic_gpu.py [--seed 42] [--device auto]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vae_diag_gpu")

OUT_DIR = REPO_ROOT / "artifacts" / "evaluation" / "vae_diagnostics"

# EGFR drugs (from retrospective.py)
REFERENCE_DRUGS = {
    "erlotinib": "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
    "gefitinib": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
}
FUTURE_DRUGS = {
    "afatinib": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1",
    "osimertinib": "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
    "dacomitinib": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCCC1",
    "lazertinib": "C=CC(=O)Nc1cccc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c1OC",
    "mobocertinib": "C=CC(=O)Nc1cc(Nc2ncc(-c3cccnc3)c(-c3ccsc3)n2)c(OC)cc1N(C)CCN(C)C",
}
ALL_DRUGS = {**REFERENCE_DRUGS, **FUTURE_DRUGS}

STATE_NAMES = ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin"]


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Saved: %s", path)


def tanimoto_similarity(smi_a: str, smi_b: str) -> float:
    """Tanimoto similarity using Morgan fingerprints (radius=2, 2048 bits)."""
    from rdkit import Chem
    from rdkit.Chem import AllChem, DataStructs

    mol_a = Chem.MolFromSmiles(smi_a)
    mol_b = Chem.MolFromSmiles(smi_b)
    if mol_a is None or mol_b is None:
        return 0.0
    fp_a = AllChem.GetMorganFingerprintAsBitVect(mol_a, 2, nBits=2048)
    fp_b = AllChem.GetMorganFingerprintAsBitVect(mol_b, 2, nBits=2048)
    return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))


def max_drug_similarity(smiles: str, drug_dict: dict[str, str]) -> tuple[float, str]:
    """Return (max_tanimoto, drug_name) for the closest drug."""
    best_sim = 0.0
    best_drug = ""
    for name, drug_smi in drug_dict.items():
        sim = tanimoto_similarity(smiles, drug_smi)
        if sim > best_sim:
            best_sim = sim
            best_drug = name
    return best_sim, best_drug


def decode_sequences(model, z, state_onehot, vocab, temperature, selfies_tokenizer):
    """Decode z → token sequences → SMILES. Returns list of SMILES strings."""
    from rdkit import Chem

    token_sequences = model.generate(
        z, state_onehot, max_len=128,
        temperature=temperature, vocab=vocab,
    )

    smiles_list = []
    for seq in token_sequences:
        tokens = vocab.decode(seq, strip_special=True)
        raw = "".join(tokens)
        if not raw:
            smiles_list.append("")
            continue
        if selfies_tokenizer is not None:
            smi = selfies_tokenizer.selfies_to_smiles(raw)
            smiles_list.append(smi if smi else "")
        else:
            smiles_list.append(raw)

    valid = []
    for smi in smiles_list:
        if smi and Chem.MolFromSmiles(smi) is not None:
            valid.append(smi)
        else:
            valid.append(None)
    return smiles_list, valid


def main() -> None:
    parser = argparse.ArgumentParser(description="VAE GPU diagnostics")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    import torch
    import yaml
    from statebind.ml.vae import ConditionalSMILESVAE, VAEConfig
    from statebind.ml.vocabulary import Vocabulary
    from statebind.ml.tokenizer import SELFIESTokenizer
    from statebind.ml.utils import get_device

    device = get_device(args.device)
    logger.info("Device: %s", device)

    # ── Load model ─────────────────────────────────────────────────────
    ckpt_dir = REPO_ROOT / "artifacts" / "models" / "vae_conditioned" / f"seed_{args.seed}"
    ckpt_path = ckpt_dir / "best_model.pt"
    vocab_path = ckpt_dir / "vocabulary.json"

    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
    ckpt_config = checkpoint.get("config", {})
    use_selfies = ckpt_config.get("representation", "smiles") == "selfies"
    selfies_tok = SELFIESTokenizer() if use_selfies else None

    if "vae_config" in checkpoint and checkpoint["vae_config"]:
        vae_config = VAEConfig(**checkpoint["vae_config"])
    else:
        vae_config = VAEConfig()

    with open(vocab_path) as f:
        vocab = Vocabulary.from_json(f.read())

    model = ConditionalSMILESVAE(vae_config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    logger.info("Model loaded: %d params, vocab=%d, latent=%d, n_states=%d",
                n_params, vae_config.vocab_size, vae_config.latent_dim, vae_config.n_states)

    # ── Load training data ─────────────────────────────────────────────
    with open(REPO_ROOT / "data" / "processed" / "egfr_smiles_train.json") as f:
        train_data = json.load(f)
    # Filter to 3-state (exclude DFGout_aCout, matching model training)
    train_data = [r for r in train_data if r["state"] != "DFGout_aCout"]
    train_smiles = [r["smiles"] for r in train_data]
    logger.info("Training data: %d molecules (3-state filtered)", len(train_smiles))

    # ===================================================================
    # TEST-G1: Reconstruction accuracy
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-G1: Reconstruction accuracy")
    logger.info("=" * 60)
    t0 = time.time()

    from statebind.ml.tokenizer import SELFIESTokenizer as SFT

    sf_tok = SFT()
    state_to_idx = {s: i for i, s in enumerate(STATE_NAMES)}

    n_test = min(500, len(train_data))  # test on 500 molecules
    rng = np.random.default_rng(42)
    test_indices = rng.choice(len(train_data), size=n_test, replace=False)

    exact_matches = 0
    tanimoto_scores = []
    failed_encode = 0

    for idx in test_indices:
        rec = train_data[idx]
        smi = rec["smiles"]
        state = rec["state"]
        state_idx = state_to_idx.get(state, 0)

        # Convert SMILES → SELFIES → tokens → tensor
        selfies_str = sf_tok.smiles_to_selfies(smi)
        if selfies_str is None:
            failed_encode += 1
            continue
        selfies_tokens = sf_tok.tokenize(selfies_str)
        token_indices = vocab.encode(selfies_tokens)

        x = torch.tensor([token_indices], device=device)
        lengths = torch.tensor([len(token_indices)], device=device)
        state_oh = torch.zeros(1, vae_config.n_states, device=device)
        state_oh[0, state_idx] = 1.0

        with torch.no_grad():
            mu, logvar = model.encode(x, lengths, state_oh)
            # Decode from mu (deterministic)
            recon_seqs = model.generate(
                mu, state_oh, max_len=128, temperature=0.0, vocab=vocab,
            )

        if recon_seqs:
            recon_tokens = vocab.decode(recon_seqs[0], strip_special=True)
            recon_raw = "".join(recon_tokens)
            if use_selfies and sf_tok:
                recon_smi = sf_tok.selfies_to_smiles(recon_raw)
            else:
                recon_smi = recon_raw

            if recon_smi and recon_smi == smi:
                exact_matches += 1
            if recon_smi:
                sim = tanimoto_similarity(smi, recon_smi)
                tanimoto_scores.append(sim)
            else:
                tanimoto_scores.append(0.0)
        else:
            tanimoto_scores.append(0.0)

    recon_results = {
        "n_tested": n_test,
        "failed_encode": failed_encode,
        "exact_match_rate": round(exact_matches / max(n_test - failed_encode, 1), 4),
        "exact_matches": exact_matches,
        "mean_tanimoto_to_input": round(float(np.mean(tanimoto_scores)), 4),
        "median_tanimoto_to_input": round(float(np.median(tanimoto_scores)), 4),
        "tanimoto_p25": round(float(np.percentile(tanimoto_scores, 25)), 4),
        "tanimoto_p75": round(float(np.percentile(tanimoto_scores, 75)), 4),
        "tanimoto_below_0.5": sum(1 for t in tanimoto_scores if t < 0.5),
        "time_seconds": round(time.time() - t0, 1),
    }
    logger.info("  Exact match rate: %d/%d = %.4f",
                exact_matches, n_test - failed_encode, recon_results["exact_match_rate"])
    logger.info("  Mean Tanimoto to input: %.4f", recon_results["mean_tanimoto_to_input"])
    save_json({"test": "G1_reconstruction", "seed": args.seed,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               **recon_results}, OUT_DIR / "test_g1_reconstruction.json")

    # ===================================================================
    # TEST-G2: Temperature sweep
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-G2: Temperature sweep")
    logger.info("=" * 60)
    t0 = time.time()

    temperatures = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.2]
    n_per_temp = 300  # 100 per state × 3 states
    temp_results = {}

    for temp in temperatures:
        logger.info("  Generating at temperature=%.1f...", temp)
        all_smi = []
        all_valid = []

        for state_idx in range(vae_config.n_states):
            n_gen = n_per_temp // vae_config.n_states
            state_oh = torch.zeros(n_gen, vae_config.n_states, device=device)
            state_oh[:, state_idx] = 1.0
            z = torch.randn(n_gen, vae_config.latent_dim, device=device)
            if temp <= 0:
                z = torch.zeros_like(z)  # For greedy: use z=0 (prior mean)

            raw_smi, valid_smi = decode_sequences(
                model, z, state_oh, vocab, max(temp, -1.0), selfies_tok
            )
            all_smi.extend(raw_smi)
            all_valid.extend(valid_smi)

        valid_smiles = [s for s in all_valid if s is not None]
        unique_smiles = list(set(valid_smiles))

        # Max similarity to future drugs
        future_sims = []
        for smi in unique_smiles[:200]:  # cap at 200 for speed
            sim, _ = max_drug_similarity(smi, FUTURE_DRUGS)
            future_sims.append(sim)

        # Max similarity to reference drugs
        ref_sims = []
        for smi in unique_smiles[:200]:
            sim, _ = max_drug_similarity(smi, REFERENCE_DRUGS)
            ref_sims.append(sim)

        temp_results[str(temp)] = {
            "n_generated": len(all_smi),
            "n_valid": len(valid_smiles),
            "n_unique": len(unique_smiles),
            "validity_rate": round(len(valid_smiles) / max(len(all_smi), 1), 4),
            "uniqueness_rate": round(len(unique_smiles) / max(len(valid_smiles), 1), 4),
            "max_future_drug_sim": round(max(future_sims) if future_sims else 0.0, 4),
            "mean_future_drug_sim": round(float(np.mean(future_sims)) if future_sims else 0.0, 4),
            "p90_future_drug_sim": round(float(np.percentile(future_sims, 90)) if future_sims else 0.0, 4),
            "max_ref_drug_sim": round(max(ref_sims) if ref_sims else 0.0, 4),
            "mean_ref_drug_sim": round(float(np.mean(ref_sims)) if ref_sims else 0.0, 4),
            "n_above_0.3_future": sum(1 for s in future_sims if s >= 0.3),
            "n_above_0.4_future": sum(1 for s in future_sims if s >= 0.4),
        }
        logger.info("    valid=%d, unique=%d, max_future_sim=%.4f, max_ref_sim=%.4f",
                     len(valid_smiles), len(unique_smiles),
                     temp_results[str(temp)]["max_future_drug_sim"],
                     temp_results[str(temp)]["max_ref_drug_sim"])

    save_json({"test": "G2_temperature_sweep", "seed": args.seed,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "temperatures": temp_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_g2_temperature_sweep.json")

    # ===================================================================
    # TEST-G3: Greedy decoding from prior mean (z=0)
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-G3: Greedy decoding from z=0")
    logger.info("=" * 60)
    t0 = time.time()

    greedy_results = {}
    for state_idx, state_name in enumerate(STATE_NAMES):
        z_zero = torch.zeros(1, vae_config.latent_dim, device=device)
        state_oh = torch.zeros(1, vae_config.n_states, device=device)
        state_oh[0, state_idx] = 1.0

        raw_smi, valid_smi = decode_sequences(
            model, z_zero, state_oh, vocab, -1.0, selfies_tok  # negative temp = greedy
        )
        smi = valid_smi[0] if valid_smi[0] else raw_smi[0]

        future_sim, future_drug = max_drug_similarity(smi, FUTURE_DRUGS) if smi else (0.0, "")
        ref_sim, ref_drug = max_drug_similarity(smi, REFERENCE_DRUGS) if smi else (0.0, "")

        greedy_results[state_name] = {
            "smiles": smi,
            "is_valid": valid_smi[0] is not None,
            "max_future_sim": round(future_sim, 4),
            "closest_future_drug": future_drug,
            "max_ref_sim": round(ref_sim, 4),
            "closest_ref_drug": ref_drug,
        }
        logger.info("  %s: %s (future_sim=%.4f→%s, ref_sim=%.4f→%s)",
                     state_name, smi[:60] if smi else "EMPTY",
                     future_sim, future_drug, ref_sim, ref_drug)

    save_json({"test": "G3_greedy_decoding", "seed": args.seed,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "note": "Greedy (argmax) decoding from z=0 with each state label",
               "results": greedy_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_g3_greedy_decoding.json")

    # ===================================================================
    # TEST-G4: Drug seeding (encode known drugs → perturb → decode)
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-G4: Drug seeding — encode-perturb-decode")
    logger.info("=" * 60)
    t0 = time.time()

    noise_scales = [0.0, 0.1, 0.3, 0.5, 1.0, 2.0]
    n_samples_per_scale = 20
    drug_seed_results = {}

    for drug_name, drug_smi in ALL_DRUGS.items():
        logger.info("  Encoding %s...", drug_name)

        # Encode drug to latent space
        selfies_str = sf_tok.smiles_to_selfies(drug_smi)
        if selfies_str is None:
            drug_seed_results[drug_name] = {"error": "SELFIES encoding failed"}
            continue

        selfies_tokens = sf_tok.tokenize(selfies_str)
        token_indices = vocab.encode(selfies_tokens)
        x = torch.tensor([token_indices], device=device)
        lengths = torch.tensor([len(token_indices)], device=device)

        # Use DFGin_aCin state (all EGFR drugs are DFGin_aCin)
        state_oh = torch.zeros(1, vae_config.n_states, device=device)
        state_oh[0, 0] = 1.0

        with torch.no_grad():
            mu, logvar = model.encode(x, lengths, state_oh)

        drug_results = {"latent_norm": round(float(mu.norm().item()), 4)}

        for scale in noise_scales:
            z_batch = mu.repeat(n_samples_per_scale, 1)
            if scale > 0:
                noise = torch.randn_like(z_batch) * scale
                z_batch = z_batch + noise

            state_oh_batch = state_oh.repeat(n_samples_per_scale, 1)
            raw_smi, valid_smi = decode_sequences(
                model, z_batch, state_oh_batch, vocab, 0.8, selfies_tok
            )

            valid_smiles = [s for s in valid_smi if s is not None]
            # Similarity back to the seed drug
            seed_sims = [tanimoto_similarity(s, drug_smi) for s in valid_smiles]
            # Similarity to future drugs
            future_sims = [max_drug_similarity(s, FUTURE_DRUGS)[0] for s in valid_smiles]

            drug_results[f"noise_{scale}"] = {
                "n_valid": len(valid_smiles),
                "mean_sim_to_seed": round(float(np.mean(seed_sims)) if seed_sims else 0.0, 4),
                "max_sim_to_seed": round(max(seed_sims) if seed_sims else 0.0, 4),
                "mean_future_sim": round(float(np.mean(future_sims)) if future_sims else 0.0, 4),
                "max_future_sim": round(max(future_sims) if future_sims else 0.0, 4),
                "example_smiles": valid_smiles[:3] if valid_smiles else [],
            }
            logger.info("    noise=%.1f: valid=%d, sim_to_seed=%.4f, future_sim=%.4f",
                         scale, len(valid_smiles),
                         drug_results[f"noise_{scale}"]["mean_sim_to_seed"],
                         drug_results[f"noise_{scale}"]["max_future_sim"])

        drug_seed_results[drug_name] = drug_results

    save_json({"test": "G4_drug_seeding", "seed": args.seed,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "note": "Encode known drugs → add Gaussian noise at various scales → decode",
               "results": drug_seed_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_g4_drug_seeding.json")

    # ===================================================================
    # TEST-G5: Conditioning effectiveness
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-G5: Conditioning effectiveness")
    logger.info("=" * 60)
    t0 = time.time()

    n_fixed_z = 50
    torch.manual_seed(42)
    fixed_z = torch.randn(n_fixed_z, vae_config.latent_dim, device=device)

    state_outputs: dict[str, list[str]] = {}
    for state_idx, state_name in enumerate(STATE_NAMES):
        state_oh = torch.zeros(n_fixed_z, vae_config.n_states, device=device)
        state_oh[:, state_idx] = 1.0
        raw_smi, valid_smi = decode_sequences(
            model, fixed_z, state_oh, vocab, 0.8, selfies_tok
        )
        state_outputs[state_name] = [s if s else "" for s in raw_smi]

    # Measure overlap: for each z, check if same SMILES across states
    n_identical_across_all = 0
    n_identical_pairwise = 0
    n_pairs = 0
    for i in range(n_fixed_z):
        outputs_i = [state_outputs[s][i] for s in STATE_NAMES]
        if len(set(outputs_i)) == 1 and outputs_i[0]:
            n_identical_across_all += 1
        for a in range(len(STATE_NAMES)):
            for b in range(a + 1, len(STATE_NAMES)):
                n_pairs += 1
                if outputs_i[a] == outputs_i[b] and outputs_i[a]:
                    n_identical_pairwise += 1

    cond_results = {
        "n_fixed_z": n_fixed_z,
        "n_identical_all_states": n_identical_across_all,
        "frac_identical_all_states": round(n_identical_across_all / n_fixed_z, 4),
        "n_identical_pairwise": n_identical_pairwise,
        "n_pairs_total": n_pairs,
        "frac_identical_pairwise": round(n_identical_pairwise / max(n_pairs, 1), 4),
        "interpretation": (
            "If frac_identical_all_states is high (>0.5), conditioning has no effect — "
            "the model ignores the state label. If low (<0.1), conditioning works."
        ),
    }
    logger.info("  Identical across all states: %d/%d = %.4f",
                n_identical_across_all, n_fixed_z, cond_results["frac_identical_all_states"])

    save_json({"test": "G5_conditioning", "seed": args.seed,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               **cond_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_g5_conditioning.json")

    # ===================================================================
    # TEST-G6: Large-batch generation (3000 molecules)
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-G6: Large-batch generation (3000 molecules)")
    logger.info("=" * 60)
    t0 = time.time()

    n_large = 1000  # per state
    all_large_smiles = []

    for state_idx, state_name in enumerate(STATE_NAMES):
        logger.info("  Generating %d for %s...", n_large, state_name)
        state_oh = torch.zeros(n_large, vae_config.n_states, device=device)
        state_oh[:, state_idx] = 1.0
        z = torch.randn(n_large, vae_config.latent_dim, device=device)
        raw_smi, valid_smi = decode_sequences(
            model, z, state_oh, vocab, 0.8, selfies_tok
        )
        for s in valid_smi:
            if s is not None:
                all_large_smiles.append(s)

    unique_large = list(set(all_large_smiles))
    logger.info("  Total valid: %d, unique: %d", len(all_large_smiles), len(unique_large))

    # Compute similarity to every future drug for all unique molecules
    future_max_sims = []
    per_drug_max = {name: 0.0 for name in FUTURE_DRUGS}
    for smi in unique_large:
        sim, drug = max_drug_similarity(smi, FUTURE_DRUGS)
        future_max_sims.append(sim)
        if sim > per_drug_max.get(drug, 0.0):
            per_drug_max[drug] = sim

    # Also check reference drugs
    ref_max_sims = []
    for smi in unique_large:
        sim, _ = max_drug_similarity(smi, REFERENCE_DRUGS)
        ref_max_sims.append(sim)

    large_batch_results = {
        "n_generated": n_large * len(STATE_NAMES),
        "n_valid": len(all_large_smiles),
        "n_unique": len(unique_large),
        "future_drug_proximity": {
            "max_sim": round(max(future_max_sims) if future_max_sims else 0.0, 4),
            "mean_sim": round(float(np.mean(future_max_sims)) if future_max_sims else 0.0, 4),
            "p90_sim": round(float(np.percentile(future_max_sims, 90)) if future_max_sims else 0.0, 4),
            "p99_sim": round(float(np.percentile(future_max_sims, 99)) if future_max_sims else 0.0, 4),
            "n_above_0.3": sum(1 for s in future_max_sims if s >= 0.3),
            "n_above_0.4": sum(1 for s in future_max_sims if s >= 0.4),
            "per_drug_max_sim": {k: round(v, 4) for k, v in per_drug_max.items()},
        },
        "reference_drug_proximity": {
            "max_sim": round(max(ref_max_sims) if ref_max_sims else 0.0, 4),
            "mean_sim": round(float(np.mean(ref_max_sims)) if ref_max_sims else 0.0, 4),
            "n_above_0.3": sum(1 for s in ref_max_sims if s >= 0.3),
            "n_above_0.4": sum(1 for s in ref_max_sims if s >= 0.4),
        },
    }
    logger.info("  Max future sim: %.4f, n>=0.3: %d, n>=0.4: %d",
                large_batch_results["future_drug_proximity"]["max_sim"],
                large_batch_results["future_drug_proximity"]["n_above_0.3"],
                large_batch_results["future_drug_proximity"]["n_above_0.4"])

    # Save the unique SMILES for CPU analysis
    save_json({"test": "G6_large_batch", "seed": args.seed,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               **large_batch_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_g6_large_batch.json")
    save_json({"smiles": unique_large,
               "generated_at": datetime.now(timezone.utc).isoformat()},
              OUT_DIR / "large_batch_smiles.json")

    # ===================================================================
    # TEST-G7: Latent space statistics
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-G7: Latent space statistics")
    logger.info("=" * 60)
    t0 = time.time()

    n_encode = min(1000, len(train_data))
    encode_indices = rng.choice(len(train_data), size=n_encode, replace=False)

    all_mu = []
    all_logvar = []
    encode_states = []

    for idx in encode_indices:
        rec = train_data[idx]
        smi = rec["smiles"]
        state = rec["state"]
        state_idx = state_to_idx.get(state, 0)

        selfies_str = sf_tok.smiles_to_selfies(smi)
        if selfies_str is None:
            continue
        selfies_tokens = sf_tok.tokenize(selfies_str)
        token_indices = vocab.encode(selfies_tokens)

        x = torch.tensor([token_indices], device=device)
        lengths = torch.tensor([len(token_indices)], device=device)
        state_oh = torch.zeros(1, vae_config.n_states, device=device)
        state_oh[0, state_idx] = 1.0

        with torch.no_grad():
            mu, logvar = model.encode(x, lengths, state_oh)

        all_mu.append(mu.cpu().numpy().flatten())
        all_logvar.append(logvar.cpu().numpy().flatten())
        encode_states.append(state)

    mu_array = np.array(all_mu)
    logvar_array = np.array(all_logvar)

    # Per-dimension statistics
    mu_means = np.mean(mu_array, axis=0)
    mu_stds = np.std(mu_array, axis=0)
    logvar_means = np.mean(logvar_array, axis=0)
    sigma_means = np.exp(0.5 * logvar_means)

    # KL per dimension: 0.5 * (mu^2 + sigma^2 - 1 - log(sigma^2))
    kl_per_dim = 0.5 * (mu_means**2 + np.exp(logvar_means) - 1 - logvar_means)

    # Active dimensions (KL > 0.01)
    active_dims = int(np.sum(kl_per_dim > 0.01))
    top_kl_dims = int(np.argsort(kl_per_dim)[-10:][::-1][0])

    # Per-state centroid distances
    state_centroids = {}
    for state_name in STATE_NAMES:
        mask = [s == state_name for s in encode_states]
        if any(mask):
            state_mu = mu_array[mask]
            state_centroids[state_name] = np.mean(state_mu, axis=0)

    centroid_distances = {}
    for i, s1 in enumerate(STATE_NAMES):
        for s2 in STATE_NAMES[i + 1:]:
            if s1 in state_centroids and s2 in state_centroids:
                dist = float(np.linalg.norm(state_centroids[s1] - state_centroids[s2]))
                centroid_distances[f"{s1}_vs_{s2}"] = round(dist, 4)

    latent_results = {
        "n_encoded": len(all_mu),
        "latent_dim": vae_config.latent_dim,
        "mu_global_mean_norm": round(float(np.linalg.norm(mu_means)), 4),
        "mu_global_std_mean": round(float(np.mean(mu_stds)), 4),
        "sigma_mean": round(float(np.mean(sigma_means)), 4),
        "active_dimensions_kl_gt_0.01": active_dims,
        "total_kl_per_sample": round(float(np.mean(np.sum(
            0.5 * (mu_array**2 + np.exp(logvar_array) - 1 - logvar_array), axis=1
        ))), 4),
        "top_10_kl_dims": [int(d) for d in np.argsort(kl_per_dim)[-10:][::-1]],
        "top_10_kl_values": [round(float(kl_per_dim[d]), 4) for d in np.argsort(kl_per_dim)[-10:][::-1]],
        "state_centroid_distances": centroid_distances,
        "interpretation": (
            "active_dimensions < 10 suggests posterior collapse. "
            "state_centroid_distances near 0 means states are not separated in latent space."
        ),
    }
    logger.info("  Active dims (KL>0.01): %d/%d", active_dims, vae_config.latent_dim)
    logger.info("  Mean KL/sample: %.4f", latent_results["total_kl_per_sample"])
    logger.info("  State centroid distances: %s", centroid_distances)

    save_json({"test": "G7_latent_space", "seed": args.seed,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               **latent_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_g7_latent_space.json")

    # ===================================================================
    # TEST-G8: Cross-seed comparison (load all 3 seeds, compare)
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-G8: Cross-seed KL and generation comparison")
    logger.info("=" * 60)
    t0 = time.time()

    seed_comparison = {}
    for seed in [42, 123, 7]:
        ckpt_dir_s = REPO_ROOT / "artifacts" / "models" / "vae_conditioned" / f"seed_{seed}"
        ckpt_path_s = ckpt_dir_s / "best_model.pt"
        if not ckpt_path_s.exists():
            seed_comparison[str(seed)] = {"error": f"Checkpoint not found: {ckpt_path_s}"}
            continue

        ckpt_s = torch.load(ckpt_path_s, map_location=device, weights_only=False)
        if "vae_config" in ckpt_s and ckpt_s["vae_config"]:
            vae_cfg_s = VAEConfig(**ckpt_s["vae_config"])
        else:
            vae_cfg_s = vae_config

        model_s = ConditionalSMILESVAE(vae_cfg_s)
        model_s.load_state_dict(ckpt_s["model_state_dict"])
        model_s.to(device)
        model_s.eval()

        # Encode a small batch and measure KL
        n_kl = min(200, len(train_data))
        kl_vals = []
        for idx in range(n_kl):
            rec = train_data[idx]
            selfies_str = sf_tok.smiles_to_selfies(rec["smiles"])
            if selfies_str is None:
                continue
            selfies_tokens = sf_tok.tokenize(selfies_str)
            token_indices = vocab.encode(selfies_tokens)
            x = torch.tensor([token_indices], device=device)
            lengths = torch.tensor([len(token_indices)], device=device)
            state_idx = state_to_idx.get(rec["state"], 0)
            state_oh = torch.zeros(1, vae_config.n_states, device=device)
            state_oh[0, state_idx] = 1.0

            with torch.no_grad():
                mu, logvar = model_s.encode(x, lengths, state_oh)
                kl = 0.5 * torch.sum(mu**2 + torch.exp(logvar) - 1 - logvar).item()
                kl_vals.append(kl)

        # Generate 100 and check drug proximity
        state_oh = torch.zeros(100, vae_config.n_states, device=device)
        state_oh[:, 0] = 1.0
        z = torch.randn(100, vae_config.latent_dim, device=device)
        raw_smi, valid_smi = decode_sequences(
            model_s, z, state_oh, vocab, 0.8, selfies_tok
        )
        valid_100 = [s for s in valid_smi if s is not None]
        future_sims_100 = [max_drug_similarity(s, FUTURE_DRUGS)[0] for s in valid_100[:50]]

        seed_comparison[str(seed)] = {
            "mean_kl_per_sample": round(float(np.mean(kl_vals)), 4),
            "std_kl_per_sample": round(float(np.std(kl_vals)), 4),
            "n_valid_from_100": len(valid_100),
            "max_future_sim_50": round(max(future_sims_100) if future_sims_100 else 0.0, 4),
            "mean_future_sim_50": round(float(np.mean(future_sims_100)) if future_sims_100 else 0.0, 4),
        }
        logger.info("  Seed %d: KL=%.4f±%.4f, valid=%d/100, max_future_sim=%.4f",
                     seed, seed_comparison[str(seed)]["mean_kl_per_sample"],
                     seed_comparison[str(seed)]["std_kl_per_sample"],
                     len(valid_100),
                     seed_comparison[str(seed)]["max_future_sim_50"])

        del model_s  # free memory

    save_json({"test": "G8_cross_seed", "seed": "all",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "results": seed_comparison,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_g8_cross_seed.json")

    logger.info("")
    logger.info("=" * 60)
    logger.info("ALL GPU DIAGNOSTICS COMPLETE")
    logger.info("=" * 60)
    logger.info("Results in: %s", OUT_DIR)


if __name__ == "__main__":
    main()
