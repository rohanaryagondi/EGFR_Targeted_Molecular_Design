#!/bin/bash
#SBATCH --job-name=ws13_validate
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p day
#SBATCH -A pi_mg269
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# ── WS13: Retrospective Time-Split Validation - End-to-End Test ──────────
#
# This script validates the entire WS13 implementation:
#   1. Installs the package in editable mode
#   2. Runs all unit tests (new + existing)
#   3. Builds time-split datasets (2010, 2015 cutoffs)
#   4. Runs the retrospective validation pipeline
#   5. Verifies output artifacts exist and are well-formed
#
# Submit from the ws13-retro worktree:
#   cd ~/projects/statebind/repo/.claude/worktrees/ws13-retro
#   sbatch scripts/slurm_ws13_validate.sh

set -euo pipefail

WORKTREE="$HOME/projects/statebind/repo/.claude/worktrees/ws13-retro"
cd "$WORKTREE"

echo "=========================================="
echo "WS13 Retrospective Validation - SLURM Job"
echo "=========================================="
echo "Date:      $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Host:      $(hostname)"
echo "Worktree:  $WORKTREE"
echo "Branch:    $(git branch --show-current)"
echo ""

# ── Step 0: Environment setup ────────────────────────────────────────────
echo ">>> Step 0: Setting up environment..."
module load Python/3.12.3
pip install -e ".[dev]" --quiet 2>&1 | tail -2
echo "Python: $(python --version)"
echo ""

# ── Step 1: Run all tests ────────────────────────────────────────────────
echo ">>> Step 1: Running full test suite..."
python -m pytest -v --tb=short 2>&1
PYTEST_EXIT=$?
echo ""
echo "pytest exit code: $PYTEST_EXIT"
if [ $PYTEST_EXIT -ne 0 ]; then
    echo "FAIL: Tests did not all pass. Aborting."
    exit 1
fi
echo ""

# ── Step 2: Run lint on new files ─────────────────────────────────────────
echo ">>> Step 2: Linting new files..."
ruff check \
    src/statebind/evaluation/retrospective.py \
    scripts/build_timesplit_datasets.py \
    scripts/run_retrospective_validation.py \
    tests/test_retrospective.py
RUFF_EXIT=$?
echo "ruff exit code: $RUFF_EXIT"
if [ $RUFF_EXIT -ne 0 ]; then
    echo "FAIL: Lint errors found."
    exit 1
fi
echo ""

# ── Step 3: Build time-split datasets ─────────────────────────────────────
echo ">>> Step 3: Building time-split datasets..."
python scripts/build_timesplit_datasets.py \
    --config configs/retrospective.yaml \
    --output-dir data/processed/ 2>&1
BUILD_EXIT=$?
echo "build exit code: $BUILD_EXIT"
if [ $BUILD_EXIT -ne 0 ]; then
    echo "FAIL: Dataset build failed."
    exit 1
fi
echo ""

# ── Step 4: Verify dataset artifacts ──────────────────────────────────────
echo ">>> Step 4: Verifying dataset artifacts..."

for CUTOFF in 2010 2015; do
    TRAIN="data/processed/timesplit_${CUTOFF}_train.json"
    META="data/processed/timesplit_${CUTOFF}_metadata.json"

    if [ ! -f "$TRAIN" ]; then
        echo "FAIL: Missing $TRAIN"
        exit 1
    fi
    if [ ! -f "$META" ]; then
        echo "FAIL: Missing $META"
        exit 1
    fi

    N_TRAIN=$(python -c "import json; d=json.load(open('$TRAIN')); print(len(d))")
    echo "  Cutoff $CUTOFF: $N_TRAIN training compounds"

    # Verify no future drug leakage
    python -c "
import json
from statebind.evaluation.retrospective import get_future_drugs, verify_no_leakage

train = json.load(open('$TRAIN'))
train_smiles = {r['smiles'] for r in train}
future = get_future_drugs($CUTOFF)
verify_no_leakage(train_smiles, future)
print('  Cutoff $CUTOFF: No leakage detected (PASS)')
"
done
echo ""

# ── Step 5: Run retrospective validation pipeline ─────────────────────────
echo ">>> Step 5: Running retrospective validation (skip-retrain)..."
python scripts/run_retrospective_validation.py \
    --config configs/retrospective.yaml \
    --skip-retrain \
    --output-dir artifacts/evaluation/ 2>&1
RETRO_EXIT=$?
echo "retrospective exit code: $RETRO_EXIT"
if [ $RETRO_EXIT -ne 0 ]; then
    echo "FAIL: Retrospective validation failed."
    exit 1
fi
echo ""

# ── Step 6: Verify output artifacts ──────────────────────────────────────
echo ">>> Step 6: Verifying output artifacts..."

SUMMARY="artifacts/evaluation/retrospective_summary.json"
if [ ! -f "$SUMMARY" ]; then
    echo "FAIL: Missing $SUMMARY"
    exit 1
fi

python -c "
import json

summary = json.load(open('$SUMMARY'))
assert 'results' in summary, 'Missing results key'
assert 'summary' in summary, 'Missing summary key'
assert len(summary['results']) > 0, 'No results'
print(f'  Summary artifact: {len(summary[\"results\"])} results')
print(f'  Cutoffs: {summary.get(\"cutoffs\", [])}')

# Check each result has required fields
for r in summary['results']:
    assert 'cutoff_year' in r, 'Missing cutoff_year'
    assert 'pipeline' in r, 'Missing pipeline'
    assert 'enrichment_factors' in r, 'Missing enrichment_factors'
    assert 'future_drug_ranks' in r, 'Missing future_drug_ranks'

print('  All result fields present (PASS)')
"

for CUTOFF in 2010 2015; do
    RETRO="artifacts/evaluation/retrospective_${CUTOFF}.json"
    if [ -f "$RETRO" ]; then
        echo "  Per-cutoff artifact: $RETRO (exists)"
    else
        echo "  WARNING: Missing $RETRO"
    fi
done
echo ""

# ── Summary ───────────────────────────────────────────────────────────────
echo "=========================================="
echo "WS13 VALIDATION COMPLETE"
echo "=========================================="
echo "All checks passed."
echo ""
echo "Results summary:"
python -c "
import json
summary = json.load(open('artifacts/evaluation/retrospective_summary.json'))
print(summary.get('summary', 'No summary available'))
"
echo ""
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
