# 012: Reinforcement Learning for State-Conditioned Molecular Optimization

**Category:** Novel Approaches, ML Improvements
**Priority:** P2: Medium
**Status:** deferred
**Date proposed:** 2026-03-30
**Effort:** Large (2-4 weeks)

## Summary

Add a reinforcement learning (RL) layer on top of the VAE that optimizes the latent space navigation toward high-scoring molecules for each conformational state. Instead of random sampling from the VAE latent space (which produces diverse but unoptimized molecules), use policy gradient methods to learn which regions of latent space produce molecules that score highly on the unified scoring function. This creates a closed-loop design cycle where the generator learns to produce increasingly better molecules for specific conformational states -- the generation step becomes an optimization, not just a sampling procedure.

## The Problem

Per `known-limitations.md` (Section 3.5), the pipeline is one-shot: generate, score, rank, done. Per `known-limitations.md` (Section 4.3), the current generation is string modification (not de novo design) and even the VAE will sample from latent space without optimization -- it produces diverse molecules but has no feedback mechanism to produce better ones.

The VAE, once trained, learns a generative distribution P(molecule | state). Sampling from this distribution produces valid molecules for a given state, but there is no guarantee these molecules are high-scoring. The scoring function exists independently of the generator. There is no gradient flowing from the scoring function back to the generation process. This means the pipeline cannot answer: "Given a specific conformational state, what is the highest-scoring molecule you can generate for it?"

## The Vision

After this improvement:

- **Targeted generation.** Instead of "sample 100 random molecules for DFGout/aCout," the system generates molecules specifically optimized for high unified scores in that state. The RL policy navigates the latent space toward high-reward regions.
- **Multi-objective RL reward.** The reward signal combines unified scoring components (or Pareto dominance from Idea 008). The RL agent learns to balance affinity, drug-likeness, and state specificity simultaneously.
- **State-specific optimization profiles.** The RL policy learns different strategies for different states -- one state might reward compact molecules (small pocket), while another rewards extended scaffolds (large pocket). This demonstrates that conformational state awareness genuinely changes the design strategy.
- **Iterative improvement.** Each RL episode generates, scores, and learns. Over hundreds of episodes, the generated molecules converge toward optimal regions of chemical space for each state.

## Impact Assessment

**Significant.** RL-guided molecular generation is an active research area (REINVENT, GCPN, MolDQN) with strong results. Applying it in a state-conditioned setting would be novel -- most RL molecular generators optimize for a single target, not for conformational state specificity. The combination of VAE + RL + state conditioning + multi-objective reward is a genuinely novel architecture that could be a standalone publication.

Affects: generation module (RL wrapper), candidate quality (optimized vs random), evaluation (before/after RL comparison), the scientific narrative (from "we sampled candidates" to "we optimized candidates for each state").

## Effort Estimate

Large. RL for molecular generation requires careful reward shaping, training stability management, and significant experimentation with hyperparameters. The REINVENT framework (open-source, from AstraZeneca) provides a reference implementation but would need adaptation for state conditioning. 2-4 weeks.

## Dependencies

- Trained VAE (must have a working generator before adding RL on top)
- Trained MPNN (for docking component of reward, otherwise reward uses proxy)
- Scoring function (as the RL reward signal)
- PyTorch (for policy gradient implementation)
- Significant GPU time (RL training: ~100-500 episodes, each generating ~100 molecules)

## Implementation Sketch

1. **RL framework: new `ml/rl_generator.py`** -- Wraps the VAE with an RL policy. Architecture:
   - **State:** conformational state embedding + current generation statistics
   - **Action:** latent vector z (sampled or perturbed from prior)
   - **Reward:** unified scoring function output for the generated molecule. Bonus for validity, diversity (reward shaping to avoid mode collapse).
   - **Policy:** REINFORCE with baseline, or PPO for better stability. The policy modifies the VAE's sampling distribution by learning a conditional prior p(z | state, policy_params).

2. **Reward design: new `ml/rl_reward.py`** -- Multi-component reward:
   ```
   reward = w1 * affinity_score
          + w2 * druglikeness_score
          + w3 * state_specificity_score
          + w4 * novelty_bonus           # reward for molecules unlike training set
          - w5 * similarity_penalty      # penalty for generating duplicates
          + w6 * validity_bonus          # reward for chemically valid SMILES
   ```
   Alternatively, use the Pareto dominance ranking (from Idea 008) as the reward.

3. **Training loop: `scripts/train_rl_generator.py`** -- For each conformational state:
   ```
   for episode in range(num_episodes):
       z = policy.sample_latent(state_embedding)
       smiles = vae.decode(z, state_embedding)
       reward = score_unified(smiles, state)
       policy.update(z, reward)
   ```
   Save the best molecules per state. Monitor: average reward per episode, validity rate, diversity (Tanimoto similarity within generated set), mode collapse detection.

4. **Integration with generation pipeline: modify `generation/generator.py`** -- Add `RLGenerator` strategy alongside existing string modification and VAE strategies. The RL generator produces pre-optimized candidates that are already high-scoring by construction.

5. **Evaluation: `evaluation/rl_analysis.py`** -- Compare: (a) random VAE sampling vs RL-guided sampling for each state. (b) RL-generated state-aware candidates vs static baseline. (c) Learning curves showing reward improvement over training.

6. **Testing** -- Verify RL training converges (reward increases over episodes). Verify generated molecules are valid and diverse (not mode-collapsed). Compare RL-generated vs random-sampled candidates under the same scoring function.

## Open Questions

- REINFORCE vs PPO vs other policy gradient methods? REINFORCE is simpler but has high variance. PPO is more stable but more complex. REINVENT (AstraZeneca) uses REINFORCE with experience replay.
- How to prevent mode collapse (RL converges to generating the same molecule repeatedly)? Diversity rewards, experience replay, or entropy bonus in the policy loss.
- Should RL operate in the VAE latent space (modify z) or in the token space (modify decoder probabilities)? Latent space RL is more principled; token-space RL (as in REINVENT) is more practical.
- What is the right balance between exploitation (high reward) and exploration (diverse candidates)? This is the fundamental RL trade-off and needs careful tuning.
- How does this interact with the active learning loop (Idea 004)? RL generates optimized candidates; active learning identifies which to investigate further. They are complementary but the interaction needs design.
