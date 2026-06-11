import json
from kafka import KafkaConsumer
from collections import deque
import statistics


# Rolling window per symbol
WINDOW_SIZE = 10
price_windows = {}


def detect_anomaly(prices):
    """
    Simple z-score style anomaly detection
    """
    if len(prices) < 5:
        return False, 0

    mean = statistics.mean(prices)
    stdev = statistics.stdev(prices)

    latest = prices[-1]

    if stdev == 0:
        return False, mean

    z_score = (latest - mean) / stdev

    return abs(z_score) > 2.5, mean


def run():
    consumer = KafkaConsumer(
        "transactions",
        bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="market-stream-processor",
        value_deserializer=lambda v: json.loads(v.decode("utf-8"))
    )

    print("Stream processor running...")

    for message in consumer:
        tick = message.value

        symbol = tick["symbol"]
        price = tick["price"]

        # Initialize rolling window
        if symbol not in price_windows:
            price_windows[symbol] = deque(maxlen=WINDOW_SIZE)

        price_windows[symbol].append(price)

        # Compute anomaly
        is_anomaly, avg = detect_anomaly(list(price_windows[symbol]))

        # Output enriched stream
        output = {
            "symbol": symbol,
            "price": price,
            "moving_avg": round(avg, 2),
            "is_anomaly": is_anomaly
        }

        if is_anomaly:
            print("🚨 ANOMALY DETECTED:", output)
        else:
            print("OK:", output)


if __name__ == "__main__":
    run()