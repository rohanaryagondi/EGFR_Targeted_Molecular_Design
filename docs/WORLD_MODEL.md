# World Model: EGFR Conformational State Dynamics

## What Is Being Modeled

The world model captures **relationships and transition probabilities between
EGFR conformational states**. Given a current conformational state (e.g.,
DFGin_aCin / active), the model predicts:

1. Which other states the kinase might transition to
2. How likely each transition is
3. What the equilibrium distribution over states looks like
4. How states relate to each other in a learned embedding space

This is a **compact state-transition model**, not a molecular dynamics
simulation. It encodes expert knowledge from the structural biology literature
into a quantitative, queryable format.

## What Is Real vs Approximated

### Real (from literature)
- **State identities**: DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout
  are well-established EGFR conformational states (KLIFS, Ruan & Bhatt 2012)
- **Transition existence**: Active ↔ Src-like and DFG-in ↔ DFG-out transitions
  are experimentally documented via crystallography and NMR
- **Activation pathways**: The routes from inactive to active conformation are
  supported by computational studies (Shan et al. 2013, Sutto & Bhatt 2014)
- **Drug-induced effects**: Type-I/II inhibitor conformational selection is
  established pharmacology

### Approximated (v1 limitations)
- **Transition probabilities**: Estimated from transition counts in curated
  sequences, not from free energy calculations or kinetic measurements
- **Transition rates**: Not modeled. The Markov model gives P(next | current)
  but not how fast transitions occur
- **Pathway intermediates**: Transitions are treated as single steps; actual
  DFG flip involves intermediate conformations not in our 4-state model
- **Mutation-specific dynamics**: The transition matrix is global, not
  conditioned on mutation identity. T790M and WT share the same matrix
- **Sequence construction**: Pseudo-trajectories are assembled from literature
  knowledge, not extracted from MD simulations

## Why This Still Adds Value

1. **Enables multi-state design strategies.** Without the world model,
   molecular design targets a single structure. With it, we can design
   molecules that account for state accessibility: "this mutation spends
   most time in the active state, but occasionally visits Src-like inactive."

2. **Provides transition-aware scoring.** A molecule that binds DFGout_aCout
   is less useful if the target rarely visits that state. The stationary
   distribution weights state relevance.

3. **Defines state relationships for embedding-based models.** The learned
   embeddings encode "kinase dynamics distance" — which states are close
   in transition space vs geometric space. These embeddings feed directly
   into state-conditioned molecular generation.

4. **Makes assumptions explicit.** Rather than implicitly assuming a single
   static structure, the world model forces documentation of which states
   matter, how often, and why.

## Downstream Consumption

### Phase 6 (State-Conditioned Generation) will use:
- **Transition probabilities** to weight multi-state design objectives
- **State embeddings** as conditioning vectors for generative models
- **Stationary distribution** to prioritize design against frequently-occupied states

### Phase 7 (Ranking) will use:
- **Transition accessibility** to penalize molecules targeting inaccessible states
- **Embedding distances** in scoring functions

## Upgrade Paths

1. **MD-derived transitions**: Replace curated sequences with actual MD
   trajectory state assignments for accurate transition probabilities
2. **Mutation-conditioned Markov model**: Separate transition matrices per
   mutation (requires more data per mutation)
3. **Hidden Markov Model**: Model intermediate states not directly observable
4. **Kinetic rates**: Replace probabilities with time-resolved rate constants
   from enhanced sampling simulations
5. **Ligand-conditioned dynamics**: How drug binding alters the transition landscape
