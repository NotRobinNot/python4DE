"""
SETUP SCRIPT - not part of your pipeline.

Simulates a live stream of new order events onto the `order_events` Kafka
topic, so your ingestion_main.py has a real streaming source to read from
(via spark.read.format("kafka")... or spark.readStream for later).

Run after `docker compose up -d`:
    python kafka_producer.py            # sends 100 events then exits
    python kafka_producer.py --forever  # sends one event every second, forever
"""

import argparse
import json
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

COUNTRIES = ["Ireland", "United Kingdom", "France", "Germany", "Spain", "Wales"]

producer = KafkaProducer(
    bootstrap_servers="localhost:19092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def make_event():
    return {
        "order_id": f"EVT{uuid.uuid4().hex[:8].upper()}",
        "customer_id": f"CUST{random.randint(1, 50):04d}",
        "amount": round(random.uniform(5, 500), 2),
        "country": random.choice(COUNTRIES),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def run(n_events, forever, delay_seconds):
    sent = 0
    while forever or sent < n_events:
        event = make_event()
        producer.send("order_events", value=event)
        sent += 1
        if forever:
            time.sleep(delay_seconds)
    producer.flush()
    print(f"Sent {sent} events to topic 'order_events'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100, help="number of events to send")
    parser.add_argument("--forever", action="store_true", help="stream continuously")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between events when --forever")
    args = parser.parse_args()

    run(args.n, args.forever, args.delay)
