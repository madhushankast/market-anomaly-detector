import json
import time
import random
from datetime import datetime

from kafka import KafkaProducer
from ingestion.schemas import MarketTick


# Connect to Kafka
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(
        v,
        default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o)
    ).encode("utf-8")
)


def generate_tick():
    return MarketTick(
        symbol=random.choice(["AAPL", "TSLA", "GOOG", "AMZN"]),
        price=round(random.uniform(100, 2000), 2),
        volume=random.randint(1, 1000),
        timestamp=datetime.utcnow()
    )


def run():
    topic = "transactions"

    while True:
        tick = generate_tick()

        # Convert to dict + validate
        message = tick.model_dump()

        # Send to Kafka
        producer.send(topic, value=message)

        print(f"Sent: {message}")

        time.sleep(1)


if __name__ == "__main__":
    run()