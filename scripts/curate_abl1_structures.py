#!/usr/bin/env python3
"""Curate ABL1 kinase domain structures from PDB and KLIFS.

Downloads structural metadata for key ABL1 structures from RCSB PDB REST API,
cross-references with KLIFS for DFG/aC-helix classification, and produces a
StructureRecord-compatible JSON dataset.

CRITICAL: Every annotation is verified against the actual PDB record. This
follows the Phase 0 lesson where 3iku (ParM, E. coli) and 4ZAU were
mislabeled in the EGFR dataset.

Key ABL1 structures from literature:
  DFGout: 1IEP (imatinib), 3PYY (nilotinib), 3CS9
  DFGin:  2GQG (dasatinib), 3QRI (bosutinib)

Usage:
    python scripts/curate_abl1_structures.py
    python scripts/curate_abl1_structures.py --output-dir data/processed/structures
    python scripts/curate_abl1_structures.py --help
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Curated ABL1 structure definitions ────────────────────────────────

# Hand-curated from literature and PDB inspection.
# state values: DFGin_aCin, DFGin_aCout, DFGout_aCin
# Sources:
#   - Nagar et al., Cancer Res 2002 (1IEP)
#   - Tokarski et al., Cancer Res 2006 (3CS9)
#   - Weisberg et al., Nat Rev Cancer 2007 (dasatinib)
#   - KLIFS database (https://klifs.net)

_ABL1_STRUCTURES: list[dict] = [
    # ── DFGout_aCin (Type-II inhibitor bound) ────────────────────────
    {
        "pdb_id": "1iep",
        "expected_state": "DFGout_aCin",
        "ligand_drug": "imatinib",
        "notes": (
            "ABL1 kinase domain bound to imatinib (STI-571). Classic DFGout "
            "structure. Nagar et al., Cancer Res 2002. First approved BCR-ABL "
            "inhibitor (2001). Reference DFGout structure for ABL1. "
            "NOTE: Organism is Mus musculus (mouse), not Homo sapiens. "
            "Mouse/human ABL1 kinase domains are >97% identical."
        ),
        "is_representative": True,
    },
    {
        "pdb_id": "3cs9",
        "expected_state": "DFGout_aCin",
        "ligand_drug": "nilotinib",
        "notes": (
            "ABL1 bound to nilotinib (AMN107). DFGout conformation. "
            "Tokarski et al., Cancer Res 2006. Human ABL1 WT. "
            "2nd-generation inhibitor, approved 2007. Higher potency "
            "than imatinib for unmutated BCR-ABL. KLIFS: DFG=out, aC=in."
        ),
        "is_representative": False,
    },
    {
        "pdb_id": "3pyy",
        "expected_state": "DFGout_aCin",
        "ligand_drug": "DPH (myristoyl pocket activator)",
        "notes": (
            "ABL1 in DFGout conformation. Jahnke et al., JACS 2010. "
            "Human ABL1 WT. IMPORTANT: Ligand (DPH) binds the allosteric "
            "myristoyl pocket, NOT the ATP binding site. The kinase domain "
            "adopts DFGout conformation regardless. KLIFS: DFG=out, aC=in. "
            "Resolution 1.85 A."
        ),
        "is_representative": False,
    },
    # ── DFGin_aCin (Active, Type-I inhibitor bound) ──────────────────
    {
        "pdb_id": "2gqg",
        "expected_state": "DFGin_aCin",
        "ligand_drug": "dasatinib",
        "notes": (
            "ABL1 bound to dasatinib. DFGin/active conformation. Dasatinib "
            "is a Type-I inhibitor that binds the active conformation. "
            "Das et al., J Mol Biol 2006. Human ABL1 WT. "
            "2nd-generation inhibitor, approved 2006. Active against most "
            "imatinib-resistant mutants except T315I. KLIFS: DFG=in, aC=in."
        ),
        "is_representative": True,
    },
    # ── DFGin_aCout (Src-like inactive) ──────────────────────────────
    {
        "pdb_id": "2g1t",
        "expected_state": "DFGin_aCout",
        "ligand_drug": "apo (ATP-peptide conjugate)",
        "notes": (
            "ABL1 in Src-like inactive conformation. DFGin but αC-helix "
            "rotated out, breaking K271-E286 salt bridge. Human ABL1 WT. "
            "Levinson et al., PLoS Biol 2006. Title: 'A Src-like Inactive "
            "Conformation in the Abl Tyrosine Kinase Domain'. "
            "Resolution 1.8 A. KLIFS: DFG=in, aC=out."
        ),
        "is_representative": True,
    },
]

# RCSB PDB REST API base URL
PDB_API_BASE = "https://data.rcsb.org/rest/v1/core/entry"

# KLIFS API base URL
KLIFS_API_BASE = "https://klifs.net/api"


def _fetch_pdb_metadata(pdb_id: str) -> dict | None:
    """Fetch structure metadata from RCSB PDB REST API.

    Retrieves: resolution, experimental method, organism, deposition date,
    and bound ligand information.

    Args:
        pdb_id: 4-character PDB ID (case-insensitive).

    Returns:
        Dict with parsed metadata, or None on failure.
    """
    import requests

    url = f"{PDB_API_BASE}/{pdb_id.upper()}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch PDB %s: %s", pdb_id, exc)
        return None
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse PDB response for %s: %s", pdb_id, exc)
        return None

    # Extract resolution
    resolution = None
    rcsb_entry = data.get("rcsb_entry_info", {})
    resolution = rcsb_entry.get("resolution_combined")
    if isinstance(resolution, list) and resolution:
        resolution = resolution[0]

    # Experimental method
    exp_method = rcsb_entry.get("experimental_method", "X-ray diffraction")

    # Deposition date
    dep_date = ""
    rcsb_accession = data.get("rcsb_accession_info", {})
    dep_date = rcsb_accession.get("deposit_date", "")
    if dep_date:
        # Truncate to date only (YYYY-MM-DD)
        dep_date = dep_date[:10]

    # Organism from entity source
    organism = "unknown"
    polymer_entities = data.get("polymer_entities", [])
    if not polymer_entities:
        # Try alternative path
        struct_data = data.get("struct", {})
        title = struct_data.get("title", "")
        if "human" in title.lower() or "homo sapiens" in title.lower():
            organism = "Homo sapiens"
    else:
        for entity in polymer_entities:
            sources = entity.get("rcsb_entity_source_organism", [])
            for src in sources:
                sci_name = src.get("ncbi_scientific_name", "")
                if sci_name:
                    organism = sci_name
                    break
            if organism != "unknown":
                break

    # Bound ligands (non-polymer entities)
    ligand_ids: list[str] = []
    nonpoly = data.get("rcsb_entry_info", {}).get("nonpolymer_entity_count", 0)
    if nonpoly > 0:
        nonpoly_entities = data.get("nonpolymer_entities", [])
        for ent in nonpoly_entities:
            comp_id = ent.get("nonpolymer_comp", {}).get("rcsb_id", "")
            if comp_id and comp_id not in ("HOH", "SO4", "PO4", "GOL", "EDO", "ACT", "CL", "NA", "MG", "ZN", "CA"):
                ligand_ids.append(comp_id)

    return {
        "resolution": resolution,
        "experimental_method": exp_method,
        "deposition_date": dep_date,
        "organism": organism,
        "ligand_ids": ligand_ids,
    }


def _fetch_pdb_entity_mutations(pdb_id: str) -> list[str]:
    """Fetch mutation information from RCSB PDB polymer entity API.

    Checks for known mutations relative to WT ABL1 sequence.
    Specifically looks for the T315I gatekeeper mutation.

    Args:
        pdb_id: 4-character PDB ID.

    Returns:
        List of mutation strings (e.g., ["T315I"]).
    """
    import requests

    # Fetch polymer entities for entity 1 (typically the kinase chain)
    url = f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id.upper()}/1"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return []
    except (json.JSONDecodeError, ValueError):
        return []

    mutations: list[str] = []

    # Check entity annotation for mutations
    mutations_list = data.get("rcsb_polymer_entity", {}).get("rcsb_mutation_count", 0)
    if mutations_list and mutations_list > 0:
        logger.info("  PDB %s: %d mutation(s) annotated", pdb_id, mutations_list)

    # Check sequence annotations for specific point mutations
    # The RCSB API stores mutations in rcsb_polymer_entity_annotation
    annotations = data.get("rcsb_polymer_entity_annotation", [])
    for ann in annotations:
        if ann.get("type") == "mutation":
            desc = ann.get("description", "")
            if desc:
                mutations.append(desc)

    # Also check struct_ref_seq_dif for sequence differences
    # This requires the entry-level API with polymer_entities included
    entry_url = f"{PDB_API_BASE}/{pdb_id.upper()}"
    try:
        resp = requests.get(entry_url, timeout=30)
        resp.raise_for_status()
        entry_data = resp.json()
    except (requests.RequestException, json.JSONDecodeError, ValueError):
        return mutations

    # Check for T315I specifically in the title or keywords
    title = entry_data.get("struct", {}).get("title", "").upper()
    if "T315I" in title:
        if "T315I" not in mutations:
            mutations.append("T315I")
            logger.info("  PDB %s: T315I gatekeeper mutation found in title", pdb_id)

    return mutations


def _fetch_klifs_classification(pdb_id: str) -> dict | None:
    """Query KLIFS API for DFG/aC-helix classification.

    Args:
        pdb_id: 4-character PDB ID.

    Returns:
        Dict with DFG and aC-helix classifications, or None on failure.
    """
    import requests

    # KLIFS structures endpoint
    url = f"{KLIFS_API_BASE}/structures_pdb_list"
    params = {"pdb-codes": pdb_id.upper()}

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("KLIFS request failed for %s: %s", pdb_id, exc)
        return None
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse KLIFS response for %s: %s", pdb_id, exc)
        return None

    if not data or not isinstance(data, list):
        logger.info("No KLIFS entry found for %s", pdb_id)
        return None

    # Take first matching entry
    entry = data[0]
    return {
        "dfg": entry.get("DFG", ""),
        "ac_helix": entry.get("aC_helix", ""),
        "klifs_id": entry.get("structure_ID"),
        "species": entry.get("species", ""),
        "kinase": entry.get("kinase", ""),
        "chain": entry.get("chain", ""),
    }


def _validate_structure(
    curated: dict,
    pdb_meta: dict | None,
    klifs_meta: dict | None,
    mutations: list[str],
) -> list[str]:
    """Validate a curated structure against PDB and KLIFS data.

    CRITICAL: This is the Phase 0 lesson -- verify every annotation
    against the actual PDB record. Catches errors like:
    - Wrong organism (3iku was ParM from E. coli, not human EGFR)
    - Wrong state classification
    - Missing mutation annotations

    Args:
        curated: The hand-curated structure definition.
        pdb_meta: Metadata fetched from PDB API.
        klifs_meta: Classification from KLIFS API.
        mutations: Mutations from PDB entity API.

    Returns:
        List of warning strings. Empty = all validations passed.
    """
    warnings: list[str] = []
    pdb_id = curated["pdb_id"]

    if pdb_meta is None:
        warnings.append(f"{pdb_id}: Could not fetch PDB metadata (API unavailable?)")
        return warnings

    # Check organism -- CRITICAL validation
    organism = pdb_meta.get("organism", "unknown")
    if organism.lower() not in ("homo sapiens", "unknown"):
        warnings.append(
            f"{pdb_id}: ORGANISM MISMATCH -- expected Homo sapiens, got '{organism}'. "
            f"This structure may not be human ABL1!"
        )

    # Check resolution
    resolution = pdb_meta.get("resolution")
    if resolution is not None and resolution > 3.5:
        warnings.append(
            f"{pdb_id}: Low resolution ({resolution:.2f} A). Consider excluding."
        )

    # Cross-check state with KLIFS if available
    if klifs_meta is not None:
        klifs_dfg = klifs_meta.get("dfg", "").lower()
        expected_state = curated["expected_state"]

        if "dfgout" in expected_state.lower() and klifs_dfg and "out" not in klifs_dfg:
            warnings.append(
                f"{pdb_id}: State mismatch -- curated as {expected_state} but "
                f"KLIFS DFG='{klifs_meta.get('dfg')}'"
            )
        elif "dfgin" in expected_state.lower() and klifs_dfg and "in" not in klifs_dfg:
            warnings.append(
                f"{pdb_id}: State mismatch -- curated as {expected_state} but "
                f"KLIFS DFG='{klifs_meta.get('dfg')}'"
            )

        # Check kinase identity in KLIFS
        klifs_kinase = klifs_meta.get("kinase", "")
        if klifs_kinase and "abl" not in klifs_kinase.lower():
            warnings.append(
                f"{pdb_id}: KINASE MISMATCH in KLIFS -- expected ABL1, got '{klifs_kinase}'"
            )

    # Check for T315I gatekeeper
    if any("T315I" in m for m in mutations):
        warnings.append(
            f"{pdb_id}: Contains T315I gatekeeper mutation. This is important "
            f"for resistance profiling."
        )

    return warnings


def _build_structure_record(
    curated: dict,
    pdb_meta: dict | None,
    klifs_meta: dict | None,
    mutations: list[str],
) -> dict:
    """Build a StructureRecord-compatible dict from curated + API data.

    Merges hand-curated metadata with PDB API data, preferring API data
    for factual fields (resolution, organism, deposition date) and curated
    data for interpretive fields (state classification, notes).

    Args:
        curated: Hand-curated structure definition.
        pdb_meta: Metadata from PDB API (may be None).
        klifs_meta: Classification from KLIFS (may be None).
        mutations: Mutation list from PDB entity API.

    Returns:
        Dict compatible with StructureRecord.model_validate().
    """
    pdb_id = curated["pdb_id"]

    # Resolution: prefer API, fall back to 0.0
    resolution = 0.0
    if pdb_meta and pdb_meta.get("resolution") is not None:
        resolution = float(pdb_meta["resolution"])

    # Experimental method
    exp_method = "X-ray diffraction"
    if pdb_meta and pdb_meta.get("experimental_method"):
        exp_method = pdb_meta["experimental_method"]

    # Deposition date
    dep_date = ""
    if pdb_meta and pdb_meta.get("deposition_date"):
        dep_date = pdb_meta["deposition_date"]

    # Organism: prefer API
    organism = "Homo sapiens"
    if pdb_meta and pdb_meta.get("organism") and pdb_meta["organism"] != "unknown":
        organism = pdb_meta["organism"]

    # Ligand: prefer API, fall back to empty
    ligand_id = ""
    ligand_bound = False
    if pdb_meta and pdb_meta.get("ligand_ids"):
        ligand_id = pdb_meta["ligand_ids"][0]  # primary ligand
        ligand_bound = True

    # State: map from curated expected_state
    state_map = {
        "DFGin_aCin": "DFGin_aCin",
        "DFGin_aCout": "DFGin_aCout",
        "DFGout_aCin": "DFGout_aCin",
    }
    state = state_map.get(curated["expected_state"], "unclassified")

    # Mutations: merge API-detected with any curated ones
    all_mutations = sorted(set(mutations))

    # Build record
    record = {
        "pdb_id": pdb_id.lower(),
        "resolution": round(resolution, 2),
        "experimental_method": exp_method,
        "is_predicted": False,
        "chain": "A",
        "state": state,
        "dfg_distance": None,
        "ac_helix_metric": None,
        "mutations_present": all_mutations,
        "ligand_id": ligand_id,
        "ligand_bound": ligand_bound,
        "is_apo": not ligand_bound,
        "is_representative": curated.get("is_representative", False),
        "deposition_date": dep_date,
        "organism": organism,
        "notes": curated.get("notes", ""),
        "target_gene": "ABL1",
        "provenance": {
            "sources": ["pdb", "klifs"] if klifs_meta else ["pdb"],
            "processing_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "notes": f"Curated for StateBind ABL1 extension. Drug: {curated.get('ligand_drug', 'unknown')}",
        },
    }

    # Add KLIFS chain if available
    if klifs_meta and klifs_meta.get("chain"):
        record["chain"] = klifs_meta["chain"]

    return record


def curate_abl1_structures(
    output_dir: Path | None = None,
    skip_api: bool = False,
) -> list[dict]:
    """Main curation pipeline for ABL1 structures.

    Steps:
    1. For each curated structure:
       a. Fetch metadata from RCSB PDB API
       b. Fetch DFG/aC classification from KLIFS API
       c. Fetch mutation data from PDB entity API
       d. Validate annotations (Phase 0 lesson)
       e. Build StructureRecord
    2. Save dataset to output file

    Args:
        output_dir: Directory for output files. Defaults to
            data/processed/structures/.
        skip_api: If True, build records from curated data only
            (for testing without network access).

    Returns:
        List of StructureRecord-compatible dicts.
    """
    if output_dir is None:
        output_dir = Path("data/processed/structures")

    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    logger.info("Curating %d ABL1 structures...", len(_ABL1_STRUCTURES))
    all_warnings: list[str] = []
    records: list[dict] = []

    for curated in _ABL1_STRUCTURES:
        pdb_id = curated["pdb_id"]
        logger.info("Processing %s (%s)...", pdb_id, curated.get("ligand_drug", ""))

        pdb_meta = None
        klifs_meta = None
        mutations: list[str] = []

        if not skip_api:
            # Fetch from APIs
            pdb_meta = _fetch_pdb_metadata(pdb_id)
            klifs_meta = _fetch_klifs_classification(pdb_id)
            mutations = _fetch_pdb_entity_mutations(pdb_id)

            # Validate
            warnings = _validate_structure(curated, pdb_meta, klifs_meta, mutations)
            if warnings:
                for w in warnings:
                    logger.warning("  VALIDATION: %s", w)
                all_warnings.extend(warnings)

        # Build record
        record = _build_structure_record(curated, pdb_meta, klifs_meta, mutations)
        records.append(record)
        logger.info(
            "  -> %s: resolution=%.2f, state=%s, ligand=%s, mutations=%s",
            record["pdb_id"],
            record["resolution"],
            record["state"],
            record["ligand_id"] or "(none)",
            record["mutations_present"] or "(none)",
        )

    # Build output dataset (matches StructureDataset schema)
    dataset = {
        "version": "1.0.0",
        "target_gene": "ABL1",
        "structures": records,
        "generated_at": now.isoformat(),
        "processing_version": "0.1.0",
    }

    # Save
    out_path = output_dir / "abl1_structures.json"
    with open(out_path, "w") as f:
        json.dump(dataset, f, indent=2, default=str)
    logger.info("Saved %d ABL1 structures to %s", len(records), out_path)

    # Print summary
    print(f"\n{'=' * 60}")
    print("ABL1 Structure Curation Summary")
    print(f"{'=' * 60}")
    print(f"Total structures: {len(records)}")

    from collections import Counter
    state_counts = Counter(r["state"] for r in records)
    print("\nState distribution:")
    for state, count in sorted(state_counts.items()):
        print(f"  {state:<20} {count}")

    rep_count = sum(1 for r in records if r["is_representative"])
    print(f"\nRepresentative structures: {rep_count}")

    if all_warnings:
        print(f"\nValidation warnings ({len(all_warnings)}):")
        for w in all_warnings:
            print(f"  WARNING: {w}")
    else:
        print("\nAll validations passed (or API was skipped).")

    print(f"\nOutput: {out_path}")
    print(f"{'=' * 60}\n")

    return records


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Curate ABL1 kinase domain structures from PDB and KLIFS",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/structures"),
        help="Output directory (default: data/processed/structures)",
    )
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Skip API calls (build from curated data only, for testing)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    records = curate_abl1_structures(
        output_dir=args.output_dir,
        skip_api=args.skip_api,
    )
    if not records:
        print("ERROR: No structures curated.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
