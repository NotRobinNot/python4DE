PIPELINE = {
    "layer": "landing",
    "run date": "01-01-1234",

    "KAFKA_CONFIG": {
        "bootstrap_servers": "localhost19092",
        "topic": ["order_events"]
    },

    # db level detail
    "DB_CONFIG" :{
        "type": "postgres",
        "host": "localhost",
        "port": 5432,
        "database": "order_db",
        "user": "etl_user",
        "password": "*****",
        "tables": ["customers"],
        "url":"jdbc:postgresql://localhost:5432/order_db"
    },

    # expected file format etc
    "FILE_CONFIG":{
        "name": ["order_history"],
        "format": "csv",
        # Static from rootproj
        "path": ["data/raw/files/orders_history.csv"],
        "header": True
    },

    # output data / landing / orders
    # Full / partial run etc 
    "LOAD_CONFIG":{
        "mode": "FULL",
        "output": "data/landing/csvfiles",
    },

    # Data expected format in tables
    "SCHEMA_CONFIG":{
        "order_id": "string",
        "amount": "decimal(10.2)",
        "country": "string",
        "created_dt": "timestamp"
    },

    # Whats expected in columns
    "DATA_CONFIG":{
        "required_columns": ["order_id", "amount", "country", "created_dt"],
        "not_null":["order_id"]
    }
}