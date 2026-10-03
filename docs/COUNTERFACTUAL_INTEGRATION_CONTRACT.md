# Counterfactual Feature — Integration Contract (for Person A and Person C)

Status: Verified against the real model, real `/predict` endpoint, 71/71 tests passing (51 existing + 20 new).
This is an **additive, optional add-on** — every existing `/predict` field is unchanged (see Phase 3/4 verification
in `reports/COUNTERFACTUAL_PHASE1_INSPECTION.md` and the final report for proof existing fields weren't touched).

## ⚠️ Breaking-change note for both of you
`counterfactual` is a **required field** on every `/predict` response (not `Optional` — always present, with
`found: false` when not applicable). If either of you has **cached/stored example responses** (e.g. Person C's
`cachedDemoFor()` fixtures) that don't include this field, **those will now fail validation** on the frontend side
once strict typing is applied. Those fixtures need a `counterfactual` key added (see example below) before this
ships — this wasn't broken by us, just flagging it before it causes a confusing bug for either of you.

## 1. Exact verified `/predict` request example (unchanged — no new request fields)
```json
{
  "request_id": "req_cf_test_1",
  "transaction_id": "txn_cf_test_1",
  "transaction_amount": 890.00,
  "merchant_category": "shopping_net",
  "transaction_time": "2026-09-28T03:15:00",
  "distance_from_home": 240.0
}
```

## 2. Exact response — flagged case, counterfactual found (real, from the live API just now)
```json
{
  "request_id": "req_cf_test_1",
  "transaction_id": "txn_cf_test_1",
  "status": "ok",
  "is_fraud": true,
  "risk_score": 99,
  "score_type": "relative_risk_0_100_not_calibrated_probability",
  "risk_status": "high",
  "model_factors": [
    "Transaction amount is unusually high",
    "Transaction location is far from customer's home",
    "Transaction occurred at an unusual hour"
  ],
  "model_version": "histgb-candidate-day3-v1",
  "counterfactual": {
    "found": true,
    "changed_feature": "amt",
    "changed_feature_label": "transaction amount",
    "original_value": 890.0,
    "suggested_value": 623.0,
    "new_risk_score": 67,
    "new_risk_status": "medium",
    "reason": "If the transaction amount had been 623.00 instead of 890.00, the risk score would have been 67 instead of the original score."
  }
}
```
Suggested Person C UI sentence (static, per the roadmap): *"If the transaction amount had been ৳623 instead of ৳890,
the risk score would have been 67 instead of 99."* — note `changed_feature_label` is already a human-readable string
("transaction amount", "time of day", "distance from home") for building this sentence without a lookup table.

## 3. Exact response — `found: false` case (real, from the live API just now, normal transaction)
```json
{
  "request_id": "req_cf_test_2",
  "transaction_id": "txn_cf_test_2",
  "status": "ok",
  "is_fraud": false,
  "risk_score": 0,
  "score_type": "relative_risk_0_100_not_calibrated_probability",
  "risk_status": "low",
  "model_factors": [],
  "model_version": "histgb-candidate-day3-v1",
  "counterfactual": {
    "found": false,
    "changed_feature": null,
    "changed_feature_label": null,
    "original_value": null,
    "suggested_value": null,
    "new_risk_score": null,
    "new_risk_status": null,
    "reason": null
  }
}
```
Person C: per the roadmap, render **nothing** for this case — no empty box.

## 4. Final typed schema (Pydantic, `schemas.py`)
```python
class Counterfactual(BaseModel):
    found: bool
    changed_feature: Optional[str]          # "amt" | "trans_hour" | "distance_from_home_km" | null
    changed_feature_label: Optional[str]    # "transaction amount" | "time of day" | "distance from home" | null
    original_value: Optional[Union[float, int]]
    suggested_value: Optional[Union[float, int]]
    new_risk_score: Optional[int]           # 0-100, same semantics as the top-level risk_score
    new_risk_status: Optional[str]          # "low" | "medium" | "high"
    reason: Optional[str]
```
Person C's TypeScript type should match this shape exactly (per the roadmap's Task 3) — `changed_feature` is one of
exactly 3 string literals or `null`, not a free-form string, if you want to type it more strictly than `string | null`.

## 5. Feature-name / value-format limitations
- `changed_feature` is always one of the model's **internal** feature names (`amt`, `trans_hour`,
  `distance_from_home_km`) — not the raw API field names (`transaction_amount`, etc.). Use
  `changed_feature_label` for anything user-facing; don't expose `changed_feature` directly in UI copy.
- `original_value`/`suggested_value` are plain numbers with no unit suffix — `amt` is in the same currency unit the
  request used, `trans_hour` is 0-23, `distance_from_home_km` is kilometers. No explicit unit field is returned.
- `trans_hour` suggestions can be any hour 0-23 (not just "nearby" hours) — the search doesn't constrain candidate
  hours to be close to the original, so a suggested hour could look like a large jump (e.g. 3am → 2pm). This is
  accurate to how the search works, not a bug, but worth knowing for how you phrase the sentence.

## 6. Actual test results
- 20/20 new tests passing (Tests A–G exactly as specified), 71/71 total (51 pre-existing + 20 new) — zero
  regressions.
- Real-data validation on 10 real flagged test-set transactions (not synthetic): **10/10 found a flip**, always on
  `amt` first (search order tries `amt` before `trans_hour`/`distance_from_home_km` — this result is a property of
  the search order and this particular sample, not a claim that amount is always the answer; see the roadmap's own
  warning and the honest limitation below).
- Average search latency: **15.4ms**, max **31.4ms** across the 10 real cases — negligible addition to `/predict`'s
  response time.
- **Confirmed non-monotonic model behavior on a real transaction** (test case `real_flagged_1694`, a $4.93
  transaction): reducing `amt` by 10% did nothing, by 20% flipped it, by 30% flipped it *back* to flagged, by 50%
  still flagged, by 70% flipped again, by 90%+ flipped back to flagged again. This is a genuine property of the
  trained gradient-boosted model on small-amount transactions, not a search bug (independently re-verified by
  hand-computing every step). **Practical implication: for very small-amount transactions, a found counterfactual
  can be fragile** — a slightly different suggested value might not reproduce the same flip. Worth knowing if this
  case ever comes up in a demo.

Full validation data: `reports/counterfactual_real_data_validation.json`.
