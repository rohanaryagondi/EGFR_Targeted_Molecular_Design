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
> I built this as a modular pipeline in Python. It starts by curating EGFR resistance mutations — T790M, C797S, L858R — with annotations about which conformational states each mutation favors. Then it classifies 30+ PDB structures by conformational state, extracts binding pockets per state, and generates candidate molecules against state-specific pockets. Finally, it scores everything with docking and compares state-aware candidates to the static baseline using proper statistical tests.
>
> The pipeline is config-driven, tested, and fully reproducible. Whether state-awareness helps or not, the answer is documented with effect sizes and honest limitations. I designed it as a real computational experiment, not a demo."

---

## 5-Minute Technical Explanation

> "Let me walk through the system architecture and the science behind it.
>
> **The biological problem:** EGFR is a receptor tyrosine kinase and one of the most targeted proteins in oncology. Three generations of inhibitors exist, and resistance mutations keep emerging. The key insight from structural biology is that these mutations don't just change the binding site — they change which conformational state the kinase prefers. T790M stabilizes the active DFG-in state. L858R destabilizes the inactive state. C797S eliminates the covalent binding site. If you're designing a molecule against the wrong state, you're solving the wrong problem.
>
> **The pipeline has five modules:**
>
> 1. **Context module** — curates 15-30 EGFR mutations with resistance mechanism annotations and known conformational effects. Data from COSMIC, ClinVar, and published structural studies.
>
> 2. **Structure module** — downloads and classifies EGFR kinase domain structures from PDB into four canonical states: DFG-in/out crossed with αC-helix-in/out. Classification uses geometric criteria — Asp-Phe Cα distance for DFG, and Lys-Glu salt bridge distance for αC-helix. Each state gets a representative structure and an extracted binding pocket.
>
> 3. **Dynamics module** — predicts which states are most relevant for a given mutation. The baseline is a curated lookup table from literature. If data supports it, I train a simple classifier on mutation-state co-occurrence from PDB metadata.
>
> 4. **Generation module** — generates candidate molecules conditioned on pocket geometry. Two parallel tracks run: state-aware (pocket from predicted state) and baseline (pocket from single best-resolution structure). Same generation method, different pockets. This is the controlled variable.
>
> 5. **Ranking module** — docks all candidates against all state pockets using Vina. Compares state-aware vs. baseline using Mann-Whitney U with effect sizes. Also measures cross-state selectivity — do state-aware candidates preferentially score well on their intended state?
>
> **Engineering choices:** src/ layout, Pydantic models, YAML configs, no hard-coded paths. Every module has typed inputs and outputs. Artifacts are serialized to disk between modules, so any module can be re-run independently. Tests cover imports, project structure, utilities, and the CLI.
>
> **What makes this rigorous:** The baseline is defined before the experiment runs. The statistical test is specified in advance. I report effect sizes, not just p-values. And I'm explicit that docking scores are proxy metrics — this is a computational hypothesis, not a drug discovery claim. If state-awareness doesn't help, I'll report that too."

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
| Docking score comparison (violin plot) | Primary result figure: state-aware vs. baseline | README, report |
| Cross-state selectivity comparison | Secondary result: selectivity of state-aware vs. baseline candidates | Report |
| Pipeline diagram | System architecture | README |
| Generation diversity scatter (UMAP/PCA of fingerprints) | Show chemical diversity of candidates | Report |

---

## What NOT to Put in the Public Story

- "AI-powered drug discovery" — this is not that
- "Novel" — the individual components are established; the contribution is the integration and benchmark
- "Superior" without qualification — always say "computationally better-scoring" and note limitations
- Protein structure visualizations generated by AI tools without attribution
- Uncontextualized docking scores (always compare to baseline, always note limitations)
