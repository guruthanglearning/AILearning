# 🚀 How to Add MCP Server in VS Code

## 📍 Step-by-Step Visual Guide

### **Method 1: Using VS Code Settings UI (Easiest)**

#### Step 1: Open Settings
1. Press `Ctrl + ,` (or `Cmd + ,` on Mac)
2. Or click: **File** → **Preferences** → **Settings**

#### Step 2: Search for MCP
1. In the search bar at top, type: `mcp`
2. Look for: **"Github Copilot Chat: MCP Servers"**

#### Step 3: Edit in settings.json
1. Click **"Edit in settings.json"** link
2. This opens your settings file

---

### **Method 2: Direct Edit settings.json (Faster)**

#### Step 1: Open Command Palette
Press: `Ctrl + Shift + P` (or `Cmd + Shift + P` on Mac)

#### Step 2: Type Command
Type: `Preferences: Open User Settings (JSON)`
OR
Type: `Preferences: Open Workspace Settings (JSON)` (for project-specific)

#### Step 3: This Opens the JSON Editor

---

## 📝 What to Add

### **Your Current Settings Location**
```
📁 D:\Study\AILearning\.vscode\settings.json
```

### **Current Content:**
```json
{
    "git.ignoreLimitWarning": true
}
```

### **Updated Content (Add MCP Server):**
```json
{
    "git.ignoreLimitWarning": true,
    
    // MCP (Model Context Protocol) Server Configuration
    "github.copilot.chat.mcp.servers": {
        
        // Stock Market Data Server (Docker-based)
        "stock-docker": {
            "command": "docker",
            "args": [
                "exec",
                "-i",
                "mcp-stock-server",
                "python",
                "/app/mcp_stock_server.py"
            ],
            "env": {
                "MCP_SERVER_NAME": "AILearning_StockServer",
                "MCP_SERVER_SOURCE": "Docker_YFinance_Server"
            }
        }
        
        // You can add more MCP servers here like:
        // "time-server": { ... },
        // "weather-server": { ... }
    }
}
```

---

## 🎯 Visual Location in VS Code

```
VS Code Interface
├── Top Menu Bar
│   └── File → Preferences → Settings (Ctrl+,)
│
├── Left Sidebar
│   ├── Explorer (Ctrl+Shift+E)
│   ├── Search (Ctrl+Shift+F)
│   ├── Source Control (Ctrl+Shift+G)
│   └── Extensions (Ctrl+Shift+X)
│
├── Settings UI (after Ctrl+,)
│   ├── Search bar: "mcp" ← Type here
│   └── Results:
│       └── Github Copilot Chat: MCP Servers
│           └── "Edit in settings.json" ← Click here
│
└── settings.json opens → Add configuration here
```

---

## 📂 File Locations

### **Workspace Settings (Recommended for this project):**
```
D:\Study\AILearning\.vscode\settings.json
```
- Only applies to this workspace
- Good for project-specific MCP servers
- Already exists in your project ✅

### **User Settings (Global for all projects):**
```
Windows: %APPDATA%\Code\User\settings.json
Mac: ~/Library/Application Support/Code/User/settings.json
Linux: ~/.config/Code/User/settings.json
```
- Applies to all VS Code workspaces
- Good for personal MCP servers you use everywhere

---

## 🖼️ Screenshot Guide

### 1️⃣ Open Settings
![Press Ctrl+,]
```
┌─────────────────────────────────────────────────────┐
│ File  Edit  Selection  View  Go  Run  Terminal      │
│ ┌─────────────────────────────────────────────┐     │
│ │ > Preferences: Open Settings (UI)           │     │  ← This appears
│ │   Preferences: Open Settings (JSON)         │     │     when you press
│ │   Preferences: Open User Settings (JSON)    │     │     Ctrl+Shift+P
│ │   Preferences: Open Workspace Settings (JSON)│    │
│ └─────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

### 2️⃣ Search for MCP
```
┌─────────────────────────────────────────────────────┐
│ Settings                                             │
│ ┌─────────────────────────────────────────────┐     │
│ │ Search settings              [mcp]           │ ← Type "mcp" here
│ └─────────────────────────────────────────────┘     │
│                                                      │
│ Results for "mcp"                                    │
│ ┌────────────────────────────────────────────┐      │
│ │ ⚙ Github Copilot Chat: MCP Servers        │      │
│ │   Configure MCP servers for GitHub Copilot │      │
│ │   Edit in settings.json                     │ ← Click this
│ └────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

