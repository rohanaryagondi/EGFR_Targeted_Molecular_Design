#!/usr/bin/env python3
"""Build time-split VAE training data from MPNN time-split datasets.

Converts ``data/processed/timesplit_{cutoff}_train.json`` (SMILES + pIC50)
to VAE format (SMILES + state) by assigning conformational states using
the same inhibitor-type heuristics as ``prepare_vae_data.py``.

Outputs:
    data/processed/egfr_smiles_pre{cutoff}_train.json
    data/processed/egfr_smiles_pre{cutoff}_val.json

Usage:
    python scripts/build_timesplit_vae_data.py
    python scripts/build_timesplit_vae_data.py --cutoff 2010
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
from datetime import datetime, timezone

from statebind.data.paths import DataPaths
from statebind.ml.vae_dataset import DEFAULT_STATE_MAPPING
from statebind.utils.io import save_json

logger = logging.getLogger(__name__)

_VALID_STATES = list(DEFAULT_STATE_MAPPING.keys())

try:
    from rdkit import Chem  # type: ignore[import-untyped]

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


# ── State assignment heuristics ──────────────────────────────────────────

# Known drug SMILES → state mapping (same logic as prepare_vae_data.py)
_KNOWN_DRUG_STATES: dict[str, str] = {
    # 1st-gen Type-I (active conformation)
    "erlotinib": "DFGin_aCin",
    "gefitinib": "DFGin_aCin",
    "icotinib": "DFGin_aCin",
    # Type-I½ (inactive αC-helix)
    "lapatinib": "DFGin_aCout",
    # Type-II (DFG-out)
    "sorafenib": "DFGout_aCin",
    # 2nd-gen covalent
    "afatinib": "DFGin_aCin",
    "dacomitinib": "DFGin_aCin",
    # 3rd-gen mutant-selective
    "osimertinib": "DFGin_aCin",
    "lazertinib": "DFGin_aCin",
    "mobocertinib": "DFGin_aCin",
}


def _assign_state_heuristic(smiles: str, rng: random.Random) -> str:
    """Assign conformational state from SMILES structure heuristics.

    Uses substructure patterns to classify:
    - Quinazoline core → Type-I (DFGin_aCin)
    - Pyrimidine + acrylamide → covalent (DFGin_aCin)
    - Urea bridge + DFG motif → Type-II (DFGout_aCin)
    - Fluorobenzamide-like → Type-I½ (DFGin_aCout)
    - Otherwise → random (documented limitation)
    """
    smi = smiles.strip()

    # Quinazoline core (4-anilinoquinazoline scaffold) → Type-I
    if re.search(r"ncnc.*Nc|Nc.*ncnc", smi):
        return "DFGin_aCin"

    # Acrylamide warhead (C=CC(=O)N) → covalent binder, active conformation
    if re.search(r"C=CC\(=O\)N|C/C=C/C\(=O\)N", smi):
        return "DFGin_aCin"

    # Urea bridge (NC(=O)N) with aromatic → Type-II
    if "NC(=O)N" in smi and re.search(r"c1.*NC\(=O\)N.*c1", smi):
        return "DFGout_aCin"

    # Fluorobenzyl ether + quinazoline → Type-I½ (lapatinib-like)
    if re.search(r"OCc.*F.*ncnc|ncnc.*OCc.*F", smi):
        return "DFGin_aCout"

    # Random assignment for unknown types (documented limitation)
    return rng.choice(_VALID_STATES)


def _validate_smiles(smiles: str) -> bool:
    """Check if a SMILES string is valid."""
    if not smiles or not smiles.strip():
        return False
    if HAS_RDKIT:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    # Heuristic fallback
    if len(smiles) < 2:
        return False
    if smiles.count("(") != smiles.count(")"):
        return False
    if smiles.count("[") != smiles.count("]"):
        return False
    return True


def build_timesplit_vae_data(
    cutoff_year: int,
    train_ratio: float = 0.8,
    seed: int = 42,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Build VAE-format train/val datasets from MPNN time-split data.

    Args:
        cutoff_year: The temporal cutoff year.
        train_ratio: Fraction for training split.
        seed: Random seed.

    Returns:
        (train_records, val_records) in ``{"smiles", "state"}`` format.
    """
    paths = DataPaths()
    source_path = paths.processed_dir / f"timesplit_{cutoff_year}_train.json"

    if not source_path.exists():
        raise FileNotFoundError(
            f"Time-split dataset not found: {source_path}. "
            f"Run build_timesplit_datasets.py first."
        )

    with open(source_path) as f:
        mpnn_data = json.load(f)

    logger.info(
        "Loaded %d compounds from %s", len(mpnn_data), source_path,
    )

    rng = random.Random(seed)

    # Convert to VAE format with state assignment
    records: list[dict[str, str]] = []
    n_invalid = 0

    for entry in mpnn_data:
        smiles = entry.get("smiles", "")
        if not _validate_smiles(smiles):
            n_invalid += 1
            continue
        state = _assign_state_heuristic(smiles, rng)
        records.append({"smiles": smiles, "state": state})

    if n_invalid:
        logger.warning("Skipped %d invalid SMILES", n_invalid)

    # Shuffle and split
    rng_split = random.Random(seed)
    rng_split.shuffle(records)
    n_train = int(len(records) * train_ratio)
    train = records[:n_train]
    val = records[n_train:]

    # Save
    output_dir = paths.processed_dir
    train_path = output_dir / f"egfr_smiles_pre{cutoff_year}_train.json"
    val_path = output_dir / f"egfr_smiles_pre{cutoff_year}_val.json"
    save_json(train, train_path)
    save_json(val, val_path)

    # Print summary
    state_counts: dict[str, int] = {}
    for rec in records:
        state_counts[rec["state"]] = state_counts.get(rec["state"], 0) + 1

    print(f"\nVAE data for cutoff {cutoff_year}:")
    print(f"  Total: {len(records)} compounds")
    print(f"  Train: {len(train)}, Val: {len(val)}")
    print("  State distribution:")
    for state in sorted(state_counts):
        print(f"    {state}: {state_counts[state]}")
    print(f"  Saved: {train_path}")
    print(f"  Saved: {val_path}")

    # Save metadata
    metadata = {
        "cutoff_year": cutoff_year,
        "source": str(source_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_train": len(train),
        "n_val": len(val),
        "state_distribution": state_counts,
        "notes": (
            f"VAE training data restricted to pre-{cutoff_year} compounds. "
            f"State assignments use structural heuristics."
        ),
    }
    save_json(
        metadata,
        output_dir / f"egfr_smiles_pre{cutoff_year}_metadata.json",
    )

    return train, val


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build time-split VAE training data",
    )
    parser.add_argument(
        "--cutoff",
        type=int,
        default=None,
        help="Cutoff year (default: both 2010 and 2015)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    cutoffs = [args.cutoff] if args.cutoff else [2010, 2015]
    for c in cutoffs:
        build_timesplit_vae_data(c, seed=args.seed)


if __name__ == "__main__":
    main()
