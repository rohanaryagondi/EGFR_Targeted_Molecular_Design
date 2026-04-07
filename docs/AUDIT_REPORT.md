# Audit Report

**Date:** 2026-03-20
**Scope:** Full repository audit — architecture, code, tests, documentation, scientific claims

---

## Audit Methodology

Every Python file (84 source files), every script (37), every test file (19), and every documentation file (20+) was read and evaluated against:
- Architectural consistency
- Code quality (dead code, duplication, naming, types)
- Documentation accuracy (claims vs. implementation)
- Test coverage and assertion strength
- Scientific honesty (unsupported claims, hidden assumptions)
- Reproducibility (determinism, path handling, seed management)

---

## Top 10 Issues Found and Resolved

### 1. CRITICAL: Unsupported claims in early docs (FIXED)

**Files:** `docs/GITHUB_STORY.md`, `docs/PROJECT_CHARTER.md`

Phase 0 documentation claimed Vina docking, Mann-Whitney U statistical tests, p-values, and "30+ PDB structures." None of these exist in the implemented code. The docking component is a stub. No statistical tests are performed. The dataset has 16 structures, not 30+.

**Fix:** Rewrote GITHUB_STORY.md 2-minute and 5-minute pitches to match actual implementation. Updated PROJECT_CHARTER.md scoring and report descriptions to reference the stub and actual metrics.

### 2. HIGH: Duplicated ValidationIssue dataclass (DOCUMENTED)

**Files:** `src/statebind/data/validation.py` line 17, `src/statebind/processing/validation.py` line 20

Two separate `ValidationIssue` dataclasses with different field sets but similar purpose. The data-layer version has `(level, category, message, path)` while the processing version has `(level, dataset, field, message)`.

**Status:** These are intentionally different — the data-layer validates directory structure while the processing layer validates dataset schemas. The field differences are meaningful, not accidental duplication. Documented but not merged.

### 3. HIGH: No weight validation in unified scoring (FIXED)

**File:** `src/statebind/ranking/scoring.py`

Scoring weights were not validated. Passing weights that don't sum to 1.0 or are missing required keys would produce silently wrong composite scores.

**Fix:** Added `_validate_weights()` function that checks all required keys are present and weights sum to 1.0 (within 1e-4 tolerance). Called at the top of `score_unified()`.

### 4. MEDIUM: Hardcoded pocket volumes without citations (FIXED)

**File:** `src/statebind/generation/conditioning.py`

Pocket volumes (450, 520, 790, 850 Å³) were stated without literature references or uncertainty bounds.

**Fix:** Added docstring with literature citations for each volume estimate and a note that exact values vary by detection method.

### 5. MEDIUM: Empty utils/__init__.py (FIXED)

**File:** `src/statebind/utils/__init__.py`

The utils module had no public API exports.

**Fix:** Added imports of `load_config`, `ensure_dir`, `save_json`, `load_json` with `__all__`.

### 6. MEDIUM: state_specificity decay function undocumented (FIXED)

**File:** `src/statebind/ranking/scoring.py`

The geometric decay (1.0 → 0.5 → 0.25 → 0.0) for state specificity had no rationale.

**Fix:** Added docstring explaining why geometric decay was chosen over linear.

### 7. MEDIUM: PHASE_PLAN.md status table stale

**File:** `docs/PHASE_PLAN.md`

Only Phase 0 is marked complete. Phases 1-7 are not updated with completion status. This is a Phase 0 document and reflects planning, not execution status.

**Status:** The README now serves as the authoritative status document. PHASE_PLAN.md is retained as historical planning artifact.

### 8. LOW: Inconsistent `from __future__ import annotations`

Approximately half the source files include this import; the other half don't. This doesn't affect runtime behavior (all type hints resolve correctly) but is stylistically inconsistent.

**Status:** Documented. Not fixed because the change would touch 30+ files with no functional impact.

### 9. LOW: Fragile path walking in DataPaths

**File:** `src/statebind/data/paths.py` line 21

`Path(__file__).resolve().parent.parent.parent.parent` walks up 4 directory levels. Moving the file would break auto-detection.

**Status:** Documented. The constructor accepts an explicit `project_root` parameter as a fallback. The auto-detection is a convenience, not a requirement.

### 10. LOW: Hash-based split assignment in processing/context.py

**File:** `src/statebind/processing/context.py`

