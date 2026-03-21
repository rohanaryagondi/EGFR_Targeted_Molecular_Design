# Interface Contracts

Exact function signatures and return types that workstreams must conform to. This document prevents workstreams from breaking each other.

## How to Read This Document

Each section defines a contract: the **producer** creates the interface, and the **consumer(s)** depend on it. If you're working on a producer workstream, you MUST implement exactly these signatures. If you're working on a consumer workstream, you can rely on these signatures being stable.

---

## Contract 1: Chemistry Module

**Producer:** Workstream 01 (Chemistry Foundation)
**Consumers:** Workstream 02 (Scoring Integration), Workstream 04 (Docking Proxy)

### `statebind.chemistry.fingerprints`

```python
HAS_RDKIT: bool
# True if rdkit is importable, False otherwise. Module-level constant.

def compute_morgan_fingerprint(
    smiles: str,
    radius: int = 2,
    n_bits: int = 2048,
) -> Any | None:
    """Returns RDKit ExplicitBitVect or None if SMILES invalid / RDKit unavailable."""

def compute_morgan_similarity(
    smiles_a: str,
    smiles_b: str,
    radius: int = 2,
    n_bits: int = 2048,
) -> float:
    """Morgan fingerprint Tanimoto similarity in [0.0, 1.0].
    Falls back to SMILES n-gram Tanimoto if RDKit unavailable."""

def compute_max_reference_similarity(
    smiles: str,
    references: list[str] | None = None,
) -> float:
    """Max Morgan similarity to reference EGFR binders.
    Uses _REFERENCE_BINDERS if references is None.
    Falls back to n-gram if RDKit unavailable.
    Return value in [0.0, 1.0]."""
```

### `statebind.chemistry.descriptors`

```python
def compute_exact_properties(smiles: str) -> dict[str, float | None]:
    """Compute molecular properties via RDKit.

    MUST return at minimum these keys (for backward compat with baselines/filtering.py):
        "estimated_mw": float | None
        "estimated_hba": float | None
        "estimated_hbd": float | None
        "n_rings": float | None
        "n_heavy_atoms": float | None

    MAY also return:
        "tpsa": float | None
        "logp": float | None
        "n_rotatable_bonds": float | None

    Returns dict with None values if SMILES invalid or RDKit unavailable.
    """
```

### `statebind.chemistry.validation`

```python
def validate_smiles(smiles: str) -> bool:
    """True if SMILES is valid. Returns True if RDKit unavailable (permissive)."""

def canonicalize_smiles(smiles: str) -> str | None:
    """Canonical SMILES string. Returns original if RDKit unavailable.
    Returns None if SMILES is invalid and RDKit is available."""
```

### `statebind.chemistry.sa_score`

```python
def compute_sa_score(smiles: str) -> float:
    """SA score in [1.0, 10.0]. 1=easy, 10=hard.
    Returns 5.0 if RDKit unavailable or SMILES invalid."""
```

---

## Contract 2: Docking Proxy

**Producer:** Workstream 04 (Docking Proxy)
**Consumers:** Workstream 02 (Scoring Integration) — via baselines/scoring.py

### `statebind.chemistry.docking_proxy`

```python
class DockingProxy:
    def __init__(self, input_dim: int = 20, hidden_dim: int = 16): ...

    def fit(
        self,
        smiles_list: list[str],
        labels: list[int],
        n_epochs: int = 200,
        lr: float = 0.01,
    ) -> list[float]:
        """Train. Returns loss history."""

    def predict(self, smiles: str) -> float:
        """EGFR-likeness score in [0.0, 1.0].
        Returns 0.5 if featurization fails."""

    def predict_batch(self, smiles_list: list[str]) -> list[float]:
        """Batch prediction. Same semantics as predict()."""

def get_default_proxy() -> DockingProxy:
    """Get or create trained singleton proxy.
    Trains on first call using embedded EGFR SAR data."""
```

---

## Contract 3: Statistics Module

**Producer:** Workstream 03 (Statistical Testing)
**Consumers:** Workstream 05 (Visualization)

### `statebind.evaluation.statistics`

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class StatisticalTest:
    name: str              # e.g., "Mann-Whitney U"
    statistic: float       # test statistic value
    p_value: float         # two-sided p-value
    effect_size: float     # standardized effect size
    ci_lower: float        # 95% CI lower bound
    ci_upper: float        # 95% CI upper bound
    interpretation: str    # plain-language summary

@dataclass
class BootstrapCI:
    metric_name: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    alpha: float = 0.05
    n_bootstrap: int = 1000

