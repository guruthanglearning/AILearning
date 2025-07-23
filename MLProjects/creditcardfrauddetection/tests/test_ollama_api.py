"""
Test script for validating Ollama API integration (both local and online).

This script tests the connectivity to both local and online Ollama APIs
and provides diagnostic information on their availability and response.

Usage:
    python test_ollama_api.py

Environment variables:
    All variables are read from .env file
"""

import os
import sys
import logging
import time
import requests
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get configuration from environment
LOCAL_OLLAMA_API_URL = os.getenv("LOCAL_LLM_API_URL", "http://localhost:11434/api")
USE_ONLINE_OLLAMA = os.getenv("USE_ONLINE_OLLAMA", "False").lower() in ("true", "1", "t")
ONLINE_OLLAMA_API_URL = os.getenv("ONLINE_OLLAMA_API_URL", "")
ONLINE_OLLAMA_API_KEY = os.getenv("ONLINE_OLLAMA_API_KEY", "")
LOCAL_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3")

def mask_api_key(api_key):
    """Return a masked version of the API key for logging/display purposes."""
    if not api_key or len(api_key) < 8:
        return "N/A"
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

def check_local_ollama():
    """Test connection to local Ollama API."""
    logger.info("Testing local Ollama API connection...")
    
    try:
        # Try to list models to check if Ollama is running
        start_time = time.time()
        response = requests.get(f"{LOCAL_OLLAMA_API_URL}/tags", timeout=5)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            logger.info(f"✓ Local Ollama API is available ({elapsed:.2f}s)")
            logger.info(f"✓ Available models: {', '.join(model_names) if model_names else 'None'}")
            
            # Check if our configured model is available
            if LOCAL_MODEL not in str(models):
                logger.warning(f"⚠ Configured model '{LOCAL_MODEL}' not found in available models")
            else:
                logger.info(f"✓ Configured model '{LOCAL_MODEL}' is available")
            
            return True
        else:
            logger.error(f"✗ Local Ollama API returned status code: {response.status_code}")
            logger.error(f"✗ Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"✗ Error checking local LLM availability: {str(e)}")
        return False

def check_online_ollama():
    """Test connection to online Ollama API."""
    if not USE_ONLINE_OLLAMA:
        logger.info("Online Ollama API is disabled in configuration")
        return False
        
    if not ONLINE_OLLAMA_API_URL:
        logger.error("✗ Online Ollama API URL is not configured")
        return False
        
    if not ONLINE_OLLAMA_API_KEY:
        logger.error("✗ Online Ollama API key is not configured")
        return False
    
    logger.info(f"Testing online Ollama API connection to {ONLINE_OLLAMA_API_URL}...")
    logger.info(f"Using API key: {mask_api_key(ONLINE_OLLAMA_API_KEY)}")
    
    headers = {
        "Authorization": f"Bearer {ONLINE_OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try multiple possible endpoints
    endpoints_to_try = [
        "/status",
        "/health",
        "/models",
        "/v1/models"
    ]
    
    for endpoint in endpoints_to_try:
        try:
            url = f"{ONLINE_OLLAMA_API_URL}{endpoint}"
            logger.info(f"Trying endpoint: {url}")
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"✓ Online Ollama API is available via {endpoint} ({elapsed:.2f}s)")
                try:
                    resp_json = response.json()
                    logger.info(f"✓ Response: {json.dumps(resp_json, indent=2)[:500]}...")
                except:
                    logger.info(f"✓ Response: {response.text[:500]}...")
                return True
            else:
                logger.warning(f"⚠ Endpoint {endpoint} returned status {response.status_code}: {response.text[:200]}...")
        except Exception as e:
            logger.warning(f"⚠ Error with endpoint {endpoint}: {str(e)}")
    
    logger.error("✗ All online Ollama API endpoints failed")
    return False

def test_inference(is_local=True):
    """Test inference with a simple prompt."""
    api_url = LOCAL_OLLAMA_API_URL if is_local else ONLINE_OLLAMA_API_URL
    headers = {}
    
    if not is_local:
        if not USE_ONLINE_OLLAMA or not ONLINE_OLLAMA_API_KEY:
            logger.info("Skipping online inference test (not configured)")
            return
        headers = {"Authorization": f"Bearer {ONLINE_OLLAMA_API_KEY}"}
    
    model = LOCAL_MODEL
    prompt = "What is the capital of France? Answer in one word."
    
    logger.info(f"Testing {'local' if is_local else 'online'} inference with prompt: '{prompt}'")
    
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.01,
                "num_predict": 50
            }
        }
        
        endpoint = f"{api_url}/generate"
        start_time = time.time()
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            logger.info(f"✓ {'Local' if is_local else 'Online'} inference successful ({elapsed:.2f}s)")
            logger.info(f"✓ Response: {response_text}")
            return True
        else:
            logger.error(f"✗ {'Local' if is_local else 'Online'} inference failed with status {response.status_code}")
            logger.error(f"✗ Error: {response.text[:500]}")
            return False
    except Exception as e:
        logger.error(f"✗ Error during {'local' if is_local else 'online'} inference: {str(e)}")
        return False

def main():
    """Run tests for both local and online Ollama APIs."""
    logger.info("=" * 50)
    logger.info("OLLAMA API TESTING SCRIPT")
    logger.info("=" * 50)
    
    # Test local Ollama
    local_available = check_local_ollama()
    
    logger.info("\n" + "=" * 50)
    
    # Test online Ollama if configured
    online_available = check_online_ollama() if USE_ONLINE_OLLAMA else False
    
    logger.info("\n" + "=" * 50)
    
    # Test inference
    if local_available:
        test_inference(is_local=True)
    
    logger.info("\n" + "=" * 50)
    
    if online_available:
        test_inference(is_local=False)
    
    logger.info("\n" + "=" * 50)
    logger.info("SUMMARY:")
    
    if local_available:
        logger.info("✓ Local Ollama API is available")
    else:
        logger.info("✗ Local Ollama API is NOT available")
        
    if USE_ONLINE_OLLAMA:
        if online_available:
            logger.info("✓ Online Ollama API is available")
        else:
            logger.info("✗ Online Ollama API is NOT available")
    else:
        logger.info("- Online Ollama API is disabled in configuration")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
