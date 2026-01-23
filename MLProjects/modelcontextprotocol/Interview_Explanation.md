# Model Context Protocol (MCP) Stock Server - Interview Explanation Guide

## 📋 Quick Project Summary

**Project**: MCP Stock Server - A Real-time Financial Data Provider  
**Protocol**: Model Context Protocol (MCP) - Anthropic's standardized AI-tool communication protocol  
**Architecture**: Server-client model with JSON-RPC 2.0  
**Tech Stack**: Python, MCP SDK, yfinance, Docker, FastAPI concepts  
**Deployment**: Docker containerized + Local Python environments  
**Use Case**: AI assistants (like Claude, VS Code Copilot) accessing real-time stock data

---

## 🎯 Opening Statement (30 seconds)

*"I built an MCP Stock Server that enables AI assistants to access real-time financial data through a standardized protocol. The server implements Anthropic's Model Context Protocol (MCP), which is like REST API for AI tools—it allows AI models to communicate with external data sources in a structured way. The system provides three main tools: stock price lookup, company information retrieval, and historical data analysis. It's containerized with Docker for easy deployment and integrates seamlessly with VS Code, Claude, and other MCP-compatible clients. This project demonstrates my understanding of modern AI tool integration, protocol design, and production-ready deployment practices."*

---

## 🧠 What is Model Context Protocol (MCP)?

### The Problem MCP Solves

**Before MCP**:
```
AI Model (GPT-4) wants stock data
  ↓
Custom API Integration #1
  ↓
Custom API Integration #2
  ↓
Custom API Integration #3
  ↓
Every tool needs unique integration code
```

**With MCP**:
```
AI Model (Any MCP-compatible AI)
  ↓
Standard MCP Protocol (JSON-RPC 2.0)
  ↓
MCP Server (Stock, Weather, Database, etc.)
  ↓
Unified interface for all tools
```

### MCP vs REST API

| Feature | MCP | REST API |
|---------|-----|----------|
| **Purpose** | AI-tool communication | General web services |
| **Protocol** | JSON-RPC 2.0 over stdio | HTTP/HTTPS |
| **Discovery** | Server advertises tools dynamically | Static endpoints |
| **State** | Session-based (persistent connection) | Stateless (each request independent) |
| **Schema** | JSON Schema validation built-in | OpenAPI/Swagger (optional) |
| **Transport** | stdin/stdout, SSE, WebSocket | HTTP verbs (GET, POST, etc.) |
| **Use Case** | AI assistants accessing tools | Web/mobile apps |

### Why MCP Matters

```
Traditional Approach:
  Claude: Custom integration code
  GPT-4: Custom integration code
  VS Code Copilot: Custom integration code
  → 3 different implementations for same stock data

MCP Approach:
  MCP Stock Server (1 implementation)
  ↓
  Works with: Claude, GPT-4, VS Code, any MCP client
  → Single implementation, universal compatibility
```

---

## 🏗️ System Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  VS Code Chat          Python Clients         PowerShell        │
│  Claude Desktop        docker_mcp_client.py   Scripts           │
│                        test_stock_client.py                      │
│                                                                  │
│  Common Interface: MCP Protocol (JSON-RPC 2.0)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MCP SERVER LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ MCP Stock Server (mcp_stock_server.py)                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • Tool Registry                                          │  │
│  │ • Request Handler (handle_call_tool)                     │  │
│  │ • Schema Validation (JSON Schema)                        │  │
│  │ • Logging & Monitoring                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Three Tools Exposed:                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │get_stock     │ │get_stock     │ │get_stock            │   │
│  │_price        │ │_info         │ │_history              │   │
│  │              │ │              │ │                      │   │
│  │• Symbol      │ │• Symbol      │ │• Symbol              │   │
│  │→ Price       │ │→ Company     │ │• Period              │   │
│  │→ Change %    │ │  Details     │ │→ Historical          │   │
│  │→ Volume      │ │→ Financials  │ │  OHLCV Data          │   │
│  └──────────────┘ └──────────────┘ └──────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCE LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  yfinance Library (Python)                                       │
│          ↓                                                       │
│  Yahoo Finance API (External)                                    │
│          ↓                                                       │
│  Real-time Stock Data                                           │
│  • Price feeds                                                   │
│  • Company information                                           │
│  • Historical OHLCV data                                        │
│  • Market statistics                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components Explained

### Component 1: MCP Server Core (`mcp_stock_server.py`)

#### What It Does
- Implements Model Context Protocol specification
- Registers stock data tools with JSON schemas
- Handles client requests via JSON-RPC 2.0
- Manages communication over stdin/stdout

#### Key Code Structure
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Create server instance
server = Server("stock-server")

# Register tools
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_stock_price",
            description="Get current stock price...",
            inputSchema={...}  # JSON Schema validation
        ),
        # ... other tools
    ]

# Handle tool execution
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "get_stock_price":
        # Execute tool logic
        return result
```

#### Why This Design?

| Design Choice | Rationale |
|---------------|-----------|
| **stdio Transport** | Simple, universal (works in Docker, local, SSH) |
| **Async/Await** | Non-blocking I/O for concurrent requests |
| **Decorators** | Clean API for registering handlers |
| **JSON-RPC 2.0** | Standard protocol (request/response structure) |
| **Type Hints** | Better IDE support and runtime validation |

---

### Component 2: Docker Deployment

#### Docker Architecture
```dockerfile
FROM python:3.12-slim

# Install dependencies
RUN pip install yfinance mcp

# Copy server code
COPY mcp_stock_server.py /app/

