#!/usr/bin/env python3
"""
Standalone UI Launcher for Credit Card Fraud Detection System
Runs only the Streamlit UI in the current terminal.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit UI."""
    # Get paths
    project_root = Path(__file__).parent.absolute()
    ui_path = project_root / "ui"
    
    print("=" * 60)
    print("Credit Card Fraud Detection - Streamlit UI")
    print("=" * 60)
    print(f"UI Path: {ui_path}")
    print("=" * 60)
    
    # Check if UI directory exists
    if not ui_path.exists():
        print(f"Error: UI directory not found at {ui_path}")
        return 1

    # Check if app.py exists
    app_file = ui_path / "app.py"
    if not app_file.exists():
        print(f"Error: app.py not found at {app_file}")
        return 1
    
    print("\nStarting Streamlit UI...")
    print("   URL: http://localhost:8501")
    print("   Press Ctrl+C to stop")
    print("\n" + "=" * 60 + "\n")

    try:
        # Run Streamlit using Python module (works with virtual environments)
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"],
            cwd=ui_path,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\nStreamlit UI stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\nError running Streamlit: {e}")
        return 1
    except FileNotFoundError:
        print("\nError: Streamlit not found. Install with: pip install streamlit")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
