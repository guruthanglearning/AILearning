"""
Tests for app/core/metrics.py (currently 62% coverage)
and app/api/metrics.py (currently 0% coverage).
"""
import pytest


# ── app/core/metrics.py ───────────────────────────────────────────────────────

class TestTrackFraudDetection:
    def test_fraud_case(self):
        from app.core.metrics import track_fraud_detection
        # Should not raise
        track_fraud_detection(is_fraud=True, confidence=0.92, processing_time=150.0, requires_review=False)

    def test_legitimate_case(self):
        from app.core.metrics import track_fraud_detection
        track_fraud_detection(is_fraud=False, confidence=0.10, processing_time=80.0, requires_review=False)

    def test_requires_review_true(self):
        from app.core.metrics import track_fraud_detection
        track_fraud_detection(is_fraud=False, confidence=0.55, processing_time=200.0, requires_review=True)

    def test_requires_review_false(self):
        from app.core.metrics import track_fraud_detection
        track_fraud_detection(is_fraud=True, confidence=0.95, processing_time=300.0, requires_review=False)

    def test_edge_confidence_zero(self):
        from app.core.metrics import track_fraud_detection
        track_fraud_detection(is_fraud=False, confidence=0.0, processing_time=50.0, requires_review=False)

    def test_edge_confidence_one(self):
        from app.core.metrics import track_fraud_detection
        track_fraud_detection(is_fraud=True, confidence=1.0, processing_time=50.0, requires_review=True)


class TestTrackLlmUsage:
    def test_increments_without_error(self):
        from app.core.metrics import track_llm_usage
        track_llm_usage()
        track_llm_usage()


class TestTransactionTracking:
    def test_start_returns_float(self):
        from app.core.metrics import start_transaction_tracking
        t = start_transaction_tracking()
        assert isinstance(t, float)
        assert t > 0

    def test_end_returns_elapsed_ms(self):
        from app.core.metrics import start_transaction_tracking, end_transaction_tracking
        import time
        start = start_transaction_tracking()
        time.sleep(0.01)  # 10ms
        elapsed = end_transaction_tracking(start)
        assert isinstance(elapsed, float)
        assert elapsed >= 0

    def test_start_end_paired(self):
        from app.core.metrics import start_transaction_tracking, end_transaction_tracking
        start1 = start_transaction_tracking()
        start2 = start_transaction_tracking()
        end_transaction_tracking(start1)
        end_transaction_tracking(start2)


# ── app/api/metrics.py Pydantic models ───────────────────────────────────────

class TestModelMetric:
    def test_instantiation(self):
        from app.api.metrics import ModelMetric
        m = ModelMetric(
            accuracy=0.95, precision=0.93, recall=0.90,
            f1_score=0.91, auc=0.97, latency_ms=45.0, throughput=120.0,
        )
        assert m.accuracy == 0.95
        assert m.f1_score == 0.91

    def test_all_fields_present(self):
        from app.api.metrics import ModelMetric
        m = ModelMetric(
            accuracy=0.8, precision=0.8, recall=0.8,
            f1_score=0.8, auc=0.8, latency_ms=100.0, throughput=50.0,
        )
        assert m.latency_ms == 100.0
        assert m.throughput == 50.0


class TestModelData:
    def test_instantiation(self):
        from app.api.metrics import ModelData, ModelMetric
        metric = ModelMetric(
            accuracy=0.95, precision=0.93, recall=0.90,
            f1_score=0.91, auc=0.97, latency_ms=45.0, throughput=120.0,
        )
        m = ModelData(
            name="XGBoost", type="traditional", version="1.0.0",
            last_trained="2025-01-01T00:00:00Z", metrics=metric,
        )
        assert m.name == "XGBoost"
        assert m.metrics.accuracy == 0.95


class TestSystemMetrics:
    def test_instantiation(self):
        from app.api.metrics import SystemMetrics
        s = SystemMetrics(
            uptime_hours=100.0, requests_per_minute=50.0,
            avg_response_time_ms=80.0, error_rate=0.01,
            cpu_usage=0.30, memory_usage=0.45, disk_usage=0.20,
        )
        assert s.uptime_hours == 100.0
        assert s.error_rate == 0.01


class TestTransactionMetrics:
    def test_instantiation(self):
        from app.api.metrics import TransactionMetrics
        t = TransactionMetrics(
            total=10000, fraudulent=300, fraud_rate=0.03,
            avg_transaction_amount=125.0, avg_fraudulent_amount=450.0,
        )
        assert t.total == 10000
        assert t.fraud_rate == 0.03


class TestModelMetricsResponse:
    def test_instantiation(self):
        from app.api.metrics import ModelMetricsResponse, ModelData, ModelMetric, SystemMetrics, TransactionMetrics
        metric = ModelMetric(
            accuracy=0.95, precision=0.93, recall=0.90,
            f1_score=0.91, auc=0.97, latency_ms=45.0, throughput=120.0,
        )
        model = ModelData(
            name="XGBoost", type="traditional", version="1.0.0",
            last_trained="2025-01-01T00:00:00Z", metrics=metric,
        )
        system = SystemMetrics(
            uptime_hours=100.0, requests_per_minute=50.0,
            avg_response_time_ms=80.0, error_rate=0.01,
            cpu_usage=0.30, memory_usage=0.45, disk_usage=0.20,
        )
        transactions = TransactionMetrics(
            total=10000, fraudulent=300, fraud_rate=0.03,
            avg_transaction_amount=125.0, avg_fraudulent_amount=450.0,
        )
        response = ModelMetricsResponse(
            timestamp="2025-01-01T00:00:00Z",
            models=[model],
            system=system,
            transactions=transactions,
        )
        assert response.timestamp == "2025-01-01T00:00:00Z"
        assert len(response.models) == 1
        assert response.models[0].name == "XGBoost"

    def test_empty_models_list(self):
        from app.api.metrics import ModelMetricsResponse, SystemMetrics, TransactionMetrics
        system = SystemMetrics(
            uptime_hours=0.0, requests_per_minute=0.0,
            avg_response_time_ms=0.0, error_rate=0.0,
            cpu_usage=0.0, memory_usage=0.0, disk_usage=0.0,
        )
        transactions = TransactionMetrics(
            total=0, fraudulent=0, fraud_rate=0.0,
            avg_transaction_amount=0.0, avg_fraudulent_amount=0.0,
        )
        response = ModelMetricsResponse(
            timestamp="2025-01-01T00:00:00Z",
            models=[],
            system=system,
            transactions=transactions,
        )
        assert response.models == []
