"""
SETUP SCRIPT - not part of your pipeline.

This just generates dummy source data so you have something real to point
your ingestion_main.py at:
  1. Seeds a `customers` table in Postgres (your DB source)
  2. Writes `raw/files/orders_history.csv` (your file source)

Run once after `docker compose up -d`:
    python generate_dummy_data.py
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

import psycopg2
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

COUNTRIES = ["Ireland", "United Kingdom", "France", "Germany", "Spain", "Wales"]
# deliberately inconsistent casing/whitespace versions to simulate messy real-world data
COUNTRY_VARIANTS = {
    "Ireland": ["Ireland", "ireland ", " IRELAND"],
    "United Kingdom": ["United Kingdom", "united kingdom", "UK "],
    "France": ["France", "france", " France "],
    "Germany": ["Germany", "germany "],
    "Spain": ["Spain", " spain"],
    "Wales": ["Wales", "wales "],
}

OUTPUT_DIR = Path("raw/files")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def seed_customers(n=50):
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="order_db",
        user="etl_user",
        password="etl_pass",
    )
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE customers")

    rows = []
    for i in range(1, n + 1):
        customer_id = f"CUST{i:04d}"
        name = fake.name()
        country = random.choice(COUNTRIES)
        signup_date = fake.date_between(start_date="-3y", end_date="today")
        rows.append((customer_id, name, country, signup_date))

    cur.executemany(
        "INSERT INTO customers (customer_id, name, country, signup_date) VALUES (%s, %s, %s, %s)",
        rows,
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded {n} rows into Postgres customers table")
    return [r[0] for r in rows]  # return customer_ids for use in orders


def write_orders_csv(customer_ids, n=500, path=OUTPUT_DIR / "orders_history.csv"):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "customer_id", "amount", "country", "created_at"])

        for i in range(1, n + 1):
            order_id = f"ORD{i:05d}"
            customer_id = random.choice(customer_ids)
            country_clean = random.choice(COUNTRIES)
            country = random.choice(COUNTRY_VARIANTS[country_clean])  # messy on purpose
            amount = round(random.uniform(5, 500), 2)
            created_at = (date.today() - timedelta(days=random.randint(0, 365))).isoformat()

            # sprinkle in some data quality problems on purpose
            if random.random() < 0.02:
                order_id = ""  # missing order_id -> should fail a NOT NULL check
            if random.random() < 0.03:
                amount = ""  # missing amount

            writer.writerow([order_id, customer_id, amount, country, created_at])

    print(f"Wrote {n} rows to {path}")


if __name__ == "__main__":
    ids = seed_customers(n=50)
    write_orders_csv(ids, n=500)
    print("Done. Postgres has `customers`, raw/files/ has orders_history.csv")
