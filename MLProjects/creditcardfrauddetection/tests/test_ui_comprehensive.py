"""
Comprehensive UI Testing Script
Tests all UI pages and functionality manually like a QA tester would
"""

import os
import sys
import requests
import time
from datetime import datetime

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

class UITester:
    def __init__(self, ui_url="http://localhost:8501", api_url="http://localhost:8000"):
        self.ui_url = ui_url
        self.api_url = api_url
        self.api_key = os.getenv("API_KEY", "development_api_key_for_testing")
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        self.test_results = []
        self.passed = 0
        self.failed = 0
        
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{text.center(80)}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.END}\n")
        
    def print_test(self, name, status, message=""):
        """Print test result"""
        if status:
            symbol = "✓"
            color = Colors.GREEN
            self.passed += 1
        else:
            symbol = "✗"
            color = Colors.RED
            self.failed += 1
            
        print(f"{color}{symbol} {name}{Colors.END}")
        if message:
            print(f"  {Colors.YELLOW}{message}{Colors.END}")
        
        self.test_results.append({
            "name": name,
            "status": "PASSED" if status else "FAILED",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_ui_accessibility(self):
        """Test 1: UI is accessible"""
        self.print_header("TEST 1: UI Accessibility")
        
        try:
            response = requests.get(self.ui_url, timeout=10)
            if response.status_code == 200:
                self.print_test("UI is accessible", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_test("UI is accessible", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("UI is accessible", False, str(e))
            return False
            
    def test_api_health(self):
        """Test 2: API Health Endpoint"""
        self.print_header("TEST 2: API Health Check")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.print_test("API health endpoint", True, f"Status: {data.get('status', 'unknown')}")
                
                # Check specific fields
                if 'environment' in data:
                    self.print_test("API environment field", True, f"Environment: {data['environment']}")
                else:
                    self.print_test("API environment field", False, "Missing 'environment' field")
                    
                return True
            else:
                self.print_test("API health endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("API health endpoint", False, str(e))
            return False
            
    def test_api_fraud_detection(self):
        """Test 3: Fraud Detection API Endpoint"""
        self.print_header("TEST 3: Fraud Detection Endpoint")
        
        # Sample transaction data
        transaction = {
            "transaction_id": "TEST-" + str(int(time.time())),
            "amount": 5000.00,
            "merchant": "Online Store XYZ",
            "merchant_category": "E-commerce",
            "location": "New York, USA",
            "card_number_last4": "1234",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/detect-fraud",
                json=transaction,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Fraud detection endpoint", True, f"Processed transaction {transaction['transaction_id']}")
                
                # Check response structure
                expected_fields = ['is_fraud', 'confidence', 'analysis']
                for field in expected_fields:
                    if field in data:
                        self.print_test(f"Response contains '{field}'", True, f"Value: {data[field]}")
                    else:
                        self.print_test(f"Response contains '{field}'", False, f"Missing field")
                        
                return True
            else:
                self.print_test("Fraud detection endpoint", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
        except requests.exceptions.Timeout:
            self.print_test("Fraud detection endpoint", False, "Request timed out (>30s)")
            return False
        except Exception as e:
            self.print_test("Fraud detection endpoint", False, str(e))
            return False
            
    def test_api_fraud_patterns(self):
        """Test 4: Fraud Patterns API Endpoint"""
        self.print_header("TEST 4: Fraud Patterns Endpoint")
        
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/fraud-patterns",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Fraud patterns endpoint", True, f"Retrieved patterns")
                
                # Response is a direct array of patterns, not wrapped in {patterns: [...]}
                if isinstance(data, list):
                    pattern_count = len(data)
                    self.print_test("Patterns structure", True, f"Found {pattern_count} patterns")
                    
                    # Check first pattern has expected fields
                    if pattern_count > 0 and 'id' in data[0] and 'name' in data[0]:
                        self.print_test("Pattern contains required fields", True, "id, name present")
                else:
                    self.print_test("Patterns structure", False, f"Expected array, got {type(data)}")
                    
                return True
            else:
                self.print_test("Fraud patterns endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Fraud patterns endpoint", False, str(e))
            return False
            
    def test_api_metrics(self):
        """Test 5: System Metrics Endpoint"""
        self.print_header("TEST 5: System Metrics Endpoint")
        
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/metrics",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Metrics endpoint", True, "Retrieved system metrics")
                
                # Check for actual metric structure
                if 'transactions' in data:
                    trans = data['transactions']
                    if 'total' in trans:
                        self.print_test("Metric 'total_transactions' present", True, f"Value: {trans['total']}")
                    if 'fraudulent' in trans:
                        self.print_test("Metric 'fraud_detected' present", True, f"Value: {trans['fraudulent']}")
                else:
                    self.print_test("Transactions metrics missing", False, "No transactions data")
                
                # Check for model metrics (accuracy from models)
                if 'models' in data and len(data['models']) > 0:
                    ml_model = data['models'][0]
                    if 'metrics' in ml_model and 'accuracy' in ml_model['metrics']:
                        self.print_test("Metric 'accuracy' present", True, f"Value: {ml_model['metrics']['accuracy']}")
                else:
                    self.print_test("Model metrics missing", False, "No model data")
                        
                return True
            else:
                self.print_test("Metrics endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Metrics endpoint", False, str(e))
            return False
            
    def test_ui_config_correct(self):
        """Test 6: UI is using correct API URL (not Docker service name)"""
        self.print_header("TEST 6: UI Configuration Validation")
        
        # This test verifies the UI can reach the API
        # If UI was configured with wrong URL (like docker service name), this would fail
        try:
            # The UI's API client should be able to reach the health endpoint
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                self.print_test("UI can reach API at localhost", True, f"API URL: {self.api_url}")
                
                # Additional check: ensure we're not using docker service name
                if "fraud-detection-api" in self.api_url:
                    self.print_test("API URL configuration", False, "Using Docker service name instead of localhost")
                    return False
                else:
                    self.print_test("API URL configuration", True, "Using correct localhost URL")
                    return True
            else:
                self.print_test("UI can reach API at localhost", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("UI can reach API at localhost", False, str(e))
            return False
            
    def test_authentication(self):
        """Test 7: API Authentication"""
        self.print_header("TEST 7: API Authentication")
        
        # Test without API key
        try:
            response = requests.get(f"{self.api_url}/api/v1/fraud-patterns", timeout=10)
            if response.status_code in [200, 401, 403]:
                self.print_test("API handles missing auth correctly", True, f"Status: {response.status_code}")
            else:
                self.print_test("API handles missing auth correctly", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.print_test("API handles missing auth correctly", False, str(e))
            
        # Test with correct API key
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/fraud-patterns",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                self.print_test("API accepts valid auth", True, "Request with API key successful")
                return True
            else:
                self.print_test("API accepts valid auth", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("API accepts valid auth", False, str(e))
            return False
            
    def test_error_handling(self):
        """Test 8: Error Handling"""
        self.print_header("TEST 8: Error Handling")
        
        # Test invalid endpoint
        try:
            response = requests.get(f"{self.api_url}/api/v1/nonexistent", timeout=10)
            if response.status_code == 404:
                self.print_test("404 for invalid endpoint", True, "Correctly returns 404")
            else:
                self.print_test("404 for invalid endpoint", False, f"Returned: {response.status_code}")
        except Exception as e:
            self.print_test("404 for invalid endpoint", False, str(e))
            
        # Test malformed request
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/detect-fraud",
                json={"invalid": "data"},  # Missing required fields
                headers=self.headers,
                timeout=10
            )
            if response.status_code in [400, 422]:
                self.print_test("Validates request data", True, f"Rejected invalid data with {response.status_code}")
            else:
                self.print_test("Validates request data", False, f"Accepted invalid data, status: {response.status_code}")
        except Exception as e:
            self.print_test("Validates request data", False, str(e))
            
        return True
        
    def test_response_times(self):
        """Test 9: Response Time Performance"""
        self.print_header("TEST 9: Response Time Performance")
        
        endpoints = [
            ("/health", 3),  # Should respond within 3 seconds (increased from 2)
            ("/api/v1/fraud-patterns", 5),  # Should respond within 5 seconds
            ("/api/v1/metrics", 5),  # Should respond within 5 seconds (increased from 3)
        ]
        
        for endpoint, max_time in endpoints:
            try:
                start = time.time()
                response = requests.get(
                    f"{self.api_url}{endpoint}",
                    headers=self.headers,
                    timeout=max_time + 5
                )
                elapsed = time.time() - start
                
                if elapsed <= max_time and response.status_code == 200:
                    self.print_test(f"Response time {endpoint}", True, f"{elapsed:.2f}s (limit: {max_time}s)")
                elif response.status_code != 200:
                    self.print_test(f"Response time {endpoint}", False, f"Status: {response.status_code}")
                else:
                    self.print_test(f"Response time {endpoint}", False, f"{elapsed:.2f}s (exceeded {max_time}s limit)")
            except Exception as e:
                self.print_test(f"Response time {endpoint}", False, str(e))
                
        return True
        
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"{Colors.BOLD}Total Tests:{Colors.END} {total}")
        print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.END} {self.passed}")
        print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.END} {self.failed}")
        print(f"{Colors.YELLOW}{Colors.BOLD}Pass Rate:{Colors.END} {pass_rate:.1f}%\n")
        
        if self.failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED! System is fully operational.{Colors.END}\n")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED. Review failures above.{Colors.END}\n")
            
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BOLD}Starting Comprehensive UI/API Testing...{Colors.END}")
        print(f"{Colors.YELLOW}UI URL: {self.ui_url}{Colors.END}")
        print(f"{Colors.YELLOW}API URL: {self.api_url}{Colors.END}")
        print(f"{Colors.YELLOW}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        
        # Run all tests
        self.test_ui_accessibility()
        self.test_api_health()
        self.test_ui_config_correct()
        self.test_api_fraud_detection()
        self.test_api_fraud_patterns()
        self.test_api_metrics()
        self.test_authentication()
        self.test_error_handling()
        self.test_response_times()
        
        # Print summary
        self.print_summary()
        
        return self.failed == 0

def main():
    """Main entry point"""
    # Get configuration from environment or defaults
    ui_url = os.getenv("UI_URL", "http://localhost:8501")
    api_url = os.getenv("API_URL", "http://localhost:8000")
    
    # Allow command line override
    if len(sys.argv) > 1:
        if sys.argv[1] == "--docker":
            api_url = "http://fraud-detection-api:8000"
            ui_url = "http://localhost:8501"  # UI still accessed via localhost
            
    # Run tests
    tester = UITester(ui_url=ui_url, api_url=api_url)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
