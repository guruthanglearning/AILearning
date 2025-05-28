"""
Transaction Analysis page for the Credit Card Fraud Detection System.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
import time
import json
from api_client import get_api_client

def generate_sample_transaction(is_fraudulent=False):
    """Generate a sample transaction for demonstration."""
    # Common transaction properties
    transaction = {
        "transaction_id": f"tx_{int(time.time())}",
        "card_id": f"card_{np.random.randint(1000000, 9999999)}",
        "customer_id": f"cust_{np.random.randint(10000, 99999)}",
        "timestamp": datetime.datetime.now().isoformat(),
        "currency": "USD",
    }
    
    if is_fraudulent:
        # Fraudulent transaction patterns
        merchant_categories = ["Electronics", "Digital Goods", "Jewelry", "Travel"]
        transaction.update({
            "merchant_id": f"merch_{np.random.randint(10000, 99999)}",
            "merchant_name": np.random.choice(["TechGiant", "LuxuryItems", "QuickBuy", "DigitalMart"]),
            "merchant_category": np.random.choice(merchant_categories),
            "merchant_country": np.random.choice(["RU", "NG", "CN", "VE"]),  # Unusual countries
            "merchant_zip": f"{np.random.randint(10000, 99999)}",
            "amount": np.random.uniform(800, 5000),  # Higher amount
            "is_online": True,
            "device_id": f"dev_{np.random.randint(1000000, 9999999)}",  # New device
            "ip_address": f"192.168.{np.random.randint(0, 255)}.{np.random.randint(0, 255)}",
            "latitude": np.random.uniform(30, 60),
            "longitude": np.random.uniform(-120, 30),
        })
    else:
        # Legitimate transaction patterns
        merchant_categories = ["Groceries", "Restaurant", "Retail", "Gas Station"]
        transaction.update({
            "merchant_id": f"merch_{np.random.randint(10000, 99999)}",
            "merchant_name": np.random.choice(["LocalGrocery", "CityDiner", "HomeShopping", "GasStop"]),
            "merchant_category": np.random.choice(merchant_categories),
            "merchant_country": "US",  # Home country
            "merchant_zip": f"{np.random.randint(10000, 99999)}",
            "amount": np.random.uniform(10, 200),  # Lower amount
            "is_online": np.random.choice([True, False]),
            "device_id": "dev_regular123",  # Regular device
            "ip_address": f"192.168.1.{np.random.randint(1, 100)}",
            "latitude": 40.7128,  # New York coordinates
            "longitude": -74.0060,
        })
    
    return transaction

def display_transaction_result(result):
    """Display the result of a fraud detection transaction."""
    if not result:
        return
    
    st.markdown("## Transaction Analysis Results")
    
    # Overall result
    result_status = ""
    if result["is_fraud"]:
        result_status = "<span class='fraud-detected'>FRAUD DETECTED</span>"
    elif result["requires_review"]:
        result_status = "<span class='review-needed'>REVIEW NEEDED</span>"
    else:
        result_status = "<span class='legitimate'>LEGITIMATE</span>"
    
    st.markdown(f"### Status: {result_status}", unsafe_allow_html=True)
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Transaction Details")
        st.markdown(f"**Transaction ID:** {result['transaction_id']}")
        st.markdown(f"**Amount:** ${result.get('amount', 'N/A')}")
        st.markdown(f"**Merchant:** {result.get('merchant_name', 'N/A')}")
        st.markdown(f"**Category:** {result.get('merchant_category', 'N/A')}")
        st.markdown(f"**Time:** {result.get('timestamp', 'N/A')}")
    
    with col2:
        st.markdown("#### Analysis Details")
        st.markdown(f"**Confidence Score:** {result['confidence_score']*100:.2f}%")
        st.markdown(f"**Processing Time:** {result['processing_time_ms']} ms")
        st.markdown(f"**Manual Review:** {'Yes' if result['requires_review'] else 'No'}")
    
    # Decision reasoning
    st.markdown("#### Decision Reasoning")
    st.markdown(f"{result['decision_reason']}")
    
    # Visualization of confidence score
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = result['confidence_score']*100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Fraud Confidence Score"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkred" if result['is_fraud'] else "darkgreen"},
            'steps': [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 70], 'color': "lightyellow"},
                {'range': [70, 100], 'color': "salmon"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

def display_feedback_form(transaction_id):
    """Display a form for submitting feedback on fraud detection results."""
    st.markdown("## Analyst Feedback")
    st.markdown("Submit your assessment of this transaction for model improvement.")
    
    # Get API client
    api_client = get_api_client()
    
    with st.form(key="feedback_form"):
        actual_fraud = st.radio(
            "Is this transaction actually fraudulent?",
            options=["Yes", "No", "Unsure"],
            horizontal=True
        )
        
        analyst_notes = st.text_area(
            "Notes (please provide details about the transaction):",
            height=100
        )
        
        submit_button = st.form_submit_button(label="Submit Feedback")
        
        if submit_button:
            if analyst_notes:
                feedback_data = {
                    "transaction_id": transaction_id,
                    "actual_fraud": actual_fraud == "Yes",
                    "analyst_notes": analyst_notes
                }
                
                response = api_client.submit_feedback(feedback_data)
                if response:
                    st.success("Feedback submitted successfully! Thank you for helping improve the model.")
            else:
                st.warning("Please provide notes for your assessment.")

def real_time_analysis():
    """Show the real-time transaction analysis tab."""
    st.markdown("### Analyze New Transaction")
    
    # Transaction generation options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Quick Test")
        test_type = st.radio(
            "Select transaction type:",
            ["Generate Legitimate Transaction", "Generate Suspicious Transaction", "Custom Transaction"]
        )
    
    # Initialize transaction data
    transaction_data = {}
    
    if test_type == "Generate Legitimate Transaction":
        transaction_data = generate_sample_transaction(is_fraudulent=False)
    elif test_type == "Generate Suspicious Transaction":
        transaction_data = generate_sample_transaction(is_fraudulent=True)
    
    # Get API client
    api_client = get_api_client()
    
    # Transaction form
    with st.form(key="transaction_form"):
        # Display the form with pre-filled values if using generated data
        st.markdown("#### Transaction Details")
        
        # Basic transaction details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            transaction_id = st.text_input(
                "Transaction ID", 
                value=transaction_data.get("transaction_id", f"tx_{int(time.time())}")
            )
        with col2:
            card_id = st.text_input(
                "Card ID", 
                value=transaction_data.get("card_id", "")
            )
        with col3:
            amount = st.number_input(
                "Amount ($)", 
                value=float(transaction_data.get("amount", 0.0)),
                min_value=0.0
            )
        
        # Merchant details
        col1, col2 = st.columns(2)
        
        with col1:
            merchant_name = st.text_input(
                "Merchant Name", 
                value=transaction_data.get("merchant_name", "")
            )
        with col2:
            merchant_category = st.text_input(
                "Merchant Category", 
                value=transaction_data.get("merchant_category", "")
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            merchant_country = st.text_input(
                "Merchant Country", 
                value=transaction_data.get("merchant_country", "US")
            )
        with col2:
            merchant_zip = st.text_input(
                "Merchant ZIP", 
                value=transaction_data.get("merchant_zip", "")
            )
        with col3:
            is_online = st.checkbox(
                "Online Transaction", 
                value=transaction_data.get("is_online", False)
            )
        
        # Additional details
        col1, col2 = st.columns(2)
        
        with col1:
            device_id = st.text_input(
                "Device ID", 
                value=transaction_data.get("device_id", "")
            )
        with col2:
            ip_address = st.text_input(
                "IP Address", 
                value=transaction_data.get("ip_address", "")
            )
        
        # Location
        col1, col2 = st.columns(2)
        
        with col1:
            latitude = st.number_input(
                "Latitude", 
                value=float(transaction_data.get("latitude", 0.0))
            )
        with col2:
            longitude = st.number_input(
                "Longitude", 
                value=float(transaction_data.get("longitude", 0.0))
            )
        
        # Submit button
        submit_button = st.form_submit_button(label="Analyze Transaction")
        
        if submit_button:
            # Prepare transaction data
            transaction = {
                "transaction_id": transaction_id,
                "card_id": card_id,
                "amount": amount,
                "merchant_name": merchant_name,
                "merchant_category": merchant_category,
                "merchant_country": merchant_country,
                "merchant_zip": merchant_zip,
                "is_online": is_online,
                "device_id": device_id,
                "ip_address": ip_address,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": datetime.datetime.now().isoformat(),
                "customer_id": transaction_data.get("customer_id", "cust_12345"),
                "merchant_id": transaction_data.get("merchant_id", "merch_67890"),
                "currency": transaction_data.get("currency", "USD")
            }
            
            # Show loading spinner
            with st.spinner("Analyzing transaction..."):
                # Call the API
                result = api_client.detect_fraud(transaction)
                
                if result:
                    # Display the result
                    display_transaction_result(result)
                      # Store the transaction ID in session state to use it outside the form
            if submit_button and result:
                st.session_state.transaction_for_feedback = transaction_id

    # Display feedback form outside of any form
    if 'transaction_for_feedback' in st.session_state:
        display_feedback_form(st.session_state.transaction_for_feedback)
        # Optional: Remove from session state after displaying
        # Uncomment the following line if you want the form to appear only once
        # del st.session_state.transaction_for_feedback

def historical_lookup():
    """Show the historical transaction lookup tab."""
    st.markdown("### Historical Transaction Lookup")
    
    # Get API client
    api_client = get_api_client()
    
    transaction_id = st.text_input("Enter Transaction ID to look up")
    
    if st.button("Look Up Transaction"):
        if transaction_id:
            with st.spinner("Looking up transaction..."):
                # This would call a history endpoint in a real implementation
                # For now, we'll simulate a response
                if transaction_id.startswith("tx_"):
                    # Mock data for demo
                    result = {
                        "transaction_id": transaction_id,
                        "timestamp": "2025-05-21T09:45:23",
                        "amount": 123.45,
                        "merchant_name": "Grocery Store",
                        "merchant_category": "Groceries",
                        "is_fraud": False,
                        "requires_review": False,
                        "confidence_score": 0.15,
                        "processing_time_ms": 235.67,
                        "decision_reason": "Transaction is consistent with customer's regular shopping patterns. Amount and merchant category are within normal ranges."
                    }
                    display_transaction_result(result)
                else:
                    st.error("Transaction not found. Please check the ID and try again.")
        else:
            st.warning("Please enter a transaction ID.")

def show_transaction_analysis():
    """Show the transaction analysis page."""
    st.markdown("<h1 class='main-header'>Transaction Analysis</h1>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2 = st.tabs(["Real-time Analysis", "Historical Lookup"])
    
    with tab1:
        real_time_analysis()
    
    with tab2:
        historical_lookup()

if __name__ == "__main__":
    show_transaction_analysis()
