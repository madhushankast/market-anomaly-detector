import pandas as pd
import numpy as np
from pathlib import Path

# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# STANDARDIZE COLUMN NAMES
# ==================================================

def standardize_columns(df):
    # Strip whitespace from column names safely
    df.columns = df.columns.str.strip()
    
    rename_dict = {
        "COMPANY ID": "company_id",
        "SHORT NAME": "short_name",
        "TRADING DATE": "trading_date",
        "PRICE HIGH (Rs.)": "price_high",
        "PRICE LOW (Rs.)": "price_low",
        "CLOSE PRICE (Rs.)": "close_price",
        "OPEN PRICE (Rs.)": "open_price",
        "TRADE VOLUME (No.)": "trade_volume",
        "SHARE VOLUME (No.)": "share_volume",
        "TURNOVER (Rs.)": "turnover",
    }
    
    return df.rename(columns=rename_dict)


# ==================================================
# TECHNICAL INDICATORS (Calculated per Series)
# ==================================================

def calculate_rsi(close, period=14):
    """Calculates Wilder's RSI using Exponential Moving Averages."""
    delta = close.diff()
    
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    
    # Using ewm with alpha=1/period matches Welles Wilder's original smoothing
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10) # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    
    return macd, signal, histogram


# ==================================================
# FEATURE ENGINEERING
# ==================================================

def build_features(df):
    # 1. Standardize columns right away
    df = standardize_columns(df).copy()

    # 2. CRITICAL: Drop rows where the text headers accidentally got duplicated in the CSV
    df = df[df["company_id"].astype(str).str.strip() != "company_id"]

    # 3. Date conversion
    df["trading_date"] = pd.to_datetime(df["trading_date"])

    # 4. Clean and convert numeric columns
    numeric_cols = [
        "open_price", "close_price", "price_high", "price_low",
        "trade_volume", "share_volume", "turnover"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            # Clean up potential string issues like commas or spaces (e.g., "1,500" -> "1500")
            df[col] = df[col].astype(str).str.replace(r'[^\d\.]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5. Handle missing volume/turnover data so ratios don't break down stream
    df["share_volume"] = df["share_volume"].fillna(0)
    df["turnover"] = df["turnover"].fillna(0)
    df["trade_volume"] = df["trade_volume"].fillna(0)

    # 6. Sort safely within each stock group before executing rolling calculations
    df = df.sort_values(["company_id", "trading_date"]).reset_index(drop=True)
    grouped = df.groupby("company_id")

    # ==================================================
    # TECHNICAL INDICATORS & RETURNS
    # ==================================================
    df["return_1d"] = grouped["close_price"].pct_change(1)
    df["return_5d"] = grouped["close_price"].pct_change(5)
    df["return_20d"] = grouped["close_price"].pct_change(20)

    df["sma_10"] = grouped["close_price"].transform(lambda x: x.rolling(10).mean())
    df["sma_20"] = grouped["close_price"].transform(lambda x: x.rolling(20).mean())
    df["sma_50"] = grouped["close_price"].transform(lambda x: x.rolling(50).mean())

    df["close_sma10_ratio"] = df["close_price"] / df["sma_10"]
    df["close_sma20_ratio"] = df["close_price"] / df["sma_20"]
    df["close_sma50_ratio"] = df["close_price"] / df["sma_50"]

    df["rsi_14"] = grouped["close_price"].transform(lambda x: calculate_rsi(x, 14))

    # MACD calculations applied per stock
    macd_df = grouped["close_price"].apply(lambda x: pd.DataFrame(index=x.index, data={
        'macd': calculate_macd(x)[0],
        'macd_signal': calculate_macd(x)[1],
        'macd_histogram': calculate_macd(x)[2]
    })).reset_index(level=0, drop=True)
    df[["macd", "macd_signal", "macd_histogram"]] = macd_df

    df["volatility_20"] = grouped["return_1d"].transform(lambda x: x.rolling(20).std())
    df["daily_range"] = (df["price_high"] - df["price_low"]) / df["close_price"]

    # ==================================================
    # VOLUME & TURNOVER RATIOS (Safely fill zeros/NaNs)
    # ==================================================
    volume_sma = grouped["share_volume"].transform(lambda x: x.rolling(20).mean())
    turnover_sma = grouped["turnover"].transform(lambda x: x.rolling(20).mean())
    trade_sma = grouped["trade_volume"].transform(lambda x: x.rolling(20).mean())

    df["volume_ratio"] = (df["share_volume"] / volume_sma).fillna(1.0)
    df["turnover_ratio"] = (df["turnover"] / turnover_sma).fillna(1.0)
    df["trade_volume_ratio"] = (df["trade_volume"] / trade_sma).fillna(1.0)

    # ==================================================
    # FUTURE TARGET & FINAL CLEANUP
    # ==================================================
    df["future_return_5d"] = grouped["close_price"].transform(lambda x: (x.shift(-5) / x) - 1)

    # Replace infinite math glitches with NaN
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Drop rows that don't have historical data or target windows (keeps dataset 100% complete)
    df.dropna(subset=["close_price", "rsi_14", "macd", "future_return_5d"], inplace=True)

    return df


# ==================================================
# PROCESS ALL FILES
# ==================================================

def main():
    csv_files = list(RAW_DIR.glob("*.csv"))
    print(f"\nFound {len(csv_files)} stock data files\n")

    if not csv_files:
        print("No CSV files found.")
        return

    for file in csv_files:
        try:
            print(f"Processing {file.name}...")
            df = pd.read_csv(file)
            
            # Skip empty files safely
            if df.empty:
                print(f"Skipped Empty File -> {file.name}")
                continue

            features_df = build_features(df)

            output_file = PROCESSED_DIR / f"{file.stem}_features.csv"
            features_df.to_csv(output_file, index=False)

            print(f"Saved -> {output_file.name} ({len(features_df)} rows)")

        except Exception as e:
            print(f"FAILED -> {file.name}")
            print(f"Error: {e}")

    print("\nFeature engineering complete.\n")


if __name__ == "__main__":
    main()