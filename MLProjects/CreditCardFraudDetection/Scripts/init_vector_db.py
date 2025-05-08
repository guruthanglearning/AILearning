#!/usr/bin/env python
"""
Initialize the vector database with sample fraud patterns.
This script should be run once before starting the API.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Import app modules
from app.services.fraud_detection_service import FraudDetectionService
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Initialize the vector database with sample fraud patterns."""
    logger.info("Initializing vector database with sample fraud patterns")
    
    # Create sample data directory if it doesn't exist
    sample_dir = project_root / "data" / "sample"
    os.makedirs(sample_dir, exist_ok=True)
    
    # Path to sample fraud patterns
    fraud_patterns_path = sample_dir / "fraud_patterns.json"
    
    # Create sample patterns if they don't exist
    if not fraud_patterns_path.exists():
        logger.warning(f"Sample fraud patterns file not found at {fraud_patterns_path}")
        logger.info("Creating sample fraud patterns file")
        
        # Sample fraud patterns
        sample_patterns = [
            {
                "case_id": "fraud_001",
                "detection_date": "2025-04-15",
                "fraud_type": "Card Not Present",
                "method": "Online purchase with stolen card",
                "amount": 899.99,
                "currency": "USD",
                "merchant_category": "Electronics",
                "pattern_description": "Series of increasingly large online purchases within 24 hours, starting with small test transactions. Purchases made from IP addresses in different countries.",
                "indicators": [
                    "Multiple transactions increasing in value",
                    "Purchases from unusual locations",
                    "High-value electronics purchases",
                    "Multiple transactions at odd hours"
                ]
            },
            {
                "case_id": "fraud_002",
                "detection_date": "2025-04-20",
                "fraud_type": "Account Takeover",
                "method": "Changed shipping address just before purchase",
                "amount": 1299.95,
                "currency": "USD",
                "merchant_category": "Luxury Goods",
                "pattern_description": "Account credentials changed within 48 hours of large purchase. Shipping address changed to a freight forwarding service. Contact email and phone also changed.",
                "indicators": [
                    "Recent account credential changes",
                    "Shipping to forwarding service",
                    "Contact information changes",
                    "Unusually large purchase compared to history"
                ]
            },
            {
                "case_id": "fraud_003",
                "detection_date": "2025-05-01",
                "fraud_type": "Card Testing",
                "method": "Rapid small transactions to test card validity",
                "amount": 9.95,
                "currency": "USD",
                "merchant_category": "Digital Goods",
                "pattern_description": "Multiple small transactions (under $10) in rapid succession to test if card is valid. Often followed by larger purchases if the small ones succeed.",
                "indicators": [
                    "Multiple small transactions",
                    "Rapid succession (seconds apart)",
                    "Digital goods or services",
                    "Followed by larger purchases"
                ]
            }
        ]
        
        # Write sample patterns to file
        with open(fraud_patterns_path, "w") as f:
            json.dump(sample_patterns, f, indent=2)
        
        logger.info(f"Created sample fraud patterns file at {fraud_patterns_path}")
    
    # Load fraud patterns
    with open(fraud_patterns_path, "r") as f:
        fraud_patterns = json.load(f)
    
    logger.info(f"Loaded {len(fraud_patterns)} fraud patterns from {fraud_patterns_path}")
    
    # Initialize fraud detection service
    fraud_service = FraudDetectionService()
    
    # Ingest fraud patterns
    count = fraud_service.ingest_fraud_patterns(fraud_patterns)
    
    logger.info(f"Successfully ingested {count} fraud patterns into vector database")
    
    # Get system status
    status = fraud_service.get_system_status()
    logger.info(f"System status: {json.dumps(status, indent=2)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())