"""
train_candidates.py — Day 3, Step 4 (Candidate Models) + Step 5 (Class Imbalance Analysis)

Trains several candidate models on the SAME chronological train/validation split
used in Day 2 (reusing train.py's load_and_split(), unchanged), so comparisons
are fair (Step 6 requirement: same split, same metric definitions for every model).

Candidates trained:
  1. Logistic Regression, class_weight=None (default)
  2. Logistic Regression, class_weight='balanced'
  3. Random Forest, class_weight=None (default)
  4. Random Forest, class_weight='balanced'
  5. HistGradientBoostingClassifier, class_weight='balanced' (fast on large data, new
     model family not tried on Day 2 — added because the prompt allows "an additional
     model only if there is a clear reason": HistGB natively handles large N with
     categorical-friendly splits and no manual scaling needed, worth comparing)
  6. Logistic Regression on UNDER-SAMPLED training data (resampling comparison,
     Step 5 requirement) — resampling applied to TRAINING data only, never to
     validation, per the strict rules.

Does NOT touch fraudTest.csv. All comparisons below are on the validation split only.

How to run (from model/ folder):
    python train_candidates.py
"""

import time
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    precision_score, recall_score, f1_score, accuracy_score,
    average_precision_score, roc_auc_score, confusion_matrix,
)

from config import RANDOM_SEED, REPORTS_DIR
from preprocessing import build_preprocessor
from train import load_and_split


def evaluate(model_name: str, config_str: str, pipeline, X_val, y_val, fit_time: float, X_train=None, y_train=None) -> dict:
    y_pred = pipeline.predict(X_val)
    y_score = pipeline.predict_proba(X_val)[:, 1] if hasattr(pipeline, "predict_proba") else y_pred

    metrics = {
        "model": model_name,
        "config": config_str,
        "fit_time_sec": round(fit_time, 1),
        "accuracy": accuracy_score(y_val, y_pred),
        "precision": precision_score(y_val, y_pred, zero_division=0),
        "recall": recall_score(y_val, y_pred, zero_division=0),
        "f1": f1_score(y_val, y_pred, zero_division=0),
        "pr_auc": average_precision_score(y_val, y_score),
        "roc_auc": roc_auc_score(y_val, y_score),
        "confusion_matrix": confusion_matrix(y_val, y_pred).tolist(),
    }

    # Optional: train-set metrics too, for Step 8's overfitting check later
    if X_train is not None:
        y_train_pred = pipeline.predict(X_train)
        y_train_score = pipeline.predict_proba(X_train)[:, 1]
        metrics["train_recall"] = recall_score(y_train, y_train_pred, zero_division=0)
        metrics["train_pr_auc"] = average_precision_score(y_train, y_train_score)

    return metrics


def print_row(m: dict):
    print(f"\n--- {m['model']} [{m['config']}] (fit={m['fit_time_sec']}s) ---")
    print(f"Accuracy={m['accuracy']:.4f}  Precision={m['precision']:.4f}  Recall={m['recall']:.4f}  "
          f"F1={m['f1']:.4f}  PR-AUC={m['pr_auc']:.4f}  ROC-AUC={m['roc_auc']:.4f}")
    tn, fp, fn, tp = np.array(m["confusion_matrix"]).ravel()
    print(f"Confusion: TN={tn} FP={fp} FN={fn} TP={tp}")
    if "train_recall" in m:
        print(f"[Train-set check] train_recall={m['train_recall']:.4f} vs val_recall={m['recall']:.4f} | "
              f"train_pr_auc={m['train_pr_auc']:.4f} vs val_pr_auc={m['pr_auc']:.4f}")


