#!/usr/bin/env python3
"""
Register schemas to Schema Registry
Run this after HA stack is deployed
Usage: python3 scripts/register_schemas.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipelines.airflow.utils.schema_registry import SchemaRegistryManager
import json

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def register_all_schemas():
    """Register all platform schemas"""
    print_header("📚 Registering Schemas to Schema Registry")
    
    # Check connection
    manager = SchemaRegistryManager()
    if not manager.client:
        print("\n❌ ERROR: Schema Registry not available!")
        print("   Make sure the HA stack is deployed and running:")
        print("   cd infra/docker-stack && ./setup-ha.sh")
        return False
    
    schemas_registered = 0
    total_schemas = 0
    
    # Schema 1: Tourism Events (Main event schema)
    print("\n1️⃣  Registering Tourism Events schema...")
    total_schemas += 1
    event_schema = json.dumps({
        "type": "record",
        "name": "Event",
        "namespace": "io.nexus.events",
        "doc": "Tourism platform event schema - main data ingestion",
        "fields": [
            {"name": "event_id", "type": "string", "doc": "Unique event identifier"},
            {"name": "event_type", "type": "string", "doc": "Type of event (booking, view, search, etc.)"},
            {"name": "user_id", "type": "int", "doc": "User identifier"},
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis", "doc": "Event timestamp in milliseconds"},
            {"name": "amount", "type": ["null", "double"], "default": None, "doc": "Transaction amount (if applicable)"},
            {"name": "region", "type": "string", "doc": "Geographic region code (VN, SG, TH, etc.)"},
            {"name": "source", "type": "string", "doc": "Data source identifier"}
        ]
    })
    
    schema_id = manager.register_schema('events-value', event_schema, 'AVRO')
    if schema_id:
        print(f"   ✅ Registered: events-value (ID: {schema_id})")
        schemas_registered += 1
    else:
        print(f"   ⚠️  Already exists or failed to register")
    
    # Schema 2: Iceberg Tourism DB
    print("\n2️⃣  Registering Iceberg Tourism DB schema...")
    total_schemas += 1
    iceberg_schema = json.dumps({
        "type": "record",
        "name": "TourismEvent",
        "namespace": "io.nexus.iceberg",
        "doc": "Iceberg table schema for processed tourism data",
        "fields": [
            {"name": "event_id", "type": "string"},
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
            {"name": "user_id", "type": "int"},
            {"name": "amount", "type": ["null", "double"], "default": None},
            {"name": "region", "type": "string"},
            {"name": "event_type", "type": "string"},
            {"name": "source", "type": "string"},
            {"name": "processed_at", "type": ["null", "long"], "default": None, "logicalType": "timestamp-millis"}
        ]
    })
    
    schema_id = manager.register_schema('iceberg-tourism_db-value', iceberg_schema, 'AVRO')
    if schema_id:
        print(f"   ✅ Registered: iceberg-tourism_db-value (ID: {schema_id})")
        schemas_registered += 1
    else:
        print(f"   ⚠️  Already exists or failed to register")
    
    # Schema 3: User Activity (for future use)
    print("\n3️⃣  Registering User Activity schema...")
    total_schemas += 1
    user_activity_schema = json.dumps({
        "type": "record",
        "name": "UserActivity",
        "namespace": "io.nexus.users",
        "doc": "User activity tracking schema",
        "fields": [
            {"name": "user_id", "type": "int"},
            {"name": "session_id", "type": "string"},
            {"name": "action", "type": "string"},
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
            {"name": "device_type", "type": ["null", "string"], "default": None},
            {"name": "location", "type": ["null", "string"], "default": None}
        ]
    })
    
    schema_id = manager.register_schema('user-activity-value', user_activity_schema, 'AVRO')
    if schema_id:
        print(f"   ✅ Registered: user-activity-value (ID: {schema_id})")
        schemas_registered += 1
    else:
        print(f"   ⚠️  Already exists or failed to register")
    
    # Schema 4: Clickhouse Analytics
    print("\n4️⃣  Registering ClickHouse Analytics schema...")
    total_schemas += 1
    clickhouse_schema = json.dumps({
        "type": "record",
        "name": "AnalyticsEvent",
        "namespace": "io.nexus.analytics",
        "doc": "ClickHouse analytics table schema",
        "fields": [
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
            {"name": "user_id", "type": "int"},
            {"name": "event_type", "type": "string"},
            {"name": "amount", "type": "double"},
            {"name": "region", "type": "string"},
            {"name": "source", "type": "string"},
            {"name": "inserted_at", "type": "long", "logicalType": "timestamp-millis"}
        ]
    })
    
    schema_id = manager.register_schema('analytics-events-value', clickhouse_schema, 'AVRO')
    if schema_id:
        print(f"   ✅ Registered: analytics-events-value (ID: {schema_id})")
        schemas_registered += 1
    else:
        print(f"   ⚠️  Already exists or failed to register")
    
    # Summary
    print_header("📊 Schema Registration Summary")
    print(f"\n  Total schemas: {total_schemas}")
    print(f"  Successfully registered: {schemas_registered}")
    print(f"  Already existed/failed: {total_schemas - schemas_registered}")
    
    # List all registered schemas
    print("\n📋 All registered schemas:")
    subjects = manager.list_subjects()
    for subject in subjects:
        versions = manager.get_schema_versions(subject)
        schema = manager.get_schema(subject)
        print(f"   • {subject}")
        print(f"     - Current version: {schema.version if schema else 'N/A'}")
        print(f"     - Total versions: {len(versions)}")
    
    print("\n✅ Schema registration complete!")
    print("\n💡 Next steps:")
    print("   1. Test schema validation: python3 scripts/test_ha_features.py")
    print("   2. Run Airflow DAG: docker exec -it airflow-webserver airflow dags trigger tourism_events_pipeline")
    print("   3. Check Grafana dashboards: http://localhost:3001")
    print("="*60 + "\n")
    
    return schemas_registered > 0

if __name__ == '__main__':
    success = register_all_schemas()
    sys.exit(0 if success else 1)
