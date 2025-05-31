"""
Distributions Tab component for the Gist Analytics Dashboard
"""

import streamlit as st
from .charts import (
    render_citations_per_prompt_chart, render_length_distribution_chart,
    render_sections_per_prompt_chart, render_turns_per_thread_chart
)
from ..utils.data_processing import (
    get_citations_per_prompt_distribution, get_length_distribution,
    get_sections_per_prompt_distribution, get_turns_per_thread_distribution
)


def render_distributions_tab(selected_date_filter, date_filter):
    """Render the Distributions tab with analytics pie charts in two columns"""
    
    # Create two columns for the analytics
    col1, col2 = st.columns(2)

    with col1:
        # Citations per prompt
        citations_data = get_citations_per_prompt_distribution()
        render_citations_per_prompt_chart(citations_data)
        
        # Length distribution
        length_data = get_length_distribution()
        render_length_distribution_chart(length_data)
        
    with col2:
        # Turns per thread
        turns_data = get_turns_per_thread_distribution()
        render_turns_per_thread_chart(turns_data)

        # Sections per prompt
        sections_data = get_sections_per_prompt_distribution()
        render_sections_per_prompt_chart(sections_data) 