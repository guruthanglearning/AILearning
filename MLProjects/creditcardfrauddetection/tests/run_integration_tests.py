"""
Test runner script for the Credit Card Fraud Detection system.
Runs all integration tests sequentially.
Supports both local and Docker deployment modes.
"""

import os
import time
import importlib
import sys
import argparse

def run_test_module(module_name):
    """Import and run a test module."""
    print(f"\n{'=' * 30}")
    print(f"Running test module: {module_name}")
    print(f"{'=' * 30}\n")
    
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Run the main function
        if hasattr(module, 'main'):
            result = module.main()
            # Check if main returns a boolean result
            if isinstance(result, bool):
                return result
            # Otherwise assume success if no exception
            return True
        else:
            print(f"Error: {module_name} does not have a main() function")
            return False
    except ImportError as e:
        print(f"Error importing {module_name}: {str(e)}")
        print(f"Make sure the module exists and is properly formatted.")
        return False
    except Exception as e:
        import traceback
        print(f"Error running {module_name}: {str(e)}")
        print("Detailed traceback:")
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    parser = argparse.ArgumentParser(description='Run integration tests for Credit Card Fraud Detection')
    parser.add_argument('--mode', choices=['local', 'docker'], default='local',
                      help='Deployment mode: local (localhost) or docker (containers)')
    args = parser.parse_args()
    
    # Set API URL based on mode
    if args.mode == 'docker':
        api_url = "http://localhost:8000"  # Access from host machine
        print(f"\n🐋 Testing DOCKER deployment (API: {api_url})")
    else:
        api_url = "http://localhost:8000"
        print(f"\n💻 Testing LOCAL deployment (API: {api_url})")
    
    # Set environment variable for tests to use
    os.environ['API_URL'] = api_url
    os.environ['DEPLOYMENT_MODE'] = args.mode
    
    # Add tests directory to the path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # List of test modules to run
    test_modules = [
        "test_api_integration",
        "test_feedback_integration",
        "test_pattern_ingestion_integration"
    ]
    
    # Run all test modules
    results = {}
    test_details = {}
    start_time = time.time()
    
    for module_name in test_modules:
        module_start = time.time()
        print(f"\nRunning {module_name}...")
        try:
            success = run_test_module(module_name)
            results[module_name] = success
            test_details[module_name] = {
                "status": "PASSED" if success else "FAILED",
                "time": round(time.time() - module_start, 2),
                "error": None
            }
        except Exception as e:
            results[module_name] = False
            test_details[module_name] = {
                "status": "ERROR",
                "time": round(time.time() - module_start, 2),
                "error": str(e)
            }
        
        time.sleep(1)  # Small delay between tests
    
    # Calculate total execution time
    total_time = round(time.time() - start_time, 2)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"TEST EXECUTION SUMMARY (Total time: {total_time}s)")
    print("=" * 60)
    
    all_passed = True
    for module_name, passed in results.items():
        details = test_details[module_name]
        status = details["status"]
        test_time = details["time"]
        error = details["error"]
        
        status_str = f"{status} ({test_time}s)"
        print(f"{module_name}: {status_str}")
        if error:
            print(f"  Error: {error}")
        
        all_passed = all_passed and passed
    
    print("\nOverall Result:", "PASSED" if all_passed else "FAILED")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
