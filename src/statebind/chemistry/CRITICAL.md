# Critical Information -- Chemistry

- `HAS_RDKIT` flag at `fingerprints.py:19-29` gates all RDKit-dependent code. Check this before calling any chemistry function.
- `_REFERENCE_BINDERS` in `baselines/scoring.py:59-66` are the canonical EGFR binder SMILES. The first 3 entries in `docking_data.py:EGFR_BINDERS` MUST match these exactly.
- DockingProxy singleton trains on first call to `get_default_proxy()` — ~0.5s with RDKit, instant no-op without RDKit. See `docking_proxy.py`.
- Feature vector: 13 top-variance Morgan FP bits + 7 descriptors (MW, LogP, TPSA, HBA, HBD, rings, rotatable bonds) = 20 features. See `docking_proxy.py:_featurize()`.
- Proxy returns 0.5 for ALL predictions when RDKit is unavailable — functionally identical to the docking stub. See `docking_proxy.py:predict()`.
- Training data is embedded as constants in `docking_data.py` — 9 binders + 25 decoys. No external files needed.
- The singleton `_DEFAULT_PROXY` uses double-checked locking with `threading.Lock`. Reset it by setting `docking_proxy._DEFAULT_PROXY = None` (only in tests).
- `get_default_proxy()` catches all exceptions during training (including import errors). If training fails, the proxy stays unfitted and returns 0.5.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
