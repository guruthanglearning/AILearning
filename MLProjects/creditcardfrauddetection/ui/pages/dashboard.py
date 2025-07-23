"""
Dashboard page for the Credit Card Fraud Detection System.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
from api_client import get_api_client

def transform_metrics_data(api_metrics):
    """
    Transform the API metrics response to the format expected by the dashboard.
    
    Args:
        api_metrics: The API metrics response
        
    Returns:
        Transformed metrics data
    """
    if not api_metrics:
        return None
    
    # Initialize with the structure we need
    transformed_data = {
        "total_transactions": 0,
        "fraud_detected": 0,
        "avg_response_time_ms": 0.0,
        "fraud_by_category": [],
        "fraud_by_hour": [],
    }
    
    # Extract transaction data from the nested structure
    if "transactions" in api_metrics:
        transactions = api_metrics["transactions"]
        transformed_data["total_transactions"] = transactions.get("total", 0)
        transformed_data["fraud_detected"] = transactions.get("fraudulent", 0)
    # Fallback: If we don't have the nested structure but have direct keys, use them
    elif "total_transactions" in api_metrics and "fraud_detected" in api_metrics:
        transformed_data["total_transactions"] = api_metrics.get("total_transactions", 0)
        transformed_data["fraud_detected"] = api_metrics.get("fraud_detected", 0)
    # Special handling for metrics nested under models
    elif "models" in api_metrics:
        # If there's transaction data under "models", extract it
        # This is just a guess at the potential structure
        models_data = api_metrics.get("models", [])
        for model in models_data:
            if "metrics" in model and "total_transactions" in model["metrics"]:
                transformed_data["total_transactions"] = model["metrics"].get("total_transactions", 0)
            if "metrics" in model and "fraud_detected" in model["metrics"]:
                transformed_data["fraud_detected"] = model["metrics"].get("fraud_detected", 0)
    
    # Extract system data
    if "system" in api_metrics:
        system = api_metrics["system"]
        transformed_data["avg_response_time_ms"] = system.get("avg_response_time_ms", 0.0)
    # Fallback: If we have direct access to avg_response_time_ms
    elif "avg_response_time_ms" in api_metrics:
        transformed_data["avg_response_time_ms"] = api_metrics.get("avg_response_time_ms", 0.0)
    # Special handling for metrics nested under models
    elif "models" in api_metrics:
        models_data = api_metrics.get("models", [])
        for model in models_data:
            if "metrics" in model and "latency_ms" in model["metrics"]:
                # Use latency as fallback for avg_response_time
                transformed_data["avg_response_time_ms"] = model["metrics"].get("latency_ms", 0.0)
                break
    
    # Calculate fraud rate for display
    fraud_rate = 0.0
    if transformed_data["total_transactions"] > 0:
        fraud_rate = (transformed_data["fraud_detected"] / transformed_data["total_transactions"]) * 100
    elif "fraud_rate" in api_metrics:
        fraud_rate = api_metrics["fraud_rate"] * 100
    elif "transactions" in api_metrics and "fraud_rate" in api_metrics["transactions"]:
        fraud_rate = api_metrics["transactions"]["fraud_rate"] * 100
        
    # Initialize empty data structures - these should be populated by API calls
    transformed_data["trend_dates"] = []
    transformed_data["trend_values"] = []
    transformed_data["fraud_by_category"] = []
    transformed_data["fraud_by_hour"] = []
    
    # Note: In a production system, these would be populated by additional API endpoints:
    # - GET /api/v1/metrics/trends for trend data
    # - GET /api/v1/metrics/by-category for category breakdown
    # - GET /api/v1/metrics/by-hour for hourly statistics
    
    return transformed_data

def display_fraud_metrics(metrics_data):
    """Display fraud detection metrics."""
    cols = st.columns(4)
    
    # Make sure metrics_data contains all required keys
    required_keys = ['total_transactions', 'fraud_detected', 'avg_response_time_ms']
    missing_keys = [key for key in required_keys if key not in metrics_data]
    
    if missing_keys:
        st.error(f"Missing required metric keys: {', '.join(missing_keys)}")
        st.info("Using fallback values for missing metrics")
        # Debug info when metrics are missing
        if st.session_state.get('debug_mode', False):
            with st.expander("Available Keys"):
                st.write(list(metrics_data.keys()))
        
        # Set default values for any missing keys
        if 'total_transactions' not in metrics_data:
            metrics_data['total_transactions'] = 0
        if 'fraud_detected' not in metrics_data:
            metrics_data['fraud_detected'] = 0
        if 'avg_response_time_ms' not in metrics_data:
            metrics_data['avg_response_time_ms'] = 0.0
    
    with cols[0]:
        st.markdown("### Total Transactions")
        st.markdown(f"<h2 style='text-align: center;'>{metrics_data['total_transactions']}</h2>", unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("### Fraud Detected")
        st.markdown(f"<h2 style='text-align: center; color: #D32F2F;'>{metrics_data['fraud_detected']}</h2>", unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("### Fraud Rate")
        fraud_rate = (metrics_data['fraud_detected'] / metrics_data['total_transactions'] * 100) if metrics_data.get('total_transactions', 0) > 0 else 0
        st.markdown(f"<h2 style='text-align: center;'>{fraud_rate:.2f}%</h2>", unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown("### Avg. Response Time")
        st.markdown(f"<h2 style='text-align: center;'>{metrics_data['avg_response_time_ms']:.2f} ms</h2>", unsafe_allow_html=True)

    # Add a fraud trend chart
    if 'trend_dates' in metrics_data and 'trend_values' in metrics_data:
        trend_df = pd.DataFrame({
            'Date': metrics_data['trend_dates'],
            'Fraud Rate (%)': metrics_data['trend_values']
        })
        fig = px.line(
            trend_df,
            x='Date', 
            y='Fraud Rate (%)',
            title='Fraud Rate Trend (Last 30 Days)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Trend data not available")

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
    api_available = False
    try:
        # Always display the API URL we're connecting to
        api_url = api_client.base_url
        
        # Create a debug expander that's always available but collapsed by default
        with st.expander("API Connection Details", expanded=st.session_state.get('debug_mode', False)):
            st.write(f"API URL: {api_url}")
            st.write(f"Health endpoint: {api_url}/health")
            st.write(f"API Key (last 4): {'*' * 8}{api_client.api_key[-4:] if len(api_client.api_key) > 4 else ''}")
            
            if st.button("Enable Debug Mode"):
                st.session_state['debug_mode'] = True
                st.session_state['show_api_errors'] = True
                st.experimental_rerun()
        
        # Indicate connection attempt is happening
        with st.spinner("Checking API connection..."):
            if st.session_state.get('debug_mode', False):
                st.info(f"Attempting to connect to API health endpoint: {api_url}/health")
            
            health_check = api_client.get_health()
        
        if health_check:
            if st.session_state.get('debug_mode', False):
                st.sidebar.markdown("### Health Response")
                st.sidebar.json(health_check)
            
            # Accept any of these status values as "healthy"
            if health_check.get("status") in ["ok", "healthy", "up"]:
                st.success("API connection successful! System is healthy.")
                api_available = True
            else:
                st.warning(f"API responded but status is unexpected: {health_check.get('status', 'unknown')}")
                if st.session_state.get('debug_mode', False):
                    st.json(health_check)  # Display the actual response for debugging
        else:
            st.warning("API connection issue. Health check endpoint returned no data.")
            st.info("The system will use development data for demonstration purposes.")
            with st.expander("⚠️ API connection troubleshooting"):
                st.markdown("""
                **Possible reasons for the connection issue:**
                1. API server is not running - start it with `launch_system.ps1`
                2. API server is running on a different port - check the API URL
                3. Network or firewall issues - check your connection settings
                4. API server has internal errors - check the API server logs
                
                **To fix:**
                1. Make sure the API server is running in a separate terminal window
                2. Check the API URL in the UI environment settings
                3. Try restarting both the API and UI with `launch_system.ps1`
                """)
    except Exception as e:
        st.warning(f"Could not connect to the API: {str(e)}")
        if st.session_state.get('debug_mode', False) or st.session_state.get('show_api_errors', False):
            import traceback
            with st.expander("⚠️ Error Details", expanded=True):
                st.markdown("### Error Details")
                st.code(traceback.format_exc())
        st.info("The system will use development data for demonstration purposes.")
    
    # Get metrics data from the API
    with st.spinner("Fetching metrics from API..."):
        metrics_data = api_client.get_metrics() if api_available else None
        
        if not metrics_data:
            st.error("Unable to fetch metrics data from API. Please ensure the API server is running.")
            st.stop()  # Stop execution if no API data is available
        else:
            # Debug information about the API response structure
            if st.session_state.get('debug_mode', False):
                with st.expander("Raw API metrics data"):
                    st.json(metrics_data)
            
            # Transform the metrics data to the expected format
            metrics_data = transform_metrics_data(metrics_data)
    
    # Display metrics
    display_fraud_metrics(metrics_data)
    
    # Recent activity
    st.markdown("### Recent Activity")
    
    # Get recent transactions from the API
    with st.spinner("Fetching recent transactions..."):
        transactions_data = api_client.get_transaction_history() if api_available else None
        
        if transactions_data and isinstance(transactions_data, list):
            # Convert API response to DataFrame
            recent_transactions = pd.DataFrame(transactions_data)
        else:
            # Use development data for demonstration
            if not api_available:
                st.info("Using development data for demonstration purposes.")
            recent_transactions = pd.DataFrame({
                "transaction_id": [f"tx_{i}" for i in range(1000, 1010)],
                "timestamp": [f"2025-05-21 {h:02d}:{m:02d}:{s:02d}" for h, m, s in [
                    (9, 45, 23), (9, 48, 12), (9, 52, 45), (9, 55, 17), (10, 2, 34),
                    (10, 8, 19), (10, 12, 5), (10, 15, 42), (10, 18, 56), (10, 22, 8)
                ]],
                "amount": [123.45, 67.89, 892.50, 45.00, 1234.56, 78.90, 456.78, 345.67, 12.34, 2345.67],
                "merchant_name": ["Grocery Store", "Gas Station", "Electronics Store", "Coffee Shop", "Online Store", 
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
    
    # Ensure the dataframe has the needed columns before displaying
    if not recent_transactions.empty:
        # Rename merchant_name column to merchant if it exists
        if 'merchant_name' in recent_transactions.columns and 'merchant' not in recent_transactions.columns:
            recent_transactions = recent_transactions.rename(columns={'merchant_name': 'merchant'})
        
        # Ensure status column exists
        if 'status' in recent_transactions.columns:
            st.dataframe(recent_transactions.style.map(color_status, subset=['status']), use_container_width=True)
        else:
            st.dataframe(recent_transactions, use_container_width=True)
    else:
        st.info("No recent transactions available.")
    
    # Fraud by category
    st.markdown("### Fraud by Category")
    
    # Get fraud by category from the metrics
    if metrics_data and 'fraud_by_category' in metrics_data:
        fraud_by_category = metrics_data['fraud_by_category']
        if fraud_by_category:
            categories = [item.get('category', '') for item in fraud_by_category]
            fraud_counts = [item.get('count', 0) for item in fraud_by_category]
            
            fig = px.bar(
                x=categories,
                y=fraud_counts,
                labels={'x': 'Category', 'y': 'Number of Fraud Cases'},
                title='Fraud Cases by Merchant Category'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No fraud by category data available.")
    else:
        st.warning("Fraud by category data not found in metrics.")
    
    # Fraud by time of day
    st.markdown("### Fraud by Time of Day")
    
    # Get fraud by time of day from the metrics
    if metrics_data and 'fraud_by_hour' in metrics_data:
        fraud_by_hour_data = metrics_data['fraud_by_hour']
        if fraud_by_hour_data:
            hours = [item.get('hour', 0) for item in fraud_by_hour_data]
            fraud_counts = [item.get('count', 0) for item in fraud_by_hour_data]
            
            fig = px.line(
                x=hours,
                y=fraud_counts,
                labels={'x': 'Hour of Day', 'y': 'Number of Fraud Cases'},
                title='Fraud Cases by Hour of Day'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No fraud by hour data available.")
    else:
        st.warning("Fraud by hour data not found in metrics.")

if __name__ == "__main__":
    show_dashboard()
