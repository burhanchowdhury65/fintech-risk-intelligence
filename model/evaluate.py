"""
evaluate.py — Step 6 (Threshold Selection on Validation) + Step 7 (Final Test Evaluation)

What this does (plain terms):
1. Reloads the saved best pipeline (trained in train.py on fraudTrain.csv's
   training portion).
2. Re-derives the SAME chronological validation split train.py used, and uses
   ONLY that validation data to pick a decision threshold (the score cutoff
   above which we call something "fraud"). We never look at fraudTest.csv for
   this — picking a threshold using the test set would itself be a form of
   leakage/cheating.
3. ONLY AFTER the threshold is locked in, loads fraudTest.csv for the first and
   only time in this whole pipeline, and reports real, final metrics.

How to run (from the model/ folder):
    python evaluate.py
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_recall_curve, precision_score, recall_score, f1_score,
    average_precision_score, roc_auc_score, confusion_matrix, classification_report,
)

from config import TEST_CSV, TARGET_COL, MODEL_PATH, REPORTS_DIR
from preprocessing import engineer_features, select_model_columns
from train import load_and_split


def pick_threshold_on_validation(pipeline, X_val, y_val, min_precision: float = 0.30) -> float:
    """
    Scans the precision-recall curve computed on VALIDATION data only, and picks
    the threshold that maximizes recall while keeping precision at or above
    `min_precision`. This reflects a product decision (favor catching more fraud,
    while keeping false alarms from becoming overwhelming) — the exact
    `min_precision` value is a placeholder and should be revisited with the team,
    see RISK_SCORE.md.
    """
    y_score = pipeline.predict_proba(X_val)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_val, y_score)

    # precision_recall_curve returns one more precision/recall point than thresholds
    precisions, recalls = precisions[:-1], recalls[:-1]

    valid = precisions >= min_precision
    if not valid.any():
        print(f"WARNING: no threshold reaches precision >= {min_precision}. Falling back to threshold=0.5.")
        return 0.5

    best_idx = np.argmax(recalls[valid])
    chosen_threshold = thresholds[valid][best_idx]

    print(f"Chosen threshold (validation only): {chosen_threshold:.4f}")
    print(f"  -> at this threshold: precision={precisions[valid][best_idx]:.4f}, recall={recalls[valid][best_idx]:.4f}")
    return float(chosen_threshold)


def evaluate_at_threshold(y_true, y_score, threshold: float, label: str) -> dict:
    y_pred = (y_score >= threshold).astype(int)
    metrics = {
        "label": label,
        "threshold": threshold,
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "pr_auc": average_precision_score(y_true, y_score),
        "roc_auc": roc_auc_score(y_true, y_score),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "support_fraud": int(y_true.sum()),
        "support_total": int(len(y_true)),
    }
    return metrics


def print_metrics(metrics: dict):
    print(f"\n=== {metrics['label']} (threshold={metrics['threshold']:.4f}) ===")
    print(f"Support: {metrics['support_fraud']} fraud / {metrics['support_total']} total "
          f"({metrics['support_fraud']/metrics['support_total']*100:.3f}% fraud)")
    print(f"Precision: {metrics['precision']:.4f}  |  Recall: {metrics['recall']:.4f}  |  F1: {metrics['f1']:.4f}")
    print(f"PR-AUC: {metrics['pr_auc']:.4f}  |  ROC-AUC: {metrics['roc_auc']:.4f}")
    tn, fp, fn, tp = np.array(metrics["confusion_matrix"]).ravel()
    print(f"Confusion matrix: TN={tn}  FP={fp}  FN={fn}  TP={tp}")
    print(f"  -> {fn} fraud cases MISSED (false negatives) | {fp} legitimate transactions wrongly flagged (false positives)")


def explain_errors_in_context():
    print("\n--- What false positives / false negatives mean here ---")
    print("False Positive (legit transaction flagged as fraud): a real customer's")
    print("  transaction gets blocked/reviewed unnecessarily -> customer friction,")
    print("  possible lost sales, support burden.")
    print("False Negative (fraud transaction missed): actual fraud goes through")
    print("  undetected -> direct financial loss, the more costly error type in")
    print("  most fraud systems, which is why we optimized for high recall above.")


def main():
    pipeline = joblib.load(MODEL_PATH)
    print(f"Loaded saved pipeline from {MODEL_PATH}")

    # Re-derive the same validation split used in train.py (chronological, deterministic)
    X_train, y_train, X_val, y_val = load_and_split()

    # STEP 6: pick threshold using validation only
    threshold = pick_threshold_on_validation(pipeline, X_val, y_val, min_precision=0.30)

    y_val_score = pipeline.predict_proba(X_val)[:, 1]
    val_metrics = evaluate_at_threshold(y_val, y_val_score, threshold, "VALIDATION (threshold selection)")
    print_metrics(val_metrics)

    # Baseline comparison note (from train.py's default 0.5-threshold run)
    print("\n--- Comparison note ---")
    print("At the default 0.5 threshold (train.py's run), RandomForest validation metrics were:")
    print("  precision=0.3449, recall=0.9550, f1=0.5068, pr_auc=0.8809, roc_auc=0.9966")
    print(f"At the tuned threshold ({threshold:.4f}), see VALIDATION metrics printed above for comparison.")

    # STEP 7: load fraudTest.csv for the FIRST AND ONLY TIME, evaluate once.
    print("\n" + "=" * 60)
    print("STEP 7 — FINAL TEST EVALUATION (fraudTest.csv touched for the first time)")
    print("=" * 60)

    test_df = pd.read_csv(TEST_CSV, index_col=0)
    y_test = test_df[TARGET_COL].copy()
    X_test = select_model_columns(engineer_features(test_df))

    y_test_score = pipeline.predict_proba(X_test)[:, 1]
    test_metrics = evaluate_at_threshold(y_test, y_test_score, threshold, "FINAL TEST (held out)")
    print_metrics(test_metrics)
    explain_errors_in_context()

    print("\n--- Split method, seed, and config used (for the record) ---")
    print("Split: chronological, 85% train / 15% validation of fraudTrain.csv")
    print("Test: fraudTest.csv, entirely held out until this step")
    print("Model: RandomForestClassifier(n_estimators=200, max_depth=12, class_weight='balanced', random_state=42)")
    print(f"Decision threshold: {threshold:.4f} (selected on validation data, min_precision=0.30 constraint)")

    REPORTS_DIR.mkdir(exist_ok=True)
    with open(REPORTS_DIR / "final_evaluation.txt", "w") as f:
        f.write(f"Validation metrics: {val_metrics}\n\n")
        f.write(f"Test metrics: {test_metrics}\n\n")
        f.write(f"Threshold: {threshold}\n")
    print(f"\nFinal report saved to {REPORTS_DIR / 'final_evaluation.txt'}")


if __name__ == "__main__":
    main()
