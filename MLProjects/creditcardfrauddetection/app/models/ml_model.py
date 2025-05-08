"""
Machine learning model for initial fraud screening.
"""

import logging
import pickle
import os
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import joblib

from app.core.config import settings

logger = logging.getLogger(__name__)

class MLModel:
    """
    Machine learning model for initial fraud screening.
    In production, this would load a pre-trained model.
    """
    def __init__(self, model_path: Optional[str] = None, scaler_path: Optional[str] = None):
        """
        Initialize the ML model.
        
        Args:
            model_path: Path to the saved model file. If None, creates a dummy model.
            scaler_path: Path to the saved scaler file. If None, creates a new scaler.
        """
        self.model = None
        self.scaler = None
        self.feature_columns = [
            "amount", "is_online", "hour_of_day", "day_of_week", 
            "txn_count_1h", "txn_count_24h", "txn_count_7d", 
            "avg_amount_7d", "merchant_risk_score", "behavior_anomaly_score",
            "distance_from_home", "distance_from_last_txn", "location_risk_score",
            "amount_velocity_24h", "unique_merchants_24h", "days_since_last_txn"
        ]
        
        if model_path and os.path.exists(model_path):
            self._load_model(model_path)
            if scaler_path and os.path.exists(scaler_path):
                self._load_scaler(scaler_path)
            else:
                logger.warning("No scaler file found. Creating a new scaler.")
                self.scaler = StandardScaler()
        else:
            # Create a demo model if no model file exists
            logger.warning("No model file found. Creating a demo model.")
            self._create_demo_model()
    
    def _load_model(self, model_path: str):
        """
        Load the pre-trained XGBoost model from a file.
        
        Args:
            model_path: Path to the saved model file
        """
        try:
            logger.info(f"Loading model from {model_path}")
            self.model = joblib.load(model_path)
            logger.info(f"Successfully loaded model from {model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self._create_demo_model()
    
    def _load_scaler(self, scaler_path: str):
        """
        Load the pre-trained scaler from a file.
        
        Args:
            scaler_path: Path to the saved scaler file
        """
        try:
            logger.info(f"Loading scaler from {scaler_path}")
            self.scaler = joblib.load(scaler_path)
            logger.info(f"Successfully loaded scaler from {scaler_path}")
        except Exception as e:
            logger.error(f"Error loading scaler: {str(e)}")
            self.scaler = StandardScaler()
    
    def _create_demo_model(self):
        """
        Create a simple demo model for development/testing.
        In production, you would use a properly trained model.
        """
        params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'scale_pos_weight': 10,  # Helps with imbalanced classes
            'min_child_weight': 1,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'seed': 42
        }
        self.model = xgb.XGBClassifier(**params)
        self.scaler = StandardScaler()
        logger.info("Created demo XGBoost model for fraud detection")
        
        # In a real implementation, we would train the model here
        # For demo purposes, we just initialize it
        
    def _preprocess_features(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Preprocess features for model prediction.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Preprocessed feature array
        """
        # Extract and order features - in production, this order must match the training data
        feature_list = []
        for col in self.feature_columns:
            if col in features:
                feature_list.append(features[col])
            else:
                # If a feature is missing, use a default value (0)
                # In production, you would handle this more carefully
                feature_list.append(0.0)
                logger.warning(f"Missing feature: {col}")
        
        # Convert to numpy array
        X = np.array(feature_list).reshape(1, -1)
        
        # Scale features if scaler exists
        # In production, we would use a pre-fitted scaler
        if self.scaler is not None:
            # In production, the scaler would be already fitted
            # For demo purposes, we just use it as is
            try:
                X = self.scaler.transform(X)
            except Exception as e:
                logger.warning(f"Could not scale features: {str(e)}")
                # If scaler is not fitted, just use unscaled features
                pass
        
        return X
    
    def predict(self, features: Dict[str, Any]) -> Tuple[float, float]:
        """
        Predict fraud probability for a transaction.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Tuple of (fraud_probability, model_confidence)
        """
        # For a real model with real data, we would use the actual model prediction
        # For demo purposes, we use a simplistic approach
        
        # Check if this is a "known" fraud pattern
        # These are simplified patterns for demonstration
        is_suspicious = (
            (features['amount'] > 1000 and features['is_online'] == 1) or
            (features['merchant_risk_score'] > 0.8) or
            (features['txn_count_24h'] > 15) or
            (features.get('distance_from_last_txn', 0) > 1000 and features['is_online'] == 0) or
            (features['hour_of_day'] in [1, 2, 3, 4] and features['amount'] > 200) or
            (features.get('behavior_anomaly_score', 0) > 0.9)
        )
        
        # If we have an actual trained model, use it
        if self.model is not None and hasattr(self.model, 'predict_proba'):
            try:
                # Preprocess features
                X = self._preprocess_features(features)
                
                # Make prediction
                y_prob = self.model.predict_proba(X)[0, 1]  # Probability of fraud
                
                # Calculate confidence - higher for extreme probabilities
                confidence = max(y_prob, 1 - y_prob)
                
                # Add some randomness for demo purposes
                # In production, we would just return the model's prediction
                # Adjust based on suspicious patterns
                if is_suspicious:
                    y_prob = max(y_prob, 0.7)  # Increase probability if suspicious
                    confidence = max(confidence, 0.8)  # Increase confidence if suspicious
                
                return y_prob, confidence
                
            except Exception as e:
                logger.error(f"Error in model prediction: {str(e)}")
                # Fall back to heuristic approach
        
        # Fallback heuristic approach when we don't have a working model
        # Extract risk factors
        risk_factors = [
            features['amount'] > 1000,
            features['is_online'] == 1,
            features['txn_count_24h'] > 10,
            features['merchant_risk_score'] > 0.7,
            features.get('location_risk_score', 0) > 0.8,
            features.get('distance_from_last_txn', 0) > 1000,
            features['hour_of_day'] < 5,  # Late night transaction
            features.get('behavior_anomaly_score', 0) > 0.7,
            features.get('amount_velocity_24h', 0) > 3.0  # Sudden increase in spending
        ]
        
        # Count risk factors
        risk_score = sum(1 for factor in risk_factors if factor) / len(risk_factors)
        
        # Confidence is higher for more extreme risk scores
        confidence = 0.5 + (abs(risk_score - 0.5) * 0.6)
        
        # Is it suspicious? Increase the risk
        if is_suspicious:
            risk_score = max(risk_score, 0.7)
            confidence = max(confidence, 0.8)
        
        return risk_score, confidence
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """
        Train the model on provided data.
        In production, this would be done offline and the model would be loaded.
        
        Args:
            X_train: Training features
            y_train: Training labels
        """
        if self.model is None:
            self._create_demo_model()
        
        if self.scaler is None:
            self.scaler = StandardScaler()
        
        # Fit the scaler
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train the model
        self.model.fit(X_train_scaled, y_train)
        logger.info("Model trained successfully")
    
    def save_model(self, model_path: str, scaler_path: str):
        """
        Save the trained model and scaler to files.
        
        Args:
            model_path: Path to save the model
            scaler_path: Path to save the scaler
        """
        if self.model is not None:
            try:
                logger.info(f"Saving model to {model_path}")
                joblib.dump(self.model, model_path)
                logger.info(f"Model saved successfully to {model_path}")
            except Exception as e:
                logger.error(f"Error saving model: {str(e)}")
        
        if self.scaler is not None:
            try:
                logger.info(f"Saving scaler to {scaler_path}")
                joblib.dump(self.scaler, scaler_path)
                logger.info(f"Scaler saved successfully to {scaler_path}")
            except Exception as e:
                logger.error(f"Error saving scaler: {str(e)}")
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate the model on test data.
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        
        if self.model is None:
            logger.error("Model not initialized")
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "auc": 0.0
            }
        
        # Scale the test data
        if self.scaler is not None:
            try:
                X_test_scaled = self.scaler.transform(X_test)
            except Exception as e:
                logger.error(f"Error scaling test data: {str(e)}")
                X_test_scaled = X_test
        else:
            X_test_scaled = X_test
        
        # Make predictions
        y_pred = self.model.predict(X_test_scaled)
        y_prob = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
            "auc": roc_auc_score(y_test, y_prob)
        }
        
        logger.info(f"Model evaluation metrics: {metrics}")
        return metrics