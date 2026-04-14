# IdeationDept -- Department-Wide Rules

These rules apply to ALL agents in the IdeationDept system. The orchestrator embeds
this document (or its key rules) into every subagent prompt.

---

## Cohort Organization

The IdeationDept runs multiple independent cohorts, each with different specialist
agents. This avoids groupthink and surfaces diverse ideas.

```
IdeationDept/
├── CLAUDE.md              # This file (shared rules)
├── context/               # Shared project context
├── templates/             # Shared document templates
├── Cohort1/               # First roundtable (completed)
│   ├── agents/            # Cohort1 specialist personas
│   └── output/            # Cohort1 research, proposals, critiques
├── Cohort2/               # Second roundtable (different specialists, completed)
│   ├── agents/            # Cohort2 specialist personas
│   └── output/            # Cohort2 research, proposals, critiques
├── ReviewCohort/          # Critical review panel (reads both cohorts)
│   ├── agents/            # Review panel member personas
│   └── output/            # Reviews, verification, deliberation, final plan
└── DiagnosticCohort/      # G2 investigation team (diagnoses ablation failure)
    ├── agents/            # Diagnostic specialist personas
    └── output/            # Investigation reports, proposals, recovery plan
```

**Shared resources** (at IdeationDept root): `context/project-briefing.md`, `templates/`.
**Cohort-specific**: Each cohort has its own `agents/` and `output/` directories.

### Contamination Firewall (Ideation Cohorts Only)

Agents in ideation cohorts (Cohort1, Cohort2) must NOT read another ideation cohort's
output. This ensures independent ideation. Specifically:
- Cohort2 agents must NOT read `Cohort1/output/` (research, proposals, critiques, etc.)
- Cohort2 agents MAY read Cohort1 agent persona files for structural inspiration only
- The orchestrator enforces this by never including cross-cohort output in subagent prompts

### ReviewCohort Exception

The ReviewCohort is the **exception** to the contamination firewall. Its entire purpose
is to read and critically evaluate output from BOTH Cohort1 and Cohort2. ReviewCohort
agents MUST read both cohorts' final agendas, proposals, and critiques.

### DiagnosticCohort

The DiagnosticCohort investigates the Gate G2 (Ablation C) NO_GO result. It reads:
- The G2 report (`reports/gate-g2-ablation-c-report.md`)
- The implementation plan (`ReviewCohort/output/final/implementation-plan.md`)
- The pre-registration (`docs/pre-registration.md`)
- Source code (VAE, scoring) for architectural context
- Project briefing for full context

Its 5 agents investigate three hypotheses for the null result: weak conditioning
mechanism (H1), insufficient state-specific data (H2), and wrong evaluation metric (H3).

---

## Mission

Generate a publication-ready research agenda for StateBind -- identifying the highest-
impact next steps to take this project from a completed computational pipeline to a
top-venue publication (Nature Computational Science, JCIM, Bioinformatics, NeurIPS).

All output is **ideation and research only**. No agent may modify source code, tests,
configs, or any file outside `IdeationDept/`.

---

## Non-Negotiable Rules

### 1. No Code Changes

Agents produce **documents only**. Never modify files in `src/`, `tests/`, `scripts/`,
`configs/`, `data/`, `artifacts/`, or any other directory outside `IdeationDept/`.
Never run `pip install`, `pytest`, `python`, or any command that modifies the project
state.

### 2. Read-Only Access to Project Files

Agents may READ project files for context:
- `src/statebind/` -- to understand current implementations
- `configs/` -- to understand current parameters
- `artifacts/` -- to understand pipeline outputs
- `CLAUDE.md`, `CRITICAL.md` -- for project rules and critical facts
- `vision/` -- for prior art (existing ideas and briefings)
- `reports/` -- for workstream results

But never WRITE to any of these locations.

### 3. Scientific Honesty

- Never overclaim. Say "computational prediction" not "result."
- Distinguish between "published evidence shows X" and "we speculate X."
- Cite specific papers, databases, and data points. Vague claims are not acceptable.
- When proposing an idea, explicitly state what is novel vs. what is established.
- Acknowledge limitations and failure modes of every proposal.

### 4. Deep Research Mandate

Every specialist agent MUST spend extensive time on internet research before writing
proposals or critiques. This means:

