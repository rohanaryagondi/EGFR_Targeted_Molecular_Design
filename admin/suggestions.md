# Admin AI: Suggestions

Structured suggestions from the Admin AI for the Head AI to triage.
Only the Head AI changes status fields.

**Status lifecycle:** `suggested` --> `accepted` --> `implemented` / `wont-fix`

---

## Active Suggestions

<!-- Newest first. Admin AI adds entries here. Head AI updates status. -->

| ID | Priority | Category | Status | Summary |
|----|----------|----------|--------|---------|
| S010 | P2 | Config | accepted | CI workflow guaranteed to fail — ~40 ruff violations block `ruff check src/` |

---

## Suggestion Details

<!-- Each suggestion gets its own ### heading below, newest first. -->

### S010: CI workflow guaranteed to fail due to ruff violations

- **Priority:** P2
- **Category:** Config
- **Status:** accepted
- **Date:** 2026-03-30
- **File(s):** `.github/workflows/ci.yml`; ~40 files in `src/` with ruff violations

**Problem:** The CI workflow runs `ruff check src/` in both the `test` and `lint` jobs. CRITICAL.md documents ~40 pre-existing ruff violations across `src/` (F401 unused imports, I001 import sorting, E501 line length, F541 f-strings, N815 naming). These violations guarantee CI failure on every push, making the CI/CD pipeline (WS06) non-functional despite being "complete."

**Suggested Fix:** Run `ruff check --fix src/` to auto-fix all fixable violations (I001, F401, most E501). Manually resolve remaining violations. Verify with `ruff check src/` before committing.

**Head AI Notes:** Accepted. Deferred to a dedicated cleanup session — fixing ~40 ruff violations across the codebase requires careful review to avoid breaking imports. Will be addressed as a standalone task, not bundled with the documentation triage.

---

## Resolved Suggestions

<!-- Suggestions that have been implemented or marked wont-fix. Never delete. -->

| ID | Priority | Category | Status | Summary | Resolution Date |
|----|----------|----------|--------|---------|----------------|
| S001 | P0 | Documentation | implemented | CLAUDE.md architecture missing chemistry/ module, lists nonexistent pockets/ | 2026-03-30 |
| S002 | P0 | Cross-Reference | implemented | 18 of 23 file:line references in CLAUDE.md and CRITICAL.md point to wrong lines | 2026-03-30 |
| S003 | P0 | Stale Content | implemented | GOALS.md Section 6 says "0 of 9 workstreams", "359 tests", everything "Not started" | 2026-03-30 |
| S004 | P1 | Stale Content | implemented | CLAUDE.md stale counts: "359 tests" (x4), "72 .py files", "14 test files" | 2026-03-30 |
| S005 | P1 | Documentation | implemented | CLAUDE.md Section 3 module table has wrong file counts for 3 modules | 2026-03-30 |
| S006 | P1 | Stale Content | implemented | CRITICAL.md and TODO.md say "540 tests" — actual count is 548 (pytest verified) | 2026-03-30 |
| S007 | P1 | Stale Content | implemented | Module READMEs stale: evaluation/ claims no stats, ml/ claims no training data | 2026-03-30 |
| S008 | P1 | Cross-Reference | implemented | INTERFACES.md contracts 5 and 6 don't match actual implementations | 2026-03-30 |
| S009 | P1 | Stale Content | implemented | TODO.md Section 2 data prep scripts shown unchecked but scripts and data exist | 2026-03-30 |
| S011 | P2 | Stale Content | implemented | GOALS.md Section 3 discusses WS01/WS03 as future priorities — both complete | 2026-03-30 |
| S012 | P3 | Scaffolding | wont-fix | Inconsistent __init__.py exports — 5 modules export, 6 modules have only docstrings | 2026-03-30 |

### Resolved Details

**S001** (implemented): Replaced pockets/ with chemistry/ (7 files) in CLAUDE.md Sections 3, 4, and 9. Added chemistry/ to pipeline diagram and dependency graph.

**S002** (implemented): Updated all file:line references in CLAUDE.md Sections 5, 13, and 15, and in CRITICAL.md. Added function name anchors alongside line numbers for durability (e.g., `:86 DEFAULT_WEIGHTS` instead of just `:40`). Note: Admin AI counted 538 tests but `pytest --co -q` yields 548 — used authoritative pytest count.

**S003** (implemented): Updated every row in GOALS.md Section 6 Success Criteria Table. Marked 10 items as Complete, 8 as Pending training. Updated "Current" column values to post-workstream reality.

**S004** (implemented): Updated all instances: "72 Python source files" → "84" (verified count), "14 test files, 359 tests" → "19 test files, 548 tests", "Existing 359 tests" → "Existing 548 tests", "total count must be >= 359" → ">= 548".

**S005** (implemented): Updated file counts: evaluation/ 4→7, generation/ 7→9, ml/ 13→15. Added chemistry/ row (7 files). Updated Key Files columns with new files (statistics.py, affinity_predictor.py, vae_integration.py, etc.).

**S006** (implemented): Admin AI counted 538, but `pytest --co -q` returns 548. Updated all references from "540" to "548" in CRITICAL.md and TODO.md.

**S007** (implemented): Updated 4 module READMEs (evaluation/, ml/, ranking/, generation/) to document new files, APIs, and completed workstreams. Removed "pending"/"future" language for completed work.

**S008** (implemented): Updated INTERFACES.md Contract 5 (VAE) to reflect actual `load_vae_candidates()` / `build_vae_libraries()` API. Updated Contract 6 (ADMET) to match actual `check_admet_pass(predictions, thresholds) -> (bool, list[str])` signature. Added design notes explaining decisions.

**S009** (implemented): Checked all three data prep items `[x]` in TODO.md Section 2.

**S011** (implemented): Updated GOALS.md Section 3 Priority 3 to mark WS01/WS03 as complete. Updated Section 4 to note all 9 workstreams are finished.

**S012** (wont-fix): Code works as-is — callers import from submodules directly. Adding `__all__` and explicit exports to 6 modules would increase maintenance burden without current benefit. If a future workstream needs clean public APIs from these modules, this can be revisited.
