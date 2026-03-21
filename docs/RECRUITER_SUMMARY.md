# Recruiter Summary: StateBind

## What Is This Project?

StateBind is a computational biology pipeline that tests whether knowing the 3D shape of a drug target helps you design better drug candidates. Most drug design software treats the target protein as frozen in one shape. But proteins move, and cancer mutations change which shapes they prefer. StateBind builds a system that designs different molecules for each shape and measures whether that approach beats the standard one.

The target is EGFR, a protein responsible for many lung cancers and the focus of three generations of targeted therapies.

---

## Skills Demonstrated

### Software Engineering
- **Modular architecture:** 10 Python submodules with typed interfaces (Pydantic v2), each independently testable
- **359 passing tests** across 13 test modules, covering schemas, pipelines, metrics, and figures
- **Config-driven design:** No hard-coded paths, YAML configuration, deterministic reproducibility
- **Clean packaging:** PEP 621 pyproject.toml, src/ layout, CLI entry point, optional dependency groups
- **33 runnable scripts** that produce reproducible artifacts from the same codebase

### Data Science / ML
- Feature engineering (33-dimensional mutation feature vectors)
- Three-tier model progression (nearest centroid → logistic regression → MLP)
- Markov transition models with contrastive embedding learning
- Ablation studies and honest reporting of single-class dataset limitations
- Unified scoring functions with explicit weight justification

### Computational Biology
- EGFR kinase domain conformational state classification
- Literature-curated structural features (DFG distance, αC-helix rotation, pocket volume)
- Pocket-conditioned molecular generation (type-I vs type-II inhibitor design)
- Resistance mutation mechanism mapping (T790M gatekeeper, C797S covalent site, L858R activation loop)

### Scientific Communication
- 7 phase reports with honest findings and stated limitations
- Comparison framework with defined fairness rules
- Explicit non-claims and conservative interpretation
- Findings framed as "qualified yes" rather than overclaimed results

---

## What Makes This Project Unusual

1. **It tests a hypothesis, not just implements a tool.** The pipeline is designed around one question with a measurable answer.
2. **The null result is acceptable.** The project reports limitations alongside results, treating "static is sufficient" as a valid outcome.
3. **It has a real baseline.** The static pipeline is implemented first, scored with the same function, and compared fairly.
4. **The documentation is stronger than most production codebases.** 17 docs files, 7 phase reports, architecture decisions, risk register, and a benchmark specification — all written before or during implementation.

---

## Resume-Ready Bullets

- Built a 7-phase computational biology pipeline (67 Python modules, 359 tests) that benchmarks conformational state-aware molecular design against a static single-structure baseline for EGFR-targeted drug discovery
- Designed a unified scoring framework that applies identical evaluation to both pipelines, producing a head-to-head comparison with overlap, diversity, rank-shift, and novelty analysis
- Implemented pocket-conditioned candidate generation across 4 EGFR conformational states, discovering 49 novel candidates (including type-II inhibitor scaffolds) inaccessible to the static baseline
- Created Markov state-transition models with contrastive embedding learning, achieving −0.91 correlation between embedding distance and transition frequency
- Engineered a modular, config-driven Python package (Pydantic v2, PEP 621, typed throughout) with deterministic reproducibility and no external API dependencies

---

## Interview Talking Points

**"Walk me through the project."**
> I built StateBind to test whether conformational state information improves computational molecular design. Kinase proteins like EGFR switch between active and inactive shapes, and mutations associated with drug resistance change which shape the protein prefers. I designed a pipeline that generates different drug candidates for each shape and compared the results against the standard approach of using just one shape. The state-aware pipeline found 49 novel candidates — particularly for the inactive conformations — that the static approach couldn't discover.

**"What was the hardest technical decision?"**
> Keeping the docking component as an honest stub rather than adding a noisy approximation. It would have been easy to add a heuristic and claim "docking-validated results," but that would misrepresent the evidence. The comparison framework is designed so real docking can be swapped in later without changing any other module.

**"What would you do with more time?"**
> Three things: (1) Replace the docking stub with AutoDock Vina, which would make the binding affinity comparison meaningful. (2) Add ECFP4 molecular fingerprints instead of SMILES n-grams for more accurate similarity scoring. (3) Expand to additional kinase families to test whether the state-aware advantage generalizes beyond EGFR.

**"What did you learn?"**
> That honest benchmarking is harder than building the pipeline. Defining what "outperforms" means before running the experiment, keeping the comparison fair, and reporting limitations alongside results required more careful thought than any individual module. The project also reinforced that modular design pays off — when I found a bug in Phase 5's evaluation script, I fixed it without touching any other phase.
