import pandas as pd
from pathlib import Path

# Paths Setup - Tailored exactly to market-anomaly-detector/
BASE_DIR = Path(__file__).resolve().parent.parent  # Points to market-anomaly-detector/ml/
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TRAINING_DIR = BASE_DIR / "data" / "training"

def build_master_dataset():
    # Ensure the ml/data/training/ directory exists
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Gather all individual processed feature files
    feature_files = list(PROCESSED_DIR.glob("*_features.csv"))
    
    if not feature_files:
        print(f"❌ No processed feature files found in {PROCESSED_DIR}")
        print("Please run your feature_engineering.py script first.")
        return

    print(f"📦 Found {len(feature_files)} stock feature files. Combining...")

    all_dfs = []
    
    # 2. Read each file and track progress
    for file_path in feature_files:
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                print(f"⚠️ Warning: {file_path.name} is empty. Skipping.")
                continue
                
            all_dfs.append(df)
            print(f"  -> Loaded {file_path.name} ({len(df)} rows)")
            
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")

    # 3. Concatenate all dataframes vertically
    if not all_dfs:
        print("❌ No valid data to combine.")
        return

    print("\n🔄 Stacking datasets vertically...")
    master_df = pd.concat(all_dfs, ignore_index=True)

    # 4. Final Data Sorting (Crucial for Time-Series tracking later)
    if "trading_date" in master_df.columns:
        master_df["trading_date"] = pd.to_datetime(master_df["trading_date"])
        master_df = master_df.sort_values("trading_date").reset_index(drop=True)

    # 5. Save the final output into ml/data/training/training_dataset.csv
    output_path = TRAINING_DIR / "training_dataset.csv"
    master_df.to_csv(output_path, index=False)
    
    print("\n==================================================")
    print(f"✅ Success! Master training dataset created.")
    print(f"📍 Location: {output_path}")
    print(f"📊 Total Rows: {master_df.shape[0]} | Total Columns: {master_df.shape[1]}")
    print("==================================================")

if __name__ == "__main__":
    build_master_dataset()