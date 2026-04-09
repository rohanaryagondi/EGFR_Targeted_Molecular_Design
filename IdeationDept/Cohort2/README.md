# IdeationDept Cohort2 -- Fresh Perspectives

A second roundtable of domain-specialist AI agents, deliberately different from Cohort1,
to generate independent ideas for StateBind's publication-ready research agenda.

---

## Quick Start

```bash
cd IdeationDept/Cohort2/agents/orchestrator
claude
# Then say: "Run the ideation department"
```

---

## Why Cohort2?

Cohort1 ran a full ideation cycle with its team of specialists and produced a prioritized
agenda. Cohort2 brings **different specialists** covering the same broad domains but
from different angles. This avoids groupthink and surfaces ideas that Cohort1's
particular composition of expertise may have missed.

**Critical:** Cohort2 agents do NOT read Cohort1's output. Independence ensures fresh
thinking.

---

## Cohort1 vs Cohort2 Agents

| Domain | Cohort1 | Cohort2 | What's Different |
|--------|---------|---------|-----------------|
| Chemistry | Sr. Medicinal Chemist (SAR, molecules) | **Sr. Drug Hunter** (programs, TPP, IND) | Molecule-focused → Program-focused |
| Physics | Sr. Computational Chemist (FEP, energy) | **Sr. Biophysicist** (kinetics, kon/koff) | Equilibrium → Kinetics |
| Structure/Data | Sr. Structural Biologist (PDB, protein) | **Sr. Cheminformatician** (representations, QSAR) | Protein-centric → Ligand-data-centric |
| Strategy | Sr. ML Researcher (venues, baselines) | **Sr. Clinical Oncologist** (patients, resistance) | "What do reviewers want?" → "What do patients need?" |
| Generation | Maverick Generative AI (3D diffusion) | **Maverick Protein ML** (ESM-2, pLMs, AlphaFold) | Ligand generation → Protein representation |
| Translational | Maverick Synth-Bio (retrosynthesis, PK) | **Maverick Kinome Pharmacologist** (selectivity, multi-kinase) | Single-molecule → Kinome-wide |
| Rigor | Maverick Data Scientist (statistics, CIs) | **Maverick Benchmark Architect** (benchmarks, open science) | Statistical methods → Community impact |

---

## Shared Resources

Cohort2 reuses shared resources from the IdeationDept root:
- `../../context/project-briefing.md` -- same project context
- `../../templates/` -- same document templates
- `../../CLAUDE.md` -- same department-wide rules

---

## Round Protocol

Same as Cohort1: R1 deep research → R2 proposals → R3 cross-review → R4+ refinement.
All output goes to `Cohort2/output/`.

---

## Output

After running, find results in `output/`:
- `output/research/` -- Research notes from each specialist
- `output/proposals/` -- Formal proposals
- `output/critiques/` -- Cross-domain reviews
- `output/roundtables/` -- Orchestrator synthesis documents
- `output/directives/` -- Round task assignments
