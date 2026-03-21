# GitHub Story: How to Present StateBind

This document defines how the project should be narrated publicly. The goal is to communicate scientific rigor, engineering quality, and honest framing — not to oversell.

---

## 30-Second Pitch

> "I built StateBind, a computational pipeline that tests whether knowing which conformational state a drug target is in helps you design better molecules. Focused on EGFR — the most important kinase in lung cancer drug resistance — it maps mutations to conformational states, generates molecules against state-specific binding pockets, and benchmarks state-aware design against the standard static-structure approach. The result is a modular, reproducible Python pipeline with a clear experimental answer: does state-awareness help, and by how much?"

**Key framing:** "tests whether" not "proves that." Computational pipeline, not drug discovery. Clear question, clear answer.

---

## 2-Minute Pitch

> "Most computational drug design treats protein targets as frozen — you pick one crystal structure, identify the binding pocket, and design molecules against that pocket. But proteins move. Kinases like EGFR exist in multiple conformational states — active, inactive, and intermediate forms — and clinically important mutations can shift which state the protein favors.
>
> StateBind tests a simple hypothesis: if you know which states matter for a given mutation, and you design molecules against those states specifically, do you get computationally better candidates than the standard single-structure approach?
>
> I built this as a modular pipeline in Python. It starts by curating 18 EGFR resistance mutations — T790M, C797S, L858R — with annotations about which conformational states each mutation favors. Then it classifies 16 PDB structures into 4 conformational states, defines state-specific binding pockets, and generates candidate molecules conditioned on each pocket's geometry. Finally, it scores everything with a unified scoring function and compares state-aware candidates to the static baseline on diversity, novelty, and ranking metrics.
>
> The pipeline is config-driven, tested (359 tests), and fully reproducible. The state-aware pipeline discovered 49 novel candidates inaccessible to the static approach, with higher chemical diversity. The docking component is currently a stub — binding affinity claims require future integration of Vina or GNINA. I designed it as a real computational experiment, not a demo."

---

## 5-Minute Technical Explanation

> "Let me walk through the system architecture and the science behind it.
>
> **The biological problem:** EGFR is a receptor tyrosine kinase and one of the most targeted proteins in oncology. Three generations of inhibitors exist, and resistance mutations keep emerging. The key insight from structural biology is that these mutations don't just change the binding site — they change which conformational state the kinase prefers. T790M stabilizes the active DFG-in state. L858R destabilizes the inactive state. C797S eliminates the covalent binding site. If you're designing a molecule against the wrong state, you're solving the wrong problem.
>
> **The pipeline has five modules:**
>
> 1. **Context module** — curates 18 EGFR mutations with resistance mechanism annotations and known conformational effects. Data from COSMIC, ClinVar, and published structural studies.
>
> 2. **Structure module** — classifies 16 EGFR kinase domain structures from PDB into four canonical states: DFG-in/out crossed with αC-helix-in/out. Classification uses literature-curated 9-dimensional structural feature vectors. Each state gets a representative structure and a pocket descriptor.
>
> 3. **Dynamics module** — models state-transition dynamics using a Markov model fitted to 16 literature-curated conformational pathways. Learns 4-D contrastive embeddings where distance correlates with transition rarity (r = −0.91).
>
> 4. **Generation module** — generates candidate molecules conditioned on pocket geometry. The static baseline uses one structure and simple analogs. The state-aware pipeline uses 4 structures × 7 strategies (hinge optimization, back-pocket extension, etc.). Same scoring, different generation — this is the controlled variable.
>
> 5. **Ranking module** — scores all candidates with an identical unified function (reference similarity, druglikeness, docking proxy stub, state specificity). Compares pipelines on diversity, novelty, score distributions, and top-K composition. Docking is a stub (constant 0.5) — real docking integration is planned future work.
>
> **Engineering choices:** src/ layout, Pydantic models, YAML configs, no hard-coded paths. Every module has typed inputs and outputs. Artifacts are serialized to disk between modules, so any module can be re-run independently. 359 tests across 13 modules.
>
> **What makes this rigorous:** The baseline is built and scored before the state-aware pipeline runs. Both pipelines are scored with the same function. The docking stub is labeled, not hidden. The result — a qualified advantage driven by structural novelty, not by scoring on shared chemistry — is reported with honest limitations."

---

## Narrative Principles

1. **Lead with the question, not the answer.** "Does state-awareness help?" is more compelling than "State-awareness helps."
2. **Demonstrate engineering through structure, not volume.** A clean 2,000-line codebase with tests beats a messy 10,000-line codebase.
3. **Be explicit about what you didn't do.** Acknowledging limitations demonstrates scientific maturity.
4. **Frame the null result as acceptable.** "We tested a hypothesis and reported the result" is always valid.
5. **Never claim biological activity from docking scores.** This is the fastest way to lose credibility.

---

## README Hero Image

The ideal README hero image is a single figure with 3-4 panels:

1. **Panel A:** EGFR conformational state atlas — small multiples showing superimposed structures colored by state (DFG-in = blue, DFG-out = red, etc.)
2. **Panel B:** State prediction — a heatmap of mutation × state relevance (rows = mutations, columns = states, color = predicted relevance)
3. **Panel C:** Score comparison — violin or box plot comparing docking score distributions for state-aware vs. baseline
4. **Panel D:** Cross-state selectivity — radar or bar chart showing a state-aware candidate's scores across all states

**Tools for figure generation:** matplotlib + seaborn for panels B/C/D. PyMOL or NGLview for panel A (structural visualization). All figure generation code should be in a notebook under `notebooks/`.

---

## Figures That Should Exist by Project End

| Figure | Purpose | Where it appears |
|--------|---------|-----------------|
| Conformational state atlas visualization | Show the structural diversity of EGFR states | README, report |
| Mutation annotation table | Show curated mutation data | Report |
| State classification scatter plot | DFG distance vs. αC-helix metric, colored by assigned state | Report, README |
| Score distribution comparison (ASCII bar chart) | Primary result figure: state-aware vs. baseline | README, report |
| Novelty breakdown by strategy | Novel candidates by generation strategy | Report |
| Pipeline diagram | System architecture | README |
| Generation diversity scatter (UMAP/PCA of fingerprints) | Show chemical diversity of candidates | Report |

---

## What NOT to Put in the Public Story

- "AI-powered drug discovery" — this is not that
- "Novel" — the individual components are established; the contribution is the integration and benchmark
- "Superior" without qualification — always say "computationally better-scoring" and note limitations
- Protein structure visualizations generated by AI tools without attribution
- Uncontextualized docking scores (always compare to baseline, always note limitations)
