"""
tests/test_pipeline.py — Step 9: Tests for data quality, preprocessing, model, and API.

Run with (from the model/ folder):
    pytest tests/ -v

Uses a small synthetic sample for fast tests, plus a couple of tests that check
the real saved artifacts if they exist (skipped otherwise, not silently passed).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import pytest
import joblib

from config import MODEL_PATH, NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGET_COL
from preprocessing import engineer_features, select_model_columns, build_preprocessor


def make_synthetic_raw_df(n=20, seed=0):
    """A small synthetic dataframe shaped like fraudTrain/fraudTest.csv, for fast tests
    that don't depend on the real 1M+ row file being present."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="h")
    dobs = pd.date_range("1970-01-01", periods=n, freq="365D")
    return pd.DataFrame({
        "trans_date_trans_time": dates.astype(str),
        "cc_num": rng.integers(1000, 9999, n),
        "merchant": [f"fraud_Merchant{i}" for i in range(n)],
        "category": rng.choice(["grocery_pos", "shopping_net", "gas_transport"], n),
        "amt": rng.uniform(1, 500, n).round(2),
        "first": ["Test"] * n,
        "last": ["User"] * n,
        "gender": rng.choice(["M", "F"], n),
        "street": ["123 St"] * n,
        "city": ["Testville"] * n,
        "state": ["TS"] * n,
        "zip": rng.integers(10000, 99999, n),
        "lat": rng.uniform(30, 45, n),
        "long": rng.uniform(-100, -80, n),
        "city_pop": rng.integers(100, 500000, n),
        "job": ["Engineer"] * n,
        "dob": dobs.astype(str),
        "trans_num": [f"tx{i}" for i in range(n)],
        "unix_time": rng.integers(1_500_000_000, 1_600_000_000, n),
        "merch_lat": rng.uniform(30, 45, n),
        "merch_long": rng.uniform(-100, -80, n),
        TARGET_COL: rng.choice([0, 1], n, p=[0.9, 0.1]),
    })


class TestDatasetSchema:
    def test_target_column_exists_and_is_binary(self):
        df = make_synthetic_raw_df()
        assert TARGET_COL in df.columns
        assert set(df[TARGET_COL].unique()).issubset({0, 1})

    def test_no_missing_values_in_synthetic_sample(self):
        df = make_synthetic_raw_df()
        assert df.isna().sum().sum() == 0

    def test_trans_num_is_unique(self):
        df = make_synthetic_raw_df()
        assert df["trans_num"].duplicated().sum() == 0


class TestFeatureEngineering:
    def test_engineered_columns_created(self):
        df = make_synthetic_raw_df()
        out = engineer_features(df)
        for col in ["trans_hour", "age_years", "distance_from_home_km"]:
            assert col in out.columns

    def test_no_nan_introduced_by_engineering(self):
        df = make_synthetic_raw_df()
        out = engineer_features(df)
        assert out[["trans_hour", "age_years", "distance_from_home_km"]].isna().sum().sum() == 0

    def test_trans_hour_in_valid_range(self):
        df = make_synthetic_raw_df()
        out = engineer_features(df)
        assert out["trans_hour"].between(0, 23).all()

    def test_distance_is_non_negative(self):
        df = make_synthetic_raw_df()
        out = engineer_features(df)
        assert (out["distance_from_home_km"] >= 0).all()

    def test_select_model_columns_raises_if_engineering_skipped(self):
        df = make_synthetic_raw_df()
        with pytest.raises(ValueError):
            select_model_columns(df)  # engineer_features() not called first

    def test_select_model_columns_returns_expected_columns(self):
        df = make_synthetic_raw_df()
        out = select_model_columns(engineer_features(df))
        assert list(out.columns) == NUMERIC_FEATURES + CATEGORICAL_FEATURES
        # identifiers/PII must NOT leak into the model-ready columns
        for leaky_col in ["cc_num", "trans_num", "first", "last", "street", TARGET_COL]:
            assert leaky_col not in out.columns


