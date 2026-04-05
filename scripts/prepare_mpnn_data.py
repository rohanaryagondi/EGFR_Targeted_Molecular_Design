#!/usr/bin/env python3
"""Prepare EGFR binding affinity data for MPNN training.

Produces a single JSON file in the format expected by
``statebind.ml.affinity_dataset.load_affinity_dataset``:

    [{"smiles": "...", "pIC50": 7.82}, ...]

Data sourcing (3-tier fallback):
  1. Local ChEMBL extract at ``data/raw/ligands/chembl_egfr_affinity.json``
  2. ChEMBL REST API (target CHEMBL203, pchembl_value >= 3)
  3. Curated EGFR compound set (~90 compounds, always available)

pIC50 = -log10(IC50 in molar). For ChEMBL records, ``pchembl_value`` is
used directly. Duplicates (same canonical SMILES) are resolved by taking
the median pIC50.
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

from statebind.baselines.scoring import _REFERENCE_BINDERS
from statebind.data.paths import DataPaths
from statebind.processing.ligands import _v1_curated_ligands
from statebind.utils.io import save_json

logger = logging.getLogger(__name__)

try:
    from rdkit import Chem  # type: ignore[import-untyped]

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


# ── Curated EGFR affinity compounds (Tier 3 fallback) ────────────────────

# Each entry: (smiles, pIC50, drug_name)
# pIC50 assignments by inhibitor class:
#   1st-gen reversible Type-I:   7.0-7.5 (moderate EGFR binders)
#   Type-I½ (Src-like inactive): 6.5-7.0 (moderate, less potent)
#   Type-II (DFG-out):           6.0-6.5 (lower EGFR affinity)
#   2nd-gen covalent:            8.0-8.5 (potent, irreversible)
#   3rd-gen mutant-selective:    8.5-9.2 (most potent against T790M)
#   Allosteric:                  5.0-5.5 (weakest class)
#   Non-binder decoys:           3.0-4.5 (background/negative examples)
# Known drug pIC50 values from ChEMBL where available.
_CURATED_EGFR_AFFINITY: list[tuple[str, float, str]] = [
    # ── 1st-generation reversible Type-I ──────────────────────────────
    ("COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC", 8.2, "erlotinib"),
    ("COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1", 8.0, "gefitinib"),
    ("CCOc1cc2ncc(C#N)c(Nc3ccc(OCc4ccccn4)c(Cl)c3)c2cc1OCC", 7.6, "icotinib"),
    ("COc1cc(OC)c2c(Nc3ccc(Br)cc3F)ncnc2c1", 7.3, "vandetanib_core"),
    ("Clc1cccc(Nc2ncnc3cc(OCCCN4CCOCC4)c(OC)cc23)c1", 7.4, "type1_analog_01"),
    ("c1ccc(Nc2ncnc3ccccc23)cc1", 5.8, "4_anilinoquinazoline_core"),
    ("COc1cc2ncnc(Nc3ccc(F)cc3)c2cc1OC", 7.2, "type1_analog_02"),
    ("Fc1ccc(Nc2ncnc3cc(OCCN4CCOCC4)ccc23)cc1Cl", 7.5, "type1_analog_03"),
    ("COc1cc2ncnc(Nc3cccc(Br)c3)c2cc1OC", 7.1, "type1_analog_04"),
    ("COc1cc2ncnc(Nc3ccc(C)cc3)c2cc1OCCCN1CCOCC1", 7.3, "type1_analog_05"),
    ("COc1cc2ncnc(Nc3ccc(OC)c(Cl)c3)c2cc1", 7.0, "type1_analog_06"),
    ("Brc1cccc(Nc2ncnc3cc(OCCCN4CCOCC4)c(OC)cc23)c1", 7.2, "type1_analog_07"),
    ("c1ccc(Nc2ncnc3cc(OCCO)c(OCCO)cc23)cc1C#C", 7.6, "erlotinib_analog_01"),
    # ── Type-I½ (Src-like inactive, αC-helix out) ────────────────────
    (
        "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1",
        7.0, "lapatinib",
    ),
    (
        "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5ccccc5)c(Cl)c4)c3c2)o1",
        6.8, "lapatinib_analog_01",
    ),
    ("Oc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)cc4)c3c2)cc1", 6.6, "type1h_analog_01"),
    (
        "O=C(Nc1ccc(-c2ccc3ncnc(Nc4ccc(F)c(Cl)c4)c3c2)cc1)c1ccccc1",
        6.7, "type1h_analog_02",
    ),
    (
        "COc1cc2ncnc(Nc3ccc(OCc4cccc(F)c4)c(Cl)c3)c2cc1OCCCN1CCOCC1",
        6.9, "type1h_analog_03",
    ),
    ("Clc1ccc(Nc2ncnc3cc(-c4ccncc4)ccc23)cc1OCc1cccc(F)c1", 6.5, "type1h_analog_04"),
    ("COc1cc2ncnc(Nc3ccc(OCc4ccc(F)cc4)c(Cl)c3)c2cc1", 6.7, "type1h_analog_05"),
    (
        "Fc1cccc(COc2ccc(Nc3ncnc4cc(OCCN5CCOCC5)ccc34)cc2Cl)c1",
        6.8, "type1h_analog_06",
    ),
    (
        "O=S(=O)(CCNCc1ccco1)c1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)cc1",
        6.6, "type1h_analog_07",
    ),
    (
        "COc1ccc(Nc2ncnc3cc(-c4ccc(CNCCCS(C)(=O)=O)o4)ccc23)cc1OCc1cccc(F)c1",
        6.9, "tucatinib_like",
    ),
    # ── Type-II (DFG-out binders) ────────────────────────────────────
    ("CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)cc2)ccn1", 6.3, "sorafenib_like_01"),
    ("Cc1ccc(NC(=O)Nc2ccc(Oc3ccnc(NC(C)=O)c3)cc2)cc1C(F)(F)F", 6.1, "type2_analog_01"),
    (
        "O=C(Nc1ccc(Oc2cc(NC(=O)c3cccnc3)ccc2F)cc1)Nc1ccc(C(F)(F)F)cc1",
        6.2, "type2_analog_02",
    ),
    ("Fc1ccc(NC(=O)Nc2ccc(-c3ccnc4ccccc34)cc2)cc1C(F)(F)F", 6.0, "type2_analog_03"),
    ("CNC(=O)c1ccc(Oc2ccc(NC(=O)Nc3ccc(Cl)cc3)cc2)nc1", 6.2, "type2_analog_04"),
    ("O=C(Nc1ccccc1)Nc1ccc(Oc2ccnc(Nc3ccccc3)c2)cc1", 5.9, "type2_analog_05"),
    ("CC(=O)Nc1cccc(-c2cc(NC(=O)Nc3ccc(OC(F)(F)F)cc3)ccc2F)c1", 6.1, "type2_analog_06"),
    ("CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3cccc(C(F)(F)F)c3)cc2)ccn1", 6.3, "type2_analog_07"),
    ("O=C(Nc1ccc(F)cc1)Nc1ccc(Oc2cc(C(=O)NC3CC3)ccn2)cc1", 6.0, "type2_analog_08"),
    (
        "Cc1ccc(NC(=O)Nc2cc(Oc3ccnc(NC(=O)C4CC4)c3)ccc2F)cc1Cl",
        6.2, "type2_analog_09",
    ),
    # ── 2nd-gen covalent (irreversible, C797) ────────────────────────
    ("CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1", 9.0, "afatinib"),
    ("CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCCC1", 8.8, "dacomitinib"),
    ("C=CC(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OCCCN1CCOCC1", 8.3, "covalent_analog_01"),
    # ── 3rd-gen mutant-selective covalent ─────────────────────────────
    (
        "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
        9.2, "osimertinib",
    ),
    (
        "C=CC(=O)Nc1cc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c(OC)cc1N(C)CCN(C)C",
        9.0, "osimertinib_analog_01",
    ),
    (
        "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2ccccn2)n1",
        8.7, "3rdgen_analog_01",
    ),
    ("C=CC(=O)Nc1cccc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c1OC", 8.5, "lazertinib_like"),
    (
        "C=CC(=O)Nc1cc(Nc2ncc(-c3cccnc3)c(-c3ccsc3)n2)c(OC)cc1N(C)CCN(C)C",
        8.6, "mobocertinib_like",
    ),
    (
        "C=CC(=O)Nc1cc(Nc2ncnc3cc(OC)c(OC)cc23)c(OC)cc1N1CCC(N(C)C)CC1",
        8.4, "aumolertinib_like",
    ),
    # ── Allosteric / non-competitive ─────────────────────────────────
    ("O=C(c1cc(F)cc(F)c1)c1ccc2[nH]c(-c3ccccc3)nc2c1", 5.3, "allosteric_01"),
    ("O=C(Nc1cccc(C(F)(F)F)c1)c1cnc2ccccc2n1", 5.1, "allosteric_02"),
    ("Cc1noc(NC(=O)c2ccc(F)cc2)c1-c1ccc(Cl)cc1", 5.2, "allosteric_03"),
    ("O=C(Nc1ccccc1F)c1cc(-c2ccncc2)no1", 5.0, "allosteric_04"),
    ("CC(=O)Nc1ccc(-c2cc(C(F)(F)F)nn2-c2ccccc2)cc1", 5.4, "allosteric_05"),
    ("O=C(Nc1ccc(F)cc1F)c1ccc(-c2cccnc2)o1", 5.1, "allosteric_06"),
    ("O=C(c1ccc(F)cc1)N1CCN(c2ncnc3ccccc23)CC1", 5.3, "allosteric_07"),
    ("Cc1cc(-c2cccc(NC(=O)c3ccc(C#N)cc3)c2)on1", 5.2, "allosteric_08"),
    ("O=C(Nc1cccc(-c2noc(C(F)(F)F)n2)c1)c1ccc(Cl)cc1", 5.0, "allosteric_09"),
    ("CC(=O)Nc1ccc2oc(-c3ccc(O)cc3)nc2c1", 5.4, "allosteric_10"),
    # ── Non-binder decoys (negative examples) ────────────────────────
    ("CC(=O)Oc1ccccc1C(O)=O", 3.0, "aspirin"),
    ("CC(=O)Nc1ccc(O)cc1", 3.2, "acetaminophen"),
    ("CN1C(=O)N(C)c2[nH]cnc2C1=O", 3.0, "caffeine"),
    ("CN(C)C(=O)Oc1cccc([N+](C)(C)C)c1", 3.1, "neostigmine"),
    ("CC(C)Cc1ccc(C(C)C(O)=O)cc1", 3.3, "ibuprofen"),
    ("CC(C)NCC(O)c1ccc(O)c(O)c1", 3.5, "isoproterenol"),
    ("CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21", 3.2, "chlordiazepoxide_core"),
    ("OC(=O)c1ccccc1O", 3.0, "salicylic_acid"),
    ("CC(=O)OC1CC(OC2OC(CO)C(O)C(O)C2O)C(O)C(O)C1O", 3.1, "glucose_acetate"),
    ("CN(CC(O)=O)N=O", 3.0, "sarcosine_nitroso"),
    ("OC(=O)CCCCC(=O)O", 3.0, "adipic_acid"),
    ("CN1C2CCC1CC(OC(=O)C(CO)c1ccccc1)C2", 3.4, "atropine"),
    ("CC12CCC3C(CCC4CC(O)CCC43C)C1CCC2O", 3.1, "testosterone"),
    ("OC(=O)c1cc(O)c(O)c(O)c1", 3.0, "gallic_acid"),
    ("Cn1c(=O)c2c(ncn2C)n(C)c1=O", 3.0, "caffeine_variant"),
    ("OC(=O)/C=C/c1ccccc1", 3.2, "cinnamic_acid"),
    ("CC1(C)CCC2(CC1)OC(=O)CC(=O)O2", 3.0, "meldrum_acid"),
    ("NC(=N)NC(=O)c1nc(Cl)c(N)n1C", 3.5, "amiloride_core"),
    ("c1ccc(NC(=O)c2ccccc2)cc1", 3.3, "benzanilide"),
    ("OC(=O)c1ccc(N)cc1", 3.1, "paba"),
    ("CC(C)(O)c1ccc(Cl)cc1", 3.0, "chlorophenol_tert"),
    ("OC(=O)CCc1ccccc1", 3.2, "hydrocinnamic_acid"),
    ("CC1=CC(=O)c2ccccc2C1=O", 3.0, "menadione"),
    ("CN(C)CCCN1c2ccccc2Sc2ccc(Cl)cc21", 3.8, "chlorpromazine"),
    ("CC(=O)Oc1ccc(OC(C)=O)c(C(C)=O)c1", 3.0, "diacetylacetophenone"),
    ("c1ccc2[nH]ccc2c1", 3.0, "indole"),
    ("Oc1ccc2ccccc2c1", 3.0, "2_naphthol"),
    ("CC(O)CC(=O)c1ccccc1", 3.1, "phenyl_hydroxyketone"),
    ("OC(=O)c1ccncc1", 3.0, "nicotinic_acid"),
    ("CC(C)C(=O)Oc1ccccc1OC(=O)C(C)C", 3.0, "diisobutyrate"),
]


def _validate_smiles_basic(smiles: str) -> bool:
    """Check if a SMILES string is plausibly valid.

    Uses RDKit if available, otherwise applies heuristic checks:
    balanced parentheses/brackets, valid characters, minimum length.
    """
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
    allowed = re.compile(
        r"^[A-Za-z0-9@+\-\[\]()\\/%=#$:.,~*!&^{}\s]+$"
    )
    return bool(allowed.match(smiles))


def _canonicalize(smiles: str) -> str:
    """Return canonical SMILES if RDKit is available, else original."""
    if HAS_RDKIT:
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            return Chem.MolToSmiles(mol)
    return smiles


def _curated_egfr_affinity_compounds() -> list[dict[str, float | str]]:
    """Return curated EGFR compounds with pIC50 values.

    Combines:
    1. Hard-coded curated set (~90 compounds with assigned pIC50)
    2. Curated ligands from processing/ligands.py (with known pIC50)
    3. Reference binders from baselines/scoring.py (assigned pIC50)

    Deduplicates by canonical SMILES.
    """
    seen: set[str] = set()
    records: list[dict[str, float | str]] = []

    # 1. Hard-coded curated compounds (primary source)
    for smiles, pic50, _name in _CURATED_EGFR_AFFINITY:
        if not smiles or not _validate_smiles_basic(smiles):
            continue
        canon = _canonicalize(smiles)
        if canon in seen:
            continue
        seen.add(canon)
        records.append({"smiles": canon, "pIC50": pic50})

    # 2. Curated ligands from processing/ligands.py:19
    for lig in _v1_curated_ligands():
        smiles = lig.canonical_smiles
        if not smiles or not _validate_smiles_basic(smiles):
            continue
        canon = _canonicalize(smiles)
        if canon in seen:
            continue
        seen.add(canon)
        # Use known pIC50 from LigandRecord if available
        pic50 = getattr(lig, "pIC50", None)
        if pic50 is None or not isinstance(pic50, (int, float)):
            pic50 = 7.5  # reasonable default for known EGFR drugs
        records.append({"smiles": canon, "pIC50": float(pic50)})

    # 3. Reference binders from baselines/scoring.py:59-66
    ref_pic50 = {
        0: 8.2,  # erlotinib
        1: 8.0,  # gefitinib
        2: 9.2,  # osimertinib
    }
    for idx, smiles in enumerate(_REFERENCE_BINDERS):
        if not _validate_smiles_basic(smiles):
            continue
        canon = _canonicalize(smiles)
        if canon in seen:
            continue
        seen.add(canon)
        records.append({"smiles": canon, "pIC50": ref_pic50.get(idx, 8.0)})

    return records


def _load_local_file(raw_dir: Path) -> list[dict[str, float | str]] | None:
    """Attempt to load ChEMBL EGFR affinity data from local file.

    Expected path: ``data/raw/ligands/chembl_egfr_affinity.json``
    Expected format: list of dicts with ``smiles`` and either
    ``pchembl_value`` or (``standard_value`` + ``standard_units``).

    Returns None if file not found or unparseable.
    """
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

    records: list[dict[str, float | str]] = []
    for entry in data:
        smiles = entry.get("smiles", "") or entry.get("canonical_smiles", "")
        if not smiles or not _validate_smiles_basic(smiles):
            continue

        # Extract pIC50
        pic50 = _extract_pic50(entry)
        if pic50 is None:
            continue

        records.append({"smiles": smiles, "pIC50": pic50})

    return records if records else None


def _extract_pic50(entry: dict) -> float | None:
    """Extract pIC50 from a ChEMBL activity record.

    Prefers ``pchembl_value`` (already -log10(M)).
    Falls back to converting ``standard_value`` + ``standard_units``.
    """
    # Prefer pchembl_value (pre-computed by ChEMBL)
    pchembl = entry.get("pchembl_value")
    if pchembl is not None:
        try:
            val = float(pchembl)
            if 2.0 <= val <= 12.0:
                return val
        except (ValueError, TypeError):
            pass

    # Fallback: convert from standard_value + standard_units
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


def _fetch_chembl_api() -> list[dict[str, float | str]] | None:
    """Fetch EGFR binding affinity data from ChEMBL REST API.

    Queries CHEMBL203 (EGFR) for compounds with pchembl_value >= 3.
    Paginates up to 5 pages (2500 records max).
    Uses urllib (no external dependencies).

    Returns None on any failure.
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

    for page in range(40):
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

        # Stop if no more pages
        if data.get("page_meta", {}).get("next") is None:
            break

    if not all_activities:
        logger.info("ChEMBL API returned no activities, using fallback")
        return None

    records: list[dict[str, float | str]] = []
    for act in all_activities:
        smiles = act.get("canonical_smiles", "")
        if not smiles or not _validate_smiles_basic(smiles):
            continue
        pic50 = _extract_pic50(act)
        if pic50 is None:
            continue
        records.append({"smiles": smiles, "pIC50": pic50})

    return records if records else None


