#!/bin/bash
# 
# Run all diagnostic scripts for the Folio application in Docker.
#
# This script runs all the diagnostic scripts to help troubleshoot
# issues with the Folio application running in a Docker container.
#
# Usage:
#   ./run_diagnostics.sh [container_name]
#
# If container_name is not provided, it defaults to "omninmo-folio-1"
#

set -e

CONTAINER_NAME=${1:-omninmo-folio-1}
SCRIPT_DIR=$(dirname "$0")

echo "=== Running diagnostics on container: $CONTAINER_NAME ==="
echo

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Error: Container $CONTAINER_NAME is not running"
    echo "Available containers:"
    docker ps
    exit 1
fi

# Copy scripts to container if they don't exist
echo "Copying diagnostic scripts to container..."
docker exec "$CONTAINER_NAME" mkdir -p /app/scripts
docker cp "$SCRIPT_DIR/check_modules.py" "$CONTAINER_NAME:/app/scripts/"
docker cp "$SCRIPT_DIR/check_network.py" "$CONTAINER_NAME:/app/scripts/"
docker cp "$SCRIPT_DIR/test_imports.py" "$CONTAINER_NAME:/app/scripts/"

# Make scripts executable
docker exec "$CONTAINER_NAME" chmod +x /app/scripts/*.py

# Run each diagnostic script
echo
echo "=== Running module checks ==="
docker exec "$CONTAINER_NAME" python /app/scripts/check_modules.py

echo
echo "=== Running import tests ==="
docker exec "$CONTAINER_NAME" python /app/scripts/test_imports.py

echo
echo "=== Running network checks ==="
docker exec "$CONTAINER_NAME" python /app/scripts/check_network.py

echo
echo "=== Diagnostics complete ==="
