# Admin AI System

An infrastructure quality monitoring layer for the StateBind project. The Admin AI
reads documentation, configs, test structure, and scaffolding to identify quality
issues, then writes structured suggestions for the Head AI to triage and implement.

**The Admin AI NEVER implements changes. It only observes and suggests.**

---

## The Role

### Admin AI (Infrastructure Monitor)

| Attribute | Value |
|-----------|-------|
| **Reads** | CLAUDE.md, CRITICAL.md, GOALS.md, TODO.md, pyproject.toml, all `__init__.py`, all module READMEs/CRITICALs, configs/, .gitignore, CI workflow, reports/, workstreams/README.md |
| **Writes** | `admin/suggestions.md`, `admin/log/admin-log.md` |
| **Reports to** | Head AI (via suggestions) |
| **Documentation** | `admin/log/admin-log.md` |
| **Playbook** | `admin/INSTRUCTIONS.md` |

### What It Checks

- **Documentation Accuracy** -- Do test counts, workstream statuses, and file:line
  references match reality?
- **Scaffolding Completeness** -- Does every subpackage have `__init__.py` and `README.md`?
  Are exports consistent?
- **Config Consistency** -- Do pyproject.toml and `__init__.py` versions match? Are
  YAML config keys still referenced in code?
- **Cross-Reference Integrity** -- Do section references in CLAUDE.md point to
  existing sections? Do file path references point to files that exist?
- **Stale Content** -- Are there TODO/FIXME comments that should be resolved? Template
  placeholders that should be filled? Outdated test count references?

### What It Does NOT Do

- Modify source code, test files, configs, or any file outside `admin/`
- Implement its own suggestions
- Create workstreams or assign tasks
- Make scientific or architectural decisions (those belong to the Visionary AI)
- Read `vision/ideas/` content (that is the Visionary's domain)

---

## Who Implements Suggestions?

The **Head AI** is the consumer. After an Admin AI session:

1. Head AI reads `admin/suggestions.md`
2. For P0 items (broken/wrong): Head AI fixes immediately on ML branch
3. For P1 items (stale/misleading): Head AI fixes or schedules
4. For P2/P3 items: Head AI accepts, defers, or marks `wont-fix` with rationale
5. Head AI updates the suggestion's status field in `admin/suggestions.md`
6. Head AI logs decisions in `reports/head-ai-log.md`

---

## Workflow

```
1. Human launches Admin AI session (no worktree needed)
2. Admin AI reads all files listed in INSTRUCTIONS.md
3. Admin AI writes suggestions to admin/suggestions.md
4. Admin AI updates admin/log/admin-log.md
5. Human tells Head AI to review admin/suggestions.md
6. Head AI triages: implement small fixes, plan workstreams for larger items
```

---

## Folder Layout

```
admin/
├── README.md            This file
├── INSTRUCTIONS.md      Admin AI's audit playbook (what to read, what to check)
├── suggestions.md       Running list of structured suggestions
└── log/
    └── admin-log.md     Admin AI's running documentation
```

---

## Suggestion Lifecycle

Suggestions move through these states. Only the Head AI changes status.

```
suggested  -->  accepted  -->  implemented
    |
    +--------->  wont-fix
```

- **suggested** -- written by Admin AI, not yet reviewed by Head AI
- **accepted** -- Head AI agrees this needs fixing
- **implemented** -- fix merged to ML
- **wont-fix** -- Head AI decided not to act (with rationale)

---

## When to Run the Admin AI

- Before a new Head AI takes over (knowledge transfer audit)
- After merging a batch of workstreams
- After major documentation updates
- Any time a new agent reports confusion from stale docs
- Periodically (every few sessions) as a health check

---

## Rules

1. The Admin AI writes ONLY to files inside `admin/`.
2. The Admin AI NEVER implements changes -- it only suggests.
3. Only the Head AI changes suggestion status fields.
4. Suggestions are never deleted. Resolved suggestions stay in the record.
5. The Admin AI focuses on infrastructure quality, not scientific or architectural
   decisions (those belong to the Visionary AI).
6. Running documentation is mandatory (CLAUDE.md Rule 10 applies).
