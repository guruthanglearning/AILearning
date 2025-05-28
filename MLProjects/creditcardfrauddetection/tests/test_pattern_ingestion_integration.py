"""
Integration test script for the ingest-patterns endpoint.
"""

import requests
import json
import time

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key"  # Replace with your actual API key if different

def test_ingest_patterns_endpoint():
    """Test the ingest-patterns endpoint."""
    url = f"{BASE_URL}/api/v1/ingest-patterns"  # Fixed the endpoint URL to include /api/v1/
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Sample fraud patterns for testing
    fraud_patterns = [
        {
            "pattern_id": f"pattern_{int(time.time())}_1",
            "description": "High value electronics purchase followed by gift cards",
            "indicators": [
                "Electronics merchant",
                "Transaction amount > $1000",
                "New device or IP",
                "Followed by gift card purchase within 24 hours"
            ],
            "risk_score": 0.85,
            "detection_strategy": "Look for high-value electronics purchases followed closely by gift card purchases"
        },
        {
            "pattern_id": f"pattern_{int(time.time())}_2",
            "description": "Multiple small transactions leading to large one",
            "indicators": [
                "Series of small purchases (< $10) within short time",
                "Followed by large transaction",
                "Multiple merchant categories",
                "Transactions across different geographic areas"
            ],
            "risk_score": 0.75,
            "detection_strategy": "Monitor for card testing pattern with small transactions followed by large purchase"
        }
    ]
    
    print(f"Testing ingest-patterns endpoint: {url}")
    print(f"Patterns data: {json.dumps(fraud_patterns, indent=2)}")
    
    response = requests.post(url, headers=headers, json=fraud_patterns)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    print("-" * 50)
    
    return response.status_code == 200

def main():
    """Run the patterns ingestion test."""
    print("=== Credit Card Fraud Detection API Pattern Ingestion Test ===")
    
    test_ingest_patterns_endpoint()
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()
