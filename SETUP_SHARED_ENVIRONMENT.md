# shared_Environment Setup Guide

This guide explains how to set up the **shared_Environment** virtual environment for all AILearning projects.

## Quick Setup (Recommended)

Run the setup script in PowerShell from the AILearning folder:

```powershell
cd D:\Study\AILearning
.\setup_shared_Environment.ps1
```

This will:
1. Install Python 3.13.2 (if not present) via winget
2. Create `shared_Environment` virtual environment
3. Install all required packages from `shared_Environment_requirements.txt`
4. Register the Jupyter kernel `shared_Environment`

## What's Included

### Projects & Dependencies Covered

| Project | Key Packages |
|---------|--------------|
| **creditcardfrauddetection** | FastAPI, Streamlit, LangChain, PyTorch, XGBoost, ChromaDB, Pinecone |
| **modelcontextprotocol** | MCP, yfinance, aiohttp |
| **StockPrediction** | pandas, scikit-learn, yfinance |
| **StockPredictionModels** | ta, plotly, matplotlib, seaborn |
| **venAIAgent** | phidata (phi), yfinance |
| **aiModelDev** | transformers, torch |
| **Instruction.txt** | numpy, pandas, scikit-learn, JupyterLab |

### Python & Core Tools

- **Python**: 3.13.2
- **Jupyter**: JupyterLab, Notebook, ipykernel
- **Data**: numpy, pandas, scipy, matplotlib, seaborn, plotly

### Optional Software (Install Manually)

| Software | Purpose | Install Link |
|----------|---------|--------------|
| **Ollama** | Local LLM (creditcardfrauddetection) | https://ollama.ai |
| **Docker** | MCP server containers | https://docs.docker.com/get-docker/ |
| **TA-Lib C Library** | Technical analysis (StockPredictionModels) | See below |

### TA-Lib Installation (Optional)

The `ta` package (pure Python) is already installed. For `TA-Lib` (C library wrapper):

1. Download: [ta-lib-0.6.4-windows-x86_64.msi](https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-windows-x86_64.msi)
2. Run the installer
3. Then: `.\shared_Environment\Scripts\pip.exe install TA-Lib`

## Manual Setup

If you prefer to set up manually:

```powershell
# 1. Create venv
python -m venv shared_Environment

# 2. Activate
.\shared_Environment\Scripts\Activate.ps1

# 3. Install packages
pip install -r shared_Environment_requirements.txt

# 4. Register Jupyter kernel
python -m ipykernel install --user --name=shared_Environment --display-name "shared_Environment"
```

## Usage

### Activate Environment

```powershell
cd D:\Study\AILearning
.\shared_Environment\Scripts\Activate.ps1
```

### Use in Cursor/VS Code

1. Press `Ctrl+Shift+P`
2. Run "Python: Select Interpreter"
3. Choose `D:\Study\AILearning\shared_Environment\Scripts\python.exe`

### Run Projects

- **Credit Card Fraud UI**: `shared_Environment\Scripts\streamlit.exe run MLProjects\creditcardfrauddetection\ui\app.py`
- **MCP Stock Server**: See `MLProjects\modelcontextprotocol\python\`
- **Jupyter**: `shared_Environment\Scripts\jupyter.exe notebook` or `jupyter lab`

## Files

| File | Description |
|------|-------------|
| `setup_shared_Environment.ps1` | Main setup script |
| `shared_Environment_requirements.txt` | Consolidated pip requirements |
| `SETUP_SHARED_ENVIRONMENT.md` | This guide |
