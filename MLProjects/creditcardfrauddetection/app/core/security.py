"""
Security utilities for the fraud detection system.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If the token is invalid
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing token"
        )

def get_api_key_hash(api_key: str) -> str:
    """
    Get a hash of the API key for secure storage.
    
    Args:
        api_key: API key to hash
        
    Returns:
        Hashed API key
    """
    # In a production system, this would use a secure hashing algorithm
    # For demonstration purposes, we're just returning the key
    # TODO: Implement proper hashing
    return api_key

def verify_api_key(api_key: str) -> bool:
    """
    Verify if an API key is valid.
    
    Args:
        api_key: API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    # In a production system, this would check against a database
    # For demonstration purposes, we're just checking against the settings
    return api_key == settings.SECRET_KEY