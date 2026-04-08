# Visionary AI -- Running Log

## Status

- **Last session:** Session 2 -- 2026-04-08
- **Total ideas proposed:** 12
- **Deep research agents designed:** 3
- **Last updated:** 2026-04-08

---

## Sessions

### Session 1 -- 2026-03-30

#### Ideas Proposed

- 001: Continuous Conformational Conditioning via Protein Language Models -- Replace discrete 4-state model with ESM-2 continuous embeddings for VAE conditioning (P0)
- 002: 3D Pocket-Conditioned Diffusion Model -- Replace SMILES VAE with DiffSBDD-style 3D generation directly in the binding pocket (P1)
- 003: Kinome-Wide Selectivity Panel -- Add multi-kinase selectivity scoring against 10-20 off-target kinases (P0)
- 004: Ensemble Uncertainty and Active Learning Loop -- Train model ensembles for uncertainty, use for iterative candidate improvement (P1)
- 005: GNINA Integration for Physics-Informed Docking -- Add real molecular docking with binding poses via GNINA (P1)
- 006: Learned Chemical Similarity from Activity Cliffs -- Replace 3-molecule Tanimoto with contrastive learned metric on thousands of EGFR actives (P1)
- 007: Retrosynthetic Feasibility Gate -- Assess synthesis routes for top candidates via retrosynthesis API or model (P2)
- 008: Pareto Multi-Objective Optimization -- Replace weighted-sum scoring with Pareto front and hypervolume comparison (P1)
- 009: Retrospective Time-Split Validation -- Validate pipeline by predicting post-2015 EGFR drugs from pre-2015 data only (P0)
- 010: Self-Supervised Pre-Training for GNN Backbone -- Pre-train graph encoder on millions of molecules before fine-tuning on EGFR (P1)
- 011: Water Thermodynamics and Solvation Analysis -- Map pocket water networks per state and score candidates by water displacement (P2)
- 012: Reinforcement Learning for State-Conditioned Molecular Optimization -- RL layer on top of VAE to optimize latent space navigation toward high-scoring state-specific molecules (P2)

#### Themes Explored

1. **Strengthening the central hypothesis** (Ideas 001, 005, 008, 009) -- The 4-state discretization, lack of physics-based docking, arbitrary scoring weights, and absence of validation all weaken the central claim. These ideas directly address the foundations of the state-aware vs static comparison.

2. **Upgrading the scoring function** (Ideas 003, 005, 006, 008) -- Three of the four scoring components have fundamental weaknesses: similarity uses only 3 references, docking is a toy proxy, and weights are arbitrary. These ideas upgrade each component individually and collectively.

3. **Next-generation molecular generation** (Ideas 002, 012) -- Moving beyond SMILES-based generation to 3D-aware design and optimization-driven generation. These are the most ambitious ideas and would place StateBind at the ML frontier.

4. **Practical drug design credibility** (Ideas 003, 007, 011) -- Selectivity, synthesis feasibility, and solvation are what practitioners expect. These ideas bridge the gap between academic pipeline and actionable drug design tool.

5. **ML best practices for small data** (Ideas 004, 010) -- Pre-training and ensemble uncertainty are standard best practices that the project currently lacks. These are the lowest-risk, highest-return ML improvements.

6. **Validation without wet lab** (Idea 009) -- The retrospective time-split is the most creative validation strategy available. It addresses the #1 peer reviewer concern without any experimental work.

#### Briefing Gaps Noticed

1. **ChEMBL EGFR active compound count.** Several ideas (003, 006, 009, 010) depend on the volume of EGFR data in ChEMBL. The briefings mention 1,678 compounds for MPNN training but do not specify the total EGFR active count. Need the Assistant AI to query ChEMBL for: total EGFR compounds (any activity), EGFR actives (pIC50 >= 6.0), and EGFR compounds with deposition dates for time-split analysis.

2. **PDB structure count and resolution per state.** Ideas 005 and 011 need to know: how many PDB structures per conformational state? What is their resolution? Do they include crystallographic waters? The briefings mention 16 PDB structures total but not per-state distribution or resolution.

3. **Existing pre-trained molecular models.** Idea 010 would benefit from knowing which pre-trained GNN checkpoints are available (GEM, MolCLR, GraphMVP, etc.) and whether they are architecturally compatible with the existing MPNN (NNConv-based). The briefings describe the MPNN architecture but do not survey the pre-trained model landscape.

4. **GNINA availability and throughput.** Idea 005 depends on GNINA being installable and fast enough. The briefings do not mention any existing docking infrastructure or conda environment constraints.

5. **Multi-kinase bioactivity data availability.** Idea 003 needs ChEMBL bioactivity data for 10-20 kinases. The briefings focus exclusively on EGFR. A brief survey of kinase data volume per target would help scope the selectivity panel idea.

#### Reflections

**What felt high-impact:**
- Ideas 001 (continuous conformational conditioning) and 009 (retrospective validation) feel like the two most transformative proposals. 001 redefines the scientific hypothesis; 009 provides validation. Together they could make the project publishable.
- Idea 003 (selectivity panel) is the most important practical improvement. Without selectivity, the pipeline is not a drug design tool.
- Idea 005 (GNINA) is the highest-return investment for the docking component. It activates 20% of scoring weight with real physics.

**What felt like diminishing returns:**
- Idea 011 (water thermodynamics) is intellectually exciting but may be too specialized for the current project scope. It requires extensive structural biology expertise and the payoff is uncertain until the more fundamental scoring issues are fixed.
- Idea 002 (3D diffusion) is the most ambitious idea and would be transformative, but the effort is Epic-scale and depends on many prerequisites.

