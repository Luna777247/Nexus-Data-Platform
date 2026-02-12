# 📚 Examples & Reference Implementations

This directory contains example implementations and reference code for the Nexus Data Platform.

## 📁 Contents

### Airflow DAGs (`airflow-dags/`)

Example Airflow DAGs showing different patterns and use cases:

#### 1. **iceberg_pipeline.py**
- **Purpose**: Demo Iceberg table operations
- **Features**: 
  - Create Iceberg tables
  - Ingest from Kafka to Iceberg
  - Process with Spark
  - Query with Trino
  - HA features (Schema Registry, DLQ)
- **Use Case**: Learning Iceberg integration patterns

#### 2. **config_driven_pipeline.py**
- **Purpose**: Generic config-driven data ingestion
- **Features**:
  - Add sources via YAML config (no code changes)
  - Extract → Validate → Publish to Kafka
  - Support for APIs, Databases, S3, etc.
  - Metadata tracking
- **Use Case**: Extensible multi-source ingestion pattern

## 🎯 Production DAG

The **active production DAG** is located in:
```
pipelines/airflow/dags/medallion_etl_pipeline.py
```

This implements the **Medallion Architecture** pattern:
- Bronze → Silver → Gold layers
- Airflow as orchestrator (triggers Spark jobs)
- Proper separation of concerns

## 📖 Usage

### Using Example DAGs

1. **Copy to Airflow DAGs** directory:
```bash
cp examples/airflow-dags/iceberg_pipeline.py /opt/airflow/dags/
```

2. **Customize** for your use case

3. **Enable in Airflow UI**

### Learning Path

1. Start with `iceberg_pipeline.py` to understand Iceberg operations
2. Study `config_driven_pipeline.py` for extensible ingestion patterns
3. Review production `medallion_etl_pipeline.py` for best practices

## 🚫 Not for Production

**These examples are for reference and learning only.**

For production deployments, use:
- `medallion_etl_pipeline.py` - Production Medallion pattern
- Custom DAGs following the orchestrator pattern

## 📚 Related Documentation

- [Architecture Improvements](../docs/ARCHITECTURE_IMPROVEMENTS.md)
- [Data Sources Architecture](../docs/DATA_SOURCES_ARCHITECTURE.md)
- [Code Changes Summary](../CODE_CHANGES_SUMMARY.md)
- [Refactoring Complete](../REFACTORING_COMPLETE.md)
