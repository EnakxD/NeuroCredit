"""
NeuroCredit - FastAPI Backend
Bridges ML model <-> Blockchain <-> Frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from ml.score import score_applicant

app = FastAPI(
    title="NeuroCredit API",
    description="Alternative credit scoring powered by ML + Blockchain",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response schemas ─────────────────────────────────────────────

class ScoreRequest(BaseModel):
    wallet_address: str = Field(..., description="Ethereum wallet address")

    # UPI
    upi_txn_count:   int   = Field(..., ge=0, le=500,  description="Monthly UPI transactions")
    upi_avg_amount:  float = Field(..., ge=0,           description="Avg UPI transaction (INR)")
    upi_consistency: float = Field(..., ge=0, le=1,     description="Transaction regularity 0–1")

    # Bills
    utility_on_time_pct: float = Field(..., ge=0, le=1, description="Utility bills paid on time")
    mobile_on_time_pct:  float = Field(..., ge=0, le=1, description="Mobile bill paid on time")
    rent_on_time_pct:    float = Field(..., ge=0, le=1, description="Rent paid on time")

    # Income
    income_sources:     int   = Field(..., ge=1, le=10, description="Number of income sources")
    monthly_income_est: float = Field(..., ge=0,         description="Est. monthly income (INR)")
    income_volatility:  float = Field(..., ge=0, le=1,   description="Income volatility 0=stable 1=volatile")

    # Savings
    savings_rate:     float = Field(..., ge=0, le=1, description="Fraction of income saved")
    has_recurring_sip: int  = Field(..., ge=0, le=1, description="Has SIP/recurring investment")

    # Stability
    mobile_tenure_months: int = Field(..., ge=0, le=240, description="Months with current mobile number")
    same_address_months:  int = Field(..., ge=0, le=240, description="Months at current address")
    employment_type:      int = Field(..., ge=0, le=2,   description="0=gig 1=self-employed 2=salaried")

    @validator("wallet_address")
    def validate_wallet(cls, v):
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format")
        return v.lower()


class ScoreResponse(BaseModel):
    wallet:     str
    score:      int
    grade:      str
    risk_level: str
    eligible:   bool
    color:      str
    percentile: int
    breakdown:  dict
    message:    str


class VerifyRequest(BaseModel):
    wallet_address: str

class VerifyResponse(BaseModel):
    wallet:   str
    score:    Optional[int]
    grade:    Optional[str]
    eligible: Optional[bool]
    found:    bool
    message:  str


# In-memory store (replace with DB / on-chain read in production)
_score_store: dict[str, dict] = {}


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"name": "NeuroCredit API", "status": "running", "version": "1.0.0"}


@app.post("/api/score", response_model=ScoreResponse)
def compute_score(req: ScoreRequest):
    """
    Run ML model on submitted data and return credit score.
    In production: also triggers SBT mint on Polygon.
    """
    try:
        data = req.dict()
        wallet = data.pop("wallet_address")

        result = score_applicant(data)

        # Store for verification endpoint
        _score_store[wallet] = {**result, "wallet": wallet}

        return ScoreResponse(
            wallet=wallet,
            score=result["score"],
            grade=result["grade"],
            risk_level=result["risk_level"],
            eligible=result["eligible"],
            color=result["color"],
            percentile=result["percentile"],
            breakdown=result["breakdown"],
            message=(
                f"Score computed successfully. "
                f"{'Eligible for credit products.' if result['eligible'] else 'Not currently eligible — improving payment consistency will raise your score.'}"
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/verify", response_model=VerifyResponse)
def verify_wallet(req: VerifyRequest):
    """
    Lender endpoint: verify a wallet's credit score.
    Returns only score + eligibility. No personal data.
    """
    wallet = req.wallet_address.lower()

    if wallet not in _score_store:
        return VerifyResponse(
            wallet=wallet,
            score=None,
            grade=None,
            eligible=None,
            found=False,
            message="No credit SBT found for this wallet address."
        )

    r = _score_store[wallet]
    return VerifyResponse(
        wallet=wallet,
        score=r["score"],
        grade=r["grade"],
        eligible=r["eligible"],
        found=True,
        message=f"Credit SBT verified on-chain. Score: {r['score']} ({r['grade']}). "
                f"{'Eligible for credit.' if r['eligible'] else 'Not currently eligible.'}"
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "model": "loaded", "chain": "polygon-amoy-testnet"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