### 3️⃣ Edit settings.json
```
┌─────────────────────────────────────────────────────┐
│ settings.json                                  × │
│─────────────────────────────────────────────────────│
│  1  {                                               │
│  2      "git.ignoreLimitWarning": true,            │
│  3                                                  │
│  4      // Add MCP configuration here ↓            │
│  5      "github.copilot.chat.mcp.servers": {       │
│  6          "stock-docker": {                      │
│  7              "command": "docker",                │
│  8              "args": [                           │
│  9                  "exec", "-i",                   │
│ 10                  "mcp-stock-server",             │
│ 11                  "python",                       │
│ 12                  "/app/mcp_stock_server.py"      │
│ 13              ]                                   │
│ 14          }                                       │
│ 15      }                                           │
│ 16  }                                               │
└─────────────────────────────────────────────────────┘
      ↑ Cursor position - paste configuration here
```

---

## ⚙️ Configuration Breakdown

### **Understanding Each Field:**

```json
"github.copilot.chat.mcp.servers": {
    // ↑ This is the VS Code setting key for MCP servers
    
    "stock-docker": {
        // ↑ Server ID (you choose this name)
        // Used to identify the server in logs and UI
        
        "command": "docker",
        // ↑ The executable to run
        // Options: "docker", "python", "node", "npx", etc.
        
        "args": [
            "exec",
            "-i",
            "mcp-stock-server",
            "python",
            "/app/mcp_stock_server.py"
        ],
        // ↑ Arguments passed to the command
        // This runs: docker exec -i mcp-stock-server python /app/mcp_stock_server.py
        
        "env": {
            "MCP_SERVER_NAME": "AILearning_StockServer",
            "MCP_SERVER_SOURCE": "Docker_YFinance_Server"
        }
        // ↑ Environment variables passed to the server
        // Optional, but useful for configuration
    }
}
```

---

## 🔄 Alternative Configurations

### **Option A: Docker-based (Current)**
```json
"stock-docker": {
    "command": "docker",
    "args": ["exec", "-i", "mcp-stock-server", "python", "/app/mcp_stock_server.py"]
}
```
✅ Pros: Isolated, consistent environment  
❌ Cons: Requires Docker running

---

### **Option B: Local Python (Direct)**
```json
"stock-local": {
    "command": "D:\\Study\\AILearning\\shared_Environment\\Scripts\\python.exe",
    "args": [
        "D:\\Study\\AILearning\\MLProjects\\modelcontextprotocol\\python\\mcp_stock_server.py"
    ],
    "env": {
        "MCP_SERVER_NAME": "AILearning_LocalStockServer"
    }
}
```
✅ Pros: No Docker needed, faster startup  
❌ Cons: Requires Python environment setup

---

### **Option C: PowerShell Wrapper**
```json
"stock-powershell": {
    "command": "powershell.exe",
    "args": [
        "-File",
        "D:\\Study\\AILearning\\MLProjects\\modelcontextprotocol\\python\\run_mcp_server.ps1"
    ]
}
```
✅ Pros: Can handle complex startup logic  
❌ Cons: Extra wrapper script needed

---

## ✅ Verification Steps

### **Step 1: Save the File**
Press: `Ctrl + S`

### **Step 2: Reload VS Code**
1. Press: `Ctrl + Shift + P`
2. Type: `Developer: Reload Window`
3. Press Enter

### **Step 3: Check if MCP Server is Loaded**

#### Method A: Check Output Panel
1. Press: `Ctrl + Shift + U` (Open Output panel)
2. In dropdown, select: **"GitHub Copilot Chat: MCP"**
3. Look for: `"Loaded MCP server: stock-docker"`

#### Method B: Try in Chat
1. Open GitHub Copilot Chat: `Ctrl + Alt + I`
2. Type: `@mcp-stock-docker get stock price for AAPL`
3. OR just: `Get stock price for AAPL` (if auto-detected)

