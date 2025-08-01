# MCP Stock Server

## Overview
A Model Context Protocol (MCP) stock server that provides real-time stock data through VS Code integration. This is part of a larger MCP ecosystem with multiple specialized servers for different data sources and functionalities.

## Project Structure

### 📁 Complete Directory Layout
```
d:\Study\AILearning\MLProjects\modelcontextprotocol\
├── python\                              # Python MCP Implementations
│   ├── mcp_stock_server.py             # 🎯 Custom Stock Data Server
│   ├── test_stock_client.py            # 🧪 Interactive Testing Tool
│   ├── final_verification.py          # ✅ Automated Verification
│   ├── README.md                       # 📖 This Documentation
│   └── logs\                           # 📝 Runtime Logs
│       └── mcp_stock_server.log        # Server Activity Log
└── c#\                                 # C# MCP Implementations (Future)
```

### 📋 File Descriptions
| File | Purpose | Usage |
|------|---------|-------|
| `mcp_stock_server.py` | Main MCP server providing 3 stock analysis tools | Production server |
| `test_stock_client.py` | Interactive menu-driven testing interface | Development/Testing |
| `final_verification.py` | Automated test suite for all server functions | CI/CD Validation |
| `logs/mcp_stock_server.log` | Runtime activity, errors, and performance metrics | Monitoring/Debug |

## MCP Server Ecosystem

This project is part of a comprehensive MCP server ecosystem configured in VS Code. Currently deployed servers:

### 🕒 Time Server (`mcp_server_time`)
- **Server ID**: `time`
- **Type**: Pre-built MCP module
- **Location**: `shared_Environment` Python installation
- **Capabilities**:
  - Current time queries with timezone support
  - Time zone conversions
  - Date/time calculations
- **Configuration**: Uses America/Los_Angeles as local timezone
- **Example Queries**: 
  - "What time is it in Tokyo?"
  - "Convert 3 PM EST to PST"

### 📈 Stock Server (`mcp_stock_server`)
- **Server ID**: `stock` 
- **Type**: Custom implementation (this project)
- **Location**: `MLProjects/modelcontextprotocol/python/`
- **Data Source**: Yahoo Finance (yfinance library)
- **Capabilities**:
  - Real-time stock price data
  - Company financial information
  - Historical price analysis
- **Example Queries**:
  - "What's Apple's current stock price?"
  - "Show me Microsoft's financial metrics"
  - "Get Tesla's stock history for the past month"

## Features
### Stock Analysis Tools:

#### 🔍 **get_stock_price**
- **Purpose**: Real-time stock price and basic metrics
- **Input**: Stock symbol (AAPL, GOOG, MSFT, etc.)
- **Output**: 
  - Current price and daily change
  - Volume and market capitalization
  - Previous close and percentage change
  - Currency and last update timestamp

#### 📊 **get_stock_info** 
- **Purpose**: Comprehensive company analysis
- **Input**: Stock symbol
- **Output**:
  - Company sector and industry classification
  - Financial ratios (P/E, Price-to-Book, Beta)
  - Market metrics (52-week high/low, average volume)
  - Business summary and company website
  - Dividend yield and enterprise value

#### 📈 **get_stock_history**
- **Purpose**: Historical price trend analysis
- **Input**: Stock symbol + time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
- **Output**:
  - OHLCV data (Open, High, Low, Close, Volume)
  - Summary statistics (highest/lowest prices, average volume)
  - Date range coverage
  - Data point count

## VS Code MCP Configuration

### Complete MCP Server Setup
Located in VS Code settings (`%APPDATA%\Code\User\settings.json`):

```json
{
  "mcp": {
    "inputs": [],
    "servers": {
      "time": {
        "command": "D:/Study/AILearning/shared_Environment/Scripts/python.exe",
        "args": ["-m", "mcp_server_time", "--local-timezone", "America/Los_Angeles"],
        "env": {
          "MCP_SERVER_NAME": "AILearning_TimeServer",
          "MCP_SERVER_SOURCE": "Local_Python_Environment"
        }
      },
      "stock": {
        "command": "D:/Study/AILearning/shared_Environment/Scripts/python.exe",
        "args": ["D:/Study/AILearning/MLProjects/modelcontextprotocol/python/mcp_stock_server.py"],  
        "env": {
          "MCP_SERVER_NAME": "AILearning_StockServer",
          "MCP_SERVER_SOURCE": "Custom_YFinance_Server"
        }
      }           
    }
  }
}
```

