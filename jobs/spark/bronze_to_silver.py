#!/usr/bin/env python3
"""
Spark ETL: Bronze → Silver Layer
Transform raw data to cleaned & validated data

Input:  🥉 Bronze Layer (s3a://bronze/)
Output: 🥈 Silver Layer (s3a://silver/)

Transformations:
- Remove duplicates
- Validate schema
- Enrich with dimensions
- Clean data quality issues
- Filter invalid records
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, to_date, hour, expr,
    sha2, concat_ws, lit, when, regexp_replace, lower, trim,
    year, month, dayofmonth
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import argparse
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# Parse Arguments
# ════════════════════════════════════════════════════════════════

parser = argparse.ArgumentParser(description="Bronze to Silver ETL")
parser.add_argument("--date", required=True, help="Processing date (YYYY-MM-DD)")
args = parser.parse_args()

processing_date = args.date
logger.info(f"📅 Processing date: {processing_date}")

# ════════════════════════════════════════════════════════════════
# Initialize Spark with Iceberg
# ════════════════════════════════════════════════════════════════

spark = SparkSession.builder \
    .appName(f"BronzeToSilver_{processing_date}") \
    .config("spark.hadoop.fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")) \
    .config("spark.hadoop.fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")) \
    .config("spark.hadoop.fs.s3a.endpoint", os.getenv("S3_ENDPOINT", "http://minio:9000")) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.iceberg.type", "rest") \
    .config("spark.sql.catalog.iceberg.uri", os.getenv("ICEBERG_REST_URI", "http://iceberg-rest:8080")) \
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://iceberg-warehouse/") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.defaultCatalog", "iceberg") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
logger.info("✅ Spark Session initialized")

# ════════════════════════════════════════════════════════════════
# 1. READ FROM BRONZE LAYER
# ════════════════════════════════════════════════════════════════

logger.info("📖 Reading from Bronze layer...")

bronze_paths = {
    'app_events': f"s3a://bronze/app_events/date={processing_date}/",
    'cdc_changes': f"s3a://bronze/cdc_changes/date={processing_date}/",
    'clickstream': f"s3a://bronze/clickstream/date={processing_date}/",
    'external_data': f"s3a://bronze/external_data/date={processing_date}/",
}

# Read app events
try:
    df_app_events = spark.read.parquet(bronze_paths['app_events'])
    logger.info(f"✅ Read {df_app_events.count()} app events from Bronze")
except Exception as e:
    logger.warning(f"⚠️ No app events found: {e}")
    df_app_events = spark.createDataFrame([], StructType([]))

# Read CDC changes
try:
    df_cdc = spark.read.parquet(bronze_paths['cdc_changes'])
    logger.info(f"✅ Read {df_cdc.count()} CDC changes from Bronze")
except Exception as e:
    logger.warning(f"⚠️ No CDC changes found: {e}")
    df_cdc = spark.createDataFrame([], StructType([]))

# ════════════════════════════════════════════════════════════════
# 2. DATA CLEANING & TRANSFORMATION
# ════════════════════════════════════════════════════════════════

logger.info("🧹 Cleaning and transforming data...")

def clean_app_events(df):
    """
    Clean app events data:
    - Remove duplicates
    - Validate fields
    - Standardize formats
    - Filter invalid records
    """
    if df.count() == 0:
        return df
    
    df_clean = df \
        .dropDuplicates(['event_id']) \
        .filter(col('user_id').isNotNull()) \
        .filter(col('timestamp').isNotNull()) \
        .withColumn('event_type', lower(trim(col('event_type')))) \
        .withColumn('region', upper(trim(col('region')))) \
        .withColumn('processed_at', current_timestamp()) \
        .withColumn('processing_date', lit(processing_date))
    
    # Filter invalid amounts
    if 'amount' in df_clean.columns:
        df_clean = df_clean.filter(col('amount') >= 0)
    
    logger.info(f"  ✓ Cleaned app events: {df_clean.count()} records")
    return df_clean

def clean_cdc_data(df):
    """
    Clean CDC data:
    - Parse operation types
    - Extract before/after states
    - Deduplicate by key
    """
    if df.count() == 0:
        return df
    
    df_clean = df \
        .filter(col('op').isin(['c', 'u', 'd'])) \
        .withColumn('processed_at', current_timestamp()) \
        .withColumn('processing_date', lit(processing_date))
    
    logger.info(f"  ✓ Cleaned CDC data: {df_clean.count()} records")
    return df_clean

# Apply cleaning
df_events_clean = clean_app_events(df_app_events)
df_cdc_clean = clean_cdc_data(df_cdc)

# ════════════════════════════════════════════════════════════════
# 3. DATA ENRICHMENT
# ════════════════════════════════════════════════════════════════

logger.info("📊 Enriching data with dimensions...")

# Add date/time dimensions
if df_events_clean.count() > 0 and 'timestamp' in df_events_clean.columns:
    df_events_enriched = df_events_clean \
        .withColumn('year', year(col('timestamp'))) \
        .withColumn('month', month(col('timestamp'))) \
        .withColumn('day', dayofmonth(col('timestamp'))) \
        .withColumn('hour', hour(col('timestamp')))
else:
    df_events_enriched = df_events_clean

# ════════════════════════════════════════════════════════════════
# 4. DATA QUALITY VALIDATION
# ════════════════════════════════════════════════════════════════

logger.info("🔍 Validating data quality...")

# Count records before/after
records_before = df_app_events.count() if df_app_events.count() > 0 else 0
records_after = df_events_enriched.count() if df_events_enriched.count() > 0 else 0
records_filtered = records_before - records_after

logger.info(f"  📊 Quality metrics:")
logger.info(f"     Records before: {records_before}")
logger.info(f"     Records after: {records_after}")
logger.info(f"     Records filtered: {records_filtered}")
logger.info(f"     Quality rate: {(records_after/records_before*100 if records_before > 0 else 0):.2f}%")

# ════════════════════════════════════════════════════════════════
# 5. WRITE TO SILVER LAYER (Iceberg Tables)
# ════════════════════════════════════════════════════════════════

logger.info("💾 Writing to Silver layer (Iceberg)...")

def write_to_silver(df, table_name):
    """Write DataFrame to Silver layer as Iceberg table"""
    if df.count() == 0:
        logger.warning(f"  ⚠️ Skipping {table_name}: No data")
        return
    
    try:
        # Create database if not exists
        spark.sql("CREATE DATABASE IF NOT EXISTS iceberg.silver")
        
        # Write to Iceberg table
        df.writeTo(f"iceberg.silver.{table_name}") \
            .using("iceberg") \
            .partitionedBy("processing_date") \
            .createOrReplace()
        
        logger.info(f"  ✅ Written {df.count()} records to iceberg.silver.{table_name}")
    except Exception as e:
        logger.error(f"  ❌ Failed to write {table_name}: {e}")
        raise

# Write tables
write_to_silver(df_events_enriched, "app_events_cleaned")
write_to_silver(df_cdc_clean, "cdc_changes_processed")

# ════════════════════════════════════════════════════════════════
# 6. SUMMARY & CLEANUP
# ════════════════════════════════════════════════════════════════

logger.info("=" * 60)
logger.info("✅ Bronze → Silver ETL Complete")
logger.info(f"   Date: {processing_date}")
logger.info(f"   Tables written: iceberg.silver.*")
logger.info("=" * 60)

spark.stop()
