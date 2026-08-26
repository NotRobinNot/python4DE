from pyspark.sql import SparkSession
from config import PIPELINE

file_config = PIPELINE["FILE_CONFIG"]
file_landing = PIPELINE["LOAD_CONFIG"]["fileLand"]

db_config = PIPELINE["DB_CONFIG"]["tables"]
db_url = PIPELINE["DB_CONFIG"]["url"]
db_user = PIPELINE["DB_CONFIG"]["user"]
#aware user info shouldnt be stored static in file like this but just like this for ease w practice
db_pwd = PIPELINE["DB_CONFIG"]["password"]
db_landing = PIPELINE["LOAD_CONFIG"]["dbLand"]

kafka_server = PIPELINE["KAFKA_CONFIG"]["bootstrap_servers"]
kafka_topics = PIPELINE["KAFKA_CONFIG"]["topic"]
kafka_startOffsets = PIPELINE["KAFKA_CONFIG"]["startingOffsets"]
kafka_endOffsets = PIPELINE["KAFKA_CONFIG"]["endingOffsets"]
kafka_landing = PIPELINE["LOAD_CONFIG"]["kafkaLand"]


spark = (SparkSession.builder
         .appName("ingestionMain")
         .config("spark.jars","postgresql-42.7.13.jar")#relative path
         .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1")
         .getOrCreate()
         )

# FILES
for name, path in zip(file_config["name"], file_config["path"]):
    #zip here combines name and path for each in list
    #print(name, path)
    df = spark.read.option("header", "true").csv(path)
    df.write.mode("overwrite").parquet(file_landing)

#df = spark.read.parquet(file_landing_path)
#df.show()
#df.printSchema()

# DATABASE TABLES
for table in db_config:
    df = (
        spark.read
        .format("jdbc")
        .option("url", db_url)
        .option("dbtable", table)
        .option("user", db_user)
        .option("password", db_pwd)
        .option("driver", "org.postgresql.Driver")
        .load()
    )
    df.write.mode("overwrite").parquet(db_landing)
#df.show()
#df.printSchema()

# KAFKA 
for topic in kafka_topics:
    df = (
        spark.read
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_server)
        .option("subscribe", topic)
        .option("startingOffsets", kafka_startOffsets)
        .option("endingOffsets", kafka_endOffsets)
        .load()
    )
    df.write.mode("overwrite").parquet(kafka_landing)
    #df.show()
    #df.printSchema()

spark.stop()