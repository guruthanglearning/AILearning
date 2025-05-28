"""
Test API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.models import Transaction, FraudDetectionResponse, FeedbackModel

client = TestClient(app)

@pytest.fixture
def mock_fraud_service():
    """Create a mock fraud detection service."""
    with patch("app.api.dependencies.get_fraud_detection_service") as mock:
        # Create a mock service
        service = MagicMock()
        
        # Configure the mock to return a valid response
        service.detect_fraud.return_value = FraudDetectionResponse(
            transaction_id="tx_test_123",
            is_fraud=False,
            confidence_score=0.9,
            decision_reason="Test transaction",
            requires_review=False,
            processing_time_ms=100.0
        )
        
        # Configure feedback processing to return True (success)
        service.process_feedback.return_value = True
        
        # Set up system status
        service.get_system_status.return_value = {
            "status": "healthy",
            "ml_model": {"type": "XGBClassifier"},
            "llm": {"model": "gpt-4-turbo-preview"},
            "vector_db": {"count": 10, "type": "chromadb"},
            "config": {
                "confidence_threshold": 0.85,
                "similarity_threshold": 0.75,
                "transaction_history_window": 30
            }
        }
        
        # Return the mock
        mock.return_value = service
        yield service

@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing."""
    return {
        "transaction_id": "tx_test_123",
        "card_id": "card_test_456",
        "merchant_id": "merch_test_789",
        "timestamp": "2025-05-07T10:23:45Z", 
        "amount": 100.00,
        "merchant_category": "Test",
        "merchant_name": "Test Store",
        "merchant_country": "US",
        "merchant_zip": "12345",
        "customer_id": "cust_test_123",
        "is_online": True,
        "device_id": "dev_test_123",
        "ip_address": "127.0.0.1",
        "currency": "USD",
        "latitude": 40.0,
        "longitude": -80.0
    }

@pytest.fixture
def sample_feedback():
    """Create a sample feedback for testing."""
    return {
        "transaction_id": "tx_test_123",
        "actual_fraud": True,
        "analyst_notes": "Test feedback"
    }

def test_detect_fraud(mock_fraud_service, sample_transaction):
    """Test the detect-fraud endpoint."""
    # Call the endpoint
    response = client.post(
        "/api/v1/detect-fraud",
        json=sample_transaction,
        headers={"X-API-Key": "development_api_key"}
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "tx_test_123"
    assert isinstance(data["is_fraud"], bool)
    assert isinstance(data["confidence_score"], float)
    
    # Verify the mock was called with the correct transaction
    # Convert the passed transaction to a dict for comparison
    call_args = mock_fraud_service.detect_fraud.call_args[0][0]
    assert call_args.transaction_id == sample_transaction["transaction_id"]
    assert call_args.amount == sample_transaction["amount"]

def test_submit_feedback(mock_fraud_service, sample_feedback):
    """Test the feedback endpoint."""
    # Call the endpoint
    response = client.post(
        "/api/v1/feedback",
        json=sample_feedback,
        headers={"X-API-Key": "development_api_key"}
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify the mock was called with the correct feedback
    # Convert the passed feedback to a dict for comparison
    call_args = mock_fraud_service.process_feedback.call_args[0][0]
    assert call_args.transaction_id == sample_feedback["transaction_id"]
    assert call_args.actual_fraud == sample_feedback["actual_fraud"]

def test_health_check():
    """Test the health check endpoint."""
    # Call the endpoint
    response = client.get("/health")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
