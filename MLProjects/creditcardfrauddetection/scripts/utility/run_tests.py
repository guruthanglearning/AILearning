#!/usr/bin/env python
"""
Script to start the API server and run tests
"""

import os
import sys
import subprocess
import time
import signal
import platform

def is_port_in_use(port):
    """Check if a port is in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    """Start the API server and run tests"""
    print("Starting Credit Card Fraud Detection System Test")
    print("="*50)
      # Get the paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(os.path.dirname(script_dir))  # Go up two levels: utility -> scripts -> project root
    python_path = os.path.join("d:", "Study", "AILearning", "shared_Environment", "Scripts", "python.exe")
    
    # Check if the API server is already running
    if is_port_in_use(8000):
        print("API server is already running on port 8000.")
    else:
        print("Starting API server...")
        
        # Start the API server
        server_process = None
        try:
            # Use different commands based on the operating system
            if platform.system() == "Windows":
                server_process = subprocess.Popen(
                    [python_path, os.path.join(project_dir, "run_server.py")],
                    cwd=project_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                server_process = subprocess.Popen(
                    [python_path, os.path.join(project_dir, "run_server.py")],
                    cwd=project_dir
                )
            
            # Wait for the server to start
            print("Waiting for API server to start...")
            max_wait = 30  # seconds
            start_time = time.time()
            while not is_port_in_use(8000):
                if time.time() - start_time > max_wait:
                    print("Timed out waiting for API server to start")
                    if server_process:
                        server_process.terminate()
                    return 1
                time.sleep(1)
                
            print(f"API server started successfully (PID: {server_process.pid})")
            
            # Give the server a bit more time to initialize fully
            time.sleep(2)
        
        except Exception as e:
            print(f"Failed to start API server: {str(e)}")
            return 1
      # Run the API tests
    print("\nRunning API tests...")
    test_process = subprocess.run(
        [python_path, os.path.join(project_dir, "tests", "api_test.py")],
        cwd=project_dir
    )
    
    # Stop the server if we started it
    if server_process:
        print("\nStopping API server...")
        if platform.system() == "Windows":
            # On Windows, we need to use taskkill to kill the process tree
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(server_process.pid)])
        else:
            server_process.terminate()
            server_process.wait(timeout=5)
        print("API server stopped")
    
    # Return the exit code from the test process
    return test_process.returncode

if __name__ == "__main__":
    sys.exit(main())
