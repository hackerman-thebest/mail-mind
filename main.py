"""
MailMind - Main Application Entry Point

This is a basic example demonstrating Ollama integration from Story 1.1.
Full UI and email integration will be added in subsequent stories.
"""

import logging
import sys
import os
import subprocess
import time
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


def run_ollama_diagnostics():
    """
    Run comprehensive Ollama diagnostics to help troubleshoot connection issues.

    Tests:
    1. Ollama service status (ollama ps)
    2. Model list access (ollama list)
    3. Basic inference test (echo "test" | ollama run <model>)
    4. HTTP endpoint connectivity (curl localhost:11434)

    Returns:
        bool: True if all tests pass, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Running Ollama Diagnostics...")
    logger.info("=" * 60)
    logger.info("")

    all_passed = True

    # Test 1: Ollama service status
    logger.info("[Test 1/4] Checking Ollama service status...")
    try:
        result = subprocess.run(
            ['ollama', 'ps'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        if result.returncode == 0:
            logger.info("  ✓ Ollama service is running")
        else:
            logger.error("  ❌ FAILED: Ollama service not responding")
            logger.error("  Troubleshooting:")
            logger.error("    1. Restart Ollama application")
            logger.error("    2. Check Task Manager for 'ollama' process")
            logger.error("    3. Try running: ollama serve")
            all_passed = False
    except subprocess.TimeoutExpired:
        logger.error("  ❌ FAILED: Ollama service check timed out")
        all_passed = False
    except FileNotFoundError:
        logger.error("  ❌ FAILED: 'ollama' command not found")
        logger.error("  Please install Ollama from https://ollama.com/download")
        all_passed = False
    except Exception as e:
        logger.error(f"  ❌ FAILED: {e}")
        all_passed = False
    logger.info("")

    # Test 2: Model list access
    logger.info("[Test 2/4] Verifying model list access...")
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        if result.returncode == 0:
            logger.info("  ✓ Model list accessible")
            if result.stdout:
                logger.info(f"  Available models:\n{result.stdout}")
        else:
            logger.error("  ❌ FAILED: Cannot access model list")
            logger.error("  Troubleshooting:")
            logger.error("    1. Check Windows Defender/antivirus settings")
            logger.error("    2. Verify firewall isn't blocking localhost")
            logger.error("    3. Try running as Administrator")
            all_passed = False
    except subprocess.TimeoutExpired:
        logger.error("  ❌ FAILED: Model list check timed out")
        all_passed = False
    except Exception as e:
        logger.error(f"  ❌ FAILED: {e}")
        all_passed = False
    logger.info("")

    # Test 3: Basic inference test
    logger.info("[Test 3/4] Testing basic model inference...")
    logger.info("  This may take 10-30 seconds on first run...")
    try:
        start_time = time.time()
        result = subprocess.run(
            ['ollama', 'run', 'llama3.1:8b-instruct-q4_K_M'],
            input='Test',
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=45  # Slightly longer timeout for first run
        )
        elapsed = time.time() - start_time

        if result.returncode == 0 and result.stdout:
            logger.info(f"  ✓ Model inference working! ({elapsed:.1f}s)")
        else:
            logger.error(f"  ❌ FAILED: Model inference not working (took {elapsed:.1f}s)")
            logger.error("  Common causes:")
            logger.error("    1. Model not downloaded - run: ollama pull llama3.1:8b-instruct-q4_K_M")
            logger.error("    2. Corrupted model - run: ollama rm llama3.1:8b-instruct-q4_K_M")
            logger.error("       Then: ollama pull llama3.1:8b-instruct-q4_K_M")
            logger.error("    3. Insufficient RAM (need 8GB+ available)")
            logger.error("    4. Windows Defender blocking model access")
            logger.error("    5. Ollama needs restart")
            all_passed = False
    except subprocess.TimeoutExpired:
        logger.error("  ❌ FAILED: Model inference timed out after 45 seconds")
        logger.error("  This is the issue your client is experiencing!")
        logger.error("  Troubleshooting:")
        logger.error("    1. Check Ollama logs: %LOCALAPPDATA%\\Ollama\\logs\\")
        logger.error("    2. Try smaller model: ollama run llama3.2:1b")
        logger.error("    3. Restart Ollama service completely")
        logger.error("    4. Check system resources (RAM, CPU)")
        logger.error("    5. Disable real-time antivirus temporarily")
        all_passed = False
    except Exception as e:
        logger.error(f"  ❌ FAILED: {e}")
        all_passed = False
    logger.info("")

    # Test 4: HTTP endpoint connectivity
    logger.info("[Test 4/4] Testing HTTP connection to Ollama...")
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:11434/api/tags'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            logger.info("  ✓ HTTP connection working")
        else:
            logger.warning("  ⚠️  WARNING: Direct HTTP connection failed")
            logger.warning("  Troubleshooting:")
            logger.warning("    1. Check if port 11434 is in use")
            logger.warning("    2. Run: netstat -ano | findstr \"11434\"")
            logger.warning("    3. Configure firewall to allow Ollama")
    except subprocess.TimeoutExpired:
        logger.warning("  ⚠️  WARNING: HTTP connection timed out")
    except FileNotFoundError:
        logger.info("  ⚠️  'curl' not found - skipping HTTP test")
    except Exception as e:
        logger.warning(f"  ⚠️  WARNING: {e}")

    logger.info("")
    logger.info("=" * 60)
    if all_passed:
        logger.info("✅ All diagnostics passed! Ollama should work correctly.")
    else:
        logger.error("❌ Some diagnostics failed. Please fix the issues above.")
        logger.error("   After fixing, you can run: python main.py")
    logger.info("=" * 60)
    logger.info("")

    return all_passed


def main():
    """
    Main application entry point.

    Currently demonstrates Story 1.1: Ollama Integration

    Command-line options:
        --diagnose    Run Ollama diagnostics and exit
    """
    # Check for diagnostic mode
    if '--diagnose' in sys.argv or '--diagnostics' in sys.argv:
        logger.info("Running in diagnostic mode...")
        logger.info("")
        success = run_ollama_diagnostics()
        return 0 if success else 1

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

        # Check if we should skip test inference (for debugging Ollama issues)
        skip_test = os.environ.get('MAILMIND_SKIP_TEST', '').lower() in ('1', 'true', 'yes')
        if skip_test:
            logger.warning("⚠️  MAILMIND_SKIP_TEST is set - skipping model test inference")

        # Attempt to connect and initialize
        success, message = ollama_manager.initialize(skip_test_inference=skip_test)

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
            logger.error("")
            logger.error("Would you like to run diagnostics to troubleshoot the issue?")
            logger.error("Run: python main.py --diagnose")
            logger.error("")
            return 1

    except OllamaConnectionError as e:
        logger.error(f"✗ Connection Error: {e}")
        logger.error("=" * 60)
        logger.error("")
        logger.error("Ollama connection failed! Running automatic diagnostics...")
        logger.error("")
        run_ollama_diagnostics()
        return 1

    except OllamaModelError as e:
        logger.error(f"✗ Model Error: {e}")
        logger.error("=" * 60)
        logger.error("")
        logger.error("Model loading failed! Running automatic diagnostics...")
        logger.error("")
        run_ollama_diagnostics()
        return 1

    except Exception as e:
        logger.exception(f"✗ Unexpected Error: {e}")
        logger.error("=" * 60)
        logger.error("")
        logger.error("Unexpected error occurred! You can run diagnostics with:")
        logger.error("  python main.py --diagnose")
        logger.error("")
        return 1


if __name__ == "__main__":
    sys.exit(main())
