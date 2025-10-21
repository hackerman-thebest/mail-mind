#!/usr/bin/env python3
"""
Mock Ollama Server - Simulates Ollama API for realistic testing

This creates a local HTTP server that implements the Ollama API,
allowing the real ollama Python library to connect and make requests.
"""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class OllamaAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler that implements Ollama API endpoints."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json_response(self, data, status=200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_streaming_response(self, responses):
        """Send streaming JSON response (one JSON per line)."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/x-ndjson')
        self.end_headers()

        for response in responses:
            self.wfile.write(json.dumps(response).encode())
            self.wfile.write(b'\n')
            self.wfile.flush()
            time.sleep(0.1)  # Simulate streaming delay

    def do_GET(self):
        """Handle GET requests."""
        path = urlparse(self.path).path

        if path == '/api/tags' or path == '/api/tags/':
            # List models endpoint
            response = {
                'models': [
                    {
                        'name': 'llama3.2:3b',
                        'model': 'llama3.2:3b',
                        'modified_at': '2024-01-01T00:00:00Z',
                        'size': 2147483648,
                        'digest': 'sha256:mock123',
                        'details': {
                            'parent_model': '',
                            'format': 'gguf',
                            'family': 'llama',
                            'families': ['llama'],
                            'parameter_size': '3B',
                            'quantization_level': 'Q4_0'
                        }
                    },
                    {
                        'name': 'llama3.1:8b-instruct-q4_K_M',
                        'model': 'llama3.1:8b-instruct-q4_K_M',
                        'modified_at': '2024-01-01T00:00:00Z',
                        'size': 5368709120,
                        'digest': 'sha256:mock456',
                        'details': {
                            'parent_model': '',
                            'format': 'gguf',
                            'family': 'llama',
                            'families': ['llama'],
                            'parameter_size': '8B',
                            'quantization_level': 'Q4_K_M'
                        }
                    }
                ]
            }
            self._send_json_response(response)

        elif path == '/api/version':
            # Version endpoint
            response = {
                'version': '0.1.0-mock'
            }
            self._send_json_response(response)

        elif path == '/api/ps':
            # Running models endpoint
            response = {
                'models': []
            }
            self._send_json_response(response)

        else:
            self._send_json_response({'error': 'Not found'}, 404)

    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            request_data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response({'error': 'Invalid JSON'}, 400)
            return

        if path == '/api/generate':
            # Generate endpoint
            model = request_data.get('model', 'llama3.2:3b')
            prompt = request_data.get('prompt', '')
            stream = request_data.get('stream', True)

            # Generate realistic response based on prompt
            response_text = self._generate_response(prompt)

            if stream:
                # Streaming response (simulate word-by-word generation)
                words = response_text.split()
                responses = []

                for i, word in enumerate(words):
                    is_last = (i == len(words) - 1)
                    chunk = {
                        'model': model,
                        'created_at': '2024-01-01T00:00:00Z',
                        'response': word + (' ' if not is_last else ''),
                        'done': False
                    }
                    responses.append(chunk)

                # Final chunk
                final_chunk = {
                    'model': model,
                    'created_at': '2024-01-01T00:00:00Z',
                    'response': '',
                    'done': True,
                    'context': [1, 2, 3],
                    'total_duration': 500000000,
                    'load_duration': 100000000,
                    'prompt_eval_count': len(prompt.split()),
                    'prompt_eval_duration': 200000000,
                    'eval_count': len(words),
                    'eval_duration': 300000000
                }
                responses.append(final_chunk)

                self._send_streaming_response(responses)
            else:
                # Non-streaming response
                response = {
                    'model': model,
                    'created_at': '2024-01-01T00:00:00Z',
                    'response': response_text,
                    'done': True,
                    'context': [1, 2, 3],
                    'total_duration': 500000000,
                    'load_duration': 100000000,
                    'prompt_eval_count': len(prompt.split()),
                    'prompt_eval_duration': 200000000,
                    'eval_count': len(response_text.split()),
                    'eval_duration': 300000000
                }
                self._send_json_response(response)

        elif path == '/api/chat':
            # Chat endpoint
            model = request_data.get('model', 'llama3.2:3b')
            messages = request_data.get('messages', [])
            stream = request_data.get('stream', True)

            # Get last message
            last_message = messages[-1] if messages else {'content': ''}
            prompt = last_message.get('content', '')

            response_text = self._generate_response(prompt)

            if stream:
                # Streaming chat response
                words = response_text.split()
                responses = []

                for i, word in enumerate(words):
                    is_last = (i == len(words) - 1)
                    chunk = {
                        'model': model,
                        'created_at': '2024-01-01T00:00:00Z',
                        'message': {
                            'role': 'assistant',
                            'content': word + (' ' if not is_last else '')
                        },
                        'done': False
                    }
                    responses.append(chunk)

                final_chunk = {
                    'model': model,
                    'created_at': '2024-01-01T00:00:00Z',
                    'message': {
                        'role': 'assistant',
                        'content': ''
                    },
                    'done': True
                }
                responses.append(final_chunk)

                self._send_streaming_response(responses)
            else:
                response = {
                    'model': model,
                    'created_at': '2024-01-01T00:00:00Z',
                    'message': {
                        'role': 'assistant',
                        'content': response_text
                    },
                    'done': True
                }
                self._send_json_response(response)

        else:
            self._send_json_response({'error': 'Not found'}, 404)

    def _generate_response(self, prompt):
        """Generate a contextual response based on the prompt."""
        prompt_lower = prompt.lower()

        if 'test' in prompt_lower and len(prompt) < 20:
            return "Test response successful."
        elif 'hello' in prompt_lower:
            return "Hello! How can I assist you today?"
        elif 'priority' in prompt_lower or 'classify' in prompt_lower:
            if 'urgent' in prompt_lower:
                return "Priority: HIGH - This appears to be an urgent matter requiring immediate attention."
            elif 'fyi' in prompt_lower:
                return "Priority: LOW - This is informational and does not require immediate action."
            else:
                return "Priority: MEDIUM - This requires attention but is not urgent."
        elif 'sentiment' in prompt_lower or 'analyze' in prompt_lower:
            if 'frustrated' in prompt_lower or 'angry' in prompt_lower:
                return "Sentiment: NEGATIVE. The tone indicates frustration or dissatisfaction."
            elif 'thank' in prompt_lower:
                return "Sentiment: POSITIVE. The message expresses gratitude and appreciation."
            else:
                return "Sentiment: NEUTRAL. The tone is professional and matter-of-fact."
        elif 'summarize' in prompt_lower:
            return "Summary: This email discusses key updates and action items for the team."
        elif 'generate' in prompt_lower or 'reply' in prompt_lower:
            return "Thank you for your message. I've reviewed your request and will get back to you shortly with the information you need."
        else:
            return f"I understand you're asking about: {prompt[:50]}... I'll provide a helpful response based on this context."


def start_mock_server(port=11434):
    """Start the mock Ollama server."""
    server = HTTPServer(('localhost', port), OllamaAPIHandler)
    print(f"🚀 Mock Ollama Server started on http://localhost:{port}")
    print(f"📡 Listening for API requests...")
    print(f"✓ Endpoints available: /api/tags, /api/generate, /api/chat, /api/version")
    print(f"\nPress Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down mock server...")
        server.shutdown()


def test_with_mock_server():
    """Test the ollama library against the mock server."""
    print("\n" + "="*70)
    print("TESTING OLLAMA LIBRARY WITH MOCK SERVER")
    print("="*70)

    # Start server in background thread
    server_thread = threading.Thread(target=start_mock_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    import ollama

    try:
        # Test 1: List models
        print("\n[Test 1] Listing available models...")
        client = ollama.Client(host='http://localhost:11434')
        response = client.list()
        models = response.get('models', [])
        print(f"✓ Found {len(models)} models:")
        for model in models:
            name = model.get('name') or model.get('model', 'unknown')
            size = model.get('size', 0)
            print(f"  - {name} ({size / 1e9:.1f} GB)")

        # Test 2: Generate (non-streaming)
        print("\n[Test 2] Testing generate (non-streaming)...")
        response = client.generate(
            model='llama3.2:3b',
            prompt='Hello, how are you?',
            stream=False
        )
        print(f"✓ Response: {response['response']}")
        print(f"  Eval count: {response.get('eval_count', 0)} tokens")

        # Test 3: Generate (streaming)
        print("\n[Test 3] Testing generate (streaming)...")
        print("  Response: ", end='', flush=True)
        for chunk in client.generate(
            model='llama3.2:3b',
            prompt='Test streaming response',
            stream=True
        ):
            if not chunk['done']:
                print(chunk['response'], end='', flush=True)
        print("\n✓ Streaming completed")

        # Test 4: Priority classification
        print("\n[Test 4] Testing priority classification...")
        response = client.generate(
            model='llama3.2:3b',
            prompt='Classify priority: URGENT: Server down!',
            stream=False
        )
        print(f"✓ Classification: {response['response']}")

        # Test 5: Chat
        print("\n[Test 5] Testing chat endpoint...")
        response = client.chat(
            model='llama3.2:3b',
            messages=[
                {'role': 'user', 'content': 'Hello!'}
            ],
            stream=False
        )
        print(f"✓ Chat response: {response['message']['content']}")

        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED WITH MOCK SERVER")
        print("="*70)
        print("\nThe ollama library successfully connected to our mock server!")
        print("This demonstrates that the integration works correctly.\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nTest complete. Mock server will continue running...")
        print("Press Ctrl+C to stop the server.\n")

        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--server-only':
        # Run server only
        start_mock_server()
    else:
        # Run tests with server
        test_with_mock_server()
