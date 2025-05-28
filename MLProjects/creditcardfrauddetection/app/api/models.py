"""
Pydantic models for API request and response schemas.
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

class Transaction(BaseModel):
    """
    Model representing a credit card transaction to be analyzed for fraud.
    """
    transaction_id: str
    card_id: str
    merchant_id: str
    timestamp: str
    amount: float
    merchant_category: str
    merchant_name: Optional[str] = None
    merchant_country: str
    merchant_zip: Optional[str] = None
    customer_id: str
    is_online: bool
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    currency: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate that timestamp is in ISO format."""
        try:
            # Try to parse the timestamp to ensure it's valid
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('timestamp must be in ISO format (e.g., "2025-05-07T10:23:45Z")')
    
    class Config:
        schema_extra = {
            "example": {
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
        }

class FraudDetectionResponse(BaseModel):
    """
    Model representing the fraud detection response.
    """
    transaction_id: str
    is_fraud: bool
    confidence_score: float
    decision_reason: str
    requires_review: bool
    processing_time_ms: float

class DetailedFraudAnalysis(BaseModel):
    """
    Model representing a detailed fraud analysis from the LLM.
    For internal use and auditing.
    """
    fraud_probability: float
    confidence: float
    reasoning: str
    recommendation: str
    full_analysis: str
    retrieved_patterns: Optional[List[str]] = None

class FeedbackModel(BaseModel):
    """
    Model for submitting analyst feedback on a transaction.
    Used to improve the system over time.
    """
    transaction_id: str
    actual_fraud: bool
    analyst_notes: Optional[str] = None

class HealthCheckResponse(BaseModel):
    """
    Model for health check response.
    """
    status: str
    version: str = "1.0.0"
    components: Dict[str, Any] = {}

class TokenResponse(BaseModel):
    """
    Model for token response.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds

class ErrorResponse(BaseModel):
    """
    Model for error response.
    """
    detail: str
    code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class FraudPattern(BaseModel):
    """
    Model representing a fraud pattern for detection.
    """
    id: Optional[str] = None
    name: str
    description: str
    pattern: Dict[str, Any]
    similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    created_at: Optional[str] = None

    @validator('created_at', pre=True, always=True)
    def set_created_at(cls, v):
        """Set created_at to current time if not provided."""
        if v is None:
            return datetime.now().isoformat()
        return v
    
    @validator('id', pre=True, always=True)
    def set_id(cls, v):
        """Set ID if not provided."""
        if v is None:
            import uuid
            return f"pattern_{str(uuid.uuid4())[:8]}"
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "High-value Electronics Purchase",
                "description": "Unusually high-value purchase from electronics retailer, especially from new device or unusual location.",
                "pattern": {
                    "merchant_category": "Electronics",
                    "transaction_type": "online",
                    "indicators": ["high_amount", "new_device", "unusual_location"]
                },
                "similarity_threshold": 0.85
            }
        }

class FraudPatternResponse(BaseModel):
    """
    Model for response when adding or retrieving a fraud pattern.
    """
    id: str
    name: str
    description: str
    pattern: Dict[str, Any]
    similarity_threshold: float
    created_at: str