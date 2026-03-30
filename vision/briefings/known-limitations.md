# Known Limitations

**Last updated:** 2026-03-30T00:00:00+00:00
**Briefing session:** 1 (first briefing)

---

Every limitation below is real. Each one is followed by an **opportunity signal** —
what fixing it would unlock for the project.

---

## 1. Scoring Limitations

### 1.1 Docking proxy is a toy model, not a binding predictor

The docking component (20% of the unified score) is currently served by a lightweight
MLP trained on 9 known EGFR binders and 25 non-EGFR decoys. This is not a docking
score — it is a binary classifier that learned to separate a tiny set of known
molecules from known non-molecules. It has never seen a novel candidate structurally
different from its training set. When the MLP encounters a truly novel molecule, its
prediction is essentially random.

The MPNN affinity predictor is designed to replace this, but it is untrained. Even when
trained, it will predict pIC50 from molecular graphs — still a learned proxy, not a
physics-based binding calculation.

> **Opportunity:** Integrating real docking software (AutoDock Vina, GNINA, or Glide)
> would provide physically interpretable binding poses and energies, activate 20% of
> scoring weight with real discriminative power, and give the project a result that
> structural biologists and medicinal chemists would trust. Even a fast surrogate
> (GNINA's CNN scoring) would be a significant upgrade.

### 1.2 Reference similarity uses only 3 molecules

The reference similarity component (35% of the score — the heaviest weight) computes
Morgan fingerprint Tanimoto similarity against exactly 3 approved EGFR drugs:
erlotinib, gefitinib, and osimertinib. This is a severe bias: it rewards candidates
that look like existing drugs and penalizes structurally novel chemotypes that might
bind EGFR through different interactions.

> **Opportunity:** Expanding the reference set to include all known EGFR active
> compounds from ChEMBL (thousands of molecules with measured IC50 < 100 nM) would
> capture diverse binding modes. Alternatively, replacing Tanimoto similarity with a
> learned similarity metric (e.g., contrastive learning on activity data) would move
> beyond fingerprint matching entirely.

### 1.3 ADMET is a filter, not a scoring component

The ADMET predictor flags candidates with hERG liability or CYP3A4 inhibition, but it
does not contribute to the unified scoring function. A candidate with terrible predicted
ADMET properties can still score highly — it only gets flagged after ranking. Safety is
a post-hoc check, not an optimization objective.

> **Opportunity:** Adding ADMET as a 5th scoring component (or restructuring as a
> constrained optimization where ADMET thresholds are hard constraints rather than
> soft penalties) would make the ranking itself safety-aware. This is how modern drug
> design programs operate — they optimize affinity subject to ADMET constraints, not
> sequentially.

### 1.4 Scoring is a fixed weighted sum

The unified score is `0.35*similarity + 0.30*druglikeness + 0.20*docking + 0.15*state`.
This linear combination has two problems:

1. The weights are human-chosen, not optimized. There is no evidence that 0.35 is the
   right weight for reference similarity.
2. A linear sum allows compensation — a candidate with zero docking affinity but high
   similarity to erlotinib still scores well. There is no concept of "minimum threshold
   on each component."

> **Opportunity:** Multi-objective Pareto optimization would explore the trade-off
> surface between competing objectives without collapsing them to a single number.
> Alternatively, constrained optimization (maximize affinity subject to drug-likeness
> >= 0.5, SA <= 4.0, hERG < threshold) would prevent the compensation problem.

---

## 2. Scientific Limitations

### 2.1 No experimental validation at any level

Zero wet-lab data. No binding assays, no cell viability tests, no animal models, no
clinical data. Every score is a computational prediction. The project has never
confirmed that any generated candidate actually binds EGFR.

> **Opportunity:** Even a minimal experimental validation — testing 5-10 top candidates
> in a fluorescence polarization binding assay — would transform this from a purely
> computational exercise to a validated pipeline. If even 1 candidate shows binding,
> the state-aware hypothesis becomes experimentally supported.

### 2.2 Conformational states are discretized

The 4-state model (DFGin/out x aCin/out) treats kinase conformation as a categorical
variable. In reality, EGFR exists on a continuous conformational landscape with many
intermediate geometries. A molecule designed for "DFGout/aCout" might actually target a
state that is 70% DFGout and 30% DFGin — a state that does not exist in the 4-category
model.

> **Opportunity:** Replacing discrete states with a continuous conformational
> representation (e.g., principal components of the dihedral angle space from MD
> trajectories, or learned embeddings from a protein structure VAE) would capture the
> full conformational landscape. This would be genuinely novel — most state-aware
> approaches in the literature also use discrete states.

### 2.3 All 17 mutations map to one state

The curated dataset of 17 EGFR resistance mutations (T790M, C797S, L858R, etc.) all
map to the DFGin/aCin state in the context model. This means the mutation-to-state
prediction is uninformative — it cannot distinguish between mutations that should shift
state preference. The model correctly predicts one class for all inputs, but this is
vacuous.

> **Opportunity:** Incorporating MD simulations of mutant EGFR structures would reveal
> actual state preferences per mutation. Alternatively, pulling structures of mutant
> EGFR from the PDB (many exist for T790M and L858R) would provide direct structural
> evidence rather than relying on prediction.

### 2.4 No molecular dynamics

The pipeline uses static crystal structures. Crystal structures are single snapshots —
they do not capture protein flexibility, water-mediated interactions, or the
thermodynamic ensemble of bound states. A molecule that fits beautifully in the
crystal structure pocket may be expelled by protein motion in solution.

> **Opportunity:** Even short MD simulations (10-100 ns) for each conformational state
> would provide an ensemble of pocket geometries, enabling ensemble docking and a more
> realistic assessment of binding. Adaptive sampling or metadynamics could enhance
> exploration of rare states.

### 2.5 No selectivity analysis

The pipeline scores binding to EGFR only. It does not check whether candidates also
bind kinases with similar ATP-binding pockets (ABL, BRAF, ALK, SRC, etc.). A molecule
that binds every kinase equally is not a useful drug — it would cause severe side
effects.

> **Opportunity:** Adding a selectivity component (either a multi-target MPNN trained
> on data from multiple kinases, or a structural comparison of binding pockets across
> the kinome) would enable designing molecules that are EGFR-specific. This is a major
> differentiator — most generative pipelines optimize for a single target without
> considering selectivity.

---

## 3. ML Limitations

### 3.1 No pre-training on large chemical databases

The MPNN and ADMET models will be trained from scratch on relatively small datasets
(1,678 compounds for MPNN, TDC benchmarks for ADMET). Modern molecular property
prediction benefits enormously from pre-training on millions of compounds (e.g.,
self-supervised pre-training on ChEMBL, PubChem, or ZINC) followed by fine-tuning on
the target task.

> **Opportunity:** Pre-training the graph encoder on a large self-supervised task (e.g.,
> masked atom prediction, contrastive learning on augmented molecular graphs) before
> fine-tuning on EGFR affinity data could significantly improve MPNN generalization.
> Existing pre-trained molecular encoders (GEM, MolBERT, ChemBERTa) could also be
> leveraged as feature extractors.

### 3.2 No external validation sets

All models will be evaluated on random train/val/test splits of the same dataset.
There is no external test set from a different source, time period, or experimental
protocol. This means performance estimates may be optimistically biased.

> **Opportunity:** Holding out an external test set (e.g., compounds published after a
> cutoff date, or data from a different lab/assay protocol) would give a more honest
> estimate of real-world performance. For ADMET, the TDC leaderboard provides
> standardized external benchmarks.

### 3.3 No uncertainty quantification

All models produce point predictions. The MPNN predicts pIC50 = 6.3, but how confident
is it? Is 6.3 a well-supported prediction based on many similar training examples, or
a wild extrapolation? Without uncertainty estimates, the pipeline cannot distinguish
between high-confidence and low-confidence predictions.

> **Opportunity:** Ensembles (training 5-10 models with different seeds), Monte Carlo
> dropout, or evidential deep learning would provide prediction intervals. This enables
> risk-aware ranking: rank candidates not just by predicted affinity but by
> confidence-adjusted affinity. It also enables active learning — selecting the most
> uncertain candidates for experimental testing.

### 3.4 VAE generates SMILES strings, not 3D structures

The conditional VAE generates SMILES (1D text representations of molecules). SMILES
encodes connectivity but not 3D geometry. Two molecules with similar SMILES can have
very different 3D binding poses. The VAE has no concept of how the molecule fits in
the EGFR pocket — it only knows that certain SMILES patterns are associated with
active EGFR compounds.

> **Opportunity:** 3D-aware generative models (e.g., diffusion models that generate
> atom coordinates directly in the binding pocket, or equivariant graph neural networks
> that generate molecular graphs in 3D space) would produce candidates that are
> structurally optimized for binding. This is a frontier area — models like DiffSBDD,
> Pocket2Mol, and TargetDiff show promising results.

### 3.5 No active learning or iterative refinement

The pipeline is one-shot: generate candidates → score → rank → done. There is no
mechanism to learn from scoring results and generate better candidates in the next
round.

> **Opportunity:** An active learning loop (generate → score → identify most
> informative/promising candidates → retrain generator → generate again) would
> iteratively improve both the model and the candidate pool. Bayesian optimization
> over the latent space of the VAE would be a natural fit.

---

## 4. Pipeline Limitations

### 4.1 No retrosynthetic analysis

The pipeline generates molecular structures but never checks whether they can be
synthesized. The SA (synthetic accessibility) score is a rough heuristic — it estimates
synthesis difficulty on a 1-10 scale based on fragment frequencies, but it does not
propose actual synthesis routes. A molecule with SA = 3.0 (seemingly easy) might
require reagents that do not exist or reactions that have never been demonstrated.

> **Opportunity:** Integrating a retrosynthetic planning tool (ASKCOS, IBM RXN, or a
> learned retrosynthesis model) would filter candidates by actual synthesizability and
> provide proposed routes. This converts computational candidates into actionable
> synthesis targets — the step that bridges computation and the wet lab.

### 4.2 No protein-ligand interaction fingerprints

The scoring function evaluates molecules in isolation — it computes molecular
properties and similarity to known binders, but it never explicitly models how the
molecule interacts with the EGFR protein. Interaction fingerprints (hydrogen bonds,
hydrophobic contacts, pi-stacking, salt bridges) capture the binding mode, not just
the molecule's shape.

> **Opportunity:** Adding interaction fingerprint analysis (e.g., PLIF from docking
> poses, or predicted contacts from a structure-aware model) would enable scoring
> candidates by how they interact with the pocket, not just what they look like.
> State-specific interaction patterns could be a powerful discriminator.

### 4.3 Candidate generation is string modification, not de novo design

The current 49 state-aware candidates and 30 static candidates are produced by
string-level SMILES modifications (substitutions, insertions, deletions on SMILES
text). This is not true molecular design — it is text manipulation that happens to
produce valid SMILES. The structural diversity is limited by the starting molecules.

> **Opportunity:** The VAE, once trained, will produce genuinely novel molecules from
> latent space sampling. Beyond that, reinforcement learning (optimize the generator
> toward high-scoring regions), genetic algorithms on molecular graphs, or 3D diffusion
> models would enable exploration of chemical space far beyond what string modification
> can reach.

### 4.4 No water or solvent modeling

The pipeline treats binding as a gas-phase interaction — molecule meets pocket in
vacuum. In reality, the binding pocket is solvated, and displacing water molecules is
a major thermodynamic driving force for binding (the hydrophobic effect). Water
networks in the pocket can form bridging interactions or create barriers.

> **Opportunity:** WaterMap-style analysis (identifying and scoring crystallographic
> water positions) or implicit solvent corrections to docking scores would add a
> critical thermodynamic dimension. Displaced high-energy waters correlate strongly
> with binding affinity.

---

## 5. What Peer Reviewers Would Attack

1. **"Where is the experimental validation?"** — Every result is computational. No
   binding assay, no cell assay, nothing. Reviewers will ask why top candidates were
   not tested.

2. **"Why only 3 reference molecules for 35% of the score?"** — The heaviest scoring
   component compares against 3 drugs. This biases toward known scaffolds and misses
   novel chemotypes.

3. **"Is 1,678 compounds enough to train a meaningful affinity predictor?"** — Modern
   molecular property prediction often uses 10,000-100,000+ compounds. 1,678 is small.

4. **"4 discrete states is a gross oversimplification."** — The conformational landscape
   is continuous. The discrete model misses intermediate states and transitions.

5. **"The state-aware advantage is only 15% of the score."** — If the improvement is
   small, reviewers will question whether 15% weight is enough to detect a real signal,
   or whether the entire comparison is underpowered.

6. **"No comparison to existing state-of-the-art generative models."** — The pipeline
   should benchmark against published molecular generation methods (REINVENT, GraphAF,
   GCPN, MolGPT) to contextualize its results.

---

## 6. What Drug Discovery Practitioners Would Find Naive

1. **No lead optimization cycle.** Real drug design is iterative: design → synthesize →
   test → redesign. This pipeline is one-shot.

2. **No ADME in scoring.** Safety should be a hard constraint, not a post-hoc filter.
   Experienced medicinal chemists screen for hERG and metabolic liabilities early.

3. **No consideration of intellectual property.** Generated molecules may infringe
   existing patents. Freedom-to-operate analysis is standard in pharma.

4. **No formulation or delivery considerations.** A molecule that binds perfectly but
   cannot be formulated for oral delivery is not a drug candidate.

5. **Pocket volume differences are stated but not exploited.** The briefing mentions
   pocket volumes from 450 to 850 cubic angstroms, but the generation strategy does not
   explicitly use pocket shape to constrain molecular size or geometry.
