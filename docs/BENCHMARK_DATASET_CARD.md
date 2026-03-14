# Benchmark Dataset Card: StateBind v1

## Dataset Identity

| Field | Value |
|-------|-------|
| **Name** | StateBind v1 EGFR Benchmark |
| **Version** | 1.0.0 |
| **Target** | EGFR (Human, UniProt P00533) |
| **Domain** | Kinase domain (residues 696–1022) |
| **Purpose** | Test whether conformational state-aware molecular design outperforms static single-structure design |

## Contents

### Context table (`context.json` / `context.csv`)

18 curated EGFR kinase domain mutations with:
- Resistance generation (activating, 1st, 3rd, 4th)
- Mechanism category (gatekeeper, covalent site, hinge, P-loop, etc.)
- Conformational effect annotation (stabilizes DFGin, destabilizes inactive, etc.)
- Preferred conformational states
- Known drug associations (affected and effective)
- PDB structure cross-references
- Literature references (PMIDs)
- Train/val/test split assignments

### Structure table (`structures.json` / `structures.csv`)

18 EGFR kinase domain PDB structures spanning all 4 canonical conformational states:
- DFGin_aCin (active): 7 structures
- DFGin_aCout (Src-like inactive): 5 structures
- DFGout_aCin: 2 structures
- DFGout_aCout (classical inactive): 2 structures
- Apo: 1 structure (DFGin_aCout)
- 1 representative structure per state

Each entry includes: resolution, chain, mutation status, ligand binding status, deposition date.

### Ligand table (`ligands.json` / `ligands.csv`)

9 EGFR ligands:
- 5 approved TKIs (gefitinib, erlotinib, afatinib, dacomitinib, osimertinib)
- 4 co-crystal ligands from the structure dataset

Each entry includes: canonical SMILES, source, pIC50, molecular weight, logP, PDB cross-reference.

### Mapping tables

- `mapping_mutation_structure.csv`: Links mutations to PDB structures containing them
- `mapping_structure_ligand.csv`: Links structures to co-crystallized ligands

## Curation Methodology

All data was manually curated from:
1. Published peer-reviewed literature (PMIDs provided per entry)
2. RCSB PDB (structure metadata and classifications)
3. KLIFS database (conformational state reference annotations)
4. DrugBank and ChEMBL (approved drug data)

No automated scraping or large database downloads were used for v1. This is
deliberate: small and correct is better than large and noisy for a benchmark.

## Splits

| Split | Count | Strategy |
|-------|-------|----------|
| Train | ~10 | Hash-based deterministic assignment |
| Val | ~3 | Hash-based deterministic assignment |
| Test | ~5 | Key mutations (T790M, L858R, C797S) forced to test + hash remainder |

The 3 key mutations (T790M, L858R, C797S) are always in the test split to
ensure the benchmark evaluates on the most clinically relevant cases.

## Known Limitations

1. **Size.** 18 mutations is small. Sufficient for pipeline development and
   proof-of-concept, but not for training data-hungry models.

2. **Selection bias.** Mutations were chosen for clinical relevance and
   structural characterization. Rare mutations are underrepresented.

3. **State assignments are literature-based.** Not yet validated by our own
   geometric classifier. May be revised in Phase 2.

4. **No geometric measurements yet.** DFG distances and αC-helix metrics are
   placeholders (null). Will be computed in Phase 2.

5. **Ligand SMILES not RDKit-validated.** Some co-crystal ligand SMILES are
   approximate. Will be validated with RDKit in Phase 4.

6. **No ADMET or selectivity data.** Beyond v1 scope.

## Provenance

Every record carries a `provenance` object with:
- Source database names
- Processing version (StateBind code version)
- Processing date

## Reproducibility

The benchmark is fully reproducible:

```bash
python scripts/assemble_benchmark.py --split-seed 42
```

The same seed always produces the same dataset with the same splits.

## Usage by Downstream Modules

| Module | Consumes |
|--------|----------|
| Context (Phase 1) | context.json — mutation queries |
| Structure (Phase 2) | structures.json — PDB IDs to download and classify |
| Dynamics (Phase 3) | context.json + structures.json — mutation→state prediction |
| Generation (Phase 4) | structures.json — pocket geometries per state |
| Ranking (Phase 5) | All tables — scoring and comparison |
