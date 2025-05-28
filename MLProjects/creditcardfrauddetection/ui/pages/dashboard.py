"""
Dashboard page for the Credit Card Fraud Detection System.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
from api_client import get_api_client

def display_fraud_metrics(metrics_data):
    """Display fraud detection metrics."""
    cols = st.columns(4)
    
    with cols[0]:
        st.markdown("### Total Transactions")
        st.markdown(f"<h2 style='text-align: center;'>{metrics_data['total_transactions']}</h2>", unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("### Fraud Detected")
        st.markdown(f"<h2 style='text-align: center; color: #D32F2F;'>{metrics_data['fraud_detected']}</h2>", unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("### Fraud Rate")
        fraud_rate = (metrics_data['fraud_detected'] / metrics_data['total_transactions'] * 100) if metrics_data['total_transactions'] > 0 else 0
        st.markdown(f"<h2 style='text-align: center;'>{fraud_rate:.2f}%</h2>", unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown("### Avg. Response Time")
        st.markdown(f"<h2 style='text-align: center;'>{metrics_data['avg_response_time_ms']:.2f} ms</h2>", unsafe_allow_html=True)

    # Add a fraud trend chart
    fig = px.line(
        x=metrics_data['trend_dates'], 
        y=metrics_data['trend_values'],
        labels={'x': 'Date', 'y': 'Fraud Rate (%)'},
        title='Fraud Rate Trend (Last 30 Days)'
    )
    st.plotly_chart(fig, use_container_width=True)

def show_dashboard():
    """Show the dashboard page."""
    st.markdown("<h1 class='main-header'>Fraud Detection Dashboard</h1>", unsafe_allow_html=True)
    
    # Get API client
    api_client = get_api_client()
    
    # Debug information
    if st.session_state.get('debug_mode', False):
        st.sidebar.markdown("### API Debug Info")
        st.sidebar.markdown(f"**API URL**: {api_client.base_url}")
        st.sidebar.markdown(f"**API Key**: {'*' * 8}{api_client.api_key[-4:] if len(api_client.api_key) > 4 else ''}")
    
    # Check API connection
    try:
        if st.session_state.get('debug_mode', False):
            st.info("Attempting to connect to API health endpoint...")
        
        health_check = api_client.get_health()
        
        if health_check:
            if st.session_state.get('debug_mode', False):
                st.sidebar.markdown("### Health Response")
                st.sidebar.json(health_check)
            
            # Accept any of these status values as "healthy"
            if health_check.get("status") in ["ok", "healthy", "up"]:
                st.success("API connection successful! System is healthy.")
            else:
                st.warning(f"API responded but status is unexpected: {health_check.get('status', 'unknown')}")
                st.json(health_check)  # Display the actual response for debugging
                return
        else:
            st.warning("API connection issue. Health check endpoint returned no data.")
            return
    except Exception as e:
        st.error(f"Could not connect to the API: {str(e)}")
        if st.session_state.get('debug_mode', False):
            import traceback
            st.sidebar.markdown("### Error Details")
            st.sidebar.code(traceback.format_exc())
        return
    
    # Get metrics data
    # In a real implementation, this would come from the API
    # For now, we'll use mock data
    metrics_data = {
        "total_transactions": 15872,
        "fraud_detected": 423,
        "fraud_rate": 2.66,
        "avg_response_time_ms": 245.32,
        "trend_dates": [f"2025-05-{day:02d}" for day in range(1, 22)],
        "trend_values": [2.4, 2.5, 2.3, 2.6, 2.7, 2.6, 2.5, 2.4, 2.7, 2.8, 2.6, 2.5, 2.7, 2.6, 2.8, 2.9, 3.0, 2.8, 2.7, 2.6, 2.5]
    }
    
    # Display metrics
    display_fraud_metrics(metrics_data)
    
    # Recent activity
    st.markdown("### Recent Activity")
    
    # In a real implementation, this would come from the API
    # For now, we'll use mock data
    recent_transactions = pd.DataFrame({
        "transaction_id": [f"tx_{i}" for i in range(1000, 1010)],
        "timestamp": [f"2025-05-21 {h:02d}:{m:02d}:{s:02d}" for h, m, s in [
            (9, 45, 23), (9, 48, 12), (9, 52, 45), (9, 55, 17), (10, 2, 34),
            (10, 8, 19), (10, 12, 5), (10, 15, 42), (10, 18, 56), (10, 22, 8)
        ]],
        "amount": [123.45, 67.89, 892.50, 45.00, 1234.56, 78.90, 456.78, 345.67, 12.34, 2345.67],
        "merchant": ["Grocery Store", "Gas Station", "Electronics Store", "Coffee Shop", "Online Store", 
                    "Restaurant", "Department Store", "Drug Store", "Fast Food", "Jewelry Store"],
        "status": ["Legitimate", "Legitimate", "Fraud", "Legitimate", "Review", 
                  "Legitimate", "Legitimate", "Legitimate", "Legitimate", "Fraud"]
    })
    
    # Style the dataframe
    def color_status(val):
        color = 'white'
        if val == 'Fraud':
            color = '#FFCDD2'
        elif val == 'Review':
            color = '#FFF9C4'
        elif val == 'Legitimate':
            color = '#C8E6C9'
        return f'background-color: {color}'
    
    st.dataframe(recent_transactions.style.map(color_status, subset=['status']), use_container_width=True)
    
    # Fraud by category
    st.markdown("### Fraud by Category")
    
    # Mock data for fraud by category
    categories = ["Electronics", "Travel", "Retail", "Dining", "Online Services", "Other"]
    fraud_counts = [145, 87, 62, 23, 74, 32]
    
    fig = px.bar(
        x=categories,
        y=fraud_counts,
        labels={'x': 'Category', 'y': 'Number of Fraud Cases'},
        title='Fraud Cases by Merchant Category'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Fraud by time of day
    st.markdown("### Fraud by Time of Day")
    
    # Mock data for fraud by time of day
    hours = list(range(24))
    fraud_by_hour = [12, 8, 5, 4, 3, 2, 4, 10, 15, 18, 22, 28, 35, 40, 38, 42, 50, 55, 48, 40, 32, 25, 20, 15]
    
    fig = px.line(
        x=hours,
        y=fraud_by_hour,
        labels={'x': 'Hour of Day', 'y': 'Number of Fraud Cases'},
        title='Fraud Cases by Hour of Day'
    )
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show_dashboard()
