"""
evaluate_candidate.py — Day 3, Step 10: Final Test Set Evaluation.

Loads the Day 3 candidate (HistGradientBoosting) and its selected threshold
(0.80, chosen on validation only in finalize_candidate.py), and evaluates it
on fraudTest.csv for the first and only time in the Day 3 workflow.

Does NOT tune anything based on this result.
"""

import json
import joblib
import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, f1_score, accuracy_score,
    average_precision_score, roc_auc_score, confusion_matrix,
)

from config import TEST_CSV, TARGET_COL, ARTIFACTS_DIR, REPORTS_DIR
from preprocessing import engineer_features, select_model_columns

CANDIDATE_MODEL_PATH = ARTIFACTS_DIR / "fraud_model_candidate_day3_histgb.joblib"


def main():
    with open(REPORTS_DIR / "day3_candidate_metadata.json") as f:
        metadata = json.load(f)
    threshold = metadata["decision_threshold"]
    print(f"Loaded candidate metadata. Using threshold={threshold} (selected on validation in Step 7).")

    pipeline = joblib.load(CANDIDATE_MODEL_PATH)

    print("\n" + "=" * 60)
    print("Loading fraudTest.csv for the FIRST TIME in the Day 3 workflow")
    print("=" * 60)
    test_df = pd.read_csv(TEST_CSV, index_col=0)
    y_test = test_df[TARGET_COL].copy()
    X_test = select_model_columns(engineer_features(test_df))

    y_score = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_score >= threshold).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "pr_auc": average_precision_score(y_test, y_score),
        "roc_auc": roc_auc_score(y_test, y_score),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "support_fraud": int(y_test.sum()),
        "support_total": int(len(y_test)),
        "threshold_used": threshold,
    }

    print(f"\n=== FINAL TEST RESULTS (Day 3 candidate: HistGradientBoosting) ===")
    print(f"Support: {metrics['support_fraud']} fraud / {metrics['support_total']} total")
    print(f"Accuracy:  {metrics['accuracy']:.4f}  (misleading alone — see note below)")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1:        {metrics['f1']:.4f}")
    print(f"PR-AUC:    {metrics['pr_auc']:.4f}")
    print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
    tn, fp, fn, tp = metrics["confusion_matrix"][0][0], metrics["confusion_matrix"][0][1], metrics["confusion_matrix"][1][0], metrics["confusion_matrix"][1][1]
    print(f"Confusion matrix: TN={tn} FP={fp} FN={fn} TP={tp}")
    print(f"  -> {fn} real fraud cases MISSED | {fp} legitimate transactions wrongly flagged")

    print("\n--- Comparison with Day 2's Random Forest final test result ---")
    print("Day 2 (RandomForest, threshold=0.4629): precision=0.2208, recall=0.9515, f1=0.3584, pr_auc=0.8354")
    print(f"Day 3 (HistGB, threshold={threshold}):        precision={metrics['precision']:.4f}, recall={metrics['recall']:.4f}, "
          f"f1={metrics['f1']:.4f}, pr_auc={metrics['pr_auc']:.4f}")
    improvement_f1 = metrics['f1'] - 0.3584
    print(f"F1 change: {'+' if improvement_f1 >= 0 else ''}{improvement_f1:.4f}")

    with open(REPORTS_DIR / "day3_final_test_evaluation.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved to {REPORTS_DIR / 'day3_final_test_evaluation.json'}")


if __name__ == "__main__":
    main()
