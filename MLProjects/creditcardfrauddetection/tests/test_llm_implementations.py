"""
Test script to try different LLM implementations in the fraud detection system.
This script allows testing different LLM providers by setting environment variables.
"""

import os
import sys
import logging
from pathlib import Path
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import the LLM service
from app.services.llm_service import LLMService 
from app.services.local_llm_service import LocalLLMService
from app.services.enhanced_mock_llm import EnhancedMockLLM
from langchain.schema import Document
from app.core.config import settings

def print_header(title):
    """Print a header for better readability"""
    width = 70
    print("\n" + "=" * width)
    print(f" {title} ".center(width))
    print("=" * width + "\n")

def create_test_data():
    """Create test transaction and pattern data"""
    # Create a sample transaction text
    transaction_text = """
    Transaction ID: TX-20250528-95123
    Date: May 28, 2025 14:35:22 GMT
    Amount: $1,250.00
    Merchant: ElectroMart
    Category: Electronics
    Location: New York, NY
    Payment Method: Credit Card (ending 1234)
    Card Present: No (Online transaction)
    IP Address Location: New York, NY
    Distance from Home: 5 miles
    User Account Age: 3 years, 2 months
    Previous transactions at this merchant: 3 (last one 45 days ago)
    """
    
    # Create some sample fraud patterns
    similar_patterns = [
        Document(
            page_content="""
            A fraudulent transaction that occurred in an online electronics store.
            The transaction was flagged as suspicious due to the location being
            different from the customer's usual location. The amount was also
            significantly higher than the customer's average transaction.
            """,
            metadata={
                "case_id": "FRD-2025-001",
                "fraud_type": "Unusual Location",
                "confidence": 0.92
            }
        ),
        Document(
            page_content="""
            Legitimate transaction at ElectroMart by a regular customer.
            The customer has made similar purchases in the past,
            and the transaction amount is consistent with their spending habits.
            """,
            metadata={
                "case_id": "LEG-2025-042",
                "fraud_type": "Legitimate",
                "confidence": 0.88
            }
        )
    ]
    
    return transaction_text, similar_patterns

def test_openai_llm():
    """Test OpenAI LLM implementation"""
    print_header("TESTING OPENAI LLM")
    
    # Save original settings
    orig_use_local = os.environ.get('USE_LOCAL_LLM', '')
    orig_force_local = os.environ.get('FORCE_LOCAL_LLM', '')
    
    # Force OpenAI use
    os.environ['USE_LOCAL_LLM'] = 'False'
    os.environ['FORCE_LOCAL_LLM'] = 'False'
    
    print("Current OpenAI API Key:", settings.OPENAI_API_KEY[:5] + "..." if settings.OPENAI_API_KEY else "Not Set")
    print("Current LLM Model:", settings.LLM_MODEL)
    
    if not settings.OPENAI_API_KEY:
        print("OpenAI API Key not set. Skipping OpenAI test.")
        # Restore original settings
        os.environ['USE_LOCAL_LLM'] = orig_use_local
        os.environ['FORCE_LOCAL_LLM'] = orig_force_local
        return False
    
    try:
        llm_service = LLMService()
        if llm_service.llm_service_type != "openai":
            print(f"Failed to initialize OpenAI LLM. Using {llm_service.llm_service_type} instead.")
            return False
            
        print("Successfully initialized OpenAI LLM")
        
        # Test transaction analysis
        transaction_text, similar_patterns = create_test_data()
        result = llm_service.analyze_transaction(transaction_text, similar_patterns)
        
        print("Analysis Results:")
        print(f"- Fraud Probability: {result.fraud_probability}")
        print(f"- Confidence: {result.confidence}")
        print(f"- Recommendation: {result.recommendation}")
        print(f"- Retrieved Patterns: {result.retrieved_patterns}")
        print("\n- Reasoning:")
        print(result.reasoning)
        
        return True
    except Exception as e:
        print(f"Error testing OpenAI LLM: {str(e)}")
        return False
    finally:
        # Restore original settings
        os.environ['USE_LOCAL_LLM'] = orig_use_local
        os.environ['FORCE_LOCAL_LLM'] = orig_force_local