class TestPreprocessingPipeline:
    def test_pipeline_fits_and_transforms_without_error(self):
        df = make_synthetic_raw_df(n=50)
        X = select_model_columns(engineer_features(df))
        preprocessor = build_preprocessor()
        X_transformed = preprocessor.fit_transform(X)
        assert X_transformed.shape[0] == 50

    def test_pipeline_handles_unseen_category_at_inference(self):
        """A category seen at inference but not during training should not crash
        (OneHotEncoder(handle_unknown='ignore') should absorb it)."""
        df_train = make_synthetic_raw_df(n=30, seed=1)
        df_new = make_synthetic_raw_df(n=5, seed=2)
        df_new.loc[0, "category"] = "totally_new_category_not_seen_in_training"

        X_train = select_model_columns(engineer_features(df_train))
        X_new = select_model_columns(engineer_features(df_new))

        preprocessor = build_preprocessor()
        preprocessor.fit(X_train)
        X_new_transformed = preprocessor.transform(X_new)  # should not raise
        assert X_new_transformed.shape[0] == 5


class TestSavedModelArtifact:
    """These tests check the REAL saved model, and are skipped (not silently passed)
    if train.py hasn't been run yet, so a missing artifact is visible, not hidden."""

    def test_model_file_exists(self):
        if not Path(MODEL_PATH).exists():
            pytest.skip(f"{MODEL_PATH} not found — run train.py first.")
        assert Path(MODEL_PATH).exists()

    def test_saved_pipeline_loads_and_predicts_expected_shape(self):
        if not Path(MODEL_PATH).exists():
            pytest.skip(f"{MODEL_PATH} not found — run train.py first.")
        pipeline = joblib.load(MODEL_PATH)
        df = make_synthetic_raw_df(n=10, seed=3)
        X = select_model_columns(engineer_features(df))
        preds = pipeline.predict(X)
        probs = pipeline.predict_proba(X)
        assert preds.shape == (10,)
        assert probs.shape == (10, 2)
        assert set(np.unique(preds)).issubset({0, 1})
        assert (probs >= 0).all() and (probs <= 1).all()

    def test_prediction_is_deterministic_on_repeat_calls(self):
        if not Path(MODEL_PATH).exists():
            pytest.skip(f"{MODEL_PATH} not found — run train.py first.")
        pipeline = joblib.load(MODEL_PATH)
        df = make_synthetic_raw_df(n=5, seed=4)
        X = select_model_columns(engineer_features(df))
        preds1 = pipeline.predict(X)
        preds2 = pipeline.predict(X)
        assert (preds1 == preds2).all()


class TestPredictModule:
    def test_predict_one_returns_expected_fields(self):
        """NOTE (Day 4): predict.py now takes raw frontend field names
        (transaction_amount, merchant_category, transaction_time, distance_from_home)
        and returns the team-agreed public field names (is_fraud, risk_status)
        instead of the old internal names (predicted_class, risk_category).
        See docs/DAY4_DATA_CONTRACT.md."""
        if not Path(MODEL_PATH).exists():
            pytest.skip(f"{MODEL_PATH} not found — run train.py first.")
        from predict import predict_one
        result = predict_one({
            "transaction_amount": 50.0, "merchant_category": "grocery_pos",
            "transaction_time": "2026-01-01T12:00:00",
            "distance_from_home": 5.0, "age_years": 30, "city_pop": 10000, "gender": "M",
        })
        for field in ["risk_score", "score_type", "is_fraud", "risk_status", "model_version", "model_factors"]:
            assert field in result
        assert 0 <= result["risk_score"] <= 100
        assert isinstance(result["is_fraud"], bool)
        assert result["risk_status"] in ("low", "medium", "high")

    def test_predict_one_missing_model_raises_filenotfound(self, monkeypatch):
        import predict
        monkeypatch.setattr(predict, "MODEL_PATH", Path("nonexistent_model.joblib"))
        monkeypatch.setattr(predict, "_pipeline", None)
        with pytest.raises(FileNotFoundError):
            predict.get_pipeline()


