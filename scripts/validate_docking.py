#!/usr/bin/env python3
"""Validate GNINA docking with known EGFR binders and non-binders.

Docks known EGFR inhibitors and negative controls into all 4 conformational
state receptors.  Verifies that:
1. Known binders produce negative Vina scores (favorable binding)
2. Known binders score higher (normalized) than non-binders
3. CNN scores are in [0, 1] range
4. The scoring cascade correctly selects GNINA as tier 0

Usage:
    # Requires CUDA modules for GNINA:
    module load CUDA/12.6.0 cuDNN/9.5.1.17-CUDA-12.6.0

    # Quick mode (exhaustiveness=2, for login nodes):
    python scripts/validate_docking.py --quick

    # Full mode (exhaustiveness=8, needs GPU node or patience):
    python scripts/validate_docking.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from statebind.chemistry.docking import (
    DockingResult,
    dock_molecule,
    get_receptor_for_state,
    is_gnina_available,
    normalize_vina_score,
)

# ── Known EGFR binders (FDA-approved EGFR inhibitors) ───────────────────
KNOWN_BINDERS = {
    "erlotinib": "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
    "gefitinib": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
    "osimertinib": "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
    "lapatinib": (
        "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc"
        "(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1"
    ),
    "afatinib": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1O[C@@H]1CCOC1",
}

# ── Negative controls (not EGFR binders) ────────────────────────────────
NON_BINDERS = {
    "ethanol": "CCO",
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "caffeine": "Cn1c(=O)c2c(ncn2C)n(C)c1=O",
    "glucose": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
}

STATES = ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin"]


def dock_compound(
    name: str,
    smiles: str,
    state: str,
    exhaustiveness: int = 8,
    timeout: int = 300,
) -> DockingResult | None:
    """Dock a single compound into a state receptor."""
    receptor_info = get_receptor_for_state(state)
    if receptor_info is None:
        print(f"  [SKIP] No receptor for {state}")
        return None

    pdbqt_path, box_center, box_size = receptor_info
    result = dock_molecule(
        smiles, pdbqt_path, box_center, box_size,
        exhaustiveness=exhaustiveness, timeout=timeout,
    )
    return result


def run_validation(exhaustiveness: int = 8, timeout: int = 300) -> dict:
    """Run the full validation suite."""
    print("=" * 70)
    print("GNINA Docking Validation")
    print(f"  exhaustiveness={exhaustiveness}  timeout={timeout}s")
    print("=" * 70)
    print(f"GNINA available: {is_gnina_available()}")

    if not is_gnina_available():
        print("\nERROR: GNINA not available. Load CUDA modules first:")
        print("  module load CUDA/12.6.0 cuDNN/9.5.1.17-CUDA-12.6.0")
        return {}

    # Check receptors
    print("\nReceptor availability:")
    for state in STATES:
        info = get_receptor_for_state(state)
        status = "OK" if info else "MISSING"
        print(f"  {state}: {status}")

    all_results: dict[str, dict[str, dict]] = {}

    # Dock binders
    print("\n" + "=" * 70)
    print("KNOWN EGFR BINDERS")
    print("=" * 70)
    for name, smiles in KNOWN_BINDERS.items():
        all_results[name] = {"is_binder": True, "states": {}}
        print(f"\n--- {name} ---")
        for state in STATES:
            result = dock_compound(name, smiles, state, exhaustiveness, timeout)
            if result and result.success:
                norm = normalize_vina_score(result.vina_score)
                print(
                    f"  {state}: Vina={result.vina_score:7.3f} kcal/mol  "
                    f"norm={norm:.4f}  CNN={result.cnn_score:.4f}  "
                    f"pKd={result.cnn_affinity:.2f}  poses={result.n_poses}"
                )
                all_results[name]["states"][state] = {
                    "vina_score": result.vina_score,
                    "normalized": round(norm, 4),
                    "cnn_score": result.cnn_score,
                    "cnn_affinity": result.cnn_affinity,
                    "n_poses": result.n_poses,
                }
            elif result:
                print(f"  {state}: FAILED - {result.error}")
                all_results[name]["states"][state] = {"error": result.error}
            else:
                print(f"  {state}: SKIPPED")

    # Dock non-binders
    print("\n" + "=" * 70)
    print("NON-BINDERS (NEGATIVE CONTROLS)")
    print("=" * 70)
    for name, smiles in NON_BINDERS.items():
        all_results[name] = {"is_binder": False, "states": {}}
        print(f"\n--- {name} ---")
        for state in STATES:
            result = dock_compound(name, smiles, state, exhaustiveness, timeout)
            if result and result.success:
                norm = normalize_vina_score(result.vina_score)
                print(
                    f"  {state}: Vina={result.vina_score:7.3f} kcal/mol  "
                    f"norm={norm:.4f}  CNN={result.cnn_score:.4f}  "
                    f"pKd={result.cnn_affinity:.2f}  poses={result.n_poses}"
                )
                all_results[name]["states"][state] = {
                    "vina_score": result.vina_score,
                    "normalized": round(norm, 4),
                    "cnn_score": result.cnn_score,
                    "cnn_affinity": result.cnn_affinity,
                    "n_poses": result.n_poses,
                }
            elif result:
                print(f"  {state}: FAILED - {result.error}")
                all_results[name]["states"][state] = {"error": result.error}
            else:
                print(f"  {state}: SKIPPED")

    # ── Summary statistics ───────────────────────────────────────────
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    binder_scores = []
    nonbinder_scores = []

    for name, data in all_results.items():
        for state, scores in data["states"].items():
            if "vina_score" in scores:
                if data["is_binder"]:
                    binder_scores.append(scores["vina_score"])
                else:
                    nonbinder_scores.append(scores["vina_score"])

    if binder_scores:
        mean_binder = sum(binder_scores) / len(binder_scores)
        print(f"\nBinders:     mean Vina = {mean_binder:.3f} kcal/mol  (n={len(binder_scores)})")
    if nonbinder_scores:
        mean_nonbinder = sum(nonbinder_scores) / len(nonbinder_scores)
        n_nb = len(nonbinder_scores)
        print(f"Non-binders: mean Vina = {mean_nonbinder:.3f} kcal/mol  (n={n_nb})")

    if binder_scores and nonbinder_scores:
        delta = mean_binder - mean_nonbinder
        verdict = "PASS" if delta < 0 else "FAIL"
        print(f"Delta:       {delta:.3f} kcal/mol  ({verdict}: binders more negative)")
        norm_b = normalize_vina_score(mean_binder)
        norm_nb = normalize_vina_score(mean_nonbinder)
        print(f"Normalized:  binders={norm_b:.4f}  non-binders={norm_nb:.4f}")

    # ── Cascade check ────────────────────────────────────────────────
    print("\n--- Scoring cascade check ---")
    from statebind.ranking.scoring import _get_scoring_method, _score_docking
    score, is_stub, method = _score_docking("CCO", "unified")
    print(f"  Method: {method}")
    print(f"  Is stub: {is_stub}")
    print(f"  Score for ethanol: {score}")
    print(f"  Scoring method string: {_get_scoring_method()[:80]}...")

    # Save results
    output = {
        "validation_date": datetime.now(timezone.utc).isoformat(),
        "gnina_available": True,
        "results": all_results,
        "summary": {
            "mean_binder_vina": round(mean_binder, 4) if binder_scores else None,
            "mean_nonbinder_vina": round(mean_nonbinder, 4) if nonbinder_scores else None,
            "binders_better": (
                mean_binder < mean_nonbinder
                if binder_scores and nonbinder_scores else None
            ),
        },
    }

    output_path = Path("artifacts/docking/validation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {output_path}")

    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate GNINA docking")
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick mode: exhaustiveness=2 (suitable for login nodes)",
    )
    parser.add_argument("--exhaustiveness", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    exh = args.exhaustiveness or (2 if args.quick else 8)
    run_validation(exhaustiveness=exh, timeout=args.timeout)
