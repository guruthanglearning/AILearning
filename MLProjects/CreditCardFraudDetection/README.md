# Real-Time Credit Card Fraud Detection System

A production-ready system for detecting fraud in real-time credit card transactions by leveraging both traditional machine learning techniques and Large Language Models with Retrieval Augmented Generation (RAG).

## Overview

This system combines traditional machine learning approaches with advanced LLM-based analysis to provide high-accuracy fraud detection with human-understandable explanations. The system uses a two-stage approach:

1. **First-pass ML screening** - Fast and efficient analysis using gradient boosting models
2. **LLM-based RAG analysis** - In-depth analysis of suspicious transactions by comparing them to historical fraud patterns

## Key Features

- Real-time transaction screening with sub-second response times
- Retrieval Augmented Generation (RAG) to leverage historical fraud patterns
- Feature engineering optimized for credit card transaction data
- Vector database for efficient similarity search of fraud patterns
- Confidence scoring and automatic/manual review routing
- Feedback loop for continual system improvement
- RESTful API for easy integration with payment processing systems
- Comprehensive logging and monitoring

## System Architecture

![System Architecture](https://example.com/architecture-diagram.png)

The system has several key components:

1. **Data Stream Processing** - Handles real-time transaction data
2. **Feature Engineering** - Extracts and normalizes transaction features
3. **Vector Database** - Stores historical fraud patterns and transaction metadata
4. **RAG-Based LLM Fraud Detection** - Uses LLM to analyze transactions with historical context
5. **Decision Engine** - Makes final fraud determination with confidence scoring
6. **Feedback Loop** - Continuous improvement through analyst feedback
7. **API Layer** - RESTful interface for integration with payment processing systems

## Getting Started

### Prerequisites

- Python 3.9+
- An OpenAI API key
- A Pinecone API key

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

## API Usage

### Fraud Detection Endpoint

```python
import requests
import json

url = "http://localhost:8000/detect-fraud"
headers = {"Content-Type": "application/json"}
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

response = requests.post(url, headers=headers, data=json.dumps(payload))
result = response.json()
print(result)
```

### Feedback Endpoint

```python
import requests
import json

url = "http://localhost:8000/feedback"
headers = {"Content-Type": "application/json"}
payload = {
    "transaction_id": "tx_123456789",
    "actual_fraud": True,
    "analyst_notes": "This was a case of account takeover. Customer confirmed they did not make this purchase."
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
result = response.json()
print(result)
```

## Testing

Run the test suite with:

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project uses OpenAI's GPT models for natural language processing
- Vector database functionality provided by Pinecone
- Built with FastAPI and LangChain