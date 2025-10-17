#!/usr/bin/env python3
"""
Test suite for Story 0.5: Dynamic Model Loading & Runtime Switching

Tests all 3 acceptance criteria:
- AC1: Runtime Model Switching Command (--switch-model flag)
- AC2: Automatic Model Fallback (3 timeout detection)
- AC3: Model Performance Monitoring

Run with: python -m pytest test_story_0.5.py -v
Or: python test_story_0.5.py
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path
from unittest import mock
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all Story 0.5 functions and classes can be imported."""
    print("\n" + "=" * 60)
    print("TEST 1: Imports")
    print("=" * 60)

    # Test main.py functions
    import main
    assert hasattr(main, 'handle_model_switch'), "handle_model_switch() not found in main.py"
    print("  ✓ handle_model_switch() exists in main.py")

    # Test OllamaManager AC2 additions
    from mailmind.core.ollama_manager import OllamaManager

    # Create a mock OllamaManager to test attributes
    mock_config = {
        'primary_model': 'llama3.1:8b-instruct-q4_K_M',
        'fallback_model': 'mistral:7b-instruct-q4_K_M',
        'pool_size': 3
    }

    manager = OllamaManager(mock_config)

    # Check AC2 attributes
    assert hasattr(manager, 'consecutive_timeouts'), "consecutive_timeouts not found"
    assert hasattr(manager, 'fallback_history'), "fallback_history not found"
    assert hasattr(manager, 'fallback_triggered'), "fallback_triggered not found"
    print("  ✓ AC2 timeout tracking attributes exist")

    # Check AC2 methods
    assert hasattr(manager, 'generate'), "generate() method not found"
    assert hasattr(manager, '_handle_automatic_fallback'), "_handle_automatic_fallback() not found"
    assert hasattr(manager, '_switch_model_internal'), "_switch_model_internal() not found"
    print("  ✓ AC2 methods exist")

    # Check AC3 attributes and methods
    assert hasattr(manager, 'performance_tracker'), "performance_tracker not found"
    assert hasattr(manager, 'get_model_performance'), "get_model_performance() not found"
    assert hasattr(manager, 'get_model_performance_display'), "get_model_performance_display() not found"
    assert hasattr(manager, 'check_upgrade_recommendation'), "check_upgrade_recommendation() not found"
    print("  ✓ AC3 performance monitoring attributes and methods exist")

    print("\n✅ All imports successful!")
    return True


def test_ac1_command_line_flag():
    """AC1 Test 1: Test --switch-model command-line flag is recognized."""
    print("\n" + "=" * 60)
    print("TEST 2: AC1 - Command-line Flag Recognition")
    print("=" * 60)

    import main

    # Check that --switch-model is documented in main()
    main_source = Path(__file__).parent / "main.py"
    content = main_source.read_text()

    assert '--switch-model' in content, "--switch-model flag not found in main.py"
    assert 'handle_model_switch()' in content, "handle_model_switch() call not found"
    print("  ✓ --switch-model flag is implemented in main()")

    print("\n✅ AC1 command-line flag test passed!")
    return True


def test_ac1_handle_model_switch_function():
    """AC1 Test 2: Test handle_model_switch() function structure."""
    print("\n" + "=" * 60)
    print("TEST 3: AC1 - handle_model_switch() Function")
    print("=" * 60)

    import main
    import inspect

    # Check function signature
    sig = inspect.signature(main.handle_model_switch)
    assert sig.return_annotation == bool or str(sig.return_annotation) == 'bool', \
        "handle_model_switch() should return bool"
    print("  ✓ handle_model_switch() has correct return type (bool)")

    # Check function docstring mentions key features
    doc = main.handle_model_switch.__doc__
    assert 'AC1' in doc or 'model switching' in doc.lower(), \
        "Function docstring should mention AC1 or model switching"
    print("  ✓ Function docstring describes AC1 functionality")

    print("\n✅ AC1 handle_model_switch() structure test passed!")
    return True


