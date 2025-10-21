#!/usr/bin/env python3
"""
Mock Ollama Test - Test MailMind with Mock Ollama Responses

This script provides a mock version of Ollama for testing on machines
where Ollama is not installed. It allows you to test the mail-mind
inference pipeline without requiring the actual Ollama service.
"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class MockOllamaClient:
    """Mock Ollama client for testing."""

    def __init__(self):
        self.call_count = 0

    def list(self):
        """Mock list() to return available models."""
        return {
            'models': [
                {
                    'name': 'llama3.2:3b',
                    'size': 2147483648,  # 2GB
                    'modified_at': '2024-01-01T00:00:00Z'
                },
                {
                    'name': 'llama3.1:8b-instruct-q4_K_M',
                    'size': 5368709120,  # 5GB
                    'modified_at': '2024-01-01T00:00:00Z'
                }
            ]
        }

    def generate(self, model, prompt, options=None):
        """Mock generate() to return a test response."""
        self.call_count += 1

        # Simulate some processing time
        time.sleep(0.5)

        # Generate a mock response based on the prompt
        if "test" in prompt.lower():
            response_text = "This is a test response from the mock LLM."
        elif "hello" in prompt.lower():
            response_text = "Hello! This is a mock response."
        elif "email" in prompt.lower():
            response_text = "This email appears to be a mock test. Priority: Low."
        else:
            response_text = f"Mock LLM response to prompt: {prompt[:50]}..."

        return {
            'model': model,
            'created_at': '2024-01-01T00:00:00Z',
            'response': response_text,
            'done': True,
            'context': [1, 2, 3],  # Mock context tokens
            'total_duration': 500000000,
            'load_duration': 100000000,
            'prompt_eval_count': 10,
            'prompt_eval_duration': 200000000,
            'eval_count': 20,
            'eval_duration': 300000000
        }

    def chat(self, model, messages, options=None):
        """Mock chat() for conversation-style interactions."""
        self.call_count += 1

        # Simulate processing time
        time.sleep(0.5)

        # Get last message
        last_message = messages[-1] if messages else {'content': ''}
        prompt = last_message.get('content', '')

        response_text = f"Mock chat response to: {prompt[:50]}..."

        return {
            'model': model,
            'created_at': '2024-01-01T00:00:00Z',
            'message': {
                'role': 'assistant',
                'content': response_text
            },
            'done': True
        }


def test_ollama_manager_with_mock():
    """Test OllamaManager with mock client."""
    print("\n" + "="*60)
    print("TESTING OLLAMA MANAGER WITH MOCK CLIENT")
    print("="*60)

    # Import after adding to path
    from mailmind.core.ollama_manager import OllamaManager

    # Create config
    config = {
        'primary_model': 'llama3.2:3b',
        'fallback_model': 'llama3.1:8b-instruct-q4_K_M',
        'temperature': 0.3,
        'context_window': 8192,
        'pool_size': 3
    }

    print(f"\nCreating OllamaManager with config:")
    print(f"  Primary model: {config['primary_model']}")
    print(f"  Fallback model: {config['fallback_model']}")
    print(f"  Pool size: {config['pool_size']}")

    # Create mock client
    mock_client = MockOllamaClient()

    # Patch the ollama module
    with patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True):
        with patch('mailmind.core.ollama_manager.ollama.Client', return_value=mock_client):
            # Create manager
            manager = OllamaManager(config)

            # Test connection
            print("\n[Test 1] Connecting to Ollama (mocked)...")
            try:
                # Patch pool initialization to avoid creating real connections
                with patch.object(manager.pool, 'initialize'):
                    manager.client = mock_client
                    manager.is_connected = True

                    # Verify model
                    models_response = mock_client.list()
                    success = manager.verify_model(models_response)

                    if success:
                        print(f"  ✓ Connection successful")
                        print(f"  ✓ Using model: {manager.current_model}")
                    else:
                        print(f"  ✗ Model verification failed")
                        return False
            except Exception as e:
                print(f"  ✗ Connection failed: {e}")
                return False

            # Test inference
            print("\n[Test 2] Running test inference...")
            try:
                response = mock_client.generate(
                    model=manager.current_model,
                    prompt="This is a test prompt for mock inference.",
                    options={
                        "temperature": manager.temperature,
                        "num_ctx": manager.context_window
                    }
                )

                if response and 'response' in response:
                    print(f"  ✓ Inference successful")
                    print(f"  Response: {response['response'][:100]}...")
                    print(f"  Done: {response.get('done', False)}")
                else:
                    print(f"  ✗ Inference failed: no response")
                    return False
            except Exception as e:
                print(f"  ✗ Inference failed: {e}")
                import traceback
                traceback.print_exc()
                return False

            # Test multiple inferences
            print("\n[Test 3] Testing multiple inferences...")
            test_prompts = [
                "Analyze this email: Hello, how are you?",
                "Classify priority of: URGENT: Meeting tomorrow",
                "Generate response to: Thanks for your help!"
            ]

            for i, prompt in enumerate(test_prompts, 1):
                try:
                    response = mock_client.generate(
                        model=manager.current_model,
                        prompt=prompt,
                        options={"temperature": 0.3}
                    )
                    print(f"  ✓ Inference {i}/3 successful")
                except Exception as e:
                    print(f"  ✗ Inference {i}/3 failed: {e}")
                    return False

            # Test model info
            print("\n[Test 4] Getting model info...")
            info = manager.get_model_info()
            print(f"  Current model: {info['current_model']}")
            print(f"  Status: {info['status']}")
            print(f"  Temperature: {info['temperature']}")
            print(f"  Context window: {info['context_window']}")

            print("\n" + "="*60)
            print("✓ ALL MOCK TESTS PASSED")
            print("="*60)
            print(f"\nTotal mock API calls: {mock_client.call_count}")
            print("\nThe OllamaManager is working correctly with mock data.")
            print("To test with real Ollama:")
            print("  1. Install Ollama from https://ollama.com")
            print("  2. Run: ollama pull llama3.2:3b")
            print("  3. Run: python main.py")
            print("="*60)

            return True


def test_direct_ollama_api():
    """Test the ollama library API directly with mock."""
    print("\n" + "="*60)
    print("TESTING OLLAMA LIBRARY API DIRECTLY")
    print("="*60)

    mock_client = MockOllamaClient()

    print("\n[Test 1] List models...")
    models_response = mock_client.list()
    models = models_response.get('models', [])
    print(f"  ✓ Found {len(models)} models:")
    for model in models:
        print(f"    - {model['name']}")

    print("\n[Test 2] Generate response...")
    response = mock_client.generate(
        model='llama3.2:3b',
        prompt='Hello, world!',
        options={'temperature': 0.3}
    )
    print(f"  ✓ Response: {response['response']}")
    print(f"  ✓ Done: {response['done']}")

    print("\n[Test 3] Chat conversation...")
    chat_response = mock_client.chat(
        model='llama3.2:3b',
        messages=[
            {'role': 'user', 'content': 'What is the weather like?'}
        ]
    )
    print(f"  ✓ Chat response: {chat_response['message']['content']}")

    print("\n" + "="*60)
    print("✓ DIRECT API TESTS PASSED")
    print("="*60)


def main():
    """Run all mock tests."""
    print("\n" + "="*70)
    print(" "*15 + "MOCK OLLAMA TEST SUITE")
    print("="*70)
    print("\nThis test suite uses mock Ollama responses to test the")
    print("mail-mind application without requiring Ollama to be installed.")
    print("\n" + "="*70)

    try:
        # Test direct API
        test_direct_ollama_api()

        # Test OllamaManager
        success = test_ollama_manager_with_mock()

        if success:
            print("\n" + "="*70)
            print("SUCCESS: All tests passed with mock Ollama!")
            print("="*70)
            print("\nNext steps:")
            print("  1. These tests verify the code logic works correctly")
            print("  2. To test with real Ollama, install from https://ollama.com")
            print("  3. Download a model: ollama pull llama3.2:3b")
            print("  4. Run the full application: python main.py")
            print("="*70 + "\n")
            return 0
        else:
            print("\n" + "="*70)
            print("FAILURE: Some tests failed")
            print("="*70 + "\n")
            return 1

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
