"""
Ollama Manager - Local LLM Integration

Manages connection to Ollama service, model verification, and inference calls.
Implements Story 1.1: Ollama Integration & Model Setup
Enhanced with Story 2.6: Model fallback and error handling
Enhanced with Story 3.3: Connection pooling for parallel processing (AC2)
"""

import logging
import time
import queue
import threading
import hashlib
import json
from contextlib import contextmanager
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Import new exception hierarchy (Story 2.6)
try:
    from mailmind.core.exceptions import OllamaConnectionError, OllamaModelError
except ImportError:
    # Fallback to local exceptions if exceptions.py not available yet
    class OllamaConnectionError(Exception):
        """Raised when Ollama service is not available"""
        pass

    class OllamaModelError(Exception):
        """Raised when model is not available or fails to load"""
        pass

logger = logging.getLogger(__name__)


class OllamaConnectionPool:
    """
    Thread-safe connection pool for Ollama clients.

    Story 3.3 AC2: Connection pooling for improved throughput

    Implements:
    - Thread-safe connection management using queue.Queue
    - Context manager for automatic connection acquisition/release
    - Connection health checking and statistics
    - Configurable pool size (2-5 connections, default: 3)

    Usage:
        pool = OllamaConnectionPool(size=3)
        with pool.acquire() as client:
            response = client.generate(...)
    """

    def __init__(self, size: int = 3):
        """
        Initialize connection pool with specified size.

        Args:
            size: Number of connections in pool (2-5, default: 3)

        Raises:
            ValueError: If size is not between 2 and 5
        """
        # Story 3.3 arch-3: Enforce pool size limits
        if not isinstance(size, int) or size < 2 or size > 5:
            raise ValueError(f"Pool size must be between 2 and 5, got: {size}")

        self.size = size
        self.pool: queue.Queue = queue.Queue(maxsize=size)
        self.active_count = 0
        self.lock = threading.Lock()
        self._initialized = False

        logger.info(f"OllamaConnectionPool created with size={size}")

    def initialize(self) -> None:
        """
        Initialize connections in the pool.

        Creates 'size' ollama.Client instances and adds them to the pool.
        Called by OllamaManager after connect() succeeds.
        """
        if self._initialized:
            logger.debug("Connection pool already initialized")
            return

        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama client not available - cannot initialize pool")

        logger.info(f"Initializing connection pool with {self.size} connections...")

        for i in range(self.size):
            try:
                conn = ollama.Client()
                self.pool.put(conn)
                logger.debug(f"Created connection {i+1}/{self.size}")
            except Exception as e:
                logger.error(f"Failed to create connection {i+1}: {e}")
                raise

        self._initialized = True
        logger.info(f"✅ Connection pool initialized with {self.size} connections")

    @contextmanager
    def acquire(self, timeout: float = 5.0):
        """
        Acquire a connection from the pool (context manager).

        Story 3.3 AC2: Context manager pattern for automatic cleanup

        Args:
            timeout: Maximum time to wait for available connection (default: 5s)

        Yields:
            ollama.Client: Connection from pool

        Raises:
            queue.Empty: If no connection available within timeout
            RuntimeError: If pool not initialized

        Usage:
            with pool.acquire() as client:
                response = client.generate(...)
        """
        if not self._initialized:
            raise RuntimeError("Connection pool not initialized. Call initialize() first.")

        conn = None
        try:
            # Acquire connection from pool
            conn = self.pool.get(timeout=timeout)

            # Increment active count (thread-safe)
            with self.lock:
                self.active_count += 1

            logger.debug(f"Connection acquired (active: {self.active_count}/{self.size})")

            # Yield connection to caller
            yield conn

        finally:
            # Always release connection back to pool
            if conn is not None:
                with self.lock:
                    self.active_count -= 1

                self.pool.put(conn)
                logger.debug(f"Connection released (active: {self.active_count}/{self.size})")

    def stats(self) -> Dict[str, int]:
        """
        Get current pool statistics.

        Story 3.3 AC2: Pool statistics for monitoring

        Returns:
            dict: {'total': int, 'active': int, 'idle': int}
        """
        with self.lock:
            return {
                'total': self.size,
                'active': self.active_count,
                'idle': self.size - self.active_count
            }

    def health_check(self) -> bool:
        """
        Check health of connection pool.

        Story 3.3 AC2: Connection health checking

        Returns:
            bool: True if pool is healthy, False otherwise
        """
        try:
            stats = self.stats()

            # Pool is healthy if initialized and has expected number of connections
            if not self._initialized:
                logger.warning("Health check failed: Pool not initialized")
                return False

            # Check pool queue size matches expected size
            expected_idle = stats['idle']
            actual_queue_size = self.pool.qsize()

            if actual_queue_size != expected_idle:
                logger.warning(
                    f"Health check failed: Queue size mismatch "
                    f"(expected: {expected_idle}, actual: {actual_queue_size})"
                )
                return False

            logger.debug(f"Health check passed: {stats}")
            return True

        except Exception as e:
            logger.error(f"Health check failed with exception: {e}")
            return False


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

        Story 3.3 AC2: Added connection pooling support

        Args:
            config: Configuration dictionary with ollama settings
                   - pool_size: Connection pool size (2-5, default: 3)
        """
        self.client: Optional[ollama.Client] = None  # Kept for backward compatibility
        self.config = config

        # Model configuration
        self.primary_model = config.get('primary_model', 'llama3.1:8b-instruct-q4_K_M')
        self.fallback_model = config.get('fallback_model', 'mistral:7b-instruct-q4_K_M')
        self.current_model = None

        # Inference parameters
        self.temperature = config.get('temperature', 0.3)
        self.context_window = config.get('context_window', 8192)

        # Story 3.3 AC2: Connection pooling
        pool_size = config.get('pool_size', 3)
        self.pool = OllamaConnectionPool(size=pool_size)

        # Status
        self.is_connected = False
        self.model_status = "not_initialized"  # not_initialized, ready, loading, error

        logger.info(f"OllamaManager initialized with model: {self.primary_model}, pool_size: {pool_size}")

    def connect(self) -> bool:
        """
        Establish connection to Ollama service.

        Story 2.6 AC12: Error Scenario - Ollama not installed
        Story 3.3 AC2: Initialize connection pool

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            OllamaConnectionError: If Ollama is not installed or not running (AC12)
        """
        if not OLLAMA_AVAILABLE:
            technical_details = "Ollama Python client not installed (pip install ollama)"
            logger.error(technical_details)
            raise OllamaConnectionError(technical_details=technical_details)

        try:
            logger.info("Attempting to connect to Ollama service...")

            # Create test client to verify Ollama is running
            self.client = ollama.Client()

            # Test connection and get available models in one call
            start_time = time.time()
            models_response = self.client.list()
            connection_time = time.time() - start_time

            self.is_connected = True
            logger.info(f"✅ Connected to Ollama service in {connection_time:.3f}s")

            # Story 3.3 AC2: Initialize connection pool
            logger.info("Initializing connection pool...")
            self.pool.initialize()

            # Verify model availability (pass models_response to avoid duplicate call)
            return self.verify_model(models_response)

        except OllamaModelError:
            # Re-raise model errors (don't wrap them)
            raise
        except Exception as e:
            self.is_connected = False
            technical_details = f"Ollama connection failed: {e}"
            logger.error(technical_details)
            # AC12: Ollama not installed or not running
            raise OllamaConnectionError(technical_details=technical_details)

    def verify_model(self, models_response: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if the primary model is available. If not, check fallback.

        Story 2.6 AC3: Model fallback (Llama 3.1 → Mistral)
        Story 3.3 AC3: Model checksum verification integrated into model loading

        Args:
            models_response: Optional cached models list response from Ollama.
                           If None, will fetch models from Ollama.

        Returns:
            bool: True if a model is available, False otherwise

        Raises:
            OllamaModelError: If no models are available (AC12 - Model not downloaded scenario)
        """
        if not self.is_connected:
            raise OllamaConnectionError(
                technical_details="verify_model() called without connection"
            )

        try:
            self.model_status = "loading"
            logger.info(f"Verifying model availability: {self.primary_model}")

            # Get list of available models (use cached response if provided)
            if models_response is None:
                models_response = self.client.list()

            # Handle different response structures from Ollama API
            models_list = models_response.get('models', [])
            available_models = []
            for m in models_list:
                # Try different possible keys for model name
                model_name = m.get('name') or m.get('model') or m.get('id')
                if model_name:
                    available_models.append(model_name)

            logger.debug(f"Available models: {available_models}")

            # Check primary model
            if self.primary_model in available_models:
                self.current_model = self.primary_model

                # Story 3.3 AC3: Verify model checksum
                self._verify_model_security(self.primary_model)

                self.model_status = "ready"
                logger.info(f"✅ Primary model verified: {self.primary_model}")
                return True

            # AC3: Model fallback - log with WARNING severity
            logger.warning(
                f"⚠️  Primary model '{self.primary_model}' not found. "
                f"Attempting fallback to '{self.fallback_model}'..."
            )

            # Check fallback model
            if self.fallback_model in available_models:
                self.current_model = self.fallback_model

                # Story 3.3 AC3: Verify model checksum
                self._verify_model_security(self.fallback_model)

                self.model_status = "ready"
                logger.warning(
                    f"✅ Using fallback model: {self.fallback_model} "
                    f"(primary model '{self.primary_model}' unavailable)"
                )
                return True

            # AC12: Error Scenario - Model not downloaded
            # No models available - raise OllamaModelError
            self.model_status = "error"
            self.current_model = None

            available_str = ', '.join(available_models) if available_models else 'None'
            technical_details = (
                f"Neither primary model ({self.primary_model}) nor "
                f"fallback model ({self.fallback_model}) are available. "
                f"Available models: {available_str}"
            )

            logger.error(f"❌ Model verification failed: {technical_details}")

            # Raise with user-friendly message
            raise OllamaModelError(
                model_name=self.primary_model,
                technical_details=technical_details
            )

        except OllamaModelError:
            # Re-raise our custom exception
            self.model_status = "error"
            raise
        except ollama.ResponseError as e:
            self.model_status = "error"
            technical_details = f"Ollama API error during model verification: {e}"
            logger.error(technical_details)
            raise OllamaModelError(
                model_name=self.primary_model,
                technical_details=technical_details
            )
        except Exception as e:
            self.model_status = "error"
            technical_details = f"Unexpected error during model verification: {e}"
            logger.error(technical_details, exc_info=True)
            raise OllamaModelError(
                model_name=self.primary_model,
                technical_details=technical_details
            )

    def _verify_model_security(self, model_name: str) -> None:
        """
        Verify model security (checksum verification) with caching.

        Story 3.3 AC3: Security verification integrated into model loading
        Story 3.3 AC3 (3.8): Cache verified models in user_preferences

        Args:
            model_name: Model name to verify

        Note:
            This method does not raise exceptions on security failures, only logs warnings.
            Unknown models will log warnings but allow usage (graceful degradation).
            Verified models are cached to skip future checks for performance.
        """
        try:
            # Check if model was previously verified (cached in preferences)
            verified_models = self._get_verified_models_cache()

            if model_name in verified_models:
                logger.debug(f"Model {model_name} previously verified - skipping checksum check")
                return

            # Run checksum verification
            logger.info(f"Running security verification for {model_name}...")
            verified, message = self.verify_model_checksum(model_name)

            if verified is True:
                # Checksum verified - add to cache
                logger.info(f"✅ Security verification passed for {model_name}")
                self._add_to_verified_models_cache(model_name)
            elif verified is False:
                # Checksum mismatch - log warning but allow usage
                logger.warning(
                    f"⚠️  SECURITY WARNING: Model {model_name} failed checksum verification!\n"
                    f"Message: {message}\n"
                    f"The model may be tampered, corrupted, or a different version than expected.\n"
                    f"Proceeding with caution (user override may be required in production)."
                )
                # TODO: In production, show UI dialog asking user to confirm trust
                # For now, we allow usage but log the security warning
            elif verified is None:
                # Unknown model or verification skipped - log info
                logger.info(
                    f"Security verification skipped for {model_name}: {message}"
                )
                # Graceful degradation - allow usage of unknown models

        except Exception as e:
            # Never fail model loading due to security verification errors
            logger.warning(
                f"Security verification failed for {model_name} with error: {e}. "
                f"Proceeding with model loading (graceful degradation)."
            )

    def _get_verified_models_cache(self) -> list:
        """
        Get list of previously verified models from user_preferences.

        Story 3.3 AC3 (3.8): Retrieve verified models cache

        Returns:
            List of model names that have been verified
        """
        try:
            # Access database via settings manager or direct database access
            from mailmind.database import DatabaseManager
            db = DatabaseManager.get_instance()

            # Get verified_models preference (stored as JSON string)
            verified_json = db.get_preference('verified_models')

            if verified_json:
                return json.loads(verified_json)
            else:
                return []

        except Exception as e:
            logger.debug(f"Could not load verified models cache: {e}")
            return []

    def _add_to_verified_models_cache(self, model_name: str) -> None:
        """
        Add model to verified models cache in user_preferences.

        Story 3.3 AC3 (3.8): Cache verified models

        Args:
            model_name: Model name to add to cache
        """
        try:
            from mailmind.database import DatabaseManager
            db = DatabaseManager.get_instance()

            # Get current cache
            verified_models = self._get_verified_models_cache()

            # Add model if not already in cache
            if model_name not in verified_models:
                verified_models.append(model_name)

                # Save back to preferences as JSON
                verified_json = json.dumps(verified_models)
                db.set_preference('verified_models', verified_json)

                logger.debug(f"Added {model_name} to verified models cache")

        except Exception as e:
            logger.warning(f"Could not save verified model to cache: {e}")

    def test_inference(self, timeout: int = 30) -> bool:
        """
        Run a test inference call to verify the model works correctly.

        Args:
            timeout: Maximum time in seconds to wait for inference (default: 30)

        Returns:
            bool: True if test successful, False otherwise
        """
        if not self.is_connected or not self.current_model:
            logger.error("Cannot test inference: not connected or no model loaded")
            return False

        try:
            logger.info(f"Running test inference with {self.current_model}...")
            logger.info(f"This may take 10-30 seconds on first run (loading model into memory)...")
            start_time = time.time()

            # Use threading to implement timeout
            import threading
            result = {'response': None, 'error': None}

            def run_inference():
                try:
                    result['response'] = self.client.generate(
                        model=self.current_model,
                        prompt="Test",
                        options={
                            "temperature": self.temperature,
                            "num_ctx": self.context_window
                        }
                    )
                except Exception as e:
                    result['error'] = e

            inference_thread = threading.Thread(target=run_inference, daemon=True)
            inference_thread.start()

            # Wait with progress updates
            elapsed = 0
            while inference_thread.is_alive() and elapsed < timeout:
                inference_thread.join(timeout=5)
                elapsed = time.time() - start_time
                if inference_thread.is_alive() and elapsed < timeout:
                    logger.info(f"Still waiting... ({elapsed:.0f}s elapsed)")

            if inference_thread.is_alive():
                logger.error(
                    f"Test inference timed out after {timeout}s. "
                    f"This may indicate the model is too large for your system or Ollama is having issues. "
                    f"Try: 1) Restart Ollama, 2) Use a smaller model, 3) Check system resources"
                )
                return False

            if result['error']:
                raise result['error']

            inference_time = time.time() - start_time
            response = result['response']

            if response and 'response' in response:
                logger.info(
                    f"✅ Test inference successful in {inference_time:.3f}s. "
                    f"Generated {len(response['response'])} characters."
                )
                return True
            else:
                logger.error("Test inference failed: no response received")
                return False

        except Exception as e:
            logger.error(f"Test inference failed: {e}", exc_info=True)
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

    def get_pool_stats(self) -> Dict[str, int]:
        """
        Get connection pool statistics.

        Story 3.3 AC2: Pool statistics for monitoring

        Returns:
            dict: Pool statistics {'total': int, 'active': int, 'idle': int}
        """
        return self.pool.stats()

    def _get_model_blob_path(self, model_name: str) -> Optional[Path]:
        """
        Get the blob file path for an Ollama model.

        Story 3.3 AC3: Helper method to locate model blob files

        Args:
            model_name: Model name (e.g., "llama3.1:8b-instruct-q4_K_M")

        Returns:
            Path to model blob file, or None if not found

        Note:
            Uses 'ollama show <model> --modelfile' to extract blob reference,
            then locates the blob in ~/.ollama/models/blobs/
        """
        try:
            import subprocess

            # Run ollama show command to get modelfile
            result = subprocess.run(
                ['ollama', 'show', model_name, '--modelfile'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.debug(f"ollama show command failed for {model_name}: {result.stderr}")
                return None

            # Parse modelfile output to find FROM line with blob reference
            # Example: FROM sha256:abc123def456...
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith('FROM '):
                    # Extract blob hash (format: "FROM sha256:HASH" or "FROM HASH")
                    parts = line.split()
                    if len(parts) >= 2:
                        blob_ref = parts[1]

                        # Remove sha256: prefix if present
                        if blob_ref.startswith('sha256:'):
                            blob_ref = blob_ref[7:]

                        # Construct blob path
                        ollama_dir = Path.home() / '.ollama' / 'models' / 'blobs'
                        blob_path = ollama_dir / f'sha256-{blob_ref}'

                        if blob_path.exists():
                            logger.debug(f"Found blob for {model_name}: {blob_path}")
                            return blob_path
                        else:
                            # Try alternative naming (some Ollama versions use plain blob_ref)
                            blob_path_alt = ollama_dir / blob_ref
                            if blob_path_alt.exists():
                                logger.debug(f"Found blob for {model_name}: {blob_path_alt}")
                                return blob_path_alt

                            logger.debug(f"Blob file not found: {blob_path}")
                            return None

            logger.debug(f"No FROM line found in modelfile for {model_name}")
            return None

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout getting blob path for {model_name}")
            return None
        except Exception as e:
            logger.debug(f"Error getting blob path for {model_name}: {e}")
            return None

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA256 checksum of a file.

        Story 3.3 AC3: Helper method for checksum calculation

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal SHA256 checksum string
        """
        sha256_hash = hashlib.sha256()

        # Read file in chunks to handle large model files efficiently
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def verify_model_checksum(self, model_name: str) -> Tuple[Optional[bool], str]:
        """
        Verify model checksum against known-good hashes.

        Story 3.3 AC3: Model checksum verification for supply chain security

        Args:
            model_name: Model name to verify

        Returns:
            Tuple[Optional[bool], str]: (verified, message)
                - (True, "verified") if checksum matches
                - (False, "mismatch warning") if checksum doesn't match
                - (None, "unknown model") if model not in checksums.json

        Implementation:
            1. Loads model_checksums.json configuration
            2. Locates model blob file via ollama show <model> --modelfile
            3. Calculates SHA256 of blob file
            4. Compares against known-good hash from configuration
        """
        try:
            # Load model checksums file
            config_path = Path(__file__).parent.parent / "config" / "model_checksums.json"

            if not config_path.exists():
                logger.info(f"model_checksums.json not found at {config_path} - skipping verification")
                return None, "unknown model - checksums file missing"

            with open(config_path, 'r') as f:
                checksums_data = json.load(f)

            models = checksums_data.get('models', {})

            if model_name not in models:
                logger.info(f"Model {model_name} not in checksums.json - user confirmation required")
                return None, f"unknown model - not in verification database"

            expected_checksum = models[model_name].get('sha256', '')

            # Check if checksum is a placeholder
            if 'placeholder' in expected_checksum.lower():
                logger.warning(
                    f"Model {model_name} has placeholder checksum - "
                    f"checksum verification skipped (real checksums not yet configured)"
                )
                return None, "verification skipped - placeholder checksum in config"

            # Get model blob path
            blob_path = self._get_model_blob_path(model_name)

            if blob_path is None:
                logger.warning(
                    f"Could not locate blob file for {model_name} - "
                    f"verification skipped (model may not be downloaded yet)"
                )
                return None, "verification skipped - blob file not found"

            # Calculate actual checksum
            logger.info(f"Calculating checksum for {model_name} blob: {blob_path}")
            actual_checksum = self._calculate_file_checksum(blob_path)

            logger.debug(f"Expected: {expected_checksum}")
            logger.debug(f"Actual:   {actual_checksum}")

            # Compare checksums
            if actual_checksum == expected_checksum:
                logger.info(f"✅ Model {model_name} checksum verified successfully")
                return True, "verified"
            else:
                logger.warning(
                    f"⚠️  SECURITY WARNING: Model {model_name} checksum MISMATCH!\n"
                    f"Expected: {expected_checksum}\n"
                    f"Actual:   {actual_checksum}\n"
                    f"This could indicate a tampered or corrupted model file."
                )
                return False, f"checksum mismatch - model may be tampered"

        except Exception as e:
            logger.error(f"Checksum verification failed: {e}", exc_info=True)
            return None, f"verification error: {e}"

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
            models_list = models_response.get('models', [])
            available_models = []
            for m in models_list:
                # Try different possible keys for model name
                model_name = m.get('name') or m.get('model') or m.get('id')
                if model_name:
                    available_models.append(model_name)
            return available_models
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
