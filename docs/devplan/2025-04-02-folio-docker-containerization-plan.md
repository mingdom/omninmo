# Folio Docker Containerization Plan

**Date:** 2025-04-02
**Author:** CTO
**Status:** Draft

## Overview

This plan details the process of containerizing the Folio portfolio dashboard application using Docker, with a focus on command-line deployment capabilities and hosting options. The containerization will enable consistent deployment across different environments and simplify the deployment process.

## Implementation Checklist

- [ ] Phase 1: Docker Configuration
- [ ] Phase 2: Local Testing
- [ ] Phase 3: CI/CD Setup
- [ ] Phase 4: Hosting Setup
- [ ] Phase 5: Command-line Deployment Tools

## Phase 1: Docker Configuration (2 days)

### 1.1 Create Dockerfile

Create a `Dockerfile` in the project root with the following configuration:

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
CMD gunicorn --workers 2 --threads 2 --timeout 60 --bind 0.0.0.0:${PORT:-8050} "src.folio.__main__:create_app()"
```

### 1.2 Create docker-compose.yml

Create a `docker-compose.yml` file for local development and testing:

```yaml
version: '3.8'

services:
  folio:
    build: .
    ports:
      - "8050:8050"
    environment:
      - FMP_API_KEY=${FMP_API_KEY}
      - PORT=8050
      - PYTHONPATH=/app
    volumes:
      - ./src:/app/src
      - ./config:/app/config
      - ./data:/app/data
      - ./.env:/app/.env
    restart: unless-stopped
```

### 1.3 Create .dockerignore

Create a `.dockerignore` file to exclude unnecessary files from the Docker build context:

```
# Version control
.git
.gitignore

# Python cache files
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/

# Virtual environment
venv/
env/
ENV/

# IDE files
.vscode/
.idea/

# Logs
logs/
*.log

# Cache directories
.cache*/
.tmp/

# Local data
data/
*.csv

# Build artifacts
dist/
build/
*.egg-info/

# Docker files (not needed in build context)
Dockerfile.dev
docker-compose.dev.yml

# Documentation
docs/
*.md
!README.md
```

### 1.4 Configure Environment Variables

Create a `.env.example` file with all required environment variables:

```
# API Keys
FMP_API_KEY=your_fmp_api_key_here

# Application Settings
PORT=8050
DEBUG=false

# Data Source Configuration
DATA_SOURCE=yfinance
```

## Phase 2: Local Testing (1 day)

### 2.1 Build and Test Docker Image

```bash
# Build the Docker image
docker build -t folio:latest .

# Run the container
docker run -p 8050:8050 --env-file .env folio:latest
```

### 2.2 Test with Docker Compose

```bash
# Start the application with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### 2.3 Test Application Functionality

- Test portfolio upload functionality
- Verify data fetching from yfinance/FMP APIs
- Check all UI components and interactions
- Verify periodic data refresh functionality

## Phase 3: CI/CD Setup (1 day)

### 3.1 Set Up GitHub Actions Workflow

Create `.github/workflows/docker-build.yml`:

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to DockerHub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: yourusername/folio
          tags: |
            type=semver,pattern={{version}}
            type=ref,event=branch
            type=sha,format=short

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 3.2 Configure Repository Secrets

Add the following secrets to the GitHub repository:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## Phase 4: Hosting Setup (1 day)

### 4.1 Hosting Options

#### Option A: DigitalOcean App Platform

**Setup Steps:**
1. Create a DigitalOcean account
2. Create a new App from the App Platform dashboard
3. Connect to your GitHub repository
4. Configure environment variables
5. Deploy the application

**Pros:**
- Simple setup and management
- Built-in SSL and domain management
- Automatic deployments from GitHub
- Reasonable pricing ($5-20/month)

**Cons:**
- Limited customization compared to raw VMs
- Higher cost than self-managed VMs for the same resources

#### Option B: Google Cloud Run

**Setup Steps:**
1. Create a Google Cloud account
2. Enable Cloud Run API
3. Set up Container Registry
4. Push Docker image to Container Registry
5. Deploy to Cloud Run with environment variables

**Pros:**
- Pay-per-use pricing (can be very cost-effective)
- Automatic scaling
- Easy integration with other Google Cloud services
- Command-line deployment with gcloud CLI

**Cons:**
- More complex setup than DigitalOcean
- Requires Google Cloud knowledge

#### Option C: AWS App Runner

