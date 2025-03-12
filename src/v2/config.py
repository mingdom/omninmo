"""
Simple configuration utility for omninmo v2
"""

import os
import yaml
from pathlib import Path

class Config:
    """Simple configuration class that loads settings from config.yaml"""
    
    def __init__(self, config_path='config.yaml'):
        """Initialize configuration with path to config file"""
        self.config_path = config_path
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from yaml file"""
        try:
            with open(self.config_path, 'r') as file:
                self.config_data = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def get(self, key_path, default=None):
        """
        Get a configuration value using dot notation path
        Example: config.get('model.training.period')
        """
        keys = key_path.split('.')
        value = self.config_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value

# Create a singleton config instance
config = Config()

if __name__ == "__main__":
    # Simple test of the configuration
    print("Model training period:", config.get('model.training.period'))
    print("Default tickers:", config.get('model.training.default_tickers'))
    print("Default watchlist:", config.get('app.watchlist.default')) 