# ReviewCohort -- Critical Analysis & Final Implementation Plan

A review panel of 5 domain experts that critically evaluates proposals from both
Cohort1 and Cohort2, verifies claims through deep research, and produces the
definitive implementation plan for StateBind's next era.

---

## Quick Start

```bash
cd IdeationDept/ReviewCohort/agents/orchestrator
claude
# Then say: "Run the review cohort"
```

---

## Why a Review Cohort?

Cohort1 and Cohort2 each independently generated research agendas through 3-round
ideation cycles with different specialist teams. The ReviewCohort:

1. **Reads both cohorts' output** -- no contamination firewall here
2. **Critically evaluates** every proposal for novelty, rigor, feasibility, and impact
3. **Verifies claims** through independent deep internet research
4. **Deliberates** over multiple rounds to build consensus
5. **Produces THE implementation plan** that determines what actually gets built

---

## The Review Panel

| Agent | Short Name | Role | Evaluates |
|-------|-----------|------|-----------|
| Sr. Journal Reviewer -- Comp Bio | compbiorev | Editorial board, Nature Comp Sci / JCIM | Novelty, rigor, impact, reproducibility |
| Sr. Journal Reviewer -- ML & AI | mlrev | Area chair, NeurIPS / ICML | ML methodology, ablations, baselines |
| Principal Computational Scientist | principal | Senior company employee (15+ years) | Technical feasibility, effort, codebase |
| Associate Research Scientist | associate | Junior company employee (2-3 years) | Implementation details, practical blockers |
| Program Director / Chief Scientist | progdir | Executive research leader (25+ years) | Prioritization, resources, publication strategy |

---

## Round Protocol

| Round | Goal | Output |
|-------|------|--------|
| 1. Independent Review | Each reviewer assesses both cohorts' agendas | `output/reviews/` |
| 2. Deep Verification | Verify specific claims via internet research | `output/research/` |
| 3. Deliberation | Cross-reviewer discussion, build consensus | `output/deliberation/` |
| 4. Final Plan | Orchestrator synthesizes the implementation plan | `output/final/` |

---

## Input (What the Panel Reviews)

- `Cohort1/output/roundtables/final-agenda.md` + 5 proposals + 11 critiques
- `Cohort2/output/roundtables/final-agenda.md` + 5 proposals + 6 critiques
- Shared project context (`context/project-briefing.md`)
- StateBind codebase (for feasibility assessment)

---

## Output

After running, find results in `output/`:
- `output/reviews/` -- Round 1 independent review assessments
- `output/research/` -- Round 2 verification research reports
- `output/deliberation/` -- Round 3 cross-reviewer deliberation
- `output/final/implementation-plan.md` -- THE definitive plan