**Setup Steps:**
1. Create an AWS account
2. Navigate to AWS App Runner console
3. Create a new service
4. Connect to container registry
5. Configure environment variables and deployment settings

**Pros:**
- Fully managed container service
- Automatic scaling
- Integration with AWS ecosystem
- Simple web interface

**Cons:**
- Higher cost than self-managed EC2
- Limited customization options

#### Option D: Self-managed VPS with Docker

**Setup Steps:**
1. Provision a VPS (DigitalOcean, Linode, AWS EC2, etc.)
2. Install Docker and Docker Compose
3. Set up Nginx as a reverse proxy
4. Configure SSL with Let's Encrypt
5. Deploy using Docker Compose

**Pros:**
- Maximum flexibility and control
- Most cost-effective for long-term hosting
- Can host multiple applications on the same server
- Full control over security and configuration

**Cons:**
- Requires more system administration knowledge
- Manual setup and maintenance
- Responsibility for security updates

### 4.2 Recommended Hosting Option

Based on the requirements for command-line deployment and ease of use, we recommend **Option D: Self-managed VPS with Docker** for the following reasons:

1. Provides the most flexibility for command-line deployment
2. Most cost-effective for long-term hosting
3. Allows for complete customization of the deployment process
4. Can be easily automated with scripts

For initial testing and proof of concept, **Option A: DigitalOcean App Platform** provides the quickest path to deployment with minimal setup.

## Phase 5: Command-line Deployment Tools (2 days)

### 5.1 Create Deployment Script

Create a `scripts/deploy.sh` script for easy deployment:

```bash
#!/bin/bash

# Folio Deployment Script
# Usage: ./scripts/deploy.sh [options]
# Options:
#   --env=<environment>    Deployment environment (dev, staging, prod)
#   --host=<hostname>      Target host for deployment
#   --port=<port>          Port to run the application on
#   --build                Build the Docker image before deploying
#   --push                 Push the Docker image to registry
#   --help                 Show this help message

# Default values
ENV="dev"
HOST="localhost"
PORT="8050"
BUILD=false
PUSH=false

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --env=*)
      ENV="${arg#*=}"
      shift
      ;;
    --host=*)
      HOST="${arg#*=}"
      shift
      ;;
    --port=*)
      PORT="${arg#*=}"
      shift
      ;;
    --build)
      BUILD=true
      shift
      ;;
    --push)
      PUSH=true
      shift
      ;;
    --help)
      echo "Folio Deployment Script"
      echo "Usage: ./scripts/deploy.sh [options]"
      echo "Options:"
      echo "  --env=<environment>    Deployment environment (dev, staging, prod)"
      echo "  --host=<hostname>      Target host for deployment"
      echo "  --port=<port>          Port to run the application on"
      echo "  --build                Build the Docker image before deploying"
      echo "  --push                 Push the Docker image to registry"
      echo "  --help                 Show this help message"
      exit 0
      ;;
    *)
      # Unknown option
      echo "Unknown option: $arg"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

echo "Deploying Folio to $ENV environment on $HOST:$PORT"

# Load environment variables
if [ -f ".env.$ENV" ]; then
  echo "Loading environment variables from .env.$ENV"
  export $(grep -v '^#' .env.$ENV | xargs)
else
  echo "Warning: .env.$ENV file not found"
fi

# Build Docker image if requested
if [ "$BUILD" = true ]; then
  echo "Building Docker image..."
  docker build -t folio:latest .
fi

# Push Docker image if requested
if [ "$PUSH" = true ]; then
  echo "Pushing Docker image to registry..."
  docker tag folio:latest yourusername/folio:latest
  docker push yourusername/folio:latest
fi

# Deploy to remote host
if [ "$HOST" != "localhost" ]; then
  echo "Deploying to remote host $HOST..."

  # Copy docker-compose file
  scp docker-compose.yml $HOST:/opt/folio/

  # Copy environment file
  scp .env.$ENV $HOST:/opt/folio/.env

  # SSH into host and start the container
  ssh $HOST "cd /opt/folio && docker-compose pull && docker-compose up -d"
else
  # Deploy locally
  echo "Deploying locally..."
  docker-compose up -d
fi

echo "Deployment completed successfully!"
```

### 5.2 Create Makefile Targets

Add the following targets to the Makefile:

