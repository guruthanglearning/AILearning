"""
Shared pytest fixtures for all tests.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.api.models import DetailedFraudAnalysis, FraudDetectionResponse


# ── Shared transaction payload ────────────────────────────────────────────────

@pytest.fixture
def valid_transaction():
    """A valid transaction payload for API testing."""
    return {
        "transaction_id": "tx_test_001",
        "card_id": "card_001",
        "merchant_id": "merch_001",
        "timestamp": "2025-05-07T10:23:45Z",
        "amount": 50.0,
        "merchant_category": "Grocery",
        "merchant_name": "Local Market",
        "merchant_country": "US",
        "customer_id": "cust_001",
        "is_online": False,
        "currency": "USD",
    }


@pytest.fixture
def fraud_transaction():
    """A high-risk transaction payload."""
    return {
        "transaction_id": "tx_fraud_001",
        "card_id": "card_002",
        "merchant_id": "merch_999",
        "timestamp": "2025-05-07T02:15:00Z",
        "amount": 5000.0,
        "merchant_category": "Electronics",
        "merchant_name": "Suspicious Store",
        "merchant_country": "NG",
        "customer_id": "cust_002",
        "is_online": True,
        "currency": "USD",
        "device_id": "dev_new_xyz",
        "ip_address": "203.0.113.45",
    }


@pytest.fixture
def api_headers():
    """Standard API headers with auth key."""
    return {
        "Content-Type": "application/json",
        "X-API-Key": "development_api_key_for_testing",
    }


# ── Mock fraud service factory ────────────────────────────────────────────────

def _make_mock_fraud_service():
    """Create a mock FraudDetectionService with sensible defaults."""
    mock_service = MagicMock()

    mock_service.detect_fraud.return_value = FraudDetectionResponse(
        transaction_id="tx_test_001",
        is_fraud=False,
        confidence_score=0.85,
        decision_reason="Legitimate transaction.",
        requires_review=False,
        processing_time_ms=100.0,
    )
    mock_service.process_feedback.return_value = True
    mock_service.ingest_fraud_patterns.return_value = 2
    mock_service.get_system_status.return_value = {
        "status": "operational",
        "ml_model": {"type": "MLModel"},
        "llm": {"service_type": "enhanced_mock"},
        "vector_db": {"vector_store_type": "Chroma"},
        "config": {},
    }
    mock_service.get_model_metrics.return_value = {
        "timestamp": "2025-05-07T10:00:00",
        "models": [
            {
                "name": "ML Model",
                "type": "traditional",
                "version": "1.2.3",
                "last_trained": "2025-05-15T09:30:00Z",
                "metrics": {
                    "accuracy": 0.95,
                    "precision": 0.93,
                    "recall": 0.90,
                    "f1_score": 0.91,
                    "auc": 0.97,
                    "latency_ms": 45.0,
                    "throughput": 120.0,
                },
            },
            {
                "name": "LLM+RAG",
                "type": "advanced",
                "version": "0.9.1",
                "last_trained": "2025-05-20T14:45:00Z",
                "metrics": {
                    "accuracy": 0.97,
                    "precision": 0.94,
                    "recall": 0.92,
                    "f1_score": 0.93,
                    "auc": 0.98,
                    "latency_ms": 78.0,
                    "throughput": 85.0,
                },
            },
            {
                "name": "Combined",
                "type": "hybrid",
                "version": "0.5.0",
                "last_trained": "2025-05-22T11:15:00Z",
                "metrics": {
                    "accuracy": 0.975,
                    "precision": 0.958,
                    "recall": 0.943,
                    "f1_score": 0.950,
                    "auc": 0.986,
                    "latency_ms": 92.7,
                    "throughput": 78.9,
                },
            },
        ],
        "system": {
            "uptime_hours": 150.0,
            "requests_per_minute": 40.0,
            "avg_response_time_ms": 70.0,
            "error_rate": 0.002,
            "cpu_usage": 0.30,
            "memory_usage": 0.40,
            "disk_usage": 0.35,
        },
        "transactions": {
            "total": 15000,
            "fraudulent": 450,
            "fraud_rate": 0.03,
            "avg_transaction_amount": 125.0,
            "avg_fraudulent_amount": 450.0,
        },
    }
    mock_service.get_transaction_history.return_value = [
        {
            "transaction_id": "tx_mock_001",
            "timestamp": "2025-06-01T12:00:00",
            "amount": 50.0,
            "merchant_name": "FashionHub",
            "merchant_category": "Retail",
            "is_fraud": False,
            "confidence_score": 0.9,
            "requires_review": False,
            "processing_time_ms": 100.0,
            "decision_reason": "Legitimate",
        }
    ]
    mock_service.get_transaction_by_id.return_value = None

    mock_service.vector_db_service.get_all_fraud_patterns.return_value = [
        {
            "id": "pattern_abc12345",
            "name": "Test Pattern",
            "description": "Test description",
            "pattern": {"fraud_type": "velocity"},
            "similarity_threshold": 0.8,
            "created_at": "2025-01-01T00:00:00",
        }
    ]
    mock_service.vector_db_service.pattern_exists.return_value = True
    mock_service.vector_db_service.delete_fraud_pattern.return_value = True
    mock_service.vector_db_service.add_fraud_patterns.return_value = 1

    mock_service.llm_service.llm_service_type = "enhanced_mock"

    return mock_service


@pytest.fixture
def mock_fraud_service():
    return _make_mock_fraud_service()


@pytest.fixture
def test_client(mock_fraud_service):
    """FastAPI TestClient with mocked fraud service dependency."""
    from app.main import app
    from app.api.dependencies import get_fraud_detection_service

    app.dependency_overrides[get_fraud_detection_service] = lambda: mock_fraud_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
