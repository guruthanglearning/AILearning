#!/usr/bin/env python
"""
Test script to manually call the metrics endpoint
"""
import requests
import json
import time
import os

def test_metrics_endpoint():
    """Send a request to the metrics endpoint and print the results"""
    print("Testing metrics endpoint...")
    
    # Set up the API key for authentication
    headers = {
        "X-API-Key": "development_api_key_for_testing",
        "Accept": "application/json"
    }
    
    # Create timestamp for logging
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Sending request to /api/v1/metrics")
    
    # Make the request
    try:
        start_time = time.time()
        response = requests.get("http://localhost:8000/api/v1/metrics", headers=headers, timeout=10)
        duration = time.time() - start_time
        
        print(f"Response time: {duration:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        # Check if request was successful
        if response.status_code == 200:
            print("✅ Successfully received metrics data!")
            
            # Save response to a file for inspection
            with open("metrics_response.json", "w") as f:
                json.dump(response.json(), f, indent=2)
            print(f"Response saved to metrics_response.json")
            
            # Display a preview of the metrics
            metrics = response.json()
            print("\nMetrics Preview:")
            print(f"- Timestamp: {metrics.get('timestamp', 'N/A')}")
            print(f"- Number of models: {len(metrics.get('models', []))}")
            
            # Display model metrics if available
            if 'models' in metrics:
                print("\nModel Metrics:")
                for model in metrics['models']:
                    name = model.get('name', 'Unknown')
                    model_metrics = model.get('metrics', {})
                    print(f"- {name}: accuracy={model_metrics.get('accuracy', 'N/A')}")
                    
        else:
            print(f"❌ Failed to get metrics data. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Check if debug output file was created
    if os.path.exists("debug_metrics_request.txt"):
        print("\nDebug file found! Contents:")
        with open("debug_metrics_request.txt", "r") as f:
            print(f.read())
    else:
        print("\nNo debug file found.")
        
    # Check server logs
    print("\nCheck your server logs for BREAKPOINT messages.")

if __name__ == "__main__":
    test_metrics_endpoint()
