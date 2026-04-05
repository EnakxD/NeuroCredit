# NeuroCredit — Alternative Credit Scoring on Blockchain

> **Frostbyte Hackathon 2026 Submission**
> Themes: AI/ML · FinTech · Blockchain/Web3 · Financial Inclusion

---

## The Problem

**1.4 billion people** globally are "credit invisible" — no credit history, no CIBIL score, no access to formal loans. This includes India's 400M+ gig workers, freelancers, and informal economy participants who are financially responsible but systematically excluded.

## The Solution

NeuroCredit is a **decentralized alternative credit scoring system** that:
1. Uses **ML (XGBoost)** to score anyone from 300–900 using 14 alternative financial signals (UPI patterns, bill payments, income stability, savings behaviour)
2. Mints the score as a **Soul Bound Token (ERC-5484 SBT)** on Polygon — owned by the user, immutable, non-transferable
3. Allows **lenders to verify** creditworthiness via a public smart contract function — zero personal data exposed

---

## Architecture

```
User Inputs (14 signals)
        │
        ▼
┌───────────────────┐
│  FastAPI Backend  │  ←── orchestrates everything
└────────┬──────────┘
         │
    ┌────┴──────────────┐
    │                   │
    ▼                   ▼
XGBoost ML Model   Polygon Smart Contract
(score 300–900)    (NeuroCredit.sol ERC-5484)
                         │
                    Soul Bound Token
                    (in user's wallet)
                         │
                    Lender calls verifyCredit()
                    ← score + eligibility only
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Model | Python · XGBoost · scikit-learn · joblib |
| Backend | FastAPI · Pydantic · Uvicorn |
| Smart Contract | Solidity 0.8.20 · ERC-5484 · Polygon Amoy |
| Frontend | HTML · CSS · Vanilla JS (no framework, fast load) |
| Storage | IPFS (metadata) · On-chain (score + eligibility) |

---

## Key Features

### ML Model
- Trained on 5,000 synthetic profiles mirroring India's informal economy
- 14 input features across 5 categories
- XGBoost with regularisation — MAE < 20 points, R² > 0.95
- Scoring breakdown by category (Payment History, Transaction Activity, Income Stability, Savings Behaviour, Tenure)

### Smart Contract (`NeuroCredit.sol`)
- ERC-5484 Soul Bound Token — permanently bound to wallet, non-transferable
- One SBT per wallet address
- `mintCredit(wallet, score, eligible, metadataURI)` — issuer only
- `updateScore(wallet, newScore, ...)` — refreshable as financial behaviour improves
- `verifyCredit(wallet)` — public lender endpoint, returns score + grade + eligibility
- Transfer locked: `transferFrom` reverts with custom error

### Privacy Model
- Raw financial data **never** stored on-chain
- Lenders only see: score (300–900), grade, eligibility boolean
- Future: ZK-proof layer so even the score derivation is private

---

## Running Locally

### 1. Train the ML model
```bash
cd neurocredit
pip install xgboost scikit-learn pandas numpy joblib
python ml/train.py
```

### 2. Start the backend
```bash
pip install fastapi uvicorn pydantic
cd backend
python main.py
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 3. Open the frontend
```bash
# Just open in browser — no build step needed
open frontend/index.html
```

### 4. Deploy contract (optional for demo)
```bash
npm install -g hardhat
# Configure polygon-amoy in hardhat.config.js with your private key
npx hardhat compile
npx hardhat run scripts/deploy.js --network polygon-amoy
```

---

## API Endpoints

### `POST /api/score`
Compute credit score from alternative data.

**Request:**
```json
{
  "wallet_address": "0x...",
  "upi_txn_count": 45,
  "upi_avg_amount": 2800,
  "upi_consistency": 0.72,
  "utility_on_time_pct": 0.85,
  "mobile_on_time_pct": 0.92,
  "rent_on_time_pct": 0.78,
  "income_sources": 2,
  "monthly_income_est": 35000,
  "income_volatility": 0.30,
  "savings_rate": 0.18,
  "has_recurring_sip": 1,
  "mobile_tenure_months": 36,
  "same_address_months": 24,
  "employment_type": 1
}
```

**Response:**
```json
{
  "wallet": "0x...",
  "score": 742,
  "grade": "Good",
  "risk_level": "Low",
  "eligible": true,
  "percentile": 74,
  "breakdown": {
    "Payment History": 85,
    "Transaction Activity": 72,
    "Income Stability": 68,
    "Savings Behaviour": 74,
    "Tenure & Stability": 60
  }
}
```

### `POST /api/verify`
Lender verification — no personal data returned.

```json
{ "wallet_address": "0x..." }
```

---

## Evaluation Criteria Mapping

| Criterion | How NeuroCredit addresses it |
|-----------|------------------------------|
| **Innovation (25%)** | First-of-kind SBT credit scoring for informal economy; ZK-proof roadmap |
| **Technical Implementation (25%)** | XGBoost ML + Solidity ERC-5484 + FastAPI — 3 distinct technical layers |
| **Practical Impact (20%)** | Addresses 1.4B credit-invisible; directly applicable in India today |
| **Design & Usability (15%)** | Clean dark-theme UI, animated score reveal, 3 distinct user journeys |
| **Presentation & Clarity (15%)** | Clear problem → solution → demo flow; live Polygon testnet mint |

---

## Team
Built for Frostbyte Hackathon Grand Finale 2026

---

## License
MIT
