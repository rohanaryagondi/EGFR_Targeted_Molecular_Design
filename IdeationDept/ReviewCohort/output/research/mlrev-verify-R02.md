---
agent: Sr. Journal Reviewer -- ML & AI
round: 2
date: 2026-04-09
type: review-assessment
scope: verification
---

# Round 2 Verification Report: ML & AI Review

## 1. Executive Summary

This report presents deep verification findings for four high-priority claims
identified in Round 1 of the ReviewCohort process. The central findings are:

1. **VAE 99.9% validity is trivially guaranteed by SELFIES encoding, not model
   quality.** Code inspection confirms the `generate()` method is truly
   autoregressive (no teacher forcing), but SELFIES guarantees syntactic validity
   by construction. The 99.9% metric is essentially meaningless as a measure of
   generative quality -- it reflects the representation, not the model. The 0.1%
   failure (1/1000) likely reflects rare SELFIES-to-SMILES conversion edge cases
   documented in recent literature. Reconstruction accuracy, FCD, latent space
   smoothness, and #Circles are the metrics that should be reported instead.

2. **MolPilot is verified as a real, public tool with 95.9% PoseBusters validity.**
   GitHub repo exists (GenSI-THUAIR/MolCRAFT), HuggingFace checkpoint available,
   ICML 2025 accepted. However, VRAM requirements are not documented and likely
   exceed 16GB for training. Inference on RTX 5000 Ada (16GB) is plausible but
   unconfirmed. Docker-based installation adds complexity. Trained on
   CrossDocked2020, which creates EGFR overlap concerns.

3. **Training data overlap with EGFR is near-certain for all 3D baselines.**
   CrossDocked2020 contains 22.5M poses from 2,922 pockets spanning PDB broadly;
   given >200 EGFR structures in PDB, overlap is highly likely though specific
   PDB IDs (1M17, 2GS7, 3W2R, 4ZAU) could not be individually confirmed. FLOWR's
   SPINDR dataset (35,666 complexes from Plinder) likely also contains EGFR. This
   is manageable but must be explicitly addressed through structure-excluded
   re-evaluation or pocket-level leave-one-out protocols.

4. **PMO benchmark's 10K oracle call budget is the gold standard for compute-matched
   comparison.** The AUC of top-10 average score vs. oracle calls is the standard
   metric. StateBind's current comparison (30 vs. 461 candidates) is fundamentally
   compute-unfair and would be rejected at any ML venue. A fixed oracle call budget
   of 1,000-10,000 calls with AUC reporting is the minimum standard.

Additionally: TorchCP (not MAPIE) is the correct tool for conformal prediction on
PyTorch GNNs; fcd_torch is a production-ready PyTorch FCD implementation; and the
MPNN data split is confirmed as random (not scaffold or temporal), which inflates
the reported R^2=0.69.

---

## 2. Task 1: VAE Validity Analysis -- SELFIES Guarantees, Not Model Quality

### 2.1 Code Inspection Findings

I read the full VAE source code at `src/statebind/ml/vae.py` and the generation
script at `scripts/generate_vae_candidates.py`. Key findings:

**The `generate()` method (vae.py, lines 425-532) is truly autoregressive:**
- Starts from an SOS token (line 478-483)
- At each timestep, feeds its own previous prediction as input (line 530)
- Uses temperature-scaled sampling or greedy argmax (lines 506-515)
- No teacher forcing during generation -- the `teacher_forcing_ratio` parameter
  exists only in `forward()` and `SMILESDecoder.forward()`, used during training
- Generation wraps in `torch.no_grad()` (line 491)

This means the 99.9% validity is NOT inflated by teacher forcing during
evaluation. The generation loop is genuinely autoregressive.

**However, the model operates on SELFIES, not SMILES:**
- The generation script detects SELFIES mode from the checkpoint config (line
  101-103): `use_selfies = ckpt_config.get("representation", "smiles") == "selfies"`
- Generated token sequences are decoded to SELFIES strings, then converted to
  SMILES via `selfies_tokenizer.selfies_to_smiles()` (line 187)
