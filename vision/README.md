# Vision System

A strategic planning layer for the StateBind project. Three AI roles work together
to continuously identify, document, and execute improvements beyond the scope of any
single workstream.

---

## The Three Roles

### 1. Assistant AI (Briefing Writer)

**What it does:** Reads the full codebase, documentation, and progress reports. Distills
everything into concise briefing documents that the Visionary AI can consume without
reading source code.

**What it reads:** Everything -- CLAUDE.md, GOALS.md, TODO.md, CRITICAL.md, all progress
reports, key source files, workstream briefs, interface contracts.

**What it writes:** Five briefing files in `vision/briefings/`:
- `project-overview.md` -- what StateBind is and why it matters
- `current-progress.md` -- what's done, what's pending, hard numbers
- `remaining-goals.md` -- targets vs reality, the gap analysis
- `architecture.md` -- modules, data flow, scoring function, ML models
- `known-limitations.md` -- weaknesses, stubs, what reviewers would attack

**When to run:** Before every Visionary AI session, so the briefings are fresh.

### 2. Visionary AI (Strategic Thinker)

**What it does:** Reads the briefings and proposes bold improvements. Thinks like a
principal investigator, a drug discovery veteran, and an ML researcher simultaneously.
Never implements anything -- only writes ideas.

**What it reads:** ONLY files inside `vision/`:
- `vision/briefings/*.md` (the Assistant's output)
- `vision/ideas/README.md` (its rules and template)
- `vision/log/visionary-log.md` (its own running log)

**What it writes:** Numbered idea files in `vision/ideas/` (e.g.,
`001-ensemble-docking.md`). Each idea follows a structured template with problem
statement, vision, impact assessment, effort estimate, and implementation sketch.

**What it NEVER does:** Read source code. Modify status fields on ideas. Implement
anything. Touch files outside `vision/`.

**When to run:** After major milestones -- all Group A workstreams done, all WS done,
after ML models are trained, after integration is complete. Any time the project feels
like it needs a strategic reset.

### 3. Head AI (Consumer and Planner)

**What it does:** After completing current work, reads the Visionary's ideas and decides
which to accept. Converts accepted ideas into workstream briefs, creates tasks for
modular agents, and updates all documentation.

**What it reads:** `vision/ideas/*.md` (all proposed ideas).

**What it writes:**
- Updates idea status fields: `proposed` -> `accepted` -> `planned` -> `in-progress`
  -> `completed` / `deferred`
- Creates new workstream briefs in `workstreams/`
- Updates `HUMANONLY.md` with new agent prompts
- Updates `reports/head-ai-log.md` with decisions

---

## Workflow

```
1. Human launches Assistant AI
   |
   v
2. Assistant AI reads full project state
   |
   v
3. Assistant AI writes/updates briefings in vision/briefings/
   |
   v
4. Human launches Visionary AI
   |
   v
5. Visionary AI reads briefings (ONLY vision/ folder)
   |
   v
6. Visionary AI writes ideas in vision/ideas/
   |
   v
7. Human tells Head AI to review vision ideas
   |
   v
8. Head AI reads ideas, accepts/defers, plans workstreams
   |
   v
9. Head AI creates tasks for modular agents
   |
   v
10. Modular agents execute new workstreams
```

---

## Folder Layout

```
vision/
├── README.md                   This file
├── briefings/
│   ├── INSTRUCTIONS.md         Assistant AI's playbook (what to read and write)
│   ├── project-overview.md     Written by Assistant AI
│   ├── current-progress.md     Written by Assistant AI
│   ├── remaining-goals.md      Written by Assistant AI
│   ├── architecture.md         Written by Assistant AI
│   └── known-limitations.md    Written by Assistant AI
├── ideas/
│   ├── README.md               Visionary AI rules and idea template
│   └── {NNN}-{title}.md        Individual idea files (written by Visionary AI)
└── log/
    ├── visionary-log.md        Visionary AI's running documentation
    └── assistant-log.md        Assistant AI's running documentation
```

---

## Rules

1. **The Visionary AI reads ONLY files inside `vision/`.** It never reads source code,
   test files, configs, or any file outside this directory. Its world is the briefings
   and its own ideas.

2. **The Assistant AI reads everything but writes only to `vision/briefings/` and
   `vision/log/assistant-log.md`.** It is a translator, not an implementer.

3. **The Head AI is the only role that modifies idea status fields.** The Visionary
   proposes; the Head AI decides.

4. **All three roles maintain running documentation.** Assistant and Visionary logs
   are in `vision/log/`. The Head AI log is at `reports/head-ai-log.md`. This is
   non-negotiable (CLAUDE.md Rule 10 applies to all AI roles).

5. **Briefings must be refreshed before every Visionary session.** Stale briefings
   produce stale ideas. Always run the Assistant AI first.

6. **Ideas are never deleted.** They are deferred, not removed. The historical record
   matters -- a deferred idea today might be the right idea next quarter.
