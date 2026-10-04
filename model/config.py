"""
config.py — central place for file paths, column names, and constants.
Change values here rather than hardcoding them in multiple scripts.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if present; safe no-op if it doesn't exist

# ---- Node server config (Day 5: Person A confirmed the ML node runs on 127.0.0.1:8001,
# separate from the backend's own 127.0.0.1:8000/analyze). Exposed via environment
# variables, per Person A's request, with sensible local-dev defaults. ----
NODE_HOST = os.environ.get("FRAUD_NODE_HOST", "127.0.0.1")
NODE_PORT = int(os.environ.get("FRAUD_NODE_PORT", "8001"))

# ---- Paths ----
# Adjust DATA_DIR to wherever fraudTrain.csv / fraudTest.csv actually live on your machine.
DATA_DIR = Path("data")
TRAIN_CSV = DATA_DIR / "fraudTrain.csv"
TEST_CSV = DATA_DIR / "fraudTest.csv"

# DAY 7 P0 FIX: anchor to this file's folder instead of the process's current working
# directory. Previously Path("artifacts") only resolved if the node was started from inside
# model/, otherwise /predict returned 503 MODEL_UNAVAILABLE while /health still said "ok".
# Reproduced and verified both before and after this fix (see reports/DAY7_*).
BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
REPORTS_DIR = Path("reports")

MODEL_PATH = ARTIFACTS_DIR / "fraud_model_pipeline.joblib"

# ---- Columns ----
TARGET_COL = "is_fraud"

# Identifier / PII columns — never used as model features (see FEATURE_CONTRACT.md)
DROP_COLS = [
    "cc_num", "trans_num", "first", "last", "street",
    "unix_time",  # redundant with trans_date_trans_time / derived trans_hour
]

# Raw columns used to build engineered features (kept temporarily, dropped after feature engineering)
HELPER_COLS = ["trans_date_trans_time", "dob", "lat", "long", "merch_lat", "merch_long"]

# Final feature columns fed to the model (after preprocessing) — matches FEATURE_CONTRACT.md
NUMERIC_FEATURES = ["amt", "distance_from_home_km", "trans_hour", "age_years", "city_pop"]
CATEGORICAL_FEATURES = ["category", "gender"]

RANDOM_SEED = 42

