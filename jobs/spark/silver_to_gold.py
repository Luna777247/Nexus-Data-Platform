#!/usr/bin/env python3
"""
Spark ETL: Silver → Gold Layer
Create business-level aggregations and analytics tables

Input:  🥈 Silver Layer (iceberg.silver.*)
Output: 🥇 Gold Layer (iceberg.gold.*)

Business Tables:
- user_360_view: Complete user profile with behavior
- booking_metrics: Booking analytics & KPIs
- tourism_analytics: Regional tourism statistics
- recommendation_features: ML features for recommendations
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, max as spark_max, min as spark_min,
    current_timestamp, to_date, datediff, lit, concat_ws,
    collect_list, struct, explode, when, coalesce
)
from pyspark.sql.window import Window
import argparse
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# Parse Arguments
# ════════════════════════════════════════════════════════════════

parser = argparse.ArgumentParser(description="Silver to Gold ETL")
parser.add_argument("--date", required=True, help="Processing date (YYYY-MM-DD)")
args = parser.parse_args()

processing_date = args.date
logger.info(f"📅 Processing date: {processing_date}")

# ════════════════════════════════════════════════════════════════
# Initialize Spark with Iceberg
# ════════════════════════════════════════════════════════════════

spark = SparkSession.builder \
    .appName(f"SilverToGold_{processing_date}") \
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
# 1. READ FROM SILVER LAYER
# ════════════════════════════════════════════════════════════════

logger.info("📖 Reading from Silver layer...")

try:
    df_events = spark.read.table("iceberg.silver.app_events_cleaned")
    logger.info(f"✅ Read {df_events.count()} events from Silver")
except Exception as e:
    logger.warning(f"⚠️ No events found in Silver: {e}")
    df_events = None

# ════════════════════════════════════════════════════════════════
# 2. CREATE GOLD TABLES
# ════════════════════════════════════════════════════════════════

logger.info("🏗️ Creating Gold layer aggregations...")

# Create database
spark.sql("CREATE DATABASE IF NOT EXISTS iceberg.gold")

# ───────────────────────────────────────────────────────────────
# GOLD TABLE 1: User 360 View
# ───────────────────────────────────────────────────────────────

if df_events and df_events.count() > 0:
    logger.info("📊 Creating user_360_view...")
    
    df_user_360 = df_events \
        .groupBy("user_id") \
        .agg(
            count("*").alias("total_events"),
            count(when(col("event_type") == "click", 1)).alias("total_clicks"),
            count(when(col("event_type") == "booking", 1)).alias("total_bookings"),
            count(when(col("event_type") == "search", 1)).alias("total_searches"),
            spark_sum(coalesce(col("amount"), lit(0))).alias("total_spent"),
            avg(coalesce(col("amount"), lit(0))).alias("avg_transaction_value"),
            collect_list("region").alias("visited_regions"),
            spark_max("timestamp").alias("last_activity_date"),
            spark_min("timestamp").alias("first_activity_date")
        ) \
        .withColumn("processing_date", lit(processing_date)) \
        .withColumn("processed_at", current_timestamp())
    
    # Write to Gold
    df_user_360.writeTo("iceberg.gold.user_360_view") \
        .using("iceberg") \
        .partitionedBy("processing_date") \
        .createOrReplace()
    
    logger.info(f"  ✅ Written {df_user_360.count()} users to user_360_view")

# ───────────────────────────────────────────────────────────────
# GOLD TABLE 2: Booking Metrics
# ───────────────────────────────────────────────────────────────

if df_events and df_events.count() > 0:
    logger.info("📊 Creating booking_metrics...")
    
    df_bookings = df_events.filter(col("event_type") == "booking")
    
    if df_bookings.count() > 0:
        df_booking_metrics = df_bookings \
            .groupBy("region", "processing_date") \
            .agg(
                count("*").alias("total_bookings"),
                spark_sum(coalesce(col("amount"), lit(0))).alias("total_revenue"),
                avg(coalesce(col("amount"), lit(0))).alias("avg_booking_value"),
                spark_max(coalesce(col("amount"), lit(0))).alias("max_booking_value"),
                spark_min(coalesce(col("amount"), lit(0))).alias("min_booking_value"),
                count("user_id").alias("unique_users")
            ) \
            .withColumn("processed_at", current_timestamp())
        
        # Write to Gold
        df_booking_metrics.writeTo("iceberg.gold.booking_metrics") \
            .using("iceberg") \
            .partitionedBy("processing_date") \
            .createOrReplace()
        
        logger.info(f"  ✅ Written {df_booking_metrics.count()} booking metrics")

# ───────────────────────────────────────────────────────────────
# GOLD TABLE 3: Tourism Analytics (Regional Statistics)
# ───────────────────────────────────────────────────────────────

if df_events and df_events.count() > 0:
    logger.info("📊 Creating tourism_analytics...")
    
    df_tourism = df_events \
        .groupBy("region", "event_type", "processing_date") \
        .agg(
            count("*").alias("event_count"),
            count("user_id").alias("unique_users")
        ) \
        .withColumn("processed_at", current_timestamp())
    
    # Pivot by event type for easier analysis
    df_tourism_pivot = df_tourism \
        .groupBy("region", "processing_date") \
        .pivot("event_type") \
        .agg(spark_sum("event_count")) \
        .na.fill(0)
    
    # Write to Gold
    df_tourism_pivot.writeTo("iceberg.gold.tourism_analytics") \
        .using("iceberg") \
        .partitionedBy("processing_date") \
        .createOrReplace()
    
    logger.info(f"  ✅ Written {df_tourism_pivot.count()} tourism analytics")

# ───────────────────────────────────────────────────────────────
# GOLD TABLE 4: Recommendation Features (ML Ready)
# ───────────────────────────────────────────────────────────────

if df_events and df_events.count() > 0:
    logger.info("📊 Creating recommendation_features...")
    
    # Calculate user behavior features for ML
    df_features = df_events \
        .groupBy("user_id") \
        .agg(
            # Engagement features
            count("*").alias("total_interactions"),
            count(when(col("event_type") == "click", 1)).alias("clicks"),
            count(when(col("event_type") == "booking", 1)).alias("bookings"),
            count(when(col("event_type") == "search", 1)).alias("searches"),
            
            # Financial features
            spark_sum(coalesce(col("amount"), lit(0))).alias("total_spend"),
            avg(coalesce(col("amount"), lit(0))).alias("avg_spend"),
            
            # Behavioral features
            count("region").alias("region_diversity"),
            
            # Recency features
            datediff(lit(processing_date), spark_max("timestamp")).alias("days_since_last_activity")
        ) \
        .withColumn("processing_date", lit(processing_date)) \
        .withColumn("processed_at", current_timestamp())
    
    # Calculate conversion rate
    df_features = df_features \
        .withColumn(
            "conversion_rate",
            when(col("total_interactions") > 0,
                 col("bookings") / col("total_interactions")
            ).otherwise(0)
        )
    
    # Write to Gold
    df_features.writeTo("iceberg.gold.recommendation_features") \
        .using("iceberg") \
        .partitionedBy("processing_date") \
        .createOrReplace()
    
    logger.info(f"  ✅ Written {df_features.count()} recommendation features")

# ───────────────────────────────────────────────────────────────
# GOLD TABLE 5: Daily Summary
# ───────────────────────────────────────────────────────────────

if df_events and df_events.count() > 0:
    logger.info("📊 Creating daily_summary...")
    
    df_summary = df_events \
        .groupBy("processing_date") \
        .agg(
            count("*").alias("total_events"),
            count("user_id").alias("unique_users"),
            count(when(col("event_type") == "booking", 1)).alias("bookings"),
            spark_sum(coalesce(col("amount"), lit(0))).alias("revenue"),
            count("region").alias("regions_active")
        ) \
        .withColumn("processed_at", current_timestamp())
    
    # Write to Gold
    df_summary.writeTo("iceberg.gold.daily_summary") \
        .using("iceberg") \
        .partitionedBy("processing_date") \
        .createOrReplace()
    
    logger.info(f"  ✅ Written daily summary")

# ════════════════════════════════════════════════════════════════
# 3. SUMMARY & CLEANUP
# ════════════════════════════════════════════════════════════════

logger.info("=" * 60)
logger.info("✅ Silver → Gold ETL Complete")
logger.info(f"   Date: {processing_date}")
logger.info("   Gold Tables Created:")
logger.info("     • iceberg.gold.user_360_view")
logger.info("     • iceberg.gold.booking_metrics")
logger.info("     • iceberg.gold.tourism_analytics")
logger.info("     • iceberg.gold.recommendation_features")
logger.info("     • iceberg.gold.daily_summary")
logger.info("=" * 60)

spark.stop()
