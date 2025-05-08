"""
Data processing utilities for fraud detection system.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_json_data(file_path: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Loaded JSON data
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded data from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {str(e)}")
        raise

def save_json_data(data: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to the JSON file
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Successfully saved data to {file_path}")
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {str(e)}")
        raise

def convert_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of dictionaries to a pandas DataFrame.
    
    Args:
        data: List of dictionaries
        
    Returns:
        Pandas DataFrame
    """
    try:
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        logger.error(f"Error converting data to DataFrame: {str(e)}")
        raise

def normalize_features(features: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize features to have zero mean and unit variance.
    
    Args:
        features: Features to normalize
        
    Returns:
        Normalized features
    """
    try:
        # Select only numeric columns
        numeric_features = features.select_dtypes(include=[np.number])
        
        # Calculate mean and standard deviation
        mean = numeric_features.mean()
        std = numeric_features.std()
        
        # Normalize
        normalized_features = (numeric_features - mean) / std
        
        # Replace original numeric columns with normalized ones
        for col in numeric_features.columns:
            features[col] = normalized_features[col]
        
        return features
    except Exception as e:
        logger.error(f"Error normalizing features: {str(e)}")
        raise

def encode_categorical_features(features: pd.DataFrame, categorical_columns: List[str]) -> pd.DataFrame:
    """
    Encode categorical features using one-hot encoding.
    
    Args:
        features: Features to encode
        categorical_columns: List of categorical column names
        
    Returns:
        DataFrame with encoded features
    """
    try:
        # Ensure all specified columns exist
        existing_cols = [col for col in categorical_columns if col in features.columns]
        
        if not existing_cols:
            logger.warning("No categorical columns found in features")
            return features
        
        # One-hot encode
        encoded_features = pd.get_dummies(features, columns=existing_cols, drop_first=True)
        
        return encoded_features
    except Exception as e:
        logger.error(f"Error encoding categorical features: {str(e)}")
        raise

def filter_transactions_by_date(transactions: List[Dict[str, Any]], start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Filter transactions by date range.
    
    Args:
        transactions: List of transaction dictionaries
        start_date: Start date in ISO format
        end_date: End date in ISO format
        
    Returns:
        Filtered transactions
    """
    try:
        # Convert dates to datetime objects
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Filter transactions
        filtered_transactions = []
        for txn in transactions:
            if 'timestamp' in txn:
                txn_dt = datetime.fromisoformat(txn['timestamp'].replace('Z', '+00:00'))
                if start_dt <= txn_dt <= end_dt:
                    filtered_transactions.append(txn)
        
        logger.info(f"Filtered {len(filtered_transactions)} transactions between {start_date} and {end_date}")
        return filtered_transactions
    except Exception as e:
        logger.error(f"Error filtering transactions by date: {str(e)}")
        raise

def aggregate_transactions_by_customer(transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate transactions by customer.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Dictionary of customer aggregates
    """
    try:
        # Group transactions by customer
        customer_txns = {}
        for txn in transactions:
            if 'customer_id' in txn:
                customer_id = txn['customer_id']
                if customer_id not in customer_txns:
                    customer_txns[customer_id] = []
                customer_txns[customer_id].append(txn)
        
        # Calculate aggregates for each customer
        customer_aggregates = {}
        for customer_id, txns in customer_txns.items():
            # Convert to DataFrame for easier aggregation
            df = pd.DataFrame(txns)
            
            # Calculate aggregates
            aggregates = {
                'txn_count': len(txns),
                'total_amount': df['amount'].sum() if 'amount' in df else 0,
                'avg_amount': df['amount'].mean() if 'amount' in df else 0,
                'max_amount': df['amount'].max() if 'amount' in df else 0,
                'min_amount': df['amount'].min() if 'amount' in df else 0,
                'std_amount': df['amount'].std() if 'amount' in df else 0,
                'unique_merchants': df['merchant_id'].nunique() if 'merchant_id' in df else 0,
            }
            
            customer_aggregates[customer_id] = aggregates
        
        return customer_aggregates
    except Exception as e:
        logger.error(f"Error aggregating transactions by customer: {str(e)}")
        raise