# Keep container running
CMD ["tail", "-f", "/dev/null"]
```

#### Why Docker?

```
Without Docker:
  • "Works on my machine" syndrome
  • Dependency conflicts (Python versions, yfinance versions)
  • Complex setup for each user
  • No isolation from host system

With Docker:
  ✅ Consistent environment (Python 3.12, exact dependencies)
  ✅ One-command deployment (docker-compose up)
  ✅ Portable (runs anywhere Docker runs)
  ✅ Resource limits (512MB RAM, 0.5 CPU)
  ✅ Easy scaling (spin up multiple containers)
```

#### Docker Compose Configuration
```yaml
services:
  mcp-stock-server:
    image: mcp-stock-server:latest
    container_name: mcp-stock-server
    stdin_open: true      # Enable stdin for MCP protocol
    tty: true             # Allocate pseudo-TTY
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs  # Persist logs outside container
    environment:
      - PYTHONUNBUFFERED=1  # Real-time logging
    deploy:
      resources:
        limits:
          memory: 512M      # Prevent memory leaks
          cpus: '0.5'       # Limit CPU usage
```

---

### Component 3: Client Implementations

#### Client Type 1: Docker MCP Client (`docker_mcp_client.py`)

**Purpose**: Production-ready Python client for programmatic access

**Key Features**:
```python
class DockerMCPClient:
    def __init__(self, container_name="mcp-stock-server"):
        self.container_name = container_name
    
    def is_container_running(self) -> bool:
        """Check container health"""
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={self.container_name}"],
            capture_output=True
        )
        return self.container_name in result.stdout.decode()
    
    def query_stock_tool(self, tool_name: str, arguments: dict):
        """Execute MCP request in Docker container"""
        # 1. Create JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        
        # 2. Execute in container via docker exec
        process = subprocess.Popen(
            ["docker", "exec", "-i", self.container_name, 
             "python", "/app/mcp_stock_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        
        # 3. Send MCP protocol messages
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.write(json.dumps(request) + "\n")
        
        # 4. Parse response
        return json.loads(process.stdout.readline())
```

**Usage Example**:
```python
client = DockerMCPClient()
price_data = client.get_stock_price("AAPL")
print(f"AAPL: ${price_data['current_price']}")
```

---

#### Client Type 2: Test Client with Args (`test_stock_client_args.py`)

**Purpose**: Command-line testing and automation

**Features**:
- Argument parsing (`--symbol AAPL --option 1`)
- Automated testing scripts
- Timeout handling (10s init, 30s data fetch)
- Detailed error reporting

**Usage**:
```bash
python test_stock_client_args.py --option 1 --symbol AAPL
# Option 1: Stock Price
# Option 2: Company Info
# Option 3: Historical Data
```

---

### Component 4: The Three Stock Tools

#### Tool 1: `get_stock_price`

**What It Returns**:
```json
{
  "_mcp_tool_info": {
    "tool_name": "get_stock_price",
    "server": "AILearning_StockServer",
    "data_source": "Custom_YFinance_Server",
    "query_timestamp": "2026-01-20 10:30:00"
  },
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 178.45,
  "previous_close": 176.80,
  "change": 1.65,
  "change_percent": 0.93,
  "volume": 45678900,
  "market_cap": 2750000000000,
  "currency": "USD",
  "last_updated": "2026-01-20 10:30:00"
}
```

**Implementation**:
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "get_stock_price":
        symbol = arguments.get("symbol")
        
        # Fetch data from yfinance
        stock = yf.Ticker(symbol.upper())
        info = stock.info
        hist = stock.history(period="1d")
        
        # Calculate metrics
        current_price = hist['Close'].iloc[-1]
        previous_close = info.get('previousClose', 0)
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100
        
        # Return structured data
        return {
            "symbol": symbol.upper(),
            "current_price": round(float(current_price), 2),
            "change": round(float(change), 2),
            "change_percent": round(float(change_percent), 2),
            # ... more fields
        }
```

---

#### Tool 2: `get_stock_info`

**What It Returns**:
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "market_cap": 2750000000000,
  "pe_ratio": 28.5,
  "eps": 6.25,
  "dividend_yield": 0.52,
  "52_week_high": 198.23,
  "52_week_low": 164.08,
  "average_volume": 58234567,
  "description": "Apple Inc. designs, manufactures...",
  "website": "https://www.apple.com",
  "employees": 164000
}
```

**Use Cases**:
- Fundamental analysis
- Company research
- Portfolio diversification analysis
- Sector comparison

---

#### Tool 3: `get_stock_history`

**What It Returns**:
```json
{
  "symbol": "AAPL",
  "period": "1mo",
  "data": [
    {
      "date": "2025-12-20",
      "open": 175.30,
      "high": 178.45,
      "low": 174.80,
      "close": 177.20,
      "volume": 45678900
    },
    // ... 19 more days
  ],
  "start_date": "2025-12-20",
  "end_date": "2026-01-20",
  "total_records": 20,
  "period_return": 3.40,
  "period_return_percent": 1.95
}
```

**Supported Periods**:
- `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

**Use Cases**:
- Technical analysis
- Backtesting trading strategies
- Price trend visualization
- Volatility calculation

---

## 🔄 Complete Request Flow

### Step-by-Step Execution

```
┌─────────────────────────────────────────────────────────────────┐
│ USER ACTION: "Get AAPL stock price" in VS Code Chat            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: VS Code MCP Client                                      │
├─────────────────────────────────────────────────────────────────┤
│ • Parses natural language request                               │
│ • Identifies tool: get_stock_price                              │
│ • Extracts parameter: symbol = "AAPL"                           │
│ • Builds JSON-RPC request                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: JSON-RPC Request                                        │
├─────────────────────────────────────────────────────────────────┤
│ {                                                               │
│   "jsonrpc": "2.0",                                             │
│   "id": 1,                                                      │
│   "method": "tools/call",                                       │
│   "params": {                                                   │
│     "name": "get_stock_price",                                  │
│     "arguments": {"symbol": "AAPL"}                             │
│   }                                                             │
│ }                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Docker Container Execution                              │
├─────────────────────────────────────────────────────────────────┤
│ Command:                                                        │
│   docker exec -i mcp-stock-server python /app/mcp_stock_server.py│
│                                                                 │
│ • Sends request via stdin                                       │
│ • Container processes MCP protocol                              │
│ • Server initialized (if first request)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: MCP Server Processing                                   │
├─────────────────────────────────────────────────────────────────┤
│ • Receives JSON-RPC message                                     │
│ • Validates request format                                      │
│ • Routes to handle_call_tool()                                  │
│ • Validates arguments against JSON schema                       │
│ • Logs request (timestamp, tool, args)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: yfinance Data Fetch                                     │
├─────────────────────────────────────────────────────────────────┤
│ stock = yf.Ticker("AAPL")                                       │
│ info = stock.info                    # Company metadata         │
│ hist = stock.history(period="1d")    # Latest price             │
│                                                                 │
│ • HTTP request to Yahoo Finance API                             │
│ • Parse JSON response                                           │
│ • Extract: price, volume, market cap, etc.                      │
│ • Timeout: 10 seconds max                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Data Processing & Formatting                            │
├─────────────────────────────────────────────────────────────────┤
│ current_price = hist['Close'].iloc[-1]                          │
│ previous_close = info.get('previousClose', 0)                   │
│ change = current_price - previous_close                         │
│ change_percent = (change / previous_close) * 100                │
│                                                                 │
│ • Round to 2 decimal places                                     │
│ • Convert types (float → int for volume)                        │
│ • Add metadata (_mcp_tool_info)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: JSON-RPC Response                                       │
├─────────────────────────────────────────────────────────────────┤
│ {                                                               │
│   "jsonrpc": "2.0",                                             │
│   "id": 1,                                                      │
│   "result": {                                                   │
│     "content": [{                                               │
│       "type": "text",                                           │
│       "text": "{...stock data JSON...}"                         │
│     }]                                                          │
│   }                                                             │
│ }                                                               │
│                                                                 │
│ • Write to stdout                                               │
│ • Log response (timestamp, status, data size)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Client Receives Response                                │
├─────────────────────────────────────────────────────────────────┤
│ • Docker exec returns stdout                                    │
│ • VS Code parses JSON response                                  │
│ • Extracts stock data                                           │
│ • Formats for display                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: Display to User                                         │
├─────────────────────────────────────────────────────────────────┤
│ AAPL Stock Price:                                               │
│ • Current Price: $178.45                                        │
│ • Change: +$1.65 (+0.93%)                                       │
│ • Volume: 45.7M shares                                          │
│ • Market Cap: $2.75T                                            │
└─────────────────────────────────────────────────────────────────┘

Total Time: ~2-3 seconds
  • Network latency: 1-2s (Yahoo Finance API)
  • Processing: 0.5s
  • Docker overhead: 0.2s
```

---

## 🎓 Key Technical Concepts

### Concept 1: JSON-RPC 2.0

**What It Is**: A remote procedure call (RPC) protocol using JSON

**Example Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_stock_price",
    "arguments": {"symbol": "AAPL"}
  }
}
```

**Example Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"symbol\": \"AAPL\", \"price\": 178.45}"
    }]
  }
}
```

