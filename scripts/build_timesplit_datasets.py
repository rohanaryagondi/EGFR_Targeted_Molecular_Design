#!/usr/bin/env python3
"""Build time-split EGFR datasets for retrospective validation.

Fetches all EGFR bioactivity data with publication dates, splits by
cutoff year (2010, 2015), and saves training datasets with no temporal
leakage. Output format matches ``statebind.ml.affinity_dataset`` so
MPNN retraining can consume it directly.

Data sourcing (3-tier fallback):
  1. Local ChEMBL extract at ``data/raw/ligands/chembl_egfr_affinity.json``
  2. ChEMBL REST API (target CHEMBL203, with document_year extraction)
  3. Curated EGFR compound set with manual year assignments
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import statistics
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from statebind.data.paths import DataPaths
from statebind.evaluation.retrospective import (
    TimeSplitDataset,
    get_future_drugs,
    get_pre_cutoff_reference_binders,
    verify_no_leakage,
)
from statebind.utils.config import load_config
from statebind.utils.io import save_json

logger = logging.getLogger(__name__)

try:
    from rdkit import Chem  # type: ignore[import-untyped]

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


# ── SMILES validation and canonicalization ─────────────────────────────────


def _validate_smiles_basic(smiles: str) -> bool:
    """Check if a SMILES string is plausibly valid."""
    if not smiles or not smiles.strip():
        return False
    if HAS_RDKIT:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    if len(smiles) < 2:
        return False
    if smiles.count("(") != smiles.count(")"):
        return False
    if smiles.count("[") != smiles.count("]"):
        return False
    allowed = re.compile(r"^[A-Za-z0-9@+\-\[\]()\\/%=#$:.,~*!&^{}\s]+$")
    return bool(allowed.match(smiles))


def _canonicalize(smiles: str) -> str:
    """Return canonical SMILES if RDKit is available, else original."""
    if HAS_RDKIT:
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            return Chem.MolToSmiles(mol)
    return smiles


def _extract_pic50(entry: dict) -> float | None:
    """Extract pIC50 from a ChEMBL activity record."""
    pchembl = entry.get("pchembl_value")
    if pchembl is not None:
        try:
            val = float(pchembl)
            if 2.0 <= val <= 12.0:
                return val
        except (ValueError, TypeError):
            pass

    std_val = entry.get("standard_value")
    std_units = entry.get("standard_units", "")
    if std_val is None:
        return None

    try:
        std_val = float(std_val)
        if std_val <= 0:
            return None
    except (ValueError, TypeError):
        return None

    units_lower = str(std_units).strip().lower()
    if units_lower == "nm":
        pic50 = 9.0 - math.log10(std_val)
    elif units_lower in ("um", "µm"):
        pic50 = 6.0 - math.log10(std_val)
    elif units_lower == "mm":
        pic50 = 3.0 - math.log10(std_val)
    else:
        return None

    if 2.0 <= pic50 <= 12.0:
        return round(pic50, 4)
    return None


def _deduplicate_by_smiles(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate by canonical SMILES, taking median pIC50.

    Preserves the earliest document_year for each compound.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        canon = _canonicalize(str(rec["smiles"]))
        if canon not in groups:
            groups[canon] = []
        groups[canon].append(rec)

    deduped: list[dict[str, Any]] = []
    for canon, entries in groups.items():
        pic50s = [float(e["pIC50"]) for e in entries]
        median_pic50 = round(statistics.median(pic50s), 4)
        years = [
            e["document_year"]
            for e in entries
            if e.get("document_year") is not None
        ]
        earliest_year = min(years) if years else None
        deduped.append({
            "smiles": canon,
            "pIC50": median_pic50,
            "document_year": earliest_year,
        })

    return deduped


# ── Curated EGFR compounds with manual year assignments ────────────────────
#
# Year assignments based on:
#   - Known drug approval dates (FDA records)
#   - Approximate first ChEMBL deposition dates for analog classes
#   - Non-binder decoys assigned 1900 (always in training)

_CURATED_WITH_YEARS: list[tuple[str, float, int, str]] = [
    # (smiles, pIC50, publication_year, name)
    # ── 1st-generation reversible Type-I (pre-2005) ─────────────────────
    ("COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC", 8.2, 2001, "erlotinib"),
    ("COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1", 8.0, 2001, "gefitinib"),
    ("CCOc1cc2ncc(C#N)c(Nc3ccc(OCc4ccccn4)c(Cl)c3)c2cc1OCC", 7.6, 2005, "icotinib"),
    ("COc1cc(OC)c2c(Nc3ccc(Br)cc3F)ncnc2c1", 7.3, 2004, "vandetanib_core"),
    ("Clc1cccc(Nc2ncnc3cc(OCCCN4CCOCC4)c(OC)cc23)c1", 7.4, 2003, "type1_analog_01"),
    ("c1ccc(Nc2ncnc3ccccc23)cc1", 5.8, 1996, "4_anilinoquinazoline_core"),
    ("COc1cc2ncnc(Nc3ccc(F)cc3)c2cc1OC", 7.2, 2003, "type1_analog_02"),
    ("Fc1ccc(Nc2ncnc3cc(OCCN4CCOCC4)ccc23)cc1Cl", 7.5, 2004, "type1_analog_03"),
    ("COc1cc2ncnc(Nc3cccc(Br)c3)c2cc1OC", 7.1, 2003, "type1_analog_04"),
    ("COc1cc2ncnc(Nc3ccc(C)cc3)c2cc1OCCCN1CCOCC1", 7.3, 2004, "type1_analog_05"),
    ("COc1cc2ncnc(Nc3ccc(OC)c(Cl)c3)c2cc1", 7.0, 2003, "type1_analog_06"),
    ("Brc1cccc(Nc2ncnc3cc(OCCCN4CCOCC4)c(OC)cc23)c1", 7.2, 2004, "type1_analog_07"),
    ("c1ccc(Nc2ncnc3cc(OCCO)c(OCCO)cc23)cc1C#C", 7.6, 2002, "erlotinib_analog_01"),
    # ── Type-I½ (Src-like inactive, αC-helix out) ~2007 ─────────────────
    (
        "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1",
        7.0, 2007, "lapatinib",
    ),
    (
        "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5ccccc5)c(Cl)c4)c3c2)o1",
        6.8, 2007, "lapatinib_analog_01",
    ),
    ("Oc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)cc4)c3c2)cc1", 6.6, 2007, "type1h_analog_01"),
    (
        "O=C(Nc1ccc(-c2ccc3ncnc(Nc4ccc(F)c(Cl)c4)c3c2)cc1)c1ccccc1",
        6.7, 2007, "type1h_analog_02",
    ),
    (
        "COc1cc2ncnc(Nc3ccc(OCc4cccc(F)c4)c(Cl)c3)c2cc1OCCCN1CCOCC1",
        6.9, 2008, "type1h_analog_03",
    ),
    ("Clc1ccc(Nc2ncnc3cc(-c4ccncc4)ccc23)cc1OCc1cccc(F)c1", 6.5, 2008, "type1h_analog_04"),
    ("COc1cc2ncnc(Nc3ccc(OCc4ccc(F)cc4)c(Cl)c3)c2cc1", 6.7, 2008, "type1h_analog_05"),
    (
        "Fc1cccc(COc2ccc(Nc3ncnc4cc(OCCN5CCOCC5)ccc34)cc2Cl)c1",
        6.8, 2008, "type1h_analog_06",
    ),
    (
        "O=S(=O)(CCNCc1ccco1)c1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)cc1",
        6.6, 2008, "type1h_analog_07",
    ),
    (
        "COc1ccc(Nc2ncnc3cc(-c4ccc(CNCCCS(C)(=O)=O)o4)ccc23)cc1OCc1cccc(F)c1",
        6.9, 2009, "tucatinib_like",
    ),
    # ── Type-II (DFG-out binders) ~2006 ──────────────────────────────────
    ("CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)cc2)ccn1", 6.3, 2006, "sorafenib_like_01"),
    ("Cc1ccc(NC(=O)Nc2ccc(Oc3ccnc(NC(C)=O)c3)cc2)cc1C(F)(F)F", 6.1, 2006, "type2_analog_01"),
    (
        "O=C(Nc1ccc(Oc2cc(NC(=O)c3cccnc3)ccc2F)cc1)Nc1ccc(C(F)(F)F)cc1",
        6.2, 2007, "type2_analog_02",
    ),
    ("Fc1ccc(NC(=O)Nc2ccc(-c3ccnc4ccccc34)cc2)cc1C(F)(F)F", 6.0, 2007, "type2_analog_03"),
    ("CNC(=O)c1ccc(Oc2ccc(NC(=O)Nc3ccc(Cl)cc3)cc2)nc1", 6.2, 2007, "type2_analog_04"),
    ("O=C(Nc1ccccc1)Nc1ccc(Oc2ccnc(Nc3ccccc3)c2)cc1", 5.9, 2006, "type2_analog_05"),
    ("CC(=O)Nc1cccc(-c2cc(NC(=O)Nc3ccc(OC(F)(F)F)cc3)ccc2F)c1", 6.1, 2008, "type2_analog_06"),
    ("CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3cccc(C(F)(F)F)c3)cc2)ccn1", 6.3, 2006, "type2_analog_07"),
    ("O=C(Nc1ccc(F)cc1)Nc1ccc(Oc2cc(C(=O)NC3CC3)ccn2)cc1", 6.0, 2008, "type2_analog_08"),
    (
        "Cc1ccc(NC(=O)Nc2cc(Oc3ccnc(NC(=O)C4CC4)c3)ccc2F)cc1Cl",
        6.2, 2008, "type2_analog_09",
    ),
    # ── 2nd-gen covalent (irreversible, C797) ~2012 ─────────────────────
    ("CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1", 9.0, 2012, "afatinib"),
    ("CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCCC1", 8.8, 2012, "dacomitinib"),
    ("C=CC(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OCCCN1CCOCC1", 8.3, 2012, "covalent_analog_01"),
    # ── 3rd-gen mutant-selective covalent ~2014-2019 ─────────────────────
    (
        "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
        9.2, 2014, "osimertinib",
    ),
    (
        "C=CC(=O)Nc1cc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c(OC)cc1N(C)CCN(C)C",
        9.0, 2014, "osimertinib_analog_01",
    ),
    (
        "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2ccccn2)n1",
        8.7, 2015, "3rdgen_analog_01",
    ),
    ("C=CC(=O)Nc1cccc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c1OC", 8.5, 2019, "lazertinib_like"),
    (
        "C=CC(=O)Nc1cc(Nc2ncc(-c3cccnc3)c(-c3ccsc3)n2)c(OC)cc1N(C)CCN(C)C",
        8.6, 2019, "mobocertinib_like",
    ),
    (
        "C=CC(=O)Nc1cc(Nc2ncnc3cc(OC)c(OC)cc23)c(OC)cc1N1CCC(N(C)C)CC1",
        8.4, 2020, "aumolertinib_like",
    ),
    # ── Allosteric / non-competitive ~2008 ───────────────────────────────
    ("O=C(c1cc(F)cc(F)c1)c1ccc2[nH]c(-c3ccccc3)nc2c1", 5.3, 2008, "allosteric_01"),
    ("O=C(Nc1cccc(C(F)(F)F)c1)c1cnc2ccccc2n1", 5.1, 2008, "allosteric_02"),
    ("Cc1noc(NC(=O)c2ccc(F)cc2)c1-c1ccc(Cl)cc1", 5.2, 2009, "allosteric_03"),
    ("O=C(Nc1ccccc1F)c1cc(-c2ccncc2)no1", 5.0, 2009, "allosteric_04"),
    ("CC(=O)Nc1ccc(-c2cc(C(F)(F)F)nn2-c2ccccc2)cc1", 5.4, 2008, "allosteric_05"),
    ("O=C(Nc1ccc(F)cc1F)c1ccc(-c2cccnc2)o1", 5.1, 2009, "allosteric_06"),
    ("O=C(c1ccc(F)cc1)N1CCN(c2ncnc3ccccc23)CC1", 5.3, 2008, "allosteric_07"),
    ("Cc1cc(-c2cccc(NC(=O)c3ccc(C#N)cc3)c2)on1", 5.2, 2009, "allosteric_08"),
    ("O=C(Nc1cccc(-c2noc(C(F)(F)F)n2)c1)c1ccc(Cl)cc1", 5.0, 2009, "allosteric_09"),
    ("CC(=O)Nc1ccc2oc(-c3ccc(O)cc3)nc2c1", 5.4, 2008, "allosteric_10"),
    # ── Non-binder decoys (always in training) ───────────────────────────
    ("CC(=O)Oc1ccccc1C(O)=O", 3.0, 1900, "aspirin"),
    ("CC(=O)Nc1ccc(O)cc1", 3.2, 1900, "acetaminophen"),
    ("CN1C(=O)N(C)c2[nH]cnc2C1=O", 3.0, 1900, "caffeine"),
    ("CN(C)C(=O)Oc1cccc([N+](C)(C)C)c1", 3.1, 1900, "neostigmine"),
    ("CC(C)Cc1ccc(C(C)C(O)=O)cc1", 3.3, 1900, "ibuprofen"),
    ("CC(C)NCC(O)c1ccc(O)c(O)c1", 3.5, 1900, "isoproterenol"),
    ("CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21", 3.2, 1900, "chlordiazepoxide_core"),
    ("OC(=O)c1ccccc1O", 3.0, 1900, "salicylic_acid"),
    ("CC(=O)OC1CC(OC2OC(CO)C(O)C(O)C2O)C(O)C(O)C1O", 3.1, 1900, "glucose_acetate"),
    ("CN(CC(O)=O)N=O", 3.0, 1900, "sarcosine_nitroso"),
    ("OC(=O)CCCCC(=O)O", 3.0, 1900, "adipic_acid"),
    ("CN1C2CCC1CC(OC(=O)C(CO)c1ccccc1)C2", 3.4, 1900, "atropine"),
    ("CC12CCC3C(CCC4CC(O)CCC43C)C1CCC2O", 3.1, 1900, "testosterone"),
    ("OC(=O)c1cc(O)c(O)c(O)c1", 3.0, 1900, "gallic_acid"),
    ("Cn1c(=O)c2c(ncn2C)n(C)c1=O", 3.0, 1900, "caffeine_variant"),
    ("OC(=O)/C=C/c1ccccc1", 3.2, 1900, "cinnamic_acid"),
    ("CC1(C)CCC2(CC1)OC(=O)CC(=O)O2", 3.0, 1900, "meldrum_acid"),
    ("NC(=N)NC(=O)c1nc(Cl)c(N)n1C", 3.5, 1900, "amiloride_core"),
    ("c1ccc(NC(=O)c2ccccc2)cc1", 3.3, 1900, "benzanilide"),
    ("OC(=O)c1ccc(N)cc1", 3.1, 1900, "paba"),
    ("CC(C)(O)c1ccc(Cl)cc1", 3.0, 1900, "chlorophenol_tert"),
    ("OC(=O)CCc1ccccc1", 3.2, 1900, "hydrocinnamic_acid"),
    ("CC1=CC(=O)c2ccccc2C1=O", 3.0, 1900, "menadione"),
    ("CN(C)CCCN1c2ccccc2Sc2ccc(Cl)cc21", 3.8, 1900, "chlorpromazine"),
    ("CC(=O)Oc1ccc(OC(C)=O)c(C(C)=O)c1", 3.0, 1900, "diacetylacetophenone"),
    ("c1ccc2[nH]ccc2c1", 3.0, 1900, "indole"),
    ("Oc1ccc2ccccc2c1", 3.0, 1900, "2_naphthol"),
    ("CC(O)CC(=O)c1ccccc1", 3.1, 1900, "phenyl_hydroxyketone"),
    ("OC(=O)c1ccncc1", 3.0, 1900, "nicotinic_acid"),
    ("CC(C)C(=O)Oc1ccccc1OC(=O)C(C)C", 3.0, 1900, "diisobutyrate"),
]


# ── Tier 1: Local file ────────────────────────────────────────────────────


def _load_local_file(raw_dir: Path) -> list[dict[str, Any]] | None:
    """Load ChEMBL EGFR affinity data from local file with document_year."""
    path = raw_dir / "ligands" / "chembl_egfr_affinity.json"
    if not path.exists():
        return None

    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.warning("Failed to parse %s, falling back", path)
        return None

    if not isinstance(data, list):
        return None

    records: list[dict[str, Any]] = []
    for entry in data:
        smiles = entry.get("smiles", "") or entry.get("canonical_smiles", "")
        if not smiles or not _validate_smiles_basic(smiles):
            continue
        pic50 = _extract_pic50(entry)
        if pic50 is None:
            continue
        doc_year = entry.get("document_year")
        if doc_year is not None:
            try:
                doc_year = int(doc_year)
            except (ValueError, TypeError):
                doc_year = None
        records.append({
            "smiles": smiles,
            "pIC50": pic50,
            "document_year": doc_year,
        })

    return records if records else None


# ── Tier 2: ChEMBL API ────────────────────────────────────────────────────


def _fetch_chembl_api_with_dates(
    max_pages: int = 40,
) -> list[dict[str, Any]] | None:
    """Fetch EGFR binding affinity data from ChEMBL REST API with dates.

    Like ``prepare_mpnn_data._fetch_chembl_api()`` but also extracts
    ``document_year`` from each activity record for time-split filtering.
    """
    base_url = (
        "https://www.ebi.ac.uk/chembl/api/data/activity.json"
        "?target_chembl_id=CHEMBL203"
        "&pchembl_value__gte=3"
        "&standard_type=IC50"
        "&limit=500"
        "&format=json"
    )

    all_activities: list[dict] = []

    for page in range(max_pages):
        url = f"{base_url}&offset={page * 500}"
        try:
            req = urllib.request.Request(
                url, headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ) as exc:
            logger.info("ChEMBL API page %d failed (%s)", page, exc)
            break

        activities = data.get("activities", [])
        if not activities:
            break
        all_activities.extend(activities)

        if data.get("page_meta", {}).get("next") is None:
            break

    if not all_activities:
        logger.info("ChEMBL API returned no activities, using fallback")
        return None

    records: list[dict[str, Any]] = []
    for act in all_activities:
        smiles = act.get("canonical_smiles", "")
        if not smiles or not _validate_smiles_basic(smiles):
            continue
        pic50 = _extract_pic50(act)
        if pic50 is None:
            continue

        doc_year = act.get("document_year")
        if doc_year is not None:
            try:
                doc_year = int(doc_year)
            except (ValueError, TypeError):
                doc_year = None

        records.append({
            "smiles": smiles,
            "pIC50": pic50,
            "document_year": doc_year,
        })

    return records if records else None


# ── Tier 3: Curated fallback ──────────────────────────────────────────────


def _curated_compounds_with_years() -> list[dict[str, Any]]:
    """Return curated EGFR compounds with pIC50 and publication years."""
    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    for smiles, pic50, year, _name in _CURATED_WITH_YEARS:
        if not smiles or not _validate_smiles_basic(smiles):
            continue
        canon = _canonicalize(smiles)
        if canon in seen:
            continue
        seen.add(canon)
        records.append({
            "smiles": canon,
            "pIC50": pic50,
            "document_year": year,
        })

    return records


# ── Time-split logic ──────────────────────────────────────────────────────


def build_timesplit_dataset(
    records: list[dict[str, Any]],
    cutoff_year: int,
    source: str = "",
) -> TimeSplitDataset:
    """Split records by cutoff year and build a TimeSplitDataset.

    Records without a ``document_year`` are excluded (cannot be reliably
    placed before or after a cutoff).

    Future drugs (from ``EGFR_DRUG_APPROVALS``) are removed from the
    training set regardless of document_year.

    Raises ``ValueError`` if temporal leakage is detected.
    """
    future_drugs = get_future_drugs(cutoff_year)
    future_smiles = {_canonicalize(d["smiles"]) for d in future_drugs}
    pre_cutoff_refs = get_pre_cutoff_reference_binders(cutoff_year)

    train_records: list[dict[str, Any]] = []
    for rec in records:
        doc_year = rec.get("document_year")
        if doc_year is None:
            continue
        if doc_year > cutoff_year:
            continue
        canon = _canonicalize(str(rec["smiles"]))
        if canon in future_smiles:
            continue
        train_records.append(rec)

    train_smiles = [str(r["smiles"]) for r in train_records]
    train_pic50 = [float(r["pIC50"]) for r in train_records]

    # Verify no leakage
    train_smiles_set = {_canonicalize(s) for s in train_smiles}
    verify_no_leakage(train_smiles_set, future_drugs)

    held_out = [
        {"name": d["name"], "smiles": d["smiles"], "approved_year": d["approved_year"]}
        for d in future_drugs
    ]

    return TimeSplitDataset(
        cutoff_year=cutoff_year,
        train_smiles=train_smiles,
        train_pIC50=train_pic50,
        n_train=len(train_smiles),
        held_out_drugs=held_out,
        n_held_out=len(held_out),
        pre_cutoff_reference_binders=pre_cutoff_refs,
        source=source,
    )


# ── Main ───────────────────────────────────────────────────────────────────


def build_all_timesplit_datasets(
    config_path: str | Path = "configs/retrospective.yaml",
    output_dir: Path | None = None,
) -> list[TimeSplitDataset]:
    """Build time-split datasets for all configured cutoffs.

    Returns list of ``TimeSplitDataset`` objects.
    """
    config = load_config(str(config_path))
    retro = config.get("retrospective", {})
    cutoffs = retro.get("cutoffs", [2010, 2015])
    data_config = config.get("data", {})
    max_pages = data_config.get("chembl_max_pages", 40)

    paths = DataPaths()
    if output_dir is None:
        output_dir = paths.processed_dir
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3-tier data sourcing
    records = _load_local_file(paths.raw_dir)
    source = "local_file"
    if records:
        logger.info("Tier 1: Loaded %d records from local file", len(records))
    else:
        records = _fetch_chembl_api_with_dates(max_pages=max_pages)
        source = "chembl_api"
        if records:
            logger.info("Tier 2: Fetched %d records from ChEMBL API", len(records))
        else:
            records = _curated_compounds_with_years()
            source = "curated_fallback"
            logger.info("Tier 3: Using %d curated compounds", len(records))

    # Deduplicate
    records = _deduplicate_by_smiles(records)
    logger.info("After dedup: %d unique compounds", len(records))

    # Count records with valid years
    with_years = sum(1 for r in records if r.get("document_year") is not None)
    logger.info("Records with publication year: %d / %d", with_years, len(records))

    # Build dataset for each cutoff
    datasets: list[TimeSplitDataset] = []
    for cutoff in cutoffs:
        ds = build_timesplit_dataset(records, cutoff, source=source)
        datasets.append(ds)

        # Save training data (MPNN-compatible format)
        train_path = output_dir / f"timesplit_{cutoff}_train.json"
        train_data = [
            {"smiles": s, "pIC50": p}
            for s, p in zip(ds.train_smiles, ds.train_pIC50)
        ]
        save_json(train_data, train_path)

        # Save metadata
        meta = {
            "cutoff_year": cutoff,
            "source": source,
            "n_train": ds.n_train,
            "n_held_out": ds.n_held_out,
            "held_out_drugs": ds.held_out_drugs,
            "pre_cutoff_reference_binders": ds.pre_cutoff_reference_binders,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "notes": (
                f"Time-split EGFR dataset for retrospective validation. "
                f"Training data restricted to compounds published <= {cutoff}. "
                f"Future drugs excluded from training set."
            ),
        }
        meta_path = output_dir / f"timesplit_{cutoff}_metadata.json"
        save_json(meta, meta_path)

        logger.info(
            "Cutoff %d: %d training compounds, %d held-out drugs",
            cutoff, ds.n_train, ds.n_held_out,
        )

    return datasets


def _print_summary(datasets: list[TimeSplitDataset]) -> None:
    """Print summary table for all time-split datasets."""
    print(f"\n{'=' * 70}")
    print("Time-Split Dataset Summary")
    print(f"{'=' * 70}")
    print(f"{'Cutoff':<10} {'Source':<18} {'N_train':<10} {'N_held_out':<12} {'Ref binders'}")
    print(f"{'-'*10} {'-'*18} {'-'*10} {'-'*12} {'-'*20}")
    for ds in datasets:
        print(
            f"{ds.cutoff_year:<10} {ds.source:<18} {ds.n_train:<10} "
            f"{ds.n_held_out:<12} {len(ds.pre_cutoff_reference_binders)}"
        )
        for drug in ds.held_out_drugs:
            print(f"  Held out: {drug['name']} (approved {drug['approved_year']})")

        if ds.train_pIC50:
            print(
                f"  pIC50: min={min(ds.train_pIC50):.2f} "
                f"mean={statistics.mean(ds.train_pIC50):.2f} "
                f"max={max(ds.train_pIC50):.2f}"
            )
    print(f"{'=' * 70}\n")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build time-split EGFR datasets for retrospective validation",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/retrospective.yaml",
        help="Path to retrospective config YAML",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/processed/)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    output = Path(args.output_dir) if args.output_dir else None
    datasets = build_all_timesplit_datasets(
        config_path=args.config,
        output_dir=output,
    )
    _print_summary(datasets)


if __name__ == "__main__":
    main()
