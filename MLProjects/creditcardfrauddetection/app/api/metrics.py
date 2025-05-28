"""
Metrics models for the API.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class ModelMetric(BaseModel):
    """Individual model metric values."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc: float
    latency_ms: float
    throughput: float

class ModelData(BaseModel):
    """Data for a specific model including metrics."""
    name: str
    type: str
    version: str
    last_trained: str
    metrics: ModelMetric

class SystemMetrics(BaseModel):
    """System performance metrics."""
    uptime_hours: float
    requests_per_minute: float
    avg_response_time_ms: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float

class TransactionMetrics(BaseModel):
    """Transaction statistics."""
    total: int
    fraudulent: int
    fraud_rate: float
    avg_transaction_amount: float
    avg_fraudulent_amount: float

class ModelMetricsResponse(BaseModel):
    """Response model for model metrics endpoint."""
    timestamp: str
    models: List[ModelData]
    system: SystemMetrics
    transactions: TransactionMetrics
