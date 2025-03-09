"""
Configuration loader utility for omninmo.
"""

import os
import yaml
from pathlib import Path
import logging
from typing import Any, Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class Config:
    """Configuration loader and manager for omninmo."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration loader."""
        if self._config is None:
            self.load_config()
    
    @staticmethod
    def _resolve_env_vars(value: Any) -> Any:
        """
        Recursively resolve environment variables in configuration values.
        
        Args:
            value: Configuration value that might contain environment variables
            
        Returns:
            Resolved value with environment variables replaced
        """
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var)
        elif isinstance(value, dict):
            return {k: Config._resolve_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [Config._resolve_env_vars(v) for v in value]
        return value
    
    @lru_cache()
    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Optional path to config file. If not provided, uses default path.
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            
            # Resolve environment variables
            self._config = self._resolve_env_vars(self._config)
            
            logger.info(f"Configuration loaded successfully from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {str(e)}")
            raise
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation path.
        
        Args:
            path: Dot notation path to configuration value (e.g., 'model.xgboost.learning_rate')
            default: Default value to return if path not found
            
        Returns:
            Configuration value at the specified path
        """
        try:
            value = self._config
            for key in path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_model_params(self) -> Dict[str, Any]:
        """Get XGBoost model parameters."""
        return self.get('model.xgboost', {})
    
    def get_training_params(self) -> Dict[str, Any]:
        """Get model training parameters."""
        return self.get('model.training', {})
    
    def get_rating_map(self) -> Dict[int, str]:
        """Get rating mapping."""
        return self.get('rating.map', {})
    
    def get_rating_colors(self) -> Dict[str, str]:
        """Get rating colors."""
        return self.get('rating.colors', {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get app configuration."""
        return self.get('app', {})
    
    def get_watchlist(self) -> list:
        """Get default watchlist."""
        return self.get('app.watchlist.default', [])
    
    def get_data_config(self) -> Dict[str, Any]:
        """Get data fetching configuration."""
        return self.get('data', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('logging', {})
    
    def get_chart_config(self) -> Dict[str, Any]:
        """Get chart configuration."""
        return self.get('charts', {})

# Create a global instance
config = Config()

# Example usage:
# from src.utils.config import config
# learning_rate = config.get('model.xgboost.learning_rate')
# or
# model_params = config.get_model_params() 