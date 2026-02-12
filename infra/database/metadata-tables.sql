-- Metadata Tables for Extensible Data Platform
-- Location: infra/database/metadata-tables.sql
-- Purpose: Track data lineage, pipeline execution, and source configuration
-- Format: Apache Iceberg with Trino/Spark SQL compatibility

-- ============================================
-- 1. Data Sources Registry
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.data_sources (
    source_id STRING NOT NULL,
    source_name STRING NOT NULL,
    source_type STRING,  -- api, jdbc, s3, gcs, etc.
    location STRING,
    format STRING,  -- json, parquet, csv, etc.
    
    -- Target configuration
    kafka_topic STRING,
    target_table STRING,
    target_database STRING,
    partition_columns STRING,  -- Comma-separated
    
    -- Schema management
    schema_version INT,
    schema_file STRING,
    required_fields STRING,  -- Comma-separated
    
    -- Scheduling
    schedule_interval STRING,  -- @daily, @hourly, etc.
    
    -- Data retention
    retention_days INT,
    archive_after_days INT,
    
    -- Status
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_extracted_at TIMESTAMP,
    
    -- Metadata
    config_json STRING,  -- Full source config as JSON
    notes STRING,
    
    PRIMARY KEY (source_id)
)
USING ICEBERG
PARTITIONED BY (source_type)
COMMENT 'Registry of all data sources in the platform';

-- ============================================
-- 2. Pipeline Execution Tracking
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.pipeline_runs (
    run_id STRING NOT NULL,
    dag_id STRING,  -- Airflow DAG name
    dag_run_id STRING,
    pipeline_name STRING,
    
    -- Execution timing
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_seconds INT,
    
    -- Status
    status STRING,  -- SUCCESS, FAILED, RUNNING, CANCELLED
    error_message STRING,
    retry_count INT DEFAULT 0,
    
    -- Resources
    executor STRING,  -- airflow, spark, kubernetes, etc.
    configured_vcpu INT,
    configured_memory_gb INT,
    actual_duration_ms INT,
    
    -- Metadata
    run_config_json STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (run_id)
)
USING ICEBERG
PARTITIONED BY (YEAR(started_at), MONTH(started_at), status)
COMMENT 'Execution history of all data pipelines';

-- ============================================
-- 3. Data Source Execution Details
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.source_executions (
    execution_id STRING NOT NULL,
    source_id STRING NOT NULL,
    pipeline_run_id STRING,
    
    -- Source details
    source_name STRING,
    kafka_topic STRING,
    target_table STRING,
    
    -- Execution metrics
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_seconds INT,
    
    -- Data metrics
    extracted_record_count INT,
    validated_record_count INT,
    failed_record_count INT,
    published_record_count INT,
    quality_score DOUBLE,  -- 0-100
    
    -- Status
    status STRING,  -- SUCCESS, FAILED, PARTIAL
    error_message STRING,
    
    -- Metadata
    execution_log STRING,  -- Full execution log as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (execution_id),
    FOREIGN KEY (source_id) REFERENCES iceberg.platform_metadata.data_sources(source_id),
    FOREIGN KEY (pipeline_run_id) REFERENCES iceberg.platform_metadata.pipeline_runs(run_id)
)
USING ICEBERG
PARTITIONED BY (YEAR(started_at), source_id)
COMMENT 'Detailed execution metrics for each data source per pipeline run';

-- ============================================
-- 4. Kafka Event Processing Metrics
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.kafka_event_metrics (
    metric_id STRING NOT NULL,
    kafka_topic STRING,
    source_id STRING,
    
    -- Kafka metrics
    partition INT,
    message_offset INT,
    message_count INT,
    
    -- Processing metrics
    received_at TIMESTAMP,
    processed_at TIMESTAMP,
    processing_latency_ms INT,
    
    -- Quality metrics
    valid_messages INT,
    invalid_messages INT,
    validation_errors STRING,  -- JSON with error details
    
    -- Iceberg metrics
    written_to_table STRING,
    record_count_written INT,
    partition_values MAP<STRING, STRING>,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (metric_id)
)
USING ICEBERG
PARTITIONED BY (YEAR(processed_at), MONTH(processed_at), kafka_topic)
COMMENT 'Real-time metrics for Kafka event processing';

-- ============================================
-- 5. Data Lineage Tracking
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.data_lineage (
    lineage_id STRING NOT NULL,
    source_id STRING NOT NULL,
    source_table STRING,
    
    target_id STRING,
    target_table STRING,
    target_database STRING,
    
    -- Transformation details
    transformation_type STRING,  -- direct, aggregation, join, etc.
    transformation_logic STRING,  -- SQL or logic description
    
    -- Versioning
    source_version INT,
    target_version INT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (lineage_id),
    FOREIGN KEY (source_id) REFERENCES iceberg.platform_metadata.data_sources(source_id)
)
USING ICEBERG
PARTITIONED BY (source_id, target_id)
COMMENT 'Data lineage: which sources feed into which tables';

