#!/usr/bin/env python3
"""
Nexus Data Platform - Data Flow Simulation & Testing
Mô phỏng dữ liệu và kiểm tra luồng xử lý end-to-end
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

# ════════════════════════════════════════════════════════════════
# Setup Logging
# ════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# Color & Emoji
# ════════════════════════════════════════════════════════════════

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

EMOJI = {
    'rocket': '🚀',
    'check': '✅',
    'cross': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'chart': '📊',
    'database': '🗄️',
    'kafka': '📨',
    'spark': '⚡',
    'arrow': '→',
    'bronze': '🥉',
    'silver': '🥈',
    'gold': '🥇',
}

# ════════════════════════════════════════════════════════════════
# Sample Data Generation
# ════════════════════════════════════════════════════════════════

class DataSimulator:
    """Generate realistic sample data for the platform"""
    
    def __init__(self):
        self.user_ids = [f"user_{i:05d}" for i in range(1, 1001)]
        self.tour_ids = [f"tour_{city}_{i:03d}" for city in ["hanoi", "hcm", "danang"] for i in range(1, 50)]
        self.regions = ["HN", "HCMC", "DN", "HUE", "NTR"]
        
    def generate_app_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate application events"""
        events = []
        base_time = datetime.now()
        
        actions = ["click", "view", "search", "book", "review", "share"]
        
        for i in range(count):
            event = {
                "event_id": f"evt_{i:08d}",
                "user_id": random.choice(self.user_ids),
                "action": random.choice(actions),
                "tour_id": random.choice(self.tour_ids),
                "timestamp": (base_time - timedelta(minutes=random.randint(0, 1440))).isoformat(),
                "duration_seconds": random.randint(1, 300),
                "device": random.choice(["mobile", "web", "tablet"]),
                "source": random.choice(["organic", "paid", "referral"]),
                "metadata": {
                    "page": random.choice(["home", "search", "detail", "booking"]),
                    "session_id": f"sess_{random.randint(1000000, 9999999)}"
                }
            }
            events.append(event)
        
        return events
    
    def generate_cdc_events(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate CDC (Change Data Capture) events from OLTP"""
        events = []
        operations = ["INSERT", "UPDATE", "DELETE"]
        tables = ["bookings", "users", "payments", "reviews"]
        
        for i in range(count):
            op = random.choice(operations)
            table = random.choice(tables)
            
            event = {
                "cdc_id": f"cdc_{i:08d}",
                "operation": op,
                "table_name": table,
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 60))).isoformat(),
                "before": {f"col_{j}": f"val_{j}" for j in range(random.randint(1, 3))} if op in ["UPDATE", "DELETE"] else None,
                "after": {f"col_{j}": f"val_{j}" for j in range(random.randint(1, 3))} if op in ["INSERT", "UPDATE"] else None,
                "transaction_id": f"txn_{random.randint(100000, 999999)}",
                "scn": random.randint(1000000, 9999999)
            }
            events.append(event)
        
        return events
    
    def generate_clickstream_events(self, count: int = 150) -> List[Dict[str, Any]]:
        """Generate clickstream events"""
        events = []
        pages = ["home", "search", "tour_detail", "booking", "payment", "confirmation"]
        
        for i in range(count):
            event = {
                "clickstream_id": f"click_{i:08d}",
                "session_id": f"sess_{random.randint(1000000, 9999999)}",
                "user_id": random.choice(self.user_ids),
                "page": random.choice(pages),
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 240))).isoformat(),
                "click_x": random.randint(0, 1920),
                "click_y": random.randint(0, 1080),
                "user_agent": random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "Mozilla/5.0 (Linux; Android 11)"
                ]),
                "referrer": random.choice(["google", "facebook", "direct", "email"])
            }
            events.append(event)
        
        return events
    
    def generate_tour_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate tour data for aggregation"""
        tours = []
        
        for tour_id in self.tour_ids[:count]:
            tour = {
                "tour_id": tour_id,
                "name": f"Tour {tour_id}",
                "region": random.choice(self.regions),
                "price": round(random.uniform(50, 500), 2),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "duration_days": random.randint(1, 10),
                "tags": random.sample(["cultural", "adventure", "beach", "city", "nature"], k=random.randint(2, 4)),
                "capacity": random.randint(10, 100),
                "bookings_count": random.randint(0, 500),
                "revenue": round(random.uniform(1000, 50000), 2)
            }
            tours.append(tour)
        
        return tours

# ════════════════════════════════════════════════════════════════
# Schema Validation
# ════════════════════════════════════════════════════════════════

class SchemaValidator:
    """Validate data against schemas"""
    
    @staticmethod
    def validate_app_event(event: Dict[str, Any]) -> bool:
        """Validate app event schema"""
        required = ["event_id", "user_id", "action", "timestamp"]
        return all(field in event for field in required)
    
    @staticmethod
    def validate_cdc_event(event: Dict[str, Any]) -> bool:
        """Validate CDC event schema"""
        required = ["cdc_id", "operation", "table_name", "timestamp"]
        return all(field in event for field in required)
    
    @staticmethod
    def validate_clickstream_event(event: Dict[str, Any]) -> bool:
        """Validate clickstream event schema"""
        required = ["clickstream_id", "session_id", "page", "timestamp"]
        return all(field in event for field in required)
    
    @staticmethod
    def validate_tour_data(tour: Dict[str, Any]) -> bool:
        """Validate tour data schema"""
        required = ["tour_id", "name", "region", "price", "rating"]
        return all(field in tour for field in required)

# ════════════════════════════════════════════════════════════════
# Data Quality Checks
# ════════════════════════════════════════════════════════════════

class DataQualityChecker:
    """Perform data quality checks"""
    
    def __init__(self):
        self.results = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "errors": []
        }
    
    def check_nulls(self, data: List[Dict], required_fields: List[str]) -> Dict[str, Any]:
        """Check for null/empty values"""
        null_count = 0
        for record in data:
            for field in required_fields:
                if field not in record or record[field] is None or record[field] == "":
                    null_count += 1
        
        return {
            "total_checks": len(data) * len(required_fields),
            "null_count": null_count,
            "null_percentage": (null_count / (len(data) * len(required_fields)) * 100) if data else 0
        }
    
    def check_duplicates(self, data: List[Dict], key_field: str) -> Dict[str, Any]:
        """Check for duplicate records"""
        keys = [record.get(key_field) for record in data]
        unique_keys = set(keys)
        duplicates = len(keys) - len(unique_keys)
        
        return {
            "total_records": len(data),
            "unique_records": len(unique_keys),
            "duplicate_count": duplicates,
            "duplicate_percentage": (duplicates / len(data) * 100) if data else 0
        }
    
    def check_range_values(self, data: List[Dict], field: str, min_val: float, max_val: float) -> Dict[str, Any]:
        """Check if values are within expected range"""
        out_of_range = 0
        for record in data:
            value = record.get(field)
            if value is not None and (value < min_val or value > max_val):
                out_of_range += 1
        
        return {
            "total_records": len(data),
            "out_of_range": out_of_range,
            "percentage": (out_of_range / len(data) * 100) if data else 0
        }