- Use `WebSearch` to find recent papers, methods, benchmarks, and tools
- Use `WebFetch` to read specific pages from ChEMBL, KLIFS, PDB, TDC, GitHub repos
- Find **specific numbers**: accuracy metrics, dataset sizes, compute costs, timelines
- Cite papers with authors, year, journal, and key findings
- Research notes should contain **real data**, not hand-wavy speculation

The expectation is that each agent's research note is 500+ lines with 20+ citations
and specific quantitative findings.

### 5. Document Conventions

All documents written by agents follow these conventions:

- **File naming**: `{agent-short-name}-R{round:02d}.md` for research notes,
  `{agent-short-name}-P{number:02d}.md` for proposals,
  `{agent-short-name}-C{proposal-id}.md` for critiques
- **Agent short names**:
  - Cohort1: `medchem`, `compchem`, `structbio`, `mlres`, `genai`, `synthbio`, `datasci`
  - Cohort2: `drughunt`, `biophys`, `cheminfo`, `clinonc`, `protml`, `kinpharm`, `bencharch`
  - ReviewCohort: `compbiorev`, `mlrev`, `principal`, `associate`, `progdir`
  - DiagnosticCohort: `condgen`, `kinchembio`, `evaldes`, `mldebug`, `pubstrat`
  - Orchestrator: `orch` (all cohorts)
- **Frontmatter**: Every document starts with YAML frontmatter:
  ```yaml
  ---
  agent: <full agent name>
  round: <round number>
  date: <ISO date>
  type: <research-note | proposal | critique | roundtable | directive>
  ---
  ```
- **Citations**: Use inline citations: `(Author et al., Year)` with a References
  section at the bottom containing full citations
- **Timestamps**: Always UTC ISO format
- **Scores and metrics**: Round to 4 decimal places when referencing project data

### 6. Output Organization

All agent output goes to their cohort's `output/` subdirectories (e.g., `Cohort2/output/`):

| Directory | Contents | Who Writes |
|-----------|----------|-----------|
| `output/research/` | Research notes -- deep literature surveys, database queries, method reviews | All specialists |
| `output/proposals/` | Formal idea proposals following the proposal template | Specialists (assigned by orchestrator) |
| `output/critiques/` | Cross-agent reviews of proposals following the critique template | Specialists (assigned by orchestrator) |
| `output/roundtables/` | Synthesis documents combining insights across agents | Orchestrator only |
| `output/directives/` | Instructions for the next round of work | Orchestrator only |

### 7. No Duplication of Vision System Ideas

The existing Vision System (`vision/ideas/001-012`) proposed 12 ideas. Three were
implemented (005, 008, 009). Nine remain deferred. Agents MUST read
`vision/ideas/*.md` (via the project briefing) and:

- Do NOT re-propose ideas that are already described in the vision system
- DO build on deferred ideas with NEW evidence from fresh research
- DO identify gaps the vision system missed entirely
- DO propose combinations of ideas that create emergent value

### 8. Publication Framing

All proposals must be framed in terms of publication impact:

- What venue is this targeting? (Nature Comp Sci, JCIM, NeurIPS, ICML, etc.)
- What would the paper's main claim be?
- What would reviewers attack?
- What comparison baselines are needed?
- What is the minimal viable experiment?

### 9. Feasibility Awareness

Proposals must account for the real constraints:

- **Compute**: Yale Bouchet HPC -- H200/RTX5000 Ada GPUs, SLURM scheduler
- **Data**: ChEMBL, PDB, KLIFS, TDC are available; proprietary pharma data is not
- **Software**: Python ecosystem, PyTorch, RDKit, GNINA v1.1, open-source tools only
- **Time**: Months, not years. Prefer approaches that reuse existing infrastructure.
- **Expertise**: Computational -- no wet lab, no collaborators assumed

### 10. Existing Project Context

Agents should be aware of these key project facts (detailed in the project briefing):

- **Thesis**: State-aware > static for EGFR molecular design
- **Key result**: 10x retrospective enrichment (EF@10 = 4.95/7.72 vs 0.47/0.79)
- **Null retained on mean score**: Static wins 0.5437 vs 0.4378
- **ML stack**: SELFIES VAE (99.9% valid), MPNN (R^2=0.69), ADMET (hERG AUROC=0.77)
- **Infrastructure**: GNINA docking, Pareto optimization, 646 tests, 12 workstreams
- **7 remaining gaps**: experimental validation, selectivity, retrosynthesis,
  continuous conformations, pre-training, ADMET in scoring, uncertainty quantification
