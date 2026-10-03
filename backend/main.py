from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import uuid

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.auth import security, verify_access_token
from backend.aria import (
    AriaChatRequest,
    AriaChatResponse,
    handle_aria_message,
)

from backend.tools import (
    dispatch_tool,
    retry_async,
)


# ============================================================
# ML / RISK NODE CONFIG
# ============================================================

ML_NODE_URL = os.getenv(
    "ML_NODE_URL",
    "http://127.0.0.1:8001"
)

# Live analysis timeout.
# If the ML node does not respond within 3 seconds,
# an exact-match cached demo response may be returned.
ML_NODE_TIMEOUT = float(
    os.getenv(
        "ML_NODE_TIMEOUT",
        "3.0"
    )
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Fintech Risk Intelligence API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class AnalyzeRequest(BaseModel):
    transaction_amount: Optional[float] = None
    transaction_type: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_time: Optional[str] = None
    distance_from_home: Optional[float] = None
    location: Optional[object] = None

    # Internal testing flags.
    # These are not exposed in the frontend UI.
    simulate_timeout: bool = False
    simulate_unavailable: bool = False


class AnalyzeResponse(BaseModel):
    request_id: str
    is_fraud: bool
    risk_score: float = Field(..., ge=0, le=100)
    risk_status: str
    model_factors: list
    model_version: str
    counterfactual: dict

    # Indicates where the result came from.
    # LIVE   = real ML/Risk node response
    # CACHED = exact-match cached demo fallback
    source_mode: str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Fintech Risk Intelligence API is running"
    }


# ============================================================
# CACHED DEMO CONFIG
# ============================================================

CACHED_DEMO_INPUT = {
    "transaction_amount": 128.5,
    "transaction_type": "purchase",
    "merchant_category": "grocery_pos",
    "transaction_time": "2026-09-26T14:30:00",
    "distance_from_home": 3.2,
    "location": None,
}

CACHED_DEMO_RESPONSE = {
    "is_fraud": False,
    "risk_score": 0.0,
    "risk_status": "low",
    "model_factors": [],
    "model_version": "histgb-candidate-day3-v1",
}


def is_exact_cached_demo(
    request: AnalyzeRequest,
) -> bool:
    """
    Returns True only when every cached-demo input field
    matches exactly.

    This prevents arbitrary transactions from receiving
    a cached/demo response.
    """

    return (
        request.transaction_amount
        == CACHED_DEMO_INPUT["transaction_amount"]
        and request.transaction_type
        == CACHED_DEMO_INPUT["transaction_type"]
        and request.merchant_category
        == CACHED_DEMO_INPUT["merchant_category"]
        and request.transaction_time
        == CACHED_DEMO_INPUT["transaction_time"]
        and request.distance_from_home
        == CACHED_DEMO_INPUT["distance_from_home"]
        and request.location
        == CACHED_DEMO_INPUT["location"]
    )


def get_cached_demo_response(
    request_id: str,
):
    """
    Builds the cached fallback response.
    """

    return {
        "request_id": request_id,
        "is_fraud": CACHED_DEMO_RESPONSE["is_fraud"],
        "risk_score": CACHED_DEMO_RESPONSE["risk_score"],
        "risk_status": CACHED_DEMO_RESPONSE["risk_status"],
        "model_factors": CACHED_DEMO_RESPONSE["model_factors"],
        "model_version": CACHED_DEMO_RESPONSE["model_version"],
        "counterfactual": {
            "found": False,
            "changed_feature": None,
            "changed_feature_label": None,
            "original_value": None,
            "suggested_value": None,
            "new_risk_score": None,
            "new_risk_status": None,
            "reason": None,
        },
        "source_mode": "CACHED",
    }


# ============================================================
# ML NODE COMMUNICATION
# ============================================================

async def call_ml_node(
    request: AnalyzeRequest
):
    # ARIA may provide time-only input such as "03:15".
    # The ML node expects transaction_time as a full ISO datetime.
    transaction_time = request.transaction_time

    if isinstance(transaction_time, str):
        import re

        if re.fullmatch(r"\\d{2}:\\d{2}", transaction_time):
            transaction_time = f"2026-01-01T{transaction_time}:00"
        elif re.fullmatch(r"\\d{2}:\\d{2}:\\d{2}", transaction_time):
            transaction_time = f"2026-01-01T{transaction_time}"

    payload = {
        "transaction_amount": request.transaction_amount,
        "transaction_type": request.transaction_type,
        "merchant_category": request.merchant_category,
        "transaction_time": transaction_time,
        "distance_from_home": request.distance_from_home,
        "location": request.location,
    }

    # --------------------------------------------------------
    # TEST: ML NODE UNAVAILABLE
    # --------------------------------------------------------

    if request.simulate_unavailable:
        raise ConnectionError("ML/Risk node unavailable")

    # --------------------------------------------------------
    # TEST: ML NODE TIMEOUT
    # --------------------------------------------------------

    if request.simulate_timeout:
        await asyncio.sleep(
            ML_NODE_TIMEOUT + 3
        )

    try:

        async def make_request():

            async with httpx.AsyncClient() as client:

                response = await client.post(
                    f"{ML_NODE_URL}/predict",
                    json=payload,
                    timeout=ML_NODE_TIMEOUT,
                )

            response.raise_for_status()

            return response.json()

        return await retry_async(
            make_request,
        )

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


