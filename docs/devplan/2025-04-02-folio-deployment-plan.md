# Folio Deployment Plan

**Date:** 2025-04-02  
**Author:** CTO  
**Status:** Draft  

## Executive Summary

The Folio app is a web-based dashboard built with Python, Dash, and related libraries that provides portfolio analysis and visualization. This deployment plan outlines several options for deploying the application, with recommendations based on needs for scalability, ease of maintenance, and cost-effectiveness.

## Application Overview

**Technology Stack:**
- **Backend**: Python 3.9+
- **Web Framework**: Dash (2.14.2)
- **UI Components**: Dash Bootstrap Components (1.5.0)
- **Data Processing**: Pandas, NumPy
- **Data Sources**: yfinance API (default), FMP API (alternative)
- **Dependencies**: Listed in requirements.txt

**Key Application Characteristics:**
- Web-based dashboard with interactive UI
- Periodic data refreshing (5-minute intervals)
- CSV file upload functionality
- External API dependencies for financial data
- Configuration via YAML files
- Environment variable requirements (API keys)

## Deployment Options

### Option 1: Traditional VPS/VM Deployment

**Description:** Deploy the application on a Virtual Private Server (VPS) or Virtual Machine (VM) from providers like DigitalOcean, AWS EC2, Google Compute Engine, or Linode.

**Implementation Steps:**
1. Provision a VPS with at least 2GB RAM, 1 vCPU
2. Install Python 3.9+ and required system dependencies
3. Clone the repository to the server
4. Set up a virtual environment and install dependencies
5. Configure environment variables for API keys
6. Set up a production WSGI server (Gunicorn)
7. Configure Nginx as a reverse proxy
8. Set up SSL with Let's Encrypt
9. Configure systemd service for automatic startup and restarts

**Estimated Timeline:** 1-2 days

**Pros:**
- Complete control over the environment
- Cost-effective for long-term hosting ($5-20/month)
- Ability to customize server configuration
- Good performance with proper setup

**Cons:**
- Manual setup and maintenance required
- Responsibility for security updates and patches
- No built-in scalability

### Option 2: Containerized Deployment with Docker

**Description:** Package the application as a Docker container and deploy to container hosting services like AWS ECS, Google Cloud Run, or Azure Container Instances.

**Implementation Steps:**
1. Create a Dockerfile for the application:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8050

# Expose the port
EXPOSE 8050

# Run the application with Gunicorn
CMD gunicorn --workers 2 --threads 2 --timeout 60 --bind 0.0.0.0:$PORT "src.folio.__main__:create_app()"
```

2. Build and test the Docker image locally
3. Set up a container registry (Docker Hub, AWS ECR, etc.)
4. Push the image to the registry
5. Deploy to your chosen container platform
6. Configure environment variables for API keys
7. Set up networking and domain mapping

**Estimated Timeline:** 2-3 days

**Pros:**
- Consistent environment across development and production
- Easier deployment and updates
- Better isolation and security
- Scalable with container orchestration
- Portable across different hosting providers

**Cons:**
- Slightly higher learning curve if new to containers
- May have higher costs for managed container services
- Additional complexity in configuration

### Option 3: Platform as a Service (PaaS)

**Description:** Deploy the application to a PaaS provider like Heroku, Render, or Fly.io that handles infrastructure management.

**Implementation Steps:**
1. Create configuration files for your chosen platform (e.g., Procfile for Heroku)
2. Set up the application on the platform
3. Configure environment variables
4. Deploy the application
5. Set up custom domain and SSL

**Example Procfile for Heroku:**
```
web: gunicorn src.folio.__main__:create_app() --workers 2 --threads 2 --timeout 60
```

**Estimated Timeline:** 1 day

**Pros:**
- Simplest deployment process
- Managed infrastructure (no server maintenance)
- Built-in scaling capabilities
- Integrated monitoring and logging
- Quick setup and deployment

**Cons:**
- Higher cost for long-term hosting
- Less control over the environment
- Potential limitations with free tiers
- May have cold starts with some providers

### Option 4: Serverless Deployment

**Description:** Deploy the application as a serverless function using AWS Lambda with API Gateway, Google Cloud Functions, or Azure Functions.

**Note:** This option requires some adaptation of the Dash application to work in a serverless environment, which may be challenging due to the stateful nature of Dash applications.

**Implementation Steps:**
1. Adapt the application for serverless architecture
2. Package the application with dependencies
3. Configure API Gateway or equivalent
4. Set up environment variables
5. Deploy the function
6. Configure domain and SSL

**Estimated Timeline:** 3-4 days

**Pros:**
- Pay only for actual usage
- Automatic scaling
- No server management
- High availability

**Cons:**
- Complex adaptation required for Dash apps
- Cold start issues
- Limited execution time
- Not ideal for applications with persistent connections

## Recommendation

Based on the nature of the Folio application and its requirements, I recommend **Option 2: Containerized Deployment with Docker** for the following reasons:

1. **Consistency:** Docker ensures the application runs the same way in all environments
2. **Portability:** Easy to move between different hosting providers
3. **Scalability:** Can start small and scale as needed
4. **Maintenance:** Simplified updates and deployments
5. **Cost-effectiveness:** Various hosting options at different price points

For initial deployment, I recommend using a simple container hosting service like:
- **Google Cloud Run:** Serverless container platform with pay-per-use pricing
- **DigitalOcean App Platform:** Simple container deployment with reasonable pricing
- **AWS App Runner:** Fully managed container service with automatic scaling

## Implementation Plan

### Phase 1: Containerization (1-2 days)
1. Create Dockerfile and docker-compose.yml
2. Test building and running the container locally
3. Document container configuration and environment variables

### Phase 2: CI/CD Setup (1 day)
1. Set up GitHub Actions or similar CI/CD pipeline
2. Configure automated testing
3. Set up automated builds and deployments

### Phase 3: Production Deployment (1 day)
1. Choose and set up hosting provider
2. Configure environment variables and secrets
3. Deploy the application
4. Set up monitoring and logging

### Phase 4: Post-Deployment (1 day)
1. Configure custom domain and SSL
2. Set up backup procedures
3. Document deployment process
4. Create monitoring alerts

## Additional Considerations

### Data Persistence
- The application currently uses local file uploads for portfolios
- Consider adding cloud storage (S3, GCS) for persistent portfolio storage

### Security
- Secure API keys using environment variables or secret management
- Implement proper authentication if the app will be publicly accessible
- Consider rate limiting for API calls

### Monitoring
- Set up application monitoring (New Relic, Datadog, etc.)
- Configure alerts for application errors or performance issues
- Monitor API usage to avoid hitting rate limits

### Cost Optimization
- Start with a minimal deployment and scale as needed
- Consider reserved instances for long-term cost savings
- Monitor and optimize resource usage

## Conclusion

The Folio application is well-suited for containerized deployment, which offers a good balance of flexibility, maintainability, and cost-effectiveness. Starting with a Docker-based deployment provides a solid foundation that can be adapted to different hosting providers as your needs evolve.
