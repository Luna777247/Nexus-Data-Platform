"""
Data Quality Checker for Nexus Data Platform
Validates data quality across medallion architecture layers
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """
    Comprehensive data quality checker for ETL pipelines
    Performs validation, completeness, uniqueness, and consistency checks
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.checks_passed = 0
        self.checks_failed = 0
        self.results = []
    
    def check_completeness(self, data: List[Dict], required_fields: List[str]) -> Dict[str, Any]:
        """
        Check data completeness - ensure required fields are present and not null
        
        Args:
            data: List of data records
            required_fields: List of required field names
            
        Returns:
            Dict with completeness check results
        """
        logger.info(f"Checking completeness for {len(data)} records")
        
        total_records = len(data)
        missing_counts = {field: 0 for field in required_fields}
        
        for record in data:
            for field in required_fields:
                if field not in record or record[field] is None or record[field] == "":
                    missing_counts[field] += 1
        
        # Calculate completion rates
        completion_rates = {
            field: ((total_records - missing) / total_records) * 100 if total_records > 0 else 0
            for field, missing in missing_counts.items()
        }
        
        # Determine pass/fail (threshold: 95% completion)
        threshold = self.config.get('completeness_threshold', 95)
        passed = all(rate >= threshold for rate in completion_rates.values())
        
        result = {
            "check": "completeness",
            "timestamp": datetime.now().isoformat(),
            "total_records": total_records,
            "required_fields": required_fields,
            "missing_counts": missing_counts,
            "completion_rates": completion_rates,
            "threshold": threshold,
            "passed": passed,
            "status": "✅ PASS" if passed else "❌ FAIL"
        }
        
        self._record_result(result)
        logger.info(f"Completeness check: {result['status']}")
        
        return result
    
    def check_uniqueness(self, data: List[Dict], unique_fields: List[str]) -> Dict[str, Any]:
        """
        Check uniqueness constraints on specified fields
        
        Args:
            data: List of data records
            unique_fields: Fields that should have unique values
            
        Returns:
            Dict with uniqueness check results
        """
        logger.info(f"Checking uniqueness for fields: {unique_fields}")
        
        total_records = len(data)
        duplicate_info = {}
        
        for field in unique_fields:
            values = [r.get(field) for r in data if r.get(field) is not None]
            unique_values = set(values)
            duplicates = len(values) - len(unique_values)
            duplicate_percentage = (duplicates / total_records * 100) if total_records > 0 else 0
            
            duplicate_info[field] = {
                "total_values": len(values),
                "unique_values": len(unique_values),
                "duplicates": duplicates,
                "duplicate_percentage": duplicate_percentage
            }
        
        # Determine pass/fail (threshold: < 1% duplicates)
        threshold = self.config.get('duplicate_threshold', 1.0)
        passed = all(info['duplicate_percentage'] < threshold for info in duplicate_info.values())
        
        result = {
            "check": "uniqueness",
            "timestamp": datetime.now().isoformat(),
            "total_records": total_records,
            "unique_fields": unique_fields,
            "duplicate_info": duplicate_info,
            "threshold": threshold,
            "passed": passed,
            "status": "✅ PASS" if passed else "❌ FAIL"
        }
        
        self._record_result(result)
        logger.info(f"Uniqueness check: {result['status']}")
        
        return result
    
    def check_range(self, data: List[Dict], field: str, min_val: float, max_val: float) -> Dict[str, Any]:
        """
        Check if numeric values fall within expected range
        
        Args:
            data: List of data records
            field: Field name to check
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value
            
        Returns:
            Dict with range check results
        """
        logger.info(f"Checking range for field {field}: [{min_val}, {max_val}]")
        
        total_records = len(data)
        out_of_range = 0
        out_of_range_records = []
        
        for record in data:
            value = record.get(field)
            if value is not None:
                try:
                    value = float(value)
                    if value < min_val or value > max_val:
                        out_of_range += 1
                        if len(out_of_range_records) < 10:  # Keep first 10 examples
                            out_of_range_records.append({
                                "record_id": record.get("id", "unknown"),
                                "value": value
                            })
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert value to float: {value}")
        
        out_of_range_percentage = (out_of_range / total_records * 100) if total_records > 0 else 0
        
        # Determine pass/fail (threshold: < 5% out of range)
        threshold = self.config.get('range_threshold', 5.0)
        passed = out_of_range_percentage < threshold
        
        result = {
            "check": "range",
            "timestamp": datetime.now().isoformat(),
            "field": field,
            "range": {"min": min_val, "max": max_val},
            "total_records": total_records,
            "out_of_range_count": out_of_range,
            "out_of_range_percentage": out_of_range_percentage,
            "examples": out_of_range_records,
            "threshold": threshold,
            "passed": passed,
            "status": "✅ PASS" if passed else "❌ FAIL"
        }
        
        self._record_result(result)
        logger.info(f"Range check: {result['status']}")
        
        return result
    
    def check_schema(self, data: List[Dict], expected_schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate that data matches expected schema
        
        Args:
            data: List of data records
            expected_schema: Dict mapping field names to expected types
            
        Returns:
            Dict with schema validation results
        """
        logger.info("Checking schema compliance")
        
        if not data:
            return {
                "check": "schema",
                "timestamp": datetime.now().isoformat(),
                "passed": False,
                "status": "❌ FAIL - No data to validate",
                "errors": ["Empty dataset"]
            }
        
        schema_errors = []
        type_mismatches = {field: 0 for field in expected_schema}
        
        for idx, record in enumerate(data):
            for field, expected_type in expected_schema.items():
                if field in record and record[field] is not None:
                    actual_type = type(record[field]).__name__
                    if actual_type != expected_type and not self._type_compatible(actual_type, expected_type):
                        type_mismatches[field] += 1
                        if len(schema_errors) < 10:  # Keep first 10 examples
                            schema_errors.append({
                                "record_index": idx,
                                "field": field,
                                "expected_type": expected_type,
                                "actual_type": actual_type,
                                "value": str(record[field])[:100]
                            })
        
        total_records = len(data)
        mismatch_percentages = {
            field: (count / total_records * 100) if total_records > 0 else 0
            for field, count in type_mismatches.items()
        }
        
        # Determine pass/fail (threshold: < 2% type mismatches)
        threshold = self.config.get('schema_threshold', 2.0)
        passed = all(pct < threshold for pct in mismatch_percentages.values())
        
        result = {
            "check": "schema",
            "timestamp": datetime.now().isoformat(),
            "expected_schema": expected_schema,
            "total_records": total_records,
            "type_mismatches": type_mismatches,
            "mismatch_percentages": mismatch_percentages,
            "errors": schema_errors,
            "threshold": threshold,
            "passed": passed,
            "status": "✅ PASS" if passed else "❌ FAIL"
        }
        
        self._record_result(result)
        logger.info(f"Schema check: {result['status']}")
        
        return result
    
    def check_freshness(self, data: List[Dict], timestamp_field: str, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Check data freshness based on timestamp field
        
        Args:
            data: List of data records
            timestamp_field: Field containing timestamp
            max_age_hours: Maximum acceptable age in hours
            
        Returns:
            Dict with freshness check results
        """
        logger.info(f"Checking data freshness (max age: {max_age_hours}h)")
        
        from dateutil import parser
        
        current_time = datetime.now()
        stale_records = 0
        oldest_timestamp = None
        newest_timestamp = None
        
        for record in data:
            if timestamp_field in record:
                try:
                    ts = parser.parse(record[timestamp_field])
                    age_hours = (current_time - ts).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        stale_records += 1
                    
                    if oldest_timestamp is None or ts < oldest_timestamp:
                        oldest_timestamp = ts
                    if newest_timestamp is None or ts > newest_timestamp:
                        newest_timestamp = ts
                        
                except Exception as e:
                    logger.warning(f"Could not parse timestamp: {record[timestamp_field]} - {e}")
        
        total_records = len(data)
        stale_percentage = (stale_records / total_records * 100) if total_records > 0 else 0
        
        # Determine pass/fail (threshold: < 10% stale records)
        threshold = self.config.get('freshness_threshold', 10.0)
        passed = stale_percentage < threshold
        
        result = {
            "check": "freshness",
            "timestamp": datetime.now().isoformat(),
            "timestamp_field": timestamp_field,
            "max_age_hours": max_age_hours,
            "total_records": total_records,
            "stale_records": stale_records,
            "stale_percentage": stale_percentage,
            "oldest_timestamp": oldest_timestamp.isoformat() if oldest_timestamp else None,
            "newest_timestamp": newest_timestamp.isoformat() if newest_timestamp else None,
            "threshold": threshold,
            "passed": passed,
            "status": "✅ PASS" if passed else "❌ FAIL"
        }
        
        self._record_result(result)
        logger.info(f"Freshness check: {result['status']}")
        
        return result
    
    def _type_compatible(self, actual: str, expected: str) -> bool:
        """Check if actual type is compatible with expected type"""
        compatible_types = {
            'int': ['float', 'int'],
            'float': ['int', 'float'],
            'str': ['str']
        }
        return actual in compatible_types.get(expected, [])
    
    def _record_result(self, result: Dict[str, Any]):
        """Record check result"""
        self.results.append(result)
        if result['passed']:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all quality checks"""
        total_checks = self.checks_passed + self.checks_failed
        success_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "total_checks": total_checks,
            "passed": self.checks_passed,
            "failed": self.checks_failed,
            "success_rate": success_rate,
            "status": "✅ PASS" if self.checks_failed == 0 else "❌ FAIL",
            "timestamp": datetime.now().isoformat(),
            "results": self.results
        }
    
    def export_results(self, output_path: str):
        """Export results to JSON file"""
        summary = self.get_summary()
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results exported to {output_path}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Sample data
    sample_data = [
        {"id": 1, "name": "User1", "age": 25, "email": "user1@example.com", "created_at": "2026-02-13T00:00:00"},
        {"id": 2, "name": "User2", "age": 30, "email": "user2@example.com", "created_at": "2026-02-13T01:00:00"},
        {"id": 3, "name": "User3", "age": 22, "email": "user3@example.com", "created_at": "2026-02-13T02:00:00"},
    ]
    
    # Initialize checker
    checker = DataQualityChecker(config={
        'completeness_threshold': 95,
        'duplicate_threshold': 1.0,
        'range_threshold': 5.0
    })
    
    # Run checks
    checker.check_completeness(sample_data, ["id", "name", "email"])
    checker.check_uniqueness(sample_data, ["id", "email"])
    checker.check_range(sample_data, "age", 18, 100)
    checker.check_schema(sample_data, {"id": "int", "name": "str", "age": "int"})
    checker.check_freshness(sample_data, "created_at", max_age_hours=24)
    
    # Print summary
    summary = checker.get_summary()
    print(json.dumps(summary, indent=2))
