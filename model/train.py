"""
train.py — Step 4 (Data Splitting) + Step 5 (Preprocessing & Baseline Models)

What this does (plain terms):
1. Loads fraudTrain.csv.
2. Sorts it by transaction time and splits it CHRONOLOGICALLY (not randomly)
   into a training portion (first ~85%) and a validation portion (last ~15%).
   Chronological splitting is used because this is transaction/time-series data —
   a random split could let the model "see the future" during training, which
   would be a subtle form of leakage.
3. Fits the preprocessing pipeline ONLY on the training portion.
4. Trains three baseline models in increasing complexity:
   - DummyClassifier (always predicts the majority class — the "floor" any real
     model must beat)
   - Logistic Regression (simple, fast, interpretable)
   - Random Forest (only if training time is reasonable — see note below)
5. Saves the best-performing pipeline (preprocessor + model together) to artifacts/.

fraudTest.csv is NEVER loaded in this file — it stays untouched until evaluate.py's
final test step, as planned in the Day 2 audit report.

How to run (from the model/ folder):
    python train.py
"""

import time
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    average_precision_score, roc_auc_score, confusion_matrix,
)

from config import TRAIN_CSV, TARGET_COL, RANDOM_SEED, ARTIFACTS_DIR, MODEL_PATH
from preprocessing import engineer_features, select_model_columns, build_preprocessor


def load_and_split(val_fraction: float = 0.15):
    """
    Loads fraudTrain.csv and splits it chronologically.
    Returns (X_train, y_train, X_val, y_val) — X's are already feature-engineered
    and column-selected (i.e. ready to feed into the preprocessor).
    """
    df = pd.read_csv(TRAIN_CSV, index_col=0)
    df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
    df = df.sort_values("trans_date_trans_time").reset_index(drop=True)

    cutoff_idx = int(len(df) * (1 - val_fraction))
    cutoff_date = df.iloc[cutoff_idx]["trans_date_trans_time"]

    train_df = df.iloc[:cutoff_idx].copy()
    val_df = df.iloc[cutoff_idx:].copy()

    print(f"Chronological split cutoff date: {cutoff_date}")
    print(f"Train: {len(train_df)} rows ({train_df['trans_date_trans_time'].min()} to {train_df['trans_date_trans_time'].max()})")
    print(f"Val:   {len(val_df)} rows ({val_df['trans_date_trans_time'].min()} to {val_df['trans_date_trans_time'].max()})")
    print(f"Train fraud rate: {train_df[TARGET_COL].mean()*100:.3f}% | Val fraud rate: {val_df[TARGET_COL].mean()*100:.3f}%")

    y_train = train_df[TARGET_COL].copy()
    y_val = val_df[TARGET_COL].copy()

    X_train = select_model_columns(engineer_features(train_df))
    X_val = select_model_columns(engineer_features(val_df))

    return X_train, y_train, X_val, y_val


def evaluate_on_validation(model_name: str, pipeline: Pipeline, X_val, y_val) -> dict:
    """Computes real validation metrics. Never touches fraudTest.csv."""
    y_pred = pipeline.predict(X_val)
    y_score = pipeline.predict_proba(X_val)[:, 1] if hasattr(pipeline, "predict_proba") else y_pred

    metrics = {
        "model": model_name,
        "precision": precision_score(y_val, y_pred, zero_division=0),
        "recall": recall_score(y_val, y_pred, zero_division=0),
        "f1": f1_score(y_val, y_pred, zero_division=0),
        "pr_auc": average_precision_score(y_val, y_score),
        "roc_auc": roc_auc_score(y_val, y_score),
        "confusion_matrix": confusion_matrix(y_val, y_pred).tolist(),
    }
    return metrics


def print_metrics(metrics: dict):
    print(f"\n--- {metrics['model']} — validation metrics ---")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1:        {metrics['f1']:.4f}")
    print(f"PR-AUC:    {metrics['pr_auc']:.4f}")
    print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
    tn, fp, fn, tp = np.array(metrics["confusion_matrix"]).ravel()
    print(f"Confusion matrix: TN={tn} FP={fp} FN={fn} TP={tp}")


def main():
    X_train, y_train, X_val, y_val = load_and_split()

    results = []

    # --- Baseline 1: DummyClassifier (the floor) ---
    dummy_pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", DummyClassifier(strategy="most_frequent")),
    ])
    dummy_pipeline.fit(X_train, y_train)
    dummy_metrics = evaluate_on_validation("DummyClassifier", dummy_pipeline, X_val, y_val)
    print_metrics(dummy_metrics)
    results.append(dummy_metrics)

    # --- Baseline 2: Logistic Regression (with class_weight to handle imbalance) ---
    logreg_pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED)),
    ])
    t0 = time.time()
    logreg_pipeline.fit(X_train, y_train)
    print(f"\nLogisticRegression training time: {time.time()-t0:.1f}s")
    logreg_metrics = evaluate_on_validation("LogisticRegression", logreg_pipeline, X_val, y_val)
    print_metrics(logreg_metrics)
    results.append(logreg_metrics)

    # --- Baseline 3: Random Forest (only if computationally feasible) ---
    rf_pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", RandomForestClassifier(
            n_estimators=200, max_depth=12, class_weight="balanced",
            random_state=RANDOM_SEED, n_jobs=-1,
        )),
    ])
    t0 = time.time()
    rf_pipeline.fit(X_train, y_train)
    rf_train_time = time.time() - t0
    print(f"\nRandomForest training time: {rf_train_time:.1f}s")
    rf_metrics = evaluate_on_validation("RandomForest", rf_pipeline, X_val, y_val)
    print_metrics(rf_metrics)
    results.append(rf_metrics)

    # --- Pick best model by PR-AUC (the right metric for severe imbalance, not accuracy) ---
    pipelines = {"DummyClassifier": dummy_pipeline, "LogisticRegression": logreg_pipeline, "RandomForest": rf_pipeline}
    best = max(results, key=lambda r: r["pr_auc"])
    best_pipeline = pipelines[best["model"]]

    print(f"\n=== Best model by PR-AUC on validation: {best['model']} (PR-AUC={best['pr_auc']:.4f}) ===")
    print("NOTE: this selection uses VALIDATION data only. fraudTest.csv has not been touched.")

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)
    print(f"Saved best pipeline to {MODEL_PATH}")

    return results


if __name__ == "__main__":
    main()
