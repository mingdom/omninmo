#!/usr/bin/env python3
"""
Test script for verifying Python imports in the Docker container.

This script attempts to import various modules used by the Folio application
to diagnose import-related issues in the Docker container environment.

Usage:
    python test_imports.py

Example in Docker:
    docker exec omninmo-folio-1 python /app/scripts/test_imports.py
"""

import sys
import importlib
import traceback


def test_import(module_name):
    """
    Test importing a module and print the result.
    
    Args:
        module_name (str): Name of the module to import
        
    Returns:
        bool: True if import successful, False otherwise
    """
    print(f"Testing import: {module_name}")
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        print(f"   Module location: {getattr(module, '__file__', 'Unknown')}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing {module_name}: {e}")
        traceback.print_exc()
        return False


def main():
    """Main function to test various imports."""
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}")
    print("\n--- Testing standard library imports ---")
    test_import("typing")
    
    print("\n--- Testing third-party library imports ---")
    test_import("dash")
    test_import("dash_bootstrap_components")
    test_import("pandas")
    test_import("numpy")
    test_import("yfinance")
    
    print("\n--- Testing application imports ---")
    test_import("src")
    test_import("src.folio")
    test_import("src.folio.app")
    test_import("src.folio.utils")
    test_import("src.folio.data_model")
    test_import("src.data_fetcher_factory")
    test_import("src.lab.option_utils")
    
    print("\n--- Testing relative imports ---")
    try:
        from src.folio.utils import format_beta, format_currency
        print("✅ Successfully imported format_beta and format_currency from src.folio.utils")
    except ImportError as e:
        print(f"❌ Failed to import from src.folio.utils: {e}")
    
    try:
        from src.data_fetcher_factory import create_data_fetcher
        print("✅ Successfully imported create_data_fetcher from src.data_fetcher_factory")
    except ImportError as e:
        print(f"❌ Failed to import from src.data_fetcher_factory: {e}")


if __name__ == "__main__":
    main()
