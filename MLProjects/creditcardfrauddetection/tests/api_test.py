"""
Utility script to test the API connection from the UI
"""

import requests
import json
import time
import sys
from pprint import pprint

API_URL = "http://localhost:8000"

def test_health():
    """Test the API health endpoint"""
    print(f"Testing API health at {API_URL}/health")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API health check successful")
            print(f"Status code: {response.status_code}")
            print("Response:")
            pprint(response.json())
            return True
        else:
            print("❌ API health check failed")
            print(f"Status code: {response.status_code}")
            print("Response:")
            pprint(response.text)
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API connection error - API server may not be running")
        return False
    except requests.exceptions.Timeout:
        print("❌ API request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_fraud_patterns():
    """Test the fraud patterns endpoint"""
    print(f"\nTesting API fraud patterns at {API_URL}/api/v1/fraud-patterns")
    
    # Test GET fraud patterns
    try:
        response = requests.get(
            f"{API_URL}/api/v1/fraud-patterns", 
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "development_api_key_for_testing"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ GET fraud patterns successful")
            print(f"Status code: {response.status_code}")
            print("Response (first pattern):")
            patterns = response.json()
            if patterns:
                pprint(patterns[0])
                print(f"Total patterns: {len(patterns)}")
            else:
                print("No patterns returned")
        else:
            print("❌ GET fraud patterns failed")
            print(f"Status code: {response.status_code}")
            print("Response:")
            pprint(response.text)
            return False
    except Exception as e:
        print(f"❌ Error getting fraud patterns: {str(e)}")
        return False
    
    # Test POST fraud pattern
    try:
        new_pattern = {
            "name": "Test Pattern",
            "description": "Pattern created by the API test script",
            "pattern": {
                "test_key": "test_value",
                "indicators": ["test_indicator"]
            },
            "similarity_threshold": 0.75
        }
        
        response = requests.post(
            f"{API_URL}/api/v1/fraud-patterns", 
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "development_api_key_for_testing"
            },
            json=new_pattern,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ POST fraud pattern successful")
            print(f"Status code: {response.status_code}")
            print("Response:")
            pprint(response.json())
            return True
        else:
            print("❌ POST fraud pattern failed")
            print(f"Status code: {response.status_code}")
            print("Response:")
            pprint(response.text)
            return False
    except Exception as e:
        print(f"❌ Error posting fraud pattern: {str(e)}")
        return False

def test_metrics():
    """Test the API metrics endpoint"""
    print(f"\nTesting API metrics at {API_URL}/metrics")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "development_api_key_for_testing"  # Using the same key as the fraud patterns test
    }
    
    try:
        response = requests.get(f"{API_URL}/metrics", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ API metrics check successful")
            print(f"Status code: {response.status_code}")
            print("Response:")
            pprint(response.json()["models"][0])  # Only show the first model's metrics
            return True
        else:
            print("❌ API metrics check failed")
            print(f"Status code: {response.status_code}")
            print("Response:")
            pprint(response.text)
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API connection error - API server may not be running")
        return False
    except Exception as e:
        print(f"❌ Error testing metrics endpoint: {str(e)}")
        return False

def main():
    """Run all API tests"""
    print("Credit Card Fraud Detection API Test")
    print("="*50)
    
    start_time = time.time()
    
    # Run tests
    health_ok = test_health()
    if health_ok:
        patterns_ok = test_fraud_patterns()
        metrics_ok = test_metrics()
    else:
        print("\n❌ Skipping pattern and metrics tests as health check failed")
        patterns_ok = False
        metrics_ok = False
    
    # Print summary
    print("\nTest Summary")
    print("="*50)
    print(f"Health check: {'✅ Passed' if health_ok else '❌ Failed'}")
    print(f"Fraud patterns: {'✅ Passed' if patterns_ok else '❌ Failed'}")
    print(f"Model metrics: {'✅ Passed' if metrics_ok else '❌ Failed'}")
    print(f"Total time: {time.time() - start_time:.2f} seconds")
    
    # Return exit code
    if health_ok and patterns_ok and metrics_ok:
        print("\n✅ All tests passed! The API is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the API server.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
