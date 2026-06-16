import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

# Paths Setup
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "training" / "training_dataset.csv"
TRAINING_DIR = BASE_DIR / "data" / "training"
MODEL_DIR = BASE_DIR / "models"

def train_classification_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_PATH.exists():
        print(f"❌ Dataset not found at {INPUT_PATH}.")
        return

    print("📖 Loading dataset for Classification...")
    df = pd.read_csv(INPUT_PATH)
    df["trading_date"] = pd.to_datetime(df["trading_date"])

    # 1. Define Features and Target (We now use target_up!)
    exclude_cols = [
        "company_id", "main_type", "sub_type", "short_name", "trading_date",
        "future_return_30", "target_up"
    ]
    features = [col for col in df.columns if col not in exclude_cols]
    target = "target_up"  # 👈 CHANGED TO CLASSIFICATION TARGET

    print(f"🎯 Target Variable: {target} (Binary Classification)")
    print(f"🧬 Selected {len(features)} Features for training.")

    # 2. Time-Based Split
    df = df.sort_values("trading_date").reset_index(drop=True)
    split_idx = int(len(df) * 0.80)
    split_date = df.loc[split_idx, "trading_date"]

    train_df = df[df["trading_date"] <= split_date].copy()
    test_df = df[df["trading_date"] > split_date].copy()

    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]

    print(f"\n📅 Splitting data at date: {split_date.strftime('%Y-%m-%d')}")

    # 3. Model Training (Regularized XGBoost)
    print("\n🏋️ Training XGBClassifier Baseline...")
    
    model = XGBClassifier(
        n_estimators=100,
        max_depth=3,           # Shallow trees to avoid overfitting noise
        learning_rate=0.03,    # Small steps to keep it stable
        subsample=0.8,         # Row subsampling
        colsample_bytree=0.8,  # Feature subsampling
        random_state=42,
        eval_metric="logloss"
    )
    model.fit(X_train, y_train)

    # 4. Quick Performance Checks
    train_preds = model.predict(X_train)
    test_preds = model.predict(X_test)
    
    print(f"   ↳ Train Accuracy: {accuracy_score(y_train, train_preds):.4f}")
    print(f"   ↳ Test Accuracy:  {accuracy_score(y_test, test_preds):.4f}")

    # 5. Save Splits and Model
    train_df.to_csv(TRAINING_DIR / "train_df.csv", index=False)
    test_df.to_csv(TRAINING_DIR / "test_df.csv", index=False)
    joblib.dump(model, MODEL_DIR / "stock_model.pkl")
    print(f"\n💾 Saved assets successfully.")

if __name__ == "__main__":
    train_classification_model()