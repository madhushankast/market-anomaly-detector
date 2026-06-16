import pandas as pd
import numpy as np
import joblib
from pathlib import Path

# Paths Setup
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "training" / "training_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "stock_model.pkl"
OUTPUT_DIR = BASE_DIR / "outputs" / "predictions"

def generate_live_signals():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_PATH.exists() or not MODEL_PATH.exists():
        print("❌ Model or feature dataset missing. Ensure pipeline steps ran.")
        return

    print("📖 Loading model and master feature matrix...")
    model = joblib.load(MODEL_PATH)
    df = pd.read_csv(INPUT_PATH)
    df["trading_date"] = pd.to_datetime(df["trading_date"])

    # 1. Isolate ONLY the most recent trading day available for each unique stock
    print("🎯 Extracting the latest available market state for each asset...")
    latest_rows = df.sort_values("trading_date").groupby("company_id").last().reset_index()

    # 2. Match the features exactly to what the model was trained on
    exclude_cols = [
        "company_id", "main_type", "sub_type", "short_name", "trading_date",
        "future_return_30", "target_up"
    ]
    features = [col for col in latest_rows.columns if col not in exclude_cols]
    
    X_latest = latest_rows[features]

    # 3. Generate Predictions and Probabilities
    print("🔮 Running inference across assets...")
    latest_rows["predicted_direction"] = model.predict(X_latest)
    
    # model.predict_proba returns [prob_of_0, prob_of_1]. We want prob_of_1 (Up probability).
    probabilities = model.predict_proba(X_latest)[:, 1]
    latest_rows["up_probability"] = probabilities

    # 4. Filter and sort by the strongest statistical anomalies
    # We want to see the highest probability setups at the very top
    trading_signals = latest_rows[[
        "company_id", "trading_date", "close_price", "rsi_14", "volatility_20", 
        "predicted_direction", "up_probability"
    ]].sort_values(by="up_probability", ascending=False).reset_index(drop=True)

    # 5. Export to outputs directory
    output_file = OUTPUT_DIR / "live_trading_signals.csv"
    trading_signals.to_csv(output_file, index=False)

    print("\n==================================================")
    print("🚀 LIVE TRADING SIGNALS GENERATED")
    print("==================================================")
    print(trading_signals.head(10)) # Print the top 10 best setups
    print("==================================================")
    print(f"💾 Active signal sheet saved to: {output_file}")

if __name__ == "__main__":
    generate_live_signals()