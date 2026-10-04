# model/ — Fraud/Risk Detection Pipeline (Day 2, Person B)

Everything in this folder has been **actually run** against the dataset downloaded from Kaggle
(`fraudTrain.csv` 1,296,675 rows + `fraudTest.csv` 555,719 rows). No numbers here are
invented — see `../reports/` for the real, executed output logs.

**Data disclosure:** this dataset ("Credit Card Transactions Fraud Detection Dataset",
Kaggle, CC0 Public Domain license — verified in `../docs/DATASET_NOTES.md`) is **simulated
data**, generated with the Sparkov data generation tool, not real bank/cardholder records.
Model performance numbers in this repo reflect behavior on this simulated data and must not
be presented or read as real-world fraud-detection performance. (Day 7 review flagged the
previous wording above — "the real Kaggle dataset" — as ambiguous enough to misread as a
claim about real transaction data; reworded here to remove that ambiguity.)

## ⚠️ Environment setup — READ FIRST (exact versions required)

The model artifact `artifacts/fraud_model_candidate_day3_histgb.joblib` was saved with
**scikit-learn 1.8.0** and only loads under that exact version. Under scikit-learn 1.9.x it fails with
`ModuleNotFoundError: No module named '_loss'` (reproduced and confirmed).

Use a **fresh, separate virtual environment** for the node (do NOT reuse the backend's `.venv`):

```powershell
cd model
py -3.13 -m venv .venv-node            # Python 3.12 or 3.13 (wheels exist for both)
.\.venv-node\Scripts\Activate.ps1
python -m pip install -r requirements.txt     # exact pinned runtime versions
python -c "import sklearn; print(sklearn.__version__)"   # MUST print 1.8.0
python api.py
```

`requirements.txt` = runtime only (pinned). `requirements-dev.txt` = adds pytest + imbalanced-learn
(only needed to run tests / training scripts). Verified environment: Python 3.12.3, scikit-learn 1.8.0,
numpy 2.4.4, scipy 1.17.1, joblib 1.5.3, pandas 3.0.2.

## Folder contents

```
model/
├── config.py            # paths, column names, constants — edit this, not hardcoded values elsewhere
├── data_inspection.py    # Step 2 — data quality report (missing values, duplicates, label distribution)
├── preprocessing.py       # Step 3 — feature engineering + sklearn preprocessing pipeline
├── train.py               # Step 4+5 — chronological split + DummyClassifier/LogReg/RandomForest training
├── evaluate.py            # Step 6+7 — threshold selection on validation, ONE final test evaluation
├── predict.py              # Step 8 — prediction logic (separate from API routing)
├── schemas.py               # Step 8 — Pydantic request/response models
├── api.py                    # Step 8 — FastAPI POST /predict endpoint
├── tests/
│   └── test_pipeline.py        # Step 9 — 21 tests, all passing (see below)
├── artifacts/
│   └── fraud_model_pipeline.joblib   # saved, trained pipeline (preprocessor + RandomForest together)
├── requirements.txt
└── README.md              # this file
```

`data/fraudTrain.csv` and `data/fraudTest.csv` are expected but **not included** here (too
large to ship in a repo/zip) — place your own copies there, or edit `config.py`'s `DATA_DIR`.

## How to run, in order

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Put fraudTrain.csv and fraudTest.csv inside model/data/

# 3. Data quality report (Step 2)
python data_inspection.py

# 4. Train baseline models — trains DummyClassifier, LogisticRegression, RandomForest,
#    picks the best by PR-AUC on a chronological validation split, saves it (Step 4+5)
python train.py
# Note: RandomForest takes ~3 minutes on the full 1.1M-row training set.

# 5. Pick a decision threshold on validation, then evaluate ONCE on the held-out test set (Step 6+7)
python evaluate.py

# 6. Run the test suite (Step 9)
pytest tests/ -v

# 7. Start the prediction API (Step 8)
uvicorn api:app --reload --port 8000
# Then in another terminal:
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{
  "request_id": "req_1", "transaction_id": "txn_1",
  "amt": 128.50, "category": "grocery_pos", "trans_hour": 14, "distance_from_home_km": 3.2
}'
```

**Windows/VS Code terminal note:** the commands above work as-is in PowerShell or VS Code's
integrated terminal once Python and pip are installed; no changes needed except using
`python` instead of `python3` if that's how Python is aliased on your machine.

## Real results (from actually running this pipeline)

### Baseline comparison (validation set, chronological split of fraudTrain.csv)
| Model | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| DummyClassifier (floor) | 0.000 | 0.000 | 0.000 | 0.006 | 0.500 |
| Logistic Regression | 0.035 | 0.760 | 0.068 | 0.167 | 0.913 |
| **Random Forest (chosen)** | 0.345 | 0.955 | 0.507 | **0.881** | 0.997 |

### Final test evaluation (fraudTest.csv, touched exactly once, threshold=0.4629 selected on validation only)
- Precision: **0.221** | Recall: **0.952** | F1: **0.358**
- PR-AUC: **0.835** | ROC-AUC: **0.995**
- Confusion matrix: TN=546,371 FP=7,203 FN=104 TP=2,041
- **104 of 2,145 real fraud cases were missed. 7,203 legitimate transactions were wrongly flagged.**

**Honest interpretation:** this baseline catches ~95% of fraud, at the cost of a high false-positive
rate (about 1.3% of all legitimate transactions get flagged). That trade-off was chosen deliberately
(recall prioritized over precision, since missed fraud is usually more costly than a false alarm) —
but it is a **provisional MVP choice**, not a validated business decision. The team should discuss
whether this trade-off is acceptable before treating this as final (see `../docs/RISK_SCORE.md` §7).

### Test suite
**21/21 tests passed** (`pytest tests/ -v`, run on 2026-09-25). Covers dataset schema, feature
engineering correctness, no-leakage checks, preprocessing pipeline robustness (including unseen
categories at inference), saved-model load/predict consistency, prediction determinism, and API
input validation (valid request, negative amount, missing field, invalid hour, empty category).

## Integration guide — for Person A (Backend)
- The `/predict` endpoint and `schemas.py` field names match `../contracts/model_io_example.json`
  from Day 1, but are still a **draft** — please review and confirm field names before wiring the
  orchestrator to call this permanently.
- Error responses: `503` with `error_code: MODEL_UNAVAILABLE` if the model file is missing;
  `500` with `error_code: PREDICTION_ERROR` for unexpected errors; `422` (FastAPI's default) for
  invalid input, with Pydantic's own detailed validation messages.
- The model is loaded once at API startup (not per-request) for performance — see `api.py`'s
  `startup` event.
- `GET /health` is available for basic liveness checks.

## Integration guide — for Person C (Frontend)
- Required fields the UI **must** collect: `amt`, `category`, `trans_hour` (or a raw timestamp the
  backend can convert to an hour).
- Optional fields (only send if actually collected): `distance_from_home_km` (needs location data —
  still an open question, see `../docs/TEAM_COORDINATION_CHECKLIST.md`), `age_years`, `city_pop`,
  `gender`.
- Response includes `risk_score` (0-100, **not a probability** — see `../docs/RISK_SCORE.md`),
  `risk_category` (low/medium/high, provisional cutoffs), and `model_factors` (a short, human-
  readable list of reasons — currently simple rule-based hints, not a formal SHAP explanation).

## Day 2 completion checklist

- [x] Dataset loaded and inspected for real (Step 1–2) — see `../reports/DAY2_STEP1_DATASET_AUDIT.md`
- [x] No missing values, no duplicate rows, no duplicate transaction IDs found
- [x] Target label (`is_fraud`) verified to exist and be binary — not assumed
- [x] Feature contract implemented in code (`preprocessing.py`), matching `../docs/FEATURE_CONTRACT.md`
- [x] Chronological train/validation split used (not random) — respects time order, documented cutoff date
- [x] fraudTest.csv held out untouched until Step 7 (verified: only loaded once, inside `evaluate.py`)
- [x] Three baseline models trained and compared honestly, including a Dummy floor
- [x] Model selected by PR-AUC (appropriate for severe class imbalance), not raw accuracy
- [x] Decision threshold selected on validation only, then applied once to test
- [x] Real final test metrics reported, including false negative / false positive counts explained in context
- [x] FastAPI endpoint built, started, and tested live with curl (valid, fraud-flagged, and 2 invalid-input cases)
- [x] 21 automated tests written and run — all passing
- [x] Model + preprocessing pipeline saved together as one artifact (`artifacts/fraud_model_pipeline.joblib`)

### Remaining open issues (not resolved today, need follow-up)
1. **Risk category cutoffs (low/medium/high) are still provisional placeholders** (0–39/40–69/70–100), not derived from the validation score distribution — should be revisited if time allows.
2. **`min_precision=0.30` in the threshold-selection logic is a placeholder**, not a team-approved business decision — the precision/recall trade-off should be discussed with the team (see `../docs/RISK_SCORE.md` §7).
3. **`model_factors` explanations are simple rule-based hints**, not a real feature-importance/SHAP-based explanation — acceptable for an MVP demo, but should be disclosed as such, not oversold.
4. Feature contract fields `distance_from_home_km`, `age_years`, `city_pop`, `gender` are only usable if Person C's frontend actually collects the underlying data — **still unconfirmed**, per `../docs/TEAM_COORDINATION_CHECKLIST.md`.
5. No model calibration has been performed — `risk_score` must continue to be described as relative, not a calibrated probability.

---

## Day 3 update — new candidate model now being served

Day 3 trained and compared 6 model configurations (Logistic Regression ×3 variants, Random Forest
×2 variants, HistGradientBoosting) on the exact same chronological split as Day 2, then selected
**HistGradientBoostingClassifier** as the new candidate — it had the highest PR-AUC (0.918) of
everything tried and trains in ~16 seconds (vs. Random Forest's ~3 minutes).

**`predict.py` and `api.py` now serve this Day 3 candidate** (`artifacts/fraud_model_candidate_day3_histgb.joblib`,
`model_version = "histgb-candidate-day3-v1"`, threshold = 0.80). Day 2's Random Forest artifact
(`artifacts/fraud_model_pipeline.joblib`) is left untouched on disk for comparison/rollback.

### Day 3 real final test results (fraudTest.csv, touched once)
| Metric | Day 2 (RandomForest) | Day 3 (HistGradientBoosting) |
|---|---|---|
| Precision | 0.221 | **0.413** |
| Recall | 0.952 | 0.928 |
| F1 | 0.358 | **0.572** |
| PR-AUC | 0.835 | 0.879 |
| False positives | 7,203 | **2,827** |
| False negatives | 104 | 154 |

Full analysis (class imbalance effects, threshold sweep, overfitting/robustness checks) in
`../reports/DAY3_MODEL_COMPARISON_AND_ANALYSIS.md`. Person A integration handoff in
`../docs/DAY3_PERSON_A_HANDOFF.md`.

### New/changed files (Day 3)
```
model/
├── train_candidates.py            # Step 4+5 — multi-model comparison (reference script; some
│                                     runs were split into separate ad-hoc scripts due to a 300s
│                                     execution limit on Random Forest — see reports/day3_results.jsonl
│                                     for the actual per-model results that were produced)
├── finalize_candidate.py           # Step 7+8+9 — threshold sweep, overfitting check, save candidate
├── evaluate_candidate.py           # Step 10 — one-time final test evaluation of the candidate
├── tests/test_day3_candidate.py    # Step 12 — 12 additional tests (all passing)
├── artifacts/
│   └── fraud_model_candidate_day3_histgb.joblib   # NEW — currently served
├── reports/
│   ├── day3_results.jsonl                   # raw per-model comparison results
│   ├── day3_candidate_metadata.json          # chosen candidate's full config/metadata
│   └── day3_final_test_evaluation.json       # final test metrics
```

### Day 3 completion checklist
- [x] Day 2 artifacts audited and re-verified (split determinism, row overlap = 0)
- [x] 6 candidate model configurations trained and compared fairly on the same validation split
- [x] Class imbalance analysis: class_weight (None vs balanced) and resampling (train-only) compared, with honest reporting that class weighting does NOT universally help (Random Forest case)
- [x] Model selected using PR-AUC + threshold-sweep evidence, not accuracy
- [x] Threshold analysis: full sweep from 0.10 to 0.90, plain-language trade-off explained, threshold selected on validation only
- [x] Overfitting check: train vs. validation PR-AUC gap small (0.025); permutation importance sanity-checked, no suspicious single-feature domination
- [x] Final candidate saved separately from Day 2's baseline (no overwrite), save/load consistency verified
- [x] Held-out test set evaluated exactly once, after threshold was already locked in
- [x] `predict.py`/`api.py` updated to serve the new candidate; live API re-tested with curl (valid request + unknown category edge case)
- [x] 12 new tests written and passing (33/33 total across both test files)
- [x] Person A handoff document written, with confirmed vs. proposed fields clearly separated

### Remaining Day 3 open issues
1. Field naming conflict between this project's `predicted_class`/`risk_category` and the Day 3 prompt's proposed `is_fraud`/`risk_status` — needs Person A's decision (see handoff doc §4).
2. Decision threshold (0.80) is Person B's proposed default — needs team business-priority confirmation.
3. Only one chronological train/validation split was checked for robustness — true stability across different time windows is not fully verified.
4. `distance_from_home_km` had surprisingly low permutation importance (0.001) despite being a Day 1-prioritized feature — worth investigating further (possible redundancy with other features) but not blocking for the MVP.
5. All Day 1 open items (frontend field availability, gender ethics discussion) remain unresolved and carry forward.

---

## Day 4 update — standalone Fraud/Risk Node API, with frontend-facing contract

Day 4's job was to turn Day 3's working-but-internal-facing API into a proper standalone node
that speaks the frontend/backend's actual field names, not the model's internal ones. **No new
model was trained** — Day 3's audited HistGradientBoosting candidate is reused as-is (re-verified
directly from the saved artifact, not assumed — see `reports/DAY4_STEP1_AUDIT.md`).

### 1. Project overview
A standalone Fraud/Risk Node: loads the trained model once at startup, accepts a transaction
request in the frontend's raw field names, translates them internally, predicts, and returns a
structured JSON response. Independent of the frontend and backend — talks to them only via HTTP.

### 2. Node architecture
```
Request (raw frontend fields)
   -> schemas.py (Pydantic validation)
   -> predict.py (raw fields -> model features -> inference)
   -> risk_engine.py (score -> is_fraud / risk_score / risk_status / model_factors)
   -> schemas.py (response, public field names)
   -> Response
