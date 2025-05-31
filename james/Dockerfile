FROM python:3.11-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Make port 8501 available for Streamlit
EXPOSE 8501

# Create a non-root user and switch to it
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Command to run the application
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501"]
