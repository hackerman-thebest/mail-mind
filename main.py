"""
MailMind - Main Application Entry Point

This is a basic example demonstrating Ollama integration from Story 1.1.
Full UI and email integration will be added in subsequent stories.
"""

import logging
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mailmind.utils.config import load_config, get_ollama_config
from mailmind.core.ollama_manager import OllamaManager, OllamaConnectionError, OllamaModelError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Main application entry point.

    Currently demonstrates Story 1.1: Ollama Integration
    """
    logger.info("Starting MailMind...")
    logger.info("=" * 60)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        ollama_config = get_ollama_config(config)

        logger.info(f"Primary model: {ollama_config['primary_model']}")
        logger.info(f"Fallback model: {ollama_config['fallback_model']}")
        logger.info("=" * 60)

        # Initialize Ollama Manager
        logger.info("Initializing Ollama Manager...")
        ollama_manager = OllamaManager(ollama_config)

        # Attempt to connect and initialize
        success, message = ollama_manager.initialize()

        if success:
            logger.info("✓ Ollama initialization successful!")
            logger.info("=" * 60)

            # Display model information
            model_info = ollama_manager.get_model_info()
            logger.info("Model Information:")
            logger.info(f"  Current Model: {model_info['current_model']}")
            logger.info(f"  Status: {model_info['status']}")
            logger.info(f"  Temperature: {model_info['temperature']}")
            logger.info(f"  Context Window: {model_info['context_window']}")

            # Display available models
            available_models = ollama_manager.get_available_models()
            logger.info(f"\nAvailable Models ({len(available_models)}):")
            for model in available_models:
                logger.info(f"  - {model}")

            logger.info("=" * 60)
            logger.info("✓ Story 1.1 (Ollama Integration) complete!")
            logger.info("Ready for Story 1.2 (Email Preprocessing)")
            return 0

        else:
            logger.error(f"✗ Initialization failed: {message}")
            logger.error("=" * 60)
            return 1

    except OllamaConnectionError as e:
        logger.error(f"✗ Connection Error: {e}")
        return 1

    except OllamaModelError as e:
        logger.error(f"✗ Model Error: {e}")
        return 1

    except Exception as e:
        logger.exception(f"✗ Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
