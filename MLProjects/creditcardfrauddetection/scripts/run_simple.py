import subprocess
import sys

def main():
    # Path to shared environment's python executable
    shared_env_python = r"d:\Study\AILearning\shared_Environment\Scripts\python.exe"
    
    # Path to verification script
    verify_script = r"d:\Study\AILearning\MLProjects\creditcardfrauddetection\scripts\verify_simple.py"
    
    print(f"Using Python: {shared_env_python}")
    print(f"Running script: {verify_script}")
    
    # Run the verification script using the shared environment's Python
    try:
        result = subprocess.run([shared_env_python, verify_script], 
                               capture_output=True, 
                               text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"Script exited with code: {result.returncode}")
            if result.stderr:
                print("Error output:")
                print(result.stderr)
            
        return result.returncode
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
