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

# Copy requirements file
COPY requirements-docker.txt .

# Install all required packages
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy all necessary application code
COPY src ./src
COPY config ./config

# Expose both ports (7860 for Hugging Face, 8050 for local)
EXPOSE 7860 8050

# Run the application with Gunicorn for production deployment
# The command will determine the correct port based on environment
CMD ["sh", "-c", "if [ -n \"$HF_SPACE\" ]; then PORT=7860; fi && gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 60 src.folio.app:server"]
