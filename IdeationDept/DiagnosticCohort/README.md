# IdeationDept DiagnosticCohort -- G2 Investigation & Recovery

A focused investigation team assembled to diagnose the Gate G2 (Ablation C) NO_GO
result and propose a concrete recovery plan for the StateBind project.

---

## Quick Start

```bash
cd IdeationDept/DiagnosticCohort/agents/orchestrator
claude
# Then say: "run the diagnostic cohort"
```

---

## Background

Gate G2 tested StateBind's core thesis: does conformational state-conditioned molecular
generation outperform unconditioned generation? After 10 seeds, ~6,800 molecules, and
2 generation modes, the result was a **definitive NO_GO** (Cohen's d = 0.059).

The G2 report (`reports/gate-g2-ablation-c-report.md`) identifies three hypotheses:

| Hypothesis | Description | Quick Test |
|-----------|-------------|-----------|
| **H1:** Weak conditioning | Prefix tokens too weak; model routes around them | Stronger mechanism (FiLM, CFG) |
| **H2:** Data/biology | EGFR states don't produce distinct chemotypes | Analyze scaffolds per state |
| **H3:** Wrong evaluation | Scoring uses fixed pocket; can't detect state-specific signal | Multi-pocket docking |

---

## The Team (5 Specialists)

| Agent | Short Name | Investigates | Core Question |
|-------|-----------|-------------|---------------|
| Conditional Generation Expert | condgen | H1 (architecture) | Is prefix-token conditioning strong enough? |
| Kinase Chemical Biology Expert | kinchembio | H2 (data/biology) | Do the 3 states select for different chemotypes? |
| Evaluation Design Expert | evaldes | H3 (metrics) | Was the evaluation unable to detect the signal? |
| ML Diagnostics Expert | mldebug | All H's (internals) | Where does the conditioning signal die? |
| Publication Strategy Advisor | pubstrat | Recovery path | What's the highest-impact next move? |

---

## Round Protocol

- **Round 1:** Independent investigation -- each agent deep-dives into their hypothesis
- **Round 2:** Cross-analysis -- agents read each other's findings, propose top 3 actions
- **Round 3:** Final recovery plan -- orchestrator synthesizes into decision tree

---

## Shared Resources

Uses shared resources from the IdeationDept root:
- `../../context/project-briefing.md` -- project context
- `../../templates/` -- document templates (research-note, proposal)

Plus diagnostic-specific inputs:
- `reports/gate-g2-ablation-c-report.md` -- the G2 failure report
- `docs/pre-registration.md` -- what was pre-registered
- `src/statebind/ml/vae.py` -- VAE conditioning code
- `src/statebind/ranking/scoring.py` -- scoring function

---

## Output

After running, find results in `output/`:
- `output/investigation/` -- Round 1 investigation reports + synthesis
- `output/proposals/` -- Round 2 cross-informed proposals
- `output/final/` -- The recovery plan (the key deliverable)
