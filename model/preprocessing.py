"""
preprocessing.py — Step 3/5: Feature engineering + preprocessing pipeline.

What this does (plain terms):
1. Takes the raw dataframe (as loaded from fraudTrain.csv / fraudTest.csv).
2. Builds a few new, meaningful features (distance from home, transaction hour, age)
   from the raw columns — this is "feature engineering."
3. Builds a scikit-learn ColumnTransformer that scales numeric features and
   one-hot encodes categorical features, WITHOUT ever looking at the target column.

Important rule this file follows: the preprocessing pipeline is fit ONLY on
training data (in train.py), then reused (not refit) on validation/test data,
so information never leaks from validation/test into training.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from config import NUMERIC_FEATURES, CATEGORICAL_FEATURES, DROP_COLS


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/long points. Used to compute
    how far a transaction happened from the customer's home address."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds engineered columns (trans_hour, age_years, distance_from_home_km) to a copy
    of the input dataframe. Does not modify the original dataframe in place.
    Safe to call on train, validation, or test data identically (no leakage —
    every value here is computed from that single row's own raw columns).
    """
    df = df.copy()

    df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
    df["dob"] = pd.to_datetime(df["dob"])

    df["trans_hour"] = df["trans_date_trans_time"].dt.hour
    df["age_years"] = (df["trans_date_trans_time"] - df["dob"]).dt.days // 365
    df["distance_from_home_km"] = _haversine_km(
        df["lat"], df["long"], df["merch_lat"], df["merch_long"]
    )

    return df


def select_model_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keeps only the columns the model is actually allowed to use
    (per FEATURE_CONTRACT.md): required numeric + categorical features.
    Drops identifiers, PII, and raw helper columns already converted into
    engineered features.
    """
    keep_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    missing = [c for c in keep_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Expected engineered/raw columns missing before model selection: {missing}. "
            f"Did you call engineer_features() first?"
        )
    return df[keep_cols]


def build_preprocessor() -> ColumnTransformer:
    """
    Builds (but does not fit) the preprocessing pipeline:
    - Numeric features: median imputation + standard scaling
    - Categorical features: most-frequent imputation + one-hot encoding
    This matches the strategy documented in FEATURE_CONTRACT.md.
    """
    numeric_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", numeric_pipeline, NUMERIC_FEATURES),
        ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
    ])

    return preprocessor


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience wrapper: engineer features, then select only model-ready columns."""
    df_eng = engineer_features(df)
    return select_model_columns(df_eng)
