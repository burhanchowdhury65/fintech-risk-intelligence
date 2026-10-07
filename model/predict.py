"""
predict.py — Day 4: Prediction logic. Translates the FRONTEND's raw request fields
into the model's actual trained feature names, runs inference, and delegates
risk classification / explanation to risk_engine.py. Kept separate from api.py's
routing concerns, per Day 4's modular-structure requirement.

Field mapping (raw API name -> trained model feature), per docs/DAY4_DATA_CONTRACT.md:
  transaction_amount   -> amt
  merchant_category    -> category
  transaction_time     -> trans_hour (hour extracted from the timestamp)
  distance_from_home   -> distance_from_home_km (assumed already in km — see PENDING note)
  age_years, city_pop, gender -> passed through unchanged, if provided

  transaction_type, location -> ACCEPTED but NOT used in prediction. No trained model
  feature exists for transaction_type (the model only knows merchant_category/'category').
  location is not used to compute distance automatically — see docs/DAY4_DECISIONS.md.
"""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path

from config import ARTIFACTS_DIR, NUMERIC_FEATURES, CATEGORICAL_FEATURES
from risk_engine import classify, build_model_factors, DECISION_THRESHOLD
from counterfactual import build_counterfactual

# Day 3 update: serving the HistGradientBoosting candidate (better F1/precision than
# Day 2's Random Forest at a similar recall level — see reports/day3_final_test_evaluation.json).
# Re-verified directly from the saved artifact on Day 4 (not just assumed) — see
# reports/DAY4_STEP1_AUDIT.md. The Day 2 artifact is left on disk, untouched, for rollback.
MODEL_PATH = ARTIFACTS_DIR / "fraud_model_candidate_day3_histgb.joblib"
MODEL_VERSION = "histgb-candidate-day3-v1"

_pipeline = None


def get_pipeline():
    """Loads the saved pipeline once (lazy singleton) rather than on every request."""
    global _pipeline
    if _pipeline is None:
        if not Path(MODEL_PATH).exists():
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PATH}. Run finalize_candidate.py first to produce it."
            )
        _pipeline = joblib.load(MODEL_PATH)
    return _pipeline


def _map_raw_request_to_features(request_dict: dict) -> dict:
    """
    Translates the frontend's raw field names into the model's trained feature names.
    This is the ONE place that mapping happens — the frontend/backend should never need
    to know the model's internal feature names (amt, category, trans_hour, ...).
    """
    transaction_time = request_dict["transaction_time"]
    # transaction_time may arrive as a datetime object (already parsed by Pydantic) or
    # as an ISO string if this function is called directly/in tests — handle both.
    if isinstance(transaction_time, str):
        transaction_time = pd.to_datetime(transaction_time)
    trans_hour = transaction_time.hour

    location = request_dict.get("location")
    calculated_distance = None

    if isinstance(location, dict):
        try:
            R = 6371.0
            lat1 = np.radians(float(location["customer_lat"]))
            lon1 = np.radians(float(location["customer_long"]))
            lat2 = np.radians(float(location["merchant_lat"]))
            lon2 = np.radians(float(location["merchant_long"]))

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = (
                np.sin(dlat / 2) ** 2
                + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
            )
            calculated_distance = float(
                R * 2 * np.arcsin(np.sqrt(a))
            )
        except (KeyError, TypeError, ValueError):
            calculated_distance = None

    return {
        "amt": request_dict["transaction_amount"],
        "category": request_dict["merchant_category"],
        "trans_hour": trans_hour,
        "distance_from_home_km": (
            calculated_distance
            if calculated_distance is not None
            else request_dict.get("distance_from_home")
        ),
        "age_years": request_dict.get("age_years"),
        "city_pop": request_dict.get("city_pop"),
        "gender": request_dict.get("gender"),
    }


def predict_one(request_dict: dict) -> dict:
    """
    Takes a dict matching TransactionRequest's fields (already Pydantic-validated by
    the caller) and returns a dict matching PredictionResponse's public fields
    (is_fraud, risk_score, risk_status, model_factors, model_version).
    """
    pipeline = get_pipeline()

    features = _map_raw_request_to_features(request_dict)
    X = pd.DataFrame([features])[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    raw_score = pipeline.predict_proba(X)[0, 1]

    # Internal names (predicted_class-equivalent logic lives in risk_engine.classify);
    # the public API response uses is_fraud / risk_status, per the team's Day 4 decision.
    is_fraud, risk_score_0_100, risk_status = classify(raw_score)
    model_factors = build_model_factors(features, is_fraud)

    # Additive, optional feature — per Phase 3 rule #6, a counterfactual-search failure
    # must never crash an otherwise-valid prediction. The original prediction above is
    # already fully computed at this point and is never touched by anything below.
    try:
        counterfactual = build_counterfactual(pipeline, features, is_fraud)
    except Exception:
        counterfactual = {
            "found": False, "changed_feature": None, "changed_feature_label": None,
            "original_value": None, "suggested_value": None,
            "new_risk_score": None, "new_risk_status": None, "reason": None,
        }

    return {
        "is_fraud": is_fraud,
        "risk_score": risk_score_0_100,
        "score_type": "relative_risk_0_100_not_calibrated_probability",
        "risk_status": risk_status,
        "model_version": MODEL_VERSION,
        "model_factors": model_factors,
        "counterfactual": counterfactual,
    }
