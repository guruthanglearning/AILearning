"""
Test ML model functionality.
"""
import pytest
import numpy as np
import os
from unittest.mock import patch, MagicMock

from app.models.ml_model import MLModel

@pytest.fixture
def sample_features():
    """Create sample features for testing."""
    return {
        "amount": 100.0,
        "is_online": 1,
        "txn_count_24h": 5,
        "merchant_risk_score": 0.3,
        "location_risk_score": 0.2,
        "distance_from_last_txn": 200,
        "hour_of_day": 14,
        "behavior_anomaly_score": 0.4,
        "amount_velocity_24h": 1.5
    }

@pytest.fixture
def mock_model():
    """Create a mock XGBoost model."""
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.8, 0.2]])  # 20% probability of fraud
    model.predict.return_value = np.array([0])  # Not fraud
    return model

def test_model_creation():
    """Test model creation."""
    # Create a model
    model = MLModel()
    
    # Check model initialized properly
    assert model.model is not None
    assert model.scaler is not None

def test_model_predict(sample_features, mock_model):
    """Test model prediction."""
    # Create a model with the mock
    with patch.object(MLModel, '_create_demo_model') as mock_create:
        model = MLModel()
        model.model = mock_model
        model.scaler = MagicMock()
        
        # Make a prediction
        fraud_probability, confidence = model.predict(sample_features)
        
        # Check results
        assert isinstance(fraud_probability, float)
        assert isinstance(confidence, float)
        assert 0 <= fraud_probability <= 1
        assert 0 <= confidence <= 1
        
        # Verify mock was called
        mock_model.predict_proba.assert_called_once()

def test_model_save_load(tmp_path):
    """Test model saving and loading."""
    # Create model paths
    model_path = os.path.join(tmp_path, "model.joblib")
    scaler_path = os.path.join(tmp_path, "scaler.joblib")
    
    # Create and save a model
    model = MLModel()
    model.save_model(model_path, scaler_path)
    
    # Check files exist
    assert os.path.exists(model_path)
    assert os.path.exists(scaler_path)
    
    # Load the model
    loaded_model = MLModel(model_path, scaler_path)
    
    # Check model loaded properly
    assert loaded_model.model is not None
    assert loaded_model.scaler is not None

def test_model_train_evaluate():
    """Test model training and evaluation."""
    # Create a model
    model = MLModel()
    
    # Create sample data
    X_train = np.random.rand(100, 10)  # 100 samples, 10 features
    y_train = np.random.randint(0, 2, 100)  # Binary labels
    
    # Train the model
    model.train(X_train, y_train)
    
    # Create test data
    X_test = np.random.rand(20, 10)  # 20 samples, 10 features
    y_test = np.random.randint(0, 2, 20)  # Binary labels
    
    # Evaluate the model
    metrics = model.evaluate(X_test, y_test)
    
    # Check metrics
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert "auc" in metrics
    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["precision"] <= 1
    assert 0 <= metrics["recall"] <= 1
    assert 0 <= metrics["f1"] <= 1
    assert 0 <= metrics["auc"] <= 1
