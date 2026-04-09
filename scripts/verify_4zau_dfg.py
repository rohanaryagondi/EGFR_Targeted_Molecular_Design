#!/usr/bin/env python
"""Verify DFG conformation of PDB 4ZAU and 5D41 by measuring key atomic distances.

Determines whether these structures are DFGin or DFGout by measuring:
  1. DFG Asp-Phe CA-CA distance (DFG motif geometry)
  2. DFG Phe CA to conserved Lys CA distance (Phe position relative to ATP site)
  3. Conserved Lys NZ to conserved Glu OE min distance (aC-helix salt bridge)

The DFG motif is located by scanning for the Asp-Phe-Gly tripeptide in the chain,
not by hardcoded residue numbers, since different EGFR PDB files may use different
numbering conventions. In 4ZAU and 5D41, the DFG motif is at Asp855-Phe856-Gly857
(full-length EGFR numbering), while the conserved Lys is at 745 and Glu at 762.

The task spec references "Asp831/Phe832" which is EGFR kinase domain numbering
(offset -24 from full-length). Both refer to the same physical residues.

This is task P0-T01 of the StateBind project plan.

Usage:
    python scripts/verify_4zau_dfg.py
"""

from __future__ import annotations

import json
import math
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# PDB download
# ---------------------------------------------------------------------------

def download_pdb(pdb_id: str, cache_dir: Path) -> Path:
    """Download a PDB file from RCSB, caching locally."""
    pdb_id_upper = pdb_id.upper()
    local_path = cache_dir / f"{pdb_id_upper}.pdb"
    if local_path.exists():
        print(f"  Using cached {local_path}")
        return local_path

    url = f"https://files.rcsb.org/download/{pdb_id_upper}.pdb"
    print(f"  Downloading {url} ...")
    try:
        urllib.request.urlretrieve(url, local_path)
        print(f"  Saved to {local_path}")
    except Exception as exc:
        print(f"  ERROR downloading {pdb_id_upper}: {exc}", file=sys.stderr)
        raise
    return local_path


# ---------------------------------------------------------------------------
# Distance helpers
# ---------------------------------------------------------------------------

def atom_distance(atom_a, atom_b) -> float:
    """Euclidean distance between two BioPython Atom objects, in Angstroms."""
    diff = atom_a.get_vector() - atom_b.get_vector()
    return math.sqrt(sum(c * c for c in diff.get_array()))


def get_residue(chain, resnum: int, resname_expected: str | None = None):
    """Get a residue from a chain by sequence number (insertion code ' ')."""
    for residue in chain:
        hetflag, seqid, icode = residue.get_id()
        if hetflag != " ":
            continue  # skip HETATMs
        if seqid == resnum:
            if resname_expected and residue.get_resname().strip() != resname_expected:
                print(
                    f"  WARNING: residue {resnum} is {residue.get_resname().strip()}, "
                    f"expected {resname_expected}"
                )
            return residue
    return None


def find_dfg_motif(chain) -> tuple | None:
    """Find the DFG (Asp-Phe-Gly) motif by scanning the sequence.

    Returns (asp_residue, phe_residue, gly_residue) or None if not found.
    """
    protein_residues = [
        r for r in chain if r.get_id()[0] == " "
    ]
    # Sort by sequence number to ensure order
    protein_residues.sort(key=lambda r: r.get_id()[1])

    for i in range(len(protein_residues) - 2):
        r0 = protein_residues[i]
        r1 = protein_residues[i + 1]
        r2 = protein_residues[i + 2]
        n0 = r0.get_resname().strip()
        n1 = r1.get_resname().strip()
        n2 = r2.get_resname().strip()
        # Check contiguous numbering (no gaps) and DFG sequence
        if (
            n0 == "ASP"
            and n1 == "PHE"
            and n2 == "GLY"
            and r1.get_id()[1] == r0.get_id()[1] + 1
            and r2.get_id()[1] == r1.get_id()[1] + 1
        ):
            return r0, r1, r2
    return None


def find_conserved_lys(chain, dfg_asp_resnum: int) -> object | None:
    """Find the conserved beta-3 lysine (K745 in EGFR).

    Strategy: the conserved Lys is ~110 residues N-terminal to the DFG Asp
    in EGFR (745 vs 855). We search for a LYS in the range [DFG-130, DFG-90].
    We pick the one closest to (DFG - 110) that is actually a LYS.
    """
    target = dfg_asp_resnum - 110
    candidates = []
    for residue in chain:
        hetflag, seqid, icode = residue.get_id()
        if hetflag != " ":
            continue
        if residue.get_resname().strip() == "LYS":
            if dfg_asp_resnum - 130 <= seqid <= dfg_asp_resnum - 90:
                candidates.append((abs(seqid - target), residue))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def find_conserved_glu(chain, dfg_asp_resnum: int) -> object | None:
    """Find the conserved aC-helix glutamate (E762 in EGFR).

    Strategy: the conserved Glu is ~93 residues N-terminal to the DFG Asp
    in EGFR (762 vs 855). We search for a GLU in the range [DFG-110, DFG-75].
    """
    target = dfg_asp_resnum - 93
    candidates = []
    for residue in chain:
        hetflag, seqid, icode = residue.get_id()
        if hetflag != " ":
            continue
        if residue.get_resname().strip() == "GLU":
            if dfg_asp_resnum - 110 <= seqid <= dfg_asp_resnum - 75:
                candidates.append((abs(seqid - target), residue))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


