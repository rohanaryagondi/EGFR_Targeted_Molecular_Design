#!/usr/bin/env python3
"""Prepare EGFR SMILES training data for the Conditional VAE.

Produces train/val JSON files in the format expected by
``statebind.ml.vae_dataset.load_smiles_dataset``:

    [{"smiles": "...", "state": "DFGin_aCin"}, ...]

Data sourcing (3-tier fallback):
  1. Local ChEMBL extract at ``data/raw/ligands/chembl_egfr.json``
  2. ChEMBL REST API (target CHEMBL203, pchembl_value >= 5)
  3. Curated EGFR inhibitor set (~55 compounds, always available)

State assignment uses inhibitor-type heuristics. Compounds without
a known type are assigned randomly (seeded) — this is a documented
limitation.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from statebind.baselines.scoring import _REFERENCE_BINDERS
from statebind.data.paths import DataPaths
from statebind.ml.vae_dataset import DEFAULT_STATE_MAPPING
from statebind.processing.ligands import _v1_curated_ligands
from statebind.utils.io import save_json

logger = logging.getLogger(__name__)

# Valid conformational states (must match DEFAULT_STATE_MAPPING keys)
_VALID_STATES = list(DEFAULT_STATE_MAPPING.keys())

try:
    from rdkit import Chem  # type: ignore[import-untyped]

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


# ── Curated EGFR inhibitor dataset (Tier 3 fallback) ────────────────────

# Each entry: (smiles, state, drug_name)
# Sources: DrugBank, ChEMBL public data, published literature.
# State assignments follow inhibitor-type conventions:
#   Type-I (active conformation binders) → DFGin_aCin
#   Type-I½ (inactive αC-helix) → DFGin_aCout
#   Type-II (DFG-out binders) → DFGout_aCin
#   Covalent / 3rd-gen → DFGin_aCin (bind active, covalent to C797)
#   Allosteric / unconventional → DFGout_aCin (formerly DFGout_aCout, removed)
_CURATED_EGFR_INHIBITORS: list[tuple[str, str, str]] = [
    # ── 1st-generation reversible Type-I ──────────────────────────────
    (
        "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
        "DFGin_aCin",
        "erlotinib",
    ),
    (
        "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
        "DFGin_aCin",
        "gefitinib",
    ),
    (
        "CCOc1cc2ncc(C#N)c(Nc3ccc(OCc4ccccn4)c(Cl)c3)c2cc1OCC",
        "DFGin_aCin",
        "icotinib",
    ),
    (
        "COc1cc(OC)c2c(Nc3ccc(Br)cc3F)ncnc2c1",
        "DFGin_aCin",
        "vandetanib_core",
    ),
    # Quinazoline scaffold variants
    (
        "Clc1cccc(Nc2ncnc3cc(OCCCN4CCOCC4)c(OC)cc23)c1",
        "DFGin_aCin",
        "type1_analog_01",
    ),
    (
        "c1ccc(Nc2ncnc3ccccc23)cc1",
        "DFGin_aCin",
        "4_anilinoquinazoline_core",
    ),
    (
        "COc1cc2ncnc(Nc3ccc(F)cc3)c2cc1OC",
        "DFGin_aCin",
        "type1_analog_02",
    ),
    (
        "Fc1ccc(Nc2ncnc3cc(OCCN4CCOCC4)ccc23)cc1Cl",
        "DFGin_aCin",
        "type1_analog_03",
    ),
    (
        "COc1cc2ncnc(Nc3cccc(Br)c3)c2cc1OC",
        "DFGin_aCin",
        "type1_analog_04",
    ),
    (
        "COc1cc2ncnc(Nc3ccc(C)cc3)c2cc1OCCCN1CCOCC1",
        "DFGin_aCin",
        "type1_analog_05",
    ),
    (
        "COc1cc2ncnc(Nc3ccc(OC)c(Cl)c3)c2cc1",
        "DFGin_aCin",
        "type1_analog_06",
    ),
    (
        "Brc1cccc(Nc2ncnc3cc(OCCCN4CCOCC4)c(OC)cc23)c1",
        "DFGin_aCin",
        "type1_analog_07",
    ),
    (
        "c1ccc(Nc2ncnc3cc(OCCO)c(OCCO)cc23)cc1C#C",
        "DFGin_aCin",
        "erlotinib_analog_01",
    ),

    # ── Type-I½ (Src-like inactive, αC-helix out) ────────────────────
    (
        "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1",
        "DFGin_aCout",
        "lapatinib",
    ),
    (
        "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5ccccc5)c(Cl)c4)c3c2)o1",
        "DFGin_aCout",
        "lapatinib_analog_01",
    ),
    (
        "Oc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)cc4)c3c2)cc1",
        "DFGin_aCout",
        "type1h_analog_01",
    ),
    (
        "O=C(Nc1ccc(-c2ccc3ncnc(Nc4ccc(F)c(Cl)c4)c3c2)cc1)c1ccccc1",
        "DFGin_aCout",
        "type1h_analog_02",
    ),
    (
        "COc1cc2ncnc(Nc3ccc(OCc4cccc(F)c4)c(Cl)c3)c2cc1OCCCN1CCOCC1",
        "DFGin_aCout",
        "type1h_analog_03",
    ),
    (
        "Clc1ccc(Nc2ncnc3cc(-c4ccncc4)ccc23)cc1OCc1cccc(F)c1",
        "DFGin_aCout",
        "type1h_analog_04",
    ),
    (
        "COc1cc2ncnc(Nc3ccc(OCc4ccc(F)cc4)c(Cl)c3)c2cc1",
        "DFGin_aCout",
        "type1h_analog_05",
    ),
    (
        "Fc1cccc(COc2ccc(Nc3ncnc4cc(OCCN5CCOCC5)ccc34)cc2Cl)c1",
        "DFGin_aCout",
        "type1h_analog_06",
    ),
    (
        "O=S(=O)(CCNCc1ccco1)c1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)cc1",
        "DFGin_aCout",
        "type1h_analog_07",
    ),
    (
        "COc1ccc(Nc2ncnc3cc(-c4ccc(CNCCCS(C)(=O)=O)o4)ccc23)cc1OCc1cccc(F)c1",
        "DFGin_aCout",
        "tucatinib_like",
    ),

    # ── Type-II (DFG-out binders) ────────────────────────────────────
    (
        "CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)cc2)ccn1",
        "DFGout_aCin",
        "sorafenib_like_01",
    ),
    (
        "Cc1ccc(NC(=O)Nc2ccc(Oc3ccnc(NC(C)=O)c3)cc2)cc1C(F)(F)F",
        "DFGout_aCin",
        "type2_analog_01",
    ),
    (
        "O=C(Nc1ccc(Oc2cc(NC(=O)c3cccnc3)ccc2F)cc1)Nc1ccc(C(F)(F)F)cc1",
        "DFGout_aCin",
        "type2_analog_02",
    ),
    (
        "Fc1ccc(NC(=O)Nc2ccc(-c3ccnc4ccccc34)cc2)cc1C(F)(F)F",
        "DFGin_aCout",
        "type2_analog_03",
    ),
    (
        "CNC(=O)c1ccc(Oc2ccc(NC(=O)Nc3ccc(Cl)cc3)cc2)nc1",
        "DFGout_aCin",
        "type2_analog_04",
    ),
    (
        "O=C(Nc1ccccc1)Nc1ccc(Oc2ccnc(Nc3ccccc3)c2)cc1",
        "DFGout_aCin",
        "type2_analog_05",
    ),
    (
        "CC(=O)Nc1cccc(-c2cc(NC(=O)Nc3ccc(OC(F)(F)F)cc3)ccc2F)c1",
        "DFGout_aCin",
        "type2_analog_06",
    ),
    (
        "CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3cccc(C(F)(F)F)c3)cc2)ccn1",
        "DFGout_aCin",
        "type2_analog_07",
    ),
    (
        "O=C(Nc1ccc(F)cc1)Nc1ccc(Oc2cc(C(=O)NC3CC3)ccn2)cc1",
        "DFGout_aCin",
        "type2_analog_08",
    ),
    (
        "Cc1ccc(NC(=O)Nc2cc(Oc3ccnc(NC(=O)C4CC4)c3)ccc2F)cc1Cl",
        "DFGout_aCin",
        "type2_analog_09",
    ),

    # ── 2nd-gen covalent (irreversible, C797) ────────────────────────
    (
        "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1",
        "DFGin_aCin",
        "afatinib",
    ),
    (
        "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCCC1",
        "DFGin_aCin",
        "dacomitinib",
    ),
    (
        "C=CC(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OCCCN1CCOCC1",
        "DFGin_aCin",
        "covalent_analog_01",
    ),

    # ── 3rd-gen mutant-selective covalent ─────────────────────────────
    (
        "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
        "DFGin_aCin",
        "osimertinib",
    ),
    (
        "C=CC(=O)Nc1cc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c(OC)cc1N(C)CCN(C)C",
        "DFGin_aCin",
        "osimertinib_analog_01",
    ),
    (
        "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2ccccn2)n1",
        "DFGin_aCin",
        "3rdgen_analog_01",
    ),
    (
        "C=CC(=O)Nc1cccc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c1OC",
        "DFGin_aCin",
        "lazertinib_like",
    ),
    (
        "C=CC(=O)Nc1cc(Nc2ncc(-c3cccnc3)c(-c3ccsc3)n2)c(OC)cc1N(C)CCN(C)C",
        "DFGin_aCin",
        "mobocertinib_like",
    ),
    (
        "C=CC(=O)Nc1cc(Nc2ncnc3cc(OC)c(OC)cc23)c(OC)cc1N1CCC(N(C)C)CC1",
        "DFGin_aCin",
        "aumolertinib_like",
    ),

    # ── Allosteric / DFGout_aCin (formerly DFGout_aCout) ─────────────
    (
        "O=C(c1cc(F)cc(F)c1)c1ccc2[nH]c(-c3ccccc3)nc2c1",
        "DFGout_aCin",
        "allosteric_01",
    ),
    (
        "O=C(Nc1cccc(C(F)(F)F)c1)c1cnc2ccccc2n1",
        "DFGout_aCin",
        "allosteric_02",
    ),
    (
        "Cc1noc(NC(=O)c2ccc(F)cc2)c1-c1ccc(Cl)cc1",
        "DFGout_aCin",
        "allosteric_03",
    ),
    (
        "O=C(Nc1ccccc1F)c1cc(-c2ccncc2)no1",
        "DFGout_aCin",
        "allosteric_04",
    ),
    (
        "CC(=O)Nc1ccc(-c2cc(C(F)(F)F)nn2-c2ccccc2)cc1",
        "DFGout_aCin",
        "allosteric_05",
    ),
    (
        "O=C(Nc1ccc(F)cc1F)c1ccc(-c2cccnc2)o1",
        "DFGout_aCin",
        "allosteric_06",
    ),
    (
        "O=C(c1ccc(F)cc1)N1CCN(c2ncnc3ccccc23)CC1",
        "DFGout_aCin",
        "allosteric_07",
    ),
    (
        "Cc1cc(-c2cccc(NC(=O)c3ccc(C#N)cc3)c2)on1",
        "DFGout_aCin",
        "allosteric_08",
    ),
    (
        "O=C(Nc1cccc(-c2noc(C(F)(F)F)n2)c1)c1ccc(Cl)cc1",
        "DFGout_aCin",
        "allosteric_09",
    ),
    (
        "CC(=O)Nc1ccc2oc(-c3ccc(O)cc3)nc2c1",
        "DFGout_aCin",
        "allosteric_10",
    ),
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
    # Only allow valid SMILES characters
    allowed = re.compile(
        r"^[A-Za-z0-9@+\-\[\]()\\/%=#$:.,~*!&^{}\s]+$"
    )
    return bool(allowed.match(smiles))


def _curated_egfr_compounds() -> list[dict[str, str]]:
    """Return curated EGFR inhibitors with state assignments.

    Combines the project's reference binders, curated ligand records,
    and a hard-coded set of ~55 known EGFR-targeting compounds.
    Deduplicates by SMILES.
    """
    seen: set[str] = set()
    records: list[dict[str, str]] = []

    # 1. Hard-coded curated inhibitors (primary source)
    for smiles, state, _name in _CURATED_EGFR_INHIBITORS:
        if smiles and smiles not in seen and _validate_smiles_basic(smiles):
            seen.add(smiles)
            records.append({"smiles": smiles, "state": state})

    # 2. Reference binders from baselines/scoring.py:59-66
    for smiles in _REFERENCE_BINDERS:
        if smiles not in seen and _validate_smiles_basic(smiles):
            seen.add(smiles)
            records.append({"smiles": smiles, "state": "DFGin_aCin"})

    # 3. Curated ligands from processing/ligands.py:19
    state_by_generation: dict[str, str] = {
        "1st": "DFGin_aCin",
        "2nd": "DFGin_aCin",
        "3rd": "DFGin_aCin",
    }
    for lig in _v1_curated_ligands():
        smiles = lig.canonical_smiles
        if not smiles or smiles in seen or not _validate_smiles_basic(smiles):
            continue
        seen.add(smiles)
        state = state_by_generation.get(
            getattr(lig, "generation", ""), "DFGin_aCin"
        )
        records.append({"smiles": smiles, "state": state})

    return records


def _load_chembl_local(raw_dir: Path) -> list[dict[str, str]] | None:
    """Attempt to load ChEMBL EGFR data from local file.

    Expected path: ``data/raw/ligands/chembl_egfr.json``
    Expected format: list of dicts with at least ``smiles`` key and
    optionally ``pchembl_value`` and ``inhibitor_type``.

    Returns None if file not found or unparseable.
    """
    path = raw_dir / "ligands" / "chembl_egfr.json"
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

    records: list[dict[str, str]] = []
    rng = random.Random(42)
    for entry in data:
        smiles = entry.get("smiles", "")
        if not smiles or not _validate_smiles_basic(smiles):
            continue
        # Use inhibitor_type if available, else random
        itype = entry.get("inhibitor_type", "")
        state = _assign_state_from_type(itype, rng)
        records.append({"smiles": smiles, "state": state})

    return records if records else None


def _fetch_chembl_api() -> list[dict[str, str]] | None:
    """Fetch EGFR actives from ChEMBL REST API (stdlib only).

    Queries CHEMBL203 (EGFR) for compounds with pchembl_value >= 5
    (IC50 < 10 μM). Paginates up to 40 pages (20,000 records max).
    Uses urllib (no external dependencies).

    Returns None on any failure (network, timeout, parse error).
    """
    base_url = (
        "https://www.ebi.ac.uk/chembl/api/data/activity.json"
        "?target_chembl_id=CHEMBL203"
        "&pchembl_value__gte=5"
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

    seen: set[str] = set()
    records: list[dict[str, str]] = []
    rng = random.Random(42)

    for act in all_activities:
        smiles = act.get("canonical_smiles", "")
        if not smiles or smiles in seen or not _validate_smiles_basic(smiles):
            continue
        seen.add(smiles)
        state = _assign_state_from_type("", rng)
        records.append({"smiles": smiles, "state": state})

    return records if records else None


def _assign_state_from_type(
    inhibitor_type: str,
    rng: random.Random,
) -> str:
    """Map inhibitor type string to conformational state.

    Falls back to random assignment for unknown types.
    """
    type_map: dict[str, str] = {
        "type_i": "DFGin_aCin",
        "type-i": "DFGin_aCin",
        "type1": "DFGin_aCin",
        "type_i.5": "DFGin_aCout",
        "type-i.5": "DFGin_aCout",
        "type_ii": "DFGout_aCin",
        "type-ii": "DFGout_aCin",
        "type2": "DFGout_aCin",
        "type_iii": "DFGout_aCin",
        "type-iii": "DFGout_aCin",
        "allosteric": "DFGout_aCin",
    }
    key = inhibitor_type.strip().lower()
    if key in type_map:
        return type_map[key]
    # Unknown type → random assignment (documented limitation)
    return rng.choice(_VALID_STATES)


def _split_train_val(
    records: list[dict[str, str]],
    train_ratio: float = 0.8,
    seed: int = 42,
    reference_smiles: set[str] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Split records into train and validation sets.

    Reference binders are forced into the training set. The remaining
    records are shuffled (seeded) and split by ``train_ratio``.
    No SMILES overlap between splits.
    """
    if reference_smiles is None:
        reference_smiles = set(_REFERENCE_BINDERS)

    # Separate reference binders (always train)
    ref_records: list[dict[str, str]] = []
    other_records: list[dict[str, str]] = []
    for rec in records:
        if rec["smiles"] in reference_smiles:
            ref_records.append(rec)
        else:
            other_records.append(rec)

    rng = random.Random(seed)
    rng.shuffle(other_records)

    n_train = int(len(other_records) * train_ratio)
    train = ref_records + other_records[:n_train]
    val = other_records[n_train:]

    # Verify no overlap
    train_smiles = {r["smiles"] for r in train}
    val_smiles = {r["smiles"] for r in val}
    overlap = train_smiles & val_smiles
    if overlap:
        logger.warning("Found %d overlapping SMILES between splits", len(overlap))
        # Remove overlaps from val
        val = [r for r in val if r["smiles"] not in overlap]

    return train, val


