# Workstream 06: CI/CD and Engineering Polish

## Goal

Add a GitHub Actions CI pipeline, a `full` extras group in pyproject.toml, and CI badges to the README. This ensures tests pass on every push across Python versions and makes the repo look professionally maintained.

## Prerequisites

None. This workstream is fully independent and can start immediately.

## Files to Create

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest -v --tb=short
      - name: Lint
        run: ruff check src/

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: ruff check src/

  test-with-chemistry:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install with all extras
        run: pip install -e ".[dev,science,chemistry]"
      - name: Run tests with optional deps
        run: pytest -v --tb=short
```

**Notes:**
- Three jobs: basic test matrix, lint-only, and full-extras test
- `test-with-chemistry` verifies that RDKit/scipy integration paths work
- No type checking job yet (mypy config is permissive, would need tightening first)

### `.github/workflows/` directory

```bash
mkdir -p .github/workflows
```

## Files to Modify

### `pyproject.toml`

Add a `full` extras group that includes all optional dependencies:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1.0",
    "mypy>=1.5",
]
science = [
    "scikit-learn>=1.3",
    "scipy>=1.11",
    "matplotlib>=3.7",
    "seaborn>=0.12",
]
structure = [
    "biopython>=1.81",
]
chemistry = [
    "rdkit",
]
full = [
    "statebind[dev,science,structure,chemistry]",
]
```

### `README.md`

Add CI badge at the top (after the title):

```markdown
![CI](https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
```

Add installation instructions for the `full` extras:

```markdown
## Installation

```bash
# Minimal (core pipeline only)
pip install -e ".[dev]"

# Full (all optional dependencies)
pip install -e ".[full]"
```

## Files NOT to Touch

- Any `src/statebind/` source files — this workstream is infrastructure only
- Any test files — this workstream doesn't add tests (it runs existing ones)
- Any docs other than README.md

## Definition of Done

- [ ] `.github/workflows/ci.yml` created with 3 jobs
- [ ] `pyproject.toml` updated with `full` extras group
- [ ] `README.md` updated with CI badge and install instructions
- [ ] CI workflow passes locally (`act` or push to test branch)
- [ ] All existing 359+ tests pass
- [ ] No changes to source code or test files

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation — edge cases, gotchas, implicit assumptions, or things that broke unexpectedly — add them to the relevant CRITICAL.md file(s):

- **Module-level**: `src/statebind/{module}/CRITICAL.md` for facts specific to the module you modified
- **Project-level**: `/CRITICAL.md` for facts that cross module boundaries

Format: one fact per line, include `file:line` references. Be detailed yet concise.

## Agent Instructions

Be detailed yet concise in all code, comments, and documentation. Include `file:line` references when noting important locations. No fluff — every line should carry information.
