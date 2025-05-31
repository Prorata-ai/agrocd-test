#!/bin/bash

# Load variables from .env file
source .env

CLICKHOUSE_HOST="localhost"
CLICKHOUSE_PORT="9001"
CLICKHOUSE_DATABASE="gist_analytics"

# Run clickhouse-client with the environment variables
clickhouse-client \
    --host="$CLICKHOUSE_HOST" \
    --port="$CLICKHOUSE_PORT" \
    --user="$CLICKHOUSE_USERNAME" \
    --password="$CLICKHOUSE_PASSWORD" \
    --database="$CLICKHOUSE_DATABASE"