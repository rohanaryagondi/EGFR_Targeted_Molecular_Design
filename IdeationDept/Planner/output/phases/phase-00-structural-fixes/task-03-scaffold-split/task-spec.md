---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T03
task_name: "MPNN Scaffold + Temporal Split (Code)"
implementation_plan_ref: "P3: MPNN Scaffold + Temporal Split"
status: completed
created: 2026-04-09T18:00:00Z
estimated_effort: "2-3 days"
---

# Task: MPNN Scaffold + Temporal Split (Code)

## Objective

Replace the MPNN's random permutation data split with scaffold-based and temporal
splitting functions. The current random split at `affinity_dataset.py:388-390`
inflates R^2 by allowing molecules with the same scaffold to appear in both
training and test sets. This is a well-known evaluation pitfall in molecular ML.

## Context

The implementation plan flags random-split MPNN evaluation as one of six
publication-blocking issues. Current R^2 = 0.69 (random split). Expected
degradation to 0.45-0.55 with scaffold split. Gate G1 requires scaffold
R^2 >= 0.35 for MPNN to remain a credible scoring component.

This task implements the code changes only. The actual GPU training and R^2
evaluation is a separate task (P0-T05) to keep code and compute separate.

## Prerequisites

- [ ] No prerequisites (independent of structural fixes)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/ml/affinity_dataset.py:300-416` | Full `AffinityDataset`, `AffinityDatasetConfig`, and `split_dataset()` |
| `src/statebind/ml/mpnn.py` | MPNN model (to understand what split feeds into) |
| `configs/mpnn.yaml` | Current MPNN config (to add split_type field) |
| `tests/test_mpnn_integration.py` | Existing MPNN tests |
| `src/statebind/chemistry/fingerprints.py` | RDKit fingerprint imports (for MurckoScaffold availability) |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `src/statebind/ml/affinity_dataset.py` | 345-416 | Add `split_type` param to `split_dataset()`, add `scaffold_split()` and `temporal_split()` functions |
| `configs/mpnn.yaml` | near end | Add `split_type: random` field (backward compat default) |
| `tests/test_mpnn_integration.py` | append | Add tests for scaffold_split, temporal_split, and split_type parameter |

## Implementation Steps

1. **Add `split_type` parameter to `split_dataset()`** at line 345:

   Modify the function signature to accept `split_type: str = "random"`:
   ```python
   def split_dataset(
       dataset: AffinityDataset,
       config: AffinityDatasetConfig | None = None,
       train_ratio: float = 0.8,
       val_ratio: float = 0.1,
       test_ratio: float = 0.1,
       seed: int = 42,
       split_type: str = "random",
   ) -> tuple[AffinityDataset, AffinityDataset, AffinityDataset]:
   ```

   If `config` is provided and has a `split_type` attribute, use it.
   Dispatch to the appropriate split function based on `split_type`:
   - `"random"`: existing random permutation logic (lines 388-416)
   - `"scaffold"`: call new `scaffold_split()` function
   - `"temporal"`: call new `temporal_split()` function

2. **Implement `scaffold_split()`**:

   ```python
   def scaffold_split(
       dataset: AffinityDataset,
       train_ratio: float = 0.8,
       val_ratio: float = 0.1,
       test_ratio: float = 0.1,
       seed: int = 42,
   ) -> tuple[AffinityDataset, AffinityDataset, AffinityDataset]:
   ```

   Implementation:
   a. Import RDKit scaffold utilities (optional dep with fallback):
      ```python
      try:
          from rdkit import Chem
          from rdkit.Chem.Scaffolds.MurckoScaffold import MakeScaffoldGeneric, GetScaffoldForMol
          HAS_SCAFFOLD = True
      except ImportError:
          HAS_SCAFFOLD = False
      ```
   b. For each molecule in `dataset.smiles_list`, compute generic Murcko scaffold:
      - `mol = Chem.MolFromSmiles(smiles)`
      - `scaffold = MakeScaffoldGeneric(GetScaffoldForMol(mol))`
      - `scaffold_smiles = Chem.MolToSmiles(scaffold)`
   c. Group molecule indices by scaffold SMILES.
   d. Shuffle scaffolds (not molecules) using `np.random.RandomState(seed)`.
   e. Assign entire scaffolds to train/val/test, maintaining approximate ratios.
      Walk through shuffled scaffolds, assigning each scaffold's molecules to the
      smallest-relative-to-target split.
   f. Return the three subsets using the existing `_subset()` pattern.
   g. If RDKit is not available, raise `ImportError("scaffold_split requires RDKit")`.

3. **Implement `temporal_split()`**:

   ```python
   def temporal_split(
       dataset: AffinityDataset,
       train_ratio: float = 0.8,
       val_ratio: float = 0.1,
       test_ratio: float = 0.1,
       year_column: str = "year",
   ) -> tuple[AffinityDataset, AffinityDataset, AffinityDataset]:
   ```

   Implementation:
   a. This requires activity year information. Check if `AffinityDataset` has a
      `metadata` or `years` attribute. If not, add an optional `years: list[int] | None`
      field to `AffinityDataset` (with default `None` for backward compat).
   b. Sort molecules by year. Split so that the earliest ~80% are train, next ~10%
      are val, and the latest ~10% are test.
   c. If years are not available, raise `ValueError("temporal_split requires year data")`.

4. **Update `AffinityDatasetConfig`** (around line 300 in the same file):

   Add `split_type: str = "random"` field if it doesn't exist. This allows config
   files to control the split type.

5. **Update `configs/mpnn.yaml`**:

   Add `split_type: random` to maintain backward compatibility. The scaffold split
   will be used via a new config or command-line override.

6. **Write tests** in `tests/test_mpnn_integration.py`:

   a. **Test scaffold_split produces non-overlapping scaffolds:**
      - Create a small dataset with known scaffolds (e.g., benzene, naphthalene
        derivatives)
      - Run scaffold_split
      - Assert no scaffold appears in both train and test
   b. **Test scaffold_split maintains approximate ratios:**
      - Assert train/val/test sizes are within 20% of target ratios
   c. **Test temporal_split orders by year:**
      - Create dataset with known years
      - Assert test set has the latest years
   d. **Test backward compatibility:**
      - Assert `split_dataset(ds, split_type="random")` produces the same output
        as the old `split_dataset(ds)` with the same seed
   e. **Test invalid split_type raises ValueError:**
      - Assert `split_dataset(ds, split_type="invalid")` raises ValueError
   f. **Test scaffold_split without RDKit:**
      - Mock RDKit unavailability
      - Assert appropriate ImportError is raised

## Verification

- [ ] `split_dataset(ds, split_type="random")` with same seed produces identical
      output to the current code (backward compat)
- [ ] `scaffold_split()` produces train/val/test with non-overlapping scaffolds
- [ ] `temporal_split()` produces train/val/test ordered by year
- [ ] `pytest tests/test_mpnn_integration.py -v` -- all tests pass
- [ ] `pytest -v --tb=short` -- full test suite passes (646+)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion

## Agent Instructions

- Follow StateBind conventions: `from __future__ import annotations`, type
  annotations on all functions, RDKit as optional dep with fallback.
- RDKit is in the `[ml]` extras group, so it should be available in ML environments.
  Still provide a clean error message if not installed.
- Keep the existing `split_dataset()` function signature backward compatible. The
  new `split_type` parameter has a default of `"random"`.
- Do NOT change `DEFAULT_WEIGHTS` or any scoring logic.
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status.

## Notes and Gotchas

- **Molecules that fail RDKit parsing** (invalid SMILES): Assign them to the training
  set. Log a warning. Do not crash.
- **Single-molecule scaffolds**: Some scaffolds may have only 1 molecule. These are
  fine -- they get assigned to whichever split needs more molecules.
- **Ratio approximation**: Scaffold split cannot perfectly match ratios because
  scaffolds have different sizes. Accept approximate ratios (within ~10% of target).
- **Existing AffinityDataset structure**: The dataset stores `graphs` and `smiles_list`
  in parallel lists. Any split must keep these aligned.
- **The `_subset()` helper** at line 399 already handles creating subsets from
  index arrays. Reuse this pattern.
