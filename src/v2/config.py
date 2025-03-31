"""
Configuration utility for omninmo v2
Supports loading configuration from multiple YAML files
"""

import logging
import os

import yaml

# Setup logging
logger = logging.getLogger(__name__)


class Config:
    """
    Configuration class that loads settings from config files

    Supports both the legacy single config.yaml file and the new multi-file
    structure in the config directory.
    """

    def __init__(self, config_path="config.yaml"):
        """
        Initialize configuration with path to config file

        Args:
            config_path: Path to the main config file or directory
        """
        self.config_path = config_path
        self.config_data = {}
        self.load_config()

    def load_config(self):
        """
        Load configuration from yaml file(s)

        If a config directory exists with a config.yaml file inside,
        it will load the multi-file configuration structure.
        Otherwise, it falls back to the legacy single file approach.
        """
        # Check if we're using the new structure
        config_dir = "config"
        main_config_path = os.path.join(config_dir, "config.yaml")

        if os.path.isdir(config_dir) and os.path.exists(main_config_path):
            # Use new multi-file structure
            try:
                # Load the main config file
                with open(main_config_path) as f:
                    main_config = yaml.safe_load(f)
                logger.debug(f"Loaded main config: {main_config}")

                # Process imports
                for import_file in main_config.get("imports", []):
                    import_path = os.path.join(config_dir, import_file)

                    try:
                        with open(import_path) as f:
                            section_config = yaml.safe_load(f)

                        # Get section name from filename (without extension)
                        section_name = os.path.splitext(os.path.basename(import_file))[
                            0
                        ]
                        logger.debug(
                            f"Loading {section_name} from {import_file}: {section_config}"
                        )

                        # Add to merged config
                        self.config_data[section_name] = section_config
                    except Exception as e:
                        logger.error(f"Error loading config file {import_path}: {e}")
            except Exception as e:
                logger.error(
                    f"Error loading main configuration file {main_config_path}: {e}"
                )
                # Fall back to legacy mode
                self._load_legacy_config()
        else:
            # Use legacy single file
            self._load_legacy_config()

        logger.debug(f"Final config_data: {self.config_data}")

    def _load_legacy_config(self):
        """Load configuration from legacy single yaml file"""
        try:
            with open(self.config_path) as file:
                self.config_data = yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def get(self, key_path, default=None):
        """
        Get a configuration value using dot notation path
        Example: config.get('model.training.period')
        """
        logger.debug(f"Getting config for key_path: {key_path}")
        keys = key_path.split(".")
        value = self.config_data

        try:
            for key in keys:
                logger.debug(
                    f"Processing key: {key}, current value type: {type(value)}, value: {value}"
                )
                if not isinstance(value, dict):
                    logger.debug(f"Value is not a dict, returning default: {default}")
                    return default
                if key not in value:
                    logger.debug(
                        f"Key {key} not found in value, returning default: {default}"
                    )
                    return default
                value = value[key]
            logger.debug(f"Final value: {value}")
            return value
        except Exception as e:
            logger.error(f"Error accessing config key {key_path}: {e}")
            return default


# Create a singleton config instance
config = Config()

if __name__ == "__main__":
    # Simple test of the configuration
    logging.basicConfig(level=logging.DEBUG)
    print("Model training period:", config.get("model.training.period"))
    print("Default tickers:", config.get("model.training.default_tickers"))
    print("Default watchlist:", config.get("watchlist.default"))
