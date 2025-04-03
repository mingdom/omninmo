#!/usr/bin/env python3
"""
Container path checker for the Folio application.

This script checks the filesystem paths in a Docker container,
verifying that the expected directories and files exist.
It's useful for diagnosing path-related issues in the container.

Usage:
    python check_container_paths.py

Example in Docker:
    docker exec omninmo-folio-1 python /app/scripts/check_container_paths.py
"""

import sys
import os

def main():
    """Check container paths and directories."""
    print(f"Current working directory: {os.getcwd()}")
    print(f"PYTHONPATH environment variable: {os.environ.get('PYTHONPATH', 'Not set')}")
    print("\nPython path:")
    for path in sys.path:
        print(f"  {path}")
    
    print("\nChecking if directories exist:")
    for path in ['/app', '/app/src', '/app/src/lab', '/app/src/folio']:
        print(f"  {path}: {os.path.exists(path)}")
    
    # Check key directories
    directories = [
        '/app',
        '/app/src',
        '/app/src/lab',
        '/app/src/folio'
    ]
    
    for directory in directories:
        print(f"\nListing {directory} directory:")
        try:
            files = os.listdir(directory)
            if files:
                for file in sorted(files):
                    full_path = os.path.join(directory, file)
                    if os.path.isdir(full_path):
                        print(f"  📁 {file}/")
                    else:
                        print(f"  📄 {file}")
            else:
                print("  (empty directory)")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()
