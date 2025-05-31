# PrtGist Analytics Dashboard

A Streamlit dashboard for visualizing and analyzing PrtGist data from ClickHouse.

## Features

- View turns data in reverse chronological order with pagination
- Filter data by time period
- Visualize daily turns count and response type distribution
- Explore detailed information about turns and their citations
- Export data to CSV or Excel formats

## Setup

1. Install requirements:
   ```
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   Create a `.env` file with the following variables:
   ```
   CLICKHOUSE_HOST=your_clickhouse_host
   CLICKHOUSE_PORT=9000
   CLICKHOUSE_USERNAME=default
   CLICKHOUSE_PASSWORD=your_password
   CLICKHOUSE_DATABASE=your_database
   ```

3. Run the dashboard:
   ```
   streamlit run gist_analytics_dashboard.py
   ```

## Usage

The dashboard provides the following sections:

1. **Overview**: Displays key metrics including turns over time and response type distribution
2. **Recent Turns**: Paginated table of turns in reverse chronological order
3. **Turn Details**: Detailed view of a selected turn including prompt and citations
4. **Export**: Options to download the data as CSV or Excel

Use the sidebar to:
- Filter data by time period
- Adjust pagination settings

## Data Model

The dashboard uses the following ClickHouse tables:

- `thread_events`: Thread-level information
- `turn_events`: Turn-level information within threads
- `citation_events`: Citations associated with turns

These tables are expected to be populated by the PrtDocumentVerification data synchronization process. 

Pending Things To Do;
1) CICD for GIST Analytics
2) Install Clickhouse Server in Production
3) Keycloak permissions + realm
4) Deploy GIST Analytics to DevInt
5) Better handling of version progress - like Kostya does it;
6) Jobs service design
