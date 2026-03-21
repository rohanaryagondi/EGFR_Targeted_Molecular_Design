"""Message Passing Neural Network (MPNN) for binding affinity prediction.

Predicts pIC50 binding affinity from molecular graphs produced by
:func:`statebind.ml.graphs.smiles_to_graph`.  Intended to replace the
docking-proxy stub (which returns a constant 0.5) in the ranking pipeline.

Architecture overview::

    Atom features (ATOM_FEATURE_DIM=35) -> Linear -> hidden_dim
                         |
    Message Passing x n_layers:
        NNConv(hidden_dim, hidden_dim, edge_nn)
        BatchNorm1d(hidden_dim)
        ReLU + residual connection
                         |
    Graph-level readout:
        "mean_max" -> concat(global_mean_pool, global_max_pool) -> 2*hidden_dim
        "set2set"  -> Set2Set(hidden_dim, processing_steps)      -> 2*hidden_dim
                         |
    Prediction head:
        Linear(2*hidden_dim, hidden_dim) -> ReLU -> Dropout -> Linear(hidden_dim, 1)

Optional dependencies:
    torch             -- core neural network operations
    torch_geometric   -- NNConv, pooling, Set2Set, BatchNorm
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator

from statebind.ml.graphs import ATOM_FEATURE_DIM, BOND_FEATURE_DIM

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------

try:
    import torch
    import torch.nn as nn

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from torch_geometric.nn import (
        BatchNorm,
        NNConv,
        Set2Set,
        global_max_pool,
        global_mean_pool,
    )

    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False

if TYPE_CHECKING:
    from torch import Tensor
    from torch_geometric.data import Batch, Data

# Conditional base class: use nn.Module when torch is available,
# otherwise plain object so the module can be imported without torch.
_ModuleBase = nn.Module if HAS_TORCH else object

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime guard helper
# ---------------------------------------------------------------------------

def _require_deps() -> None:
    """Raise RuntimeError if torch or torch_geometric is not installed."""
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for the MPNN model but is not installed. "
            "Install it with: pip install torch"
        )
    if not HAS_TORCH_GEOMETRIC:
        raise RuntimeError(
            "PyTorch Geometric is required for the MPNN model but is not "
            "installed.  Install it with: pip install torch_geometric"
        )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class MPNNConfig(BaseModel):
    """Pydantic configuration for :class:`AffinityMPNN`.

    Attributes:
        atom_feature_dim: Input atom feature dimension (must match
            :data:`~statebind.ml.graphs.ATOM_FEATURE_DIM`).
        bond_feature_dim: Input bond feature dimension (must match
            :data:`~statebind.ml.graphs.BOND_FEATURE_DIM`).
        hidden_dim: Hidden layer width for message passing and prediction head.
        n_message_passing_layers: Number of stacked message-passing layers.
        dropout: Dropout probability in the prediction head.
        readout: Graph-level aggregation method.  ``"mean_max"`` concatenates
            global mean and max pooling.  ``"set2set"`` uses a Set2Set readout.
        set2set_steps: Number of processing steps for Set2Set (only used when
            ``readout == "set2set"``).
    """

    atom_feature_dim: int = Field(
        default=ATOM_FEATURE_DIM,
        description="Input atom feature dimension from graph encoder.",
    )
    bond_feature_dim: int = Field(
        default=BOND_FEATURE_DIM,
        description="Input bond feature dimension from graph encoder.",
    )
    hidden_dim: int = Field(default=128, ge=8, description="Hidden layer width.")
    n_message_passing_layers: int = Field(
        default=3, ge=1, le=10, description="Number of message-passing layers."
    )
    dropout: float = Field(
        default=0.1, ge=0.0, le=0.5, description="Dropout probability."
    )
    readout: Literal["mean_max", "set2set"] = Field(
        default="mean_max", description="Graph-level readout method."
    )
    set2set_steps: int = Field(
        default=3, ge=1, description="Set2Set processing steps."
    )

    @field_validator("atom_feature_dim", "bond_feature_dim")
    @classmethod
    def _positive_dim(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"Feature dimension must be >= 1, got {v}")
        return v


# ---------------------------------------------------------------------------
# Sub-modules
# ---------------------------------------------------------------------------


class EdgeNetwork(_ModuleBase):
    """Transform bond features into NNConv message weight matrices.

    Maps a bond feature vector of size ``bond_feature_dim`` to a matrix of
    shape ``(hidden_dim, hidden_dim)`` that the :class:`NNConv` layer uses to
    weight messages.

    Args:
        bond_feature_dim: Dimension of the bond feature vector.
        hidden_dim: Node hidden dimension (message weight matrix is
            ``hidden_dim x hidden_dim``).
    """

    def __init__(self, bond_feature_dim: int, hidden_dim: int) -> None:
        _require_deps()
        super().__init__()
        self.nn = nn.Sequential(
            nn.Linear(bond_feature_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, hidden_dim * hidden_dim),
        )

    def forward(self, edge_attr: Tensor) -> Tensor:
        """Compute message weight matrices from bond features.

        Args:
            edge_attr: Bond feature tensor of shape ``(num_edges, bond_feature_dim)``.

        Returns:
            Weight matrices of shape ``(num_edges, hidden_dim * hidden_dim)``.
        """
        return self.nn(edge_attr)


class MPNNLayer(_ModuleBase):
    """Single message-passing layer: NNConv + BatchNorm + ReLU + residual.

    The residual connection is applied when the input and output dimensions
    match (which they always do after the initial linear projection).

    Args:
        hidden_dim: Node hidden dimension.
        bond_feature_dim: Bond feature dimension (passed to :class:`EdgeNetwork`).
    """

    def __init__(self, hidden_dim: int, bond_feature_dim: int) -> None:
        _require_deps()
        super().__init__()
        self.edge_nn = EdgeNetwork(bond_feature_dim, hidden_dim)
        self.conv = NNConv(
            in_channels=hidden_dim,
            out_channels=hidden_dim,
            nn=self.edge_nn.nn,
            aggr="add",
        )
        self.bn = BatchNorm(hidden_dim)
        self.act = nn.ReLU()

    def forward(
        self,
        x: Tensor,
        edge_index: Tensor,
        edge_attr: Tensor,
    ) -> Tensor:
        """Run one round of message passing.

        Args:
            x: Node features of shape ``(num_nodes, hidden_dim)``.
            edge_index: COO edge index of shape ``(2, num_edges)``.
            edge_attr: Bond features of shape ``(num_edges, bond_feature_dim)``.

        Returns:
            Updated node features of shape ``(num_nodes, hidden_dim)``.
        """
        residual = x
        out = self.conv(x, edge_index, edge_attr)
        out = self.bn(out)
        out = self.act(out)
        # Residual connection (dims always match after initial projection)
        out = out + residual
        return out


# ---------------------------------------------------------------------------
# Full model
# ---------------------------------------------------------------------------


class AffinityMPNN(_ModuleBase):
    """Message Passing Neural Network for molecular binding affinity prediction.

    Consumes PyTorch Geometric :class:`Data` objects produced by
    :func:`~statebind.ml.graphs.smiles_to_graph` and outputs a predicted
    pIC50 value (continuous regression target).

    The forward pass is::

        atom features -> linear projection -> message passing layers
                      -> graph-level readout -> prediction MLP -> pIC50

    Args:
        config: An :class:`MPNNConfig` instance with model hyper-parameters.
            If ``None``, default values are used.

    Example::

        from statebind.ml.mpnn import AffinityMPNN, MPNNConfig
        from statebind.ml.graphs import smiles_to_graph
        from torch_geometric.data import Batch

        config = MPNNConfig(hidden_dim=64, n_message_passing_layers=2)
        model = AffinityMPNN(config)

        graphs = [smiles_to_graph("CCO"), smiles_to_graph("c1ccccc1")]
        batch = Batch.from_data_list([g for g in graphs if g is not None])
        pred = model(batch)  # shape: (batch_size, 1)
    """

    def __init__(self, config: MPNNConfig | None = None) -> None:
        _require_deps()
        super().__init__()

        if config is None:
            config = MPNNConfig()

        self.config = config

        # --- Initial atom feature projection --------------------------------
        self.atom_encoder = nn.Linear(config.atom_feature_dim, config.hidden_dim)

        # --- Message passing layers -----------------------------------------
        self.mp_layers = nn.ModuleList([
            MPNNLayer(config.hidden_dim, config.bond_feature_dim)
            for _ in range(config.n_message_passing_layers)
        ])

        # --- Graph-level readout --------------------------------------------
        readout_dim: int
        if config.readout == "set2set":
            self.set2set = Set2Set(
                in_channels=config.hidden_dim,
                processing_steps=config.set2set_steps,
            )
            readout_dim = config.hidden_dim * 2  # Set2Set doubles the dim
        else:
            # "mean_max": concatenate global_mean_pool and global_max_pool
            self.set2set = None
            readout_dim = config.hidden_dim * 2  # mean + max concatenated

        # --- Prediction head ------------------------------------------------
        self.prediction_head = nn.Sequential(
            nn.Linear(readout_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, 1),
        )

    def forward(self, data: Data | Batch) -> Tensor:
        """Predict pIC50 binding affinity for a batch of molecular graphs.

        Args:
            data: A PyTorch Geometric :class:`~torch_geometric.data.Data` or
                :class:`~torch_geometric.data.Batch` object with attributes:

                - ``x`` — atom features ``(num_nodes, atom_feature_dim)``
                - ``edge_index`` — COO edge index ``(2, num_edges)``
                - ``edge_attr`` — bond features ``(num_edges, bond_feature_dim)``
                - ``batch`` — batch assignment vector (present in Batch objects;
                  for a single Data object, all-zeros is assumed)

        Returns:
            Predicted pIC50 values of shape ``(batch_size, 1)``.
        """
        x: Tensor = data.x
        edge_index: Tensor = data.edge_index
        edge_attr: Tensor = data.edge_attr

        # Batch vector: for single graphs, create an all-zeros vector
        batch_vec: Tensor
        if hasattr(data, "batch") and data.batch is not None:
            batch_vec = data.batch
        else:
            batch_vec = torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        # --- Initial projection ---------------------------------------------
        x = self.atom_encoder(x)
        x = torch.relu(x)

        # --- Message passing ------------------------------------------------
        for mp_layer in self.mp_layers:
            x = mp_layer(x, edge_index, edge_attr)

        # --- Graph-level readout --------------------------------------------
        if self.config.readout == "set2set" and self.set2set is not None:
            graph_repr = self.set2set(x, batch_vec)
        else:
            # mean_max: concatenate mean-pool and max-pool
            mean_pool = global_mean_pool(x, batch_vec)
            max_pool = global_max_pool(x, batch_vec)
            graph_repr = torch.cat([mean_pool, max_pool], dim=-1)

        # --- Prediction head ------------------------------------------------
        out = self.prediction_head(graph_repr)
        return out
