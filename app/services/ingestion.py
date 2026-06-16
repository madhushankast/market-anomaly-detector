import time
import requests
from app.streaming.producer import publish_tick

TARGET_COMPANIES = ['JKH', 'CCS', 'COMB', 'CONN', 'LLUB', 'LIOC']

def fetch_cse_data():
    try:
        # Based on user description, endpoints are POST with form-urlencoded
        # We will use todaySharePrice as it seems to provide daily details.
        url = "https://www.cse.lk/api/tradeSummary"
        # If it needs payload, typically empty or specific params. Assuming empty for all securities.
        response = requests.post(url, data={})
        
        # If API gives JSON response, we parse it
        if response.status_code == 200:
            data = response.json()
            return data.get("reqTradeSummery", []) if isinstance(data, dict) else data
        else:
            print(f"⚠️ CSE API returned status {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Failed to fetch CSE data: {e}")
        return []

def safe_float(val):
    try:
        if val is None or val == '': return 0.0
        if isinstance(val, str):
            val = val.replace(',', '')
        return float(val)
    except:
        return 0.0

def safe_int(val):
    try:
        if val is None or val == '': return 0
        if isinstance(val, str):
            val = val.replace(',', '')
        return int(float(val))
    except:
        return 0

def run_ingestion_loop():
    print("🔥 CSE API Producer Running")

    while True:
        data = fetch_cse_data()
        items = data if isinstance(data, list) else data.get("reqTodaySharePrice", []) or data.get("data", []) or []
        
        for item in items:
            # Check for the company ID, might be 'COMPANY ID', 'symbol', or similar.
            raw_symbol = item.get("symbol", "")
            company_id = raw_symbol.split('.')[0] if '.' in raw_symbol else raw_symbol
            
            if company_id in TARGET_COMPANIES:
                payload = {
                    "company_id": company_id,
                    "main_type": "",
                    "sub_type": "",
                    "short_name": item.get("name", ""),
                    "trading_date": str(item.get("lastTradedTime", "")),
                    "price_high": safe_float(item.get("high", 0)),
                    "price_low": safe_float(item.get("low", 0)),
                    "close_price": safe_float(item.get("closingPrice", 0)),
                    "open_price": safe_float(item.get("open", 0)),
                    "trade_volume": safe_int(item.get("tradevolume", 0)),
                    "share_volume": safe_int(item.get("sharevolume", 0)),
                    "turnover": safe_float(item.get("turnover", 0))
                }

                print("📤 PRODUCE:", payload["company_id"])
                try:
                    publish_tick(payload)
                except Exception as e:
                    print(f"⚠️ Failed to publish tick for {company_id}: {e}")

        time.sleep(60)