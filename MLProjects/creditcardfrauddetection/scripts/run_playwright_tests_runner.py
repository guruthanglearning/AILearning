#!/usr/bin/env python3
"""
Playwright E2E Tests Runner - Credit Card Fraud Detection
Runs Playwright end-to-end UI tests
"""

import os
import sys
import subprocess
import argparse
import time
import requests
from pathlib import Path

def is_service_running(port, timeout=2):
    """Check if service is running on specified port"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Run Playwright E2E tests")
    parser.add_argument('--start-services', action='store_true', help='Start API and UI servers if not running')
    parser.add_argument('--headless', action='store_true', help='Run tests in headless mode')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent.absolute()
    python_path = Path("D:/Study/AILearning/shared_Environment/Scripts/python.exe")
    
    print("\n" + "=" * 50)
    print("Credit Card Fraud Detection - Playwright E2E Tests")
    print("=" * 50)
    
    os.chdir(project_root)
    
    # Check if services are running
    api_running = is_service_running(8000)
    ui_running = is_service_running(8501)
    
    if api_running:
        print("✅ API server is running on port 8000")
    else:
        print("⚠️  API server is not running on port 8000")
    
    if ui_running:
        print("✅ UI server is running on port 8501")
    else:
        print("⚠️  UI server is not running on port 8501")
    
    api_process = None
    ui_process = None
    
    if not api_running or not ui_running:
        if args.start_services:
            if not api_running:
                print("\nStarting API server...")
                api_process = subprocess.Popen(
                    [str(python_path), "run_server.py"],
                    cwd=project_root,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                )
                time.sleep(10)
            
            if not ui_running:
                print("Starting UI server...")
                ui_process = subprocess.Popen(
                    [str(python_path), "run_ui.py"],
                    cwd=project_root,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                )
                time.sleep(8)
            
            print("✅ Services started successfully")
        else:
            print("❌ Both API and UI servers must be running. Use --start-services flag to start them automatically.")
            print("   Or run: python start.py both")
            return 1
    
    print("\nRunning Playwright E2E tests...")
    
    env = os.environ.copy()
    if args.headless:
        env["PLAYWRIGHT_HEADLESS"] = "true"
    
    result = subprocess.run([str(python_path), "tests/test_ui_e2e.py"], env=env)
    
    # Stop services if we started them
    if api_process:
        print("\nStopping API server...")
        api_process.terminate()
    
    if ui_process:
        print("Stopping UI server...")
        ui_process.terminate()
    
    if api_process or ui_process:
        print("✅ Services stopped")
    
    print("\n" + "=" * 50)
    
    # Check for latest report
    reports_dir = project_root / "tests" / "reports"
    if reports_dir.exists():
        html_files = sorted(reports_dir.glob("ui_e2e_test_*.html"), key=lambda x: x.stat().st_mtime, reverse=True)
        if html_files:
            print(f"\n📄 Test report: {html_files[0]}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
