# Real-Time Credit Card Fraud Detection System

A production-ready system for detecting fraud in real-time credit card transactions by leve### Feedback Loop**: Analyst feedback is incorporated back into:
   - Vector database for improving pattern detection
   - Training data for ML model improvement

### Key System Components

#### 1. Machine Learning Model
- **Purpose**: Provides fast, initial screening of transactions
- **Type**: Gradient Boosted Decision Trees (optimized for speed and accuracy)
- **Inputs**: Engineered features from transaction data
- **Outputs**: Fraud probability score and confidence level
- **Advantages**: Fast processing, handles high transaction volumes

#### 2. Vector Database
- **Purpose**: Stores historical fraud patterns for similarity search
- **Technology**: Either Chroma or Pinecone vector DB (configurable)
- **Content**: Embeddings of historical fraud patterns with metadata
- **Role**: Powers the RAG (Retrieval Augmented Generation) for the LLM
- **Advantages**: Efficient similarity search, continuous learning from feedback

#### 3. Large Language Model (LLM)
- **Purpose**: In-depth analysis of transactions flagged as uncertain
- **Capability**: Analyzes transaction details against known fraud patterns
- **Enhancement**: Uses RAG to provide relevant context from historical patterns
- **Outputs**: Fraud probability, detailed reasoning, and recommendations
- **Advantages**: Human-like reasoning, explainability, adaptability to new fraud types

#### 4. Feature Engineering
- **Purpose**: Transforms raw transaction data into model-ready features
- **Process**: Extracts and normalizes attributes from transaction data
- **Features Generated**: Transaction timing anomalies, customer behavior patterns, merchant risk scores
- **Advantages**: Enhances detection accuracy through domain-specific transformationsing both traditional machine learning techniques and Large Language Models with Retrieval Augmented Generation (RAG).

## Overview

This system combines traditional machine learning approaches with advanced LLM-based analysis to provide high-accuracy fraud detection with human-understandable explanations. The system uses a two-stage approach:

1. **First-pass ML screening** - Fast and efficient analysis using gradient boosting models
2. **LLM-based RAG analysis** - In-depth analysis of suspicious transactions by comparing them to historical fraud patterns

## Quick Start

### Setting Up and Running the System

1. **Prerequisites**
   - Python 3.10+
   - Git
   - Shared Python environment located at `d:\Study\AILearning\shared_Environment`

2. **Start the System**
   ```powershell
   # Start both API and UI with a single command
   .\start_system.ps1
   ```

   This will:
   - Start the API server on http://localhost:8000
   - Start the UI application on http://localhost:8501
   - Wait for the API to be fully initialized before starting the UI

3. **Alternative: Start Components Separately**
   ```powershell
   # Start API server only
   .\start_api.ps1
   
   # In a separate terminal, start the UI
   .\run_ui_fixed.ps1
   ```

4. **Run Tests**
   ```powershell
   # Run all system tests
   python run_tests.py
   ```

### Accessing the Application

- **UI Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## System Architecture

The system consists of two main components that work together:

### 1. API Server (Backend)

The API server handles all the data processing, fraud detection logic, and provides endpoints for the UI to consume:

- **RESTful API** built with FastAPI
- **Machine Learning Models** for transaction analysis
- **LLM Integration** for advanced fraud pattern analysis
- **Vector Database** for storing historical fraud patterns
- **Secure Authentication** with API keys

### 2. Streamlit UI (Frontend)

The UI provides a user-friendly interface for monitoring fraud detection results and managing the system:

- **Dashboard** for monitoring system performance
- **Transaction Analysis** for reviewing individual transactions
- **Fraud Pattern Management** for maintaining the fraud pattern database
- **System Health Monitoring** for tracking system performance

## How the Fraud Detection Works

The system employs a sophisticated two-stage approach to detect fraudulent credit card transactions with high accuracy while providing human-understandable explanations.

### Detection Workflow

