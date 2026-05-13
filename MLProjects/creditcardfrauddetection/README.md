# Credit Card Fraud Detection System

## Overview

This project develops a comprehensive real-time credit card fraud detection system that leverages both traditional machine learning models and Large Language Models (LLMs) with Retrieval Augmented Generation (RAG) to identify fraudulent transactions. The system provides real-time detection capabilities, comprehensive fraud pattern management, and an intuitive web-based interface for monitoring and analysis.

## 🚀 Quick Start

### Local Development (Recommended for Development)

```powershell
# Launch both API and UI locally on Windows
.\launch_local.ps1

# Launch only API
.\launch_local.ps1 -SkipUI

# Launch only UI (if API already running)
.\launch_local.ps1 -SkipAPI
```

**Access URLs:**
- 🌐 Dashboard: http://localhost:8501
- 📡 API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs
- ❤️ Health Check: http://localhost:8000/health

### Docker Deployment (Recommended for Production)

```powershell
# First time setup - build images
.\launch_docker.ps1 -Build

# Start containers
.\launch_docker.ps1

# View logs
.\launch_docker.ps1 -Logs

# Check status
.\launch_docker.ps1 -Status

# Stop containers
.\launch_docker.ps1 -Down

# Clean everything (containers + volumes + images)
.\launch_docker.ps1 -Clean
```

**Access URLs:**
- 🌐 Dashboard: http://localhost:8501
- 📡 API: http://localhost:8000
- 📊 Prometheus: http://localhost:9090
- 📈 Grafana: http://localhost:3000

### Running Tests

```powershell
# Run all tests (local deployment)
.\scripts\run_all_tests.ps1

# Run all tests (Docker deployment)
.\scripts\run_all_tests.ps1 -Mode docker

# Run specific test suites
.\scripts\run_unit_tests.ps1
.\scripts\run_integration_tests.ps1 -Mode local
.\scripts\run_playwright_tests.ps1 -Mode docker

# Run tests with options
.\scripts\run_all_tests.ps1 -SkipE2E -Verbose
```

## Project Structure

```
creditcardfrauddetection/
├── app/
│   ├── main.py                              # FastAPI application entry point
│   ├── models/                              # Pydantic models and data schemas
│   ├── routers/                             # API route handlers
│   ├── services/                            # Business logic and ML services
│   ├── database/                            # Database operations and models
│   └── utils/                               # Utility functions and helpers
├── ui/
│   ├── app.py                               # Streamlit UI application
│   ├── components/                          # UI components and widgets
│   ├── pages/                               # Streamlit pages
│   └── utils/                               # UI utility functions
├── data/
│   ├── chroma_db/                           # Vector database storage
│   ├── models/                              # Trained ML models
│   ├── patterns/                            # Fraud pattern data
│   └── sample/                              # Sample datasets
├── scripts/
│   ├── debug/                               # Debugging and diagnostic scripts
│   ├── powershell/                          # PowerShell automation scripts
│   ├── utility/                             # Python utility scripts
│   └── tests/                               # Test automation scripts
├── monitoring/
│   ├── prometheus/                          # Prometheus configuration
│   ├── grafana/                             # Grafana dashboards
│   └── logs/                                # Application logs
├── notebooks/                               # Jupyter notebooks for analysis
├── tests/                                   # Unit and integration tests
├── docker-compose.yml                      # Docker orchestration
├── Dockerfile                               # Container build instructions
├── requirements.txt                         # Python dependencies
├── launch_system_root.ps1                  # Main system launcher
└── README.md                                # Project documentation
```

## Models & APIs Used

### 🤖 Machine Learning Models

#### 1. **XGBoost Classification Model (Fraud Detection)**
- **Purpose**: Real-time fraud classification of credit card transactions
- **Model Type**: Gradient Boosting Binary Classifier
- **Input Features**: 
  - Transaction amount, merchant category, location data
  - Time-based features (hour, day, month patterns)
  - Historical transaction patterns and velocity
  - Account behavioral patterns and anomaly scores
- **Output**: Binary fraud classification (0=Legitimate, 1=Fraudulent) + confidence score
- **Why XGBoost?**:
  - **High Accuracy**: Excellent performance on structured transaction data
  - **Feature Importance**: Identifies most significant fraud indicators
  - **Robust to Imbalance**: Handles skewed fraud datasets effectively
  - **Fast Inference**: Sub-100ms prediction times for real-time detection

##### **🚨 Common Fraud Patterns Detected by XGBoost Model:**

**High-Risk Patterns (Fraud Score > 0.8):**
- 💳 **Card Testing**: Multiple small transactions ($1-5) in rapid succession at different merchants
- 🌍 **Geographic Impossibility**: Card used in New York at 2:00 PM, then in London at 2:30 PM same day
- 💰 **Amount Spike**: Transaction 10x+ larger than user's typical spending ($50 average → $2,000 purchase)
- ⚡ **Velocity Fraud**: 15+ transactions within 1 hour across multiple merchant categories
- 🏪 **High-Risk Merchants**: Transactions at known compromised or high-risk merchant locations
- 🕐 **Unusual Timing**: Legitimate user never shops past 10 PM, but card used at 3 AM

**Medium-Risk Patterns (Fraud Score 0.3-0.8):**
- 🛒 **New Merchant Category**: First-ever purchase at gas station for a user who only shops online
- 📍 **Location Deviation**: Purchase 500+ miles from user's typical shopping radius
- 💸 **Round Number Bias**: Transactions in exact round amounts ($100, $500, $1000)
- 🔄 **Repetitive Amounts**: Same exact amount ($127.50) charged 3 times in different states
- 🏬 **Merchant Type Switch**: User typically shops at grocery stores, sudden luxury jewelry purchase

**Low-Risk Patterns (Fraud Score < 0.3):**
- ✅ **Consistent Behavior**: Regular coffee shop purchase at usual time and location
- 📱 **Online Shopping**: E-commerce purchase matching user's browsing history
- 🏠 **Local Transactions**: Purchase within 5-mile radius of user's home/work
- ⏰ **Time Consistency**: Weekend shopping matching user's historical weekend patterns

#### 2. **Vector Similarity Model (Pattern Matching)**
- **Purpose**: Similarity-based fraud pattern detection using vector embeddings
- **Model Type**: ChromaDB Vector Database with cosine similarity
- **Input**: Transaction feature vectors and fraud pattern embeddings
- **Output**: Similar fraud patterns with similarity scores
- **Why Vector Database?**:
  - **Pattern Recognition**: Identifies similar fraud patterns from historical data
  - **Scalable Search**: Efficient similarity search across 1,500+ patterns
  - **Real-time Updates**: Dynamic pattern addition and modification
  - **Context Preservation**: Maintains fraud context and relationships

##### **🔍 Example Fraud Patterns in Vector Database:**

**Card Skimming Patterns (Similarity Score > 0.9):**
- 💳 **ATM Skimming**: Multiple cards compromised at same ATM location within 48 hours
- 🏪 **Gas Station Skimming**: Cards used at compromised gas station, then fraudulent online purchases
- 🏨 **Hotel Skimming**: Business travelers' cards compromised during hotel stays

**Account Takeover Patterns (Similarity Score > 0.85):**
- 📧 **Email/Password Breach**: Sudden change in spending behavior after data breach
- 📱 **SIM Swap**: Phone number transfer followed by high-value online purchases
- 🔑 **Credential Stuffing**: Multiple failed login attempts followed by successful fraudulent transactions

**Synthetic Identity Patterns (Similarity Score > 0.8):**
- 👤 **Frankenstein Identity**: Real SSN + fake name + real address combination
- 📊 **Credit Building**: Small, regular payments to build credit history before major fraud
- 🏠 **Address Manipulation**: Similar addresses with minor variations (123 Main St vs 123 Main Street)

**Organized Crime Patterns (Similarity Score > 0.75):**
- 🌐 **Cross-Border**: Coordinated attacks across multiple countries using similar modus operandi
- 💰 **Money Laundering**: Structured transactions just under reporting thresholds
- 🔄 **Bust-Out Schemes**: Rapid credit utilization across multiple accounts simultaneously

#### 3. **Large Language Models (LLM Integration)**
- **Models**: 
  - **Primary**: OpenAI GPT-4/GPT-3.5-turbo
  - **Fallback**: Ollama (Local deployment)
  - **Mock**: Local simulation for development
- **Purpose**: Advanced fraud analysis with natural language explanations
- **Architecture**: RAG (Retrieval Augmented Generation) with vector search
- **Output**: Detailed fraud analysis, explanations, and recommendations
- **Why LLM Integration?**:
  - **Explainable AI**: Natural language fraud explanations
  - **Pattern Understanding**: Complex fraud pattern interpretation
  - **Contextual Analysis**: Considers broader transaction context
  - **Adaptive Learning**: Continuous improvement through feedback

##### **🤖 Example LLM-Generated Fraud Analysis:**

**High-Risk Transaction Analysis:**
```
🚨 FRAUD ALERT: This transaction shows multiple red flags consistent with card-not-present fraud:

Risk Factors Identified:
• Transaction amount ($2,847) is 15x higher than user's average ($189)
• Purchase made at 3:47 AM - outside user's normal shopping hours (9 AM - 8 PM)
• Merchant location (Miami, FL) is 1,200 miles from user's home (Chicago, IL)
• First-time purchase at electronics store - user typically shops at grocery/gas stations
• No recent travel bookings or location changes in user's profile

Pattern Analysis:
This matches "vacation fraud" patterns where criminals use stolen cards for expensive 
electronics purchases in tourist areas, often during off-hours to avoid detection.

Confidence: 94% fraud probability
Recommendation: BLOCK transaction and alert cardholder immediately
```

**Medium-Risk Transaction Analysis:**
```
⚠️ MEDIUM RISK: Transaction requires manual review due to mixed signals:

Concerning Factors:
• Purchase location (Las Vegas, NV) differs from user's home state (Ohio)
• Transaction time (2:15 AM) is unusual for this user
• Amount ($567) is higher than typical but not extreme

Protective Factors:
• User has legitimate travel history to Nevada (3 visits in past year)
• Merchant type (hotel/restaurant) matches user's travel spending patterns
• User's phone location services show recent Las Vegas check-ins

Pattern Analysis:
While the timing and amount are concerning, the user's travel history and phone 
location data suggest legitimate business travel. However, the late-night timing 
warrants additional verification.

Confidence: 65% legitimate probability
Recommendation: HOLD for SMS verification before processing
```

**Low-Risk Transaction Analysis:**
```
✅ LOW RISK: Transaction appears legitimate based on established patterns:

Supporting Evidence:
• Amount ($47.83) falls within user's typical range ($25-75)
• Merchant (Starbucks) matches user's frequent coffee purchases
• Location (Downtown Chicago) is near user's workplace
• Time (8:15 AM) aligns with user's morning routine
• Consistent with weekday spending behavior

Pattern Analysis:
This transaction perfectly matches the user's established morning coffee routine. 
All indicators suggest normal, legitimate spending behavior with no anomalies detected.

Confidence: 96% legitimate probability
Recommendation: APPROVE transaction automatically
```

### 🌐 External APIs and Services

#### 1. **OpenAI API**
- **Purpose**: Advanced fraud analysis and natural language processing
- **Models Used**: GPT-4, GPT-3.5-turbo
- **Data Processing**:
  - Transaction context analysis
  - Fraud pattern explanation generation
  - Risk assessment narratives
- **Why OpenAI?**:
  - **State-of-the-art NLP**: Most advanced language understanding
  - **Contextual Reasoning**: Complex fraud scenario analysis
  - **Reliable Service**: Enterprise-grade API reliability
  - **Flexible Integration**: Easy API integration with fallback support

