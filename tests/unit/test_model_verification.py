"""
Unit tests for model checksum verification (Story 3.3 AC3).

Tests cover:
- Checksum calculation from blob files
- Verification against known-good hashes
- Graceful degradation for unknown models
- User preferences caching
- Integration with model loading flow
"""

import pytest
import json
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from mailmind.core.ollama_manager import OllamaManager


class TestModelChecksumCalculation:
    """Test checksum calculation helper methods."""

    def test_calculate_file_checksum_small_file(self):
        """Test SHA256 calculation for small file."""
        manager = OllamaManager({'pool_size': 3})

        # Create mock file content
        test_content = b"test model data"
        expected_checksum = hashlib.sha256(test_content).hexdigest()

        with patch('builtins.open', mock_open(read_data=test_content)):
            actual_checksum = manager._calculate_file_checksum(Path('/fake/path'))

        assert actual_checksum == expected_checksum

    def test_calculate_file_checksum_large_file(self):
        """Test SHA256 calculation for large file (chunked reading)."""
        manager = OllamaManager({'pool_size': 3})

        # Create large mock file content (>8KB to test chunking)
        test_content = b"a" * 10000
        expected_checksum = hashlib.sha256(test_content).hexdigest()

        with patch('builtins.open', mock_open(read_data=test_content)):
            actual_checksum = manager._calculate_file_checksum(Path('/fake/path'))

        assert actual_checksum == expected_checksum

    @patch('subprocess.run')
    def test_get_model_blob_path_success(self, mock_run):
        """Test successful blob path extraction from ollama show."""
        manager = OllamaManager({'pool_size': 3})

        # Mock ollama show output
        mock_run.return_value = Mock(
            returncode=0,
            stdout="FROM sha256:abc123def456\nPARAMETER temperature 0.7"
        )

        with patch.object(Path, 'exists', return_value=True):
            blob_path = manager._get_model_blob_path('llama3.1:8b')

        assert blob_path is not None
        assert 'abc123def456' in str(blob_path)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_model_blob_path_command_failed(self, mock_run):
        """Test blob path extraction when ollama show fails."""
        manager = OllamaManager({'pool_size': 3})

        mock_run.return_value = Mock(returncode=1, stderr="error")

        blob_path = manager._get_model_blob_path('invalid-model')

        assert blob_path is None

    @patch('subprocess.run')
    def test_get_model_blob_path_no_from_line(self, mock_run):
        """Test blob path extraction when modelfile has no FROM line."""
        manager = OllamaManager({'pool_size': 3})

        mock_run.return_value = Mock(
            returncode=0,
            stdout="PARAMETER temperature 0.7\nSYSTEM You are helpful"
        )

        blob_path = manager._get_model_blob_path('llama3.1:8b')

        assert blob_path is None

    @patch('subprocess.run')
    def test_get_model_blob_path_timeout(self, mock_run):
        """Test blob path extraction when command times out."""
        import subprocess
        manager = OllamaManager({'pool_size': 3})

        mock_run.side_effect = subprocess.TimeoutExpired('ollama', 10)

        blob_path = manager._get_model_blob_path('llama3.1:8b')

        assert blob_path is None


class TestModelChecksumVerification:
    """Test verify_model_checksum method."""

    def test_verify_checksum_file_missing(self):
        """Test verification when model_checksums.json doesn't exist."""
        manager = OllamaManager({'pool_size': 3})

        with patch.object(Path, 'exists', return_value=False):
            verified, message = manager.verify_model_checksum('llama3.1:8b')

        assert verified is None
        assert 'checksums file missing' in message

    def test_verify_checksum_unknown_model(self):
        """Test verification for model not in checksums.json."""
        manager = OllamaManager({'pool_size': 3})

        checksums_data = {
            'version': '1.0.0',
            'models': {
                'known-model': {'sha256': 'abc123'}
            }
        }

        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(checksums_data))):
                verified, message = manager.verify_model_checksum('unknown-model')

        assert verified is None
        assert 'not in verification database' in message

    def test_verify_checksum_placeholder(self):
        """Test verification when checksum is a placeholder."""
        manager = OllamaManager({'pool_size': 3})

        checksums_data = {
            'version': '1.0.0',
            'models': {
                'llama3.1:8b': {
                    'sha256': 'placeholder_for_actual_checksum',
                    'size_bytes': 4900000000
                }
            }
        }

        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(checksums_data))):
                verified, message = manager.verify_model_checksum('llama3.1:8b')

        assert verified is None
        assert 'placeholder checksum' in message

    @patch('mailmind.core.ollama_manager.OllamaManager._get_model_blob_path')
    def test_verify_checksum_blob_not_found(self, mock_get_blob):
        """Test verification when blob file not found."""
        manager = OllamaManager({'pool_size': 3})
        mock_get_blob.return_value = None

        checksums_data = {
            'version': '1.0.0',
            'models': {
                'llama3.1:8b': {
                    'sha256': 'abc123def456',
                    'size_bytes': 4900000000
                }
            }
        }

        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(checksums_data))):
                verified, message = manager.verify_model_checksum('llama3.1:8b')

        assert verified is None
        assert 'blob file not found' in message

    @patch('mailmind.core.ollama_manager.OllamaManager._get_model_blob_path')
    @patch('mailmind.core.ollama_manager.OllamaManager._calculate_file_checksum')
    def test_verify_checksum_match(self, mock_calculate, mock_get_blob):
        """Test successful checksum verification (match)."""
        manager = OllamaManager({'pool_size': 3})

        expected_checksum = 'abc123def456'
        mock_get_blob.return_value = Path('/fake/blob')
        mock_calculate.return_value = expected_checksum

        checksums_data = {
            'version': '1.0.0',
            'models': {
                'llama3.1:8b': {
                    'sha256': expected_checksum,
                    'size_bytes': 4900000000
                }
            }
        }

        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(checksums_data))):
                verified, message = manager.verify_model_checksum('llama3.1:8b')

        assert verified is True
        assert message == 'verified'

    @patch('mailmind.core.ollama_manager.OllamaManager._get_model_blob_path')
    @patch('mailmind.core.ollama_manager.OllamaManager._calculate_file_checksum')
    def test_verify_checksum_mismatch(self, mock_calculate, mock_get_blob):
        """Test checksum verification failure (tampered model)."""
        manager = OllamaManager({'pool_size': 3})

        expected_checksum = 'abc123def456'
        actual_checksum = 'different_hash_999'

        mock_get_blob.return_value = Path('/fake/blob')
        mock_calculate.return_value = actual_checksum

        checksums_data = {
            'version': '1.0.0',
            'models': {
                'llama3.1:8b': {
                    'sha256': expected_checksum,
                    'size_bytes': 4900000000
                }
            }
        }

        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(checksums_data))):
                verified, message = manager.verify_model_checksum('llama3.1:8b')

        assert verified is False
        assert 'checksum mismatch' in message