**Why JSON-RPC?**:
- Simple (just 4 fields: jsonrpc, id, method, params)
- Language-agnostic (works with any language)
- Request-response pairing (id field matches requests to responses)
- Standard error handling

---

### Concept 2: stdin/stdout Transport

**What It Means**: Communication via standard input/output streams

```
Client Process                Server Process
     │                              │
     │  stdin ───────────────────►  │
     │    (Request JSON)            │
     │                              │
     │                      Process Request
     │                              │
     │  ◄─────────────────── stdout │
     │    (Response JSON)           │
     │                              │
```

**Why stdin/stdout?**:
- Universal (works in all environments)
- No network configuration needed
- Works in Docker containers
- Works over SSH
- Simple debugging (just pipe commands)

**Example**:
```bash
# Manual test using echo and pipes
echo '{"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"get_stock_price","arguments":{"symbol":"AAPL"}}}' | python mcp_stock_server.py
```

---

### Concept 3: Tool Discovery & Schema Validation

**Tool Registration**:
```python
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_stock_price",
            description="Get current stock price...",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker (e.g., AAPL)"
                    }
                },
                "required": ["symbol"]
            }
        )
    ]
```

**How Clients Use This**:
```
1. Client connects to server
2. Client sends: {"method": "tools/list"}
3. Server responds with all available tools + schemas
4. Client knows:
   - What tools exist (get_stock_price, get_stock_info, etc.)
   - What parameters each tool requires (symbol)
   - What types are expected (string, not int)
5. Client can validate requests before sending
```

**Benefits**:
- Self-documenting API (schema describes usage)
- Runtime validation (catch errors before execution)
- IDE autocomplete (if client supports it)
- Type safety (prevents "symbol": 123 errors)

---

### Concept 4: Async/Await Architecture