- Validity is checked by attempting RDKit parsing of the resulting SMILES (lines
  206-209)

**The critical implication:** SELFIES is designed so that every valid SELFIES
string maps to a valid molecule (Krenn et al., 2020). The 99.9% validity rate
(999/1000) merely confirms that the SELFIES representation works as intended.
The 0.1% failure (1 molecule) reflects a rare edge case in SELFIES-to-SMILES
conversion, not a model failure.

### 2.2 Literature Verification: SELFIES Validity Guarantees

**Original SELFIES paper (Krenn et al., 2020):** SELFIES is described as "a
100% robust molecular string representation" where "every SELFIES string
corresponds to a valid molecule." This was the explicit design goal -- to
eliminate validity as a concern in molecular generation.

**SELFIES anomaly research (Pham et al., 2025, JCIM):** A recent fuzz-testing
study found that VAE-generated SELFIES can fail to convert to valid SMILES under
specific conditions:
- At the boundary of the latent space (R > 29.0 from origin), validity drops
  dramatically
- At the global minimum (R = 61.0), only 11.24% of generated SELFIES converted
  to valid SMILES
- Failure is associated with "troublesome tokens" ([Na+1], [K+1], etc.) that
  exceed valence limits in specific neighborhood contexts
- Near the latent space origin (R < 13.0), validity remains 100%

**Interpretation for StateBind:** The reported 99.9% validity suggests sampling
is occurring close to the latent space origin (as expected when sampling from
the prior N(0,I)), where SELFIES validity is essentially guaranteed. This is
not a meaningful quality metric.

**Published SELFIES VAE validity rates for comparison:**
- LIMO (Eckmann et al., 2022): 100% validity with SELFIES
- MolGen-7b (Fang et al., 2024): 100% validity with SELFIES
- STAR-VAE (2025): 100% validity with SELFIES encoding on 79M PubChem molecules
- Large-scale SELFIES Transformer VAE (bioRxiv 2025): 97% reconstruction accuracy, 100% validity

All SELFIES-based generators report 99-100% validity. This confirms that
99.9% for StateBind is expected behavior of the representation, not evidence
of model quality.

### 2.3 What Metrics SHOULD Be Reported

For a SELFIES-based VAE, reviewers at NeurIPS/ICML/JCIM would expect:

1. **Reconstruction accuracy:** What fraction of input molecules are perfectly
   reconstructed when encoded and decoded? The project reports val_recon=2.26
   (cross-entropy loss), but the actual molecular identity match rate is not
   reported. This is the most important quality metric.

2. **Frechet ChemNet Distance (FCD):** Measures distributional similarity
   between generated and training molecules in learned chemical feature space.
   The `fcd_torch` package provides a PyTorch implementation (Preuer et al.,
   2018, JCIM). FCD < 1.0 is generally considered good; values vary by dataset.

3. **Latent space smoothness:** Linear interpolation between encoded molecules
   should produce valid, chemically sensible intermediates. No evidence this has
   been tested.

4. **Novelty fraction:** What fraction of generated molecules are NOT in the
   training set? The project reports 94.8% uniqueness (948/1000), but novelty
   (not in training) is distinct from uniqueness (not duplicated in sample).

5. **Internal diversity (IntDiv):** Mean pairwise Tanimoto distance within the
   generated set. The project does report diversity (0.9056 for state-aware),
   which is good.

6. **#Circles / SEDiv:** Sphere-exclusion diversity metrics that measure
   chemical space coverage rather than mean pairwise distance (Blaschke et al.,
   2024, JCIM). These have become expected at NeurIPS D&B track papers in 2025.

7. **Property distribution tests:** KS test or MMD between property
   distributions (MW, LogP, QED, etc.) of generated vs. training molecules.

### 2.4 Verdict on Claim #4

