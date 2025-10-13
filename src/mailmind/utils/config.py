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

    Args:
        config_path: Path to configuration file. If None, uses default config.

    Returns:
        dict: Configuration dictionary

    Raises:
        ConfigurationError: If config file cannot be loaded or is invalid
    """
    if config_path is None:
        # Use default config
        default_config = Path(__file__).parent.parent.parent.parent / "config" / "default.yaml"
        config_path = str(default_config)

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
