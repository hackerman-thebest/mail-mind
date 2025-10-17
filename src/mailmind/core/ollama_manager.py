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

# Import PerformanceTracker for AC3 (Story 0.5)
try:
    from mailmind.core.performance_tracker import PerformanceTracker
    PERFORMANCE_TRACKER_AVAILABLE = True
except ImportError:
    PERFORMANCE_TRACKER_AVAILABLE = False
    logger.debug("PerformanceTracker not available")


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

        # AC2: Timeout tracking for automatic fallback (Story 0.5)
        self.consecutive_timeouts = 0
        self.fallback_history = []  # Track fallback attempts to prevent infinite loops
        self.fallback_triggered = False

        # AC3: Performance monitoring (Story 0.5)
        self.performance_tracker = None
        if PERFORMANCE_TRACKER_AVAILABLE:
            try:
                # Use database path from config or default
                db_path = config.get('database_path', 'data/mailmind.db')
                self.performance_tracker = PerformanceTracker(db_path)
                logger.debug("PerformanceTracker initialized for model performance monitoring")
            except Exception as e:
                logger.warning(f"Could not initialize PerformanceTracker: {e}")

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
                logger.error("=" * 60)
                logger.error(f"❌ Test inference TIMED OUT after {timeout}s")
                logger.error("=" * 60)
                logger.error("")
                logger.error("This is a common issue with multiple possible causes:")
                logger.error("")
                logger.error("IMMEDIATE ACTIONS:")
                logger.error("  1. Restart Ollama completely:")
                logger.error("     - Close Ollama from system tray")
                logger.error("     - Reopen Ollama application")
                logger.error("     - Wait 10 seconds, then try again")
                logger.error("")
                logger.error("  2. Check Ollama service:")
                logger.error("     - Open Command Prompt")
                logger.error("     - Run: ollama ps")
                logger.error("     - Should show running models")
                logger.error("")
                logger.error("  3. Verify model:")
                logger.error("     - Run: ollama list")
                logger.error("     - Check if llama3.1:8b-instruct-q4_K_M is listed")
                logger.error("")
                logger.error("COMMON CAUSES:")
                logger.error("  • Ollama service not responding (restart needed)")
                logger.error("  • Model corrupted (run: ollama rm llama3.1:8b-instruct-q4_K_M && ollama pull llama3.1:8b-instruct-q4_K_M)")
                logger.error("  • Insufficient RAM (need 8GB+ available)")
                logger.error("  • Windows Defender blocking (add Ollama to exclusions)")
                logger.error("  • Antivirus interference (temporarily disable to test)")
                logger.error("  • Port 11434 conflict (check with: netstat -ano | findstr \"11434\")")
                logger.error("")
                logger.error("DIAGNOSTIC TOOL:")
                logger.error("  Run automatic diagnostics to identify the issue:")
                logger.error("  python main.py --diagnose")
                logger.error("")
                logger.error("ALTERNATIVE WORKAROUND:")
                logger.error("  Skip test inference (not recommended, only for debugging):")
                logger.error("  set MAILMIND_SKIP_TEST=1")
                logger.error("  python main.py")
                logger.error("")
                logger.error("=" * 60)
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
                encoding='utf-8',
                errors='replace',
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

    def initialize(self, skip_test_inference: bool = False) -> Tuple[bool, str]:
        """
        Complete initialization: connect, verify model, test inference.

        Args:
            skip_test_inference: If True, skip the test inference step (useful for debugging)

        Returns:
            Tuple[bool, str]: (success: bool, message: str)
        """
        try:
            # Step 1: Connect to Ollama
            logger.info("Starting Ollama initialization...")
            self.connect()

            # Step 2: Test inference (optional)
            if skip_test_inference:
                logger.warning("⚠️  Skipping test inference (skip_test_inference=True)")
                logger.warning("⚠️  Model functionality not verified - inference may fail at runtime")
                logger.info("Ollama initialization complete (test skipped)!")
                return True, f"Successfully initialized with model: {self.current_model} (test skipped)"
            else:
                if not self.test_inference():
                    logger.warning(
                        "⚠️  Test inference failed, but connection and model verification succeeded.\n"
                        "⚠️  This usually means:\n"
                        "   1. Ollama service has issues (try restarting Ollama)\n"
                        "   2. Model is corrupted (try: ollama pull llama3.1:8b-instruct-q4_K_M)\n"
                        "   3. System resources are insufficient (close other apps, check RAM)\n"
                        "   4. Windows Defender or antivirus is blocking (check exclusions)\n"
                        "⚠️  You can skip this test by setting skip_test_inference=True"
                    )
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

    def generate(self, prompt: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Generate response from model with automatic timeout tracking.

        Story 0.5 AC2: Tracks consecutive timeouts and triggers automatic fallback

        Args:
            prompt: Input prompt for the model
            timeout: Maximum time in seconds to wait for response (default: 30)

        Returns:
            Response dict from Ollama, or None if timeout/error

        Note:
            After 3 consecutive timeouts, will prompt user for automatic model fallback
        """
        if not self.is_connected or not self.current_model:
            logger.error("Cannot generate: not connected or no model loaded")
            return None

        try:
            logger.debug(f"Generating response with {self.current_model}...")
            start_time = time.time()

            # Use threading to implement timeout
            result = {'response': None, 'error': None, 'timeout': False}

            def run_inference():
                try:
                    result['response'] = self.client.generate(
                        model=self.current_model,
                        prompt=prompt,
                        options={
                            "temperature": self.temperature,
                            "num_ctx": self.context_window
                        }
                    )
                except Exception as e:
                    result['error'] = e

            inference_thread = threading.Thread(target=run_inference, daemon=True)
            inference_thread.start()
            inference_thread.join(timeout=timeout)

            if inference_thread.is_alive():
                # Timeout occurred
                result['timeout'] = True
                elapsed = time.time() - start_time
                logger.warning(f"⚠️  Inference timeout after {elapsed:.1f}s")

                # AC2: Track consecutive timeouts
                self.consecutive_timeouts += 1
                logger.warning(
                    f"Consecutive timeouts: {self.consecutive_timeouts}/3 "
                    f"(fallback will trigger at 3)"
                )

                # Check if we should trigger automatic fallback
                if self.consecutive_timeouts >= 3:
                    self._handle_automatic_fallback()

                return None

            if result['error']:
                # Reset timeout counter on non-timeout errors
                self.consecutive_timeouts = 0
                raise result['error']

            # Success - reset timeout counter
            self.consecutive_timeouts = 0
            inference_time = time.time() - start_time
            inference_time_ms = int(inference_time * 1000)
            logger.debug(f"Generation successful in {inference_time:.3f}s")

            # AC3: Log performance metrics
            if self.performance_tracker:
                try:
                    # Calculate tokens per second if response available
                    tokens_per_sec = None
                    if response and 'response' in response:
                        # Rough approximation: 1 token ≈ 4 characters
                        approx_tokens = len(response['response']) / 4
                        tokens_per_sec = approx_tokens / inference_time if inference_time > 0 else 0

                    self.performance_tracker.log_operation(
                        operation='model_inference',
                        processing_time_ms=inference_time_ms,
                        tokens_per_second=tokens_per_sec,
                        model_version=self.current_model
                    )
                    logger.debug(f"Performance logged for {self.current_model}: {inference_time_ms}ms")
                except Exception as e:
                    logger.warning(f"Failed to log performance: {e}")

            return result['response']

        except Exception as e:
            self.consecutive_timeouts = 0  # Reset on errors
            logger.error(f"Generation failed: {e}", exc_info=True)
            return None

    def _handle_automatic_fallback(self) -> None:
        """
        Handle automatic model fallback after repeated timeouts.

        Story 0.5 AC2: Automatic Model Fallback

        Prompts user to switch to a faster model after 3 consecutive timeouts.
        Stores fallback history to prevent infinite loops.
        """
        # Prevent triggering multiple times
        if self.fallback_triggered:
            logger.debug("Fallback already triggered, skipping")
            return

        self.fallback_triggered = True

        # Log warning
        logger.warning("=" * 60)
        logger.warning("⚠️  Model inference timing out repeatedly")
        logger.warning(f"Current model: {self.current_model}")
        logger.warning(f"Consecutive timeouts: {self.consecutive_timeouts}")
        logger.warning("=" * 60)

        # Check if we've already tried this model fallback
        if self.current_model in self.fallback_history:
            logger.warning(
                f"Model {self.current_model} already in fallback history. "
                f"Cannot fallback further to prevent infinite loop."
            )
            logger.warning("Please manually switch to a different model using: python main.py --switch-model")
            self.fallback_triggered = False  # Allow future attempts after manual intervention
            return

        # Determine next smaller model
        fallback_chain = {
            'llama3.1:8b-instruct-q4_K_M': 'llama3.2:3b',
            'llama3.2:3b': 'llama3.2:1b',
            'llama3.2:1b': None  # No smaller model available
        }

        next_model = fallback_chain.get(self.current_model)

        if next_model is None:
            logger.warning(
                f"Already using the smallest model ({self.current_model}). "
                f"Cannot fallback to a smaller model."
            )
            logger.warning("Please check system resources: python main.py --diagnose")
            self.fallback_triggered = False
            return

        # Import colorama for colored output
        try:
            from colorama import Fore, Style, init
            init()
        except ImportError:
            # Fallback if colorama not available
            class Fore:
                YELLOW = RED = GREEN = CYAN = ""
            class Style:
                RESET_ALL = ""

        # Prompt user
        print(f"\n{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️  Model Performance Issue Detected{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}\n")
        print(f"Your current model ({Fore.CYAN}{self.current_model}{Style.RESET_ALL}) is timing out repeatedly.")
        print(f"This usually means your system needs a faster, smaller model.\n")
        print(f"Recommended action: Switch to {Fore.GREEN}{next_model}{Style.RESET_ALL}")
        print(f"  • Faster inference")
        print(f"  • Lower memory usage")
        print(f"  • Better performance on your system\n")

        try:
            response = input(f"{Fore.CYAN}Switch to faster model now? (y/n): {Style.RESET_ALL}").strip().lower()

            if response == 'y':
                logger.info(f"User accepted automatic fallback to {next_model}")

                # Add current model to fallback history
                self.fallback_history.append(self.current_model)

                # Attempt to switch model
                success = self._switch_model_internal(next_model)

                if success:
                    print(f"\n{Fore.GREEN}✓ Successfully switched to {next_model}{Style.RESET_ALL}")
                    print(f"The new model will be used for subsequent inference calls.\n")

                    # Reset timeout counter
                    self.consecutive_timeouts = 0
                    self.fallback_triggered = False

                    # Display notification
                    logger.info("=" * 60)
                    logger.info(f"📢 MODEL SWITCHED: {self.current_model}")
                    logger.info(f"Reason: Automatic fallback due to repeated timeouts")
                    logger.info("=" * 60)
                else:
                    print(f"\n{Fore.RED}✗ Failed to switch to {next_model}{Style.RESET_ALL}")
                    print(f"Please switch manually: python main.py --switch-model\n")
                    self.fallback_triggered = False
            else:
                logger.info("User declined automatic fallback")
                print(f"\n{Fore.YELLOW}Continuing with current model: {self.current_model}{Style.RESET_ALL}")
                print(f"You can manually switch models later: python main.py --switch-model\n")

                # Reset counters to allow retries
                self.consecutive_timeouts = 0
                self.fallback_triggered = False

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Fallback cancelled by user{Style.RESET_ALL}")
            self.consecutive_timeouts = 0
            self.fallback_triggered = False
        except Exception as e:
            logger.error(f"Error during automatic fallback: {e}")
            self.fallback_triggered = False

    def _switch_model_internal(self, new_model: str) -> bool:
        """
        Internal method to switch model programmatically.

        Args:
            new_model: Name of model to switch to

        Returns:
            bool: True if switch successful, False otherwise
        """
        try:
            import subprocess
            import yaml
            from pathlib import Path

            logger.info(f"Switching model from {self.current_model} to {new_model}...")

            # Step 1: Check if model is downloaded
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )

            model_exists = False
            if result.returncode == 0:
                model_exists = new_model in result.stdout

            # Step 2: Download model if needed
            if not model_exists:
                logger.info(f"Model {new_model} not found. Downloading...")
                print(f"Downloading {new_model}... (this may take a few minutes)")

                download_result = subprocess.run(
                    ['ollama', 'pull', new_model],
                    encoding='utf-8',
                    errors='replace',
                    timeout=900  # 15 minute timeout
                )

                if download_result.returncode != 0:
                    logger.error(f"Failed to download {new_model}")
                    return False

                logger.info(f"✓ Model {new_model} downloaded successfully")

            # Step 3: Update user_config.yaml
            # Find config directory (go up from src/mailmind/core/ to root)
            config_dir = Path(__file__).parent.parent.parent.parent / "config"
            user_config_path = config_dir / "user_config.yaml"

            user_config = {}
            if user_config_path.exists():
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}

            if 'ollama' not in user_config:
                user_config['ollama'] = {}

            user_config['ollama']['selected_model'] = new_model
            user_config['ollama']['primary_model'] = new_model

            # Determine model size
            if '8b' in new_model.lower():
                user_config['ollama']['model_size'] = 'large'
            elif '3b' in new_model.lower():
                user_config['ollama']['model_size'] = 'medium'
            else:
                user_config['ollama']['model_size'] = 'small'

            with open(user_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f, default_flow_style=False)

            logger.info(f"✓ Configuration updated to use {new_model}")

            # Step 4: Update internal state
            self.current_model = new_model
            self.primary_model = new_model

            return True

        except subprocess.TimeoutExpired:
            logger.error("Model switch timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to switch model: {e}", exc_info=True)
            return False

    def get_model_performance(self, model_name: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get performance statistics for a specific model.

        Story 0.5 AC3: Model Performance Monitoring

        Args:
            model_name: Model to get stats for (default: current_model)
            days: Number of days to analyze (default: 30)

        Returns:
            Performance stats dict:
            {
                'model': 'llama3.2:3b',
                'avg_inference_time_sec': 4.2,
                'avg_tokens_per_sec': 15.3,
                'inference_count': 250,
                'min_time_ms': 850,
                'max_time_ms': 12000
            }
        """
        if not self.performance_tracker:
            logger.warning("PerformanceTracker not available")
            return {}

        model = model_name or self.current_model

        try:
            # Get metrics summary from performance tracker
            summary = self.performance_tracker.get_metrics_summary(days=days)

            # Filter for model_inference operations
            if 'model_inference' not in summary:
                logger.debug(f"No performance data available for model_inference (last {days} days)")
                return {
                    'model': model,
                    'message': 'No performance data available yet'
                }

            inference_stats = summary['model_inference']

            # Get model-specific data from database (filtered by model_version)
            import sqlite3
            from datetime import datetime, timedelta

            conn = sqlite3.connect(self.performance_tracker.db_path)
            cursor = conn.cursor()

            date_threshold = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute('''
                SELECT
                    COUNT(*) as count,
                    AVG(processing_time_ms) as avg_time_ms,
                    AVG(tokens_per_second) as avg_tokens_per_sec,
                    MIN(processing_time_ms) as min_time_ms,
                    MAX(processing_time_ms) as max_time_ms
                FROM performance_metrics
                WHERE operation = 'model_inference'
                  AND model_version = ?
                  AND timestamp > ?
            ''', (model, date_threshold))

            row = cursor.fetchone()
            conn.close()

            if row and row[0] > 0:  # Has data
                return {
                    'model': model,
                    'inference_count': row[0],
                    'avg_inference_time_ms': round(row[1], 2) if row[1] else 0,
                    'avg_inference_time_sec': round(row[1] / 1000, 2) if row[1] else 0,
                    'avg_tokens_per_sec': round(row[2], 2) if row[2] else None,
                    'min_time_ms': row[3] or 0,
                    'max_time_ms': row[4] or 0,
                    'period_days': days
                }
            else:
                return {
                    'model': model,
                    'message': f'No performance data for {model} in last {days} days'
                }

        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            return {
                'model': model,
                'error': str(e)
            }

    def get_model_performance_display(self) -> str:
        """
        Get formatted model performance string for UI display.

        Story 0.5 AC3: Display format for settings UI

        Returns:
            Formatted string: "Current model: llama3.2:3b (avg: 4.2s)"
        """
        if not self.current_model:
            return "No model loaded"

        perf = self.get_model_performance(days=7)  # Last 7 days

        if 'error' in perf:
            return f"Current model: {self.current_model}"

        if 'message' in perf:
            return f"Current model: {self.current_model} (no recent data)"

        avg_time = perf.get('avg_inference_time_sec', 0)
        return f"Current model: {self.current_model} (avg: {avg_time}s)"

    def check_upgrade_recommendation(self) -> Optional[Dict[str, Any]]:
        """
        Check if system resources have improved to recommend model upgrade.

        Story 0.5 AC3: Recommend upgrade if system resources improve

        Returns:
            Recommendation dict if upgrade suggested, None otherwise:
            {
                'current_model': 'llama3.2:3b',
                'recommended_model': 'llama3.1:8b-instruct-q4_K_M',
                'reason': 'Your system now has sufficient RAM for a higher quality model',
                'available_ram_gb': 12.5
            }
        """
        if not self.current_model:
            return None

        try:
            # Import system diagnostics
            from mailmind.utils.system_diagnostics import check_system_resources, recommend_model

            # Check current system resources
            resources = check_system_resources()
            recommended, reasoning, perf = recommend_model(resources)

            # Model hierarchy (smallest to largest)
            model_hierarchy = [
                'llama3.2:1b',
                'llama3.2:3b',
                'llama3.1:8b-instruct-q4_K_M'
            ]

            # Get current model index
            try:
                current_idx = model_hierarchy.index(self.current_model)
            except ValueError:
                # Current model not in hierarchy
                return None

            # Get recommended model index
            try:
                recommended_idx = model_hierarchy.index(recommended)
            except ValueError:
                # Recommended model not in hierarchy
                return None

            # If recommended model is better than current, suggest upgrade
            if recommended_idx > current_idx:
                return {
                    'current_model': self.current_model,
                    'recommended_model': recommended,
                    'reason': reasoning,
                    'available_ram_gb': round(resources['ram']['available_gb'], 1),
                    'expected_quality': perf['quality'],
                    'expected_speed': perf['tokens_per_second']
                }

            # No upgrade recommended
            return None

        except Exception as e:
            logger.error(f"Failed to check upgrade recommendation: {e}")
            return None
