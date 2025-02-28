"""
Data fetching module for omninmo.
Fetches stock data using yfinance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


class StockDataFetcher:
    """Class for fetching stock data using yfinance."""

    def __init__(self):
        """Initialize the StockDataFetcher."""
        pass

    def fetch_stock_data(self, ticker, period="1y", interval="1d"):
        """
        Fetch historical stock data for a given ticker.

        Args:
            ticker (str): Stock ticker symbol (e.g., 'NVDA')
            period (str): Period to fetch data for (default: '1y')
            interval (str): Data interval (default: '1d')

        Returns:
            pd.DataFrame: DataFrame containing the stock data
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                raise ValueError(f"No data found for ticker {ticker}")

            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None

    def fetch_stock_info(self, ticker):
        """
        Fetch company information for a given ticker.

        Args:
            ticker (str): Stock ticker symbol (e.g., 'NVDA')

        Returns:
            dict: Dictionary containing company information
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info
        except Exception as e:
            print(f"Error fetching info for {ticker}: {e}")
            return None

    def fetch_financials(self, ticker):
        """
        Fetch financial data for a given ticker.

        Args:
            ticker (str): Stock ticker symbol (e.g., 'NVDA')

        Returns:
            dict: Dictionary containing financial data
        """
        try:
            stock = yf.Ticker(ticker)

            # Get key financial data
            financials = {
                "income_statement": stock.income_stmt,
                "balance_sheet": stock.balance_sheet,
                "cash_flow": stock.cashflow,
                "earnings": stock.earnings,
            }

            return financials
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            return None
