"""
Debug script for testing and debugging the LLM Service
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import the LLM service
from app.services.llm_service import LLMService
from langchain.schema import Document
from app.core.config import settings

def print_separator(title):
    """Print a separator with title for better readability"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

def test_llm_service():
    """Test the LLM service functionality"""
    print_separator("INITIALIZING LLM SERVICE")
    # Create LLM service instance
    llm_service = LLMService()
    
    # Print which LLM service type got initialized
    print(f"LLM Service Type: {llm_service.llm_service_type}")
    print(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    
    # Create a sample transaction text
    print_separator("TESTING TRANSACTION ANALYSIS")
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
    
    # Analyze the transaction
    try:
        result = llm_service.analyze_transaction(transaction_text, similar_patterns)
        
        # Print the results
        print(f"Fraud Probability: {result.fraud_probability}")
        print(f"Confidence: {result.confidence}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Retrieved Patterns: {result.retrieved_patterns}")
        print("\nReasoning:")
        print(result.reasoning)
        print("\nFull Analysis:")
        print(result.full_analysis)
        
    except Exception as e:
        logger.error(f"Error during transaction analysis: {str(e)}")
    
    print_separator("TESTING COMPLETE")

def main():
    """Main function to run the debug script"""
    try:
        print("Starting LLM Service debug script...")
        print(f"Current environment: {settings.APP_ENV}")
        
        # Display key settings 
        print("\nActive Settings:")
        print(f"- OpenAI API Key configured: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
        print(f"- LLM Model: {settings.LLM_MODEL}")
        print(f"- Use Local LLM: {settings.USE_LOCAL_LLM}")
        print(f"- Force Local LLM: {settings.FORCE_LOCAL_LLM}")
        print(f"- Local LLM Model: {settings.LOCAL_LLM_MODEL}")
        
        # Test the LLM service
        test_llm_service()
        
    except Exception as e:
        logger.error(f"Error in debug script: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
