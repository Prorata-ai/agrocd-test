"""
Chart components for the Gist Analytics Dashboard
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def render_daily_turns_chart(daily_turns, selected_date_filter, date_filter):
    """Render the daily turns over time chart"""
    if not daily_turns.empty:
        # Create dynamic title based on date filter
        if date_filter is None:
            chart_title = "Daily Turns Count (All Time)"
        elif selected_date_filter == "Last 24 hours":
            chart_title = "Daily Turns Count (Last 24 Hours)"
        elif selected_date_filter == "Last 7 days":
            chart_title = "Daily Turns Count (Last 7 Days)"
        elif selected_date_filter == "Last 30 days":
            chart_title = "Daily Turns Count (Last 30 Days)"
        else:
            chart_title = f"Daily Turns Count ({selected_date_filter})"
            
        fig = px.line(
            daily_turns, 
            x='Day', 
            y='Count', 
            title=chart_title,
            labels={'Count': 'Number of Turns', 'Day': 'Date'},
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No daily turns data available")


def render_response_types_chart(response_types):
    """Render the response types distribution pie chart"""
    if not response_types.empty:
        fig = px.pie(
            response_types, 
            values='Count', 
            names='Response Type',
            title='Distribution of Response Types'
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No response type data available")


def render_citation_scores_chart(citations):
    """Render citation scores bar chart"""
    if 'Score' in citations.columns and len(citations) > 0:
        fig = px.bar(
            citations, 
            x='Domain', 
            y='Score',
            title='Citation Scores by Domain',
            labels={'Score': 'Attribution Score', 'Domain': 'Website Domain'},
            color='Score'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Citation data available but cannot create chart (missing score data)")


def render_citations_per_prompt_chart(data):
    """Render citations per prompt pie chart"""
    if not data.empty:
        fig = px.pie(
            data, 
            values='Count', 
            names='Citation Group',
            title='Citations per Prompt',
            category_orders={'Citation Group': data['Citation Group'].tolist()}  # Preserve DataFrame order
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No citations per prompt data available")


def render_length_distribution_chart(data):
    """Render response length distribution pie chart"""
    if not data.empty:
        fig = px.pie(
            data, 
            values='Count', 
            names='Length Group',
            title='Response Length',
            category_orders={'Length Group': data['Length Group'].tolist()}  # Preserve DataFrame order
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No length distribution data available")


def render_sections_per_prompt_chart(data):
    """Render sections per prompt pie chart"""
    if not data.empty:
        fig = px.pie(
            data, 
            values='Count', 
            names='Sections Group',
            title='Sections per Prompt',
            category_orders={'Sections Group': data['Sections Group'].tolist()}  # Preserve DataFrame order
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sections per prompt data available")


def render_turns_per_thread_chart(data):
    """Render turns per thread pie chart"""
    if not data.empty:
        fig = px.pie(
            data, 
            values='Count', 
            names='Turns Group',
            title='Turns per Thread Distribution',
            category_orders={'Turns Group': data['Turns Group'].tolist()}  # Preserve DataFrame order
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No turns per thread data available") 