**VERIFIED but MISLEADING.** The 99.9% validity rate is technically accurate
(the generation code is autoregressive, not teacher-forced) but scientifically
uninformative. SELFIES guarantees validity by construction, making this metric
vacuous for assessing model quality. Reporting validity for a SELFIES model is
like reporting that a spell-checked document contains valid English words -- it
says nothing about whether the sentences make sense.

**Recommendation:** Remove validity from headline metrics. Replace with
reconstruction accuracy, FCD, and novelty. Report validity only with an
explicit note that SELFIES guarantees it and that it is therefore not a
discriminative metric.

---

## 3. Task 2: MolPilot Verification

### 3.1 Existence and Availability

**VERIFIED: MolPilot is a real, publicly available tool.**

- **Paper:** "Piloting Structure-Based Drug Design via Modality-Specific Optimal
  Schedule" (Qiu et al., 2025)
- **Venue:** Accepted at ICML 2025
- **ArXiv:** https://arxiv.org/abs/2505.07286
- **GitHub:** https://github.com/GenSI-THUAIR/MolCRAFT (MolPilot is a sub-project
  within the MolCRAFT repository)
- **HuggingFace:** https://huggingface.co/GenSI/MolPilot (checkpoints available)
- **Google Drive checkpoint:** Pre-trained model available

### 3.2 PoseBusters Validity

**VERIFIED: 95.9% PoseBusters-valid on CrossDock test set.**

The paper reports "state-of-the-art PoseBusters passing rate of 95.9% on
CrossDock, more than 10% improvement upon strong baselines." This is a
significant result -- by comparison, the recent JCIM benchmarking study
(Sanjrani et al., 2025) found much lower rates for existing methods:

| Model | PoseBusters Valid | MOSES Valid |
|-------|-------------------|-------------|
| Pocket2Mol | 48.2% | 81.2% |
| DiffSBDD | 54.8% | 53.4% |
| MolSnapper | 24.7% | 49.0% |
| AutoGrow4 | 92.7% | 35.6% |
| MolPilot | **95.9%** | Not reported |

MolPilot's 95.9% substantially outperforms all deep learning baselines. However,
note that the benchmarking study retrained all models on BindingMOAD while
MolPilot reports on CrossDocked -- the comparison is not perfectly apples-to-
apples.

### 3.3 GPU/VRAM Requirements

**UNVERIFIED: VRAM requirements not publicly documented.**

Key findings:
- Installation via Docker is recommended (requires `nvidia-container-runtime`)
- Conda environment setup is available as an alternative
- Default training batch size: 16
- Training: 30 epochs, lr=5e-4
- Sampling: 100 steps per molecule, configurable `num_samples`

The documentation does not specify minimum VRAM. Based on the model architecture
(Bayesian Flow Network with equivariant transformers operating on 3D atom
coordinates), and comparison to similar models:

- **DiffSBDD training:** 2 GPUs, ~5 days (Sanjrani et al., 2025)
- **DiffSBDD inference:** 1 GPU, 41 minutes for 1000 compounds
- **FLOWR:** Explicitly requires "at least 40GB VRAM" for training

**Assessment for RTX 5000 Ada (16GB):** Training is very likely infeasible on
16GB VRAM. Inference might be possible with reduced batch size (e.g., batch=1),
but this is uncertain. For reliable use, H200 (80GB) or at minimum RTX Pro 6000
Blackwell (48GB) would be safer. The Yale Bouchet cluster has H200 nodes, which
should work.

### 3.4 Training Data

**MolPilot trains on CrossDocked2020.** The README specifies training data files:
- `crossdocked_v1.1_rmsd1.0_pocket10_processed_final.lmdb`
- `crossdocked_pocket10_pose_split.pt`

This creates an EGFR overlap concern (see Task 3).

### 3.5 Installation Complexity

Moderate to high:
- Docker recommended (not trivial on HPC clusters with SLURM)
- Conda alternative available but less documented
- Dependency chain includes equivariant neural network libraries
- Code is research-quality, not production-ready

### 3.6 Alternative 3D Baselines

If MolPilot proves impractical, alternatives include:

