# Fintech Risk Intelligence System

An AI-powered  risk intelligence platform that analyzes financial transactions, generates a risk score, explains the factors behind the result, and provides natural-language assistance through ARIA.

# Fintech Risk Intelligence

> AI-powered transaction risk analysis and fraud detection system.

## 🚀 Live Demo

👉 [Open Fintech Risk Intelligence](https://fintech-risk-intelligence.vercel.app/)

## 📦 GitHub Repository

👉 [View Source Code](https://github.com/burhanchowdhury65/fintech-risk-intelligence)

> **Hackathon Prototype**
>
> This system uses simulated transaction data for demonstration purposes. It is not intended for real financial transactions or production financial decision-making.

---

## 1. Project Overview

Fintech Risk Intelligence is a unified transaction risk analysis platform designed to demonstrate how machine learning and AI agents can work together to identify potentially risky financial transactions.

The platform allows users to:

- Submit transaction information
- Analyze transaction risk
- Receive a 0–100 risk score
- See whether the transaction is classified as fraudulent
- View the factors contributing to the risk
- View a counterfactual explanation showing how a tested feature change could affect the risk score
- Ask ARIA questions about the transaction and its result

The system separates the machine-learning result from the AI-generated explanation.

The ML/Risk node provides the verified analysis result, while ARIA explains that result in natural language.

---

## 2. Problem Statement

Financial transaction risk systems can produce numerical risk scores that are difficult for users to understand.

A user may know that a transaction has a high risk score, but may not understand:

- Why the transaction was flagged
- Which factors contributed to the risk
- What hypothetical feature change could affect the score
- How to interpret the result

This project addresses this explainability problem by combining structured risk analysis with an AI assistant and counterfactual explanations.

---

## 3. Proposed Solution

The platform combines:

1. A web-based transaction analysis interface
2. A FastAPI backend
3. A Fraud/Risk Detection node
4. A machine-learning risk model
5. ARIA, an AI assistant for natural-language interaction
6. Counterfactual explanations for supported transaction analyses

The general flow is:

```text
User
  │
  ▼
Next.js Frontend
  │
  ▼
FastAPI / Application Backend
  │
  ├──────────────► ARIA
  │                 │
  │                 ▼
  │             LLM Provider
  │
  ▼
Fraud / Risk Analysis
  │
  ▼
ML Risk Model
  │
  ▼
Risk Result
  │
  ├── Risk Score
  ├── Fraud Classification
  ├── Model Factors
  └── Counterfactual
          │
          ▼
      Frontend Result
          │
          ▼
      ARIA Explanation
```

---

## 4. Key Features

### Transaction Risk Analysis

Users can provide transaction information including:

- Transaction amount
- Transaction type
- Merchant category
- Transaction time
- Distance from home
- Location

The backend returns a structured risk analysis.

### Risk Score

The system produces a risk score between:

```text
0 – 100
```

The score is a relative risk score and should not be interpreted as a calibrated probability.

### Fraud Classification

The analysis includes an `is_fraud` result indicating whether the model classified the transaction as potentially fraudulent.

### Model Factors

The system provides factors that contributed to the risk result.

Example:

```text
Transaction amount is unusually high
Transaction location is far from customer's home
Transaction occurred at an unusual hour
```

### Counterfactual Explanation

The system provides counterfactual explanations for supported transaction analyses.

A counterfactual explanation shows a hypothetical change to a transaction feature and how that tested change affects the model's risk score and risk status.

Example:

```text
Original transaction amount: 890
Hypothetical amount: 623

Original risk score: 99
Hypothetical risk score: 67

Original risk status: High
Hypothetical risk status: Medium
```

The counterfactual explanation is displayed in a dedicated result card in the frontend.

Counterfactual results are hypothetical and illustrative. They do not guarantee that changing a transaction feature would prevent fraud or make a transaction safe.

### ARIA AI Assistant

ARIA allows users to interact with the system using natural language.

ARIA can:

- Analyze a transaction
- Explain an existing analysis
- Explain model factors
- Explain the counterfactual result
- Answer general questions related to the system

ARIA uses the existing transaction context when explaining an already-analyzed transaction.

For example, after a transaction has been analyzed, the user can ask:

```text
Why is this transaction high risk?
```

or:

```text
What would change this result?
```

ARIA can use the existing verified analysis result, including the counterfactual information, to generate an explanation.

### Error Handling

The backend handles cases including:

- Invalid input
- ML node timeout
- ML node unavailable
- ML validation errors

### LLM Provider Fallback

The ARIA layer supports an LLM provider fallback mechanism.

### Demo Inputs

The frontend provides predefined demo scenarios for testing the application without entering transaction data manually.

---

## 5. System Architecture

### Frontend

The frontend is implemented using:

- Next.js
- React
- TypeScript

It provides:

- Transaction analysis interface
- Result display
- Counterfactual card
- ARIA chat interface
- Demo transaction inputs

### Backend

The backend is implemented using:

- Python
- FastAPI
- Pydantic

The backend handles:

- Transaction validation
- Risk analysis orchestration
- ARIA orchestration
- Error handling
- API responses

### ARIA

ARIA acts as the natural-language intelligence layer.

The general ARIA flow is:

```text
User Message
     │
     ▼
ARIA Decision
     │
     ├── Chat
     │
     ├── Analyze Transaction
     │
     └── Explain Current Result
              │
              ▼
       Existing Analysis
              │
              ├── Risk Score
              ├── Model Factors
              └── Counterfactual
                      │
                      ▼
                ARIA Explanation
```

When explaining an existing result, ARIA receives the structured analysis result rather than trying to reconstruct the result from the conversation text.

---

## 6. AI / ML Approach

The risk analysis node provides a structured result containing:

```json
{
  "request_id": "...",
  "is_fraud": true,
  "risk_score": 99,
  "risk_status": "high",
  "model_factors": [],
  "model_version": "...",
  "counterfactual": {},
  "source_mode": "LIVE"
}
```

### Risk Model

Current model version:

```text
histgb-candidate-day3-v1
```

### Risk Factors

The model result may contain multiple factors explaining why the transaction received its risk score.

### Counterfactual Analysis

The counterfactual component provides a tested hypothetical change to a feature and reports the corresponding model output.

A counterfactual result can contain:

- Changed feature
- Feature label
- Original value
- Suggested/hypothetical value
- Original risk score
- New risk score
- Original risk status
- New risk status
- Explanation of the hypothetical change

Example:

```json
{
  "found": true,
  "changed_feature": "amt",
  "changed_feature_label": "transaction amount",
  "original_value": 890.0,
  "suggested_value": 623.0,
  "new_risk_score": 67,
  "new_risk_status": "medium"
}
```

The counterfactual is treated as a hypothetical model scenario. It is not a guarantee that changing the feature would prevent fraud or make a transaction safe.

### ARIA and Verified Results

ARIA does not act as the source of truth for the risk result.

The structured ML/Risk analysis remains authoritative for:

- Risk score
- Risk status
- Fraud classification
- Model factors
- Model version
- Counterfactual result

ARIA converts these verified results into a user-friendly natural-language explanation.

---

## 7. Technology Stack

### Frontend

- Next.js
- React
- TypeScript
- Turbopack

### Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

### AI

- ARIA AI Agent
- Groq
- LLM provider fallback

### Machine Learning

- Histogram Gradient Boosting based risk model
- Model version: `histgb-candidate-day3-v1`

### Development Tools

- Git
- GitHub
- VS Code
- npm
- Python virtual environment

---

## 8. Requirements

### Software

- Node.js
- npm
- Python 3.x
- Git
- Modern web browser

### API / Environment Requirements

The project may require configured LLM/API credentials depending on the enabled configuration.

Do not commit API keys or other secrets to GitHub.

---

## 9. Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/burhanchowdhury65/fintech-risk-intelligence.git
cd fintech-risk-intelligence
```

### 2. Backend Setup

Create and activate the Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

---

## 10. Environment Variables

Create the required environment configuration according to the project's environment template.

Example:

```env
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

For the frontend, configure the required environment variables according to the provided `.env.example`.

Example:

```env
NEXT_PUBLIC_USE_MOCK_API=false
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
DEV_JWT=your_development_jwt
```

### Important

Never commit real API keys, JWT secrets, or other sensitive credentials to GitHub.

Use local environment files for development secrets and keep them excluded through `.gitignore`.

---

## 11. Running the Project

### Start the Backend

From the project root:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

The backend runs on:

```text
http://127.0.0.1:8000
```

### Development Frontend

From the `frontend` directory:

```bash
npm run dev
```

For LAN access during development:

```bash
npm run dev -- --hostname 0.0.0.0
```

### Production Frontend

Build the frontend:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

For LAN access:

```bash
npm start -- --hostname 0.0.0.0
```

---

## 12. Testing

### Test 1 — Normal Transaction

Use the frontend's normal transaction demo.

Expected:

- Transaction analysis completes
- Risk score is displayed
- Risk status is displayed
- Model factors are displayed

### Test 2 — Flagged Transaction

Use the flagged transaction demo.

Expected:

- Higher risk result
- Fraud classification
- Model factors
- Counterfactual information when available

### Test 3 — Counterfactual Explanation

After analyzing a transaction where a counterfactual result is available, verify that the counterfactual card is displayed.

The card should show:

- Original feature value
- Suggested/hypothetical feature value
- Original risk score
- New risk score
- Original risk status
- New risk status
- Explanation of the hypothetical change

The counterfactual should remain associated with the corresponding transaction analysis result.

### Test 4 — ARIA Current Result Context

After analyzing a transaction, ask ARIA:

```text
Why is this transaction high risk?
```

Then try:

```text
What factors affected this result?
```

And:

```text
What would change this result?
```

Expected behavior:

- ARIA uses the existing transaction result
- ARIA does not unnecessarily request a new transaction analysis
- ARIA can explain the model factors
- ARIA can explain available counterfactual information
- The existing counterfactual card remains displayed

### Test 5 — Cached Demo

Use the predefined cached demo input.

Expected:

- The exact predefined demo transaction can use the cached fallback behavior
- The returned result identifies the appropriate source mode

### Test 6 — Invalid Input

Use the invalid-input demo.

Expected:

- Validation error
- No application crash

### Test 7 — API Health

Check the backend:

```bash
curl http://127.0.0.1:8000/
```

Expected:

```json
{
  "message": "Fintech Risk Intelligence API is running"
}
```

---

## 13. API Overview

### Health Check

```http
GET /
```

### Transaction Analysis

```http
POST /api/analyze
```

### ARIA Chat

```http
POST /api/aria/chat
```

The frontend uses server-side API proxy routes so that backend/API configuration does not need to be exposed directly to the browser.

---

## 14. Security Notes

- API keys must not be committed to the repository.
- Environment variables should be used for secrets.
- The frontend communicates with the application through API routes.
- Authentication-related tokens should not be hard-coded into frontend source code.
- Demo data is synthetic and should not contain real financial information.
- Development credentials should not be reused as production credentials.

---

## 15. Limitations

- This is a hackathon prototype.
- The model is trained/evaluated using simulated transaction data.
- The risk score is a relative ranking and not a calibrated probability.
- Model explanations are limited to the available model factors.
- Counterfactual results are hypothetical and illustrative.
- A counterfactual change does not guarantee that a transaction would become safe or that fraud would be prevented.
- The system is not intended to make real-world financial decisions.
- Production deployment would require additional security, monitoring, validation, privacy, and compliance controls.

---

## 16. Future Work

Potential future improvements include:

- Additional risk intelligence nodes
- More advanced fraud detection models
- Real-time transaction monitoring
- Improved explainability
- More sophisticated counterfactual analysis
- Additional financial intelligence capabilities
- Improved multilingual interaction
- Production-grade authentication and authorization
- Cloud deployment and scalable infrastructure

---

## 17. Project Structure

```text
fintech-risk-intelligence/
│
├── backend/
│   ├── main.py
│   ├── aria.py
│   ├── aria_tools.py
│   └── ...
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── ...
│
├── docs/
│   ├── api-contract.md
│   ├── mvp-definition.md
│   └── ...
│
├── .env.example
├── .gitignore
├── README.md
└── ...
```

---

## 18. Demo Disclaimer

This project is a hackathon demonstration.

All transaction examples shown in the application are synthetic/demo data and should not be treated as real financial records.

The system's risk score, fraud classification, model factors, and counterfactual results are intended to demonstrate the concept of AI-assisted transaction risk intelligence.

---

## 19. Repository

GitHub:

https://github.com/burhanchowdhury65/fintech-risk-intelligence

---

## 20. Team

**Fintech Risk Intelligence**

Built as a hackathon project demonstrating AI-assisted financial transaction risk analysis, explainability, counterfactual analysis, and natural-language interaction.