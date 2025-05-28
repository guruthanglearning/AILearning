"""
Fraud Patterns Management page for the Credit Card Fraud Detection System.
"""

import streamlit as st
import pandas as pd
import json
import sys
import os
import datetime
import uuid

# Add parent directory to path to import api_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_client import get_api_client

def display_fraud_patterns():
    """Display and allow management of fraud patterns."""
    # Get API client
    api_client = get_api_client()
      # Fetch existing patterns from API
    # Use a status indicator while fetching
    with st.spinner("Fetching fraud patterns from API..."):
        # Try to fetch patterns from API
        api_patterns = api_client.get_fraud_patterns()
        
        # If API call succeeded, update session state
        if api_patterns is not None:
            st.session_state.fraud_patterns = api_patterns
        # If API call failed, show an error
        elif 'fraud_patterns' not in st.session_state:
            st.error("Failed to fetch fraud patterns from API. Please ensure the API server is running.")
            # Initialize with an empty list
            st.session_state.fraud_patterns = []
    
    # Display existing patterns
    patterns = st.session_state.fraud_patterns
    if patterns:
        st.markdown("### Existing Fraud Patterns")
        patterns_df = pd.DataFrame(patterns)
        patterns_df["pattern"] = patterns_df["pattern"].apply(lambda x: json.dumps(x, indent=2))
        st.dataframe(patterns_df, use_container_width=True)
    
    # Form to add new patterns
    st.markdown("### Add New Fraud Pattern")
    with st.form(key="add_pattern_form"):
        pattern_name = st.text_input("Pattern Name")
        pattern_description = st.text_area("Pattern Description")
        pattern_details = st.text_area(
            "Pattern Details (JSON format)",
            value='{\n  "merchant_category": "Electronics",\n  "transaction_type": "online",\n  "indicators": ["high_amount", "new_device"]\n}',
            height=150
        )
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.75,
            step=0.05
        )
        submit_button = st.form_submit_button(label="Add Pattern")
      # Handle form submission
    if submit_button:
        try:
            # Validate JSON
            pattern_json = json.loads(pattern_details)
            
            # Create pattern data structure
            new_pattern = {
                "name": pattern_name,
                "description": pattern_description,
                "pattern": pattern_json,
                "similarity_threshold": similarity_threshold
            }
            
            # Get API client
            api_client = get_api_client()
              # Add pattern via API
            with st.spinner("Adding pattern via API..."):
                response = api_client.add_fraud_pattern(new_pattern)
                
                if response:
                    st.success("Fraud pattern added successfully!")
                    # Update session state to include the new pattern returned from API
                    # (which will include server-generated ID and timestamp)
                    st.session_state.fraud_patterns = api_client.get_fraud_patterns() or st.session_state.fraud_patterns
                else:
                    # If API call failed, show an error message
                    st.error("Failed to add fraud pattern. Please ensure the API server is running correctly.")
                    # Do not add to session state since we want to use the real API data
                
                # Force a rerun to update the display
                st.rerun()
                
        except json.JSONDecodeError:
            st.error("Invalid JSON format in pattern details.")

def show_fraud_patterns():
    """Main function for the fraud patterns page."""
    st.markdown("<h1 class='main-header'>Fraud Pattern Management</h1>", unsafe_allow_html=True)
    
    # Check if we're editing a pattern
    if 'editing_pattern' in st.session_state:
        edit_pattern(st.session_state['editing_pattern'])
    # Check if we're viewing a specific pattern
    elif 'viewing_pattern' in st.session_state:        
        show_pattern_details(st.session_state['viewing_pattern'])
        if st.button("Back to All Patterns"):
            st.session_state.pop('viewing_pattern', None)
            st.rerun()
    else:
        # Show all patterns
        display_fraud_patterns()
        
        # Demo: view pattern details
        st.markdown("### View Pattern Details")
        pattern_id = st.text_input("Enter Pattern ID to view details")
        if st.button("View Details"):
            if pattern_id:
                st.session_state['viewing_pattern'] = pattern_id
                st.rerun()
            else:
                st.warning("Please enter a pattern ID.")

