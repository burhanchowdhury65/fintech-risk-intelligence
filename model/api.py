"""
api.py — Day 4: FastAPI prediction endpoint for the Fraud/Risk Node.

Run with:
    uvicorn api:app --reload --host 127.0.0.1 --port 8001
    (or simply: python api.py — reads FRAUD_NODE_HOST/FRAUD_NODE_PORT from config.py,
    which in turn reads them from environment variables / a .env file, per Person A's
    Day 5 request. Defaults to 127.0.0.1:8001 if not set — this is a SEPARATE port from
    the main backend, which runs its own /analyze endpoint on 127.0.0.1:8000.)

Then test with:
    curl -X POST http://127.0.0.1:8001/predict -H "Content-Type: application/json" -d '{
      "request_id": "req_test_1",
      "transaction_id": "txn_test_1",
      "transaction_amount": 128.50,
      "merchant_category": "grocery_pos",
      "transaction_time": "2026-09-26T14:30:00",
      "distance_from_home": 3.2
    }'

Note on error codes: the backend (Person A) has proposed ML_NODE_UNAVAILABLE (503) /
ML_NODE_TIMEOUT (504) as BACKEND-level error codes for when it can't reach this node.
This node does NOT implement those codes itself — it uses its own node-level codes
(MODEL_UNAVAILABLE, PREDICTION_ERROR) below, per the Day 4 instruction not to assume
backend-level proposals apply inside the node unless the team explicitly agrees.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import NODE_HOST, NODE_PORT
from schemas import TransactionRequest, PredictionResponse, ErrorResponse
from predict import predict_one, get_pipeline, MODEL_VERSION

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_risk_node")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model once when the API starts (modern replacement for the deprecated
    @app.on_event('startup') decorator), so the first request isn't slow and so we fail
    loudly at startup if the model file is missing, rather than on a live user request."""
    try:
        get_pipeline()
        logger.info(f"Model pipeline loaded successfully. model_version={MODEL_VERSION}")
    except FileNotFoundError as e:
        logger.warning(f"{e}")
        logger.warning("The /predict endpoint will return MODEL_UNAVAILABLE until finalize_candidate.py is run.")
    yield  # app runs here
    logger.info("Fraud/Risk Node shutting down.")


app = FastAPI(title="Fraud/Risk Detection Node", version="0.1.0-draft", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse, responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
def predict(request: TransactionRequest):
    # Basic logging (Day 4 Step 9 requirement) — request_id/transaction_id only, never
    # raw transaction amounts or any PII-adjacent fields (gender, age), per the rule
    # against exposing sensitive data in logs.
    logger.info(f"Received prediction request. request_id={request.request_id} transaction_id={request.transaction_id}")

    try:
        result = predict_one(request.model_dump())
    except FileNotFoundError:
        logger.error(f"Model unavailable for request_id={request.request_id}")
        error = ErrorResponse(
            request_id=request.request_id,
            transaction_id=request.transaction_id,
            error_code="MODEL_UNAVAILABLE",
            error_message="The Fraud/Risk model is not currently loaded. Run finalize_candidate.py to produce the model artifact.",
        )
        return JSONResponse(status_code=503, content=error.model_dump())
    except Exception as e:
        logger.error(f"Prediction error for request_id={request.request_id}: {str(e)}")
        error = ErrorResponse(
            request_id=request.request_id,
            transaction_id=request.transaction_id,
            error_code="PREDICTION_ERROR",
            error_message=f"An unexpected error occurred during prediction: {str(e)}",
        )
        return JSONResponse(status_code=500, content=error.model_dump())

    logger.info(f"Prediction complete. request_id={request.request_id} is_fraud={result['is_fraud']} risk_score={result['risk_score']}")

    return PredictionResponse(
        request_id=request.request_id,
        transaction_id=request.transaction_id,
        status="ok",
        **result,
    )


if __name__ == "__main__":
    # Convenience for beginners: `python api.py` works the same as the uvicorn command
    # above, using the host/port from config.py (env-var driven, per Person A's request).
    import uvicorn
    logger.info(f"Starting Fraud/Risk Node on {NODE_HOST}:{NODE_PORT}")
    uvicorn.run("api:app", host=NODE_HOST, port=NODE_PORT)

