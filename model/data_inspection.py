"""
data_inspection.py — Step 2: Data Quality Report

What this does (in plain terms):
Loads fraudTrain.csv and fraudTest.csv, checks their shape, missing values,
duplicates, and target-label distribution, and prints/saves a short report.

It does NOT delete or modify any rows/columns — it only reports what it finds.
Run this before trusting any downstream step.

How to run (from the model/ folder):
    python data_inspection.py
"""

import pandas as pd
from pathlib import Path
from config import TRAIN_CSV, TEST_CSV, TARGET_COL, REPORTS_DIR


def load_csv_safely(path: Path) -> pd.DataFrame:
    """Load a CSV, dropping the unnamed index column Kaggle includes, and fail loudly if missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Expected dataset file not found at {path}. "
            f"Check config.py's DATA_DIR / TRAIN_CSV / TEST_CSV settings."
        )
    return pd.read_csv(path, index_col=0)


def inspect(df: pd.DataFrame, name: str) -> dict:
    """Compute real data-quality stats for one dataframe. Returns a dict for reporting."""
    report = {}
    report["name"] = name
    report["rows"], report["cols"] = df.shape
    report["missing_total"] = int(df.isna().sum().sum())
    report["missing_by_col"] = df.isna().sum()
    report["missing_by_col"] = report["missing_by_col"][report["missing_by_col"] > 0].to_dict()
    report["exact_duplicate_rows"] = int(df.duplicated().sum())

    if "trans_num" in df.columns:
        report["duplicate_trans_num"] = int(df["trans_num"].duplicated().sum())

    if TARGET_COL in df.columns:
        vc = df[TARGET_COL].value_counts()
        vc_pct = df[TARGET_COL].value_counts(normalize=True) * 100
        report["target_counts"] = vc.to_dict()
        report["target_pct"] = {k: round(v, 4) for k, v in vc_pct.to_dict().items()}
        report["target_unique_values"] = sorted(df[TARGET_COL].unique().tolist())
    else:
        report["target_counts"] = None

    if "amt" in df.columns:
        report["amt_min"] = float(df["amt"].min())
        report["amt_max"] = float(df["amt"].max())
        report["amt_invalid_le_zero"] = int((df["amt"] <= 0).sum())

    if "trans_date_trans_time" in df.columns:
        report["date_min"] = str(df["trans_date_trans_time"].min())
        report["date_max"] = str(df["trans_date_trans_time"].max())

    report["memory_mb"] = round(df.memory_usage(deep=True).sum() / 1e6, 2)
    return report


def print_report(report: dict) -> None:
    print(f"\n=== Data Quality Report: {report['name']} ===")
    print(f"Shape: {report['rows']} rows x {report['cols']} columns")
    print(f"Memory usage: {report['memory_mb']} MB")
    print(f"Total missing values: {report['missing_total']}")
    if report["missing_by_col"]:
        print(f"  Missing by column: {report['missing_by_col']}")
    print(f"Exact duplicate rows: {report['exact_duplicate_rows']}")
    if "duplicate_trans_num" in report:
        print(f"Duplicate trans_num (should be 0, it's a unique ID): {report['duplicate_trans_num']}")
    if report["target_counts"]:
        print(f"Target ('{TARGET_COL}') distribution: {report['target_counts']}")
        print(f"Target ('{TARGET_COL}') percentage: {report['target_pct']}")
        print(f"Target unique values (should be [0, 1]): {report['target_unique_values']}")
    if "amt_min" in report:
        print(f"amt range: {report['amt_min']} to {report['amt_max']} | invalid (<=0): {report['amt_invalid_le_zero']}")
    if "date_min" in report:
        print(f"Date range: {report['date_min']} to {report['date_max']}")


def check_train_test_overlap(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """Confirms no transaction leaks across the train/test boundary."""
    if "trans_num" not in train_df.columns or "trans_num" not in test_df.columns:
        print("\nSkipping overlap check: trans_num column missing.")
        return
    overlap = set(train_df["trans_num"]) & set(test_df["trans_num"])
    print(f"\n=== Train/Test overlap check ===")
    print(f"Transactions (trans_num) appearing in BOTH train and test: {len(overlap)} (should be 0)")
    if len(overlap) > 0:
        print("WARNING: leakage detected — the same transaction appears in both train and test!")


def main():
    train_df = load_csv_safely(TRAIN_CSV)
    test_df = load_csv_safely(TEST_CSV)

    train_report = inspect(train_df, "fraudTrain.csv")
    test_report = inspect(test_df, "fraudTest.csv")

    print_report(train_report)
    print_report(test_report)
    check_train_test_overlap(train_df, test_df)

    REPORTS_DIR.mkdir(exist_ok=True)
    with open(REPORTS_DIR / "data_quality_report.txt", "w") as f:
        for report in (train_report, test_report):
            f.write(f"{report}\n\n")
    print(f"\nReport also saved to {REPORTS_DIR / 'data_quality_report.txt'}")


if __name__ == "__main__":
    main()
