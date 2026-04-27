#!/usr/bin/env python3
"""
Unit Tests Runner - Credit Card Fraud Detection
Runs unit tests with code coverage
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Run unit tests with coverage")
    parser.add_argument('--no-coverage', action='store_true', help='Skip code coverage')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent.absolute()
    python_path = Path("D:/Study/AILearning/shared_Environment/Scripts/python.exe")
    
    print("\n" + "=" * 50)
    print("Credit Card Fraud Detection - Unit Tests")
    print("=" * 50)
    
    os.chdir(project_root)
    
    test_files = [
        "tests/test_ml_model.py",
        "tests/test_system.py",
        "tests/test_transaction_endpoints.py"
    ]
    
    cmd = [str(python_path), "-m", "pytest"] + test_files
    
    if not args.no_coverage:
        print("\nRunning unit tests with code coverage...")
        cmd.extend(["--cov=app", "--cov-report=term", "--cov-report=html"])
    else:
        print("\nRunning unit tests without coverage...")
    
    if args.verbose:
        cmd.append("-v")
    
    result = subprocess.run(cmd)
    
    if result.returncode in (0, 1) and not args.no_coverage:
        print("\n✅ Coverage report generated in 'htmlcov' directory")
        print("   Open htmlcov/index.html to view detailed coverage")
    
    print("\n" + "=" * 50)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
