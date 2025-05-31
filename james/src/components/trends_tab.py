"""
Trends Tab component for the Gist Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from ..utils.data_processing import get_weekly_trends_data


def get_trends_date_filter_options():
    """Get the date filter options for trends"""
    return {
        "Last week": datetime.now() - timedelta(weeks=1),
        "Last 6 months": datetime.now() - timedelta(days=180),
        "Last year": datetime.now() - timedelta(days=365),
        "All time": None
    }


def render_response_length_trend_chart(trends_data):
    """Render line chart for average response length trend"""
    if trends_data.empty:
        st.info("No data available for response length trends")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trends_data['week'],
        y=trends_data['avg_response_length'],
        mode='lines+markers',
        name='Average Response Length',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Average Response Length Over Time",
        xaxis_title="Week",
        yaxis_title="Characters",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_citations_trend_chart(trends_data):
    """Render line chart for average citations per prompt trend"""
    if trends_data.empty:
        st.info("No data available for citations trends")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trends_data['week'],
        y=trends_data['avg_citations_per_prompt'],
        mode='lines+markers',
        name='Average Citations per Prompt',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Average Citations per Prompt Over Time",
        xaxis_title="Week",
        yaxis_title="Citations",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_sections_trend_chart(trends_data):
    """Render line chart for average sections per prompt trend"""
    if trends_data.empty:
        st.info("No data available for sections trends")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trends_data['week'],
        y=trends_data['avg_sections_per_prompt'],
        mode='lines+markers',
        name='Average Sections per Prompt',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Average Sections per Prompt Over Time",
        xaxis_title="Week",
        yaxis_title="Sections",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_turns_per_thread_trend_chart(trends_data):
    """Render line chart for average turns per thread trend"""
    if trends_data.empty:
        st.info("No data available for turns per thread trends")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trends_data['week'],
        y=trends_data['avg_turns_per_thread'],
        mode='lines+markers',
        name='Average Turns per Thread',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Average Turns per Thread Over Time",
        xaxis_title="Week",
        yaxis_title="Turns",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_trends_tab(selected_date_filter, date_filter):
    """Render the Trends tab with time-based analytics in two columns"""
    
    st.header("📈 Trends Analysis")
    
    # Get trends data
    trends_data = get_weekly_trends_data(date_filter)
    
    # Create two columns for the analytics (same layout as distributions)
    col1, col2 = st.columns(2)

    with col1:
        # Citations per prompt trend
        render_citations_trend_chart(trends_data)
        
        # Response length trend
        render_response_length_trend_chart(trends_data)
        
    with col2:
        # Turns per thread trend
        render_turns_per_thread_trend_chart(trends_data)

        # Sections per prompt trend
        render_sections_trend_chart(trends_data) 