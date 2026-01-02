#!/usr/bin/env python3
"""
Simple startup script for the Credit Card Fraud Detection System
Usage: python start.py [api|ui|both]

This script starts services in separate PowerShell windows on Windows,
or separate terminal processes on Linux/Mac.
"""

import sys
import subprocess
import os
import platform
import time
from pathlib import Path

def start_in_new_window(command, title, project_root):
    """
    Start a command in a new terminal window.
    
    Args:
        command: Command string to execute
        title: Window title
        project_root: Project root directory
    
    Returns:
        subprocess.Popen object
    """
    system = platform.system()
    
    if system == "Windows":
        # PowerShell command with proper escaping
        ps_command = f"cd '{project_root}'; {command}"
        
        # Start in new PowerShell window with -NoExit to keep window open
        return subprocess.Popen(
            ["powershell", "-NoExit", "-Command", ps_command],
            creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
        )
    elif system == "Darwin":  # macOS
        # Use osascript to open new Terminal window
        script = f'tell application "Terminal" to do script "cd {project_root} && {command}"'
        return subprocess.Popen(["osascript", "-e", script])
    else:  # Linux
        # Try common terminal emulators
        terminals = [
            ["gnome-terminal", "--", "bash", "-c", f"cd {project_root} && {command}; exec bash"],
            ["xterm", "-hold", "-e", f"cd {project_root} && {command}"],
            ["konsole", "-e", f"cd {project_root} && {command}"]
        ]
        
        for terminal_cmd in terminals:
            try:
                return subprocess.Popen(terminal_cmd)
            except FileNotFoundError:
                continue
        
        # Fallback: run in background
        print(f"Warning: Could not find terminal emulator. Running {title} in background.")
        return subprocess.Popen(command, shell=True, cwd=project_root)

def main():
    """Main startup function."""
    args = sys.argv[1:] if len(sys.argv) > 1 else ["both"]
    mode = args[0].lower()
    
    project_root = Path(__file__).parent.absolute()
    shared_env = project_root.parent.parent / "shared_Environment"
    
    print("=" * 60)
    print("Credit Card Fraud Detection System")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print(f"Shared Environment: {shared_env}")
    print(f"Mode: {mode}")
    print("=" * 60)
    
    processes = []
    
    if mode in ["api", "both"]:
        print("\n[1/2] Starting API Server in separate window...")
        try:
            # Activate virtual environment and run API server
            if platform.system() == "Windows":
                activate_cmd = f"& '{shared_env}\\Scripts\\Activate.ps1'"
                api_command = f"{activate_cmd}; python '{project_root}\\run_server.py'"
            else:
                activate_cmd = f"source {shared_env}/bin/activate"
                api_command = f"{activate_cmd} && python {project_root}/run_server.py"
            
            api_process = start_in_new_window(
                api_command,
                "Credit Card Fraud Detection - API Server",
                project_root
            )
            processes.append(("API Server", api_process))
            print("✅ API Server window opened")
            print("   URL: http://localhost:8000")
            print("   Docs: http://localhost:8000/docs")
            
            # Wait for API to start
            if mode == "both":
                print("   Waiting 8 seconds for API to initialize...")
                time.sleep(8)
                
        except Exception as e:
            print(f"❌ Error starting API server: {e}")
            return 1
    
    if mode in ["ui", "both"]:
        print("\n[2/2] Starting Streamlit UI in separate window...")
        try:
            ui_path = project_root / "ui"
            
            # Activate virtual environment and run Streamlit
            if platform.system() == "Windows":
                activate_cmd = f"& '{shared_env}\\Scripts\\Activate.ps1'"
                ui_command = f"{activate_cmd}; cd '{ui_path}'; streamlit run app.py --server.port 8501"
            else:
                activate_cmd = f"source {shared_env}/bin/activate"
                ui_command = f"{activate_cmd} && cd {ui_path} && streamlit run app.py --server.port 8501"
            
            ui_process = start_in_new_window(
                ui_command,
                "Credit Card Fraud Detection - Streamlit UI",
                project_root
            )
            processes.append(("Streamlit UI", ui_process))
            print("✅ Streamlit UI window opened")
            print("   URL: http://localhost:8501")
            
        except Exception as e:
            print(f"❌ Error starting UI: {e}")
            # Clean up API process if it was started
            for name, proc in processes:
                proc.terminate()
            return 1
    
    if mode not in ["api", "ui", "both"]:
        print("\n❌ Invalid mode specified!")
        print("\nUsage: python start.py [api|ui|both]")
        print("  api  - Start only the API server in a new window")
        print("  ui   - Start only the UI in a new window")
        print("  both - Start both API and UI in separate windows (default)")
        return 1
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ System Launched Successfully!")
    print("=" * 60)
    
    if mode in ["api", "both"]:
        print("\n📊 API Server:")
        print("   - Running in separate PowerShell window")
        print("   - API: http://localhost:8000")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Health: http://localhost:8000/health")
    
    if mode in ["ui", "both"]:
        print("\n🖥️  Streamlit UI:")
        print("   - Running in separate PowerShell window")
        print("   - Dashboard: http://localhost:8501")
    
    print("\n📝 Notes:")
    print("   - Each service runs in its own window")
    print("   - Close the windows to stop the services")
    print("   - Check window logs for any errors")
    print("   - Model loads automatically with API server")
    
    print("\n🛑 To stop the services:")
    print("   - Close each PowerShell window, or")
    print("   - Press Ctrl+C in each window")
    
    print("\n" + "=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
