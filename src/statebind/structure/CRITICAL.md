# Critical Information -- Structure

- Structural features are LITERATURE-CURATED values, NOT computed from PDB coordinates -- `features.py:1-15` explicitly documents this.
- 16 structures classified into 4 conformational states (DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout) -- curated in `features.py:40+`.
- Pocket volumes are approximate estimates from literature, not calculated by fpocket/SiteMap -- `features.py:38`.
- Feature vectors are 9-dimensional: dfg_asp_phe_dist, dfg_phe_position, ac_helix_salt_bridge, ac_helix_rotation, p_loop_displacement, hinge_angle, activation_loop_rmsd, gatekeeper_sidechain, pocket_volume -- `features.py:43-49`.
- `_curated_features()` at `features.py:28` returns `dict[str, tuple[StructuralFeatures, PocketDescriptor]]` keyed by PDB ID.
- `PocketDescriptor` includes `back_pocket_accessible`, `covalent_cys_exposed`, `gatekeeper_clearance`, `hinge_accessibility`, `p_loop_conformation` -- `features.py:50-54`.
- This module depends on `processing.models.ConformationalState` for state labels -- `features.py:19`.
- Future phases plan to compute features from PDB coordinates using BioPython or MDAnalysis -- `features.py:12-14`.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