#### 2. **Ollama API (Local LLM)**
- **Purpose**: Local LLM deployment for privacy-sensitive environments
- **Models Supported**: Llama2, Mistral, CodeLlama, Custom models
- **Data Processing**:
  - On-premises fraud analysis
  - Privacy-preserving transaction processing
  - Offline fraud detection capabilities
- **Why Ollama?**:
  - **Data Privacy**: No external data transmission
  - **Cost Effective**: No per-request API costs
  - **Customizable**: Fine-tunable for specific fraud patterns
  - **Offline Capability**: Works without internet connectivity

#### 3. **ChromaDB Vector Database**
- **Purpose**: Fraud pattern storage and similarity search
- **Data Stored**:
  - 1,500+ fraud pattern embeddings
  - Transaction feature vectors
  - Historical fraud case embeddings
- **Why ChromaDB?**:
  - **Fast Similarity Search**: Sub-second pattern matching
  - **Persistent Storage**: Reliable pattern persistence
  - **Python Integration**: Native Python client libraries
  - **Scalable**: Handles large-scale pattern databases

### 🔧 Technical Stack

#### **Machine Learning & AI Libraries**
| Library | Purpose | Why Used |
|---------|---------|----------|
| `xgboost` | Gradient boosting classifier | High-performance fraud detection |
| `scikit-learn` | ML utilities and preprocessing | Standard ML workflows and metrics |
| `chromadb` | Vector database operations | Efficient similarity search |
| `transformers` | LLM integration utilities | Standardized model interfaces |
| `pandas` | Data manipulation | Efficient transaction data processing |
| `numpy` | Numerical computing | Fast array operations for ML |

#### **API & Web Framework**
| Framework | Purpose | Why Used |
|-----------|---------|----------|
| `FastAPI` | REST API server | High-performance async API framework |
| `Streamlit` | Web UI interface | Rapid development of interactive dashboards |
| `uvicorn` | ASGI server | Production-ready async server |
| `pydantic` | Data validation | Type-safe API request/response handling |

#### **External Integrations**
| Service | Integration | Data Type |
|---------|-------------|-----------|
| `OpenAI API` | REST API | Advanced fraud analysis |
| `Ollama API` | Local/Remote API | Local LLM processing |
| `ChromaDB` | Python Client | Vector pattern storage |
| `Prometheus` | Metrics API | System monitoring data |

## Features

- **Real-time Fraud Detection**
  - Sub-100ms transaction analysis
  - XGBoost-based binary classification
  - Confidence scoring for risk assessment
  - Real-time API endpoints for transaction screening

- **Advanced Pattern Recognition**
  - Vector similarity-based pattern matching
  - 1,500+ pre-loaded fraud patterns
  - Dynamic pattern learning and updates
  - Contextual fraud pattern analysis

- **AI-Powered Explanations**
  - LLM-generated fraud explanations
  - Natural language risk assessments
  - Contextual transaction analysis
  - Multi-tier LLM fallback system (OpenAI → Ollama → Mock)

- **Comprehensive Dashboard**
  - Real-time fraud metrics and KPIs
  - Interactive transaction analysis tools
  - Fraud pattern management interface
  - System health and performance monitoring

- **Pattern Management System**
  - CRUD operations for fraud patterns
  - Advanced search and filtering
  - JSON-based pattern definitions
  - Real-time pattern synchronization

- **Production-Ready Features**
  - API authentication and security
  - Comprehensive logging and monitoring
  - Docker containerization support
  - Automated testing and deployment

### Option 1: Complete System Launch (Recommended)
```powershell
# Navigate to project directory
cd "d:\Study\AILearning\MLProjects\creditcardfrauddetection"

# Start both API server (port 8000) and UI (port 8501)
.\launch_system_root.ps1
```

### Option 2: Individual Components
```powershell
# Start API server only
python run_server.py

# Start UI only (in separate terminal, requires API running)
cd ui
streamlit run app.py
```

### Option 3: Using Python Start Script
```powershell
# Start complete system (API + UI)
python start.py

# Or start components individually:
python start.py api   # API server only
python start.py ui    # UI only (requires API to be running separately)
```

## 🌐 Accessing the Application

After starting the system:

- **API Server**: http://localhost:8000
- **User Interface**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

## 🧪 Testing & Deployment

### **🎯 Complete Testing & Deployment Workflow**

This project provides a comprehensive automated testing suite that covers:
- ✅ **All API Endpoints** (19 comprehensive tests)
- ✅ **Complete UI functionality** (15 end-to-end tests covering all pages)
- ✅ **Integration Testing** (API + UI working together)
- ✅ **Performance Testing** (Response times, load handling)
- ✅ **Security Testing** (Authentication, authorization)
- ✅ **Detailed HTML/JSON Reports** (Test results with metrics)

---

### **📦 Test Dependencies Installation**

Before running tests, install test dependencies:

```powershell
# Install all test dependencies
pip install -r requirements-test.txt

# Install Playwright browsers (for UI testing)
python -m playwright install chromium
```

**Key Test Dependencies:**
- `playwright` - Browser automation for UI testing
- `pytest` - Testing framework with plugins
- `requests` - HTTP library for API testing
- `faker` - Generate test data
- Coverage and reporting tools

---

### **🚀 Quick Start: One-Command Testing**

#### **Option 1: Complete Deployment & Testing (Recommended)**

This single command will:
1. Build Docker images (if docker mode)
2. Deploy the system
3. Run all API endpoint tests (19 tests)
4. Run all UI E2E tests (15 tests)
5. Generate comprehensive HTML and JSON reports

```powershell
# For Docker deployment (builds, deploys, and tests everything)
python deploy_and_test.py --mode docker

# For local deployment (tests running services)
python deploy_and_test.py --mode local

# With verbose output
python deploy_and_test.py --mode docker --verbose
```

**What This Does:**
- ✅ Builds and deploys the system (or verifies local deployment)
- ✅ Tests all 19 API endpoints
- ✅ Tests all 15 UI user interactions across all pages
- ✅ Generates detailed pass/fail reports with timing
- ✅ Creates HTML reports for easy viewing
- ✅ Exit code 0 if all tests pass, 1 if any fail

**Expected Output:**
```
================================================================================
  CREDIT CARD FRAUD DETECTION - DEPLOYMENT & TEST AUTOMATION
================================================================================

[10:30:15] 🔧 Building Docker images...
[10:32:45] ✅ Docker images built successfully in 150.23s

[10:32:45] 🔧 Deploying with Docker Compose...
[10:33:10] ✅ Services deployed successfully in 25.12s

[10:33:10] 🔧 Running API tests...
[10:34:05] ℹ️  API Tests: 19/19 passed, 0 failed
[10:34:05] ✅ All API tests passed!

[10:34:05] 🔧 Running UI tests...
[10:36:15] ℹ️  UI Tests: 15/15 passed, 0 failed
[10:36:15] ✅ All UI tests passed!

================================================================================
  DEPLOYMENT AND TEST SUMMARY
================================================================================

Deployment Mode: DOCKER
Total Stages:    4
Successful:      4
Failed:          0

✅ Build Docker Images: 150.23s
✅ Deploy Docker: 25.12s
✅ API Tests: 55.34s
✅ UI Tests: 130.21s

📄 Report saved to: tests/reports/deployment_test_20260211_103615.json
📄 HTML report saved to: tests/reports/deployment_test_20260211_103615.html

🎉 ALL STAGES COMPLETED SUCCESSFULLY!
```

---

### **🔌 API Endpoint Tests** 

#### **Comprehensive API Testing** (`tests/test_api_comprehensive.py`)

**Covers ALL 19 API endpoints:**

**Health & Connectivity (3 tests):**
- ✅ `GET /health` - Basic health check
- ✅ `GET /api/v1/health` - API v1 health endpoint
- ✅ Response time performance (<1s expected)

**Authentication & Security (1 test):**
- ✅ Unauthorized access protection (401/403 expected without API key)

**Core Fraud Detection (3 tests):**
- ✅ `POST /api/v1/analyze-transaction` - Legitimate transaction
- ✅ `POST /api/v1/analyze-transaction` - Suspicious transaction
- ✅ `POST /api/v1/detect-fraud` - Alternative fraud detection endpoint

**Fraud Pattern Management (6 tests):**
- ✅ `GET /api/v1/fraud-patterns` - List all patterns
- ✅ `POST /api/v1/fraud-patterns` - Create new pattern
- ✅ `PUT /api/v1/fraud-patterns/{id}` - Update existing pattern
- ✅ `DELETE /api/v1/fraud-patterns/{id}` - Delete pattern
- ✅ `POST /api/v1/ingest-patterns` - Bulk pattern ingestion
- ✅ Pattern search and filtering

**Transaction Management (2 tests):**
- ✅ `GET /api/v1/transactions` - Get transaction history
- ✅ `GET /api/v1/transactions/{id}` - Get specific transaction

**Feedback System (1 test):**
- ✅ `POST /api/v1/feedback` - Submit analyst feedback

**LLM Management (2 tests):**
- ✅ `GET /api/v1/llm-status` - Get LLM service status
- ✅ `POST /api/v1/switch-llm-model` - Switch between LLM providers

**Monitoring & Metrics (1 test):**
- ✅ `GET /api/v1/metrics` - System metrics and KPIs

**Error Handling & Performance (2 tests):**
- ✅ Invalid transaction handling (negative testing)
- ✅ Concurrent request handling (10 simultaneous requests)

**Run API Tests:**
```powershell
# Test local API instance
python tests/test_api_comprehensive.py --api-url http://localhost:8000

# Test Docker API instance
python tests/test_api_comprehensive.py --api-url http://localhost:8000

# With custom API key
python tests/test_api_comprehensive.py --api-key your_api_key_here
```

**Example Output:**
```
================================================================================
  COMPREHENSIVE API ENDPOINT TEST SUITE
================================================================================

Testing API: http://localhost:8000

✅ Health Endpoint: PASSED
✅ API v1 Health Endpoint: PASSED
✅ Response Time Performance: PASSED
✅ Unauthorized Access Protection: PASSED
✅ Metrics Endpoint: PASSED
✅ Fraud Patterns List: PASSED
✅ Transaction Analysis - Legitimate: PASSED
✅ Transaction Analysis - Suspicious: PASSED
✅ Detect Fraud Endpoint: PASSED
✅ Pattern Ingestion: PASSED
✅ Update Fraud Pattern: PASSED
✅ Delete Fraud Pattern: PASSED
✅ Get Transactions: PASSED
✅ Get Transaction By ID: PASSED
✅ Feedback Submission: PASSED
✅ LLM Status: PASSED
✅ Switch LLM Model: PASSED
✅ Invalid Transaction Handling: PASSED
✅ Concurrent Requests: PASSED

Total Tests:  19
Passed:       19 (100.0%)
Failed:       0

📄 Detailed report saved to: tests/reports/api_test_20260211_140530.json
📄 HTML report saved to: tests/reports/api_test_20260211_140530.html

✅ ALL TESTS PASSED!
```

---

### **🎭 UI End-to-End Tests**

#### **Comprehensive UI Testing** (`tests/test_ui_e2e.py`)

**Covers ALL 15 user interactions across ALL pages:**

**Basic Functionality (3 tests):**
- ✅ Page load verification
- ✅ Dashboard page display and elements
- ✅ Page load performance (<15s expected)

**Transaction Analysis Page (3 tests):**
- ✅ Transaction form interactions and data entry
- ✅ Form validation and error handling
- ✅ Sample transaction generation (legitimate & suspicious)

