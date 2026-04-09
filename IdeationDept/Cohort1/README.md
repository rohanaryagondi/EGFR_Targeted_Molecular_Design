# IdeationDept -- Multi-Agent Ideation System for StateBind

A simulated R&D department where domain-specialist AI agents collaborate to produce a
publication-ready research agenda for the StateBind project.

---

## Quick Start

```bash
cd IdeationDept/agents/orchestrator
claude
# Then say: "Run the ideation department"
```

That's it. The orchestrator handles everything from there.

---

## How It Works

The **orchestrator** is the only agent you interact with. It reads the project context
and specialist persona files, then launches 7 domain-specialist agents as subagents
using the `Agent` tool with `model: "opus"`. Each specialist conducts deep internet
research (WebSearch, WebFetch), writes research notes and proposals, and the
orchestrator synthesizes their output across multiple rounds.

```
You (operator)
  |
  v
Orchestrator (department head)
  |
  +-- launches --> Sr. Medicinal Chemist      (SAR, ADMET, clinical)
  +-- launches --> Sr. Computational Chemist   (FEP, MD, physics)
  +-- launches --> Sr. Structural Biologist    (conformations, KLIFS, PDB)
  +-- launches --> Sr. ML Researcher           (benchmarks, venues, baselines)
  +-- launches --> Maverick Generative AI      (3D diffusion, flow matching)
  +-- launches --> Maverick Synth-Bio / DMPK   (retrosynthesis, PK)
  +-- launches --> Maverick Data Scientist     (statistics, validation design)
```

### Round Protocol

1. **Round 1 -- Deep Research:** All 7 specialists research in parallel. Each produces
   a 500+ line research note with 20+ citations. Output: `output/research/`

2. **Round 2 -- Proposals:** Based on Round 1 findings, the orchestrator assigns 3-5
   specialists to write formal proposals. Output: `output/proposals/`

3. **Round 3 -- Cross-Review:** Specialists critique each other's proposals from their
   domain perspective. Output: `output/critiques/`

4. **Round 4+ -- Refinement:** Iterate until convergence. Revised proposals, deeper
   research on specific questions, new specialists if needed.

5. **Final Output:** A prioritized research agenda in `output/roundtables/final-agenda.md`

---

## Directory Structure

```
IdeationDept/
├── CLAUDE.md                  # Dept-wide rules (all agents inherit)
├── README.md                  # This file
├── context/
│   └── project-briefing.md    # Shared project context (~500 lines)
├── agents/
│   ├── orchestrator/          # The department head (your entry point)
│   │   └── CLAUDE.md
│   ├── senior-medicinal-chemist/
│   │   └── CLAUDE.md
│   ├── senior-computational-chemist/
│   │   └── CLAUDE.md
│   ├── senior-structural-biologist/
│   │   └── CLAUDE.md
│   ├── senior-ml-researcher/
│   │   └── CLAUDE.md
│   ├── maverick-generative-ai/
│   │   └── CLAUDE.md
│   ├── maverick-synth-bio/
│   │   └── CLAUDE.md
│   └── maverick-data-scientist/
│       └── CLAUDE.md
├── output/
│   ├── research/              # Research notes from specialists
│   ├── proposals/             # Formal idea proposals
│   ├── critiques/             # Cross-agent reviews
│   ├── roundtables/           # Orchestrator synthesis docs
│   └── directives/            # Orchestrator task assignments
└── templates/
    ├── research-note.md       # Template for research output
    ├── proposal.md            # Template for proposals
    └── critique.md            # Template for cross-reviews
```

---

## Agent Profiles

### Senior Track (conservative, experienced)

| Agent | Focus | Brings |
|-------|-------|--------|
| **Sr. Medicinal Chemist** | Drug-likeness, SAR, clinical translation | "Would a med-chem team pursue this?" |
| **Sr. Computational Chemist** | FEP, MD, solvation, force fields | "What physics is being ignored?" |
| **Sr. Structural Biologist** | Kinase conformations, KLIFS, PDB | "What do the other 400 structures say?" |
| **Sr. ML Researcher** | Benchmarks, venues, ablation design | "What would Reviewer 2 say?" |

### Maverick Track (bold, ambitious)

| Agent | Focus | Brings |
|-------|-------|--------|
| **Maverick Generative AI** | 3D diffusion, flow matching | "Why are we still using SMILES in 2026?" |
| **Maverick Synth-Bio / DMPK** | Retrosynthesis, PK, end-to-end | "Can a chemist actually make this?" |
| **Maverick Data Scientist** | Statistics, validation, rigor | "What's the confidence interval?" |

---

## What This Produces

After running through multiple rounds, you'll find in `output/`:

- **Research notes** with citations, data points, and evidence from the literature
- **Proposals** with implementation plans, effort estimates, and publication strategy
- **Critiques** with cross-domain feedback and suggested modifications
- **Roundtable summaries** synthesizing insights and resolving disagreements
- **A final prioritized research agenda** for making StateBind publication-ready

---

## Relationship to Vision System

IdeationDept builds on (does not replace) the existing Vision System in `vision/`.
The orchestrator reads prior vision ideas to avoid duplication and to revisit deferred
ideas with fresh evidence from the new research.

---

## Notes

- All agents produce documents only -- no code changes, no test modifications
- Agents do extensive internet research (WebSearch, WebFetch) -- expect long run times
- The orchestrator can create new specialist agents if the team needs different expertise
- Each round takes significant time due to deep research; the full process may take
  several hours of wall time
- All output is in `IdeationDept/output/` -- organized by type and round