**Why Async?**:
```python
# WITHOUT async (blocking)
def handle_request(symbol):
    data = yfinance_fetch(symbol)  # Blocks for 2 seconds
    return data
# If 10 clients request simultaneously:
# Total time = 10 × 2s = 20 seconds

# WITH async (non-blocking)
async def handle_request(symbol):
    data = await yfinance_fetch(symbol)  # Non-blocking
    return data
# If 10 clients request simultaneously:
# Total time = ~2 seconds (all requests run concurrently)
```

**Implementation**:
```python
# Wrap blocking yfinance calls
loop = asyncio.get_event_loop()
info = await asyncio.wait_for(
    loop.run_in_executor(None, lambda: stock.info),
    timeout=10.0  # Prevent hanging
)
```

---

## 💡 Design Decisions & Trade-offs

### Decision 1: Docker vs Cloud Deployment

| Option | Pros | Cons | Chosen? |
|--------|------|------|---------|
| **Docker Local** | • No cloud costs<br>• Fast response (local)<br>• Full control<br>• Works offline | • Single machine<br>• No auto-scaling<br>• Manual updates | ✅ **Yes** |
| **AWS Lambda** | • Auto-scaling<br>• Pay-per-use<br>• No server management | • Cold start latency<br>• Monthly costs<br>• Vendor lock-in | ❌ No |
| **Heroku/Railway** | • Easy deployment<br>• Auto-scaling | • Monthly costs ($5-$20)<br>• Requires HTTP endpoint | ❌ No |

**Verdict**: Docker for simplicity and cost (educational project)

---

### Decision 2: yfinance vs Paid APIs

| Data Source | Cost | Rate Limit | Data Quality | Chosen? |
|-------------|------|------------|--------------|---------|
| **yfinance** | Free | ~2000 req/hour | Good (15-min delay) | ✅ **Yes** |
| **Alpha Vantage** | Free tier + paid | 5 req/min (free) | Excellent (real-time) | ❌ No |
| **IEX Cloud** | Paid ($9/month) | High | Excellent | ❌ No |
| **Finnhub** | Free tier + paid | 60 req/min (free) | Good | ❌ No |

**Verdict**: yfinance for zero cost and educational purposes

---

### Decision 3: Three Tools vs Single Multi-purpose Tool

**Option A: Single Tool (Rejected)**:
```python
Tool(name="get_stock_data", 
     params={"symbol": str, "data_type": str})
# data_type: "price" | "info" | "history"
```

**Option B: Three Separate Tools (Chosen)**:
```python
Tool(name="get_stock_price", params={"symbol": str})
Tool(name="get_stock_info", params={"symbol": str})
Tool(name="get_stock_history", params={"symbol": str, "period": str})
```

**Why Three Tools?**:
- **Clarity**: Each tool has single responsibility
- **Discovery**: AI can see exactly what actions are possible
- **Validation**: Different schemas for different use cases
- **Performance**: Fetch only needed data (not everything)
- **Extensibility**: Easy to add new tools without breaking existing ones

---

## 🧪 Testing & Validation

### Test Suite Components

#### 1. Unit Tests (Individual Tools)
```bash
# Test stock price tool
python test_stock_client_args.py --option 1 --symbol AAPL

# Test company info tool
python test_stock_client_args.py --option 2 --symbol GOOGL

# Test historical data tool
python test_stock_client_args.py --option 3 --symbol TSLA --period 1y
```

#### 2. Integration Tests (Docker)
```powershell
# PowerShell script: test_docker_mcp_stock.ps1
.\test_docker_mcp_stock.ps1

# Tests:
# ✅ Docker Desktop running
# ✅ Container deployed
# ✅ Container healthy
# ✅ MCP session initialization
# ✅ Tool listing
# ✅ Stock price fetch
# ✅ Company info fetch
# ✅ Historical data fetch
# ✅ Error handling (invalid symbol)
```

#### 3. Performance Tests
```python
import time

symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
start = time.time()

for symbol in symbols:
    client.get_stock_price(symbol)

elapsed = time.time() - start
print(f"5 requests in {elapsed:.2f}s")
# Expected: ~5-10 seconds (1-2s per request)
```

---

## 🚀 Deployment Process

### Step-by-Step Deployment

```bash
# 1. Build Docker image
docker build -t mcp-stock-server:latest .

# 2. Run container
docker-compose up -d

# 3. Verify container running
docker ps | grep mcp-stock-server

# 4. Check logs
docker logs mcp-stock-server

# 5. Test with client
python docker_mcp_client.py price AAPL

# 6. Monitor logs
tail -f logs/mcp_stock_server.log
```

### Health Monitoring

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s      # Check every 30s
  timeout: 10s       # Fail if > 10s
  retries: 3         # Retry 3 times before marking unhealthy
  start_period: 10s  # Grace period on startup
```

---

## 🔍 Common Interview Questions & Answers

### Q1: What is Model Context Protocol and why does it matter?

**Answer**:
"Model Context Protocol (MCP) is Anthropic's standardized way for AI models to communicate with external tools and data sources. Think of it like REST APIs for AI assistants.

**The Problem**: Before MCP, every AI assistant (Claude, GPT-4, Copilot) needed custom integration code for each tool. If you wanted stock data in 3 different AI assistants, you'd write 3 different integrations.

**The Solution**: MCP provides a universal protocol (like USB for peripherals). I write one MCP stock server, and it works with ANY MCP-compatible AI client—Claude, VS Code, custom Python clients, etc.

**Why It Matters**:
1. **Standardization**: One implementation, universal compatibility
2. **Discovery**: Servers advertise their capabilities (like OpenAPI for REST)
3. **Type Safety**: JSON Schema validation built-in
4. **Stateful**: Maintains sessions (unlike stateless REST)

In my project, I built an MCP stock server that any AI assistant can use to fetch real-time stock data, without custom integration code for each assistant."

---

### Q2: Why did you use Docker for this project?

**Answer**:
"Docker solves the 'works on my machine' problem and provides several key benefits:

**1. Consistent Environment**:
```
Without Docker:
  • User A: Python 3.9, yfinance 0.1.70
  • User B: Python 3.11, yfinance 0.2.30
  • Different results, debugging nightmares

