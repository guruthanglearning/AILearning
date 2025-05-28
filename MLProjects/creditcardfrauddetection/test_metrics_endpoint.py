"""
Simple test for the metrics endpoint
"""
import requests
import json
import time

print("Testing metrics endpoint...")

# Set up the API key
headers = {
    "X-API-Key": "development_api_key_for_testing"
}

# First test the health endpoint to make sure the server is running
print("Testing health endpoint first...")
try:
    health_response = requests.get("http://localhost:8000/health", headers=headers, timeout=5)
    print(f"Health endpoint response: {health_response.status_code}")
    print(health_response.json())
except Exception as e:
    print(f"Health endpoint error: {str(e)}")

# Wait a moment
print("Waiting 2 seconds...")
time.sleep(2)

# Test the metrics endpoint
print("Testing metrics endpoint...")
try:
    response = requests.get("http://localhost:8000/metrics", headers=headers, timeout=10)
    if response.status_code == 200:
        print("✅ API metrics endpoint successful!")
        print(f"Status code: {response.status_code}")
        print("Response (first model):")
        data = response.json()
        print(json.dumps(data["models"][0], indent=2))
        print(f"Total models: {len(data['models'])}")
    else:
        print("❌ API metrics endpoint failed!")
        print(f"Status code: {response.status_code}")
        print("Response:")
        print(response.text)
except Exception as e:
    print(f"❌ Error: {str(e)}")
