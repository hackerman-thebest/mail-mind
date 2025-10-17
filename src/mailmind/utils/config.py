"""
Configuration management utilities.

Handles loading and validation of application configuration.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded"""
    pass


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Story 0.2: Now checks for user_config.yaml first and merges with default.yaml.
    User configuration takes precedence over defaults.

    Args:
        config_path: Path to configuration file. If None, uses default config
                     and merges with user_config.yaml if it exists.

    Returns:
        dict: Configuration dictionary

    Raises:
        ConfigurationError: If config file cannot be loaded or is invalid
    """
    if config_path is None:
        # Load default config
        config_dir = Path(__file__).parent.parent.parent.parent / "config"
        default_config = config_dir / "default.yaml"
        user_config = config_dir / "user_config.yaml"

        # Load default configuration
        if not default_config.exists():
            raise ConfigurationError(f"Default configuration file not found: {default_config}")

        try:
            with open(default_config, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from: {default_config}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in default configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load default configuration: {e}")

        # Load user configuration if it exists and merge
        if user_config.exists():
            try:
                with open(user_config, 'r') as f:
                    user_cfg = yaml.safe_load(f)

                # Merge user config into default config (user settings take precedence)
                if user_cfg:
                    # Deep merge for nested dictionaries
                    config = _merge_configs(config, user_cfg)
                    logger.info(f"User configuration merged from: {user_config}")

                    # If user selected a model, override primary_model
                    if 'ollama' in user_cfg and 'selected_model' in user_cfg['ollama']:
                        if 'ollama' not in config:
                            config['ollama'] = {}
                        config['ollama']['primary_model'] = user_cfg['ollama']['selected_model']
                        logger.info(f"Using user-selected model: {user_cfg['ollama']['selected_model']}")

            except yaml.YAMLError as e:
                logger.warning(f"Invalid YAML in user configuration file: {e}")
                logger.warning("Falling back to default configuration")
            except Exception as e:
                logger.warning(f"Failed to load user configuration: {e}")
                logger.warning("Falling back to default configuration")

        return config

    else:
        # Custom config path provided
        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            logger.info(f"Configuration loaded from: {config_path}")
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")


def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two configuration dictionaries.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        dict: Merged configuration (override takes precedence)
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = _merge_configs(result[key], value)
        else:
            # Override value
            result[key] = value

    return result


def get_ollama_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract Ollama-specific configuration.

    Args:
        config: Full configuration dictionary

    Returns:
        dict: Ollama configuration section
    """
    ollama_config = config.get('ollama', {})

    # Provide defaults if keys are missing
    defaults = {
        'primary_model': 'llama3.1:8b-instruct-q4_K_M',
        'fallback_model': 'mistral:7b-instruct-q4_K_M',
        'temperature': 0.3,
        'context_window': 8192,
        'auto_download': False,
        'gpu_acceleration': True
    }

    # Merge with defaults
    return {**defaults, **ollama_config}
