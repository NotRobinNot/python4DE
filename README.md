*** 
Note: all detail in this txt file, as well as all of the files found in the 'source_setup' & 'raw' folders, were generated using AI to simply create a starting point with dummy data in various environments that I could begin using for a basic pipeline project with python. Any other files / folders / content have been created by me for the purposes of carrying out a basic python pipeline project.
***

DATA ENGINEERING PIPELINE - ENVIRONMENT SETUP LOG
====================================================
Reference notes for the data-side setup (Postgres, Kafka/Redpanda, dummy
data). Covers what was done, in what order, and every issue hit along the
way with its fix. Keep this with the project folder for future reference.


1. PREREQUISITES INSTALLED
----------------------------------------------------
- Docker Desktop for Mac (docker.com/products/docker-desktop)
- Java via Homebrew: `brew install openjdk@17`
  (required because PySpark runs on the JVM under the hood)
- Python 3.11 via Homebrew: `brew install python@3.11`
  IMPORTANT: PySpark 3.5.1 only officially supports Python up to 3.11.
  macOS's default `python3` was 3.14 (too new), which caused a build
  failure on psycopg2-binary. Fix was to install 3.11 specifically and
  build the venv from that interpreter, not the system default.
- Postgres client tools via Homebrew: `brew install postgresql@16`
  (gives you `pg_config` and `psql` on PATH)


2. PYTHON VIRTUAL ENVIRONMENT
----------------------------------------------------
    python3.11 -m venv .venv
    source .venv/bin/activate
    python --version        # confirm it says 3.11.x, NOT 3.14
    pip install -r requirements.txt

requirements.txt contents:
    pyspark==3.5.1
    faker==26.0.0
    psycopg2-binary==2.9.9
    kafka-python==2.0.2
    pandas==2.2.2


3. PROJECT FOLDER STRUCTURE
----------------------------------------------------
    python_pipeline/
      docker-compose.yml
      requirements.txt
      generate_dummy_data.py
      kafka_producer.py
      postgres-init/
        01_create_customers.sql
      raw/
        files/
          orders_history.csv      (generated, not committed by hand)
      .venv/                      (your virtual environment)
      config.py                   <- your own pipeline code starts here

NOTE: postgres-init/01_create_customers.sql must physically exist inside
postgres-init/ with real content. If you download files individually
through a browser, subfolders can get flattened and the file can end up
missing or in the wrong place - always verify with `ls -la postgres-init/`
before assuming it's there.


4. DOCKER COMPOSE STACK
----------------------------------------------------
Three services: Postgres, Redpanda (Kafka-compatible broker), Redpanda
Console (web UI for inspecting Kafka topics).

Correct working image references (verified via web search - the initial
attempt used a wrong registry domain and stale version tags that no
longer resolve):
    postgres:16
    docker.redpanda.com/redpandadata/redpanda:v26.2.1
    docker.redpanda.com/redpandadata/console:v3.10.0

KAFKA LISTENER FIX (important):
Redpanda needs TWO separate advertised listeners, not one, because it's
accessed from two different network contexts:
  - "internal" listener (redpanda:9092) - used by other containers on the
    same Docker network, e.g. the Redpanda Console container
  - "external" listener (localhost:19092) - used by anything running on
    your actual Mac: your terminal, kafka_producer.py, PySpark, etc.

If you only set one advertised address (e.g. localhost:9092 for
everything), containers other than the broker itself will try to dial
"localhost" meaning themselves, and fail with "connection refused."

Relevant docker-compose.yml command block:
    command:
      - redpanda
      - start
      - --mode=dev-container
      - --smp=1
      - --node-id=0
      - --kafka-addr=internal://0.0.0.0:9092,external://0.0.0.0:19092
      - --advertise-kafka-addr=internal://redpanda:9092,external://localhost:19092
    ports:
      - "19092:19092"
      - "9644:9644"

Result: from your OWN scripts / PySpark, the Kafka bootstrap server is
    localhost:19092
NOT localhost:9092. Port 9092 only exists inside Docker's internal network.


5. BRINGING THE STACK UP
----------------------------------------------------
    docker compose up -d
    docker compose ps          # wait until postgres shows "healthy"

If you ever need to wipe everything and start completely clean (e.g.
after changing postgres-init/ contents, or after a Kafka config change):
    docker compose down -v     # -v removes volumes too, not just containers
    docker compose up -d

IMPORTANT GOTCHA: Postgres only runs the scripts in postgres-init/ the
VERY FIRST TIME it initializes a data volume. If you edit
01_create_customers.sql after the volume already exists, nothing happens
until you `down -v` and `up -d` again to force a fresh init.


6. VERIFYING POSTGRES
----------------------------------------------------
    docker exec -it pipeline-postgres psql -U etl_user -d order_db -c "\dt"

Should list the `customers` table. If it says "Did not find any
relations":
  - Check postgres-init/01_create_customers.sql actually has content:
        ls -la postgres-init/
  - Check what Postgres logged on startup:
        docker compose logs postgres | grep -i init
    Look for "ignoring /docker-entrypoint-initdb.d/*" - that means the
    folder was empty and nothing ran.
  - Fix: recreate the SQL file properly, then `docker compose down -v`
    followed by `docker compose up -d` again.


7. GENERATING DUMMY DATA
----------------------------------------------------
    python generate_dummy_data.py

This does two things in one run:
  - Seeds 50 rows into the Postgres `customers` table (via psycopg2)
  - Writes raw/files/orders_history.csv (500 rows) via plain csv module