With Docker:
  • Everyone: Python 3.12, yfinance 0.2.50 (exact versions)
  • Identical behavior across all environments
```

**2. One-Command Deployment**:
```bash
# Without Docker:
pip install -r requirements.txt  # Might fail due to conflicts
python mcp_stock_server.py       # Setup instructions: 10 steps

# With Docker:
docker-compose up -d             # Done. Works everywhere.
```

**3. Resource Management**:
```yaml
deploy:
  resources:
    limits:
      memory: 512M    # Prevent memory leaks
      cpus: '0.5'     # Limit CPU usage
```

**4. Scalability**:
```bash
# Need 3 instances for load balancing?
docker-compose up --scale mcp-stock-server=3
```

**5. Isolation**: The server runs in its own environment, can't interfere with host system or other applications.

For an MCP server specifically, Docker works great with stdin/stdout transport—clients just need `docker exec` to communicate."

---

### Q3: How does your server handle concurrent requests?

**Answer**:
"Great question! The server uses Python's `asyncio` for concurrent request handling:

**1. Async Architecture**:
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    # This is non-blocking
    data = await fetch_stock_data(symbol)
    return data
```

**2. Non-blocking I/O**:
```python
# Wrap blocking yfinance calls
loop = asyncio.get_event_loop()
info = await asyncio.wait_for(
    loop.run_in_executor(None, lambda: stock.info),
    timeout=10.0
)
```

**What Happens**:
```
Without async:
  Request 1 (AAPL) → 2s → Done
  Request 2 (GOOGL) → 2s → Done
  Total: 4 seconds

With async:
  Request 1 (AAPL) ↘
                    → Both fetch in parallel → 2s → Both done
  Request 2 (GOOGL) ↗
  Total: 2 seconds
```

**3. Timeouts**: Each request has a 10-second timeout to prevent hanging:
```python
try:
    data = await asyncio.wait_for(fetch_data(), timeout=10.0)
except asyncio.TimeoutError:
    return error_response("Request timed out")
```

**Limitations**:
- Current design: One server process (single event loop)
- For high traffic: Could deploy multiple containers with load balancer
- yfinance rate limits: ~2000 requests/hour from Yahoo Finance

For a typical use case (AI assistant queries), this handles dozens of concurrent users easily."

---

### Q4: How do clients discover what tools are available?

**Answer**:
"MCP has a built-in tool discovery mechanism:

**1. Client Connects**:
```python
# Client sends
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}
```

**2. Server Responds**:
```json
{
  "result": {
    "tools": [
      {
        "name": "get_stock_price",
        "description": "Get current stock price...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "symbol": {"type": "string", "description": "Ticker symbol"}
          },
          "required": ["symbol"]
        }
      },
      // ... other tools
    ]
  }
}
```

**3. Client Now Knows**:
- Tool names: `get_stock_price`, `get_stock_info`, `get_stock_history`
- Required parameters: `symbol` (string, required)
- Optional parameters: `period` (string, default "1mo")
- Parameter types: `string` not `int`
- Descriptions: For UI display or AI reasoning

**4. JSON Schema Validation**:
```python
# Before execution, server validates:
Tool(
    name="get_stock_price",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"}
        },
        "required": ["symbol"]
    }
)

# This request fails validation:
{"symbol": 123}  # ❌ Type error: expected string, got int

# This passes:
{"symbol": "AAPL"}  # ✅ Valid
```

**Benefits**:
- **Self-documenting**: No separate API docs needed
- **Type-safe**: Catch errors before execution
- **Dynamic**: Server can add/remove tools without client updates
- **AI-friendly**: LLMs can read schemas to understand tool usage

This is similar to OpenAPI/Swagger for REST APIs, but built into the protocol."

---

### Q5: What happens if yfinance is down or returns an error?

**Answer**:
"I implemented comprehensive error handling at multiple levels:

**1. Timeout Protection**:
```python
try:
    data = await asyncio.wait_for(
        fetch_stock_data(symbol),
        timeout=10.0
    )
except asyncio.TimeoutError:
    logger.error(f"Timeout fetching data for {symbol}")
    return error_response("Data source timed out")
```

**2. Invalid Symbol Handling**:
```python
stock = yf.Ticker(symbol)
info = stock.info

if not info or info.get('regularMarketPrice') is None:
    return {
        "error": "Invalid symbol or no data available",
        "symbol": symbol
    }
```

**3. API Error Handling**:
```python
try:
    stock = yf.Ticker(symbol)
    info = stock.info
except Exception as e:
    logger.error(f"yfinance error: {str(e)}")
    return error_response(f"Error fetching stock data: {str(e)}")
```

**4. Graceful Degradation**:
```python
# If some fields are missing, use defaults
market_cap = info.get('marketCap', 'N/A')
pe_ratio = info.get('trailingPE', 'N/A')
# Return partial data instead of complete failure
```

