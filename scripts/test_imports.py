#!/usr/bin/env python3
"""
Script to test that all imports work correctly.
"""

import os
import sys
import unittest
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run the import tests."""
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Add the project root to the Python path
    sys.path.insert(0, project_root)
    
    # Import the test module
    try:
        from tests.test_imports import TestImports
    except ImportError as e:
        logger.error(f"Failed to import test module: {e}")
        sys.exit(1)
    
    # Run the tests
    logger.info("Running import tests...")
    
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestImports)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Check if all tests passed
    if result.wasSuccessful():
        logger.info("All import tests passed!")
        return 0
    else:
        logger.error("Some import tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 