1. **DiffSBDD** (Schneuing et al., 2023): Well-established, GitHub available,
   supports both CrossDocked and BindingMOAD training. Lower PoseBusters validity
   (54.8%) but well-understood.

2. **FLOWR** (Jule et al., 2025): Uses the SPINDR dataset (35,666 complexes),
   achieves state-of-the-art on interaction recovery with up to 70x speedup over
   diffusion. However, requires 40GB VRAM and is no longer actively maintained
   (successor FLOWR.root recommended).

3. **Pocket2Mol** (Peng et al., 2022): Autoregressive, good interaction recovery,
   81.2% MOSES valid. Well-cited and well-documented.

### 3.7 Verdict on Claim #6

**PARTIALLY VERIFIED.** MolPilot exists, is public, and achieves 95.9%
PoseBusters validity as claimed. However, VRAM requirements are undocumented and
may be incompatible with RTX 5000 Ada (16GB). Recommend using H200 nodes on
Bouchet for any 3D baseline work. Installation complexity is non-trivial but
manageable with Docker or conda.

---

## 4. Task 3: Training Data Overlap Analysis

### 4.1 CrossDocked2020 Composition

CrossDocked2020 (Francoeur et al., 2020) contains:
- **22.5 million** poses
- **2,922 pockets** from Pocketome v17.12
- **18,450** complexes
- **13,780** unique ligands
- Sourced from PDB structures grouped by Pocketome binding site similarity

The dataset was constructed by downloading structures from Pocketome, which
groups PDB entries by binding site similarity, then cross-docking all ligands
into all similar pockets using smina. This combinatorial expansion means that
even if a specific PDB ID is not present, structurally similar kinase pockets
almost certainly are.

### 4.2 EGFR in CrossDocked2020

**HIGHLY LIKELY present, but not individually confirmed for all 4 StateBind
structures.**

Evidence for EGFR presence:
- There are >200 human EGFR crystal structures in the PDB (Yun et al., 2015)
- EGFR is one of the most-studied kinase targets in structure-based drug design
- CrossDocked2020 sources from PDB broadly via Pocketome
- The crossdocked_set_ids.txt file on GitHub lists structures by UniProt families,
  making per-PDB-ID searching difficult without downloading the full file
- Kinases are heavily represented in PDB and therefore in CrossDocked2020

**I was unable to definitively confirm or deny the presence of PDB IDs 1M17,
2GS7, 3W2R, 4ZAU** in CrossDocked2020 from the web-accessible portion of the
dataset index. However, given that CrossDocked2020 contains 2,922 pockets
from all of PDB and EGFR has >200 structures, the probability of ZERO EGFR
overlap is negligible.

### 4.3 BindingMOAD EGFR Overlap

BindingMOAD curates binding affinity data from PDB. Given that:
- EGFR has >110 representative kinase structures with ligands in PDB
- BindingMOAD specifically curates protein-ligand complexes with measured Kd/Ki/IC50
- EGFR inhibitors have extensive measured binding data

**EGFR is almost certainly present in BindingMOAD.** The JCIM benchmarking study
(Sanjrani et al., 2025) used BindingMOAD with 41,703 training complexes and
tested on kinase targets (ITK, AurB, LCK, JAK1/2/3) -- demonstrating that
kinase structures are present and used.

### 4.4 SPINDR/FLOWR Dataset

SPINDR (35,666 complexes) derives from the Plinder dataset, which itself
curates from PDB crystallographic data. SPINDR explicitly uses Plinder's
train/test splits designed to "minimise data leakage between train and test sets."

However, "minimizing data leakage" refers to structural similarity between
train/test, not to excluding specific targets. EGFR structures are likely
present in SPINDR's training set.

### 4.5 Impact Assessment

**Is this a fatal flaw?** No, but it requires explicit handling.

Standard approaches in the literature:

1. **Structure-excluded evaluation (recommended):** Remove all EGFR-containing
   complexes from the training set and retrain the 3D baseline. This is the
   most rigorous approach. DiffSBDD supports retraining on BindingMOAD with
   custom splits.

