#!/usr/bin/env python
"""Wrapper script for running REINVENT 4 EGFR baseline and converting output.

Verifies prerequisites (GNINA binary, receptor file, reinvent4 env),
launches REINVENT 4 with the EGFR config, and converts the generated
SMILES into StateBind candidate format for downstream comparison.

This script should be run inside the reinvent4 conda environment.

Usage:
    python scripts/run_reinvent4_egfr.py
    python scripts/run_reinvent4_egfr.py --config configs/reinvent4_egfr.toml
    python scripts/run_reinvent4_egfr.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "configs" / "reinvent4_egfr.toml"
OUTPUT_DIR = REPO_ROOT / "artifacts" / "generation"
OUTPUT_FILE = OUTPUT_DIR / "reinvent4_egfr_candidates.json"
RECEPTOR_PATH = REPO_ROOT / "data" / "processed" / "docking" / "receptors" / "1m17.pdbqt"
GNINA_BIN = REPO_ROOT / "bin" / "gnina"


# ── Prerequisite checks ───────────────────────────────────────────────


def check_gnina() -> bool:
    """Check if GNINA binary is available."""
    if GNINA_BIN.exists() and GNINA_BIN.is_file():
        logger.info("GNINA binary found: %s", GNINA_BIN)
        return True
    path = shutil.which("gnina")
    if path is not None:
        logger.info("GNINA binary found on PATH: %s", path)
        return True
    logger.error("GNINA binary not found at %s or on PATH", GNINA_BIN)
    return False


def check_receptor() -> bool:
    """Check if the 1M17 receptor file exists."""
    if RECEPTOR_PATH.exists():
        logger.info("Receptor file found: %s", RECEPTOR_PATH)
        return True
    logger.error("Receptor file not found: %s", RECEPTOR_PATH)
    return False


def check_reinvent() -> bool:
    """Check if REINVENT 4 is importable."""
    try:
        import reinvent  # noqa: F401

        logger.info("REINVENT 4 is available")
        return True
    except ImportError:
        logger.error(
            "REINVENT 4 not importable. "
            "Ensure you are in the reinvent4 conda environment."
        )
        return False


def check_prerequisites() -> bool:
    """Run all prerequisite checks. Returns True if all pass."""
    results = [
        ("GNINA binary", check_gnina()),
        ("Receptor file", check_receptor()),
        ("REINVENT 4", check_reinvent()),
    ]
    all_ok = all(ok for _, ok in results)
    if not all_ok:
        logger.error("Prerequisite check failed:")
        for name, ok in results:
            status = "OK" if ok else "FAILED"
            logger.error("  %s: %s", name, status)
    return all_ok


# ── REINVENT 4 execution ──────────────────────────────────────────────


def run_reinvent(config_path: Path) -> int:
    """Launch REINVENT 4 with the given config.

    Args:
        config_path: Path to the REINVENT 4 TOML config file.

    Returns:
        Process return code (0 = success).
    """
    cmd = [
        sys.executable,
        "-m",
        "reinvent",
        str(config_path),
    ]

    logger.info("Running REINVENT 4: %s", " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
    )

    if proc.returncode != 0:
        logger.error("REINVENT 4 exited with code %d", proc.returncode)
    else:
        logger.info("REINVENT 4 completed successfully")

    return proc.returncode


# ── Output conversion ─────────────────────────────────────────────────


def find_reinvent_output(config_path: Path) -> Path | None:
    """Locate the REINVENT 4 output CSV with generated SMILES.

    REINVENT 4 writes summary CSVs with a prefix specified in the config.
    Searches for files matching the expected pattern.

    Args:
        config_path: Path to the config (used to derive output prefix).

    Returns:
        Path to the output CSV, or None if not found.
    """
    summary_prefix = OUTPUT_DIR / "reinvent4_egfr_summary"

    # REINVENT 4 appends suffixes like _0.csv, _1.csv, etc.
    candidates = sorted(
        OUTPUT_DIR.glob("reinvent4_egfr_summary*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if candidates:
        logger.info("Found REINVENT output: %s", candidates[0])
        return candidates[0]

    # Also check for staged_*.csv or scaffold_memory.csv patterns
    for pattern in ["reinvent4_egfr*.csv", "staged_*.csv"]:
        found = sorted(
            OUTPUT_DIR.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if found:
            logger.info("Found REINVENT output: %s", found[0])
            return found[0]

    logger.warning(
        "No REINVENT output CSV found matching prefix: %s", summary_prefix
    )
    return None


def convert_to_statebind_format(
    csv_path: Path,
    output_path: Path,
) -> dict:
    """Convert REINVENT 4 output CSV to StateBind candidate JSON.

    Reads the SMILES from REINVENT's CSV output and writes them in the
    same JSON format as artifacts/generation/vae_candidates.json.

    Args:
        csv_path: Path to REINVENT CSV with generated SMILES.
        output_path: Path to write the StateBind-format JSON.

    Returns:
        Summary statistics dict.
    """
    smiles_set: set[str] = set()
    all_smiles: list[str] = []

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # REINVENT 4 CSV has a 'SMILES' column (may vary)
            smi = row.get("SMILES") or row.get("smiles") or row.get("Smiles", "")
            smi = smi.strip()
            if smi:
                all_smiles.append(smi)
                smiles_set.add(smi)

    candidates = []
    for smi in all_smiles:
        candidates.append(
            {
                "smiles": smi,
                "state": "DFGin_aCin",
                "is_valid": True,
                "is_novel": True,
                "source": "reinvent4_rl",
            }
        )

    stats = {
        "total_generated": len(all_smiles),
        "total_unique": len(smiles_set),
        "uniqueness_rate": round(len(smiles_set) / max(len(all_smiles), 1), 4),
    }

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "REINVENT4_RL",
        "config": "configs/reinvent4_egfr.toml",
        "receptor": "1m17",
        "state": "DFGin_aCin",
        "notes": (
            "External RL baseline using REINVENT 4 with GNINA scoring. "
            "Single receptor (1M17), no state conditioning. "
            "For fair comparison with StateBind static baseline."
        ),
        "stats": stats,
        "total_candidates": len(all_smiles),
        "total_unique": len(smiles_set),
        "candidates": candidates,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(
        "Wrote %d candidates (%d unique) to %s",
        len(all_smiles),
        len(smiles_set),
        output_path,
    )
    return stats


# ── CLI ────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="Run REINVENT 4 EGFR baseline and convert output to StateBind format.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to REINVENT 4 TOML config (default: {DEFAULT_CONFIG}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help=f"Path to write StateBind candidate JSON (default: {OUTPUT_FILE}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check prerequisites only, do not run REINVENT 4.",
    )
    parser.add_argument(
        "--convert-only",
        type=Path,
        default=None,
        metavar="CSV",
        help="Skip REINVENT run; convert an existing CSV to StateBind format.",
    )
    return parser


def main() -> None:
    """Main entry point."""
    args = build_parser().parse_args()

    # Prerequisite checks
    if not check_prerequisites():
        if not args.convert_only:
            sys.exit(1)
        logger.warning(
            "Some prerequisites failed, but --convert-only specified; continuing."
        )

    if args.dry_run:
        logger.info("Dry run complete. All prerequisites passed.")
        sys.exit(0)

    # Convert-only mode
    if args.convert_only:
        if not args.convert_only.exists():
            logger.error("CSV file not found: %s", args.convert_only)
            sys.exit(1)
        stats = convert_to_statebind_format(args.convert_only, args.output)
        logger.info("Conversion stats: %s", stats)
        sys.exit(0)

    # Verify config exists
    if not args.config.exists():
        logger.error("Config file not found: %s", args.config)
        sys.exit(1)

    # Run REINVENT 4
    retcode = run_reinvent(args.config)
    if retcode != 0:
        sys.exit(retcode)

    # Find and convert output
    csv_path = find_reinvent_output(args.config)
    if csv_path is None:
        logger.error(
            "REINVENT completed but no output CSV found. "
            "Check logs/reinvent4_egfr_tb/ for details."
        )
        sys.exit(1)

    stats = convert_to_statebind_format(csv_path, args.output)
    logger.info("Pipeline complete. Stats: %s", stats)


if __name__ == "__main__":
    main()
