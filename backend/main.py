from typing import Optional

import asyncio
import os
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


ML_NODE_URL = os.getenv(
    "ML_NODE_URL",
    "http://127.0.0.1:8001"
)

ML_NODE_TIMEOUT = float(
    os.getenv(
        "ML_NODE_TIMEOUT",
        "2.0"
    )
)


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


class AnalyzeResponse(BaseModel):
    request_id: str
    is_fraud: bool
    risk_score: float
    risk_status: str
    model_factors: list
    model_version: str


@app.get("/")
def root():
    return {
        "message": "Fintech Risk Intelligence API is running"
    }


async def call_ml_node(
    request: AnalyzeRequest
):
    payload = {
        "transaction_amount": request.transaction_amount,
        "transaction_type": request.transaction_type,
        "merchant_category": request.merchant_category,
        "transaction_time": request.transaction_time,
        "distance_from_home": request.distance_from_home,
        "location": request.location,
    }

    if request.simulate_unavailable:
        raise ConnectionError("ML/Risk node unavailable")

    if request.simulate_timeout:
        await asyncio.sleep(ML_NODE_TIMEOUT + 3)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ML_NODE_URL}/predict",
                json=payload,
                timeout=ML_NODE_TIMEOUT
            )

        response.raise_for_status()

        return response.json()

    except httpx.TimeoutException as exc:
        raise asyncio.TimeoutError from exc

    except (
        httpx.ConnectError,
        httpx.ConnectTimeout,
        httpx.NetworkError
    ) as exc:
        raise ConnectionError(
            "ML/Risk node unavailable"
        ) from exc


async def run_risk_analysis(
    request: AnalyzeRequest,
    request_id: str
):
    result = await call_ml_node(request)

    return result


@app.post(
    "/analyze",
    response_model=AnalyzeResponse
)
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
            run_risk_analysis(
                request,
                request_id
            ),
            timeout=ML_NODE_TIMEOUT
        )

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail={
                "error_code": "ML_NODE_TIMEOUT",
                "message": (
                    "ML/Risk node did not respond "
                    "within the timeout limit"
                ),
                "request_id": request_id
            }
        )

    except ConnectionError:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "ML_NODE_UNAVAILABLE",
                "message": (
                    "ML/Risk node is currently unavailable"
                ),
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