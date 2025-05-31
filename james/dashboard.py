"""
Gist Analytics Dashboard - Main Application with Keycloak Authentication
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
from src.auth.keycloak_auth_simple import SimpleKeycloakAuth, simple_require_authentication, simple_render_user_info

# Import our modular components
from src.config.styles import get_dashboard_styles
from src.utils.data_processing import get_filtered_turn_count
from src.components.tab_sidebar import render_tab_sidebar
from src.components.top_controls import render_top_controls
from src.components.prompt_tab import render_prompt_tab
from src.components.distributions_tab import render_distributions_tab
from src.components.trends_tab import render_trends_tab, get_trends_date_filter_options

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Gist Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Apply styling
st.markdown(get_dashboard_styles(), unsafe_allow_html=True)

# Initialize Keycloak authentication
try:
    auth = SimpleKeycloakAuth()
    
    # Require authentication - this will redirect to login if not authenticated
    user_info = simple_require_authentication(auth)
    
    # If we reach here, user is authenticated
    st.success(f"Welcome, {user_info.get('name', user_info.get('preferred_username', 'User'))}! 👋")
    
except ValueError as e:
    st.error(f"Authentication configuration error: {str(e)}")
    st.info("Please check your Keycloak environment variables in the .env file")
    st.stop()
except Exception as e:
    st.error(f"Authentication error: {str(e)}")
    st.stop()

# Render sidebar with tab selection
selected_tab = render_tab_sidebar()

# Render user info and logout button in sidebar
simple_render_user_info(auth)

# For Prompts tab, we need controls and data processing
if selected_tab == "Prompts":
    # We need to handle the controls for the Prompts tab
    # First get a rough count for initial controls rendering
    total_turns_initial = get_filtered_turn_count(None)  # Get total count first
    
    # Render top controls
    controls = render_top_controls(total_turns_initial)
    selected_date_filter = controls['selected_date_filter']
    date_filter = controls['date_filter']
    
    # Get the actual filtered count
    total_turns = get_filtered_turn_count(date_filter)
    
    # Re-render controls with correct total if needed (but avoid duplicate widgets)
    if total_turns != total_turns_initial:
        # Update the controls with correct total, but we'll use the existing values
        page_size = controls['page_size']
        page_number = controls['page_number']
        offset = controls['offset']
        max_pages = (total_turns + page_size - 1) // page_size if total_turns > 0 else 1
    else:
        page_size = controls['page_size']
        page_number = controls['page_number']
        max_pages = controls['max_pages']
        offset = controls['offset']
    
    # Render the Prompts tab
    render_prompt_tab(page_size, offset, date_filter, total_turns, page_number, max_pages)

elif selected_tab == "Distributions":
    # For Distributions tab, we only need date filter
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        from src.components.top_controls import get_date_filter_options
        date_filter_options = get_date_filter_options()
        selected_date_filter = st.selectbox(
            "Time period",
            options=list(date_filter_options.keys()),
            index=3,
            key="distributions_date_filter"
        )
        date_filter = date_filter_options[selected_date_filter]
    
    # Render the Distributions tab
    render_distributions_tab(selected_date_filter, date_filter)

elif selected_tab == "Trends":
    # For Trends tab, we need a different set of date filter options
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trends_date_filter_options = get_trends_date_filter_options()
        selected_date_filter = st.selectbox(
            "Time period",
            options=list(trends_date_filter_options.keys()),
            index=3,  # Default to "All time"
            key="trends_date_filter"
        )
        date_filter = trends_date_filter_options[selected_date_filter]
    
    # Render the Trends tab
    render_trends_tab(selected_date_filter, date_filter)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center'>PrtGist Analytics Dashboard © 2025 | Secured with Keycloak</p>", unsafe_allow_html=True) 