def _print_summary(
    train: list[dict[str, str]],
    val: list[dict[str, str]],
    source: str,
) -> None:
    """Print summary statistics for the prepared dataset."""
    print("\n" + "=" * 60)
    print("VAE Training Data Summary")
    print("=" * 60)
    print(f"Data source: {source}")
    print(f"Total records: {len(train) + len(val)}")
    print(f"  Train: {len(train)}")
    print(f"  Val:   {len(val)}")

    for split_name, split_data in [("Train", train), ("Val", val)]:
        state_counts: dict[str, int] = {}
        lengths: list[int] = []
        for rec in split_data:
            state_counts[rec["state"]] = state_counts.get(rec["state"], 0) + 1
            lengths.append(len(rec["smiles"]))

        print(f"\n  {split_name} state distribution:")
        for state in sorted(state_counts):
            print(f"    {state}: {state_counts[state]}")

        if lengths:
            print(f"  {split_name} SMILES length: "
                  f"min={min(lengths)}, "
                  f"mean={sum(lengths) / len(lengths):.1f}, "
                  f"max={max(lengths)}")

    print("=" * 60 + "\n")


def prepare_vae_training_data(
    seed: int = 42,
    output_dir: Path | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Prepare VAE training and validation data.

    Uses 3-tier fallback: local ChEMBL file → ChEMBL API → curated set.

    Parameters
    ----------
    seed:
        Random seed for splitting and state assignment.
    output_dir:
        Directory to write JSON files. Defaults to ``data/processed/``.

    Returns
    -------
    tuple[list, list]:
        (train_records, val_records) where each record is
        ``{"smiles": str, "state": str}``.
    """
    paths = DataPaths()

    if output_dir is None:
        output_dir = paths.processed_dir

    # Tier 1: Local ChEMBL file
    source = "curated_fallback"
    records = _load_chembl_local(paths.raw_dir)
    if records:
        source = "chembl_local"
        logger.info("Loaded %d records from local ChEMBL file", len(records))
    else:
        # Tier 2: ChEMBL API
        records = _fetch_chembl_api()
        if records:
            source = "chembl_api"
            logger.info("Fetched %d records from ChEMBL API", len(records))
        else:
            # Tier 3: Curated fallback
            records = _curated_egfr_compounds()
            logger.info(
                "Using curated fallback dataset (%d compounds)", len(records)
            )

    # Validate all state labels
    for rec in records:
        if rec["state"] not in _VALID_STATES:
            rec["state"] = random.Random(seed).choice(_VALID_STATES)

    # Split
    train, val = _split_train_val(records, train_ratio=0.8, seed=seed)

    # Write output
    train_path = output_dir / "egfr_smiles_train.json"
    val_path = output_dir / "egfr_smiles_val.json"
    save_json(train, train_path)
    save_json(val, val_path)

    _print_summary(train, val, source)

    # Write metadata
    metadata = {
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "n_train": len(train),
        "n_val": len(val),
        "train_path": str(train_path),
        "val_path": str(val_path),
        "state_mapping": DEFAULT_STATE_MAPPING,
        "notes": (
            "State assignments use inhibitor-type heuristics. "
            "Compounds without known type are assigned randomly. "
            f"Data source: {source}."
        ),
    }
    save_json(metadata, output_dir / "egfr_smiles_metadata.json")

    return train, val


def main() -> None:
    """CLI entry point for VAE data preparation."""
    parser = argparse.ArgumentParser(
        description="Prepare EGFR SMILES data for VAE training",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/processed/)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    output_dir = Path(args.output_dir) if args.output_dir else None
    prepare_vae_training_data(seed=args.seed, output_dir=output_dir)


if __name__ == "__main__":
    main()
