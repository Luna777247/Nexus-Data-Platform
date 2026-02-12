#!/usr/bin/env python3
"""
Spark Structured Streaming Job - Extensible Kafka Ingestion
Location: spark/kafka_streaming_job.py

Purpose:
- Subscribe to all Kafka topics matching pattern: topic_*
- No code changes needed when adding new sources
- Stream → Validate → Write to Iceberg lakehouse
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, get_json_object, current_timestamp,
    window, explode, lit, when
)
from pyspark.sql.types import StructType, StructField, StringType, MapType
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# Initialize Spark Session with Iceberg
# ============================================

spark = SparkSession.builder \
    .appName("KafkaStreamingToIceberg") \
    .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "minioadmin")) \
    .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "minioadmin123")) \
    .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT", "http://minio:9000")) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.iceberg.type", "rest") \
    .config("spark.sql.catalog.iceberg.uri", os.getenv("ICEBERG_REST_URI", "http://iceberg-rest:8080")) \
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://iceberg-warehouse/") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.defaultCatalog", "iceberg") \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")
logger.info("✅ Spark Session initialized with Iceberg support")

# ============================================
# Kafka Configuration
# ============================================

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_SUBSCRIBE_PATTERN = "topic_.*"  # Matches: topic_user_events, topic_booking_events, etc.
ICEBERG_NAMESPACE = "tourism_db"
CHECKPOINT_LOCATION = "s3a://iceberg-warehouse/_checkpoints/kafka_stream"

logger.info(f"📡 Kafka Configuration:")
logger.info(f"   Bootstrap Servers: {KAFKA_BOOTSTRAP_SERVERS}")
logger.info(f"   Subscribe Pattern: {KAFKA_SUBSCRIBE_PATTERN}")
logger.info(f"   Iceberg Namespace: {ICEBERG_NAMESPACE}")

# ============================================
# Define Kafka Message Schema
# ============================================

kafka_message_schema = StructType([
    StructField("source_id", StringType(), True),
    StructField("source_name", StringType(), True),
    StructField("ingestion_timestamp", StringType(), True),
    StructField("data", MapType(StringType(), StringType(), True), True),  # Flexible data field
])

# ============================================
# Read from Kafka with Pattern Matching
# ============================================

logger.info(f"\n🔄 Starting Kafka stream subscription with pattern: {KAFKA_SUBSCRIBE_PATTERN}")

df_kafka = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribePattern", KAFKA_SUBSCRIBE_PATTERN) \
    .option("startingOffsets", "latest") \
    .option("maxOffsetsPerTrigger", 10000) \
    .option("failOnDataLoss", "false") \
    .load()

logger.info("✅ Kafka stream created (waiting for data)")

# ============================================
# Parse and Transform Stream
# ============================================

df_parsed = df_kafka \
    .select(
        col("topic").alias("kafka_topic"),
        col("partition"),
        col("offset"),
        col("timestamp").alias("kafka_timestamp"),
        from_json(col("value").cast("string"), kafka_message_schema).alias("message")
    ) \
    .select(
        "kafka_topic",
        "partition",
        "offset",
        "kafka_timestamp",
        col("message.source_id"),
        col("message.source_name"),
        col("message.ingestion_timestamp"),
        col("message.data").alias("raw_data"),
    ) \
    .withColumn("processed_timestamp", current_timestamp()) \
    .withColumn("batch_id", lit(f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"))

# ============================================
# Data Quality Checks
# ============================================

df_validated = df_parsed \
    .withColumn(
        "is_valid",
        when(
            (col("source_id").isNotNull()) & 
            (col("raw_data").isNotNull()) &
            (col("ingestion_timestamp").isNotNull()),
            True
        ).otherwise(False)
    ) \
    .withColumn(
        "quality_score",
        when(col("is_valid"), 100).otherwise(0)
    )

# ============================================
# Write to Iceberg (Streaming)
# ============================================

def write_stream_to_iceberg(micro_batch_df, batch_id):
    """
    Write microBatch to Iceberg table
    Called for each Kafka micro-batch
    """
    
    if micro_batch_df.rdd.isEmpty():
        logger.info(f"⏭️  Batch {batch_id}: Empty micro-batch, skipping")
        return
    
    try:
        record_count = micro_batch_df.count()
        logger.info(f"💾 Writing batch {batch_id}: {record_count} records")
        
        # Create table if not exists, append if exists
        micro_batch_df \
            .select(
                col("kafka_topic"),
                col("source_id"),
                col("source_name"),
                col("partition"),
                col("offset"),
                col("kafka_timestamp"),
                col("ingestion_timestamp"),
                col("processed_timestamp"),
                col("raw_data"),
                col("is_valid"),
                col("quality_score"),
            ) \
            .writeTo(f"{ICEBERG_NAMESPACE}.kafka_events_raw") \
            .append()
        
        # Partition by processing date
        logger.info(f"✅ Batch {batch_id}: {record_count} records written to Iceberg")
        
        # Also write to summary table (aggregated)
        summary_df = micro_batch_df.groupBy("source_id", "source_name") \
            .agg(
                {"raw_data": "count"},
                {"quality_score": "avg"},
                {"kafka_topic": "first"}
            )
        
        summary_df \
            .withColumns({
                "processed_date": current_timestamp(),
                "batch_id": lit(str(batch_id))
            }) \
            .writeTo(f"{ICEBERG_NAMESPACE}.kafka_events_summary") \
            .append()
        
    except Exception as e:
        logger.error(f"❌ Error writing batch {batch_id}: {e}")
        raise

# ============================================
# Execute Streaming Query
# ============================================

query = df_validated \
    .writeStream \
    .format("iceberg") \
    .option("path", f"s3a://iceberg-warehouse/{ICEBERG_NAMESPACE}/kafka_events_raw") \
    .option("checkpointLocation", CHECKPOINT_LOCATION) \
    .trigger(processingTime="10 seconds") \
    .option("mergeSchema", "true") \
    .foreachBatch(write_stream_to_iceberg) \
    .start()

logger.info("\n" + "="*60)
logger.info("🚀 KAFKA STREAMING JOB STARTED")
logger.info("="*60)
logger.info(f"Listening to topics matching: {KAFKA_SUBSCRIBE_PATTERN}")
logger.info(f"Writing to Iceberg table: {ICEBERG_NAMESPACE}.kafka_events_raw")
logger.info(f"Checkpoint location: {CHECKPOINT_LOCATION}")
logger.info(f"Batch interval: 10 seconds")
logger.info("="*60 + "\n")

# ============================================
# Monitoring & Logging
# ============================================

def monitor_stream():
    """Monitor streaming query status"""
    while query.isActive:
        status = query.status
        logger.info(f"⚡ Streaming Status:")
        logger.info(f"   - Message: {status.get('message', 'Running')}")
        logger.info(f"   - Is Trigger Active: {query.isActive}")
        
        if hasattr(query, 'recentProgress') and query.recentProgress:
            latest = query.recentProgress[-1] if query.recentProgress else {}
            logger.info(f"   - Records processed: {latest.get('numInputRows', 0)}")
            logger.info(f"   - Processing time: {latest.get('processingTime', 'N/A')} ms")

# Keep streaming job running
try:
    query.awaitTermination()
except KeyboardInterrupt:
    logger.info("⏹️  Shutting down streaming job...")
    query.stop()
    logger.info("✅ Streaming job stopped")
finally:
    spark.stop()
    logger.info("✅ Spark session closed")
