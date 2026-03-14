# Architecture Decision Records

## ADR-001: src/ Layout with pyproject.toml

**Date:** 2026-03-14
**Status:** Accepted

**Context:** Need a clean, installable Python package structure.

**Decision:** Use `src/` layout with `pyproject.toml` (PEP 621). No `setup.py`.

**Rationale:** Modern Python packaging standard. Prevents accidental imports from the working directory. Supported by all major tools (pip, setuptools, flit, hatch).

---

## ADR-002: EGFR-Only Scope for v1

**Date:** 2026-03-14
**Status:** Accepted

**Context:** Could target multiple kinases or broader protein families.

**Decision:** Restrict to EGFR kinase domain only.

**Rationale:** Depth over breadth. EGFR has rich structural data, well-characterized mutations, and clinical relevance. One target done well demonstrates more than many targets done superficially.

---

## ADR-003: Config-Driven Execution

**Date:** 2026-03-14
**Status:** Accepted

**Context:** Need reproducible pipeline runs without hard-coded parameters.

**Decision:** All parameters in YAML config files. Scripts load configs, never hard-code paths or thresholds.

**Rationale:** Reproducibility. Any run can be replicated by sharing the config file + code version.

---

## ADR-004: Baseline-First Development

**Date:** 2026-03-14
**Status:** Accepted

**Context:** Temptation to jump to sophisticated ML models.

**Decision:** Every phase starts with the simplest viable baseline. Only add complexity when the baseline is established and the improvement is measurable.

**Rationale:** Scientific rigor. You can't claim your method is better if you don't know what "better than" means.

---

## ADR-005: Artifacts as Module Interface

**Date:** 2026-03-14
**Status:** Accepted

**Context:** Modules need to communicate results.

**Decision:** Modules write serialized artifacts (JSON, CSV, PDB) to `artifacts/`. Downstream modules read from `artifacts/`.

**Rationale:** Decouples modules. Any module can be re-run independently. Artifacts serve as checkpoints and are inspectable.