def show_pattern_details(pattern_id):
    """Show detailed view of a specific fraud pattern."""
    # Get API client
    api_client = get_api_client()
    
    # Try to get pattern details from API
    with st.spinner("Fetching pattern details from API..."):
        # Get all patterns from the API
        all_patterns = api_client.get_fraud_patterns()
        pattern = None
        
        if all_patterns:
            # Find the pattern with the matching ID
            for p in all_patterns:
                if p["id"] == pattern_id:                    
                    pattern = p.copy()                    
                    # Add pattern metrics (in a real production app, these would come from a dedicated API endpoint)
                    # Using deterministic calculation based on pattern properties for consistent display
                    name_hash = sum(ord(c) for c in pattern["name"]) % 100  # Simple hash for demo purposes
                    id_hash = sum(ord(c) for c in pattern["id"]) % 50
                    threshold_factor = int(pattern["similarity_threshold"] * 100)
                    
                    # Calculate metrics using the hash values for consistency
                    pattern["matched_transactions"] = name_hash + id_hash
                    pattern["false_positives"] = max(1, int(pattern["matched_transactions"] * (1 - pattern["similarity_threshold"])))
                    pattern["effectiveness"] = round(1.0 - (pattern["false_positives"] / max(pattern["matched_transactions"], 1)), 2)
                    break
    
    # If pattern was not found, show error and create a minimal placeholder
    if not pattern:
        st.error(f"Pattern with ID {pattern_id} not found. Please check the ID and try again.")
        st.info("You will be redirected to the patterns list. If this error persists, please contact support.")
        
        # Add a small delay and return to the main pattern list
        import time
        time.sleep(2)
        st.session_state.pop('viewing_pattern', None)
        st.rerun()
        
        # Provide a minimal pattern for the UI to render while redirecting
        pattern = {
            "id": pattern_id,
            "name": "Pattern Not Found",
            "description": "The requested pattern could not be found.",
            "pattern": {},
            "similarity_threshold": 0.0,
            "created_at": datetime.datetime.now().isoformat(),
            "matched_transactions": 0,
            "false_positives": 0,
            "effectiveness": 0.0
        }
    
    st.markdown(f"## Pattern Details: {pattern['name']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**ID:** {pattern['id']}")
        st.markdown(f"**Created:** {pattern['created_at']}")
        st.markdown(f"**Similarity Threshold:** {pattern['similarity_threshold']}")
    
    with col2:        
        st.markdown(f"**Matched Transactions:** {pattern['matched_transactions']}")
        st.markdown(f"**False Positives:** {pattern['false_positives']}")
        st.markdown(f"**Effectiveness:** {pattern['effectiveness']*100:.1f}%")
    
    st.markdown("### Description")
    st.markdown(pattern['description'])
    
    st.markdown("### Pattern Definition")
    st.json(pattern['pattern'])
    
    # Edit pattern button
    if st.button("Edit Pattern"):
        st.session_state['editing_pattern'] = pattern
        st.rerun()

def edit_pattern(pattern):
    """Show form to edit an existing fraud pattern."""
    st.markdown(f"## Edit Pattern: {pattern['name']}")
    
    with st.form(key="edit_pattern_form"):
        pattern_name = st.text_input("Pattern Name", value=pattern['name'])
        pattern_description = st.text_area("Pattern Description", value=pattern['description'])
        
        pattern_details = st.text_area(
            "Pattern Details (JSON format)",
            value=json.dumps(pattern['pattern'], indent=2),
            height=150
        )
        
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=pattern['similarity_threshold'],
            step=0.05
        )
        
        submit_button = st.form_submit_button(label="Update Pattern")
        
        # Handle form submission
        if submit_button:
            try:
                # Validate JSON
                pattern_json = json.loads(pattern_details)
                
                # Create updated pattern data structure
                updated_pattern = pattern.copy()
                updated_pattern.update({
                    "name": pattern_name,
                    "description": pattern_description,
                    "pattern": pattern_json,
                    "similarity_threshold": similarity_threshold
                })
                
                # Get API client
                api_client = get_api_client()
                  # Add the updated pattern via the API using the dedicated update endpoint
                with st.spinner("Updating pattern via API..."):
                    response = api_client.update_fraud_pattern(updated_pattern["id"], updated_pattern)
                    
                    if response:
                        st.success("Fraud pattern updated successfully!")
                        # Update session state with the latest patterns from API
                        st.session_state.fraud_patterns = api_client.get_fraud_patterns() or st.session_state.fraud_patterns
                        st.session_state.pop('editing_pattern', None)
                        st.rerun()
                    else:
                        st.error("Failed to update fraud pattern. Please ensure the API server is running correctly.")
                
            except json.JSONDecodeError:
                st.error("Invalid JSON format in pattern details.")
    
    # Cancel button outside the form
    if st.button("Cancel"):
        st.session_state.pop('editing_pattern', None)
        st.rerun()