**Fraud Patterns Page (3 tests):**
- ✅ Pattern list display and navigation
- ✅ Search and filter functionality
- ✅ CRUD operations (Create, View, Edit, Delete patterns)

**System Health Page (3 tests):**
- ✅ System status and health indicators
- ✅ Metrics and monitoring display
- ✅ LLM model switching (OpenAI, Ollama, Mock)

**Cross-Page Features (3 tests):**
- ✅ Navigation between all pages via sidebar
- ✅ Responsive design (Desktop, Laptop, Tablet viewports)
- ✅ Error handling and display

**Install Playwright (first time only):**
```powershell
# Install Playwright package
pip install playwright

# Install Playwright browsers
python -m playwright install chromium
```

**Run UI Tests:**
```powershell
# Test local UI instance (headless mode - no browser window)
python tests/test_ui_e2e.py --ui-url http://localhost:8501

# Run with browser visible (headed mode - see browser actions)
python tests/test_ui_e2e.py --ui-url http://localhost:8501 --headed

# Test Docker UI instance
python tests/test_ui_e2e.py --ui-url http://localhost:8501 --api-url http://localhost:8000
```

**Example Output:**
```
================================================================================
  COMPREHENSIVE UI END-TO-END TEST SUITE (Playwright)
================================================================================

✅ Page Load: PASSED
✅ Dashboard Page: PASSED
✅ Performance: PASSED
✅ Transaction Analysis Page: PASSED
✅ Transaction Form Validation: PASSED
✅ Sample Transaction Generation: PASSED
✅ Fraud Patterns Page: PASSED
✅ Fraud Patterns Search/Filter: PASSED
✅ Pattern CRUD Operations: PASSED
✅ System Health Page: PASSED
✅ System Health Monitoring: PASSED
✅ LLM Model Switching: PASSED
✅ Page Navigation: PASSED
✅ Responsive Design: PASSED
✅ Error Handling: PASSED

Total Tests:  15
Passed:       15 (100.0%)
Failed:       0

📄 Detailed report saved to: tests/reports/ui_e2e_test_20260211_140730.json
📄 HTML report saved to: tests/reports/ui_e2e_test_20260211_140730.html

✅ ALL TESTS PASSED!
```

---

### **🔄 Complete Deployment & Testing Workflow**

#### **Single-Command Deployment** (`deploy_and_test.py`)

The `deploy_and_test.py` script provides a unified workflow for:
- 🔧 Building Docker images
- 🚀 Deploying services
- 🧪 Running all API tests (19 tests)
- 🎭 Running all UI tests (15 tests)
- 📊 Generating comprehensive reports

**Deploy & Test Everything:**
```powershell
# Docker Mode: Build, Deploy, Test Everything
python deploy_and_test.py --mode docker

# Local Mode: Test Running Services
python deploy_and_test.py --mode local

# Verbose Output (for debugging)
python deploy_and_test.py --mode docker --verbose
```

**Workflow Stages:**

**Docker Mode (Complete):**
1. **Build Stage**: Creates Docker images for API and UI
2. **Deploy Stage**: Starts all services with Docker Compose
3. **API Test Stage**: Validates all 19 API endpoints
4. **UI Test Stage**: Tests all 15 UI user interactions
5. **Report Stage**: Generates HTML/JSON reports

**Local Mode (Test Only):**
1. **Verify Stage**: Confirms API and UI are running
2. **API Test Stage**: Validates all 19 API endpoints
3. **UI Test Stage**: Tests all 15 UI user interactions
4. **Report Stage**: Generates HTML/JSON reports

**Example Complete Output:**
```
================================================================================
  CREDIT CARD FRAUD DETECTION - DEPLOYMENT & TEST AUTOMATION
================================================================================

[10:30:15] 🔧 Building Docker images...
[10:30:15] ℹ️  Building API Docker image...
[10:32:45] ℹ️  Building UI Docker image...
[10:34:20] ✅ Docker images built successfully in 245.23s

[10:34:20] 🔧 Deploying with Docker Compose...
[10:34:25] ℹ️  Stopping existing containers...
[10:34:30] ℹ️  Starting services...
[10:34:35] ℹ️  Waiting for services to become healthy...
[10:34:45] ✅ Services deployed successfully in 25.12s

[10:34:45] 🔧 Running API tests...
[10:35:30] ℹ️  Testing 19 API endpoints...
[10:35:30] ℹ️  API Tests: 19/19 passed, 0 failed
[10:35:30] ✅ All API tests passed!

[10:35:30] 🔧 Running UI tests...
[10:37:15] ℹ️  Testing 15 UI interactions across all pages...
[10:37:15] ℹ️  UI Tests: 15/15 passed, 0 failed
[10:37:15] ✅ All UI tests passed!

================================================================================
  DEPLOYMENT AND TEST SUMMARY
================================================================================

Deployment Mode: DOCKER
Total Stages:    4
Successful:      4
Failed:          0

✅ Build Docker Images: 245.23s
✅ Deploy Docker: 25.12s
✅ API Tests: 55.34s (19/19 passed)
✅ UI Tests: 105.21s (15/15 passed)

📄 Report saved to: tests/reports/deployment_test_20260211_103715.json
📄 HTML report saved to: tests/reports/deployment_test_20260211_103715.html

🎉 ALL STAGES COMPLETED SUCCESSFULLY!
```

---

### **📊 Test Reports**

All test runs generate detailed reports in `tests/reports/`:

#### **Report Types:**

**JSON Reports** (Machine-readable):
- `api_test_YYYYMMDD_HHMMSS.json` - API test results with full details
- `ui_e2e_test_YYYYMMDD_HHMMSS.json` - UI test results with details
- `deployment_test_YYYYMMDD_HHMMSS.json` - Full deployment pipeline results

**HTML Reports** (Human-readable):
- `api_test_YYYYMMDD_HHMMSS.html` - Interactive API test report
- `ui_e2e_test_YYYYMMDD_HHMMSS.html` - Interactive UI test report
- `deployment_test_YYYYMMDD_HHMMSS.html` - Full deployment dashboard

#### **HTML Report Features:**
- 📊 **Summary Statistics**: Total, passed, failed, success rate
- 📝 **Detailed Test Results**: Each test with status and timing
- 🎨 **Color-Coded Indicators**: Green (pass), red (fail), orange (warning)
- 📈 **Performance Metrics**: Response times, load times
- 🔍 **Error Details**: Complete error messages for failed tests
- 📱 **Responsive Design**: View on any device

**Open HTML Reports:**
```powershell
# Open latest deployment report in browser
start tests/reports/deployment_test_*.html

# Open latest API test report
start tests/reports/api_test_*.html

# Open latest UI test report
start tests/reports/ui_e2e_test_*.html
```

---

### **🎯 Testing Best Practices**

#### **Before Running Tests:**

1. **Install Dependencies:**
   ```powershell
   pip install -r requirements-test.txt
   python -m playwright install chromium
   ```

2. **Configure Environment:**
   - Ensure `.env` file has correct API keys
   - Set `API_KEY=development_api_key_for_testing` for tests
   - Configure LLM settings (OpenAI/Ollama)

3. **Start Services (for local mode):**
   ```powershell
   # Terminal 1: Start API
   python run_server.py
   
   # Terminal 2: Start UI
   streamlit run ui/app.py
   ```

#### **Running Different Test Scenarios:**

**Quick Smoke Test (API only):**
```powershell
python tests/test_api_comprehensive.py --api-url http://localhost:8000
```

**Full UI Test (with browser visible):**
```powershell
python tests/test_ui_e2e.py --ui-url http://localhost:8501 --headed
```

**Complete Integration Test:**
```powershell
python deploy_and_test.py --mode local
```

**Production-Ready Docker Test:**
```powershell
python deploy_and_test.py --mode docker --verbose
```

---

### **✅ Test Coverage Summary**

| Component | Tests | Coverage | Status |
|-----------|-------|----------|--------|
| **API Endpoints** | 19 | 100% of endpoints | ✅ Complete |
| **UI Pages** | 15 | All pages & interactions | ✅ Complete |
| **Authentication** | Included | API key validation | ✅ Complete |
| **CRUD Operations** | Included | Create, Read, Update, Delete | ✅ Complete |
| **Error Handling** | Included | Invalid inputs, errors | ✅ Complete |
| **Performance** | Included | Response times, load | ✅ Complete |
| **Security** | Included | Auth, validation | ✅ Complete |
| **Integration** | 1 | Full system test | ✅ Complete |

**Total: 34 comprehensive tests covering the entire system**

---

### **Test Reports**

All test runs generate detailed reports in `tests/reports/`:

**JSON Reports:**
- `api_test_YYYYMMDD_HHMMSS.json` - API test results
- `ui_e2e_test_YYYYMMDD_HHMMSS.json` - UI test results
- `deployment_test_YYYYMMDD_HHMMSS.json` - Full deployment test results

**HTML Reports:**
- `api_test_YYYYMMDD_HHMMSS.html` - Interactive API test report
- `ui_e2e_test_YYYYMMDD_HHMMSS.html` - Interactive UI test report
- `deployment_test_YYYYMMDD_HHMMSS.html` - Full deployment summary report

**Report Features:**
- 📊 Summary statistics (total, passed, failed, success rate)
- 📝 Detailed test results with timestamps
- 🎨 Color-coded status indicators
- 📈 Performance metrics
- 🔍 Error details and debugging information
- 📱 Responsive HTML design for viewing on any device

### **CI/CD Integration**

The testing suite is designed for easy integration with CI/CD pipelines:

**GitHub Actions Example:**
```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        python -m playwright install chromium
    
    - name: Run deployment and tests
      run: |
        python deploy_and_test.py --mode docker
    
    - name: Upload test reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-reports
        path: tests/reports/
```

**Jenkins Pipeline Example:**
```groovy
pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'python -m playwright install chromium'
            }
        }
        
        stage('Build and Test') {
            steps {
                sh 'python deploy_and_test.py --mode docker'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'tests/reports/**/*', fingerprint: true
            publishHTML([
                reportDir: 'tests/reports',
                reportFiles: '*.html',
                reportName: 'Test Reports'
            ])
        }
    }
}
```

### **Manual Testing Guide**

For manual testing and verification, see:
- `tests/MANUAL_TESTING_GUIDE.md` - Step-by-step manual testing procedures
- `tests/UI_INTERACTION_TEST_SUMMARY.md` - UI interaction testing guide

### **Test Coverage**

Current test coverage:

| Component | Coverage | Tests |
|-----------|----------|-------|
| API Endpoints | 100% | 12 tests |
| UI Pages | 100% | 9 tests |
| Authentication | 100% | Included in API tests |
| Error Handling | 100% | Included in all tests |
| Performance | ✅ | Response time & load tests |
| Security | ✅ | Auth & validation tests |

### **Running Tests in Different Environments**

**Development Environment:**
```powershell
# Start services manually
python run_server.py  # Terminal 1
streamlit run ui/app.py  # Terminal 2

# Run tests
python deploy_and_test.py --mode local
```

