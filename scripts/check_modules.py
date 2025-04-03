#!/usr/bin/env python3
"""
Module availability checker for the Folio application.

This script checks for the availability and versions of Python modules
required by the Folio application. It helps diagnose dependency issues
in the Docker container environment.

Usage:
    python check_modules.py

Example in Docker:
    docker exec omninmo-folio-1 python /app/scripts/check_modules.py
"""

import importlib
import importlib.metadata
import os
import sys
import subprocess
from pathlib import Path


def get_module_version(module_name):
    """
    Get the version of an installed module.
    
    Args:
        module_name (str): Name of the module
        
    Returns:
        str: Version of the module or "Not found" if not installed
    """
    try:
        return importlib.metadata.version(module_name)
    except importlib.metadata.PackageNotFoundError:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "Unknown")
            return version
        except ImportError:
            return "Not found"
    except Exception as e:
        return f"Error: {str(e)}"


def check_module(module_name):
    """
    Check if a module is available and get its version.
    
    Args:
        module_name (str): Name of the module to check
        
    Returns:
        tuple: (bool, str) - Success status and version/error message
    """
    try:
        module = importlib.import_module(module_name)
        version = get_module_version(module_name)
        return True, version
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_typing_features():
    """Check for availability of specific typing features."""
    print("\n--- Checking typing features ---")
    
    # Check for NotRequired
    print("\nChecking for NotRequired:")
    try:
        from typing import NotRequired
        print("✅ NotRequired is available in typing module")
    except ImportError:
        print("❌ NotRequired is not available in typing module")
        try:
            from typing_extensions import NotRequired
            print("✅ NotRequired is available in typing_extensions module")
        except ImportError:
            print("❌ NotRequired is not available in typing_extensions module")
    
    # Print typing module details
    print("\nTyping module details:")
    try:
        import typing
        print(f"Typing module location: {typing.__file__}")
        print(f"Typing module version: {getattr(typing, '__version__', 'Unknown')}")
        
        # List all attributes in typing module
        print("\nTyping module attributes:")
        typing_attrs = [attr for attr in dir(typing) if not attr.startswith('_')]
        print(", ".join(typing_attrs))
    except ImportError:
        print("Could not import typing module")


def check_application_structure():
    """Check the structure of the application code."""
    print("\n--- Checking application structure ---")
    
    # Check for src directory
    src_dir = Path("/app/src") if os.path.exists("/app/src") else Path("./src")
    if not src_dir.exists():
        print(f"❌ Source directory not found at {src_dir}")
        return
    
    print(f"✅ Source directory found at {src_dir}")
    
    # Check for key files
    key_files = [
        "folio/app.py",
        "folio/utils.py",
        "folio/data_model.py",
        "data_fetcher_factory.py",
        "lab/option_utils.py"
    ]
    
    for file_path in key_files:
        full_path = src_dir / file_path
        if full_path.exists():
            print(f"✅ Found {file_path}")
        else:
            print(f"❌ Missing {file_path}")


def main():
    """Main function to check module availability."""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    
    # Check for required modules
    required_modules = [
        "dash",
        "dash_bootstrap_components",
        "pandas",
        "numpy",
        "yfinance",
        "yaml",
        "requests",
        "scipy",
        "typing",
        "typing_extensions"
    ]
    
    print("\n--- Checking required modules ---")
    for module_name in required_modules:
        success, version = check_module(module_name)
        if success:
            print(f"✅ {module_name}: {version}")
        else:
            print(f"❌ {module_name}: {version}")
    
    # Check typing features
    check_typing_features()
    
    # Check application structure
    check_application_structure()
    
    # List all installed packages
    print("\n--- All installed packages ---")
    try:
        subprocess.run([sys.executable, "-m", "pip", "list"], check=True)
    except subprocess.SubprocessError:
        print("Could not list installed packages")


if __name__ == "__main__":
    main()