```

### 3. Folder structure (current, adapted from Day 4's suggested layout rather than rebuilt from scratch)
```
model/
├── config.py            # paths, feature lists, constants
├── risk_engine.py        # NEW Day 4 — classification threshold + risk_status logic, isolated
├── predict.py             # UPDATED Day 4 — raw-field-to-feature mapping + inference
├── schemas.py              # UPDATED Day 4 — frontend-facing request/response field names
├── api.py                   # UPDATED Day 4 — logging added, error messages updated
├── preprocessing.py          # unchanged since Day 2/3
├── train.py, evaluate.py, train_candidates.py, finalize_candidate.py, evaluate_candidate.py  # training/eval scripts, unchanged
├── tests/
│   ├── test_pipeline.py        # UPDATED Day 4 — new field names
│   ├── test_day3_candidate.py  # UPDATED Day 4 — new field names
│   └── test_risk_engine.py     # NEW Day 4
├── artifacts/            # both Day 2 and Day 3 models still present, untouched
├── reports/
└── requirements.txt, README.md
```
No `.env`-based configuration was added (Day 4's suggested `.env.example`) — `config.py`'s
hardcoded values already worked and adding environment variables wasn't necessary to make the
node function; flagged as a possible future improvement, not done to avoid unnecessary complexity.

### 4-5. Environment setup and dependencies
```bash
cd model/
pip install -r requirements.txt   # includes imbalanced-learn (Day 3) — needed only for
                                    # train_candidates.py, not for running the API itself
