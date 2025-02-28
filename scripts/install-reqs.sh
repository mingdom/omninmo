#!/bin/bash
# Script to install all required dependencies for the omninmo project

echo "Installing dependencies for omninmo..."

# Check if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Get the project root directory
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Install dependencies from requirements.txt
echo "Installing Python dependencies from requirements.txt..."
pip3 install -r "$PROJECT_ROOT/requirements.txt"

# Make all Python scripts executable
echo "Making Python scripts executable..."
chmod +x "$SCRIPT_DIR"/*.py

echo "Installation complete!" 