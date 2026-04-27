"""
Unified Deployment and Testing Script
Handles build, deploy, API testing, UI testing, and reporting
"""

import os
import sys
import time
import json
import subprocess
import argparse
from datetime import datetime
from typing import Dict, List, Tuple


class DeploymentTester:
    """Unified deployment and testing orchestrator"""
    
    def __init__(self, mode="local", verbose=False):
        self.mode = mode  # 'local' or 'docker'
        self.verbose = verbose
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.test_results = {
            "deployment_mode": mode,
            "timestamp": datetime.now().isoformat(),
            "stages": []
        }
    
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "STEP": "🔧"
        }.get(level, "📝")
        
        print(f"[{timestamp}] {prefix} {message}")
    
    def run_command(self, command: List[str], cwd=None, capture_output=True, timeout=300) -> Tuple[bool, str, str]:
        """Run a shell command and return success status and output"""
        try:
            if self.verbose:
                self.log(f"Running: {' '.join(command)}", "INFO")
            
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                shell=True if sys.platform == "win32" else False
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def stage_result(self, stage_name: str, success: bool, duration: float, details: Dict = None):
        """Record stage result"""
        self.test_results["stages"].append({
            "name": stage_name,
            "success": success,
            "duration_seconds": round(duration, 2),
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def build_docker_images(self) -> bool:
        """Build Docker images"""
        self.log("Building Docker images...", "STEP")
        start_time = time.time()
        
        try:
            # Build API image
            self.log("Building API Docker image...")
            success, stdout, stderr = self.run_command(
                ["docker", "build", "-f", "Dockerfile.api", "-t", "fraud-detection-api:latest", "."],
                timeout=600
            )
            
            if not success:
                self.log(f"Failed to build API image: {stderr}", "ERROR")
                self.stage_result("Build Docker Images", False, time.time() - start_time, {"error": stderr})
                return False
            
            # Build UI image
            self.log("Building UI Docker image...")
            success, stdout, stderr = self.run_command(
                ["docker", "build", "-f", "Dockerfile.ui", "-t", "fraud-detection-ui:latest", "."],
                timeout=600
            )
            
            if not success:
                self.log(f"Failed to build UI image: {stderr}", "ERROR")
                self.stage_result("Build Docker Images", False, time.time() - start_time, {"error": stderr})
                return False
            
            duration = time.time() - start_time
            self.log(f"Docker images built successfully in {duration:.2f}s", "SUCCESS")
            self.stage_result("Build Docker Images", True, duration)
            return True
            
        except Exception as e:
            self.log(f"Error building Docker images: {e}", "ERROR")
            self.stage_result("Build Docker Images", False, time.time() - start_time, {"error": str(e)})
            return False
    
    def deploy_docker(self) -> bool:
        """Deploy using Docker Compose"""
        self.log("Deploying with Docker Compose...", "STEP")
        start_time = time.time()
        
        try:
            # Stop any existing containers
            self.log("Stopping existing containers...")
            self.run_command(["docker-compose", "-f", "docker-compose.prod.yml", "down"], timeout=60)
            
            # Start services
            self.log("Starting services...")
            success, stdout, stderr = self.run_command(
                ["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d"],
                timeout=120
            )
            
            if not success:
                self.log(f"Failed to start services: {stderr}", "ERROR")
                self.stage_result("Deploy Docker", False, time.time() - start_time, {"error": stderr})
                return False
            
            # Wait for services to be healthy
            self.log("Waiting for services to become healthy...")
            time.sleep(15)  # Give services time to start
            
            # Check if containers are running
            success, stdout, stderr = self.run_command(
                ["docker-compose", "-f", "docker-compose.prod.yml", "ps"],
                timeout=30
            )
            
            duration = time.time() - start_time
            self.log(f"Services deployed successfully in {duration:.2f}s", "SUCCESS")
            self.stage_result("Deploy Docker", True, duration)
            return True
            
        except Exception as e:
            self.log(f"Error deploying Docker: {e}", "ERROR")
            self.stage_result("Deploy Docker", False, time.time() - start_time, {"error": str(e)})
            return False
    
    def deploy_local(self) -> bool:
        """Deploy locally (start API and UI servers)"""
        self.log("Starting local deployment...", "STEP")
        start_time = time.time()
        
        try:
            # Note: For local deployment, services should be started manually
            # This stage just verifies they are running
            
            import requests
            
            # Check if API is running
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code != 200:
                    self.log("API not responding correctly", "ERROR")
                    self.stage_result("Deploy Local", False, time.time() - start_time, 
                                    {"error": "API not healthy"})
                    return False
            except:
                self.log("API not running on http://localhost:8000", "ERROR")
                self.log("Please start the API server first: uvicorn app.main:app --host 0.0.0.0 --port 8000", "INFO")
                self.stage_result("Deploy Local", False, time.time() - start_time, 
                                {"error": "API not running"})
                return False
            
            # Check if UI is running
            try:
                response = requests.get("http://localhost:8501", timeout=5)
                if response.status_code != 200:
                    self.log("UI not responding correctly", "WARNING")
            except:
                self.log("UI not running on http://localhost:8501", "WARNING")
                self.log("Please start the UI server: streamlit run ui/app.py", "INFO")
            
            duration = time.time() - start_time
            self.log(f"Local deployment verified in {duration:.2f}s", "SUCCESS")
            self.stage_result("Deploy Local", True, duration)
            return True
            
        except Exception as e:
            self.log(f"Error verifying local deployment: {e}", "ERROR")
            self.stage_result("Deploy Local", False, time.time() - start_time, {"error": str(e)})
            return False
    
    def run_api_tests(self) -> bool:
        """Run comprehensive API tests"""
        self.log("Running API tests...", "STEP")
        start_time = time.time()
        
        try:
            # Determine API URL based on deployment mode
            api_url = "http://fraud-detection-api:8000" if self.mode == "docker" else "http://localhost:8000"
            
            # For docker mode, we need to run tests from within a container or use localhost
            if self.mode == "docker":
                api_url = "http://localhost:8000"  # Access via port mapping
            
            # Run the comprehensive API test
            test_script = os.path.join(self.project_root, "tests", "test_api_comprehensive.py")
            
            success, stdout, stderr = self.run_command(
                [sys.executable, test_script, "--api-url", api_url],
                timeout=180
            )
            
            if self.verbose:
                print(stdout)
            
            # Parse results if available
            try:
                # Look for the latest report file
                reports_dir = os.path.join(self.project_root, "tests", "reports")
                if os.path.exists(reports_dir):
                    json_files = [f for f in os.listdir(reports_dir) if f.startswith("api_test_") and f.endswith(".json")]
                    if json_files:
                        latest_report = max([os.path.join(reports_dir, f) for f in json_files], key=os.path.getmtime)
                        with open(latest_report, 'r') as f:
                            api_results = json.load(f)
                            
                        passed = api_results.get("passed", 0)
                        failed = api_results.get("failed", 0)
                        total = api_results.get("total_tests", 0)
                        
                        self.log(f"API Tests: {passed}/{total} passed, {failed} failed")
                        
                        duration = time.time() - start_time
                        self.stage_result("API Tests", failed == 0, duration, {
                            "total": total,
                            "passed": passed,
                            "failed": failed,
                            "report": latest_report
                        })
                        
                        if failed == 0:
                            self.log("All API tests passed!", "SUCCESS")
                            return True
                        else:
                            self.log(f"{failed} API test(s) failed", "ERROR")
                            return False
            except Exception as e:
                self.log(f"Could not parse API test results: {e}", "WARNING")
            
            duration = time.time() - start_time
            self.stage_result("API Tests", success, duration)
            
            if success:
                self.log("API tests completed successfully", "SUCCESS")
            else:
                self.log("API tests failed", "ERROR")
            
            return success
            
        except Exception as e:
            self.log(f"Error running API tests: {e}", "ERROR")
            self.stage_result("API Tests", False, time.time() - start_time, {"error": str(e)})
            return False
    
    def run_ui_tests(self) -> bool:
        """Run comprehensive UI tests"""
        self.log("Running UI tests...", "STEP")
        start_time = time.time()
        
        try:
            # Determine UI URL based on deployment mode
            ui_url = "http://localhost:8501"
            api_url = "http://localhost:8000"
            
            # Run the comprehensive UI test
            test_script = os.path.join(self.project_root, "tests", "test_ui_e2e.py")
            
            # Check if Playwright is installed
            self.log("Installing Playwright browsers if needed...")
            self.run_command([sys.executable, "-m", "playwright", "install", "chromium"], timeout=300)
            
            success, stdout, stderr = self.run_command(
                [sys.executable, test_script, "--ui-url", ui_url, "--api-url", api_url],
                timeout=300
            )
            
            if self.verbose:
                print(stdout)
            
            # Parse results if available
            try:
                reports_dir = os.path.join(self.project_root, "tests", "reports")
                if os.path.exists(reports_dir):
                    json_files = [f for f in os.listdir(reports_dir) if f.startswith("ui_e2e_test_") and f.endswith(".json")]
                    if json_files:
                        latest_report = max([os.path.join(reports_dir, f) for f in json_files], key=os.path.getmtime)
                        with open(latest_report, 'r') as f:
                            ui_results = json.load(f)
                        
                        passed = ui_results.get("passed", 0)
                        failed = ui_results.get("failed", 0)
                        total = ui_results.get("total_tests", 0)
                        
                        self.log(f"UI Tests: {passed}/{total} passed, {failed} failed")
                        
                        duration = time.time() - start_time
                        self.stage_result("UI Tests", failed == 0, duration, {
                            "total": total,
                            "passed": passed,
                            "failed": failed,
                            "report": latest_report
                        })
                        
                        if failed == 0:
                            self.log("All UI tests passed!", "SUCCESS")
                            return True
                        else:
                            self.log(f"{failed} UI test(s) failed", "ERROR")
                            return False
            except Exception as e:
                self.log(f"Could not parse UI test results: {e}", "WARNING")
            
            duration = time.time() - start_time
            self.stage_result("UI Tests", success, duration)
            
            if success:
                self.log("UI tests completed successfully", "SUCCESS")
            else:
                self.log("UI tests failed", "ERROR")
            
            return success
            
        except Exception as e:
            self.log(f"Error running UI tests: {e}", "ERROR")
            self.stage_result("UI Tests", False, time.time() - start_time, {"error": str(e)})
            return False
    
    def generate_final_report(self):
        """Generate comprehensive deployment and test report"""
        self.log("Generating final report...", "STEP")
        
        # Calculate summary
        total_stages = len(self.test_results["stages"])
        successful_stages = sum(1 for s in self.test_results["stages"] if s["success"])
        failed_stages = total_stages - successful_stages
        
        # Print summary
        print("\n" + "="*80)
        print("  DEPLOYMENT AND TEST SUMMARY")
        print("="*80 + "\n")
        
        print(f"Deployment Mode: {self.mode.upper()}")
        print(f"Total Stages:    {total_stages}")
        print(f"Successful:      {successful_stages}")
        print(f"Failed:          {failed_stages}")
        print()
        
        # Print stage details
        for stage in self.test_results["stages"]:
            status_icon = "✅" if stage["success"] else "❌"
            print(f"{status_icon} {stage['name']}: {stage['duration_seconds']}s")
            if not stage["success"] and "error" in stage.get("details", {}):
                print(f"   Error: {stage['details']['error'][:100]}")
        
        print()
        
        # Save report
        os.makedirs("tests/reports", exist_ok=True)
        report_file = f"tests/reports/deployment_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"📄 Report saved to: {report_file}")
        
        # Generate HTML report
        html_report = self.generate_html_report()
        html_file = report_file.replace('.json', '.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        print(f"📄 HTML report saved to: {html_file}")
        print("="*80 + "\n")
        
        if failed_stages == 0:
            print("🎉 ALL STAGES COMPLETED SUCCESSFULLY!")
            return 0
        else:
            print(f"⚠️  {failed_stages} STAGE(S) FAILED")
            return 1
    
    def generate_html_report(self):
        """Generate HTML report"""
        total_stages = len(self.test_results["stages"])
        successful_stages = sum(1 for s in self.test_results["stages"] if s["success"])
        failed_stages = total_stages - successful_stages
        success_rate = (successful_stages / total_stages * 100) if total_stages > 0 else 0
        
        stage_rows = ""
        for stage in self.test_results["stages"]:
            status_class = "passed" if stage["success"] else "failed"
            status_icon = "✅" if stage["success"] else "❌"
            
            details = stage.get("details", {})
            details_html = ""
            if details:
                if "total" in details:
                    details_html = f"{details.get('passed', 0)}/{details.get('total', 0)} tests passed"
                elif "error" in details:
                    details_html = f"Error: {details['error'][:100]}"
            
            stage_rows += f"""
            <tr class="{status_class}">
                <td>{status_icon} {stage['name']}</td>
                <td>{stage['duration_seconds']}s</td>
                <td>{'Success' if stage['success'] else 'Failed'}</td>
                <td>{details_html}</td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Deployment & Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .mode {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .summary-card {{ padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card h3 {{ margin: 0; font-size: 32px; }}
        .summary-card p {{ margin: 5px 0 0 0; color: #666; }}
        .total {{ background: #2196F3; color: white; }}
        .passed {{ background: #4CAF50; color: white; }}
        .failed {{ background: #f44336; color: white; }}
        .rate {{ background: #FF9800; color: white; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #333; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        tr.passed td {{ background: #f1f8f4; }}
        tr.failed td {{ background: #ffebee; }}
        .timestamp {{ color: #666; font-size: 14px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Deployment & Test Report</h1>
        <p class="timestamp">Generated: {self.test_results['timestamp']}</p>
        
        <div class="mode">
            <strong>Deployment Mode:</strong> {self.test_results['deployment_mode'].upper()}
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>{total_stages}</h3>
                <p>Total Stages</p>
            </div>
            <div class="summary-card passed">
                <h3>{successful_stages}</h3>
                <p>Successful</p>
            </div>
            <div class="summary-card failed">
                <h3>{failed_stages}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card rate">
                <h3>{success_rate:.1f}%</h3>
                <p>Success Rate</p>
            </div>
        </div>
        
        <h2>Stage Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Duration</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {stage_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html
    
    def run(self):
        """Run the complete deployment and test pipeline"""
        print("\n" + "="*80)
        print("  CREDIT CARD FRAUD DETECTION - DEPLOYMENT & TEST AUTOMATION")
        print("="*80 + "\n")
        
        start_time = time.time()
        
        # Stage 1: Build (Docker mode only)
        if self.mode == "docker":
            if not self.build_docker_images():
                self.log("Build failed, stopping pipeline", "ERROR")
                self.generate_final_report()
                return 1
        
        # Stage 2: Deploy
        if self.mode == "docker":
            if not self.deploy_docker():
                self.log("Deployment failed, stopping pipeline", "ERROR")
                self.generate_final_report()
                return 1
        else:
            if not self.deploy_local():
                self.log("Local deployment verification failed", "ERROR")
                self.generate_final_report()
                return 1
        
        # Stage 3: Run API Tests
        api_test_success = self.run_api_tests()
        
        # Stage 4: Run UI Tests
        ui_test_success = self.run_ui_tests()
        
        # Generate final report
        total_time = time.time() - start_time
        self.log(f"Total pipeline duration: {total_time:.2f}s", "INFO")
        
        exit_code = self.generate_final_report()
        
        return exit_code


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Unified Deployment and Testing Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Local deployment (requires API and UI to be running)
  python deploy_and_test.py --mode local
  
  # Docker deployment (builds and deploys)
  python deploy_and_test.py --mode docker
  
  # Verbose output
  python deploy_and_test.py --mode docker --verbose
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['local', 'docker'],
        default='local',
        help='Deployment mode: local (use running services) or docker (build and deploy)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    deployer = DeploymentTester(mode=args.mode, verbose=args.verbose)
    exit_code = deployer.run()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