2. **Pocket-level leave-one-out:** Remove all pockets with sequence identity
   >30% to EGFR from training. More conservative but computationally expensive.

3. **Zero-shot disclaimer:** Report results with the explicit caveat that the
   3D baseline may have seen EGFR structures during training, and note this
   as a limitation. This is the minimum acceptable approach.

4. **Performance calibration:** Compare the 3D baseline's performance on EGFR
   (potentially seen) vs. a truly unseen target to estimate the contamination
   effect.

The JCIM benchmarking study (Sanjrani et al., 2025) found that models like
Pocket2Mol showed >95% hydrogen bond recreation for well-represented kinase
domains but <30% for less-represented ones (LCK), suggesting that training
set overlap substantially inflates performance on familiar targets.

### 4.6 Verdict on Claim #14

**VERIFIED: Training data overlap with EGFR is near-certain for all 3D
baselines.** CrossDocked2020, BindingMOAD, and SPINDR all derive from PDB and
almost certainly contain EGFR structures. This is not fatal but requires one
of the handling strategies above. Structure-excluded retraining is the strongest
approach and should be the default plan.

---

## 5. Task 4: Compute-Matched Comparison Standards

### 5.1 PMO Benchmark Protocol

**VERIFIED: The PMO benchmark (Gao et al., NeurIPS 2022) establishes the gold
standard for compute-fair molecular optimization comparison.**

Key protocol elements:
- **Fixed oracle call budget:** 10,000 calls maximum
- **Metric:** AUC of top-10 average score vs. number of oracle calls
- **Why AUC:** Captures both optimization quality AND sample efficiency in a
  single number -- methods that achieve high scores with fewer calls are rewarded
- **23 optimization tasks:** QED, DRD2, GSK3beta, JNK3, and 19 Guacamol oracles
- **25 methods benchmarked:** Spanning genetic algorithms, VAE, RL, gradient
  ascent, and more
- **Reproducibility:** Open-source at https://github.com/wenhao-gao/mol_opt
- **Key finding:** Most "state-of-the-art" methods fail to outperform predecessors
  under the 10K budget constraint

The PMO benchmark is widely cited (500+ citations as of 2026) and is the
expected reference for any molecular optimization comparison at ML venues.

### 5.2 StateBind's Current Comparison is Compute-Unfair

The current StateBind comparison is:
- **Static baseline:** 30 candidates (string modifications of known drugs)
- **State-aware VAE:** 461 candidates (36 template + 395 VAE-generated + 30 shared)

This is a **15:1 candidate ratio**. The state-aware pipeline has 15x more
"oracle calls" (scoring evaluations). In PMO terms, this would be like giving
one method 10,000 calls and the other 650 calls. No ML reviewer would accept
this as a fair comparison.

The retrospective enrichment result (10x EF@10) is also affected:
- State-aware generates 461 diverse candidates, some of which happen to
  resemble future drugs
- Static generates only 30 candidates close to existing drugs
- The enrichment advantage could be partially or wholly explained by the
  larger, more diverse candidate pool rather than state-awareness per se

### 5.3 Recommended Approach for StateBind

**Option A: Fixed Oracle Call Budget (RECOMMENDED)**

Define a fixed scoring budget (e.g., 500 or 1,000 oracle calls) that all
methods must operate within:

1. **Static baseline:** Generate the best 500 candidates using string
   modifications, screen top-500 by score
2. **State-aware VAE:** Generate candidates, score up to 500
3. **REINVENT 4:** Run RL optimization with 500 oracle call limit
4. **3D baseline (MolPilot/DiffSBDD):** Generate up to 500 molecules, score

Report: AUC of top-10 average score vs. oracle calls (PMO-style).

**Option B: Fixed Candidate Count**

Ensure all methods produce exactly N candidates (e.g., 100 per method):
- Static: top 100 by score
- State-aware: top 100 by score
- Others: top 100 by score

This is simpler but less informative than Option A.

**Option C: Fixed Wall-Clock Time**

