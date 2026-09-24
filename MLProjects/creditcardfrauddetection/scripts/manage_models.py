#!/usr/bin/env python3
"""
Script for managing ML models used in the fraud detection system.
This script can download pretrained models, train new models, and evaluate model performance.
"""

import os
import sys
import argparse
import logging
import joblib
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.ml_model import MLModel
from app.utils.feature_engineering import engineer_features, select_features_for_ml
from app.api.models import Transaction
from app.core.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_data(data_path, sample_size=None):
    """
    Load transaction data from a CSV file.
    
    Args:
        data_path (str): Path to the data file
        sample_size (int, optional): Number of samples to use
        
    Returns:
        DataFrame: Loaded data
    """
    logger.info(f"Loading data from {data_path}")
    
    # Load data
    df = pd.read_csv(data_path)
    
    # Sample if requested
    if sample_size and sample_size < len(df):
        df = df.sample(sample_size, random_state=42)
    
    logger.info(f"Loaded {len(df)} transactions")
    return df

def _clean(value, default=None):
    """Convert a pandas NaN/missing scalar cell to `default`; pass everything else through unchanged."""
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return value  # not a scalar pd.isna can judge (e.g. list-valued cell) - leave as-is
    return default if isinstance(missing, bool) and missing else value

_TRUE_TOKENS = {"true", "1", "yes", "y"}
_FALSE_TOKENS = {"false", "0", "no", "n"}