def test_local_llm():
    """Test Local LLM implementation"""
    print_header("TESTING LOCAL LLM")
    
    # Save original settings
    orig_use_local = os.environ.get('USE_LOCAL_LLM', '')
    orig_force_local = os.environ.get('FORCE_LOCAL_LLM', '')
    
    # Force local LLM
    os.environ['USE_LOCAL_LLM'] = 'True'
    os.environ['FORCE_LOCAL_LLM'] = 'True'
    
    print("Local LLM Model:", settings.LOCAL_LLM_MODEL)
    print("Local LLM API URL:", settings.LOCAL_LLM_API_URL)
    
    try:
        # First check if local LLM is available
        local_service = LocalLLMService(model_name=settings.LOCAL_LLM_MODEL)
        if not local_service.available:
            print("Local LLM service is not available. Make sure Ollama is running.")
            return False
            
        print("Local LLM is available. Testing full service...")
        
        llm_service = LLMService()
        if llm_service.llm_service_type != "local":
            print(f"Failed to initialize Local LLM. Using {llm_service.llm_service_type} instead.")
            return False
            
        print("Successfully initialized Local LLM")
        
        # Test transaction analysis
        transaction_text, similar_patterns = create_test_data()
        result = llm_service.analyze_transaction(transaction_text, similar_patterns)
        
        print("Analysis Results:")
        print(f"- Fraud Probability: {result.fraud_probability}")
        print(f"- Confidence: {result.confidence}")
        print(f"- Recommendation: {result.recommendation}")
        print(f"- Retrieved Patterns: {result.retrieved_patterns}")
        print("\n- Reasoning:")
        print(result.reasoning)
        
        return True
    except Exception as e:
        print(f"Error testing Local LLM: {str(e)}")
        return False
    finally:
        # Restore original settings
        os.environ['USE_LOCAL_LLM'] = orig_use_local
        os.environ['FORCE_LOCAL_LLM'] = orig_force_local

def test_mock_llm():
    """Test Enhanced Mock LLM implementation"""
    print_header("TESTING ENHANCED MOCK LLM")
    
    # Save original settings
    orig_use_local = os.environ.get('USE_LOCAL_LLM', '')
    orig_force_local = os.environ.get('FORCE_LOCAL_LLM', '')
    orig_openai_key = os.environ.get('OPENAI_API_KEY', '')
    
    # Force mock LLM by disabling others
    os.environ['USE_LOCAL_LLM'] = 'False'
    os.environ['FORCE_LOCAL_LLM'] = 'False'
    os.environ['OPENAI_API_KEY'] = ''
    
    try:
        # Initialize the service - should fall back to mock
        llm_service = LLMService()
        print(f"LLM Service Type: {llm_service.llm_service_type}")
        
        if llm_service.llm_service_type not in ["enhanced_mock", "basic_mock"]:
            print("Failed to use mock LLM.")
            return False
            
        print(f"Successfully initialized {llm_service.llm_service_type}")
        
        # Test transaction analysis
        transaction_text, similar_patterns = create_test_data()
        result = llm_service.analyze_transaction(transaction_text, similar_patterns)
        
        print("Analysis Results:")
        print(f"- Fraud Probability: {result.fraud_probability}")
        print(f"- Confidence: {result.confidence}")
        print(f"- Recommendation: {result.recommendation}")
        print(f"- Retrieved Patterns: {result.retrieved_patterns}")
        print("\n- Reasoning:")
        print(result.reasoning)
        
        return True
    except Exception as e:
        print(f"Error testing Mock LLM: {str(e)}")
        return False
    finally:
        # Restore original settings
        os.environ['USE_LOCAL_LLM'] = orig_use_local
        os.environ['FORCE_LOCAL_LLM'] = orig_force_local
        os.environ['OPENAI_API_KEY'] = orig_openai_key

def test_fallback_mechanism():
    """Test the fallback mechanism chain"""
    print_header("TESTING FALLBACK MECHANISM")
    
    # Save original settings
    orig_openai_key = os.environ.get('OPENAI_API_KEY', '')
    orig_use_local = os.environ.get('USE_LOCAL_LLM', '')
    
    try:
        # First try with invalid OpenAI key but local LLM enabled
        os.environ['OPENAI_API_KEY'] = 'sk-invalid-key'
        os.environ['USE_LOCAL_LLM'] = 'True'
        
        print("Testing with invalid OpenAI key but local LLM enabled...")
        llm_service = LLMService()
        print(f"Fallback path 1 result: {llm_service.llm_service_type}")
        
        # Then try with both invalid
        os.environ['USE_LOCAL_LLM'] = 'False'
        
        print("Testing with invalid OpenAI key and local LLM disabled...")
        llm_service = LLMService()
        print(f"Fallback path 2 result: {llm_service.llm_service_type}")
        
        return True
    except Exception as e:
        print(f"Error testing fallback mechanism: {str(e)}")
        return False
    finally:
        # Restore original settings
        os.environ['OPENAI_API_KEY'] = orig_openai_key
        os.environ['USE_LOCAL_LLM'] = orig_use_local

def main():
    """Main function to run the LLM implementation tests"""
    try:
        print_header("LLM IMPLEMENTATION TESTING")
        print("This script tests different LLM implementations in the fraud detection system.")
        print(f"Current environment: {settings.APP_ENV}")
        print(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {}
        
        # Test each implementation
        results["OpenAI LLM"] = test_openai_llm()
        results["Local LLM"] = test_local_llm()
        results["Mock LLM"] = test_mock_llm()
        results["Fallback Mechanism"] = test_fallback_mechanism()
        
        # Print summary
        print_header("TEST RESULTS SUMMARY")
        for name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{name}: {status}")
            
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
