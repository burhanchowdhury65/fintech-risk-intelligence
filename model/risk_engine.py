"""
risk_engine.py — Day 4, Step 3: risk classification and explanation logic,
kept separate from model inference (predict.py) and API routing (api.py),
per Day 4's requested modular structure.

Everything here is explicitly PROVISIONAL / PENDING CONFIRMATION where noted —
see docs/RISK_SCORE.md and docs/DAY4_DECISIONS.md for the full reasoning.
"""

# Decision threshold selected on VALIDATION data only (Day 3's finalize_candidate.py).
# Applied to the model's raw [0,1] score to decide the boolean is_fraud classification.
# FROZEN FOR DAY 5: Person A confirmed (Day 5 kickoff) this default is acceptable for the
# integration/demo, on the condition that the validation basis and trade-off are documented
# rather than presented as a universally business-optimal value — see docs/RISK_SCORE.md §7
# and reports/DAY3_MODEL_COMPARISON_AND_ANALYSIS.md's threshold sweep for that documentation.
# This is still not claimed as a validated long-term business decision, only a demo default.
DECISION_THRESHOLD = 0.80

# PROVISIONAL risk_status cutoffs (0-100 display scale) — NOT derived from a validated
# business decision. See docs/RISK_SCORE.md §6. Kept as named constants here (rather than
# hardcoded in the function below) specifically so they are easy to find and override
# once the team confirms real thresholds.
RISK_STATUS_LOW_MAX = 40
RISK_STATUS_MEDIUM_MAX = 70


def classify(raw_score: float) -> tuple[bool, int, str]:
    """
    Takes the model's raw [0,1] probability-like score and returns:
    (is_fraud: bool, risk_score_0_100: int, risk_status: str)

    is_fraud is threshold-based (DECISION_THRESHOLD), not just "is risk_status == high" —
    these are two independent, configurable pieces of logic that happen to both derive
    from the same underlying raw_score.
    """
    risk_score_0_100 = int(round(raw_score * 100))
    is_fraud = bool(raw_score >= DECISION_THRESHOLD)

    if risk_score_0_100 < RISK_STATUS_LOW_MAX:
        risk_status = "low"
    elif risk_score_0_100 < RISK_STATUS_MEDIUM_MAX:
        risk_status = "medium"
    else:
        risk_status = "high"

    return is_fraud, risk_score_0_100, risk_status


def build_model_factors(features: dict, is_fraud: bool) -> list[str]:
    """
    PROVISIONAL: very simple, transparent rule-based explanation hints.
    NOT a formal SHAP/feature-importance explanation — do not present this as one
    to the team, judges, or end users. See docs/DAY4_PERSON_A_HANDOFF.md §9.

    Only surfaces factors when a prediction is flagged as fraud; an empty list for a
    legitimate-looking prediction is expected behavior, not a bug.
    """
    factors = []
    if not is_fraud:
        return factors

    if features.get("amt", 0) > 500:
        factors.append("Transaction amount is unusually high")
    if features.get("distance_from_home_km") is not None and features["distance_from_home_km"] > 100:
        factors.append("Transaction location is far from customer's home")
    if features.get("trans_hour") is not None and (features["trans_hour"] < 5 or features["trans_hour"] > 23):
        factors.append("Transaction occurred at an unusual hour")

    if not factors:
        factors.append("Model flagged this transaction as high risk based on overall pattern")
    return factors
