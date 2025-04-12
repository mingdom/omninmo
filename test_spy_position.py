"""
Test script to analyze the SPY position from the real portfolio.
"""

import datetime
import logging
import sys

from src.folio.pnl import analyze_asymptotic_behavior

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))

# Create the SPY position from the real portfolio
spy_positions = [
    # SPY stock position
    {"position_type": "stock", "quantity": 1, "price": 524.53, "ticker": "SPY"},
    # Short calls (unbounded loss on upside)
    {
        "position_type": "option",
        "option_type": "CALL",
        "strike": 560,
        "expiration": datetime.date.today() + datetime.timedelta(days=60),
        "quantity": -40,
        "price": 12.06,
        "ticker": "SPY",
    },
    # Short puts (bounded loss on downside)
    {
        "position_type": "option",
        "option_type": "PUT",
        "strike": 450,
        "expiration": datetime.date.today() + datetime.timedelta(days=60),
        "quantity": -10,
        "price": 9.72,
        "ticker": "SPY",
    },
    # Short puts (bounded loss on downside)
    {
        "position_type": "option",
        "option_type": "PUT",
        "strike": 470,
        "expiration": datetime.date.today() + datetime.timedelta(days=60),
        "quantity": -30,
        "price": 12.80,
        "ticker": "SPY",
    },
    # Long puts (bounded profit on downside)
    {
        "position_type": "option",
        "option_type": "PUT",
        "strike": 490,
        "expiration": datetime.date.today() + datetime.timedelta(days=60),
        "quantity": 10,
        "price": 16.73,
        "ticker": "SPY",
    },
    # Long puts (bounded profit on downside)
    {
        "position_type": "option",
        "option_type": "PUT",
        "strike": 525,
        "expiration": datetime.date.today() + datetime.timedelta(days=60),
        "quantity": 30,
        "price": 27.25,
        "ticker": "SPY",
    },
]

# Analyze the SPY position
result = analyze_asymptotic_behavior(spy_positions, 524.53)

# Print the results