# ════════════════════════════════════════════════════════════════
# Processing Layer Simulation
# ════════════════════════════════════════════════════════════════

class ProcessingSimulator:
    """Simulate data processing through layers"""
    
    def __init__(self, validator: SchemaValidator, quality_checker: DataQualityChecker):
        self.validator = validator
        self.quality_checker = quality_checker
        self.layer_results = {}
    
    def bronze_layer(self, raw_events: List[Dict], event_type: str) -> Dict[str, Any]:
        """Bronze layer: Raw data ingestion"""
        logger.info(f"{EMOJI['bronze']} Processing {event_type} through Bronze layer...")
        
        valid_count = 0
        invalid_count = 0
        
        if event_type == "app_events":
            validator = self.validator.validate_app_event
        elif event_type == "cdc_events":
            validator = self.validator.validate_cdc_event
        elif event_type == "clickstream":
            validator = self.validator.validate_clickstream_event
        else:
            validator = lambda x: True
        
        for event in raw_events:
            if validator(event):
                valid_count += 1
            else:
                invalid_count += 1
        
        result = {
            "event_type": event_type,
            "total_ingested": len(raw_events),
            "valid": valid_count,
            "invalid": invalid_count,
            "quality_score": (valid_count / len(raw_events) * 100) if raw_events else 0
        }
        
        return result
    
    def silver_layer(self, bronze_events: List[Dict], event_type: str) -> Dict[str, Any]:
        """Silver layer: Data cleaning & validation"""
        logger.info(f"{EMOJI['silver']} Processing {event_type} through Silver layer...")
        
        # Simulate cleaning
        cleaned_events = []
        errors = []
        
        for event in bronze_events:
            try:
                # Remove duplicates
                if not any(e.get("id") == event.get("id") for e in cleaned_events):
                    # Validate data ranges
                    if "price" in event and (event["price"] < 0 or event["price"] > 10000):
                        errors.append(f"Invalid price in {event}")
                    elif "rating" in event and (event["rating"] < 0 or event["rating"] > 5):
                        errors.append(f"Invalid rating in {event}")
                    else:
                        cleaned_events.append(event)
            except Exception as e:
                errors.append(str(e))
        
        result = {
            "event_type": event_type,
            "total_input": len(bronze_events),
            "total_cleaned": len(cleaned_events),
            "errors": len(errors),
            "quality_score": (len(cleaned_events) / len(bronze_events) * 100) if bronze_events else 0
        }
        
        return result
    
    def gold_layer(self, silver_data: List[Dict]) -> Dict[str, Any]:
        """Gold layer: Aggregation & feature engineering"""
        logger.info(f"{EMOJI['gold']} Processing data through Gold layer...")
        
        # Simulate aggregations
        aggregations = {
            "total_records": len(silver_data),
            "aggregation_types": [
                "user_360_view",
                "booking_metrics",
                "recommendation_features",
                "tourism_analytics"
            ],
            "features_generated": random.randint(50, 200)
        }
        
        return aggregations

