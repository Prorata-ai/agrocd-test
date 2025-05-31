"""
Data processing utilities for the Gist Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from ..types.turn import TurnEvent
from ..types.citation import CitationEvent
from ..clients.clickhouse_client import ClickHouseClient


@st.cache_data(ttl=300)
def get_turn_count():
    """Get total count of turns in the database"""
    return TurnEvent.get_count()


@st.cache_data(ttl=300)
def get_turns_data(limit=50, offset=0, date_filter=None):
    """Get turns data with pagination and optional date filter"""
    start_time = time.time()
    result = TurnEvent.get_turns_data(limit=limit, offset=offset, date_filter=date_filter)
    query_time = time.time() - start_time
    
    # Convert to DataFrame
    columns = [
        'Thread ID', 'Turn Index', 'Created At', 'User ID', 'Prompt Text', 
        'Response Length', 'Response Type', 'Has List', 'Has Table', 
        'Response Time (ms)', 'Thread Title'
    ]
    
    df = pd.DataFrame(result, columns=columns)
    
    # Format the date
    if not df.empty:
        df['Created At'] = pd.to_datetime(df['Created At'])
        df['Created At'] = df['Created At'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return df, query_time


@st.cache_data(ttl=300)
def get_citation_count(thread_id, turn_index):
    """Get citation count for a specific turn"""
    return CitationEvent.get_count_for_turn(thread_id, turn_index)


@st.cache_data(ttl=300)
def get_citations_for_turn(thread_id, turn_index):
    """Get citations for a specific turn"""
    result = CitationEvent.get_citations_for_turn(thread_id, turn_index)
    
    # Convert to DataFrame
    columns = ['Domain', 'URL', 'Title', 'Score', 'Rank', 'Clicked']
    return pd.DataFrame(result, columns=columns)


@st.cache_data(ttl=300)
def get_daily_turns_count(days=30, date_filter=None):
    """Get count of turns by day for the last N days or from a specific date"""
    result = TurnEvent.get_daily_count(days=days, date_filter=date_filter)
    
    # Convert to DataFrame
    df = pd.DataFrame(result, columns=['Day', 'Count'])
    if not df.empty:
        df['Day'] = pd.to_datetime(df['Day'])
    
    return df


@st.cache_data(ttl=300)
def get_response_type_distribution():
    """Get distribution of response types"""
    result = TurnEvent.get_response_type_distribution()
    
    # Convert to DataFrame
    return pd.DataFrame(result, columns=['Response Type', 'Count'])


@st.cache_data(ttl=300)
def get_citations_per_prompt_distribution():
    """Get distribution of citations per prompt"""
    result = TurnEvent.get_citations_per_prompt_distribution()
    
    # Extract only the citation_group and count columns (ignore sort_order)
    processed_result = [(row[0], row[2]) for row in result]  # (citation_group, count)
    
    # Convert to DataFrame
    return pd.DataFrame(processed_result, columns=['Citation Group', 'Count'])


@st.cache_data(ttl=300)
def get_length_distribution():
    """Get distribution of response lengths"""
    result = TurnEvent.get_length_distribution()
    
    # Extract only the length_group and count columns (ignore sort_order)
    processed_result = [(row[0], row[2]) for row in result]  # (length_group, count)
    
    # Convert to DataFrame
    return pd.DataFrame(processed_result, columns=['Length Group', 'Count'])


@st.cache_data(ttl=300)
def get_sections_per_prompt_distribution():
    """Get distribution of sections per prompt"""
    result = TurnEvent.get_sections_per_prompt_distribution()
    
    # Extract only the sections_group and count columns (ignore sort_order)
    processed_result = [(row[0], row[2]) for row in result]  # (sections_group, count)
    
    # Convert to DataFrame
    return pd.DataFrame(processed_result, columns=['Sections Group', 'Count'])


@st.cache_data(ttl=300)
def get_turns_per_thread_distribution():
    """Get distribution of turns per thread"""
    result = TurnEvent.get_turns_per_thread_distribution()
    
    # Extract only the turns_group and count columns (ignore sort_order)
    processed_result = [(row[0], row[2]) for row in result]  # (turns_group, count)
    
    # Convert to DataFrame
    return pd.DataFrame(processed_result, columns=['Turns Group', 'Count'])


@st.cache_data(ttl=300)
def get_all_citation_details_batch(turn_ids_with_citations):
    """Get citation details for all turns that have citations in a single batch query"""
    if not turn_ids_with_citations:
        return {}
        
    # Use the new batch method to get all citation details at once
    raw_citation_details = CitationEvent.get_citations_batch(list(turn_ids_with_citations))
    
    # Convert to DataFrames
    citation_details = {}
    columns = ['Domain', 'URL', 'Title', 'Score', 'Rank', 'Clicked']
    
    for key, citation_list in raw_citation_details.items():
        citation_details[key] = pd.DataFrame(citation_list, columns=columns)
        
    return citation_details


def get_filtered_turn_count(date_filter):
    """Get turn count with date filter applied"""
    if date_filter:
        # For filtered data, we need to count with the same filter
        client = ClickHouseClient(
            url=os.getenv("CLICKHOUSE_URL"),
            user=os.getenv("CLICKHOUSE_USERNAME"), 
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE")
        )
        client.connect()
        try:
            formatted_date = date_filter.strftime('%Y-%m-%d %H:%M:%S')
            result = client.execute_query(f"SELECT count() FROM turn_events WHERE created_at >= '{formatted_date}'")
            return result[0][0]
        finally:
            client.close()
    else:
        return get_turn_count()


def process_turns_data_with_citations(turns_data):
    """Process turns data and add citation information"""
    if turns_data.empty:
        return turns_data, {}
    
    # Get citation counts for all turns in a single batch query
    turn_identifiers = [(row['Thread ID'], row['Turn Index']) for _, row in turns_data.iterrows()]
    citation_counts = CitationEvent.get_citation_counts_batch(turn_identifiers)
    
    # Add citation count to the turns data using the batch results
    turns_data['Citations'] = turns_data.apply(
        lambda row: citation_counts.get((row['Thread ID'], row['Turn Index']), 0), 
        axis=1
    )
    
    # Reorder columns as requested: Created At, Thread Title, Prompt Text, Response Length, Citations, then the rest, and finally User ID and Thread ID
    column_order = [
        'Created At', 'Prompt Text', 'Response Length', 'Citations',
        'Turn Index', 'Response Type', 'Has List', 'Has Table', 'Response Time (ms)',
        'Thread Title', 'Thread ID', 'User ID'
    ]
    turns_data = turns_data[column_order]
    
    # Get turns that have citations
    turns_with_citations = [
        (row['Thread ID'], row['Turn Index']) 
        for _, row in turns_data.iterrows() 
        if citation_counts.get((row['Thread ID'], row['Turn Index']), 0) > 0
    ]
    
    # Pre-load all citation details
    all_citation_details = get_all_citation_details_batch(tuple(turns_with_citations)) if turns_with_citations else {}
    
    return turns_data, all_citation_details


@st.cache_data(ttl=300)
def get_weekly_trends_data(date_filter=None):
    """Get weekly aggregated trends data for key metrics"""
    client = ClickHouseClient(
        url=os.getenv("CLICKHOUSE_URL"),
        user=os.getenv("CLICKHOUSE_USERNAME"), 
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE")
    )
    client.connect()
    
    try:
        # Build date condition
        date_condition = ""
        if date_filter:
            formatted_date = date_filter.strftime('%Y-%m-%d %H:%M:%S')
            date_condition = f"WHERE te.created_at >= '{formatted_date}'"
        
        # Query for weekly trends
        query = f"""
        WITH weekly_data AS (
            SELECT 
                toStartOfWeek(te.created_at) as week,
                te.thread_id,
                te.turn_index,
                te.response_length,
                te.response_num_sections,
                count(ce.thread_id) as citation_count
            FROM turn_events te
            LEFT JOIN citation_events ce ON te.thread_id = ce.thread_id AND te.turn_index = ce.turn_id
            {date_condition}
            GROUP BY week, te.thread_id, te.turn_index, te.response_length, te.response_num_sections
        ),
        thread_turn_counts AS (
            SELECT 
                week,
                thread_id,
                count() as turns_in_thread
            FROM weekly_data
            GROUP BY week, thread_id
        )
        SELECT 
            wd.week,
            avg(wd.response_length) as avg_response_length,
            avg(ttc.turns_in_thread) as avg_turns_per_thread,
            avg(wd.citation_count) as avg_citations_per_prompt,
            avg(wd.response_num_sections) as avg_sections_per_prompt
        FROM weekly_data wd
        JOIN thread_turn_counts ttc ON wd.week = ttc.week AND wd.thread_id = ttc.thread_id
        GROUP BY wd.week
        ORDER BY wd.week
        """
        
        result = client.execute_query(query)
        
        # Convert to DataFrame
        columns = [
            'week', 'avg_response_length', 'avg_turns_per_thread', 
            'avg_citations_per_prompt', 'avg_sections_per_prompt'
        ]
        df = pd.DataFrame(result, columns=columns)
        
        if not df.empty:
            df['week'] = pd.to_datetime(df['week'])
            # Round the averages for better display
            df['avg_response_length'] = df['avg_response_length'].round(1)
            df['avg_turns_per_thread'] = df['avg_turns_per_thread'].round(2)
            df['avg_citations_per_prompt'] = df['avg_citations_per_prompt'].round(2)
            df['avg_sections_per_prompt'] = df['avg_sections_per_prompt'].round(2)
        
        return df
        
    finally:
        client.close() 