# ============================================================
# RISK ANALYSIS
# ============================================================

async def run_risk_analysis(
    request: AnalyzeRequest,
    request_id: str
):

    result = await call_ml_node(request)

    return result


# ============================================================
# ARIA ANALYSIS TOOL
# ============================================================

async def aria_analyze_tool(
    **arguments
):

    request = AnalyzeRequest(
        **arguments
    )

    return await analyze_transaction_tool(
        request
    )


# ============================================================
# ANALYZE TRANSACTION TOOL
# ============================================================

async def analyze_transaction_tool(
    request: AnalyzeRequest,
):

    """
    Allow-listed tool handler for transaction risk analysis.

    Flow:

    1. Validate input.
    2. Call ML/Risk node.
    3. Wait maximum 3 seconds.
    4. If ML responds -> LIVE response.
    5. If ML times out:
       - exact cached demo input -> CACHED response
       - otherwise -> 504 timeout
    6. If ML node is unavailable -> 503.
    """

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if (
        request.transaction_amount is not None
        and request.transaction_amount < 0
    ):

        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_INPUT",
                "message": (
                    "transaction_amount cannot be negative"
                )
            }
        )

    request_id = str(
        uuid.uuid4()
    )

    # --------------------------------------------------------
    # LIVE ML ANALYSIS
    # --------------------------------------------------------

    try:

        result = await asyncio.wait_for(
            run_risk_analysis(
                request,
                request_id
            ),
            timeout=ML_NODE_TIMEOUT
        )

    # --------------------------------------------------------
    # 3-SECOND TIMEOUT
    # --------------------------------------------------------

    except asyncio.TimeoutError:

        # IMPORTANT:
        # Only the exact predefined cached demo input
        # receives the CACHED fallback.

        if is_exact_cached_demo(request):

            return get_cached_demo_response(
                request_id
            )

        # Any other transaction keeps the normal
        # timeout behavior.

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

    # --------------------------------------------------------
    # ML NODE UNAVAILABLE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # ML NODE VALIDATION ERROR
    # --------------------------------------------------------

    except httpx.HTTPStatusError as exc:

        if exc.response.status_code == 422:

            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_INPUT",
                    "message": (
                        "ML/Risk node rejected the input"
                    ),
                    "request_id": request_id
                }
            )

        raise

    # --------------------------------------------------------
    # LIVE RESPONSE
    # --------------------------------------------------------

    return {
        "request_id": request_id,
        "is_fraud": result["is_fraud"],
        "risk_score": result["risk_score"],
        "risk_status": result["risk_status"],
        "model_factors": result["model_factors"],
        "model_version": result["model_version"],
        "counterfactual": result["counterfactual"],
        "source_mode": "LIVE",
    }


# ============================================================
# HEALTH STATUS TOOL
# ============================================================

async def health_status_tool():

    return {
        "status": "ok",
        "service": "fintech-risk-intelligence-api"
    }


# ============================================================
# /analyze
# ============================================================

@app.post(
    "/analyze",
    response_model=AnalyzeResponse
)
async def analyze(
    request: AnalyzeRequest,
    user: str = Depends(
        lambda credentials=Depends(security):
        verify_access_token(credentials)
    ),
):

    return await dispatch_tool(
        "analyze_transaction",
        {
            "analyze_transaction": analyze_transaction_tool,
            "health/status": health_status_tool,
        },
        request=request,
    )


# ============================================================
# /health
# ============================================================

@app.get("/health")
async def health_check():

    return await dispatch_tool(
        "health/status",
        {
            "analyze_transaction": analyze_transaction_tool,
            "health/status": health_status_tool,
        },
    )


# ============================================================
# /aria/chat
# ============================================================

@app.post(
    "/aria/chat",
    response_model=AriaChatResponse,
)
async def aria_chat(
    request: AriaChatRequest,
    user: str = Depends(
        lambda credentials=Depends(security):
        verify_access_token(credentials)
    ),
):

    reply, provider, tool_result = await handle_aria_message(
        message=request.message,
        language=request.language,
        analyze_tool=aria_analyze_tool,
        context=request.context,
    )

    return AriaChatResponse(
        reply=reply,
        provider=provider,
        session_id=request.session_id,
        tool_result=tool_result,
    )