def _parse_bool(value, field_name="value"):
    """Strictly parse a CSV cell into a bool; raises ValueError rather than guessing on anything ambiguous."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in _TRUE_TOKENS:
        return True
    if isinstance(value, str) and value.strip().lower() in _FALSE_TOKENS:
        return False
    raise ValueError(f"unrecognized boolean value {value!r} for {field_name}")

def prepare_data(df):
    """
    Prepare data for training.

    Args:
        df (DataFrame): Raw data

    Returns:
        tuple: X (features), y (labels), feature_names
    """
    logger.info("Preparing data for training")

    # MLModel.predict() reads features through this same ordered column list
    # (defaulting anything missing to 0.0) - reuse it here so a model trained
    # from this script's output has the schema MLModel actually expects,
    # regardless of which optional features (e.g. geo) a given row has.
    feature_columns = MLModel().feature_columns

    # Engineer features
    features_list = []
    labels = []
    skipped = 0

    for i, row in df.iterrows():
        try:
            # engineer_features() requires a Transaction (attribute access, e.g.
            # transaction.timestamp), not a plain dict - build one here, filling in
            # required fields the sample CSVs don't carry with deterministic defaults.
            timestamp = _clean(row.get("timestamp"))
            amount = _clean(row.get("amount"))
            merchant_category = _clean(row.get("merchant_category"))
            merchant_country = _clean(row.get("merchant_country"))
            fraud_label = _clean(row.get("is_fraud"))
            if None in (timestamp, amount, merchant_category, merchant_country, fraud_label):
                raise ValueError("missing a required field (timestamp/amount/merchant_category/merchant_country/is_fraud)")

            # ZIPs are frequently inferred as float by pandas (e.g. 98040.0)
            # when the column has blank cells elsewhere; strip that artifact.
            merchant_zip = _clean(row.get("merchant_zip"))
            if merchant_zip is not None:
                merchant_zip = str(merchant_zip)
                if merchant_zip.endswith(".0"):
                    merchant_zip = merchant_zip[:-2]

            transaction = Transaction(
                transaction_id=str(_clean(row.get("transaction_id"), f"tx_{i}")),
                card_id=str(_clean(row.get("card_id"), f"card_{i}")),
                merchant_id=str(_clean(row.get("merchant_id"), f"merch_{i}")),
                timestamp=str(timestamp),
                amount=float(amount),
                merchant_category=str(merchant_category),
                merchant_name=_clean(row.get("merchant_name")),
                merchant_country=str(merchant_country),
                merchant_zip=merchant_zip,
                customer_id=str(_clean(row.get("customer_id"), f"cust_{i}")),
                is_online=_parse_bool(_clean(row.get("is_online"), False), "is_online"),
                currency=str(_clean(row.get("currency"), "USD")),
                latitude=_clean(row.get("latitude")),
                longitude=_clean(row.get("longitude")),
            )

            # Extract features
            features = engineer_features(transaction)
            ml_features = select_features_for_ml(features)
            label = _parse_bool(fraud_label, "is_fraud")
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping row {i}: {e}")
            skipped += 1
            continue

        features_list.append(ml_features)
        labels.append(label)

    if skipped:
        logger.warning(f"Skipped {skipped} row(s) with missing required fields")

    # Convert to arrays, using a fixed column order/width (0.0 for anything a
    # given row's features are missing, e.g. geo features) so rows stay
    # rectangular regardless of which optional features were computed.
    X = np.array([[f.get(col, 0.0) for col in feature_columns] for f in features_list])
    y = np.array(labels)
    feature_names = feature_columns

    logger.info(f"Prepared {len(X)} samples with {len(feature_names)} features")
    return X, y, feature_names

def train_model(X_train, y_train, output_dir):
    """
    Train an XGBoost model for fraud detection.
    
    Args:
        X_train (array): Training features
        y_train (array): Training labels
        output_dir (str): Directory to save the model
        
    Returns:
        MLModel: Trained model
    """
    logger.info("Training XGBoost model")
    
    # Initialize model
    model = MLModel()
    
    # Train
    model.train(X_train, y_train)
    
    # Save model
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "fraud_model.joblib")
    scaler_path = os.path.join(output_dir, "scaler.joblib")
    model.save_model(model_path, scaler_path)
    
    logger.info(f"Model saved to {model_path}")
    return model

def evaluate_model(model, X_test, y_test):
    """
    Evaluate model performance.
    
    Args:
        model (MLModel): Trained model
        X_test (array): Test features
        y_test (array): Test labels
        
    Returns:
        dict: Evaluation metrics
    """
    logger.info("Evaluating model performance")
    
    # Evaluate
    metrics = model.evaluate(X_test, y_test)
    
    # Print metrics
    logger.info(f"Model evaluation metrics: {metrics}")
    
    # Generate classification report - model.model was fit on scaled features
    # (see MLModel.train()), so predicting on raw X_test here would silently
    # score against the wrong distribution; scale it the same way first.
    X_test_scaled = model.scaler.transform(X_test) if model.scaler is not None else X_test
    y_pred = model.model.predict(X_test_scaled)
    report = classification_report(y_test, y_pred, output_dict=True)
    
    # Generate confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    logger.info(f"Classification report:\n{json.dumps(report, indent=2)}")
    logger.info(f"Confusion matrix:\n{cm}")
    
    return metrics

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage ML models for fraud detection")
    parser.add_argument("--action", choices=["train", "evaluate", "download"], default="train",
                        help="Action to perform")
    parser.add_argument("--data-path", type=str, help="Path to the data file")
    parser.add_argument("--output-dir", type=str, default="./data/models",
                        help="Directory to save models")
    parser.add_argument("--test-size", type=float, default=0.2,
                        help="Fraction of data to use for testing")
    parser.add_argument("--sample-size", type=int, default=None,
                        help="Number of samples to use")
    args = parser.parse_args()
    
    if args.action == "train":
        if not args.data_path:
            logger.error("--data-path is required for training")
            return
        
        # Load and prepare data
        df = load_data(args.data_path, args.sample_size)
        X, y, feature_names = prepare_data(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=args.test_size, random_state=42)
        
        # Train model
        model = train_model(X_train, y_train, args.output_dir)
        
        # Evaluate model
        evaluate_model(model, X_test, y_test)
        
    elif args.action == "evaluate":
        if not args.data_path:
            logger.error("--data-path is required for evaluation")
            return
        
        # Load model
        model_path = os.path.join(args.output_dir, "fraud_model.joblib")
        scaler_path = os.path.join(args.output_dir, "scaler.joblib")
        
        if not os.path.exists(model_path):
            logger.error(f"Model not found at {model_path}")
            return
        
        model = MLModel(model_path, scaler_path)
        
        # Load and prepare data
        df = load_data(args.data_path, args.sample_size)
        X, y, feature_names = prepare_data(df)
        
        # Evaluate model
        evaluate_model(model, X, y)
        
    elif args.action == "download":
        # Download pretrained models
        logger.info("Downloading pretrained models")
        # In a real implementation, this would download from a model repository
        # For now, just create a simple model
        model = MLModel()
        
        # Save model
        os.makedirs(args.output_dir, exist_ok=True)
        model_path = os.path.join(args.output_dir, "fraud_model.joblib")
        scaler_path = os.path.join(args.output_dir, "scaler.joblib")
        model.save_model(model_path, scaler_path)
        
        logger.info(f"Pretrained model saved to {model_path}")

if __name__ == "__main__":
    main()
