"""Regex-based SMILES tokenizer.

Correctly splits SMILES strings into chemically meaningful tokens,
handling multi-character atoms (Cl, Br, Si, Se), bracketed atoms
([nH], [C@@H], [O-], [N+]), ring closures (single and double-digit),
bonds, branches, and aromatic atoms.
"""

from __future__ import annotations

import re

# Ordered so that multi-character patterns match before single-character ones.
# - Bracketed atoms: [nH], [C@@H], [O-], etc.
# - Two-letter atoms: Br, Cl, Si, Se, se, Te, te
# - Double-digit ring closures: %10, %11, etc.
# - Single-character atoms, bonds, branches, digits
SMILES_REGEX = (
    r"("
    r"\[[^\]]+\]"       # bracketed atoms: [nH], [C@@H], [O-], [N+], etc.
    r"|Br|Cl"           # two-letter halogens
    r"|Si|Se|se|Te|te"  # other multi-char atoms
    r"|[BCNOPSFIbcnops]"  # single-letter atoms (organic subset + aromatic)
    r"|%\d{2}"          # double-digit ring closures: %10, %11, ...
    r"|\d"              # single-digit ring closures: 1-9
    r"|[=#:/\\()\.\-\+]"  # bonds, branches, dot, charges
    r")"
)


class SMILESTokenizer:
    """Regex-based SMILES tokenizer.

    Correctly splits SMILES strings into chemically meaningful tokens.

    Examples
    --------
    >>> tok = SMILESTokenizer()
    >>> tok.tokenize("c1ccccc1")
    ['c', '1', 'c', 'c', 'c', 'c', 'c', '1']
    >>> tok.tokenize("[C@@H](Cl)Br")
    ['[C@@H]', '(', 'Cl', ')', 'Br']
    """

    def __init__(self) -> None:
        self.pattern: re.Pattern[str] = re.compile(SMILES_REGEX)

    def tokenize(self, smiles: str) -> list[str]:
        """Split a SMILES string into chemically meaningful tokens.

        Parameters
        ----------
        smiles:
            A SMILES string to tokenize.

        Returns
        -------
        list[str]:
            Ordered list of tokens extracted from *smiles*.
        """
        return self.pattern.findall(smiles)

    def detokenize(self, tokens: list[str]) -> str:
        """Join tokens back into a SMILES string.

        Parameters
        ----------
        tokens:
            List of SMILES tokens.

        Returns
        -------
        str:
            Concatenated SMILES string.
        """
        return "".join(tokens)

    def is_valid_tokenization(self, smiles: str) -> bool:
        """Check whether tokenization is lossless.

        Returns ``True`` if tokenizing *smiles* and then detokenizing
        produces the original string (no characters lost).

        Parameters
        ----------
        smiles:
            A SMILES string to check.

        Returns
        -------
        bool:
            ``True`` when ``detokenize(tokenize(smiles)) == smiles``.
        """
        tokens = self.tokenize(smiles)
        return self.detokenize(tokens) == smiles
