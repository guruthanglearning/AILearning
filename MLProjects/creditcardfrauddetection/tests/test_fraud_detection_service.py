"""
Unit tests for the FraudDetectionService.
Tests the core fraud detection pipeline, feedback processing, and system status.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock

from app.api.models import Transaction, FraudDetectionResponse, FeedbackModel, DetailedFraudAnalysis
from app.services.fraud_detection_service import FraudDetectionService


def make_transaction(**kwargs):
    """Create a Transaction with sensible defaults."""
    defaults = {
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
    defaults.update(kwargs)
    return Transaction(**defaults)


def make_fraud_service():
    """
    Create a FraudDetectionService with mocked dependencies so tests
    do not require a live Ollama/OpenAI/Chroma instance.
    """
    with patch("app.services.fraud_detection_service.MLModel") as MockML, \
         patch("app.services.fraud_detection_service.VectorDBService") as MockVDB, \
         patch("app.services.fraud_detection_service.LLMService") as MockLLM:

        mock_ml = MagicMock()
        mock_ml.predict.return_value = (0.2, 0.85)
        MockML.return_value = mock_ml

        mock_vdb = MagicMock()
        mock_vdb.search_similar_patterns.return_value = []
        mock_vdb.get_stats.return_value = {"vector_store_type": "Chroma"}
        MockVDB.return_value = mock_vdb

        mock_llm = MagicMock()
        mock_llm.llm_service_type = "enhanced_mock"
        mock_llm.analyze_transaction.return_value = DetailedFraudAnalysis(
            fraud_probability=0.2,
            confidence=0.85,
            reasoning="Legitimate transaction.",
            recommendation="Approve",
            full_analysis="Full analysis text.",
            retrieved_patterns=[]
        )
        MockLLM.return_value = mock_llm

        service = FraudDetectionService()
        return service


class TestDetectFraud:
    def test_returns_fraud_detection_response(self):
        service = make_fraud_service()
        txn = make_transaction()
        result = service.detect_fraud(txn)
        assert isinstance(result, FraudDetectionResponse)

    def test_legitimate_transaction_low_score(self):
        service = make_fraud_service()
        service.ml_model.predict.return_value = (0.1, 0.95)
        txn = make_transaction(amount=20.0, merchant_country="US")
        result = service.detect_fraud(txn)
        assert isinstance(result.confidence_score, float)
        assert 0.0 <= result.confidence_score <= 1.0

    def test_sanctioned_country_auto_fraud(self):
        service = make_fraud_service()
        txn = make_transaction(merchant_country="RU")
        result = service.detect_fraud(txn)
        assert result.is_fraud is True
        assert result.confidence_score >= 0.9

    def test_sanctioned_country_no_review_needed(self):
        service = make_fraud_service()
        txn = make_transaction(merchant_country="KP")
        result = service.detect_fraud(txn)
        assert result.requires_review is False

    def test_response_has_required_fields(self):
        service = make_fraud_service()
        txn = make_transaction()
        result = service.detect_fraud(txn)
        assert result.transaction_id == "tx_test_001"
        assert isinstance(result.is_fraud, bool)
        assert isinstance(result.confidence_score, float)
        assert isinstance(result.decision_reason, str)
        assert isinstance(result.requires_review, bool)
        assert result.processing_time_ms >= 0

    def test_processing_time_recorded(self):
        service = make_fraud_service()
        txn = make_transaction()
        result = service.detect_fraud(txn)
        assert result.processing_time_ms > 0

    def test_error_returns_safe_default(self):
        service = make_fraud_service()
        service.ml_model.predict.side_effect = RuntimeError("model failure")
        txn = make_transaction()
        result = service.detect_fraud(txn)
        # Should not raise - returns conservative default
        assert isinstance(result, FraudDetectionResponse)
        assert result.requires_review is True
        assert result.is_fraud is False

    def test_high_risk_transaction(self):
        service = make_fraud_service()
        service.ml_model.predict.return_value = (0.85, 0.9)
        service.llm_service.analyze_transaction.return_value = DetailedFraudAnalysis(
            fraud_probability=0.9,
            confidence=0.95,
            reasoning="High fraud risk.",
            recommendation="Deny",
            full_analysis="Full analysis text.",
            retrieved_patterns=[]
        )
        txn = make_transaction(amount=5000.0, merchant_country="NG", is_online=True)
        result = service.detect_fraud(txn)
        assert isinstance(result.is_fraud, bool)


class TestProcessFeedback:
    def test_feedback_success(self):
        service = make_fraud_service()
        feedback = FeedbackModel(
            transaction_id="tx_001",
            actual_fraud=True,
            analyst_notes="Confirmed fraud case",
        )
        result = service.process_feedback(feedback)
        assert result is True

    def test_feedback_false_positive(self):
        service = make_fraud_service()
        feedback = FeedbackModel(
            transaction_id="tx_002",
            actual_fraud=False,
            analyst_notes="Customer confirmed legitimate purchase",
        )
        result = service.process_feedback(feedback)
        assert result is True

    def test_feedback_without_notes(self):
        service = make_fraud_service()
        feedback = FeedbackModel(
            transaction_id="tx_003",
            actual_fraud=True,
        )
        result = service.process_feedback(feedback)
        assert result is True

    def test_feedback_error_returns_false(self):
        service = make_fraud_service()
        service.vector_db_service.add_feedback_as_pattern.side_effect = RuntimeError("DB error")
        feedback = FeedbackModel(
            transaction_id="tx_004",
            actual_fraud=True,
            analyst_notes="Fraud notes",
        )
        result = service.process_feedback(feedback)
        assert result is False


class TestGetSystemStatus:
    def test_returns_dict(self):
        service = make_fraud_service()
        status = service.get_system_status()
        assert isinstance(status, dict)

    def test_status_operational(self):
        service = make_fraud_service()
        status = service.get_system_status()
        assert status["status"] == "operational"

    def test_contains_required_keys(self):
        service = make_fraud_service()
        status = service.get_system_status()
        assert "ml_model" in status
        assert "llm" in status
        assert "vector_db" in status
        assert "config" in status


class TestGetModelMetrics:
    def test_returns_dict(self):
        service = make_fraud_service()
        metrics = service.get_model_metrics()
        assert isinstance(metrics, dict)

    def test_contains_models(self):
        service = make_fraud_service()
        metrics = service.get_model_metrics()
        assert "models" in metrics
        assert isinstance(metrics["models"], list)
        assert len(metrics["models"]) == 3

    def test_contains_system_metrics(self):
        service = make_fraud_service()
        metrics = service.get_model_metrics()
        assert "system" in metrics
        assert "transactions" in metrics


class TestGetTransactionHistory:
    def test_returns_list(self):
        service = make_fraud_service()
        transactions = service.get_transaction_history(limit=10)
        assert isinstance(transactions, list)

    def test_respects_limit(self):
        service = make_fraud_service()
        transactions = service.get_transaction_history(limit=5)
        assert len(transactions) <= 5

    def test_transactions_have_required_fields(self):
        service = make_fraud_service()
        transactions = service.get_transaction_history(limit=1)
        if transactions:
            txn = transactions[0]
            assert "transaction_id" in txn
            assert "amount" in txn
            assert "is_fraud" in txn


class TestGetTransactionById:
    def test_known_test_transaction(self):
        service = make_fraud_service()
        txn = service.get_transaction_by_id("test_transaction_1")
        assert txn is not None
        assert txn["transaction_id"] == "test_transaction_1"

    def test_known_fraud_test_transaction(self):
        service = make_fraud_service()
        txn = service.get_transaction_by_id("test_fraud_transaction_1")
        assert txn is not None
        assert txn["is_fraud"] is True

    def test_nonexistent_transaction_returns_none(self):
        service = make_fraud_service()
        txn = service.get_transaction_by_id("nonexistent_tx_id_xyz")
        assert txn is None


class TestIngestFraudPatterns:
    def test_ingest_patterns_success(self):
        service = make_fraud_service()
        service.vector_db_service.add_fraud_patterns.return_value = 3
        patterns = [
            {"case_id": "p1", "fraud_type": "velocity"},
            {"case_id": "p2", "fraud_type": "geo"},
            {"case_id": "p3", "fraud_type": "card_not_present"},
        ]
        count = service.ingest_fraud_patterns(patterns)
        assert count == 3

    def test_ingest_patterns_error_propagates(self):
        service = make_fraud_service()
        service.vector_db_service.add_fraud_patterns.side_effect = RuntimeError("DB error")
        with pytest.raises(RuntimeError):
            service.ingest_fraud_patterns([{"case_id": "p1"}])