```
┌──────────────────┐     ┌───────────────────┐     ┌─────────────────────┐     ┌───────────────────┐
│  Transaction     │     │  Feature          │     │  ML Model           │     │  Initial Fraud    │
│  Received        │────>│  Engineering      │────>│  Analysis           │────>│  Probability      │
└──────────────────┘     └───────────────────┘     └─────────────────────┘     └─────────┬─────────┘
                                                                                         │
                                                                                         ▼
                                 ┌──────────────────────────────────────────────────────────┐
                                 │  Confidence Check: Is ML result confident?               │
                                 └────────────────┬─────────────────────────┬───────────────┘
                                                  │                         │
                                                 No                        Yes
                                                  │                         │
                                                  ▼                         ▼
┌───────────────────┐     ┌───────────────────┐     ┌────────────────────────────────────────┐
│  Final Decision & │     │  LLM Analysis     │     │  Return ML-based Decision               │
│  Response         │<────│  with Reasoning   │     │  (Skip LLM for clear-cut cases)         │
└───────────────────┘     └────────┬──────────┘     └────────────────────────────────────────┘
                                   │
                                   ▼
┌───────────────────┐     ┌───────────────────┐     ┌────────────────────────────────────────┐
│  Similar Patterns │<────│  Vector DB        │     │  Transaction Text                       │
│  Retrieved        │     │  Search           │<────│  Creation                               │
└───────────────────┘     └───────────────────┘     └────────────────────────────────────────┘
```

### Detection Process Steps

1. **Transaction Intake**: The system receives a transaction with details like amount, merchant, location, etc.

2. **Feature Engineering**: Raw transaction data is transformed into ML-ready features including:
   - Transaction attributes (amount, time, location)
   - Historical patterns for the card/customer
   - Merchant risk scoring
   - Behavioral anomaly detection

3. **ML Model Analysis**: A gradient-boosted decision tree model analyzes the features and returns:
   - Initial fraud probability score
   - Confidence level of the prediction

4. **Confidence Assessment**: Based on the ML model's confidence:
   - If highly confident (clear legitimate or fraudulent), use ML result directly
   - If uncertain, proceed with LLM analysis for deeper inspection

5. **Vector Database Search**: For uncertain cases:
   - Transaction is converted to text representation
   - Vector database is searched for similar historical fraud patterns
   - Top-K most similar patterns are retrieved

6. **LLM Analysis**: For uncertain cases:
   - Similar patterns are provided as context to the LLM
   - Transaction details are analyzed against known fraud patterns
   - LLM provides fraud probability, reasoning, and recommendations

7. **Final Decision & Response**:
   - Combined score from ML model and LLM (weighted)
   - Final fraud probability and confidence determined
   - Decision reasoning included in response
   - Transaction flagged for review if confidence below threshold

8. **Feedback Loop**: Analyst feedback is incorporated back into:
   - Vector database for improving pattern detection
   - Training data for ML model improvement

## API and UI Integration

The UI communicates with the API server to perform operations:

1. **Fetch Data**: The UI retrieves fraud patterns, transaction history, and metrics from the API
2. **Add/Update Patterns**: The UI allows analysts to create and modify fraud patterns via the API
3. **Transaction Analysis**: The UI sends transaction data to the API for analysis

If the API is unavailable, the UI will display mock data for demonstration purposes, but in production, all data should come from the API.

## Project Structure

```
creditcardfrauddetection/
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore file
├── RUN_INSTRUCTIONS.md               # Detailed instructions for running the system
├── docker-compose.yml                # Docker composition configuration
├── Dockerfile                        # Docker container definition
├── run_server.py                     # Server startup script
├── run_ui_fixed.ps1                  # Script to start the UI with shared environment
├── start_api.ps1                     # Script to start the API server
├── start_system.ps1                  # Script to start both API and UI
├── run_tests.py                      # Script to run all system tests
├── app/                              # Main application code
│   ├── __init__.py
│   ├── main.py                       # Application entry point
│   ├── api/                          # API layer
│   │   ├── __init__.py
│   │   ├── models.py                 # Pydantic models for requests/responses
│   │   ├── endpoints.py              # API route definitions
│   │   └── dependencies.py           # Dependency injection
│   ├── core/                         # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration settings
│   │   ├── logging.py                # Logging configuration
│   │   ├── security.py               # Security utilities for authentication
│   ├── services/                     # Business logic services
│   │   ├── __init__.py
│   │   ├── fraud_detection_service.py # Main fraud detection logic
│   │   ├── llm_service.py            # LLM interactions
│   │   └── vector_db_service.py      # Vector database operations
│   ├── models/                       # ML models
│   │   ├── __init__.py
│   │   ├── ml_model.py               # Machine learning model
│   │   ├── embeddings.py             # Embedding model for vector representations
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       ├── feature_engineering.py    # Feature extraction
│       ├── data_processing.py        # Data processing utilities
├── data/                             # Data storage
│   ├── __init__.py
│   ├── sample/                       # Sample data files
│   │   ├── __init__.py
│   │   └── fraud_patterns.json       # Sample fraud patterns
├── scripts/                          # Utility scripts
│   ├── __init__.py
│   ├── init_vector_db.py             # Initialize vector database
│   └── generate_sample_data.py       # Generate sample transaction data
├── tests/                            # Test files
│   ├── README.md                     # Test documentation
│   ├── run_integration_tests.py      # Test runner
│   ├── test_api_integration.py       # API integration tests
│   ├── test_feedback_integration.py  # Feedback integration tests
│   └── test_pattern_ingestion_integration.py  # Pattern ingestion tests

```

