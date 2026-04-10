---
phase: "Phase 1: Core Experiments"
task_id: P1-T05
task_name: "ABL1 Schema + Data Curation Script"
implementation_plan_ref: "P12: Multi-Kinase Extension -- ABL1 (steps 1-2)"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "2-3 days"
---

# Task: ABL1 Schema + Data Curation Script

## Objective

Add a `target_gene` field to `StructureRecord` for multi-kinase support, and
create data curation scripts for ABL1 bioactivity data from ChEMBL and ABL1
structures from PDB. This is the first step toward demonstrating that state-aware
molecular design generalizes beyond EGFR.

## Context

ABL1 is the ideal second kinase because: (1) it has genuine DFGout structures
(imatinib-bound, PDB 1IEP), unlike EGFR which only has DFGin structures; (2) it
has a rich drug timeline (imatinib 2001 through asciminib 2021) for retrospective
validation; (3) it's the canonical kinase for conformational switching studies.

The implementation plan (P12) estimates 8-10 weeks total for ABL1. This task
covers steps 1-2 (schema + data curation), which are ~5 days and can run in
parallel with other Phase 1 work.

## Prerequisites

- [x] Phase 0 complete
- [x] Internet access for ChEMBL and PDB queries

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/processing/models.py:125-179` | StructureRecord (no target_gene), StructureDataset (has target_gene), LigandRecord (has target_gene) |
| `src/statebind/processing/structures.py` | EGFR-specific structure curation -- template for ABL1 |
| `scripts/build_structure_dataset.py` | How structure datasets are built |
| `scripts/build_ligand_dataset.py` | How ligand datasets are built |
| `scripts/prepare_mpnn_data.py` | How MPNN training data is prepared from ChEMBL |
| `scripts/prepare_vae_data.py` | How VAE training data is prepared |
| `data/processed/egfr_affinity.json` | EGFR affinity data format -- ABL1 should match |
| `data/processed/egfr_smiles_train.json` | EGFR SMILES data format -- ABL1 should match |
| `tests/test_processing.py` | Existing processing tests |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `src/statebind/processing/models.py` | 125-149 | Add `target_gene: str = Field(default="EGFR")` to StructureRecord |
| NEW: `scripts/curate_abl1_data.py` | -- | ChEMBL ABL1 bioactivity curation script |
| NEW: `scripts/curate_abl1_structures.py` | -- | PDB ABL1 structure curation script |
| `tests/test_processing.py` | append | Add test for StructureRecord.target_gene field |

## Implementation Steps

1. **Add `target_gene` to `StructureRecord`** at `processing/models.py:125-149`:

   Add after line 148 (before `provenance`):
   ```python
   target_gene: str = Field(default="EGFR", description="Target gene symbol")
   ```
   This is backward-compatible: existing StructureRecords default to "EGFR".
   The docstring on line 126 should be updated from "A single EGFR structure
   entry" to "A single kinase structure entry".

2. **Create `scripts/curate_abl1_data.py`**:

   Script to query ChEMBL for ABL1 bioactivity data:
   ```python
   # Query ChEMBL REST API for target CHEMBL1862 (ABL1)
   # Filters:
   #   - assay_type: "B" (binding) or "F" (functional)
   #   - standard_type: "IC50"
   #   - standard_relation: "="  (exact measurements only)
   #   - target_organism: "Homo sapiens"
   #   - pchembl_value not null
   # Output format matches EGFR: list of {smiles, pIC50, assay_type, chembl_id, year}
   # Include state assignment based on co-crystal structure if available
   ```

   Key requirements:
   - Use `requests` to query ChEMBL REST API (no chembl_webresource_client)
   - Filter for quality: exact IC50, single protein, human target
   - Convert IC50 to pIC50 (-log10(IC50_in_M))
   - Report statistics: total compounds, assay distribution, year range
   - Output to `data/processed/abl1_affinity.json`
   - Data quality checkpoint: print warnings if < 100 compounds pass filters

3. **Create `scripts/curate_abl1_structures.py`**:

   Script to curate ABL1 PDB structures:
   ```python
   # Key ABL1 structures (from literature):
   # DFGout (Type-II):
   #   1IEP - imatinib-bound (the canonical DFGout structure)
   #   3PYY - nilotinib-bound
   #   3CS9 - ponatinib precursor
   # DFGin (Type-I):
   #   2GQG - dasatinib-bound
   #   3QRI - bosutinib-bound
   # aC-out:
   #   Check KLIFS for aC classification

   # For each PDB ID:
   # 1. Download PDB header from RCSB REST API
   # 2. Extract: resolution, organism, mutations, ligand_id, deposition_date
   # 3. Cross-reference with KLIFS for DFG/aC classification
   # 4. Create StructureRecord with target_gene="ABL1"
   # 5. Output to data/processed/structures/abl1_structures.json
   ```

   **CRITICAL**: Verify every annotation against the actual PDB record. The EGFR
   Phase 0 experience showed that metadata errors are common. For each structure:
   - Check organism (must be Homo sapiens)
   - Check mutations (many ABL1 structures have T315I gatekeeper mutation)
   - Check DFG conformation from KLIFS or by inspection
   - Document any discrepancies

4. **Update tests**:

   Add to `tests/test_processing.py`:
   ```python
   def test_structure_record_target_gene_default():
       """StructureRecord defaults to EGFR for backward compat."""
       record = StructureRecord(pdb_id="1m17")
       assert record.target_gene == "EGFR"

   def test_structure_record_target_gene_abl1():
       """StructureRecord accepts non-EGFR target_gene."""
       record = StructureRecord(pdb_id="1iep", target_gene="ABL1")
       assert record.target_gene == "ABL1"
   ```

## Verification

- [ ] `StructureRecord(pdb_id="test").target_gene == "EGFR"` (backward compat)
- [ ] `StructureRecord(pdb_id="1iep", target_gene="ABL1").target_gene == "ABL1"`
- [ ] Existing StructureRecord serialization/deserialization still works
- [ ] `curate_abl1_data.py` produces `data/processed/abl1_affinity.json` with >= 100 compounds
- [ ] `curate_abl1_structures.py` produces verified ABL1 structure records
- [ ] `pytest tests/test_processing.py -v` -- all tests pass
- [ ] `pytest -v --tb=short` -- 669+ tests pass, no regressions
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- The StructureRecord change is small and backward-compatible. Existing tests
  should not break because the field has a default.
- ChEMBL REST API: `https://www.ebi.ac.uk/chembl/api/data/` -- use JSON format
- PDB REST API: `https://data.rcsb.org/rest/v1/core/entry/{pdb_id}`
- KLIFS API: `https://klifs.net/api/` -- for DFG/aC classification
- Do NOT modify `_v1_curated_structures()` in structures.py -- that stays EGFR-only.
  ABL1 gets its own curation function in the new script.
- Output data format must match EGFR for downstream pipeline compatibility
- Log all filtering decisions (how many compounds excluded and why)

## Notes and Gotchas

- **ChEMBL API pagination**: Results are paginated (default 20 per page). Use
  `limit` and `offset` parameters, or set `limit=-1` for all results.
- **ABL1 assay heterogeneity**: Unlike EGFR, ABL1 ChEMBL data comes from many
  different constructs and assay conditions. Filter strictly for quality.
- **T315I gatekeeper mutation**: Many ABL1 structures carry T315I. Document this
  clearly -- it's the resistance mutation analogous to EGFR T790M.
- **ABL1 has genuine DFGout structures**: This is a key advantage over EGFR. The
  DFGout classification should be more straightforward to verify.
- **Data quality checkpoint at ~day 3** (mentioned in implementation plan): if
  fewer than 100 compounds pass filters, consider BRAF or SRC as alternatives.
