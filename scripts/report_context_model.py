#!/usr/bin/env python3
"""Generate Phase 4 report: context-to-state model.

Produces reports/phase4_context_model.md with:
- Dataset summary
- Feature sets used
- Model descriptions
- Ablation comparison
- Per-mutation diagnostics
- Interpretation

Usage:
    python scripts/report_context_model.py
"""

from datetime import datetime, timezone
from pathlib import Path

from statebind.context.evaluation import (
    compare_ablations,
    evaluate_model,
    evaluation_to_dict,
)
from statebind.context.features import (
    all_feature_names,
    mutation_feature_names,
    pathway_feature_names,
)
from statebind.context.training import load_data, run_ablation_suite

REPORT_PATH = Path("reports/phase4_context_model.md")


def main() -> None:
    print("Generating Phase 4 report...")

    context = load_data(split_seed=42)
    experiments = run_ablation_suite(context)
    comparison = compare_ablations(experiments, eval_split="test")

    # Get best model details
    best_name = comparison.best_model
    best_exp = next(e for e in experiments if e.name == best_name)
    assert best_exp.trained is not None
    best_test = evaluate_model(best_exp.trained, "test")
    best_train = evaluate_model(best_exp.trained, "train")

    # Split counts
    sd = best_exp.trained.split_data
    n_train = len(sd.train_X)
    n_val = len(sd.val_X)
    n_test = len(sd.test_X)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = []
    lines.append("# Phase 4: Context-to-State Model Report")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append("**Artifacts:** `artifacts/context/ablation_v1`, `artifacts/context/evaluation_v1`")
    lines.append("")

    # 1. Dataset
    lines.append("## 1. Dataset")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|----------|-------|")
    lines.append(f"| Mutations | {len(context.mutations)} |")
    lines.append(f"| Train | {n_train} |")
    lines.append(f"| Val | {n_val} |")
    lines.append(f"| Test | {n_test} |")
    lines.append(f"| Classes | {sd.n_classes} |")
    lines.append(f"| Class labels | {', '.join(sd.class_labels)} |")
    lines.append("")
    lines.append("**Split strategy:** Key mutations (T790M, L858R, C797S) forced to test. "
                 "Remaining assigned by position hash (~60/20/20).")
    lines.append("")

    # Label assignments
    lines.append("### Label Assignment Assumptions")
    lines.append("")
    lines.append("State labels are derived from `preferred_states` on each mutation record:")
    lines.append("- If `preferred_states` is non-empty, the first entry is the primary label.")
    lines.append("- If `preferred_states` is empty, DFGin_aCin is assigned by default (most mutations retain active-state binding).")
    lines.append("- Soft label distributions assign 70% to preferred states, 30% spread to others.")
    lines.append("- Mutations with empty `preferred_states` get uniform distribution (maximum uncertainty).")
    lines.append("")

    # 2. Feature sets
    lines.append("## 2. Feature Sets")
    lines.append("")
    lines.append("### Mutation-only features")
    lines.append(f"**{len(mutation_feature_names())} features:**")
    lines.append("")
    for name in mutation_feature_names():
        lines.append(f"- `{name}`")
    lines.append("")

    lines.append("### Pathway proxy features")
    lines.append(f"**{len(pathway_feature_names())} features** (v1 proxies, not real expression data):")
    lines.append("")
    for name in pathway_feature_names():
        lines.append(f"- `{name}`")
    lines.append("")

    lines.append("### Combined features")
    lines.append(f"**{len(all_feature_names())} features** (mutation + pathway)")
    lines.append("")

    # 3. Models
    lines.append("## 3. Models Trained")
    lines.append("")
    lines.append("| # | Name | Features | Model | Description |")
    lines.append("|---|------|----------|-------|-------------|")
    lines.append("| 1 | mutation_only_centroid | mutation | Nearest centroid | Simplest baseline. Class centroids in mutation feature space. |")
    lines.append("| 2 | pathway_only_centroid | pathway | Nearest centroid | Pathway features only. Tests if pathway context alone predicts state. |")
    lines.append("| 3 | combined_centroid | all | Nearest centroid | Combined features with same simple classifier. |")
    lines.append("| 4 | mutation_only_logistic | mutation | Logistic regression | Learned decision boundary on mutation features. |")
    lines.append("| 5 | combined_logistic | all | Logistic regression | Learned boundary on combined features. |")
    lines.append("| 6 | combined_embedding_mlp | all | 2-layer MLP | Hidden embedding layer learns nonlinear feature combinations. |")
    lines.append("")

    # 4. Ablation results
    lines.append("## 4. Ablation Results (Test Set)")
    lines.append("")
    lines.append("| Model | Features | Accuracy | Macro F1 | Cross-Entropy | ECE |")
    lines.append("|-------|----------|----------|----------|---------------|-----|")
    mutation_only_acc = 0.0
    for row in comparison.rows:
        if row["name"] == "mutation_only_centroid":
            mutation_only_acc = row["accuracy"]  # type: ignore[assignment]
        lines.append(
            f"| {row['name']} | {row['feature_set']} | "
            f"{row['accuracy']:.3f} | {row['macro_f1']:.3f} | "
            f"{row['cross_entropy']:.3f} | {row['ece']:.3f} |"
        )
    lines.append("")
    lines.append(f"**Best model:** {comparison.best_model} (accuracy={comparison.best_accuracy:.3f})")
    lines.append("")

    # 5. Ablation interpretation
    lines.append("## 5. Ablation Interpretation")
    lines.append("")

    # mutation-only vs pathway-only
    pathway_only_acc = next(
        (r["accuracy"] for r in comparison.rows if r["name"] == "pathway_only_centroid"), 0.0
    )
    lines.append("### Mutation-only vs Pathway-only")
    lines.append(f"- Mutation-only accuracy: {mutation_only_acc:.3f}")
    lines.append(f"- Pathway-only accuracy: {pathway_only_acc:.3f}")
    if mutation_only_acc >= pathway_only_acc:
        lines.append("- Mutation features are more informative than pathway proxies alone.")
        lines.append("  This is expected: mutation identity directly determines conformational preference.")
    else:
        lines.append("- Pathway features outperform mutation-only, suggesting indirect "
                     "pathway effects carry state information.")
    lines.append("")

    # combined vs mutation-only
    combined_centroid_acc = next(
        (r["accuracy"] for r in comparison.rows if r["name"] == "combined_centroid"), 0.0
    )
    lines.append("### Adding pathway features")
    lines.append(f"- Combined centroid accuracy: {combined_centroid_acc:.3f} "
                 f"(vs {mutation_only_acc:.3f} mutation-only)")
    delta = combined_centroid_acc - mutation_only_acc  # type: ignore[operator]
    if delta > 0.01:
        lines.append(f"- Pathway features add +{delta:.3f} accuracy. Pathway context contributes beyond mutation alone.")
    elif delta < -0.01:
        lines.append(f"- Pathway features decrease accuracy by {abs(delta):.3f}. "
                     "Noise from proxy features outweighs signal.")
    else:
        lines.append("- Pathway features have negligible impact. Mutation features dominate.")
    lines.append("")

    # logistic vs centroid
    combined_logistic_acc = next(
        (r["accuracy"] for r in comparison.rows if r["name"] == "combined_logistic"), 0.0
    )
    lines.append("### Logistic regression vs Nearest centroid")
    lines.append(f"- Combined logistic: {combined_logistic_acc:.3f} vs combined centroid: {combined_centroid_acc:.3f}")
    lines.append("")

    # MLP vs logistic
    mlp_acc = next(
        (r["accuracy"] for r in comparison.rows if r["name"] == "combined_embedding_mlp"), 0.0
    )
    lines.append("### Embedding MLP vs Logistic")
    lines.append(f"- MLP: {mlp_acc:.3f} vs logistic: {combined_logistic_acc:.3f}")
    if mlp_acc > combined_logistic_acc:
        lines.append("- Nonlinear feature combinations in the MLP improve predictions.")
    else:
        lines.append("- With only 17 mutations, the MLP does not outperform logistic regression. "
                     "This is expected: the dataset is too small for deep models to show advantage.")
    lines.append("")

    # 6. Per-mutation diagnostics
    lines.append("## 6. Per-Mutation Test Predictions (Best Model)")
    lines.append("")
    lines.append("| Mutation | True State | Predicted | Confidence | Correct |")
    lines.append("|----------|-----------|-----------|------------|---------|")
    for p in best_test.predictions:
        true_label = next(
            (y for mid, y in zip(sd.test_ids, sd.test_y) if mid == p.mutation_id),
            "?"
        )
        correct = "yes" if p.predicted_label == true_label else "no"
        lines.append(
            f"| {p.mutation_id} | {true_label} | {p.predicted_label} | "
            f"{p.confidence:.2f} | {correct} |"
        )
    lines.append("")

    # 7. Limitations
    lines.append("## 7. Limitations")
    lines.append("")
    lines.append("1. **17 mutations is very small.** Train/test splits have <10 samples each. "
                 "Metrics have high variance. Results are directional, not statistically robust.")
    lines.append("2. **Label assignment is partially assumed.** Mutations without `preferred_states` "
                 "default to DFGin_aCin. This biases the dataset toward the active state.")
    lines.append("3. **Pathway features are proxies.** v1 pathway scores are literature-curated "
                 "estimates, not measured expression or phosphoproteomics data.")
    lines.append("4. **No cross-validation.** With n=17, leave-one-out CV would be more "
                 "appropriate but adds complexity. Single train/test split is used.")
    lines.append("5. **Models are intentionally simple.** The MLP has 16 hidden units. "
                 "With more data, larger architectures could learn richer representations.")
    lines.append("6. **Soft labels not used for training.** Label distributions are computed "
                 "but models train on hard labels. Soft-label training could improve calibration.")
    lines.append("")

    # 8. How this sets up state-aware design
    lines.append("## 8. Setup for State-Aware Molecular Design")
    lines.append("")
    lines.append("The context-to-state model provides Phase 5 with:")
    lines.append("")
    lines.append("1. **State prediction per mutation** — given a mutation profile, predict which "
                 "conformational state(s) to design against.")
    lines.append("2. **Probability distribution** — not just one state, but a distribution over "
                 "all 4 states, enabling multi-state design strategies.")
    lines.append("3. **Confidence scores** — mutations with uncertain state preference "
                 "(low confidence) can trigger multi-state design as a hedging strategy.")
    lines.append("4. **Ablation evidence** — we know which features matter for prediction, "
                 "guiding future feature engineering.")
    lines.append("")

    # Write report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"Report written to {REPORT_PATH}")
    print("Done.")


if __name__ == "__main__":
    main()
