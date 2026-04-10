---
phase: "Phase 1: Core Experiments"
task_id: P1-T06
task_name: "REINVENT 4 Environment + GNINA Plugin"
implementation_plan_ref: "P9: REINVENT 4 Baseline on EGFR (part 1 -- setup)"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "3-5 days"
---

# Task: REINVENT 4 Environment + GNINA Plugin

## Objective

Set up REINVENT 4 as an external molecular generation baseline and create a
custom scoring component that wraps GNINA docking. This enables a fair
comparison: REINVENT 4 (state-of-the-art RL-based generator, no state labels)
vs StateBind (state-conditioned VAE). Both use the same GNINA scoring oracle.

## Context

REINVENT 4 is a widely-used molecular optimization framework that uses
reinforcement learning to generate molecules optimizing a reward function.
By configuring it with GNINA docking as the reward, we create an external
baseline that uses the same physics-based scoring but without any
conformational state information. This is a strong external baseline that
JCIM reviewers will expect.

## Prerequisites

- [x] Phase 0 complete
- [x] GNINA available on the cluster
- [x] Prepared receptor files for EGFR (1M17) in `data/processed/docking/receptors/`

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/chemistry/docking.py:346-524` | dock_molecule() and dock_batch() -- GNINA wrapper to replicate |
| `configs/docking.yaml` | GNINA settings: exhaustiveness, num_modes, receptor paths |
| REINVENT 4 docs | https://github.com/MolecularAI/REINVENT4 -- understand plugin system |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `scripts/setup_reinvent4.sh` | -- | Environment setup script |
| NEW: `scripts/reinvent4_gnina_component.py` | -- | Custom GNINA ExternalProcess scoring component |
| NEW: `configs/reinvent4_egfr.toml` | -- | REINVENT 4 configuration for EGFR |
| NEW: `scripts/run_reinvent4_egfr.py` | -- | Wrapper script to launch REINVENT 4 run |
| NEW: `scripts/slurm_reinvent4.sh` | -- | SLURM submission script |

## Implementation Steps

1. **Create environment setup script** (`scripts/setup_reinvent4.sh`):

   ```bash
   #!/bin/bash
   # REINVENT 4 environment setup for Bouchet cluster
   module load miniconda
   eval "$(conda shell.bash hook)"

   # Create separate env to avoid conflicts with statebind
   conda create -n reinvent4 python=3.11 -y
   conda activate reinvent4

   # Install REINVENT 4
   pip install reinvent

   # Install GNINA-related deps
   pip install rdkit numpy

   # Verify installation
   python -c "import reinvent; print('REINVENT 4 installed:', reinvent.__version__)"
   ```

2. **Create GNINA ExternalProcess scoring component**
   (`scripts/reinvent4_gnina_component.py`):

   REINVENT 4 supports custom scoring via ExternalProcess components. This
   script receives SMILES on stdin and returns scores on stdout.

   ```python
   #!/usr/bin/env python3
   """GNINA docking scoring component for REINVENT 4.

   Reads SMILES from stdin (one per line), docks each against a prepared
   receptor using GNINA, and writes docking scores to stdout.

   Usage (called by REINVENT 4 ExternalProcess):
       echo "CCO" | python reinvent4_gnina_component.py --receptor receptor.pdb
   """
   ```

   Implementation:
   a. Read SMILES from stdin (one per line, REINVENT 4 format)
   b. For each SMILES:
      - Convert to 3D SDF using RDKit (EmbedMolecule + MMFF optimization)
      - Run GNINA docking against the specified receptor
      - Extract CNN affinity score
      - Normalize to [0, 1] using sigmoid(-score / scale)
   c. Write scores to stdout (one per line)
   d. Handle failures gracefully: return 0.0 for molecules that fail
      3D conversion or docking

   Key: replicate the SMILES→3D→GNINA→score pipeline from
   `chemistry/docking.py:346-464` but as a standalone script (no statebind
   imports, since REINVENT runs in its own environment).

3. **Create REINVENT 4 configuration** (`configs/reinvent4_egfr.toml`):

   REINVENT 4 uses TOML config files. Key settings:
   ```toml
   [parameters]
   prior_file = "path/to/prior"  # REINVENT's pretrained model
   agent_file = "path/to/agent"  # Starts as copy of prior

   [scoring]
   type = "custom_product"

   [[scoring.component]]
   [scoring.component.ExternalProcess]
   name = "gnina_docking"
   weight = 1.0

   [scoring.component.ExternalProcess.endpoint]
   executable = "python"
   args = ["scripts/reinvent4_gnina_component.py", "--receptor", "data/processed/docking/receptors/1m17_receptor.pdb"]

   [stage.0]
   max_steps = 500
   n_molecules = 128
   ```

   Note: REINVENT 4 uses a single receptor (1M17, same as static baseline).
   No state conditioning. This is the key comparison.

4. **Create wrapper script** (`scripts/run_reinvent4_egfr.py`):

   Wrapper that:
   - Activates the reinvent4 conda environment
   - Verifies GNINA is available
   - Launches REINVENT 4 with the EGFR config
   - Collects generated SMILES from REINVENT output
   - Converts to StateBind candidate format for downstream scoring
   - Outputs to `artifacts/generation/reinvent4_egfr_candidates.json`

5. **Create SLURM script** (`scripts/slurm_reinvent4.sh`):

   ```bash
   #!/bin/bash
   #SBATCH --job-name=reinvent4_egfr
   #SBATCH --output=logs/reinvent4_%j.out
   #SBATCH --error=logs/reinvent4_%j.err
   #SBATCH -p priority
   #SBATCH -A prio_gerstein
   #SBATCH --gpus=h200:1
   #SBATCH --cpus-per-task=8
   #SBATCH --mem=32G
   #SBATCH -t 12:00:00

   module load miniconda
   eval "$(conda shell.bash hook)"
   conda activate reinvent4
   mkdir -p logs

   python scripts/run_reinvent4_egfr.py --config configs/reinvent4_egfr.toml
   ```

6. **Test the GNINA component end-to-end**:

   Run manually with a single molecule to verify the pipeline:
   ```bash
   echo "c1ccccc1" | python scripts/reinvent4_gnina_component.py \
       --receptor data/processed/docking/receptors/1m17_receptor.pdb
   ```
   Should output a single docking score (float between 0 and 1).

## Verification

- [ ] `setup_reinvent4.sh` creates environment and installs REINVENT 4 successfully
- [ ] `reinvent4_gnina_component.py` accepts SMILES on stdin and returns scores on stdout
- [ ] Single-molecule test produces a valid docking score
- [ ] `configs/reinvent4_egfr.toml` is valid TOML and references correct paths
- [ ] SLURM script has correct partition and account settings
- [ ] `pytest -v --tb=short` -- 669+ tests pass (no new tests needed for external tool)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- REINVENT 4 runs in its OWN conda environment, separate from statebind.
  Do not install it into the statebind environment.
- The GNINA component script must be STANDALONE -- no `from statebind import`
  allowed, since REINVENT runs in a different environment. Replicate the
  necessary SMILES→3D→GNINA logic from docking.py.
- Use the same GNINA parameters as StateBind: exhaustiveness=8, num_modes=5,
  CNN scoring mode=rescore (from configs/docking.yaml).
- The receptor file for 1M17 should already be prepared. If not, the task
  agent should prepare it using `scripts/prepare_docking_receptors.py`.
- REINVENT 4's ExternalProcess expects scores on stdout, one per line,
  matching the input SMILES order.

## Notes and Gotchas

- **REINVENT 4 environment conflicts**: REINVENT 4 has its own PyTorch
  dependency. Using a separate conda env avoids version conflicts with
  statebind's ML stack.
- **GNINA binary path**: The GNINA binary must be accessible from the
  REINVENT 4 environment. It's likely in `$PATH` or `bin/gnina` in the
  repo root. Verify with `which gnina`.
- **ExternalProcess timeout**: GNINA docking takes ~30s per molecule.
  REINVENT generates 128 molecules per step. Each step takes ~1 hour
  of docking. Plan for long runtimes.
- **Fallback to Vina scoring**: If GNINA integration fails after 2 weeks,
  the implementation plan says to fall back to REINVENT + Vina scoring
  (less comparable but still valid). Gate G3 covers this.
- **Prior model**: REINVENT 4 comes with pretrained priors. Use the
  default prior for the baseline -- this represents the "generic"
  chemical space without EGFR-specific training.
- **This task is setup only**: The actual REINVENT 4 run happens in P1-T11.
