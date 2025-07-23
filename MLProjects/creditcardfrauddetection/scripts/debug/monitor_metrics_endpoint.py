#!/usr/bin/env python
"""
Monitor script for the metrics API endpoint.
This script provides a non-interactive way to monitor the metrics endpoint.
Created: June 13, 2025
"""

import sys
import os
import requests
import json
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
print(f"Project root: {project_root}")
sys.path.append(str(project_root))

# Import necessary modules
from app.services.fraud_detection_service import FraudDetectionService

def print_separator(title=None):
    """Print a separator line with optional title."""
    print("\n" + "="*80)
    if title:
        print(title.center(80))
        print("="*80)

def monitor_metrics_endpoint():
    """Monitor the metrics endpoint"""
    print_separator("Starting metrics endpoint monitoring")
    
    # Set up the API key
    headers = {
        "X-API-Key": "development_api_key_for_testing"
    }
    
    # Method 1: Direct call to the service
    print_separator("METHOD 1: Direct call to FraudDetectionService")
    try:
        fraud_service = FraudDetectionService()
        print("Calling fraud_service.get_model_metrics()...")
        start_time = time.time()
        metrics = fraud_service.get_model_metrics()
        duration = time.time() - start_time
        print(f"Call completed in {duration:.2f} seconds")
        
        # Print high-level summary
        print("\nMetrics summary:")
        print(f"- Timestamp: {metrics.get('timestamp', 'N/A')}")
        print(f"- Number of models: {len(metrics.get('models', []))}")
        print(f"- System metrics available: {', '.join(metrics.get('system', {}).keys())}")
        print(f"- Transaction metrics available: {', '.join(metrics.get('transactions', {}).keys())}")
        
        # Print model names
        if 'models' in metrics:
            print("\nModels:")
            for model in metrics['models']:
                print(f"- {model.get('name', 'Unknown')} ({model.get('type', 'Unknown')}) v{model.get('version', 'Unknown')}")
    except Exception as e:
        print(f"Error making direct service call: {str(e)}")
    
    # Method 2: Prometheus metrics endpoint
    print_separator("METHOD 2: Prometheus /metrics endpoint")
    try:
        print("Making HTTP request to /metrics...")
        start_time = time.time()
        metrics_response = requests.get("http://localhost:8000/metrics", headers=headers, timeout=5)
        duration = time.time() - start_time
        print(f"Request completed in {duration:.2f} seconds with status code {metrics_response.status_code}")
        
        if metrics_response.status_code == 200:
            print("\nResponse received! Preview of content:")
            content = metrics_response.text[:500]  # Get first 500 chars only
            print(f"{content}...")
            print(f"\n(Response truncated, total length: {len(metrics_response.text)} characters)")
    except Exception as e:
        print(f"Error calling /metrics endpoint: {str(e)}")
    
    # Method 3: API v1 metrics endpoint
    print_separator("METHOD 3: API /api/v1/metrics endpoint")
    try:
        print("Making HTTP request to /api/v1/metrics...")
        start_time = time.time()
        api_response = requests.get("http://localhost:8000/api/v1/metrics", headers=headers, timeout=5)
        duration = time.time() - start_time
        print(f"Request completed in {duration:.2f} seconds with status code {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            print("\nResponse received! Summary of content:")
            print(f"- Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"- Number of models: {len(data.get('models', []))}")
            
            # Print model performance metrics
            if 'models' in data:
                print("\nModel Performance:")
                for model in data['models']:
                    name = model.get('name', 'Unknown')
                    metrics = model.get('metrics', {})
                    print(f"- {name}: accuracy={metrics.get('accuracy', 'N/A'):.3f}, "
                          f"precision={metrics.get('precision', 'N/A'):.3f}, "
                          f"recall={metrics.get('recall', 'N/A'):.3f}, "
                          f"f1={metrics.get('f1_score', 'N/A'):.3f}")
            
            # Print system metrics
            if 'system' in data:
                print("\nSystem Metrics:")
                system = data['system']
                for key, value in system.items():
                    print(f"- {key}: {value}")
            
            # Print transaction metrics  
            if 'transactions' in data:
                print("\nTransaction Metrics:")
                txns = data['transactions']
                for key, value in txns.items():
                    print(f"- {key}: {value}")
    except Exception as e:
        print(f"Error calling /api/v1/metrics endpoint: {str(e)}")

    print_separator("Monitoring Complete")

if __name__ == "__main__":
    # Import app modules for inspection
    print("Importing application modules...")
    try:
        from app.main import app
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure you're running this from the project root directory.")
        sys.exit(1)
        
    print("Application modules imported successfully.")
    
    # Execute monitor function
    monitor_metrics_endpoint()
