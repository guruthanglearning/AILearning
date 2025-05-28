#!/usr/bin/env python
"""
Verify the environment setup for the Credit Card Fraud Detection system.
This script checks that all necessary dependencies are installed and accessible.
"""

import importlib
import sys
from typing import List, Dict

def check_modules(modules_to_check: List[Dict]) -> bool:
    """Check if modules are installed and can be imported."""
    all_passed = True
    
    print("\nChecking required modules:")
    print("=========================")
    
    for module_info in modules_to_check:
        module_name = module_info["module"]
        description = module_info.get("description", "")
        min_version = module_info.get("min_version")
        import_name = module_info.get("import_name", module_name)
        
        try:
            # Special case for scikit-learn
            if module_name == "scikit-learn":
                import sklearn
                module = sklearn
            else:
                module = importlib.import_module(import_name)
                
            version = getattr(module, "__version__", "unknown")
            if min_version and version != "unknown":
                if version < min_version:
                    print(f"X {module_name} (version {version}, but {min_version}+ is required) - {description}")
                    all_passed = False
                    continue
            
            print(f"+ {module_name} (version {version}) - {description}")
        except ImportError:
            print(f"X {module_name} not found - {description}")
            all_passed = False
    
    return all_passed

def check_environment() -> bool:
    """Verify the environment has all required dependencies."""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Define modules to check - both API and UI dependencies
    modules = [
        {"module": "fastapi", "description": "API framework", "min_version": "0.103.0"},
        {"module": "pydantic", "description": "Data validation", "min_version": "2.0.0"},
        {"module": "uvicorn", "description": "ASGI server", "min_version": "0.23.0"},
        {"module": "numpy", "description": "Numerical computation", "min_version": "1.24.0"},
        {"module": "pandas", "description": "Data manipulation", "min_version": "2.0.0"},
        {"module": "scikit-learn", "description": "Machine learning", "min_version": "1.3.0"},
        {"module": "langchain", "description": "LLM framework", "min_version": "0.0.300"},
        {"module": "openai", "description": "OpenAI API client", "min_version": "1.0.0"},
        {"module": "streamlit", "description": "UI framework", "min_version": "1.28.0"},
        {"module": "plotly", "description": "Interactive visualizations", "min_version": "5.13.0"},
    ]
    
    return check_modules(modules)

if __name__ == "__main__":
    print("Credit Card Fraud Detection System - Environment Verification")
    print("===========================================================")
    success = check_environment()
    
    if success:
        print("\n[SUCCESS] All dependencies are properly installed!")
        print("The environment is correctly set up for both API and UI components.")
        sys.exit(0)
    else:
        print("\n[ERROR] Some dependencies are missing or have incorrect versions.")
        print("Please install the missing dependencies with: pip install -r requirements.txt")
        sys.exit(1)