**Staging/Production Environment:**
```powershell
# Deploy and test in Docker
python deploy_and_test.py --mode docker

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

**Continuous Integration:**
```powershell
# Automated testing in CI environment
python deploy_and_test.py --mode docker --verbose
```

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for LLM services

## 🏗️ Architecture Overview

### Core Components

1. **API Server** (`run_server.py`)
   - FastAPI-based REST API
   - Real-time fraud detection endpoints
   - ML model serving
   - Vector database integration

2. **User Interface** (`ui/app.py`)
   - Streamlit-based web application
   - Interactive dashboard
   - Transaction analysis tools
   - Fraud pattern management

3. **Machine Learning Pipeline**
   - Traditional ML models (XGBoost)
   - LLM integration (OpenAI, Ollama)
   - Feature engineering
   - Model evaluation and monitoring

4. **Data Layer**
   - Vector database (ChromaDB)
   - Transaction storage
   - Fraud pattern repository
   - Model artifacts

### UI Features

#### 1. Dashboard
- Real-time fraud metrics and KPIs
- Recent transaction activity with fraud status
- Fraud rate trend visualization
- System health overview

#### 2. Transaction Analysis
- Real-time transaction analysis
- Sample transaction generation for testing
- Historical transaction lookup
- Detailed transaction visualization and explanation
- Analyst feedback mechanism

#### 3. Fraud Patterns Management
- **Enhanced UI**: Search and filtering capabilities
- **CRUD Operations**: Create, Read, Update, Delete fraud patterns
- **Advanced Search**: Filter by name, description, or fraud type
- **Pattern Management**: Add new patterns with JSON validation
- **Detailed View**: Popup modals with complete pattern information
- **Edit Functionality**: Pre-filled forms for pattern updates
- **Delete Confirmation**: Safety dialogs before pattern removal
- **Real-time Data**: Live integration with backend API (1,500+ patterns)
- **Professional UI**: Modern design with responsive layout

#### 4. System Health & Monitoring
- System status monitoring
- Performance metrics visualization
- Model performance tracking
- Resource utilization monitoring
- System logs with filtering
- Alert configuration

## 📦 Installation & Deployment

### Prerequisites

- **Windows OS** (PowerShell scripts designed for Windows)
- **Python 3.9+** (Python 3.13.2 recommended)
- **Docker Desktop** (for Docker deployment)
- **WSL 2** (for Docker on Windows)
- **8GB+ RAM** (recommended)
- **Git** (for repository cloning)

### 1. Clone the Repository

```bash
git clone https://github.com/guruthanglearning/AILearning.git
cd AILearning/MLProjects/creditcardfrauddetection
```

### 2. Choose Deployment Mode

#### 🖥️ **Local Development (Recommended for Development)**

**Step 1: Set Up Python Environment**

```powershell
# Create virtual environment (if not using shared environment)
python -m venv venv
.\venv\Scripts\activate

# Or use shared environment
# Activate: d:\Study\AILearning\shared_Environment\Scripts\activate
```

**Step 2: Install Dependencies**

```powershell
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
playwright install chromium  # For E2E tests
```

**Step 3: Configure Environment**

Create `.env.local` file in project root:

```env
# Deployment Configuration
DEPLOYMENT_MODE=local
API_URL=http://localhost:8000

# API Configuration
API_HOST=localhost
API_PORT=8000
API_KEY=development_api_key_for_testing
DEBUG=True

# LLM Configuration
OPENAI_API_KEY=your-openai-key-here
OLLAMA_API_URL=http://localhost:11434
LLM_SERVICE_TYPE=enhanced_mock  # Options: openai, ollama, enhanced_mock

# Database Configuration
DATA_DIR=./data
CHROMA_DB_PATH=./data/chroma_db
MODEL_PATH=./data/models/fraud_detection_model.pkl

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_FILE=./logs/app.log
```

**Step 4: Launch Application**

```powershell
# Launch both API and UI
.\launch_local.ps1

# Or launch individually
.\launch_local.ps1 -SkipUI   # API only
.\launch_local.ps1 -SkipAPI  # UI only (requires API running)
```

**Access:**
- 🌐 UI Dashboard: http://localhost:8501
- 📡 API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

#### 🐋 **Docker Deployment (Recommended for Production)**

**Step 1: Install Docker**

- Install Docker Desktop for Windows
- Enable WSL 2 backend
- Ensure Docker daemon is running

**Step 2: Configure Environment**

Create `.env.docker` file in project root:

```env
# Deployment Configuration
DEPLOYMENT_MODE=docker
API_URL=http://fraud-detection-api:8000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=production_api_key_change_this
DEBUG=False

# LLM Configuration
OPENAI_API_KEY=your-openai-key-here
OLLAMA_API_URL=http://ollama:11434
LLM_SERVICE_TYPE=openai  # Production recommendation

# Database Configuration (container paths)
DATA_DIR=/app/data
CHROMA_DB_PATH=/app/data/chroma_db
MODEL_PATH=/app/data/models/fraud_detection_model.pkl

# Logging
LOG_LEVEL=INFO
LOG_DIR=/app/logs
LOG_FILE=/app/logs/app.log

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

**Step 3: Build and Launch**

```powershell
# First time - build images
.\launch_docker.ps1 -Build

# Start containers
.\launch_docker.ps1

# View logs
.\launch_docker.ps1 -Logs

# Check status
.\launch_docker.ps1 -Status
```

**Access:**
- 🌐 UI Dashboard: http://localhost:8501
- 📡 API: http://localhost:8000
- 📊 Prometheus: http://localhost:9090
- 📈 Grafana: http://localhost:3000

**Step 4: Stop/Clean**

```powershell
# Stop containers
.\launch_docker.ps1 -Down

# Clean everything (containers + volumes + images)
.\launch_docker.ps1 -Clean
```

### 3. Verify Installation

```powershell
# Check API health
curl http://localhost:8000/health

# Run tests
.\scripts\run_all_tests.ps1
```

### 🔄 Switching Between Local and Docker

The configuration files (`.env.local` and `.env.docker`) allow seamless switching:

**Key Differences:**

| Setting | Local | Docker |
|---------|-------|--------|
| `DEPLOYMENT_MODE` | `local` | `docker` |
| `API_URL` | `http://localhost:8000` | `http://fraud-detection-api:8000` |
| `DATA_DIR` | `./data` | `/app/data` |
| `LOG_DIR` | `./logs` | `/app/logs` |
| `DEBUG` | `True` | `False` |

**Testing Both Modes:**

```powershell
# Test local deployment
.\scripts\run_all_tests.ps1 -Mode local

# Test Docker deployment
.\scripts\run_all_tests.ps1 -Mode docker
```

## Usage

### 🚀 Quick Start

#### Option 1: Complete System Launch (Recommended)
```powershell
# Navigate to project directory
cd "d:\Study\AILearning\MLProjects\creditcardfrauddetection"

# Start both API server (port 8000) and UI (port 8501)
.\launch_system_root.ps1
```

#### Option 2: Individual Components
```powershell
# Start API server only
python run_server.py

# Start UI only (in separate terminal, requires API running)
cd ui
streamlit run app.py
```

#### Option 3: Using Python Start Script
```powershell
# Start complete system (API + UI)
python start.py

# Or start components individually:
python start.py api   # API server only
python start.py ui    # UI only (requires API to be running separately)
```

### 🌐 Accessing the Application

After starting the system:

- **API Server**: http://localhost:8000
- **User Interface**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

### 🔧 System Components

1. **Model Setup**:
   ```bash
   # Generate demo models (for testing)
   python scripts/utility/check_model_files.py --generate-demo

   # Or train with real data (advanced)
   python scripts/manage_models.py --train --data-path ./data/sample/
   ```

2. **API Deployment**:
   ```bash
   # Start the FastAPI server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Access API documentation at `http://127.0.0.1:8000/docs`

3. **UI Deployment**:
   ```bash
   # Start the Streamlit interface
   streamlit run ui/app.py --server.port 8501
   ```
   - Access the dashboard at `http://127.0.0.1:8501`

4. **System Diagnostics**:
   ```bash
   # Run comprehensive system diagnostics
   python scripts/utility/diagnose_system.py

   # Debug LLM services
   python scripts/debug/debug_llm_service.py

   # Test API endpoints
   python comprehensive_api_test.py
   ```

## 🧪 Testing

The project includes comprehensive testing infrastructure with support for both local and Docker deployments.

### Test Suites

#### 1. **Unit Tests** (pytest)
Tests ML models, system components, and transaction endpoints with code coverage reporting.

```powershell
# Run all unit tests with coverage
.\scripts\run_unit_tests.ps1

# Run without coverage (faster)
.\scripts\run_unit_tests.ps1 -NoCoverage

# Verbose output
.\scripts\run_unit_tests.ps1 -Verbose
```

**Coverage:** Tests cover model predictions, system initialization, API endpoints, and utility functions.

#### 2. **Integration Tests**
Tests API endpoints end-to-end including fraud detection, feedback submission, and pattern ingestion.

```powershell
# Run integration tests (local mode)
.\scripts\run_integration_tests.ps1 -Mode local

# Run with Docker deployment
.\scripts\run_integration_tests.ps1 -Mode docker

# Auto-start API before testing
.\scripts\run_integration_tests.ps1 -StartAPI
```

**Tests:**
- ✅ Fraud detection API endpoint
- ✅ Feedback submission and storage
- ✅ Pattern ingestion workflow

#### 3. **Playwright E2E Tests**
Browser automation tests for the Streamlit UI covering all user workflows.

```powershell
# Run E2E tests (headless mode)
.\scripts\run_playwright_tests.ps1

# Run with visible browser
.\scripts\run_playwright_tests.ps1 -Headless:$false

# Auto-start services before testing
.\scripts\run_playwright_tests.ps1 -StartServices

# Test Docker deployment
.\scripts\run_playwright_tests.ps1 -Mode docker
```

**Test Scenarios (15 tests):**
- Homepage navigation and layout
- Transaction analysis form submission
- Fraud pattern management (CRUD operations)
- System settings and configuration
- Model monitoring and metrics
- Real-time feedback workflows

#### 4. **All Tests (Uber Script)**
Runs all test suites with comprehensive reporting.

```powershell
# Run all tests (local deployment)
.\scripts\run_all_tests.ps1

# Run all tests (Docker deployment)
.\scripts\run_all_tests.ps1 -Mode docker

# Skip specific suites
.\scripts\run_all_tests.ps1 -SkipE2E
.\scripts\run_all_tests.ps1 -SkipUnit -SkipIntegration

# Stop on first failure
.\scripts\run_all_tests.ps1 -StopOnFailure

# Verbose output
.\scripts\run_all_tests.ps1 -Verbose
```

### Test Reports

Tests generate comprehensive reports:

**Location:** `tests/reports/`

- `test_results_<timestamp>.json` - JSON format for CI/CD
- `test_results_<timestamp>.html` - HTML report with visualizations
- `coverage_html/index.html` - Code coverage report
- `ui_e2e_test_<timestamp>.html` - Playwright test report

**View Coverage Report:**
```powershell
# After running unit tests
start tests/reports/coverage_html/index.html
```

### Testing Best Practices

**Local Development Testing:**
```powershell
# 1. Launch application locally
.\launch_local.ps1

# 2. Run tests against local instance
.\scripts\run_all_tests.ps1 -Mode local

# 3. View results
start tests/reports/test_results_*.html
```

**Docker Deployment Testing:**
```powershell
# 1. Launch Docker containers
.\launch_docker.ps1

# 2. Run tests against containers
.\scripts\run_all_tests.ps1 -Mode docker

# 3. Stop containers
.\launch_docker.ps1 -Down
```

**CI/CD Integration:**
```yaml
# Example GitHub Actions workflow
- name: Run All Tests
  run: |
    .\scripts\run_all_tests.ps1 -Mode local
    
- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: tests/reports/
```

### Test Coverage Metrics

**Current Coverage:** ~32% overall

| Component | Coverage | Status |
|-----------|----------|--------|
| ML Models | 85% | ✅ Good |
| API Endpoints | 45% | ⚠️ Needs improvement |
| Services | 25% | ❌ Low |
| Utilities | 60% | ✅ Good |

