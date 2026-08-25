from pyspark.sql import SparkSession
from config import PIPELINE

file_config = PIPELINE["FILE_CONFIG"]
file_landing_path = PIPELINE["LOAD_CONFIG"]["output"]

db_config = PIPELINE["DB_CONFIG"]["tables"]
db_url = PIPELINE["DB_CONFIG"]["url"]
db_user = PIPELINE["DB_CONFIG"]["user"]
#aware user info shouldnt be stored static in file like this but just like this for ease w practice
db_pwd = PIPELINE["DB_CONFIG"]["password"]

spark = (SparkSession.builder
         .appName("ingestionMain")
         .config("spark.jars","postgresql-42.7.13.jar")#relative path
         .getOrCreate()
         )

# FILES
for name, path in zip(file_config["name"], file_config["path"]):
    #zip here combines name and path for each in list
    #print(name, path)
    df = spark.read.option("header", "true").csv(path)
    df.write.mode("overwrite").parquet(file_landing_path)

df = spark.read.parquet(file_landing_path)
df.show()
df.printSchema()

# DATABASE TABLES
for table in db_config:
    df = (
        spark.read
        .format("jdbc")
        .option("url", db_url)
        .option("dbtable", table)
        .option("user", db_user)
        .option("password", db_pwd)
        .load()
    )


df.show()
df.printSchema()

spark.stop()