### Configuration Details

#### Time Server Configuration
- **Python Environment**: `shared_Environment` (shared across projects)
- **Module**: Built-in `mcp_server_time` package
- **Arguments**: `--local-timezone America/Los_Angeles`
- **Environment Variables**:
  - `MCP_SERVER_NAME`: "AILearning_TimeServer"
  - `MCP_SERVER_SOURCE`: "Local_Python_Environment"

#### Stock Server Configuration  
- **Python Environment**: `shared_Environment` (shared across projects)
- **Script**: Custom `mcp_stock_server.py` implementation
- **Dependencies**: `yfinance`, `mcp` libraries
- **Environment Variables**:
  - `MCP_SERVER_NAME`: "AILearning_StockServer" 
  - `MCP_SERVER_SOURCE`: "Custom_YFinance_Server"

## Usage & Testing

### 🚀 Production Usage
- **VS Code Integration**: Use with Claude Dev, Continue, or other MCP-compatible extensions
- **Natural Language Queries**: Ask questions like:
  - "What's the current price of Apple stock?"
  - "Show me Google's financial metrics"
  - "What time is it in London right now?"
  - "Get Amazon's stock history for the past year"

### 🧪 Development & Testing

#### Interactive Testing
```bash
python test_stock_client.py
```
**Features**:
- Menu-driven interface for testing each tool
- Manual stock symbol input
- Real-time response display
- Error handling validation

#### Automated Testing  
```bash
python final_verification.py
```
**Features**:
- Tests all three stock tools automatically
- Uses MSFT as test symbol
- Validates JSON response format
- Performance timing metrics

### 📊 Monitoring & Logs
- **Log Location**: `logs/mcp_stock_server.log`
- **Log Contents**: 
  - Tool execution requests and responses
  - Error messages and stack traces  
  - Performance metrics and timing
  - API call success/failure rates

## Technical Architecture

### 🏗️ System Integration
```
VS Code Editor
    ↓ (MCP Protocol)
Claude Dev / Continue Extension  
    ↓ (JSON-RPC)
MCP Server (Python)
    ↓ (API Calls)
Yahoo Finance / System Time
```

### 🔧 Dependencies & Environment
```
Python 3.8+ Environment: shared_Environment/
├── mcp library (Model Context Protocol core)
├── yfinance (Yahoo Finance API wrapper)  
├── asyncio (Async I/O operations)
├── json (Response serialization)
└── logging (Activity monitoring)
```

## Dependencies & Requirements

### 🐍 Python Environment
- **Version**: Python 3.8+
- **Environment**: `shared_Environment` (shared across AI projects)
- **Location**: `D:/Study/AILearning/shared_Environment/`

### 📦 Required Packages
| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | Latest | Model Context Protocol core library |
| `yfinance` | Latest | Yahoo Finance API wrapper for stock data |
| `asyncio` | Built-in | Asynchronous I/O operations |
| `json` | Built-in | JSON serialization/deserialization |
| `logging` | Built-in | Activity logging and monitoring |

### 🔗 ModelContextProtocol Project Structure
```
d:\Study\AILearning\MLProjects\modelcontextprotocol\
├── python\                              # Python MCP Implementations
│   ├── mcp_stock_server.py             # Custom Stock Data Server
│   ├── test_stock_client.py            # Interactive Testing Tool
│   ├── final_verification.py          # Automated Verification
│   ├── README.md                       # Project Documentation
│   └── logs\                           # Runtime Logs
│       └── mcp_stock_server.log        # Server Activity Log
└── c#\                                 # C# MCP Implementations (Future)
```

**Status**: Production Ready ✅

---
*Part of the AILearning Model Context Protocol ecosystem - providing intelligent data access for AI applications*