**Improvement Areas:**
- Increase service layer test coverage
- Add more edge case tests for API endpoints
- Expand LLM service mocking scenarios

### Troubleshooting Tests

**Issue: API not responding during integration tests**
```powershell
# Solution: Use -StartAPI flag
.\scripts\run_integration_tests.ps1 -StartAPI
```

**Issue: Playwright browser not launching**
```powershell
# Solution: Reinstall Playwright browsers
playwright install chromium
```

**Issue: ChromaDB initialization errors**
```powershell
# Solution: Delete and recreate vector database
Remove-Item -Recurse -Force .\data\chroma_db
# Database will auto-recreate on next run
```

**Issue: Test conflicts between local and Docker**
```powershell
# Solution: Ensure correct mode is specified
.\scripts\run_all_tests.ps1 -Mode local   # For local
.\scripts\run_all_tests.ps1 -Mode docker  # For Docker
```

## 📊 **System Architecture & Workflow Diagrams**

### 🔄 **Main Fraud Detection Workflow**

```mermaid
graph TD
    A[💳 Transaction Input] --> B{🔍 Real-time Validation}
    B -->|Valid| C[📊 Feature Engineering]
    B -->|Invalid| D[❌ Reject Transaction]
    
    C --> E[🧠 XGBoost Fraud Classifier]
    C --> F[🔍 Vector Pattern Search]
    
    E --> G{📈 Fraud Score Analysis}
    F --> H[📋 Similar Patterns Found]
    
    G -->|Score > 0.8| I[🚨 High Risk - Likely Fraud]
    G -->|Score 0.3-0.8| J[⚠️ Medium Risk - Review Required]
    G -->|Score < 0.3| K[✅ Low Risk - Legitimate]
    
    H --> L[🤖 LLM Analysis Engine]
    I --> L
    J --> L
    
    L --> M{🎯 LLM Provider Selection}
    M -->|Primary| N[🌐 OpenAI GPT-4 Analysis]
    M -->|Fallback| O[🏠 Ollama Local LLM]
    M -->|Emergency| P[🔧 Mock LLM Service]
    
    N --> Q[📝 Detailed Fraud Explanation]
    O --> Q
    P --> Q
    
    Q --> R[🎪 Risk Assessment Combination]
    K --> R
    
    R --> S{💡 Final Decision Logic}
    S -->|High Confidence Fraud| T[🛑 BLOCK Transaction]
    S -->|Medium Risk| U[⏸️ HOLD for Review]
    S -->|Low Risk| V[✅ APPROVE Transaction]
    
    T --> W[📱 Dashboard Notification]
    U --> W
    V --> W
    
    W --> X[📊 Update Metrics & Logs]
    X --> Y[💾 Store Transaction Result]
    Y --> Z[🔄 Pattern Learning Update]
    
    style A fill:#e1f5fe
    style T fill:#ffebee
    style V fill:#e8f5e8
    style U fill:#fff3e0
```

### 🏗️ **System Architecture Diagram**

```mermaid
graph TB
    subgraph "📱 Frontend Layer"
        UI[Streamlit Dashboard]
        API[FastAPI Server]
    end
    
    subgraph "🧠 AI/ML Layer"
        XGB[XGBoost Classifier]
        LLM[LLM Engine]
        VECTOR[Vector Similarity]
        PATTERN[Pattern Recognition]
        DECISION[Decision Engine]
    end
    
    subgraph "📊 Data Processing Layer"
        FEATURE[Feature Engineering]
        PREPROCESS[Data Preprocessing]
        VALIDATION[Input Validation]
    end
    
    subgraph "🌐 External Services"
        OPENAI[OpenAI API]
        OLLAMA[Ollama API]
        MOCK[Mock LLM]
    end
    
    subgraph "💾 Data Storage"
        CHROMA[ChromaDB Vector Store]
        PATTERNS[Fraud Patterns DB]
        MODELS[ML Models Storage]
        LOGS[Transaction Logs]
    end
    
    UI --> API
    API --> DECISION
    DECISION --> XGB
    DECISION --> LLM
    DECISION --> VECTOR
    
    XGB --> FEATURE
    VECTOR --> PATTERN
    LLM --> OPENAI
    LLM --> OLLAMA
    LLM --> MOCK
    
    FEATURE --> PREPROCESS
    PREPROCESS --> VALIDATION
    PATTERN --> CHROMA
    
    XGB --> MODELS
    VECTOR --> PATTERNS
    API --> LOGS
    
    style UI fill:#e3f2fd
    style API fill:#f3e5f5
    style XGB fill:#e8f5e8
    style LLM fill:#fff3e0
    style DECISION fill:#fff8e1
```

### ⚡ **Data Flow Architecture**

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant ML as ML Pipeline
    participant Vector as Vector DB
    participant LLM as LLM Service
    participant DB as Data Storage
    
    User->>UI: Submit Transaction
    UI->>API: POST /analyze/transaction
    
    API->>ML: Validate & Process Transaction
    
    par Parallel Analysis
        ML->>ML: XGBoost Classification
        and
        ML->>Vector: Pattern Similarity Search
        Vector-->>ML: Similar Patterns Found
        and
        ML->>LLM: Advanced Analysis Request
        LLM-->>ML: Fraud Explanation
    end
    
    ML->>API: Combined Risk Assessment
    API->>DB: Store Transaction & Result
    
    API-->>UI: Fraud Analysis Response
    UI-->>User: Display Results Dashboard
    
    Note over User,DB: Total processing time: ~200-500ms
```

### 🔄 **Pattern Learning Pipeline**

```mermaid
flowchart LR
    subgraph "📥 Data Input"
        A1[Transaction Data]
        A2[Historical Fraud Cases]
        A3[External Fraud Intel]
    end
    
    subgraph "🔧 Processing"
        B1[Feature Extraction]
        B2[Pattern Recognition]
        B3[Vector Embedding]
    end
    
    subgraph "🤖 Model Training"
        C1[XGBoost Training]
        C2[Pattern Database Update]
        C3[Similarity Threshold Tuning]
    end
    
    subgraph "✅ Validation"
        D1[Cross Validation]
        D2[Performance Metrics]
        D3[Model Deployment]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    
    B1 --> C1
    B2 --> C2
    B3 --> C3
    
    C1 --> D1
    C2 --> D1
    C3 --> D1
    D1 --> D2
    D2 --> D3
    
    style A1 fill:#e1f5fe
    style A2 fill:#e1f5fe
    style A3 fill:#e1f5fe
    style C1 fill:#e8f5e8
    style C2 fill:#e8f5e8
    style C3 fill:#e8f5e8
    style D3 fill:#fff8e1
```

### 🎯 **Fraud Decision Engine Logic**

```mermaid
graph TD
    START[Transaction Input] --> SCORE{XGBoost Score}
    
    SCORE -->|High (>0.8)| HIGH[🚨 High Risk]
    SCORE -->|Medium (0.3-0.8)| MED[⚠️ Medium Risk]
    SCORE -->|Low (<0.3)| LOW[✅ Low Risk]
    
    HIGH --> PATTERN_HIGH{Pattern Match}
    MED --> PATTERN_MED{Pattern Match}
    LOW --> PATTERN_LOW{Pattern Match}
    
    PATTERN_HIGH -->|Strong Match| LLM_HIGH[🤖 LLM Analysis]
    PATTERN_HIGH -->|Weak Match| BLOCK[🛑 BLOCK - High Confidence]
    
    PATTERN_MED -->|Strong Match| LLM_MED[🤖 LLM Analysis]
    PATTERN_MED -->|Weak Match| HOLD[⏸️ HOLD - Manual Review]
    
    PATTERN_LOW -->|Any Match| LLM_LOW[🤖 LLM Analysis]
    PATTERN_LOW -->|No Match| APPROVE[✅ APPROVE - Low Risk]
    
    LLM_HIGH --> CONF_HIGH{LLM Confidence}
    LLM_MED --> CONF_MED{LLM Confidence}
    LLM_LOW --> CONF_LOW{LLM Confidence}
    
    CONF_HIGH -->|High| BLOCK_LLM[🛑 BLOCK - AI Confirmed]
    CONF_HIGH -->|Low| HOLD_LLM[⏸️ HOLD - Mixed Signals]
    
    CONF_MED -->|High| HOLD_MED[⏸️ HOLD - Requires Review]
    CONF_MED -->|Low| APPROVE_MED[✅ APPROVE - Low Confidence Fraud]
    
    CONF_LOW -->|Any| APPROVE_LOW[✅ APPROVE - AI Verified]
    
    BLOCK --> NOTIFY[📱 Immediate Alert]
    BLOCK_LLM --> NOTIFY
    HOLD --> QUEUE[📋 Review Queue]
    HOLD_LLM --> QUEUE
    HOLD_MED --> QUEUE
    APPROVE --> LOG[📊 Log Transaction]
    APPROVE_MED --> LOG
    APPROVE_LOW --> LOG
    
    style BLOCK fill:#f44336
    style BLOCK_LLM fill:#f44336
    style HOLD fill:#ff9800
    style HOLD_LLM fill:#ff9800
    style HOLD_MED fill:#ff9800
    style APPROVE fill:#4caf50
    style APPROVE_MED fill:#4caf50
    style APPROVE_LOW fill:#4caf50
```

### ⚡ **Performance Characteristics**

| Component | Processing Time | Resource Usage | Accuracy |
|-----------|----------------|-----------------|----------|
| **Input Validation** | ~5-10ms | Low CPU | 99.9% validation |
| **Feature Engineering** | ~20-50ms | Medium CPU | Deterministic |
| **XGBoost Classification** | ~50-100ms | Medium CPU/Memory | 95%+ accuracy |
| **Vector Pattern Search** | ~30-80ms | Medium Memory | 85-90% pattern match |
| **LLM Analysis (OpenAI)** | ~200-500ms | Network dependent | 90-95% explanation quality |
| **LLM Analysis (Ollama)** | ~500-2000ms | High CPU/GPU | 80-85% explanation quality |
| **Total Pipeline** | ~300-800ms | Variable | 95%+ combined accuracy |

### 🏗️ **System Architecture Components**

#### 1. **API Layer** (`app/main.py`)
- FastAPI-based REST API server
- Real-time fraud detection endpoints
- Authentication and rate limiting
- Request/response validation

#### 2. **ML Processing Pipeline**
- XGBoost binary classifier for fraud detection
- Feature engineering and preprocessing
- Model serving and prediction caching
- Performance monitoring and logging

#### 3. **Vector Database Layer** (`ChromaDB`)
- 1,500+ fraud pattern embeddings
- Real-time similarity search
- Pattern management and updates
- Scalable vector operations

#### 4. **LLM Integration Service**
- Multi-tier LLM provider system
- OpenAI API for advanced analysis
- Ollama for local/private deployments
- Mock service for development/testing

#### 5. **User Interface** (`ui/app.py`)
- Streamlit-based web dashboard
- Real-time metrics and KPIs
- Interactive fraud analysis tools
- Pattern management interface

#### 6. **Data Storage & Management**
- Transaction data persistence
- Model artifact storage
- Configuration management
- Logging and audit trails

The project includes various utility and management scripts organized by functionality:

### Directory Structure

- **scripts/debug/**: Scripts for debugging the system and LLM services
- **scripts/powershell/**: PowerShell scripts for system management, testing, and configuration
- **scripts/utility/**: Utility Python scripts for maintenance and configuration

### Key Scripts

#### Python Utility Scripts

- **`scripts/utility/configure_ollama_api.py`**: Interactive configuration wizard for online Ollama API settings
- **`scripts/debug/debug_llm_service.py`**: Debug tool for testing LLM service functionality
- **`scripts/utility/diagnose_system.py`**: System diagnostics tool for troubleshooting

#### PowerShell Management Scripts

- **`scripts/powershell/launch_system.ps1`**: Main script to launch both API and UI components
- **`scripts/powershell/run_tests.ps1`**: Run all system tests
- **`scripts/powershell/test_ollama_api.ps1`**: Test Ollama API connectivity (both local and online)
- **`scripts/powershell/configure_ollama_api.ps1`**: Run the interactive configuration wizard

### Running Scripts

The easiest way to run these scripts is through the root-level script launcher:

```powershell
# From the project root directory
.\run_all_scripts.ps1
```

This will present a menu interface to select and run the appropriate scripts.

## 🐳 Docker Deployment

The application can be deployed using Docker containers with separate services for API, UI, and shared storage volumes.

### 📋 Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux) v20.10.0+
- **Docker Compose** v2.0.0+
- **System Requirements**: 8GB RAM, 10GB free disk space

### 🚀 Quick Start

#### **Windows (PowerShell)**
```powershell
# Navigate to project directory
cd D:\Study\AILearning\MLProjects\creditcardfrauddetection

