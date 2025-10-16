"""
Key Management for Database Encryption

Provides Windows DPAPI-based key management for SQLCipher database encryption.
Implements secure key generation, storage, and derivation using DPAPI and PBKDF2.

Story 3.1 AC2: Windows DPAPI Key Management
- Generate random 32-byte keys
- Protect keys with Windows DPAPI (CryptProtectData/CryptUnprotectData)
- Derive 64-byte SQLCipher keys using PBKDF2 (100K iterations, SHA-256)
- Store DPAPI-protected keys in Windows Credential Manager
- Store salt in user_preferences table for key derivation

Security Features:
- No hardcoded keys (AC2)
- Keys tied to user account + machine (DPAPI security model)
- PBKDF2 adds additional security layer
- Salt randomization prevents rainbow table attacks

Platform Support:
- Windows 10/11: Full support via pywin32
- macOS/Linux: Graceful degradation (encryption disabled)
"""

import os
import sys
import logging
import hashlib
import base64
from typing import Optional, Tuple
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Platform detection
IS_WINDOWS = sys.platform == "win32"

# Import Windows-specific modules
if IS_WINDOWS:
    try:
        import win32crypt
        import win32cred
        import pywintypes
        DPAPI_AVAILABLE = True
    except ImportError:
        logger.warning("pywin32 not available - encryption will be disabled")
        DPAPI_AVAILABLE = False
else:
    DPAPI_AVAILABLE = False
    logger.info(f"Platform {sys.platform} does not support DPAPI - encryption will be disabled")


# ============================================================================
# Exception Classes
# ============================================================================

class KeyManagementError(Exception):
    """Base exception for key management errors."""
    pass


class KeyGenerationError(KeyManagementError):
    """Raised when key generation fails."""
    pass


class KeyRetrievalError(KeyManagementError):
    """Raised when key retrieval fails."""
    pass


class KeyStorageError(KeyManagementError):
    """Raised when key storage fails."""
    pass


# ============================================================================
# KeyManager Class
# ============================================================================

