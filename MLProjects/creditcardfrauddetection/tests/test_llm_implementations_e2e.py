#!/usr/bin/env python
"""
End-to-end test script for the Credit Card Fraud Detection system with focus on LLM implementations.
This script tests the system with different LLM configurations to validate the fallback mechanisms.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
import argparse
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("llm_test_runner")

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
sys.path.append(str(project_root))

# Import necessary components
from app.api.models import Transaction
from app.services.fraud_detection_service import FraudDetectionService
from app.services.llm_service import LLMService
from app.core.config import settings


def create_test_transaction(risk_level="low"):
    """
    Create a test transaction with specified risk level.
    
    Args:
        risk_level: "low", "medium", or "high" risk transaction
    
    Returns:
        Transaction object
    """
    # Base transaction
    transaction = Transaction(
        transaction_id=f"test-{int(time.time())}",
        card_id="card_1234567890",
        merchant_id="merch_123456",
        timestamp="2025-05-28T12:34:56Z",
        amount=99.99,
        currency="USD",
        is_online=True,
        ip_address="192.168.1.1",
        merchant_category="Retail",
        customer_id="cust_12345",
        merchant_name="Local Store",
        merchant_country="US",
        location_country="US",
        location_state="CA"
    )
    
    # Adjust based on risk level
    if risk_level == "medium":
        transaction.amount = 999.99
        transaction.merchant_country = "UK"
        transaction.merchant_category = "Electronics"
    elif risk_level == "high":
        transaction.amount = 4999.99
        transaction.merchant_country = "RO"  # Romania - different from usual
        transaction.location_country = "CN"  # China - different from card country
        transaction.merchant_category = "Jewelry"
        transaction.merchant_name = "Online Luxury Shop"
    
    return transaction


def test_with_config(config_name, env_vars=None):
    """
    Test the system with a specific configuration.
    
    Args:
        config_name: Name of the configuration for logging
        env_vars: Dictionary of environment variables to set
    """
    # Save original environment variables
    original_env = {}
    if env_vars:
        for key, value in env_vars.items():
            if key in os.environ:
                original_env[key] = os.environ[key]
            os.environ[key] = str(value)
    
    try:
        logger.info(f"\n{'='*80}\n TESTING WITH CONFIG: {config_name}\n{'='*80}")
        
        # Reload settings to pick up environment changes
        from importlib import reload
        from app.core import config as config_module
        reload(config_module)
        from app.core.config import settings
        
        # Initialize the fraud detection service
        fraud_service = FraudDetectionService()
        
        # Check system status
        status = fraud_service.get_system_status()
        logger.info(f"System status: {json.dumps(status, indent=2)}")
        
        llm_type = status["llm"]["service_type"]
        logger.info(f"Using LLM service type: {llm_type}")
        
        # Process test transactions with different risk levels
        for risk_level in ["low", "medium", "high"]:
            transaction = create_test_transaction(risk_level)
            logger.info(f"\nProcessing {risk_level} risk transaction (${transaction.amount} at {transaction.merchant_name})...")
            
            start_time = time.time()
            result = fraud_service.detect_fraud(transaction)
            elapsed = time.time() - start_time
            
            logger.info(f"Result: {'FRAUD' if result.is_fraud else 'LEGITIMATE'}")
            logger.info(f"Confidence: {result.confidence_score:.2f}")
            logger.info(f"Recommendation: {'Review' if result.requires_review else 'Auto-processed'}")
            logger.info(f"Reasoning: {result.decision_reason[:100]}...")
            logger.info(f"Processing time: {elapsed:.2f} seconds")
        
        logger.info(f"\n{'='*80}\n END OF TEST: {config_name}\n{'='*80}\n")
        
    finally:
        # Restore original environment variables
        for key, value in original_env.items():
            os.environ[key] = value
        for key in env_vars or {}:
            if key not in original_env:
                os.environ.pop(key, None)


def test_api_endpoint_with_config(config_name, env_vars=None):
    """
    Test the API endpoint with a specific configuration.
    
    Args:
        config_name: Name of the configuration for logging
        env_vars: Dictionary of environment variables to set
    """
    # This would need to be run with the API server running with the specified config
    # For now, we'll just add a placeholder
    logger.info(f"API endpoint testing with {config_name} configuration would be done here.")
    logger.info("For actual API testing, the server needs to be running with the specified configuration.")


def main():
    """Run tests with different configurations."""
    parser = argparse.ArgumentParser(description="Test the Credit Card Fraud Detection system with different LLM configurations")
    parser.add_argument("--api-test", action="store_true", help="Test the API endpoints (requires API server to be running)")
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Define the test configurations
    configs = [
        {
            "name": "OpenAI configuration",
            "env": {
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
                "USE_LOCAL_LLM": "False",
                "FORCE_LOCAL_LLM": "False"
            }
        },
        {
            "name": "Enhanced Mock LLM configuration",
            "env": {
                "OPENAI_API_KEY": "invalid-key",
                "USE_LOCAL_LLM": "False",
                "FORCE_LOCAL_LLM": "False"
            }
        },
        {
            "name": "Local LLM configuration (if available)",
            "env": {
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
                "USE_LOCAL_LLM": "True",
                "FORCE_LOCAL_LLM": "True",
                "LOCAL_LLM_MODEL": "llama3",
                "LOCAL_LLM_API_URL": "http://localhost:11434/api"
            }
        },
        {
            "name": "Fallback configuration (OpenAI key valid, but force local LLM which is unavailable)",
            "env": {
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
                "USE_LOCAL_LLM": "True",
                "FORCE_LOCAL_LLM": "True",
                "LOCAL_LLM_MODEL": "nonexistent-model",
                "LOCAL_LLM_API_URL": "http://invalid-url:11434/api"
            }
        }
    ]
    
    # Run tests for each configuration
    for config in configs:
        try:
            if args.api_test:
                test_api_endpoint_with_config(config["name"], config["env"])
            else:
                test_with_config(config["name"], config["env"])
        except Exception as e:
            logger.error(f"Error testing with {config['name']}: {str(e)}")
    
    logger.info("All tests completed")


if __name__ == "__main__":
    main()
