# Debug Scripts for LLM Service

This directory contains scripts for debugging the LLM service component of the Credit Card Fraud Detection application.

## Available Scripts

### debug_llm_service_unified.py (Recommended)
A unified debug script that supports multiple debugging modes:

- **Normal mode**: Standard console output
- **Breakpoint mode**: Uses Python's PDB for step-by-step debugging
- **VS Code mode**: Uses debugpy for visual debugging in VS Code

#### Usage:
```powershell
# For normal debugging:
python debug_llm_service_unified.py --mode normal

# For breakpoint debugging:
python debug_llm_service_unified.py --mode breakpoint

# For VS Code debugging:
python debug_llm_service_unified.py --mode vscode
```

### Legacy Debug Scripts

The following scripts are kept for backward compatibility but are deprecated in favor of the unified script:

- `debug_llm_service.py` - Basic debugging with console output
- `debug_llm_service_breakpoints.py` - Debugging with PDB breakpoints
- `debug_llm_service_vscode.py` - Debugging with VS Code integration

## Setup for VS Code Debugging

1. Install the debugpy module:
```powershell
pip install debugpy
```

2. Run the script in VS Code mode:
```powershell
python debug_llm_service_unified.py --mode vscode
```

3. Attach to the running script in VS Code by:
   - Opening the debugging panel (Ctrl+Shift+D)
   - Selecting the "Python: Attach" configuration
   - Pressing F5 to attach to the running script

## Common Debugging Tasks

- Test basic query processing
- Test document processing
- Verify LLM model responses
- Debug vector database integration
