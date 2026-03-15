# State-Conditioned Molecular Generation

## How State/Pocket Conditioning Works

Each EGFR conformational state has a distinct pocket geometry (from the Phase 3
atlas). The generation module maps pocket features to modification strategies:

| Pocket Feature | Threshold | Strategy Triggered |
|---------------|-----------|-------------------|
| Hinge accessibility > 0.8 | DFGin_aCin | Hinge-optimized (pyridyl swaps, amino groups) |
| Back pocket accessible | DFGout states | Back pocket extension (CF3, amide linkers, piperazine) |
| Pocket volume > 600 ų | DFGout states | Volume filling (cyclohexyl, naphthyl) |
| Gatekeeper clearance < 4 Å | DFGin_aCin | Gatekeeper avoiding (shrink substituents, Cl→F) |
| Covalent C797 exposed | All states | Covalent warhead (acrylamide) |
| P-loop folded | DFGout_aCout | P-loop interaction (sulfonamide) |

This produces different candidate sets per state — not just different selections
from one pool, but different chemical modifications driven by pocket geometry.

## How This Differs From the Static Baseline

| Aspect | Static Baseline (Phase 2) | State-Conditioned (Phase 6) |
|--------|--------------------------|---------------------------|
| Target structure | 1M17 only (active state) | All 4 state representatives |
| Pocket context | Single pocket (450 ų) | 4 pockets (420–850 ų) |
| Modifications | Halogen/methyl swaps only | Pocket-specific strategies |
| Back pocket design | Impossible (pocket closed) | Enabled for DFG-out states |
| Volume filling | Not needed (compact pocket) | For DFG-out (780–850 ų) |
| P-loop engagement | Not considered | DFGout_aCout only (folded P-loop) |
| Type-II motifs | None | CF3, amide-phenyl, piperazine extensions |
| Filtering | Single filter set | State-appropriate (type-I vs type-II) |

## Filtering Logic

### Type-I filters (DFGin states)
Standard Lipinski-like rules for ATP-competitive inhibitors:
- MW: 200–600 Da
- HBA: 1–10
- HBD: 0–5
- Heavy atoms: 15–50
- Rings: 1–8

### Type-II filters (DFGout states)
Relaxed for larger type-II inhibitors:
- MW: 250–800 Da
- HBA: 1–12
- HBD: 0–6
- Heavy atoms: 18–60
- Rings: 2–10

## Important Assumptions

1. **SMILES-level chemistry.** All modifications are string-level operations,
   not 3D-aware. A "back pocket extension" is appended to the SMILES, not
   grown into the actual back pocket cavity.

2. **Strategy selection is rule-based.** Pocket features trigger strategies via
   hard-coded thresholds, not learned mappings. These thresholds are derived
   from structural biology knowledge.

3. **No binding affinity estimation.** Generated candidates are not scored for
   binding. That happens in Phase 7 (ranking).

4. **Reference compound seeding.** Generation starts from known EGFR TKIs.
   This biases toward the TKI chemical series. De novo generation from scratch
   would produce more diverse but less drug-like candidates.

5. **Property estimation is approximate.** MW, HBA/HBD counts use SMILES
   heuristics with ~5-10% error vs exact calculations.