## Key Features

- Real-time transaction screening with sub-second response times
- Retrieval Augmented Generation (RAG) to leverage historical fraud patterns
- Feature engineering optimized for credit card transaction data
- Vector database for efficient similarity search of fraud patterns
- Confidence scoring and automatic/manual review routing
- Feedback loop for continual system improvement
- RESTful API for easy integration with payment processing systems
- Comprehensive logging and monitoring
- Interactive Streamlit-based user interface for analysts and administrators

## Recent Improvements (May 2025)

- **Fixed Vector Database Integration**: Resolved issues with storing and retrieving complex metadata in the vector database by properly handling JSON serialization/deserialization
- **Removed Mock Data Dependencies**: Updated the UI to always use real data from the API instead of fallbacks to mock data
- **Simplified Script Structure**: Removed redundant scripts and consolidated to a few key scripts for system operation
- **Enhanced Documentation**: Updated README.md and RUN_INSTRUCTIONS.md with clearer instructions
- **Fixed API Client Issues**: Resolved indentation errors and added proper support for all HTTP methods

## RAG Implementation Details

This system's unique approach to fraud detection is powered by Retrieval Augmented Generation (RAG). Here's how it works:

### 1. Transaction Processing and Feature Engineering
When a transaction is received, the system:
- Extracts numerical features (amount, time, etc.)
- Calculates derived features (transaction velocity, distance from home, etc.)
- Creates a textual description of the transaction and its context

### 2. Initial ML Screening
A traditional machine learning model (XGBoost) performs initial screening to:
- Provide fast first-pass analysis
- Calculate initial fraud probability
- Determine if further LLM analysis is warranted

### 3. Vector Database Retrieval
The system then:
- Converts the transaction description to a vector embedding
- Searches the vector database for similar historical fraud patterns
- Retrieves the most relevant cases for analysis

### 4. LLM-Based Analysis
The large language model:
- Receives the transaction details and similar fraud patterns
- Analyzes contextual similarities and differences
- Provides a detailed fraud probability assessment and reasoning
- Explains why the transaction might be fraudulent

### 5. Decision Fusion
The system:
- Combines ML and LLM fraud probabilities with appropriate weighting
- Applies confidence thresholds to determine final disposition
- Routes borderline cases for human review
- Returns detailed reasoning for the decision

### 6. Continuous Improvement
The system includes:
- A feedback loop for analyst judgments to be incorporated
- Automatic addition of confirmed fraud patterns to the vector database
- Periodic retraining of the ML model with new data

## Getting Started

### Prerequisites

- Python 3.9+
- An OpenAI API key
- A Pinecone API key (or you can use the included Chroma local vector database)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/fraud-detection-system.git
   cd fraud-detection-system
   ```

2. Use the shared environment or create a new virtual environment and install dependencies:
   
   **Option 1: Using shared environment (recommended)**
   ```powershell
   # Activate the shared environment
   & "d:\Study\AILearning\shared_Environment\Scripts\Activate.ps1"
   ```
   
   **Option 2: Create new environment**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy the example environment file and update with your credentials:
   ```
   cp .env.example .env
   # Edit .env with your OpenAI and Pinecone API keys
   ```

4. Initialize the vector database with sample fraud patterns:
   ```
   python scripts/init_vector_db.py
   ```

5. Start the API server:
   ```
   python run_server.py
   # Or alternatively:
   uvicorn app.main:app --reload
   ```

### Docker Deployment

To deploy with Docker:

```
docker-compose up -d
```

## Usage Examples

### Fraud Detection Endpoint

```python
import requests
import json

# Production endpoint would use HTTPS and proper authentication
url = "http://localhost:8000/api/v1/detect-fraud"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your_api_key_here"  # Required in production mode
}

