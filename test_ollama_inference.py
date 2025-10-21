#!/usr/bin/env python3
"""
Test Ollama Inference - Diagnostic Script for Ollama Library Issues

This script helps diagnose and test the ollama Python library on machines
where Ollama may not be installed or working properly.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_ollama_installation():
    """Check if Ollama CLI is installed."""
    import subprocess
    print("\n" + "="*60)
    print("1. CHECKING OLLAMA CLI INSTALLATION")
    print("="*60)

    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Ollama CLI installed: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ Ollama CLI found but returned error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("✗ Ollama CLI not found in PATH")
        print("  Install from: https://ollama.com/download")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama CLI: {e}")
        return False


def check_ollama_library():
    """Check if ollama Python library is installed."""
    print("\n" + "="*60)
    print("2. CHECKING OLLAMA PYTHON LIBRARY")
    print("="*60)

    try:
        import ollama
        print(f"✓ ollama library installed")
        print(f"  Location: {ollama.__file__}")

        # Try to get version
        try:
            version = ollama.__version__
            print(f"  Version: {version}")
        except AttributeError:
            print("  Version: (not available)")

        return True, ollama
    except ImportError as e:
        print(f"✗ ollama library not installed: {e}")
        print("  Install with: pip install ollama")
        return False, None


def check_ollama_service():
    """Check if Ollama service is running."""
    print("\n" + "="*60)
    print("3. CHECKING OLLAMA SERVICE")
    print("="*60)

    try:
        import requests
        response = requests.get('http://localhost:11434/api/version', timeout=2)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✓ Ollama service is running")
            print(f"  Version: {version_info.get('version', 'unknown')}")
            return True
        else:
            print(f"✗ Ollama service responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Ollama service on localhost:11434")
        print("  The service may not be running")
        return False
    except requests.exceptions.Timeout:
        print("✗ Timeout connecting to Ollama service")
        return False
    except ImportError:
        print("! requests library not installed, trying alternative method")

        # Try using ollama library directly
        try:
            import ollama
            client = ollama.Client()
            models = client.list()
            print(f"✓ Ollama service is accessible via library")
            return True
        except Exception as e:
            print(f"✗ Cannot access Ollama service: {e}")
            return False
    except Exception as e:
        print(f"✗ Error checking Ollama service: {e}")
        return False


def list_available_models(ollama_lib):
    """List available models."""
    print("\n" + "="*60)
    print("4. LISTING AVAILABLE MODELS")
    print("="*60)

    try:
        client = ollama_lib.Client()
        response = client.list()
        models = response.get('models', [])

        if models:
            print(f"✓ Found {len(models)} model(s):")
            for model in models:
                name = model.get('name', 'unknown')
                size = model.get('size', 0) / (1024**3)  # Convert to GB
                print(f"  - {name} ({size:.2f} GB)")
            return models
        else:
            print("! No models installed")
            print("  Download a model with: ollama pull llama3.2:3b")
            return []
    except Exception as e:
        print(f"✗ Error listing models: {e}")
        return []


def test_inference(ollama_lib, model_name=None):
    """Test inference with a model."""
    print("\n" + "="*60)
    print("5. TESTING MODEL INFERENCE")
    print("="*60)

    if model_name is None:
        # Try to get a model
        try:
            client = ollama_lib.Client()
            response = client.list()
            models = response.get('models', [])
            if models:
                model_name = models[0].get('name')
                print(f"Using first available model: {model_name}")
            else:
                print("✗ No models available for testing")
                return False
        except Exception as e:
            print(f"✗ Cannot list models: {e}")
            return False

    print(f"\nTesting inference with model: {model_name}")
    print("(This may take 10-30 seconds on first run...)")

    try:
        import time
        client = ollama_lib.Client()

        start_time = time.time()
        response = client.generate(
            model=model_name,
            prompt="Say 'Hello, World!' and nothing else.",
            options={
                "temperature": 0.1,
                "num_ctx": 512
            }
        )
        elapsed = time.time() - start_time

        if response and 'response' in response:
            result_text = response['response'].strip()
            print(f"\n✓ Inference successful in {elapsed:.2f}s")
            print(f"  Model response: {result_text}")
            return True
        else:
            print(f"✗ Inference returned unexpected response: {response}")
            return False

    except Exception as e:
        print(f"\n✗ Inference failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def run_mock_test():
    """Run a mock test without requiring Ollama."""
    print("\n" + "="*60)
    print("MOCK TEST MODE (No Ollama Required)")
    print("="*60)

    print("\nSimulating Ollama functionality for testing purposes...")

    # Create a mock ollama manager
    mock_config = {
        'primary_model': 'llama3.2:3b',
        'temperature': 0.3,
        'context_window': 8192
    }

    print(f"\nMock Configuration:")
    print(f"  Model: {mock_config['primary_model']}")
    print(f"  Temperature: {mock_config['temperature']}")
    print(f"  Context Window: {mock_config['context_window']}")

    print("\nMock Inference Test:")
    print("  Prompt: 'Hello, World!'")
    print("  Response: 'Hello! I'm a mock LLM response for testing.'")
    print("  Status: ✓ Success (mocked)")

    print("\n" + "="*60)
    print("Mock test complete. This demonstrates the expected behavior.")
    print("To test with real Ollama, install it from https://ollama.com")
    print("="*60)


def main():
    """Main diagnostic routine."""
    print("\n" + "="*60)
    print("OLLAMA LIBRARY DIAGNOSTIC TOOL")
    print("="*60)
    print("\nThis tool will help diagnose issues with the Ollama library")
    print("and test inference capabilities.\n")

    # Step 1: Check Ollama CLI
    cli_installed = check_ollama_installation()

    # Step 2: Check ollama library
    lib_installed, ollama_lib = check_ollama_library()

    if not lib_installed:
        print("\n" + "="*60)
        print("DIAGNOSIS: Ollama library not installed")
        print("="*60)
        print("\nTo install: pip install ollama")
        print("\nRunning mock test instead...")
        run_mock_test()
        return

    # Step 3: Check Ollama service
    service_running = check_ollama_service()

    if not cli_installed or not service_running:
        print("\n" + "="*60)
        print("DIAGNOSIS: Ollama not installed or service not running")
        print("="*60)
        print("\nThe ollama Python library is installed, but:")
        if not cli_installed:
            print("  - Ollama CLI is not installed")
        if not service_running:
            print("  - Ollama service is not running")

        print("\nTo fix:")
        print("  1. Download Ollama from https://ollama.com/download")
        print("  2. Install and run Ollama")
        print("  3. Download a model: ollama pull llama3.2:3b")
        print("\nRunning mock test instead...")
        run_mock_test()
        return

    # Step 4: List models
    models = list_available_models(ollama_lib)

    if not models:
        print("\n" + "="*60)
        print("DIAGNOSIS: No models available")
        print("="*60)
        print("\nDownload a model with: ollama pull llama3.2:3b")
        print("Or: ollama pull llama3.1:8b-instruct-q4_K_M")
        return

    # Step 5: Test inference
    inference_success = test_inference(ollama_lib)

    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    print(f"  Ollama CLI: {'✓' if cli_installed else '✗'}")
    print(f"  Python Library: {'✓' if lib_installed else '✗'}")
    print(f"  Service Running: {'✓' if service_running else '✗'}")
    print(f"  Models Available: {'✓' if models else '✗'}")
    print(f"  Inference Test: {'✓' if inference_success else '✗'}")

    if all([cli_installed, lib_installed, service_running, models, inference_success]):
        print("\n✓ All tests passed! Ollama is working correctly.")
    else:
        print("\n⚠ Some tests failed. See details above.")

    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