-- ============================================
-- 6. Data Quality Metrics
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.data_quality_metrics (
    metric_id STRING NOT NULL,
    source_id STRING,
    target_table STRING,
    
    -- Quality checks
    check_timestamp TIMESTAMP NOT NULL,
    total_records INT,
    valid_records INT,
    invalid_records INT,
    null_count INT,
    duplicate_count INT,
    
    -- Quality scores
    completeness_score DOUBLE,  -- % of non-null values
    uniqueness_score DOUBLE,   -- % of unique values
    consistency_score DOUBLE,  -- % matching business rules
    accuracy_score DOUBLE,     -- % matching validations
    overall_quality_score DOUBLE,  -- 0-100
    
    -- Thresholds
    quality_threshold DOUBLE,
    threshold_met BOOLEAN,
    
    -- Details
    quality_issues STRING,  -- JSON with detailed issues
    recommendations STRING,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (metric_id)
)
USING ICEBERG
PARTITIONED BY (YEAR(check_timestamp), source_id)
COMMENT 'Data quality metrics for all ingested data';

-- ============================================
-- 7. Configuration Change Audit
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.config_audit_log (
    audit_id STRING NOT NULL,
    source_id STRING NOT NULL,
    
    -- Change details
    change_type STRING,  -- CREATED, MODIFIED, DELETED
    changed_fields MAP<STRING, STRUCT<old_value: STRING, new_value: STRING>>,
    
    -- Change metadata
    changed_by STRING,  -- username or system
    changed_at TIMESTAMP NOT NULL,
    change_reason STRING,
    
    -- Version control
    config_version_before STRING,
    config_version_after STRING,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (audit_id),
    FOREIGN KEY (source_id) REFERENCES iceberg.platform_metadata.data_sources(source_id)
)
USING ICEBERG
PARTITIONED BY (YEAR(changed_at), source_id)
COMMENT 'Audit trail of all configuration changes';

-- ============================================
-- 8. Raw Kafka Events Storage
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.kafka_events_raw (
    kafka_topic STRING,
    source_id STRING,
    source_name STRING,
    partition INT,
    offset INT,
    kafka_timestamp LONG,
    ingestion_timestamp STRING,
    processed_timestamp TIMESTAMP,
    raw_data MAP<STRING, STRING>,
    is_valid BOOLEAN,
    quality_score INT,
    batch_id STRING,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
USING ICEBERG
PARTITIONED BY (YEAR(processed_timestamp), MONTH(processed_timestamp), source_id)
COMMENT 'Raw Kafka events before processing';

-- ============================================
-- 9. Kafka Events Summary (Aggregated)
-- ============================================

CREATE TABLE IF NOT EXISTS iceberg.platform_metadata.kafka_events_summary (
    source_id STRING,
    source_name STRING,
    kafka_topic STRING,
    
    processed_date TIMESTAMP,
    batch_id STRING,
    
    -- Aggregations
    event_count INT,
    avg_quality_score DOUBLE,
    valid_events INT,
    invalid_events INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
USING ICEBERG
PARTITIONED BY (YEAR(processed_date), MONTH(processed_date), source_id)
COMMENT 'Aggregated summary of Kafka events by source';

-- ============================================
-- Views for Analysis
-- ============================================

-- View 1: Recent source executions
CREATE OR REPLACE VIEW iceberg.platform_metadata.v_recent_executions AS
SELECT
    source_id,
    source_name,
    status,
    extracted_record_count,
    validated_record_count,
    quality_score,
    error_message,
    started_at,
    duration_seconds
FROM iceberg.platform_metadata.source_executions
WHERE started_at >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
ORDER BY started_at DESC;

-- View 2: Data sources with execution status
CREATE OR REPLACE VIEW iceberg.platform_metadata.v_source_status AS
SELECT
    ds.source_id,
    ds.source_name,
    ds.source_type,
    ds.is_enabled,
    COUNT(DISTINCT se.execution_id) as total_executions,
    SUM(CASE WHEN se.status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_executions,
    SUM(CASE WHEN se.status = 'FAILED' THEN 1 ELSE 0 END) as failed_executions,
    MAX(se.started_at) as last_execution_time,
    AVG(se.quality_score) as avg_quality_score,
    ds.last_extracted_at
FROM iceberg.platform_metadata.data_sources ds
LEFT JOIN iceberg.platform_metadata.source_executions se
    ON ds.source_id = se.source_id
GROUP BY
    ds.source_id, ds.source_name, ds.source_type,
    ds.is_enabled, ds.last_extracted_at;

-- View 3: Pipeline execution summary
CREATE OR REPLACE VIEW iceberg.platform_metadata.v_pipeline_summary AS
SELECT
    TRUNC(started_at) as execution_date,
    dag_id,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
    AVG(duration_seconds) as avg_duration_seconds,
    MAX(duration_seconds) as max_duration_seconds,
    MIN(duration_seconds) as min_duration_seconds
FROM iceberg.platform_metadata.pipeline_runs
GROUP BY
    TRUNC(started_at), dag_id
ORDER BY execution_date DESC, dag_id;

-- ============================================
-- Indexes for Performance
-- ============================================

-- These are suggestions for table optimization
-- Run periodically: OPTIMIZE iceberg.platform_metadata.{table_name}

-- Note: Iceberg doesn't have traditional indexes,
-- but we can use OPTIMIZE and REWRITE_DATA_FILES procedure

-- ============================================
-- End of Metadata Tables Setup
-- ============================================

-- Run this script against Trino with Iceberg catalog:
-- trino --catalog iceberg --execute "@metadata-tables.sql"

-- Or with Spark:
-- spark-sql -i metadata-tables.sql
