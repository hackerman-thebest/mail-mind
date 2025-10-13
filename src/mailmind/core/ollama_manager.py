"""
Ollama Manager - Local LLM Integration

Manages connection to Ollama service, model verification, and inference calls.
Implements Story 1.1: Ollama Integration & Model Setup
"""

import logging
import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class OllamaConnectionError(Exception):
    """Raised when Ollama service is not available"""
    pass


class OllamaModelError(Exception):
    """Raised when model is not available or fails to load"""
    pass


class OllamaManager:
    """
    Manages Ollama client connection, model management, and inference.

    Responsible for:
    - Connecting to local Ollama service
    - Verifying and downloading models
    - Running test inference
    - Providing model status information
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama Manager with configuration.

        Args:
            config: Configuration dictionary with ollama settings
        """
        self.client: Optional[ollama.Client] = None
        self.config = config

        # Model configuration
        self.primary_model = config.get('primary_model', 'llama3.1:8b-instruct-q4_K_M')
        self.fallback_model = config.get('fallback_model', 'mistral:7b-instruct-q4_K_M')
        self.current_model = None

        # Inference parameters
        self.temperature = config.get('temperature', 0.3)
        self.context_window = config.get('context_window', 8192)

        # Status
        self.is_connected = False
        self.model_status = "not_initialized"  # not_initialized, ready, loading, error

        logger.info(f"OllamaManager initialized with model: {self.primary_model}")

    def connect(self) -> bool:
        """
        Establish connection to Ollama service.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            OllamaConnectionError: If Ollama is not installed or not running
        """
        if not OLLAMA_AVAILABLE:
            error_msg = (
                "Ollama Python client not installed. "
                "Please install with: pip install ollama"
            )
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg)

        try:
            logger.info("Attempting to connect to Ollama service...")
            self.client = ollama.Client()

            # Test connection and get available models in one call
            start_time = time.time()
            models_response = self.client.list()
            connection_time = time.time() - start_time

            self.is_connected = True
            logger.info(f"Connected to Ollama service in {connection_time:.3f}s")

            # Verify model availability (pass models_response to avoid duplicate call)
            return self.verify_model(models_response)

        except Exception as e:
            self.is_connected = False
            error_msg = (
                f"Failed to connect to Ollama service: {e}\n\n"
                "Please ensure:\n"
                "1. Ollama is installed (https://ollama.com/download)\n"
                "2. Ollama service is running\n"
                "3. Run 'ollama serve' in a terminal if not running"
            )
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg)

    def verify_model(self, models_response: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if the primary model is available. If not, check fallback.

        Args:
            models_response: Optional cached models list response from Ollama.
                           If None, will fetch models from Ollama.

        Returns:
            bool: True if a model is available, False otherwise

        Raises:
            OllamaModelError: If no models are available
        """
        if not self.is_connected:
            raise OllamaConnectionError("Not connected to Ollama service")

        try:
            self.model_status = "loading"
            logger.info(f"Verifying model availability: {self.primary_model}")

            # Get list of available models (use cached response if provided)
            if models_response is None:
                models_response = self.client.list()
            available_models = [m['name'] for m in models_response.get('models', [])]

            logger.debug(f"Available models: {available_models}")

            # Check primary model
            if self.primary_model in available_models:
                self.current_model = self.primary_model
                self.model_status = "ready"
                logger.info(f"Primary model verified: {self.primary_model}")
                return True

            # Check fallback model
            if self.fallback_model in available_models:
                self.current_model = self.fallback_model
                self.model_status = "ready"
                logger.warning(
                    f"Primary model not found. Using fallback: {self.fallback_model}"
                )
                return True

            # No models available
            self.model_status = "error"
            error_msg = (
                f"Neither primary model ({self.primary_model}) nor "
                f"fallback model ({self.fallback_model}) are available.\n\n"
                f"Available models: {', '.join(available_models) if available_models else 'None'}\n\n"
                "To download the primary model, run:\n"
                f"  ollama pull {self.primary_model}"
            )
            logger.error(error_msg)
            raise OllamaModelError(error_msg)

        except ollama.ResponseError as e:
            self.model_status = "error"
            logger.error(f"Failed to verify model: {e}")
            raise OllamaModelError(f"Model verification failed: {e}")

    def test_inference(self) -> bool:
        """
        Run a test inference call to verify the model works correctly.

        Returns:
            bool: True if test successful, False otherwise
        """
        if not self.is_connected or not self.current_model:
            logger.error("Cannot test inference: not connected or no model loaded")
            return False

        try:
            logger.info(f"Running test inference with {self.current_model}...")
            start_time = time.time()

            response = self.client.generate(
                model=self.current_model,
                prompt="Test",
                options={
                    "temperature": self.temperature,
                    "num_ctx": self.context_window
                }
            )

            inference_time = time.time() - start_time

            if response and 'response' in response:
                logger.info(
                    f"Test inference successful in {inference_time:.3f}s. "
                    f"Generated {len(response['response'])} characters."
                )
                return True
            else:
                logger.error("Test inference failed: no response received")
                return False

        except Exception as e:
            logger.error(f"Test inference failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            dict: Model information including name, status, parameters
        """
        return {
            'current_model': self.current_model,
            'primary_model': self.primary_model,
            'fallback_model': self.fallback_model,
            'status': self.model_status,
            'is_connected': self.is_connected,
            'temperature': self.temperature,
            'context_window': self.context_window
        }

    def get_available_models(self) -> list:
        """
        Get list of all available models in Ollama.

        Returns:
            list: List of model names
        """
        if not self.is_connected:
            return []

        try:
            models_response = self.client.list()
            return [m['name'] for m in models_response.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []

    def prompt_model_download(self, model_name: Optional[str] = None) -> str:
        """
        Generate user-friendly message prompting model download.

        Args:
            model_name: Model to download (defaults to primary_model)

        Returns:
            str: User-friendly download instruction message
        """
        model = model_name or self.primary_model
        return (
            f"Model '{model}' is not available.\n\n"
            "To download this model, run the following command in your terminal:\n"
            f"  ollama pull {model}\n\n"
            f"Model size: approximately 5GB\n"
            "This is a one-time download and will be stored locally."
        )

    def initialize(self) -> Tuple[bool, str]:
        """
        Complete initialization: connect, verify model, test inference.

        Returns:
            Tuple[bool, str]: (success: bool, message: str)
        """
        try:
            # Step 1: Connect to Ollama
            logger.info("Starting Ollama initialization...")
            self.connect()

            # Step 2: Test inference
            if not self.test_inference():
                return False, "Model loaded but test inference failed"

            logger.info("Ollama initialization complete!")
            return True, f"Successfully initialized with model: {self.current_model}"

        except OllamaConnectionError as e:
            return False, f"Connection error: {str(e)}"
        except OllamaModelError as e:
            return False, f"Model error: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error during initialization")
            return False, f"Unexpected error: {str(e)}"
