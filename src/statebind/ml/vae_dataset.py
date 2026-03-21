"""Dataset and collation utilities for SMILES VAE training.

Loads SMILES strings with conformational state labels from JSON files,
tokenizes and encodes them using the project's :class:`~statebind.ml.tokenizer.SMILESTokenizer`
and :class:`~statebind.ml.vocabulary.Vocabulary`, and yields padded
batches suitable for the :class:`~statebind.ml.vae.ConditionalSMILESVAE`.

Classes:
    SMILESDatasetConfig  -- Pydantic configuration for dataset construction.
    SMILESDataset        -- PyTorch Dataset of tokenized SMILES with state labels.

Functions:
    collate_smiles       -- Custom collate that pads sequences to batch max length.
    load_smiles_dataset  -- Convenience loader from JSON/CSV files.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from statebind.ml.tokenizer import SMILESTokenizer
from statebind.ml.vocabulary import Vocabulary

try:
    import torch

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default conformational state mapping
# ---------------------------------------------------------------------------

DEFAULT_STATE_MAPPING: dict[str, int] = {
    "DFGin_aCin": 0,
    "DFGin_aCout": 1,
    "DFGout_aCin": 2,
    "DFGout_aCout": 3,
}


def _require_torch() -> None:
    """Raise RuntimeError if torch is not installed."""
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for SMILESDataset but is not installed. "
            "Install it with: pip install torch"
        )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class SMILESDatasetConfig(BaseModel):
    """Configuration for building a :class:`SMILESDataset`.

    Parameters
    ----------
    max_len:
        Maximum sequence length (including SOS and EOS tokens).  Sequences
        longer than this are truncated.
    n_states:
        Number of conformational states for the one-hot encoding.
    state_mapping:
        Mapping from state label strings to integer indices.  Must cover
        all states present in the data.  Defaults to the four EGFR
        conformational states.
    add_sos:
        Whether to prepend the SOS token during encoding.
    add_eos:
        Whether to append the EOS token during encoding.
    """

    max_len: int = Field(default=128, description="Maximum sequence length including SOS/EOS")
    n_states: int = Field(default=4, description="Number of conformational states")
    state_mapping: dict[str, int] = Field(
        default_factory=lambda: dict(DEFAULT_STATE_MAPPING),
        description="State label -> integer index mapping",
    )
    add_sos: bool = True
    add_eos: bool = True


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class SMILESDataset:
    """Dataset of tokenized SMILES strings with conformational state labels.

    Each item returns a tuple of:

    - ``token_indices`` — :class:`torch.LongTensor` of shape ``(seq_len,)``,
      the encoded SMILES with SOS/EOS tokens.
    - ``length`` — ``int``, the actual (un-padded) sequence length.
    - ``state_onehot`` — :class:`torch.FloatTensor` of shape ``(n_states,)``,
      one-hot state conditioning vector.

    The dataset does **not** pad sequences; padding is deferred to
    :func:`collate_smiles` so that each batch is padded to its own
    maximum length rather than a global maximum.

    Parameters
    ----------
    smiles_list:
        Raw SMILES strings.
    state_labels:
        Conformational state label for each SMILES (same length as
        *smiles_list*).
    tokenizer:
        A :class:`~statebind.ml.tokenizer.SMILESTokenizer` instance.
    vocab:
        A :class:`~statebind.ml.vocabulary.Vocabulary` instance.
    config:
        Dataset configuration.
    """

    def __init__(
        self,
        smiles_list: list[str],
        state_labels: list[str],
        tokenizer: SMILESTokenizer,
        vocab: Vocabulary,
        config: SMILESDatasetConfig | None = None,
    ) -> None:
        _require_torch()

        if len(smiles_list) != len(state_labels):
            raise ValueError(
                f"Length mismatch: {len(smiles_list)} SMILES vs "
                f"{len(state_labels)} state labels"
            )

        self.config = config or SMILESDatasetConfig()
        self.tokenizer = tokenizer
        self.vocab = vocab

        # Pre-encode all sequences
        self._encoded: list[torch.Tensor] = []
        self._state_onehots: list[torch.Tensor] = []
        self._lengths: list[int] = []

        n_skipped = 0
        for smiles, state in zip(smiles_list, state_labels):
            # Validate state label
            if state not in self.config.state_mapping:
                logger.warning(
                    "Unknown state label '%s' for SMILES '%s' — skipping",
                    state, smiles,
                )
                n_skipped += 1
                continue

            # Tokenize and encode
            tokens = self.tokenizer.tokenize(smiles)
            indices = self.vocab.encode(
                tokens,
                add_sos=self.config.add_sos,
                add_eos=self.config.add_eos,
            )

            # Truncate to max_len
            if len(indices) > self.config.max_len:
                indices = indices[: self.config.max_len]

            self._encoded.append(torch.tensor(indices, dtype=torch.long))
            self._lengths.append(len(indices))

            # Build one-hot state vector
            state_idx = self.config.state_mapping[state]
            onehot = torch.zeros(self.config.n_states, dtype=torch.float)
            onehot[state_idx] = 1.0
            self._state_onehots.append(onehot)

        if n_skipped > 0:
            logger.info(
                "Skipped %d / %d entries with unknown state labels",
                n_skipped, len(smiles_list),
            )

    def __len__(self) -> int:
        return len(self._encoded)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int, torch.Tensor]:
        """Return (token_indices, length, state_onehot) for item *idx*."""
        return self._encoded[idx], self._lengths[idx], self._state_onehots[idx]


# ---------------------------------------------------------------------------
# Collation
# ---------------------------------------------------------------------------


def collate_smiles(
    batch: list[tuple[torch.Tensor, int, torch.Tensor]],
    pad_idx: int = 0,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Collate a list of dataset items into a padded batch.

    Pads token sequences to the maximum length within the batch (not the
    global ``max_len``), which is more memory-efficient for batches of
    short sequences.

    Parameters
    ----------
    batch:
        A list of ``(token_indices, length, state_onehot)`` tuples as
        returned by :meth:`SMILESDataset.__getitem__`.
    pad_idx:
        Token index used for padding (default: 0, matching
        :class:`~statebind.ml.vocabulary.Vocabulary` conventions).

    Returns
    -------
    tuple[Tensor, Tensor, Tensor]:
        - ``tokens`` — :class:`torch.LongTensor` of shape ``(batch, max_len_in_batch)``.
        - ``lengths`` — :class:`torch.LongTensor` of shape ``(batch,)``.
        - ``state_onehots`` — :class:`torch.FloatTensor` of shape ``(batch, n_states)``.
    """
    _require_torch()

    token_seqs, lengths, state_vecs = zip(*batch)

    # Pad to the maximum length in this specific batch
    max_len = max(lengths)
    padded: list[torch.Tensor] = []
    for seq in token_seqs:
        pad_size = max_len - len(seq)
        if pad_size > 0:
            padding = torch.full((pad_size,), pad_idx, dtype=torch.long)
            padded.append(torch.cat([seq, padding]))
        else:
            padded.append(seq)

    tokens = torch.stack(padded, dim=0)
    lengths_tensor = torch.tensor(lengths, dtype=torch.long)
    state_onehots = torch.stack(list(state_vecs), dim=0)

    return tokens, lengths_tensor, state_onehots


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def load_smiles_dataset(
    path: Path | str,
    tokenizer: SMILESTokenizer,
    vocab: Vocabulary,
    config: SMILESDatasetConfig | None = None,
) -> SMILESDataset:
    """Load a :class:`SMILESDataset` from a JSON file.

    The JSON file must contain a list of objects, each with at least
    ``"smiles"`` and ``"state"`` keys::

        [
            {"smiles": "c1ccc(NC(=O)...)cc1", "state": "DFGin_aCin"},
            {"smiles": "CC(=O)Nc1ccc...",     "state": "DFGout_aCout"},
            ...
        ]

    CSV files (with ``smiles`` and ``state`` columns) are also supported.

    Parameters
    ----------
    path:
        Path to the JSON or CSV data file.
    tokenizer:
        A :class:`~statebind.ml.tokenizer.SMILESTokenizer` instance.
    vocab:
        A :class:`~statebind.ml.vocabulary.Vocabulary` instance.
    config:
        Optional dataset configuration.  If ``None``, defaults are used.

    Returns
    -------
    SMILESDataset:
        The constructed dataset ready for use with a
        :class:`~torch.utils.data.DataLoader`.

    Raises
    ------
    FileNotFoundError:
        If *path* does not exist.
    ValueError:
        If the file format is unsupported or records are missing required
        keys.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".json":
        with open(path) as f:
            records: list[dict] = json.load(f)
    elif suffix == ".csv":
        import csv

        records = []
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
    else:
        raise ValueError(
            f"Unsupported file format '{suffix}'. Expected .json or .csv."
        )

    # Validate and extract fields
    smiles_list: list[str] = []
    state_labels: list[str] = []

    for i, record in enumerate(records):
        if "smiles" not in record:
            raise ValueError(f"Record {i} is missing the 'smiles' key: {record}")
        if "state" not in record:
            raise ValueError(f"Record {i} is missing the 'state' key: {record}")
        smiles_list.append(record["smiles"])
        state_labels.append(record["state"])

    logger.info("Loaded %d records from %s", len(records), path)

    return SMILESDataset(
        smiles_list=smiles_list,
        state_labels=state_labels,
        tokenizer=tokenizer,
        vocab=vocab,
        config=config,
    )
