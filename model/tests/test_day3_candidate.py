"""
tests/test_day3_candidate.py — Day 3, Step 12: additional tests for the new
HistGradientBoosting candidate and API edge cases not covered by Day 2's suite.

Run with (from model/ folder):
    pytest tests/test_day3_candidate.py -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import joblib
import numpy as np
import pytest

from config import ARTIFACTS_DIR, REPORTS_DIR

CANDIDATE_MODEL_PATH = ARTIFACTS_DIR / "fraud_model_candidate_day3_histgb.joblib"


class TestDay3CandidateArtifact:
    def test_day3_candidate_file_exists(self):
        if not CANDIDATE_MODEL_PATH.exists():
            pytest.skip(f"{CANDIDATE_MODEL_PATH} not found — run finalize_candidate.py first.")
        assert CANDIDATE_MODEL_PATH.exists()

    def test_day2_baseline_artifact_still_untouched(self):
        """Day 3 must not overwrite or delete the Day 2 baseline artifact."""
        from config import MODEL_PATH as DAY2_MODEL_PATH
        assert DAY2_MODEL_PATH.exists(), "Day 2 baseline artifact is missing — it should never be deleted."

    def test_day3_metadata_file_has_required_fields(self):
        meta_path = REPORTS_DIR / "day3_candidate_metadata.json"
        if not meta_path.exists():
            pytest.skip("day3_candidate_metadata.json not found — run finalize_candidate.py first.")
        with open(meta_path) as f:
            meta = json.load(f)
        for field in ["model_version", "decision_threshold", "feature_order", "split_method", "validation_pr_auc"]:
            assert field in meta

    def test_day3_candidate_reproducible_on_reload(self):
        if not CANDIDATE_MODEL_PATH.exists():
            pytest.skip(f"{CANDIDATE_MODEL_PATH} not found — run finalize_candidate.py first.")
        import pandas as pd
        pipeline = joblib.load(CANDIDATE_MODEL_PATH)
        sample = pd.DataFrame([{
            "amt": 50.0, "distance_from_home_km": 5.0, "trans_hour": 12,
            "age_years": 30, "city_pop": 10000, "category": "grocery_pos", "gender": "M",
        }])
        preds1 = pipeline.predict(sample)
        preds2 = pipeline.predict(sample)
        assert (preds1 == preds2).all()


class TestDay3PredictModule:
    """Updated Day 4: predict_one() now takes raw frontend field names and returns
    is_fraud/risk_status (not predicted_class/risk_category). See docs/DAY4_DATA_CONTRACT.md."""

    def test_predict_uses_day3_model_version(self):
        if not CANDIDATE_MODEL_PATH.exists():
            pytest.skip(f"{CANDIDATE_MODEL_PATH} not found — run finalize_candidate.py first.")
        from predict import predict_one, MODEL_VERSION
        assert MODEL_VERSION == "histgb-candidate-day3-v1"
        result = predict_one({
            "transaction_amount": 50.0, "merchant_category": "grocery_pos",
            "transaction_time": "2026-01-01T12:00:00",
            "distance_from_home": 5.0, "age_years": 30, "city_pop": 10000, "gender": "M",
        })
        assert result["model_version"] == "histgb-candidate-day3-v1"

    def test_predict_handles_unknown_category_gracefully(self):
        """A merchant category the model never saw during training must not crash
        the API — OneHotEncoder(handle_unknown='ignore') should absorb it."""
        if not CANDIDATE_MODEL_PATH.exists():
            pytest.skip(f"{CANDIDATE_MODEL_PATH} not found — run finalize_candidate.py first.")
        from predict import predict_one
        result = predict_one({
            "transaction_amount": 50.0, "merchant_category": "some_totally_new_category_xyz",
            "transaction_time": "2026-01-01T12:00:00",
            "distance_from_home": 5.0, "age_years": 30, "city_pop": 10000, "gender": "M",
        })
        assert "risk_score" in result  # did not raise

    def test_predict_handles_missing_optional_fields(self):
        """Optional fields (distance_from_home/age/city_pop/gender) may legitimately be
        absent if the frontend doesn't collect them — must not crash."""
        if not CANDIDATE_MODEL_PATH.exists():
            pytest.skip(f"{CANDIDATE_MODEL_PATH} not found — run finalize_candidate.py first.")
        from predict import predict_one
        result = predict_one({
            "transaction_amount": 50.0, "merchant_category": "grocery_pos",
            "transaction_time": "2026-01-01T12:00:00",
        })
        assert "risk_score" in result

    def test_predict_ignores_transaction_type_and_location(self):
        """Day 4 decision: transaction_type/location are accepted by the schema but
        have NO effect on the prediction (no trained feature exists for them yet).
        Confirms two requests differing ONLY in these fields give the identical result."""
        if not CANDIDATE_MODEL_PATH.exists():
            pytest.skip(f"{CANDIDATE_MODEL_PATH} not found — run finalize_candidate.py first.")
        from predict import predict_one
        base = {
            "transaction_amount": 50.0, "merchant_category": "grocery_pos",
            "transaction_time": "2026-01-01T12:00:00",
        }
        result_without = predict_one(base)
        result_with = predict_one({**base, "transaction_type": "transfer", "location": {"lat": 1, "long": 2}})
        assert result_without["risk_score"] == result_with["risk_score"]
        assert result_without["is_fraud"] == result_with["is_fraud"]


class TestAPIEdgeCases:
    def test_wrong_type_for_amount_rejected(self):
        from schemas import TransactionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionRequest(request_id="r1", transaction_id="t1", transaction_amount="not_a_number",
                                merchant_category="grocery_pos", transaction_time="2026-01-01T10:00:00")

    def test_extra_unexpected_field_does_not_crash(self):
        """Pydantic v2 default behavior: extra fields are ignored unless configured
        otherwise. Confirms this doesn't raise for the orchestrator's convenience."""
        from schemas import TransactionRequest
        req = TransactionRequest(
            request_id="r1", transaction_id="t1", transaction_amount=10.0, merchant_category="grocery_pos",
            transaction_time="2026-01-01T10:00:00", some_unexpected_field="ignored",
        )
        assert req.transaction_amount == 10.0

    def test_malformed_datetime_type_rejected(self):
        from schemas import TransactionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionRequest(request_id="r1", transaction_id="t1", transaction_amount=10.0,
                                merchant_category="grocery_pos", transaction_time="noon-ish")


class TestReproducibility:
    def test_random_seed_documented_in_config(self):
        from config import RANDOM_SEED
        assert isinstance(RANDOM_SEED, int)

    def test_split_is_deterministic(self):
        from train import load_and_split
        _, y_train1, _, y_val1 = load_and_split()
        _, y_train2, _, y_val2 = load_and_split()
        assert len(y_train1) == len(y_train2)
        assert y_val1.sum() == y_val2.sum()