```

### 6. Model artifact requirements
`artifacts/fraud_model_candidate_day3_histgb.joblib` must exist (already present in this
repo/zip). If missing, the API starts anyway (per Step 3's "handle missing artifacts safely"
requirement) but `/predict` returns `503 MODEL_UNAVAILABLE` until `finalize_candidate.py` is re-run.

### 7. Environment variables
None currently required — see folder-structure note above.

### 8. How to start the API
```bash
uvicorn api:app --reload --port 8000
```

### 9. API endpoint documentation
`POST /predict` — see `docs/DAY4_PERSON_A_HANDOFF.md` for the full request/response schema,
field-by-field mapping, and error codes. `GET /health` — liveness check.

### 10. Example request and response
See `docs/DAY4_PERSON_A_HANDOFF.md` §3-5 — real examples captured from this session's live curl tests.

### 11. How to run tests
```bash
pytest tests/ -v
```
**46/46 tests passing** as of this session (real, executed — see below for the breakdown).

### 12. Known limitations
- `transaction_type` and `location` are accepted by the API but have **zero effect** on the
  prediction — verified with a passing test (`test_predict_ignores_transaction_type_and_location`)
  that two otherwise-identical requests differing only in these fields produce identical results.
  This is intentional per the Day 4 team decision, not a bug, but must not be misrepresented to
  Person A/C as "the node uses transaction type."
- `distance_from_home`'s unit (assumed kilometers) is not yet confirmed by the team.
- No authentication, rate limiting, or HTTP timeout is configured on the node side yet.
- Threshold (0.80) and risk_status cutoffs remain provisional, not team-approved.
- Only one chronological validation split was used to select the underlying model (carried
  forward from Day 3) — true long-term temporal stability is not fully verified.

### 13. Integration instructions for Person A
Full detail in `docs/DAY4_PERSON_A_HANDOFF.md`, including 6 explicitly unresolved questions that
need Person A's/Person C's input before this contract can be called final.

### 14. Model version and threshold configuration
- `model_version`: `histgb-candidate-day3-v1`
- `DECISION_THRESHOLD`: `0.80` — now isolated in `risk_engine.py` as a named constant for easy
  reconfiguration.
- `risk_status` cutoffs: `low` < 40, `medium` 40-69, `high` ≥ 70 — also isolated constants in `risk_engine.py`.

### Day 4 test suite results (real, executed)
- `tests/test_pipeline.py` (updated) + `tests/test_day3_candidate.py` (updated) + `tests/test_risk_engine.py` (new) = **46 tests, 46 passing**.
- Live API re-tested with curl: health check, valid request (new field names), request with
  `transaction_type`/`location` present (confirmed inert), minimal request (only required fields),
  negative amount (422), missing required field (422), malformed datetime (422) — **7/7 real,
  correct responses**.

### Day 4 completion checklist
- [x] Day 3 artifacts re-audited and re-verified (model, threshold, features — not assumed)
- [x] Real mismatch found and documented between frontend's proposed fields and the model's actual trained features (`transaction_type`, `location`)
- [x] Team decisions recorded (`docs/DAY4_DECISIONS.md`)
- [x] Input contract finalized with raw frontend field names (`docs/DAY4_DATA_CONTRACT.md`)
- [x] Output contract updated to `is_fraud`/`risk_score`/`risk_status`/`model_factors`/`model_version`
- [x] `risk_engine.py` split out as its own module (Day 4's suggested modular structure)
- [x] Model loads once at startup, not per-request (unchanged from Day 3, re-verified)
- [x] Input validation via Pydantic (extended for new fields, unusable fields accepted-but-inert)
- [x] Logging added (request_id/transaction_id/is_fraud/risk_score only — no PII/amounts logged)
- [x] Node-level error codes kept distinct from the backend's proposed codes, per instruction
- [x] 46/46 automated tests passing; live API re-tested end-to-end with curl (7/7 cases correct)
- [x] Person A integration handoff written, with confirmed vs. pending items clearly separated

### Day 4 remaining open issues (unresolved, not silently decided)
See `docs/DAY4_PERSON_A_HANDOFF.md` §11 for the full list — six concrete questions for Person A/C,
plus the carried-forward Day 1 items (frontend field availability, gender ethics discussion) that
are now four days old and still unanswered.