---

## 🐛 Troubleshooting

### **Issue 1: Server Not Found**
```
Error: MCP server 'stock-docker' not found
```

**Solution:**
1. Check spelling in settings.json
2. Reload VS Code window
3. Check Docker container is running: `docker ps | findstr mcp-stock-server`

---

### **Issue 2: Docker Not Running**
```
Error: Cannot connect to the Docker daemon
```

**Solution:**
```powershell
# Start Docker Desktop
# Then verify:
docker ps

# Start MCP container if not running:
cd D:\Study\AILearning\MLProjects\modelcontextprotocol\python
docker-compose up -d
```

---

### **Issue 3: Python Path Not Found**
```
Error: Command 'python' not found
```

**Solution:**
Use full path to Python:
```json
"command": "D:\\Study\\AILearning\\shared_Environment\\Scripts\\python.exe"
```

---

### **Issue 4: Settings Not Taking Effect**
**Solution:**
1. Save file: `Ctrl + S`
2. Reload window: `Ctrl + Shift + P` → "Developer: Reload Window"
3. Or restart VS Code completely

---

## 📋 Complete Example (Copy-Paste Ready)

### **For Your Workspace (.vscode/settings.json):**

```json
{
    "git.ignoreLimitWarning": true,
    "github.copilot.chat.mcp.servers": {
        "stock-docker": {
            "command": "docker",
            "args": [
                "exec",
                "-i",
                "mcp-stock-server",
                "python",
                "/app/mcp_stock_server.py"
            ],
            "env": {
                "MCP_SERVER_NAME": "AILearning_StockServer",
                "MCP_SERVER_SOURCE": "Docker_YFinance_Server"
            }
        }
    }
}
```

---

## 🎓 Usage Examples

After adding the MCP server, you can use it in VS Code Copilot Chat:

### **Example 1: Get Stock Price**
```
You: Get the current stock price for Apple
Copilot: [Uses stock-docker MCP server]
Response: AAPL: $178.45 (+0.93%)
```

### **Example 2: Company Information**
```
You: Show me detailed information about Tesla
Copilot: [Uses stock-docker MCP server]
Response: Tesla Inc. (TSLA)
- Sector: Automotive
- Market Cap: $850B
- P/E Ratio: 45.3
```

### **Example 3: Historical Data**
```
You: Get 6-month stock history for Microsoft
Copilot: [Uses stock-docker MCP server]
Response: [Returns historical OHLCV data]
```

---

## 🔗 Additional Resources

- **MCP Documentation**: https://modelcontextprotocol.io/
- **Your Project README**: `D:\Study\AILearning\MLProjects\modelcontextprotocol\python\README.md`
- **VS Code MCP Extension**: Search "MCP" in Extensions (Ctrl+Shift+X)

---

## 🚀 Quick Start Checklist

- [ ] Docker Desktop is running
- [ ] MCP Stock Server container is running (`docker ps`)
- [ ] Opened VS Code settings (`Ctrl + ,`)
- [ ] Found MCP settings or opened settings.json
- [ ] Added MCP server configuration
- [ ] Saved file (`Ctrl + S`)
- [ ] Reloaded VS Code window (`Ctrl + Shift + P` → "Reload Window")
- [ ] Tested in Copilot Chat

---

## 💡 Pro Tips

### **Tip 1: Multiple MCP Servers**
You can add multiple servers:
```json
"github.copilot.chat.mcp.servers": {
    "stock-docker": { ... },
    "weather-api": { ... },
    "database-query": { ... }
}
```

### **Tip 2: Different Environments**
Use workspace settings (`.vscode/settings.json`) for project-specific servers  
Use user settings for personal servers you want everywhere

### **Tip 3: Logging**
Check MCP logs:
```
Output Panel (Ctrl+Shift+U) → Select "GitHub Copilot Chat: MCP"
```

### **Tip 4: Disable Temporarily**
Comment out server without deleting:
```json
// "stock-docker": {
//     "command": "docker",
//     ...
// }
```

---

*Last Updated: January 21, 2026*  
*For: AILearning MCP Stock Server Project*
