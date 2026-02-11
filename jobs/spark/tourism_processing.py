"""
Nexus Data Platform - Spark Processing Job
Transform raw tourism data and generate recommendations
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, avg, count, sum as spark_sum, 
    window, explode, split, regexp_extract, year, month, dayofmonth, lit, current_timestamp
)
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, TimestampType, DoubleType
from datetime import datetime
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# Initialize Spark Session
# ============================================

spark = SparkSession.builder \
    .appName("NexusTourismProcessing") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin123") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")

logger.info("✅ Spark Session initialized")

# ============================================
# Define Schema (shared contract)
# ============================================

SCHEMA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared", "schemas", "event.schema.json")
)

def _json_schema_to_spark(schema: dict) -> StructType:
    type_map = {
        "string": StringType(),
        "integer": IntegerType(),
        "number": DoubleType(),
    }
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    fields = []
    for name in required:
        prop = properties.get(name, {})
        field_type = type_map.get(prop.get("type", "string"), StringType())
        fields.append(StructField(name, field_type, nullable=False))
    return StructType(fields)

def _load_event_schema() -> StructType:
    try:
        with open(SCHEMA_PATH, "r") as schema_file:
            schema = json.load(schema_file)
        return _json_schema_to_spark(schema)
    except Exception as exc:
        logger.warning(f"⚠️  Could not load shared schema: {exc}")
        return StructType([
            StructField("id", StringType()),
            StructField("user_id", IntegerType()),
            StructField("event_type", StringType()),
            StructField("amount", FloatType()),
            StructField("region", StringType()),
            StructField("source", StringType()),
        ])

event_schema = _load_event_schema()

# ============================================
# 1. READ RAW DATA
# ============================================

logger.info("Reading raw tourism events data...")

# In production, read from MinIO
# df_raw = spark.read.json("s3a://data-lake/raw/tourism/*/events.json")

# For demo, create sample data
sample_events = [
    ("1", 101, "booking", 999.99, "VN", "api"),
    ("2", 102, "view", 0.0, "SG", "web"),
    ("3", 103, "booking", 1999.99, "TH", "mobile"),
    ("4", 104, "review", 0.0, "ID", "web"),
    ("5", 105, "booking", 499.99, "VN", "api"),
    ("6", 106, "click", 0.0, "SG", "mobile"),
    ("7", 107, "booking", 1499.99, "TH", "api"),
    ("8", 108, "view", 0.0, "ID", "web"),
]

df_raw = spark.createDataFrame(sample_events, schema=event_schema)

logger.info(f"✅ Loaded {df_raw.count()} raw events")
df_raw.show(5)

# ============================================
# 2. DATA CLEANING
# ============================================

logger.info("Cleaning and transforming data...")

df_clean = df_raw \
    .dropna(subset=['user_id', 'event_type']) \
    .filter(col('amount') >= 0) \
    .withColumn('event_date', current_timestamp()) \
    .withColumn('processed_at', current_timestamp())

logger.info(f"✅ Cleaned {df_clean.count()} records")

# ============================================
# 3. AGGREGATIONS
# ============================================

logger.info("Computing aggregations...")

# Regional metrics
df_regional = df_clean.groupBy('region', 'event_type') \
    .agg(
        count('*').alias('event_count'),
        spark_sum('amount').alias('total_revenue'),
        avg('amount').alias('avg_amount'),
    ) \
    .filter(col('event_count') > 0) \
    .orderBy(col('total_revenue').desc())

logger.info("Regional aggregation:")
df_regional.show()

# User metrics
df_user_metrics = df_clean.groupBy('user_id', 'region') \
    .agg(
        count('*').alias('session_count'),
        spark_sum('amount').alias('total_spent'),
        avg('amount').alias('avg_transaction'),
        spark_sum(
            when(col('event_type') == 'booking', 1).otherwise(0)
        ).alias('purchase_count'),
    )

logger.info("User metrics:")
df_user_metrics.show(5)

# ============================================
# 4. HYBRID RECOMMENDATIONS (Collaborative Filtering)
# ============================================

logger.info("Generating hybrid recommendations...")

# Simple collaborative filtering: similar users + popular tours
popular_tours = df_clean.filter(col('event_type') == 'booking') \
    .groupBy('region') \
    .agg(
        count('*').alias('popularity'),
        avg('amount').alias('avg_price'),
    ) \
    .withColumn('match_score', 
        col('popularity') / (col('popularity').cast('float') + 100)
    )

logger.info("Popular tours by region:")
popular_tours.show()

# ============================================
# 5. DATA QUALITY CHECKS
# ============================================

logger.info("Running data quality checks...")

quality_metrics = {
    'total_records': df_clean.count(),
    'unique_users': df_clean.select('user_id').distinct().count(),
    'regions': df_clean.select('region').distinct().count(),
    'duplicate_rate': (df_raw.count() - df_clean.count()) / df_raw.count() * 100 if df_raw.count() > 0 else 0,
}

logger.info("Data Quality Metrics:")
for metric, value in quality_metrics.items():
    logger.info(f"  {metric}: {value}")

# ============================================
# 6. WRITE RESULTS TO CLICKHOUSE
# ============================================

logger.info("Writing processed data to ClickHouse...")

# Configure ClickHouse connection
clickhouse_jdbc_url = "jdbc:clickhouse://localhost:8123"
clickhouse_user = "admin"
clickhouse_password = "admin123"

try:
    # Write regional metrics
    df_regional.write \
        .format("clickhouse") \
        .mode("append") \
        .option("url", clickhouse_jdbc_url) \
        .option("user", clickhouse_user) \
        .option("password", clickhouse_password) \
        .option("dbtable", "analytics.regional_metrics") \
        .save()
    
    logger.info("✅ Regional metrics written to ClickHouse")
except Exception as e:
    logger.warning(f"⚠️  Could not write to ClickHouse: {e}")
    logger.info("Writing to Parquet instead...")
    
    # Fallback: write to Parquet in MinIO
    df_regional.coalesce(1).write \
        .mode("overwrite") \
        .parquet(f"s3a://data-lake/processed/regional_metrics/{datetime.now().strftime('%Y/%m/%d')}/")
    
    logger.info("✅ Regional metrics written to Parquet")

# ============================================
# 7. SAVE RECOMMENDATIONS
# ============================================

logger.info("Saving recommendations...")

df_recommendations = df_user_metrics.join(
    popular_tours,
    on='region',
    how='left'
) \
    .withColumn('match_score', col('match_score') * 0.75)  # Weight recommendations

# Write to Parquet
df_recommendations.coalesce(1).write \
    .mode("overwrite") \
    .parquet(f"s3a://data-lake/processed/recommendations/{datetime.now().strftime('%Y/%m/%d')}/")

logger.info(f"✅ Saved {df_recommendations.count()} recommendations")

# ============================================
# 8. GENERATE REPORT
# ============================================

logger.info("=" * 50)
logger.info("NEXUS TOURISM PROCESSING - FINAL REPORT")
logger.info("=" * 50)
logger.info(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info(f"Total Events Processed: {df_clean.count()}")
logger.info(f"Unique Users: {quality_metrics['unique_users']}")
logger.info(f"Regions: {quality_metrics['regions']}")
logger.info(f"Total Revenue: ${df_clean.agg(spark_sum('amount')).collect()[0][0]:.2f}")
logger.info(f"Output Location: s3://data-lake/processed/{datetime.now().strftime('%Y/%m/%d')}/")
logger.info("=" * 50)

spark.stop()

logger.info("✅ Spark job completed successfully!")
