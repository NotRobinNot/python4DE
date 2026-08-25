-- This runs automatically the first time the postgres container starts
-- (postgres docker images execute anything in /docker-entrypoint-initdb.d on init)

CREATE TABLE IF NOT EXISTS customers (
    customer_id   VARCHAR(10) PRIMARY KEY,
    name          VARCHAR(100),
    country       VARCHAR(50),
    signup_date   DATE
);
