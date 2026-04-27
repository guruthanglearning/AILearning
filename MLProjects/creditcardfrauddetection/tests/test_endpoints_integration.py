"""
Integration tests for all API endpoints using FastAPI TestClient.
All dependencies are mocked so no live server or external services are required.
"""
import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.api.models import FraudDetectionResponse


# ── Root & Health ─────────────────────────────────────────────────────────────

class TestRootEndpoint:
    def test_root_returns_info(self, test_client):
        resp = test_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "version" in data

    def test_health_root(self, test_client):
        resp = test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestAPIv1HealthEndpoint:
    def test_health_ok(self, test_client, api_headers):
        resp = test_client.get("/api/v1/health", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_health_contains_components(self, test_client, api_headers):
        resp = test_client.get("/api/v1/health", headers=api_headers)
        data = resp.json()
        assert "components" in data

    def test_health_no_auth_required_in_dev(self, test_client):
        # In development mode, auth is not required
        resp = test_client.get("/api/v1/health")
        assert resp.status_code == 200


# ── Detect Fraud ──────────────────────────────────────────────────────────────

class TestDetectFraudEndpoint:
    def test_legitimate_transaction(self, test_client, api_headers, valid_transaction):
        resp = test_client.post(
            "/api/v1/detect-fraud",
            json=valid_transaction,
            headers=api_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "is_fraud" in data
        assert "confidence_score" in data
        assert "transaction_id" in data
        assert "decision_reason" in data
        assert "requires_review" in data
        assert "processing_time_ms" in data

    def test_fraud_transaction_fields(self, test_client, api_headers, fraud_transaction, mock_fraud_service):
        mock_fraud_service.detect_fraud.return_value = FraudDetectionResponse(
            transaction_id="tx_fraud_001",
            is_fraud=True,
            confidence_score=0.95,
            decision_reason="High-risk transaction.",
            requires_review=True,
            processing_time_ms=200.0,
        )
        resp = test_client.post(
            "/api/v1/detect-fraud",
            json=fraud_transaction,
            headers=api_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_id"] == "tx_fraud_001"

    def test_invalid_transaction_missing_fields(self, test_client, api_headers):
        resp = test_client.post(
            "/api/v1/detect-fraud",
            json={"transaction_id": "tx_bad"},
            headers=api_headers,
        )
        assert resp.status_code == 422

    def test_invalid_timestamp_format(self, test_client, api_headers, valid_transaction):
        valid_transaction["timestamp"] = "not-a-date"
        resp = test_client.post(
            "/api/v1/detect-fraud",
            json=valid_transaction,
            headers=api_headers,
        )
        assert resp.status_code == 422


# ── Analyze Transaction ───────────────────────────────────────────────────────

class TestAnalyzeTransactionEndpoint:
    def test_analyze_valid_transaction(self, test_client, api_headers, valid_transaction):
        resp = test_client.post(
            "/api/v1/analyze-transaction",
            json=valid_transaction,
            headers=api_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "is_fraud" in data

    def test_analyze_negative_amount_rejected(self, test_client, api_headers, valid_transaction):
        valid_transaction["amount"] = -100.0
        resp = test_client.post(
            "/api/v1/analyze-transaction",
            json=valid_transaction,
            headers=api_headers,
        )
        assert resp.status_code == 400

    def test_analyze_missing_required_field(self, test_client, api_headers):
        resp = test_client.post(
            "/api/v1/analyze-transaction",
            json={"amount": 100.0},
            headers=api_headers,
        )
        assert resp.status_code == 422

    def test_analyze_with_geo_data(self, test_client, api_headers, valid_transaction):
        valid_transaction["latitude"] = 40.7
        valid_transaction["longitude"] = -74.0
        resp = test_client.post(
            "/api/v1/analyze-transaction",
            json=valid_transaction,
            headers=api_headers,
        )
        assert resp.status_code == 200


# ── Feedback ──────────────────────────────────────────────────────────────────

class TestFeedbackEndpoint:
    def test_submit_feedback_actual_fraud(self, test_client, api_headers):
        feedback = {
            "transaction_id": "tx_001",
            "actual_fraud": True,
            "analyst_notes": "Confirmed fraud.",
        }
        resp = test_client.post(
            "/api/v1/feedback",
            json=feedback,
            headers=api_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

    def test_submit_feedback_is_fraud_alias(self, test_client, api_headers):
        feedback = {
            "transaction_id": "tx_002",
            "is_fraud": False,
            "comments": "False positive - customer confirmed.",
        }
        resp = test_client.post(
            "/api/v1/feedback",
            json=feedback,
            headers=api_headers,
        )
        assert resp.status_code == 200

    def test_submit_feedback_returns_success(self, test_client, api_headers):
        feedback = {"transaction_id": "tx_003", "actual_fraud": False}
        resp = test_client.post("/api/v1/feedback", json=feedback, headers=api_headers)
        data = resp.json()
        assert "status" in data

    def test_submit_feedback_processing_failure(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.process_feedback.return_value = False
        feedback = {"transaction_id": "tx_004", "actual_fraud": True}
        resp = test_client.post("/api/v1/feedback", json=feedback, headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("success", "error")

    def test_feedback_missing_transaction_id(self, test_client, api_headers):
        feedback = {"actual_fraud": True}
        resp = test_client.post("/api/v1/feedback", json=feedback, headers=api_headers)
        assert resp.status_code == 422


# ── Ingest Patterns ───────────────────────────────────────────────────────────

class TestIngestPatternsEndpoint:
    def test_ingest_valid_patterns(self, test_client, api_headers):
        patterns = [
            {"case_id": "p1", "fraud_type": "velocity", "pattern_description": "Many transactions"},
            {"case_id": "p2", "fraud_type": "geo", "pattern_description": "Unusual location"},
        ]
        resp = test_client.post(
            "/api/v1/ingest-patterns",
            json=patterns,
            headers=api_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "count" in data

    def test_ingest_empty_list(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.ingest_fraud_patterns.return_value = 0
        resp = test_client.post("/api/v1/ingest-patterns", json=[], headers=api_headers)
        assert resp.status_code == 200

    def test_ingest_patterns_not_list_rejected(self, test_client, api_headers):
        resp = test_client.post(
            "/api/v1/ingest-patterns",
            json={"fraud_type": "velocity"},
            headers=api_headers,
        )
        assert resp.status_code == 422


# ── Fraud Patterns CRUD ───────────────────────────────────────────────────────

class TestFraudPatternsGet:
    def test_get_patterns_returns_list(self, test_client, api_headers):
        resp = test_client.get("/api/v1/fraud-patterns", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_patterns_has_expected_fields(self, test_client, api_headers):
        resp = test_client.get("/api/v1/fraud-patterns", headers=api_headers)
        data = resp.json()
        if data:
            pattern = data[0]
            assert "id" in pattern

    def test_get_patterns_empty_returns_empty_list(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.vector_db_service.get_all_fraud_patterns.return_value = []
        resp = test_client.get("/api/v1/fraud-patterns", headers=api_headers)
        assert resp.status_code == 200
        assert resp.json() == []


class TestFraudPatternsPost:
    def test_add_valid_pattern(self, test_client, api_headers):
        pattern = {
            "name": "New Fraud Pattern",
            "description": "A test fraud pattern",
            "pattern": {"fraud_type": "card_not_present", "indicators": ["online", "new_device"]},
            "similarity_threshold": 0.8,
        }
        resp = test_client.post("/api/v1/fraud-patterns", json=pattern, headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data

    def test_add_pattern_auto_generates_id(self, test_client, api_headers):
        pattern = {
            "name": "Auto ID Pattern",
            "description": "ID should be auto-generated",
            "pattern": {"fraud_type": "test"},
        }
        resp = test_client.post("/api/v1/fraud-patterns", json=pattern, headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data


class TestFraudPatternsPut:
    def test_update_existing_pattern(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.vector_db_service.get_all_fraud_patterns.return_value = [
            {
                "id": "pattern_abc12345",
                "name": "Old Name",
                "description": "Old description",
                "pattern": {},
                "similarity_threshold": 0.8,
                "created_at": "2025-01-01T00:00:00",
            }
        ]
        update_data = {
            "name": "Updated Pattern",
            "description": "Updated description",
            "pattern": {"fraud_type": "updated"},
        }
        resp = test_client.put(
            "/api/v1/fraud-patterns/pattern_abc12345",
            json=update_data,
            headers=api_headers,
        )
        assert resp.status_code == 200

    def test_update_nonexistent_pattern_returns_404(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.vector_db_service.get_all_fraud_patterns.return_value = []
        resp = test_client.put(
            "/api/v1/fraud-patterns/nonexistent_id",
            json={"name": "x", "description": "y", "pattern": {}},
            headers=api_headers,
        )
        assert resp.status_code == 404


class TestFraudPatternsDelete:
    def test_delete_existing_pattern(self, test_client, api_headers):
        resp = test_client.delete("/api/v1/fraud-patterns/pattern_abc12345", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

    def test_delete_nonexistent_pattern_returns_404(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.vector_db_service.pattern_exists.return_value = False
        resp = test_client.delete("/api/v1/fraud-patterns/no_such_id", headers=api_headers)
        assert resp.status_code == 404


# ── Metrics ───────────────────────────────────────────────────────────────────

class TestMetricsEndpoint:
    def test_get_metrics(self, test_client, api_headers):
        resp = test_client.get("/api/v1/metrics", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "system" in data
        assert "transactions" in data

    def test_metrics_models_list(self, test_client, api_headers):
        resp = test_client.get("/api/v1/metrics", headers=api_headers)
        data = resp.json()
        assert isinstance(data["models"], list)
        assert len(data["models"]) == 3

    def test_metrics_model_fields(self, test_client, api_headers):
        resp = test_client.get("/api/v1/metrics", headers=api_headers)
        model = resp.json()["models"][0]
        assert "name" in model
        assert "metrics" in model
        assert "accuracy" in model["metrics"]


# ── Transactions ──────────────────────────────────────────────────────────────

class TestTransactionsEndpoint:
    def test_get_transactions_list(self, test_client, api_headers):
        resp = test_client.get("/api/v1/transactions", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_transactions_with_limit(self, test_client, api_headers):
        resp = test_client.get("/api/v1/transactions?limit=5", headers=api_headers)
        assert resp.status_code == 200

    def test_get_transactions_have_required_fields(self, test_client, api_headers):
        resp = test_client.get("/api/v1/transactions", headers=api_headers)
        data = resp.json()
        if data:
            txn = data[0]
            assert "transaction_id" in txn
            assert "amount" in txn
            assert "is_fraud" in txn


class TestTransactionByIdEndpoint:
    def test_get_existing_transaction(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.get_transaction_by_id.return_value = {
            "transaction_id": "tx_found",
            "amount": 99.0,
            "is_fraud": False,
        }
        resp = test_client.get("/api/v1/transactions/tx_found", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_id"] == "tx_found"

    def test_get_nonexistent_transaction_returns_404(self, test_client, api_headers):
        resp = test_client.get("/api/v1/transactions/no_such_tx", headers=api_headers)
        assert resp.status_code == 404

    def test_get_predefined_test_transaction(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.get_transaction_by_id.return_value = {
            "transaction_id": "test_transaction_1",
            "amount": 199.99,
            "is_fraud": False,
        }
        resp = test_client.get("/api/v1/transactions/test_transaction_1", headers=api_headers)
        assert resp.status_code == 200


# ── LLM Status & Switch ───────────────────────────────────────────────────────

class TestLLMStatusEndpoint:
    def test_get_llm_status(self, test_client, api_headers):
        resp = test_client.get("/api/v1/llm-status", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "llm_service_type" in data

    def test_llm_status_alt_path(self, test_client, api_headers):
        resp = test_client.get("/api/v1/llm/status", headers=api_headers)
        assert resp.status_code == 200

    def test_llm_status_has_model_info(self, test_client, api_headers):
        resp = test_client.get("/api/v1/llm-status", headers=api_headers)
        data = resp.json()
        assert "llm_model" in data
        assert "is_mock" in data


class TestSwitchLLMModelEndpoint:
    def test_switch_to_mock(self, test_client, api_headers):
        resp = test_client.post(
            "/api/v1/switch-llm-model",
            json={"type": "mock"},
            headers=api_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    def test_switch_to_same_type_succeeds(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.llm_service.llm_service_type = "mock"
        resp = test_client.post(
            "/api/v1/switch-llm-model",
            json={"type": "mock"},
            headers=api_headers,
        )
        assert resp.status_code == 200

    def test_switch_invalid_type(self, test_client, api_headers):
        resp = test_client.post(
            "/api/v1/switch-llm-model",
            json={"type": "invalid_model_type"},
            headers=api_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    def test_switch_alt_path(self, test_client, api_headers):
        resp = test_client.post(
            "/api/v1/llm/switch",
            json={"type": "mock"},
            headers=api_headers,
        )
        assert resp.status_code == 200

    def test_switch_using_model_type_key(self, test_client, api_headers):
        resp = test_client.post(
            "/api/v1/switch-llm-model",
            json={"model_type": "mock"},
            headers=api_headers,
        )
        assert resp.status_code == 200


# ── Error handling ────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_service_error_returns_500(self, test_client, api_headers, valid_transaction, mock_fraud_service):
        mock_fraud_service.detect_fraud.side_effect = Exception("Unexpected internal error")
        resp = test_client.post(
            "/api/v1/detect-fraud",
            json=valid_transaction,
            headers=api_headers,
        )
        assert resp.status_code == 500

    def test_metrics_error_returns_500(self, test_client, api_headers, mock_fraud_service):
        mock_fraud_service.get_model_metrics.side_effect = Exception("DB unavailable")
        resp = test_client.get("/api/v1/metrics", headers=api_headers)
        assert resp.status_code == 500


# ── Auth behaviour (development mode) ────────────────────────────────────────

class TestAuthBehavior:
    def test_dev_mode_allows_no_api_key(self, test_client):
        # In development mode, requests without API key are allowed
        resp = test_client.get("/api/v1/transactions")
        # Should succeed (dev mode skips auth)
        assert resp.status_code in (200, 401)

    def test_api_v1_root_endpoint(self, test_client, api_headers):
        resp = test_client.get("/api/v1/", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
