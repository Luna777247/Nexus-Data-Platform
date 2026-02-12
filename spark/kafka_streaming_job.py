#!/usr/bin/env python3
"""
Spark Structured Streaming Job - Kafka to Bronze Layer
Location: spark/kafka_streaming_job.py

Purpose:
- Subscribe to all Kafka topics matching pattern: topic_*
- Real-time streaming ingestion
- Write to 🥉 Bronze Layer (Raw Data)
- Partitioned by date and hour for efficient queries

Architecture:
    Kafka Topics → Spark Streaming → Bronze Layer (Parquet/Iceberg)
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
KAFKA_SUBSCRIBE_PATTERN = "topic_.*"  # Matches: topic_app_events, topic_cdc_changes, etc.
BRONZE_BUCKET = "s3a://bronze"
CHECKPOINT_LOCATION = "s3a://bronze/_checkpoints/kafka_stream"

logger.info(f"📡 Kafka to Bronze Configuration:")
logger.info(f"   Bootstrap Servers: {KAFKA_BOOTSTRAP_SERVERS}")
logger.info(f"   Subscribe Pattern: {KAFKA_SUBSCRIBE_PATTERN}")
logger.info(f"   Bronze Layer: {BRONZE_BUCKET}")

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
# Write to Bronze Layer (Streaming)
# ============================================

def write_stream_to_bronze(micro_batch_df, batch_id):
    """
    Write microBatch to Bronze Layer in Parquet format
    Partitioned by: date, hour, source
    
    Bronze Layer Structure:
        s3a://bronze/{source_type}/date={date}/hour={hour}/
    """
    
    if micro_batch_df.rdd.isEmpty():
        logger.info(f"⏭️  Batch {batch_id}: Empty micro-batch, skipping")
        return
    
    try:
        record_count = micro_batch_df.count()
        logger.info(f"💾 Writing batch {batch_id}: {record_count} records to Bronze")
        
        # Add partitioning columns
        df_with_partitions = micro_batch_df \
            .withColumn("ingestion_date", to_date(col("processed_timestamp"))) \
            .withColumn("ingestion_hour", hour(col("processed_timestamp")))
        
        # Determine source type from kafka topic
        # topic_app_events -> app_events
        # topic_cdc_changes -> cdc_changes
        df_with_source = df_with_partitions \
            .withColumn("source_type", 
                       expr("regexp_replace(kafka_topic, '^topic_', '')"))
        
        # Write to Bronze partitioned by source, date, hour
        df_with_source \
            .select(
                "kafka_topic",
                "source_id",
                "source_name",
                "partition",
                "offset",
                "kafka_timestamp",
                "ingestion_timestamp",
                "processed_timestamp",
                "raw_data",
                "is_valid",
                "quality_score",
                "source_type",
                "ingestion_date",
                "ingestion_hour"
            ) \
            .write \
            .mode("append") \
            .partitionBy("source_type", "ingestion_date", "ingestion_hour") \
            .parquet(f"{BRONZE_BUCKET}/kafka_events")
        
        logger.info(f"✅ Batch {batch_id}: {record_count} records written to Bronze Layer")
        
    except Exception as e:
        logger.error(f"❌ Error writing batch {batch_id}: {e}")
        raise

# ============================================
# Execute Streaming Query
# ============================================

query = df_validated \
    .writeStream \
    .outputMode("append") \
    .option("checkpointLocation", CHECKPOINT_LOCATION) \
    .trigger(processingTime="10 seconds") \
    .foreachBatch(write_stream_to_bronze) \
    .start()

logger.info("\n" + "="*60)
logger.info("🚀 KAFKA → BRONZE STREAMING JOB STARTED")
logger.info("="*60)
logger.info(f"Listening to topics matching: {KAFKA_SUBSCRIBE_PATTERN}")
logger.info(f"Writing to Bronze Layer: {BRONZE_BUCKET}")
logger.info(f"Checkpoint location: {CHECKPOINT_LOCATION}")
logger.info(f"Batch interval: 10 seconds")
logger.info(f"Partitioning: source_type/date/hour")
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
