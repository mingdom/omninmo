"""
Interface for data fetchers.

This module defines a common interface for data fetchers, allowing for
interchangeable use of different data sources (FMP API, Yahoo Finance, etc.).
"""

from abc import ABC, abstractmethod


class DataFetcherInterface(ABC):
    """Interface for data fetchers"""
    
    # Default period for beta calculations
    beta_period = "6m"

    @abstractmethod
    def fetch_data(self, ticker, period="1y", interval="1d"):
        """
        Fetch stock data for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)
            
        Returns:
            pandas.DataFrame: DataFrame with stock data
        """
        pass

    @abstractmethod
    def fetch_market_data(self, market_index="SPY", period=None, interval="1d"):
        """
        Fetch market index data for beta calculations.
        
        Args:
            market_index (str): Market index ticker symbol (default: 'SPY')
            period (str, optional): Time period. If None, uses beta_period.
            interval (str): Data interval ('1d', '1wk', etc.)
            
        Returns:
            pandas.DataFrame: DataFrame with market index data
        """
        pass
