"""VAE quality metrics beyond trivial SELFIES validity.

Provides meaningful evaluation of generative model quality:

- **FCD** (Frechet ChemNet Distance): distributional similarity between
  generated and reference molecules.
- **Reconstruction accuracy**: fraction of input molecules perfectly
  reconstructed through encode-decode.
- **Novelty**: fraction of valid generated molecules absent from the
  training set.
- **Internal diversity**: 1 - mean pairwise Tanimoto similarity among
  generated molecules.

All heavy dependencies (``fcd_torch``, ``torch``, ``rdkit``) are optional.
Functions gracefully return ``None`` when the required library is missing.
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------

HAS_FCD: bool
try:
    import fcd_torch  # noqa: F401

    HAS_FCD = True
except ImportError:
    HAS_FCD = False

HAS_TORCH: bool
try:
    import torch  # noqa: F401

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

HAS_RDKIT: bool
try:
    from rdkit import Chem as _Chem
    from rdkit import DataStructs as _DataStructs
    from rdkit.Chem import AllChem as _AllChem

    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

if TYPE_CHECKING:
    from statebind.ml.vae import ConditionalSMILESVAE
    from statebind.ml.vae_dataset import SMILESDataset
    from statebind.ml.vocabulary import Vocabulary


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


class VaeMetricsResult(BaseModel):
    """Aggregated VAE quality metrics."""

    fcd_score: float | None = None
    """Frechet ChemNet Distance (lower is better). ``None`` when
    ``fcd_torch`` is unavailable."""

    reconstruction_accuracy: float | None = None
    """Fraction of training molecules exactly reconstructed. ``None``
    when ``torch`` is unavailable."""

    novelty: float
    """Fraction of valid generated SMILES not present in the training set."""

    internal_diversity: float | None = None
    """1 - mean pairwise Tanimoto among generated molecules. ``None``
    when ``rdkit`` is unavailable."""

    n_generated: int
    """Total number of generated SMILES evaluated."""

    n_valid: int
    """Number of valid SMILES among generated (always equals
    ``n_generated`` for SELFIES-based VAE)."""

    n_novel: int
    """Number of generated SMILES not found in the training set."""


# ---------------------------------------------------------------------------
# Canonicalization helper
# ---------------------------------------------------------------------------


def _canonicalize(smiles: str) -> str:
    """Return canonical SMILES if RDKit is available, else stripped string."""
    if HAS_RDKIT:
        mol = _Chem.MolFromSmiles(smiles)
        if mol is not None:
            return _Chem.MolToSmiles(mol)
    return smiles.strip()


# ---------------------------------------------------------------------------
# FCD
# ---------------------------------------------------------------------------


def compute_fcd(
    generated_smiles: list[str],
    reference_smiles: list[str],
) -> float | None:
    """Frechet ChemNet Distance between generated and reference sets.

    Parameters
    ----------
    generated_smiles:
        SMILES strings from the generative model.
    reference_smiles:
        SMILES strings from the training/reference set.

    Returns
    -------
    float | None:
        FCD score (lower is better), or ``None`` when ``fcd_torch`` is
        not installed.
    """
    if not HAS_FCD:
        logger.info("fcd_torch not available -- skipping FCD computation")
        return None

    if not generated_smiles or not reference_smiles:
        logger.warning("Empty SMILES list provided to compute_fcd")
        return None

    if len(generated_smiles) < 100:
        logger.warning(
            "FCD with n=%d generated molecules is unreliable "
            "(recommend n >= 100)",
            len(generated_smiles),
        )
    if len(reference_smiles) < 100:
        logger.warning(
            "FCD with n=%d reference molecules is unreliable "
            "(recommend n >= 100)",
            len(reference_smiles),
        )

    from fcd_torch import FCD

    fcd_calculator = FCD(device="cpu", n_jobs=1)
    score = fcd_calculator(generated_smiles, reference_smiles)
    return round(float(score), 4)


# ---------------------------------------------------------------------------
# Reconstruction accuracy
# ---------------------------------------------------------------------------


def compute_reconstruction_accuracy(
    model: ConditionalSMILESVAE,
    dataset: SMILESDataset,
    vocab: Vocabulary,
    device: str = "cpu",
    max_samples: int | None = None,
) -> float | None:
    """Fraction of dataset molecules perfectly reconstructed by the VAE.

    Encodes each molecule, then decodes greedily (temperature=0) and
    checks exact string match against the original tokenized sequence.

    Parameters
    ----------
    model:
        A trained :class:`~statebind.ml.vae.ConditionalSMILESVAE`.
    dataset:
        The :class:`~statebind.ml.vae_dataset.SMILESDataset` to
        reconstruct.
    vocab:
        The :class:`~statebind.ml.vocabulary.Vocabulary` used for
        encoding/decoding.
    device:
        Torch device string (``"cpu"`` or ``"cuda"``).
    max_samples:
        If set, evaluate only this many samples (randomly chosen).

    Returns
    -------
    float | None:
        Reconstruction accuracy in ``[0, 1]``, or ``None`` if torch is
        unavailable.
    """
    if not HAS_TORCH:
        logger.info("torch not available -- skipping reconstruction accuracy")
        return None

    import torch as _torch

    n_total = len(dataset)
    if n_total == 0:
        return None

    indices = list(range(n_total))
    if max_samples is not None and max_samples < n_total:
        rng = random.Random(42)
        indices = rng.sample(indices, max_samples)

    model = model.to(device)
    model.eval()

    n_correct = 0
    for idx in indices:
        tokens_tensor, length, state_onehot = dataset[idx]

        # Original token indices (strip SOS/EOS for comparison)
        original_indices = tokens_tensor.tolist()
        # Strip SOS (index 1) from the front and EOS (index 2) from the end
        original_body: list[int] = []
        for tok_idx in original_indices:
            if tok_idx == vocab.sos_idx or tok_idx == vocab.eos_idx:
                continue
            if tok_idx == vocab.pad_idx:
                continue
            original_body.append(tok_idx)

        # Encode
        x = tokens_tensor.unsqueeze(0).to(device)
        lengths = _torch.tensor([length], dtype=_torch.long, device=device)
        state = state_onehot.unsqueeze(0).to(device)

        with _torch.no_grad():
            mu, logvar = model.encode(x, lengths, state)
            # Deterministic: use mu directly (model.eval sets sample=mu)
            z = mu

        # Greedy decode
        max_len = len(original_body) + 10  # generous margin
        decoded_seqs = model.generate(
            z, state, max_len=max_len, temperature=0, vocab=vocab,
        )
        decoded_indices = decoded_seqs[0]

        if decoded_indices == original_body:
            n_correct += 1

    accuracy = round(n_correct / len(indices), 4)
    return accuracy


# ---------------------------------------------------------------------------
# Novelty
# ---------------------------------------------------------------------------


def compute_novelty(
    generated_smiles: list[str],
    training_smiles: list[str],
) -> float:
    """Fraction of generated SMILES not present in the training set.

    Canonicalizes SMILES with RDKit when available; otherwise compares
    stripped strings.

    Parameters
    ----------
    generated_smiles:
        SMILES from the generative model.
    training_smiles:
        SMILES from the training set.

    Returns
    -------
    float:
        Novelty in ``[0, 1]``. Returns ``0.0`` if ``generated_smiles``
        is empty.
    """
    if not generated_smiles:
        return 0.0

    training_canonical = {_canonicalize(s) for s in training_smiles}

    n_novel = 0
    for smi in generated_smiles:
        canon = _canonicalize(smi)
        if canon not in training_canonical:
            n_novel += 1

    return round(n_novel / len(generated_smiles), 4)


# ---------------------------------------------------------------------------
# Internal diversity
# ---------------------------------------------------------------------------


def compute_internal_diversity(
    smiles_list: list[str],
    n_sample: int = 1000,
    seed: int = 42,
) -> float | None:
    """Internal diversity: 1 - mean pairwise Tanimoto similarity.

    Uses Morgan fingerprints (radius 2, 2048 bits) for proper molecular
    similarity when RDKit is available.

    Parameters
    ----------
    smiles_list:
        SMILES strings to evaluate.
    n_sample:
        Maximum number of molecules to consider (randomly sampled for
        computational tractability). Pairwise comparison is O(n^2).
    seed:
        Random seed for reproducible subsampling.

    Returns
    -------
    float | None:
        Diversity in ``[0, 1]`` (1 = maximally diverse, 0 = all
        identical), or ``None`` if RDKit is unavailable.
    """
    if not HAS_RDKIT:
        logger.info(
            "RDKit not available -- skipping internal diversity "
            "(Morgan fingerprints required)"
        )
        return None

    if len(smiles_list) < 2:
        return 0.0

    # Subsample if needed
    if len(smiles_list) > n_sample:
        rng = random.Random(seed)
        smiles_list = rng.sample(smiles_list, n_sample)

    # Compute fingerprints, skip invalid molecules
    fps = []
    for smi in smiles_list:
        mol = _Chem.MolFromSmiles(smi)
        if mol is not None:
            fp = _AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            fps.append(fp)

    n = len(fps)
    if n < 2:
        return 0.0

    # Mean pairwise Tanimoto
    total_sim = 0.0
    n_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_sim += _DataStructs.TanimotoSimilarity(fps[i], fps[j])
            n_pairs += 1

    mean_tanimoto = total_sim / n_pairs if n_pairs > 0 else 0.0
    diversity = 1.0 - mean_tanimoto
    return round(diversity, 4)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def evaluate_vae_quality(
    generated_smiles: list[str],
    training_smiles: list[str],
    model: ConditionalSMILESVAE | None = None,
    dataset: SMILESDataset | None = None,
    vocab: Vocabulary | None = None,
    device: str = "cpu",
    max_recon_samples: int | None = None,
    diversity_n_sample: int = 1000,
) -> VaeMetricsResult:
    """Evaluate VAE quality across all four metrics.

    Parameters
    ----------
    generated_smiles:
        SMILES strings produced by the VAE.
    training_smiles:
        SMILES strings from the training set.
    model:
        Trained VAE model (optional -- needed for reconstruction).
    dataset:
        Training dataset (optional -- needed for reconstruction).
    vocab:
        Vocabulary (optional -- needed for reconstruction).
    device:
        Torch device string for reconstruction evaluation.
    max_recon_samples:
        Cap on reconstruction evaluation sample count.
    diversity_n_sample:
        Cap on pairwise diversity comparison count.

    Returns
    -------
    VaeMetricsResult:
        Aggregated quality metrics.
    """
    # FCD
    fcd = compute_fcd(generated_smiles, training_smiles)

    # Reconstruction accuracy
    recon: float | None = None
    if model is not None and dataset is not None and vocab is not None:
        recon = compute_reconstruction_accuracy(
            model, dataset, vocab, device=device,
            max_samples=max_recon_samples,
        )

    # Novelty (always computable -- pure Python fallback)
    novelty = compute_novelty(generated_smiles, training_smiles)

    # Internal diversity
    diversity = compute_internal_diversity(
        generated_smiles, n_sample=diversity_n_sample,
    )

    # Count novel molecules
    training_canonical = {_canonicalize(s) for s in training_smiles}
    n_novel = sum(
        1 for s in generated_smiles
        if _canonicalize(s) not in training_canonical
    )

    return VaeMetricsResult(
        fcd_score=fcd,
        reconstruction_accuracy=recon,
        novelty=novelty,
        internal_diversity=diversity,
        n_generated=len(generated_smiles),
        n_valid=len(generated_smiles),
        n_novel=n_novel,
    )
