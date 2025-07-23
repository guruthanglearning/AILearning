"""
Test script for LLM fallback order: OpenAI API → Online Ollama → Local Ollama → Mock LLM.
This script validates that the system correctly follows the fallback order when issues arise.

Usage:
    python test_llm_fallback_order.py
"""

import os
import sys
import logging
import time
from typing import Dict, Any
import requests
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import the services (needs to happen after sys.path is updated and env vars are loaded)
from app.services.llm_service import LLMService
from app.services.local_llm_service import LocalLLMService
from app.core.config import settings

class FallbackOrderTester:
    """Class for testing the LLM fallback order."""
    
    def __init__(self):
        """Initialize the tester."""
        self.original_openai_key = settings.OPENAI_API_KEY
        self.original_force_local = settings.FORCE_LOCAL_LLM
        self.original_use_local = settings.USE_LOCAL_LLM
        self.original_use_online = settings.USE_ONLINE_OLLAMA

    def restore_settings(self):
        """Restore original settings."""
        os.environ["OPENAI_API_KEY"] = self.original_openai_key
        os.environ["FORCE_LOCAL_LLM"] = str(self.original_force_local)
        os.environ["USE_LOCAL_LLM"] = str(self.original_use_local)
        os.environ["USE_ONLINE_OLLAMA"] = str(self.original_use_online)
        # Reload settings
        from importlib import reload
        from app.core import config
        reload(config)
        logger.info("Original settings restored")

    def check_openai_availability(self) -> bool:
        """Check if OpenAI API is available."""
        if not settings.OPENAI_API_KEY or len(settings.OPENAI_API_KEY) < 20:
            return False
            
        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            # Try a simple model list call
            response = client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI API check failed: {str(e)}")
            return False

    def check_online_ollama_availability(self) -> bool:
        """Check if online Ollama API is available."""
        if not (settings.USE_ONLINE_OLLAMA and settings.ONLINE_OLLAMA_API_URL and settings.ONLINE_OLLAMA_API_KEY):
            return False
            
        try:
            headers = {"Authorization": f"Bearer {settings.ONLINE_OLLAMA_API_KEY}"}
            response = requests.get(
                f"{settings.ONLINE_OLLAMA_API_URL}/status", 
                headers=headers, 
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            try:
                # Try alternative endpoint
                response = requests.get(
                    f"{settings.ONLINE_OLLAMA_API_URL}/models", 
                    headers=headers, 
                    timeout=5
                )
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"Online Ollama API check failed: {str(e)}")
                return False

    def check_local_ollama_availability(self) -> bool:
        """Check if local Ollama is available."""
        try:
            api_url = settings.LOCAL_LLM_API_URL or "http://localhost:11434/api"
            response = requests.get(f"{api_url}/tags", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Local Ollama check failed: {str(e)}")
            return False

    def test_openai_to_online_ollama_fallback(self):
        """Test fallback from OpenAI API to online Ollama API."""
        logger.info("\n===== TESTING OPENAI TO ONLINE OLLAMA FALLBACK =====")
        
        # Configure environment to force the fallback path we want to test
        os.environ["OPENAI_API_KEY"] = "sk-invalid-key-to-force-failure"
        os.environ["FORCE_LOCAL_LLM"] = "False"
        os.environ["USE_LOCAL_LLM"] = "True"
        os.environ["USE_ONLINE_OLLAMA"] = "True"
        
        # Reload settings
        from importlib import reload
        from app.core import config
        reload(config)
        
        # Check if online Ollama is available for this test
        if not self.check_online_ollama_availability():
            logger.error("❌ Test cannot be run: Online Ollama API is not available")
            return False
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Check which LLM service type was selected
        if llm_service.llm_service_type == "local" and hasattr(llm_service.local_llm_service, "prefer_online") and llm_service.local_llm_service.prefer_online:
            logger.info("✅ SUCCESS: System correctly switched to online Ollama API")
            return True
        else:
            logger.error(f"❌ FAILED: System selected {llm_service.llm_service_type} instead of online Ollama API")
            return False

    def test_online_ollama_to_local_ollama_fallback(self):
        """Test fallback from online Ollama API to local Ollama."""
        logger.info("\n===== TESTING ONLINE OLLAMA TO LOCAL OLLAMA FALLBACK =====")
        
        # Configure environment to force the fallback path we want to test
        os.environ["OPENAI_API_KEY"] = "sk-invalid-key-to-force-failure"
        os.environ["FORCE_LOCAL_LLM"] = "False"
        os.environ["USE_LOCAL_LLM"] = "True"
        os.environ["USE_ONLINE_OLLAMA"] = "True"
        
        # Modify online Ollama settings to force failure
        original_online_url = os.environ.get("ONLINE_OLLAMA_API_URL", "")
        original_online_key = os.environ.get("ONLINE_OLLAMA_API_KEY", "")
        os.environ["ONLINE_OLLAMA_API_URL"] = "https://invalid-url-to-force-failure.com"
        os.environ["ONLINE_OLLAMA_API_KEY"] = "invalid-key"
        
        # Reload settings
        from importlib import reload
        from app.core import config
        reload(config)
        
        # Check if local Ollama is available for this test
        if not self.check_local_ollama_availability():
            logger.error("❌ Test cannot be run: Local Ollama is not available")
            # Restore online Ollama settings
            os.environ["ONLINE_OLLAMA_API_URL"] = original_online_url
            os.environ["ONLINE_OLLAMA_API_KEY"] = original_online_key
            return False
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Restore online Ollama settings
        os.environ["ONLINE_OLLAMA_API_URL"] = original_online_url
        os.environ["ONLINE_OLLAMA_API_KEY"] = original_online_key
        
        # Check which LLM service type was selected
        if llm_service.llm_service_type == "local" and (not hasattr(llm_service.local_llm_service, "prefer_online") or not llm_service.local_llm_service.prefer_online):
            logger.info("✅ SUCCESS: System correctly switched to local Ollama")
            return True
        else:
            logger.error(f"❌ FAILED: System selected {llm_service.llm_service_type} instead of local Ollama")
            return False

    def test_all_to_mock_llm_fallback(self):
        """Test fallback to mock LLM when all others fail."""
        logger.info("\n===== TESTING FALLBACK TO MOCK LLM =====")
        
        # Configure environment to force the fallback path we want to test
        os.environ["OPENAI_API_KEY"] = "sk-invalid-key-to-force-failure"
        os.environ["FORCE_LOCAL_LLM"] = "False"
        os.environ["USE_LOCAL_LLM"] = "False"  # Disable local LLM
        os.environ["USE_ONLINE_OLLAMA"] = "False"  # Disable online Ollama
        
        # Reload settings
        from importlib import reload
        from app.core import config
        reload(config)
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Check which LLM service type was selected
        if llm_service.llm_service_type in ["enhanced_mock", "basic_mock"]:
            logger.info("✅ SUCCESS: System correctly switched to mock LLM")
            return True
        else:
            logger.error(f"❌ FAILED: System selected {llm_service.llm_service_type} instead of mock LLM")
            return False

    def test_direct_openai_usage(self):
        """Test direct OpenAI API usage when available."""
        logger.info("\n===== TESTING DIRECT OPENAI API USAGE =====")
        
        # Skip this test if OpenAI API is not available
        if not self.check_openai_availability():
            logger.warning("⚠️ Skipping test: No valid OpenAI API key available")
            return None
            
        # Configure environment to use OpenAI directly
        os.environ["FORCE_LOCAL_LLM"] = "False"
        
        # Reload settings
        from importlib import reload
        from app.core import config
        reload(config)
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Check which LLM service type was selected
        if llm_service.llm_service_type == "openai":
            logger.info("✅ SUCCESS: System correctly uses OpenAI API directly")
            return True
        else:
            logger.error(f"❌ FAILED: System selected {llm_service.llm_service_type} instead of OpenAI")
            return False

def main():
    """Run the LLM fallback order tests."""
    print("\n============================================")
    print("    LLM FALLBACK ORDER TESTING SCRIPT")
    print("============================================\n")
    
    tester = FallbackOrderTester()
    
    try:
        # Test all fallback scenarios
        results = {
            "openai_to_online": tester.test_openai_to_online_ollama_fallback(),
            "online_to_local": tester.test_online_ollama_to_local_ollama_fallback(),
            "all_to_mock": tester.test_all_to_mock_llm_fallback(),
            "direct_openai": tester.test_direct_openai_usage()
        }
        
        # Restore original settings
        tester.restore_settings()
        
        # Print summary
        print("\n============================================")
        print("                SUMMARY")
        print("============================================")
        
        success_count = sum(1 for result in results.values() if result is True)
        fail_count = sum(1 for result in results.values() if result is False)
        skip_count = sum(1 for result in results.values() if result is None)
        
        print(f"Tests passed: {success_count}")
        print(f"Tests failed: {fail_count}")
        print(f"Tests skipped: {skip_count}")
        print("============================================\n")
        
        for test, result in results.items():
            status = "✅ PASSED" if result is True else "❌ FAILED" if result is False else "⚠️ SKIPPED"
            print(f"{test}: {status}")
            
        if fail_count > 0:
            print("\nSome tests failed. Please check the logs above for details.")
            return 1
        else:
            print("\nAll tests passed or were skipped. The LLM fallback order is working as expected.")
            return 0
            
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        # Ensure original settings are restored even if tests fail
        tester.restore_settings()
        return 1

if __name__ == "__main__":
    sys.exit(main())
