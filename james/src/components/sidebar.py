"""
Sidebar components for the Gist Analytics Dashboard
"""

import streamlit as st
from datetime import datetime, timedelta


def get_date_filter_options():
    """Get the date filter options dictionary"""
    return {
        "Last 24 hours": datetime.now() - timedelta(days=1),
        "Last 7 days": datetime.now() - timedelta(days=7),
        "Last 30 days": datetime.now() - timedelta(days=30),
        "All time": None
    }


def render_date_filter():
    """Render the date filter selector"""
    date_filter_options = get_date_filter_options()
    selected_date_filter = st.sidebar.selectbox(
        "Time period",
        options=list(date_filter_options.keys()),
        index=3
    )
    date_filter = date_filter_options[selected_date_filter]
    
    return selected_date_filter, date_filter


def render_pagination_controls(total_turns):
    """Render pagination controls and return pagination parameters"""
    page_size = st.sidebar.selectbox("Items per page", [10, 25, 50, 100], index=1)

    # Fix pagination logic for empty database
    if total_turns == 0:
        max_pages = 1
        page_number = 1
        offset = 0
        st.sidebar.info("No data available - pagination disabled")
    else:
        max_pages = (total_turns + page_size - 1) // page_size  # Ceiling division
        
        # Initialize page number in session state if not exists
        if "sidebar_page_number" not in st.session_state:
            st.session_state.sidebar_page_number = 1
        
        # Ensure page number is within valid range
        if st.session_state.sidebar_page_number > max_pages:
            st.session_state.sidebar_page_number = max_pages
        if st.session_state.sidebar_page_number < 1:
            st.session_state.sidebar_page_number = 1
        
        # Create pagination controls
        nav_col1, nav_col2, nav_col3 = st.sidebar.columns([1, 2, 1])
        
        with nav_col1:
            if st.button("◀", key="sidebar_prev_page", disabled=(st.session_state.sidebar_page_number <= 1)):
                st.session_state.sidebar_page_number -= 1
                st.rerun()
        
        with nav_col2:
            st.markdown(
                f"<div style='text-align: center;'>Page {st.session_state.sidebar_page_number} of {max_pages}</div>", 
                unsafe_allow_html=True
            )
        
        with nav_col3:
            if st.button("▶", key="sidebar_next_page", disabled=(st.session_state.sidebar_page_number >= max_pages)):
                st.session_state.sidebar_page_number += 1
                st.rerun()
        
        page_number = st.session_state.sidebar_page_number
        offset = (page_number - 1) * page_size

    return page_size, page_number, max_pages, offset


def render_sidebar_controls(total_turns):
    """Render all sidebar controls and return their values"""
    selected_date_filter, date_filter = render_date_filter()
    page_size, page_number, max_pages, offset = render_pagination_controls(total_turns)
    
    return {
        'selected_date_filter': selected_date_filter,
        'date_filter': date_filter,
        'page_size': page_size,
        'page_number': page_number,
        'max_pages': max_pages,
        'offset': offset
    } 