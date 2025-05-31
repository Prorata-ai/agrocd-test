"""
Top controls component for the Gist Analytics Dashboard
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


def render_top_controls(total_turns):
    """Render the top controls section with filters and pagination"""
    # Create columns for controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Date filter
        date_filter_options = get_date_filter_options()
        selected_date_filter = st.selectbox(
            "Time period",
            options=list(date_filter_options.keys()),
            index=3,
            key="top_date_filter"
        )
        date_filter = date_filter_options[selected_date_filter]
    
    with col2:
        # Page size
        page_size = st.selectbox(
            "Items per page", 
            [10, 25, 50, 100], 
            index=1,
            key="top_page_size"
        )
    
    with col3:
        # Custom pagination with arrow buttons - right aligned
        if total_turns == 0:
            max_pages = 1
            page_number = 1
            st.info("No data available")
        else:
            max_pages = (total_turns + page_size - 1) // page_size  # Ceiling division
            
            # Initialize page number in session state if not exists
            if "top_page_number" not in st.session_state:
                st.session_state.top_page_number = 1
            
            # Ensure page number is within valid range
            if st.session_state.top_page_number > max_pages:
                st.session_state.top_page_number = max_pages
            if st.session_state.top_page_number < 1:
                st.session_state.top_page_number = 1
            
            # Create right-aligned pagination controls
            st.markdown(
                """
                <div style="display: flex; justify-content: flex-end; align-items: center; margin-top: 25px;">
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
            
            with nav_col1:
                if st.button("◀", key="top_prev_page", disabled=(st.session_state.top_page_number <= 1)):
                    st.session_state.top_page_number -= 1
                    st.rerun()
            
            with nav_col2:
                st.markdown(
                    f"<div style='text-align: center;'>Page {st.session_state.top_page_number} of {max_pages}</div>", 
                    unsafe_allow_html=True
                )
            
            with nav_col3:
                if st.button("▶", key="top_next_page", disabled=(st.session_state.top_page_number >= max_pages)):
                    st.session_state.top_page_number += 1
                    st.rerun()
            
            page_number = st.session_state.top_page_number
        
        offset = (page_number - 1) * page_size
    
    with col4:
        # Display current page info with smaller font
        if total_turns > 0:
            start_record = offset + 1
            end_record = min(offset + page_size, total_turns)
    
    return {
        'selected_date_filter': selected_date_filter,
        'date_filter': date_filter,
        'page_size': page_size,
        'page_number': page_number,
        'max_pages': max_pages,
        'offset': offset
    } 