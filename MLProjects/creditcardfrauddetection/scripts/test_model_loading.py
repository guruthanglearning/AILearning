"""
Test script to verify the ML model is loading from file.
"""
import os
import sys
import logging
import json

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.ml_model import MLModel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Test the ML model loading."""
    
    # Model paths
    model_path = os.path.join("data", "models", "fraud_model.joblib")
    scaler_path = os.path.join("data", "models", "scaler.joblib")
    
    # Check if model files exist
    logger.info(f"Checking model file: {model_path}")
    if os.path.exists(model_path):
        logger.info("Model file exists!")
    else:
        logger.warning("Model file does not exist!")
        
    logger.info(f"Checking scaler file: {scaler_path}")
    if os.path.exists(scaler_path):
        logger.info("Scaler file exists!")
    else:
        logger.warning("Scaler file does not exist!")
    
    # Try to load the model
    logger.info("Attempting to load ML model from files")
    model = MLModel(model_path=model_path, scaler_path=scaler_path)
    
    # Create sample features
    sample = {
        "amount": 999.99,
        "is_online": True,
        "hour_of_day": 14,
        "day_of_week": 3,
        "txn_count_1h": 1,
        "txn_count_24h": 5,
        "txn_count_7d": 12,
        "avg_amount_7d": 325.75,
        "merchant_risk_score": 0.8,
        "behavior_anomaly_score": 0.6,
        "distance_from_home": 1000,
        "distance_from_last_txn": 950,
        "location_risk_score": 0.7,
        "amount_velocity_24h": 1500.0,
        "unique_merchants_24h": 4,
        "days_since_last_txn": 1
    }
    
    # Make a prediction
    fraud_probability, confidence = model.predict(sample)
    
    # Print result
    logger.info(f"Prediction result: Fraud probability = {fraud_probability:.4f}, Confidence = {confidence:.4f}")

if __name__ == "__main__":
    main()