class TestAPISchemas:
    """Updated Day 4: TransactionRequest now uses the frontend's raw field names
    (transaction_amount, merchant_category, transaction_time) instead of the model's
    internal feature names (amt, category, trans_hour). See docs/DAY4_DATA_CONTRACT.md."""

    def test_valid_request_passes_validation(self):
        from schemas import TransactionRequest
        req = TransactionRequest(
            request_id="r1", transaction_id="t1", transaction_amount=100.0,
            merchant_category="grocery_pos", transaction_time="2026-01-01T10:00:00",
        )
        assert req.transaction_amount == 100.0

    def test_negative_amount_rejected(self):
        from schemas import TransactionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionRequest(request_id="r1", transaction_id="t1", transaction_amount=-5,
                                merchant_category="grocery_pos", transaction_time="2026-01-01T10:00:00")

    def test_missing_required_field_rejected(self):
        from schemas import TransactionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionRequest(request_id="r1", transaction_id="t1",
                                merchant_category="grocery_pos", transaction_time="2026-01-01T10:00:00")  # transaction_amount missing

    def test_invalid_datetime_rejected(self):
        from schemas import TransactionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionRequest(request_id="r1", transaction_id="t1", transaction_amount=10,
                                merchant_category="grocery_pos", transaction_time="not-a-date")

    def test_empty_category_rejected(self):
        from schemas import TransactionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionRequest(request_id="r1", transaction_id="t1", transaction_amount=10,
                                merchant_category="   ", transaction_time="2026-01-01T10:00:00")

    def test_transaction_type_and_location_accepted_but_optional(self):
        """Day 4 decision: transaction_type/location are accepted (not rejected) even
        though no trained model feature currently uses them."""
        from schemas import TransactionRequest
        req = TransactionRequest(
            request_id="r1", transaction_id="t1", transaction_amount=10,
            merchant_category="grocery_pos", transaction_time="2026-01-01T10:00:00",
            transaction_type="transfer", location={"lat": 1.0, "long": 2.0},
        )
        assert req.transaction_type == "transfer"

    def test_missing_request_id_and_transaction_id_auto_generated(self):
        """Day 5 bug fix: Person A's real backend example omits request_id/transaction_id
        entirely. The node must NOT hard-reject this (previous behavior, verified broken
        in this session's Phase 1 test) — it should auto-generate placeholders instead."""
        from schemas import TransactionRequest
        req = TransactionRequest(
            transaction_amount=1250.50, merchant_category="shopping_net",
            transaction_time="2026-09-27T14:30:00",
        )
        assert req.request_id is not None and req.request_id.startswith("auto_")
        assert req.transaction_id is not None and req.transaction_id.startswith("auto_")

    def test_provided_request_id_is_preserved_not_overwritten(self):
        from schemas import TransactionRequest
        req = TransactionRequest(
            request_id="my_real_id", transaction_id="my_real_txn",
            transaction_amount=10, merchant_category="grocery_pos",
            transaction_time="2026-01-01T10:00:00",
        )
        assert req.request_id == "my_real_id"
        assert req.transaction_id == "my_real_txn"

    def test_null_merchant_category_accepted_not_rejected(self):
        """Day 5 bug fix: Person A's backend types merchant_category as 'string or null'.
        The node previously hard-rejected null with a 422 (verified broken in this
        session's Phase 1 test). Null must now be accepted — the trained imputer fills
        it with the most-frequent training category (verified working separately)."""
        from schemas import TransactionRequest
        req = TransactionRequest(
            request_id="r1", transaction_id="t1", transaction_amount=10,
            merchant_category=None, transaction_time="2026-01-01T10:00:00",
        )
        assert req.merchant_category is None

    def test_empty_string_category_still_rejected(self):
        """Distinguishes genuine 'unknown' (null, now allowed) from a likely caller bug
        (empty string, still rejected)."""
        from schemas import TransactionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionRequest(
                request_id="r1", transaction_id="t1", transaction_amount=10,
                merchant_category="   ", transaction_time="2026-01-01T10:00:00",
            )

    def test_null_transaction_amount_still_rejected(self):
        """transaction_amount stays required/non-null even though Person A's backend
        types it as 'float or null' — flagged as an open question, not silently patched,
        since a transaction cannot be meaningfully risk-scored without an amount."""
        from schemas import TransactionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionRequest(
                request_id="r1", transaction_id="t1", transaction_amount=None,
                merchant_category="grocery_pos", transaction_time="2026-01-01T10:00:00",
            )
