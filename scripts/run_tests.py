#!/usr/bin/env python3
"""
Script to run all tests for the omninmo project.
"""

import os
import sys
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_path):
    """Run a Python script and return the exit code."""
    try:
        logger.info(f"Running {os.path.basename(script_path)}...")
        result = subprocess.run([sys.executable, script_path], check=False)
        return result.returncode
    except Exception as e:
        logger.error(f"Error running {script_path}: {e}")
        return 1

def main():
    """Run all tests."""
    # Get the absolute path to the scripts directory
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of test scripts to run
    test_scripts = [
        os.path.join(scripts_dir, 'test_imports.py'),
        os.path.join(scripts_dir, 'test_trainer.py')
    ]
    
    # Run each test script
    failed_tests = []
    
    for script in test_scripts:
        if not os.path.exists(script):
            logger.error(f"Test script not found: {script}")
            failed_tests.append(os.path.basename(script))
            continue
        
        exit_code = run_script(script)
        
        if exit_code != 0:
            logger.error(f"Test failed: {os.path.basename(script)}")
            failed_tests.append(os.path.basename(script))
    
    # Print summary
    if failed_tests:
        logger.error(f"Failed tests: {', '.join(failed_tests)}")
        return 1
    else:
        logger.info("All tests passed!")
        return 0

if __name__ == '__main__':
    sys.exit(main()) 