# Demo Readiness

## Required Services

Before the demo, ensure:

1. Backend is running on `http://127.0.0.1:8000`.
2. ML/Risk node is running on `http://127.0.0.1:8001`.
3. Required environment variables are configured.
4. A valid development JWT is available.
5. Frontend is configured to use the backend.

## Deterministic Demo Cases

### Normal Transaction
Use a normal transaction to demonstrate a low-risk LIVE response.

### Flagged Transaction
Use the predefined high-risk transaction to demonstrate:
- `is_fraud: true`
- high `risk_score`
- `risk_status: high`
- explanatory `model_factors`
- `source_mode: LIVE`

### Invalid Input
Send an invalid transaction field and verify that the API returns HTTP `422`.

### ML Node Unavailable
Stop the ML/Risk node and verify that the backend returns HTTP `503`.

### Cached Demo Fallback
Use the exact predefined cached-demo transaction with `simulate_timeout: true`.
Expected result:
- HTTP `200`
- `source_mode: CACHED`

### Non-demo Timeout
Use a different transaction with `simulate_timeout: true`.
Expected result:
- HTTP `504`
- `error_code: ML_NODE_TIMEOUT`

## Backup Plan

If the live ML/Risk node is unavailable during the demo:

- Use the exact predefined cached demo transaction.
- Do not use arbitrary transactions as cached fallback.
- Keep the backend running.
- Restart the ML/Risk node if live analysis is required.

## Security

- Never commit `.env` or real API keys.
- Never expose JWTs or API keys in logs.
- Use development JWTs only for local/demo purposes.