class TestVerifiedModelsCache:
    """Test user_preferences caching of verified models."""

    @patch('mailmind.database.DatabaseManager')
    def test_get_verified_models_cache_empty(self, mock_db_class):
        """Test retrieving cache when no models verified yet."""
        manager = OllamaManager({'pool_size': 3})

        mock_db = Mock()
        mock_db.get_preference.return_value = None
        mock_db_class.get_instance.return_value = mock_db

        cache = manager._get_verified_models_cache()

        assert cache == []
        mock_db.get_preference.assert_called_once_with('verified_models')

    @patch('mailmind.database.DatabaseManager')
    def test_get_verified_models_cache_with_models(self, mock_db_class):
        """Test retrieving cache with previously verified models."""
        manager = OllamaManager({'pool_size': 3})

        cached_models = ['llama3.1:8b', 'mistral:7b']
        mock_db = Mock()
        mock_db.get_preference.return_value = json.dumps(cached_models)
        mock_db_class.get_instance.return_value = mock_db

        cache = manager._get_verified_models_cache()

        assert cache == cached_models

    @patch('mailmind.database.DatabaseManager')
    def test_add_to_verified_models_cache_new_model(self, mock_db_class):
        """Test adding new model to cache."""
        manager = OllamaManager({'pool_size': 3})

        existing_cache = ['llama3.1:8b']
        mock_db = Mock()
        mock_db.get_preference.return_value = json.dumps(existing_cache)
        mock_db_class.get_instance.return_value = mock_db

        manager._add_to_verified_models_cache('mistral:7b')

        # Verify set_preference called with updated list
        expected_json = json.dumps(['llama3.1:8b', 'mistral:7b'])
        mock_db.set_preference.assert_called_once_with('verified_models', expected_json)

    @patch('mailmind.database.DatabaseManager')
    def test_add_to_verified_models_cache_duplicate(self, mock_db_class):
        """Test adding model that's already in cache (no-op)."""
        manager = OllamaManager({'pool_size': 3})

        existing_cache = ['llama3.1:8b', 'mistral:7b']
        mock_db = Mock()
        mock_db.get_preference.return_value = json.dumps(existing_cache)
        mock_db_class.get_instance.return_value = mock_db

        manager._add_to_verified_models_cache('mistral:7b')

        # Should not call set_preference since model already in cache
        mock_db.set_preference.assert_not_called()


