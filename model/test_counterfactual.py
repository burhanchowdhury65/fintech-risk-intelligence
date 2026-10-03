"""
tests/test_counterfactual.py — Phase 5, Tests A-G for the counterfactual feature.

Run with (from model/ folder):
    pytest tests/test_counterfactual.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import copy
import joblib
import pandas as pd
import pytest

from config import ARTIFACTS_DIR, NUMERIC_FEATURES, CATEGORICAL_FEATURES
from counterfactual import build_counterfactual
from risk_engine import classify

MODEL_PATH = ARTIFACTS_DIR / "fraud_model_candidate_day3_histgb.joblib"

FLAGGED = {"amt": 890.0, "distance_from_home_km": 240.0, "trans_hour": 3,
           "age_years": None, "city_pop": None, "category": "shopping_net", "gender": None}
NORMAL = {"amt": 45.0, "distance_from_home_km": None, "trans_hour": 14,
          "age_years": None, "city_pop": None, "category": "grocery_pos", "gender": None}


@pytest.fixture(scope="module")
def pipeline():
    if not Path(MODEL_PATH).exists():
        pytest.skip(f"{MODEL_PATH} not found — run finalize_candidate.py first.")
    return joblib.load(MODEL_PATH)


def _score(pipeline, features):
    X = pd.DataFrame([features])[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    return float(pipeline.predict_proba(X)[0, 1])


class TestA_CounterfactualFound:
    """Test A — real, reproducible flagged transaction (the team's agreed demo scenario)."""

    def test_original_is_flagged(self, pipeline):
        raw = _score(pipeline, FLAGGED)
        is_fraud, _, _ = classify(raw)
        assert is_fraud is True

    def test_valid_candidate_found(self, pipeline):
        raw = _score(pipeline, FLAGGED)
        is_fraud, _, _ = classify(raw)
        result = build_counterfactual(pipeline, FLAGGED, is_fraud)
        assert result["found"] is True

    def test_only_one_feature_changes(self, pipeline):
        result = build_counterfactual(pipeline, FLAGGED, True)
        assert result["changed_feature"] in ("amt", "trans_hour", "distance_from_home_km")
        # exactly one of original/suggested pair is reported, not multiple
        assert result["original_value"] is not None and result["suggested_value"] is not None

    def test_candidate_is_no_longer_flagged(self, pipeline):
        result = build_counterfactual(pipeline, FLAGGED, True)
        candidate = dict(FLAGGED)
        candidate[result["changed_feature"]] = result["suggested_value"]
        raw = _score(pipeline, candidate)
        is_fraud, _, _ = classify(raw)
        assert is_fraud is False

    def test_returned_score_matches_fresh_prediction(self, pipeline):
        result = build_counterfactual(pipeline, FLAGGED, True)
        candidate = dict(FLAGGED)
        candidate[result["changed_feature"]] = result["suggested_value"]
        raw = _score(pipeline, candidate)
        _, fresh_score, fresh_status = classify(raw)
        assert fresh_score == result["new_risk_score"]
        assert fresh_status == result["new_risk_status"]

    def test_original_input_dict_not_mutated(self, pipeline):
        original_copy = copy.deepcopy(FLAGGED)
        build_counterfactual(pipeline, FLAGGED, True)
        assert FLAGGED == original_copy


class TestB_NonFlagged:
    """Test B — non-flagged transaction returns found:false without searching."""

    def test_found_false(self, pipeline):
        result = build_counterfactual(pipeline, NORMAL, False)
        assert result["found"] is False

    def test_all_other_fields_null(self, pipeline):
        result = build_counterfactual(pipeline, NORMAL, False)
        for field in ("changed_feature", "changed_feature_label", "original_value",
                      "suggested_value", "new_risk_score", "new_risk_status", "reason"):
            assert result[field] is None

    def test_no_exception_raised(self, pipeline):
        try:
            build_counterfactual(pipeline, NORMAL, False)
        except Exception as e:
            pytest.fail(f"Raised unexpectedly: {e}")


class TestC_NoCandidateFound:
    """Test C — bounded search returns found:false cleanly when nothing in range flips it."""

    def test_extreme_case_with_no_searchable_features(self, pipeline):
        # amt/trans_hour/distance all None/0 -> nothing to search -> found:False, not an error
        no_features = {"amt": None, "distance_from_home_km": None, "trans_hour": None,
                        "age_years": None, "city_pop": None, "category": "shopping_net", "gender": None}
        result = build_counterfactual(pipeline, no_features, True)
        assert result["found"] is False
        assert result["reason"] is None


class TestD_MissingOrInvalidFeatures:
    """Test D — missing/invalid features never crash /predict."""

    def test_missing_distance_does_not_crash(self, pipeline):
        features = {**FLAGGED, "distance_from_home_km": None}
        try:
            result = build_counterfactual(pipeline, features, True)
        except Exception as e:
            pytest.fail(f"Raised unexpectedly: {e}")
        assert "found" in result

    def test_missing_trans_hour_does_not_crash(self, pipeline):
        features = {**FLAGGED, "trans_hour": None}
        try:
            result = build_counterfactual(pipeline, features, True)
        except Exception as e:
            pytest.fail(f"Raised unexpectedly: {e}")
        assert "found" in result

    def test_zero_amt_does_not_crash(self, pipeline):
        features = {**FLAGGED, "amt": 0}
        try:
            result = build_counterfactual(pipeline, features, True)
        except Exception as e:
            pytest.fail(f"Raised unexpectedly: {e}")
        assert "found" in result

    def test_negative_distance_does_not_crash(self, pipeline):
        """Shouldn't occur via the real API (schema rejects negative), but the search
        function itself must still not crash if ever called with one directly."""
        features = {**FLAGGED, "distance_from_home_km": -5}
        try:
            result = build_counterfactual(pipeline, features, True)
        except Exception as e:
            pytest.fail(f"Raised unexpectedly: {e}")
        assert "found" in result


class TestE_SchemaCompatibility:
    """Test E — existing response fields remain present and correctly typed, with
    counterfactual added, via the real predict_one() entry point."""

    def test_existing_fields_present_and_typed(self):
        if not Path(MODEL_PATH).exists():
            pytest.skip(f"{MODEL_PATH} not found.")
        from predict import predict_one
        result = predict_one({
            "transaction_amount": 890.0, "merchant_category": "shopping_net",
            "transaction_time": "2026-09-28T03:15:00", "distance_from_home": 240.0,
        })
        assert isinstance(result["is_fraud"], bool)
        assert isinstance(result["risk_score"], int)
        assert isinstance(result["risk_status"], str)
        assert isinstance(result["model_factors"], list)
        assert isinstance(result["model_version"], str)
        assert "counterfactual" in result
        assert isinstance(result["counterfactual"], dict)
        assert isinstance(result["counterfactual"]["found"], bool)

    def test_pydantic_schema_validates_flagged_response(self):
        from schemas import PredictionResponse
        payload = {
            "request_id": "r1", "transaction_id": "t1", "is_fraud": True, "risk_score": 99,
            "risk_status": "high", "model_factors": ["x"], "model_version": "v1",
            "counterfactual": {"found": True, "changed_feature": "amt", "changed_feature_label": "amount",
                                "original_value": 890.0, "suggested_value": 623.0,
                                "new_risk_score": 67, "new_risk_status": "medium", "reason": "because"},
        }
        resp = PredictionResponse(**payload)
        assert resp.counterfactual.found is True

    def test_pydantic_schema_validates_not_found_response(self):
        from schemas import PredictionResponse
        payload = {
            "request_id": "r1", "transaction_id": "t1", "is_fraud": False, "risk_score": 0,
            "risk_status": "low", "model_factors": [], "model_version": "v1",
            "counterfactual": {"found": False, "changed_feature": None, "changed_feature_label": None,
                                "original_value": None, "suggested_value": None,
                                "new_risk_score": None, "new_risk_status": None, "reason": None},
        }
        resp = PredictionResponse(**payload)
        assert resp.counterfactual.found is False


class TestF_Determinism:
    """Test F — same input run repeatedly returns the same candidate."""

    def test_repeated_runs_identical(self, pipeline):
        results = [build_counterfactual(pipeline, FLAGGED, True) for _ in range(5)]
        assert all(r == results[0] for r in results)


class TestG_RealEndpoint:
    """Test G — the actual /predict endpoint, real model inference, not a mock."""

    def test_real_predict_one_flagged_has_counterfactual(self):
        if not Path(MODEL_PATH).exists():
            pytest.skip(f"{MODEL_PATH} not found.")
        from predict import predict_one
        result = predict_one({
            "transaction_amount": 890.0, "merchant_category": "shopping_net",
            "transaction_time": "2026-09-28T03:15:00", "distance_from_home": 240.0,
        })
        assert result["counterfactual"]["found"] is True
        assert result["counterfactual"]["new_risk_score"] < result["risk_score"]

    def test_real_predict_one_normal_has_not_found(self):
        if not Path(MODEL_PATH).exists():
            pytest.skip(f"{MODEL_PATH} not found.")
        from predict import predict_one
        result = predict_one({
            "transaction_amount": 45.0, "merchant_category": "grocery_pos",
            "transaction_time": "2026-09-28T14:30:00",
        })
        assert result["counterfactual"]["found"] is False