Uses `hashlib.md5(mutation_id.encode()).hexdigest()` for deterministic train/val/test splits. MD5 is deterministic across platforms and Python versions, so this is actually robust. The magic bucket thresholds (< 6 → train, < 8 → val) encode a 60/20/20 split.

**Status:** Documented but acceptable. Would benefit from named constants.

---

## 5 Most Dangerous Scientific Assumptions

1. **Docking proxy is learned, not physics-based.** [PARTIALLY RESOLVED] The MPNN proxy (RMSE=0.72, trained on 10,466 compounds) replaced the constant 0.5 stub, but binding claims should be qualified as "MPNN-predicted" not "experimentally validated." Physics-based docking (Vina/GNINA) remains future work.

2. **SMILES n-gram Tanimoto is a crude similarity metric.** [RESOLVED] Morgan/ECFP4 Tanimoto is now the primary metric (WS02). SMILES n-grams remain as fallback only.

3. **state_specificity gives state-aware candidates a built-in advantage.** This component (weight 0.15) is structurally zero for the baseline. The static pipeline still achieves a higher mean score (0.5437 vs 0.4378), so this advantage is insufficient to overcome the static pipeline's similarity-score advantage.

4. **Single-class context dataset.** All 17 mutations map to DFGin_aCin. The context model achieves 100% accuracy trivially. Phase 4 ablations are uninformative.

5. **Literature-curated transitions, not MD-derived.** The Markov model's transition probabilities reflect publication frequency, not thermodynamic equilibrium. Active-state transitions are overrepresented because they are more commonly studied.

---

## 5 Weakest Engineering Choices

1. **SMILES-level molecular modifications.** String transformations (appending "C(F)(F)F" for CF3) are not validated against 3D geometry. [PARTIALLY RESOLVED] RDKit SA scoring (WS01) now filters synthetically inaccessible candidates, and a VAE (9.5M params, SELFIES) generates valid molecules. 3D geometry validation remains unaddressed.

2. **No CI/CD pipeline.** [RESOLVED] GitHub Actions workflow implemented in WS06. Automated pytest on push/PR.

3. **No formal statistical testing.** [RESOLVED] Mann-Whitney U, bootstrap CI, and Cohen's d implemented in WS03. 548 tests across 12 subpackages. Null hypothesis formally retained.

4. **Report files are gitignored.** Phase reports are generated by scripts but excluded from git. A reader cloning the repo cannot see results without running scripts first.

5. **RDKit is optional.** [RESOLVED] Morgan/ECFP4 fingerprints (WS02), SA scoring (WS01), and ADMET profiling (WS09) all use RDKit. SMILES n-grams remain as fallback when RDKit is unavailable, but RDKit is now the primary path.

---

## 5 Most Recruiter-Impressive Strengths

1. **Hypothesis-driven architecture.** The entire codebase is organized around answering one question, with the baseline defined before the experiment runs. This demonstrates scientific thinking, not just coding ability.

2. **548 tests across 12 subpackages (19 test files).** Comprehensive test coverage with fast execution. Tests validate schemas, pipelines, metrics, ML models, and figure generation — not just "does it run."

3. **Honest reporting.** The null hypothesis is formally retained — state-aware does not beat static on mean score. Limitations are stated alongside results. The docking proxy's nature (MPNN, not physics-based) is labeled. This is rarer and more valuable than positive-only results.

4. **7-phase phased delivery.** Each phase has defined inputs, outputs, pass/fail conditions, and a report. This mirrors real research engineering workflow.

5. **20+ documentation files.** Architecture decisions, risk register, benchmark specification, evaluation framework, recruiter summary, technical deep dive. The documentation is stronger than most production codebases.

---

## Items Remaining Unresolved

| Item | Severity | Status |
|------|----------|--------|
| Inconsistent `__future__` imports | Low | Unresolved — 30+ files, no functional impact |
| PHASE_PLAN.md status table | Low | Unresolved — historical planning doc; README is authoritative |
| Reports gitignored | Low | Unresolved — by design (generated artifacts) |
| No CI/CD | Low | **[RESOLVED]** GitHub Actions implemented (WS06) |
| RDKit not required | Medium | **[RESOLVED]** Morgan/ECFP4, SA scoring, ADMET all use RDKit (WS01/WS02/WS09) |
| No statistical tests | Medium | **[RESOLVED]** Mann-Whitney U, bootstrap CI, Cohen's d implemented (WS03) |
