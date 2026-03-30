# 007: Retrosynthetic Feasibility Gate

**Category:** Pipeline Gaps
**Priority:** P2: Medium
**Status:** proposed
**Date proposed:** 2026-03-30
**Effort:** Medium (1-2 weeks)

## Summary

Add a retrosynthetic analysis step that evaluates whether generated candidates can actually be synthesized in a chemistry lab. The current SA (synthetic accessibility) score is a heuristic estimate; replace it with a learned retrosynthesis model that proposes actual synthesis routes. Candidates without feasible synthesis routes are deprioritized or filtered. This bridges the gap between computational design and experimental action -- the step that converts virtual molecules into real drug candidates.

## The Problem

Per `known-limitations.md` (Section 4.1), the pipeline generates molecular structures but never checks whether they can be synthesized. The SA score is a rough heuristic based on fragment frequencies -- it estimates synthesis difficulty on a 1-10 scale but does not propose actual routes. A molecule with SA = 3.0 ("easy") might require a reaction that has never been demonstrated or a reagent that does not exist commercially.

Per `known-limitations.md` (Section 6, point 1), drug discovery practitioners would find the lack of synthesis planning naive. In pharma, every computational candidate goes through a "Can we make it?" check before any resource is committed. No medicinal chemistry team would pursue a computationally promising molecule without seeing at least one plausible synthesis route.

## The Vision

After this improvement:

- **Every top-ranked candidate has a proposed synthesis route.** The retrosynthesis model decomposes the target molecule into available starting materials through a sequence of known reactions.
- **Synthesis feasibility becomes a scoring signal.** Candidates with short, high-confidence routes score higher than candidates requiring exotic reactions or many steps.
- **The evaluation report includes synthesis plans.** The final comparison shows not just score distributions but actionable synthesis targets -- molecules a chemist could make tomorrow.
- **A "synthesizability-weighted" ranking** where candidates are sorted by `score * synthesis_feasibility` gives the most practically useful output.

## Impact Assessment

**Moderate.** This does not change the scientific hypothesis test directly, but it transforms the practical value of the pipeline output. It addresses a major practitioner critique and would make the final candidate list actionable rather than theoretical. It also helps assess whether state-aware design produces more synthesizable molecules than static design -- a useful secondary finding.

Affects: candidate filtering, evaluation (synthesis analysis), practical utility of results.

## Effort Estimate

Medium. Two approaches: (1) Integrate an existing retrosynthesis API (ASKCOS, IBM RXN) -- fast to implement but requires internet access and API keys. (2) Train or adapt a single-step retrosynthesis model (e.g., Molecular Transformer) -- more self-contained but requires training data and GPU time. Option 1 is recommended for speed.

## Dependencies

- Top-ranked candidates (from ranking module)
- RDKit for SMILES manipulation and reaction template matching
- External: ASKCOS API or IBM RXN API (option 1) OR Molecular Transformer weights (option 2)
- Commercial reagent databases (optional, for starting material availability check)

## Implementation Sketch

1. **API wrapper: new `chemistry/retrosynthesis.py`** -- Wrapper around retrosynthesis service. Input: SMILES. Output: list of proposed routes, each with: reactions, reagents, estimated step count, confidence score. Supports multiple backends with fallback.

2. **Synthesis scoring: new function `_score_synthesis_feasibility()`** -- Normalize synthesis feasibility to [0, 1]. Factors: number of steps (fewer = better), maximum single-step confidence (higher = better), starting material availability (commercially available = bonus), known reaction types vs novel reactions.

3. **Integration options:**
   - **As a filter:** After ranking, remove candidates with no feasible route (confidence < threshold). Report filtered count.
   - **As a scoring component:** Add as a 5th component to the unified score, re-normalizing weights. E.g., similarity 0.30, druglikeness 0.25, docking 0.20, state 0.15, synthesis 0.10.
   - **As a post-hoc enrichment:** Keep scoring unchanged but add synthesis routes to the evaluation report for top-K candidates.

4. **Evaluation enhancement: `evaluation/synthesis.py`** -- Compare synthesis feasibility distributions between static and state-aware candidates. Are state-specific molecules harder to make? This is an important practical question.

5. **Testing** -- Verify known drugs (erlotinib, gefitinib) have high feasibility scores. Verify obviously impossible molecules (strained rings, exotic elements) score low. Test API fallback behavior.

## Open Questions

- Which retrosynthesis service to use? ASKCOS (MIT, free academic API) vs IBM RXN (IBM, free tier available) vs a local model? Need the Assistant AI to check current API availability and terms.
- How to handle API rate limits for batch processing 80+ candidates? Caching and batching strategies needed.
- Should synthesis feasibility be part of the unified score or a separate analysis? Adding it to the score changes the comparison; keeping it separate is safer but less impactful.
- What is the correlation between SA score and actual retrosynthetic feasibility? If high, the current SA-based approach may be sufficient. If low, the retrosynthesis model adds real value.
