# Docker Setup for Folio

This document provides instructions for running the Folio application using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Quick Start

1. **Create a .env file** (optional)

   Copy the example environment file if you want to customize settings:

   ```bash
   cp .env.example .env
   # Edit .env to customize settings if needed
   ```

   Note: Since we're using yfinance as the default data source, no API keys are required.

2. **Build and run with Docker Compose**

   ```bash
   # Build and start the container in detached mode
   make docker-compose-up

   # Or use docker-compose directly
   docker-compose up -d
   ```

3. **Access the application**

   Open your browser and navigate to:

   ```
   http://localhost:8050
   ```

4. **Stop the application**

   ```bash
   make docker-compose-down

   # Or use docker-compose directly
   docker-compose down
   ```

## Manual Docker Commands

If you prefer to use Docker directly without Docker Compose:

1. **Build the Docker image**

   ```bash
   make docker-build

   # Or use docker directly
   docker build -t folio:latest .
   ```

2. **Run the Docker container**

   ```bash
   make docker-run

   # Or use docker directly
   docker run -p 8050:8050 --env-file .env folio:latest
   ```

## Troubleshooting

- **Port conflicts**: If port 8050 is already in use, modify the `PORT` environment variable in your `.env` file and update the port mapping in `docker-compose.yml`.

- **Data source issues**: By default, the application uses yfinance as the data source. If you want to use FMP instead, you'll need to set the FMP_API_KEY in your `.env` file and change DATA_SOURCE to 'fmp'.

- **Volume mounting**: If you're making changes to the code and want to see them reflected immediately, ensure the volumes in `docker-compose.yml` are correctly mapping your local directories.

- **Dependencies**: The Docker image uses `requirements-docker.txt` for its dependencies. If you need to add or update dependencies, modify this file instead of editing the Dockerfile directly.

## Next Steps

After successfully running the application locally with Docker, you can consider:

1. Setting up CI/CD with GitHub Actions
2. Deploying to a hosting platform like Hugging Face Spaces
3. Implementing additional Docker configurations for production environments
