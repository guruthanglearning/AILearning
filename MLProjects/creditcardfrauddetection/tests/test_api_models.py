"""
Unit tests for Pydantic API models.
Tests validation, defaults, and model behavior.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.api.models import (
    Transaction,
    FraudDetectionResponse,
    FeedbackModel,
    HealthCheckResponse,
    ErrorResponse,
    ModelMetricsResponse,
)


# ── Transaction ──────────────────────────────────────────────────────────────

class TestTransaction:
    def _valid(self, **overrides):
        data = {
            "transaction_id": "tx_001",
            "card_id": "card_001",
            "merchant_id": "merch_001",
            "timestamp": "2025-05-07T10:23:45Z",
            "amount": 100.0,
            "merchant_category": "Grocery",
            "merchant_name": "Local Market",
            "merchant_country": "US",
            "customer_id": "cust_001",
            "is_online": False,
            "currency": "USD",
        }
        data.update(overrides)
        return data

    def test_valid_transaction(self):
        txn = Transaction(**self._valid())
        assert txn.transaction_id == "tx_001"
        assert txn.amount == 100.0

    def test_optional_fields_default_none(self):
        txn = Transaction(**self._valid())
        assert txn.merchant_name is None or txn.merchant_name == "Local Market"
        assert txn.latitude is None
        assert txn.longitude is None

    def test_with_geo_data(self):
        txn = Transaction(**self._valid(latitude=40.7, longitude=-74.0))
        assert txn.latitude == 40.7
        assert txn.longitude == -74.0

    def test_invalid_timestamp_raises(self):
        with pytest.raises(ValidationError):
            Transaction(**self._valid(timestamp="not-a-date"))

    def test_valid_iso_timestamp(self):
        txn = Transaction(**self._valid(timestamp="2025-12-31T23:59:59Z"))
        assert txn.timestamp == "2025-12-31T23:59:59Z"

    def test_negative_amount_allowed(self):
        # Model doesn't validate negative amounts at model level
        txn = Transaction(**self._valid(amount=-10.0))
        assert txn.amount == -10.0

    def test_is_online_bool(self):
        txn = Transaction(**self._valid(is_online=True))
        assert txn.is_online is True

    def test_missing_required_field_raises(self):
        data = self._valid()
        del data["transaction_id"]
        with pytest.raises(ValidationError):
            Transaction(**data)


# ── FraudDetectionResponse ───────────────────────────────────────────────────

class TestFraudDetectionResponse:
    def test_create_response(self):
        resp = FraudDetectionResponse(
            transaction_id="tx_001",
            is_fraud=False,
            confidence_score=0.85,
            decision_reason="Legitimate",
            requires_review=False,
            processing_time_ms=100.0,
        )
        assert resp.is_fraud is False
        assert resp.confidence_score == 0.85

    def test_fraud_true(self):
        resp = FraudDetectionResponse(
            transaction_id="tx_002",
            is_fraud=True,
            confidence_score=0.95,
            decision_reason="Fraud detected",
            requires_review=True,
            processing_time_ms=200.0,
        )
        assert resp.is_fraud is True

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            FraudDetectionResponse(
                transaction_id="tx_003",
                is_fraud=True,
                # missing confidence_score
                decision_reason="x",
                requires_review=False,
                processing_time_ms=50.0,
            )


# ── FeedbackModel ────────────────────────────────────────────────────────────

class TestFeedbackModel:
    def test_basic_feedback(self):
        fb = FeedbackModel(transaction_id="tx_001", actual_fraud=True)
        assert fb.transaction_id == "tx_001"
        assert fb.actual_fraud is True

    def test_is_fraud_maps_to_actual_fraud(self):
        fb = FeedbackModel(transaction_id="tx_002", is_fraud=True)
        assert fb.actual_fraud is True

    def test_comments_map_to_analyst_notes(self):
        fb = FeedbackModel(transaction_id="tx_003", actual_fraud=False, comments="OK")
        assert fb.analyst_notes == "OK"

    def test_optional_fields_default_none(self):
        fb = FeedbackModel(transaction_id="tx_004", actual_fraud=False)
        assert fb.analyst_notes is None
        assert fb.user_id is None

    def test_all_optional_fields(self):
        fb = FeedbackModel(
            transaction_id="tx_005",
            actual_fraud=True,
            analyst_notes="fraud",
            feedback_type="false_negative",
            confidence=0.9,
            user_id="analyst_1",
        )
        assert fb.user_id == "analyst_1"
        assert fb.confidence == 0.9


# ── HealthCheckResponse ──────────────────────────────────────────────────────

class TestHealthCheckResponse:
    def test_create_healthy(self):
        resp = HealthCheckResponse(status="healthy")
        assert resp.status == "healthy"
        assert resp.version == "1.0.0"
        assert resp.components == {}

    def test_with_components(self):
        resp = HealthCheckResponse(
            status="healthy",
            components={"ml_model": "ok", "vector_db": "ok"}
        )
        assert resp.components["ml_model"] == "ok"

    def test_unhealthy_status(self):
        resp = HealthCheckResponse(status="unhealthy", components={"error": "db down"})
        assert resp.status == "unhealthy"


# ── ErrorResponse ────────────────────────────────────────────────────────────

class TestErrorResponse:
    def test_create_error(self):
        err = ErrorResponse(detail="Something went wrong")
        assert err.detail == "Something went wrong"
        assert err.code is None
        assert err.timestamp is not None

    def test_with_code(self):
        err = ErrorResponse(detail="Not found", code="404")
        assert err.code == "404"


# ── ModelMetricsResponse ─────────────────────────────────────────────────────

class TestModelMetricsResponse:
    def _make_metric(self):
        return {
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.90,
            "f1_score": 0.91,
            "auc": 0.97,
            "latency_ms": 45.0,
            "throughput": 120.0,
        }

    def test_create_metrics_response(self):
        resp = ModelMetricsResponse(
            timestamp=datetime.now().isoformat(),
            models=[{
                "name": "ML Model",
                "type": "traditional",
                "version": "1.0.0",
                "last_trained": "2025-01-01T00:00:00",
                "metrics": self._make_metric(),
            }],
            system={
                "uptime_hours": 100.0,
                "requests_per_minute": 50.0,
                "avg_response_time_ms": 70.0,
                "error_rate": 0.001,
                "cpu_usage": 0.3,
                "memory_usage": 0.4,
                "disk_usage": 0.35,
            },
            transactions={
                "total": 15000,
                "fraudulent": 450,
                "fraud_rate": 0.03,
                "avg_transaction_amount": 125.0,
                "avg_fraudulent_amount": 450.0,
            }
        )
        assert resp.models[0].name == "ML Model"
        assert resp.system.uptime_hours == 100.0
        assert resp.transactions.total == 15000