```makefile
# Docker targets
.PHONY: docker-build docker-run docker-push docker-deploy

docker-build:
	@echo "Building Docker image..."
	docker build -t folio:latest .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8050:8050 --env-file .env folio:latest

docker-push:
	@echo "Pushing Docker image to registry..."
	docker tag folio:latest yourusername/folio:latest
	docker push yourusername/folio:latest

docker-deploy:
	@echo "Deploying with Docker..."
	./scripts/deploy.sh $(ARGS)
```

### 5.3 Server Setup Script

Create a `scripts/setup-server.sh` script to automate server setup:

```bash
#!/bin/bash

# Folio Server Setup Script
# Usage: ./scripts/setup-server.sh [hostname]

# Check if hostname is provided
if [ -z "$1" ]; then
  echo "Usage: ./scripts/setup-server.sh [hostname]"
  exit 1
fi

HOST=$1
SSH_KEY="$HOME/.ssh/id_rsa.pub"

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
  echo "SSH key not found at $SSH_KEY"
  echo "Please generate an SSH key with: ssh-keygen -t rsa -b 4096"
  exit 1
fi

echo "Setting up server at $HOST..."

# Copy SSH key to server
ssh-copy-id root@$HOST

# Install Docker and Docker Compose
ssh root@$HOST "apt-get update && \
  apt-get install -y apt-transport-https ca-certificates curl software-properties-common && \
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
  add-apt-repository 'deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable' && \
  apt-get update && \
  apt-get install -y docker-ce docker-compose-plugin && \
  systemctl enable docker && \
  systemctl start docker"

# Create application directory
ssh root@$HOST "mkdir -p /opt/folio"

# Set up Nginx and Let's Encrypt
ssh root@$HOST "apt-get install -y nginx certbot python3-certbot-nginx && \
  systemctl enable nginx && \
  systemctl start nginx"

# Create Nginx configuration
cat > nginx.conf << EOF
server {
    listen 80;
    server_name $HOST;

    location / {
        proxy_pass http://localhost:8050;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Copy Nginx configuration to server
scp nginx.conf root@$HOST:/etc/nginx/sites-available/folio
ssh root@$HOST "ln -sf /etc/nginx/sites-available/folio /etc/nginx/sites-enabled/folio && \
  nginx -t && \
  systemctl reload nginx"

# Set up SSL with Let's Encrypt
ssh root@$HOST "certbot --nginx -d $HOST --non-interactive --agree-tos --email your-email@example.com"

echo "Server setup completed successfully!"
echo "You can now deploy Folio using: make docker-deploy ARGS=\"--host=$HOST --env=prod\""
```

## Hosting Comparison and Recommendation

| Hosting Option | Ease of Setup | Cost | Scalability | Command-line Deployment | Maintenance Effort |
|----------------|---------------|------|-------------|-------------------------|-------------------|
| DigitalOcean App Platform | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★★★ |
| Google Cloud Run | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★★☆ |
| AWS App Runner | ★★★★☆ | ★★☆☆☆ | ★★★★☆ | ★★★☆☆ | ★★★★☆ |
| Self-managed VPS | ★★☆☆☆ | ★★★★★ | ★★☆☆☆ | ★★★★★ | ★★☆☆☆ |

**Final Recommendation:**

For the initial deployment, we recommend starting with a **Self-managed VPS with Docker** on DigitalOcean or Linode, as it provides:

1. The most flexibility for command-line deployment
2. Cost-effective hosting ($5-10/month for a basic server)
3. Complete control over the deployment process
4. Easy automation with the provided scripts

As the application grows, you can evaluate moving to Google Cloud Run for better scalability and pay-per-use pricing, especially if usage patterns are sporadic.

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Docker Configuration | 2 days | None |
| Local Testing | 1 day | Docker Configuration |
| CI/CD Setup | 1 day | Docker Configuration |
| Hosting Setup | 1 day | Docker Configuration, Local Testing |
| Command-line Deployment Tools | 2 days | Hosting Setup |
| **Total** | **7 days** | |

## Conclusion

This Docker containerization plan provides a comprehensive approach to containerizing the Folio application with a focus on command-line deployment capabilities. By following this plan, we will create a portable, consistent, and easily deployable application that can be hosted on various platforms according to our needs.

The recommended self-managed VPS approach with the provided deployment scripts will enable easy command-line deployment while maintaining flexibility and cost-effectiveness. As the application evolves, we can reassess our hosting needs and potentially migrate to more managed solutions like Google Cloud Run for improved scalability.
