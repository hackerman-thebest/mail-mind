"""
Core functionality for MailMind.

This package contains the core business logic including AI integration,
email processing, and data management.
"""

from .ollama_manager import OllamaManager, OllamaConnectionError, OllamaModelError

__all__ = ['OllamaManager', 'OllamaConnectionError', 'OllamaModelError']
