"""
schemas.py — Day 4: Pydantic request/response schemas for POST /predict.

Field naming reflects the Day 4 team decisions (see docs/DAY4_DECISIONS.md):
- Request uses the FRONTEND's raw field names (transaction_amount, merchant_category,
  transaction_type, transaction_time, distance_from_home, location), NOT the model's
  internal feature names. The node itself is responsible for translating raw fields
  into the exact features the trained model expects — the frontend/backend must never
  have to know about `amt`, `category`, `trans_hour`, etc.
- Response uses the team-agreed public names: is_fraud, risk_score, risk_status,
  model_factors, model_version (NOT predicted_class/risk_category, which are the
  internal names used only inside predict.py).

Everything marked PROVISIONAL below is still pending final confirmation from Person A
and Person C — see docs/DAY4_DECISIONS.md and docs/DAY4_DATA_CONTRACT.md.
"""

from typing import Optional, Any, Union
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class TransactionRequest(BaseModel):
    """
    Raw API input, using the FRONTEND's field names (not the model's internal feature
    names). See docs/DAY4_DATA_CONTRACT.md for the full mapping table and which fields
    are actually used by the trained model vs. accepted-but-currently-unused.

    Day 5 fix: Person A's actual backend contract types transaction_amount, merchant_category,
    transaction_time, distance_from_home, and location as "or null" (Optional), and Person A's
    example /predict payload does not include request_id/transaction_id at all. The node was
    previously rejecting these with a hard 422, which would break real integration. Fixed here:
    - request_id / transaction_id: now Optional — node auto-generates one if the backend doesn't
      send it (see the validators below), rather than hard-failing. If the backend DOES send one,
      it's used and echoed back unchanged.
    - merchant_category: now Optional[str] — a null value is passed through to the trained
      pipeline's most-frequent-category imputer (verified working), rather than rejected outright.
    - transaction_amount is intentionally KEPT REQUIRED (not nullable) even though Person A's
      backend types it as "float or null" — a transaction cannot be meaningfully risk-scored
      without an amount, so a null here is treated as a genuine input error (422), not silently
      imputed. This is flagged as an open question for Person A in the Phase 2 compatibility
      table rather than silently patched, since imputing a fabricated amount could produce a
      misleading prediction.
    """
    request_id: Optional[str] = Field(default_factory=lambda: f"auto_{uuid4().hex[:12]}", description="If not provided by the caller, the node generates one")
    transaction_id: Optional[str] = Field(default_factory=lambda: f"auto_{uuid4().hex[:12]}", description="If not provided by the caller, the node generates one")

    # --- Required, used by the model ---
    transaction_amount: float = Field(..., gt=0, description="Maps to model feature 'amt'. Required — cannot be null (see class docstring).")
    merchant_category: Optional[str] = Field(None, description="Maps to model feature 'category'. Node handles encoding internally. Null is accepted — the trained imputer fills it with the most-frequent training category.")
    transaction_time: datetime = Field(..., description="ISO 8601 datetime; node derives 'trans_hour' (0-23) from this internally")

    # --- Accepted, but NOT used by the currently trained model (PROVISIONAL / PENDING) ---
    transaction_type: Optional[str] = Field(
        None,
        description="PENDING CONFIRMATION: no trained model feature currently corresponds to this field. "
                    "Accepted and stored, but NOT used in the current prediction. See docs/DAY4_DATA_CONTRACT.md.",
    )
    location: Optional[Any] = Field(
        None,
        description="PENDING CONFIRMATION: format not yet defined. NOT used to compute distance_from_home "
                    "automatically — the node does not calculate this on its own. See docs/DAY4_DECISIONS.md.",
    )

    # --- Optional, used by the model IF provided ---
    distance_from_home: Optional[float] = Field(
        None, ge=0,
        description="Optional numeric input, assumed to be in kilometers (matches how the model was trained "
                    "— see docs/RISK_SCORE.md/FEATURE_CONTRACT.md). Maps to model feature 'distance_from_home_km'. "
                    "The node does NOT calculate this from 'location' — if not provided, treated as missing.",
    )
    age_years: Optional[int] = Field(None, ge=0, le=120, description="Not in the frontend's current proposed field list — optional, used if provided")
    city_pop: Optional[int] = Field(None, ge=0, description="Not in the frontend's current proposed field list — optional, used if provided")
    gender: Optional[str] = Field(None, description="Not in the frontend's current proposed field list — optional; also flagged for a fairness/ethics discussion since Day 1, still unresolved")

    @field_validator("merchant_category")
    @classmethod
    def category_empty_string_rejected(cls, v: Optional[str]) -> Optional[str]:
        """None is fine (imputer handles it) — but an empty/whitespace STRING is almost
        certainly a caller bug, not a genuine 'no category' signal, so that's still rejected."""
        if v is not None and not v.strip():
            raise ValueError("merchant_category must not be an empty string (use null instead if truly unknown)")
        return v

    @field_validator("request_id", mode="before")
    @classmethod
    def generate_request_id_if_missing(cls, v):
        return v if v else f"auto_{uuid4().hex[:12]}"

    @field_validator("transaction_id", mode="before")
    @classmethod
    def generate_transaction_id_if_missing(cls, v):
        return v if v else f"auto_{uuid4().hex[:12]}"


