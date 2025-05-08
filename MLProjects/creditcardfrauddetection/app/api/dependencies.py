"""
Dependency injection for the FastAPI application.
"""

import logging
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.services.fraud_detection_service import FraudDetectionService
from app.core.config import settings
from app.core.security import verify_api_key

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize global service instances
_fraud_detection_service = None

# API key security
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_fraud_detection_service() -> FraudDetectionService:
    """
    Get the fraud detection service instance.
    Creates a singleton instance if it doesn't exist.
    
    Returns:
        FraudDetectionService instance
    """
    global _fraud_detection_service
    
    if _fraud_detection_service is None:
        logger.info("Initializing fraud detection service")
        _fraud_detection_service = FraudDetectionService()
    
    return _fraud_detection_service

async def verify_api_key_header(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """
    Verify the API key from the request header.
    
    Args:
        api_key: API key from the request header
        
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If the API key is invalid
    """
    # In development mode, allow requests without API key
    if settings.APP_ENV == "development" and not settings.SECRET_KEY:
        return "development"
    
    # Check if API key is provided
    if not api_key:
        logger.warning("API key missing in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Verify API key
    if not verify_api_key(api_key):
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    return api_key