def mann_whitney_u(scores_a: list[float], scores_b: list[float]) -> StatisticalTest: ...
def bootstrap_confidence_interval(
    values: list[float],
    statistic_fn: Callable[[list[float]], float],
    alpha: float = 0.05,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> BootstrapCI: ...
def cohens_d(scores_a: list[float], scores_b: list[float]) -> float: ...
def cliff_delta(scores_a: list[float], scores_b: list[float]) -> float: ...
def permutation_test(
    scores_a: list[float],
    scores_b: list[float],
    n_permutations: int = 10000,
    seed: int = 42,
) -> StatisticalTest: ...
```

### `statebind.evaluation.sensitivity`

```python
from dataclasses import dataclass
from statebind.ranking.models import MergedRanking

@dataclass
class SensitivityResult:
    weight_config: dict[str, float]
    static_mean: float
    state_aware_mean: float
    winner: str              # "static", "state_aware", or "tie"
    delta: float             # state_aware_mean - static_mean

@dataclass
class SensitivitySummary:
    n_configs: int
    state_aware_wins: int
    static_wins: int
    ties: int
    state_aware_win_fraction: float
    results: list[SensitivityResult]

def run_weight_sensitivity(
    merged: MergedRanking,
    n_samples: int = 100,
    seed: int = 42,
) -> SensitivitySummary: ...

def run_ablation_analysis(merged: MergedRanking) -> list[SensitivityResult]: ...

def run_weight_sweep(
    merged: MergedRanking,
    component: str,
    values: list[float],
) -> list[SensitivityResult]: ...
```

---

## Contract 4: MPNN Affinity Predictor

**Producer:** Workstream 08 (MPNN Affinity)
**Consumers:** Workstream 02 (Scoring Integration) — replaces docking stub in ranking/scoring.py

### `statebind.ml.affinity_predictor` (to be created during integration)

```python
def predict_affinity(smiles: str) -> float:
    """Predict binding affinity score in [0.0, 1.0].

    Internally: MPNN predicts pIC50, then normalizes via sigmoid((pIC50 - 5) / 2).
    Falls back to 0.5 (docking stub) if model not available or SMILES invalid.
    """

def predict_affinity_batch(smiles_list: list[str]) -> list[float]:
    """Batch prediction. Same semantics as predict_affinity()."""
```

### Cascading fallback in `ranking/scoring.py`

```python
# Priority order for docking_proxy score:
# 1. MPNN prediction (if trained model exists and torch available)
# 2. DockingProxy MLP (Workstream 04, if trained)
# 3. Constant 0.5 stub (current default)
```

---

## Contract 5: Conditional SMILES VAE

**Producer:** Workstream 07 (Conditional VAE)
**Consumers:** generation pipeline — produces StateConditionedCandidate objects

### `statebind.ml.vae_integration` (to be created during integration)

```python
from statebind.generation.models import StateConditionedCandidate

def generate_vae_candidates(
    state: str,
    n_samples: int = 100,
    temperature: float = 0.8,
    checkpoint_path: str = "artifacts/models/vae/best_model.pt",
) -> list[StateConditionedCandidate]:
    """Generate novel molecules for a specific conformational state.

    Each candidate has:
        source = CandidateSource.ML_GENERATED
        strategy = GenerationStrategy.VAE_GENERATED
        target_state = state

    Returns empty list if model not available or torch not installed.
    """
```

---

## Contract 6: Multi-Task ADMET Predictor

**Producer:** Workstream 09 (ADMET)
**Consumers:** generation/filtering pipeline, evaluation reports

### `statebind.ml.admet_predictor` (to be created during integration)

```python
def predict_admet(smiles: str) -> dict[str, float]:
    """Predict ADMET properties for a single molecule.

    Returns dict mapping task name to predicted value:
        Regression tasks: raw predicted value
        Classification tasks: probability in [0.0, 1.0]

    Returns empty dict if model not available.
    """

def check_admet_pass(
    smiles: str,
    thresholds: dict[str, float] | None = None,
) -> tuple[bool, dict[str, float]]:
    """Check if molecule passes ADMET safety criteria.

    Returns (pass_bool, predictions_dict).
    Default thresholds flag hERG > 0.5 and CYP3A4 > 0.5 as failures.
    Returns (True, {}) if model not available (permissive fallback).
    """
```

---

## Contract 7: Existing Interfaces (Do Not Break)

These are existing interfaces that multiple workstreams depend on. Do NOT change their signatures.

### `statebind.baselines.scoring`

```python
def _score_reference_similarity(smiles: str) -> float: ...
def _score_druglikeness(properties: dict[str, float | None]) -> float: ...
def _score_docking_stub(smiles: str, pdb_id: str) -> float: ...
def _tanimoto_ngram(smiles_a: str, smiles_b: str, n: int = 3) -> float: ...
def score_candidates(
    filtered: FilteredLibrary,
    target_pdb_id: str = "1m17",
    weights: dict[str, float] | None = None,
) -> RankedCandidates: ...
```

### `statebind.baselines.filtering`

```python
def compute_properties(smiles: str) -> dict[str, float | None]: ...
# Return dict MUST include: estimated_mw, estimated_hba, estimated_hbd, n_rings, n_heavy_atoms
```

### `statebind.ranking.scoring`

```python
DEFAULT_WEIGHTS: dict[str, float]
# {"reference_similarity": 0.35, "druglikeness": 0.30, "docking_proxy": 0.20, "state_specificity": 0.15}

def score_unified(
    smiles: str,
    target_state: str,
    pipeline: PipelineLabel,
    state_smiles_map: dict[str, set[str]],
    weights: dict[str, float] | None = None,
) -> tuple[list[UnifiedScoreComponent], float]: ...
```

### `statebind.evaluation.comparison`

```python
def run_full_comparison(
    merged: MergedRanking,
    top_k: int = 10,
) -> ComparativeResult: ...
# Workstream 03 may add optional parameter: run_statistics: bool = False
```
