#!/usr/bin/env python
"""
Check if all the required dependencies for both the API and UI are installed in the shared environment.
"""

import sys
import subprocess
import importlib
from pathlib import Path
import pkg_resources

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def check_requirements_file(requirements_path):
    """Check if all packages in a requirements file are installed."""
    print(f"\nChecking requirements file: {requirements_path}")
    print("="*80)
    
    missing_packages = []
    installed_wrong_version = []
    
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines, comments, and lines starting with specific characters
            if not line or line.startswith(('#', '/', '-')):
                continue
                
            # Split the line to handle comments after package specification
            parts = line.split('#')[0].strip()
            
            # Handle extras and version constraints
            if '>=' in parts:
                package, version = parts.split('>=', 1)
                version = version.strip()
                package = package.strip()
                
                try:
                    installed_version = pkg_resources.get_distribution(package).version
                    print(f"✓ {package} (installed: {installed_version}, required: >={version})")
                    
                    if pkg_resources.parse_version(installed_version) < pkg_resources.parse_version(version):
                        print(f"  ⚠ Warning: Installed version {installed_version} is older than required {version}")
                        installed_wrong_version.append((package, installed_version, version))
                        
                except pkg_resources.DistributionNotFound:
                    print(f"✖ {package} is missing (required: >={version})")
                    missing_packages.append((package, version))
                    
            elif '==' in parts:
                package, version = parts.split('==', 1)
                version = version.strip()
                package = package.strip()
                
                try:
                    installed_version = pkg_resources.get_distribution(package).version
                    print(f"✓ {package} (installed: {installed_version}, required: =={version})")
                    
                    if installed_version != version:
                        print(f"  ⚠ Warning: Installed version {installed_version} differs from required {version}")
                        installed_wrong_version.append((package, installed_version, version))
                        
                except pkg_resources.DistributionNotFound:
                    print(f"✖ {package} is missing (required: =={version})")
                    missing_packages.append((package, version))
                    
            else:
                # No version specified
                package = parts.strip()
                
                try:
                    installed_version = pkg_resources.get_distribution(package).version
                    print(f"✓ {package} (installed: {installed_version})")
                except pkg_resources.DistributionNotFound:
                    print(f"✖ {package} is missing")
                    missing_packages.append((package, "any"))
    
    return missing_packages, installed_wrong_version

def main():
    print("Credit Card Fraud Detection System - Environment Check")
    print("="*80)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Check main requirements file
    main_requirements = PROJECT_ROOT / "requirements.txt"
    missing, wrong_version = check_requirements_file(main_requirements)
    
    # Check if there are any issues
    if missing or wrong_version:
        print("\nSummary of Issues:")
        print("="*80)
        
        if missing:
            print("\nMissing packages:")
            for package, version in missing:
                if version == "any":
                    print(f"  - {package}")
                else:
                    print(f"  - {package}>={version}")
        
        if wrong_version:
            print("\nPackages with incorrect versions:")
            for package, installed, required in wrong_version:
                print(f"  - {package} (installed: {installed}, required: {required})")
        
        print("\nTo install missing packages, run:")
        print(f"  {sys.executable} -m pip install -r {main_requirements}")
        
        print("\nEnvironment check completed with issues.")
        return 1
    else:
        print("\n✅ All required packages are installed with correct versions.")
        print("Environment check completed successfully.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
