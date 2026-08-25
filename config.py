PIPELINE = {
    "layer": "landing",
    "run date": "01-01-1234",

    # db level detail
    "database" :{
        "type": "postgres",
        "host": "db.randcomp.internal",
        "port": 5432,
        "database": "orders_db",
        "user": "etl_user",
        "password": "*****",
        "tables": ["orders"]
    },

    # expected file format etc
    "files":{
        "format": "csv",
        # Static from rootproj
        "path": "/data/raw/files/orders_history.csv",
        "header": True
    },

    # output data / landing / orders
    "paths":{
        "output": "/data/landing/files/orders.csv",
    },

    # Full / partial run etc 
    "Load":{
        "mode": "FULL"
    },

    # Data expected format in tables
    "Schemas":{
        "order_id": "string",
        "amount": "decimal(10.2)",
        "country": "string",
        "created_dt": "timestamp"
    },

    # Whats expected in columns
    "Data Quality":{
        "required_columns": ["order_id", "amount", "country", "created_dt"],
        "not_null":["order_id"]
    },
}