class KeyManager:
    """
    Manages encryption keys using Windows DPAPI and PBKDF2 key derivation.

    Key Management Flow:
    1. Generate random 32-byte key
    2. Protect with Windows DPAPI (CryptProtectData)
    3. Store in Windows Credential Manager
    4. Retrieve salt from user_preferences (or generate new)
    5. Derive 64-byte SQLCipher key using PBKDF2(DPAPI_key, salt, 100K iterations)
    6. Return hex-encoded key for SQLCipher PRAGMA key command

    Storage:
    - DPAPI-protected key: Windows Credential Manager (target: "MailMind_DatabaseEncryptionKey")
    - Salt: user_preferences table (key: "encryption_salt", base64-encoded 16 bytes)

    Attributes:
        credential_target (str): Windows Credential Manager target name
        pbkdf2_iterations (int): PBKDF2 iteration count (100,000 recommended)
        salt_length (int): Salt length in bytes (16 bytes = 128 bits)
        key_length (int): Derived key length for SQLCipher (64 bytes = 512 bits)
    """

    # Constants
    CREDENTIAL_TARGET = "MailMind_DatabaseEncryptionKey"
    PBKDF2_ITERATIONS = 100000  # 100K iterations (AC2 requirement)
    SALT_LENGTH = 16  # 16 bytes = 128 bits
    DPAPI_KEY_LENGTH = 32  # 32 bytes = 256 bits
    SQLCIPHER_KEY_LENGTH = 64  # 64 bytes = 512 bits (SQLCipher default)

    def __init__(self, db_manager=None):
        """
        Initialize KeyManager.

        Args:
            db_manager: DatabaseManager instance for salt storage (optional, can be set later)
        """
        self.db_manager = db_manager
        self._cached_key = None  # Cache derived key for performance

        # Check platform support
        if not DPAPI_AVAILABLE:
            logger.warning(
                "DPAPI not available on this platform. "
                "Database encryption will be disabled. "
                "Windows 10/11 required for encryption support."
            )

    def is_encryption_available(self) -> bool:
        """
        Check if encryption is available on this platform.

        Returns:
            bool: True if DPAPI available (Windows), False otherwise
        """
        return DPAPI_AVAILABLE

    def get_or_create_key(self) -> Optional[str]:
        """
        Get existing encryption key or create new one if doesn't exist.

        Returns hex-encoded 64-byte SQLCipher key ready for PRAGMA key command.

        Flow:
        1. Check if key exists in cache
        2. Check if key exists in Credential Manager
        3. If exists: Retrieve and derive SQLCipher key
        4. If not exists: Generate new key, store, derive SQLCipher key
        5. Cache and return derived key

        Returns:
            str: Hex-encoded 64-byte key (128 hex characters), or None if encryption unavailable

        Raises:
            KeyManagementError: If key operations fail
        """
        # Return cached key if available
        if self._cached_key:
            logger.debug("Using cached encryption key")
            return self._cached_key

        # Check platform support
        if not DPAPI_AVAILABLE:
            logger.info("Encryption not available on this platform")
            return None

        try:
            # Try to retrieve existing key from Credential Manager
            dpapi_key = self._retrieve_dpapi_key()

            if dpapi_key is None:
                # No existing key - generate new one
                logger.info("No existing encryption key found - generating new key")
                dpapi_key = self._generate_and_store_dpapi_key()
            else:
                logger.debug("Retrieved existing encryption key from Credential Manager")

            # Get or generate salt
            salt = self._get_or_generate_salt()

            # Derive SQLCipher key using PBKDF2
            sqlcipher_key = self._derive_sqlcipher_key(dpapi_key, salt)

            # Convert to hex for SQLCipher PRAGMA key command
            key_hex = sqlcipher_key.hex()

            # Cache for performance
            self._cached_key = key_hex

            logger.info("Encryption key ready (64 bytes, 128 hex chars)")
            return key_hex

        except Exception as e:
            logger.error(f"Failed to get or create encryption key: {e}", exc_info=True)
            raise KeyManagementError(f"Key management failed: {e}")

    def _generate_dpapi_key(self) -> bytes:
        """
        Generate random 32-byte (256-bit) key.

        Returns:
            bytes: Random 32-byte key

        Raises:
            KeyGenerationError: If key generation fails
        """
        try:
            # Use os.urandom for cryptographically secure random bytes
            key = os.urandom(self.DPAPI_KEY_LENGTH)
            logger.debug(f"Generated {self.DPAPI_KEY_LENGTH}-byte random key")
            return key
        except Exception as e:
            raise KeyGenerationError(f"Failed to generate random key: {e}")

    def _protect_with_dpapi(self, data: bytes) -> bytes:
        """
        Protect data using Windows DPAPI.

        Args:
            data: Raw bytes to protect

        Returns:
            bytes: DPAPI-protected data

        Raises:
            KeyStorageError: If DPAPI protection fails
        """
        if not DPAPI_AVAILABLE:
            raise KeyStorageError("DPAPI not available on this platform")

        try:
            # Protect data with DPAPI
            # CryptProtectData(data, description, entropy, reserved, prompt_struct, flags)
            protected = win32crypt.CryptProtectData(
                data,
                "MailMind Database Encryption Key",  # Description
                None,  # entropy (optional additional secret)
                None,  # reserved
                None,  # prompt_struct (no UI prompt)
                0      # flags
            )
            logger.debug("Data protected with DPAPI")
            return protected
        except pywintypes.error as e:
            raise KeyStorageError(f"DPAPI protection failed: {e}")

    def _unprotect_with_dpapi(self, protected_data: bytes) -> bytes:
        """
        Unprotect data using Windows DPAPI.

        Args:
            protected_data: DPAPI-protected data

        Returns:
            bytes: Unprotected raw data

        Raises:
            KeyRetrievalError: If DPAPI unprotection fails
        """
        if not DPAPI_AVAILABLE:
            raise KeyRetrievalError("DPAPI not available on this platform")

        try:
            # Unprotect data with DPAPI
            # CryptUnprotectData returns (description, data) tuple
            description, data = win32crypt.CryptUnprotectData(
                protected_data,
                None,  # entropy
                None,  # reserved
                None,  # prompt_struct
                0      # flags
            )
            logger.debug("Data unprotected with DPAPI")
            return data
        except pywintypes.error as e:
            raise KeyRetrievalError(f"DPAPI unprotection failed: {e}")

    def _store_in_credential_manager(self, dpapi_protected_key: bytes) -> None:
        """
        Store DPAPI-protected key in Windows Credential Manager.

        Args:
            dpapi_protected_key: DPAPI-protected key bytes

        Raises:
            KeyStorageError: If credential storage fails
        """
        if not DPAPI_AVAILABLE:
            raise KeyStorageError("Credential Manager not available on this platform")

        try:
            # Create credential structure
            credential = {
                "Type": win32cred.CRED_TYPE_GENERIC,
                "TargetName": self.CREDENTIAL_TARGET,
                "CredentialBlob": dpapi_protected_key,
                "Comment": "MailMind database encryption key (DPAPI-protected)",
                "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
            }

            # Write credential
            win32cred.CredWrite(credential, 0)
            logger.info(f"Encryption key stored in Credential Manager: {self.CREDENTIAL_TARGET}")

        except pywintypes.error as e:
            raise KeyStorageError(f"Failed to store key in Credential Manager: {e}")

    def _retrieve_from_credential_manager(self) -> Optional[bytes]:
        """
        Retrieve DPAPI-protected key from Windows Credential Manager.

        Returns:
            bytes: DPAPI-protected key, or None if not found

        Raises:
            KeyRetrievalError: If credential retrieval fails (other than not found)
        """
        if not DPAPI_AVAILABLE:
            return None

        try:
            # Read credential
            credential = win32cred.CredRead(
                Type=win32cred.CRED_TYPE_GENERIC,
                TargetName=self.CREDENTIAL_TARGET
            )

            # Extract credential blob (DPAPI-protected key)
            protected_key = credential["CredentialBlob"]
            logger.debug(f"Retrieved key from Credential Manager: {self.CREDENTIAL_TARGET}")
            return protected_key

        except pywintypes.error as e:
            # ERROR_NOT_FOUND is expected if key doesn't exist yet
            if e.winerror == 1168:  # ERROR_NOT_FOUND
                logger.debug(f"No credential found in Credential Manager: {self.CREDENTIAL_TARGET}")
                return None
            else:
                raise KeyRetrievalError(f"Failed to retrieve key from Credential Manager: {e}")

    def _generate_and_store_dpapi_key(self) -> bytes:
        """
        Generate new DPAPI key and store in Credential Manager.

        Returns:
            bytes: Raw 32-byte DPAPI key (unprotected)

        Raises:
            KeyManagementError: If generation or storage fails
        """
        # Generate random key
        dpapi_key = self._generate_dpapi_key()

        # Protect with DPAPI
        protected_key = self._protect_with_dpapi(dpapi_key)

        # Store in Credential Manager
        self._store_in_credential_manager(protected_key)

        logger.info("New encryption key generated and stored successfully")
        return dpapi_key

    def _retrieve_dpapi_key(self) -> Optional[bytes]:
        """
        Retrieve and unprotect DPAPI key from Credential Manager.

        Returns:
            bytes: Raw 32-byte DPAPI key (unprotected), or None if not found

        Raises:
            KeyRetrievalError: If retrieval or unprotection fails
        """
        # Retrieve protected key from Credential Manager
        protected_key = self._retrieve_from_credential_manager()

        if protected_key is None:
            return None

        # Unprotect with DPAPI
        dpapi_key = self._unprotect_with_dpapi(protected_key)

        return dpapi_key

    def _get_or_generate_salt(self) -> bytes:
        """
        Get salt from user_preferences or generate new one.

        Salt is stored in user_preferences table as base64-encoded string.
        Salt is not secret but must be consistent for key derivation.

        Returns:
            bytes: 16-byte salt

        Raises:
            KeyManagementError: If salt operations fail
        """
        if self.db_manager is None:
            # No db_manager - generate ephemeral salt (not recommended for production)
            logger.warning("No db_manager provided - generating ephemeral salt")
            return os.urandom(self.SALT_LENGTH)

        try:
            # Try to retrieve existing salt
            salt_b64 = self.db_manager.get_preference("encryption_salt")

            if salt_b64:
                # Decode base64 salt
                salt = base64.b64decode(salt_b64)
                logger.debug("Retrieved existing salt from user_preferences")
                return salt
            else:
                # Generate new salt
                salt = os.urandom(self.SALT_LENGTH)

                # Store as base64
                salt_b64 = base64.b64encode(salt).decode('ascii')
                self.db_manager.set_preference("encryption_salt", salt_b64)

                logger.info("Generated and stored new salt in user_preferences")
                return salt

        except Exception as e:
            logger.error(f"Failed to get/generate salt: {e}")
            raise KeyManagementError(f"Salt operations failed: {e}")

    def _derive_sqlcipher_key(self, dpapi_key: bytes, salt: bytes) -> bytes:
        """
        Derive 64-byte SQLCipher key using PBKDF2.

        PBKDF2 Parameters (AC2 requirements):
        - Hash algorithm: SHA-256 (secure and fast)
        - Iterations: 100,000 (balance security vs performance)
        - Key length: 64 bytes (SQLCipher default)
        - Salt: 16 bytes (from user_preferences)

        Args:
            dpapi_key: 32-byte DPAPI-protected key (password)
            salt: 16-byte salt

        Returns:
            bytes: 64-byte derived key for SQLCipher

        Raises:
            KeyManagementError: If derivation fails
        """
        try:
            # Derive key using PBKDF2-HMAC-SHA256
            derived_key = hashlib.pbkdf2_hmac(
                'sha256',                      # Hash algorithm
                dpapi_key,                     # Password (DPAPI key)
                salt,                          # Salt (from user_preferences)
                self.PBKDF2_ITERATIONS,        # Iterations (100,000)
                dklen=self.SQLCIPHER_KEY_LENGTH  # Desired key length (64 bytes)
            )

            logger.debug(
                f"Derived {self.SQLCIPHER_KEY_LENGTH}-byte SQLCipher key "
                f"using PBKDF2 ({self.PBKDF2_ITERATIONS} iterations)"
            )

            return derived_key

        except Exception as e:
            raise KeyManagementError(f"Key derivation failed: {e}")

    def delete_key(self) -> bool:
        """
        Delete encryption key from Credential Manager.

        Used when user explicitly disables encryption (AC8).

        Returns:
            bool: True if deletion successful, False if key not found

        Raises:
            KeyManagementError: If deletion fails (other than not found)
        """
        if not DPAPI_AVAILABLE:
            logger.info("No key to delete (DPAPI not available)")
            return False

        try:
            # Delete credential
            win32cred.CredDelete(
                Type=win32cred.CRED_TYPE_GENERIC,
                TargetName=self.CREDENTIAL_TARGET
            )

            # Clear cache
            self._cached_key = None

            logger.info(f"Encryption key deleted from Credential Manager: {self.CREDENTIAL_TARGET}")
            return True

        except pywintypes.error as e:
            # ERROR_NOT_FOUND is not an error - key doesn't exist
            if e.winerror == 1168:  # ERROR_NOT_FOUND
                logger.debug(f"No key found to delete: {self.CREDENTIAL_TARGET}")
                return False
            else:
                raise KeyManagementError(f"Failed to delete key: {e}")

    def rotate_key(self, old_key_hex: str) -> str:
        """
        Rotate encryption key (future enhancement).

        Not implemented in Story 3.1 - requires database re-encryption with PRAGMA rekey.
        Placeholder for future Story 3.x enhancement.

        Args:
            old_key_hex: Current hex-encoded key

        Returns:
            str: New hex-encoded key

        Raises:
            NotImplementedError: Not implemented in Story 3.1
        """
        raise NotImplementedError(
            "Key rotation not implemented in Story 3.1. "
            "Requires database re-encryption with SQLCipher PRAGMA rekey command. "
            "Planned for future enhancement."
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def get_key_manager(db_manager=None) -> KeyManager:
    """
    Factory function to create KeyManager instance.

    Args:
        db_manager: Optional DatabaseManager for salt storage

    Returns:
        KeyManager: Configured KeyManager instance
    """
    return KeyManager(db_manager=db_manager)


def is_encryption_supported() -> bool:
    """
    Check if encryption is supported on current platform.

    Returns:
        bool: True if Windows with pywin32, False otherwise
    """
    return DPAPI_AVAILABLE
