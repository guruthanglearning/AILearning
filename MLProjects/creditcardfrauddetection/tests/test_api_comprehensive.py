"""
Comprehensive API Endpoint Testing
Tests all API endpoints with various scenarios
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any
import os


class APIEndpointTester:
    """Comprehensive API endpoint testing"""
    
    def __init__(self, api_url="http://localhost:8000", api_key="development_api_key_for_testing"):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        self.results = {
            "test_suite": "API Endpoint Tests",
            "timestamp": datetime.now().isoformat(),
            "api_url": api_url,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "tests": []
        }
    
    def log_test(self, test_name, status, message, details=None):
        """Log test result"""
        self.results["total_tests"] += 1
        
        if status == "PASSED":
            self.results["passed"] += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.results["failed"] += 1
            print(f"❌ {test_name}: FAILED - {message}")
        
        self.results["tests"].append({
            "name": test_name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def test_health_endpoint(self):
        """Test 1: Health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Endpoint", "PASSED", 
                                 "API is healthy", 
                                 {"response": data})
                    return True
                else:
                    self.log_test("Health Endpoint", "FAILED", 
                                 f"Unexpected status: {data.get('status')}")
                    return False
            else:
                self.log_test("Health Endpoint", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Endpoint", "FAILED", str(e))
            return False
    
    def test_api_v1_health_endpoint(self):
        """Test 2: API v1 health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/health", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("API v1 Health Endpoint", "PASSED", 
                             "API v1 health check successful", 
                             {"response": data})
                return True
            else:
                self.log_test("API v1 Health Endpoint", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API v1 Health Endpoint", "FAILED", str(e))
            return False
    
    def test_metrics_endpoint(self):
        """Test 3: Metrics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/metrics", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Metrics Endpoint", "PASSED", 
                             "Metrics retrieved successfully", 
                             {"metrics_keys": list(data.keys()) if isinstance(data, dict) else "list"})
                return True
            else:
                self.log_test("Metrics Endpoint", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Metrics Endpoint", "FAILED", str(e))
            return False
    
    def test_fraud_patterns_list(self):
        """Test 4: Get fraud patterns list"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/fraud-patterns", 
                                   headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                pattern_count = len(data) if isinstance(data, list) else 0
                self.log_test("Fraud Patterns List", "PASSED", 
                             f"Retrieved {pattern_count} fraud patterns", 
                             {"count": pattern_count})
                return True
            else:
                self.log_test("Fraud Patterns List", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Fraud Patterns List", "FAILED", str(e))
            return False
    
    def test_transaction_analysis_legitimate(self):
        """Test 5: Analyze legitimate transaction"""
        transaction = {
            "transaction_id": f"test_legit_{int(time.time())}",
            "card_id": "card_1234567",
            "customer_id": "cust_12345",
            "merchant_id": "merch_67890",
            "merchant_name": "Local Grocery Store",
            "merchant_category": "Groceries",
            "merchant_country": "US",
            "merchant_zip": "10001",
            "amount": 45.50,
            "currency": "USD",
            "timestamp": datetime.now().isoformat(),
            "is_online": False,
            "device_id": "dev_regular123",
            "ip_address": "192.168.1.100",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        try:
            response = requests.post(f"{self.api_url}/api/v1/analyze-transaction", 
                                    json=transaction, 
                                    headers=self.headers, 
                                    timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                is_fraud = data.get("is_fraud", False)
                confidence = data.get("confidence_score", 0)
                
                if not is_fraud and confidence < 0.5:
                    self.log_test("Transaction Analysis - Legitimate", "PASSED", 
                                 f"Correctly identified as legitimate (confidence: {confidence})", 
                                 {"result": data})
                    return True
                else:
                    self.log_test("Transaction Analysis - Legitimate", "FAILED", 
                                 f"Misclassified (is_fraud: {is_fraud}, confidence: {confidence})")
                    return False
            else:
                self.log_test("Transaction Analysis - Legitimate", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Transaction Analysis - Legitimate", "FAILED", str(e))
            return False
    
    def test_transaction_analysis_suspicious(self):
        """Test 6: Analyze suspicious transaction"""
        transaction = {
            "transaction_id": f"test_fraud_{int(time.time())}",
            "card_id": "card_9876543",
            "customer_id": "cust_54321",
            "merchant_id": "merch_99999",
            "merchant_name": "Suspicious Electronics",
            "merchant_category": "Electronics",
            "merchant_country": "NG",  # High-risk country
            "merchant_zip": "00000",
            "amount": 2999.99,  # High amount
            "currency": "USD",
            "timestamp": datetime.now().isoformat(),
            "is_online": True,
            "device_id": f"dev_new_{int(time.time())}",  # New device
            "ip_address": "203.0.113.45",  # Different IP
            "latitude": 9.0820,
            "longitude": 8.6753
        }
        
        try:
            response = requests.post(f"{self.api_url}/api/v1/analyze-transaction", 
                                    json=transaction, 
                                    headers=self.headers, 
                                    timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                confidence = data.get("confidence_score", 0)
                
                # Should flag as suspicious (high confidence) or require review
                if confidence > 0.3 or data.get("requires_review"):
                    self.log_test("Transaction Analysis - Suspicious", "PASSED", 
                                 f"Correctly flagged as suspicious (confidence: {confidence})", 
                                 {"result": data})
                    return True
                else:
                    self.log_test("Transaction Analysis - Suspicious", "WARNING", 
                                 f"Low suspicion score (confidence: {confidence})")
                    return True  # Still pass but with warning
            else:
                self.log_test("Transaction Analysis - Suspicious", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Transaction Analysis - Suspicious", "FAILED", str(e))
            return False
    
    def test_feedback_submission(self):
        """Test 7: Submit feedback"""
        feedback = {
            "transaction_id": f"test_tx_{int(time.time())}",
            "feedback_type": "false_positive",
            "is_fraud": False,
            "confidence": 0.85,
            "comments": "This is a test feedback submission",
            "user_id": "test_user"
        }
        
        try:
            response = requests.post(f"{self.api_url}/api/v1/feedback", 
                                    json=feedback, 
                                    headers=self.headers, 
                                    timeout=10)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test("Feedback Submission", "PASSED", 
                             "Feedback submitted successfully", 
                             {"response": data})
                return True
            else:
                self.log_test("Feedback Submission", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Feedback Submission", "FAILED", str(e))
            return False
    
    def test_pattern_ingestion(self):
        """Test 8: Ingest fraud pattern"""
        pattern = {
            "pattern_id": f"test_pattern_{int(time.time())}",
            "name": "Test Fraud Pattern",
            "description": "This is a test fraud pattern for API testing",
            "fraud_type": "velocity_fraud",
            "indicators": {
                "transaction_count": 10,
                "time_window_minutes": 60,
                "amount_threshold": 1000
            },
            "severity": "high",
            "created_by": "test_system"
        }
        
        try:
            response = requests.post(f"{self.api_url}/api/v1/fraud-patterns", 
                                    json=pattern, 
                                    headers=self.headers, 
                                    timeout=10)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test("Pattern Ingestion", "PASSED", 
                             "Pattern ingested successfully", 
                             {"response": data})
                return True
            else:
                self.log_test("Pattern Ingestion", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Pattern Ingestion", "FAILED", str(e))
            return False
    
    def test_invalid_transaction(self):
        """Test 9: Submit invalid transaction (negative testing)"""
        invalid_transaction = {
            "transaction_id": "invalid_test",
            "amount": -100,  # Invalid negative amount
        }
        
        try:
            response = requests.post(f"{self.api_url}/api/v1/analyze-transaction", 
                                    json=invalid_transaction, 
                                    headers=self.headers, 
                                    timeout=10)
            
            # Should return 400 or 422 for validation error
            if response.status_code in [400, 422]:
                self.log_test("Invalid Transaction Handling", "PASSED", 
                             "API correctly rejected invalid transaction", 
                             {"status_code": response.status_code})
                return True
            else:
                self.log_test("Invalid Transaction Handling", "FAILED", 
                             f"Expected 400/422, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invalid Transaction Handling", "FAILED", str(e))
            return False
    
    def test_unauthorized_access(self):
        """Test 10: Test unauthorized access (without API key)"""
        try:
            headers_no_key = {"Content-Type": "application/json"}
            response = requests.get(f"{self.api_url}/api/v1/metrics", 
                                   headers=headers_no_key, 
                                   timeout=10)
            
            # Should return 401 or 403 for unauthorized
            if response.status_code in [401, 403]:
                self.log_test("Unauthorized Access Protection", "PASSED", 
                             "API correctly requires authentication", 
                             {"status_code": response.status_code})
                return True
            elif response.status_code == 200:
                # If it allows access without auth, that's a security issue but not a critical failure
                self.log_test("Unauthorized Access Protection", "WARNING", 
                             "API allows access without authentication")
                return True
            else:
                self.log_test("Unauthorized Access Protection", "FAILED", 
                             f"Unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Unauthorized Access Protection", "FAILED", str(e))
            return False
    
    def test_response_time(self):
        """Test 11: API response time performance"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/health", headers=self.headers, timeout=10)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                if response_time < 1000:  # Under 1 second
                    self.log_test("Response Time Performance", "PASSED", 
                                 f"Response time: {response_time:.2f}ms", 
                                 {"response_time_ms": response_time})
                    return True
                elif response_time < 3000:  # Under 3 seconds
                    self.log_test("Response Time Performance", "WARNING", 
                                 f"Acceptable but slow: {response_time:.2f}ms")
                    return True
                else:
                    self.log_test("Response Time Performance", "FAILED", 
                                 f"Too slow: {response_time:.2f}ms")
                    return False
            else:
                self.log_test("Response Time Performance", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Response Time Performance", "FAILED", str(e))
            return False
    
    def test_concurrent_requests(self):
        """Test 12: Handle concurrent requests"""
        try:
            import concurrent.futures
            
            def make_request():
                try:
                    response = requests.get(f"{self.api_url}/health", 
                                          headers=self.headers, timeout=10)
                    return response.status_code == 200
                except:
                    return False
            
            # Make 10 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            successful = sum(results)
            
            if successful >= 8:  # At least 80% success
                self.log_test("Concurrent Requests", "PASSED", 
                             f"Handled {successful}/10 concurrent requests successfully")
                return True
            else:
                self.log_test("Concurrent Requests", "FAILED", 
                             f"Only {successful}/10 requests succeeded")
                return False
        except Exception as e:
            self.log_test("Concurrent Requests", "FAILED", str(e))
            return False
    
    def test_update_fraud_pattern(self):
        """Test 13: Update existing fraud pattern (PUT)"""
        # First create a pattern to update
        pattern_id = f"test_update_{int(time.time())}"
        create_pattern = {
            "pattern_id": pattern_id,
            "name": "Test Pattern for Update",
            "description": "Original description",
            "fraud_type": "test_fraud",
            "indicators": {"test": "value"},
            "severity": "medium"
        }
        
        try:
            # Create the pattern first
            create_response = requests.post(f"{self.api_url}/api/v1/fraud-patterns", 
                                          json=create_pattern, 
                                          headers=self.headers, 
                                          timeout=10)
            
            if create_response.status_code not in [200, 201]:
                self.log_test("Update Fraud Pattern", "SKIPPED", 
                             "Could not create pattern for update test")
                return True
            
            # Now update it
            update_pattern = {
                "name": "Updated Test Pattern",
                "description": "Updated description",
                "severity": "high"
            }
            
            response = requests.put(f"{self.api_url}/api/v1/fraud-patterns/{pattern_id}", 
                                   json=update_pattern, 
                                   headers=self.headers, 
                                   timeout=10)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test("Update Fraud Pattern", "PASSED", 
                             "Pattern updated successfully", 
                             {"response": data})
                return True
            elif response.status_code == 404:
                self.log_test("Update Fraud Pattern", "FAILED", 
                             "Pattern not found after creation")
                return False
            else:
                self.log_test("Update Fraud Pattern", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Update Fraud Pattern", "FAILED", str(e))
            return False
    
    def test_delete_fraud_pattern(self):
        """Test 14: Delete fraud pattern (DELETE)"""
        # First create a pattern to delete
        pattern_id = f"test_delete_{int(time.time())}"
        create_pattern = {
            "pattern_id": pattern_id,
            "name": "Test Pattern for Deletion",
            "description": "This pattern will be deleted",
            "fraud_type": "test_fraud",
            "indicators": {"test": "value"},
            "severity": "low"
        }
        
        try:
            # Create the pattern first
            create_response = requests.post(f"{self.api_url}/api/v1/fraud-patterns", 
                                          json=create_pattern, 
                                          headers=self.headers, 
                                          timeout=10)
            
            if create_response.status_code not in [200, 201]:
                self.log_test("Delete Fraud Pattern", "SKIPPED", 
                             "Could not create pattern for delete test")
                return True
            
            # Now delete it
            response = requests.delete(f"{self.api_url}/api/v1/fraud-patterns/{pattern_id}", 
                                      headers=self.headers, 
                                      timeout=10)
            
            if response.status_code in [200, 204]:
                self.log_test("Delete Fraud Pattern", "PASSED", 
                             "Pattern deleted successfully")
                return True
            elif response.status_code == 404:
                self.log_test("Delete Fraud Pattern", "FAILED", 
                             "Pattern not found after creation")
                return False
            else:
                self.log_test("Delete Fraud Pattern", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Delete Fraud Pattern", "FAILED", str(e))
            return False
    
    def test_get_transactions(self):
        """Test 15: Get transaction history (GET /transactions)"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/transactions", 
                                   headers=self.headers, 
                                   timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                transaction_count = len(data) if isinstance(data, list) else 0
                self.log_test("Get Transactions", "PASSED", 
                             f"Retrieved {transaction_count} transactions", 
                             {"count": transaction_count})
                return True
            else:
                self.log_test("Get Transactions", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Transactions", "FAILED", str(e))
            return False
    
    def test_get_transaction_by_id(self):
        """Test 16: Get specific transaction by ID (GET /transactions/{id})"""
        # Use a test transaction ID
        test_transaction_id = f"test_tx_{int(time.time())}"
        
        try:
            response = requests.get(f"{self.api_url}/api/v1/transactions/{test_transaction_id}", 
                                   headers=self.headers, 
                                   timeout=10)
            
            # Either 200 (found) or 404 (not found) are acceptable
            if response.status_code in [200, 404]:
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Get Transaction By ID", "PASSED", 
                                 "Transaction retrieved successfully", 
                                 {"transaction_id": test_transaction_id})
                else:
                    self.log_test("Get Transaction By ID", "PASSED", 
                                 "Endpoint working (transaction not found as expected)")
                return True
            else:
                self.log_test("Get Transaction By ID", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Transaction By ID", "FAILED", str(e))
            return False
    
    def test_llm_status(self):
        """Test 17: Get LLM service status (GET /llm-status)"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/llm-status", 
                                   headers=self.headers, 
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("LLM Status", "PASSED", 
                             "LLM status retrieved successfully", 
                             {"status": data})
                return True
            else:
                self.log_test("LLM Status", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("LLM Status", "FAILED", str(e))
            return False
    
    def test_switch_llm_model(self):
        """Test 18: Switch LLM model (POST /switch-llm-model)"""
        # Test switching to mock model
        switch_request = {
            "model_type": "mock"
        }
        
        try:
            response = requests.post(f"{self.api_url}/api/v1/switch-llm-model", 
                                    json=switch_request, 
                                    headers=self.headers, 
                                    timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Switch LLM Model", "PASSED", 
                             "LLM model switched successfully", 
                             {"response": data})
                return True
            else:
                self.log_test("Switch LLM Model", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Switch LLM Model", "FAILED", str(e))
            return False
    
    def test_detect_fraud_endpoint(self):
        """Test 19: Detect fraud endpoint (alternative transaction analysis)"""
        transaction = {
            "transaction_id": f"test_detect_{int(time.time())}",
            "amount": 125.50,
            "merchant": "Test Merchant",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(f"{self.api_url}/api/v1/detect-fraud", 
                                    json=transaction, 
                                    headers=self.headers, 
                                    timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Detect Fraud Endpoint", "PASSED", 
                             "Fraud detection completed", 
                             {"result": data})
                return True
            else:
                self.log_test("Detect Fraud Endpoint", "FAILED", 
                             f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Detect Fraud Endpoint", "FAILED", str(e))
            return False
    
    def run_all_tests(self):
        """Run all API endpoint tests"""
        print("\n" + "="*80)
        print("  COMPREHENSIVE API ENDPOINT TEST SUITE")
        print("="*80 + "\n")
        print(f"Testing API: {self.api_url}\n")
        
        # Run all tests in logical order
        # Basic health and connectivity
        self.test_health_endpoint()
        self.test_api_v1_health_endpoint()
        self.test_response_time()
        
        # Authentication and security
        self.test_unauthorized_access()
        
        # Core functionality
        self.test_metrics_endpoint()
        self.test_fraud_patterns_list()
        self.test_transaction_analysis_legitimate()
        self.test_transaction_analysis_suspicious()
        self.test_detect_fraud_endpoint()
        
        # CRUD operations on patterns
        self.test_pattern_ingestion()
        self.test_update_fraud_pattern()
        self.test_delete_fraud_pattern()
        
        # Transaction management
        self.test_get_transactions()
        self.test_get_transaction_by_id()
        
        # Feedback system
        self.test_feedback_submission()
        
        # LLM management
        self.test_llm_status()
        self.test_switch_llm_model()
        
        # Error handling and performance
        self.test_invalid_transaction()
        self.test_concurrent_requests()
        
        # Generate report
        self.generate_report()
        
        return self.results
    
    def generate_report(self):
        """Generate and save test report"""
        print("\n" + "="*80)
        print("  TEST RESULTS SUMMARY")
        print("="*80 + "\n")
        
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests:  {total}")
        print(f"Passed:       {passed} ({pass_rate:.1f}%)")
        print(f"Failed:       {failed}")
        print()
        
        # Save detailed report
        os.makedirs("tests/reports", exist_ok=True)
        report_file = f"tests/reports/api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")
        
        # Generate HTML report
        html_report = self.generate_html_report()
        html_file = report_file.replace('.json', '.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        print(f"📄 HTML report saved to: {html_file}")
        print("="*80 + "\n")
        
        if failed == 0:
            print("✅ ALL TESTS PASSED!")
            return 0
        else:
            print(f"❌ {failed} TEST(S) FAILED!")
            return 1
    
    def generate_html_report(self):
        """Generate HTML report"""
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        test_rows = ""
        for test in self.results["tests"]:
            status_class = test["status"].lower()
            status_icon = "✅" if test["status"] == "PASSED" else "❌" if test["status"] == "FAILED" else "⚠️"
            test_rows += f"""
            <tr class="{status_class}">
                <td>{status_icon} {test['name']}</td>
                <td>{test['status']}</td>
                <td>{test['message']}</td>
                <td>{test['timestamp']}</td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>API Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .summary-card {{ padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card h3 {{ margin: 0; font-size: 32px; }}
        .summary-card p {{ margin: 5px 0 0 0; color: #666; }}
        .total {{ background: #2196F3; color: white; }}
        .passed {{ background: #4CAF50; color: white; }}
        .failed {{ background: #f44336; color: white; }}
        .rate {{ background: #FF9800; color: white; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #333; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .passed td {{ background: #f1f8f4; }}
        .failed td {{ background: #ffebee; }}
        .warning td {{ background: #fff3e0; }}
        .timestamp {{ color: #666; font-size: 14px; margin-top: 20px; }}
        .api-info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔌 API Endpoint Test Report</h1>
        <p class="timestamp">Generated: {self.results['timestamp']}</p>
        
        <div class="api-info">
            <strong>API URL:</strong> {self.results['api_url']}
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>{total}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h3>{passed}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h3>{failed}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card rate">
                <h3>{pass_rate:.1f}%</h3>
                <p>Pass Rate</p>
            </div>
        </div>
        
        <h2>Test Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Message</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
                {test_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run API Endpoint Tests')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API URL')
    parser.add_argument('--api-key', default='development_api_key_for_testing', help='API Key')
    
    args = parser.parse_args()
    
    tester = APIEndpointTester(api_url=args.api_url, api_key=args.api_key)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results["failed"] == 0 else 1
    exit(exit_code)


if __name__ == "__main__":
    main()
