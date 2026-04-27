#!/usr/bin/env python3
"""
Integration Tests Runner - Credit Card Fraud Detection
Runs integration tests for API endpoints
"""

import os
import sys
import subprocess
import argparse
import time
import requests
from pathlib import Path

def is_api_running(timeout=2):
    """Check if API is running on port 8000"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument('--start-api', action='store_true', help='Start API server if not running')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent.absolute()
    python_path = Path("D:/Study/AILearning/shared_Environment/Scripts/python.exe")
    
    print("\n" + "=" * 50)
    print("Credit Card Fraud Detection - Integration Tests")
    print("=" * 50)
    
    os.chdir(project_root)
    
    # Check if API is running
    api_running = is_api_running()
    api_process = None
    
    if api_running:
        print("✅ API server is already running on port 8000")
    else:
        print("⚠️  API server is not running on port 8000")
        
        if args.start_api:
            print("\nStarting API server...")
            api_process = subprocess.Popen(
                [str(python_path), "run_server.py"],
                cwd=project_root,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            print("Waiting for API server to start...")
            time.sleep(10)
            
            if is_api_running(timeout=5):
                print("✅ API server started successfully")
            else:
                print("❌ Failed to start API server")
                if api_process:
                    api_process.terminate()
                return 1
        else:
            print("❌ API server must be running. Use --start-api flag to start it automatically.")
            print("   Or run: python run_server.py")
            return 1
    
    print("\nRunning integration tests...")
    result = subprocess.run([str(python_path), "tests/run_integration_tests.py"])
    
    # Stop API if we started it
    if api_process:
        print("\nStopping API server...")
        api_process.terminate()
        print("✅ API server stopped")
    
    print("\n" + "=" * 50)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
