# Data Schema

This document defines the schema for raw and processed data in StateBind. Every field is typed. Every record carries provenance. Downstream modules consume processed data exclusively.

---

## Canonical Identifiers

Every entity in StateBind has a single canonical ID format. All modules must use these formats.

| Entity | ID Format | Example | Source |
|--------|-----------|---------|--------|
| **Gene** | HGNC symbol | `EGFR` | HGNC |
| **Protein** | UniProt accession | `P00533` | UniProt |
| **Mutation** | `<WT><position><MUT>` (single-letter AA) | `T790M` | Standard notation |
| **PDB structure** | 4-character PDB ID (lowercase) | `1m17` | RCSB PDB |
| **Conformational state** | `<DFG>_<aC>` enum | `DFGin_aCin` | StateBind convention |
| **Ligand (PDB)** | 3-character PDB ligand code | `AEE` | PDB |
| **Ligand (ChEMBL)** | ChEMBL compound ID | `CHEMBL939` | ChEMBL |
| **Ligand (canonical)** | Canonical SMILES (RDKit) | `c1ccc(-c2nn...)cc1` | RDKit canonicalization |

### Conformational State Enum

```
DFGin_aCin    # Active state
DFGin_aCout   # Src-like inactive
DFGout_aCin   # Intermediate
DFGout_aCout  # Classical inactive
```

### Mutation Compound Notation

For compound mutations: `T790M+C797S` (alphabetically sorted by position, `+` delimited).

---

## Provenance Fields

Every manifest entry and processed record carries:

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | `str` | Identifier within the source database |
| `source_name` | `str` | Database name (e.g., `cosmic`, `pdb`, `chembl`) |
| `source_version` | `str` | Database version or download date (ISO 8601) |
| `source_url` | `str` | URL used for retrieval |
| `download_date` | `str` | ISO 8601 date of download |
| `file_hash` | `str` | SHA-256 hash of the raw downloaded file |
| `processing_version` | `str` | StateBind code version that produced processed output |
| `notes` | `str` | Free-text notes (e.g., "filtered to kinase domain only") |

---

## Raw Data Schemas

Raw data is stored as-downloaded, never modified. One file per source per category.

### Raw Context: Mutation Records

**Location:** `data/raw/context/`

| File | Format | Contents |
|------|--------|----------|
| `cosmic_egfr_mutations.tsv` | TSV | COSMIC export filtered to EGFR |
| `clinvar_egfr_variants.xml` | XML | ClinVar download for EGFR gene |
| `manual_curated_mutations.json` | JSON | Hand-curated mutation annotations |

**manual_curated_mutations.json schema:**

```json
{
  "mutations": [
    {
      "mutation_id": "T790M",
      "gene": "EGFR",
      "uniprot_id": "P00533",
      "position": 790,
      "wild_type": "T",
      "mutant": "M",
      "resistance_generation": "1st",
      "mechanism_category": "gatekeeper",
      "conformational_effect": "stabilizes_DFGin",
      "known_drugs_affected": ["gefitinib", "erlotinib"],
      "known_drugs_effective": ["osimertinib"],
      "references": ["PMID:18408761", "PMID:15737014"],
      "notes": "Bulky methionine blocks 1st-gen TKI access; stabilizes hydrophobic spine"
    }
  ]
}
```

### Raw Structure: PDB Files

**Location:** `data/raw/structures/`

| File pattern | Format | Contents |
|-------------|--------|----------|
| `<pdb_id>.pdb` | PDB | Full PDB coordinate file |
| `pdb_metadata.json` | JSON | Metadata queried from RCSB API |
| `klifs_egfr.csv` | CSV | KLIFS classification export for EGFR |

### Raw Ligands: Compound Data

**Location:** `data/raw/ligands/`

| File | Format | Contents |
|------|--------|----------|
| `chembl_egfr_binders.csv` | CSV | ChEMBL query results (SMILES, IC50, assay) |
| `pdb_cocrystal_ligands.sdf` | SDF | Extracted co-crystal ligands |
| `approved_egfr_tkis.json` | JSON | Approved drugs (manual curation) |

---

## Processed Data Schemas

Processed data is derived from raw data by StateBind scripts. Every processed record is traceable to raw source(s).

