#!/bin/bash

# Set the working directory to the script location
cd "$(dirname "$0")"

# Ensure the virtual environment exists or create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install or update requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run the Streamlit app
echo "Starting dashboard..."
streamlit run dashboard.py --server.port=8501 