#!/usr/bin/env python3
"""
ALL TESTS RUNNER (UBER SCRIPT)
Credit Card Fraud Detection System
Runs all test suites: Unit, Integration, and E2E with comprehensive reporting
"""

import os
import sys
import subprocess
import argparse
import json
import time
import requests
from pathlib import Path
from datetime import datetime

def is_service_running(port, timeout=2):
    """Check if service is running on specified port"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def run_test_suite(name, description, command, skip=False, verbose=False):
    """Run a test suite and return results"""
    result = {
        "name": name,
        "description": description,
        "status": "NOT_RUN",
        "start_time": None,
        "end_time": None,
        "duration_seconds": 0,
        "exit_code": None,
        "error": None
    }
    
    if skip:
        print(f"\n[{name}] SKIPPED")
        print(f"  {description}")
        result["status"] = "SKIPPED"
        return result, True
    
    print("\n" + "-" * 60)
    print(f"[{name}] STARTING")
    print(f"  {description}")
    print("-" * 60)
    
    result["start_time"] = datetime.now().isoformat()
    start_time = time.time()
    
    try:
        process_result = subprocess.run(command, shell=False)
        exit_code = process_result.returncode
        result["exit_code"] = exit_code
        
        end_time = time.time()
        duration = end_time - start_time
        result["end_time"] = datetime.now().isoformat()
        result["duration_seconds"] = round(duration, 2)
        
        if exit_code == 0:
            print(f"\n[{name}] ✅ PASSED ({duration:.2f}s)")
            result["status"] = "PASSED"
            return result, True
        else:
            print(f"\n[{name}] ❌ FAILED (exit code: {exit_code}, {duration:.2f}s)")
            result["status"] = "FAILED"
            result["error"] = f"Exit code: {exit_code}"
            return result, False
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        result["end_time"] = datetime.now().isoformat()
        result["duration_seconds"] = round(duration, 2)
        result["status"] = "ERROR"
        result["error"] = str(e)
        
        print(f"\n[{name}] ❌ ERROR ({duration:.2f}s)")
        print(f"  Error: {e}")
        return result, False

def generate_html_report(results, output_path):
    """Generate HTML report from results"""
    total_duration = sum(s["duration_seconds"] for s in results["suites"])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Results - Credit Card Fraud Detection</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ flex: 1; padding: 20px; border-radius: 5px; text-align: center; }}
        .stat-box h3 {{ margin: 0; font-size: 36px; }}
        .stat-box p {{ margin: 10px 0 0 0; color: #666; }}
        .passed {{ background-color: #d4edda; color: #155724; }}
        .failed {{ background-color: #f8d7da; color: #721c24; }}
        .skipped {{ background-color: #fff3cd; color: #856404; }}
        .total {{ background-color: #d1ecf1; color: #0c5460; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #007bff; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status-passed {{ color: #28a745; font-weight: bold; }}
        .status-failed {{ color: #dc3545; font-weight: bold; }}
        .status-error {{ color: #dc3545; font-weight: bold; }}
        .status-skipped {{ color: #ffc107; font-weight: bold; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Test Execution Report</h1>
        <p><strong>Project:</strong> Credit Card Fraud Detection System</p>
        <p><strong>Timestamp:</strong> {results['timestamp']}</p>
        <p><strong>Total Duration:</strong> {total_duration:.2f} seconds</p>
        
        <h2>Summary</h2>
        <div class="summary">
            <div class="stat-box total">
                <h3>{results['summary']['total_suites']}</h3>
                <p>Total Suites</p>
            </div>
            <div class="stat-box passed">
                <h3>{results['summary']['passed_suites']}</h3>
                <p>Passed</p>
            </div>
            <div class="stat-box failed">
                <h3>{results['summary']['failed_suites']}</h3>
                <p>Failed</p>
            </div>
            <div class="stat-box skipped">
                <h3>{results['summary']['skipped_suites']}</h3>
                <p>Skipped</p>
            </div>
        </div>
        
        <h2>Test Suite Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Suite</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for suite in results["suites"]:
        status_class = f"status-{suite['status'].lower()}"
        error_info = f"<br><small>Error: {suite['error']}</small>" if suite.get('error') else ""
        html_content += f"""
                <tr>
                    <td><strong>{suite['name']}</strong><br><small>{suite['description']}</small></td>
                    <td class="{status_class}">{suite['status']}</td>
                    <td>{suite['duration_seconds']}</td>
                    <td>Exit Code: {suite.get('exit_code', 'N/A')}{error_info}</td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>Generated by Credit Card Fraud Detection Test Suite</p>
            <p>For detailed logs, check individual test reports in the tests/reports directory</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description="Run all test suites")
    parser.add_argument('--skip-unit', action='store_true', help='Skip unit tests')
    parser.add_argument('--skip-integration', action='store_true', help='Skip integration tests')
    parser.add_argument('--skip-e2e', action='store_true', help='Skip E2E tests')
    parser.add_argument('--stop-on-failure', action='store_true', help='Stop on first failure')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--output-report', default=f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", help='Output report filename')
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent.absolute()
    python_path = Path("D:/Study/AILearning/shared_Environment/Scripts/python.exe")
    
    results = {
        "test_suite": "All Tests",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "project_root": str(project_root),
            "python_path": str(python_path)
        },
        "summary": {
            "total_suites": 0,
            "passed_suites": 0,
            "failed_suites": 0,
            "skipped_suites": 0
        },
        "suites": []
    }
    
    print("\n" + "=" * 60)
    print("  CREDIT CARD FRAUD DETECTION - ALL TESTS RUNNER")
    print("=" * 60)
    print(f"  Project: {project_root}")
    print(f"  Timestamp: {results['timestamp']}")
    print("=" * 60)
    
    os.chdir(project_root)
    
    all_passed = True
    
    # 1. Unit Tests
    results["summary"]["total_suites"] += 1
    unit_cmd = [str(python_path), "-m", "pytest", 
                "tests/test_ml_model.py", 
                "tests/test_system.py", 
                "tests/test_transaction_endpoints.py",
                "--cov=app", "--cov-report=term", "--cov-report=html"]
    if args.verbose:
        unit_cmd.append("-v")
    
    suite_result, passed = run_test_suite(
        "Unit Tests",
        "Testing ML models, system components, and transaction endpoints with code coverage",
        unit_cmd,
        skip=args.skip_unit,
        verbose=args.verbose
    )
    results["suites"].append(suite_result)
    
    if suite_result["status"] == "PASSED":
        results["summary"]["passed_suites"] += 1
    elif suite_result["status"] == "SKIPPED":
        results["summary"]["skipped_suites"] += 1
    else:
        results["summary"]["failed_suites"] += 1
    
    if not passed and args.stop_on_failure:
        print("\n❌ Stopping due to unit test failure (--stop-on-failure enabled)")
        all_passed = False
    else:
        all_passed = all_passed and passed
    
    # 2. Integration Tests
    if all_passed or not args.stop_on_failure:
        results["summary"]["total_suites"] += 1
        integration_cmd = [str(python_path), "tests/run_integration_tests.py"]
        
        suite_result, passed = run_test_suite(
            "Integration Tests",
            "Testing API endpoints: fraud detection, feedback, and pattern ingestion",
            integration_cmd,
            skip=args.skip_integration,
            verbose=args.verbose
        )
        results["suites"].append(suite_result)
        
        if suite_result["status"] == "PASSED":
            results["summary"]["passed_suites"] += 1
        elif suite_result["status"] == "SKIPPED":
            results["summary"]["skipped_suites"] += 1
        else:
            results["summary"]["failed_suites"] += 1
        
        if not passed and args.stop_on_failure:
            print("\n❌ Stopping due to integration test failure (--stop-on-failure enabled)")
            all_passed = False
        else:
            all_passed = all_passed and passed
    
    # 3. Playwright E2E Tests
    if all_passed or not args.stop_on_failure:
        # Check if services are running
        api_running = is_service_running(8000)
        ui_running = is_service_running(8501)
        
        skip_e2e = args.skip_e2e
        if not api_running or not ui_running:
            print("\n⚠️  Warning: API or UI not running. Playwright tests will be skipped.")
            print("   Start services with: python start.py both")
            skip_e2e = True
        
        results["summary"]["total_suites"] += 1
        e2e_cmd = [str(python_path), "tests/test_ui_e2e.py"]
        
        suite_result, passed = run_test_suite(
            "Playwright E2E Tests",
            "Testing UI interactions, navigation, forms, and end-to-end workflows",
            e2e_cmd,
            skip=skip_e2e,
            verbose=args.verbose
        )
        results["suites"].append(suite_result)
        
        if suite_result["status"] == "PASSED":
            results["summary"]["passed_suites"] += 1
        elif suite_result["status"] == "SKIPPED":
            results["summary"]["skipped_suites"] += 1
        else:
            results["summary"]["failed_suites"] += 1
        
        all_passed = all_passed and passed
    
    # Generate summary
    print("\n" + "=" * 60)
    print("  TEST EXECUTION SUMMARY")
    print("=" * 60)
    
    total_duration = sum(s["duration_seconds"] for s in results["suites"])
    print(f"  Total Suites:   {results['summary']['total_suites']}")
    print(f"  Passed:         {results['summary']['passed_suites']}")
    print(f"  Failed:         {results['summary']['failed_suites']}")
    print(f"  Skipped:        {results['summary']['skipped_suites']}")
    print(f"  Total Duration: {total_duration:.2f}s")
    print("=" * 60)
    
    print("\nSuite Details:")
    for suite in results["suites"]:
        status_icon = {"PASSED": "✅", "FAILED": "❌", "ERROR": "❌", "SKIPPED": "⏭️ "}.get(suite["status"], "⚪")
        print(f"  {status_icon} {suite['name']}: {suite['status']}", end="")
        if suite["duration_seconds"] > 0:
            print(f" ({suite['duration_seconds']}s)")
        else:
            print()
        
        if suite.get("error"):
            print(f"     Error: {suite['error']}")
    
    print("=" * 60)
    
    # Save reports
    reports_dir = project_root / "tests" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = reports_dir / args.output_report
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Generate HTML report
    html_report = report_path.with_suffix('.html')
    generate_html_report(results, html_report)
    print(f"📄 HTML report saved to: {html_report}")
    
    print("\n" + "=" * 60 + "\n")
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
