# Fintech Risk Intelligence API — Current API Contract

## Status

This document describes the current proposed API contract for the
Fintech Risk Intelligence system.

The ML-specific feature selection and risk thresholds are not final yet.
They will be updated after dataset and model validation.

---

## 1. API Information

**API Name:** Fintech Risk Intelligence API

**Version:** 1.0.0

**Framework:** FastAPI

**Development URL:**

http://127.0.0.1:8000

**Swagger Documentation:**

http://127.0.0.1:8000/docs

---

## 2. Health Check

### GET /

Used to verify that the backend API is running.

### Response

```json
{
  "message": "Fintech Risk Intelligence API is running"
}