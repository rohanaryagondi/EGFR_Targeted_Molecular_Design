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
```

## Running Pipeline Stages

Each phase has a corresponding script in `scripts/`. All scripts are config-driven.

```bash
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

- **Artifacts:** `artifacts/<module>/<run_name>/` — Pipeline outputs, intermediate data
- **Reports:** `reports/<run_name>/` — Analysis reports, figures

## Troubleshooting

### Import errors after install

```bash
pip install -e ".[dev]" --force-reinstall
```

### Tests not finding package

Ensure you installed in development mode (`pip install -e .`), not just `pip install .`.