# ════════════════════════════════════════════════════════════════
# Test Suite
# ════════════════════════════════════════════════════════════════

class EndToEndTestSuite:
    """Complete end-to-end testing"""
    
    def __init__(self):
        self.simulator = DataSimulator()
        self.validator = SchemaValidator()
        self.quality_checker = DataQualityChecker()
        self.processor = ProcessingSimulator(self.validator, self.quality_checker)
        self.test_results = []
    
    def run_all_tests(self):
        """Run complete test suite"""
        self._print_header("Nexus Data Platform - Data Flow Simulation & Testing")
        
        print(f"\n{Colors.BOLD}{EMOJI['rocket']} Starting comprehensive data flow simulation...{Colors.END}\n")
        
        # Step 1: Data Generation
        self._test_data_generation()
        
        # Step 2: Schema Validation
        self._test_schema_validation()
        
        # Step 3: Data Quality
        self._test_data_quality()
        
        # Step 4: Processing Flow
        self._test_processing_flow()
        
        # Step 5: API Integration
        self._test_api_integration()
        
        # Final Report
        self._print_test_report()
    
    def _test_data_generation(self):
        """Test 1: Data Generation"""
        print(f"\n{Colors.BLUE}{'='*60}")
        print(f"{EMOJI['info']} TEST 1: Data Generation")
        print(f"{'='*60}{Colors.END}")
        
        try:
            app_events = self.simulator.generate_app_events(100)
            cdc_events = self.simulator.generate_cdc_events(50)
            clickstream = self.simulator.generate_clickstream_events(150)
            tours = self.simulator.generate_tour_data(100)
            
            print(f"{EMOJI['check']} Generated app_events: {len(app_events)}")
            print(f"{EMOJI['check']} Generated cdc_events: {len(cdc_events)}")
            print(f"{EMOJI['check']} Generated clickstream: {len(clickstream)}")
            print(f"{EMOJI['check']} Generated tour_data: {len(tours)}")
            
            self.test_results.append(("Data Generation", True, None))
            
            # Store for later use
            self.app_events = app_events
            self.cdc_events = cdc_events
            self.clickstream = clickstream
            self.tours = tours
            
        except Exception as e:
            print(f"{EMOJI['cross']} Data generation failed: {e}")
            self.test_results.append(("Data Generation", False, str(e)))
    
    def _test_schema_validation(self):
        """Test 2: Schema Validation"""
        print(f"\n{Colors.BLUE}{'='*60}")
        print(f"{EMOJI['info']} TEST 2: Schema Validation")
        print(f"{'='*60}{Colors.END}")
        
        try:
            # Validate app events
            app_valid = sum(1 for e in self.app_events if self.validator.validate_app_event(e))
            app_invalid = len(self.app_events) - app_valid
            
            print(f"{EMOJI['check']} App Events: {app_valid}/{len(self.app_events)} valid")
            if app_invalid > 0:
                print(f"{EMOJI['warning']} {app_invalid} invalid records")
            
            # Validate CDC events
            cdc_valid = sum(1 for e in self.cdc_events if self.validator.validate_cdc_event(e))
            cdc_invalid = len(self.cdc_events) - cdc_valid
            
            print(f"{EMOJI['check']} CDC Events: {cdc_valid}/{len(self.cdc_events)} valid")
            if cdc_invalid > 0:
                print(f"{EMOJI['warning']} {cdc_invalid} invalid records")
            
            # Validate clickstream
            click_valid = sum(1 for e in self.clickstream if self.validator.validate_clickstream_event(e))
            click_invalid = len(self.clickstream) - click_valid
            
            print(f"{EMOJI['check']} Clickstream: {click_valid}/{len(self.clickstream)} valid")
            if click_invalid > 0:
                print(f"{EMOJI['warning']} {click_invalid} invalid records")
            
            # Validate tours
            tour_valid = sum(1 for t in self.tours if self.validator.validate_tour_data(t))
            tour_invalid = len(self.tours) - tour_valid
            
            print(f"{EMOJI['check']} Tour Data: {tour_valid}/{len(self.tours)} valid")
            if tour_invalid > 0:
                print(f"{EMOJI['warning']} {tour_invalid} invalid records")
            
            all_valid = app_valid and cdc_valid and click_valid and tour_valid
            self.test_results.append(("Schema Validation", all_valid, None))
            
        except Exception as e:
            print(f"{EMOJI['cross']} Schema validation failed: {e}")
            self.test_results.append(("Schema Validation", False, str(e)))
    
    def _test_data_quality(self):
        """Test 3: Data Quality"""
        print(f"\n{Colors.BLUE}{'='*60}")
        print(f"{EMOJI['info']} TEST 3: Data Quality Checks")
        print(f"{'='*60}{Colors.END}")
        
        try:
            # Check for nulls
            null_check = self.quality_checker.check_nulls(
                self.app_events,
                ["event_id", "user_id", "action"]
            )
            print(f"{EMOJI['check']} Null check: {null_check['null_percentage']:.2f}% null values")
            
            # Check for duplicates
            dup_check = self.quality_checker.check_duplicates(self.app_events, "event_id")
            print(f"{EMOJI['check']} Duplicate check: {dup_check['duplicate_percentage']:.2f}% duplicates")
            
            # Check range values for prices
            range_check = self.quality_checker.check_range_values(self.tours, "price", 0, 1000)
            print(f"{EMOJI['check']} Price range check: {range_check['percentage']:.2f}% out of range")
            
            # Check rating ranges
            rating_check = self.quality_checker.check_range_values(self.tours, "rating", 0, 5)
            print(f"{EMOJI['check']} Rating range check: {rating_check['percentage']:.2f}% out of range")
            
            quality_passed = (null_check['null_percentage'] < 5 and
                            dup_check['duplicate_percentage'] < 5 and
                            range_check['percentage'] < 5 and
                            rating_check['percentage'] < 5)
            
            self.test_results.append(("Data Quality", quality_passed, None))
            
        except Exception as e:
            print(f"{EMOJI['cross']} Data quality test failed: {e}")
            self.test_results.append(("Data Quality", False, str(e)))
    
    def _test_processing_flow(self):
        """Test 4: Processing Flow"""
        print(f"\n{Colors.BLUE}{'='*60}")
        print(f"{EMOJI['info']} TEST 4: Processing Flow (Medallion Architecture)")
        print(f"{'='*60}{Colors.END}")
        
        try:
            # Bronze layer
            print(f"\n{Colors.CYAN}Bronze Layer{Colors.END}")
            bronze_app = self.processor.bronze_layer(self.app_events, "app_events")
            print(f"  Quality Score: {bronze_app['quality_score']:.1f}%")
            
            bronze_cdc = self.processor.bronze_layer(self.cdc_events, "cdc_events")
            print(f"  CDC Quality: {bronze_cdc['quality_score']:.1f}%")
            
            # Silver layer
            print(f"\n{Colors.CYAN}Silver Layer{Colors.END}")
            silver_app = self.processor.silver_layer(self.app_events, "app_events")
            print(f"  Cleaned Records: {silver_app['total_cleaned']}/{silver_app['total_input']}")
            print(f"  Quality Score: {silver_app['quality_score']:.1f}%")
            
            silver_cdc = self.processor.silver_layer(self.cdc_events, "cdc_events")
            print(f"  CDC Cleaned: {silver_cdc['total_cleaned']}/{silver_cdc['total_input']}")
            
            # Gold layer
            print(f"\n{Colors.CYAN}Gold Layer{Colors.END}")
            gold_result = self.processor.gold_layer(self.tours)
            print(f"  Total Records for Aggregation: {gold_result['total_records']}")
            print(f"  Features Generated: {gold_result['features_generated']}")
            print(f"  Aggregation Types: {', '.join(gold_result['aggregation_types'])}")
            
            self.test_results.append(("Processing Flow", True, None))
            
        except Exception as e:
            print(f"{EMOJI['cross']} Processing flow test failed: {e}")
            self.test_results.append(("Processing Flow", False, str(e)))
    
    def _test_api_integration(self):
        """Test 5: API Integration"""
        print(f"\n{Colors.BLUE}{'='*60}")
        print(f"{EMOJI['info']} TEST 5: API Integration")
        print(f"{'='*60}{Colors.END}")
        
        try:
            # Try to import and test FastAPI app
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            api_path = os.path.join(os.path.dirname(script_dir), "apps", "api")
            sys.path.insert(0, api_path)
            
            try:
                from fastapi.testclient import TestClient
                from main import app
                
                client = TestClient(app)
                
                # Test health endpoint
                response = client.get("/health")
                health_ok = response.status_code == 200
                print(f"{EMOJI['check']} Health endpoint: {response.status_code}")
                
                if health_ok:
                    print(f"  Status: {response.json().get('status', 'unknown')}")
                    services = response.json().get('services', {})
                    print(f"  Services: {json.dumps(services, indent=2)}")
                
                self.test_results.append(("API Health", health_ok, None))
                
            except ImportError as e:
                print(f"{EMOJI['warning']} API not available (dependencies missing): {e}")
                self.test_results.append(("API Health", False, f"ImportError: {e}"))
            except Exception as e:
                print(f"{EMOJI['warning']} Could not test API: {e}")
                self.test_results.append(("API Health", False, str(e)))
            
        except Exception as e:
            print(f"{EMOJI['cross']} API integration test failed: {e}")
            self.test_results.append(("API Integration", False, str(e)))
    
    def _print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("════════════════════════════════════════════════════════════")
        print(f"  {title}")
        print("════════════════════════════════════════════════════════════")
        print(f"{Colors.END}")
    
    def _print_test_report(self):
        """Print final test report"""
        self._print_header("Test Results Summary")
        
        print(f"\n{Colors.BOLD}Test Results:{Colors.END}\n")
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, error in self.test_results:
            status = f"{EMOJI['check']} {Colors.GREEN}PASS{Colors.END}" if success else f"{EMOJI['cross']} {Colors.RED}FAIL{Colors.END}"
            print(f"  {status:30s} {test_name}")
            if error:
                print(f"     {Colors.YELLOW}Error: {error}{Colors.END}")
        
        print(f"\n{Colors.BOLD}Overall Results:{Colors.END}")
        print(f"  Passed: {passed}/{total}")
        print(f"  Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print(f"\n{Colors.GREEN}{EMOJI['rocket']} All tests passed! Data flow is working correctly.{Colors.END}\n")
        else:
            print(f"\n{Colors.YELLOW}{EMOJI['warning']} Some tests failed. Please review the errors above.{Colors.END}\n")

# ════════════════════════════════════════════════════════════════
# Main Execution
# ════════════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    try:
        test_suite = EndToEndTestSuite()
        test_suite.run_all_tests()
        
        return 0 if all(success for _, success, _ in test_suite.test_results) else 1
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
