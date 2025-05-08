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
    
    # Calculate velocity features (would connect to a database in production)
    # These would be calculated from historical data in a real implementation
    features.update(get_velocity_features(transaction.customer_id, transaction.card_id))
    
    # Calculate location-based features if geographical data is available
    if transaction.latitude and transaction.longitude:
        geo_features = calculate_geo_features(transaction)
        features.update(geo_features)
        
    # Calculate merchant risk score (would be from a real database)
    features["merchant_risk_score"] = get_merchant_risk_score(transaction.merchant_id)
    
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
    # In a real implementation, this would calculate:
    # - Distance from home address
    # - Distance from last transaction
    # - Velocity (distance/time) from last transaction
    # - Whether location is in a high-fraud area
    
    # Mock data for demonstration
    return {
        "distance_from_home": 15.2,  # Miles or km from billing address
        "distance_from_last_txn": 12.8,  # Distance from last transaction
        "location_risk_score": 0.3,  # Risk score of current location (0-1)
        "velocity_since_last_txn": 25.6,  # Speed (distance/time) since last transaction
        "unusual_location": 0,  # Binary indicator for unusual location (1=unusual)
        "high_risk_region": 0,  # Binary indicator for high-risk region (1=high risk)
    }

def get_merchant_risk_score(merchant_id: str) -> float:
    """
    Get risk score for a merchant based on historical fraud.
    
    In production, this would query a database of merchant risk scores
    that are regularly updated based on fraud patterns.
    
    Args:
        merchant_id: Merchant identifier
        
    Returns:
        Risk score from 0-1 where higher is riskier
    """
    # Mock data for demonstration
    merchant_scores = {
        "merch_24680": 0.12,
        "merch_13579": 0.85,
        "merch_98765": 0.05,
        # Add more merchants here
    }
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
    
    transaction_text = f"""
    Transaction ID: {transaction.transaction_id}
    Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({features['hour_of_day']}:00, day of week: {features['day_of_week']})
    Amount: {transaction.amount} {transaction.currency}
    Merchant: {transaction.merchant_name or 'Unknown'} (ID: {transaction.merchant_id})
    Merchant Category: {transaction.merchant_category}
    Merchant Location: {transaction.merchant_country} {transaction.merchant_zip if transaction.merchant_zip else ''}
    Transaction Type: {"Online" if transaction.is_online else "In-person"}
    
    Recent Activity:
    - Transactions in last hour: {features['txn_count_1h']}
    - Transactions in last 24 hours: {features['txn_count_24h']}
    - Transactions in last 7 days: {features['txn_count_7d']}
    - Average transaction amount (7 days): {features['avg_amount_7d']} {transaction.currency}
    - Unique merchants in last 24h: {features['unique_merchants_24h']}
    
    Risk Indicators:
    - Merchant risk score: {features['merchant_risk_score']}
    - Days since last transaction: {features['days_since_last_txn']}
    - Behavior anomaly score: {features['behavior_anomaly_score']}
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