#!/usr/bin/env python3
"""
Gold → ClickHouse Sync Job
Sync aggregated Gold layer tables to ClickHouse for analytics

Input:  🥇 Gold Layer (iceberg.gold.*)
Output: ClickHouse tables (analytics.*)
"""

from pyspark.sql import SparkSession
import argparse
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# Parse Arguments
# ════════════════════════════════════════════════════════════════

parser = argparse.ArgumentParser(description="Gold to ClickHouse Sync")
parser.add_argument("--date", required=True, help="Processing date (YYYY-MM-DD)")
args = parser.parse_args()

processing_date = args.date
logger.info(f"📅 Syncing Gold → ClickHouse for date: {processing_date}")

# ════════════════════════════════════════════════════════════════
# Initialize Spark with Iceberg
# ════════════════════════════════════════════════════════════════

spark = SparkSession.builder \
    .appName(f"GoldToClickHouse_{processing_date}") \
    .config("spark.hadoop.fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")) \
    .config("spark.hadoop.fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")) \
    .config("spark.hadoop.fs.s3a.endpoint", os.getenv("S3_ENDPOINT", "http://minio:9000")) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.iceberg.type", "rest") \
    .config("spark.sql.catalog.iceberg.uri", os.getenv("ICEBERG_REST_URI", "http://iceberg-rest:8080")) \
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://iceberg-warehouse/") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.defaultCatalog", "iceberg") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
logger.info("✅ Spark Session initialized")

# ClickHouse connection
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT", "8123")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DATABASE", "analytics")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "admin")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "admin123")

clickhouse_url = f"jdbc:clickhouse://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/{CLICKHOUSE_DB}"

logger.info(f"🔗 ClickHouse connection: {clickhouse_url}")

# ════════════════════════════════════════════════════════════════
# Read Gold Tables and Write to ClickHouse
# ════════════════════════════════════════════════════════════════

gold_tables = [
    "user_360_view",
    "booking_metrics",
    "tourism_analytics",
    "recommendation_features",
    "daily_summary"
]

for table_name in gold_tables:
    try:
        logger.info(f"📊 Syncing {table_name}...")
        
        # Read from Gold (Iceberg)
        df = spark.read.table(f"iceberg.gold.{table_name}") \
            .filter(f"processing_date = '{processing_date}'")
        
        record_count = df.count()
        
        if record_count == 0:
            logger.warning(f"  ⚠️ No data for {table_name} on {processing_date}")
            continue
        
        # Write to ClickHouse
        df.write \
            .format("jdbc") \
            .option("url", clickhouse_url) \
            .option("dbtable", table_name) \
            .option("user", CLICKHOUSE_USER) \
            .option("password", CLICKHOUSE_PASSWORD) \
            .option("driver", "ru.yandex.clickhouse.ClickHouseDriver") \
            .mode("append") \
            .save()
        
        logger.info(f"  ✅ Synced {record_count} records to analytics.{table_name}")
        
    except Exception as e:
        logger.error(f"  ❌ Failed to sync {table_name}: {e}")

# ════════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════════

logger.info("=" * 60)
logger.info("✅ Gold → ClickHouse Sync Complete")
logger.info(f"   Date: {processing_date}")
logger.info(f"   ClickHouse Database: {CLICKHOUSE_DB}")
logger.info("=" * 60)

spark.stop()
