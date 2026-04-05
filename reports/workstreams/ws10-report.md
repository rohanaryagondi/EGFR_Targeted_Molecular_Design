# WS10: Training Data Scarcity Fix -- Progress Report

## Status

- **State:** Complete
- **Last updated:** 2026-04-05T20:03:00+00:00
- **Session count:** 1
- **Test count added:** 0
- **Files created:** 1 (this report)
- **Files modified:** 2 scripts + 6 data/metadata files regenerated

## Objective

Fix critically small training datasets for all 3 ML models (VAE, MPNN, ADMET)
that would have prevented meaningful model training. The root causes were:
a missing PyTDC dependency (ADMET), missing API pagination (VAE), and
under-pagination (MPNN).

---

## Progress Log

### Session 1 -- 2026-04-05

#### Completed

1. **Diagnosed all three data preparation scripts** end-to-end:
   - `scripts/prepare_admet_data.py`: PyTDC not installed → Tier 1 failed → fell to Tier 3 curated (55 molecules)
   - `scripts/prepare_vae_data.py`: ChEMBL API fetch at line 449 had `limit=500` with **no pagination** → only got first 500 of 19,361 available activities → 276 train / 69 val after dedup
   - `scripts/prepare_mpnn_data.py`: Paginated but only 5 pages (2,500 records max) of 18,650 available → 1,678 after dedup

2. **Installed PyTDC** (`pip install PyTDC --no-deps` + missing deps `fuzzywuzzy`, `huggingface_hub`) into `/home/rag88/projects/statebind/envs/statebind/`

3. **Fixed VAE pagination** (`scripts/prepare_vae_data.py:441-500`):
   - Replaced single-page fetch with pagination loop (up to 40 pages × 500 = 20,000 records)
   - Modeled on the existing MPNN script's pagination pattern
   - Checks `page_meta.next` to stop when no more pages

4. **Expanded MPNN pagination** (`scripts/prepare_mpnn_data.py:388`):
   - Changed `range(5)` → `range(40)` to capture all ~18,650 IC50 records

5. **Added `--skip-graph-validation` flag** to ADMET script (`scripts/prepare_admet_data.py`):
   - Graph validation (PyG conversion of each SMILES) caused OOM on login node for 27K molecules
   - Added `skip_graph_validation` parameter to `prepare_admet_data()` and CLI flag
   - Graph filtering will happen during training instead

6. **Re-ran all three scripts** and verified output:

   | Model | Before | After | Source | Improvement |
   |-------|--------|-------|--------|-------------|
   | ADMET | 55 molecules | 27,698 molecules | TDC API (6 endpoints) | 503× |
   | VAE | 276 train / 69 val | 8,109 train / 2,027 val | ChEMBL API (paginated) | 29× |
   | MPNN | 1,678 compounds | 10,466 compounds | ChEMBL API (paginated) | 6.2× |

7. **Validated all outputs**:
   - Zero duplicate SMILES in all datasets
   - Zero train/val overlap in VAE data
   - All 4 conformational states present in VAE data
   - Correct JSON schema in all files
   - Metadata files updated with correct counts and source info

8. **Ran tests**: 76 passed, 6 skipped (model quality tests that need trained models)

#### Decisions Made

- **Kept pchembl >= 5 filter for VAE**: Scientifically sound (IC50 < 10μM is a standard activity threshold for EGFR). Relaxing to >= 4 would only add ~1,200 more activities (marginal gain for weaker compounds).
- **Kept all assay types for VAE (not just IC50)**: VAE needs SMILES diversity for generation, not affinity values. Including Ki, Kd, and EC50 assays broadens the chemical space.
- **Kept pchembl >= 3 for MPNN**: MPNN needs the full affinity range including weak/inactive compounds for discrimination. pchembl >= 3 covers IC50 < 1mM.
- **Skipped graph validation for ADMET data prep**: Pragmatic decision. Login nodes have limited memory. Graph conversion filtering happens during training when GPU nodes have ample memory. Added CLI flag rather than removing the feature.
- **Did not relax MPNN to include Ki data**: The existing IC50-only filter with expanded pagination gave 10,466 compounds (6× increase), which is sufficient. Adding Ki would mix assay types and complicate pIC50 interpretation.

#### Issues Encountered

- **PyTDC install failed initially**: `pip install PyTDC` triggered scikit-learn metadata rebuild which caused OOM. Fixed with `--no-deps` since scikit-learn was already installed. Required manual install of `fuzzywuzzy` and `huggingface_hub`.
- **ADMET OOM on graph validation**: 27,698 molecules × PyG graph conversion exhausted login node memory. Added `--skip-graph-validation` flag.
- **VAE + MPNN scripts killed when run concurrently**: Three background scripts exceeded memory together. Fixed by running sequentially.

---

## Current State

**Complete.** All three datasets have been expanded to training-viable sizes:

- ADMET: 27,698 molecules across 6 endpoints (from TDC API)
- VAE: 8,109 train / 2,027 val SMILES (from ChEMBL API, paginated)
- MPNN: 10,466 compounds with pIC50 values (from ChEMBL API, paginated)

All outputs validated. Tests passing.

## Next Steps

1. **Train models on GPU** (separate SLURM jobs — NOT part of this workstream):
   - `sbatch slurm/train_vae.slurm`
   - `sbatch slurm/train_mpnn.slurm`
   - `sbatch slurm/train_admet.slurm`

2. **Optional: Save TDC data as cache** for reproducibility:
   - Could save TDC downloads to `data/raw/admet_tdc_cache.json` so Tier 2 works without PyTDC

3. **Optional: Save ChEMBL data locally** for reproducibility:
   - Could save API results to `data/raw/ligands/chembl_egfr.json` and `chembl_egfr_affinity.json`

---

## Files Created
- `reports/workstreams/ws10-report.md` — this report

## Files Modified
- `scripts/prepare_vae_data.py` — added pagination to `_fetch_chembl_api()` (lines 441-500)
- `scripts/prepare_mpnn_data.py` — expanded pagination from 5 to 40 pages (line 388)
- `scripts/prepare_admet_data.py` — added `skip_graph_validation` parameter and CLI flag

## Data Files Regenerated
- `data/processed/admet_combined.json` — 27,698 molecules (was 55)
- `data/processed/admet_metadata.json` — source: tdc_api
- `data/processed/egfr_smiles_train.json` — 8,109 records (was 276)
- `data/processed/egfr_smiles_val.json` — 2,027 records (was 69)
- `data/processed/egfr_smiles_metadata.json` — source: chembl_api, updated counts
- `data/processed/egfr_affinity.json` — 10,466 compounds (was 1,678)
- `data/processed/egfr_affinity_metadata.json` — source: chembl_api, updated counts

---

## Handoff Notes

- PyTDC has version conflicts with current numpy (2.4.4 vs required <2.0), pandas (3.0.2 vs <3.0), and rdkit (2026.3.1 vs <2024.3.1). It works despite these warnings because TDC only uses these libraries for data loading, not computation. Monitor for breakage on TDC updates.
- The TDC downloads are cached in `~/.tdc/` by default. Future runs will use cached data without re-downloading.
- ChEMBL API pagination can be slow (~10 seconds per page × 40 pages = ~7 minutes). The VAE script took ~3 minutes, MPNN ~2 minutes.
- Graph validation for ADMET should be done during training (GPU node has more memory). The `--skip-graph-validation` flag is the recommended approach for data prep on login nodes.
