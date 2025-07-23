#!/usr/bin/env python
"""
Comprehensive API Testing Script for Credit Card Fraud Detection System

This script tests ALL API endpoints systematically and provides detailed reporting.
It covers CRUD operations, system endpoints, and provides validation for each endpoint.

Usage:
    python comprehensive_api_test.py

Features:
- Tests all 15+ API endpoints
- CRUD operations for fraud patterns
- Transaction processing and history
- LLM management and switching
- System health and metrics
- Detailed reporting with pass/fail status
- Error handling and diagnostics
- Performance metrics
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pprint import pprint

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "development_api_key_for_testing"

class APITestRunner:
    """Comprehensive API test runner with detailed reporting."""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        self.test_pattern_id = None
        
    def log_test(self, endpoint: str, method: str, status: str, 
                 status_code: int = None, message: str = "", 
                 response_time: float = None, details: str = ""):
        """Log test result."""
        self.results.append({
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "status_code": status_code,
            "message": message,
            "response_time": response_time,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def print_header(self, title: str):
        """Print test section header."""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
        
    def print_test(self, test_name: str):
        """Print individual test name."""
        print(f"\n🧪 {test_name}")
        print("-" * 60)
        
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    timeout: int = 10) -> Tuple[requests.Response, float]:
        """Make HTTP request with timing."""
        url = f"{API_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response_time = time.time() - start_time
            return response, response_time
            
        except Exception as e:
            response_time = time.time() - start_time
            print(f"❌ Request failed: {str(e)}")
            return None, response_time

    def test_health_endpoint(self):
        """Test health check endpoint."""
        self.print_test("Health Check - GET /health")
        
        response, response_time = self.make_request("GET", "/health")
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful ({response_time:.2f}s)")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   LLM Type: {data.get('llm_service_type')}")
            print(f"   Environment: {data.get('environment')}")
            
            self.log_test("/health", "GET", "PASS", response.status_code, 
                         "Health check successful", response_time, 
                         f"Status: {data.get('status')}")
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Health check failed (Code: {status_code})")
            self.log_test("/health", "GET", "FAIL", status_code, 
                         "Health check failed", response_time)
            return False

    def test_api_health_endpoint(self):
        """Test API health check endpoint."""
        self.print_test("API Health Check - GET /api/v1/health")
        
        response, response_time = self.make_request("GET", "/api/v1/health")
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"✅ API health check successful ({response_time:.2f}s)")
            print(f"   Status: {data.get('status')}")
            print(f"   Components: {list(data.get('components', {}).keys())}")
            
            self.log_test("/api/v1/health", "GET", "PASS", response.status_code, 
                         "API health check successful", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ API health check failed (Code: {status_code})")
            self.log_test("/api/v1/health", "GET", "FAIL", status_code, 
                         "API health check failed", response_time)
            return False

    def test_fraud_patterns_get(self):
        """Test GET fraud patterns endpoint."""
        self.print_test("Get Fraud Patterns - GET /api/v1/fraud-patterns")
        
        response, response_time = self.make_request("GET", "/api/v1/fraud-patterns")
        
        if response and response.status_code == 200:
            patterns = response.json()
            print(f"✅ Get fraud patterns successful ({response_time:.2f}s)")
            print(f"   Total patterns: {len(patterns)}")
            
            if patterns:
                # Show sample pattern info
                sample = patterns[0]
                print(f"   Sample ID: {sample.get('id', 'Unknown')}")
                print(f"   Sample name: {sample.get('name', 'Unknown')}")
                print(f"   Sample fraud type: {sample.get('pattern', {}).get('fraud_type', 'Unknown')}")
                
                # Count fraud types
                fraud_types = set()
                for pattern in patterns:
                    fraud_type = pattern.get('pattern', {}).get('fraud_type')
                    if fraud_type:
                        fraud_types.add(fraud_type)
                print(f"   Unique fraud types: {len(fraud_types)}")
            
            self.log_test("/api/v1/fraud-patterns", "GET", "PASS", response.status_code, 
                         f"Retrieved {len(patterns)} patterns", response_time)
            return True, patterns
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Get fraud patterns failed (Code: {status_code})")
            self.log_test("/api/v1/fraud-patterns", "GET", "FAIL", status_code, 
                         "Failed to get patterns", response_time)
            return False, []

    def test_fraud_patterns_post(self):
        """Test POST fraud patterns endpoint."""
        self.print_test("Create Fraud Pattern - POST /api/v1/fraud-patterns")
        
        # Create test pattern
        test_pattern = {
            "name": f"API Test Pattern {uuid.uuid4().hex[:8]}",
            "description": "Pattern created by comprehensive API test",
            "pattern": {
                "fraud_type": "Test Fraud Type",
                "merchant_category": "Testing",
                "indicators": ["automated_test", "api_testing"],
                "test_metadata": {
                    "created_by": "comprehensive_api_test",
                    "test_run": datetime.now().isoformat()
                }
            },
            "similarity_threshold": 0.85
        }
        
        response, response_time = self.make_request("POST", "/api/v1/fraud-patterns", test_pattern)
        
        if response and response.status_code == 200:
            created_pattern = response.json()
            pattern_id = created_pattern.get('id')
            self.test_pattern_id = pattern_id  # Store for later tests
            
            print(f"✅ Create fraud pattern successful ({response_time:.2f}s)")
            print(f"   Created pattern ID: {pattern_id}")
            print(f"   Pattern name: {created_pattern.get('name')}")
            
            self.log_test("/api/v1/fraud-patterns", "POST", "PASS", response.status_code, 
                         f"Created pattern {pattern_id}", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Create fraud pattern failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/fraud-patterns", "POST", "FAIL", status_code, 
                         "Failed to create pattern", response_time)
            return False

    def test_fraud_patterns_put(self):
        """Test PUT fraud patterns endpoint."""
        if not self.test_pattern_id:
            print("⚠️  Skipping PUT test - no test pattern ID available")
            return False
            
        self.print_test(f"Update Fraud Pattern - PUT /api/v1/fraud-patterns/{self.test_pattern_id}")
        
        # Update pattern data
        updated_pattern = {
            "name": f"Updated API Test Pattern {uuid.uuid4().hex[:8]}",
            "description": "Pattern updated by comprehensive API test",
            "pattern": {
                "fraud_type": "Updated Test Fraud Type",
                "merchant_category": "Updated Testing",
                "indicators": ["automated_test", "api_testing", "updated"],
                "test_metadata": {
                    "updated_by": "comprehensive_api_test",
                    "update_time": datetime.now().isoformat()
                }
            },
            "similarity_threshold": 0.90
        }
        
        response, response_time = self.make_request("PUT", f"/api/v1/fraud-patterns/{self.test_pattern_id}", 
                                                   updated_pattern)
        
        if response and response.status_code == 200:
            updated = response.json()
            print(f"✅ Update fraud pattern successful ({response_time:.2f}s)")
            print(f"   Updated pattern ID: {updated.get('id')}")
            print(f"   New name: {updated.get('name')}")
            
            self.log_test(f"/api/v1/fraud-patterns/{self.test_pattern_id}", "PUT", "PASS", 
                         response.status_code, "Pattern updated successfully", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Update fraud pattern failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test(f"/api/v1/fraud-patterns/{self.test_pattern_id}", "PUT", "FAIL", 
                         status_code, "Failed to update pattern", response_time)
            return False

    def test_fraud_patterns_delete(self):
        """Test DELETE fraud patterns endpoint."""
        if not self.test_pattern_id:
            print("⚠️  Skipping DELETE test - no test pattern ID available")
            return False
            
        self.print_test(f"Delete Fraud Pattern - DELETE /api/v1/fraud-patterns/{self.test_pattern_id}")
        
        response, response_time = self.make_request("DELETE", f"/api/v1/fraud-patterns/{self.test_pattern_id}")
        
        if response and response.status_code == 200:
            result = response.json()
            print(f"✅ Delete fraud pattern successful ({response_time:.2f}s)")
            print(f"   Result: {result.get('message', 'Pattern deleted')}")
            
            self.log_test(f"/api/v1/fraud-patterns/{self.test_pattern_id}", "DELETE", "PASS", 
                         response.status_code, "Pattern deleted successfully", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Delete fraud pattern failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test(f"/api/v1/fraud-patterns/{self.test_pattern_id}", "DELETE", "FAIL", 
                         status_code, "Failed to delete pattern", response_time)
            return False

    def test_detect_fraud_endpoint(self):
        """Test fraud detection endpoint."""
        self.print_test("Fraud Detection - POST /api/v1/detect-fraud")
        
        # Create test transaction
        test_transaction = {
            "transaction_id": f"test_txn_{uuid.uuid4().hex[:8]}",
            "card_id": f"card_{uuid.uuid4().hex[:8]}",
            "merchant_id": f"merchant_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "amount": 1500.00,
            "currency": "USD",
            "is_online": True,
            "merchant_category": "Electronics",
            "ip_address": "192.168.1.100",
            "device_id": f"device_{uuid.uuid4().hex[:8]}",
            "location_country": "US",
            "location_state": "CA"
        }
        
        response, response_time = self.make_request("POST", "/api/v1/detect-fraud", test_transaction)
        
        if response and response.status_code == 200:
            result = response.json()
            print(f"✅ Fraud detection successful ({response_time:.2f}s)")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            print(f"   Is Fraud: {result.get('is_fraud')}")
            print(f"   Confidence: {result.get('confidence_score', 0):.3f}")
            print(f"   Risk Level: {result.get('risk_level')}")
            
            self.log_test("/api/v1/detect-fraud", "POST", "PASS", response.status_code, 
                         f"Fraud detection completed - Risk: {result.get('risk_level')}", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Fraud detection failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/detect-fraud", "POST", "FAIL", status_code, 
                         "Fraud detection failed", response_time)
            return False

    def test_feedback_endpoint(self):
        """Test feedback submission endpoint."""
        self.print_test("Submit Feedback - POST /api/v1/feedback")
        
        # Create test feedback
        test_feedback = {
            "transaction_id": f"test_feedback_txn_{uuid.uuid4().hex[:8]}",
            "actual_fraud": True,
            "analyst_notes": "Test feedback from comprehensive API test - marking as fraud for testing purposes"
        }
        
        response, response_time = self.make_request("POST", "/api/v1/feedback", test_feedback)
        
        if response and response.status_code == 200:
            result = response.json()
            print(f"✅ Feedback submission successful ({response_time:.2f}s)")
            print(f"   Status: {result.get('status', 'completed')}")
            print(f"   Message: {result.get('message', 'Feedback processed')}")
            
            self.log_test("/api/v1/feedback", "POST", "PASS", response.status_code, 
                         "Feedback submitted successfully", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Feedback submission failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/feedback", "POST", "FAIL", status_code, 
                         "Feedback submission failed", response_time)
            return False

    def test_metrics_endpoint(self):
        """Test system metrics endpoint."""
        self.print_test("System Metrics - GET /api/v1/metrics")
        
        response, response_time = self.make_request("GET", "/api/v1/metrics")
        
        if response and response.status_code == 200:
            metrics = response.json()
            print(f"✅ System metrics successful ({response_time:.2f}s)")
            print(f"   Timestamp: {metrics.get('timestamp')}")
            print(f"   Models available: {len(metrics.get('models', []))}")
            
            # Show model metrics
            models = metrics.get('models', [])
            for model in models[:2]:  # Show first 2 models
                name = model.get('name', 'Unknown')
                model_metrics = model.get('metrics', {})
                print(f"   Model {name}:")
                print(f"     Accuracy: {model_metrics.get('accuracy', 'N/A')}")
                print(f"     F1 Score: {model_metrics.get('f1_score', 'N/A')}")
            
            # Show system metrics
            system = metrics.get('system', {})
            if system:
                print(f"   System metrics: {list(system.keys())}")
            
            self.log_test("/api/v1/metrics", "GET", "PASS", response.status_code, 
                         f"Retrieved metrics for {len(models)} models", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ System metrics failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/metrics", "GET", "FAIL", status_code, 
                         "System metrics failed", response_time)
            return False

    def test_prometheus_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        self.print_test("Prometheus Metrics - GET /metrics")
        
        response, response_time = self.make_request("GET", "/metrics")
        
        if response and response.status_code == 200:
            content = response.text
            print(f"✅ Prometheus metrics successful ({response_time:.2f}s)")
            print(f"   Content length: {len(content)} characters")
            
            # Count metrics
            lines = content.split('\n')
            metric_lines = [line for line in lines if line and not line.startswith('#')]
            print(f"   Metric entries: {len(metric_lines)}")
            
            self.log_test("/metrics", "GET", "PASS", response.status_code, 
                         f"Retrieved {len(metric_lines)} metric entries", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Prometheus metrics failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/metrics", "GET", "FAIL", status_code, 
                         "Prometheus metrics failed", response_time)
            return False

    def test_transactions_endpoint(self):
        """Test transactions list endpoint."""
        self.print_test("Get Transactions - GET /api/v1/transactions")
        
        response, response_time = self.make_request("GET", "/api/v1/transactions?limit=5")
        
        if response and response.status_code == 200:
            transactions = response.json()
            print(f"✅ Get transactions successful ({response_time:.2f}s)")
            print(f"   Retrieved transactions: {len(transactions)}")
            
            if transactions:
                sample = transactions[0]
                print(f"   Sample transaction ID: {sample.get('transaction_id')}")
                print(f"   Sample amount: {sample.get('amount')}")
                print(f"   Sample merchant: {sample.get('merchant_category')}")
            
            self.log_test("/api/v1/transactions", "GET", "PASS", response.status_code, 
                         f"Retrieved {len(transactions)} transactions", response_time)
            return True, transactions
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Get transactions failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/transactions", "GET", "FAIL", status_code, 
                         "Get transactions failed", response_time)
            return False, []

    def test_transaction_by_id_endpoint(self, transactions):
        """Test get transaction by ID endpoint."""
        if not transactions:
            print("⚠️  Skipping transaction by ID test - no transactions available")
            return False
            
        transaction_id = transactions[0].get('transaction_id')
        self.print_test(f"Get Transaction by ID - GET /api/v1/transactions/{transaction_id}")
        
        response, response_time = self.make_request("GET", f"/api/v1/transactions/{transaction_id}")
        
        if response and response.status_code == 200:
            transaction = response.json()
            print(f"✅ Get transaction by ID successful ({response_time:.2f}s)")
            print(f"   Transaction ID: {transaction.get('transaction_id')}")
            print(f"   Amount: {transaction.get('amount')}")
            print(f"   Status: {transaction.get('fraud_status', 'Unknown')}")
            
            self.log_test(f"/api/v1/transactions/{transaction_id}", "GET", "PASS", 
                         response.status_code, "Retrieved transaction details", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Get transaction by ID failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test(f"/api/v1/transactions/{transaction_id}", "GET", "FAIL", 
                         status_code, "Failed to get transaction", response_time)
            return False

    def test_llm_status_endpoint(self):
        """Test LLM status endpoint."""
        self.print_test("LLM Status - GET /api/v1/llm-status")
        
        response, response_time = self.make_request("GET", "/api/v1/llm-status")
        
        if response and response.status_code == 200:
            status = response.json()
            print(f"✅ LLM status successful ({response_time:.2f}s)")
            print(f"   Service type: {status.get('llm_service_type')}")
            print(f"   Model: {status.get('llm_model')}")
            print(f"   Is API: {status.get('is_api')}")
            print(f"   Is Local: {status.get('is_local')}")
            print(f"   Is Mock: {status.get('is_mock')}")
            
            self.log_test("/api/v1/llm-status", "GET", "PASS", response.status_code, 
                         f"LLM type: {status.get('llm_service_type')}", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ LLM status failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/llm-status", "GET", "FAIL", status_code, 
                         "LLM status failed", response_time)
            return False

    def test_switch_llm_endpoint(self):
        """Test LLM model switching endpoint."""
        self.print_test("Switch LLM Model - POST /api/v1/switch-llm-model")
        
        # Test switching to mock LLM (should always work)
        switch_data = {"type": "mock"}
        
        response, response_time = self.make_request("POST", "/api/v1/switch-llm-model", switch_data)
        
        if response and response.status_code == 200:
            result = response.json()
            print(f"✅ Switch LLM model successful ({response_time:.2f}s)")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Current type: {result.get('current_type')}")
            
            self.log_test("/api/v1/switch-llm-model", "POST", "PASS", response.status_code, 
                         f"Switched to {result.get('current_type')}", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Switch LLM model failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/switch-llm-model", "POST", "FAIL", status_code, 
                         "LLM model switch failed", response_time)
            return False

    def test_ingest_patterns_endpoint(self):
        """Test pattern ingestion endpoint."""
        self.print_test("Ingest Patterns - POST /api/v1/ingest-patterns")
        
        # Create test patterns for ingestion
        test_patterns = [
            {
                "pattern_id": f"ingest_test_{uuid.uuid4().hex[:8]}",
                "description": "Test pattern from comprehensive API test",
                "indicators": [
                    "High-value transaction",
                    "New merchant",
                    "Unusual time"
                ],
                "risk_score": 0.75,
                "detection_strategy": "Monitor for unusual high-value transactions at new merchants"
            }
        ]
        
        response, response_time = self.make_request("POST", "/api/v1/ingest-patterns", test_patterns)
        
        if response and response.status_code == 200:
            result = response.json()
            print(f"✅ Ingest patterns successful ({response_time:.2f}s)")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Count: {result.get('count')}")
            
            self.log_test("/api/v1/ingest-patterns", "POST", "PASS", response.status_code, 
                         f"Ingested {result.get('count', 0)} patterns", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Ingest patterns failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/ingest-patterns", "POST", "FAIL", status_code, 
                         "Pattern ingestion failed", response_time)
            return False

    def test_root_endpoint(self):
        """Test root endpoint."""
        self.print_test("Root Endpoint - GET /api/v1/")
        
        response, response_time = self.make_request("GET", "/api/v1/")
        
        if response and response.status_code == 200:
            result = response.json()
            print(f"✅ Root endpoint successful ({response_time:.2f}s)")
            print(f"   Response: {result}")
            
            self.log_test("/api/v1/", "GET", "PASS", response.status_code, 
                         "Root endpoint accessible", response_time)
            return True
        else:
            status_code = response.status_code if response else 0
            print(f"❌ Root endpoint failed (Code: {status_code})")
            if response:
                print(f"   Error: {response.text}")
            self.log_test("/api/v1/", "GET", "FAIL", status_code, 
                         "Root endpoint failed", response_time)
            return False

    def run_all_tests(self):
        """Run all API tests."""
        self.print_header("COMPREHENSIVE API TESTING - CREDIT CARD FRAUD DETECTION SYSTEM")
        print(f"🚀 Starting comprehensive API tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📡 API URL: {API_URL}")
        print(f"🔑 API Key: {API_KEY[:20]}...")
        
        # Test basic connectivity first
        self.print_header("SECTION 1: BASIC CONNECTIVITY")
        health_ok = self.test_health_endpoint()
        api_health_ok = self.test_api_health_endpoint()
        root_ok = self.test_root_endpoint()
        
        if not (health_ok or api_health_ok):
            print("\n❌ CRITICAL: Basic connectivity failed! Cannot proceed with other tests.")
            return
            
        # Test fraud patterns CRUD
        self.print_header("SECTION 2: FRAUD PATTERNS CRUD OPERATIONS")
        patterns_get_ok, patterns = self.test_fraud_patterns_get()
        patterns_post_ok = self.test_fraud_patterns_post()
        patterns_put_ok = self.test_fraud_patterns_put()
        patterns_delete_ok = self.test_fraud_patterns_delete()
        
        # Test core fraud detection
        self.print_header("SECTION 3: FRAUD DETECTION & FEEDBACK")
        fraud_detect_ok = self.test_detect_fraud_endpoint()
        feedback_ok = self.test_feedback_endpoint()
        
        # Test system monitoring
        self.print_header("SECTION 4: SYSTEM MONITORING & METRICS")
        metrics_ok = self.test_metrics_endpoint()
        prometheus_ok = self.test_prometheus_metrics_endpoint()
        
        # Test transaction management
        self.print_header("SECTION 5: TRANSACTION MANAGEMENT")
        transactions_ok, transactions = self.test_transactions_endpoint()
        transaction_by_id_ok = self.test_transaction_by_id_endpoint(transactions)
        
        # Test LLM management
        self.print_header("SECTION 6: LLM MANAGEMENT")
        llm_status_ok = self.test_llm_status_endpoint()
        llm_switch_ok = self.test_switch_llm_endpoint()
        
        # Test pattern ingestion
        self.print_header("SECTION 7: PATTERN INGESTION")
        ingest_ok = self.test_ingest_patterns_endpoint()
        
        # Generate final report
        self.generate_final_report()

    def generate_final_report(self):
        """Generate comprehensive test report."""
        self.print_header("COMPREHENSIVE TEST RESULTS SUMMARY")
        
        total_time = time.time() - self.start_time
        passed_tests = [r for r in self.results if r['status'] == 'PASS']
        failed_tests = [r for r in self.results if r['status'] == 'FAIL']
        
        print(f"📊 Test Execution Summary")
        print(f"   Total tests: {len(self.results)}")
        print(f"   Passed: {len(passed_tests)} ✅")
        print(f"   Failed: {len(failed_tests)} ❌")
        print(f"   Success rate: {len(passed_tests)/len(self.results)*100:.1f}%")
        print(f"   Total execution time: {total_time:.2f} seconds")
        
        # Response time analysis
        response_times = [r['response_time'] for r in self.results if r['response_time']]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"\n⏱️  Response Time Analysis")
            print(f"   Average: {avg_response_time:.3f}s")
            print(f"   Minimum: {min_response_time:.3f}s")
            print(f"   Maximum: {max_response_time:.3f}s")
        
        # Detailed results by category
        print(f"\n📋 Detailed Results by Endpoint")
        print(f"{'Endpoint':<35} {'Method':<8} {'Status':<8} {'Code':<6} {'Time':<8} {'Message':<40}")
        print("-" * 110)
        
        for result in self.results:
            endpoint = result['endpoint'][:34]
            method = result['method']
            status = "✅ PASS" if result['status'] == 'PASS' else "❌ FAIL"
            code = str(result['status_code']) if result['status_code'] else "N/A"
            time_str = f"{result['response_time']:.3f}s" if result['response_time'] else "N/A"
            message = result['message'][:39] if result['message'] else ""
            
            print(f"{endpoint:<35} {method:<8} {status:<8} {code:<6} {time_str:<8} {message:<40}")
        
        # Failed tests details
        if failed_tests:
            print(f"\n🚨 Failed Tests Details")
            for test in failed_tests:
                print(f"   ❌ {test['method']} {test['endpoint']}")
                print(f"      Status Code: {test['status_code']}")
                print(f"      Error: {test['message']}")
                print()
        
        # Overall system health
        critical_endpoints = ['/health', '/api/v1/health', '/api/v1/fraud-patterns']
        critical_passed = sum(1 for r in passed_tests if r['endpoint'] in critical_endpoints)
        
        print(f"\n🏥 System Health Assessment")
        if critical_passed >= 2:
            print("   ✅ SYSTEM HEALTHY - Core endpoints are functional")
        else:
            print("   ❌ SYSTEM UNHEALTHY - Critical endpoints are failing")
        
        # Recommendations
        print(f"\n💡 Recommendations")
        if len(failed_tests) == 0:
            print("   🎉 Excellent! All endpoints are working perfectly.")
            print("   🚀 System is ready for production use.")
        elif len(failed_tests) <= 2:
            print("   ⚠️  Minor issues detected. Review failed endpoints.")
            print("   🔧 System is mostly functional but needs attention.")
        else:
            print("   🚨 Multiple endpoints failing. System needs investigation.")
            print("   🛠️  Check server logs and configuration.")
        
        # Save detailed report
        report_file = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': len(self.results),
                    'passed': len(passed_tests),
                    'failed': len(failed_tests),
                    'success_rate': len(passed_tests)/len(self.results)*100,
                    'execution_time': total_time,
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.results,
                'performance': {
                    'response_times': response_times,
                    'avg_response_time': avg_response_time if response_times else 0,
                    'max_response_time': max_response_time if response_times else 0,
                    'min_response_time': min_response_time if response_times else 0
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        print(f"\n{'='*80}")
        print("COMPREHENSIVE API TESTING COMPLETED")
        print(f"{'='*80}")


def main():
    """Main function to run comprehensive API tests."""
    print("🔍 Credit Card Fraud Detection System - Comprehensive API Test Suite")
    print("=" * 80)
    
    # Initialize test runner
    test_runner = APITestRunner()
    
    try:
        # Run all tests
        test_runner.run_all_tests()
        
        # Exit with appropriate code
        failed_count = len([r for r in test_runner.results if r['status'] == 'FAIL'])
        sys.exit(0 if failed_count == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during test execution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