The CSV has INTENTIONAL data quality problems baked in on purpose, so
later cleaning/validation scripts have real issues to catch:
  - ~2% of rows have a blank order_id
  - ~3% of rows have a blank amount
  - country values are inconsistently cased/whitespaced
    (e.g. "Ireland", "ireland ", " IRELAND" all appear)

REMEMBER: any time you run `docker compose down -v`, this wipes the
Postgres data AND does not touch the CSV (CSV lives on your host
filesystem, not in a Docker volume) - but if you also delete or regenerate
raw/files/, you'll need to rerun this script for both sources to be
in sync again. When in doubt, just rerun generate_dummy_data.py - it's
idempotent for Postgres (TRUNCATEs before inserting) and simply
overwrites the CSV.


8. POPULATING KAFKA
----------------------------------------------------
    python kafka_producer.py --n 200

Sends 200 simulated live order events (JSON) onto the `order_events`
topic. Options:
    --n <count>      how many events to send (default 100)
    --forever        stream continuously instead of a fixed batch
    --delay <secs>   delay between events when --forever is used (default 1)

Verify in the browser: http://localhost:8080 -> Topics -> order_events
Should list messages with no errors. (Early on this threw a 500 error /
"connection refused" - that was the listener misconfiguration described
in section 4, fixed by adding the internal/external dual listener setup.)


9. SOURCE CONNECTION DETAILS (for config.py)
----------------------------------------------------
Postgres:
    host:     localhost
    port:     5432
    db:       order_db
    user:     etl_user
    password: etl_pass
    table:    customers

Kafka:
    bootstrap servers: localhost:19092
    topic:              order_events

Files:
    path:   raw/files/orders_history.csv
    format: csv
    header: true


10. STATUS AT END OF SETUP
----------------------------------------------------
All three source types confirmed live and populated:
  [x] Postgres `customers` table - 50 rows
  [x] raw/files/orders_history.csv - 500 rows, with intentional dirty data
  [x] Kafka topic `order_events` - 200 messages, visible in Redpanda Console

Ready to begin writing config.py and the rest of the pipeline
(ingestion_main.py, logs.py, data_quality.py, cleaning_data.py, logic.py)
per the original project notes.



----------------------------------------------------
# Data Engineering Pipeline — Environment & Dummy Data

This folder is **infrastructure only**. Nothing in here is the pipeline itself —
that's what you're building in `config.py`, `ingestion_main.py`, `logs.py`,
`data_quality.py`, `cleaning_data.py`, and `logic.py` per your notes.

## What's here

| File | Purpose |
|---|---|
| `docker-compose.yml` | Spins up Postgres + Redpanda (Kafka-compatible broker) + a web UI for Kafka |
| `postgres-init/01_create_customers.sql` | Auto-creates the `customers` table on first Postgres start |
| `requirements.txt` | Python deps: pyspark, faker, psycopg2-binary, kafka-python |
| `generate_dummy_data.py` | Seeds `customers` into Postgres, writes `raw/files/orders_history.csv` |
| `kafka_producer.py` | Streams simulated live order events onto the `order_events` topic |

## Your three source types, mapped

Your notes describe needing to read from files, a database, and Kafka. Here's
what each one is in this setup:

1. **Database source** → Postgres `customers` table (`order_db`, table `customers`)
2. **File source** → `raw/files/orders_history.csv` (historical orders, CSV)
3. **Kafka source** → topic `order_events` (simulated live orders coming in)

This mirrors your `PIPELINE` config draft closely — `database.tables`,
`files.path`, and you'll add a `kafka.topic` key yourself.

Note the CSV data has **intentional problems** baked in (~2% missing
`order_id`, ~3% missing `amount`, inconsistent country casing/whitespace like
`" IRELAND"` vs `"ireland "`). That's deliberate — it gives your
`data_quality.py` and `cleaning_data.py` (Step 2) something real to catch.

## Setup order

```bash
# 1. from this folder, start the containers
docker compose up -d
docker compose ps        # wait until postgres shows "healthy"

# 2. create + activate your venv, install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. generate the dummy data (creates raw/files/orders_history.csv + seeds Postgres)
python generate_dummy_data.py

# 4. send some events onto Kafka
python kafka_producer.py --n 200
```

## Verifying each source works before you start scripting

**Postgres** — connect and check the table exists:
```bash
docker exec -it pipeline-postgres psql -U etl_user -d order_db -c "SELECT * FROM customers LIMIT 5;"
```

**Kafka / Redpanda** — open the console UI in a browser: http://localhost:8080
You should see the `order_events` topic with messages in it once you've run
the producer.

**Files** — just `cat raw/files/orders_history.csv | head` or open it.

**PySpark** — from the activated venv, run `pyspark` in the terminal. You
should land on a `>>>` Spark shell prompt with no errors. Type `exit()` to
leave.

## Connection details (for your config.py)

```
Postgres:
  host: localhost
  port: 5432
  db:   order_db
  user: etl_user
  password: etl_pass
  table: customers

Kafka:
  bootstrap servers: localhost:9092
  topic: order_events

Files:
  path: raw/files/orders_history.csv
  format: csv
  header: true
```

## Docs worth having open while you build

- PySpark DataFrame reader/writer: https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/spark_session.html
- Reading Kafka with Spark: https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html
- Spark JDBC (for the Postgres read): https://spark.apache.org/docs/latest/sql-data-sources-jdbc.html
- Python `logging` module: https://docs.python.org/3/library/logging.html

When you hit a specific step, come back and we'll work through it — what the
Spark JDBC options actually mean, why a for loop over tables is the right
shape here, etc.




