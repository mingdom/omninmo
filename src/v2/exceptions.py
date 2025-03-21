"""
Custom exceptions for the stock prediction model
"""


class ModelError(Exception):
    """Base class for model-related exceptions"""

    pass


class ModelNotLoadedError(ModelError):
    """Raised when attempting to use an unloaded model"""

    pass


class InsufficientDataError(ModelError):
    """Raised when there is not enough data for prediction"""

    pass


class FeatureGenerationError(ModelError):
    """Raised when feature generation fails"""

    pass


class DataFetchError(ModelError):
    """Raised when data fetching fails"""

    pass


class ConfigurationError(ModelError):
    """Raised when there are configuration issues"""

    pass
