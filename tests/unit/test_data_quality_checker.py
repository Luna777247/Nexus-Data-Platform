"""
Unit Tests for Data Quality Checker
"""

import pytest
from datetime import datetime, timedelta
from pipelines.airflow.utils.data_quality_checker import DataQualityChecker


class TestCompletenessCheck:
    """Test completeness validation"""
    
    def test_all_fields_complete(self):
        """Test when all required fields are present"""
        checker = DataQualityChecker()
        data = [
            {"id": 1, "name": "User1", "email": "user1@example.com"},
            {"id": 2, "name": "User2", "email": "user2@example.com"},
            {"id": 3, "name": "User3", "email": "user3@example.com"},
        ]
        
        result = checker.check_completeness(data, ["id", "name", "email"])
        
        assert result["passed"] is True
        assert result["completion_rates"]["id"] == 100.0
        assert result["completion_rates"]["name"] == 100.0
        assert result["completion_rates"]["email"] == 100.0
    
    def test_missing_fields(self):
        """Test when some fields are missing"""
        checker = DataQualityChecker(config={'completeness_threshold': 95})
        data = [
            {"id": 1, "name": "User1", "email": "user1@example.com"},
            {"id": 2, "name": None, "email": "user2@example.com"},  # Missing name
            {"id": 3, "name": "User3", "email": ""},  # Empty email
        ]
        
        result = checker.check_completeness(data, ["id", "name", "email"])
        
        assert result["passed"] is False
        assert result["missing_counts"]["name"] == 1
        assert result["missing_counts"]["email"] == 1
    
    def test_empty_dataset(self):
        """Test with empty dataset"""
        checker = DataQualityChecker()
        result = checker.check_completeness([], ["id", "name"])
        
        assert result["total_records"] == 0


class TestUniquenessCheck:
    """Test uniqueness validation"""
    
    def test_all_unique_values(self):
        """Test when all values are unique"""
        checker = DataQualityChecker()
        data = [
            {"id": 1, "email": "user1@example.com"},
            {"id": 2, "email": "user2@example.com"},
            {"id": 3, "email": "user3@example.com"},
        ]
        
        result = checker.check_uniqueness(data, ["id", "email"])
        
        assert result["passed"] is True
        assert result["duplicate_info"]["id"]["duplicates"] == 0
        assert result["duplicate_info"]["email"]["duplicates"] == 0
    
    def test_duplicate_values(self):
        """Test when duplicates exist"""
        checker = DataQualityChecker(config={'duplicate_threshold': 1.0})
        data = [
            {"id": 1, "email": "user1@example.com"},
            {"id": 2, "email": "user2@example.com"},
            {"id": 2, "email": "user2@example.com"},  # Duplicate
            {"id": 3, "email": "user1@example.com"},  # Duplicate email
        ]
        
        result = checker.check_uniqueness(data, ["id", "email"])
        
        assert result["passed"] is False  # Exceeds threshold
        assert result["duplicate_info"]["id"]["duplicates"] > 0
        assert result["duplicate_info"]["email"]["duplicates"] > 0


class TestRangeCheck:
    """Test range validation"""
    
    def test_values_in_range(self):
        """Test when all values are within range"""
        checker = DataQualityChecker()
        data = [
            {"id": 1, "age": 25},
            {"id": 2, "age": 30},
            {"id": 3, "age": 22},
        ]
        
        result = checker.check_range(data, "age", 18, 100)
        
        assert result["passed"] is True
        assert result["out_of_range_count"] == 0
    
    def test_values_out_of_range(self):
        """Test when values are out of range"""
        checker = DataQualityChecker(config={'range_threshold': 5.0})
        data = [
            {"id": 1, "age": 25},
            {"id": 2, "age": 15},  # Below minimum
            {"id": 3, "age": 105},  # Above maximum
            {"id": 4, "age": 30},
        ]
        
        result = checker.check_range(data, "age", 18, 100)
        
        assert result["out_of_range_count"] == 2
        assert result["out_of_range_percentage"] == 50.0


class TestSchemaCheck:
    """Test schema validation"""
    
    def test_correct_schema(self):
        """Test when data matches expected schema"""
        checker = DataQualityChecker()
        data = [
            {"id": 1, "name": "User1", "age": 25},
            {"id": 2, "name": "User2", "age": 30},
        ]
        
        expected_schema = {
            "id": "int",
            "name": "str",
            "age": "int"
        }
        
        result = checker.check_schema(data, expected_schema)
        
        assert result["passed"] is True
        assert all(count == 0 for count in result["type_mismatches"].values())
    
    def test_schema_mismatch(self):
        """Test when data doesn't match schema"""
        checker = DataQualityChecker(config={'schema_threshold': 2.0})
        data = [
            {"id": 1, "name": "User1", "age": "twenty-five"},  # Wrong type
            {"id": "2", "name": "User2", "age": 30},  # Wrong type for id
        ]
        
        expected_schema = {
            "id": "int",
            "name": "str",
            "age": "int"
        }
        
        result = checker.check_schema(data, expected_schema)
        
        assert result["passed"] is False
        assert result["type_mismatches"]["age"] > 0


class TestFreshnessCheck:
    """Test data freshness validation"""
    
    def test_fresh_data(self):
        """Test when data is fresh"""
        checker = DataQualityChecker()
        now = datetime.now()
        data = [
            {"id": 1, "timestamp": now.isoformat()},
            {"id": 2, "timestamp": (now - timedelta(hours=1)).isoformat()},
            {"id": 3, "timestamp": (now - timedelta(hours=2)).isoformat()},
        ]
        
        result = checker.check_freshness(data, "timestamp", max_age_hours=24)
        
        assert result["passed"] is True
        assert result["stale_records"] == 0
    
    def test_stale_data(self):
        """Test when data is stale"""
        checker = DataQualityChecker(config={'freshness_threshold': 10.0})
        now = datetime.now()
        data = [
            {"id": 1, "timestamp": (now - timedelta(hours=48)).isoformat()},  # Stale
            {"id": 2, "timestamp": (now - timedelta(hours=36)).isoformat()},  # Stale
            {"id": 3, "timestamp": (now - timedelta(hours=12)).isoformat()},  # Fresh
        ]
        
        result = checker.check_freshness(data, "timestamp", max_age_hours=24)
        
        assert result["stale_records"] == 2
        assert result["stale_percentage"] > 50


class TestSummaryGeneration:
    """Test summary and reporting"""
    
    def test_summary_all_passed(self):
        """Test summary when all checks pass"""
        checker = DataQualityChecker()
        data = [
            {"id": 1, "name": "User1", "age": 25},
            {"id": 2, "name": "User2", "age": 30},
        ]
        
        checker.check_completeness(data, ["id", "name"])
        checker.check_uniqueness(data, ["id"])
        checker.check_range(data, "age", 18, 100)
        
        summary = checker.get_summary()
        
        assert summary["total_checks"] == 3
        assert summary["passed"] == 3
        assert summary["failed"] == 0
        assert summary["success_rate"] == 100.0
    
    def test_summary_some_failed(self):
        """Test summary when some checks fail"""
        checker = DataQualityChecker(config={'range_threshold': 5.0})
        data = [
            {"id": 1, "name": None, "age": 15},  # Incomplete, out of range
            {"id": 2, "name": "User2", "age": 30},
        ]
        
        checker.check_completeness(data, ["id", "name"])  # Fails
        checker.check_range(data, "age", 18, 100)  # Fails
        
        summary = checker.get_summary()
        
        assert summary["failed"] >= 1
        assert summary["success_rate"] < 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