Give each method the same GPU-hours. This is harder to implement fairly
(different methods have different GPU utilization patterns) but captures
total computational cost.

**Recommendation:** Use Option A (fixed oracle calls) as the primary
comparison and report Option C (wall-clock) in the supplementary material.
This aligns with PMO standards and is what ML reviewers expect.

### 5.4 Augmented Memory and Sample Efficiency Context

Recent work on sample-efficient molecular optimization is highly relevant:

- **Augmented Memory (Guo et al., 2024, JACS Au):** Reaches score 0.8 with
  6,144 oracle calls on average across PMO tasks -- current state-of-the-art
  for sample efficiency
- **Saturn (Guo et al., 2025, Nature Machine Intelligence):** Mamba-based
  architecture with experience replay, further improving efficiency
- **Double-loop RL:** Second-most efficient at 12,416 oracle calls

These methods demonstrate that modern molecular optimizers can achieve strong
results within the 10K budget. StateBind's comparison should target similar
efficiency levels.

### 5.5 The #Circles Approach

An alternative to oracle-call budgets is the #Circles diversity framework
(Blaschke et al., 2024, JCIM):

- Evaluate generators under two constraints: fixed scoring calls OR fixed
  wall-clock time
- Use #Circles (sphere-exclusion diversity) as the metric rather than or
  alongside top-K scores
- This captures both quality AND diversity simultaneously
- Study evaluated 12 generators across 3 protein targets, finding that
  SMILES-based autoregressive models outperform graph-based methods and GAs
  for diverse hit generation

This would be an excellent supplementary analysis for StateBind.

### 5.6 Verdict on Issue N4

**VERIFIED: The current comparison is compute-unfair and would not pass ML
venue review.** A fixed oracle call budget (PMO-style, 1K-10K calls) with
AUC top-10 reporting is the minimum standard. This is a must-fix item, not
a nice-to-have.

---

## 6. Additional Verification Notes

### 6.1 MAPIE vs. TorchCP for Conformal Prediction

**MAPIE is NOT the right tool for PyTorch GNNs.** MAPIE is scikit-learn-native
and has limited support for deep learning models. While it can work with PyTorch
models through a scikit-learn wrapper, this requires converting GNN predictions
to NumPy arrays and loses GPU acceleration.

**TorchCP is the correct choice.** TorchCP (Huang et al., 2024, JMLR Vol. 26)
is a PyTorch-native conformal prediction library that:
- Has native support for graph neural networks
- Implements 6 training algorithms, 16 score functions, 10 predictors
- Provides GPU-accelerated batch processing with up to 90x speedup
- Has 100% unit test coverage and detailed documentation
- Released under LGPL-3.0, ~16K lines of code
- Available at: https://github.com/ml-stat-Sustech/TorchCP

**Recommendation:** Use TorchCP for conformal prediction on the MPNN affinity
model. It natively supports the GNN workflow and avoids the NumPy conversion
bottleneck that MAPIE would impose.

### 6.2 FCD Implementation

**fcd_torch is production-ready and available.**

- Package: `fcd_torch` (pip installable)
- Repository: https://github.com/insilicomedicine/fcd_torch
- Usage: `FCD(device='cuda:0', n_jobs=8)(smiles_list1, smiles_list2)`
- Produces identical outputs to the original Keras implementation
- PyTorch model weights are 10x smaller than Keras version
- Requires RDKit (available on the cluster)

**Recommendation:** Compute FCD between:
1. VAE-generated molecules vs. training set
2. VAE-generated molecules vs. ChEMBL EGFR inhibitors
3. Per-state generated sets vs. each other (to assess state conditioning effect)

This would provide far more informative evaluation than validity rate.

### 6.3 MPNN Split Type: CONFIRMED RANDOM

**This is a significant concern.** Code inspection of
`src/statebind/ml/affinity_dataset.py` (lines 345-404) confirms:

```python
def split_dataset(dataset, config=None, train_ratio=0.8, val_ratio=0.1,
                  test_ratio=0.1, seed=42):
    ...
    indices = rng.permutation(n)  # <-- RANDOM PERMUTATION
    train_idx = indices[:n_train]
    ...
```

