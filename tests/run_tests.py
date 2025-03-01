#!/usr/bin/env python3
"""
Script to run all tests for the omninmo project.
"""

import os
import sys
import unittest
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run all tests in the tests directory."""
    # Get the absolute path to the tests directory
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(tests_dir, '..'))
    
    # Add the project root to the Python path
    sys.path.insert(0, project_root)
    
    # Discover and run all tests
    logger.info("Discovering tests...")
    
    # Create a test suite that discovers all test files in the tests directory
    test_suite = unittest.defaultTestLoader.discover(tests_dir, pattern="test_*.py")
    
    # Run the tests
    logger.info("Running tests...")
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Print summary
    if result.wasSuccessful():
        logger.info("All tests passed!")
        return 0
    else:
        logger.error(f"Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 