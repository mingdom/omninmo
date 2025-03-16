#!/usr/bin/env python3
"""
Command-line script for training the v2 stock prediction model
"""

import os
import sys
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v2.train import train_model


def main():
    """Main function to parse arguments and train model"""
    parser = argparse.ArgumentParser(description="Train stock prediction model")
    parser.add_argument("--tickers", type=str, nargs="+", help="List of ticker symbols")
    parser.add_argument("--model-path", type=str, help="Path to save the model")
    parser.add_argument("--period", type=str, help="Period to fetch data (e.g., 5y)")
    parser.add_argument("--interval", type=str, help="Data interval (e.g., 1d)")
    parser.add_argument(
        "--forward-days", type=int, help="Days to look ahead for returns"
    )
    parser.add_argument("--force-sample", action="store_true", help="Use sample data")
    parser.add_argument(
        "--enhanced-features",
        action="store_true",
        help="Use enhanced features with risk metrics",
    )
    parser.add_argument(
        "--risk-adjusted-target",
        action="store_true",
        help="Use risk-adjusted target (Sharpe ratio)",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true", help="Overwrite without asking"
    )

    args = parser.parse_args()

    train_model(
        tickers=args.tickers,
        model_path=args.model_path,
        period=args.period,
        interval=args.interval,
        forward_days=args.forward_days,
        force_sample=args.force_sample,
        overwrite=args.yes,
        use_enhanced_features=args.enhanced_features,
        use_risk_adjusted_target=args.risk_adjusted_target
    )


if __name__ == "__main__":
    main()
