# MVP Definition — Fintech Risk Intelligence

## 1. MVP Scope

The MVP focuses on demonstrating a complete transaction fraud/risk analysis flow.

The core flow is:

User
→ Dashboard / Transaction Input
→ ARIA
→ Allowed Backend Tool
→ FastAPI Orchestrator
→ Fraud/Risk Node
→ Structured Result
→ ARIA Explanation
→ User

## 2. MVP Cut-line

The MVP must support:

- Transaction analysis through `/analyze`
- Structured transaction input
- Request ID generation
- Fraud/non-fraud result
- Risk score
- Risk status
- Model factors
- Model version
- Input validation
- Timeout handling
- ML/Risk node unavailable handling
- Health/status checking
- Clear error responses

The MVP does not require:

- Multiple sector-specific models
- Advanced production-scale infrastructure
- Additional optional intelligence nodes
- Non-essential UI features

## 3. Demo Flow

### Normal Transaction

1. User submits a transaction.
2. ARIA identifies the transaction-analysis intent.
3. ARIA selects the allowed `analyze_transaction` tool.
4. Backend validates the request.
5. Backend sends the request to the Fraud/Risk Node.
6. Fraud/Risk Node returns a structured prediction.
7. Backend returns the structured result.
8. ARIA explains the result to the user.

### Error Cases

The demo should also show:

- Invalid transaction input → `400`
- ML/Risk node timeout → `504`
- ML/Risk node unavailable → `503`

## 4. Definition of Done

The MVP is considered complete when:

- `/health` is available.
- `/analyze` is available.
- Request validation works.
- `request_id` is generated.
- Successful analysis returns the agreed response structure.
- Invalid input returns a structured error.
- ML timeout is handled.
- ML/Risk node unavailability is handled.
- The backend can consume the agreed Fraud/Risk Node contract.
- The complete mock end-to-end flow can be demonstrated.
- API documentation is available.
- Required configuration files are documented.
- Changes are committed to the team's Git repository.

## 5. Initial Test Cases

| Test Case | Expected Result |
|-----------|-----------------|
| Valid transaction | `200` |
| Negative transaction amount | `400` |
| ML/Risk node timeout | `504` |
| ML/Risk node unavailable | `503` |
| Health check | `200` |
| Request ID generation | Unique request ID |
| Structured success response | Required response fields |