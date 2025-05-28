"""
Integration test script for the fraud detection API.
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key"  # Replace with your actual API key if different

def test_health_endpoint():
    """Test the health endpoint."""
    url = f"{BASE_URL}/health"
    headers = {"X-API-Key": API_KEY}
    
    print(f"Testing health endpoint: {url}")
    response = requests.get(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)
    
    return response.status_code == 200

def test_fraud_detection(transaction_data):
    """Test the fraud detection endpoint."""
    url = f"{BASE_URL}/api/v1/detect-fraud"  # Fixed the endpoint URL to include /api/v1/
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"Testing fraud detection endpoint: {url}")
    print(f"Transaction data: {json.dumps(transaction_data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=transaction_data)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    print("-" * 50)
    
    return response.status_code == 200

def create_test_transactions():
    """Create test transactions for testing."""
    # Get current timestamp in ISO format
    current_time = datetime.utcnow().isoformat() + "Z"
    
    # Sample legitimate transaction (low amount, common merchant)
    legitimate_transaction = {
        "transaction_id": f"test_legitimate_{int(time.time())}",
        "card_id": "card_7890123456",
        "merchant_id": "merch_24680",
        "timestamp": current_time,
        "amount": 25.99,
        "merchant_category": "Grocery",
        "merchant_name": "Local Supermarket",
        "merchant_country": "US",
        "merchant_zip": "98040",
        "customer_id": "cust_12345",
        "is_online": False,
        "currency": "USD",
        "latitude": 47.5874,
        "longitude": -122.2352
    }
    
    # Sample suspicious transaction (high amount, unusual location)
    suspicious_transaction = {
        "transaction_id": f"test_suspicious_{int(time.time())}",
        "card_id": "card_7890123456",
        "merchant_id": "merch_54321",
        "timestamp": current_time,
        "amount": 2999.99,
        "merchant_category": "Electronics",
        "merchant_name": "Unknown Electronics Store",
        "merchant_country": "RU",  # Unusual location
        "merchant_zip": "101000",
        "customer_id": "cust_12345",
        "is_online": True,
        "device_id": "new_device_xyz",
        "ip_address": "203.0.113.195",  # Random IP
        "currency": "USD",
        "latitude": 55.7558,
        "longitude": 37.6173
    }
    
    # Sample fraudulent transaction (very high amount, suspicious category)
    fraudulent_transaction = {
        "transaction_id": f"test_fraudulent_{int(time.time())}",
        "card_id": "card_7890123456",
        "merchant_id": "merch_99999",
        "timestamp": current_time,
        "amount": 9999.99,
        "merchant_category": "Cryptocurrency",
        "merchant_name": "QuickCrypto Exchange",
        "merchant_country": "NG",  # Unusual country
        "customer_id": "cust_12345",
        "is_online": True,
        "device_id": "unknown_device",
        "ip_address": "185.176.43.89",  # Random IP
        "currency": "BTC",  # Unusual currency
        "latitude": 6.5244,
        "longitude": 3.3792
    }
    
    return [legitimate_transaction, suspicious_transaction, fraudulent_transaction]

def main():
    """Run the tests."""
    print("=== Credit Card Fraud Detection API Test ===")
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    if not health_ok:
        print("Health endpoint test failed. Exiting.")
        return
    
    # Test fraud detection with different transactions
    transactions = create_test_transactions()
    
    for i, transaction in enumerate(transactions):
        print(f"\nTesting Transaction {i+1}:")
        test_fraud_detection(transaction)
        time.sleep(2)  # Small delay between requests
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()
