# StateBind

**Context-Aware Conformational State Modeling for EGFR-Targeted Molecular Design**

## Thesis

Most structure-based drug design treats protein targets as static entities—one crystal structure, one binding pocket, one docking campaign. But kinases like EGFR exist in multiple conformational states (active DFG-in, inactive DFG-out, αC-helix-in/out, and more), and clinically relevant resistance mutations shift the equilibrium between these states.

**StateBind** builds a pipeline that:

1. Starts from disease context (mutation profile, resistance mechanism)
2. Infers the most relevant EGFR conformational states
3. Models those states structurally
4. Identifies state-specific binding pockets
5. Generates candidate binders conditioned on pocket geometry
6. Ranks candidates against strong baselines

**Core claim:** State-aware molecular design outperforms static single-structure design on EGFR, measured by docking scores, pocket complementarity, and selectivity across conformational states.

## System Overview

```
Disease Context (mutations, resistance)
        │
        ▼
┌──────────────────┐
│ Context Module    │  Curate mutations, map to known resistance mechanisms
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Structure Module  │  Build conformational state atlas from PDB/AlphaFold
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Dynamics Module   │  Lightweight state/dynamics modeling
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Generation Module │  State-conditioned molecular generation
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Ranking Module    │  Score, rerank, compare to baselines
└────────┴─────────┘
         │
         ▼
    Artifacts & Reports
```

## Phased Plan

| Phase | Name | Goal | Status |
|-------|------|------|--------|
| 0 | Scaffold | Repo structure, docs, CI basics | ✅ Complete |
| 1 | Context & Data | EGFR mutation atlas, resistance context curation | 🔨 In progress |
| 2 | Structure Atlas | Conformational state classification from PDB | 🔲 Not started |
| 3 | Dynamics | Lightweight conformational state predictor | 🔲 Not started |
| 4 | Generation | State-conditioned molecular generation | 🔲 Not started |
| 5 | Ranking | Docking, reranking, baseline comparison | 🔲 Not started |
| 6 | Integration | End-to-end pipeline, demo, report | 🔲 Not started |

See [docs/PHASE_PLAN.md](docs/PHASE_PLAN.md) for detailed breakdowns.

## Current Status

**Phase 1: Context & Data — In Progress**

- Data layer infrastructure built (manifests, registry, validation, paths)
- Source registry defines all v1 data sources with provenance tracking
- Data documentation: [DATA_SOURCES.md](docs/DATA_SOURCES.md), [DATA_SCHEMA.md](docs/DATA_SCHEMA.md)
- Next: curate mutation atlas, download structural data

## Quick Start

```bash
# Clone
git clone https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design.git
cd EGFR_Targeted_Molecular_Design

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# CLI
statebind --help
```

## Project Structure

```
├── src/statebind/          # Main package
│   ├── context/            # Disease context & mutation curation
│   ├── structure/          # Conformational state atlas
│   ├── dynamics/           # State modeling & dynamics
│   ├── generation/         # Molecular generation
│   ├── ranking/            # Scoring & reranking
│   ├── data/               # Data layer (registry, manifests, validation)
│   └── utils/              # Shared utilities
├── data/                   # Data directory (see below)
│   ├── manifests/          # Provenance-tracking manifest files (committed)
│   ├── raw/                # Downloaded source files (gitignored)
│   └── processed/          # Derived data (gitignored)
├── configs/                # YAML configuration files
├── scripts/                # Runnable pipeline scripts
├── tests/                  # Test suite
├── notebooks/              # Analysis & visualization only
├── artifacts/              # Pipeline outputs (gitignored)
├── reports/                # Generated reports (gitignored)
└── docs/                   # Project documentation
```

## Documentation

- [Project Charter](docs/PROJECT_CHARTER.md) — Scope, hypotheses, success criteria
- [Architecture](docs/ARCHITECTURE.md) — System design, module contracts, baselines, ablations
- [Phase Plan](docs/PHASE_PLAN.md) — Detailed phase breakdown with pass/fail conditions
- [Benchmark Spec](docs/BENCHMARK_SPEC.md) — Metrics, baselines, what constitutes a "win"
- [Risk Register](docs/RISK_REGISTER.md) — Bottlenecks, limitations, fallback plans
- [Data Sources](docs/DATA_SOURCES.md) — All public data sources with licensing and quality notes
- [Data Schema](docs/DATA_SCHEMA.md) — Raw/processed schemas, canonical IDs, provenance
- [GitHub Story](docs/GITHUB_STORY.md) — How to present and narrate the project
- [Decisions](docs/DECISIONS.md) — Architecture decision records
- [Runbook](docs/RUNBOOK.md) — How to run each phase

## License

MIT
