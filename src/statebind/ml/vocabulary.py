"""Token-to-index vocabulary for SMILES tokens.

Provides a ``Vocabulary`` class that maintains a bidirectional mapping
between string tokens and integer indices, with dedicated special tokens
for padding, start/end of sequence, and unknown tokens.  Also provides
``build_vocabulary`` for constructing a vocabulary from a corpus of
SMILES strings.
"""

from __future__ import annotations

import json

from statebind.ml.tokenizer import SMILESTokenizer


class Vocabulary:
    """Token-to-index mapping for SMILES tokens.

    Special tokens (always present, always occupy indices 0-3):

    ======= ===== ===========
    Token   Index Purpose
    ======= ===== ===========
    <pad>   0     Padding for batching
    <sos>   1     Start of sequence
    <eos>   2     End of sequence
    <unk>   3     Unknown / out-of-vocabulary token
    ======= ===== ===========

    Examples
    --------
    >>> vocab = Vocabulary()
    >>> vocab.add_token("C")
    4
    >>> vocab.encode(["C", "=", "O"])
    [1, 4, 3, 3, 2]
    """

    PAD: str = "<pad>"
    SOS: str = "<sos>"
    EOS: str = "<eos>"
    UNK: str = "<unk>"
    SPECIAL_TOKENS: list[str] = [PAD, SOS, EOS, UNK]

    def __init__(self) -> None:
        self.token_to_idx: dict[str, int] = {}
        self.idx_to_token: dict[int, str] = {}
        # Special tokens always occupy the first indices.
        for i, tok in enumerate(self.SPECIAL_TOKENS):
            self.token_to_idx[tok] = i
            self.idx_to_token[i] = tok

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Total number of tokens (including special tokens)."""
        return len(self.token_to_idx)

    @property
    def pad_idx(self) -> int:
        """Index of the ``<pad>`` token."""
        return self.token_to_idx[self.PAD]

    @property
    def sos_idx(self) -> int:
        """Index of the ``<sos>`` token."""
        return self.token_to_idx[self.SOS]

    @property
    def eos_idx(self) -> int:
        """Index of the ``<eos>`` token."""
        return self.token_to_idx[self.EOS]

    @property
    def unk_idx(self) -> int:
        """Index of the ``<unk>`` token."""
        return self.token_to_idx[self.UNK]

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def add_token(self, token: str) -> int:
        """Add *token* to the vocabulary if absent and return its index.

        Parameters
        ----------
        token:
            The token string to add.

        Returns
        -------
        int:
            The integer index assigned to *token*.
        """
        if token not in self.token_to_idx:
            idx = len(self.token_to_idx)
            self.token_to_idx[token] = idx
            self.idx_to_token[idx] = token
        return self.token_to_idx[token]

    # ------------------------------------------------------------------
    # Encode / Decode
    # ------------------------------------------------------------------

    def encode(
        self,
        tokens: list[str],
        add_sos: bool = True,
        add_eos: bool = True,
    ) -> list[int]:
        """Convert a list of tokens to a list of integer indices.

        Tokens not in the vocabulary are mapped to the ``<unk>`` index.

        Parameters
        ----------
        tokens:
            Ordered SMILES tokens (e.g. from ``SMILESTokenizer.tokenize``).
        add_sos:
            If ``True``, prepend the ``<sos>`` index.
        add_eos:
            If ``True``, append the ``<eos>`` index.

        Returns
        -------
        list[int]:
            Integer-encoded sequence.
        """
        unk = self.unk_idx
        indices: list[int] = [self.token_to_idx.get(t, unk) for t in tokens]
        if add_sos:
            indices.insert(0, self.sos_idx)
        if add_eos:
            indices.append(self.eos_idx)
        return indices

    def decode(
        self,
        indices: list[int],
        strip_special: bool = True,
    ) -> list[str]:
        """Convert a list of integer indices back to tokens.

        Parameters
        ----------
        indices:
            Integer-encoded sequence.
        strip_special:
            If ``True``, remove ``<pad>``, ``<sos>``, and ``<eos>`` tokens
            from the output.  ``<unk>`` is always preserved so the caller
            can see where information was lost.

        Returns
        -------
        list[str]:
            Decoded token list.
        """
        special = {self.PAD, self.SOS, self.EOS}
        tokens: list[str] = []
        for idx in indices:
            token = self.idx_to_token.get(idx, self.UNK)
            if strip_special and token in special:
                continue
            tokens.append(token)
        return tokens

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """Serialize the vocabulary to a JSON string.

        Returns
        -------
        str:
            JSON string representation that can be round-tripped via
            ``Vocabulary.from_json``.
        """
        payload = {
            "token_to_idx": self.token_to_idx,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> Vocabulary:
        """Reconstruct a ``Vocabulary`` from a JSON string.

        Parameters
        ----------
        json_str:
            JSON string previously produced by ``to_json``.

        Returns
        -------
        Vocabulary:
            Restored vocabulary with identical token-to-index mapping.
        """
        payload = json.loads(json_str)
        vocab = cls.__new__(cls)
        vocab.token_to_idx = {}
        vocab.idx_to_token = {}
        for token, idx in payload["token_to_idx"].items():
            idx_int = int(idx)
            vocab.token_to_idx[token] = idx_int
            vocab.idx_to_token[idx_int] = token
        return vocab

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self.size

    def __contains__(self, token: str) -> bool:
        return token in self.token_to_idx

    def __repr__(self) -> str:
        return f"Vocabulary(size={self.size})"


# ------------------------------------------------------------------
# Factory
# ------------------------------------------------------------------


def build_vocabulary(
    smiles_list: list[str],
    tokenizer: SMILESTokenizer | None = None,
) -> Vocabulary:
    """Build a ``Vocabulary`` from a corpus of SMILES strings.

    Every unique token found across *smiles_list* is added to the
    vocabulary.  Special tokens (``<pad>``, ``<sos>``, ``<eos>``,
    ``<unk>``) are always present regardless of the input corpus.

    Parameters
    ----------
    smiles_list:
        SMILES strings to extract tokens from.
    tokenizer:
        An optional pre-constructed tokenizer.  If ``None`` a default
        ``SMILESTokenizer`` is created.

    Returns
    -------
    Vocabulary:
        A vocabulary containing all unique tokens found in the corpus
        plus the four special tokens.
    """
    if tokenizer is None:
        tokenizer = SMILESTokenizer()

    vocab = Vocabulary()
    for smi in smiles_list:
        for token in tokenizer.tokenize(smi):
            vocab.add_token(token)
    return vocab