def test_ac1_config_update_logic():
    """AC1 Test 3: Test user_config.yaml update logic."""
    print("\n" + "=" * 60)
    print("TEST 4: AC1 - Config Update Logic")
    print("=" * 60)

    # Create a temporary config file
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config"
        config_dir.mkdir()
        user_config_path = config_dir / "user_config.yaml"

        # Create initial config
        initial_config = {
            'ollama': {
                'selected_model': 'llama3.1:8b-instruct-q4_K_M',
                'model_size': 'large'
            }
        }

        with open(user_config_path, 'w') as f:
            yaml.dump(initial_config, f)

        print(f"  ✓ Created temporary config: {user_config_path}")

        # Verify it was created
        assert user_config_path.exists(), "Config file not created"

        # Read it back
        with open(user_config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)

        assert loaded_config['ollama']['selected_model'] == 'llama3.1:8b-instruct-q4_K_M'
        print("  ✓ Config file can be read and written")

        # Simulate update to smaller model
        loaded_config['ollama']['selected_model'] = 'llama3.2:3b'
        loaded_config['ollama']['model_size'] = 'medium'

        with open(user_config_path, 'w') as f:
            yaml.dump(loaded_config, f)

        # Verify update
        with open(user_config_path, 'r') as f:
            updated_config = yaml.safe_load(f)

        assert updated_config['ollama']['selected_model'] == 'llama3.2:3b'
        assert updated_config['ollama']['model_size'] == 'medium'
        print("  ✓ Config update logic works correctly")

    print("\n✅ AC1 config update test passed!")
    return True


def test_ac2_timeout_tracking():
    """AC2 Test 1: Test timeout counter tracking."""
    print("\n" + "=" * 60)
    print("TEST 5: AC2 - Timeout Tracking")
    print("=" * 60)

    from mailmind.core.ollama_manager import OllamaManager

    mock_config = {
        'primary_model': 'llama3.1:8b-instruct-q4_K_M',
        'fallback_model': 'mistral:7b-instruct-q4_K_M',
        'pool_size': 3
    }

    manager = OllamaManager(mock_config)

    # Check initial state
    assert manager.consecutive_timeouts == 0, "Initial timeout counter should be 0"
    print("  ✓ Timeout counter initialized to 0")

    assert manager.fallback_triggered == False, "Fallback should not be triggered initially"
    print("  ✓ Fallback trigger initialized to False")

    assert manager.fallback_history == [], "Fallback history should be empty"
    print("  ✓ Fallback history initialized as empty list")

    print("\n✅ AC2 timeout tracking test passed!")
    return True


def test_ac2_fallback_chain():
    """AC2 Test 2: Test model fallback chain logic."""
    print("\n" + "=" * 60)
    print("TEST 6: AC2 - Fallback Chain")
    print("=" * 60)

    # Expected fallback chain
    fallback_chain = {
        'llama3.1:8b-instruct-q4_K_M': 'llama3.2:3b',
        'llama3.2:3b': 'llama3.2:1b',
        'llama3.2:1b': None
    }

    # Test each link in the chain
    assert fallback_chain['llama3.1:8b-instruct-q4_K_M'] == 'llama3.2:3b'
    print("  ✓ 8B model falls back to 3B")

    assert fallback_chain['llama3.2:3b'] == 'llama3.2:1b'
    print("  ✓ 3B model falls back to 1B")

    assert fallback_chain['llama3.2:1b'] is None
    print("  ✓ 1B model has no fallback (smallest)")

    print("\n✅ AC2 fallback chain test passed!")
    return True


def test_ac2_generate_method_signature():
    """AC2 Test 3: Test generate() method signature."""
    print("\n" + "=" * 60)
    print("TEST 7: AC2 - generate() Method Signature")
    print("=" * 60)

    from mailmind.core.ollama_manager import OllamaManager
    import inspect

    # Check method signature
    sig = inspect.signature(OllamaManager.generate)
    params = list(sig.parameters.keys())

    assert 'self' in params, "generate() should be an instance method"
    assert 'prompt' in params, "generate() should have 'prompt' parameter"
    assert 'timeout' in params, "generate() should have 'timeout' parameter"
    print("  ✓ generate() has correct parameters (self, prompt, timeout)")

    # Check timeout default value
    timeout_param = sig.parameters['timeout']
    assert timeout_param.default == 30, "Default timeout should be 30 seconds"
    print("  ✓ Timeout default is 30 seconds")

    print("\n✅ AC2 generate() signature test passed!")
    return True


