"""Feature preprocessing: scaling, encoding, and split generation.

Handles:
- Standard scaling (mean=0, std=1) fit on training data only
- Split generation from pre-assigned splits
- Feature matrix conversion to numpy-like lists
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from statebind.context.features import FeatureSet


@dataclass
class SplitData:
    """Train/val/test split with feature matrices and labels."""

    train_X: list[list[float]] = field(default_factory=list)
    train_y: list[str] = field(default_factory=list)
    train_y_dist: list[dict[str, float]] = field(default_factory=list)
    train_ids: list[str] = field(default_factory=list)

    val_X: list[list[float]] = field(default_factory=list)
    val_y: list[str] = field(default_factory=list)
    val_y_dist: list[dict[str, float]] = field(default_factory=list)
    val_ids: list[str] = field(default_factory=list)

    test_X: list[list[float]] = field(default_factory=list)
    test_y: list[str] = field(default_factory=list)
    test_y_dist: list[dict[str, float]] = field(default_factory=list)
    test_ids: list[str] = field(default_factory=list)

    feature_names: list[str] = field(default_factory=list)
    n_features: int = 0
    n_classes: int = 0
    class_labels: list[str] = field(default_factory=list)


@dataclass
class ScalerParams:
    """Parameters for standard scaling, fit on training data."""

    means: list[float] = field(default_factory=list)
    stds: list[float] = field(default_factory=list)
    feature_names: list[str] = field(default_factory=list)

    def transform(self, X: list[list[float]]) -> list[list[float]]:
        """Apply standardization to feature matrix."""
        result = []
        for row in X:
            scaled = []
            for i, val in enumerate(row):
                if self.stds[i] > 1e-10:
                    scaled.append((val - self.means[i]) / self.stds[i])
                else:
                    scaled.append(0.0)  # constant feature
            result.append(scaled)
        return result


def fit_scaler(X: list[list[float]], feature_names: list[str]) -> ScalerParams:
    """Fit a standard scaler on training data.

    Args:
        X: Training feature matrix (list of feature vectors).
        feature_names: Ordered feature names.

    Returns:
        ScalerParams with means and stds computed from X.
    """
    n = len(X)
    if n == 0:
        return ScalerParams(
            means=[0.0] * len(feature_names),
            stds=[1.0] * len(feature_names),
            feature_names=feature_names,
        )

    n_features = len(X[0])
    means = [0.0] * n_features
    stds = [0.0] * n_features

    # Compute means
    for row in X:
        for i, val in enumerate(row):
            means[i] += val
    means = [m / n for m in means]

    # Compute stds
    for row in X:
        for i, val in enumerate(row):
            stds[i] += (val - means[i]) ** 2
    stds = [math.sqrt(s / max(n - 1, 1)) for s in stds]

    return ScalerParams(means=means, stds=stds, feature_names=feature_names)


def generate_splits(
    feature_sets: list[FeatureSet],
    scale: bool = True,
) -> tuple[SplitData, ScalerParams | None]:
    """Generate train/val/test splits from pre-assigned FeatureSets.

    Splits are determined by the `split` field on each FeatureSet,
    which was assigned upstream during context dataset construction.
    This function does NOT re-randomize — it respects existing assignments.

    Args:
        feature_sets: List of FeatureSet objects with split assignments.
        scale: If True, fit StandardScaler on train and apply to all splits.

    Returns:
        (SplitData, ScalerParams or None if scale=False)
    """
    # Separate by split
    train_fs = [fs for fs in feature_sets if fs.split == "train"]
    val_fs = [fs for fs in feature_sets if fs.split == "val"]
    test_fs = [fs for fs in feature_sets if fs.split == "test"]

    # Extract matrices
    def _extract(fsets: list[FeatureSet]) -> tuple[
        list[list[float]], list[str], list[dict[str, float]], list[str]
    ]:
        X = [fs.values for fs in fsets]
        y = [fs.label for fs in fsets]
        y_dist = [fs.label_distribution for fs in fsets]
        ids = [fs.mutation_id for fs in fsets]
        return X, y, y_dist, ids

    train_X, train_y, train_y_dist, train_ids = _extract(train_fs)
    val_X, val_y, val_y_dist, val_ids = _extract(val_fs)
    test_X, test_y, test_y_dist, test_ids = _extract(test_fs)

    # Feature names from first available
    names = feature_sets[0].feature_names if feature_sets else []

    # Scaling (fit on train only)
    scaler = None
    if scale and train_X:
        scaler = fit_scaler(train_X, names)
        train_X = scaler.transform(train_X)
        if val_X:
            val_X = scaler.transform(val_X)
        if test_X:
            test_X = scaler.transform(test_X)

    # Class labels
    all_labels = sorted(set(train_y + val_y + test_y))

    split_data = SplitData(
        train_X=train_X, train_y=train_y,
        train_y_dist=train_y_dist, train_ids=train_ids,
        val_X=val_X, val_y=val_y,
        val_y_dist=val_y_dist, val_ids=val_ids,
        test_X=test_X, test_y=test_y,
        test_y_dist=test_y_dist, test_ids=test_ids,
        feature_names=names,
        n_features=len(names),
        n_classes=len(all_labels),
        class_labels=all_labels,
    )

    return split_data, scaler
