# Fintech Risk Intelligence API — API Contract

## Status

This document defines the locked Day 1 API contract for the
Fintech Risk Intelligence system.

The API field names, service responsibilities, MVP scope,
and integration architecture have been confirmed by the
Backend, ML/Risk Node, and Frontend sides.

Model-specific details that still require later ML artifact
verification are explicitly marked as provisional/TBD.

---

# 1. API Information

**API Name:** Fintech Risk Intelligence API

**Version:** 1.0.0

**Framework:** FastAPI

**Development URL:**

http://127.0.0.1:8000

**Swagger Documentation:**

http://127.0.0.1:8000/docs

---

# 2. Endpoint Ownership

| Endpoint / Component | Purpose | Owner |
|---|---|---|
| GET / | Basic API availability | Person A / Backend |
| GET /health | Backend health check | Person A / Backend |
| POST /analyze | Transaction risk analysis | Person A / Backend |
| POST /predict | Fraud/risk prediction | Person B / ML/Risk Node |
| Frontend integration | Display analysis result | Person C / Frontend |

The backend is responsible for:

- Request validation
- Generating a unique request_id
- Calling the ML/Risk Node
- Handling ML Node timeout
- Handling ML Node unavailability
- Returning the agreed structured response

The ML/Risk Node is responsible for:

- Input validation
- Model preprocessing
- Model inference
- Model-level prediction output

The frontend is responsible for:

- Collecting the agreed user-facing fields
- Sending requests to `/analyze`
- Displaying backend-provided results
- Displaying backend-provided risk status
- Displaying the risk score as a 0–100 score
- Displaying model factors without inventing explanations

---

# 3. GET /

Used to verify that the backend API is running.

## Response

**Status:** `200 OK`

```json
{
  "message": "Fintech Risk Intelligence API is running"
}
---
# 7. Risk Score and Risk Status

## Risk Score

The `risk_score` is a numeric value from `0` to `100`.

It represents the transaction's relative risk level.

It must NOT be described as:

- a probability
- a percentage
- a probability of fraud

The frontend must display the score in this format:

```text
72 / 100
Risk Status Mapping

The current implementation maps the 0–100 risk score to a provisional
risk status as follows:

Risk Score	Risk Status
0–39	low
40–69	medium
70–100	high

These risk-status boundaries are provisional and are not validated
business thresholds.

The fraud decision (is_fraud) is a separate classification decision
based on the model's configured decision threshold. Therefore,
risk_status and is_fraud must not be treated as identical fields.

The current implementation uses a decision threshold of 0.80 on the
model's raw score for the is_fraud decision.

The risk score itself is a relative 0–100 display score and is not a
calibrated probability.
It represents the transaction's risk level.

It must NOT be described as:

- a probability
- a percentage
- a probability of fraud

The frontend must display the score in this format:

```text
72 / 100
---

# 14. MVP Scope

The MVP focuses on demonstrating a complete transaction
fraud/risk analysis flow.

## Included in MVP

- Transaction input through the frontend
- Backend `POST /analyze`
- Request validation
- Unique `request_id` generation
- HTTP communication with the Fraud/Risk Node
- Actual ML/Risk Node prediction when available
- Structured fraud prediction
- `risk_score`
- `risk_status`
- `model_factors`
- `model_version`
- Basic error handling
- ML Node timeout handling
- ML Node unavailable handling
- Backend health checking
- Complete end-to-end demo

## Excluded from Initial MVP

The following are not required for the initial MVP:

- Real-time bank integration
- Live transaction monitoring
- Production-grade fraud prevention
- Automatic transaction blocking
- Multiple sector-specific models
- Advanced production infrastructure
- Complex multi-agent coordination beyond the agreed architecture
- Advanced explainability that has not been validated
- Real home-location tracking
- Automatic distance-from-home calculation
- Additional non-essential UI features

---

# 15. Frontend User-Facing Fields

The normal user-facing transaction form requires:

| Field | Required |
|---|---|
| `transaction_amount` | Yes |
| `transaction_type` | Yes |
| `merchant_category` | Yes |
| `transaction_time` | Yes |
| `distance_from_home` | No |
| `location` | No |

The frontend must not add the following fields to the normal
user-facing form:

- `age_years`
- `city_pop`
- `gender`
- `simulate_timeout`
- `simulate_unavailable`

The frontend should use the 14 model-supported
`merchant_category` values defined in this document.

---

# 16. Demo Flow

## Normal Transaction Flow

1. User opens the dashboard.
2. User enters transaction details.
3. Frontend sends the transaction to `POST /analyze`.
4. Backend validates the request.
5. Backend generates a unique `request_id`.
6. Backend forwards the transaction to the Fraud/Risk Node.
7. Fraud/Risk Node validates the input and runs model inference.
8. Fraud/Risk Node returns the structured prediction.
9. Backend returns the structured result to the frontend.
10. Frontend displays:
    - fraud classification
    - risk score
    - risk status
    - model factors
    - model version
    - request ID
11. ARIA may explain the returned result without modifying it.

---

## Error Flow

### Invalid Input

```text
Frontend
   ↓
