#!/usr/bin/env python3
"""
Package diagnostics script for the Folio application.

This script checks the Python environment and installed packages,
with a specific focus on dependencies that have caused issues
in the Docker container (like SciPy and typing.NotRequired).

Usage:
    python diagnose_packages.py

Example in Docker:
    docker exec omninmo-folio-1 python /app/scripts/diagnose_packages.py
"""

import sys
import pkg_resources

def main():
    """Run package diagnostics."""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print("\nInstalled packages:")
    
    for package in sorted([f"{d.project_name}=={d.version}" for d in pkg_resources.working_set]):
        print(f"  {package}")
    
    try:
        import scipy
        print(f"\nSciPy is installed: {scipy.__version__}")
        print(f"SciPy path: {scipy.__file__}")
    except ImportError as e:
        print(f"\nSciPy import error: {e}")
    
    try:
        from typing import NotRequired
        print("\nNotRequired is available in typing")
    except ImportError:
        print("\nNotRequired is NOT available in typing")
        try:
            from typing_extensions import NotRequired
            print("NotRequired is available in typing_extensions")
        except ImportError:
            print("NotRequired is NOT available in typing_extensions either")
    
    print("\nPYTHONPATH:")
    for path in sys.path:
        print(f"  {path}")

if __name__ == "__main__":
    main()
