"""
Streamlit UI for Credit Card Fraud Detection System.
This is the main application file for the Streamlit UI.
"""

import os
import json
import time
import datetime
import pandas as pd
import numpy as np
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Import page functions
from pages.fraud_patterns import show_fraud_patterns
from pages.system_health import display_system_health
from pages.dashboard import show_dashboard
from pages.transaction_analysis import show_transaction_analysis
from api_client import display_api_connection_status

# Load environment variables - UI-SPECIFIC ONLY
# CRITICAL: Load ONLY from ui/ directory, never from parent directory
# This prevents Docker configs from being loaded in local deployment
import sys
ui_dir = os.path.dirname(os.path.abspath(__file__))

# FORCE: Clear any existing API_URL environment variable first
if 'API_URL' in os.environ:
    del os.environ['API_URL']
    print(f"[UI CONFIG] Cleared existing API_URL env var", file=sys.stderr)

# Load ui/.env.local FIRST (highest priority)
ui_env_local = os.path.join(ui_dir, '.env.local')
if os.path.exists(ui_env_local):
    load_dotenv(dotenv_path=ui_env_local, override=True)
    print(f"[UI CONFIG] Loaded: {ui_env_local}", file=sys.stderr)
else:
    # Fallback to ui/.env
    ui_env = os.path.join(ui_dir, '.env')
    if os.path.exists(ui_env):
        load_dotenv(dotenv_path=ui_env, override=True)
        print(f"[UI CONFIG] Loaded: {ui_env}", file=sys.stderr)

# Constants - Get API URL from environment
# FORCE LOCAL API if not explicitly set to Docker
API_URL = os.getenv("API_URL", "http://localhost:8000")
if "fraud-detection-api" in API_URL:
    print(f"[UI CONFIG] WARNING: Docker API URL detected, forcing local", file=sys.stderr)
    API_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "development_api_key_for_testing")

# Debug output - verify configuration
print(f"[UI CONFIG] API_URL = {API_URL}", file=sys.stderr)
print(f"[UI CONFIG] Working from: {ui_dir}", file=sys.stderr)

# Set page configuration
st.set_page_config(
    page_title="Credit Card Fraud Detection System",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Credit Card Fraud Detection System"
    }
)

# Hide Streamlit's default navigation
hide_streamlit_nav = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
div[data-testid="stSidebarNav"] {display: none;}
</style>
"""
st.markdown(hide_streamlit_nav, unsafe_allow_html=True)

# Custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .card {
        border-radius: 5px;
        background-color: #f9f9f9;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    .fraud-detected {
        color: #D32F2F;
        font-weight: bold;
    }
    .legitimate {
        color: #388E3C;
        font-weight: bold;
    }
    .review-needed {
        color: #FFA000;
        font-weight: bold;
    }
    .info-box {
        background-color: #E3F2FD;
        border-left: 5px solid #1E88E5;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def call_api(endpoint, data, method="POST"):
    """Call the fraud detection API."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return None


def main():
    """Main function to build the Streamlit UI."""
    global API_URL, API_KEY
    st.markdown("<h1 class='main-header'>Credit Card Fraud Detection System</h1>", unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["Dashboard", "Transaction Analysis", "Fraud Patterns", "System Health"]
    )
    
    # Sidebar API configuration
    st.sidebar.title("API Configuration")
    api_url = st.sidebar.text_input("API URL", value=API_URL)
    api_key = st.sidebar.text_input("API Key", value=API_KEY, type="password")
    
    # Debug mode toggle
    debug_mode = st.sidebar.checkbox("Debug Mode", value=st.session_state.get('debug_mode', False))
    st.session_state.debug_mode = debug_mode
    
    if api_url != API_URL or api_key != API_KEY:
        API_URL = api_url
        API_KEY = api_key
        st.sidebar.success("API configuration updated!")
    
    # Display API connection status once in sidebar
    display_api_connection_status()
    
    # Display the selected page
    if page == "Dashboard":
        show_dashboard()
        
    elif page == "Transaction Analysis":
        show_transaction_analysis()
    
    elif page == "Fraud Patterns":
        st.markdown("<h2 class='sub-header'>Fraud Pattern Management</h2>", unsafe_allow_html=True)
        
        # Use the show_fraud_patterns function from the imported module
        show_fraud_patterns()
    
    elif page == "System Health":
        st.markdown("<h2 class='sub-header'>System Health & Monitoring</h2>", unsafe_allow_html=True)
        
        # Use the imported display_system_health function
        display_system_health()

if __name__ == "__main__":
    main()
