"""
Feature engineering utilities for credit card fraud detection.
Extracts and computes features from transaction data.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from app.api.models import Transaction

logger = logging.getLogger(__name__)

def engineer_features(transaction: Transaction) -> Dict[str, Any]:
    """
    Extract and compute features from transaction data.
    
    Args:
        transaction: The transaction data
        
    Returns:
        Dict containing computed features
    """
    # Parse timestamp
    timestamp = datetime.fromisoformat(transaction.timestamp.replace('Z', '+00:00'))
    
    # Extract basic features
    features = {
        "transaction_id": transaction.transaction_id,
        "amount": transaction.amount,
        "is_online": int(transaction.is_online),
        "hour_of_day": timestamp.hour,
        "day_of_week": timestamp.weekday(),
        "merchant_category": transaction.merchant_category,
        "merchant_country": transaction.merchant_country,
        "currency": transaction.currency,
        "timestamp": timestamp,
    }
    
    # DATA QUALITY VALIDATION - Add risk score for missing/suspicious data
    data_quality_score = calculate_data_quality_risk(transaction)
    features["data_quality_risk_score"] = data_quality_score
    
    # Calculate velocity features (would connect to a database in production)
    # These would be calculated from historical data in a real implementation
    features.update(get_velocity_features(transaction.customer_id, transaction.card_id))
    
    # CRITICAL: Always calculate country and category risk (not just when coordinates present)
    features["country_risk_score"] = calculate_country_risk(transaction.merchant_country)
    features["category_risk_score"] = calculate_category_risk(transaction.merchant_category)
    
    # Check for sanctioned countries
    features["is_sanctioned_country"] = is_sanctioned_country(transaction.merchant_country)
    
    # Detect category mismatch (e.g., Gas Station selling Electronics)
    features["category_mismatch"] = detect_category_mismatch(
        transaction.merchant_name, 
        transaction.merchant_category
    )
    
    # Calculate location-based features if geographical data is available
    if transaction.latitude and transaction.longitude:
        geo_features = calculate_geo_features(transaction)
        features.update(geo_features)
    else:
        # Missing location data for online transaction is suspicious
        features["location_risk_score"] = 0.7 if transaction.is_online else 0.3
        
    # Calculate merchant risk score (would be from a real database)
    features["merchant_risk_score"] = get_merchant_risk_score(transaction.merchant_id, transaction.merchant_name)
    
    # Additional behavioral features (would be from actual data in production)
    behavior_features = calculate_behavioral_features(transaction.customer_id)
    features.update(behavior_features)
    
    return features

def get_velocity_features(customer_id: str, card_id: str) -> Dict[str, float]:
    """
    Calculate transaction velocity features.
    
    In production, this would query a database of recent transactions
    for the specific customer/card to calculate actual metrics.
    
    Args:
        customer_id: Customer identifier
        card_id: Card identifier
        
    Returns:
        Dict of velocity features
    """
    # Mock velocity features for demonstration
    # In production, these would be calculated from real transaction history
    return {
        "txn_count_1h": 2.0,  # Number of transactions in last hour
        "txn_count_24h": 5.0,  # Number of transactions in last 24 hours
        
        "txn_count_7d": 12.0,  # Number of transactions in last 7 days
        "avg_amount_7d": 120.0,  # Average transaction amount in last 7 days
        "amount_velocity_24h": 1.5,  # Rate of spending increase/decrease in 24h
        "unique_merchants_24h": 3.0,  # Number of unique merchants in 24h
        "max_amount_30d": 250.0,  # Maximum transaction amount in last 30 days
        "std_amount_30d": 75.0,  # Standard deviation of amounts in last 30 days
    }

def is_sanctioned_country(merchant_country: str) -> bool:
    """
    Check if a country is under sanctions.
    
    Args:
        merchant_country: 2-letter country code
        
    Returns:
        True if country is sanctioned, False otherwise
    """
    # SANCTIONED COUNTRIES - Transactions should be blocked
    SANCTIONED_COUNTRIES = {
        "RU",  # Russia
        "BY",  # Belarus
        "KP",  # North Korea
        "IR",  # Iran
        "SY",  # Syria
        "CU",  # Cuba (partial sanctions)
        "VE",  # Venezuela (targeted sanctions)
    }
    
    country = merchant_country.upper() if merchant_country else ""
    return country in SANCTIONED_COUNTRIES

def calculate_country_risk(merchant_country: str) -> float:
    """
    Calculate risk score based on merchant country.
    
    Args:
        merchant_country: 2-letter country code
        
    Returns:
        Risk score from 0-1 where higher indicates higher fraud risk
    """
    # Check for sanctioned countries first
    if is_sanctioned_country(merchant_country):
        country_code = merchant_country.upper() if merchant_country else ""
        logger.warning(f"SANCTIONED COUNTRY DETECTED: {country_code} - AUTO-DENY")
        return 0.99  # Maximum risk for sanctioned countries
    
    # HIGH-RISK COUNTRIES - Known for higher fraud rates
    HIGH_RISK_COUNTRIES = {
        "NG": 0.95,  # Nigeria - Very high risk
        "GH": 0.90,  # Ghana - Very high risk
        "PK": 0.85,  # Pakistan - High risk
        "BD": 0.85,  # Bangladesh - High risk
        "ID": 0.80,  # Indonesia - High risk
        "PH": 0.75,  # Philippines - Elevated risk
        "VN": 0.75,  # Vietnam - Elevated risk
        "RO": 0.80,  # Romania - High risk
        "BG": 0.80,  # Bulgaria - High risk
        "UA": 0.80,  # Ukraine - High risk
        "CN": 0.70,  # China - Elevated risk
        "IN": 0.65,  # India - Moderate-high risk
        "BR": 0.70,  # Brazil - Elevated risk
        "MX": 0.65,  # Mexico - Moderate-high risk
    }
    
    # MEDIUM-RISK COUNTRIES
    MEDIUM_RISK_COUNTRIES = {
        "TR": 0.55,  # Turkey
        "ZA": 0.50,  # South Africa
        "TH": 0.50,  # Thailand
        "MY": 0.50,  # Malaysia
    }
    
    # LOW-RISK COUNTRIES (US, Canada, Western Europe, etc.)
    # Default to low risk for developed nations
    country = merchant_country.upper() if merchant_country else "US"
    
    if country in HIGH_RISK_COUNTRIES:
        risk = HIGH_RISK_COUNTRIES[country]
        logger.info(f"High-risk country detected: {country} (risk={risk})")
        return risk
    elif country in MEDIUM_RISK_COUNTRIES:
        return MEDIUM_RISK_COUNTRIES[country]
    else:
        # Default low risk for established markets (US, CA, UK, EU, etc.)
        return 0.25

def calculate_category_risk(merchant_category: str) -> float:
    """
    Calculate risk score based on merchant category.
    
    Args:
        merchant_category: Merchant business category
        
    Returns:
        Risk score from 0-1 where higher indicates higher fraud risk
    """
    # HIGH-RISK CATEGORIES - Commonly targeted by fraudsters
    HIGH_RISK_CATEGORIES = {
        "Digital Goods": 0.90,  # Very high risk - easy to resell
        "digital goods": 0.90,
        "electronics": 0.85,  # High risk - valuable and resellable
        "Electronics": 0.85,
        "cryptocurrency": 0.95,  # Very high risk
        "Cryptocurrency": 0.95,
        "gift cards": 0.92,  # Very high risk - like cash
        "Gift Cards": 0.92,
        "prepaid cards": 0.92,
        "Prepaid Cards": 0.92,
        "jewelry": 0.80,  # High risk - valuable
        "Jewelry": 0.80,
        "luxury goods": 0.80,
        "Luxury Goods": 0.80,
        "money transfer": 0.88,
        "Money Transfer": 0.88,
    }
    
    # MEDIUM-RISK CATEGORIES
    MEDIUM_RISK_CATEGORIES = {
        "online retail": 0.55,
        "Online Retail": 0.55,
        "clothing": 0.50,
        "Clothing": 0.50,
        "entertainment": 0.50,
        "Entertainment": 0.50,
    }
    
    # LOW-RISK CATEGORIES
    LOW_RISK_CATEGORIES = {
        "grocery": 0.25,
        "Grocery": 0.25,
        "gas station": 0.20,
        "Gas Station": 0.20,
        "restaurant": 0.30,
        "Restaurant": 0.30,
        "pharmacy": 0.25,
        "Pharmacy": 0.25,
        "utilities": 0.15,
        "Utilities": 0.15,
    }
    
    category = merchant_category if merchant_category else "unknown"
    
    if category in HIGH_RISK_CATEGORIES:
        risk = HIGH_RISK_CATEGORIES[category]
        logger.info(f"High-risk category detected: {category} (risk={risk})")
        return risk
    elif category in MEDIUM_RISK_CATEGORIES:
        return MEDIUM_RISK_CATEGORIES[category]
    elif category in LOW_RISK_CATEGORIES:
        return LOW_RISK_CATEGORIES[category]
    else:
        # Default moderate risk for unknown categories
        return 0.40

def detect_category_mismatch(merchant_name: str, merchant_category: str) -> float:
    """
    Detect if merchant name doesn't match the stated category.
    This is a common fraud indicator (e.g., Gas Station selling Electronics).
    
    Args:
        merchant_name: Name of the merchant
        merchant_category: Stated category
        
    Returns:
        Mismatch risk score from 0-1
    """
    if not merchant_name or not merchant_category:
        return 0.0
    
    merchant_name_lower = merchant_name.lower()
    merchant_category_lower = merchant_category.lower()
    
    # Define expected keywords for each category
    CATEGORY_KEYWORDS = {
        "electronics": ["tech", "electron", "computer", "phone", "gadget", "device"],
        "gas station": ["gas", "fuel", "petrol", "shell", "exxon", "chevron", "bp"],
        "grocery": ["grocery", "market", "food", "supermarket", "store"],
        "restaurant": ["restaurant", "cafe", "diner", "grill", "bistro", "eatery"],
        "pharmacy": ["pharmacy", "drug", "cvs", "walgreens", "rite aid"],
        "jewelry": ["jewelry", "jewel", "diamond", "gold"],
    }
    
    # Check if merchant name contains keywords from a different category
    for category, keywords in CATEGORY_KEYWORDS.items():
        # If merchant name suggests one category but transaction is in another
        if any(keyword in merchant_name_lower for keyword in keywords):
            if category != merchant_category_lower and merchant_category_lower in CATEGORY_KEYWORDS:
                logger.warning(f"CATEGORY MISMATCH: Merchant '{merchant_name}' suggests '{category}' "
                             f"but transaction category is '{merchant_category}'")
                return 0.90  # High mismatch risk
    
    return 0.0  # No mismatch detected

def calculate_geo_features(transaction: Transaction) -> Dict[str, float]:
    """
    Calculate geographical features from transaction data.
    
    In production, this would compare the current transaction location
    to the customer's home address and recent transaction locations.
    
    Args:
        transaction: Transaction data with location information
        
    Returns:
        Dict of geographical features
    """
    # Use the dedicated risk calculation functions
    country_risk = calculate_country_risk(transaction.merchant_country)
    category_risk = calculate_category_risk(transaction.merchant_category)
    
    # Combine risks for location risk score
    location_risk = max(country_risk, 0.3)  # Base location risk
    
    logger.info(f"Transaction {transaction.transaction_id}: Country={transaction.merchant_country}, "
                f"Country Risk={country_risk}, Category={transaction.merchant_category}, Category Risk={category_risk}")
    
    # In a real implementation, this would calculate:
    # - Distance from home address
    # - Distance from last transaction
    # - Velocity (distance/time) from last transaction
    # - Whether location is in a high-fraud area
    
    # Mock data for demonstration with real risk assessment
    return {
        "distance_from_home": 15.2,  # Miles or km from billing address
        "distance_from_last_txn": 12.8,  # Distance from last transaction
        "location_risk_score": location_risk,  # Risk score of current location (0-1)
        "country_risk_score": country_risk,  # NEW: Country-specific risk
        "category_risk_score": category_risk,  # NEW: Category-specific risk
        "velocity_since_last_txn": 25.6,  # Speed (distance/time) since last transaction
        "unusual_location": 1 if country_risk > 0.7 else 0,  # Binary indicator for unusual location
        "high_risk_region": 1 if country_risk > 0.7 else 0,  # Binary indicator for high-risk region
    }

def calculate_data_quality_risk(transaction: Transaction) -> float:
    """
    Calculate risk score based on data quality issues.
    Missing or suspicious data patterns indicate higher fraud risk.
    
    Args:
        transaction: Transaction data to validate
        
    Returns:
        Risk score from 0-1 where higher indicates more data quality issues
    """
    risk_factors = []
    
    # Check for missing or suspicious merchant information
    if not transaction.merchant_name or transaction.merchant_name.strip() == "":
        risk_factors.append(0.9)  # Missing merchant name is very suspicious
        logger.warning(f"Transaction {transaction.transaction_id}: Missing merchant name")
    elif transaction.merchant_name in ["No merchant name", "Unknown", "N/A", "Test"]:
        risk_factors.append(0.8)  # Placeholder merchant name
        logger.warning(f"Transaction {transaction.transaction_id}: Suspicious merchant name: {transaction.merchant_name}")
    
    # Check for null island coordinates (0, 0)
    if transaction.latitude == 0.0 and transaction.longitude == 0.0:
        risk_factors.append(0.95)  # Null island is highly suspicious
        logger.warning(f"Transaction {transaction.transaction_id}: Null island coordinates detected")
    
    # Check for missing location on online transaction
    if transaction.is_online and (not transaction.latitude or not transaction.longitude):
        risk_factors.append(0.6)  # Online transaction should have IP geolocation
    
    # Check for invalid/missing merchant category
    if not transaction.merchant_category or transaction.merchant_category in ["N/A", "Unknown", ""]:
        risk_factors.append(0.7)  # Missing category is suspicious
    
    # Check for suspicious merchant ZIP/postal codes
    if hasattr(transaction, 'merchant_zip'):
        merchant_zip = str(getattr(transaction, 'merchant_zip', ''))
        if len(merchant_zip) > 10 or not merchant_zip.replace('-', '').isalnum():
            risk_factors.append(0.6)  # Invalid ZIP format
            logger.warning(f"Transaction {transaction.transaction_id}: Suspicious ZIP code: {merchant_zip}")
    
    # Check for missing device/tracking info on online transactions
    if transaction.is_online:
        # In a real system, check for device_id, ip_address, user_agent
        # For now, we'll check if merchant_id looks suspicious
        if not transaction.merchant_id or transaction.merchant_id == "unknown":
            risk_factors.append(0.5)
    
    # Calculate average risk from all factors
    if risk_factors:
        return sum(risk_factors) / len(risk_factors)
    return 0.0  # No data quality issues detected


def get_merchant_risk_score(merchant_id: str, merchant_name: str = None) -> float:
    """
    Get risk score for a merchant based on historical fraud.
    
    In production, this would query a database of merchant risk scores
    that are regularly updated based on fraud patterns.
    
    Args:
        merchant_id: Merchant identifier
        merchant_name: Merchant name (optional, for additional validation)
        
    Returns:
        Risk score from 0-1 where higher is riskier
    """
    # Check for missing/suspicious merchant name first
    if not merchant_name or merchant_name.strip() == "":
        return 0.85  # Missing merchant name is high risk
    
    if merchant_name in ["No merchant name", "Unknown", "N/A", "Test", ""]:
        return 0.80  # Placeholder merchant name is high risk
    
    # Mock data for demonstration
    merchant_scores = {
        "merch_24680": 0.12,
        "merch_13579": 0.85,
        "merch_98765": 0.05,
        # Add more merchants here
    }
    
    # Check if merchant_id looks suspicious
    if not merchant_id or merchant_id == "unknown" or merchant_id == "":
        return 0.75  # Missing merchant ID is suspicious
    
    return merchant_scores.get(merchant_id, 0.5)  # Default score if merchant not found

def calculate_behavioral_features(customer_id: str) -> Dict[str, float]:
    """
    Calculate behavioral features based on customer history.
    
    In production, this would analyze the customer's transaction patterns
    to identify deviations from normal behavior.
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Dict of behavioral features
    """
    # Mock data for demonstration
    # In production, these would be calculated from customer's transaction history
    return {
        "avg_txn_frequency": 2.3,  # Average transactions per day
        "avg_daily_spend": 85.0,  # Average daily spending amount
        "behavior_anomaly_score": 0.2,  # Anomaly score for recent behavior
        "days_since_last_txn": 1.5,  # Days since last transaction
        "typical_txn_hour": 15,  # Typical hour of day for transactions (24h format)
        "typical_txn_amount": 65.0,  # Typical transaction amount
    }

def create_transaction_text(transaction: Transaction, features: Dict[str, Any]) -> str:
    """
    Create a text description of the transaction for the LLM.
    
    Args:
        transaction: Transaction data
        features: Computed features
        
    Returns:
        Formatted text description
    """
    timestamp = datetime.fromisoformat(transaction.timestamp.replace('Z', '+00:00'))
    
    # Add warnings for critical risk factors
    warnings = []
    if features.get('is_sanctioned_country', False):
        warnings.append(f"⚠️ CRITICAL: Merchant country {transaction.merchant_country} is under sanctions")
    if features.get('category_mismatch', 0) > 0.8:
        warnings.append(f"⚠️ WARNING: Merchant name '{transaction.merchant_name}' doesn't match category '{transaction.merchant_category}'")
    if features.get('country_risk_score', 0) > 0.85:
        warnings.append(f"⚠️ HIGH RISK: Country {transaction.merchant_country} has very high fraud rate")
    
    warnings_text = "\n    ".join(warnings) if warnings else "None"
    
    transaction_text = f"""
    Transaction ID: {transaction.transaction_id}
    Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({features['hour_of_day']}:00, day of week: {features['day_of_week']})
    Amount: {transaction.amount} {transaction.currency}
    Merchant: {transaction.merchant_name or 'Unknown'} (ID: {transaction.merchant_id})
    Merchant Category: {transaction.merchant_category}
    Merchant Location: {transaction.merchant_country} {transaction.merchant_zip if transaction.merchant_zip else ''}
    Transaction Type: {"Online" if transaction.is_online else "In-person"}
    
    CRITICAL WARNINGS:
    {warnings_text}
    
    Recent Activity:
    - Transactions in last hour: {features['txn_count_1h']}
    - Transactions in last 24 hours: {features['txn_count_24h']}
    - Transactions in last 7 days: {features['txn_count_7d']}
    - Average transaction amount (7 days): {features['avg_amount_7d']} {transaction.currency}
    - Unique merchants in last 24h: {features['unique_merchants_24h']}
    
    Risk Indicators:
    - Country risk score: {features['country_risk_score']:.2f}
    - Category risk score: {features['category_risk_score']:.2f}
    - Category mismatch score: {features.get('category_mismatch', 0):.2f}
    - Merchant risk score: {features['merchant_risk_score']:.2f}
    - Days since last transaction: {features['days_since_last_txn']}
    - Behavior anomaly score: {features['behavior_anomaly_score']:.2f}
    """
    
    if transaction.latitude and transaction.longitude:
        transaction_text += f"""
    Geographic Information:
    - Location: {transaction.latitude}, {transaction.longitude}
    - Distance from billing address: {features['distance_from_home']} miles
    - Distance from last transaction: {features['distance_from_last_txn']} miles
    - Location risk score: {features['location_risk_score']}
        """
    
    return transaction_text

def select_features_for_ml(features: Dict[str, Any]) -> Dict[str, float]:
    """
    Select and normalize features for machine learning model.
    
    Args:
        features: Complete set of computed features
        
    Returns:
        Dict of features formatted for ML model input
    """
    # Select only numerical features for the ML model
    ml_features = {
        "amount": features["amount"],
        "is_online": features["is_online"],
        "hour_of_day": features["hour_of_day"] / 24.0,  # Normalize to 0-1
        "day_of_week": features["day_of_week"] / 6.0,  # Normalize to 0-1
        "txn_count_1h": features["txn_count_1h"] / 10.0,  # Normalize
        "txn_count_24h": features["txn_count_24h"] / 20.0,  # Normalize
        "txn_count_7d": features["txn_count_7d"] / 50.0,  # Normalize
        "avg_amount_7d": features["avg_amount_7d"] / 1000.0,  # Normalize
        "merchant_risk_score": features["merchant_risk_score"],
        "behavior_anomaly_score": features["behavior_anomaly_score"],
    }
    
    # Add geographical features if available
    if "distance_from_home" in features:
        geo_features = {
            "distance_from_home": features["distance_from_home"] / 100.0,  # Normalize
            "distance_from_last_txn": features["distance_from_last_txn"] / 100.0,  # Normalize
            "location_risk_score": features["location_risk_score"],
        }
        ml_features.update(geo_features)
    
    return ml_features