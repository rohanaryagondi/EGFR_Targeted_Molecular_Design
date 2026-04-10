#!/usr/bin/env python
"""Run PMO compute-matched comparison between static and state-aware pipelines.

Implements Practical Molecular Optimization (Gao et al. 2022) by giving
each pipeline an equal oracle budget of N GNINA docking calls.

This script creates CODE infrastructure and pre-filters candidates.
Actual GNINA docking execution happens in P1-T08 (requires GPU SLURM job).

Usage:
    python scripts/run_pmo_comparison.py
    python scripts/run_pmo_comparison.py --budget 500
    python scripts/run_pmo_comparison.py --budget 1000 --output artifacts/evaluation/pmo_comparison.json
    python scripts/run_pmo_comparison.py --dry-run   # pre-filter only, no docking
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.baselines.candidates import build_candidate_library
from statebind.baselines.filtering import apply_filters
from statebind.baselines.pipeline import run_static_baseline
from statebind.evaluation.pmo_comparison import (
    PMOResult,
    compare_pmo,
    format_comparison_table,
    prefilter_score,
    run_pipeline_with_budget,
)
from statebind.generation.generator import generate_all_states


def _collect_static_candidates() -> list[str]:
    """Collect candidate SMILES from the static baseline pipeline.

    Runs structure selection, candidate generation, and filtering
    (but NOT docking -- that is the oracle).
    """
    print("[static] Building candidate library...")
    library = build_candidate_library(
        target_pdb_id="1m17",
        pocket_id="1m17_atp_site",
        enumerate_analogs=True,
    )
    print(f"[static] Generated {library.n_candidates} candidates")

    filtered = apply_filters(library)
    print(f"[static] After filtering: {filtered.n_passed}/{filtered.n_input}")

    smiles_list = [
        r.smiles for r in filtered.results if r.passed
    ]
    return smiles_list


def _collect_state_aware_candidates() -> list[str]:
    """Collect candidate SMILES from the state-aware pipeline.

    Runs multi-state generation (but NOT docking -- that is the oracle).
    """
    print("[state_aware] Generating candidates for all states...")
    gen_result = generate_all_states()
    print(
        f"[state_aware] Generated {gen_result.total_candidates} total, "
        f"{gen_result.total_unique_smiles} unique"
    )

    smiles_list = []
    for lib in gen_result.libraries:
        for c in lib.candidates:
            smiles_list.append(c.smiles)

    return smiles_list


def _stub_dock_fn(smiles: str) -> float:
    """Stub docking function for dry-run mode.

    Returns a deterministic pseudo-score based on SMILES hash.
    This is NOT a real docking score -- used only for testing the
    infrastructure without GNINA.
    """
    h = hash(smiles) % 1000
    return round(h / 1000.0, 4)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PMO compute-matched pipeline comparison"
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=500,
        help="Oracle budget (GNINA calls) per pipeline (default: 500)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/evaluation/pmo_comparison.json"),
        help="Output JSON path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use stub docking (no GNINA). Tests infrastructure only.",
    )
    parser.add_argument(
        "--sample-interval",
        type=int,
        default=10,
        help="AUC curve sampling interval (every N calls)",
    )
    args = parser.parse_args()

    if args.budget < 1:
        print(f"ERROR: --budget must be >= 1, got {args.budget}", file=sys.stderr)
        sys.exit(1)

    print("=" * 65)
    print("StateBind -- PMO Compute-Matched Comparison")
    print("=" * 65)
    print(f"  Oracle budget:    {args.budget} GNINA calls per pipeline")
    print(f"  Output:           {args.output}")
    print(f"  Dry run:          {args.dry_run}")
    print()

    # ── Select docking function ──────────────────────────────────────
    if args.dry_run:
        print("DRY RUN: Using stub docking (deterministic pseudo-scores)")
        dock_fn = _stub_dock_fn
    else:
        # Import GNINA docking -- will fail if GNINA not available
        try:
            from statebind.chemistry.docking import (
                dock_molecule,
                get_receptor_for_state,
                is_gnina_available,
                normalize_vina_score,
            )

            if not is_gnina_available():
                print(
                    "ERROR: GNINA not available. Use --dry-run for testing.",
                    file=sys.stderr,
                )
                sys.exit(1)

            receptor_info = get_receptor_for_state("DFGin_aCin")
            if receptor_info is None:
                print(
                    "ERROR: Receptor not prepared. Run receptor prep first.",
                    file=sys.stderr,
                )
                sys.exit(1)

            pdbqt_path, box_center, box_size = receptor_info

            def dock_fn(smiles: str) -> float:
                result = dock_molecule(
                    smiles, pdbqt_path, box_center, box_size,
                    exhaustiveness=8, timeout=120,
                )
                if result.success:
                    return normalize_vina_score(result.vina_score)
                return 0.0

        except ImportError:
            print(
                "ERROR: Docking module not available. Use --dry-run for testing.",
                file=sys.stderr,
            )
            sys.exit(1)

    # ── Collect candidates ───────────────────────────────────────────
    print("[1/4] Collecting static pipeline candidates...")
    static_candidates = _collect_static_candidates()
    print(f"       {len(static_candidates)} candidates ready\n")

    print("[2/4] Collecting state-aware pipeline candidates...")
    sa_candidates = _collect_state_aware_candidates()
    print(f"       {len(sa_candidates)} candidates ready\n")

    # ── Run PMO comparison ───────────────────────────────────────────
    print(f"[3/4] Running PMO with budget={args.budget}...")
    print(f"       Static: {len(static_candidates)} candidates -> top {args.budget} docked")
    static_result = run_pipeline_with_budget(
        pipeline_label="static",
        budget=args.budget,
        candidates=static_candidates,
        dock_fn=dock_fn,
        sample_interval=args.sample_interval,
    )
    print(f"       Static done: {static_result.calls_used} calls, "
          f"top-10 avg = {static_result.top_10_avg_score:.4f}\n")

    print(f"       State-aware: {len(sa_candidates)} candidates -> top {args.budget} docked")
    sa_result = run_pipeline_with_budget(
        pipeline_label="state_aware",
        budget=args.budget,
        candidates=sa_candidates,
        dock_fn=dock_fn,
        sample_interval=args.sample_interval,
    )
    print(f"       State-aware done: {sa_result.calls_used} calls, "
          f"top-10 avg = {sa_result.top_10_avg_score:.4f}\n")

    # ── Compare ──────────────────────────────────────────────────────
    print("[4/4] Comparing results...")
    comparison = compare_pmo(static_result, sa_result)

    # Print results
    print(format_comparison_table(comparison))

    # ── Write output ─────────────────────────────────────────────────
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(comparison.model_dump(mode="json"), f, indent=2, default=str)
    print(f"Results written to {args.output}")

    # ── Limitations ──────────────────────────────────────────────────
    print()
    if args.dry_run:
        print("NOTE: This was a DRY RUN with stub docking scores.")
        print("      Real GNINA docking will be executed in P1-T08 (GPU SLURM job).")
    print("IMPORTANT: PMO comparison assumes the same docking protocol for both")
    print("           pipelines.  State-aware uses 3 receptors vs 1 for static;")
    print("           budget is per-pipeline total, not per-receptor.")


if __name__ == "__main__":
    main()