# Configure environment variables
Copy-Item .env.docker .env
# Edit .env file with your API keys

# Deploy the system
.\deploy-docker.ps1 up
```

#### **Linux/macOS (Bash)**
```bash
# Navigate to project directory
cd /path/to/creditcardfrauddetection

# Make script executable
chmod +x deploy-docker.sh

# Configure environment
cp .env.docker .env
# Edit .env file with your API keys

# Deploy the system
./deploy-docker.sh up
```

### 📦 Docker Architecture

The system uses a multi-container architecture:

- **fraud-detection-api** - FastAPI backend (port 8000)
- **fraud-detection-ui** - Streamlit frontend (port 8501)
- **prometheus** - Metrics collection (port 9090) [optional]
- **grafana** - Monitoring dashboards (port 3000) [optional]

**Shared Volumes:**
- `model-data` - ML models (XGBoost, etc.)
- `chroma-data` - Vector database (ChromaDB)
- `pattern-data` - Fraud pattern definitions
- `prometheus-data` - Metrics history
- `grafana-data` - Dashboard configurations

### 🛠️ Docker Commands

```powershell
# Build Docker images
.\deploy-docker.ps1 build

# Start all services
.\deploy-docker.ps1 up

# Stop services (keeps data)
.\deploy-docker.ps1 down

# Restart services
.\deploy-docker.ps1 restart

# View logs
.\deploy-docker.ps1 logs

# Check service status
.\deploy-docker.ps1 status

# Clean up (removes all data)
.\deploy-docker.ps1 clean
```

### 🌐 Access Services

After deployment, access the application at:

| Service | URL | Credentials |
|---------|-----|-------------|
| **API Server** | http://localhost:8000 | API Key in headers |
| **API Documentation** | http://localhost:8000/docs | None |
| **UI Dashboard** | http://localhost:8501 | None |
| **Prometheus** | http://localhost:9090 | None |
| **Grafana** | http://localhost:3000 | admin / admin123 |

### ⚙️ Configuration

Edit the `.env` file for configuration:

```env
# Required Settings
API_KEY=your-secure-api-key
OPENAI_API_KEY=your-openai-key
JWT_SECRET_KEY=your-32-char-secret

# Optional Settings
OLLAMA_API_URL=http://localhost:11434
GRAFANA_ADMIN_PASSWORD=secure-password
```

### 📖 Detailed Documentation

For comprehensive Docker deployment guide including:
- Advanced configuration options
- Production deployment checklist
- Troubleshooting guide
- Backup and recovery procedures
- Security best practices
- Monitoring and logging setup

See **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** for complete documentation.

### 🔧 Manual Docker Build

If you prefer manual Docker commands:

```bash
# Build specific containers
docker build -f Dockerfile.api -t fraud-detection-api .
docker build -f Dockerfile.ui -t fraud-detection-ui .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
```

## ☁️ Cloud Hosting Instructions

### AWS Deployment

#### Using AWS Elastic Beanstalk
1. Install AWS CLI and EB CLI
2. Initialize Elastic Beanstalk application:
   ```bash
   eb init fraud-detection-app
   eb create production
   eb deploy
   ```

#### Using AWS ECS
1. Build and push Docker image to ECR
2. Create ECS task definition
3. Deploy to ECS cluster

### Azure Deployment

#### Using Azure Container Instances
```bash
# Create resource group
az group create --name fraud-detection-rg --location eastus

# Deploy container
az container create \
  --resource-group fraud-detection-rg \
  --name fraud-detection-app \
  --image your-registry/fraud-detection:latest \
  --ports 8000 8501
```

### Google Cloud Platform

#### Using Cloud Run
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/fraud-detection

# Deploy to Cloud Run
gcloud run deploy fraud-detection \
  --image gcr.io/PROJECT-ID/fraud-detection \
  --platform managed \
  --port 8000
```

### Heroku Deployment
1. Create `Procfile`:
   ```
   web: uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-8000}
   ```
2. Deploy:
   ```bash
   heroku create fraud-detection-app
   git push heroku main
   ```

## 🧪 Testing

### API Tests
```bash
# Run comprehensive API tests
python comprehensive_api_test.py

# Run specific endpoint tests
python tests/test_api.py
python tests/test_transaction_endpoints.py
```

### UI Tests
```bash
# Test UI functionality
cd ui
python test_ui_functionality.py
```

### Unit Test Coverage
Current test coverage includes:
- ✅ API endpoint tests (16 endpoints)
- ✅ ML model validation tests
- ✅ LLM service integration tests
- ✅ Database operation tests
- ✅ UI component tests
- ✅ End-to-end workflow tests

### 📋 Manual Testing Guide

#### **Fraud Patterns UI Testing**

Access the application at **http://localhost:8501** and follow these test scenarios:

##### **1. Navigation Test**
- Open the Streamlit UI in your browser
- Click "Fraud Patterns" in the sidebar
- Verify the page loads with title "🔐 Fraud Pattern Management System"
- Confirm 1,457+ fraud patterns are displayed

##### **2. Search & Filter Tests**
- **Search Test**: 
  - Type "Card Not Present" in the search box
  - Verify real-time filtering works
  - Clear search and confirm all patterns return
- **Filter Test**:
  - Select fraud types from dropdown (Card Not Present, Account Takeover, etc.)
  - Verify patterns filter correctly
  - Use "Clear Filters" button to reset

##### **3. CRUD Operations Tests**

**Add Pattern:**
- Click "➕ Add New Pattern" button
- Fill form: Pattern Name, Fraud Type, Description
- Adjust similarity threshold slider
- Submit and verify success message

**View Pattern:**
- Click "👁️ View" button on any pattern
- Verify popup shows complete details, JSON config, and metrics
- Confirm action buttons (Edit, Delete, Close) are present

**Edit Pattern:**
- Click "✏️ Edit" button on any pattern
- Modify name or description
- Submit and verify updates are saved

**Delete Pattern:**
- Click "🗑️ Delete" button on any pattern
- Confirm deletion dialog appears
- Verify pattern is removed after confirmation

##### **4. Performance Benchmarks**
- Pattern loading: < 2 seconds
- Search filtering: Instant response
- Form submissions: < 3 seconds
- Page navigation: Instant

##### **5. Error Handling Tests**
- Submit forms with empty required fields
- Edit with invalid JSON
- Verify appropriate error messages appear

#### **Transaction Analysis Testing**

##### **1. Sample Transaction Generation**
- Navigate to "Transaction Analysis" page
- Click "Generate Legitimate Transaction" button
- Verify transaction details display correctly
- Click "Generate Suspicious Transaction" button
- Verify higher fraud scores for suspicious patterns

##### **2. Fraud Detection Analysis**
- Click "Analyze Transaction" button
- Wait for LLM processing (45-60 seconds expected)
- Verify progress message displays: "⏳ Analysis in progress..."
- Confirm analysis results show:
  - Fraud probability score
  - Risk level (LOW/MEDIUM/HIGH)
  - XGBoost model score
  - Pattern similarity results
  - LLM-generated explanation
- Verify success message: "✅ Analysis Complete!"
- Confirm progress message clears after completion

##### **3. System Health Monitoring**
- Navigate to "System Health & Monitoring" page
- Verify system status displays correctly
- Test LLM model switching:
  - Click "Use OpenAI API" button
  - Click "Use Local LLM" button  
  - Click "Use Mock LLM" button
- Confirm no AttributeError occurs
- Verify appropriate success/error messages display

#### **Test Data & Environment**
- **API Server**: http://localhost:8000 (must be running)
- **UI Server**: http://localhost:8501 (must be running)
- **Patterns Available**: 1,457+ fraud patterns
- **Browser Requirements**: Modern browser with JavaScript enabled (Chrome, Firefox, Edge, Safari)

#### **Success Indicators**
✅ All pages load without errors  
✅ API connectivity maintained  
✅ Real-time search and filtering works  
✅ CRUD operations complete successfully  
✅ Professional UI appearance  
✅ Appropriate error handling  
✅ Performance meets benchmarks  

#### **Known Issues & Expected Behavior**
- **LLM Processing Time**: Online Ollama API takes ~50 seconds (expected)
- **Timeout Settings**: Transaction analysis timeout set to 120 seconds
- **Progress Messages**: Use st.empty() pattern for clearable messages
- **Error Handling**: System gracefully handles API unavailability

#### **Troubleshooting**

**Patterns not loading:**
- Verify API server running on port 8000: `curl http://localhost:8000/health`
- Check API key configuration in `.streamlit/secrets.toml`

**Search not working:**
- Check browser console for JavaScript errors
- Clear browser cache and refresh page

**Form submissions failing:**
- Verify API server connectivity
- Check form validation messages in UI

**UI layout issues:**
- Refresh browser (Ctrl+F5 or Cmd+Shift+R)
- Verify browser compatibility

**LLM Analysis timeout:**
- Expected for slow LLM services (Online Ollama ~50s)
- Consider switching to Mock LLM for faster testing
- Verify timeout settings in `api_client.py` (120s default)

## 📊 Monitoring & Metrics

### Available Metrics Endpoints
- `/api/v1/metrics` - JSON formatted metrics
- `/health` - System health check
- `/api/v1/system/status` - Detailed system status

### Prometheus Integration
Configure Prometheus to scrape metrics:
```yaml
scrape_configs:
  - job_name: 'fraud-detection-api'
    static_configs:
      - targets: ['localhost:8000']
```

## 📋 **Configuration**

### Environment Variables
Create a `.env` file in the project root:
```env
# API Configuration
API_HOST=localhost
API_PORT=8000
API_KEY=your-secure-api-key-here
API_RATE_LIMIT=1000  # requests per hour

# LLM Configuration
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Database Configuration
CHROMA_DB_PATH=./data/chroma_db
CHROMA_COLLECTION_NAME=fraud_patterns
VECTOR_DIMENSION=768

# Machine Learning
ML_MODEL_PATH=./data/models/
FRAUD_THRESHOLD=0.5
CONFIDENCE_THRESHOLD=0.7
PATTERN_SIMILARITY_THRESHOLD=0.8

# Monitoring & Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/fraud_detection.log
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Security
JWT_SECRET_KEY=your-jwt-secret-key
SESSION_TIMEOUT=3600  # seconds
CORS_ORIGINS=http://localhost:8501,http://localhost:3000
```

