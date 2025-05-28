#!/usr/bin/env python
"""
Script to run the Credit Card Fraud Detection API server.
This is a convenience wrapper around the FastAPI application.
"""
import os
import sys
import uvicorn
from app.core.config import settings

def main():
    """Run the FastAPI application with uvicorn server."""
    print(f"Starting Credit Card Fraud Detection API on {settings.HOST}:{settings.PORT}")
    print(f"Environment: {settings.APP_ENV}")
    print(f"Debug mode: {settings.DEBUG}")
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if settings.APP_ENV == "production" else 1
    )

if __name__ == "__main__":
    main()