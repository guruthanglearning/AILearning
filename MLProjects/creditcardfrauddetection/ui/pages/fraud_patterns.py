"""
Fraud Patterns Management page for the Credit Card Fraud Detection System.
Enhanced with grid view, CRUD operations, filtering, and search functionality.
"""

import streamlit as st
import pandas as pd
import json
import datetime
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import api_client from parent directory
from api_client import get_api_client

def display_fraud_patterns():
    """Display fraud patterns in a grid with search, filter, and CRUD operations."""
    # Initialize session state
    if 'fraud_patterns' not in st.session_state:
        st.session_state.fraud_patterns = []
    if 'filtered_patterns' not in st.session_state:
        st.session_state.filtered_patterns = []
    if 'show_add_form' not in st.session_state:
        st.session_state.show_add_form = False
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    if 'fraud_type_filter' not in st.session_state:
        st.session_state.fraud_type_filter = "All"

    # Get API client
    api_client = get_api_client()
    
    # Load patterns from API
    with st.spinner("Loading fraud patterns..."):
        try:
            api_patterns = api_client.get_fraud_patterns()
            if api_patterns is not None:
                st.session_state.fraud_patterns = api_patterns
            elif not st.session_state.fraud_patterns:
                st.error("Failed to fetch fraud patterns from API. Please ensure the API server is running.")
                st.session_state.fraud_patterns = []
        except Exception as e:
            st.error(f"Error loading patterns: {str(e)}")
            st.session_state.fraud_patterns = []

    # Header section
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("### 🔍 Fraud Patterns Management")
    with col2:
        if st.button("🔄 Refresh", help="Reload patterns from API"):
            st.rerun()
    with col3:
        if st.button("➕ Add New Pattern", type="primary"):
            st.session_state.show_add_form = not st.session_state.show_add_form
            st.rerun()

    # Search and Filter Section
    st.markdown("#### Search & Filter")
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 Search patterns", 
            value=st.session_state.search_term,
            placeholder="Search by name, description, or fraud type...",
            key="search_input"
        )
        if search_term != st.session_state.search_term:
            st.session_state.search_term = search_term
            st.rerun()
    
    with col2:
        # Get unique fraud types for filter
        fraud_types = ["All"]
        if st.session_state.fraud_patterns:
            unique_types = set()
            for pattern in st.session_state.fraud_patterns:
                fraud_type = pattern.get("pattern", {}).get("fraud_type", "Unknown")
                if fraud_type:
                    unique_types.add(fraud_type)
            fraud_types.extend(sorted(unique_types))
        
        fraud_type_filter = st.selectbox(
            "📊 Filter by Fraud Type",
            fraud_types,
            index=fraud_types.index(st.session_state.fraud_type_filter) if st.session_state.fraud_type_filter in fraud_types else 0,
            key="fraud_type_filter_select"
        )
        if fraud_type_filter != st.session_state.fraud_type_filter:
            st.session_state.fraud_type_filter = fraud_type_filter
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Filters", help="Clear search and filters"):
            st.session_state.search_term = ""
            st.session_state.fraud_type_filter = "All"
            st.rerun()

    # Apply filters
    filtered_patterns = apply_filters(st.session_state.fraud_patterns, search_term, fraud_type_filter)
    st.session_state.filtered_patterns = filtered_patterns

    # Display results count
    st.markdown(f"**Showing {len(filtered_patterns)} of {len(st.session_state.fraud_patterns)} patterns**")

    # Add new pattern form (collapsible)
    if st.session_state.show_add_form:
        with st.expander("➕ Add New Fraud Pattern", expanded=True):
            add_pattern_form()

    # Display patterns in grid format
    if filtered_patterns:
        display_patterns_grid(filtered_patterns)
    else:
        if st.session_state.fraud_patterns:
            st.info("No patterns match your search criteria. Try adjusting your filters.")
        else:
            st.info("📝 No fraud patterns found. Click 'Add New Pattern' to get started!")

