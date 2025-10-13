"""
Utility functions and helpers for MailMind.
"""

from .config import load_config, get_ollama_config, ConfigurationError

__all__ = ['load_config', 'get_ollama_config', 'ConfigurationError']
