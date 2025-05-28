"""
Prometheus metrics instrumentation for the FastAPI application.
"""

from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Counter, Histogram, Gauge
import time

# Initialize instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_PROMETHEUS_METRICS",
)

# Custom metrics
FRAUD_DETECTION_COUNTER = Counter(
    "fraud_detection_total", 
    "Total number of fraud detection requests",
    ["result"]  # "fraud" or "legitimate"
)

FRAUD_CONFIDENCE_HISTOGRAM = Histogram(
    "fraud_confidence",
    "Histogram of fraud confidence scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
)

PROCESSING_TIME_HISTOGRAM = Histogram(
    "processing_time_ms",
    "Histogram of processing time in milliseconds",
    buckets=[50, 100, 200, 300, 500, 1000, 2000, 5000, 10000]
)

LLM_USAGE_COUNTER = Counter(
    "llm_usage_total",
    "Total number of LLM API calls"
)

REVIEW_REQUIRED_COUNTER = Counter(
    "review_required_total",
    "Total number of transactions requiring manual review"
)

ACTIVE_TRANSACTIONS_GAUGE = Gauge(
    "active_transactions",
    "Number of transactions currently being processed"
)

# Add default metrics
instrumentator.add(metrics.latency())
instrumentator.add(metrics.requests())
# instrumentator.add(metrics.requests_in_progress())  # Not available in this version
# instrumentator.add(metrics.dependent_requests())    # Not available in this version
# instrumentator.add(metrics.cpu_usage())            # Not available in this version
# instrumentator.add(metrics.memory_usage())         # Not available in this version

def track_fraud_detection(is_fraud: bool, confidence: float, processing_time: float, requires_review: bool):
    """Track fraud detection metrics."""
    result = "fraud" if is_fraud else "legitimate"
    FRAUD_DETECTION_COUNTER.labels(result=result).inc()
    FRAUD_CONFIDENCE_HISTOGRAM.observe(confidence)
    PROCESSING_TIME_HISTOGRAM.observe(processing_time)
    
    if requires_review:
        REVIEW_REQUIRED_COUNTER.inc()

def track_llm_usage():
    """Track LLM API usage."""
    LLM_USAGE_COUNTER.inc()

def start_transaction_tracking():
    """Start tracking a transaction."""
    ACTIVE_TRANSACTIONS_GAUGE.inc()
    return time.time()

def end_transaction_tracking(start_time: float) -> float:
    """End tracking a transaction and return the elapsed time in ms."""
    ACTIVE_TRANSACTIONS_GAUGE.dec()
    return (time.time() - start_time) * 1000

def setup_metrics(app):
    """Set up metrics for the FastAPI application."""
    instrumentator.instrument(app).expose(app, include_in_schema=False, should_gzip=True)
