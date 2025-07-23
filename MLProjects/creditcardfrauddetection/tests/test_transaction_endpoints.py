#!/usr/bin/env python
"""
Test script to verify the transaction history endpoints.
"""
import sys
import json
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# API settings
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "development_api_key")

def test_transaction_endpoints():
    """Test the transaction endpoints."""
    print("Testing Transaction History Endpoints...")
    
    # Set headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # Test get all transactions
    print("\n1. Testing GET /api/v1/transactions")
    try:
        response = requests.get(f"{API_URL}/api/v1/transactions", headers=headers)
        
        if response.status_code == 200:
            transactions = response.json()
            print(f"✅ Success! Received {len(transactions)} transactions")
            print(f"Sample transaction: {json.dumps(transactions[0], indent=2)}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test get a specific transaction (first try with a valid format that should exist)
    print("\n2. Testing GET /api/v1/transactions/{transaction_id} with valid ID")
    try:
        # First get all transactions to find a valid ID
        all_response = requests.get(f"{API_URL}/api/v1/transactions", headers=headers)
        
        if all_response.status_code == 200:
            all_transactions = all_response.json()
            if all_transactions:
                transaction_id = all_transactions[0]["transaction_id"]
                print(f"Using transaction ID: {transaction_id}")
                
                # Now get the specific transaction
                response = requests.get(f"{API_URL}/api/v1/transactions/{transaction_id}", headers=headers)
                
                if response.status_code == 200:
                    transaction = response.json()
                    print(f"✅ Success! Retrieved transaction details: {json.dumps(transaction, indent=2)}")
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
            else:
                print("❌ No transactions available to test with")
        else:
            print(f"❌ Error getting transactions: {all_response.status_code} - {all_response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
      # Test with an invalid transaction ID
    print("\n3. Testing GET /api/v1/transactions/{transaction_id} with invalid ID")
    try:
        invalid_id = "nonexistent_transaction_id"
        response = requests.get(f"{API_URL}/api/v1/transactions/{invalid_id}", headers=headers)
        
        if response.status_code == 404:
            print(f"✅ Success! Correctly returned 404 for nonexistent transaction ID")
        else:
            print(f"❌ Unexpected status code: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        
    # Test with predefined test transactions
    print("\n4. Testing GET /api/v1/transactions/test_transaction_1")
    try:
        response = requests.get(f"{API_URL}/api/v1/transactions/test_transaction_1", headers=headers)
        
        if response.status_code == 200:
            transaction = response.json()
            print(f"✅ Success! Retrieved test transaction: {json.dumps(transaction, indent=2)}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        
    print("\n5. Testing GET /api/v1/transactions/test_fraud_transaction_1")
    try:
        response = requests.get(f"{API_URL}/api/v1/transactions/test_fraud_transaction_1", headers=headers)
        
        if response.status_code == 200:
            transaction = response.json()
            print(f"✅ Success! Retrieved fraud test transaction: {json.dumps(transaction, indent=2)}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_transaction_endpoints()
