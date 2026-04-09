---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T01
task_name: "Verify 4ZAU DFG Conformation"
implementation_plan_ref: "P0: Verify 4ZAU DFG Conformation"
status: pending
created: 2026-04-09T18:00:00Z
estimated_effort: "2 hours"
---

# Task: Verify 4ZAU DFG Conformation

## Objective

Programmatically determine whether PDB 4ZAU's DFG motif is in the "in" or "out"
conformation by measuring three key atomic distances. This determines whether the
project uses a 3-state or 4-state conformational model for the rest of the pipeline.

## Context

The implementation plan identified that 4ZAU is classified as `DFGout_aCout` in
`processing/structures.py:206`, but the bound ligand (osimertinib) is a Type I
covalent inhibitor, which strongly suggests DFGin. If 4ZAU is actually DFGin,
there are no genuine EGFR DFGout structures in the atlas, and the project must
switch from 4 states to 3 states.

This is the first task in the entire project plan. No other structural work can
proceed until this is resolved. The result feeds directly into Gate G0.

## Prerequisites

- [ ] No prerequisites (this is the first task)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/processing/structures.py:200-226` | Current 4ZAU and 5D41 StructureRecord definitions |
| `src/statebind/structure/features.py:241-269` | Current DFGout_aCout curated features (for comparison) |
| `CLAUDE.md` | Project conventions |
| `configs/docking.yaml` | Current docking receptor references |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `scripts/verify_4zau_dfg.py` | NEW | Create verification script |
| `artifacts/verification/4zau_dfg_verification.json` | NEW | Output artifact with measurements |

## Implementation Steps

1. **Create output directory:**
   ```bash
   mkdir -p artifacts/verification
   ```

2. **Write verification script** at `scripts/verify_4zau_dfg.py`:

   The script must:
   a. Download PDB 4ZAU from RCSB (use `urllib.request` or `Bio.PDB.PDBList`).
      Since this is an HPC cluster without GUI tools, everything must be
      programmatic.
   b. Parse the structure using BioPython's `PDBParser` (BioPython is available
      in the `[structure]` optional deps).
   c. Identify chain A residues (the EGFR kinase domain).
   d. Measure these three distances:
      - **DFG Asp-Phe Ca-Ca distance:** Find Asp831 and Phe832 (EGFR numbering).
        Measure Calpha-to-Calpha distance.
        - DFGin: ~5-6 Angstroms
        - DFGout: ~9-12 Angstroms
      - **Phe832 position relative to ATP site:** Measure distance from Phe832
        Calpha to ATP-site reference (e.g., Lys745 Calpha or the ligand center
        of mass).
        - DFGin: Phe under P-loop (close to ATP site)
        - DFGout: Phe flipped into allosteric pocket (far from ATP site)
      - **K745-E762 salt bridge (NZ-OE distance):** Find Lys745 NZ atom and
        Glu762 OE1/OE2 atoms. Measure minimum distance.
        - aCin (aC-helix in): < 4 Angstroms
        - aCout (aC-helix out): > 6 Angstroms
   e. Determine classification based on measurements.
   f. Write results to `artifacts/verification/4zau_dfg_verification.json`.

3. **Output artifact format** (`artifacts/verification/4zau_dfg_verification.json`):
   ```json
   {
     "pdb_id": "4ZAU",
     "chain": "A",
     "generated_at": "<UTC ISO timestamp>",
     "measurements": {
       "dfg_asp831_phe832_ca_ca_distance_angstrom": <float>,
       "phe832_to_lys745_ca_distance_angstrom": <float>,
       "lys745_nz_to_glu762_oe_min_distance_angstrom": <float>
     },
     "classification": {
       "dfg_state": "<DFGin or DFGout>",
       "ac_helix_state": "<aCin or aCout>",
       "combined_state": "<DFGin_aCin, DFGin_aCout, DFGout_aCin, or DFGout_aCout>",
       "confidence": "<high, medium, or low based on how clearly distances match thresholds>"
     },
     "interpretation": "<1-2 sentence summary of the finding>",
     "implications": {
       "current_classification": "DFGout_aCout",
       "correct_classification": "<the determined classification>",
       "model_change_needed": "<3-state or 4-state or none>"
     },
     "notes": "Automated measurement from PDB coordinates. Verify against published structures."
   }
   ```

4. **Run the script:**
   ```bash
   module load Python/3.12.3
   source envs/<appropriate-env>/bin/activate
   python scripts/verify_4zau_dfg.py
   ```
   If BioPython is not installed in any available env, install it:
   ```bash
   pip install biopython
   ```

5. **Cross-validate** by also checking PDB 5D41 (the other DFGout_aCout structure)
   with the same measurements. Add its results to the artifact.

## Verification

- [ ] Script runs without errors
- [ ] Output artifact exists at `artifacts/verification/4zau_dfg_verification.json`
- [ ] Measurements are physically reasonable (distances in Angstrom range, not NaN or 0)
- [ ] Classification is clearly stated (DFGin or DFGout)
- [ ] 5D41 measurements are also included
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion

## Agent Instructions

- This is a **standalone verification task** -- it produces a script and an artifact.
  It does NOT modify the structural atlas or any source files.
- Use `from __future__ import annotations` in the script.
- Use `datetime.now(timezone.utc).isoformat()` for the `generated_at` field.
- The script should be self-contained and re-runnable.
- If BioPython is not available, try `gemmi` as an alternative PDB parser.
- If the PDB file cannot be downloaded (network issues on compute node), check
  if there's a local copy in `data/raw/` or download it on the login node first.
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status.

## Notes and Gotchas

- **EGFR numbering:** PDB 4ZAU uses EGFR numbering directly (Asp831, Phe832,
  Lys745, Glu762). Verify by checking the SEQRES or looking at the residue names.
  Some EGFR structures use different numbering schemes.
- **Multiple chains:** 4ZAU may have multiple chains. Use chain A only (consistent
  with `structures.py:205`).
- **Ligand presence:** 4ZAU has osimertinib (ligand ID 4ZA) covalently bound to
  Cys797. This does not affect distance measurements but confirms it's a Type I
  covalent structure.
- **Expected result:** DFGin is strongly expected because osimertinib is a Type I
  covalent inhibitor that binds in the active (DFGin) conformation. If DFGout is
  measured, double-check the atom selection and numbering.
- **The curated features in `features.py:242-269`** show DFG distances of 10.8-11.0 A
  for the DFGout_aCout entries. If the actual PDB measurement shows ~5-6 A, this
  confirms the features were literature-derived archetypes, not measured from these
  specific PDB files.
