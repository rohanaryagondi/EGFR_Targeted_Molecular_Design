#!/usr/bin/env python3
"""Prepare unconditioned training data for Ablation C (thesis test).

Reads the standard EGFR SMILES training and validation JSON files and remaps
every ``"state"`` field to ``"unconditioned"``.  This makes the one-hot
conditioning vector a constant ``[1.0]`` when the VAE is trained with
``n_states=1``, so state information carries zero signal.

Usage::

    python scripts/prepare_ablation_c_data.py
    python scripts/prepare_ablation_c_data.py \\
        --input-dir data/processed \\
        --output-dir data/processed
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TARGET_STATE = "unconditioned"


def remap_states(
    records: list[dict[str, str]],
    target_state: str = TARGET_STATE,
) -> tuple[list[dict[str, str]], Counter[str]]:
    """Remap all ``"state"`` fields to *target_state*.

    Parameters
    ----------
    records:
        List of dicts, each with at least ``"smiles"`` and ``"state"`` keys.
    target_state:
        The single state label to assign to every record.

    Returns
    -------
    tuple[list[dict[str, str]], Counter[str]]:
        The remapped records and a counter of the original state distribution.
    """
    original_counts: Counter[str] = Counter()
    remapped: list[dict[str, str]] = []

    for record in records:
        original_counts[record["state"]] += 1
        remapped.append({
            "smiles": record["smiles"],
            "state": target_state,
        })

    return remapped, original_counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare unconditioned data for Ablation C",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/processed",
        help="Directory containing egfr_smiles_train.json and egfr_smiles_val.json",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to write unconditioned JSON files",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    splits = {
        "train": "egfr_smiles_train.json",
        "val": "egfr_smiles_val.json",
    }

    print("=" * 60)
    print("  Ablation C — Unconditioned Data Preparation")
    print("=" * 60)
    print(f"  Input dir:  {input_dir}")
    print(f"  Output dir: {output_dir}")
    print(f"  Target:     all states -> '{TARGET_STATE}'")
    print("=" * 60)

    for split_name, filename in splits.items():
        input_path = input_dir / filename
        output_filename = filename.replace(
            f"egfr_smiles_{split_name}",
            f"egfr_smiles_unconditioned_{split_name}",
        )
        output_path = output_dir / output_filename

        if not input_path.exists():
            logger.error("Input file not found: %s", input_path)
            raise FileNotFoundError(f"Input file not found: {input_path}")

        logger.info("Reading %s ...", input_path)
        with open(input_path) as f:
            records: list[dict[str, str]] = json.load(f)

        remapped, original_counts = remap_states(records)

        logger.info(
            "Remapped %d %s entries to '%s':",
            len(remapped),
            split_name,
            TARGET_STATE,
        )
        for state, count in sorted(original_counts.items()):
            logger.info("  %s: %d -> %s", state, count, TARGET_STATE)

        with open(output_path, "w") as f:
            json.dump(remapped, f, indent=2)

        logger.info("Wrote %s", output_path)

    print()
    print(f"Done. Generated at {datetime.now(timezone.utc).isoformat()}")
    print("Files written:")
    for split_name, filename in splits.items():
        output_filename = filename.replace(
            f"egfr_smiles_{split_name}",
            f"egfr_smiles_unconditioned_{split_name}",
        )
        print(f"  {output_dir / output_filename}")


if __name__ == "__main__":
    main()