def _deduplicate_by_smiles(
    records: list[dict[str, float | str]],
) -> list[dict[str, float | str]]:
    """Deduplicate records by canonical SMILES, taking median pIC50.

    Returns a new list with unique canonical SMILES.
    """
    # Group pIC50 values by canonical SMILES
    groups: dict[str, list[float]] = {}
    for rec in records:
        canon = _canonicalize(str(rec["smiles"]))
        pic50 = float(rec["pIC50"])
        if canon not in groups:
            groups[canon] = []
        groups[canon].append(pic50)

    # Take median for each group
    deduped: list[dict[str, float | str]] = []
    for canon, values in groups.items():
        median_pic50 = round(statistics.median(values), 4)
        deduped.append({"smiles": canon, "pIC50": median_pic50})

    return deduped


def prepare_mpnn_training_data(
    seed: int = 42,
    output_dir: Path | None = None,
) -> tuple[list[dict[str, float | str]], str]:
    """Prepare MPNN training data with 3-tier fallback.

    Args:
        seed: Random seed for reproducibility.
        output_dir: Directory for output JSON. Defaults to
            ``data/processed/``.

    Returns:
        (records, source_name) where records is the deduplicated dataset
        and source_name describes which tier was used.
    """
    paths = DataPaths()
    if output_dir is None:
        output_dir = paths.processed_dir

    # Tier 1: Local file
    records = _load_local_file(paths.raw_dir)
    source = "local_file"
    if records:
        logger.info("Tier 1: Loaded %d records from local file", len(records))
    else:
        # Tier 2: ChEMBL API
        records = _fetch_chembl_api()
        source = "chembl_api"
        if records:
            logger.info("Tier 2: Fetched %d records from ChEMBL API", len(records))
        else:
            # Tier 3: Curated compounds
            records = _curated_egfr_affinity_compounds()
            source = "curated_fallback"
            logger.info("Tier 3: Using %d curated compounds", len(records))

    # Deduplicate
    records = _deduplicate_by_smiles(records)
    logger.info("After deduplication: %d unique compounds", len(records))

    # Save output
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "egfr_affinity.json"
    save_json(records, output_path)
    logger.info("Saved training data to %s", output_path)

    # Save metadata
    pic50_values = [float(r["pIC50"]) for r in records]
    metadata = {
        "source": source,
        "n_compounds": len(records),
        "pIC50_min": round(min(pic50_values), 4) if pic50_values else 0.0,
        "pIC50_max": round(max(pic50_values), 4) if pic50_values else 0.0,
        "pIC50_mean": round(statistics.mean(pic50_values), 4) if pic50_values else 0.0,
        "pIC50_median": round(statistics.median(pic50_values), 4) if pic50_values else 0.0,
        "pIC50_stdev": (
            round(statistics.stdev(pic50_values), 4) if len(pic50_values) > 1 else 0.0
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "notes": (
            "EGFR binding affinity data for MPNN training. "
            "pIC50 = -log10(IC50 in molar). Higher = more potent."
        ),
    }
    meta_path = output_dir / "egfr_affinity_metadata.json"
    save_json(metadata, meta_path)

    return records, source


def _print_summary(
    records: list[dict[str, float | str]],
    source: str,
) -> None:
    """Print summary statistics for the prepared dataset."""
    n = len(records)
    pic50s = [float(r["pIC50"]) for r in records]

    print(f"\n{'=' * 60}")
    print("MPNN Training Data Summary")
    print(f"{'=' * 60}")
    print(f"Source:     {source}")
    print(f"Compounds:  {n}")
    if pic50s:
        print(f"pIC50 min:  {min(pic50s):.2f}")
        print(f"pIC50 max:  {max(pic50s):.2f}")
        print(f"pIC50 mean: {statistics.mean(pic50s):.2f}")
        print(f"pIC50 std:  {statistics.stdev(pic50s) if len(pic50s) > 1 else 0:.2f}")

        # Distribution by potency class
        potent = sum(1 for v in pic50s if v >= 8.0)
        moderate = sum(1 for v in pic50s if 6.0 <= v < 8.0)
        weak = sum(1 for v in pic50s if 4.0 <= v < 6.0)
        inactive = sum(1 for v in pic50s if v < 4.0)
        print("\nPotency distribution:")
        print(f"  Potent (pIC50 >= 8):   {potent:4d} ({100*potent/n:.1f}%)")
        print(f"  Moderate (6-8):        {moderate:4d} ({100*moderate/n:.1f}%)")
        print(f"  Weak (4-6):            {weak:4d} ({100*weak/n:.1f}%)")
        print(f"  Inactive (< 4):        {inactive:4d} ({100*inactive/n:.1f}%)")
    print(f"{'=' * 60}\n")


def main() -> None:
    """Entry point for data preparation."""
    parser = argparse.ArgumentParser(
        description="Prepare EGFR affinity data for MPNN training"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: data/processed/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    records, source = prepare_mpnn_training_data(
        seed=args.seed,
        output_dir=args.output_dir,
    )
    _print_summary(records, source)


if __name__ == "__main__":
    main()