def apply_filters(patterns, search_term, fraud_type_filter):
    """Apply search and filter criteria to patterns."""
    filtered = patterns.copy()
    
    # Apply search filter
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            p for p in filtered
            if (search_lower in p.get("name", "").lower() or
                search_lower in p.get("description", "").lower() or
                search_lower in p.get("pattern", {}).get("fraud_type", "").lower())
        ]
    
    # Apply fraud type filter
    if fraud_type_filter != "All":
        filtered = [
            p for p in filtered
            if p.get("pattern", {}).get("fraud_type") == fraud_type_filter
        ]
    
    return filtered

def display_patterns_grid(patterns):
    """Display patterns in a grid format with action buttons."""
    st.markdown("#### 📋 Patterns Grid")
    
    # Create DataFrame for better display
    grid_data = []
    for i, pattern in enumerate(patterns):
        grid_data.append({
            "ID": pattern.get("id", "Unknown"),
            "Name": pattern.get("name", "Unnamed"),
            "Description": pattern.get("description", "No description")[:50] + ("..." if len(pattern.get("description", "")) > 50 else ""),
            "Fraud Type": pattern.get("pattern", {}).get("fraud_type", "Unknown"),
            "Threshold": f"{pattern.get('similarity_threshold', 0.0):.2f}",
            "Created": pattern.get("created_at", "Unknown")[:10] if pattern.get("created_at") else "Unknown",
            "Actions": i  # We'll use this index for action buttons
        })
    
    if not grid_data:
        st.info("No patterns to display.")
        return
    
    df = pd.DataFrame(grid_data)
    
    # Display the grid
    st.dataframe(
        df[["ID", "Name", "Description", "Fraud Type", "Threshold", "Created"]], 
        use_container_width=True,
        hide_index=True
    )
    
    # Action buttons for each pattern
    st.markdown("#### Actions")
    
    # Create columns for action buttons
    num_cols = min(len(patterns), 3)  # Max 3 patterns per row
    
    for i in range(0, len(patterns), num_cols):
        cols = st.columns(num_cols)
        
        for j in range(num_cols):
            pattern_idx = i + j
            if pattern_idx < len(patterns):
                pattern = patterns[pattern_idx]
                
                with cols[j]:
                    st.markdown(f"**{pattern.get('name', 'Unnamed')}**")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("👁️ View", key=f"view_{pattern_idx}", help="View details"):
                            st.session_state['viewing_pattern'] = pattern
                            st.rerun()
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{pattern_idx}", help="Edit pattern"):
                            st.session_state['editing_pattern'] = pattern
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{pattern_idx}", help="Delete pattern", type="secondary"):
                            st.session_state[f'confirm_delete_{pattern_idx}'] = True
                            st.rerun()
                    
                    # Delete confirmation
                    if st.session_state.get(f'confirm_delete_{pattern_idx}', False):
                        st.warning(f"⚠️ Delete '{pattern.get('name')}'?")
                        col_yes, col_no = st.columns(2)
                        
                        with col_yes:
                            if st.button("✅ Yes", key=f"confirm_yes_{pattern_idx}"):
                                delete_pattern(pattern.get('id'), pattern.get('name'))
                                st.session_state.pop(f'confirm_delete_{pattern_idx}', None)
                                st.rerun()
                        
                        with col_no:
                            if st.button("❌ No", key=f"confirm_no_{pattern_idx}"):
                                st.session_state.pop(f'confirm_delete_{pattern_idx}', None)
                                st.rerun()
                    
                    st.markdown("---")

def delete_pattern(pattern_id, pattern_name):
    """Delete a pattern from the database."""
    api_client = get_api_client()
    
    with st.spinner(f"Deleting pattern '{pattern_name}'..."):
        try:
            response = api_client.delete_fraud_pattern(pattern_id)
            if response:
                st.success(f"✅ Pattern '{pattern_name}' deleted successfully!")
                # Refresh patterns from API
                updated_patterns = api_client.get_fraud_patterns()
                if updated_patterns is not None:
                    st.session_state.fraud_patterns = updated_patterns
            else:
                st.error("❌ Failed to delete pattern. Please check API connection.")
        except Exception as e:
            st.error(f"❌ Error deleting pattern: {str(e)}")