# Example transaction data
payload = {
    "transaction_id": "tx_123456789",
    "card_id": "card_7890123456",
    "merchant_id": "merch_24680",
    "timestamp": "2025-05-07T10:23:45Z", 
    "amount": 325.99,
    "merchant_category": "Electronics",
    "merchant_name": "TechWorld Store",
    "merchant_country": "US",
    "merchant_zip": "98040",
    "customer_id": "cust_12345",
    "is_online": True,
    "device_id": "dev_abcxyz",
    "ip_address": "192.168.1.1",
    "currency": "USD",
    "latitude": 47.5874,
    "longitude": -122.2352
}

# Send the request
response = requests.post(url, headers=headers, data=json.dumps(payload))
result = response.json()

# Process the result
if response.status_code == 200:
    print(f"Transaction ID: {result['transaction_id']}")
    print(f"Fraud Detected: {result['is_fraud']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Reason: {result['decision_reason']}")
    print(f"Requires Review: {result['requires_review']}")
    print(f"Processing Time: {result['processing_time_ms']} ms")
else:
    print(f"Error: {result.get('detail', 'Unknown error')}")
```

### Feedback Endpoint

```python
import requests
import json

url = "http://localhost:8000/api/v1/feedback"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your_api_key_here"  # Required in production mode
}

# Example feedback data from fraud analyst
payload = {
    "transaction_id": "tx_123456789",
    "actual_fraud": True,
    "analyst_notes": "This was a case of account takeover. Customer confirmed they did not make this purchase. Fraudster also attempted to change contact email and shipping address prior to purchase."
}

# Send the request
response = requests.post(url, headers=headers, data=json.dumps(payload))
result = response.json()

# Process the result
if response.status_code == 200:
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
else:
    print(f"Error: {result.get('detail', 'Unknown error')}")
```

### Batch Processing Example

For high-volume environments, you can implement batch processing:

```python
import requests
import json
import asyncio
import aiohttp
from typing import List, Dict, Any

async def process_transactions_batch(transactions: List[Dict[str, Any]], api_key: str) -> List[Dict[str, Any]]:
    """Process a batch of transactions asynchronously."""
    url = "http://localhost:8000/api/v1/detect-fraud"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for transaction in transactions:
            task = asyncio.create_task(
                session.post(url, headers=headers, json=transaction)
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        results = []
        
        for response in responses:
            if response.status == 200:
                results.append(await response.json())
            else:
                # Handle error
                error_text = await response.text()
                results.append({"error": error_text})
        
        return results

# Example usage
async def main():
    # Your batch of transactions
    transactions = [
        {
            "transaction_id": "tx_123456789",
            "card_id": "card_7890123456",
            # ... other fields
        },
        {
            "transaction_id": "tx_987654321",
            "card_id": "card_1234567890",
            # ... other fields
        }
    ]
    
    api_key = "your_api_key_here"
    results = await process_transactions_batch(transactions, api_key)
    
    # Process results
    for result in results:
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Transaction {result['transaction_id']}: {'FRAUD' if result['is_fraud'] else 'LEGITIMATE'}")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
```

## Deployment Options

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/fraud-detection-system.git
cd fraud-detection-system

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and settings

# Initialize the vector database
python scripts/init_vector_db.py

# Run tests
python tests/run_integration_tests.py

# Start the API server in development mode
python run_server.py
# Or with uvicorn directly:
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and start the containers
docker-compose up -d

# View logs
docker-compose logs -f

# Scale the API service for higher throughput
docker-compose up -d --scale fraud-detection-api=3

# Stop the services
docker-compose down
```

### Production Deployment

For production environments, consider:

1. **Kubernetes Deployment**: For scalability and high availability
   - Use the provided Dockerfile to build a container image
   - Deploy using Kubernetes manifests 
   - Set up autoscaling based on CPU/memory usage

2. **Cloud Provider Solutions**:
   - AWS: ECS or EKS with load balancing
   - Google Cloud: GKE with Cloud Load Balancing
   - Azure: AKS with Azure Load Balancer

3. **Security Considerations**:
   - Use proper API key management
   - Enable HTTPS with proper certificates
   - Implement rate limiting
   - Set up proper network security groups

4. **Monitoring**:
   - Use the included Prometheus/Grafana setup
   - Set up alerts for high error rates or latency
   - Monitor system resource usage

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project uses OpenAI's GPT models for natural language processing
- Vector database functionality provided by Pinecone/Chroma
- Built with FastAPI and LangChain