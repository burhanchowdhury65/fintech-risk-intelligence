"""
tests/test_risk_engine.py — Day 4, Step 7: tests for risk_engine.py's classification
and explanation logic, isolated from the model/API.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from risk_engine import classify, build_model_factors, DECISION_THRESHOLD


class TestClassify:
    def test_score_below_threshold_is_not_fraud(self):
        is_fraud, score, status = classify(0.1)
        assert is_fraud is False
        assert score == 10

    def test_score_above_threshold_is_fraud(self):
        is_fraud, score, status = classify(0.95)
        assert is_fraud is True
        assert score == 95

    def test_score_exactly_at_threshold_is_fraud(self):
        """>= threshold, not > threshold — boundary check."""
        is_fraud, score, status = classify(DECISION_THRESHOLD)
        assert is_fraud is True

    def test_risk_score_is_native_int(self):
        _, score, _ = classify(0.5)
        assert isinstance(score, int)

    def test_is_fraud_is_native_bool_not_numpy_bool(self):
        """Regression test: an earlier version returned numpy.bool_, which can behave
        unexpectedly under some JSON serializers. Must be a plain Python bool."""
        is_fraud, _, _ = classify(0.9)
        assert type(is_fraud) is bool

    def test_status_low_medium_high_boundaries(self):
        _, _, status_low = classify(0.05)     # score 5
        _, _, status_med = classify(0.50)     # score 50
        _, _, status_high = classify(0.90)    # score 90
        assert status_low == "low"
        assert status_med == "medium"
        assert status_high == "high"


class TestBuildModelFactors:
    def test_no_factors_when_not_fraud(self):
        factors = build_model_factors({"amt": 900, "distance_from_home_km": 300}, is_fraud=False)
        assert factors == []

    def test_high_amount_factor_present_when_fraud(self):
        factors = build_model_factors({"amt": 900}, is_fraud=True)
        assert any("amount" in f.lower() for f in factors)

    def test_far_distance_factor_present_when_fraud(self):
        factors = build_model_factors({"amt": 10, "distance_from_home_km": 500}, is_fraud=True)
        assert any("distance" in f.lower() or "home" in f.lower() for f in factors)

    def test_unusual_hour_factor_present_when_fraud(self):
        factors = build_model_factors({"amt": 10, "trans_hour": 3}, is_fraud=True)
        assert any("hour" in f.lower() for f in factors)

    def test_fallback_factor_when_nothing_unusual_but_still_fraud(self):
        """The model can still say 'fraud' even when no individual rule-of-thumb
        threshold is triggered — must not return an empty, unexplained list."""
        factors = build_model_factors({"amt": 10, "distance_from_home_km": 1, "trans_hour": 12}, is_fraud=True)
        assert len(factors) >= 1
