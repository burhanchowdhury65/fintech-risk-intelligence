# Fintech Risk Intelligence API — API Contract

## Status

This document defines the current API contract for the
Fintech Risk Intelligence system.

The API contract is being finalized during Day 1.
ML-specific feature selection, final risk-score thresholds,
and final model behavior are still subject to confirmation
from the ML/Risk Node.

---

# 1. API Information

**API Name:** Fintech Risk Intelligence API

**Version:** 1.0.0

**Framework:** FastAPI

**Development URL:**

http://127.0.0.1:8000

**Swagger Documentation:**

http://127.0.0.1:8000/docs


# 2. Endpoint Ownership

| Endpoint | Purpose | Owner |
|---|---|---|
| GET / | Basic API availability | Person A / Backend |
| GET /health | Backend health check | Person A / Backend |
| POST /analyze | Transaction risk analysis | Person A / Backend |
| ML/Risk Node | Fraud/risk prediction | Person B / ML |
| Frontend integration | Display analysis result | Person C / Frontend |

The backend is responsible for validating requests,
generating request IDs, calling the ML/Risk Node,
handling timeout/unavailability errors, and returning
the agreed API response.


# 3. GET /

Used to verify that the backend API is running.

## Response

**Status:** `200 OK`

```json
{
  "message": "Fintech Risk Intelligence API is running"
}