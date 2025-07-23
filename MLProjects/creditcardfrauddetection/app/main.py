"""
Main application module for the credit card fraud detection system.
"""

import logging
import time
import json
from typing import Dict, Any

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints import router as api_router
from app.api.dependencies import verify_api_key_header
from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import setup_metrics  # Add this import

# Create FastAPI application
app = FastAPI(
    title="Credit Card Fraud Detection API",
    description="AI-powered credit card fraud detection using LLM and RAG",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.time()
    
    # Get client IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0]
    else:
        client_ip = request.client.host
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
    
    try:
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Response: {response.status_code} in {process_time:.2f}ms")
        
        return response
    except Exception as e:
        # Log exception
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Error: {str(e)} in {process_time:.2f}ms")
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID to each request."""
    # Generate request ID
    request_id = f"req_{int(time.time() * 1000)}"
    
    # Add to request state
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response

# Include API router
if settings.APP_ENV == "production":
    # In production, require API key for all endpoints
    app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(verify_api_key_header)])
else:
    # In development, don't require API key
    app.include_router(api_router, prefix="/api/v1")

# Set up Prometheus metrics
if settings.ENABLE_PROMETHEUS:
    setup_metrics(app)
    logger.info("Prometheus metrics instrumentation enabled")

# Add root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Credit Card Fraud Detection System",
        "version": "1.0.0",
        "description": "AI-powered credit card fraud detection using LLM and RAG",
        "docs": "/docs" if settings.DEBUG else None
    }

# Add health check endpoint
@app.get("/health", tags=["Health"], response_model=Dict[str, Any])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    This endpoint doesn't require authentication.
    """
    # Import here to avoid circular imports
    from app.api.dependencies import get_llm_service
    
    # Get current LLM service type
    llm_service = get_llm_service()
    llm_type = llm_service.llm_service_type if llm_service else "unknown"
    
    # Get model name based on service type
    model_name = "N/A"
    if llm_type == "openai":
        model_name = settings.LLM_MODEL
    elif llm_type == "local":
        model_name = settings.LOCAL_LLM_MODEL
    elif llm_type == "enhanced_mock":
        model_name = "Enhanced Mock LLM"
    elif llm_type == "basic_mock":
        model_name = "Basic Mock LLM"
    
    return {
        "status": "healthy",  # Changed from "ok" to match what dashboard expects
        "status_code": "ok",  # Keep "ok" as a backup field
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "llm_service_type": llm_type,
        "llm_model": model_name,
        "timestamp": time.time()
    }

# Add event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Credit Card Fraud Detection API")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize mock data in development mode
    if settings.APP_ENV == "development":
        # Import here to avoid circular imports
        from app.api.dependencies import get_fraud_detection_service
        
        try:
            # Get fraud detection service
            fraud_service = get_fraud_detection_service()
            
            # Load mock fraud patterns
            try:
                with open("data/sample/fraud_patterns.json", "r") as f:
                    fraud_patterns = json.load(f)
                
                # Ingest fraud patterns
                count = fraud_service.ingest_fraud_patterns(fraud_patterns)
                logger.info(f"Ingested {count} mock fraud patterns")
            except FileNotFoundError:
                logger.warning("Mock fraud patterns file not found")
            except Exception as e:
                logger.error(f"Error loading mock fraud patterns: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error initializing fraud detection service: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Credit Card Fraud Detection API")

# Run the application if executed as a script
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if settings.APP_ENV == "production" else 1
    )