def add_pattern_form():
    """Form to add a new fraud pattern."""
    with st.form(key="add_pattern_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            pattern_name = st.text_input("Pattern Name*", placeholder="e.g., High Amount Online Purchase")
            fraud_type = st.selectbox(
                "Fraud Type*",
                ["Card Not Present", "ATM Fraud", "Online Fraud", "POS Fraud", "Account Takeover", "Identity Theft", "Other"]
            )
            merchant_category = st.text_input("Merchant Category", placeholder="e.g., Electronics, Gas Station")
        
        with col2:
            similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.75, 0.05)
            transaction_type = st.selectbox("Transaction Type", ["online", "offline", "atm", "pos", "other"])
            amount_threshold = st.number_input("Amount Threshold ($)", min_value=0.0, value=1000.0, step=50.0)
        
        pattern_description = st.text_area("Description*", placeholder="Describe the fraud pattern...")
        
        # Pattern details as JSON
        st.markdown("**Pattern Indicators (JSON)**")
        default_pattern = {
            "fraud_type": fraud_type if fraud_type else "Other",
            "merchant_category": merchant_category if merchant_category else "Unknown",
            "transaction_type": transaction_type,
            "amount_threshold": amount_threshold,
            "indicators": ["high_amount", "unusual_location"],
            "risk_factors": ["new_device", "velocity_check"]
        }
        
        pattern_details = st.text_area(
            "Pattern Details",
            value=json.dumps(default_pattern, indent=2),
            height=150,
            help="JSON format describing the fraud pattern"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("💾 Add Pattern", type="primary")
        with col2:
            cancel_button = st.form_submit_button("❌ Cancel")
        
        if cancel_button:
            st.session_state.show_add_form = False
            st.rerun()
        
        if submit_button:
            if not pattern_name or not pattern_description:
                st.error("❌ Please fill in all required fields (marked with *).")
                return
            
            try:
                # Validate JSON
                pattern_json = json.loads(pattern_details)
                pattern_json["fraud_type"] = fraud_type  # Ensure consistency
                
                # Create new pattern
                new_pattern = {
                    "name": pattern_name,
                    "description": pattern_description,
                    "pattern": pattern_json,
                    "similarity_threshold": similarity_threshold
                }
                
                # Submit to API
                api_client = get_api_client()
                with st.spinner("Adding new pattern..."):
                    response = api_client.add_fraud_pattern(new_pattern)
                    
                    if response:
                        st.success(f"✅ Pattern '{pattern_name}' added successfully!")
                        # Refresh patterns
                        updated_patterns = api_client.get_fraud_patterns()
                        if updated_patterns is not None:
                            st.session_state.fraud_patterns = updated_patterns
                        st.session_state.show_add_form = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to add pattern. Please check API connection.")
                        
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON format: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error adding pattern: {str(e)}")

def show_pattern_details_popup(pattern):
    """Show pattern details in a popup-style modal."""
    st.markdown("---")
    st.markdown(f"## 👁️ Pattern Details: {pattern.get('name', 'Unknown')}")
    
    # Basic information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pattern ID", pattern.get('id', 'Unknown'))
        st.metric("Similarity Threshold", f"{pattern.get('similarity_threshold', 0.0):.2f}")
    with col2:
        st.metric("Fraud Type", pattern.get('pattern', {}).get('fraud_type', 'Unknown'))
        st.metric("Created Date", pattern.get('created_at', 'Unknown')[:10] if pattern.get('created_at') else 'Unknown')
    with col3:
        st.metric("Merchant Category", pattern.get('pattern', {}).get('merchant_category', 'Unknown'))
        st.metric("Transaction Type", pattern.get('pattern', {}).get('transaction_type', 'Unknown'))
    
    # Description
    st.markdown("### 📝 Description")
    st.markdown(pattern.get('description', 'No description available'))
    
    # Pattern details
    st.markdown("### 🔍 Pattern Configuration")
    pattern_data = pattern.get('pattern', {})
    
    # Display as formatted JSON
    st.json(pattern_data)
    
    # Pattern metrics (simulated for demo)
    st.markdown("### 📊 Pattern Performance")
    col1, col2, col3, col4 = st.columns(4)
    
    # Generate consistent demo metrics based on pattern properties
    pattern_hash = hash(pattern.get('id', '') + pattern.get('name', '')) % 1000
    matched_transactions = abs(pattern_hash) % 500 + 10
    false_positives = max(1, int(matched_transactions * (1 - pattern.get('similarity_threshold', 0.8))))
    effectiveness = round((matched_transactions - false_positives) / matched_transactions * 100, 1)
    
    with col1:
        st.metric("Matched Transactions", matched_transactions)
    with col2:
        st.metric("False Positives", false_positives)
    with col3:
        st.metric("Effectiveness", f"{effectiveness}%")
    with col4:
        st.metric("Last Used", "2 days ago")  # Demo data
    
    # Action buttons
    st.markdown("### Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✏️ Edit Pattern", type="primary"):
            st.session_state['editing_pattern'] = pattern
            st.session_state.pop('viewing_pattern', None)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Delete Pattern", type="secondary"):
            st.session_state[f'confirm_delete_view'] = True
            st.rerun()
    
    with col3:
        if st.button("❌ Close", help="Close details view"):
            st.session_state.pop('viewing_pattern', None)
            st.rerun()
    
    # Delete confirmation for view mode
    if st.session_state.get('confirm_delete_view', False):
        st.markdown("---")
        st.warning(f"⚠️ **Are you sure you want to delete '{pattern.get('name')}'?**")
        st.markdown("This action cannot be undone and will permanently remove the pattern from the database.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Delete Permanently", type="primary"):
                delete_pattern(pattern.get('id'), pattern.get('name'))
                st.session_state.pop('viewing_pattern', None)
                st.session_state.pop('confirm_delete_view', None)
                st.rerun()
        with col2:
            if st.button("❌ Cancel Deletion"):
                st.session_state.pop('confirm_delete_view', None)
                st.rerun()

def edit_pattern_popup(pattern):
    """Show edit form in a popup-style interface."""
    st.markdown("---")
    st.markdown(f"## ✏️ Edit Pattern: {pattern.get('name', 'Unknown')}")
    
    with st.form(key="edit_pattern_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            pattern_name = st.text_input("Pattern Name*", value=pattern.get('name', ''))
            current_fraud_type = pattern.get('pattern', {}).get('fraud_type', 'Other')
            fraud_type = st.selectbox(
                "Fraud Type*",
                ["Card Not Present", "ATM Fraud", "Online Fraud", "POS Fraud", "Account Takeover", "Identity Theft", "Other"],
                index=["Card Not Present", "ATM Fraud", "Online Fraud", "POS Fraud", "Account Takeover", "Identity Theft", "Other"].index(current_fraud_type) if current_fraud_type in ["Card Not Present", "ATM Fraud", "Online Fraud", "POS Fraud", "Account Takeover", "Identity Theft", "Other"] else 6
            )
            merchant_category = st.text_input("Merchant Category", value=pattern.get('pattern', {}).get('merchant_category', ''))
        
        with col2:
            similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, pattern.get('similarity_threshold', 0.75), 0.05)
            current_trans_type = pattern.get('pattern', {}).get('transaction_type', 'other')
            transaction_type = st.selectbox(
                "Transaction Type", 
                ["online", "offline", "atm", "pos", "other"],
                index=["online", "offline", "atm", "pos", "other"].index(current_trans_type) if current_trans_type in ["online", "offline", "atm", "pos", "other"] else 4
            )
            amount_threshold = st.number_input("Amount Threshold ($)", min_value=0.0, value=pattern.get('pattern', {}).get('amount_threshold', 1000.0), step=50.0)
        
        pattern_description = st.text_area("Description*", value=pattern.get('description', ''))
        
        # Pattern details as JSON
        st.markdown("**Pattern Configuration (JSON)**")
        current_pattern = pattern.get('pattern', {})
        current_pattern.update({
            "fraud_type": fraud_type,
            "merchant_category": merchant_category,
            "transaction_type": transaction_type,
            "amount_threshold": amount_threshold
        })
        
        pattern_details = st.text_area(
            "Pattern Details",
            value=json.dumps(current_pattern, indent=2),
            height=150,
            help="JSON format describing the fraud pattern"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            save_button = st.form_submit_button("💾 Save Changes", type="primary")
        with col2:
            cancel_button = st.form_submit_button("❌ Cancel")
        with col3:
            preview_button = st.form_submit_button("👁️ Preview")
        
        if cancel_button:
            st.session_state.pop('editing_pattern', None)
            st.rerun()
        
        if preview_button:
            st.markdown("### 👁️ Preview")
            try:
                preview_pattern = json.loads(pattern_details)
                st.json(preview_pattern)
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {str(e)}")
        
        if save_button:
            if not pattern_name or not pattern_description:
                st.error("❌ Please fill in all required fields (marked with *).")
                return
            
            try:
                # Validate JSON
                pattern_json = json.loads(pattern_details)
                pattern_json["fraud_type"] = fraud_type  # Ensure consistency
                
                # Create updated pattern
                updated_pattern = {
                    "id": pattern.get('id'),
                    "name": pattern_name,
                    "description": pattern_description,
                    "pattern": pattern_json,
                    "similarity_threshold": similarity_threshold
                }
                
                # Submit to API
                api_client = get_api_client()
                with st.spinner("Updating pattern..."):
                    response = api_client.update_fraud_pattern(pattern.get('id'), updated_pattern)
                    
                    if response:
                        st.success(f"✅ Pattern '{pattern_name}' updated successfully!")
                        # Refresh patterns
                        updated_patterns = api_client.get_fraud_patterns()
                        if updated_patterns is not None:
                            st.session_state.fraud_patterns = updated_patterns
                        st.session_state.pop('editing_pattern', None)
                        st.rerun()
                    else:
                        st.error("❌ Failed to update pattern. Please check API connection.")
                        
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON format: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error updating pattern: {str(e)}")

def show_fraud_patterns():
    """Main function for the fraud patterns page with enhanced UI."""
    # Apply custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .action-button {
        margin: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-header'>🔐 Fraud Pattern Management System</h1>", unsafe_allow_html=True)
    
    # Check for different UI states
    if 'editing_pattern' in st.session_state:
        edit_pattern_popup(st.session_state['editing_pattern'])
    elif 'viewing_pattern' in st.session_state:
        show_pattern_details_popup(st.session_state['viewing_pattern'])
    else:
        # Show main patterns management interface
        display_fraud_patterns()
        
        # Quick stats section
        if st.session_state.get('fraud_patterns'):
            st.markdown("---")
            st.markdown("### 📊 Quick Statistics")
            
            patterns = st.session_state.fraud_patterns
            total_patterns = len(patterns)
            fraud_types = set(p.get('pattern', {}).get('fraud_type', 'Unknown') for p in patterns)
            avg_threshold = sum(p.get('similarity_threshold', 0) for p in patterns) / max(total_patterns, 1)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Patterns", total_patterns)
            with col2:
                st.metric("Fraud Types", len(fraud_types))
            with col3:
                st.metric("Avg. Threshold", f"{avg_threshold:.2f}")
            with col4:
                st.metric("Active Filters", "✅" if st.session_state.search_term or st.session_state.fraud_type_filter != "All" else "❌")