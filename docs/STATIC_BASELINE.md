# Static Baseline

## What It Is

The static baseline is a conventional structure-based design pipeline applied to EGFR.
It takes **one** crystal structure, defines **one** binding pocket, generates candidate
molecules, filters them by drug-like properties, and ranks them using simple scoring.

It is the simplest honest approach to the problem — and it is the approach that
state-aware design must outperform to justify its added complexity.

## Why It Is Necessary

Without a baseline, there is no way to claim that state-aware design is better.
"Better" requires "better than X." The static baseline is X.

The static baseline represents what a computational chemist would get by:
1. Going to the PDB
2. Picking the best-looking EGFR co-crystal structure
3. Defining the binding pocket
4. Running a virtual screen
5. Filtering and ranking hits

This is standard practice in many drug discovery programs. If state-aware
design can't beat this, it isn't worth the extra complexity.

## Pipeline

```
Select Structure (1M17, WT EGFR, active)
        │
        ▼
Define Pocket (literature-derived ATP-binding site)
        │
        ▼
Build Candidate Library (reference compounds + simple analogs)
        │
        ▼
Apply Property Filters (Lipinski-like MW, HBA, HBD, rings)
        │
        ▼
Score Candidates (similarity + drug-likeness + docking proxy)
        │
        ▼
Rank and Evaluate (composite score, diversity, validity)
```

## Structure Choice

**PDB 1M17**: Wild-type human EGFR kinase domain co-crystallized with erlotinib.
- Resolution: 2.6 Å
- Conformation: DFGin, αC-helix-in (active state)
- This is a common starting point for EGFR structure-based design

## Assumptions

1. **Single conformation is sufficient.** The baseline assumes that one crystal
   structure adequately represents the target. (This is what we challenge.)

2. **Active state is the right state.** The baseline uses the active conformation.
   Resistance mutations may shift the equilibrium to inactive states. (This is
   what we challenge.)

3. **Literature pocket definition is adequate.** The pocket residues are known.
   But the actual pocket shape changes with conformation. (This is what we challenge.)

4. **Known binder similarity is predictive.** Scoring by similarity to known drugs
   is a reasonable heuristic for a baseline.

## Deliberate Limitations

These limitations are **by design** — they define the gap that state-aware design fills:

| Limitation | What State-Aware Design Adds |
|------------|------------------------------|
| One structure | Multiple conformational states from the atlas |
| One pocket | State-specific pocket geometries |
| No mutation context | Mutation → state prediction |
| Static scoring | State-ensemble scoring |
| No conformational dynamics | State probability weighting |

## Scoring Components

| Component | Weight | Method | Status |
|-----------|--------|--------|--------|
| Reference similarity | 0.4 | SMILES 3-gram Tanimoto to known binders | Implemented (heuristic) |
| Drug-likeness | 0.3 | Property-based linear scoring | Implemented (heuristic) |
| Docking proxy | 0.3 | 3-tier cascade: MPNN → DockingProxy MLP → stub | **Active** (MPNN RMSE=0.72) |

## What Replacing the Stubs Would Change

- **MPNN proxy → Vina/GNINA**: The MPNN cascade now provides real discriminative signal
  (RMSE=0.72 pIC50), but physics-based docking would add pose-level information and
  interaction-specific discrimination beyond what the learned proxy captures.

- **SMILES similarity → Morgan fingerprints**: Would improve structural comparison
  accuracy. Moderate impact on ranking quality.

- **Property estimates → RDKit**: Would improve filtering precision. Minor impact
  on overall pipeline quality.

## How to Run

```bash
python scripts/run_static_baseline.py
```

## Artifacts

```
artifacts/baselines/static_v1/
├── structure_selection.json   # Why 1M17 was chosen
├── pocket_definition.json     # ATP-binding site residues
├── candidate_library.json     # All candidates (reference + analogs)
├── filtered_library.json      # Filter pass/fail per candidate
├── ranked_candidates.json     # Final ranked list
├── evaluation.json            # Quality metrics
└── ranking_table.csv          # Human-readable ranking
```
