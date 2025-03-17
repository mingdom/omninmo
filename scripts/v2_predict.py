#!/usr/bin/env python3
"""
Command-line script for running stock predictions with the v2 console app
"""

import argparse
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.v2.console_app import ConsoleApp


def main():
    """Main function for running the console app"""
    parser = argparse.ArgumentParser(description='Stock Prediction Console App')
    parser.add_argument('--tickers', type=str, nargs='+', help='List of tickers to predict')
    parser.add_argument('--model', type=str, help='Path to model file (uses latest if not specified)')
    parser.add_argument('--sample', action='store_true', help='Use sample data instead of API')
    parser.add_argument('--format', type=str, choices=['table', 'csv', 'json'], default='table',
                        help='Output format (table, csv, or json)')

    args = parser.parse_args()

    app = ConsoleApp()

    # Load model
    if not app.load_model(args.model):
        sys.exit(1)

    # Run predictions
    app.run_predictions(args.tickers, args.sample, args.format)

if __name__ == "__main__":
    main()