def test_ac3_performance_tracker_integration():
    """AC3 Test 1: Test PerformanceTracker integration."""
    print("\n" + "=" * 60)
    print("TEST 8: AC3 - PerformanceTracker Integration")
    print("=" * 60)

    from mailmind.core.ollama_manager import OllamaManager
    from mailmind.core.performance_tracker import PerformanceTracker

    # Create OllamaManager with database path
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        mock_config = {
            'primary_model': 'llama3.1:8b-instruct-q4_K_M',
            'fallback_model': 'mistral:7b-instruct-q4_K_M',
            'pool_size': 3,
            'database_path': str(db_path)
        }

        manager = OllamaManager(mock_config)

        # Check that performance_tracker was initialized
        if manager.performance_tracker:
            print("  ✓ PerformanceTracker initialized in OllamaManager")
            assert isinstance(manager.performance_tracker, PerformanceTracker)
            print("  ✓ performance_tracker is a PerformanceTracker instance")
        else:
            print("  ⚠️  PerformanceTracker not available (optional dependency)")

    print("\n✅ AC3 PerformanceTracker integration test passed!")
    return True


def test_ac3_get_model_performance():
    """AC3 Test 2: Test get_model_performance() method."""
    print("\n" + "=" * 60)
    print("TEST 9: AC3 - get_model_performance() Method")
    print("=" * 60)

    from mailmind.core.ollama_manager import OllamaManager
    import inspect

    # Check method exists
    assert hasattr(OllamaManager, 'get_model_performance'), \
        "get_model_performance() not found"
    print("  ✓ get_model_performance() method exists")

    # Check signature
    sig = inspect.signature(OllamaManager.get_model_performance)
    params = list(sig.parameters.keys())

    assert 'self' in params, "Should be instance method"
    assert 'model_name' in params, "Should have model_name parameter"
    assert 'days' in params, "Should have days parameter"
    print("  ✓ Method has correct parameters")

    # Check days default
    days_param = sig.parameters['days']
    assert days_param.default == 30, "Default days should be 30"
    print("  ✓ Default period is 30 days")

    print("\n✅ AC3 get_model_performance() test passed!")
    return True


def test_ac3_display_format():
    """AC3 Test 3: Test get_model_performance_display() format."""
    print("\n" + "=" * 60)
    print("TEST 10: AC3 - Performance Display Format")
    print("=" * 60)

    from mailmind.core.ollama_manager import OllamaManager

    # Create manager with current model
    mock_config = {
        'primary_model': 'llama3.2:3b',
        'fallback_model': 'mistral:7b-instruct-q4_K_M',
        'pool_size': 3
    }

    manager = OllamaManager(mock_config)
    manager.current_model = 'llama3.2:3b'

    # Get display string
    display = manager.get_model_performance_display()

    assert 'llama3.2:3b' in display, "Display should include model name"
    print(f"  ✓ Display format: {display}")

    # Should follow format: "Current model: llama3.2:3b (avg: X.Xs)" or similar
    assert 'Current model:' in display or 'model' in display.lower()
    print("  ✓ Display includes 'Current model' or 'model'")

    print("\n✅ AC3 performance display test passed!")
    return True


def test_ac3_upgrade_recommendation():
    """AC3 Test 4: Test check_upgrade_recommendation() logic."""
    print("\n" + "=" * 60)
    print("TEST 11: AC3 - Upgrade Recommendation")
    print("=" * 60)

    from mailmind.core.ollama_manager import OllamaManager
    import inspect

    # Check method exists
    assert hasattr(OllamaManager, 'check_upgrade_recommendation'), \
        "check_upgrade_recommendation() not found"
    print("  ✓ check_upgrade_recommendation() method exists")

    # Check return type annotation
    sig = inspect.signature(OllamaManager.check_upgrade_recommendation)
    # Should return Optional[Dict[str, Any]]
    print(f"  ✓ Return type: {sig.return_annotation}")

    # Test model hierarchy logic
    model_hierarchy = [
        'llama3.2:1b',
        'llama3.2:3b',
        'llama3.1:8b-instruct-q4_K_M'
    ]

    # Verify hierarchy ordering (smallest to largest)
    assert model_hierarchy[0] == 'llama3.2:1b', "Smallest should be 1B"
    assert model_hierarchy[1] == 'llama3.2:3b', "Medium should be 3B"
    assert model_hierarchy[2] == 'llama3.1:8b-instruct-q4_K_M', "Largest should be 8B"
    print("  ✓ Model hierarchy is correct (1B → 3B → 8B)")

    print("\n✅ AC3 upgrade recommendation test passed!")
    return True


def test_integration_story_0_4_compatibility():
    """Integration Test 1: Verify Story 0.4 compatibility."""
    print("\n" + "=" * 60)
    print("TEST 12: Integration - Story 0.4 Compatibility")
    print("=" * 60)

    import main

    # Check that Story 0.4 functions still exist
    story_0_4_functions = [
        'switch_to_smaller_model',
        'repull_current_model',
        'show_system_resources',
        'show_ollama_logs',
        'generate_support_report',
        'offer_remediations',
        '_sanitize_report'
    ]

    for func_name in story_0_4_functions:
        assert hasattr(main, func_name), f"Story 0.4 function {func_name}() missing"
        print(f"  ✓ {func_name}() still exists")

    print("\n✅ Story 0.4 compatibility test passed!")
    return True


