"""
Turn details components for the Gist Analytics Dashboard
"""

import streamlit as st
import pandas as pd
from .charts import render_citation_scores_chart


def render_turn_selector(turns_data):
    """Render the turn selector dropdown"""
    return st.selectbox(
        "Select a turn to view details:",
        options=range(len(turns_data)),
        format_func=lambda i: f"{turns_data.iloc[i]['Thread ID']} - Turn {turns_data.iloc[i]['Turn Index']}",
        key="turn_selector"
    )


def render_turn_information(selected_turn):
    """Render the comprehensive turn information including prompt and response details"""
    st.subheader("Turn Information")
    
    # Create a comprehensive DataFrame combining all turn details
    combined_data = {
        'Attribute': [
            'Thread ID',
            'Turn Index', 
            'Created At',
            'User ID',
            'Thread Title',
            'User Prompt',
            'Response Length',
            'Response Type',
            'Response Time',
            'Citations',
            'Has List',
            'Has Table'
        ],
        'Value': [
            str(selected_turn['Thread ID']),
            str(selected_turn['Turn Index']),
            str(selected_turn['Created At']),
            str(selected_turn['User ID']),
            str(selected_turn['Thread Title']) if selected_turn['Thread Title'] else "No Title",
            str(selected_turn['Prompt Text']),
            f"{selected_turn['Response Length']:,} chars",
            str(selected_turn['Response Type']),
            f"{selected_turn['Response Time (ms)']}ms",
            str(selected_turn['Citations']),
            "Yes" if selected_turn['Has List'] else "No",
            "Yes" if selected_turn['Has Table'] else "No"
        ]
    }
    
    combined_df = pd.DataFrame(combined_data)
    st.dataframe(combined_df, use_container_width=True, hide_index=True)


def render_citations_section(selected_turn, all_citation_details):
    """Render the citations section with table and chart"""
    if selected_turn['Citations'] > 0:
        st.subheader("Citations")
        citations = all_citation_details.get((selected_turn['Thread ID'], selected_turn['Turn Index']), pd.DataFrame())
        if not citations.empty:
            st.dataframe(citations)
            render_citation_scores_chart(citations)
        else:
            st.info("No citation details available for this turn")
    else:
        st.info("This turn has no citations")


def render_turn_details_section(turns_data, all_citation_details):
    """Render the complete turn details section"""
    st.markdown("<h2 class='section-header'>Turn Details</h2>", unsafe_allow_html=True)
    
    # Select a turn to view details
    selected_index = render_turn_selector(turns_data)
    
    if selected_index is not None:
        selected_turn = turns_data.iloc[selected_index]
        
        # Display comprehensive turn information
        render_turn_information(selected_turn)
        render_citations_section(selected_turn, all_citation_details) 