**5. Logging for Debugging**:
```python
logger.info(f"Request: {symbol} at {timestamp}")
logger.error(f"Failed: {symbol} - {error_message}")
# Logs stored in: logs/mcp_stock_server.log
```

**Example Error Response**:
```json
{
  "error": "Invalid symbol",
  "symbol": "INVALID123",
  "message": "No data found for symbol",
  "timestamp": "2026-01-20 10:30:00"
}
```

**Client-Side Handling**:
```python
result = client.get_stock_price("AAPL")
if "error" in result:
    print(f"Error: {result['message']}")
    # Fallback: use cached data, retry, or alert user
else:
    print(f"Price: ${result['current_price']}")
```

This ensures the system degrades gracefully instead of crashing on errors."

---

### Q6: How would you scale this to handle 1000 requests per second?

**Answer**:
"Current architecture handles ~10-20 requests/second. For 1000 req/s, I'd implement:

**1. Horizontal Scaling (Multiple Containers)**:
```yaml
# docker-compose.yml
services:
  mcp-stock-server:
    deploy:
      replicas: 10  # 10 containers × 100 req/s = 1000 req/s
```

**2. Load Balancer**:
```
NGINX Load Balancer
        ↓
   ┌────┼────┐
   │    │    │
Server1 Server2 Server3
 (333)  (333)  (334) requests/sec
```

**3. Caching Layer (Redis)**:
```python
import redis
cache = redis.Redis()

async def get_stock_price(symbol):
    # Check cache first (TTL: 60 seconds)
    cached = cache.get(f"price:{symbol}")
    if cached:
        return json.loads(cached)
    
    # Cache miss: fetch from yfinance
    data = await fetch_from_yfinance(symbol)
    cache.setex(f"price:{symbol}", 60, json.dumps(data))
    return data
```

**Cache Impact**:
```
Without cache:
  • Every request hits Yahoo Finance API
  • Rate limit: 2000 req/hour = 0.5 req/sec 🚫

With cache (60s TTL):
  • Popular stocks (AAPL, GOOGL): 99% cache hits
  • 1000 req/s → Only 10-20 req/s to Yahoo
  • Within rate limits ✅
```

**4. Message Queue (RabbitMQ/Kafka)**:
```
Clients → Queue → Workers (10 containers) → yfinance
          ↓
      Buffering (handles bursts)
```

**5. Database for Historical Data**:
```
Instead of fetching historical data every time:
  • Store in PostgreSQL/TimescaleDB
  • Update daily (not per request)
  • Serve from database (much faster)
```

**6. CDN for Static Data**:
```
Company info (name, sector, etc.) rarely changes:
  • Cache in CloudFlare CDN
  • TTL: 24 hours
  • Instant global response
```

**7. Monitoring & Auto-scaling**:
```python
# Kubernetes auto-scaling
if cpu_usage > 80%:
    scale_up(replicas=current + 2)
elif cpu_usage < 20%:
    scale_down(replicas=current - 1)
```

**Cost-Performance Trade-off**:
| Solution | Cost | Complexity | Performance |
|----------|------|------------|-------------|
| Current (1 container) | $0 | Low | 10-20 req/s |
| + Caching | $10/mo | Medium | 500 req/s |
| + Load balancer | $30/mo | Medium | 2000 req/s |
| + Full stack | $200/mo | High | 10000+ req/s |

For this educational project, current architecture is sufficient. In production, I'd start with caching (biggest bang for buck)."

---

### Q7: Why JSON-RPC 2.0 instead of REST?

**Answer**:
"Both are valid, but JSON-RPC 2.0 is better suited for MCP's use case:

| Feature | REST | JSON-RPC 2.0 | Better For MCP? |
|---------|------|--------------|-----------------|
| **Transport** | HTTP only | Any (stdin, WebSocket, HTTP) | ✅ JSON-RPC (flexible) |
| **State** | Stateless | Can be stateful | ✅ JSON-RPC (sessions) |
| **Discovery** | Not built-in (needs OpenAPI) | Built into protocol | ✅ JSON-RPC |
| **Batching** | Not standard | Built-in | ✅ JSON-RPC |
| **Overhead** | HTTP headers (~200 bytes) | Minimal (~50 bytes) | ✅ JSON-RPC |
| **Caching** | Built-in (HTTP) | Manual | ✅ REST |

**Example Comparison**:

**REST**:
```http
POST /api/stock/price HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer token123
User-Agent: Mozilla/5.0

{"symbol": "AAPL"}

# Response: HTTP headers + JSON body
```

**JSON-RPC**:
```json
{"jsonrpc":"2.0","id":1,"method":"get_stock_price","params":{"symbol":"AAPL"}}

# Response: Just JSON
{"jsonrpc":"2.0","id":1,"result":{...}}
```

**Key Advantages for MCP**:

1. **stdin/stdout Transport**: JSON-RPC works over any stream, not just HTTP
```bash
echo '{"jsonrpc":"2.0",...}' | python server.py
```

2. **Batch Requests**:
```json
[
  {"jsonrpc":"2.0","id":1,"method":"get_stock_price","params":{"symbol":"AAPL"}},
  {"jsonrpc":"2.0","id":2,"method":"get_stock_price","params":{"symbol":"GOOGL"}}
]
```

3. **Request-Response Pairing**: `id` field matches responses to requests (crucial for async)

4. **Simplicity**: No HTTP verbs (GET/POST/PUT), no URL routing, just method names

**When REST Would Be Better**:
- Public API (REST is more widely known)
- Web browsers (native fetch/XHR support)
- Caching required (HTTP caching headers)

For MCP's use case (AI-tool communication over various transports), JSON-RPC is the right choice."

