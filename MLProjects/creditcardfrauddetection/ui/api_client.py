"""
Utility functions for the Streamlit UI to interact with the API.
"""

import requests
import json
import streamlit as st

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
            transaction_id: Optional transaction ID to get details for a specific transaction
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        if transaction_id:
            url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        else:
            url = f"{self.base_url}/api/v1/transactions"
        
        return self._make_request("GET", url)    
    
    def _make_request(self, method, url, data=None):
        """
        Make an HTTP request to the API.
        
        Args:
            method: The HTTP method (GET, POST, etc.)
            url: The URL to make the request to
            data: Optional data to send with the request
            
        Returns:
            The API response as a dict, or None if there was an error
        """
        if st.session_state.get('debug_mode', False):
            st.sidebar.write(f"API Request: {method} {url}")
            if data:
                st.sidebar.write("Request Data:")
                st.sidebar.json(data)
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10) 
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            else:
                st.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Process response
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if st.session_state.get('debug_mode', False):
                        st.sidebar.write("Response Data:")
                        st.sidebar.json(response_data)
                    return response_data
                except ValueError:
                    st.error("API returned invalid JSON")
                    return None
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error(f"Connection error: Could not connect to {url}. Make sure the API server is running.")
            return None
        except requests.exceptions.Timeout:
            st.error(f"Request timed out: {url} did not respond within timeout period.")
            return None
        except Exception as e:
            st.error(f"Error calling API: {str(e)}")
            return None

# Function to get or create a session-specific API client
def get_api_client():
    """
    Get or create a session-specific API client.
    
    Returns:
        A FraudDetectionAPI instance
    """
    if 'api_client' not in st.session_state:
        # Get API URL and key from session state or use defaults
        api_url = st.session_state.get('api_url', 'http://localhost:8000')
        api_key = st.session_state.get('api_key', 'development_api_key_for_testing')
        
        # Create the API client
        st.session_state.api_client = FraudDetectionAPI(api_url, api_key)
        
        # For debugging
        if st.session_state.get('debug_mode', False):
            st.sidebar.write(f"API Client created with URL: {api_url}")
    
    return st.session_state.api_client

# Function to update API configuration
def update_api_config(api_url, api_key):
    """
    Update the API configuration.
    
    Args:
        api_url: The base URL of the API
        api_key: The API key for authentication
    """
    # Update session state
    st.session_state['api_url'] = api_url
    st.session_state['api_key'] = api_key
    
    # Create a new API client
    st.session_state.api_client = FraudDetectionAPI(api_url, api_key)
    
    # Return the new client
    return st.session_state.api_client
