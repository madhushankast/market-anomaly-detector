import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, classification_report

# Paths Setup
BASE_DIR = Path(__file__).resolve().parent.parent
TEST_DATA_PATH = BASE_DIR / "data" / "training" / "test_df.csv"
MODEL_PATH = BASE_DIR / "models" / "stock_model.pkl"
OUTPUT_DIR = BASE_DIR / "outputs" / "metrics"

def evaluate_classification_model():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not TEST_DATA_PATH.exists() or not MODEL_PATH.exists():
        print("❌ Missing data or model files.")
        return

    print("📖 Loading model and test dataset...")
    model = joblib.load(MODEL_PATH)
    test_df = pd.read_csv(TEST_DATA_PATH)

    exclude_cols = [
        "company_id", "main_type", "sub_type", "short_name", "trading_date",
        "future_return_30", "target_up"
    ]
    features = [col for col in test_df.columns if col not in exclude_cols]
    
    X_test = test_df[features]
    y_test_real = test_df["target_up"]

    print("🔮 Generating classification predictions...")
    predictions = model.predict(X_test)

    # Calculate metrics
    accuracy = accuracy_score(y_test_real, predictions)
    precision = precision_score(y_test_real, predictions, zero_division=0)

    print("\n==================================================")
    print("📊 XGBOOST CLASSIFICATION METRICS (TEST SET)")
    print("==================================================")
    print(f"🎯 Directional Accuracy (Hit Rate): {accuracy*100:.2f}%")
    print(f"🔥 Precision (When it says UP, how often is it right?): {precision*100:.2f}%")
    print("==================================================")
    print("\n📋 Detailed Classification Report:\n")
    print(classification_report(y_test_real, predictions, zero_division=0))

if __name__ == "__main__":
    evaluate_classification_model()