**Priority ordering for the Head AI:**
1. **Tier 1 (do first):** 009 (validation), 001 (continuous conditioning), 003 (selectivity)
2. **Tier 2 (do next):** 005 (GNINA), 006 (learned similarity), 010 (pre-training), 004 (uncertainty)
3. **Tier 3 (do when foundation is solid):** 008 (Pareto), 012 (RL), 007 (retrosynthesis)
4. **Tier 4 (aspirational):** 002 (3D diffusion), 011 (water thermodynamics)

**What to explore next session:**
- Protein-ligand interaction fingerprints (mentioned in `known-limitations.md` Section 4.2 but not addressed in any idea)
- Comparison benchmarking against published generative models (REINVENT, GraphAF, MolGPT) -- the peer reviewer concern about missing SOTA comparisons
- Federated or multi-site learning across kinase targets
- IP/patent freedom-to-operate analysis mentioned in practitioner critique

---

### Session 2 -- 2026-04-08

#### Mission

User wants StateBind to become publication-worthy at a top venue (Nature Computational
Science, JCIM, or similar). Designed a Gemini Deep Research strategy to survey the
full landscape of techniques, data, and ML approaches that would elevate the project.

#### Deep Research Agents Designed

3 Gemini Deep Research agents, each with a self-contained briefing doc in `vision/DeepResearch/`:

1. **Agent 1: Techniques & Methods** (`techniques-and-methods.md`)
   - 10 research questions covering: 3D structure-based generation, conformational ensemble methods, physics-informed affinity, multi-objective optimization, active learning, uncertainty quantification, selectivity scoring, retrosynthetic analysis, protein-ligand interaction fingerprints, water/solvation modeling
   - Addresses deferred ideas: 001, 002, 003, 004, 007, 011, 012

2. **Agent 2: Data & Validation** (`data-and-validation.md`)
   - 10 research questions covering: KLIFS database, multi-kinase PDB/ChEMBL data, approved drug timelines, benchmark datasets, validation methodologies, clinical outcome data, selectivity datasets, conformational state databases, expansion target ranking
   - Addresses the generalizability problem (EGFR-only) and small validation sample (3-5 drugs)
   - Critical for publication: need >=3 additional kinase targets with sufficient data

3. **Agent 3: Foundation Models & Benchmarks** (`foundation-models-and-benchmarks.md`)
   - 10 research questions covering: pre-trained molecular representations, protein language models, protein-ligand co-representations, SOTA generative models, published benchmarks, self-supervised pre-training, transfer learning, multi-task learning, integration patterns, computational requirements
   - Addresses deferred ideas: 001, 006, 010 and the "no SOTA comparison" reviewer concern

#### Key Strategic Insights

1. **The 10x enrichment is the publication anchor.** Everything should amplify and validate this finding. Multi-kinase replication is the highest-priority expansion.

2. **Three pillars for top-venue publication:**
   - Generalizability (works across kinase families, not just EGFR)
   - Technical sophistication (foundation models, 3D awareness, uncertainty)
   - Rigorous benchmarking (comparison against published SOTA methods)

3. **The scoring function tension is the paper's intellectual contribution.** Static wins on mean score but loses on enrichment. This reveals that weighted-sum similarity scoring and enrichment measure fundamentally different things. A paper that formalizes this insight -- and shows it generalizes across kinases -- is genuinely novel.

4. **Foundation model integration is the fastest path to ML novelty.** Replacing one-hot state conditioning with ESM-2 conformational embeddings (idea 001) + replacing scratch GNN with pre-trained backbone (idea 010) are architecturally simple but dramatically more sophisticated. The combination is publishable.

#### Briefing Observations (Session 3 briefings, updated 2026-04-07)

- All 12 workstreams complete (up from 10 at session 1 briefing)
- 3 of my session-1 ideas were accepted and implemented: 005 (GNINA), 008 (Pareto), 009 (retrospective)
- Retrospective validation result (10x enrichment) is the strongest finding in the project
- Remaining 9 ideas still deferred -- the deep research agents will provide evidence to prioritize them
- 7 remaining gaps identified in briefings, all addressable by the deep research strategy

#### Reflections

**What felt right:**
- Splitting by techniques / data / ML is clean and non-overlapping
- Each doc is self-contained -- Gemini reads only its file, no repo exploration needed
- The data agent is arguably the most important: multi-kinase expansion is the #1 path to publication
- 10 questions per agent is enough for depth without overwhelming

**What I'm uncertain about:**
- Whether Gemini Deep Research will find specific enough data (exact ChEMBL compound counts per kinase per state) vs general survey-level answers
- Whether the foundation model landscape moves too fast -- some models in my list may already be superseded
- Whether we should add a 4th agent focused specifically on publication strategy (target journals, reviewer expectations, impact metrics). Deferred for now; can run separately.

**What to explore in session 3:**
- Results from all 3 Gemini Deep Research agents -- synthesize into concrete expansion plan
- Prioritize deferred ideas based on deep research findings
- Design new workstreams (WS14+) for the highest-impact expansions
- Consider a 4th deep research agent for publication strategy if needed

---

## Current State

**What is done:** 12 ideas from session 1 (3 accepted/implemented, 9 deferred). 3 Gemini Deep Research briefing docs written and pushed to GitHub. Awaiting Gemini agent runs.

**Next steps:**
1. User runs 3 Gemini Deep Research agents with provided prompts
2. Visionary reviews Gemini outputs and synthesizes into expansion plan
3. Propose new workstreams (WS14+) based on deep research findings
4. Design publication narrative and target venues

---

## Context Recovery

If your context compacts:
1. Re-read this log
2. Re-read all briefings in `vision/briefings/`
3. Re-read your existing ideas in `vision/ideas/`
4. Resume from "Next steps" above
