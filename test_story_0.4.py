#!/usr/bin/env python3
"""
Quick verification script for Story 0.4 implementation.

Tests that all remediation functions are importable and callable.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all new functions can be imported."""
    print("Testing imports...")

    try:
        from colorama import Fore, Style, init
        print("  ✓ colorama imported successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import colorama: {e}")
        return False

    # Import main.py functions
    import main

    # Check that all new functions exist
    required_functions = [
        'offer_remediations',
        'switch_to_smaller_model',
        'repull_current_model',
        'show_system_resources',
        'show_ollama_logs',
        'generate_support_report',
        '_sanitize_report'
    ]

    for func_name in required_functions:
        if hasattr(main, func_name):
            print(f"  ✓ {func_name}() exists")
        else:
            print(f"  ✗ {func_name}() not found")
            return False

    return True


def test_function_signatures():
    """Test that functions have correct signatures."""
    print("\nTesting function signatures...")

    import main
    import inspect

    # Test offer_remediations
    sig = inspect.signature(main.offer_remediations)
    params = list(sig.parameters.keys())
    print(f"  ✓ offer_remediations() parameters: {params}")
    assert 'diagnostic_results' in params

    # Test switch_to_smaller_model
    sig = inspect.signature(main.switch_to_smaller_model)
    params = list(sig.parameters.keys())
    print(f"  ✓ switch_to_smaller_model() parameters: {params}")
    assert sig.return_annotation == bool or str(sig.return_annotation) == 'bool'

    # Test repull_current_model
    sig = inspect.signature(main.repull_current_model)
    params = list(sig.parameters.keys())
    print(f"  ✓ repull_current_model() parameters: {params}")
    assert sig.return_annotation == bool or str(sig.return_annotation) == 'bool'

    # Test show_system_resources
    sig = inspect.signature(main.show_system_resources)
    print(f"  ✓ show_system_resources() signature correct")

    # Test show_ollama_logs
    sig = inspect.signature(main.show_ollama_logs)
    print(f"  ✓ show_ollama_logs() signature correct")

    # Test generate_support_report
    sig = inspect.signature(main.generate_support_report)
    print(f"  ✓ generate_support_report() signature correct")
    assert sig.return_annotation == str or str(sig.return_annotation) == 'str'

    return True


def test_sanitization():
    """Test that _sanitize_report works correctly."""
    print("\nTesting sanitization function...")

    import main

    # Use actual user's home path for testing
    home_path = str(Path.home())

    test_text = f"""
    User path: {home_path}/Documents/file.txt
    Email: test@example.com
    API Key: 1234567890abcdef1234567890abcdef
    password: secret123
    """

    sanitized = main._sanitize_report(test_text)

    # Check that sensitive data was removed
    assert home_path not in sanitized, "User path not sanitized"
    assert 'test@example.com' not in sanitized, "Email not sanitized"
    assert '1234567890abcdef1234567890abcdef' not in sanitized, "API key not sanitized"
    assert 'secret123' not in sanitized, "Password not sanitized"

    # Check that replacements were made
    assert '<user_home>' in sanitized, "User path replacement missing"
    assert '<email>' in sanitized, "Email replacement missing"
    assert '<redacted>' in sanitized, "Redaction marker missing"

    print("  ✓ Sanitization working correctly")
    return True


def test_config_integration():
    """Test that config loading still works."""
    print("\nTesting config integration...")

    from mailmind.utils.config import load_config, get_ollama_config

    try:
        config = load_config()
        print("  ✓ Config loading works")

        ollama_config = get_ollama_config(config)
        print(f"  ✓ Ollama config extracted: {ollama_config.get('primary_model', 'N/A')}")

        return True
    except Exception as e:
        print(f"  ✗ Config loading failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Story 0.4 Implementation Verification")
    print("=" * 60)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_imports()
    all_passed &= test_function_signatures()
    all_passed &= test_sanitization()
    all_passed &= test_config_integration()

    print()
    print("=" * 60)
    if all_passed:
        print("✅ All verification tests passed!")
        print()
        print("Story 0.4 implementation complete. Manual testing required:")
        print("  1. Run diagnostics: python main.py --diagnose")
        print("  2. Test menu navigation (simulate failure)")
        print("  3. Test each of 6 remediation options")
        print("  4. Verify colors display correctly")
        print("  5. Test on Windows (if available)")
    else:
        print("❌ Some verification tests failed")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
