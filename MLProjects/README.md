# AI Models Learning Collection

This directory contains various AI and machine learning model implementations for educational purposes, along with a comprehensive AI prompting system for consistent, high-quality interactions.

---

## 📑 Table of Contents

- [Available Projects](#-available-projects)
  - [Production-Ready Projects](#-production-ready-projects)
  - [Learning & Experimental](#-learning--experimental-projects)
- [Project Comparison Matrix](#-project-comparison-matrix)
- [Project Status](#-project-status)
- [Interview Preparation](#-interview-preparation)
- [AI Prompting System](#-ai-prompting-system)
- [Getting Started](#-getting-started)
- [Quick Start Commands](#-quick-start-commands)
- [Quick Navigation](#-quick-navigation)
- [External Integrations](#-external-integrations)
- [Documentation Standards](#-documentation-standards)
- [Tech Stack Overview](#️-tech-stack-overview)
- [Skills Demonstrated](#-skills-demonstrated)
- [Project Highlights](#-project-highlights)
- [Learning Path](#-learning-path-recommendations)
- [FAQ & Troubleshooting](#-faq--troubleshooting)
- [Related Resources](#-related-resources)
- [Contact & Portfolio](#-contact--portfolio)
- [License](#-license)

---

## 📚 Available Projects

### 🎯 Production-Ready Projects

#### **1. Credit Card Fraud Detection** (`creditcardfrauddetection/`)
- **Type**: Hybrid AI System (XGBoost + BERT + LLM)
- **Models**: XGBoost classifier, BERT embeddings, GPT-4/Ollama
- **Features**: Real-time fraud detection, pattern matching with ChromaDB, explainable AI
- **Tech Stack**: FastAPI, Streamlit, Docker, Prometheus monitoring
- **Accuracy**: 98.7% fraud detection rate
- **Documentation**: [Interview Guide](creditcardfrauddetection/Interview_Explanation.md)

#### **2. Log Classification System** (`LogClassification/`)
- **Type**: Tri-tier Hybrid Classification
- **Models**: Regex (Tier 1) → BERT + Logistic Regression (Tier 2) → Llama 3.3 via Groq (Tier 3)
- **Features**: Multi-tier fallback architecture, 98.7% overall accuracy
- **Tech Stack**: all-MiniLM-L6-v2 BERT, Groq API
- **Performance**: 0.1ms (Regex) → 10ms (BERT) → 500ms (LLM)
- **Documentation**: [Interview Guide](LogClassification/Interview_Explanation.md)

#### **3. Stock Prediction System** (`StockPrediction/`)
- **Type**: Multi-model Forecasting & Trend Analysis
- **Models**: XGBoost Regression, XGBoost Classification, FinBERT Sentiment
- **Features**: Price forecasting, trend classification, sentiment analysis, technical indicators
- **Tech Stack**: FastAPI, Streamlit, yfinance, NewsAPI, Finnhub
- **Indicators**: SMA, EMA, RSI, MACD, ATR, OBV, ZigZag
- **Documentation**: [Interview Guide](StockPrediction/Interview_Explanation.md)

#### **4. Model Context Protocol (MCP) Stock Server** (`modelcontextprotocol/`)
- **Type**: AI Tool Integration Server (Protocol Implementation)
- **Protocol**: Model Context Protocol (MCP) - Anthropic's JSON-RPC 2.0
- **Features**: Real-time stock data, company info, historical data via MCP
- **Tools**: `get_stock_price`, `get_stock_info`, `get_stock_history`
- **Tech Stack**: Python MCP SDK, yfinance, Docker
- **Clients**: VS Code, Claude Desktop, Python clients
- **Documentation**: [Interview Guide](modelcontextprotocol/Interview_Explanation.md)

### 🧪 Learning & Experimental Projects

#### **5. AI Model Development** (`AIModels/Learning/`)
- **Type**: Educational implementations and experiments
- **Focus**: Hands-on ML algorithm implementations
- **Purpose**: Learning foundational concepts

---

## 📊 Project Comparison Matrix

| Project | Type | Primary Tech | Accuracy/Performance | Use Case |
|---------|------|--------------|---------------------|----------|
| **Credit Card Fraud** | Classification | XGBoost + BERT + LLM | 98.7% | Financial security |
| **Log Classification** | Multi-tier Classification | Regex + BERT + Llama | 98.7% overall | System monitoring |
| **Stock Prediction** | Regression + Classification | XGBoost + FinBERT | ~87% price accuracy | Trading analysis |
| **MCP Stock Server** | Protocol Server | MCP + yfinance | ~2-3s response time | AI tool integration |
| **AI Models** | Educational | Various | N/A | Learning |

---

## 🎓 Interview Preparation

Each production project includes a comprehensive **Interview_Explanation.md** file with:
- 30-second project pitch
- Detailed model explanations
- System architecture diagrams
- 10+ common interview Q&A
- Technical deep-dives
- Skills demonstrated

Perfect for technical interviews and portfolio presentations!

## 🎯 AI Prompting System

This directory includes a sophisticated prompting framework designed to ensure consistent, high-quality AI interactions for ML/AI projects:

### 📁 Core Prompting Files

#### **PROMPTING_RULES.md** - The Foundation
- **42 comprehensive rules** organized into 6 categories
- **Categories**: General Project, ML-Specific, Financial/Stock Analysis, Educational Content, Code Generation, Analysis & Reporting
- **Purpose**: Establishes standards for AI responses including documentation, testing, performance metrics, and best practices

#### **PROMPTING_TEMPLATES.md** - Ready-to-Use Formats  
- **10 specialized templates** for different scenarios
- **Templates include**: Code Generation, ML Model Development, Stock Analysis, Learning, Debugging, Performance Optimization, Feature Engineering, Model Selection, Data Analysis, Production Deployment
- **Structure**: Each template has placeholder brackets `[LIKE_THIS]` for customization
- **Usage instructions** and best practices included

#### **QUICK_RULES_REFERENCE.md** - Fast Access
- **Condensed rule combinations** for common tasks
- **Copy-paste ready** rule sets for immediate use  
- **Quick examples** showing proper usage patterns
- **Time-saving** alternative to reading full rule sets

#### **rule_selector.py** - Interactive Tool
- **Interactive CLI tool** for selecting appropriate prompting rules
- **Menu-driven interface** for rule and template selection
- **Copy-paste output** ready for immediate use
- **Help system** with detailed explanations

### 🚀 How to Use the Prompting System

#### **For Routine Tasks:**
1. Use `QUICK_RULES_REFERENCE.md` → Copy appropriate rule combination
2. Add your specific question/request  
3. Paste into AI conversation

#### **For Interactive Selection:**
1. Run `python rule_selector.py`
2. Follow the menu to select appropriate rules/templates
3. Copy the generated prompt format
4. Fill in your specific details

#### **For Complex Projects:**
1. Check `PROMPTING_TEMPLATES.md` → Find matching template
2. Fill in all `[BRACKETED]` placeholders
3. Reference `PROMPTING_RULES.md` for additional context if needed

### 💡 Practical Example

**Instead of asking:**
```
"How do I build a stock prediction model?"
```

**Use the prompting system:**
```
Rules: Apply ML Specific + Financial Analysis + Educational rules from PROMPTING_RULES.md

Scenario: Stock price direction prediction for day trading
Data: Daily OHLCV data for S&P 500 stocks  
Current Model: Basic linear regression with technical indicators
Performance: 52% accuracy, need 60%+ for profitable trading
Goal: Improve directional prediction accuracy

Question: How can I enhance my feature engineering and model selection to achieve profitable trading accuracy while maintaining proper risk management and backtesting methodology?
```

This framework transforms vague requests into structured, comprehensive prompts that yield much better AI responses with proper context, safety considerations, and actionable advice.

### ✅ Key Benefits

- **Consistency** - Standardized approach to AI interactions
- **Quality** - Ensures comprehensive, well-documented responses  
- **Efficiency** - Templates save time and reduce trial-and-error
- **Learning** - Educational rules promote understanding over just solutions
- **Safety** - Financial rules include appropriate disclaimers and risk considerations

## 🎯 Purpose

Educational AI model implementations focusing on:
- Practical machine learning applications
- Hands-on learning experiences
- Real-world data scenarios
- Performance evaluation and validation
- Structured AI interaction methodology

## 🚀 Getting Started

### For ML Project Exploration
1. **Browse projects** in the comparison matrix above
2. **Navigate to project folders** for detailed READMEs and code
3. **Review Interview Guides** for comprehensive project understanding

### For AI Prompting System
1. **Quick tasks**: Use `QUICK_RULES_REFERENCE.md` → Copy rule combination
2. **Interactive**: Run `python rule_selector.py` for menu-driven selection
3. **Complex projects**: Use `PROMPTING_TEMPLATES.md` templates

### For Interview Preparation
1. Read project-specific `Interview_Explanation.md` files
2. Understand model architectures and design decisions
3. Practice explaining with provided Q&A sections

---

## 📂 Quick Navigation

```
MLProjects/
├── creditcardfrauddetection/     # Fraud detection with hybrid AI
│   ├── Interview_Explanation.md  # Interview guide
│   ├── README.md                  # Full documentation
│   └── app/                       # FastAPI backend
│
├── LogClassification/             # Tri-tier log classification
│   ├── Interview_Explanation.md  # Interview guide
│   └── classify.py                # Main classifier
│
├── StockPrediction/               # Price forecasting system
│   ├── Interview_Explanation.md  # Interview guide
│   ├── README.md                  # Full documentation
│   └── Src/                       # Source code
│
├── modelcontextprotocol/          # MCP server implementation
│   ├── Interview_Explanation.md  # Interview guide
│   ├── HOW_TO_ADD_MCP_IN_VSCODE.md  # VS Code setup guide
│   └── python/                    # Server code
│       ├── mcp_stock_server.py    # Main server
│       └── docker-compose.yml     # Docker deployment
│
├── PROMPTING_RULES.md             # 42 AI prompting rules
├── PROMPTING_TEMPLATES.md         # 10 ready-to-use templates
├── QUICK_RULES_REFERENCE.md       # Quick reference guide
└── rule_selector.py               # Interactive rule selector
```

---

## 🔗 External Integrations

- **VS Code**: MCP server integration for Copilot Chat
- **Claude Desktop**: MCP server support
- **Docker**: Containerized deployments for all production projects
- **FastAPI**: REST API backends
- **Streamlit**: Interactive UIs

---

## 📝 Documentation Standards

All production projects follow consistent documentation:
- ✅ Comprehensive README with architecture diagrams
- ✅ Interview preparation guides with Q&A
- ✅ Deployment instructions (Docker + local)
- ✅ Testing examples and validation
- ✅ Performance metrics and benchmarks

---

## 🛠️ Tech Stack Overview

### Machine Learning
- **XGBoost**: Fraud detection, stock prediction, log classification
- **BERT Models**: Embeddings (all-MiniLM-L6-v2), FinBERT sentiment
- **LLMs**: GPT-4, Llama 3.3 (via Groq), Ollama

### Infrastructure
- **APIs**: FastAPI, REST
- **Databases**: ChromaDB (vector), PostgreSQL (proposed)
- **Containerization**: Docker, docker-compose
- **Monitoring**: Prometheus, Grafana

### Data Sources
- **Financial**: yfinance, Finnhub, NewsAPI
- **ML Libraries**: scikit-learn, transformers, sentence-transformers

---

## 📊 Skills Demonstrated

### Technical Skills
- Machine Learning (classification, regression, NLP)
- Protocol Implementation (MCP, JSON-RPC 2.0)
- API Development (FastAPI, REST)
- Containerization (Docker)
- Vector Databases (ChromaDB)
- Real-time Systems

### Software Engineering
- System Architecture Design
- Error Handling & Logging
- Testing & Validation
- Documentation
- Deployment Automation

### Domain Knowledge
- Financial Analysis (fraud detection, stock prediction)
- System Monitoring (log classification)
- AI Tool Integration (MCP protocol)

---

## 🎯 Project Highlights

### Most Complex Architecture
**Credit Card Fraud Detection** - Combines 3 AI models (XGBoost + BERT + LLM) with RAG

### Most Innovative
**MCP Stock Server** - Implements cutting-edge Model Context Protocol (2024 spec)

### Best Performance
**Log Classification** - 0.1ms response time for Regex tier, 98.7% overall accuracy

### Most Production-Ready
**Credit Card Fraud** - Full monitoring stack (Prometheus + Grafana), Docker deployment

---

---

## 🏃 Quick Start Commands

### Prerequisites
```bash
# Install Python 3.10+
python --version

# Install Docker Desktop (for containerized projects)
docker --version
```

### Running Projects

#### Credit Card Fraud Detection
```bash
cd creditcardfrauddetection
docker-compose up -d
# Access UI: http://localhost:8501
# Access API: http://localhost:8000
```

#### Log Classification
```bash
cd LogClassification
python classify.py --log "ERROR: Database connection failed"
```

#### Stock Prediction
```bash
cd StockPrediction/Src
python UI.py
# Access dashboard: http://localhost:8501
```

#### MCP Stock Server
```bash
cd modelcontextprotocol/python
docker-compose up -d
# Test: python docker_mcp_client.py price AAPL
```

---

## 🤝 Contributing

These projects are for educational and portfolio purposes. However:
- Bug reports and suggestions are welcome
- Feel free to fork and adapt for your own learning
- Please maintain proper attribution

---

---

## ❓ FAQ & Troubleshooting

### Q: Which project should I start with?
**A:** Start with **Stock Prediction** - it has the clearest ML fundamentals and is easier to understand.

### Q: Do I need Docker for all projects?
**A:** No. Only Credit Card Fraud and MCP Stock Server require Docker. Others can run locally with Python.

### Q: How do I use the AI Prompting System?
**A:** 
1. For quick tasks: Open `QUICK_RULES_REFERENCE.md` and copy relevant rules
2. For interactive: Run `python rule_selector.py`
3. For templates: Check `PROMPTING_TEMPLATES.md`

### Q: Where are the Interview Guides?
**A:** Each project folder has an `Interview_Explanation.md` file with comprehensive Q&A.

### Q: Can I use these projects in my portfolio?
**A:** Yes! These are educational projects. Fork and adapt them. Just maintain proper attribution.

### Q: Which project is best for interviews?
**A:** All 4 production projects have interview guides. Choose based on role:
- **ML Engineer**: Credit Card Fraud or Stock Prediction
- **Software Engineer**: MCP Stock Server
- **Data Scientist**: Log Classification or Stock Prediction

### Q: How do I run projects without Docker?
**A:** Check each project's README for local installation instructions. Generally:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py  # or specific entry point
```

### Common Issues

**Issue: Docker container won't start**
```bash
# Check Docker is running
docker ps

# Restart Docker Desktop
# Then: docker-compose up -d
```

**Issue: Python package conflicts**
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Issue: API keys missing**
```bash
# Create .env file in project root
# Add required keys (see project README)
```

---

## 🔗 Related Resources

- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)
- **XGBoost**: [xgboost.readthedocs.io](https://xgboost.readthedocs.io/)
- **Transformers**: [huggingface.co/docs/transformers](https://huggingface.co/docs/transformers)
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
- **Docker**: [docs.docker.com](https://docs.docker.com/)

---

## 📧 Contact & Portfolio

- **GitHub**: [gurunathan6378](https://github.com/gurunathan6378)
- **Repository**: [AILearning](https://github.com/gurunathan6378/AILearning)
- **Projects**: 4 production-ready ML/AI systems + prompting framework

---

## 📜 License

Educational and portfolio purposes. Individual projects may have specific requirements:
- Financial projects include appropriate disclaimers
- No warranties or guarantees for trading/financial advice
- Use at your own risk

---

---

## 📊 Project Status

| Project | Status | Deployment | Documentation | Tests |
|---------|--------|------------|---------------|-------|
| **Credit Card Fraud** | ✅ Complete | ✅ Docker | ✅ Full | ✅ Yes |
| **Log Classification** | ✅ Complete | ✅ Local | ✅ Full | ✅ Yes |
| **Stock Prediction** | ✅ Complete | ✅ Docker | ✅ Full | ✅ Yes |
| **MCP Stock Server** | ✅ Complete | ✅ Docker | ✅ Full | ✅ Yes |
| **AI Models** | 🔄 Ongoing | - | ⚠️ Partial | - |

**Legend:**
- ✅ Complete and documented
- 🔄 Work in progress
- ⚠️ Partial documentation
- ❌ Not implemented

---

## 🎓 Learning Path Recommendations

### For Beginners
1. Start with **AI Prompting System** (QUICK_RULES_REFERENCE.md)
2. Explore **Stock Prediction** (clearest ML fundamentals)
3. Try **Log Classification** (understand multi-tier systems)

### For Intermediate
1. Study **Credit Card Fraud** (complex hybrid AI)
2. Understand **MCP Stock Server** (protocol implementation)
3. Read all Interview_Explanation.md files

### For Advanced
1. Deploy all projects with Docker
2. Modify and extend features
3. Integrate multiple projects together

---

## 📅 Last Updated
**January 22, 2026**

---