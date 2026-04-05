"""
NeuroCredit - Alternative Credit Scoring ML Model
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib, json, os

np.random.seed(42)

def generate_synthetic_data(n=5000):
    data = []
    for _ in range(n):
        upi_txn_count        = np.random.randint(5, 200)
        upi_avg_amount       = np.random.lognormal(7, 1.2)
        upi_consistency      = np.random.beta(5, 2)
        utility_on_time_pct  = np.random.beta(7, 2)
        mobile_on_time_pct   = np.random.beta(8, 2)
        rent_on_time_pct     = np.random.beta(6, 3)
        income_sources       = np.random.randint(1, 5)
        monthly_income_est   = np.random.lognormal(10, 0.8)
        income_volatility    = np.random.beta(3, 5)
        savings_rate         = np.clip(np.random.normal(0.15, 0.08), 0, 0.6)
        has_recurring_sip    = int(np.random.choice([0, 1], p=[0.6, 0.4]))
        mobile_tenure_months = np.random.randint(6, 120)
        same_address_months  = np.random.randint(6, 84)
        employment_type      = int(np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2]))
        score = 300
        score += (utility_on_time_pct*80 + mobile_on_time_pct*60 + rent_on_time_pct*80)
        score += (min(upi_txn_count/200,1)*80 + upi_consistency*70)
        score += (min(monthly_income_est/100000,1)*60 + (1-income_volatility)*50 + income_sources*8)
        score += (savings_rate/0.6*50 + has_recurring_sip*20)
        score += (min(mobile_tenure_months/120,1)*25 + min(same_address_months/84,1)*25 + employment_type*10)
        score += np.random.normal(0, 15)
        score = float(np.clip(score, 300, 900))
        data.append({"upi_txn_count":upi_txn_count,"upi_avg_amount":round(float(upi_avg_amount),2),
            "upi_consistency":round(float(upi_consistency),4),"utility_on_time_pct":round(float(utility_on_time_pct),4),
            "mobile_on_time_pct":round(float(mobile_on_time_pct),4),"rent_on_time_pct":round(float(rent_on_time_pct),4),
            "income_sources":income_sources,"monthly_income_est":round(float(monthly_income_est),2),
            "income_volatility":round(float(income_volatility),4),"savings_rate":round(float(savings_rate),4),
            "has_recurring_sip":has_recurring_sip,"mobile_tenure_months":mobile_tenure_months,
            "same_address_months":same_address_months,"employment_type":employment_type,"credit_score":round(score,2)})
    return pd.DataFrame(data)

def train_model():
    print("Generating 5,000 synthetic training profiles...")
    df = generate_synthetic_data(5000)
    os.makedirs("ml/artifacts", exist_ok=True)
    df.to_csv("ml/training_data.csv", index=False)
    print(f"Score range: {df.credit_score.min():.0f} to {df.credit_score.max():.0f}")
    FEATURES = [c for c in df.columns if c != "credit_score"]
    X, y = df[FEATURES], df["credit_score"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)
    print("Training GradientBoosting model (300 estimators)...")
    model = GradientBoostingRegressor(n_estimators=300,max_depth=5,learning_rate=0.05,subsample=0.8,random_state=42)
    model.fit(X_train_s, y_train)
    preds = model.predict(X_test_s)
    print(f"MAE: {mean_absolute_error(y_test,preds):.2f} | R2: {r2_score(y_test,preds):.4f}")
    joblib.dump(model,  "ml/artifacts/model.joblib")
    joblib.dump(scaler, "ml/artifacts/scaler.joblib")
    with open("ml/artifacts/features.json","w") as f: json.dump(FEATURES, f)
    with open("ml/artifacts/feature_importance.json","w") as f:
        json.dump(dict(zip(FEATURES, model.feature_importances_.tolist())), f, indent=2)
    print("Model + artifacts saved!")

if __name__ == "__main__":
    train_model()
