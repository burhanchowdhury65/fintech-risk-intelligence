from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import asyncio


app = FastAPI(
    title="Fintech Risk Intelligence API",
    version="1.0.0"
)


class AnalyzeRequest(BaseModel):
    transaction_amount: Optional[float] = None
    transaction_type: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_time: Optional[str] = None
    distance_from_home: Optional[float] = None
    location: Optional[object] = None
    simulate_timeout: bool = False
    simulate_unavailable: bool = False


@app.get("/")
def root():
    return {
        "message": "Fintech Risk Intelligence API is running"
    }


async def call_ml_node(
    simulate_timeout: bool = False,
    simulate_unavailable: bool = False
):
    if simulate_unavailable:
        raise ConnectionError("ML/Risk node unavailable")

    if simulate_timeout:
        await asyncio.sleep(5)

    return {
        "is_fraud": False,
        "risk_score": 0.0,
        "risk_status": "low",
        "model_factors": [],
        "model_version": "baseline-v1"
    }


class AnalyzeResponse(BaseModel):
    request_id: str
    is_fraud: bool
    risk_score: float
    risk_status: str
    model_factors: list
    model_version: str


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):

    if (
        request.transaction_amount is not None
        and request.transaction_amount < 0
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_INPUT",
                "message": "transaction_amount cannot be negative"
            }
        )

    request_id = str(uuid.uuid4())

    try:
        result = await asyncio.wait_for(
            call_ml_node(
                request.simulate_timeout,
                request.simulate_unavailable
            ),
            timeout=2.0
        )

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail={
                "error_code": "ML_NODE_TIMEOUT",
                "message": "ML/Risk node did not respond within the timeout limit",
                "request_id": request_id
            }
        )

    except ConnectionError:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "ML_NODE_UNAVAILABLE",
                "message": "ML/Risk node is currently unavailable",
                "request_id": request_id
            }
        )

    return AnalyzeResponse(
        request_id=request_id,
        is_fraud=result["is_fraud"],
        risk_score=result["risk_score"],
        risk_status=result["risk_status"],
        model_factors=result["model_factors"],
        model_version=result["model_version"]
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "fintech-risk-intelligence-api"
    }