#!/usr/bin/env python3
"""
Simple startup script for the Credit Card Fraud Detection System
Usage: python start.py [api|ui|both]
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    """Main startup function."""
    args = sys.argv[1:] if len(sys.argv) > 1 else ["both"]
    mode = args[0].lower()
    
    project_root = Path(__file__).parent
    
    print("Credit Card Fraud Detection System")
    print("==================================")
    
    if mode in ["api", "both"]:
        print("Starting API server...")
        try:
            if mode == "api":
                # Start API server in foreground
                subprocess.run([sys.executable, "run_server.py"], cwd=project_root)
            else:
                # Start API server in background for "both" mode
                subprocess.Popen([sys.executable, "run_server.py"], cwd=project_root)
                print("API server started in background")
        except Exception as e:
            print(f"Error starting API server: {e}")
            return 1
    
    if mode in ["ui", "both"]:
        print("Starting UI...")
        try:
            ui_path = project_root / "ui"
            subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], cwd=ui_path)
        except Exception as e:
            print(f"Error starting UI: {e}")
            return 1
    
    if mode not in ["api", "ui", "both"]:
        print("Usage: python start.py [api|ui|both]")
        print("  api  - Start only the API server")
        print("  ui   - Start only the UI")
        print("  both - Start both API and UI (default)")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
