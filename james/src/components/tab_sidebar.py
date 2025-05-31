"""
Tab sidebar component for the Gist Analytics Dashboard
"""

import streamlit as st


def render_tab_sidebar():
    """Render the sidebar with an always-expanded menu using buttons with selection indicators"""
    st.sidebar.header("📊 GIST Analytics Dashboard")
    
    # Initialize session state for selected tab if not exists
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "Prompts"
    
    # Prompts button with checkmark if selected
    prompts_label = "✅ 📋 Prompts" if st.session_state.selected_tab == "Prompts" else "📋 Prompts"
    if st.sidebar.button(prompts_label, key="prompts_btn", use_container_width=True):
        st.session_state.selected_tab = "Prompts"
    
    # Distributions button with checkmark if selected
    distributions_label = "✅ 📊 Distributions" if st.session_state.selected_tab == "Distributions" else "📊 Distributions"
    if st.sidebar.button(distributions_label, key="distributions_btn", use_container_width=True):
        st.session_state.selected_tab = "Distributions"
    
    # Trends button with checkmark if selected
    trends_label = "✅ 📈 Trends" if st.session_state.selected_tab == "Trends" else "📈 Trends"
    if st.sidebar.button(trends_label, key="trends_btn", use_container_width=True):
        st.session_state.selected_tab = "Trends"
    
    return st.session_state.selected_tab 