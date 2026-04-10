#!/usr/bin/env bash
# Setup script for REINVENT 4 conda environment on Yale Bouchet HPC.
#
# Creates a separate conda environment (reinvent4) with REINVENT 4
# installed via pip, plus RDKit and numpy for the GNINA scoring component.
#
# Usage:
#   chmod +x scripts/setup_reinvent4.sh
#   bash scripts/setup_reinvent4.sh
#
# Prerequisites:
#   - miniconda module available via Lmod
#   - Internet access (for pip/conda downloads)

set -euo pipefail

ENV_NAME="reinvent4"
PYTHON_VERSION="3.11"

echo "=== REINVENT 4 Environment Setup ==="
echo "Environment name: ${ENV_NAME}"
echo "Python version:   ${PYTHON_VERSION}"
echo ""

# ── Load miniconda ──────────────────────────────────────────────────────
module load miniconda
eval "$(conda shell.bash hook)"

# ── Check if env already exists ─────────────────────────────────────────
if conda env list | grep -qw "${ENV_NAME}"; then
    echo "WARNING: conda env '${ENV_NAME}' already exists."
    echo "To recreate, first run: conda env remove -n ${ENV_NAME}"
    echo "Then re-run this script."
    exit 1
fi

# ── Create conda environment ───────────────────────────────────────────
echo "Creating conda environment '${ENV_NAME}' with Python ${PYTHON_VERSION}..."
conda create -y -n "${ENV_NAME}" python="${PYTHON_VERSION}"

echo "Activating environment..."
conda activate "${ENV_NAME}"

# ── Install REINVENT 4 via pip ──────────────────────────────────────────
echo "Installing REINVENT 4..."
pip install --no-cache-dir reinvent

# ── Install dependencies for GNINA scoring component ───────────────────
echo "Installing RDKit and numpy..."
conda install -y -c conda-forge rdkit numpy

# ── Verification ────────────────────────────────────────────────────────
echo ""
echo "=== Verification ==="

echo -n "Python version: "
python --version

echo -n "REINVENT import: "
python -c "import reinvent; print('OK')" 2>/dev/null || echo "FAILED"

echo -n "RDKit import:    "
python -c "from rdkit import Chem; print('OK')" 2>/dev/null || echo "FAILED"

echo -n "NumPy import:    "
python -c "import numpy; print(f'OK (v{numpy.__version__})')" 2>/dev/null || echo "FAILED"

# Check GNINA binary is accessible (should be in repo bin/ or PATH)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GNINA_BIN="${REPO_ROOT}/bin/gnina"
if [ -x "${GNINA_BIN}" ]; then
    echo "GNINA binary:    OK (${GNINA_BIN})"
elif command -v gnina &>/dev/null; then
    echo "GNINA binary:    OK ($(which gnina))"
else
    echo "GNINA binary:    NOT FOUND -- docking will fail"
    echo "  Expected at: ${GNINA_BIN}"
fi

echo ""
echo "=== Setup complete ==="
echo "Activate with: module load miniconda && eval \"\$(conda shell.bash hook)\" && conda activate ${ENV_NAME}"
