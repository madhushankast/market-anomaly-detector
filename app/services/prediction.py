import os
import requests
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy import desc

from ml.src.predict import generate_live_signals
from app.db.session import SessionLocal
from app.db.models import MarketTick

TARGET_COMPANIES = ['JKH', 'CCS', 'COMB', 'CONN', 'LLUB', 'LIOC']

class PredictionService:
    _cached_signals: Optional[List[Dict[str, Any]]] = None

    @staticmethod
    def get_recent_db_ticks(company_id: str, since_dt: pd.Timestamp) -> List[MarketTick]:
        db = SessionLocal()
        try:
            rows = (
                db.query(MarketTick)
                .filter(MarketTick.company_id == company_id)
                .filter(MarketTick.timestamp >= since_dt)
                .order_by(MarketTick.timestamp.asc())
                .all()
            )
            return rows
        except Exception as e:
            print(f"⚠️ DB query failed for {company_id}: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def fetch_live_tick_api(symbol: str) -> Optional[dict]:
        url = "https://www.cse.lk/api/companyInfoSummery"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.cse.lk/",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        # Standard format is SYMBOL.N0000
        payload = {"symbol": f"{symbol}.N0000"}
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                res_json = response.json()
                info = res_json.get("reqSymbolInfo", {})
                if info:
                    return info
        except Exception as e:
            print(f"⚠️ API fetch failed for {symbol}: {e}")
        return None

    @classmethod
    def get_hybrid_series(cls, symbol: str) -> pd.DataFrame:
        # 1. Load CSV data
        csv_path = Path(f"d:/Projects/2026.06.11 market-anomaly-detector/market-anomaly-detector/ml/data/raw/{symbol}_all_years.csv")
        if not csv_path.exists():
            print(f"⚠️ CSV not found for {symbol} at {csv_path}")
            return pd.DataFrame()
            
        df_csv = pd.read_csv(csv_path)
        
        # Clean and rename columns
        rename_mapping = {
            "COMPANY ID": "company_id",
            "MAIN TYPE": "main_type",
            "SUB TYPE": "sub_type",
            "SHORT NAME": "short_name",
            "TRADING DATE": "trading_date",
            "PRICE HIGH (Rs.)": "price_high",
            "PRICE LOW (Rs.)": "price_low",
            "CLOSE PRICE (Rs.)": "close_price",
            "OPEN PRICE (Rs.)": "open_price",
            "TRADE VOLUME (No.)": "trade_volume",
            "SHARE VOLUME (No.)": "share_volume",
            "TURNOVER (Rs.)": "turnover"
        }
        df_csv = df_csv.rename(columns=rename_mapping)
        df_csv.columns = df_csv.columns.str.lower().str.replace(' ', '_')
        
        # Drop rows that don't have a valid date
        df_csv = df_csv.dropna(subset=["trading_date"])
        df_csv["trading_date"] = pd.to_datetime(df_csv["trading_date"])
        df_csv = df_csv.sort_values("trading_date").reset_index(drop=True)
        
        # Clean and convert numeric columns
        numeric_cols = [
            "open_price", "close_price", "price_high", "price_low",
            "trade_volume", "share_volume", "turnover"
        ]
        for col in numeric_cols:
            if col in df_csv.columns:
                df_csv[col] = df_csv[col].astype(str).str.replace(r'[^\d\.]', '', regex=True)
                df_csv[col] = pd.to_numeric(df_csv[col], errors="coerce")
                df_csv[col] = df_csv[col].fillna(0.0)
                
        # Keep last 100 entries for warm-up
        df_csv = df_csv.tail(100).copy()
        
        # 2. Query recent ticks from database
        last_csv_date = df_csv["trading_date"].max()
        db_ticks = cls.get_recent_db_ticks(symbol, last_csv_date)
        
        if db_ticks:
            # Convert DB ticks to DataFrame
            ticks_data = []
            for tick in db_ticks:
                ticks_data.append({
                    "company_id": tick.company_id,
                    "main_type": tick.main_type,
                    "sub_type": tick.sub_type,
                    "short_name": tick.short_name,
                    "trading_date": tick.trading_date,
                    "price_high": tick.price_high,
                    "price_low": tick.price_low,
                    "close_price": tick.close_price,
                    "open_price": tick.open_price,
                    "trade_volume": tick.trade_volume,
                    "share_volume": tick.share_volume,
                    "turnover": tick.turnover,
                    "timestamp": tick.timestamp
                })
            df_ticks = pd.DataFrame(ticks_data)
            
            # Aggregate ticks by date
            df_ticks["date"] = df_ticks["timestamp"].dt.date
            df_daily_ticks = df_ticks.sort_values("timestamp").groupby("date").last().reset_index()
            
            # Format columns to match df_csv
            df_daily_ticks["trading_date"] = pd.to_datetime(df_daily_ticks["date"])
            df_daily_ticks = df_daily_ticks.drop(columns=["date", "timestamp"])
            
            # Concat CSV and daily ticks
            min_tick_date = df_daily_ticks["trading_date"].min()
            df_csv = df_csv[df_csv["trading_date"] < min_tick_date]
            df_merged = pd.concat([df_csv, df_daily_ticks], ignore_index=True)
        else:
            df_merged = df_csv.copy()
            
        # 3. Fetch absolute latest live tick from CSE API for today
        live_tick = cls.fetch_live_tick_api(symbol)
        if live_tick:
            today_date = pd.to_datetime(pd.Timestamp.now().date())
            
            live_row = {
                "company_id": symbol,
                "main_type": "N",
                "sub_type": "0",
                "short_name": live_tick.get("name", symbol),
                "trading_date": today_date,
                "price_high": float(live_tick.get("hiTrade") or live_tick.get("lastTradedPrice") or 0.0),
                "price_low": float(live_tick.get("lowTrade") or live_tick.get("lastTradedPrice") or 0.0),
                "close_price": float(live_tick.get("lastTradedPrice") or 0.0),
                "open_price": float(live_tick.get("previousClose") or live_tick.get("lastTradedPrice") or 0.0),
                "trade_volume": int(live_tick.get("tdyTradeVolume") or 0),
                "share_volume": int(live_tick.get("tdyShareVolume") or 0),
                "turnover": float(live_tick.get("tdyTurnover") or 0.0)
            }
            
            # Append or update today's row in df_merged
            if not df_merged.empty and df_merged.loc[df_merged.index[-1], "trading_date"] == today_date:
                for k, v in live_row.items():
                    df_merged.loc[df_merged.index[-1], k] = v
            else:
                df_merged = pd.concat([df_merged, pd.DataFrame([live_row])], ignore_index=True)
                
        df_merged = df_merged.sort_values("trading_date").reset_index(drop=True)
        return df_merged

    @staticmethod
    def compute_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        close = df["close_price"]
        
        df["return_1d"] = close.pct_change(1)
        df["return_5d"] = close.pct_change(5)
        df["return_20d"] = close.pct_change(20)

        df["sma_10"] = close.rolling(10).mean()
        df["sma_20"] = close.rolling(20).mean()
        df["sma_50"] = close.rolling(50).mean()

        df["close_sma10_ratio"] = close / df["sma_10"]
        df["close_sma20_ratio"] = close / df["sma_20"]
        df["close_sma50_ratio"] = close / df["sma_50"]

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df["rsi_14"] = 100 - (100 / (1 + rs))

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        df["volatility_20"] = df["return_1d"].rolling(20).std()

        share_vol_sma = df["share_volume"].rolling(20).mean()
        df["volume_ratio"] = (df["share_volume"] / share_vol_sma).fillna(1.0)
        df["volume_ratio"] = df["volume_ratio"].replace([np.inf, -np.inf], 1.0)

        turnover_sma = df["turnover"].rolling(20).mean()
        df["turnover_ratio"] = (df["turnover"] / turnover_sma).fillna(1.0)
        df["turnover_ratio"] = df["turnover_ratio"].replace([np.inf, -np.inf], 1.0)

        trade_vol_sma = df["trade_volume"].rolling(20).mean()
        df["trade_volume_ratio"] = (df["trade_volume"] / trade_vol_sma).fillna(1.0)
        df["trade_volume_ratio"] = df["trade_volume_ratio"].replace([np.inf, -np.inf], 1.0)
        
        return df

    @classmethod
    def get_live_signals(cls, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get live trading signals. Uses cached signals if available unless force_refresh is True.
        """
        if cls._cached_signals is not None and not force_refresh:
            return cls._cached_signals

        try:
            print("🔄 Computing live features dynamically for target companies...")
            target_rows = []
            for symbol in TARGET_COMPANIES:
                df_series = cls.get_hybrid_series(symbol)
                if df_series.empty or len(df_series) < 50:
                    print(f"⚠️ Insufficient history for {symbol}, row count: {len(df_series)}")
                    continue
                
                df_features = cls.compute_features(df_series)
                last_row = df_features.tail(1).copy()
                target_rows.append(last_row)
                
            if not target_rows:
                raise ValueError("No stock features could be calculated.")
                
            df_live = pd.concat(target_rows, ignore_index=True)
            df_signals = generate_live_signals(df_live)
            
            if df_signals is None or df_signals.empty:
                raise ValueError("Prediction engine returned empty signals.")
                
            if "trading_date" in df_signals.columns:
                df_signals["trading_date"] = df_signals["trading_date"].astype(str)
                
            cls._cached_signals = df_signals.to_dict(orient="records")
            print(f"✅ Live predictions successfully calculated for {len(cls._cached_signals)} companies.")
            return cls._cached_signals
            
        except Exception as e:
            print(f"❌ Real-time signal generation failed: {e}. Falling back to CSV cache.")
            df_fallback = generate_live_signals(df=None)
            if df_fallback is not None and not df_fallback.empty:
                if "trading_date" in df_fallback.columns:
                    df_fallback["trading_date"] = df_fallback["trading_date"].astype(str)
                cls._cached_signals = df_fallback.to_dict(orient="records")
                return cls._cached_signals
            
            cls._cached_signals = []
            return cls._cached_signals

    @classmethod
    def run_prediction(cls) -> List[Dict[str, Any]]:
        """
        Manually trigger the prediction engine and refresh the cache.
        """
        return cls.get_live_signals(force_refresh=True)
