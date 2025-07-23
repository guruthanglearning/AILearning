#!/usr/bin/env python
"""
Debug script for the metrics API endpoint.
This script adds breakpoints to help step through the code.
Created: June 12, 2025
Updated: June 13, 2025
"""

import sys
import os
import requests
import json
from pathlib import Path
import importlib
import traceback
import time

# Define fallback debug function
def debug_pause(msg="Debug pause point. Press Enter to continue..."):
    """Simple alternative to pdb for environments where it doesn't work."""
    print(f"\n[DEBUG PAUSE] {msg}")
    input("Press Enter to continue...")

# Try to import pdb, or use the debug function as fallback
try:
    import pdb
    HAS_PDB = True
except (ImportError, AttributeError):
    HAS_PDB = False

def set_debug_trace(msg=None):
    """Set a breakpoint with proper error handling."""
    if msg:
        print(f"[BREAKPOINT] {msg}")
        
    if HAS_PDB:
        try:
            pdb.set_trace()
        except Exception as e:
            print(f"Error setting breakpoint: {str(e)}")
            debug_pause()
    else:
        debug_pause()

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
print(f"Project root: {project_root}")
sys.path.append(str(project_root))

# Import the necessary modules for debugging
from app.api.endpoints import get_metrics
from app.services.fraud_detection_service import FraudDetectionService
from app.api.dependencies import get_fraud_detection_service

def debug_metrics_endpoint():
    """Debug the metrics endpoint"""
    print("Starting debug session for metrics endpoint...")
    
    print("1. Setting up initial breakpoint to explore imports...")
    # Set up debugging breakpoint here
    set_debug_trace("Initial breakpoint to explore imports")
    
    # Set up the API key
    headers = {
        "X-API-Key": "development_api_key_for_testing"
    }# First let's add breakpoint to step into the get_metrics route handler
    print("2. Adding breakpoint at get_metrics route handler in endpoints.py...")
    import inspect
    print(f"Function signature: {inspect.signature(get_metrics)}")
    print(f"Function source location: {inspect.getfile(get_metrics)}")
    
    # Add a breakpoint to FraudDetectionService.get_model_metrics
    print("3. Adding breakpoint at FraudDetectionService.get_model_metrics...")    # Create an instance of FraudDetectionService for debugging
    fraud_service = FraudDetectionService()
    # Set a breakpoint in the get_model_metrics method
    original_get_model_metrics = fraud_service.get_model_metrics
    
    def debug_get_model_metrics(*args, **kwargs):
        print("DEBUG: Inside get_model_metrics method")
        set_debug_trace("Inside get_model_metrics method")
        return original_get_model_metrics(*args, **kwargs)
    
    # Patch the method with our debug version
    fraud_service.get_model_metrics = debug_get_model_metrics
    
    # Try calling the method directly (optional for debugging)
    print("4. Testing direct call to get_model_metrics...")
    set_debug_trace("Before direct call to get_model_metrics")
    metrics_result = fraud_service.get_model_metrics()
    print(f"Direct call result type: {type(metrics_result)}")
      # Then try the standard Prometheus metrics endpoint
    print("5. Testing /metrics endpoint (Prometheus metrics)...")
    try:
        set_debug_trace("Before HTTP request to /metrics")
        metrics_response = requests.get("http://localhost:8000/metrics", headers=headers, timeout=5)
        print(f"Metrics endpoint response: {metrics_response.status_code}")
        if metrics_response.status_code == 200:
            print("Response received from /metrics")
    except Exception as e:
        print(f"Metrics endpoint error: {str(e)}")
    
    # Then try the API v1 version
    print("6. Testing /api/v1/metrics endpoint...")
    try:
        set_debug_trace("Before HTTP request to /api/v1/metrics")
        metrics_api_response = requests.get("http://localhost:8000/api/v1/metrics", headers=headers, timeout=5)
        print(f"API Metrics endpoint response: {metrics_api_response.status_code}")
        if metrics_api_response.status_code == 200:
            print("Response received from /api/v1/metrics")
            # Pretty print just a small section to avoid clutter
            data = metrics_api_response.json()
            print(f"Timestamp: {data.get('timestamp')}")
            print(f"Number of models: {len(data.get('models', []))}")
    except Exception as e:
        print(f"API Metrics endpoint error: {str(e)}")
    
    # Final breakpoint to explore results
    print("7. Final breakpoint for exploration...")
    set_debug_trace("Final exploration point")

    print("Debug session complete.")

def print_debugging_instructions():
    """Print instructions for using the debugger."""
    print("\n" + "=" * 80)
    print("DEBUGGER USAGE INSTRUCTIONS".center(80))
    print("=" * 80)
    print("When the debugger stops (at a breakpoint), you can use these commands:")
    print("  n or next      - Execute the current line and move to the next line")
    print("  s or step      - Step into a function call")
    print("  c or continue  - Continue execution until the next breakpoint")
    print("  q or quit      - Quit the debugger")
    print("  l or list      - Show the current code around the breakpoint")
    print("  p <expression> - Print the value of an expression")
    print("  pp <expression>- Pretty-print the value of an expression")
    print("  w or where     - Show the call stack")
    print("\nTips for debugging the metrics endpoint:")
    print("1. Use 's' to step into functions to see their implementation")
    print("2. Use 'n' to skip over function calls you're not interested in")
    print("3. Use 'p <variable>' to inspect variables (e.g., 'p metrics')")
    print("4. Use 'pp <variable>' for pretty-printed output")
    print("5. Use 'w' to see which functions called the current function\n")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    # Import app modules for inspection
    print("Importing application modules...")
    try:
        from app.main import app
        from app.api.endpoints import router as api_router
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure you're running this from the project root directory.")
        sys.exit(1)
        
    print("Application modules imported successfully.")
    
    # Print debugging instructions
    print_debugging_instructions()
    
    # Execute debug function
    debug_metrics_endpoint()
