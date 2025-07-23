#!/usr/bin/env python
"""
Simple script to test the metrics endpoint
"""

import requests
import json
import sys

def test_metrics():
    """Test the metrics endpoint"""
    print("Testing metrics endpoints...")
    
    base_url = "http://localhost:8000"
    headers = {"X-API-Key": "development_api_key_for_testing"}
    
    # Test the Prometheus metrics endpoint
    print("\nTesting /metrics endpoint:")
    try:
        response = requests.get(f"{base_url}/metrics", headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Prometheus metrics endpoint successful!")
            print(f"Response length: {len(response.text)} characters")
        else:
            print("❌ Prometheus metrics endpoint failed!")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test the API metrics endpoint
    print("\nTesting /api/v1/metrics endpoint:")
    try:
        response = requests.get(f"{base_url}/api/v1/metrics", headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✅ API metrics endpoint successful!")
            data = response.json()
            print(f"Models: {len(data.get('models', []))}")
            print("Model names:")
            for model in data.get('models', []):
                print(f"  - {model.get('name', 'Unknown')}")
        else:
            print("❌ API metrics endpoint failed!")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_metrics()