POST /analyze
   ↓
Backend validation
   ↓
HTTP 400
### ML Node Unavailable

```text
Frontend
   ↓
POST /analyze
   ↓
Backend
   ↓
ML/Risk Node unavailable
   ↓
HTTP 503
Frontend
   ↓
POST /analyze
   ↓
Backend
   ↓
ML/Risk Node timeout
   ↓
HTTP 504
# 17. ARIA Responsibility

ARIA is responsible for understanding user intent, selecting the allowed backend tool, and explaining returned results.

ARIA must not:
- generate fraud/risk predictions
- modify risk_score
- modify risk_status
- invent model_factors
- replace the Fraud/Risk Node as the source of truth

---

# 18. Definition of Done

Day 1 is considered complete when:

- [x] Person B confirms the API/integration baseline.
- [x] Person C confirms the frontend contract.
- [x] API field names and responsibilities are documented.
- [x] MVP cut-line is documented.
- [x] Demo flow is documented.
- [x] Error behavior is documented.
- [x] Shared test cases are documented.
- [x] ARIA responsibilities are documented.
- [ ] Final ML-specific feature/threshold details remain TBD until Day 3 verification.
- [ ] Final model_version is locked after model artifact verification.
- [ ] Final source_mode values are locked later.

---

# 19. Day 1 Audit Status

**Status: READY FOR DAY 1 COMPLETION**

Person B and Person C have confirmed the Day 1 contract baseline.

The following remain intentionally provisional:
- Final ML feature requirements
- Risk-score calculation/thresholds
- Risk-status thresholds
- Model-factor schema
- Final model version
- source_mode

These items will be verified during the appropriate ML/integration phase.


# 20. Counterfactual Response

The `/analyze` response may include an optional `counterfactual` object when a counterfactual explanation is available.

The counterfactual object describes one suggested feature change and the resulting risk assessment.

## Counterfactual Schema

```json
{
  "counterfactual": {
    "found": true,
    "changed_feature": "transaction_amount",
    "changed_feature_label": "Transaction Amount",
    "original_value": 1250.50,
    "suggested_value": 850.00,
    "new_risk_score": 32.0,
    "new_risk_status": "low",
    "reason": "Lowering the transaction amount reduces the predicted risk."
  }
}
```

### Fields

| Field | Description |
|---|---|
| `found` | Indicates whether a counterfactual suggestion is available. |
| `changed_feature` | Machine-readable name of the changed feature. |
| `changed_feature_label` | User-friendly name of the changed feature. |
| `original_value` | Original value of the selected feature. |
| `suggested_value` | Suggested alternative value. |
| `new_risk_score` | Risk score after applying the suggested change. |
| `new_risk_status` | Risk status after applying the suggested change. |
| `reason` | Human-readable explanation of the suggested change. |

The counterfactual object is additive to the existing `/analyze` response and must not remove or rename existing response fields.
