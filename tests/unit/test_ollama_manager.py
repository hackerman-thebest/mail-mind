"""
Unit tests for OllamaManager.

Tests Story 1.1: Ollama Integration & Model Setup
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.mailmind.core.ollama_manager import (
    OllamaManager,
    OllamaConnectionError,
    OllamaModelError
)


@pytest.fixture
def mock_config():
    """Provide test configuration"""
    return {
        'primary_model': 'llama3.1:8b-instruct-q4_K_M',
        'fallback_model': 'mistral:7b-instruct-q4_K_M',
        'temperature': 0.3,
        'context_window': 8192
    }


@pytest.fixture
def ollama_manager(mock_config):
    """Provide OllamaManager instance with test config"""
    return OllamaManager(mock_config)


class TestOllamaManagerInitialization:
    """Test OllamaManager initialization"""

    def test_initialization_with_config(self, mock_config):
        """Test that OllamaManager initializes with provided config"""
        manager = OllamaManager(mock_config)

        assert manager.primary_model == 'llama3.1:8b-instruct-q4_K_M'
        assert manager.fallback_model == 'mistral:7b-instruct-q4_K_M'
        assert manager.temperature == 0.3
        assert manager.context_window == 8192
        assert manager.is_connected is False
        assert manager.model_status == "not_initialized"

    def test_initialization_with_defaults(self):
        """Test that OllamaManager uses defaults for missing config"""
        manager = OllamaManager({})

        assert manager.primary_model == 'llama3.1:8b-instruct-q4_K_M'
        assert manager.fallback_model == 'mistral:7b-instruct-q4_K_M'
        assert manager.temperature == 0.3
        assert manager.context_window == 8192


class TestOllamaConnection:
    """Test Ollama service connection"""

    @patch('src.mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    @patch('src.mailmind.core.ollama_manager.ollama')
    def test_connect_success(self, mock_ollama, ollama_manager):
        """Test successful connection to Ollama service"""
        # Mock client and list response
        mock_client = MagicMock()
        mock_client.list.return_value = {
            'models': [
                {'name': 'llama3.1:8b-instruct-q4_K_M'}
            ]
        }
        mock_ollama.Client.return_value = mock_client

        result = ollama_manager.connect()

        assert result is True
        assert ollama_manager.is_connected is True
        assert ollama_manager.current_model == 'llama3.1:8b-instruct-q4_K_M'

    @patch('src.mailmind.core.ollama_manager.OLLAMA_AVAILABLE', False)
    def test_connect_ollama_not_installed(self, ollama_manager):
        """Test connection failure when Ollama is not installed"""
        with pytest.raises(OllamaConnectionError) as exc_info:
            ollama_manager.connect()

        assert "not installed" in str(exc_info.value)
        assert ollama_manager.is_connected is False

    @patch('src.mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    @patch('src.mailmind.core.ollama_manager.ollama')
    def test_connect_service_not_running(self, mock_ollama, ollama_manager):
        """Test connection failure when Ollama service is not running"""
        mock_ollama.Client.side_effect = Exception("Connection refused")

        with pytest.raises(OllamaConnectionError) as exc_info:
            ollama_manager.connect()

        assert "Failed to connect" in str(exc_info.value)
        assert ollama_manager.is_connected is False


class TestModelVerification:
    """Test model verification and fallback logic"""

    @patch('src.mailmind.core.ollama_manager.ollama')
    def test_verify_primary_model_available(self, mock_ollama, ollama_manager):
        """Test model verification when primary model is available"""
        ollama_manager.client = MagicMock()
        ollama_manager.is_connected = True
        ollama_manager.client.list.return_value = {
            'models': [
                {'name': 'llama3.1:8b-instruct-q4_K_M'},
                {'name': 'mistral:7b-instruct-q4_K_M'}
            ]
        }

        result = ollama_manager.verify_model()

        assert result is True
        assert ollama_manager.current_model == 'llama3.1:8b-instruct-q4_K_M'
        assert ollama_manager.model_status == "ready"

    @patch('src.mailmind.core.ollama_manager.ollama')
    def test_verify_fallback_to_mistral(self, mock_ollama, ollama_manager):
        """Test fallback to Mistral when primary model unavailable"""
        ollama_manager.client = MagicMock()
        ollama_manager.is_connected = True
        ollama_manager.client.list.return_value = {
            'models': [
                {'name': 'mistral:7b-instruct-q4_K_M'}
            ]
        }

        result = ollama_manager.verify_model()

        assert result is True
        assert ollama_manager.current_model == 'mistral:7b-instruct-q4_K_M'
        assert ollama_manager.model_status == "ready"

    def test_verify_no_models_available(self, ollama_manager):
        """Test error when no models are available"""
        ollama_manager.client = MagicMock()
        ollama_manager.is_connected = True
        ollama_manager.client.list.return_value = {'models': []}

        with pytest.raises(OllamaModelError) as exc_info:
            ollama_manager.verify_model()

        assert "Neither primary model" in str(exc_info.value)
        assert ollama_manager.model_status == "error"

    def test_verify_not_connected(self, ollama_manager):
        """Test that verification fails if not connected"""
        with pytest.raises(OllamaConnectionError):
            ollama_manager.verify_model()


class TestInference:
    """Test model inference functionality"""

    def test_test_inference_success(self, ollama_manager):
        """Test successful test inference"""
        ollama_manager.client = MagicMock()
        ollama_manager.is_connected = True
        ollama_manager.current_model = 'llama3.1:8b-instruct-q4_K_M'
        ollama_manager.client.generate.return_value = {
            'response': 'Test response',
            'done': True
        }

        result = ollama_manager.test_inference()

        assert result is True
        ollama_manager.client.generate.assert_called_once()

    def test_test_inference_not_connected(self, ollama_manager):
        """Test inference fails when not connected"""
        result = ollama_manager.test_inference()

        assert result is False

    def test_test_inference_exception(self, ollama_manager):
        """Test inference handles exceptions gracefully"""
        ollama_manager.client = MagicMock()
        ollama_manager.is_connected = True
        ollama_manager.current_model = 'llama3.1:8b-instruct-q4_K_M'
        ollama_manager.client.generate.side_effect = Exception("Inference error")

        result = ollama_manager.test_inference()

        assert result is False


class TestModelInfo:
    """Test model information retrieval"""

    def test_get_model_info(self, ollama_manager):
        """Test getting model information"""
        ollama_manager.current_model = 'llama3.1:8b-instruct-q4_K_M'
        ollama_manager.model_status = 'ready'
        ollama_manager.is_connected = True

        info = ollama_manager.get_model_info()

        assert info['current_model'] == 'llama3.1:8b-instruct-q4_K_M'
        assert info['status'] == 'ready'
        assert info['is_connected'] is True
        assert info['temperature'] == 0.3
        assert info['context_window'] == 8192

    def test_get_available_models(self, ollama_manager):
        """Test getting list of available models"""
        ollama_manager.client = MagicMock()
        ollama_manager.is_connected = True
        ollama_manager.client.list.return_value = {
            'models': [
                {'name': 'llama3.1:8b-instruct-q4_K_M'},
                {'name': 'mistral:7b-instruct-q4_K_M'}
            ]
        }

        models = ollama_manager.get_available_models()

        assert len(models) == 2
        assert 'llama3.1:8b-instruct-q4_K_M' in models
        assert 'mistral:7b-instruct-q4_K_M' in models

    def test_get_available_models_not_connected(self, ollama_manager):
        """Test getting models when not connected returns empty list"""
        models = ollama_manager.get_available_models()

        assert models == []


class TestInitialization:
    """Test complete initialization workflow"""

    @patch('src.mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    @patch('src.mailmind.core.ollama_manager.ollama')
    def test_initialize_success(self, mock_ollama, ollama_manager):
        """Test complete successful initialization"""
        mock_client = MagicMock()
        mock_client.list.return_value = {
            'models': [{'name': 'llama3.1:8b-instruct-q4_K_M'}]
        }
        mock_client.generate.return_value = {
            'response': 'Test',
            'done': True
        }
        mock_ollama.Client.return_value = mock_client

        success, message = ollama_manager.initialize()

        assert success is True
        assert "Successfully initialized" in message
        assert ollama_manager.is_connected is True
        assert ollama_manager.current_model == 'llama3.1:8b-instruct-q4_K_M'

    @patch('src.mailmind.core.ollama_manager.OLLAMA_AVAILABLE', False)
    def test_initialize_connection_error(self, ollama_manager):
        """Test initialization fails with connection error"""
        success, message = ollama_manager.initialize()

        assert success is False
        assert "Connection error" in message


class TestDownloadPrompt:
    """Test model download prompting"""

    def test_prompt_model_download_primary(self, ollama_manager):
        """Test download prompt for primary model"""
        message = ollama_manager.prompt_model_download()

        assert 'llama3.1:8b-instruct-q4_K_M' in message
        assert 'ollama pull' in message
        assert '5GB' in message

    def test_prompt_model_download_specific(self, ollama_manager):
        """Test download prompt for specific model"""
        message = ollama_manager.prompt_model_download('custom-model')

        assert 'custom-model' in message
        assert 'ollama pull' in message
