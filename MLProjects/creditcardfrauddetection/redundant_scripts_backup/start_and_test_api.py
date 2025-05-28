"""
Script to start the API server and run tests.
This ensures that the server is running before tests are executed.
"""

import os
import sys
import time
import subprocess
import signal
import atexit
import requests
from pathlib import Path

# Set paths
PROJECT_DIR = Path("d:/Study/AILearning/MLProjects/creditcardfrauddetection")
PYTHON_PATH = Path("d:/Study/AILearning/shared_Environment/Scripts/python.exe")

def is_server_running():
    """Check if the API server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Start the API server as a subprocess."""
    print("Starting API server...")
    
    # Change to the project directory
    os.chdir(PROJECT_DIR)
    
    # Start the server process
    server_process = subprocess.Popen(
        [str(PYTHON_PATH), "run_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Register function to kill server on exit
    def cleanup():
        print("Stopping API server...")
        if server_process.poll() is None:  # If process is still running
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
    
    atexit.register(cleanup)
    
    # Wait for server to start
    print("Waiting for server to initialize...")
    max_wait = 30  # Maximum wait time in seconds
    wait_interval = 1  # Time between connection attempts
    
    for _ in range(max_wait):
        if is_server_running():
            print("Server is up and running!")
            return server_process
        
        # Check if process is still running
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print("Server failed to start!")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
            
        time.sleep(wait_interval)
        print(".", end="", flush=True)
    
    print("\nTimeout waiting for server to start!")
    return None

def run_tests():
    """Run the API tests."""
    print("\nRunning API tests...")
    result = subprocess.run(
        [str(PYTHON_PATH), "ui/api_test.py"],
        cwd=PROJECT_DIR
    )
    return result.returncode

def main():
    """Main function."""
    # Check if server is already running
    if is_server_running():
        print("API server is already running.")
    else:
        # Start server
        server_process = start_server()
        if server_process is None:
            print("Failed to start API server. Exiting.")
            return 1
    
    # Run tests
    return run_tests()

if __name__ == "__main__":
    sys.exit(main())
