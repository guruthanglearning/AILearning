"""
Configure Online Ollama API settings interactively.
This script helps you set up your online Ollama API configuration
in the .env file, including testing the connection.

Usage:
    python configure_ollama_api.py
"""

import os
import sys
import logging
import requests
import json
from getpass import getpass
from dotenv import load_dotenv, set_key, find_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Common Ollama API providers
OLLAMA_PROVIDERS = {
    "1": {
        "name": "Ollama Cloud",
        "url": "https://api.ollama.cloud/v1",
        "description": "Official hosted Ollama service"
    },
    "2": {
        "name": "RunPod",
        "url": "https://api.runpod.ai/v2/{your-pod-id}/ollama",
        "description": "GPU cloud provider with Ollama templates"
    },
    "3": {
        "name": "Replicate",
        "url": "https://api.replicate.com/v1/ollama",
        "description": "Supports Ollama-compatible endpoints for various models"
    },
    "4": {
        "name": "Custom",
        "url": "",
        "description": "Enter your own custom Ollama API provider"
    }
}

def mask_api_key(api_key):
    """Return a masked version of the API key for logging/display purposes."""
    if not api_key or len(api_key) < 8:
        return "N/A"
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

def test_ollama_api_connection(api_url, api_key):
    """Test connection to an Ollama API provider."""
    if not api_url:
        logger.error("API URL is required")
        return False
        
    if not api_key:
        logger.error("API key is required")
        return False
    
    logger.info(f"Testing connection to {api_url}...")
    logger.info(f"Using API key: {mask_api_key(api_key)}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
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
            url = f"{api_url.rstrip('/')}{endpoint}"
            logger.info(f"Trying endpoint: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✓ Connection successful via {endpoint}")
                try:
                    resp_json = response.json()
                    logger.info(f"✓ Response: {json.dumps(resp_json)[:200]}...")
                except:
                    logger.info(f"✓ Response: {response.text[:200]}...")
                return True
            else:
                logger.warning(f"⚠ Endpoint {endpoint} returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠ Error with endpoint {endpoint}: {str(e)}")
    
    # If we've tried all endpoints with no success, try a simple generate request
    try:
        generate_url = f"{api_url.rstrip('/')}/generate"
        logger.info(f"Trying generate endpoint: {generate_url}")
        
        payload = {
            "model": "llama3",  # Most providers support this model
            "prompt": "Hello",
            "stream": False
        }
        
        response = requests.post(
            generate_url, 
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            logger.info("✓ Generate endpoint is working")
            return True
        else:
            logger.warning(f"⚠ Generate endpoint returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠ Error with generate endpoint: {str(e)}")
    
    logger.error("✗ All connection attempts failed")
    return False

def update_env_file(use_online_ollama, api_url, api_key):
    """Update the .env file with the Ollama API settings."""
    try:
        # Find the .env file
        dotenv_path = find_dotenv()
        if not dotenv_path:
            logger.error("No .env file found")
            dotenv_path = os.path.join(os.getcwd(), '.env')
            logger.info(f"Creating new .env file at {dotenv_path}")
            with open(dotenv_path, 'w') as f:
                f.write("# Ollama API Settings\n")
        
        # Update the settings
        set_key(dotenv_path, "USE_ONLINE_OLLAMA", str(use_online_ollama))
        set_key(dotenv_path, "ONLINE_OLLAMA_API_URL", api_url)
        set_key(dotenv_path, "ONLINE_OLLAMA_API_KEY", api_key)
        
        logger.info(f"✓ Updated settings in {dotenv_path}")
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        return False

def main():
    """Run the configuration wizard."""
    print("\n============================================")
    print("    ONLINE OLLAMA API CONFIGURATION WIZARD")
    print("============================================\n")
    
    # Load current settings
    load_dotenv()
    current_use_online = os.getenv("USE_ONLINE_OLLAMA", "False").lower() in ("true", "1", "t")
    current_api_url = os.getenv("ONLINE_OLLAMA_API_URL", "")
    current_api_key = os.getenv("ONLINE_OLLAMA_API_KEY", "")
    
    print("Current settings:")
    print(f"  USE_ONLINE_OLLAMA: {current_use_online}")
    print(f"  ONLINE_OLLAMA_API_URL: {current_api_url}")
    print(f"  ONLINE_OLLAMA_API_KEY: {mask_api_key(current_api_key)}")
    print("\n")
    
    # Ask if user wants to enable online Ollama
    enable_online = input("Enable online Ollama API? (y/n) [y]: ").lower() or "y"
    use_online_ollama = enable_online in ("y", "yes", "true", "1")
    
    if not use_online_ollama:
        print("\nOnline Ollama API will be disabled.")
        update_env_file(False, "", "")
        return
    
    # Select a provider
    print("\nSelect an Ollama API provider:")
    for key, provider in OLLAMA_PROVIDERS.items():
        print(f"  {key}: {provider['name']} - {provider['description']}")
    
    provider_choice = input("\nEnter choice (1-4) [1]: ") or "1"
    selected_provider = OLLAMA_PROVIDERS.get(provider_choice, OLLAMA_PROVIDERS["4"])
    
    # Get API URL
    default_url = selected_provider["url"] if selected_provider["name"] != "Custom" else current_api_url
    api_url = input(f"API URL [{default_url}]: ") or default_url
    
    # For RunPod, guide the user to replace the placeholder
    if "{your-pod-id}" in api_url:
        pod_id = input("Enter your RunPod ID: ")
        api_url = api_url.replace("{your-pod-id}", pod_id)
    
    # Get API key
    print("\nEnter your API key (input will be hidden):")
    api_key = getpass("API Key: ") or current_api_key
    
    # Test the connection
    print("\nTesting connection to the Ollama API provider...")
    connection_successful = test_ollama_api_connection(api_url, api_key)
    
    if connection_successful:
        print("\n✓ Connection successful!")
        
        # Save the settings
        save_settings = input("Save these settings to .env? (y/n) [y]: ").lower() or "y"
        if save_settings in ("y", "yes", "true", "1"):
            update_env_file(True, api_url, api_key)
            print("\n✓ Settings saved successfully!")
    else:
        print("\n✗ Connection failed.")
        print("Please check your API URL and key and try again.")
        
        # Still offer to save
        save_anyway = input("Save these settings anyway? (y/n) [n]: ").lower() or "n"
        if save_anyway in ("y", "yes", "true", "1"):
            update_env_file(True, api_url, api_key)
            print("\nSettings saved, but connection failed. You may need to check with your provider.")
    
    print("\n============================================")
    print("Configuration complete!")
    print("============================================")

if __name__ == "__main__":
    main()
