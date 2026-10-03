# DAY 06 STATUS

Every claim below is labeled **VERIFIED** (I ran it, this session), **NOT VERIFIED** (not tested, requires
something I don't have access to), or **ASSUMED** (inferred from code reading but not executed). Raw evidence:
`reports/day6_phase2_baseline_results.json`, `reports/day6_phase4_real_data_validation.json`, and this file's
inline output.

## 1. Current System State
- ML/Risk Node: FastAPI, `POST /predict` + `GET /health`, runs on `127.0.0.1:8001` (env-configurable). **VERIFIED
  running and responding correctly** throughout this session.
- Model: `HistGradientBoostingClassifier`, artifact `artifacts/fraud_model_candidate_day3_histgb.joblib`
  (465,690 bytes). **VERIFIED loads successfully**, `predict_proba` confirmed present.
- Counterfactual "What Would Fix This?" feature: present, wired into `/predict`'s response as an additive
  `counterfactual` field. **VERIFIED present and returning real (non-fabricated) values.**
- Full automated test suite: **71/71 passing** (51 pre-existing + 20 counterfactual-specific), re-run at the end
  of this session after all manual testing — **VERIFIED**.

## 2. What I Inspected
Read fresh (not from memory): `predict.py`, `risk_engine.py`, `counterfactual.py`, `schemas.py`, `api.py`,
`preprocessing.py`, `config.py`, all 4 existing test files. Full findings in
`reports/DAY6_PHASE1_IMPLEMENTATION_MAP.md`. Confirmed the exact feature list
(`amt, distance_from_home_km, trans_hour, age_years, city_pop, category, gender`), the exact classification logic
(`risk_engine.classify()`), and the exact integration point (`predict.py` calls `build_counterfactual()` right
after `build_model_factors()`, adds one key to the response dict, no `api.py` changes needed). **VERIFIED** via
direct file reads, not assumed from the roadmap documents.

## 3. Bugs Found
**None found that required a code change.** One correctness *question* was investigated and resolved as **not a
bug**: a real test case (`day6_real_1215`) showed `counterfactual.found: true` with `new_risk_status: "high"`
still shown. Traced directly: `is_fraud` uses the 0.80 raw-score threshold while `risk_status` uses a separate
0–100 display-scale cutoff (`>=70` → "high") — these are two independently-computed values by design (confirmed
in `risk_engine.py`'s own docstring and re-verified by hand-computing the exact case). **VERIFIED as intentional
design, not a bug** — flagged as a UX communication point for Person C (§13), not a code fix.

One pre-existing robustness gap noted, **not a confirmed bug**: `MODEL_VERSION` in `predict.py` is a hardcoded
string, not derived from the loaded artifact file at runtime, so a silent artifact swap wouldn't be self-detected
by the string alone. This is the same *class* of issue that caused the real Day 5 incident (wrong service on
port 8001), though at a different layer (file content vs. network routing). **ASSUMED risk, not verified as an
active problem** — no evidence the current artifact is wrong, just noting the structural gap for awareness.

## 4. Bugs Fixed
**None.** No confirmed bugs were found this session that required a fix, per the instruction not to make
unnecessary changes. All 14 counterfactual correctness checks (Phase 3) and all 8 edge cases (Phase 5) passed
without any code modification needed.

## 5. Counterfactual Validation
All 14 Phase 3 checklist items **VERIFIED** with live execution this session (not reused from the earlier
feature-build session):
1–2. Correct feature representation + same trained pipeline — PASS
3. Original feature dict not mutated — PASS (deep-copy comparison before/after)
4. Only one feature changed per candidate — PASS (code-confirmed: single-key assignment per candidate)
5. Valid feature ranges respected — PASS (only reductions toward zero for amt/distance, hour always 0–23)
6–7. No fabricated results; every candidate re-runs real `predict_proba()` — PASS (fresh re-prediction matched
   the reported `new_risk_score` exactly: 67 == 67)
8. Correctly identifies True→False flips — PASS
9–10. `new_risk_score`/`new_risk_status` from the real `classify()` function — PASS
11. `found=false` handled safely for non-flagged input — PASS
12. Missing optional feature (`distance_from_home` omitted) via the real `predict_one()` — PASS, no crash
13. Invalid value (`distance_from_home_km=-999`) at the function level — PASS, no crash, no corruption
14. Original prediction stable/unchanged across repeated identical calls — PASS

## 6. Real Test Results
**10 fresh real flagged transactions** (rows 150,001–300,000 of `fraudTest.csv`, a different slice than used in
the earlier feature-build session, to avoid re-testing the same cases): **10/10 found a counterfactual, all via
`amt`.** Zero `found:false` in this batch — reported honestly, not cherry-picked (a separate `found:false` case was
exercised via Phase 5's synthetic edge case #7 instead, since this particular real sample happened not to produce
one). Full table: `reports/day6_phase4_real_data_validation.json`. No suspicious results (no case where
`new_risk_score` was still ≥ the 80-point threshold despite `found:true`).

Phase 2 baseline (Cases A, B, D, E via direct `predict_one()`; Case C via live HTTP for the validation-error path):
all 5 **VERIFIED PASS** — see `reports/day6_phase2_baseline_results.json` and the inline curl output in this
session. Case C (negative amount) correctly returns `422`, not a 500 or a silently-accepted request.

## 7. API / Schema Verification
**VERIFIED**: existing fields (`is_fraud`, `risk_score`, `risk_status`, `model_factors`, `model_version`,
`request_id`, `transaction_id`, `status`, `score_type`) all present and correctly typed in every live response
captured this session. `counterfactual` is additive — present in every response, `found:false` with all other
sub-fields `null` when not applicable (schema-validated via Pydantic, re-confirmed in the existing
`test_counterfactual.py::TestE_SchemaCompatibility`, re-run this session). No field was renamed or removed.
JSON serialization confirmed working via real `curl` calls, not just the Python-level dict.

## 8. Performance Findings
**VERIFIED**, measured this session (20-iteration average each):
- Bare model `predict_proba()` only: **4.1ms**
- Full `/predict` logic on a **flagged** transaction (counterfactual search runs): **20.0ms** (+15.9ms for the
  search)
- Full `/predict` logic on a **normal** transaction (no search needed, early return): **5.1ms** (+0.9ms overhead)

No excessive repeated preprocessing found — `counterfactual.py` reuses the exact same DataFrame construction as
the real prediction, no redundant model reload (confirmed singleton `get_pipeline()` pattern), no network calls
introduced. The +15.9ms on flagged transactions is well within a reasonable response-time budget for an
interactive demo. **No optimization made — none was needed** (no verified bottleneck), per the instruction not to
optimize without a confirmed problem.

## 9. Integration Status
- ML Node ↔ its own model: **VERIFIED working**, extensively, this session.
- ML Node ↔ Backend (`/analyze`): **NOT VERIFIED this session** — no live backend process available in this
  environment to call. This was separately verified in the Day 5 report (with real evidence at the time); not
  re-verified here since Day 5's backend isn't running in this session. **Reporting this honestly as NOT VERIFIED
  for Day 6**, not assumed still-working from Day 5's evidence.
- ML Node ↔ Frontend: **NOT VERIFIED this session** — same reason, no live frontend available here.
- Full Frontend → Backend → ML Node chain: **NOT AVAILABLE for testing in this session.** Per the instruction to
  report this clearly rather than pretend it passed: **this was not tested in Day 6** and should not be assumed
  still-correct just because the `counterfactual` field is additive — Person A and Person C need to actually run
  it against the updated node (with the new field) before this can be called verified for Day 6.

## 10. Remaining Problems
None confirmed as active bugs. Two structural notes carried forward, not blocking:
1. `MODEL_VERSION` hardcoded, not self-verifying against the loaded artifact (§3).
2. `counterfactual` is a required (not Optional) field — any cached/stored response fixtures on the frontend side
   that predate this feature will fail schema validation until updated (already flagged to Person C previously;
   re-confirmed still true, not yet independently verified as fixed on her side).

## 11. Unverified Items
- Full E2E (Frontend → Backend → ML Node) with the counterfactual field present — **NOT VERIFIED**, no live
  backend/frontend available this session (§9).
- Day 5's two carried-forward exceptions (real 504 timeout test, full OpenAI-fallback success demo) — **NOT
  VERIFIED**, out of this Day 6 ML-node scope, unchanged since Day 5.
- Whether Person C's frontend has been updated to handle the new required `counterfactual` field — **NOT
  VERIFIED**, needs her confirmation.
- Behavior under concurrent/parallel load — **NOT VERIFIED**, not load-tested this session.

## 12. Handoff for Person A
- `/predict` response shape is **unchanged except for one new additive field**: `counterfactual` (always present,
  `found:false` with nulls when not applicable). No change needed to how `/analyze` passes through existing
  fields — it should already forward `counterfactual` unchanged if it passes through the full response body
  without allowlisting specific fields; **please confirm this explicitly rather than assume it**, since this
  wasn't re-verified against your live backend this session.
- Error behavior **unchanged**: `422` for input validation (FastAPI/Pydantic default), `503 MODEL_UNAVAILABLE` if
  the artifact fails to load (re-verified this session by actually removing the artifact file and confirming the
  503 response, then restoring it), `500 PREDICTION_ERROR` for unexpected internal errors.
- No backend-side contract change is required for this feature per the original roadmap — this is confirmed
  consistent with what was implemented.

## 13. Handoff for Person C
- New field in every `/predict` (and therefore `/analyze`, assuming pass-through) response: `counterfactual`
  object — see `docs/COUNTERFACTUAL_INTEGRATION_CONTRACT.md` for the full shape and real examples.
- `found: true` behavior: show the static sentence using `changed_feature_label` + `original_value` +
  `suggested_value` + `new_risk_score`, per the roadmap. `found: false`: render nothing.
- **New observation from this session's testing**: a `found:true` result can still show `new_risk_status: "high"`
  (not necessarily dropping to "medium"/"low") — because `is_fraud` and `risk_status` use independent thresholds.
  Worth considering in the UI copy so it doesn't read as contradictory (e.g. avoid implying the suggested change
  makes it "safe," since it may still display as high risk by the status label even though the fraud flag itself
  flipped).
- **Action needed, not yet confirmed done**: any cached/mock example responses used for demo/testing need a
  `counterfactual` key added, or they'll fail schema validation once strict typing is enforced on your side.
- Real data confirmed: all `counterfactual` values in every test this session came from actual
  `pipeline.predict_proba()` calls on the real artifact — never fabricated or hardcoded.

## 14. Final Day 06 Checklist
| Item | Status |
|---|---|
| Existing ML prediction still works | ✅ VERIFIED |
| Day 05 integration issues fixed or documented | N/A this session — no live backend/frontend to test against (§9); Day 5's own report already documents its 2 exceptions |
| Counterfactual does not break normal prediction | ✅ VERIFIED (Phase 2, 3, all existing tests still pass) |
| Counterfactual works on verified real flagged cases | ✅ VERIFIED (10/10 real cases, fresh sample) |
| Counterfactual returns found=false cleanly when no flip found | ✅ VERIFIED (Phase 5, edge case #7) |
| Non-flagged transactions handled correctly | ✅ VERIFIED |
| Missing features do not crash the node | ✅ VERIFIED (Phase 5 #2, #3; Phase 9) |
| Feature mapping verified | ✅ VERIFIED (Phase 1, Phase 7 trace) |
| API schema still compatible | ✅ VERIFIED |
| Risk score remains 0–100 | ✅ VERIFIED, never changed |
| No fake model outputs used | ✅ VERIFIED — every number in this report came from a real `predict_proba()` call |
| No unnecessary major changes introduced | ✅ VERIFIED — zero code changes made this session (no bugs required fixing) |
| Performance checked | ✅ VERIFIED (§8) |
| Error handling checked | ✅ VERIFIED (§Phase 9: malformed JSON, invalid types, missing fields, model-unavailable) |
| Test matrix recorded | ✅ see `reports/DAY6_TEST_MATRIX.md` |
| Person A receives confirmed ML/API behavior | ✅ §12, with an explicit ask to re-verify pass-through himself |
| Person C receives confirmed frontend data behavior | ✅ §13, with an explicit action item flagged |
| Remaining unknowns explicitly documented | ✅ §11 |
