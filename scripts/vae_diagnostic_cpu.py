"""VAE enrichment failure diagnostics — CPU-only analysis tests.

Runs 7 diagnostic tests that require only RDKit and numpy (no GPU):

  TEST-C1: Training set drug proximity (can we even reach future drugs?)
  TEST-C2: Scaffold analysis (Bemis-Murcko scaffolds in training vs generated vs drugs)
  TEST-C3: Generated vs training distribution (MW, LogP, num rings, etc.)
  TEST-C4: SELFIES roundtrip fidelity (do EGFR drugs survive SMILES→SELFIES→SMILES?)
  TEST-C5: Random SELFIES baseline (how does random generation compare to VAE?)
  TEST-C6: Nearest-neighbor analysis (how close are generated mols to training set?)
  TEST-C7: Per-state analysis of existing candidates

Each test writes a JSON artifact to artifacts/evaluation/vae_diagnostics/.

Usage:
    python scripts/vae_diagnostic_cpu.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vae_diag_cpu")

OUT_DIR = REPO_ROOT / "artifacts" / "evaluation" / "vae_diagnostics"

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


def tanimoto_sim(mol_a, mol_b):
    from rdkit.Chem import AllChem, DataStructs
    fp_a = AllChem.GetMorganFingerprintAsBitVect(mol_a, 2, nBits=2048)
    fp_b = AllChem.GetMorganFingerprintAsBitVect(mol_b, 2, nBits=2048)
    return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))


def tanimoto_from_smiles(smi_a: str, smi_b: str) -> float:
    from rdkit import Chem
    from rdkit.Chem import AllChem, DataStructs
    m_a = Chem.MolFromSmiles(smi_a)
    m_b = Chem.MolFromSmiles(smi_b)
    if not m_a or not m_b:
        return 0.0
    fp_a = AllChem.GetMorganFingerprintAsBitVect(m_a, 2, nBits=2048)
    fp_b = AllChem.GetMorganFingerprintAsBitVect(m_b, 2, nBits=2048)
    return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))


def get_scaffold(mol):
    """Bemis-Murcko scaffold."""
    from rdkit.Chem.Scaffolds import MurckoScaffold
    from rdkit import Chem
    try:
        core = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(core)
    except Exception:
        return None


def mol_descriptors(mol) -> dict:
    """Compute basic descriptors."""
    from rdkit.Chem import Descriptors, Lipinski
    return {
        "mw": Descriptors.MolWt(mol),
        "logp": Descriptors.MolLogP(mol),
        "hbd": Lipinski.NumHDonors(mol),
        "hba": Lipinski.NumHAcceptors(mol),
        "tpsa": Descriptors.TPSA(mol),
        "num_rings": Lipinski.RingCount(mol),
        "num_aromatic_rings": Descriptors.NumAromaticRings(mol),
        "num_heavy_atoms": mol.GetNumHeavyAtoms(),
        "num_rotatable_bonds": Descriptors.NumRotatableBonds(mol),
    }


def main() -> None:
    from rdkit import Chem

    # ── Load data ──────────────────────────────────────────────────────
    with open(REPO_ROOT / "data" / "processed" / "egfr_smiles_train.json") as f:
        train_data = json.load(f)
    train_data_3s = [r for r in train_data if r["state"] != "DFGout_aCout"]
    train_smiles = [r["smiles"] for r in train_data_3s]
    train_smiles_set = set(train_smiles)
    logger.info("Training data: %d molecules (3-state)", len(train_smiles))

    # Load generated candidates (conditioned seed 42, as representative)
    gen_path = REPO_ROOT / "artifacts" / "generation" / "vae_conditioned_seed42.json"
    with open(gen_path) as f:
        gen_data = json.load(f)
    gen_smiles = [c["smiles"] for c in gen_data["candidates"]]
    gen_smiles_unique = list(set(gen_smiles))
    logger.info("Generated candidates (seed 42): %d total, %d unique", len(gen_smiles), len(gen_smiles_unique))

    # ===================================================================
    # TEST-C1: Training set drug proximity
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-C1: Training set drug proximity analysis")
    logger.info("=" * 60)
    t0 = time.time()

    # For each training molecule, compute max similarity to each future drug
    drug_mols = {}
    for name, smi in ALL_DRUGS.items():
        mol = Chem.MolFromSmiles(smi)
        if mol:
            drug_mols[name] = mol

    # Sample training set for speed
    rng = np.random.default_rng(42)
    n_sample = min(2000, len(train_smiles))
    sample_idx = rng.choice(len(train_smiles), size=n_sample, replace=False)
    sample_smiles = [train_smiles[i] for i in sample_idx]

    per_drug_sims: dict[str, list[float]] = {name: [] for name in ALL_DRUGS}
    max_overall_sims = []

    for smi in sample_smiles:
        mol = Chem.MolFromSmiles(smi)
        if not mol:
            continue
        best_sim = 0.0
        for name, drug_mol in drug_mols.items():
            sim = tanimoto_sim(mol, drug_mol)
            per_drug_sims[name].append(sim)
            if sim > best_sim:
                best_sim = sim
        max_overall_sims.append(best_sim)

    proximity_results = {
        "n_sampled": n_sample,
        "overall_max_sim_to_any_drug": round(max(max_overall_sims), 4),
        "overall_mean_max_sim": round(float(np.mean(max_overall_sims)), 4),
        "n_training_above_0.3": sum(1 for s in max_overall_sims if s >= 0.3),
        "n_training_above_0.4": sum(1 for s in max_overall_sims if s >= 0.4),
        "n_training_above_0.5": sum(1 for s in max_overall_sims if s >= 0.5),
        "per_drug_stats": {},
    }

    for name in ALL_DRUGS:
        sims = per_drug_sims[name]
        if sims:
            proximity_results["per_drug_stats"][name] = {
                "max_sim_in_training": round(max(sims), 4),
                "mean_sim": round(float(np.mean(sims)), 4),
                "n_above_0.3": sum(1 for s in sims if s >= 0.3),
                "n_above_0.4": sum(1 for s in sims if s >= 0.4),
            }
            logger.info("  %s: max_in_training=%.4f, n>=0.4=%d",
                         name, max(sims), sum(1 for s in sims if s >= 0.4))

    # Enrichment of random training subsets (theoretical max)
    logger.info("  Computing enrichment of random training subsets...")
    from statebind.evaluation.retrospective import (
        compute_candidate_future_similarities,
        compute_enrichment_factor,
        get_future_drugs,
    )
    future_drugs = get_future_drugs(2010)
    future_smiles = [d["smiles"] for d in future_drugs]

    ef10_values = []
    for trial in range(50):
        subset = rng.choice(sample_smiles, size=300, replace=False).tolist()
        sims = compute_candidate_future_similarities(subset, future_smiles)
        ef10 = compute_enrichment_factor(sims, threshold=0.4, top_k=10)
        ef10_values.append(ef10)

    proximity_results["random_training_subset_ef10"] = {
        "n_trials": 50,
        "subset_size": 300,
        "mean_ef10": round(float(np.mean(ef10_values)), 4),
        "max_ef10": round(float(max(ef10_values)), 4),
        "min_ef10": round(float(min(ef10_values)), 4),
        "n_nonzero": sum(1 for e in ef10_values if e > 0),
    }
    logger.info("  Random training subset EF@10: mean=%.4f, max=%.4f, nonzero=%d/50",
                float(np.mean(ef10_values)), max(ef10_values),
                sum(1 for e in ef10_values if e > 0))

    save_json({"test": "C1_training_proximity",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               **proximity_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_c1_training_proximity.json")

    # ===================================================================
    # TEST-C2: Scaffold analysis
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-C2: Bemis-Murcko scaffold analysis")
    logger.info("=" * 60)
    t0 = time.time()

    # Training scaffolds
    train_scaffolds = Counter()
    for smi in sample_smiles:
        mol = Chem.MolFromSmiles(smi)
        if mol:
            sc = get_scaffold(mol)
            if sc:
                train_scaffolds[sc] += 1

    # Generated scaffolds
    gen_scaffolds = Counter()
    for smi in gen_smiles_unique:
        mol = Chem.MolFromSmiles(smi)
        if mol:
            sc = get_scaffold(mol)
            if sc:
                gen_scaffolds[sc] += 1

    # Drug scaffolds
    drug_scaffolds = {}
    for name, smi in ALL_DRUGS.items():
        mol = Chem.MolFromSmiles(smi)
        if mol:
            drug_scaffolds[name] = get_scaffold(mol)

    # Overlap analysis
    train_scaffold_set = set(train_scaffolds.keys())
    gen_scaffold_set = set(gen_scaffolds.keys())
    drug_scaffold_set = set(drug_scaffolds.values())

    scaffold_results = {
        "n_training_scaffolds": len(train_scaffold_set),
        "n_generated_scaffolds": len(gen_scaffold_set),
        "n_drug_scaffolds": len(drug_scaffold_set),
        "overlap_gen_in_train": len(gen_scaffold_set & train_scaffold_set),
        "overlap_gen_not_in_train": len(gen_scaffold_set - train_scaffold_set),
        "frac_gen_novel_scaffolds": round(
            len(gen_scaffold_set - train_scaffold_set) / max(len(gen_scaffold_set), 1), 4),
        "drug_scaffolds_in_training": {
            name: sc in train_scaffold_set
            for name, sc in drug_scaffolds.items()
        },
        "drug_scaffolds_in_generated": {
            name: sc in gen_scaffold_set
            for name, sc in drug_scaffolds.items()
        },
        "drug_scaffold_smiles": drug_scaffolds,
        "top_10_training_scaffolds": dict(train_scaffolds.most_common(10)),
        "top_10_generated_scaffolds": dict(gen_scaffolds.most_common(10)),
    }

    for name, sc in drug_scaffolds.items():
        in_train = sc in train_scaffold_set
        in_gen = sc in gen_scaffold_set
        logger.info("  %s scaffold: %s — in_training=%s, in_generated=%s",
                     name, sc[:50] if sc else "None", in_train, in_gen)

    save_json({"test": "C2_scaffold_analysis",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               **scaffold_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_c2_scaffolds.json")

    # ===================================================================
    # TEST-C3: Generated vs training distribution
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-C3: Descriptor distribution comparison")
    logger.info("=" * 60)
    t0 = time.time()

    # Training descriptors
    train_descs = []
    for smi in sample_smiles[:1000]:
        mol = Chem.MolFromSmiles(smi)
        if mol:
            train_descs.append(mol_descriptors(mol))

    # Generated descriptors
    gen_descs = []
    for smi in gen_smiles_unique:
        mol = Chem.MolFromSmiles(smi)
        if mol:
            gen_descs.append(mol_descriptors(mol))

    # Drug descriptors
    drug_descs = {}
    for name, smi in ALL_DRUGS.items():
        mol = Chem.MolFromSmiles(smi)
        if mol:
            drug_descs[name] = mol_descriptors(mol)

    # Compare distributions
    desc_keys = ["mw", "logp", "hbd", "hba", "tpsa", "num_rings",
                 "num_aromatic_rings", "num_heavy_atoms", "num_rotatable_bonds"]
    distribution_comparison = {}
    for key in desc_keys:
        train_vals = [d[key] for d in train_descs]
        gen_vals = [d[key] for d in gen_descs]
        distribution_comparison[key] = {
            "training_mean": round(float(np.mean(train_vals)), 2),
            "training_std": round(float(np.std(train_vals)), 2),
            "generated_mean": round(float(np.mean(gen_vals)), 2),
            "generated_std": round(float(np.std(gen_vals)), 2),
            "shift": round(float(np.mean(gen_vals)) - float(np.mean(train_vals)), 2),
        }
        logger.info("  %s: training=%.1f±%.1f, generated=%.1f±%.1f, shift=%.1f",
                     key,
                     distribution_comparison[key]["training_mean"],
                     distribution_comparison[key]["training_std"],
                     distribution_comparison[key]["generated_mean"],
                     distribution_comparison[key]["generated_std"],
                     distribution_comparison[key]["shift"])

    save_json({"test": "C3_distributions",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "distribution_comparison": distribution_comparison,
               "drug_descriptors": drug_descs,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_c3_distributions.json")

    # ===================================================================
    # TEST-C4: SELFIES roundtrip fidelity
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-C4: SELFIES roundtrip fidelity for EGFR drugs")
    logger.info("=" * 60)
    t0 = time.time()

    from statebind.ml.tokenizer import SELFIESTokenizer
    sf_tok = SELFIESTokenizer()

    roundtrip_results = {}
    for name, smi in ALL_DRUGS.items():
        selfies_str = sf_tok.smiles_to_selfies(smi)
        if selfies_str is None:
            roundtrip_results[name] = {
                "original_smiles": smi,
                "selfies": None,
                "roundtrip_smiles": None,
                "roundtrip_success": False,
                "error": "SELFIES encoding failed",
            }
            continue

        roundtrip_smi = sf_tok.selfies_to_smiles(selfies_str)
        # Canonicalize both for comparison
        orig_canon = Chem.MolToSmiles(Chem.MolFromSmiles(smi)) if Chem.MolFromSmiles(smi) else smi
        rt_canon = Chem.MolToSmiles(Chem.MolFromSmiles(roundtrip_smi)) if roundtrip_smi and Chem.MolFromSmiles(roundtrip_smi) else roundtrip_smi

        # Tanimoto between original and roundtrip
        sim = tanimoto_from_smiles(smi, roundtrip_smi) if roundtrip_smi else 0.0

        # Token count
        selfies_tokens = sf_tok.tokenize(selfies_str)

        roundtrip_results[name] = {
            "original_smiles": smi,
            "canonical_smiles": orig_canon,
            "selfies": selfies_str,
            "n_selfies_tokens": len(selfies_tokens),
            "roundtrip_smiles": roundtrip_smi,
            "roundtrip_canonical": rt_canon,
            "exact_match": orig_canon == rt_canon,
            "tanimoto_similarity": round(sim, 4),
        }
        logger.info("  %s: exact_match=%s, tanimoto=%.4f, n_tokens=%d",
                     name, orig_canon == rt_canon, sim, len(selfies_tokens))

    save_json({"test": "C4_selfies_roundtrip",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "results": roundtrip_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_c4_selfies_roundtrip.json")

    # ===================================================================
    # TEST-C5: Random SELFIES baseline
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-C5: Random SELFIES baseline")
    logger.info("=" * 60)
    t0 = time.time()

    try:
        import selfies as sf
        # Generate random SELFIES
        alphabet = list(sf.get_semantic_robust_alphabet())
        n_random = 1000
        max_len_selfies = 30  # Average SELFIES length in training set

        random_smiles = []
        for _ in range(n_random):
            length = rng.integers(10, max_len_selfies + 1)
            tokens = [rng.choice(alphabet) for _ in range(length)]
            selfies_str = "".join(tokens)
            smi = sf.decoder(selfies_str)
            if smi:
                mol = Chem.MolFromSmiles(smi)
                if mol and mol.GetNumHeavyAtoms() >= 5:
                    random_smiles.append(smi)

        logger.info("  Generated %d valid random SELFIES molecules from %d attempts",
                     len(random_smiles), n_random)

        # Drug proximity of random molecules
        random_future_sims = []
        for smi in random_smiles[:300]:
            best_sim = 0.0
            for drug_smi in FUTURE_DRUGS.values():
                sim = tanimoto_from_smiles(smi, drug_smi)
                if sim > best_sim:
                    best_sim = sim
            random_future_sims.append(best_sim)

        random_baseline = {
            "n_attempted": n_random,
            "n_valid": len(random_smiles),
            "validity_rate": round(len(random_smiles) / n_random, 4),
            "max_future_drug_sim": round(max(random_future_sims) if random_future_sims else 0.0, 4),
            "mean_future_drug_sim": round(float(np.mean(random_future_sims)) if random_future_sims else 0.0, 4),
            "n_above_0.3_future": sum(1 for s in random_future_sims if s >= 0.3),
            "n_above_0.4_future": sum(1 for s in random_future_sims if s >= 0.4),
        }
        logger.info("  Random SELFIES: max_future_sim=%.4f, mean=%.4f",
                     random_baseline["max_future_drug_sim"],
                     random_baseline["mean_future_drug_sim"])

    except ImportError:
        logger.warning("selfies library not available, skipping random baseline")
        random_baseline = {"error": "selfies library not installed"}

    save_json({"test": "C5_random_baseline",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               **random_baseline,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_c5_random_baseline.json")

    # ===================================================================
    # TEST-C6: Nearest-neighbor analysis
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-C6: Nearest-neighbor to training set")
    logger.info("=" * 60)
    t0 = time.time()

    from rdkit.Chem import AllChem, DataStructs

    # Precompute training fingerprints (sample)
    train_fps = []
    train_smi_for_fps = []
    for smi in sample_smiles[:1000]:
        mol = Chem.MolFromSmiles(smi)
        if mol:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            train_fps.append(fp)
            train_smi_for_fps.append(smi)

    # For each generated molecule, find NN in training
    nn_sims = []
    for smi in gen_smiles_unique:
        mol = Chem.MolFromSmiles(smi)
        if not mol:
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
        sims = DataStructs.BulkTanimotoSimilarity(fp, train_fps)
        nn_sims.append(max(sims))

    nn_results = {
        "n_generated_tested": len(nn_sims),
        "n_training_fps": len(train_fps),
        "mean_nn_sim": round(float(np.mean(nn_sims)), 4),
        "median_nn_sim": round(float(np.median(nn_sims)), 4),
        "p25_nn_sim": round(float(np.percentile(nn_sims, 25)), 4),
        "p75_nn_sim": round(float(np.percentile(nn_sims, 75)), 4),
        "max_nn_sim": round(max(nn_sims), 4),
        "min_nn_sim": round(min(nn_sims), 4),
        "n_nn_above_0.5": sum(1 for s in nn_sims if s >= 0.5),
        "n_nn_above_0.7": sum(1 for s in nn_sims if s >= 0.7),
        "n_nn_above_0.9": sum(1 for s in nn_sims if s >= 0.9),
        "interpretation": (
            "If mean NN similarity is low (<0.3), the VAE generates molecules "
            "in a very different chemical space from training. If high (>0.7), "
            "the VAE closely reproduces training distribution."
        ),
    }
    logger.info("  NN similarity: mean=%.4f, median=%.4f, max=%.4f",
                nn_results["mean_nn_sim"], nn_results["median_nn_sim"], nn_results["max_nn_sim"])

    save_json({"test": "C6_nearest_neighbor",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               **nn_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_c6_nearest_neighbor.json")

    # ===================================================================
    # TEST-C7: Per-state analysis of existing candidates
    # ===================================================================
    logger.info("=" * 60)
    logger.info("TEST-C7: Per-state analysis of candidates across seeds")
    logger.info("=" * 60)
    t0 = time.time()

    state_analysis = {}
    for seed in [42, 123, 7]:
        cand_path = REPO_ROOT / "artifacts" / "generation" / f"vae_conditioned_seed{seed}.json"
        if not cand_path.exists():
            continue
        with open(cand_path) as f:
            cand_data = json.load(f)

        for cand in cand_data["candidates"]:
            state = cand.get("state", "unknown")
            if state not in state_analysis:
                state_analysis[state] = {"smiles": [], "seeds": []}
            state_analysis[state]["smiles"].append(cand["smiles"])
            state_analysis[state]["seeds"].append(seed)

    state_results = {}
    for state, data in state_analysis.items():
        smiles_list = data["smiles"]
        unique = list(set(smiles_list))

        # Drug proximity
        future_sims = []
        for smi in unique:
            best = 0.0
            for drug_smi in FUTURE_DRUGS.values():
                sim = tanimoto_from_smiles(smi, drug_smi)
                if sim > best:
                    best = sim
            future_sims.append(best)

        # NN to training
        state_nn_sims = []
        for smi in unique[:100]:
            mol = Chem.MolFromSmiles(smi)
            if not mol:
                continue
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            sims = DataStructs.BulkTanimotoSimilarity(fp, train_fps)
            state_nn_sims.append(max(sims))

        state_results[state] = {
            "n_total": len(smiles_list),
            "n_unique": len(unique),
            "n_seeds": len(set(data["seeds"])),
            "overlap_across_seeds": len(smiles_list) - len(unique),
            "mean_future_sim": round(float(np.mean(future_sims)) if future_sims else 0.0, 4),
            "max_future_sim": round(max(future_sims) if future_sims else 0.0, 4),
            "mean_nn_to_training": round(float(np.mean(state_nn_sims)) if state_nn_sims else 0.0, 4),
        }
        logger.info("  %s: unique=%d, max_future_sim=%.4f, mean_nn=%.4f",
                     state, len(unique),
                     state_results[state]["max_future_sim"],
                     state_results[state]["mean_nn_to_training"])

    save_json({"test": "C7_per_state",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "results": state_results,
               "time_seconds": round(time.time() - t0, 1)}, OUT_DIR / "test_c7_per_state.json")

    logger.info("")
    logger.info("=" * 60)
    logger.info("ALL CPU DIAGNOSTICS COMPLETE")
    logger.info("=" * 60)
    logger.info("Results in: %s", OUT_DIR)


if __name__ == "__main__":
    main()
