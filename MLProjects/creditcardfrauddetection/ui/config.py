"""
Configuration settings for the Streamlit UI.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API settings
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "development_api_key_for_testing")

# UI settings
PAGE_TITLE = "Credit Card Fraud Detection System"
PAGE_ICON = "💳"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# Theme settings
PRIMARY_COLOR = "#1E88E5"
SECONDARY_COLOR = "#424242"
BACKGROUND_COLOR = "#f9f9f9"
FRAUD_COLOR = "#D32F2F"
LEGITIMATE_COLOR = "#388E3C"
REVIEW_COLOR = "#FFA000"
INFO_COLOR = "#E3F2FD"

# Default transaction fields
DEFAULT_TRANSACTION = {
    "card_id": "card_1234567890",
    "customer_id": "cust_12345",
    "merchant_id": "merch_67890",
    "merchant_name": "Local Store",
    "merchant_category": "Retail",
    "merchant_country": "US",
    "merchant_zip": "98040",
    "amount": 100.00,
    "is_online": False,
    "device_id": "dev_regular123",
    "ip_address": "192.168.1.100",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "currency": "USD"
}
