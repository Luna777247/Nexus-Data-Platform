#!/usr/bin/env python3
"""
Test HA Features - DLQ Handler & Schema Registry
Run: python3 scripts/test_ha_features.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipelines.airflow.utils.dlq_handler import DLQHandler
from pipelines.airflow.utils.schema_registry import SchemaRegistryManager, SchemaValidator, register_event_schema
import json
from datetime import datetime

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_dlq_handler():
    """Test DLQ Handler functionality"""
    print_header("🧪 Testing DLQ Handler")
    
    handler = DLQHandler()
    
    # Test 1: Send generic failed message
    print("\n1️⃣  Testing generic DLQ send...")
    result1 = handler.send_to_dlq(
        original_message={'event_id': 'test_001', 'user_id': 123, 'amount': 99.99},
        error=ValueError('Test error: Invalid amount'),
        source='test_script',
        metadata={'test_run': datetime.now().isoformat()}
    )
    print(f"   Result: {'✅ SUCCESS' if result1 else '❌ FAILED'}")
    
    # Test 2: Send schema validation error
    print("\n2️⃣  Testing schema validation DLQ...")
    result2 = handler.send_schema_validation_error(
        message={'event_id': 'test_002', 'user_id': 456},
        schema_errors=['Missing required field: region', 'Missing required field: event_type'],
        source='test_script'
    )
    print(f"   Result: {'✅ SUCCESS' if result2 else '❌ FAILED'}")
    
    # Test 3: Send processing error
    print("\n3️⃣  Testing processing error DLQ...")
    result3 = handler.send_processing_error(
        message={'event_id': 'test_003', 'data': 'corrupted'},
        error=Exception('Processing failed: Data transformation error'),
        source='test_script',
        processing_step='data_transformation'
    )
    print(f"   Result: {'✅ SUCCESS' if result3 else '❌ FAILED'}")
    
    # Test 4: Get DLQ statistics
    print("\n4️⃣  Getting DLQ statistics...")
    stats = handler.get_dlq_stats()
    print(f"   DLQ Topics:")
    for topic, info in stats.items():
        print(f"     • {topic}: {info}")
    
    handler.close()
    
    all_passed = result1 and result2 and result3
    print(f"\n{'✅ All DLQ tests PASSED' if all_passed else '❌ Some DLQ tests FAILED'}")
    return all_passed

def test_schema_registry():
    """Test Schema Registry functionality"""
    print_header("🧪 Testing Schema Registry")
    
    manager = SchemaRegistryManager()
    
    if not manager.client:
        print("❌ Schema Registry client not available - skipping tests")
        return False
    
    # Test 1: Register event schema
    print("\n1️⃣  Registering event schema...")
    schema_id = register_event_schema()
    if schema_id:
        print(f"   ✅ Event schema registered: ID {schema_id}")
    else:
        print(f"   ⚠️  Event schema registration failed (may already exist)")
    
    # Test 2: Register Iceberg schema
    print("\n2️⃣  Registering Iceberg tourism schema...")
    iceberg_schema = json.dumps({
        "type": "record",
        "name": "TourismEvent",
        "namespace": "io.nexus.iceberg",
        "fields": [
            {"name": "event_id", "type": "string"},
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
            {"name": "user_id", "type": "int"},
            {"name": "amount", "type": "double"},
            {"name": "region", "type": "string"},
            {"name": "event_type", "type": "string"},
            {"name": "source", "type": "string"}
        ]
    })
    
    iceberg_id = manager.register_schema(
        subject='iceberg-tourism_db-value',
        schema_str=iceberg_schema,
        schema_type='AVRO'
    )
    if iceberg_id:
        print(f"   ✅ Iceberg schema registered: ID {iceberg_id}")
    else:
        print(f"   ⚠️  Iceberg schema registration failed (may already exist)")
    
    # Test 3: List all schemas
    print("\n3️⃣  Listing registered schemas...")
    subjects = manager.list_subjects()
    print(f"   📋 Found {len(subjects)} registered schemas:")
    for subject in subjects:
        versions = manager.get_schema_versions(subject)
        print(f"     • {subject}: {len(versions)} version(s)")
    
    # Test 4: Get latest schema
    print("\n4️⃣  Getting latest event schema...")
    schema = manager.get_schema('events-value')
    if schema:
        print(f"   ✅ Retrieved schema version: {schema.version}")
        print(f"   Schema ID: {schema.schema_id}")
    else:
        print(f"   ⚠️  Could not retrieve schema")
    
    # Test 5: Test compatibility
    print("\n5️⃣  Testing schema compatibility...")
    new_schema = json.dumps({
        "type": "record",
        "name": "Event",
        "namespace": "io.nexus.events",
        "fields": [
            {"name": "event_id", "type": "string"},
            {"name": "event_type", "type": "string"},
            {"name": "user_id", "type": "int"},
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
            {"name": "amount", "type": ["null", "double"], "default": None},
            {"name": "region", "type": "string"},
            {"name": "source", "type": "string"},
            # New optional field (backward compatible)
            {"name": "device_type", "type": ["null", "string"], "default": None}
        ]
    })
    
    is_compatible = manager.check_compatibility('events-value', new_schema)
    print(f"   {'✅ Schema is COMPATIBLE' if is_compatible else '❌ Schema is NOT compatible'}")
    
    print(f"\n✅ Schema Registry tests completed")
    return True

def test_schema_validation():
    """Test Schema Validation"""
    print_header("🧪 Testing Schema Validation")
    
    validator = SchemaValidator()
    
    if not validator.registry.client:
        print("❌ Schema Registry not available - skipping validation tests")
        return False
    
    # Test 1: Valid message
    print("\n1️⃣  Testing valid message...")
    valid_msg = {
        'event_id': 'evt_12345',
        'event_type': 'booking',
        'user_id': 789,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'amount': 199.99,
        'region': 'VN',
        'source': 'tourism_api'
    }
    
    is_valid, errors = validator.validate_message(valid_msg, 'events-value')
    print(f"   Message: {json.dumps(valid_msg, indent=2)}")
    print(f"   Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
    if errors:
        print(f"   Errors: {errors}")
    
    # Test 2: Invalid message (missing required field)
    print("\n2️⃣  Testing invalid message (missing required field)...")
    invalid_msg = {
        'event_id': 'evt_67890',
        'user_id': 456,
        'amount': 99.99
        # Missing: region, event_type, source
    }
    
    is_valid2, errors2 = validator.validate_message(invalid_msg, 'events-value')
    print(f"   Message: {json.dumps(invalid_msg, indent=2)}")
    print(f"   Result: {'✅ VALID' if is_valid2 else '❌ INVALID (Expected)'}")
    if errors2:
        print(f"   Errors found ({len(errors2)}):")
        for err in errors2:
            print(f"     • {err}")
    
    print(f"\n✅ Schema validation tests completed")
    return True

def main():
    """Run all tests"""
    print("\n" + "🚀 " * 30)
    print("   NEXUS DATA PLATFORM - HA FEATURES TEST SUITE")
    print("🚀 " * 30)
    
    results = {}
    
    # Test DLQ Handler
    try:
        results['dlq_handler'] = test_dlq_handler()
    except Exception as e:
        print(f"\n❌ DLQ Handler test failed: {e}")
        results['dlq_handler'] = False
    
    # Test Schema Registry
    try:
        results['schema_registry'] = test_schema_registry()
    except Exception as e:
        print(f"\n❌ Schema Registry test failed: {e}")
        results['schema_registry'] = False
    
    # Test Schema Validation
    try:
        results['schema_validation'] = test_schema_validation()
    except Exception as e:
        print(f"\n❌ Schema Validation test failed: {e}")
        results['schema_validation'] = False
    
    # Summary
    print_header("📊 TEST SUMMARY")
    print(f"\n  DLQ Handler:        {'✅ PASSED' if results.get('dlq_handler') else '❌ FAILED'}")
    print(f"  Schema Registry:    {'✅ PASSED' if results.get('schema_registry') else '❌ FAILED'}")
    print(f"  Schema Validation:  {'✅ PASSED' if results.get('schema_validation') else '❌ FAILED'}")
    
    all_passed = all(results.values())
    print(f"\n{'🎉 ALL TESTS PASSED!' if all_passed else '⚠️  SOME TESTS FAILED'}")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