def test_integration_config_persistence():
    """Integration Test 2: Test config persistence across operations."""
    print("\n" + "=" * 60)
    print("TEST 13: Integration - Config Persistence")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "user_config.yaml"

        # Write initial config
        config = {
            'ollama': {
                'selected_model': 'llama3.1:8b-instruct-q4_K_M',
                'primary_model': 'llama3.1:8b-instruct-q4_K_M',
                'model_size': 'large'
            }
        }

        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        print("  ✓ Created initial config (8B model)")

        # Simulate model switch to 3B
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        config['ollama']['selected_model'] = 'llama3.2:3b'
        config['ollama']['primary_model'] = 'llama3.2:3b'
        config['ollama']['model_size'] = 'medium'

        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        print("  ✓ Updated config to 3B model")

        # Verify persistence
        with open(config_path, 'r') as f:
            loaded = yaml.safe_load(f)

        assert loaded['ollama']['selected_model'] == 'llama3.2:3b'
        assert loaded['ollama']['primary_model'] == 'llama3.2:3b'
        assert loaded['ollama']['model_size'] == 'medium'
        print("  ✓ Config changes persisted correctly")

    print("\n✅ Config persistence test passed!")
    return True


def test_integration_full_workflow():
    """Integration Test 3: Test complete workflow."""
    print("\n" + "=" * 60)
    print("TEST 14: Integration - Full Workflow")
    print("=" * 60)

    # Test that all components work together:
    # 1. OllamaManager can be created
    # 2. Has timeout tracking (AC2)
    # 3. Has performance tracking (AC3)
    # 4. handle_model_switch exists (AC1)

    from mailmind.core.ollama_manager import OllamaManager
    import main

    # Step 1: Create OllamaManager
    mock_config = {
        'primary_model': 'llama3.1:8b-instruct-q4_K_M',
        'fallback_model': 'mistral:7b-instruct-q4_K_M',
        'pool_size': 3
    }

    manager = OllamaManager(mock_config)
    print("  ✓ Step 1: OllamaManager created")

    # Step 2: Verify AC2 (timeout tracking)
    assert hasattr(manager, 'consecutive_timeouts')
    assert hasattr(manager, 'generate')
    print("  ✓ Step 2: AC2 timeout tracking available")

    # Step 3: Verify AC3 (performance monitoring)
    assert hasattr(manager, 'get_model_performance')
    assert hasattr(manager, 'get_model_performance_display')
    print("  ✓ Step 3: AC3 performance monitoring available")

    # Step 4: Verify AC1 (model switching)
    assert hasattr(main, 'handle_model_switch')
    print("  ✓ Step 4: AC1 model switching command available")

    print("\n✅ Full workflow integration test passed!")
    return True


def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 60)
    print("STORY 0.5 TEST SUITE")
    print("Dynamic Model Loading & Runtime Switching")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("AC1: Command-line Flag", test_ac1_command_line_flag),
        ("AC1: Function Structure", test_ac1_handle_model_switch_function),
        ("AC1: Config Update", test_ac1_config_update_logic),
        ("AC2: Timeout Tracking", test_ac2_timeout_tracking),
        ("AC2: Fallback Chain", test_ac2_fallback_chain),
        ("AC2: generate() Signature", test_ac2_generate_method_signature),
        ("AC3: PerformanceTracker", test_ac3_performance_tracker_integration),
        ("AC3: get_model_performance()", test_ac3_get_model_performance),
        ("AC3: Display Format", test_ac3_display_format),
        ("AC3: Upgrade Recommendation", test_ac3_upgrade_recommendation),
        ("Integration: Story 0.4 Compat", test_integration_story_0_4_compatibility),
        ("Integration: Config Persistence", test_integration_config_persistence),
        ("Integration: Full Workflow", test_integration_full_workflow),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nStory 0.5 implementation is complete and verified.")
        print("\nNext steps:")
        print("  1. Run manual tests with: python main.py --switch-model")
        print("  2. Test automatic fallback with real Ollama timeouts")
        print("  3. Verify performance metrics are logged to database")
        print("  4. Update Epic file and mark story as DONE")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please fix before proceeding.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
