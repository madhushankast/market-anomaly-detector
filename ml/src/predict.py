import pandas as pd
import numpy as np
import joblib
from pathlib import Path

# Paths Setup
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "training" / "training_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "stock_model.pkl"
OUTPUT_DIR = BASE_DIR / "outputs" / "predictions"

def generate_live_signals(df=None):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MODEL_PATH.exists():
        print("❌ Model missing.")
        return None

    print("📖 Loading model...")
    model = joblib.load(MODEL_PATH)

    if df is None:
        if not INPUT_PATH.exists():
            print("❌ Master feature dataset missing.")
            return None
        print("📖 Loading master feature matrix...")
        df = pd.read_csv(INPUT_PATH)
        df["trading_date"] = pd.to_datetime(df["trading_date"])
        # Isolate ONLY the most recent trading day available for each unique stock
        print("🎯 Extracting the latest available market state for each asset...")
        latest_rows = df.sort_values("trading_date").groupby("company_id").last().reset_index()
    else:
        latest_rows = df.copy()

    # Match the features exactly to what the model was trained on
    features = model.get_booster().feature_names
    if not features:
        exclude_cols = [
            "company_id", "main_type", "sub_type", "short_name", "trading_date",
            "future_return_30", "target_up"
        ]
        features = [col for col in latest_rows.columns if col not in exclude_cols]
    
    # Ensure all required features are present
    missing_features = [f for f in features if f not in latest_rows.columns]
    if missing_features:
        print(f"❌ Missing features in input: {missing_features}")
        return None
        
    X_latest = latest_rows[features]

    # Generate Predictions and Probabilities
    print("🔮 Running inference across assets...")
    latest_rows["predicted_direction"] = model.predict(X_latest)
    
    probabilities = model.predict_proba(X_latest)[:, 1]
    latest_rows["up_probability"] = probabilities

    # Filter and sort by the strongest statistical anomalies
    signal_cols = ["company_id", "trading_date", "close_price"]
    optional_cols = ["rsi_14", "volatility_20"]
    for col in optional_cols:
        if col in latest_rows.columns:
            signal_cols.append(col)
    signal_cols.extend(["predicted_direction", "up_probability"])
    
    trading_signals = latest_rows[signal_cols].sort_values(by="up_probability", ascending=False).reset_index(drop=True)

    # Export to outputs directory
    output_file = OUTPUT_DIR / "live_trading_signals.csv"
    trading_signals.to_csv(output_file, index=False)

    print("\n==================================================")
    print("🚀 LIVE TRADING SIGNALS GENERATED")
    print("==================================================")
    print(trading_signals.head(10)) # Print the top 10 best setups
    print("==================================================")
    print(f"💾 Active signal sheet saved to: {output_file}")
    
    return trading_signals

if __name__ == "__main__":
    generate_live_signals()