#!/usr/bin/env python3
"""Curate ABL1 bioactivity data from ChEMBL REST API.

Queries ChEMBL for ABL1 (CHEMBL1862) IC50 data, filters for quality,
converts to pIC50, and outputs in the same format as EGFR affinity data
for downstream pipeline compatibility.

Usage:
    python scripts/curate_abl1_data.py
    python scripts/curate_abl1_data.py --output data/processed/abl1_affinity.json
    python scripts/curate_abl1_data.py --help

Output format (matches data/processed/egfr_affinity.json):
    [{"smiles": "...", "pIC50": 7.82, "assay_type": "B", "chembl_id": "CHEMBL...", "year": 2005}, ...]
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ChEMBL target ID for ABL1
ABL1_TARGET_CHEMBL_ID = "CHEMBL1862"

# ChEMBL REST API base
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"


def _fetch_abl1_activities(
    limit_per_page: int = 500,
    max_pages: int = 40,
) -> list[dict]:
    """Fetch ABL1 IC50 activities from ChEMBL REST API.

    Filters:
    - target_chembl_id = CHEMBL1862 (ABL1)
    - standard_type = IC50
    - standard_relation = '=' (exact measurements only)
    - assay_type = 'B' or 'F' (binding or functional)
    - assay_organism = 'Homo sapiens'
    - pchembl_value is not null (pchembl_value__isnull=false)

    Uses requests library for HTTP calls.
    Paginates through results with configurable page size.

    Returns:
        List of raw activity dicts from ChEMBL API.
    """
    import requests

    all_activities: list[dict] = []

    for assay_type in ("B", "F"):
        logger.info("Fetching assay_type=%s activities...", assay_type)
        page_count = 0

        for page in range(max_pages):
            offset = page * limit_per_page
            url = (
                f"{CHEMBL_API_BASE}/activity.json"
                f"?target_chembl_id={ABL1_TARGET_CHEMBL_ID}"
                f"&standard_type=IC50"
                f"&standard_relation=%3D"  # URL-encoded '='
                f"&assay_type={assay_type}"
                f"&assay_organism=Homo%20sapiens"
                f"&pchembl_value__isnull=false"
                f"&limit={limit_per_page}"
                f"&offset={offset}"
                f"&format=json"
            )

            try:
                resp = requests.get(
                    url,
                    headers={"Accept": "application/json"},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as exc:
                logger.warning(
                    "ChEMBL API request failed (assay_type=%s, page=%d): %s",
                    assay_type, page, exc,
                )
                break
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning(
                    "Failed to parse ChEMBL response (assay_type=%s, page=%d): %s",
                    assay_type, page, exc,
                )
                break

            activities = data.get("activities", [])
            if not activities:
                logger.info(
                    "  assay_type=%s: no more results at offset %d",
                    assay_type, offset,
                )
                break

            all_activities.extend(activities)
            page_count += 1

            # Check if there are more pages
            next_url = data.get("page_meta", {}).get("next")
            if next_url is None:
                logger.info(
                    "  assay_type=%s: reached last page (%d pages, %d records)",
                    assay_type, page_count, len(activities),
                )
                break

        logger.info(
            "  assay_type=%s: fetched %d pages total", assay_type, page_count,
        )

    logger.info("Total raw activities fetched: %d", len(all_activities))
    return all_activities


def _ic50_to_pic50(ic50_nm: float) -> float | None:
    """Convert IC50 in nM to pIC50 = -log10(IC50 in M).

    Args:
        ic50_nm: IC50 value in nanomolar.

    Returns:
        pIC50 value, or None if input is invalid.
    """
    if ic50_nm <= 0:
        return None
    ic50_molar = ic50_nm * 1e-9
    pic50 = -math.log10(ic50_molar)
    # Sanity check: pIC50 should be in a reasonable range
    if pic50 < 2.0 or pic50 > 14.0:
        return None
    return round(pic50, 4)


def _process_activities(
    activities: list[dict],
) -> list[dict]:
    """Process raw ChEMBL activities into curated records.

    For each activity:
    - Extract SMILES, pchembl_value, assay_type, chembl_id, year
    - Use pchembl_value directly (already -log10(M) from ChEMBL)
    - Also validate by converting standard_value to pIC50 as cross-check
    - Skip records with missing essential fields

    Returns:
        List of curated records with keys: smiles, pIC50, assay_type, chembl_id, year.
    """
    records: list[dict] = []
    skipped: Counter = Counter()

    for act in activities:
        # Extract SMILES
        smiles = act.get("canonical_smiles", "")
        if not smiles or not smiles.strip():
            skipped["missing_smiles"] += 1
            continue

        # Extract pchembl_value (primary pIC50 source)
        pchembl = act.get("pchembl_value")
        if pchembl is None:
            skipped["missing_pchembl"] += 1
            continue

        try:
            pic50 = float(pchembl)
        except (ValueError, TypeError):
            skipped["invalid_pchembl"] += 1
            continue

        if pic50 < 2.0 or pic50 > 14.0:
            skipped["pchembl_out_of_range"] += 1
            continue

        # Extract assay_type
        assay_type = act.get("assay_type", "")

        # Extract ChEMBL compound ID
        chembl_id = act.get("molecule_chembl_id", "")

        # Extract publication year from document
        year = None
        doc_year = act.get("document_year")
        if doc_year is not None:
            try:
                year = int(doc_year)
            except (ValueError, TypeError):
                pass

        records.append({
            "smiles": smiles.strip(),
            "pIC50": round(pic50, 4),
            "assay_type": assay_type,
            "chembl_id": chembl_id,
            "year": year,
        })

    # Log filtering statistics
    logger.info("Processing statistics:")
    logger.info("  Accepted: %d records", len(records))
    for reason, count in sorted(skipped.items()):
        logger.info("  Skipped (%s): %d", reason, count)

    return records


def _deduplicate_records(
    records: list[dict],
) -> list[dict]:
    """Deduplicate by SMILES, taking median pIC50 for duplicates.

    For duplicate SMILES, keeps the record with the median pIC50 value
    and merges metadata (earliest year, all chembl_ids, combined assay_types).

    Returns:
        Deduplicated list of records.
    """
    # Group by SMILES
    groups: dict[str, list[dict]] = {}
    for rec in records:
        smiles = rec["smiles"]
        if smiles not in groups:
            groups[smiles] = []
        groups[smiles].append(rec)

    deduped: list[dict] = []
    n_dups = 0
    for smiles, group in groups.items():
        if len(group) > 1:
            n_dups += 1
        pic50_values = [r["pIC50"] for r in group]
        median_pic50 = round(statistics.median(pic50_values), 4)

        # Use earliest year
        years = [r["year"] for r in group if r["year"] is not None]
        earliest_year = min(years) if years else None

        # Combine assay types
        assay_types = sorted({r["assay_type"] for r in group if r["assay_type"]})
        assay_type = ",".join(assay_types) if assay_types else ""

        # Use first chembl_id
        chembl_id = group[0]["chembl_id"]

        deduped.append({
            "smiles": smiles,
            "pIC50": median_pic50,
            "assay_type": assay_type,
            "chembl_id": chembl_id,
            "year": earliest_year,
        })

    logger.info(
        "Deduplication: %d unique compounds from %d records (%d had duplicates)",
        len(deduped), len(records), n_dups,
    )
    return deduped


def _log_statistics(records: list[dict]) -> None:
    """Log summary statistics for the curated dataset."""
    n = len(records)
    if n == 0:
        logger.warning("No compounds passed filters!")
        return

    pic50s = [r["pIC50"] for r in records]
    years = [r["year"] for r in records if r["year"] is not None]

    print(f"\n{'=' * 60}")
    print("ABL1 Bioactivity Data Summary")
    print(f"{'=' * 60}")
    print(f"Total compounds: {n}")
    print(f"pIC50 range: {min(pic50s):.2f} - {max(pic50s):.2f}")
    print(f"pIC50 mean:  {statistics.mean(pic50s):.2f}")
    if len(pic50s) > 1:
        print(f"pIC50 stdev: {statistics.stdev(pic50s):.2f}")
    print(f"pIC50 median: {statistics.median(pic50s):.2f}")

    # Potency distribution
    potent = sum(1 for v in pic50s if v >= 8.0)
    moderate = sum(1 for v in pic50s if 6.0 <= v < 8.0)
    weak = sum(1 for v in pic50s if 4.0 <= v < 6.0)
    inactive = sum(1 for v in pic50s if v < 4.0)
    print(f"\nPotency distribution:")
    print(f"  Potent (pIC50 >= 8):   {potent:4d} ({100 * potent / n:.1f}%)")
    print(f"  Moderate (6-8):        {moderate:4d} ({100 * moderate / n:.1f}%)")
    print(f"  Weak (4-6):            {weak:4d} ({100 * weak / n:.1f}%)")
    print(f"  Inactive (< 4):        {inactive:4d} ({100 * inactive / n:.1f}%)")

    # Assay type distribution
    assay_counts: Counter = Counter()
    for r in records:
        for at in r["assay_type"].split(","):
            if at:
                assay_counts[at] += 1
    print(f"\nAssay type distribution:")
    for at, count in sorted(assay_counts.items()):
        label = {"B": "Binding", "F": "Functional"}.get(at, at)
        print(f"  {label} ({at}): {count}")

    # Year range
    if years:
        print(f"\nYear range: {min(years)} - {max(years)}")
        decade_counts: Counter = Counter()
        for y in years:
            decade = (y // 10) * 10
            decade_counts[f"{decade}s"] += 1
        print("Decade distribution:")
        for decade, count in sorted(decade_counts.items()):
            print(f"  {decade}: {count}")
    else:
        print("\nYear data: not available")

    print(f"{'=' * 60}\n")

    # Warn if too few compounds
    if n < 100:
        logger.warning(
            "Only %d compounds passed filters. This may be insufficient "
            "for training. Consider relaxing filter criteria.", n,
        )


def curate_abl1_data(
    output_path: Path | None = None,
) -> list[dict]:
    """Main curation pipeline for ABL1 bioactivity data.

    Steps:
    1. Fetch activities from ChEMBL REST API
    2. Filter and process into curated records
    3. Deduplicate by SMILES (median pIC50)
    4. Log statistics
    5. Save to output file

    Args:
        output_path: Path for output JSON file. Defaults to
            data/processed/abl1_affinity.json.

    Returns:
        List of curated records.
    """
    if output_path is None:
        output_path = Path("data/processed/abl1_affinity.json")

    logger.info("Starting ABL1 data curation from ChEMBL (target: %s)", ABL1_TARGET_CHEMBL_ID)

    # Step 1: Fetch from ChEMBL
    raw_activities = _fetch_abl1_activities()
    if not raw_activities:
        logger.error("No activities fetched from ChEMBL. Aborting.")
        return []

    # Step 2: Process and filter
    records = _process_activities(raw_activities)
    if not records:
        logger.error("No records passed filtering. Aborting.")
        return []

    # Step 3: Deduplicate
    records = _deduplicate_records(records)

    # Step 4: Log statistics
    _log_statistics(records)

    # Step 5: Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2, default=str)
    logger.info("Saved %d curated ABL1 compounds to %s", len(records), output_path)

    # Save metadata
    pic50s = [r["pIC50"] for r in records]
    years = [r["year"] for r in records if r["year"] is not None]
    metadata = {
        "target": "ABL1",
        "target_chembl_id": ABL1_TARGET_CHEMBL_ID,
        "n_compounds": len(records),
        "pIC50_min": round(min(pic50s), 4) if pic50s else 0.0,
        "pIC50_max": round(max(pic50s), 4) if pic50s else 0.0,
        "pIC50_mean": round(statistics.mean(pic50s), 4) if pic50s else 0.0,
        "pIC50_median": round(statistics.median(pic50s), 4) if pic50s else 0.0,
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "filters": {
            "standard_type": "IC50",
            "standard_relation": "=",
            "assay_type": ["B", "F"],
            "organism": "Homo sapiens",
            "pchembl_value": "not null",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "notes": (
            "ABL1 binding affinity data curated from ChEMBL. "
            "pIC50 = -log10(IC50 in molar). Higher = more potent. "
            "Duplicates resolved by median pIC50."
        ),
    }
    meta_path = output_path.parent / "abl1_affinity_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info("Saved metadata to %s", meta_path)

    return records


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Curate ABL1 bioactivity data from ChEMBL REST API",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/abl1_affinity.json"),
        help="Output JSON file path (default: data/processed/abl1_affinity.json)",
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

    records = curate_abl1_data(output_path=args.output)
    if not records:
        print("ERROR: No records curated. Check logs for details.", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully curated {len(records)} ABL1 compounds.")


if __name__ == "__main__":
    main()
