"""
Export components for the Gist Analytics Dashboard
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO


def render_csv_export(turns_data):
    """Render CSV export button"""
    if not turns_data.empty:
        csv = turns_data.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"gist_analytics_turns_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


def render_excel_export(turns_data, all_citation_details):
    """Render Excel export button with multiple sheets"""
    if not turns_data.empty:
        # Create Excel file in memory using BytesIO
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            turns_data.to_excel(writer, sheet_name='Turns', index=False)
            
            # If we have citation data, add it as a separate sheet
            if 'Citations' in turns_data.columns and turns_data['Citations'].sum() > 0:
                all_citations = pd.DataFrame()
                for i, row in turns_data.iterrows():
                    if row['Citations'] > 0:
                        citations = all_citation_details.get((row['Thread ID'], row['Turn Index']), pd.DataFrame())
                        if not citations.empty:
                            citations['Thread ID'] = row['Thread ID']
                            citations['Turn Index'] = row['Turn Index']
                            all_citations = pd.concat([all_citations, citations])
                
                if not all_citations.empty:
                    all_citations.to_excel(writer, sheet_name='Citations', index=False)
        
        output.seek(0)
        st.download_button(
            label="Download as Excel",
            data=output.getvalue(),
            file_name=f"gist_analytics_turns_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


def render_export_section(turns_data, all_citation_details):
    """Render the complete export section"""
    st.markdown("<h2 class='section-header'>Export Data</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        render_csv_export(turns_data)

    with col2:
        render_excel_export(turns_data, all_citation_details) 