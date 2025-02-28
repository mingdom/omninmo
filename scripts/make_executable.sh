#!/bin/bash
# Make all scripts executable

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Make all Python scripts in the scripts directory executable
echo "Making Python scripts executable..."
chmod +x "$SCRIPT_DIR"/*.py

# Make all shell scripts in the scripts directory executable
echo "Making shell scripts executable..."
chmod +x "$SCRIPT_DIR"/*.sh

echo "Done!" 