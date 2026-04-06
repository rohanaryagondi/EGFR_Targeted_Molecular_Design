"""Regex-based SMILES and SELFIES tokenizers.

Correctly splits SMILES strings into chemically meaningful tokens,
handling multi-character atoms (Cl, Br, Si, Se), bracketed atoms
([nH], [C@@H], [O-], [N+]), ring closures (single and double-digit),
bonds, branches, and aromatic atoms.

Also provides a :class:`SELFIESTokenizer` that uses the ``selfies``
library for bracket-delimited tokenization.  SELFIES guarantees that
every generated string decodes to a valid molecule.
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


class SELFIESTokenizer:
    """Tokenizer for SELFIES molecular representations.

    SELFIES (SELF-referencing Embedded Strings) use bracket-delimited
    tokens (e.g. ``[C]``, ``[=N]``, ``[Branch1]``).  Every SELFIES
    string decodes to a valid molecule, eliminating the need for
    post-hoc validity filtering during generation.

    Requires the ``selfies`` package: ``pip install selfies``.

    Examples
    --------
    >>> tok = SELFIESTokenizer()
    >>> tok.tokenize("[C][=C][C][=O]")
    ['[C]', '[=C]', '[C]', '[=O]']
    >>> tok.smiles_to_selfies("CCO")
    '[C][C][O]'
    """

    def __init__(self) -> None:
        try:
            import selfies as sf

            self._sf = sf
        except ImportError as exc:
            raise ImportError(
                "SELFIESTokenizer requires the 'selfies' package. "
                "Install with: pip install selfies"
            ) from exc
        self._bracket_re: re.Pattern[str] = re.compile(r"\[[^\]]*\]")

    def tokenize(self, selfies_str: str) -> list[str]:
        """Split a SELFIES string into bracket-delimited tokens."""
        return self._bracket_re.findall(selfies_str)

    def detokenize(self, tokens: list[str]) -> str:
        """Join tokens back into a SELFIES string."""
        return "".join(tokens)

    def smiles_to_selfies(self, smiles: str) -> str | None:
        """Convert a SMILES string to its SELFIES representation.

        Returns ``None`` if the conversion fails.
        """
        try:
            return self._sf.encoder(smiles)
        except Exception:
            return None

    def selfies_to_smiles(self, selfies_str: str) -> str | None:
        """Convert a SELFIES string back to SMILES.

        Returns ``None`` if the conversion fails.
        """
        try:
            return self._sf.decoder(selfies_str)
        except Exception:
            return None

    def is_valid_tokenization(self, selfies_str: str) -> bool:
        """Check whether tokenization is lossless."""
        tokens = self.tokenize(selfies_str)
        return self.detokenize(tokens) == selfies_str