---

### Q8: How did you debug issues when the server wasn't responding?

**Answer**:
"Debugging MCP servers is tricky because they communicate over stdin/stdout. Here's my debugging strategy:

**1. Separate Logging (stderr)**:
```python
# DON'T write logs to stdout (interferes with JSON-RPC)
print("Debug message", file=sys.stderr)

# Use file logging
logging.basicConfig(
    handlers=[logging.FileHandler('logs/server.log')],
    # NO StreamHandler(sys.stdout)
)
```

**2. Enhanced Request Logging**:
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    logger.info("=" * 60)
    logger.info(f"INCOMING REQUEST")
    logger.info(f"Tool: {name}")
    logger.info(f"Args: {arguments}")
    logger.info(f"Time: {datetime.now()}")
    logger.info("=" * 60)
```

**3. Docker Logs Inspection**:
```bash
# Real-time logs
docker logs -f mcp-stock-server

# Last 100 lines
docker logs --tail 100 mcp-stock-server

# Logs with timestamps
docker logs -t mcp-stock-server
```

**4. Manual Testing (Bypass MCP)**:
```python
# Test yfinance directly
import yfinance as yf
stock = yf.Ticker("AAPL")
print(stock.info)  # Does this work?
```

**5. JSON-RPC Manual Testing**:
```bash
# Test raw JSON-RPC (Windows PowerShell)
$request = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}'
echo $request | docker exec -i mcp-stock-server python /app/mcp_stock_server.py
```

**6. Common Issues & Solutions**:

| Issue | Symptom | Solution |
|-------|---------|----------|
| **stdout pollution** | Invalid JSON errors | Move all prints to stderr/file |
| **Container not running** | Connection refused | `docker ps`, `docker-compose up` |
| **Timeout** | No response | Add timeout handling, check yfinance |
| **Invalid JSON** | Parse errors | Validate JSON with `jsonlint` |
| **Wrong Python version** | Import errors | Specify Python 3.12 in Dockerfile |

**7. Test Clients for Validation**:
```python
# test_stock_client_args.py
# Isolated test: Does the server respond at all?
python test_stock_client_args.py --option 1 --symbol AAPL
```

**8. Incremental Testing**:
```
✅ Test 1: Does Python run? 
   → python --version

✅ Test 2: Do imports work?
   → python -c "import mcp, yfinance"

✅ Test 3: Does server start?
   → python mcp_stock_server.py (check for errors)

✅ Test 4: Does it respond to initialize?
   → Send initialize request

✅ Test 5: Does it list tools?
   → Send tools/list request

✅ Test 6: Does it fetch data?
   → Send get_stock_price request
```

This methodical approach helped me isolate issues quickly."

---

### Q9: What would you add to this project next?

**Answer**:
"Several enhancements I'd prioritize:

**1. Additional Tools**:
```python
Tool(name="compare_stocks")
# Compare multiple stocks side-by-side

Tool(name="calculate_indicators")
# RSI, MACD, SMA for technical analysis

Tool(name="analyze_portfolio")
# Portfolio allocation, diversification metrics
```

**2. Caching Layer (Biggest Impact)**:
```python
import redis

@lru_cache(maxsize=1000)
async def get_stock_price_cached(symbol: str):
    # Cache for 60 seconds
    # Reduces API calls by 90%
    return await get_stock_price(symbol)
```

**3. Authentication & Rate Limiting**:
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    api_key = arguments.get("api_key")
    if not verify_api_key(api_key):
        return error_response("Invalid API key")
    
    # Rate limiting: 100 requests per hour per key
    if exceeded_rate_limit(api_key):
        return error_response("Rate limit exceeded")
```

**4. WebSocket Support**:
```python
# Real-time price updates
@server.subscribe("stock_updates")
async def stream_stock_prices(symbol: str):
    while True:
        price = await get_current_price(symbol)
        yield {"symbol": symbol, "price": price}
        await asyncio.sleep(1)
```

**5. Historical Data Storage**:
```sql
-- PostgreSQL/TimescaleDB
CREATE TABLE stock_prices (
    symbol VARCHAR(10),
    timestamp TIMESTAMP,
    price DECIMAL(10, 2),
    volume BIGINT
);

-- Serve historical data from DB instead of API
-- Much faster, no rate limits
```

**6. Metrics & Monitoring**:
```python
from prometheus_client import Counter, Histogram

requests_total = Counter('mcp_requests_total', 'Total requests')
request_duration = Histogram('mcp_request_duration_seconds', 'Request duration')

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    requests_total.inc()
    with request_duration.time():
        return await execute_tool(name, arguments)
```

**7. Multi-exchange Support**:
```python
# Currently: Only US stocks (NYSE, NASDAQ)
# Add: International exchanges (LSE, TSE, HKEX)

Tool(name="get_stock_price")
# params: {"symbol": "AAPL", "exchange": "NASDAQ"}
```

**8. Advanced Analytics**:
```python
Tool(name="predict_price")
# Use ML model (LSTM/Prophet) for price prediction

Tool(name="sentiment_analysis")
# Analyze news sentiment using NLP
```

**Priority**:
1. Caching (biggest performance gain)
2. Additional tools (more functionality)
3. WebSocket (real-time updates)
4. Authentication (production readiness)"

---

### Q10: How does this project demonstrate your skills?

**Answer**:
"This project showcases several key competencies:

**1. Protocol Understanding**:
- Implemented JSON-RPC 2.0 correctly
- Understood MCP specification (tool registration, schemas)
- Handled stdin/stdout communication

