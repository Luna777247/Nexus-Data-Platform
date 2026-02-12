"""
Data Quality Checker using Great Expectations
Integrates with Spark DataFrames for validation
"""

from great_expectations.core import ExpectationSuite, ExpectationConfiguration
from great_expectations.dataset import SparkDFDataset
from pyspark.sql import DataFrame
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """
    Data Quality validation using Great Expectations
    Supports Bronze, Silver, and Gold layer validations
    """
    
    def __init__(self, layer: str = "bronze"):
        """
        Initialize Quality Checker
        
        Args:
            layer: Data lake layer (bronze/silver/gold)
        """
        self.layer = layer
        self.validation_results = []
        
    def validate_schema(
        self, 
        df: DataFrame, 
        expected_columns: List[str],
        dataset_name: str
    ) -> Dict:
        """
        Validate DataFrame schema
        
        Args:
            df: Spark DataFrame to validate
            expected_columns: List of expected column names
            dataset_name: Name of the dataset for reporting
            
        Returns:
            Validation result dict
        """
        logger.info(f"🔍 Validating schema for {dataset_name}...")
        
        result = {
            "dataset": dataset_name,
            "layer": self.layer,
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "success": True
        }
        
        # Check 1: All expected columns exist
        actual_columns = set(df.columns)
        expected_columns_set = set(expected_columns)
        
        missing_columns = expected_columns_set - actual_columns
        extra_columns = actual_columns - expected_columns_set
        
        if missing_columns:
            result["success"] = False
            result["checks"].append({
                "check": "expected_columns_exist",
                "status": "FAILED",
                "message": f"Missing columns: {missing_columns}"
            })
        else:
            result["checks"].append({
                "check": "expected_columns_exist",
                "status": "PASSED",
                "message": "All expected columns present"
            })
            
        if extra_columns:
            result["checks"].append({
                "check": "no_extra_columns",
                "status": "WARNING",
                "message": f"Extra columns found: {extra_columns}"
            })
        
        self.validation_results.append(result)
        return result
    
    def validate_data_quality(
        self,
        df: DataFrame,
        dataset_name: str,
        rules: Optional[Dict] = None
    ) -> Dict:
        """
        Run data quality checks on DataFrame
        
        Args:
            df: Spark DataFrame
            dataset_name: Name of dataset
            rules: Custom validation rules
            
        Returns:
            Validation result
        """
        logger.info(f"🔍 Running data quality checks for {dataset_name}...")
        
        result = {
            "dataset": dataset_name,
            "layer": self.layer,
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "success": True,
            "row_count": df.count()
        }
        
        # Check 1: No empty DataFrame
        if result["row_count"] == 0:
            result["success"] = False
            result["checks"].append({
                "check": "non_empty_dataset",
                "status": "FAILED",
                "message": "DataFrame is empty"
            })
            return result
        else:
            result["checks"].append({
                "check": "non_empty_dataset",
                "status": "PASSED",
                "message": f"Dataset contains {result['row_count']} rows"
            })
        
        # Check 2: No duplicate rows (based on all columns)
        total_rows = df.count()
        distinct_rows = df.distinct().count()
        duplicate_count = total_rows - distinct_rows
        
        if duplicate_count > 0:
            duplicate_percentage = (duplicate_count / total_rows) * 100
            if duplicate_percentage > 5:  # Threshold: 5%
                result["success"] = False
                result["checks"].append({
                    "check": "duplicate_rows",
                    "status": "FAILED",
                    "message": f"{duplicate_count} duplicates ({duplicate_percentage:.2f}%)"
                })
            else:
                result["checks"].append({
                    "check": "duplicate_rows",
                    "status": "WARNING",
                    "message": f"{duplicate_count} duplicates ({duplicate_percentage:.2f}%)"
                })
        else:
            result["checks"].append({
                "check": "duplicate_rows",
                "status":  "PASSED",
                "message": "No duplicate rows"
            })
        
        # Check 3: Null value analysis
        null_counts = {}
        for column in df.columns:
            null_count = df.filter(df[column].isNull()).count()
            if null_count > 0:
                null_percentage = (null_count / total_rows) * 100
                null_counts[column] = {
                    "count": null_count,
                    "percentage": null_percentage
                }
        
        if null_counts:
            critical_nulls = {col: info for col, info in null_counts.items() 
                            if info["percentage"] > 50}
            if critical_nulls:
                result["success"] = False
                result["checks"].append({
                    "check": "null_values",
                    "status": "FAILED",
                    "message": f"Critical null values in: {list(critical_nulls.keys())}"
                })
            else:
                result["checks"].append({
                    "check": "null_values",
                    "status": "WARNING",
                    "message": f"Null values in: {list(null_counts.keys())}"
                })
        else:
            result["checks"].append({
                "check": "null_values",
                "status": "PASSED",
                "message": "No null values"
            })
        
        # Apply custom rules if provided
        if rules:
            for rule_name, rule_config in rules.items():
                rule_result = self._apply_custom_rule(df, rule_name, rule_config)
                result["checks"].append(rule_result)
                if rule_result["status"] == "FAILED":
                    result["success"] = False
        
        self.validation_results.append(result)
        return result
    
    def _apply_custom_rule(
        self,
        df: DataFrame,
        rule_name: str,
        rule_config: Dict
    ) -> Dict:
        """Apply custom validation rule"""
        # Example: Check value ranges
        if rule_config.get("type") == "range":
            column = rule_config["column"]
            min_val = rule_config.get("min")
            max_val = rule_config.get("max")
            
            if min_val is not None:
                invalid_count = df.filter(df[column] < min_val).count()
                if invalid_count > 0:
                    return {
                        "check": rule_name,
                        "status": "FAILED",
                        "message": f"{invalid_count} rows below minimum {min_val}"
                    }
            
            if max_val is not None:
                invalid_count = df.filter(df[column] > max_val).count()
                if invalid_count > 0:
                    return {
                        "check": rule_name,
                        "status": "FAILED",
                        "message": f"{invalid_count} rows above maximum {max_val}"
                    }
        
        return {
            "check": rule_name,
            "status": "PASSED",
            "message": "Rule passed"
        }
    
    def get_quality_score(self) -> float:
        """
        Calculate overall quality score (0-100)
        Based on passed checks vs total checks
        """
        if not self.validation_results:
            return 0.0
        
        total_checks = 0
        passed_checks = 0
        
        for result in self.validation_results:
            for check in result["checks"]:
                total_checks += 1
                if check["status"] == "PASSED":
                    passed_checks += 1
        
        if total_checks == 0:
            return 0.0
        
        return (passed_checks / total_checks) * 100
    
    def emit_metrics(self) -> Dict:
        """
        Emit metrics for Prometheus
        Returns metrics in format ready for push gateway
        """
        quality_score = self.get_quality_score()
        
        metrics = {
            "data_quality_score": quality_score,
            "layer": self.layer,
            "total_validations": len(self.validation_results),
            "failed_validations": sum(
                1 for r in self.validation_results if not r["success"]
            ),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Quality Score: {quality_score:.2f}%")
        return metrics
    
    def generate_report(self) -> str:
        """Generate human-readable quality report"""
        report = [
            "=" * 60,
            f"DATA QUALITY REPORT - {self.layer.upper()} LAYER",
            "=" * 60,
            f"Overall Quality Score: {self.get_quality_score():.2f}%",
            f"Total Datasets Validated: {len(self.validation_results)}",
            ""
        ]
        
        for result in self.validation_results:
            report.append(f"\n📦 Dataset: {result['dataset']}")
            report.append(f"   Status: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            report.append(f"   Row Count: {result.get('row_count', 'N/A')}")
            report.append("   Checks:")
            
            for check in result["checks"]:
                status_icon = {
                    "PASSED": "✅",
                    "FAILED": "❌",
                    "WARNING": "⚠️"
                }.get(check["status"], "❓")
                
                report.append(f"     {status_icon} {check['check']}: {check['message']}")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)
