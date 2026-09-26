from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="Mock Fraud Risk Node",
    version="1.0.0"
)


class RiskRequest(BaseModel):
    transaction_amount: float | None = None
    transaction_type: str | None = None
    merchant_category: str | None = None
    transaction_time: str | None = None
    distance_from_home: float | None = None
    location: object | None = None


class RiskResponse(BaseModel):
    is_fraud: bool
    risk_score: float
    risk_status: str
    model_factors: list
    model_version: str


@app.get("/")
def root():
    return {
        "message": "Mock Fraud Risk Node is running"
    }


@app.post("/predict", response_model=RiskResponse)
def predict(request: RiskRequest):

    return RiskResponse(
        is_fraud=False,
        risk_score=0.0,
        risk_status="low",
        model_factors=[],
        model_version="baseline-v1"
    )