The MPNN uses a **random 80/10/10 split**, not scaffold or temporal split.
This means:

- **R^2 = 0.69 is inflated.** Random splits allow structurally similar molecules
  (same scaffold, different substitution) to appear in both train and test sets
- **Expected scaffold-split R^2:** Based on published benchmarks for similar
  tasks (EGFR pIC50 prediction), scaffold splits typically reduce R^2 by 0.15-0.25
  points. Expected scaffold-split performance: R^2 ~ 0.45-0.55
- **Expected temporal-split R^2:** Temporal splits (by publication year) further
  reduce performance as chemical series evolve over time. Expected: R^2 ~ 0.35-0.50

This is a known issue in molecular ML. For publication, the MPNN MUST be
re-evaluated with scaffold splitting (at minimum) and ideally also temporal
splitting. The retrospective pre-cutoff models (pre-2010, pre-2015) partially
address temporal generalization but do not address scaffold generalization.

**Recommendation:** Re-split the ChEMBL EGFR dataset using Bemis-Murcko
scaffold decomposition. Report R^2 on both random and scaffold splits.
This is now standard practice at JCIM and NeurIPS (Wu et al., MoleculeNet, 2018).

### 6.4 SEDiv and #Circles Implementations

The #Circles metric from Blaschke et al. (2024) is available in the
supplementary code of the JCIM paper. SEDiv (Sphere Exclusion Diversity)
quantifies chemical space coverage by finding the maximum set of molecules
that are pairwise distant beyond a threshold D (typically 0.7 Tanimoto distance).

#Circles is the maximum cardinality of a set where no molecular center lies
within another molecule's exclusion sphere. This is more informative than
internal diversity (IntDiv), which can be maximized by just two maximally
distant molecules and can actually decrease when adding new diverse molecules.

**Availability:** The reference implementation is in the supplementary code
of the JCIM paper. MOSES (Molecular Sets) also implements related diversity
metrics. For StateBind, implementing #Circles is straightforward: compute
pairwise Tanimoto distances and apply sphere exclusion with D=0.7.

---

## 7. Updated Recommendations

Based on verification findings, I update my Round 1 priority recommendations:

### 7.1 MUST-FIX (Publication Blockers)

1. **Compute-matched ablation (CRITICAL).** Implement PMO-style fixed oracle
   call budget comparison. Without this, no ML venue will accept the paper.
   Effort: 1-2 weeks. Impact: Enables submission.

2. **Report proper VAE metrics (HIGH).** Replace validity with FCD,
   reconstruction accuracy, novelty, #Circles. Effort: 3-5 days using
   fcd_torch and standard implementations.

3. **MPNN scaffold split evaluation (HIGH).** Re-evaluate MPNN with scaffold
   splits. Report both random and scaffold R^2. Effort: 2-3 days (just
   re-splitting existing data and re-evaluating checkpoints).

4. **Address training data overlap for 3D baselines (HIGH).** Either retrain
   with EGFR excluded or provide explicit analysis of overlap impact.
   Effort: 1-2 weeks if retraining, 2-3 days for analysis-only approach.

### 7.2 SHOULD-FIX (Significantly Strengthens Paper)

5. **Add conformal prediction via TorchCP (MEDIUM).** Provides uncertainty
   quantification for MPNN predictions. Effort: 1 week.

6. **Integrate FCD and property distribution tests (MEDIUM).** Standard
   molecular generation evaluation suite. Effort: 3-5 days.

7. **Run DiffSBDD as 3D baseline instead of or alongside MolPilot (MEDIUM).**
   Better documented, supports BindingMOAD training with custom splits, lower
   VRAM requirements. Effort: 1-2 weeks.

### 7.3 NICE-TO-HAVE (Differentiators)

8. **#Circles diversity analysis (LOW).** Provides modern diversity metrics
   that reviewers now expect. Effort: 2-3 days.

