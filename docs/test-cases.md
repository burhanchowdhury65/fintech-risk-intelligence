# Fintech Risk Intelligence — Shared Test Cases

## Purpose

This document defines the shared test cases for the
Fintech Risk Intelligence API.

The test cases cover successful requests, input validation,
Backend-to-ML/Risk Node communication, ML/Risk Node
unavailability, timeout handling, and structured responses.

Model-specific validation requirements remain provisional
until the actual Fraud/Risk Node implementation is verified.

---

# 1. API Availability

## TC-001 — Basic API Availability

**Endpoint:** `GET /`

**Expected Status:** `200 OK`

**Expected Response:**

```json
{
  "message": "Fintech Risk Intelligence API is running"
}

Status: PASS — manually verified.

# 2. Health Check
## TC-002 — Backend Health Check

Endpoint: GET /health

Expected Status: 200 OK

Expected Response:

{
  "status": "ok",
  "service": "fintech-risk-intelligence-api"
}

Status: PASS — manually verified with GET /health.

# 3. Valid Transaction Analysis
## TC-003 — Valid Transaction

Endpoint: POST /analyze

Input:

{
  "transaction_amount": 1250.50,
  "transaction_type": "transfer",
  "merchant_category": "shopping_net",
  "transaction_time": "2026-09-27T14:30:00",
  "distance_from_home": null,
  "location": null
}

Expected Status: 200 OK

Expected Response Fields:

request_id
is_fraud
risk_score
risk_status
model_factors
model_version

Status: PASS — manually verified through Backend → ML Node E2E using the current mock node.

# 4. Invalid Transaction Amount
## TC-004 — Negative Transaction Amount

Endpoint: POST /analyze

Input:

{
  "transaction_amount": -100,
  "transaction_type": "transfer",
  "merchant_category": "shopping_net",
  "transaction_time": "2026-09-27T14:30:00"
}

Expected Status: 400

Expected Error Code:

INVALID_INPUT

Status: PASS — manually verified.

# 5. ML/Risk Node Communication
## TC-005 — Backend-to-ML Node Communication

Flow:

POST /analyze
      ↓
Backend
      ↓
POST /predict
      ↓
ML/Risk Node
      ↓
Structured response
      ↓
Backend

Expected Result:

Backend successfully sends the transaction payload to
the configured ML/Risk Node and consumes the returned
structured response.

Status: PASS — manually verified using the current mock node.

Note:

The actual Fraud/Risk Node from Person B has not yet been
connected to the shared backend environment.

# 6. ML/Risk Node Successful Response
## TC-006 — Successful ML Response

Expected Response Fields:

is_fraud
risk_score
risk_status
model_factors
model_version

Status: PASS — fields successfully received from the
current mock node.

Current mock response example:

{
  "is_fraud": false,
  "risk_score": 0.0,
  "risk_status": "low",
  "model_factors": [],
  "model_version": "baseline-v1"
}

Important:

This response is from the mock node and must not be treated
as the final real model output.

# 7. ML/Risk Node Unavailable
## TC-007 — ML Node Unavailable

Condition:

The ML/Risk Node is not running or cannot be reached.

Expected Status: 503

Expected Error Code:

ML_NODE_UNAVAILABLE

Expected Response Structure:

{
  "detail": {
    "error_code": "ML_NODE_UNAVAILABLE",
    "message": "ML/Risk node is currently unavailable",
    "request_id": "<unique-request-id>"
  }
}

Status: PASS — manually verified.

# 8. ML/Risk Node Timeout
## TC-008 — ML Node Timeout

Condition:

The ML/Risk Node does not respond within the configured
timeout limit.

Expected Status: 504

Expected Error Code:

ML_NODE_TIMEOUT

Expected Response Structure:

{
  "detail": {
    "error_code": "ML_NODE_TIMEOUT",
    "message": "ML/Risk node did not respond within the timeout limit",
    "request_id": "<unique-request-id>"
  }
}

Status: PASS — manually verified using the backend
timeout simulation.

# 9. Request ID
## TC-009 — Request ID Generation

Condition:

A valid /analyze request is submitted.

Expected Result:

The backend generates a unique request_id.

Status: PASS — manually verified.

# 10. Risk Score
## TC-010 — Risk Score Response

Expected Field:

risk_score

Contract:

The risk score is defined as a 0–100 risk score/indicator.

It is not a probability and must not be represented as a
probability or percentage.

Status: Provisional — final real-model score behavior
requires verification with the actual Fraud/Risk Node.

# 11. Risk Status
## TC-011 — Risk Status Response

Expected Field:

risk_status

The exact final risk-status values and threshold mapping
remain subject to verification from the actual ML/Risk Node.

Status: Provisional.

# 12. Model Factors
## TC-012 — Model Factors

Expected Field:

model_factors

The factors must represent genuine model-derived
explanations or evidence.

The backend and frontend must not fabricate or invent
model factors.

Status: Provisional — final structure and explanation
method require verification from the actual ML/Risk Node.

# 13. Model Version
## TC-013 — Model Version

Expected Field:

model_version

The backend must return the model version supplied by the
Fraud/Risk Node.

Status: PASS for the current mock integration.

Current mock value:

baseline-v1

Final real model version: TBD.

# 14. Missing Required Fields
## TC-014 — Missing Required Input

Purpose:

Verify behavior when required transaction information is
missing.

Status: PENDING.

Note:

The exact required-field list is not finalized because the
actual Fraud/Risk Node request schema has not yet been
re-verified.

# 15. Invalid Field Types
## TC-015 — Invalid Field Types

Purpose:

Verify behavior when transaction fields contain invalid
data types.

Test:

transaction_amount = "invalid"

Expected Status: 422

Expected Result:

FastAPI/Pydantic rejects the invalid field type before the
request reaches the ML/Risk Node.

Status: PASS — manually verified.

Note:

Final validation behavior for the complete real ML/Risk Node
contract remains pending until the verified Fraud/Risk Node
schema is available.
# 16. Unsupported Merchant Category
## TC-016 — Unsupported Merchant Category

Purpose:

Verify behavior for an unsupported merchant_category.

Status: PENDING.

Note:

The final supported merchant-category list must be verified
against the actual Fraud/Risk Node implementation before
this test is finalized.

# 17. Optional Fields Omitted
## TC-017 — Optional Fields Omitted

Purpose:

Verify that supported optional fields can be omitted without
breaking the analysis request.

Status: PENDING.

Note:

Final optional-field behavior must be verified against the
actual Fraud/Risk Node implementation.

# 18. Frontend Success Handling
## TC-018 — Frontend Successful Analysis

Expected Result:

Frontend receives and displays:

fraud classification
risk score
risk status
model factors
model version
request ID

Status: PENDING — Frontend integration test.

# 19. Frontend Error Handling
## TC-019 — Frontend Error Handling

Expected Result:

Frontend clearly handles backend errors including:

400 invalid input
503 ML/Risk Node unavailable
504 ML/Risk Node timeout

Status: PENDING — Frontend integration test.

# 20. Real ML/Risk Node End-to-End Test
## TC-020 — Real ML Node E2E

Flow:

Transaction Input
      ↓
POST /analyze
      ↓
Backend
      ↓
POST /predict
      ↓
Real Fraud/Risk Node
      ↓
Actual trained model
      ↓
Real model response
      ↓
Backend
      ↓
Structured /analyze response

Expected Result:

Backend successfully consumes the actual Fraud/Risk Node
response and returns the agreed structured result.

Status: PENDING.

Reason:

The actual Fraud/Risk Node implementation and verified
request/response contract have not yet been added to the
shared repository/environment.

# 21. Current Day 3 Test Summary
Test ID	Test	Status
TC-001	Basic API availability	PASS
TC-002	Health check	PENDING
TC-003	Valid transaction	PASS
TC-004	Negative amount	PASS
TC-005	Backend → ML communication	PASS
TC-006	Successful ML response	PASS — Mock
TC-007	ML unavailable	PASS
TC-008	ML timeout	PASS
TC-009	Request ID	PASS
TC-010	Risk score	PROVISIONAL
TC-011	Risk status	PROVISIONAL
TC-012	Model factors	PROVISIONAL
TC-013	Model version	PASS — Mock
TC-014	Missing required fields	PENDING
TC-015	Invalid field types	PENDING
TC-016	Unsupported merchant category	PENDING
TC-017	Optional fields omitted	PENDING
TC-018	Frontend success	PENDING
TC-019	Frontend errors	PENDING
TC-020	Real ML Node E2E	PENDING
# 22. Testing Notes

The current successful E2E tests use the local mock node:

backend.mock_ml:app

running at:

http://127.0.0.1:8001

The backend runs at:

http://127.0.0.1:8000

The real Fraud/Risk Node integration remains pending until
the verified ML implementation and contract are available.

Testing-only fields such as:

simulate_timeout
simulate_unavailable

are internal development/testing mechanisms and are not
considered normal user-facing transaction fields.
# 14. Day 5 Verification

## TC-014 — Day 5 Normal Backend → Fraud Node → Result

Flow:

Orchestrator / Backend → Fraud Node → Result

Expected Status: 200 OK

Verified Result:

is_fraud: false
risk_score: 0.0
risk_status: low
model_version: histgb-candidate-day3-v1

Status: PASS — manually verified on Day 5.

## TC-015 — Day 5 ML Node Unavailable

Expected Status: 503

Expected Error Code:

ML_NODE_UNAVAILABLE

Status: PASS — manually verified on Day 5.

## TC-016 — Day 5 ML Node Timeout

Expected Status: 504

Expected Error Code:

ML_NODE_TIMEOUT

Status: PASS — manually verified on Day 5.

## TC-017 — Day 5 Validation Error

Expected Status: 400

Expected Error Code:

INVALID_INPUT

Status: PASS — manually verified on Day 5.

## Day 5 Pending Items

Loading: PENDING — frontend verification required.
Empty state: PENDING — frontend verification required.
Sector Node: SKIPPED — no Sector Node found in the current project.
