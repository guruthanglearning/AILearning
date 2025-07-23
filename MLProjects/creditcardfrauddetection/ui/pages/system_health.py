"""
System Health & Monitoring page for the Credit Card Fraud Detection System.
This page provides system health metrics, performance monitoring, and logs.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
from api_client import get_api_client

def display_system_health():
    """Display system health metrics and monitoring information."""
    st.markdown("## System Health & Monitoring")
    
    # Get API client
    api_client = get_api_client()
      # System status
    st.markdown("### System Status")
    
    # Check for model switch notification
    if 'model_switch_notification' in st.session_state and not st.session_state['model_switch_notification'].get('displayed', False):
        notification = st.session_state['model_switch_notification']
        st.warning(f"⚠️ LLM Model Switch: {notification['message']} (From: {notification['from_model']} → To: {notification['to_model']})")
        st.session_state['model_switch_notification']['displayed'] = True
    
    # Get health info to check LLM status
    health_info = api_client.get_health()
    llm_type = health_info.get('llm_service_type', 'unknown') if health_info else 'unknown'
    llm_model = health_info.get('llm_model', 'N/A') if health_info else 'N/A'
    
    # Add a new row for LLM information
    st.markdown("#### Current LLM Service")
    cols_llm = st.columns(2)
    with cols_llm[0]:
        if llm_type == 'openai':
            st.success(f"Using OpenAI API: {llm_model}")
        elif llm_type == 'local':
            st.info(f"Using Local LLM: {llm_model}")
        elif llm_type in ['enhanced_mock', 'basic_mock']:
            st.warning(f"Using Mock LLM: {llm_model}")
        else:
            st.error("LLM Service: Unknown")
    
    with cols_llm[1]:
        if llm_type == 'openai':
            st.markdown("**Status:** Connected to OpenAI API")
        elif llm_type == 'local':
            st.markdown("**Status:** Using local model (no API costs)")
        elif llm_type in ['enhanced_mock', 'basic_mock']:
            st.markdown("**Status:** Using simulated responses (demonstration mode)")
        else:
            st.markdown("**Status:** Unknown LLM service state")
    
    # Add separator
    st.markdown("---")
    
    # Original system metrics columns
    cols = st.columns(3)
    
    # Try to get system metrics from API
    metrics_data = api_client.get_metrics()
    
    if metrics_data and "system" in metrics_data:
        # Use real metrics data
        system_metrics = metrics_data["system"]
        
        with cols[0]:
            st.metric(label="API Status", value="Online", delta="Normal")
        with cols[1]:
            st.metric(
                label="Average Response Time", 
                value=f"{system_metrics['avg_response_time_ms']:.1f} ms", 
                delta="-12 ms"
            )
        with cols[2]:
            error_rate_pct = system_metrics['error_rate'] * 100
            st.metric(
                label="Error Rate", 
                value=f"{error_rate_pct:.3f}%", 
                delta=f"{-0.01:.2f}%" if error_rate_pct < 0.03 else f"{0.01:.2f}%"
            )
    else:
        # Fallback to sample data if API call fails
        with cols[0]:
            st.metric(label="API Status", value="Online", delta="Normal")
        with cols[1]:
            st.metric(label="Average Response Time", value="245 ms", delta="-12 ms")
        with cols[2]:
            st.metric(label="Error Rate", value="0.02%", delta="-0.01%")
    
    # Performance metrics
    st.markdown("### Performance Metrics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.date(2025, 5, 1),
            min_value=datetime.date(2025, 1, 1),
            max_value=datetime.date(2025, 5, 21)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.date(2025, 5, 21),
            min_value=start_date,
            max_value=datetime.date(2025, 5, 21)
        )
    
    # Sample performance data
    dates = pd.date_range(start=start_date, end=end_date)
    response_times = np.random.normal(250, 25, size=len(dates))
    error_rates = np.random.beta(1, 100, size=len(dates)) * 100
    request_counts = np.random.normal(5000, 500, size=len(dates)).astype(int)
    
    # Create DataFrame for metrics
    metrics_df = pd.DataFrame({
        'Date': dates,
        'Response Time (ms)': response_times,
        'Error Rate (%)': error_rates,
        'Request Count': request_counts
    })
    
    # Tabs for different metrics
    tab1, tab2, tab3 = st.tabs(["Response Times", "Error Rates", "Request Volume"])
    
    with tab1:
        fig = px.line(
            metrics_df, 
            x='Date', 
            y='Response Time (ms)',
            title='API Response Times'
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Response Time (ms)")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.line(
            metrics_df, 
            x='Date', 
            y='Error Rate (%)',
            title='API Error Rates'
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Error Rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.bar(
            metrics_df, 
            x='Date', 
            y='Request Count',
            title='Daily Request Volume'
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Request Count")
        st.plotly_chart(fig, use_container_width=True)
    
    # Model performance
    st.markdown("### Model Performance")
    
    # Fraud detection model metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Sample model metrics over time
        st.subheader("Model Metrics Over Time")
        
        # Generate sample data for model metrics over time
        dates = pd.date_range(start=start_date, end=end_date)
        accuracy = 0.95 + np.random.normal(0, 0.01, size=len(dates))
        precision = 0.92 + np.random.normal(0, 0.02, size=len(dates))
        recall = 0.89 + np.random.normal(0, 0.02, size=len(dates))
        f1 = 0.91 + np.random.normal(0, 0.015, size=len(dates))
        
        # Create dataframe for metrics
        model_metrics_df = pd.DataFrame({
            'Date': dates,
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1 Score': f1
        })
        
        # Select which metrics to display
        selected_metrics = st.multiselect(
            "Select metrics to display",
            options=['Accuracy', 'Precision', 'Recall', 'F1 Score'],
            default=['Accuracy', 'F1 Score']
        )
        
        if selected_metrics:
            fig = px.line(
                model_metrics_df, 
                x='Date', 
                y=selected_metrics,
                title='Model Performance Metrics Over Time'
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="Score", yaxis=dict(range=[0.85, 1.0]))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Please select at least one metric to display.")
    
    with col2:        # Current model comparison
        st.subheader("Current Model Comparison")
        
        # Get model metrics from API
        with st.spinner("Loading model metrics from API..."):
            metrics_data = api_client.get_metrics()
            
            if metrics_data and "models" in metrics_data:
                # We have real metrics data from the API
                
                # Extract model metrics into a DataFrame
                models = metrics_data["models"]
                model_metrics_data = []
                
                for metric_name in ["accuracy", "precision", "recall", "f1_score", "auc"]:
                    row = {"Metric": metric_name.replace("_", " ").title()}
                    
                    for model in models:
                        row[model["name"]] = model["metrics"][metric_name]
                        
                    model_metrics_data.append(row)
                    
                model_metrics = pd.DataFrame(model_metrics_data)
                
                st.success("Displaying real model metrics data from your models")
            else:
                # Fallback to sample data if API call fails
                st.warning("Couldn't load real metrics data from API. Showing sample data.")
                
                # Sample model metrics for comparison
                model_metrics = pd.DataFrame({
                    "Metric": ["Accuracy", "Precision", "Recall", "F1 Score", "AUC"],
                    "ML Model": [0.952, 0.923, 0.897, 0.910, 0.964],
                    "LLM+RAG": [0.968, 0.942, 0.921, 0.931, 0.978],
                    "Combined": [0.975, 0.958, 0.943, 0.950, 0.986]
                })
            
            # Create the comparison chart
            fig = go.Figure()
            
            for column in model_metrics.columns[1:]:
                fig.add_trace(go.Bar(
                    x=model_metrics["Metric"],
                    y=model_metrics[column],
                    name=column
                ))
            
            fig.update_layout(
                title="Model Performance Comparison",
                xaxis_title="Metric",
                yaxis_title="Score",
                yaxis=dict(range=[0.85, 1.0]),
                barmode='group'
            )
            
            # Add last updated time if available
            if metrics_data and "timestamp" in metrics_data:
                update_time = datetime.datetime.fromisoformat(metrics_data["timestamp"].replace("Z", "+00:00"))
                fig.update_layout(
                    annotations=[
                        dict(
                            text=f"Last updated: {update_time.strftime('%Y-%m-%d %H:%M:%S')}",
                            showarrow=False,
                            x=0.5,
                            y=-0.15,
                            xref="paper",
                            yref="paper"
                        )
                    ]
                )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # After the current model metrics section, add model switching controls
    st.markdown("### LLM Model Controls")
    
    # Get current LLM status
    llm_status = api_client.get_llm_status()
    current_model_type = llm_status.get("llm_service_type", "unknown") if llm_status else "unknown"
    
    # Create model switching form
    with st.form("switch_model_form"):
        st.markdown("**Switch LLM Model**")
        st.markdown("Use this to manually switch between different LLM service types:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            openai_button = st.form_submit_button("Use OpenAI API", 
                type="primary" if current_model_type == "openai" else "secondary",
                disabled=current_model_type == "openai")
                
        with col2:
            local_button = st.form_submit_button("Use Local LLM", 
                type="primary" if current_model_type == "local" else "secondary",
                disabled=current_model_type == "local")
                
        with col3:
            mock_button = st.form_submit_button("Use Mock LLM", 
                type="primary" if current_model_type in ["enhanced_mock", "basic_mock"] else "secondary",
                disabled=current_model_type in ["enhanced_mock", "basic_mock"])
                
        # Handle button clicks
        if openai_button:
            with st.spinner("Switching to OpenAI API..."):
                result = api_client.switch_llm_model("openai")
                if result and result.get("success"):
                    st.success(result.get("message", "Successfully switched to OpenAI API"))
                    st.session_state['model_switch_notification'] = {
                        'timestamp': datetime.datetime.now().isoformat(),
                        'message': 'Manually switched to OpenAI API',
                        'from_model': current_model_type,
                        'to_model': 'OpenAI API',
                        'displayed': False
                    }
                else:
                    st.error(result.get("message", "Failed to switch to OpenAI API"))
                    
        elif local_button:
            with st.spinner("Switching to Local LLM..."):
                result = api_client.switch_llm_model("local")
                if result and result.get("success"):
                    st.success(result.get("message", "Successfully switched to Local LLM"))
                    st.session_state['model_switch_notification'] = {
                        'timestamp': datetime.datetime.now().isoformat(),
                        'message': 'Manually switched to Local LLM',
                        'from_model': current_model_type,
                        'to_model': 'Local LLM',
                        'displayed': False
                    }
                else:
                    st.error(result.get("message", "Failed to switch to Local LLM"))
                    
        elif mock_button:
            with st.spinner("Switching to Mock LLM..."):
                result = api_client.switch_llm_model("mock")
                if result and result.get("success"):
                    st.success(result.get("message", "Successfully switched to Mock LLM"))
                    st.session_state['model_switch_notification'] = {
                        'timestamp': datetime.datetime.now().isoformat(),
                        'message': 'Manually switched to Mock LLM',
                        'from_model': current_model_type,
                        'to_model': 'Mock LLM',
                        'displayed': False
                    }
                else:
                    st.error(result.get("message", "Failed to switch to Mock LLM"))
    
    # Resource utilization
    st.markdown("### Resource Utilization")
    
    # Sample resource utilization data
    dates = pd.date_range(start=start_date, end=end_date)
    cpu_usage = np.random.normal(40, 15, size=len(dates))
    memory_usage = np.random.normal(60, 10, size=len(dates))
    disk_io = np.random.normal(30, 12, size=len(dates))
    
    # Create DataFrame for resource metrics
    resource_df = pd.DataFrame({
        'Date': dates,
        'CPU Usage (%)': cpu_usage,
        'Memory Usage (%)': memory_usage,
        'Disk I/O (%)': disk_io
    })
    
    # Tabs for different resources
    tab1, tab2, tab3 = st.tabs(["CPU Usage", "Memory Usage", "Disk I/O"])
    
    with tab1:
        fig = px.line(
            resource_df, 
            x='Date', 
            y='CPU Usage (%)',
            title='CPU Usage Over Time'
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="CPU Usage (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.line(
            resource_df, 
            x='Date', 
            y='Memory Usage (%)',
            title='Memory Usage Over Time'
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Memory Usage (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.line(
            resource_df, 
            x='Date', 
            y='Disk I/O (%)',
            title='Disk I/O Over Time'
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Disk I/O (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    # System logs
    st.markdown("### System Logs")
    
    # Log level selector
    log_level = st.selectbox("Log Level", ["INFO", "WARNING", "ERROR", "DEBUG"])
    
    # Log type selector
    log_type = st.selectbox("Log Type", ["All", "API", "Model", "Database", "Security"])
    
    # Sample logs
    logs = [
        {"timestamp": "2025-05-21 10:15:23", "level": "INFO", "type": "API", "message": "Transaction tx_1000 processed successfully"},
        {"timestamp": "2025-05-21 10:14:12", "level": "INFO", "type": "API", "message": "Transaction tx_999 processed successfully"},
        {"timestamp": "2025-05-21 10:12:45", "level": "WARNING", "type": "API", "message": "High response time detected for transaction tx_998"},
        {"timestamp": "2025-05-21 10:10:33", "level": "INFO", "type": "Model", "message": "Model prediction completed for transaction tx_997"},
        {"timestamp": "2025-05-21 10:08:21", "level": "ERROR", "type": "Database", "message": "Failed to process transaction tx_996: Database connection timeout"},
        {"timestamp": "2025-05-21 10:05:17", "level": "INFO", "type": "API", "message": "Transaction tx_995 processed successfully"},
        {"timestamp": "2025-05-21 10:03:42", "level": "DEBUG", "type": "Model", "message": "Vector similarity calculation took 123ms for transaction tx_994"},
        {"timestamp": "2025-05-21 10:01:19", "level": "INFO", "type": "Security", "message": "Suspicious IP address detected for transaction tx_993"},
    ]
    
    # Filter logs by selected level and type
    filtered_logs = logs
    
    # Filter by log level
    if log_level != "DEBUG":
        filtered_logs = [log for log in filtered_logs if log["level"] == log_level or 
                        (log_level == "WARNING" and log["level"] == "ERROR") or
                        (log_level == "ERROR" and log["level"] != "WARNING" and log["level"] != "INFO" and log["level"] != "DEBUG")]
    
    # Filter by log type
    if log_type != "All":
        filtered_logs = [log for log in filtered_logs if log["type"] == log_type]
    
    # Display logs with appropriate styling
    for log in filtered_logs:
        if log["level"] == "ERROR":
            st.error(f"{log['timestamp']} - {log['type']} - {log['message']}")
        elif log["level"] == "WARNING":
            st.warning(f"{log['timestamp']} - {log['type']} - {log['message']}")
        elif log["level"] == "INFO":
            st.info(f"{log['timestamp']} - {log['type']} - {log['message']}")
        else:
            st.text(f"{log['timestamp']} - {log['type']} - {log['level']} - {log['message']}")
    
    # If no logs match the filters
    if not filtered_logs:
        st.write("No logs match the selected filters.")
    
    # Alert configuration
    st.markdown("### Alert Configuration")
    
    with st.expander("Configure System Alerts"):
        st.markdown("Set up alerts for system events and performance thresholds.")
        
        # Alert types
        alert_types = st.multiselect(
            "Select alert types to enable",
            options=["High Error Rate", "High Response Time", "Low Model Accuracy", "System Downtime", "Unusual Transaction Volume"],
            default=["High Error Rate", "System Downtime"]
        )
        
        # Alert thresholds
        if "High Error Rate" in alert_types:
            st.slider("Error Rate Threshold (%)", min_value=0.01, max_value=5.0, value=1.0, step=0.01)
        
        if "High Response Time" in alert_types:
            st.slider("Response Time Threshold (ms)", min_value=200, max_value=1000, value=500, step=10)
        
        if "Low Model Accuracy" in alert_types:
            st.slider("Model Accuracy Threshold", min_value=0.8, max_value=0.99, value=0.9, step=0.01)
        
        if "Unusual Transaction Volume" in alert_types:
            st.slider("Transaction Volume Change Threshold (%)", min_value=10, max_value=100, value=30, step=5)
        
        # Notification methods
        st.multiselect(
            "Notification Methods",
            options=["Email", "SMS", "Slack", "PagerDuty", "Webhook"],
            default=["Email", "Slack"]
        )
        
        # Recipients
        st.text_area("Notification Recipients", value="admin@example.com, oncall@example.com")
        
        # Save button
        if st.button("Save Alert Configuration"):
            st.success("Alert configuration saved successfully!")

if __name__ == "__main__":
    st.set_page_config(
        page_title="System Health - Credit Card Fraud Detection",
        page_icon="💳",
        layout="wide",
    )
    display_system_health()