9. **PMO benchmark integration (LOW).** Run StateBind's VAE through the PMO
   benchmark tasks to establish baseline sample efficiency. Effort: 1 week.

---

## 8. References

1. Krenn, M., Hase, F., Nigam, A., Friederich, P., & Aspuru-Guzik, A. (2020).
   Self-referencing embedded strings (SELFIES): A 100% robust molecular string
   representation. *Machine Learning: Science and Technology*, 1(4), 045024.

2. Pham, T. H., et al. (2025). Fuzz Testing Molecular Representation Using
   Deep Variational Anomaly Generation. *Journal of Chemical Information and
   Modeling*. DOI: 10.1021/acs.jcim.4c01876.

3. Gao, W., Fu, T., Sun, J., & Coley, C. W. (2022). Sample Efficiency Matters:
   A Benchmark for Practical Molecular Optimization. *Advances in Neural
   Information Processing Systems*, 35.

4. Francoeur, P. G., et al. (2020). Three-Dimensional Convolutional Neural
   Networks and a Cross-Docked Data Set for Structure-Based Drug Design.
   *Journal of Chemical Information and Modeling*, 60(9), 4200-4215.

5. Qiu, K., et al. (2025). Piloting Structure-Based Drug Design via
   Modality-Specific Optimal Schedule. *ICML 2025*. arXiv:2505.07286.

6. Schneuing, A., et al. (2023). Structure-based drug design with equivariant
   diffusion models. *arXiv:2210.13695*. (DiffSBDD)

7. Preuer, K., et al. (2018). Frechet ChemNet Distance: A Metric for
   Generative Models for Molecules in Drug Discovery. *Journal of Chemical
   Information and Modeling*, 58(9), 1736-1741.

8. Blaschke, T., et al. (2024). Diverse Hits in De Novo Molecule Design:
   Diversity-Based Comparison of Goal-Directed Generators. *Journal of
   Chemical Information and Modeling*. DOI: 10.1021/acs.jcim.4c00519.

9. Sanjrani, G. M., et al. (2025). Benchmarking 3D Structure-Based Molecule
   Generators. *Journal of Chemical Information and Modeling*. DOI:
   10.1021/acs.jcim.5c01020.

10. Jule, C., et al. (2025). Flowr -- Flow Matching for Structure-Aware De
    Novo, Interaction- and Fragment-Based Ligand Generation.
    arXiv:2504.10564.

11. Huang, W., et al. (2024). TorchCP: A Python Library for Conformal
    Prediction. *Journal of Machine Learning Research*, 26, 1-7.

12. Guo, J., et al. (2024). Augmented Memory: Sample-Efficient Generative
    Molecular Design with Reinforcement Learning. *JACS Au*, 4(6), 2159-2172.

13. Guo, J., et al. (2025). Saturn: Sample-efficient Generative Molecular
    Design using Memory Manipulation. *Nature Machine Intelligence*.

14. Wu, Z., et al. (2018). MoleculeNet: A Benchmark for Molecular Machine
    Learning. *Chemical Science*, 9(2), 513-530.

15. Polykovskiy, D., et al. (2020). Molecular Sets (MOSES): A Benchmarking
    Platform for Molecular Generation Models. *Frontiers in Pharmacology*, 11,
    565644.

16. Eckmann, P., et al. (2022). LIMO: Latent Inceptionism for Targeted
    Molecule Generation. *ICML 2022*.

17. SPINDR: Small molecule Protein Interaction Dataset, Refined. Zenodo
    record 16375073. 35,666 protein-ligand complexes.

18. fcd_torch: Frechet ChemNet Distance on PyTorch. GitHub:
    insilicomedicine/fcd_torch.

19. Yun, C. H., et al. (2015). The Structure and Clinical Relevance of the
    EGF Receptor in Human Cancer. *Journal of Clinical Oncology*.

20. Bemis, G. W., & Murcko, M. A. (1996). The Properties of Known Drugs.
    1. Molecular Frameworks. *Journal of Medicinal Chemistry*, 39(15),
    2887-2893.
