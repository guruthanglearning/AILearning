#!/usr/bin/env python
"""
Generate sample transaction data for testing the fraud detection system.
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
NUM_TRANSACTIONS = 100
NUM_CUSTOMERS = 10
NUM_MERCHANTS = 20
MERCHANT_CATEGORIES = [
    "Electronics", "Grocery", "Restaurant", "Travel", "Entertainment",
    "Clothing", "Jewelry", "Automotive", "Healthcare", "Digital Goods"
]
COUNTRIES = ["US", "CA", "UK", "DE", "FR", "AU", "JP", "CN", "BR", "IN"]
CURRENCIES = ["USD", "EUR", "GBP", "CAD", "JPY", "AUD"]

# Define fraud patterns to include in the data
FRAUD_PATTERNS = [
    {
        "name": "Card Testing",
        "description": "Multiple small transactions in rapid succession",
        "generator": lambda customer_id: [
            {
                "amount": random.uniform(1.0, 10.0),
                "is_online": True,
                "merchant_category": "Digital Goods",
                "merchant_country": random.choice(COUNTRIES),
                "currency": "USD",
            } for _ in range(random.randint(3, 8))
        ]
    },
    {
        "name": "Account Takeover",
        "description": "Unusual large purchase after credential change",
        "generator": lambda customer_id: [
            {
                "amount": random.uniform(800.0, 2000.0),
                "is_online": True,
                "merchant_category": random.choice(["Luxury Goods", "Electronics", "Jewelry"]),
                "merchant_country": random.choice(COUNTRIES),
                "currency": "USD",
            }
        ]
    },
    {
        "name": "Unusual Location",
        "description": "Transaction from a different country than normal",
        "generator": lambda customer_id: [
            {
                "amount": random.uniform(100.0, 500.0),
                "is_online": random.choice([True, False]),
                "merchant_category": random.choice(MERCHANT_CATEGORIES),
                "merchant_country": random.choice(["RU", "NG", "UA", "CO", "VN"]),  # Unusual countries
                "currency": "USD",
            }
        ]
    }
]

def generate_customer_ids(num_customers: int) -> list:
    """Generate random customer IDs."""
    return [f"cust_{i:05d}" for i in range(1, num_customers + 1)]

def generate_merchant_ids(num_merchants: int) -> list:
    """Generate random merchant IDs."""
    return [f"merch_{i:05d}" for i in range(1, num_merchants + 1)]

def generate_card_ids(num_customers: int) -> dict:
    """Generate random card IDs for each customer."""
    card_ids = {}
    for i in range(1, num_customers + 1):
        customer_id = f"cust_{i:05d}"
        card_ids[customer_id] = [f"card_{uuid.uuid4().hex[:12]}" for _ in range(random.randint(1, 3))]
    return card_ids

def generate_merchant_data(merchant_ids: list) -> dict:
    """Generate random merchant data."""
    merchant_data = {}
    for merchant_id in merchant_ids:
        merchant_data[merchant_id] = {
            "name": f"Merchant {merchant_id.split('_')[1]}",
            "category": random.choice(MERCHANT_CATEGORIES),
            "country": random.choice(COUNTRIES),
            "zip": f"{random.randint(10000, 99999)}",
            "risk_score": random.uniform(0.0, 1.0)
        }
    return merchant_data

def generate_transaction(
    customer_id: str,
    card_ids: dict,
    merchant_ids: list,
    merchant_data: dict,
    timestamp: datetime,
    is_fraud: bool = False,
    fraud_pattern: dict = None
) -> dict:
    """Generate a random transaction."""
    # Select a random card for the customer
    card_id = random.choice(card_ids[customer_id])
    
    # Select a random merchant
    merchant_id = random.choice(merchant_ids)
    merchant = merchant_data[merchant_id]
    
    # Generate base transaction
    transaction = {
        "transaction_id": f"tx_{uuid.uuid4().hex}",
        "card_id": card_id,
        "customer_id": customer_id,
        "merchant_id": merchant_id,
        "timestamp": timestamp.isoformat() + "Z",
        "amount": random.uniform(10.0, 200.0),
        "merchant_category": merchant["category"],
        "merchant_name": merchant["name"],
        "merchant_country": merchant["country"],
        "merchant_zip": merchant["zip"],
        "is_online": random.choice([True, False]),
        "currency": "USD"
    }
    
    # Add location data for in-person transactions
    if not transaction["is_online"]:
        transaction["latitude"] = random.uniform(25.0, 49.0)  # US latitudes
        transaction["longitude"] = random.uniform(-125.0, -70.0)  # US longitudes
    else:
        # Add device and IP for online transactions
        transaction["device_id"] = f"dev_{uuid.uuid4().hex[:8]}"
        transaction["ip_address"] = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    # If this is a fraud transaction, apply the fraud pattern
    if is_fraud and fraud_pattern:
        pattern_transaction = fraud_pattern["generator"](customer_id)[0]
        transaction.update(pattern_transaction)
    
    return transaction

def main():
    """Generate sample transaction data."""
    logger.info("Generating sample transaction data")
    
    # Create data directory if it doesn't exist
    data_dir = project_root / "data" / "sample"
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate customer and merchant data
    customer_ids = generate_customer_ids(NUM_CUSTOMERS)
    merchant_ids = generate_merchant_ids(NUM_MERCHANTS)
    card_ids = generate_card_ids(NUM_CUSTOMERS)
    merchant_data = generate_merchant_data(merchant_ids)
    
    # Generate transactions
    transactions = []
    current_time = datetime.now()
    
    # Generate normal transactions
    for i in range(NUM_TRANSACTIONS):
        # Select a random customer
        customer_id = random.choice(customer_ids)
        
        # Generate a random timestamp in the last 30 days
        days_ago = random.uniform(0, 30)
        hours_ago = random.uniform(0, 24)
        tx_timestamp = current_time - timedelta(days=days_ago, hours=hours_ago)
        
        # Determine if this is a fraud transaction (10% chance)
        is_fraud = random.random() < 0.1
        fraud_pattern = random.choice(FRAUD_PATTERNS) if is_fraud else None
        
        # Generate the transaction
        transaction = generate_transaction(
            customer_id, card_ids, merchant_ids, merchant_data, tx_timestamp, is_fraud, fraud_pattern
        )
        
        # Add to transactions list
        transactions.append(transaction)
    
    # Sort transactions by timestamp
    transactions.sort(key=lambda x: x["timestamp"])
    
    # Save transactions to file
    transactions_path = data_dir / "sample_transactions.json"
    with open(transactions_path, "w") as f:
        json.dump(transactions, f, indent=2)
    
    logger.info(f"Generated {len(transactions)} sample transactions and saved to {transactions_path}")
    
    # Save fraud patterns to file (for documentation)
    fraud_patterns_info = [
        {
            "name": pattern["name"],
            "description": pattern["description"]
        } for pattern in FRAUD_PATTERNS
    ]
    
    fraud_patterns_path = data_dir / "sample_fraud_patterns_info.json"
    with open(fraud_patterns_path, "w") as f:
        json.dump(fraud_patterns_info, f, indent=2)
    
    logger.info(f"Saved fraud pattern information to {fraud_patterns_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())