# ---------------------------------------------------------------------------
# Measurement logic
# ---------------------------------------------------------------------------

def measure_structure(pdb_path: Path, pdb_id: str, chain_id: str = "A") -> dict:
    """Measure DFG and aC-helix distances for a single PDB structure."""
    from Bio.PDB import PDBParser

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(pdb_id, str(pdb_path))

    # Get the first model, specified chain
    model = structure[0]
    if chain_id not in model:
        available = [c.id for c in model]
        raise ValueError(
            f"Chain {chain_id} not found in {pdb_id}. Available: {available}"
        )
    chain = model[chain_id]

    # ----- Find the DFG motif by sequence pattern -----
    dfg_result = find_dfg_motif(chain)
    if dfg_result is None:
        raise ValueError(f"Could not find DFG motif (Asp-Phe-Gly) in {pdb_id} chain {chain_id}")
    dfg_asp, dfg_phe, dfg_gly = dfg_result
    dfg_asp_num = dfg_asp.get_id()[1]
    dfg_phe_num = dfg_phe.get_id()[1]
    print(f"  DFG motif found: Asp{dfg_asp_num}-Phe{dfg_phe_num}-Gly{dfg_gly.get_id()[1]}")

    # ----- Find the conserved Lys (beta-3 lysine, K745 in EGFR) -----
    cons_lys = find_conserved_lys(chain, dfg_asp_num)
    if cons_lys is None:
        # Fallback: try the exact residue 745
        cons_lys = get_residue(chain, 745, "LYS")
    if cons_lys is None:
        raise ValueError(f"Could not find conserved beta-3 Lys in {pdb_id} chain {chain_id}")
    lys_num = cons_lys.get_id()[1]
    print(f"  Conserved Lys (beta-3): Lys{lys_num} ({cons_lys.get_resname().strip()})")

    # ----- Find the conserved Glu (aC-helix, E762 in EGFR) -----
    cons_glu = find_conserved_glu(chain, dfg_asp_num)
    if cons_glu is None:
        # Fallback: try the exact residue 762
        cons_glu = get_residue(chain, 762, "GLU")
    if cons_glu is None:
        raise ValueError(f"Could not find conserved aC-helix Glu in {pdb_id} chain {chain_id}")
    glu_num = cons_glu.get_id()[1]
    print(f"  Conserved Glu (aC-helix): Glu{glu_num} ({cons_glu.get_resname().strip()})")

    # ----- Measurement 1: DFG Asp-Phe CA-CA distance -----
    dfg_asp_ca = dfg_asp["CA"]
    dfg_phe_ca = dfg_phe["CA"]
    dfg_ca_ca_dist = atom_distance(dfg_asp_ca, dfg_phe_ca)
    print(f"  DFG Asp{dfg_asp_num}-Phe{dfg_phe_num} CA-CA: {dfg_ca_ca_dist:.2f} A")

    # ----- Measurement 2: DFG Phe CA to conserved Lys CA distance -----
    lys_ca = cons_lys["CA"]
    phe_to_lys_dist = atom_distance(dfg_phe_ca, lys_ca)
    print(f"  Phe{dfg_phe_num}-Lys{lys_num} CA-CA: {phe_to_lys_dist:.2f} A")

    # ----- Measurement 3: Lys NZ to Glu OE minimum distance -----
    lys_nz = cons_lys["NZ"]
    oe_atoms = []
    if "OE1" in cons_glu:
        oe_atoms.append(cons_glu["OE1"])
    if "OE2" in cons_glu:
        oe_atoms.append(cons_glu["OE2"])
    if not oe_atoms:
        raise ValueError(f"Glu{glu_num} has no OE1/OE2 atoms in {pdb_id}")

    salt_bridge_dists = [atom_distance(lys_nz, oe) for oe in oe_atoms]
    salt_bridge_min = min(salt_bridge_dists)
    print(f"  Lys{lys_num} NZ - Glu{glu_num} OE min: {salt_bridge_min:.2f} A")

    # ----- Classification -----
    # DFG state: CA-CA distance < 7A => DFGin, > 8A => DFGout
    if dfg_ca_ca_dist < 7.0:
        dfg_state = "DFGin"
        dfg_confidence = "high" if dfg_ca_ca_dist < 6.5 else "medium"
    elif dfg_ca_ca_dist > 8.0:
        dfg_state = "DFGout"
        dfg_confidence = "high" if dfg_ca_ca_dist > 9.0 else "medium"
    else:
        dfg_state = "ambiguous"
        dfg_confidence = "low"

    # aC-helix state: salt bridge distance < 4A => aCin, > 6A => aCout
    if salt_bridge_min < 4.0:
        ac_state = "aCin"
        ac_confidence = "high" if salt_bridge_min < 3.5 else "medium"
    elif salt_bridge_min > 6.0:
        ac_state = "aCout"
        ac_confidence = "high" if salt_bridge_min > 7.0 else "medium"
    else:
        ac_state = "ambiguous"
        ac_confidence = "low"

    # Overall confidence
    if dfg_confidence == "high" and ac_confidence == "high":
        overall_confidence = "high"
    elif dfg_confidence == "low" or ac_confidence == "low":
        overall_confidence = "low"
    else:
        overall_confidence = "medium"

    combined = f"{dfg_state}_{ac_state}"

    # Determine implications
    current_classification = "DFGout_aCout"
    if combined == current_classification:
        model_change = "none"
    elif dfg_state == "DFGin":
        model_change = "3-state (remove DFGout_aCout, no genuine EGFR DFGout structures)"
    else:
        model_change = "4-state (keep current)"

    interpretation = (
        f"PDB {pdb_id} chain {chain_id}: DFG Asp{dfg_asp_num}-Phe{dfg_phe_num} CA-CA "
        f"distance = {dfg_ca_ca_dist:.2f} A (threshold: <7A=DFGin, >8A=DFGout). "
        f"Lys{lys_num}-Glu{glu_num} salt bridge = {salt_bridge_min:.2f} A "
        f"(threshold: <4A=aCin, >6A=aCout). "
        f"Classification: {combined}."
    )

    return {
        "pdb_id": pdb_id.upper(),
        "chain": chain_id,
        "residue_numbering": {
            "dfg_asp": dfg_asp_num,
            "dfg_phe": dfg_phe_num,
            "dfg_gly": dfg_gly.get_id()[1],
            "conserved_lys": lys_num,
            "conserved_glu": glu_num,
            "note": (
                "These PDBs use full-length EGFR numbering (DFG at 855-857). "
                "The task spec references kinase-domain numbering (DFG at 831-833, "
                "offset -24). Both refer to the same physical residues."
            ),
        },
        "measurements": {
            "dfg_asp_phe_ca_ca_distance_angstrom": round(dfg_ca_ca_dist, 4),
            "dfg_phe_to_conserved_lys_ca_distance_angstrom": round(phe_to_lys_dist, 4),
            "conserved_lys_nz_to_glu_oe_min_distance_angstrom": round(salt_bridge_min, 4),
        },
        "classification": {
            "dfg_state": dfg_state,
            "ac_helix_state": ac_state,
            "combined_state": combined,
            "confidence": overall_confidence,
        },
        "interpretation": interpretation,
        "implications": {
            "current_classification": current_classification,
            "correct_classification": combined,
            "model_change_needed": model_change,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    artifact_dir = repo_root / "artifacts" / "verification"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = repo_root / "data" / "raw" / "pdb_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("StateBind -- DFG Conformation Verification (P0-T01)")
    print("=" * 60)

    structures_to_check = ["4ZAU", "5D41"]
    results = []

    for pdb_id in structures_to_check:
        print(f"\n--- {pdb_id} ---")
        pdb_path = download_pdb(pdb_id, cache_dir)
        result = measure_structure(pdb_path, pdb_id, chain_id="A")
        results.append(result)
        print(f"  => {result['classification']['combined_state']} "
              f"(confidence: {result['classification']['confidence']})")

    # Build output artifact
    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task": "P0-T01: Verify 4ZAU DFG Conformation",
        "structures": results,
        "summary": {
            "4ZAU": results[0]["classification"]["combined_state"],
            "5D41": results[1]["classification"]["combined_state"],
        },
        "notes": (
            "Automated measurement from PDB coordinates using BioPython. "
            "DFG motif located by Asp-Phe-Gly sequence scan (found at 855-857 in both PDBs, "
            "which is full-length EGFR numbering; kinase-domain numbering would be 831-833). "
            "Conserved Lys745 (beta-3) and Glu762 (aC-helix) identified by proximity to DFG. "
            "Thresholds: DFGin CA-CA < 7A, DFGout CA-CA > 8A; aCin salt bridge < 4A, "
            "aCout salt bridge > 6A."
        ),
    }

    output_path = artifact_dir / "4zau_dfg_verification.json"
    with open(output_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact written to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        cls = r["classification"]
        meas = r["measurements"]
        impl = r["implications"]
        rn = r["residue_numbering"]
        print(f"  {r['pdb_id']}: {cls['combined_state']} "
              f"(confidence: {cls['confidence']})")
        print(f"    DFG Asp{rn['dfg_asp']}-Phe{rn['dfg_phe']} CA-CA: "
              f"{meas['dfg_asp_phe_ca_ca_distance_angstrom']:.2f} A")
        print(f"    Phe{rn['dfg_phe']}-Lys{rn['conserved_lys']} CA: "
              f"{meas['dfg_phe_to_conserved_lys_ca_distance_angstrom']:.2f} A")
        print(f"    Lys{rn['conserved_lys']}-Glu{rn['conserved_glu']} salt bridge: "
              f"{meas['conserved_lys_nz_to_glu_oe_min_distance_angstrom']:.2f} A")
        print(f"    Implication: {impl['model_change_needed']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
