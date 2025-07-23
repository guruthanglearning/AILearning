# Utility Scripts

This directory contains utility scripts for the Credit Card Fraud Detection project.

## Available Scripts

### clean_workspace.py (Recommended)
A unified cleaning utility script that provides multiple cleaning functionalities:

1. Clean old log files (archive files older than a specified number of days)
2. Remove redundant files and backups
3. Clean cached files (__pycache__, .pyc)
4. List potential redundant files without removing them

#### Usage:
```powershell
# Clean all (logs, redundant files, cache files, and list potential redundancies)
python clean_workspace.py --mode all

# Clean only log files older than 30 days
python clean_workspace.py --mode logs --days 30

# Clean only redundant files
python clean_workspace.py --mode files

# Clean only cache files
python clean_workspace.py --mode cache

# List potential redundant files without cleaning
python clean_workspace.py --mode list

# Perform a dry run (show what would be cleaned without taking action)
python clean_workspace.py --dry-run

# Create backups before cleaning
python clean_workspace.py --backup
```

### clean_logs.py
A specialized utility for managing log files.

#### Usage:
```powershell
python clean_logs.py --days 30  # Archive logs older than 30 days
```

### run_tests.py
Runs the test suite for the project.

### diagnose_system.py
Runs diagnostics on the system to check for proper configuration.

### configure_ollama_api.py
Configures the Ollama API integration.

### fix_api_client.py
Fixes issues with the API client configuration.

## Archive

The `archive` directory contains older utility scripts that have been replaced by newer, more efficient versions:

- clean_files.py - Replaced by clean_workspace.py
- clean_files.bat - Windows batch script version of clean_files.py
- list_redundant_files.py - Functionality now included in clean_workspace.py
