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
import argparse
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# Initialize Spark Session
# ============================================

parser = argparse.ArgumentParser(description="Nexus Tourism Spark Processing")
parser.add_argument("--input", dest="input_path", default=os.getenv("RAW_INPUT_PATH"))
parser.add_argument("--output", dest="output_path", default=os.getenv("PROCESSED_OUTPUT_PATH"))
args = parser.parse_args()

input_path = args.input_path or "s3a://data-lake/raw/tourism/*/events.json"
output_path = args.output_path or f"s3a://data-lake/processed/tourism/events/{datetime.now().strftime('%Y/%m/%d')}/"

s3_endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
s3_access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
s3_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")

spark = SparkSession.builder \
    .appName("NexusTourismProcessing") \
    .config("spark.hadoop.fs.s3a.access.key", s3_access_key) \
    .config("spark.hadoop.fs.s3a.secret.key", s3_secret_key) \
    .config("spark.hadoop.fs.s3a.endpoint", s3_endpoint) \
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

SCHEMA_PATH = os.getenv(
    "EVENT_SCHEMA_PATH",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared", "schemas", "event.schema.json")
    ),
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
logger.info(f"Input path: {input_path}")

df_raw = spark.read.json(input_path)

if 'records' in df_raw.columns:
    df_events = df_raw.select(
        col('source').alias('source_name'),
        explode(col('records')).alias('record')
    ).select(
        col('record.id').alias('id'),
        col('record.user_id').cast('int').alias('user_id'),
        col('record.event_type').alias('event_type'),
        col('record.amount').cast('double').alias('amount'),
        col('record.region').alias('region'),
        col('record.source').alias('source')
    )
else:
    df_events = df_raw

df_events = df_events.filter(col('id').isNotNull())
logger.info(f"✅ Loaded {df_events.count()} raw events")

# ============================================
# 2. DATA CLEANING
# ============================================

logger.info("Cleaning and transforming data...")

df_clean = df_events \
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

logger.info("Writing processed data to MinIO...")

df_clean.coalesce(1).write \
    .mode("overwrite") \
    .json(output_path)

logger.info(f"✅ Processed events written to {output_path}")

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
total_revenue = df_clean.agg(spark_sum('amount')).collect()[0][0] or 0.0
logger.info(f"Total Revenue: ${total_revenue:.2f}")
logger.info(f"Output Location: {output_path}")
logger.info("=" * 50)

spark.stop()

logger.info("✅ Spark job completed successfully!")