class Counterfactual(BaseModel):
    """
    "What would fix this?" — Day 5+ optional add-on (see Counterfactual_Feature_Roadmap).
    Describes a HYPOTHETICAL single-feature change that would have flipped is_fraud to
    False, using the same trained pipeline and the same classify() decision logic as the
    real prediction. This is NOT a real transaction modification and NOT a guarantee that
    any similar transaction would be safe — see docs for full limitations once written.

    found=False case: every other field is null, by design (not an error state) — either
    the original transaction wasn't flagged, or no candidate within the bounded search
    range flipped the result. The two causes are not distinguished in this schema; both
    present identically as found=False.
    """
    found: bool = Field(..., description="Whether a single-feature change was found that flips is_fraud to False")
    changed_feature: Optional[str] = Field(None, description="Internal model feature name changed (e.g. 'amt', 'trans_hour', 'distance_from_home_km'), null if not found")
    changed_feature_label: Optional[str] = Field(None, description="Human-readable label for changed_feature, null if not found")
    original_value: Optional[Union[float, int]] = Field(None, description="The transaction's actual value for changed_feature, null if not found")
    suggested_value: Optional[Union[float, int]] = Field(None, description="The hypothetical candidate value that flipped the result, null if not found")
    new_risk_score: Optional[int] = Field(None, ge=0, le=100, description="Risk score the candidate would have produced, null if not found")
    new_risk_status: Optional[str] = Field(None, description="Risk status the candidate would have produced, null if not found")
    reason: Optional[str] = Field(None, description="Plain-language explanation of the hypothetical change, null if not found")


class PredictionResponse(BaseModel):
    """
    Public response schema, per Day 4's team decision:
    is_fraud / risk_score / risk_status / model_factors / model_version.
    Internally, predict.py still computes 'predicted_class' and 'risk_category' —
    this schema is where that gets mapped to the agreed public names.

    counterfactual: added as part of the optional "What Would Fix This?" add-on. This is
    a REQUIRED field on every response (always present, found=False when not applicable),
    not Optional — see docs for the integration note to Person A/C about this being a new
    required field for any existing stored/cached fixtures.
    """
    request_id: str
    transaction_id: str
    status: str = "ok"

    is_fraud: bool = Field(..., description="Final boolean fraud classification, derived from the model's score vs. the current decision threshold")
    risk_score: int = Field(..., ge=0, le=100, description="Relative risk score 0-100 — NOT a calibrated probability (see docs/RISK_SCORE.md)")
    score_type: str = "relative_risk_0_100_not_calibrated_probability"
    risk_status: str = Field(..., description="'low' / 'medium' / 'high' — PENDING CONFIRMATION: cutoffs are provisional, not team-approved (see docs/RISK_SCORE.md)")
    model_factors: list[str] = Field(default_factory=list, description="PROVISIONAL: simple rule-based explanation hints, NOT a formal SHAP/feature-importance explanation — see docs/DAY4_PERSON_A_HANDOFF.md")
    model_version: str
    counterfactual: Counterfactual = Field(..., description="Optional add-on: a hypothetical single-feature change that would have avoided the flag. found=False when not flagged or no candidate found.")


class ErrorResponse(BaseModel):
    request_id: Optional[str] = None
    transaction_id: Optional[str] = None
    status: str = "error"
    error_code: str
    error_message: str
