"""
Utility functions for the Streamlit UI to interact with the API.
"""

import requests
import json
import streamlit as st
import traceback

class FraudDetectionAPI:
    """Class to interact with the Fraud Detection API."""
    
    def __init__(self, base_url, api_key):
        """
        Initialize the API client.
        
        Args:
            base_url: The base URL of the API
            api_key: The API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
    
    def detect_fraud(self, transaction_data):
        """
        Send a transaction to the fraud detection endpoint.
        
        Args:
            transaction_data: The transaction data to analyze
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/detect-fraud"
        return self._make_request("POST", url, transaction_data)
    
    def submit_feedback(self, feedback_data):
        """
        Submit feedback on a transaction.
        
        Args:
            feedback_data: The feedback data to submit
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/feedback"
        return self._make_request("POST", url, feedback_data)
    
    def get_fraud_patterns(self):
        """
        Get all fraud patterns.
        
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/fraud-patterns"
        return self._make_request("GET", url)
    
    def add_fraud_pattern(self, pattern_data):
        """
        Add a new fraud pattern.
        
        Args:
            pattern_data: The pattern data to add
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/fraud-patterns"
        return self._make_request("POST", url, pattern_data)
    
    def update_fraud_pattern(self, pattern_id, pattern_data):
        """
        Update an existing fraud pattern.
        
        Args:
            pattern_id: ID of the pattern to update
            pattern_data: Updated pattern data
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/fraud-patterns/{pattern_id}"
        return self._make_request("PUT", url, pattern_data)
    
    def delete_fraud_pattern(self, pattern_id):
        """
        Delete an existing fraud pattern.
        
        Args:
            pattern_id: ID of the pattern to delete
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/fraud-patterns/{pattern_id}"
        return self._make_request("DELETE", url)
    
    def get_metrics(self):
        """
        Get system metrics.
        
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/metrics"
        return self._make_request("GET", url)
    
    def get_health(self):
        """
        Get system health status.
        
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/health"
        return self._make_request("GET", url)
    
    def get_transaction_history(self, transaction_id=None):
        """
        Get transaction history.
        
        Args:
            transaction_id: Optional transaction ID to filter by
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        if transaction_id:
            url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        else:
            url = f"{self.base_url}/api/v1/transactions"
        return self._make_request("GET", url)
    
    def get_llm_status(self):
        """
        Get LLM service status.
        
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/llm/status"
        return self._make_request("GET", url)
    
    def switch_llm_model(self, model_type):
        """
        Switch LLM model.
        
        Args:
            model_type: The model type to switch to
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        url = f"{self.base_url}/api/v1/llm/switch"
        return self._make_request("POST", url, {"model_type": model_type})
    
    def _make_request(self, method, url, data=None):
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: URL to make the request to
            data: Optional data to send with the request
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                st.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API request failed with status code {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API server. Please ensure the server is running.")
            return None
        except requests.exceptions.Timeout:
            st.error("API request timed out. Please try again.")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return None
        except json.JSONDecodeError:
            st.error("Invalid JSON response from API.")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            st.error(f"Traceback: {traceback.format_exc()}")
            return None

@st.cache_resource
def get_api_client():
    """
    Get a cached API client instance.
    
    Returns:
        FraudDetectionAPI instance
    """
    try:
        # Check if we're running in Streamlit
        if hasattr(st, 'session_state'):
            # Try to get config from Streamlit secrets first
            if hasattr(st, 'secrets') and 'api' in st.secrets:
                base_url = st.secrets.api.get("base_url", "http://localhost:8000")
                api_key = st.secrets.api.get("api_key", "development_api_key_for_testing")
            else:
                # Fall back to default values
                base_url = "http://localhost:8000"
                api_key = "development_api_key_for_testing"
        else:
            # Not in Streamlit context, use defaults
            base_url = "http://localhost:8000"
            api_key = "development_api_key_for_testing"
        
        # Display connection info
        st.sidebar.markdown("### API Connection")
        st.sidebar.markdown(f"**URL:** {base_url}")
        st.sidebar.markdown(f"**Status:** Testing connection...")
        
        # Create and test the API client
        api_client = FraudDetectionAPI(base_url, api_key)
        
        # Test the connection
        health_check = api_client.get_health()
        if health_check:
            st.sidebar.markdown(f"**Status:** ✅ Connected")
            return api_client
        else:
            st.sidebar.markdown(f"**Status:** ❌ Connection failed")
            st.error("API CLIENT ERROR: Connection error: Could not connect to http://localhost:8000/health. Make sure the API server is running.")
            return api_client  # Return anyway so the UI can still load
            
    except Exception as e:
        st.error(f"Error creating API client: {str(e)}")
        # Return a basic client anyway
        return FraudDetectionAPI("http://localhost:8000", "development_api_key_for_testing")