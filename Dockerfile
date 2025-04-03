FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
# Use PORT 7860 for Hugging Face Spaces, 8050 for local development
# The application will check for HF_SPACE environment variable to determine the environment
ENV PORT=8050
ENV HF_SPACE=1
# Set logging level to WARNING for Hugging Face deployment (for privacy reasons)
ENV LOG_LEVEL=WARNING

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

# Expose both ports (7860 for Hugging Face, 8050 for local)
EXPOSE 7860 8050

# Run the application with Python directly
# The entrypoint script will determine the correct port based on environment
CMD ["sh", "-c", "if [ -n \"$HF_SPACE\" ]; then PORT=7860; fi && python -m src.folio.app --port $PORT --host 0.0.0.0"]
