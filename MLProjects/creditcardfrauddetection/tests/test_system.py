#!/usr/bin/env python
"""
Test script to verify all components of the fraud detection system.
This script will check all dependencies and configurations.
"""
import os
import sys
import logging
import json
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("system_test")

# Add project root to Python path
project_root = Path(__file__).parent.resolve()
sys.path.append(str(project_root))

# Import system components
from app.services.fraud_detection_service import FraudDetectionService
from app.services.vector_db_service import VectorDBService
from app.services.llm_service import LLMService
from app.api.models import Transaction
from app.core.config import settings

def test_system_components():
    """Test all system components and configurations."""
    logger.info("="*50)
    logger.info("CREDIT CARD FRAUD DETECTION SYSTEM TEST")
    logger.info("="*50)
    
    # Check environment variables
    logger.info("\n[1/5] Checking environment variables...")
    env_ok = test_environment()
    
    # Test vector database
    logger.info("\n[2/5] Testing vector database...")
    vector_db_ok = test_vector_db()
    
    # Test LLM service
    logger.info("\n[3/5] Testing LLM service...")
    llm_ok = test_llm_service()
    
    # Test fraud detection service
    logger.info("\n[4/5] Testing fraud detection service...")
    fraud_service_ok = test_fraud_detection()
    
    # Test full pipeline with a sample transaction
    logger.info("\n[5/5] Testing full pipeline with sample transaction...")
    pipeline_ok = test_full_pipeline()
    
    # Report results
    logger.info("\n"+"="*50)
    logger.info("SYSTEM TEST RESULTS")
    logger.info("="*50)
    logger.info(f"Environment variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    logger.info(f"Vector database: {'✅ PASS' if vector_db_ok else '❌ FAIL'}")
    logger.info(f"LLM service: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    logger.info(f"Fraud detection service: {'✅ PASS' if fraud_service_ok else '❌ FAIL'}")
    logger.info(f"Full pipeline: {'✅ PASS' if pipeline_ok else '❌ FAIL'}")
    logger.info("="*50)
    
    if all([env_ok, vector_db_ok, llm_ok, fraud_service_ok, pipeline_ok]):
        logger.info("✅ ALL TESTS PASSED - System is ready for use")
    else:
        logger.info("❌ SOME TESTS FAILED - See details above")

def test_environment():
    """Test environment variables and configuration."""
    try:
        # Check OpenAI API key
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set - will use mock LLM")
            return False
        elif len(settings.OPENAI_API_KEY) < 20:
            logger.warning(f"OPENAI_API_KEY appears invalid (length: {len(settings.OPENAI_API_KEY)})")
            return False
        else:
            logger.info("OPENAI_API_KEY is set properly")
        
        # Check vector DB settings
        if settings.PINECONE_API_KEY and os.getenv("USE_PINECONE", "").lower() in ("true", "1", "t"):
            logger.info("Vector DB: Using Pinecone")
        else:
            logger.info("Vector DB: Using local Chroma")
            chroma_dir = os.path.join(project_root, 'data', 'chroma_db')
            if not os.path.exists(chroma_dir):
                os.makedirs(chroma_dir, exist_ok=True)
                logger.info(f"Created Chroma DB directory: {chroma_dir}")
            else:
                logger.info(f"Chroma DB directory exists: {chroma_dir}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking environment: {str(e)}")
        return False

def test_vector_db():
    """Test vector database service."""
    try:
        vector_db = VectorDBService()
        stats = vector_db.get_stats()
        logger.info(f"Vector DB stats: {json.dumps(stats, indent=2)}")
        
        # Test retrieving patterns
        patterns = vector_db.get_all_fraud_patterns()
        logger.info(f"Retrieved {len(patterns)} fraud patterns")
        
        if len(patterns) > 0:
            logger.info(f"Sample pattern: {json.dumps(patterns[0], indent=2)}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing vector DB: {str(e)}")
        return False

def test_llm_service():
    """Test LLM service."""
    try:
        llm_service = LLMService()
        
        # Create a test document
        from langchain.schema import Document
        doc = Document(
            page_content="This is a test fraud pattern for high-value electronics purchase.",
            metadata={
                "case_id": "test-pattern-001",
                "name": "Test Pattern",
                "description": "Test pattern for system check"
            }
        )
        
        # Test simple LLM analysis
        test_transaction = "Customer bought a 4K TV for $2,500 at an electronics store."
        analysis = llm_service.analyze_transaction(test_transaction, [doc])
        
        logger.info(f"LLM Analysis: {analysis.recommendation}")
        logger.info(f"Reasoning: {analysis.reasoning[:100]}...")
        
        # Check if using mock or real LLM
        if "mock" in str(type(llm_service.llm)).lower():
            logger.warning("Using mock LLM - system will use fake responses")
            return False
        else:
            logger.info(f"Using real LLM: {settings.LLM_MODEL}")
            return True
            
    except Exception as e:
        logger.error(f"Error testing LLM service: {str(e)}")
        return False

def test_fraud_detection():
    """Test fraud detection service."""
    try:
        fraud_service = FraudDetectionService()
        status = fraud_service.get_system_status()
        logger.info(f"Fraud detection system status: {json.dumps(status, indent=2)}")
        return status.get("status") == "operational"
    except Exception as e:
        logger.error(f"Error testing fraud detection service: {str(e)}")
        return False

def test_full_pipeline():
    """Test the full fraud detection pipeline."""
    try:
        # Initialize the fraud detection service
        fraud_service = FraudDetectionService()
        
        # Create a test transaction
        transaction = Transaction(
            transaction_id="test-txn-001",
            card_id="card_1234567890",
            customer_id="cust_12345",
            merchant_id="merch_67890",
            merchant_name="Test Electronics Store",
            merchant_category="Electronics",
            merchant_country="US",
            timestamp="2025-05-28T12:34:56Z",
            amount=1299.99,
            currency="USD",
            is_online=True,
            device_id="dev_abcdef123456",
            ip_address="192.168.1.1"
        )
        
        logger.info("Processing test transaction through fraud detection pipeline...")
        start_time = time.time()
        
        # Process the transaction
        result = fraud_service.detect_fraud(transaction)
        
        # Log results
        elapsed = time.time() - start_time
        logger.info(f"Transaction processed in {elapsed:.2f} seconds")
        logger.info(f"Fraud prediction: {result.is_fraudulent}")
        logger.info(f"Confidence: {result.confidence}")
        logger.info(f"Recommendation: {result.recommendation}")
        
        # Check for indicators of mock data
        if "mock" in str(result.full_analysis).lower():
            logger.warning("Response contains mock data indicators")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error testing full pipeline: {str(e)}")
        return False

if __name__ == "__main__":
    test_system_components()
