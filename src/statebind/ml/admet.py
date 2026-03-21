"""Multi-task ADMET predictor with shared GNN backbone and task-specific heads.

Predicts multiple drug-safety / pharmacokinetic endpoints simultaneously from
a molecular graph representation.  The architecture uses a shared Graph
Isomorphism Network (GIN) or Graph Convolution Network (GCN) backbone followed
by task-specific prediction heads — one per ADMET endpoint.

Supported endpoints (default):
    caco2           Caco-2 permeability (regression)
    herg            hERG inhibition (classification)
    cyp3a4          CYP3A4 inhibition (classification)
    clearance       Hepatic clearance (regression)
    lipophilicity   LogD / LogP (regression)
    solubility      Aqueous solubility (regression)

Architecture::

    Atom features → Linear(atom_dim, hidden_dim)
                            ↓
    Shared GNN Backbone (N GIN/GCN layers):
      For each layer:
        - GINConv or GCNConv(hidden_dim, hidden_dim)
        - BatchNorm1d(hidden_dim)
        - ReLU
        - Dropout
                            ↓
    Graph readout: global_mean_pool + global_max_pool → concat → (2*hidden_dim)
                            ↓
    Shared projection: Linear(2*hidden_dim, hidden_dim) → ReLU → Dropout
                            ↓
    Task-specific heads (one per ADMET endpoint):
      Each: Linear(hidden_dim, hidden_dim//2) → ReLU → Dropout → Linear(hidden_dim//2, 1)

Optional dependencies:
    torch             — required for model definition and training
    torch_geometric   — required for GNN layers and graph pooling
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

try:
    import torch
    import torch.nn as nn

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from torch_geometric.nn import GCNConv, GINConv, global_max_pool, global_mean_pool

    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False

if TYPE_CHECKING:
    from torch import Tensor
    from torch_geometric.data import Batch, Data

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_TASK_NAMES: list[str] = [
    "caco2",
    "herg",
    "cyp3a4",
    "clearance",
    "lipophilicity",
    "solubility",
]

_DEFAULT_TASK_TYPES: dict[str, str] = {
    "caco2": "regression",
    "herg": "classification",
    "cyp3a4": "classification",
    "clearance": "regression",
    "lipophilicity": "regression",
    "solubility": "regression",
}


# ---------------------------------------------------------------------------
# Pydantic configuration
# ---------------------------------------------------------------------------


class ADMETConfig(BaseModel):
    """Configuration for the multi-task ADMET predictor.

    Attributes:
        atom_feature_dim: Dimensionality of input atom features (must match
            :data:`statebind.ml.graphs.ATOM_FEATURE_DIM`).
        bond_feature_dim: Dimensionality of input bond features (must match
            :data:`statebind.ml.graphs.BOND_FEATURE_DIM`).
        hidden_dim: Hidden dimensionality used throughout the GNN backbone and
            shared projection layer.
        n_gnn_layers: Number of message-passing layers in the shared backbone.
        dropout: Dropout probability applied after each activation.
        task_names: Ordered list of ADMET endpoint names.
        task_types: Mapping from task name to ``"regression"`` or
            ``"classification"``.  Every entry in *task_names* must have a
            corresponding entry here.
        gnn_type: GNN layer type — ``"gin"`` (Graph Isomorphism Network) or
            ``"gcn"`` (Graph Convolutional Network).
    """

    atom_feature_dim: int = 35
    bond_feature_dim: int = 11
    hidden_dim: int = 128
    n_gnn_layers: int = 3
    dropout: float = 0.2
    task_names: list[str] = Field(default_factory=lambda: list(_DEFAULT_TASK_NAMES))
    task_types: dict[str, str] = Field(
        default_factory=lambda: dict(_DEFAULT_TASK_TYPES)
    )
    gnn_type: str = "gin"

    @field_validator("gnn_type")
    @classmethod
    def _validate_gnn_type(cls, v: str) -> str:
        allowed = {"gin", "gcn"}
        if v not in allowed:
            raise ValueError(f"gnn_type must be one of {allowed}, got {v!r}")
        return v

    @field_validator("task_types")
    @classmethod
    def _validate_task_types(cls, v: dict[str, str]) -> dict[str, str]:
        allowed_types = {"regression", "classification"}
        for name, ttype in v.items():
            if ttype not in allowed_types:
                raise ValueError(
                    f"Task type for {name!r} must be one of {allowed_types}, "
                    f"got {ttype!r}"
                )
        return v

    @field_validator("dropout")
    @classmethod
    def _validate_dropout(cls, v: float) -> float:
        if not 0.0 <= v < 1.0:
            raise ValueError(f"dropout must be in [0.0, 1.0), got {v}")
        return v


# ---------------------------------------------------------------------------
# Torch dependency guard
# ---------------------------------------------------------------------------


def _require_deps() -> None:
    """Raise RuntimeError if torch or torch_geometric are missing."""
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for MultiTaskADMET but is not installed. "
            "Install it with: pip install torch"
        )
    if not HAS_TORCH_GEOMETRIC:
        raise RuntimeError(
            "PyTorch Geometric is required for MultiTaskADMET but is not installed. "
            "Install it with: pip install torch_geometric"
        )


# ---------------------------------------------------------------------------
# Task head
# ---------------------------------------------------------------------------

if HAS_TORCH:

    class TaskHead(nn.Module):
        """Single task-specific prediction head.

        Architecture::

            Linear(input_dim, input_dim // 2) → ReLU → Dropout → Linear(input_dim // 2, 1)

        Outputs raw logits (for classification, apply sigmoid externally).

        Args:
            input_dim: Dimensionality of the shared representation fed to this
                head.
            dropout: Dropout probability.
        """

        def __init__(self, input_dim: int, dropout: float = 0.2) -> None:
            super().__init__()
            mid_dim = max(input_dim // 2, 1)
            self.net = nn.Sequential(
                nn.Linear(input_dim, mid_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(mid_dim, 1),
            )

        def forward(self, x: Tensor) -> Tensor:
            """Forward pass.

            Args:
                x: Shared graph-level representation of shape
                    ``(batch_size, input_dim)``.

            Returns:
                Predictions of shape ``(batch_size, 1)``.
            """
            return self.net(x)

    # -------------------------------------------------------------------
    # Multi-task ADMET model
    # -------------------------------------------------------------------

    class MultiTaskADMET(nn.Module):
        """Multi-task ADMET predictor with shared GNN backbone.

        The model converts a molecular graph (PyG :class:`Data` or
        :class:`Batch`) into per-task scalar predictions via a shared
        message-passing backbone and task-specific linear heads.

        Args:
            config: An :class:`ADMETConfig` instance controlling architecture
                and task definitions.
        """

        def __init__(self, config: ADMETConfig | None = None) -> None:
            _require_deps()
            super().__init__()

            if config is None:
                config = ADMETConfig()
            self.config = config

            hidden = config.hidden_dim

            # --- Input projection ---
            self.atom_encoder = nn.Linear(config.atom_feature_dim, hidden)

            # --- Shared GNN backbone ---
            self.gnn_layers = nn.ModuleList()
            self.batch_norms = nn.ModuleList()

            for _ in range(config.n_gnn_layers):
                if config.gnn_type == "gin":
                    mlp = nn.Sequential(
                        nn.Linear(hidden, hidden),
                        nn.ReLU(),
                        nn.Linear(hidden, hidden),
                    )
                    conv = GINConv(nn=mlp)
                else:  # gcn
                    conv = GCNConv(hidden, hidden)

                self.gnn_layers.append(conv)
                self.batch_norms.append(nn.BatchNorm1d(hidden))

            self.activation = nn.ReLU()
            self.dropout = nn.Dropout(config.dropout)

            # --- Shared projection (after readout) ---
            # Readout concatenates mean-pool and max-pool → 2 * hidden
            self.shared_projection = nn.Sequential(
                nn.Linear(2 * hidden, hidden),
                nn.ReLU(),
                nn.Dropout(config.dropout),
            )

            # --- Task-specific heads ---
            self.task_heads = nn.ModuleDict(
                {
                    name: TaskHead(hidden, config.dropout)
                    for name in config.task_names
                }
            )

        def forward(self, data: Data | Batch) -> dict[str, Tensor]:
            """Forward pass: molecular graph → per-task predictions.

            Args:
                data: A PyG :class:`~torch_geometric.data.Data` (single
                    molecule) or :class:`~torch_geometric.data.Batch` (batched
                    molecules).  Must contain ``x``, ``edge_index``, and
                    (for batches) ``batch``.

            Returns:
                Dictionary mapping task name to prediction tensor of shape
                ``(batch_size, 1)``.
            """
            x, edge_index = data.x, data.edge_index

            # Determine batch vector (needed for graph-level pooling)
            if hasattr(data, "batch") and data.batch is not None:
                batch_vec = data.batch
            else:
                # Single graph — all nodes belong to graph 0
                batch_vec = torch.zeros(
                    x.size(0), dtype=torch.long, device=x.device
                )

            # --- Atom encoding ---
            h = self.atom_encoder(x)

            # --- Message passing ---
            for conv, bn in zip(self.gnn_layers, self.batch_norms):
                h_new = conv(h, edge_index)
                h_new = bn(h_new)
                h_new = self.activation(h_new)
                h_new = self.dropout(h_new)
                # Residual connection (skip connection)
                h = h + h_new

            # --- Graph-level readout ---
            h_mean = global_mean_pool(h, batch_vec)  # (B, hidden)
            h_max = global_max_pool(h, batch_vec)  # (B, hidden)
            graph_repr = torch.cat([h_mean, h_max], dim=-1)  # (B, 2*hidden)

            # --- Shared projection ---
            shared = self.shared_projection(graph_repr)  # (B, hidden)

            # --- Task heads ---
            predictions: dict[str, Tensor] = {}
            for name, head in self.task_heads.items():
                predictions[name] = head(shared)  # (B, 1)

            return predictions

        @torch.no_grad()
        def predict(self, data: Data) -> dict[str, float]:
            """Single-molecule prediction (inference mode).

            Runs the model in eval mode on a single graph and returns a
            dictionary of scalar scores.  Classification tasks are passed
            through a sigmoid so the returned value is a probability.

            Args:
                data: A PyG :class:`~torch_geometric.data.Data` for one
                    molecule.

            Returns:
                Dictionary mapping task name to a single float score.
            """
            was_training = self.training
            self.eval()

            raw = self.forward(data)

            results: dict[str, float] = {}
            for name, tensor in raw.items():
                value = tensor.squeeze().item()
                # Apply sigmoid for classification tasks
                if self.config.task_types.get(name) == "classification":
                    value = torch.sigmoid(torch.tensor(value)).item()
                results[name] = round(value, 4)

            if was_training:
                self.train()

            return results


# ---------------------------------------------------------------------------
# Multi-task loss function
# ---------------------------------------------------------------------------


def admet_loss(
    predictions: dict[str, Tensor],
    targets: Tensor,
    task_types: dict[str, str],
    task_names: list[str],
    task_weights: dict[str, float] | None = None,
) -> tuple[Tensor, dict[str, Tensor]]:
    """Compute multi-task ADMET loss with NaN masking.

    Handles missing labels by masking out NaN entries so they do not
    contribute to the loss.  Classification tasks use
    ``BCEWithLogitsLoss``; regression tasks use ``MSELoss``.

    Args:
        predictions: Dictionary mapping task name to prediction tensor of
            shape ``(batch_size, 1)``.
        targets: Target tensor of shape ``(batch_size, n_tasks)`` where
            ``n_tasks == len(task_names)``.  Missing labels are encoded as
            ``NaN``.
        task_types: Mapping from task name to ``"regression"`` or
            ``"classification"``.
        task_names: Ordered list of task names (determines column order in
            *targets*).
        task_weights: Optional per-task weighting.  If ``None``, all tasks
            are weighted equally (1.0).

    Returns:
        A ``(total_loss, per_task_losses)`` tuple.  ``per_task_losses`` is a
        dictionary mapping task name to its individual (weighted) loss
        tensor.  Tasks with no valid labels in the batch contribute a
        zero-valued tensor.

    Raises:
        RuntimeError: If torch is not installed.
    """
    if not HAS_TORCH:
        raise RuntimeError(
            "PyTorch is required for admet_loss but is not installed."
        )

    if task_weights is None:
        task_weights = {name: 1.0 for name in task_names}

    bce_loss_fn = nn.BCEWithLogitsLoss(reduction="none")
    mse_loss_fn = nn.MSELoss(reduction="none")

    total_loss = torch.tensor(0.0, device=targets.device, requires_grad=True)
    per_task_losses: dict[str, Tensor] = {}

    for i, name in enumerate(task_names):
        if name not in predictions:
            continue

        pred = predictions[name].squeeze(-1)  # (B,)
        target_col = targets[:, i]  # (B,)

        # Mask out NaN labels
        valid_mask = ~torch.isnan(target_col)

        if valid_mask.sum() == 0:
            # No valid labels for this task in the batch
            per_task_losses[name] = torch.tensor(
                0.0, device=targets.device, requires_grad=False
            )
            continue

        pred_valid = pred[valid_mask]
        target_valid = target_col[valid_mask]

        # Compute per-sample loss
        if task_types.get(name) == "classification":
            sample_losses = bce_loss_fn(pred_valid, target_valid)
        else:
            sample_losses = mse_loss_fn(pred_valid, target_valid)

        # Mean over valid samples, then weight
        task_loss = sample_losses.mean() * task_weights.get(name, 1.0)
        per_task_losses[name] = task_loss
        total_loss = total_loss + task_loss

    return total_loss, per_task_losses
