"""
API endpoints for fraud detection system.
"""

import logging
import uuid
import datetime
from typing import Dict, Any, List, Optional
import time

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse

from app.api.models import (
    Transaction, 
    FraudDetectionResponse, 
    FeedbackModel, 
    HealthCheckResponse,
    ErrorResponse,
    ModelMetricsResponse
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

@router.get("/fraud-patterns", response_model=List[Dict[str, Any]], responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def get_fraud_patterns(
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Get all fraud patterns.
    
    Returns:
        List of fraud patterns
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received request to get all fraud patterns")
        
        # Get patterns from the vector database service
        patterns = fraud_service.vector_db_service.get_all_fraud_patterns()
        
        # If no patterns were found, return an empty list
        if not patterns:
            logger.warning("No fraud patterns found in the vector database.")
            patterns = []
        
        return patterns
    except Exception as e:
        logger.error(f"Error getting fraud patterns: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting fraud patterns: {str(e)}")

@router.post("/fraud-patterns", response_model=Dict[str, Any], responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def add_fraud_pattern(
    pattern_data: Dict[str, Any],
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Add a new fraud pattern.
    
    Args:
        pattern_data: The pattern data to add
        
    Returns:
        The added pattern with ID and timestamp
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received request to add fraud pattern: {pattern_data['name']}")
        
        # Add ID and timestamp if not already present
        if "id" not in pattern_data:
            pattern_data["id"] = f"pattern_{str(uuid.uuid4())[:8]}"
        if "created_at" not in pattern_data:
            pattern_data["created_at"] = datetime.datetime.now().isoformat()
        
        # Save the pattern to the vector database
        result = fraud_service.vector_db_service.add_fraud_patterns([pattern_data])
        if result > 0:
            logger.info(f"[{request_id}] Successfully added fraud pattern with ID: {pattern_data['id']}")
            return pattern_data
        else:
            logger.error(f"[{request_id}] Failed to add fraud pattern")
            raise HTTPException(status_code=500, detail="Failed to add fraud pattern")
        
        return pattern_data
    except Exception as e:        
        logger.error(f"Error adding fraud pattern: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding fraud pattern: {str(e)}")

@router.put("/fraud-patterns/{pattern_id}", response_model=Dict[str, Any], responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Pattern not found"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def update_fraud_pattern(
    pattern_id: str,
    pattern_data: Dict[str, Any],
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Update an existing fraud pattern.
    
    Args:
        pattern_id: ID of the pattern to update
        pattern_data: Updated pattern data
        
    Returns:
        The updated pattern
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received request to update fraud pattern: {pattern_id}")
        
        # Ensure the ID in the URL matches the ID in the data
        pattern_data["id"] = pattern_id
        
        # Keep the original created_at timestamp
        # First, try to get the existing pattern
        all_patterns = fraud_service.vector_db_service.get_all_fraud_patterns()
        existing_pattern = None
        for pattern in all_patterns:
            if pattern["id"] == pattern_id:
                existing_pattern = pattern
                break
                
        if not existing_pattern:
            logger.error(f"[{request_id}] Pattern with ID {pattern_id} not found")
            raise HTTPException(status_code=404, detail=f"Pattern with ID {pattern_id} not found")
            
        # Preserve the original created_at timestamp
        if "created_at" not in pattern_data and "created_at" in existing_pattern:
            pattern_data["created_at"] = existing_pattern["created_at"]
        
        # Remove the old pattern (not ideal, but a simple approach for now)
        # In a real database we would do an update operation
        
        # Add the updated pattern to the vector database
        result = fraud_service.vector_db_service.add_fraud_patterns([pattern_data])
        
        if result > 0:
            logger.info(f"[{request_id}] Successfully updated fraud pattern with ID: {pattern_id}")
            return pattern_data
        else:
            logger.error(f"[{request_id}] Failed to update fraud pattern")
            raise HTTPException(status_code=500, detail="Failed to update fraud pattern")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating fraud pattern: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating fraud pattern: {str(e)}")

@router.delete("/fraud-patterns/{pattern_id}", response_model=Dict[str, Any], responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Pattern not found"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def delete_fraud_pattern(
    pattern_id: str,
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Delete an existing fraud pattern.
    
    Args:
        pattern_id: ID of the pattern to delete
        
    Returns:
        Success message
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received request to delete fraud pattern: {pattern_id}")
          # First, check if the pattern exists
        if not fraud_service.vector_db_service.pattern_exists(pattern_id):
            logger.error(f"[{request_id}] Pattern with ID {pattern_id} not found")
            raise HTTPException(status_code=404, detail=f"Pattern with ID {pattern_id} not found")
        
        # Delete the pattern from the vector database
        result = fraud_service.vector_db_service.delete_fraud_pattern(pattern_id)
        
        if result:
            logger.info(f"[{request_id}] Successfully deleted fraud pattern with ID: {pattern_id}")
            return {
                "status": "success",
                "message": f"Successfully deleted fraud pattern with ID: {pattern_id}",
                "pattern_id": pattern_id
            }
        else:
            logger.error(f"[{request_id}] Failed to delete fraud pattern")
            raise HTTPException(status_code=500, detail="Failed to delete fraud pattern")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting fraud pattern: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting fraud pattern: {str(e)}")

@router.get("/metrics", response_model=ModelMetricsResponse, responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def get_metrics(
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Get system metrics including model performance.
    
    Returns:
        Dict containing various system metrics and model performance data
    """
   
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received request to get system metrics")
        
        
        # Get real model metrics data from the fraud detection service
        metrics = fraud_service.get_model_metrics()
        
        # Log the metrics for debugging
        logger.critical(f"METRICS: {metrics}")
        
        # Return the metrics
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")

@router.get("/transactions", response_model=List[Dict[str, Any]], responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def get_transactions(
    request: Request,
    limit: int = 10,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Get transaction history.
    
    Args:
        limit: Maximum number of transactions to return (default: 10)
        
    Returns:
        List of recent transactions
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received request to get transaction history (limit={limit})")
        
        # Get transaction history from the service
        transactions = fraud_service.get_transaction_history(limit)
        
        return transactions
    except Exception as e:
        logger.error(f"Error getting transaction history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting transaction history: {str(e)}")

@router.get("/transactions/{transaction_id}", response_model=Dict[str, Any], responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Transaction not found"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def get_transaction(
    transaction_id: str,
    request: Request,
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Get details for a specific transaction.
    
    Args:
        transaction_id: ID of the transaction to retrieve
        
    Returns:
        Transaction details
    """
    try:
        # Get request ID for logging
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Received request to get transaction {transaction_id}")
        
        # Get transaction details from the service
        transaction = fraud_service.get_transaction_by_id(transaction_id)
        
        if not transaction:
            logger.warning(f"[{request_id}] Transaction {transaction_id} not found")
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
            
        return transaction
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting transaction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting transaction: {str(e)}")

@router.get("/llm-status", response_model=Dict[str, Any])
async def get_llm_status(
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Get the current LLM service status.
    
    Returns:
        Dictionary containing LLM service information
    """
    llm_service = fraud_service.llm_service
    
    # Get model name based on service type
    model_name = "N/A"
    if llm_service.llm_service_type == "openai":
        model_name = settings.LLM_MODEL
    elif llm_service.llm_service_type == "local":
        model_name = settings.LOCAL_LLM_MODEL
    elif llm_service.llm_service_type == "enhanced_mock":
        model_name = "Enhanced Mock LLM"
    elif llm_service.llm_service_type == "basic_mock":
        model_name = "Basic Mock LLM"
    
    return {
        "llm_service_type": llm_service.llm_service_type,
        "llm_model": model_name,
        "is_api": llm_service.llm_service_type == "openai",
        "is_local": llm_service.llm_service_type == "local",
        "is_mock": llm_service.llm_service_type in ["enhanced_mock", "basic_mock"]
    }

@router.post("/switch-llm-model", response_model=Dict[str, Any])
async def switch_llm_model(
    model_type: Dict[str, str],
    fraud_service: FraudDetectionService = Depends(get_fraud_detection_service),
    api_key: str = Depends(verify_api_key_header)
):
    """
    Switch the LLM model type.
    
    Args:
        model_type: Dictionary with "type" key containing either "openai", "local", or "mock"
        
    Returns:
        Dictionary with result of the switch operation
    """
    llm_service = fraud_service.llm_service
    target_type = model_type.get("type", "").lower()
    current_type = llm_service.llm_service_type
    
    if target_type == current_type:
        return {
            "success": True,
            "message": f"Already using {target_type} LLM model",
            "current_type": current_type
        }
    
    # Handle switching based on target type
    if target_type == "openai":
        # Try to switch to OpenAI
        try:
            from langchain.schema.messages import HumanMessage
            from langchain_openai import ChatOpenAI
            
            # Attempt to initialize OpenAI
            api_key = settings.OPENAI_API_KEY
            if not api_key or len(api_key) < 20:
                return {
                    "success": False,
                    "message": "Cannot switch to OpenAI: Invalid API key",
                    "current_type": current_type
                }
            
            temp_llm = ChatOpenAI(
                model_name=settings.LLM_MODEL,
                temperature=0,
                openai_api_key=api_key
            )
            
            # Test connection
            test_response = temp_llm.invoke([HumanMessage(content="Test")])
            
            # If successful, switch the LLM type
            llm_service.llm = temp_llm
            llm_service.llm_service_type = "openai"
            
            return {
                "success": True,
                "message": f"Successfully switched to OpenAI LLM ({settings.LLM_MODEL})",
                "current_type": "openai"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to switch to OpenAI LLM: {str(e)}",
                "current_type": current_type
            }
            
    elif target_type == "local":
        # Try to switch to local LLM
        try:
            from app.services.local_llm_service import LocalLLMService
            
            local_llm = LocalLLMService(model_name=settings.LOCAL_LLM_MODEL)
            if local_llm.available:
                llm_service.local_llm_service = local_llm
                llm_service.llm_service_type = "local"
                
                # Create a placeholder llm instance for compatibility
                from langchain_community.llms.fake import FakeListLLM
                llm_service.llm = FakeListLLM(responses=["Local LLM will be used instead"])
                
                return {
                    "success": True,
                    "message": f"Successfully switched to local LLM ({settings.LOCAL_LLM_MODEL})",
                    "current_type": "local"
                }
            else:
                return {
                    "success": False,
                    "message": "Local LLM is not available",
                    "current_type": current_type
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to switch to local LLM: {str(e)}",
                "current_type": current_type
            }
            
    elif target_type == "mock":
        # Switch to enhanced mock LLM
        try:
            from app.services.enhanced_mock_llm import EnhancedMockLLM, EnhancedFakeListLLM
            
            llm_service.enhanced_mock = EnhancedMockLLM()
            llm_service.llm = EnhancedFakeListLLM()
            llm_service.llm_service_type = "enhanced_mock"
            
            return {
                "success": True,
                "message": "Successfully switched to enhanced mock LLM",
                "current_type": "enhanced_mock"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to switch to mock LLM: {str(e)}",
                "current_type": current_type
            }
    else:
        return {
            "success": False,
            "message": f"Invalid model type '{target_type}'. Supported types: openai, local, mock",
            "current_type": current_type
        }