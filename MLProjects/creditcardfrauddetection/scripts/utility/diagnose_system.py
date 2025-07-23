#!/usr/bin/env python
"""
Diagnostic script to test if the fraud detection system components are working correctly.
Run this script to check for dependency issues and verify system functionality.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("diagnosis")

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
sys.path.append(str(project_root))

def test_environment_variables():
    """Test if required environment variables are set."""
    logger.info("Testing environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        logger.warning("OPENAI_API_KEY is not set. Will use mock LLM mode.")
    else:
        logger.info("OPENAI_API_KEY is set.")
    
    # Check vector database settings
    use_pinecone = os.getenv("USE_PINECONE", "").lower() in ("true", "1", "t")
    if use_pinecone:
        logger.info("System configured to use Pinecone.")
        pinecone_key = os.getenv("PINECONE_API_KEY", "")
        if not pinecone_key:
            logger.warning("USE_PINECONE=True but PINECONE_API_KEY is not set.")
    else:
        logger.info("System configured to use local Chroma database.")
    
    return True

def test_vector_db_initialization():
    """Test if the vector database can be initialized."""
    logger.info("Testing vector database initialization...")
    try:
        from app.services.vector_db_service import VectorDBService
        vector_db = VectorDBService()
        stats = vector_db.get_stats()
        logger.info(f"Vector database stats: {stats}")
        return True
    except Exception as e:
        logger.error(f"Vector database initialization failed: {str(e)}")
        return False

def test_llm_service_initialization():
    """Test if the LLM service can be initialized."""
    logger.info("Testing LLM service initialization...")
    try:
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        logger.info("LLM service initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"LLM service initialization failed: {str(e)}")
        return False

def test_fraud_detection_service():
    """Test if the fraud detection service can be initialized."""
    logger.info("Testing fraud detection service initialization...")
    try:
        from app.services.fraud_detection_service import FraudDetectionService
        fraud_service = FraudDetectionService()
        status = fraud_service.get_system_status()
        logger.info(f"Fraud detection system status: {status}")
        return True
    except Exception as e:
        logger.error(f"Fraud detection service initialization failed: {str(e)}")
        return False

def test_fraud_detection_endpoint():
    """Test if the fraud detection API endpoint works."""
    logger.info("Testing fraud detection endpoint...")
    try:
        from app.api.models import Transaction
        from app.services.fraud_detection_service import FraudDetectionService
        
        # Create a test transaction
        transaction = Transaction(
            transaction_id="test-txn-123",
            card_id="card-123",
            merchant_id="merchant-456",
            timestamp="2025-05-28T12:00:00Z",
            amount=123.45,
            currency="USD",
            is_online=True,
            merchant_category="Electronics",
            ip_address="192.168.1.1",
            device_id="device-789",
            location_country="US",
            location_state="CA"
        )
        
        # Initialize service
        fraud_service = FraudDetectionService()
        
        # Process transaction
        result = fraud_service.detect_fraud(transaction)
        logger.info(f"Fraud detection result: {result}")
        return True
    except Exception as e:
        logger.error(f"Fraud detection endpoint test failed: {str(e)}")
        return False

def main():
    """Run all diagnostic tests."""
    logger.info("Starting fraud detection system diagnostics...")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Vector Database", test_vector_db_initialization),
        ("LLM Service", test_llm_service_initialization),
        ("Fraud Detection Service", test_fraud_detection_service),
        ("Fraud Detection Endpoint", test_fraud_detection_endpoint)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            logger.info(f"Running {name} test...")
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"Test {name} raised an unexpected exception: {str(e)}")
            results.append((name, False))
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("DIAGNOSTIC RESULTS SUMMARY")
    logger.info("="*50)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        logger.info("\n✅ All tests passed! The system should be working correctly.")
        return 0
    else:
        logger.warning("\n❌ Some tests failed. See the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
