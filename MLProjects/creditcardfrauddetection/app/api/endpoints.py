"""
API endpoints for fraud detection system.
"""

import logging
from typing import Dict, Any, List, Optional
import time

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse

from app.api.models import (
    Transaction, 
    FraudDetectionResponse, 
    FeedbackModel, 
    HealthCheckResponse,
    ErrorResponse
)
from app.services.fraud_detection_service import FraudDetectionService
from app.core.config import settings
from app.api.dependencies import get_fraud_detection_service, verify_api_key_header

# Initialize router
router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

@router.post("/detect-fraud", response_model=FraudDetectionResponse, responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def detect_fraud(
    transaction: Transaction,
    background_tasks: BackgroundTasks,
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Detect fraud in a credit card transaction.
    
    Args:
        transaction: The transaction to analyze
        
    Returns:
        Fraud detection result
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received fraud detection request for transaction {transaction.transaction_id}")
        
        # Process the transaction
        response = fraud_service.detect_fraud(transaction)
        
        # Log the result
        fraud_status = "FRAUD" if response.is_fraud else "LEGITIMATE"
        logger.info(
            f"[{request_id}] Transaction {transaction.transaction_id} classified as {fraud_status} "
            f"with confidence {response.confidence_score:.2f}"
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing transaction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing transaction: {str(e)}")

@router.post("/feedback", response_model=Dict[str, Any], responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def submit_feedback(
    feedback: FeedbackModel,
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Submit analyst feedback on a transaction.
    
    Args:
        feedback: Analyst feedback data
        
    Returns:
        Success status
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received feedback for transaction {feedback.transaction_id}")
        
        # Process the feedback
        success = fraud_service.process_feedback(feedback)
        
        if success:
            return {"status": "success", "message": "Feedback processed successfully"}
        else:
            return {"status": "error", "message": "Error processing feedback"}
    
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")

@router.post("/ingest-patterns", response_model=Dict[str, Any], responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def ingest_patterns(
    fraud_patterns: List[Dict[str, Any]],
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Ingest fraud patterns into the system.
    
    Args:
        fraud_patterns: List of fraud pattern data
        
    Returns:
        Success status and count of patterns ingested
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received request to ingest {len(fraud_patterns)} fraud patterns")
        
        # Ingest the patterns
        count = fraud_service.ingest_fraud_patterns(fraud_patterns)
        
        return {
            "status": "success", 
            "message": f"Successfully ingested {count} fraud patterns",
            "count": count
        }
    
    except Exception as e:
        logger.error(f"Error ingesting fraud patterns: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting fraud patterns: {str(e)}")

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service)
):
    """
    Health check endpoint.
    
    Returns:
        Health status of the system
    """
    try:
        # Get system status
        status = fraud_service.get_system_status()
        
        return HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            components=status
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            components={"error": str(e)}
        )

@router.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        Basic API information
    """
    return {
        "name": "Credit Card Fraud Detection API",
        "version": "1.0.0",
        "description": "AI-powered credit card fraud detection system using LLM and RAG"
    }