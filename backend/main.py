from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


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


@app.get("/")
def root():
    return {
        "message": "Fintech Risk Intelligence API is running"
    }


class AnalyzeResponse(BaseModel):
    is_fraud: bool
    risk_score: float
    risk_status: str
    model_factors: list
    model_version: str


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):

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

    return AnalyzeResponse(
        is_fraud=False,
        risk_score=0.0,
        risk_status="low",
        model_factors=[],
        model_version="baseline-v1"
    )