"""
Streamlit CSS styling configuration for the Gist Analytics Dashboard
"""

def get_dashboard_styles():
    """Return the CSS styles for the dashboard"""
    return """
    <style>
        .main-header {
            font-size: 2.5rem;
            margin-bottom: 20px;
        }
        .section-header {
            font-size: 1.5rem;
            margin-bottom: 10px;
        }
        .data-info {
            font-size: 1rem;
            font-style: italic;
            color: #888;
        }
        .stAlert {
            background-color: #f8f9fa;
        }
        /* More specific targeting for metric values */
        [data-testid="metric-container"] {
            font-size: 0.9rem !important;
        }
        [data-testid="metric-container"] [data-testid="metric-value"] {
            font-size: 1rem !important;
            font-weight: 600 !important;
        }
        [data-testid="metric-container"] [data-testid="metric-label"] {
            font-size: 0.8rem !important;
            color: #666 !important;
        }
        /* Alternative targeting for metric containers */
        .metric-container {
            font-size: 0.9rem !important;
        }
        .metric-container > div {
            font-size: 0.9rem !important;
        }
        /* Target the actual metric value text */
        div[data-testid="metric-container"] > div > div {
            font-size: 1rem !important;
        }
        /* Reduce overall metric component size */
        .stMetric {
            font-size: 0.9rem !important;
        }
        .stMetric > div {
            font-size: 0.9rem !important;
        }
    </style>
    """ 