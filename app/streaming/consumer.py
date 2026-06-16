import json
import time
from kafka import KafkaConsumer
from app.db.session import SessionLocal
from app.db.models import MarketTick


def run_consumer():
    print("🔥 Kafka Consumer Starting...")
    
    # Retry until Kafka is ready
    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                "market-ticks",
                bootstrap_servers="kafka:9092",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True
            )
            print("🔥 Kafka Consumer Connected")
        except Exception as e:
            print("⚠️ Waiting for Kafka...", e)
            time.sleep(5)

    db = SessionLocal()
    for msg in consumer:
        data = msg.value
        tick = MarketTick(
            company_id=data.get("company_id"),
            main_type=data.get("main_type"),
            sub_type=data.get("sub_type"),
            short_name=data.get("short_name"),
            trading_date=data.get("trading_date"),
            price_high=data.get("price_high"),
            price_low=data.get("price_low"),
            close_price=data.get("close_price"),
            open_price=data.get("open_price"),
            trade_volume=data.get("trade_volume"),
            share_volume=data.get("share_volume"),
            turnover=data.get("turnover")
        )
        db.add(tick)
        db.commit()
        print("💾 DB WRITE:", data.get("company_id"))
