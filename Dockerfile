FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8050

# Install only the necessary system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install all required packages
RUN pip install --no-cache-dir \
    dash==2.14.2 \
    dash-bootstrap-components==1.5.0 \
    yfinance>=0.2.37 \
    PyYAML==6.0.1 \
    requests==2.31.0 \
    scipy>=1.11.0 \
    pandas==2.2.1 \
    numpy==1.26.4

# Copy all necessary application code
COPY src ./src

# Expose the port
EXPOSE 8050

# Run the application with Python directly
CMD ["python", "-m", "src.folio.app", "--port", "8050", "--host", "0.0.0.0"]