class TestSecurityVerificationIntegration:
    """Test integration of security verification into model loading."""

    @patch('mailmind.core.ollama_manager.OllamaManager._get_verified_models_cache')
    @patch('mailmind.core.ollama_manager.OllamaManager.verify_model_checksum')
    @patch('mailmind.core.ollama_manager.OllamaManager._add_to_verified_models_cache')
    def test_verify_model_security_cached(self, mock_add_cache, mock_verify_checksum, mock_get_cache):
        """Test security verification skipped for cached models."""
        manager = OllamaManager({'pool_size': 3})

        # Model already in cache
        mock_get_cache.return_value = ['llama3.1:8b']

        manager._verify_model_security('llama3.1:8b')

        # Should not call verify_model_checksum since cached
        mock_verify_checksum.assert_not_called()
        mock_add_cache.assert_not_called()

    @patch('mailmind.core.ollama_manager.OllamaManager._get_verified_models_cache')
    @patch('mailmind.core.ollama_manager.OllamaManager.verify_model_checksum')
    @patch('mailmind.core.ollama_manager.OllamaManager._add_to_verified_models_cache')
    def test_verify_model_security_success(self, mock_add_cache, mock_verify_checksum, mock_get_cache):
        """Test security verification for new model (verification passes)."""
        manager = OllamaManager({'pool_size': 3})

        mock_get_cache.return_value = []
        mock_verify_checksum.return_value = (True, 'verified')

        manager._verify_model_security('llama3.1:8b')

        mock_verify_checksum.assert_called_once_with('llama3.1:8b')
        mock_add_cache.assert_called_once_with('llama3.1:8b')

    @patch('mailmind.core.ollama_manager.OllamaManager._get_verified_models_cache')
    @patch('mailmind.core.ollama_manager.OllamaManager.verify_model_checksum')
    @patch('mailmind.core.ollama_manager.OllamaManager._add_to_verified_models_cache')
    def test_verify_model_security_mismatch(self, mock_add_cache, mock_verify_checksum, mock_get_cache):
        """Test security verification for tampered model (logs warning, allows usage)."""
        manager = OllamaManager({'pool_size': 3})

        mock_get_cache.return_value = []
        mock_verify_checksum.return_value = (False, 'checksum mismatch')

        # Should not raise exception (graceful degradation)
        manager._verify_model_security('llama3.1:8b')

        mock_verify_checksum.assert_called_once_with('llama3.1:8b')
        # Should NOT add to cache when checksum fails
        mock_add_cache.assert_not_called()

    @patch('mailmind.core.ollama_manager.OllamaManager._get_verified_models_cache')
    @patch('mailmind.core.ollama_manager.OllamaManager.verify_model_checksum')
    def test_verify_model_security_unknown_model(self, mock_verify_checksum, mock_get_cache):
        """Test security verification for unknown model (graceful degradation)."""
        manager = OllamaManager({'pool_size': 3})

        mock_get_cache.return_value = []
        mock_verify_checksum.return_value = (None, 'unknown model')

        # Should not raise exception
        manager._verify_model_security('custom-model:latest')

        mock_verify_checksum.assert_called_once_with('custom-model:latest')

    @patch('mailmind.core.ollama_manager.OllamaManager._get_verified_models_cache')
    @patch('mailmind.core.ollama_manager.OllamaManager.verify_model_checksum')
    def test_verify_model_security_exception(self, mock_verify_checksum, mock_get_cache):
        """Test security verification handles exceptions gracefully."""
        manager = OllamaManager({'pool_size': 3})

        mock_get_cache.return_value = []
        mock_verify_checksum.side_effect = Exception("Unexpected error")

        # Should not raise exception (graceful degradation)
        manager._verify_model_security('llama3.1:8b')

        # Exception should be caught and logged


class TestEndToEndModelVerification:
    """Test full model verification flow integrated into verify_model()."""

    @patch('ollama.Client')
    @patch('mailmind.core.ollama_manager.OllamaManager._verify_model_security')
    def test_verify_model_calls_security_verification(self, mock_security_verify, mock_client_class):
        """Test that verify_model() calls security verification."""
        manager = OllamaManager({
            'pool_size': 3,
            'primary_model': 'llama3.1:8b',
            'fallback_model': 'mistral:7b'
        })
        manager.is_connected = True

        mock_client = Mock()
        mock_client.list.return_value = {
            'models': [{'name': 'llama3.1:8b'}]
        }
        manager.client = mock_client

        result = manager.verify_model()

        assert result is True
        mock_security_verify.assert_called_once_with('llama3.1:8b')

    @patch('ollama.Client')
    @patch('mailmind.core.ollama_manager.OllamaManager._get_verified_models_cache')
    @patch('mailmind.core.ollama_manager.OllamaManager.verify_model_checksum')
    def test_verify_model_security_failure_does_not_block(self, mock_verify_checksum, mock_get_cache, mock_client_class):
        """Test that security verification failure doesn't block model loading."""
        manager = OllamaManager({
            'pool_size': 3,
            'primary_model': 'llama3.1:8b',
            'fallback_model': 'mistral:7b'
        })

        # Set connected state and mock client
        manager.is_connected = True
        mock_client = Mock()
        mock_client.list.return_value = {
            'models': [{'name': 'llama3.1:8b'}]
        }
        manager.client = mock_client

        # Mock cache to return empty (model not cached)
        mock_get_cache.return_value = []

        # Security verification raises exception (should not block loading)
        mock_verify_checksum.side_effect = Exception("Security check failed")

        # Provide models_response to avoid re-calling list()
        models_response = {'models': [{'name': 'llama3.1:8b'}]}
        result = manager.verify_model(models_response)

        # Should still succeed despite security check exception (graceful degradation)
        assert result is True
        assert manager.model_status == 'ready'
        mock_verify_checksum.assert_called_once_with('llama3.1:8b')
