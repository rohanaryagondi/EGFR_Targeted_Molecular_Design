"""Evaluation metrics and calibration for context-to-state models.

Computes:
- Accuracy, per-class precision/recall/F1
- Confusion matrix
- Calibration (expected calibration error)
- Cross-entropy loss
- Ablation comparison tables
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from statebind.context.models import Prediction
from statebind.context.training import AblationExperiment, TrainedModel


@dataclass
class ClassMetrics:
    """Per-class precision, recall, F1."""

    label: str
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    support: int = 0  # number of true instances


@dataclass
class ConfusionEntry:
    """Single cell in confusion matrix."""

    true_label: str
    predicted_label: str
    count: int = 0


@dataclass
class CalibrationBin:
    """A single calibration bin."""

    bin_lower: float
    bin_upper: float
    avg_confidence: float
    avg_accuracy: float
    count: int


@dataclass
class EvaluationResult:
    """Complete evaluation result for a model on a split."""

    split_name: str
    accuracy: float = 0.0
    macro_precision: float = 0.0
    macro_recall: float = 0.0
    macro_f1: float = 0.0
    cross_entropy: float = 0.0
    expected_calibration_error: float = 0.0
    per_class: list[ClassMetrics] = field(default_factory=list)
    confusion: list[ConfusionEntry] = field(default_factory=list)
    calibration_bins: list[CalibrationBin] = field(default_factory=list)
    n_samples: int = 0
    predictions: list[Prediction] = field(default_factory=list)


@dataclass
class AblationComparison:
    """Comparison of ablation experiments."""

    rows: list[dict[str, object]] = field(default_factory=list)
    best_model: str = ""
    best_accuracy: float = 0.0


def compute_accuracy(predictions: list[Prediction], true_labels: list[str]) -> float:
    """Compute classification accuracy."""
    if not predictions:
        return 0.0
    correct = sum(
        1 for p, y in zip(predictions, true_labels)
        if p.predicted_label == y
    )
    return correct / len(predictions)


def compute_cross_entropy(
    predictions: list[Prediction],
    true_labels: list[str],
) -> float:
    """Compute cross-entropy loss."""
    if not predictions:
        return 0.0
    total = 0.0
    for p, y in zip(predictions, true_labels):
        prob = p.probabilities.get(y, 1e-8)
        total -= math.log(max(prob, 1e-8))
    return total / len(predictions)


def compute_confusion_matrix(
    predictions: list[Prediction],
    true_labels: list[str],
    class_labels: list[str],
) -> list[ConfusionEntry]:
    """Compute confusion matrix."""
    counts: dict[tuple[str, str], int] = {}
    for t in class_labels:
        for p_label in class_labels:
            counts[(t, p_label)] = 0

    for p, y in zip(predictions, true_labels):
        key = (y, p.predicted_label)
        if key in counts:
            counts[key] += 1

    return [
        ConfusionEntry(true_label=t, predicted_label=p, count=c)
        for (t, p), c in sorted(counts.items())
    ]


def compute_per_class_metrics(
    predictions: list[Prediction],
    true_labels: list[str],
    class_labels: list[str],
) -> list[ClassMetrics]:
    """Compute precision, recall, F1 per class."""
    results = []
    for label in class_labels:
        tp = sum(
            1 for p, y in zip(predictions, true_labels)
            if p.predicted_label == label and y == label
        )
        fp = sum(
            1 for p, y in zip(predictions, true_labels)
            if p.predicted_label == label and y != label
        )
        fn = sum(
            1 for p, y in zip(predictions, true_labels)
            if p.predicted_label != label and y == label
        )
        support = sum(1 for y in true_labels if y == label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )

        results.append(ClassMetrics(
            label=label, precision=precision, recall=recall,
            f1=f1, support=support,
        ))
    return results


def compute_calibration(
    predictions: list[Prediction],
    true_labels: list[str],
    n_bins: int = 5,
) -> tuple[float, list[CalibrationBin]]:
    """Compute expected calibration error (ECE) and calibration bins.

    ECE = sum(|accuracy_bin - confidence_bin| * n_bin / N)
    """
    if not predictions:
        return 0.0, []

    bins: list[list[tuple[float, bool]]] = [[] for _ in range(n_bins)]
    for p, y in zip(predictions, true_labels):
        conf = p.confidence
        correct = p.predicted_label == y
        bin_idx = min(int(conf * n_bins), n_bins - 1)
        bins[bin_idx].append((conf, correct))

    ece = 0.0
    cal_bins = []
    n_total = len(predictions)

    for i in range(n_bins):
        lower = i / n_bins
        upper = (i + 1) / n_bins
        if not bins[i]:
            cal_bins.append(CalibrationBin(
                bin_lower=lower, bin_upper=upper,
                avg_confidence=0.0, avg_accuracy=0.0, count=0,
            ))
            continue

        avg_conf = sum(c for c, _ in bins[i]) / len(bins[i])
        avg_acc = sum(1 for _, correct in bins[i] if correct) / len(bins[i])
        ece += abs(avg_acc - avg_conf) * len(bins[i]) / n_total

        cal_bins.append(CalibrationBin(
            bin_lower=lower, bin_upper=upper,
            avg_confidence=avg_conf, avg_accuracy=avg_acc,
            count=len(bins[i]),
        ))

    return ece, cal_bins


def evaluate_model(
    trained: TrainedModel,
    split: str = "test",
) -> EvaluationResult:
    """Full evaluation of a trained model on a given split.

    Args:
        trained: TrainedModel container.
        split: One of "train", "val", "test".

    Returns:
        EvaluationResult with all metrics.
    """
    split_map = {
        "train": (trained.train_predictions, trained.split_data.train_y),
        "val": (trained.val_predictions, trained.split_data.val_y),
        "test": (trained.test_predictions, trained.split_data.test_y),
    }

    preds, true_labels = split_map[split]
    class_labels = trained.split_data.class_labels

    if not preds:
        return EvaluationResult(split_name=split, n_samples=0)

    accuracy = compute_accuracy(preds, true_labels)
    ce = compute_cross_entropy(preds, true_labels)
    confusion = compute_confusion_matrix(preds, true_labels, class_labels)
    per_class = compute_per_class_metrics(preds, true_labels, class_labels)
    ece, cal_bins = compute_calibration(preds, true_labels)

    macro_p = sum(c.precision for c in per_class) / max(len(per_class), 1)
    macro_r = sum(c.recall for c in per_class) / max(len(per_class), 1)
    macro_f1 = sum(c.f1 for c in per_class) / max(len(per_class), 1)

    return EvaluationResult(
        split_name=split,
        accuracy=accuracy,
        macro_precision=macro_p,
        macro_recall=macro_r,
        macro_f1=macro_f1,
        cross_entropy=ce,
        expected_calibration_error=ece,
        per_class=per_class,
        confusion=confusion,
        calibration_bins=cal_bins,
        n_samples=len(preds),
        predictions=preds,
    )


def compare_ablations(
    experiments: list[AblationExperiment],
    eval_split: str = "test",
) -> AblationComparison:
    """Compare ablation experiment results.

    Evaluates each experiment on the specified split and produces
    a comparison table.
    """
    rows = []
    best_model = ""
    best_acc = -1.0

    for exp in experiments:
        if exp.trained is None:
            continue

        result = evaluate_model(exp.trained, split=eval_split)

        row = {
            "name": exp.name,
            "feature_set": exp.feature_set,
            "model_type": exp.model_type,
            "accuracy": result.accuracy,
            "macro_f1": result.macro_f1,
            "cross_entropy": result.cross_entropy,
            "ece": result.expected_calibration_error,
            "n_samples": result.n_samples,
        }
        rows.append(row)

        if result.accuracy > best_acc:
            best_acc = result.accuracy
            best_model = exp.name

    return AblationComparison(
        rows=rows, best_model=best_model, best_accuracy=best_acc
    )


def evaluation_to_dict(result: EvaluationResult) -> dict:
    """Serialize evaluation result to a JSON-friendly dict."""
    return {
        "split": result.split_name,
        "n_samples": result.n_samples,
        "accuracy": result.accuracy,
        "macro_precision": result.macro_precision,
        "macro_recall": result.macro_recall,
        "macro_f1": result.macro_f1,
        "cross_entropy": result.cross_entropy,
        "expected_calibration_error": result.expected_calibration_error,
        "per_class": [
            {
                "label": c.label,
                "precision": c.precision,
                "recall": c.recall,
                "f1": c.f1,
                "support": c.support,
            }
            for c in result.per_class
        ],
        "confusion_matrix": [
            {
                "true": c.true_label,
                "predicted": c.predicted_label,
                "count": c.count,
            }
            for c in result.confusion
        ],
        "calibration": [
            {
                "bin_lower": b.bin_lower,
                "bin_upper": b.bin_upper,
                "avg_confidence": b.avg_confidence,
                "avg_accuracy": b.avg_accuracy,
                "count": b.count,
            }
            for b in result.calibration_bins
        ],
        "predictions": [
            {
                "mutation_id": p.mutation_id,
                "predicted": p.predicted_label,
                "confidence": p.confidence,
                "probabilities": p.probabilities,
            }
            for p in result.predictions
        ],
    }