### Processed Context: Mutation Atlas

**Location:** `data/processed/context/mutation_atlas.json`

```json
{
  "version": "1.0.0",
  "generated_by": "statebind.data",
  "generated_at": "2026-03-14T00:00:00Z",
  "gene": "EGFR",
  "uniprot_id": "P00533",
  "mutations": [
    {
      "mutation_id": "T790M",
      "position": 790,
      "wild_type": "T",
      "mutant": "M",
      "domain": "kinase",
      "resistance_generation": "1st",
      "mechanism_category": "gatekeeper",
      "conformational_effect": "stabilizes_DFGin",
      "cosmic_frequency": 1247,
      "clinvar_significance": "drug_response",
      "known_drugs_affected": ["gefitinib", "erlotinib"],
      "known_drugs_effective": ["osimertinib"],
      "pdb_structures": ["2jit", "3w2o"],
      "references": ["PMID:18408761"],
      "provenance": {
        "sources": ["cosmic", "clinvar", "manual"],
        "processing_version": "0.1.0",
        "processing_date": "2026-03-14"
      }
    }
  ]
}
```

### Processed Structure: State Atlas

**Location:** `data/processed/structures/state_atlas.json`

```json
{
  "version": "1.0.0",
  "structures": [
    {
      "pdb_id": "1m17",
      "resolution": 2.6,
      "state": "DFGin_aCin",
      "dfg_distance": 8.2,
      "ac_helix_metric": 3.1,
      "mutations_present": [],
      "ligand_id": "AEE",
      "chain": "A",
      "pocket_file": "data/processed/structures/pockets/DFGin_aCin/1m17_pocket.json",
      "is_representative": true,
      "provenance": {
        "source": "pdb",
        "classification_method": "geometric",
        "classification_version": "0.1.0"
      }
    }
  ]
}
```

### Processed Ligands: Reference Compounds

**Location:** `data/processed/ligands/reference_compounds.csv`

| Column | Type | Description |
|--------|------|-------------|
| `compound_id` | str | Canonical ID (ChEMBL or PDB ligand code) |
| `canonical_smiles` | str | RDKit-canonicalized SMILES |
| `source` | str | `chembl`, `pdb_cocrystal`, `approved_drug` |
| `pIC50` | float | -log10(IC50) in molar, if available |
| `assay_type` | str | Binding, functional, cell-based |
| `mw` | float | Molecular weight |
| `logp` | float | Calculated logP |
| `pdb_id` | str | PDB ID if co-crystal ligand, else null |
| `provenance_source` | str | Source database |
| `provenance_date` | str | Download date |

---

## Manifest Format

Every file in `data/raw/` and `data/processed/` must have a corresponding entry in a manifest file under `data/manifests/`.

**Manifest file:** `data/manifests/<category>.json`

```json
{
  "manifest_version": "1.0.0",
  "category": "context",
  "entries": [
    {
      "file_path": "data/raw/context/cosmic_egfr_mutations.tsv",
      "description": "COSMIC somatic mutations for EGFR, filtered to kinase domain",
      "source_name": "cosmic",
      "source_version": "v99",
      "source_url": "https://cancer.sanger.ac.uk/cosmic/download",
      "download_date": "2026-03-14",
      "file_hash": "sha256:abc123...",
      "file_size_bytes": 102400,
      "format": "tsv",
      "status": "pending",
      "notes": ""
    }
  ]
}
```

**Status values:** `pending` (registered but not yet downloaded), `downloaded` (raw file present), `validated` (hash verified), `processed` (processed derivative exists).

---

## Metadata Required by Downstream Modules

Each downstream module has specific metadata requirements:

| Module | Required from data layer |
|--------|------------------------|
| **Context** | mutation_id, position, wild_type, mutant, resistance_generation, mechanism_category, conformational_effect |
| **Structure** | pdb_id, resolution, chain, state label, DFG/αC metrics, pocket geometry, co-crystal ligand |
| **Dynamics** | mutation_id → state associations (from context + structure), state frequencies |
| **Generation** | pocket geometry (coordinates, pharmacophore features), reference SMILES |
| **Ranking** | candidate SMILES, pocket coordinates per state, reference compound scores |