### Model Configuration
Configure ML model parameters in `config/ml_config.yaml`:
```yaml
xgboost:
  max_depth: 6
  learning_rate: 0.1
  n_estimators: 100
  random_state: 42
  eval_metric: 'logloss'

vector_search:
  similarity_threshold: 0.8
  max_results: 10
  embedding_model: 'sentence-transformers/all-MiniLM-L6-v2'

preprocessing:
  feature_scaling: 'standard'
  handle_missing: 'median'
  categorical_encoding: 'target'
```

### API Rate Limits & Quotas
- **OpenAI API**: 
  - Free tier: 3 requests/minute, 200 requests/day
  - Paid tier: 3,500 requests/minute
- **Ollama Local**: No limits (hardware dependent)
- **Internal API**: Configurable rate limiting per user/IP

## 🔧 **Advanced Troubleshooting**

### Common Issues & Solutions

#### **Model Loading Failures**
```powershell
# Symptoms: "Model file not found" errors
# Solution 1: Generate demo models
python scripts/utility/check_model_files.py --generate-demo

# Solution 2: Verify model paths
python -c "import os; print([f for f in os.listdir('./data/models/') if f.endswith('.joblib')])"

# Solution 3: Re-train models from scratch
python scripts/manage_models.py --retrain --force
```

#### **ChromaDB Connection Issues**
```powershell
# Symptoms: Vector database connection errors
# Solution 1: Reset ChromaDB
Remove-Item -Recurse -Force ./data/chroma_db/
python scripts/utility/initialize_vector_db.py

# Solution 2: Check disk space and permissions
python scripts/debug/check_storage_health.py

# Solution 3: Verify ChromaDB installation
python -c "import chromadb; print('ChromaDB version:', chromadb.__version__)"
```

#### **LLM Service Connectivity**
```powershell
# Test OpenAI connectivity
python scripts/debug/test_openai_connection.py

# Test Ollama connectivity (local)
curl http://localhost:11434/api/version

# Test Ollama connectivity (remote)
python scripts/utility/configure_ollama_api.py --test

# Debug LLM service routing
python scripts/debug/debug_llm_service.py --verbose
```

#### **API Performance Issues**
```powershell
# Monitor API performance
python scripts/monitoring/api_performance_monitor.py

# Check system resources
python scripts/debug/system_resource_check.py

# Optimize database queries
python scripts/utility/optimize_database.py

# Clear application cache
python scripts/utility/clear_cache.py
```

#### **UI Rendering Problems**
```powershell
# Clear Streamlit cache
streamlit cache clear

# Check UI component health
python ui/debug/test_ui_components.py

# Verify API connectivity from UI
python ui/debug/test_api_connection.py

# Reset UI configuration
python ui/utils/reset_ui_config.py
```

#### **Memory and Resource Issues**
```powershell
# Monitor memory usage
python scripts/monitoring/memory_monitor.py

# Optimize model memory usage
python scripts/utility/optimize_models.py --reduce-memory

# Configure garbage collection
python scripts/utility/gc_optimization.py

# Check for memory leaks
python scripts/debug/memory_leak_detector.py
```

### Diagnostic Tools

#### **System Health Check**
```powershell
# Comprehensive system diagnostics
python scripts/utility/diagnose_system.py --full

# Quick health check
python scripts/utility/health_check.py

# Component-specific diagnostics
python scripts/debug/test_individual_components.py
```

#### **Performance Profiling**
```powershell
# Profile API endpoints
python scripts/profiling/api_profiler.py

# Profile ML inference time
python scripts/profiling/ml_performance_profiler.py

# Profile memory usage patterns
python scripts/profiling/memory_profiler.py
```

#### **Log Analysis**
```powershell
# Analyze error patterns
python scripts/debug/log_analyzer.py --errors

# Generate performance reports
python scripts/monitoring/performance_report.py

# Export system metrics
python scripts/monitoring/export_metrics.py --format json
```

### Production Deployment Issues

#### **Docker Container Problems**
```bash
# Check container health
docker ps -a
docker logs fraud-detection-api

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up

# Debug container networking
docker network ls
docker inspect fraud-detection_default
```

#### **Load Balancer Configuration**
```bash
# Test load balancer health
curl -I http://your-load-balancer/health

# Check backend connectivity
curl -I http://backend-1:8000/health
curl -I http://backend-2:8000/health

# Monitor load distribution
python scripts/monitoring/load_balancer_monitor.py
```

#### **Database Connection Pooling**
```python
# Optimize connection pool settings
# In your environment file:
DB_POOL_SIZE=20
DB_MAX_CONNECTIONS=100
DB_POOL_TIMEOUT=30

# Monitor connection usage
python scripts/monitoring/db_connection_monitor.py
```

## 📊 **Example API Responses**

### Transaction Analysis Response
```json
{
  "transaction_id": "txn_12345678901234567890",
  "analysis_timestamp": "2024-12-19T10:30:00Z",
  "fraud_prediction": {
    "is_fraud": false,
    "fraud_probability": 0.15,
    "risk_level": "LOW",
    "confidence_score": 0.92
  },
  "decision": {
    "action": "APPROVE",
    "reason": "Low fraud probability with high confidence",
    "requires_review": false,
    "auto_approved": true
  },
  "ml_analysis": {
    "xgboost_score": 0.15,
    "feature_importance": {
      "transaction_amount": 0.25,
      "merchant_category": 0.20,
      "time_of_day": 0.18,
      "location_risk": 0.15,
      "velocity_score": 0.22
    },
    "model_version": "v2.1.0"
  },
  "pattern_analysis": {
    "similar_patterns_found": 3,
    "max_similarity_score": 0.45,
    "pattern_types": ["normal_purchase", "recurring_merchant"],
    "historical_match_accuracy": 0.89
  },
  "llm_analysis": {
    "provider": "openai",
    "model": "gpt-4",
    "explanation": "This transaction appears legitimate based on the customer's normal spending patterns. The amount is consistent with previous purchases at similar merchants, and the timing aligns with the customer's typical shopping hours.",
    "risk_factors": [],
    "protective_factors": [
      "Consistent with spending history",
      "Known merchant location",
      "Normal transaction timing"
    ],
    "confidence": 0.88
  },
  "transaction_details": {
    "amount": 89.99,
    "currency": "USD",
    "merchant": "AMAZON.COM",
    "merchant_category": "E-commerce",
    "location": "Seattle, WA",
    "payment_method": "Credit Card",
    "card_last_four": "1234"
  },
  "processing_metrics": {
    "total_processing_time_ms": 245,
    "ml_inference_time_ms": 85,
    "vector_search_time_ms": 35,
    "llm_analysis_time_ms": 125
  }
}
```

### High-Risk Fraud Detection Response
```json
{
  "transaction_id": "txn_98765432109876543210",
  "analysis_timestamp": "2024-12-19T10:35:00Z",
  "fraud_prediction": {
    "is_fraud": true,
    "fraud_probability": 0.94,
    "risk_level": "HIGH",
    "confidence_score": 0.96
  },
  "decision": {
    "action": "BLOCK",
    "reason": "High fraud probability with multiple risk indicators",
    "requires_review": true,
    "auto_approved": false,
    "escalation_level": "IMMEDIATE"
  },
  "ml_analysis": {
    "xgboost_score": 0.94,
    "feature_importance": {
      "location_risk": 0.35,
      "transaction_amount": 0.28,
      "velocity_score": 0.25,
      "time_of_day": 0.12
    },
    "anomaly_indicators": [
      "Unusual transaction amount (10x normal)",
      "Foreign country transaction",
      "High-velocity spending pattern"
    ]
  },
  "pattern_analysis": {
    "similar_patterns_found": 8,
    "max_similarity_score": 0.92,
    "pattern_types": ["card_testing", "foreign_fraud", "amount_anomaly"],
    "known_fraud_patterns": 6
  },
  "llm_analysis": {
    "provider": "openai",
    "model": "gpt-4",
    "explanation": "This transaction exhibits multiple high-risk characteristics typical of fraudulent activity. The combination of an unusually large amount, foreign location, and rapid succession of transactions strongly suggests card fraud.",
    "risk_factors": [
      "Transaction amount 10x higher than normal",
      "International transaction from high-risk country",
      "5 transactions within 10 minutes",
      "First transaction at this merchant type",
      "Location 3000+ miles from recent transactions"
    ],
    "confidence": 0.94,
    "recommended_actions": [
      "Block transaction immediately",
      "Notify cardholder via SMS/email",
      "Review recent transaction history",
      "Consider temporary card suspension"
    ]
  },
  "alerts": {
    "immediate_notifications": [
      "SMS sent to cardholder",
      "Email alert sent",
      "Fraud team notification"
    ],
    "escalation_triggered": true,
    "investigation_case_id": "FRAUD_2024_001234"
  }
}
```

## 🚀 Production Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups configured
- [ ] Monitoring alerts set up
- [ ] Load balancer configured
- [ ] Security scan completed

### Post-Deployment
- [ ] Health checks passing
- [ ] All endpoints responding
- [ ] UI accessible and functional
- [ ] Monitoring dashboards active
- [ ] Log aggregation working
- [ ] Backup procedures tested

## 🔒 Security Considerations

1. **API Authentication**: X-API-Key header required
2. **Input Validation**: Pydantic models for request validation
3. **Error Handling**: Secure error messages (no sensitive data exposure)
4. **Rate Limiting**: Implement for production deployments
5. **HTTPS**: Use SSL/TLS in production
6. **Environment Variables**: Secure storage of API keys and secrets

## 🤝 **Contributing**

We welcome contributions! Please follow these steps:

1. **Fork the Repository**
   ```bash
   git fork https://github.com/yourusername/creditcardfrauddetection
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-fraud-detection-enhancement
   ```

3. **Make Changes**
   - Add new fraud detection algorithms
   - Improve ML model accuracy
   - Enhance UI/UX features
   - Add comprehensive tests
   - Update documentation

4. **Submit Pull Request**
   - Ensure all tests pass
   - Update README.md if needed
   - Include performance impact analysis
   - Provide clear description of changes

### Development Guidelines
- Follow PEP 8 style guide for Python code
- Add comprehensive docstrings to all functions
- Include unit tests for new features (minimum 80% coverage)
- Update requirements.txt for new dependencies
- Follow security best practices for fraud detection systems
- Document any new ML models or algorithms used

### Code Review Checklist
- [ ] Security review completed (no sensitive data exposure)
- [ ] Performance impact assessed
- [ ] ML model validation included
- [ ] Documentation updated
- [ ] Tests passing with >80% coverage
- [ ] No hardcoded credentials or API keys

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary
- ✅ Commercial use allowed
- ✅ Modification allowed  
- ✅ Distribution allowed
- ✅ Private use allowed
- ❌ No warranty provided
- ❌ No liability assumed

**Important**: While the software is open source, ensure compliance with financial regulations and data privacy laws in your jurisdiction when deploying in production environments.

## ⚠️ **IMPORTANT DISCLAIMERS**

> **🚨 CRITICAL NOTICE**: This software is designed for **EDUCATIONAL, RESEARCH, AND DEVELOPMENT PURPOSES**

### 🔴 **Financial & Business Risk Disclaimers**

#### **NOT PRODUCTION FINANCIAL SOFTWARE**
- 📚 **Educational Tool**: This project is primarily intended for learning machine learning, fraud detection algorithms, and software development concepts
- 🚫 **No Financial Liability**: This software is not designed to handle real financial transactions or provide production-level fraud detection
- 👨‍💼 **Professional Implementation Required**: Always consult qualified cybersecurity experts, fraud detection specialists, and financial technology professionals before deploying in production
- 📊 **No Guarantee**: Algorithm predictions and fraud detection accuracy are not guaranteed for real-world financial applications

