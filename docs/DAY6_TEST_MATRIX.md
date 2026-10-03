# Day 6 — Test Matrix

All tests actually executed this session (live `curl` calls or direct Python execution) — no test marked PASS
without being run. Raw outputs in this session's log and in `reports/day6_phase2_baseline_results.json` /
`reports/day6_phase4_real_data_validation.json`.

| Test ID | Scenario | Input Summary | Expected Result | Actual Result | HTTP Status | Pass/Fail | Notes |
|---|---|---|---|---|---|---|---|
| T1 | Normal transaction | amt=45, grocery_pos | is_fraud=false, low risk | is_fraud=false, risk_score=0, low | 200 | ✅ PASS | counterfactual.found=false (correct, not flagged) |
| T2 | Flagged transaction | amt=890, shopping_net, 03:15, dist=240km | is_fraud=true, high risk | is_fraud=true, risk_score=99, high, 3 factors | 200 | ✅ PASS | counterfactual.found=true, flips via amt |
| T3 | Non-flagged transaction (counterfactual-specific) | amt=45, grocery_pos | counterfactual.found=false, no search | found=false, all sub-fields null | 200 | ✅ PASS | Confirmed no unnecessary search performed |
| T4 | Invalid amount | amt=-50 | Rejected before reaching the model | 422, `transaction_amount` "greater than 0" | 422 | ✅ PASS | Pydantic validation, no model call made |
| T5 | Missing optional field | amt=60, gas_transport, no distance/age/city_pop/gender | 200, missing fields imputed safely | is_fraud=false, risk_score=0 | 200 | ✅ PASS | No crash, trained imputer handles it |
| T6 | Boundary case | amt=500.01 (just above the >500 model_factors rule) | Stable, no crash at the boundary | is_fraud=false, risk_score=1 | 200 | ✅ PASS | No off-by-one error observed |
| T7 | Counterfactual found=true | 10 real flagged test-set transactions | At least some find a flip | 10/10 found, all via `amt` | 200 (each) | ✅ PASS | Reported honestly incl. that none were found=false in this specific sample |
| T8 | Counterfactual found=false | Synthetic: amt=None, distance=None, trans_hour=None, flagged=true | found=false, clean, no crash | found=false | N/A (function-level) | ✅ PASS | Exercised directly since no real-data case produced this in T7's sample |
| T9 | Missing-feature case | amt=None (the search's own first-choice feature missing) | Graceful fallback to next feature | found=true via `trans_hour` instead of `amt` | N/A (function-level) | ✅ PASS | Confirms fallback chain works, not just the happy path |
| T10 | Repeated same input | Same flagged input run 5× | Identical result every time | All 5 runs byte-identical | 200 (each) | ✅ PASS | No randomness, fully deterministic |
| T11 | Backend → ML integration | N/A | N/A | **Not tested this session** | N/A | ⬜ NOT VERIFIED | No live backend process available in this environment — see Final Report §9 |
| T12 | Real frontend → backend → ML flow | N/A | N/A | **Not tested this session** | N/A | ⬜ NOT VERIFIED | No live frontend available in this environment — see Final Report §9 |

## Additional robustness tests run (beyond the required 12)
| Test ID | Scenario | Actual Result | HTTP Status | Pass/Fail |
|---|---|---|---|---|
| T13 | Malformed JSON body | Clean 422 JSON-decode error, no crash | 422 | ✅ PASS |
| T14 | Invalid numeric type (string for amount) | Clean 422 type error | 422 | ✅ PASS |
| T15 | Missing required field (transaction_time) | Clean 422 "field required" | 422 | ✅ PASS |
| T16 | Unexpected field type (string for distance) | Clean 422 type error | 422 | ✅ PASS |
| T17 | Model artifact missing (simulated) | Clean 503 MODEL_UNAVAILABLE, health endpoint still responds | 503 (predict) / 200 (health) | ✅ PASS |
| T18 | Invalid value at counterfactual function level (distance=-999) | No crash, handled internally | N/A (function-level) | ✅ PASS |
| T19 | Extreme-but-valid values (amt=999999, distance=9999) | Stable, found=false (nothing in bounded range flips it) | N/A (function-level) | ✅ PASS |

**Totals: 19/19 executed tests passed. 2 items (T11, T12) explicitly not verified — no live backend/frontend
available in this session, reported honestly rather than assumed.**
