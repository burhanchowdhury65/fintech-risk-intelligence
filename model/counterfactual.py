"""
counterfactual.py — "What Would Fix This?" — Phase 2.

Reuses the already-trained pipeline's predict_proba(). No retraining, no new model.

Searches ONE feature at a time, over a bounded, documented set of candidate values,
until a candidate flips risk_engine.classify()'s is_fraud decision to False. Reuses
risk_engine.classify() itself for the flip check, so this can never silently drift
from the real decision logic if the threshold/cutoffs change later (see Phase 1
inspection risk #3).

Candidate order: amt, then trans_hour, then distance_from_home_km — matches the
roadmap's stated order. The search returns the FIRST feature (in that order) that
finds a flip, not necessarily the "best" one — documented as a limitation, not hidden.
"""

import pandas as pd
from risk_engine import classify
from config import NUMERIC_FEATURES, CATEGORICAL_FEATURES

# --- Bounded, documented candidate ranges ---
# amt: proportional reductions. Domain reasoning: a counterfactual "lower amount" only
# makes sense as a reduction (raising amount to reduce fraud risk is not a realistic
# or intended suggestion), so only reductions are tried, in increasing steps.
AMT_REDUCTION_FRACTIONS = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 0.97]

# trans_hour: every valid hour of day (0-23) except the original hour, tried in a fixed
# deterministic order (0..23) so results are reproducible run-to-run.
HOUR_CANDIDATES = list(range(24))

# distance_from_home_km: proportional reductions, same reasoning as amt (a shorter
# distance is the realistic "what if" direction, not a longer one).
DISTANCE_REDUCTION_FRACTIONS = [0.5, 0.7, 0.9, 0.97, 0.99]

FEATURE_LABELS = {
    "amt": "transaction amount",
    "trans_hour": "time of day",
    "distance_from_home_km": "distance from home",
}

# Order matters: this is the order features are tried in. First flip found wins.
SEARCH_ORDER = ["amt", "trans_hour", "distance_from_home_km"]

NOT_FOUND = {
    "found": False,
    "changed_feature": None,
    "changed_feature_label": None,
    "original_value": None,
    "suggested_value": None,
    "new_risk_score": None,
    "new_risk_status": None,
    "reason": None,
}


def _score(pipeline, features: dict) -> float:
    """Runs one candidate through the exact same DataFrame construction predict_one()
    uses (Phase 1 risk #2) — same column order, same feature set."""
    X = pd.DataFrame([features])[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    return float(pipeline.predict_proba(X)[0, 1])


def _try_amt(pipeline, features: dict):
    original = features.get("amt")
    if original is None or original <= 0:
        return None
    for frac in AMT_REDUCTION_FRACTIONS:
        candidate = dict(features)  # fresh copy — never mutate the original (Phase 1 risk #1)
        candidate["amt"] = round(original * (1 - frac), 2)
        raw_score = _score(pipeline, candidate)
        is_fraud, risk_score, risk_status = classify(raw_score)  # reuse real decision logic (risk #3)
        if not is_fraud:
            return {
                "found": True,
                "changed_feature": "amt",
                "changed_feature_label": FEATURE_LABELS["amt"],
                "original_value": original,
                "suggested_value": candidate["amt"],
                "new_risk_score": risk_score,
                "new_risk_status": risk_status,
                "reason": f"If the transaction amount had been {candidate['amt']:.2f} instead of {original:.2f}, "
                          f"the risk score would have been {risk_score} instead of the original score.",
            }
    return None


def _try_trans_hour(pipeline, features: dict):
    original = features.get("trans_hour")
    if original is None:
        return None
    for hour in HOUR_CANDIDATES:
        if hour == original:
            continue
        candidate = dict(features)
        candidate["trans_hour"] = hour
        raw_score = _score(pipeline, candidate)
        is_fraud, risk_score, risk_status = classify(raw_score)
        if not is_fraud:
            return {
                "found": True,
                "changed_feature": "trans_hour",
                "changed_feature_label": FEATURE_LABELS["trans_hour"],
                "original_value": original,
                "suggested_value": hour,
                "new_risk_score": risk_score,
                "new_risk_status": risk_status,
                "reason": f"If the transaction had occurred at hour {hour} instead of {original}, "
                          f"the risk score would have been {risk_score} instead of the original score.",
            }
    return None


def _try_distance(pipeline, features: dict):
    original = features.get("distance_from_home_km")
    if original is None or original <= 0:
        return None  # missing/zero distance: nothing meaningful to reduce (Phase 1 risk #4)
    for frac in DISTANCE_REDUCTION_FRACTIONS:
        candidate = dict(features)
        candidate["distance_from_home_km"] = round(original * (1 - frac), 2)
        raw_score = _score(pipeline, candidate)
        is_fraud, risk_score, risk_status = classify(raw_score)
        if not is_fraud:
            return {
                "found": True,
                "changed_feature": "distance_from_home_km",
                "changed_feature_label": FEATURE_LABELS["distance_from_home_km"],
                "original_value": original,
                "suggested_value": candidate["distance_from_home_km"],
                "new_risk_score": risk_score,
                "new_risk_status": risk_status,
                "reason": f"If the transaction had been {candidate['distance_from_home_km']:.1f}km from home "
                          f"instead of {original:.1f}km, the risk score would have been {risk_score} instead of the original score.",
            }
    return None


_SEARCH_FUNCS = {
    "amt": _try_amt,
    "trans_hour": _try_trans_hour,
    "distance_from_home_km": _try_distance,
}


def build_counterfactual(pipeline, features: dict, is_fraud: bool) -> dict:
    """
    Entry point, matching predict.py's existing call pattern for build_model_factors(features, is_fraud).

    - Non-flagged transaction: returns {"found": False, ...} immediately, no search performed.
    - Flagged transaction: searches amt, then trans_hour, then distance_from_home_km (SEARCH_ORDER),
      returns the first flip found.
    - No candidate flips it within the bounded ranges: returns {"found": False, ...} cleanly.
    - Never raises: a missing feature is skipped (returns None from that feature's search), not an error.
    - Never mutates `features` — every candidate is built from a fresh dict copy.
    """
    if not is_fraud:
        return dict(NOT_FOUND)

    for feature_name in SEARCH_ORDER:
        try:
            result = _SEARCH_FUNCS[feature_name](pipeline, features)
        except Exception:
            # A single feature's search failing must not crash the whole counterfactual search,
            # let alone the prediction endpoint (Phase 3 requirement) — skip to the next feature.
            result = None
        if result is not None:
            return result

    return dict(NOT_FOUND)