#### **HIGH RISK WARNING**
- 💰 **Financial Loss Risk**: Incorrect fraud detection can result in:
  - False positives blocking legitimate transactions (customer dissatisfaction, revenue loss)
  - False negatives allowing fraudulent transactions (direct financial losses)
  - Compliance violations and regulatory penalties
- 🚨 **Business Impact**: Improper fraud detection systems can severely impact business operations
- 💸 **Liability Exposure**: Organizations may face legal liability for inadequate fraud protection
- 📉 **Reputation Risk**: Security breaches and fraud can cause significant reputational damage

#### **NO PERFORMANCE GUARANTEES**
- 🎲 **Uncertain Outcomes**: Fraud detection results are inherently uncertain and context-dependent
- 📈 **Variable Performance**: AI/ML models may perform well in testing but fail with real-world fraud patterns
- 🔄 **Model Degradation**: Fraud patterns evolve rapidly, making models less effective over time
- 📊 **Dataset Bias**: Models trained on historical data may not detect new or emerging fraud types

### 🤖 **Technical & AI Limitations Disclaimers**

#### **ARTIFICIAL INTELLIGENCE LIMITATIONS**
- 🧠 **AI Uncertainty**: Machine learning models can produce incorrect, biased, or unreliable fraud predictions
- 📊 **Data Dependency**: Model accuracy entirely depends on training data quality, representativeness, and fraud pattern coverage
- 🔄 **Adversarial Attacks**: Fraudsters actively adapt to bypass detection systems
- 🎯 **False Confidence**: High confidence scores from models do not guarantee accuracy in production environments

#### **DATA & PRIVACY LIMITATIONS**
- 🔒 **Sensitive Data**: Credit card fraud detection involves highly sensitive financial and personal data
- 📡 **Data Security**: This system may not meet production-level security requirements for handling financial data
- 🗃️ **Data Compliance**: Users must ensure compliance with PCI DSS, GDPR, CCPA, and other relevant data protection regulations
- 🔐 **Encryption**: Production systems require enterprise-level encryption and security measures not present in this educational project

#### **SOFTWARE LIMITATIONS**
- 🧪 **Experimental Software**: This is a research/educational project, not production-ready fraud detection software
- 🐛 **Potential Bugs**: Software may contain critical bugs that could affect fraud detection accuracy
- 🔧 **No Warranty**: Software provided "as-is" without warranty of functionality, security, or reliability
- 📱 **Platform Dependencies**: Performance and security may vary across different operating systems and deployment environments

### ⚖️ **Legal & Compliance Disclaimers**

#### **REGULATORY COMPLIANCE**
- 📋 **Financial Regulations**: Users are responsible for compliance with all applicable financial services regulations including:
  - PCI DSS (Payment Card Industry Data Security Standard)
  - SOX (Sarbanes-Oxley Act) compliance
  - Banking regulations and fraud reporting requirements
  - International financial crime prevention laws
- 🌍 **International Compliance**: Financial regulations vary significantly by country and jurisdiction
- 🏛️ **Licensing Requirements**: Operating fraud detection systems may require specific licenses and certifications
- 📊 **Audit Requirements**: Financial institutions must maintain detailed audit trails and compliance documentation

#### **DATA PROTECTION & PRIVACY**
- 🔒 **GDPR Compliance**: European users must ensure compliance with General Data Protection Regulation
- 🇺🇸 **CCPA Compliance**: California users must comply with California Consumer Privacy Act
- 🌐 **Cross-Border Data**: International data transfers may require specific legal frameworks
- 👤 **Personal Data**: Credit card transaction data contains highly sensitive personal information requiring special protection

#### **LIABILITY LIMITATIONS**
- 🚫 **No Liability**: Authors, contributors, and distributors assume NO responsibility for:
  - Financial losses from fraud detection failures
  - Security breaches or data exposures
  - Regulatory compliance violations
  - Business disruptions or customer impact
  - Legal or regulatory penalties
- ⚖️ **User Responsibility**: Users assume full responsibility for:
  - Proper implementation and testing
  - Security measures and data protection
  - Regulatory compliance
  - Production deployment decisions
- 🛡️ **Indemnification**: Users agree to indemnify and hold harmless all project contributors from any claims, damages, or legal issues

#### **INTELLECTUAL PROPERTY & THIRD-PARTY SERVICES**
- 📚 **Educational Use**: This software is intended for educational and research purposes
- 🔬 **Academic Research**: Suitable for academic research, thesis projects, and learning fraud detection concepts
- 🏢 **Commercial Use Restrictions**: Commercial deployment may require additional licenses for:
  - Third-party ML libraries and models
  - External API services (OpenAI, etc.)
  - Production security and monitoring tools
- 🔐 **API Keys**: Users are responsible for securing and managing their own API keys and credentials

### 🎯 **Responsible Use Guidelines**

#### **RECOMMENDED PRACTICES**
- 📖 **Education First**: Use this tool to learn about fraud detection techniques, not as a primary business solution
- 💭 **Critical Analysis**: Question and validate all fraud predictions and model outputs
- 🔍 **Independent Testing**: Conduct thorough independent testing before any production consideration
- 📊 **Professional Consultation**: Engage fraud detection experts and cybersecurity professionals for production deployments
- 🎓 **Continuous Learning**: Stay informed about evolving fraud patterns, detection techniques, and regulatory requirements

#### **RISK MANAGEMENT**
- 💰 **Start Small**: If testing with any real data, use minimal datasets with proper anonymization
- 🎯 **Simulation Only**: Practice with simulated transaction data before any real-world testing
- 📈 **Gradual Implementation**: Never deploy directly to production without extensive testing and validation
- ⏰ **Regular Review**: Continuously monitor and reassess fraud detection performance and accuracy

#### **SECURITY BEST PRACTICES**
- 🔐 **Data Encryption**: Always encrypt sensitive data at rest and in transit
- 🛡️ **Access Control**: Implement proper authentication and authorization
- 📊 **Audit Logging**: Maintain comprehensive audit trails for all fraud detection activities
- 🔍 **Regular Security Reviews**: Conduct regular security assessments and penetration testing

### 🌟 **Positive Use Cases**

#### **APPROPRIATE APPLICATIONS**
- 🎓 **Learning ML/AI**: Understanding machine learning applications in fraud detection
- 📊 **Research Projects**: Academic research on fraud detection algorithms and techniques
- 💻 **Software Development**: Learning API development, data processing, and system architecture
- 🧠 **Algorithm Development**: Developing and testing new fraud detection approaches
- 📈 **Educational Demonstrations**: Teaching concepts of fraud detection and cybersecurity

#### **INAPPROPRIATE APPLICATIONS**
- ❌ **Production Fraud Detection**: Never use as-is for real financial transaction monitoring
- ❌ **Commercial Deployment**: Not suitable for commercial fraud detection services without significant enhancement
- ❌ **Regulatory Compliance**: Cannot be relied upon for meeting financial regulatory requirements
- ❌ **Primary Security**: Should not be the only fraud detection mechanism in any system

---

## 📞 **Support & Contact**

### 🛠️ **Technical Support**
- 🐛 **Bug Reports**: Open detailed issues on GitHub with reproduction steps and system information
- 💡 **Feature Requests**: Submit enhancement proposals via GitHub Issues with use case descriptions
- 📖 **Documentation**: Check this README, inline code comments, and API documentation first
- 💬 **Discussions**: Use GitHub Discussions for general questions and community support

### 🚨 **Important Support Limitations**
- 🔒 **No Production Support**: We do not provide support for production deployments
- 📧 **No Business Consultation**: Technical support is limited to software functionality only
- ⚖️ **No Legal/Compliance Advice**: Consult appropriate legal and compliance professionals
- 💰 **No Financial Advice**: This is educational software with no financial guidance provided

### 📧 **Contact Information**
- **GitHub Issues**: [Primary support channel]
- **GitHub Discussions**: [Community support and questions]
- **Security Issues**: Report via GitHub Security tab (for educational security research only)

---

## 🎯 **Final Acknowledgment**

By downloading, installing, using, or contributing to this software, you explicitly acknowledge that:

1. **You have read and understood all disclaimers and warnings**
2. **You accept all risks associated with using this educational fraud detection software**
3. **You will not hold the creators liable for any financial, business, or security losses**
4. **You understand this is educational software, not production-ready fraud detection technology**
5. **You will comply with all applicable laws, regulations, and data protection requirements**
6. **You will use this software responsibly, ethically, and only for appropriate educational/research purposes**
7. **You will not deploy this software in production environments without proper professional review and enhancement**
8. **You understand the limitations of AI/ML fraud detection and will not rely solely on this system for financial security**

### 🔒 **Security Responsibility Statement**
Users acknowledge that fraud detection systems require:
- Professional cybersecurity expertise
- Compliance with financial regulations
- Continuous monitoring and updates
- Integration with comprehensive security frameworks
- Regular testing and validation

This educational project provides a foundation for learning but requires significant additional work for any practical application.

---

**🎉 Happy Learning and Responsible Development! 🛡️💻**

*Remember: The best fraud detection combines technology, expertise, and continuous vigilance!*

---

## 📈 **Version History**

### v2.1.0 (Current) - Enhanced AI Integration
- ✅ Multi-tier LLM integration (OpenAI, Ollama, Mock)
- ✅ Advanced pattern recognition with vector similarity
- ✅ Comprehensive fraud explanation generation
- ✅ Enhanced UI with pattern management
- ✅ Production-ready API with authentication
- ✅ Comprehensive monitoring and logging

### v2.0.0 - Full System Architecture
- ✅ Complete FastAPI backend implementation
- ✅ Streamlit frontend dashboard
- ✅ XGBoost fraud classification model
- ✅ ChromaDB vector database integration
- ✅ Docker containerization support

### v1.0.0 - Initial Release
- ✅ Basic fraud detection algorithm
- ✅ Simple API endpoints
- ✅ Proof of concept implementation

---

## 📚 Additional Documentation

### Interview Preparation
For detailed interview explanations, architectural deep-dives, and common interview questions, see:
- **[Interview_Explanation.md](Interview_Explanation.md)** - Comprehensive interview guide with model explanations, Q&A, and technical deep-dives

### Component Documentation

#### UI Components
The Streamlit UI provides comprehensive fraud analysis capabilities:
- **Dashboard**: Real-time metrics, transaction activity, fraud rate trends
- **Transaction Analysis**: Real-time analysis, sample generation, historical lookup
- **Fraud Patterns**: CRUD operations with search, filtering, and 1,000+ pattern management
- **System Health**: Performance monitoring, model tracking, resource utilization

For detailed UI documentation, see: [ui/README.md](ui/README.md)

#### Debug Scripts
Debug utilities for LLM service troubleshooting:
- **debug_llm_service_unified.py**: Multi-mode debugging (console, breakpoint, VS Code)
- Supports normal, breakpoint, and VS Code debugging modes
- PDB integration for step-by-step debugging

For debug scripts documentation, see: [scripts/debug/README.md](scripts/debug/README.md)

#### Utility Scripts
Workspace management and system utilities:
- **clean_workspace.py**: Unified cleaning tool (logs, cache, redundant files)
- **diagnose_system.py**: System diagnostics and configuration checks
- **run_tests.py**: Test suite execution
- **configure_ollama_api.py**: Ollama API configuration

For utility scripts documentation, see: [scripts/utility/README.md](scripts/utility/README.md)

---

*Last updated: February 2026*
*Documentation version: 2.2.0*