def main():
    X_train, y_train, X_val, y_val = load_and_split()
    results = []

    # --- 1 & 2: Logistic Regression, class_weight None vs balanced ---
    for cw in [None, "balanced"]:
        pipe = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("model", LogisticRegression(max_iter=1000, class_weight=cw, random_state=RANDOM_SEED)),
        ])
        t0 = time.time()
        pipe.fit(X_train, y_train)
        m = evaluate("LogisticRegression", f"class_weight={cw}", pipe, X_val, y_val, time.time() - t0, X_train, y_train)
        print_row(m)
        results.append(m)

    # --- 3 & 4: Random Forest, class_weight None vs balanced ---
    for cw in [None, "balanced"]:
        pipe = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("model", RandomForestClassifier(
                n_estimators=200, max_depth=12, class_weight=cw,
                random_state=RANDOM_SEED, n_jobs=-1,
            )),
        ])
        t0 = time.time()
        pipe.fit(X_train, y_train)
        m = evaluate("RandomForest", f"class_weight={cw}", pipe, X_val, y_val, time.time() - t0, X_train, y_train)
        print_row(m)
        results.append(m)

    # --- 5: HistGradientBoostingClassifier (new model family, fast on large N) ---
    pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", HistGradientBoostingClassifier(
            max_iter=300, class_weight="balanced", random_state=RANDOM_SEED,
        )),
    ])
    t0 = time.time()
    pipe.fit(X_train, y_train)
    m = evaluate("HistGradientBoosting", "class_weight=balanced, max_iter=300", pipe, X_val, y_val, time.time() - t0, X_train, y_train)
    print_row(m)
    results.append(m)

    # --- 6: Resampling comparison — RandomUnderSampler on TRAINING data only, LogisticRegression ---
    from imblearn.under_sampling import RandomUnderSampler
    rus = RandomUnderSampler(random_state=RANDOM_SEED)
    # Preprocess first (fit on train only), then resample the transformed training matrix.
    preprocessor_for_resample = build_preprocessor()
    X_train_transformed = preprocessor_for_resample.fit_transform(X_train)
    X_train_res, y_train_res = rus.fit_resample(X_train_transformed, y_train)
    print(f"\nResampling: original train {len(y_train)} rows ({y_train.mean()*100:.3f}% fraud) "
          f"-> undersampled {len(y_train_res)} rows ({y_train_res.mean()*100:.3f}% fraud)")

    logreg_res = LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)
    t0 = time.time()
    logreg_res.fit(X_train_res, y_train_res)
    fit_time = time.time() - t0

    X_val_transformed = preprocessor_for_resample.transform(X_val)  # validation NOT resampled, per the rules
    y_pred = logreg_res.predict(X_val_transformed)
    y_score = logreg_res.predict_proba(X_val_transformed)[:, 1]
    m = {
        "model": "LogisticRegression",
        "config": "trained on RandomUnderSampler(train-only)",
        "fit_time_sec": round(fit_time, 1),
        "accuracy": accuracy_score(y_val, y_pred),
        "precision": precision_score(y_val, y_pred, zero_division=0),
        "recall": recall_score(y_val, y_pred, zero_division=0),
        "f1": f1_score(y_val, y_pred, zero_division=0),
        "pr_auc": average_precision_score(y_val, y_score),
        "roc_auc": roc_auc_score(y_val, y_score),
        "confusion_matrix": confusion_matrix(y_val, y_pred).tolist(),
    }
    print_row(m)
    results.append(m)

    # --- Summary table ---
    print("\n" + "=" * 100)
    print(f"{'Model':<22}{'Config':<40}{'Prec':>7}{'Recall':>8}{'F1':>7}{'PR-AUC':>8}{'ROC-AUC':>9}")
    print("=" * 100)
    for r in results:
        print(f"{r['model']:<22}{r['config']:<40}{r['precision']:>7.3f}{r['recall']:>8.3f}{r['f1']:>7.3f}{r['pr_auc']:>8.3f}{r['roc_auc']:>9.3f}")

    REPORTS_DIR.mkdir(exist_ok=True)
    with open(REPORTS_DIR / "day3_candidate_comparison.txt", "w") as f:
        for r in results:
            f.write(f"{r}\n\n")
    print(f"\nSaved to {REPORTS_DIR / 'day3_candidate_comparison.txt'}")

    return results


if __name__ == "__main__":
    main()
