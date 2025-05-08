# Real-Time Credit Card Fraud Detection System

A production-ready system for detecting fraud in real-time credit card transactions by leveraging both traditional machine learning techniques and Large Language Models with Retrieval Augmented Generation (RAG).

## Overview

This system combines traditional machine learning approaches with advanced LLM-based analysis to provide high-accuracy fraud detection with human-understandable explanations. The system uses a two-stage approach:

1. **First-pass ML screening** - Fast and efficient analysis using gradient boosting models
2. **LLM-based RAG analysis** - In-depth analysis of suspicious transactions by comparing them to historical fraud patterns

## Project Structure

```
creditcardfrauddetection/
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── docker-compose.yml                # Docker composition configuration
├── Dockerfile                        # Docker container definition
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
│   │   ├── __init__.py
│   └── init_vector_db.py             # Initialize vector database
│   └── generate_sample_data.py       # Generate sample transaction data

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

2. Create a virtual environment and install dependencies:
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

# Start the API server in development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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