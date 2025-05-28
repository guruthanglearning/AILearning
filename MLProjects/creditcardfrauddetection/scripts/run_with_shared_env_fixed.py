import os
import subprocess
import sys

def main():
    # Path to shared environment's python executable
    shared_env_python = r"d:\Study\AILearning\shared_Environment\Scripts\python.exe"
    
    # Path to verification script (using the fixed one)
    verify_script = r"d:\Study\AILearning\MLProjects\creditcardfrauddetection\scripts\verify_env_fixed.py"
    
    print(f"Using Python: {shared_env_python}")
    print(f"Running script: {verify_script}")
    
    if not os.path.exists(shared_env_python):
        print(f"ERROR: Python executable not found: {shared_env_python}")
        return 1
        
    if not os.path.exists(verify_script):
        print(f"ERROR: Verification script not found: {verify_script}")
        return 1
    
    # Run the verification script using the shared environment's Python
    try:
        print("Executing verification script...")
        result = subprocess.run([shared_env_python, verify_script], 
                               capture_output=True, 
                               text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"Script exited with code: {result.returncode}")
            print("Error output:")
            print(result.stderr)
            
        return result.returncode
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
