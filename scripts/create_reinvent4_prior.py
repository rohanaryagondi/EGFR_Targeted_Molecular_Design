#!/usr/bin/env python
"""Create a REINVENT 4 prior model from EGFR SMILES.

Builds a new REINVENT model with vocabulary learned from the EGFR SMILES
dataset. This produces an untrained model file that serves as both the
prior and the starting agent for transfer learning.

This script runs inside the reinvent4 conda environment.

Usage:
    python scripts/create_reinvent4_prior.py
    python scripts/create_reinvent4_prior.py --smiles data/processed/egfr_all_smiles.smi
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SMILES = REPO_ROOT / "data" / "processed" / "egfr_all_smiles_standardized.smi"
DEFAULT_OUTPUT = REPO_ROOT / "models" / "reinvent4_egfr_prior.model"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a REINVENT 4 prior model from SMILES.",
    )
    parser.add_argument(
        "--smiles",
        type=Path,
        default=DEFAULT_SMILES,
        help=f"Input SMILES file, one per line (default: {DEFAULT_SMILES}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output model file (default: {DEFAULT_OUTPUT}).",
    )
    args = parser.parse_args()

    if not args.smiles.exists():
        logger.error("SMILES file not found: %s", args.smiles)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Creating REINVENT 4 prior model")
    logger.info("  SMILES file: %s", args.smiles)
    logger.info("  Output:      %s", args.output)

    try:
        from reinvent.runmodes.create_model.create_reinvent import create_model
    except ImportError as exc:
        logger.error("Cannot import REINVENT 4: %s", exc)
        sys.exit(1)

    metadata = {
        "data_source": "StateBind EGFR SMILES (ChEMBL)",
        "comment": "EGFR-focused prior for StateBind baseline comparison",
    }

    model = create_model(
        num_layers=3,
        layer_size=512,
        dropout=0.0,
        max_sequence_length=256,
        cell_type="lstm",
        embedding_layer_size=256,
        layer_normalization=False,
        standardize=True,
        input_smiles_path=str(args.smiles),
        output_model_path=str(args.output),
        metadata=metadata,
    )

    logger.info("Prior model created successfully: %s", args.output)
    logger.info("  Vocabulary size: %d", len(model.vocabulary.tokens()))

    # Verify the model can be loaded
    import torch
    save_dict = torch.load(str(args.output), map_location="cpu", weights_only=False)
    logger.info("  Model type: %s", save_dict.get("model_type", "unknown"))
    logger.info("  Verification: model loads OK")


if __name__ == "__main__":
    main()
