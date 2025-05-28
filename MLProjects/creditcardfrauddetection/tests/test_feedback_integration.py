"""
Integration test script for the feedback endpoint.
"""

import requests
import json
import time

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key"  # Replace with your actual API key if different

def test_feedback_endpoint(transaction_id, is_fraud):
    """Test the feedback endpoint."""
    url = f"{BASE_URL}/api/v1/feedback"  # Fixed the endpoint URL to include /api/v1/
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    feedback_data = {
        "transaction_id": transaction_id,
        "actual_fraud": is_fraud,
        "analyst_notes": f"Test feedback for transaction {transaction_id}. {'This was actually fraud.' if is_fraud else 'This was actually legitimate.'}"
    }
    
    print(f"Testing feedback endpoint: {url}")
    print(f"Feedback data: {json.dumps(feedback_data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=feedback_data)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    print("-" * 50)
    
    return response.status_code == 200

def main():
    """Run the feedback test."""
    print("=== Credit Card Fraud Detection API Feedback Test ===")
    
    # You would typically get these transaction IDs from previous detect-fraud calls
    # For this test, we'll use dummy IDs
    transaction_id_legitimate = f"test_legitimate_{int(time.time())}"
    transaction_id_fraudulent = f"test_fraudulent_{int(time.time())}"
    
    # Test feedback for a legitimate transaction
    print("\nSubmitting feedback for legitimate transaction:")
    test_feedback_endpoint(transaction_id_legitimate, False)
    
    # Test feedback for a fraudulent transaction
    print("\nSubmitting feedback for fraudulent transaction:")
    test_feedback_endpoint(transaction_id_fraudulent, True)
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()