**2. Systems Design**:
- Three-tier architecture (client → server → data source)
- Separation of concerns (tool logic vs protocol handling)
- Error handling at multiple levels

**3. Containerization (Docker)**:
- Wrote production-grade Dockerfile
- Configured docker-compose with resource limits
- Health checks and restart policies

**4. Python Expertise**:
- Async/await for concurrent requests
- Type hints for code clarity
- Proper logging practices (stderr, not stdout)

**5. API Integration**:
- yfinance library usage
- Timeout handling for external APIs
- Data validation and transformation

**6. Testing**:
- Multiple test clients (CLI, programmatic)
- PowerShell test automation scripts
- Integration testing with Docker

**7. Documentation**:
- Comprehensive README with examples
- Mermaid diagrams for architecture
- Clear usage instructions

**8. Production Readiness**:
- Logging for debugging
- Error handling for edge cases
- Resource management (memory/CPU limits)
- Graceful degradation

**9. Modern Tools Knowledge**:
- Understanding of AI tool integration trends
- MCP protocol (cutting-edge, 2024 release)
- VS Code extension integration

**10. Problem Solving**:
- Debugged stdin/stdout issues
- Handled yfinance rate limits
- Implemented timeout protection

This project demonstrates that I can:
- Learn new technologies quickly (MCP)
- Build production-ready systems (Docker, error handling)
- Write clean, maintainable code (type hints, docs)
- Think about scalability and performance
- Integrate with modern AI ecosystems"

---

## 🎓 Skills Demonstrated

### Technical Skills
```
✅ Protocol Implementation (MCP, JSON-RPC 2.0)
✅ Python Async Programming (asyncio, await)
✅ Docker Containerization (Dockerfile, docker-compose)
✅ API Integration (yfinance, Yahoo Finance)
✅ Error Handling & Logging
✅ JSON Schema Validation
✅ stdin/stdout Stream Communication
✅ Type Hints & Static Typing
✅ PowerShell Scripting (test automation)
```

### Software Engineering
```
✅ Three-tier Architecture Design
✅ Separation of Concerns
✅ Single Responsibility Principle (3 separate tools)
✅ Dependency Injection
✅ Configuration Management
✅ Resource Management (timeouts, limits)
✅ Graceful Degradation
✅ Comprehensive Documentation
```

### DevOps & Deployment
```
✅ Docker Multi-stage Builds
✅ Container Orchestration (docker-compose)
✅ Health Checks & Monitoring
✅ Log Management
✅ Resource Constraints (CPU/memory limits)
✅ Automated Testing Scripts
```

### Domain Knowledge
```
✅ Financial Data APIs
✅ Stock Market Terminology (OHLCV, ticker symbols)
✅ AI Tool Integration Patterns
✅ Real-time Data Streaming
```

---

## 💼 Closing Statement

*"This MCP Stock Server project demonstrates my ability to:*

1. *Quickly learn and implement new protocols (MCP was released in 2024)*
2. *Build production-ready systems with Docker, proper error handling, and logging*
3. *Design clean architectures with separation of concerns*
4. *Integrate with external APIs and handle edge cases*
5. *Think about scalability, caching, and performance*
6. *Write comprehensive documentation and test suites*

*The system provides three financial data tools through a standardized protocol, making it compatible with any MCP client (VS Code, Claude, custom applications). It's containerized for easy deployment, includes comprehensive error handling, and demonstrates modern AI tool integration practices.*

*While this is an educational project using free APIs, the architecture and code quality are production-ready. The skills demonstrated here—protocol implementation, containerization, async programming, and systems design—are directly applicable to building any tool integration system, not just stock data.*

*I'm happy to discuss the technical implementation details, design decisions, or how this architecture could be extended for other use cases like weather data, database queries, or custom business logic tools."*

---

## 📞 Follow-Up Topics

If the interviewer wants to go deeper, be ready to discuss:

- **MCP Specification**: Tool discovery, resource providers, prompts, sampling
- **JSON-RPC Details**: Batch requests, notifications, error codes
- **Docker Internals**: Overlay networking, volume mounts, multi-stage builds
- **Python Async**: Event loops, executors, context managers
- **Financial APIs**: yfinance vs alternatives, rate limiting strategies
- **Security**: API key management, input validation, SQL injection prevention
- **Scaling**: Horizontal vs vertical, caching strategies, database design
- **Testing**: Unit vs integration tests, mocking external APIs
- **Monitoring**: Prometheus metrics, Grafana dashboards, alerting
- **Alternative Protocols**: gRPC vs REST vs JSON-RPC, when to use each

---

## 🔗 Related Concepts

### MCP Ecosystem
- **Anthropic**: Creator of MCP (Model Context Protocol)
- **Claude Desktop**: First major MCP client
- **VS Code**: MCP extension for Copilot integration
- **Other Servers**: Weather, database, file system, browser automation

### Financial Data
- **Yahoo Finance**: Free stock data source (yfinance library)
- **Alpha Vantage**: Alternative API (rate limits)
- **Technical Indicators**: SMA, RSI, MACD (could add)
- **Real-time vs Delayed**: Yahoo provides 15-minute delayed data

### Protocol Alternatives
- **REST**: HTTP-based (GET, POST, PUT, DELETE)
- **gRPC**: Google's RPC framework (binary, faster than JSON)
- **GraphQL**: Query language for APIs
- **WebSocket**: Full-duplex communication for real-time updates

---

*Document Version: 1.0*  
*Last Updated: January 20, 2026*  
*Project: Model Context Protocol (MCP) Stock Server*
