# Credit Card Fraud Detection - Test Suite

This directory contains various tests for the Credit Card Fraud Detection system.

## Test Types

### Unit Tests
- `test_api.py` - Unit tests for API endpoints using FastAPI TestClient
- `test_ml_model.py` - Unit tests for the ML model

### Integration Tests
- `test_api_integration.py` - End-to-end tests for the fraud detection API
- `test_feedback_integration.py` - Tests for the analyst feedback functionality
- `test_pattern_ingestion_integration.py` - Tests for ingesting new fraud patterns

## Running the Tests

### Unit Tests
Run with pytest:

```bash
# Run all unit tests
pytest

# Run specific test file
pytest test_api.py
```

### Integration Tests
These tests require the API server to be running. Start the server before running these tests:

```bash
# Start the server
python ../run_server.py

# In another terminal, run the integration tests
python test_api_integration.py
python test_feedback_integration.py
python test_pattern_ingestion_integration.py
```

## Notes
- The integration tests use the actual API endpoints and require the server to be running
- Make sure to initialize the vector database before running the tests: `python ../scripts/init_vector_db.py`
- The API key used in tests is "test-api-key" - you can modify this in each test file if needed
