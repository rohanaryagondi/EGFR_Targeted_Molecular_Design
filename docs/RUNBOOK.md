# Runbook

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design.git
cd EGFR_Targeted_Molecular_Design

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in development mode
pip install -e ".[dev]"

# Verify installation
statebind --help
pytest
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=statebind

# Specific module
pytest tests/test_context.py

# Data layer tests only
pytest tests/test_data.py -v
```

## Data Management

### How data is organized

```
data/
├── manifests/          # JSON manifest files tracking every data asset (committed to git)
│   ├── context.json    # Mutation/resistance data sources
│   ├── structures.json # PDB structure sources
│   └── ligands.json    # Ligand/compound sources
├── raw/                # Downloaded source files (gitignored — never modify in place)
│   ├── context/        # COSMIC, ClinVar, manual curation files
│   ├── structures/     # PDB files, KLIFS data, UniProt
│   └── ligands/        # ChEMBL, co-crystal ligands, approved drugs
└── processed/          # Derived data produced by StateBind scripts (gitignored)
    ├── context/        # mutation_atlas.json
    ├── structures/     # state_atlas.json, pockets/
    └── ligands/        # reference_compounds.csv
```

### How manifests work

Every file in `data/raw/` and `data/processed/` has a corresponding entry in a manifest
file under `data/manifests/`. Manifest entries track:
- Source database, version, and URL
- Download date
- SHA-256 file hash
- Status: `pending` → `downloaded` → `validated` → `processed`

Manifests are committed to git. Raw/processed files are gitignored (too large, or require
database accounts to download). This means anyone cloning the repo can see exactly what
data is expected, where to get it, and verify they have the correct version.

### Data workflow

```bash
# Step 1: Register all known sources (creates manifests + directories)
python scripts/register_sources.py

# Step 2: Manually download raw data files according to manifest notes
#         (See docs/DATA_SOURCES.md for instructions per source)

# Step 3: Validate that expected files are present
python scripts/validate_data_layout.py

# Step 4: Check coverage summary
python scripts/summarize_data_inventory.py
```

### How future phases consume data

All downstream modules import from `statebind.data`:

```python
from statebind.data import DataPaths

paths = DataPaths()
atlas = json.load(open(paths.mutation_atlas_path))
```

Modules never construct data paths manually. The `DataPaths` class is the single source
of truth for where data lives. This means data directory structure can change without
breaking module code.

## Running Pipeline Stages

Each phase has a corresponding script in `scripts/`. All scripts are config-driven.

```bash
# Phase 1: Register and validate data sources
python scripts/register_sources.py
python scripts/validate_data_layout.py

# Phase 1: Build mutation atlas
python scripts/run_context.py --config configs/context.yaml

# Phase 2: Build structure atlas
python scripts/run_structure.py --config configs/structure.yaml

# Phase 3: Predict states
python scripts/run_dynamics.py --config configs/dynamics.yaml

# Phase 4: Generate candidates
python scripts/run_generation.py --config configs/generation.yaml

# Phase 5: Rank candidates
python scripts/run_ranking.py --config configs/ranking.yaml
```

## Outputs

- **Data:** `data/processed/` — Processed datasets consumed by pipeline modules
- **Artifacts:** `artifacts/<module>/` — Pipeline outputs, intermediate results
- **Reports:** `reports/` — Analysis reports, figures

## Troubleshooting

### Import errors after install

```bash
pip install -e ".[dev]" --force-reinstall
```

### Tests not finding package

Ensure you installed in development mode (`pip install -e .`), not just `pip install .`.

### Data validation fails

Run `python scripts/register_sources.py` first to create manifests and directories,
then check `python scripts/summarize_data_inventory.py` to see which files are missing.
