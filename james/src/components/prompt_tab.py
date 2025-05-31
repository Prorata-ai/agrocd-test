"""
Prompt Tab component for the Gist Analytics Dashboard
"""

import streamlit as st
import pandas as pd
from .turn_details import render_turn_details_section
from .export import render_export_section
from ..utils.data_processing import get_turns_data, process_turns_data_with_citations


def render_prompt_tab(page_size, offset, date_filter, total_turns, page_number, max_pages):
    """Render the Prompts tab with turns table, details, and export functionality"""
    
    turns_data, query_time = get_turns_data(
        limit=page_size, 
        offset=offset,
        date_filter=date_filter
    )

    # Display info about the data
    if total_turns == 0:
        st.markdown(
            f"<p class='data-info'>No records found in database. Query time: {query_time:.2f}s</p>", 
            unsafe_allow_html=True
        )
    else:
        start_record = offset + 1
        end_record = min(offset + len(turns_data), total_turns)
        st.markdown(
            f"<p class='data-info'>Showing records {start_record}-{end_record} of {total_turns} total (page {page_number} of {max_pages}). "
            f"Query time: {query_time:.2f}s</p>", 
            unsafe_allow_html=True
        )

    if not turns_data.empty:
        # Process turns data and add citations
        turns_data, all_citation_details = process_turns_data_with_citations(turns_data)
        
        # Show the turns table
        st.dataframe(turns_data, use_container_width=True)
        
        # Turn details section
        render_turn_details_section(turns_data, all_citation_details)
        
        # Export section
        render_export_section(turns_data, all_citation_details)
    else:
        st.info("No turns data available for the selected filters")
        
        # Show empty export section
        render_export_section(pd.DataFrame(), {}) 