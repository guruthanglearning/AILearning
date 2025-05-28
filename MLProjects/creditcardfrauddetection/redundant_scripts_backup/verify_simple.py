#!/usr/bin/env python
"""
Simple verification script for Credit Card Fraud Detection system.
"""

import importlib
import sys

def check_modules():
    """Check if modules are installed."""
    modules = [
        {"module": "fastapi", "desc": "API framework"},
        {"module": "pydantic", "desc": "Data validation"},
        {"module": "uvicorn", "desc": "ASGI server"},
        {"module": "numpy", "desc": "Numerical computation"},
        {"module": "pandas", "desc": "Data manipulation"},
        {"module": "sklearn", "desc": "Machine learning", "import_name": "sklearn"},
        {"module": "langchain", "desc": "LLM framework"},
        {"module": "openai", "desc": "OpenAI API client"},
        {"module": "streamlit", "desc": "UI framework"},
        {"module": "plotly", "desc": "Interactive visualizations"},
    ]
    
    print("\nChecking required modules:")
    print("=========================")
    
    all_passed = True
    for module_info in modules:
        module_name = module_info["module"]
        desc = module_info.get("desc", "")
        import_name = module_info.get("import_name", module_name)
        
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, "__version__", "unknown")
            print(f"+ {module_name} (version {version}) - {desc}")
        except ImportError:
            print(f"X {module_name} not found - {desc}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("Credit Card Fraud Detection System - Environment Verification")
    print("===========================================================")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    success = check_modules()
    
    if success:
        print("\n[SUCCESS] All dependencies are properly installed!")
        sys.exit(0)
    else:
        print("\n[ERROR] Some dependencies are missing.")
        print("Please install the missing dependencies with: pip install -r requirements.txt")
        sys.exit(1)
