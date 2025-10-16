"""
Unit Tests for KeyManager

Tests Story 3.1 AC2: Windows DPAPI Key Management
- Key generation (32-byte random keys)
- DPAPI protection/unprotection
- PBKDF2 key derivation (100K iterations, SHA-256)
- Windows Credential Manager storage
- Salt management via user_preferences
- Error handling and edge cases

Test Coverage:
- Key generation: random, unique, correct length
- DPAPI operations: protect, unprotect, roundtrip
- PBKDF2 derivation: deterministic, correct length
- Salt operations: generate, store, retrieve
- Credential Manager: store, retrieve, delete
- Integration: get_or_create_key flow
- Error handling: platform support, missing dependencies
"""

import os
import sys
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import KeyManager
from mailmind.core import key_manager
from mailmind.core.key_manager import (
    KeyManager,
    KeyManagementError,
    KeyGenerationError,
    KeyRetrievalError,
    KeyStorageError,
    is_encryption_supported,
    get_key_manager
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_db_manager():
    """Mock DatabaseManager for testing."""
    db_mgr = Mock()
    db_mgr.get_preference = Mock(return_value=None)
    db_mgr.set_preference = Mock()
    return db_mgr


@pytest.fixture
def temp_db_path():
    """Temporary database path for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


# ============================================================================
# Platform Detection Tests
# ============================================================================

class TestPlatformDetection:
    """Test platform detection and DPAPI availability."""

    def test_platform_detection(self):
        """Test platform detection is accurate."""
        # IS_WINDOWS should be True on Windows, False elsewhere
        assert isinstance(key_manager.IS_WINDOWS, bool)
        assert key_manager.IS_WINDOWS == (sys.platform == "win32")

    def test_dpapi_available_flag(self):
        """Test DPAPI_AVAILABLE flag is set correctly."""
        assert isinstance(key_manager.DPAPI_AVAILABLE, bool)

        # On Windows with pywin32, should be True
        # On other platforms or without pywin32, should be False
        if sys.platform == "win32":
            # May be True or False depending on pywin32 installation
            pass
        else:
            # Non-Windows platforms should have DPAPI_AVAILABLE = False
            assert key_manager.DPAPI_AVAILABLE == False

    def test_is_encryption_supported(self):
        """Test is_encryption_supported() function."""
        result = is_encryption_supported()
        assert isinstance(result, bool)
        assert result == key_manager.DPAPI_AVAILABLE


# ============================================================================
# KeyManager Initialization Tests
# ============================================================================

class TestKeyManagerInit:
    """Test KeyManager initialization."""

    def test_init_without_db_manager(self):
        """Test KeyManager initialization without db_manager."""
        km = KeyManager()
        assert km.db_manager is None
        assert km._cached_key is None

    def test_init_with_db_manager(self, mock_db_manager):
        """Test KeyManager initialization with db_manager."""
        km = KeyManager(db_manager=mock_db_manager)
        assert km.db_manager is mock_db_manager
        assert km._cached_key is None

    def test_init_constants(self):
        """Test KeyManager constants are correct."""
        km = KeyManager()
        assert km.CREDENTIAL_TARGET == "MailMind_DatabaseEncryptionKey"
        assert km.PBKDF2_ITERATIONS == 100000
        assert km.SALT_LENGTH == 16
        assert km.DPAPI_KEY_LENGTH == 32
        assert km.SQLCIPHER_KEY_LENGTH == 64

    def test_is_encryption_available(self):
        """Test is_encryption_available() method."""
        km = KeyManager()
        result = km.is_encryption_available()
        assert isinstance(result, bool)
        assert result == key_manager.DPAPI_AVAILABLE


# ============================================================================
# Key Generation Tests
# ============================================================================

class TestKeyGeneration:
    """Test key generation functionality."""

    def test_generate_dpapi_key_length(self):
        """Test generated keys have correct length."""
        km = KeyManager()
        key = km._generate_dpapi_key()

        assert isinstance(key, bytes)
        assert len(key) == 32  # 32 bytes = 256 bits

    def test_generate_dpapi_key_uniqueness(self):
        """Test generated keys are unique."""
        km = KeyManager()

        key1 = km._generate_dpapi_key()
        key2 = km._generate_dpapi_key()

        assert key1 != key2  # Should be different (cryptographically random)

    def test_generate_dpapi_key_randomness(self):
        """Test generated keys are cryptographically random."""
        km = KeyManager()

        # Generate 10 keys
        keys = [km._generate_dpapi_key() for _ in range(10)]

        # All should be different
        assert len(set(keys)) == 10

        # Should not be all zeros or all ones
        for key in keys:
            assert key != b'\x00' * 32
            assert key != b'\xff' * 32


# ============================================================================
# PBKDF2 Key Derivation Tests
# ============================================================================

class TestPBKDF2Derivation:
    """Test PBKDF2 key derivation."""

    def test_derive_sqlcipher_key_length(self):
        """Test derived key has correct length."""
        km = KeyManager()

        dpapi_key = b'test_key_32_bytes_long_______'  # 32 bytes
        salt = b'test_salt_16byte'  # 16 bytes

        derived = km._derive_sqlcipher_key(dpapi_key, salt)

        assert isinstance(derived, bytes)
        assert len(derived) == 64  # 64 bytes = 512 bits

    def test_derive_sqlcipher_key_deterministic(self):
        """Test key derivation is deterministic (same inputs = same output)."""
        km = KeyManager()

        dpapi_key = b'test_key_32_bytes_long_______'
        salt = b'test_salt_16byte'

        derived1 = km._derive_sqlcipher_key(dpapi_key, salt)
        derived2 = km._derive_sqlcipher_key(dpapi_key, salt)

        assert derived1 == derived2  # Should be identical

    def test_derive_sqlcipher_key_different_inputs(self):
        """Test different inputs produce different outputs."""
        km = KeyManager()

        dpapi_key1 = b'test_key_32_bytes_long_____01'
        dpapi_key2 = b'test_key_32_bytes_long_____02'
        salt = b'test_salt_16byte'

        derived1 = km._derive_sqlcipher_key(dpapi_key1, salt)
        derived2 = km._derive_sqlcipher_key(dpapi_key2, salt)

        assert derived1 != derived2  # Different keys = different outputs

    def test_derive_sqlcipher_key_different_salts(self):
        """Test different salts produce different outputs."""
        km = KeyManager()

        dpapi_key = b'test_key_32_bytes_long_______'
        salt1 = b'test_salt_16byt1'
        salt2 = b'test_salt_16byt2'

        derived1 = km._derive_sqlcipher_key(dpapi_key, salt1)
        derived2 = km._derive_sqlcipher_key(dpapi_key, salt2)

        assert derived1 != derived2  # Different salts = different outputs


# ============================================================================
# Salt Management Tests
# ============================================================================

class TestSaltManagement:
    """Test salt generation and storage."""

    def test_get_or_generate_salt_without_db_manager(self):
        """Test salt generation without db_manager (ephemeral)."""
        km = KeyManager(db_manager=None)

        salt = km._get_or_generate_salt()

        assert isinstance(salt, bytes)
        assert len(salt) == 16  # 16 bytes = 128 bits

    def test_get_or_generate_salt_generates_new(self, mock_db_manager):
        """Test salt generation when no salt exists."""
        mock_db_manager.get_preference.return_value = None
        km = KeyManager(db_manager=mock_db_manager)

        salt = km._get_or_generate_salt()

        assert isinstance(salt, bytes)
        assert len(salt) == 16

        # Should have called set_preference to store salt
        mock_db_manager.set_preference.assert_called_once()
        call_args = mock_db_manager.set_preference.call_args
        assert call_args[0][0] == "encryption_salt"
        assert isinstance(call_args[0][1], str)  # Base64-encoded

    def test_get_or_generate_salt_retrieves_existing(self, mock_db_manager):
        """Test salt retrieval when salt exists."""
        import base64

        # Simulate existing salt
        existing_salt = os.urandom(16)
        salt_b64 = base64.b64encode(existing_salt).decode('ascii')
        mock_db_manager.get_preference.return_value = salt_b64

        km = KeyManager(db_manager=mock_db_manager)
        salt = km._get_or_generate_salt()

        assert salt == existing_salt

        # Should NOT have called set_preference
        mock_db_manager.set_preference.assert_not_called()

    def test_salt_uniqueness(self):
        """Test generated salts are unique."""
        km = KeyManager()

        salt1 = km._get_or_generate_salt()
        salt2 = km._get_or_generate_salt()

        assert salt1 != salt2  # Should be different


# ============================================================================
# DPAPI Operations Tests (Windows-only, mocked elsewhere)
# ============================================================================

class TestDPAPIOperations:
    """Test DPAPI protect/unprotect operations."""

    @pytest.mark.skipif(not key_manager.DPAPI_AVAILABLE, reason="DPAPI not available")
    def test_protect_with_dpapi(self):
        """Test DPAPI protection (Windows only)."""
        km = KeyManager()

        data = b"test_data_to_protect"
        protected = km._protect_with_dpapi(data)

        assert isinstance(protected, bytes)
        assert protected != data  # Should be encrypted
        assert len(protected) > len(data)  # DPAPI adds overhead

    @pytest.mark.skipif(not key_manager.DPAPI_AVAILABLE, reason="DPAPI not available")
    def test_unprotect_with_dpapi(self):
        """Test DPAPI unprotection (Windows only)."""
        km = KeyManager()

        data = b"test_data_to_protect"
        protected = km._protect_with_dpapi(data)
        unprotected = km._unprotect_with_dpapi(protected)

        assert unprotected == data  # Should match original

    @pytest.mark.skipif(not key_manager.DPAPI_AVAILABLE, reason="DPAPI not available")
    def test_dpapi_roundtrip(self):
        """Test DPAPI protect/unprotect roundtrip (Windows only)."""
        km = KeyManager()

        original = b"secret_data_" + os.urandom(16)
        protected = km._protect_with_dpapi(original)
        recovered = km._unprotect_with_dpapi(protected)

        assert recovered == original

    def test_protect_without_dpapi_raises_error(self):
        """Test DPAPI protection fails gracefully without DPAPI."""
        if key_manager.DPAPI_AVAILABLE:
            pytest.skip("DPAPI available - cannot test error case")

        km = KeyManager()

        with pytest.raises(KeyStorageError):
            km._protect_with_dpapi(b"test_data")

    def test_unprotect_without_dpapi_raises_error(self):
        """Test DPAPI unprotection fails gracefully without DPAPI."""
        if key_manager.DPAPI_AVAILABLE:
            pytest.skip("DPAPI available - cannot test error case")

        km = KeyManager()

        with pytest.raises(KeyRetrievalError):
            km._unprotect_with_dpapi(b"test_data")


# ============================================================================
# Convenience Functions Tests
# ============================================================================

class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_key_manager_factory(self):
        """Test get_key_manager factory function."""
        km = get_key_manager()

        assert isinstance(km, KeyManager)
        assert km.db_manager is None

    def test_get_key_manager_with_db_manager(self, mock_db_manager):
        """Test get_key_manager with db_manager parameter."""
        km = get_key_manager(db_manager=mock_db_manager)

        assert isinstance(km, KeyManager)
        assert km.db_manager is mock_db_manager


# ============================================================================
# Integration Tests
# ============================================================================

class TestKeyManagerIntegration:
    """Integration tests for KeyManager."""

    def test_get_or_create_key_without_dpapi(self):
        """Test get_or_create_key returns None without DPAPI."""
        if key_manager.DPAPI_AVAILABLE:
            pytest.skip("DPAPI available - cannot test non-DPAPI case")

        km = KeyManager()
        result = km.get_or_create_key()

        assert result is None

    def test_cached_key(self, mock_db_manager):
        """Test key caching works correctly."""
        if not key_manager.DPAPI_AVAILABLE:
            pytest.skip("DPAPI not available")

        km = KeyManager(db_manager=mock_db_manager)

        # Mock the internal methods
        with patch.object(km, '_retrieve_dpapi_key', return_value=b'test_key_32_bytes_long_______'):
            with patch.object(km, '_get_or_generate_salt', return_value=b'test_salt_16byte'):
                # First call
                key1 = km.get_or_create_key()

                # Second call (should use cache)
                key2 = km.get_or_create_key()

                assert key1 == key2
                assert km._cached_key is not None

    def test_delete_key_clears_cache(self):
        """Test delete_key clears cached key."""
        if not key_manager.DPAPI_AVAILABLE:
            pytest.skip("DPAPI not available")

        km = KeyManager()
        km._cached_key = "cached_key_value"

        with patch('mailmind.core.key_manager.win32cred.CredDelete', side_effect=Exception("Not found")):
            try:
                km.delete_key()
            except:
                pass

        # Cache should be cleared
        assert km._cached_key is None


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_key_generation_error_handling(self):
        """Test error handling in key generation."""
        km = KeyManager()

        with patch('os.urandom', side_effect=Exception("Random generation failed")):
            with pytest.raises(KeyGenerationError):
                km._generate_dpapi_key()

    def test_key_derivation_error_handling(self):
        """Test error handling in key derivation."""
        km = KeyManager()

        with patch('hashlib.pbkdf2_hmac', side_effect=Exception("Derivation failed")):
            with pytest.raises(KeyManagementError):
                km._derive_sqlcipher_key(b'key' * 10, b'salt' * 4)

    def test_rotate_key_not_implemented(self):
        """Test key rotation raises NotImplementedError."""
        km = KeyManager()

        with pytest.raises(NotImplementedError):
            km.rotate_key("old_key_hex")


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests for key operations."""

    def test_key_generation_performance(self):
        """Test key generation is fast (<10ms)."""
        import time

        km = KeyManager()

        start = time.time()
        for _ in range(100):
            km._generate_dpapi_key()
        elapsed = time.time() - start

        # 100 keys in <100ms = <1ms per key
        assert elapsed < 0.1, f"Key generation too slow: {elapsed:.3f}s for 100 keys"

    def test_pbkdf2_derivation_performance(self):
        """Test PBKDF2 derivation completes in reasonable time (<500ms)."""
        import time

        km = KeyManager()
        dpapi_key = b'test_key_32_bytes_long_______'
        salt = b'test_salt_16byte'

        start = time.time()
        km._derive_sqlcipher_key(dpapi_key, salt)
        elapsed = time.time() - start

        # 100K iterations should complete in <500ms on modern hardware
        assert elapsed < 0.5, f"PBKDF2 derivation too slow: {elapsed:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
