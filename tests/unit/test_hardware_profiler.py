"""
Unit Tests for HardwareProfiler

Tests Story 1.6: Performance Optimization & Caching (AC2, AC9)
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from src.mailmind.core.hardware_profiler import HardwareProfiler


class TestHardwareDetection:
    """Test hardware detection functionality."""

    def test_detect_hardware_returns_profile(self):
        """Test hardware detection returns complete profile."""
        profile = HardwareProfiler.detect_hardware()

        # Verify all required fields are present
        assert 'cpu_cores' in profile
        assert 'cpu_logical_cores' in profile
        assert 'cpu_architecture' in profile
        assert 'ram_total_gb' in profile
        assert 'ram_available_gb' in profile
        assert 'os' in profile
        assert 'os_version' in profile
        assert 'hardware_tier' in profile
        assert 'expected_tokens_per_second' in profile
        assert 'recommended_model' in profile

    def test_cpu_detection(self):
        """Test CPU cores and architecture detection."""
        profile = HardwareProfiler.detect_hardware()

        assert profile['cpu_cores'] >= 1
        assert profile['cpu_logical_cores'] >= profile['cpu_cores']
        assert isinstance(profile['cpu_architecture'], str)
        assert len(profile['cpu_architecture']) > 0

    def test_ram_detection(self):
        """Test RAM detection."""
        profile = HardwareProfiler.detect_hardware()

        assert profile['ram_total_gb'] > 0
        assert profile['ram_available_gb'] > 0
        assert profile['ram_available_gb'] <= profile['ram_total_gb']

    def test_hardware_detection_performance(self):
        """Test hardware detection completes in <5 seconds."""
        start = time.time()
        profile = HardwareProfiler.detect_hardware()
        detection_time = time.time() - start

        assert detection_time < 5.0, f"Hardware detection took {detection_time:.2f}s (expected <5s)"

    @patch('src.mailmind.core.hardware_profiler.psutil')
    def test_gpu_detection_fallback(self, mock_psutil):
        """Test graceful fallback when GPU detection fails."""
        # Mock psutil methods
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.cpu_freq.return_value = MagicMock(current=3600)
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=32 * 1024**3,
            available=24 * 1024**3
        )

        profile = HardwareProfiler.detect_hardware()

        # Should have CPU/RAM but no GPU
        assert profile['cpu_cores'] == 8
        assert profile['ram_total_gb'] > 0
        assert profile['gpu_detected'] is None
        assert profile['gpu_vram_gb'] is None


class TestHardwareTierClassification:
    """Test hardware tier classification."""

    def test_optimal_tier_classification(self):
        """Test optimal tier classification (high GPU + high RAM)."""
        profile = {
            'ram_available_gb': 32.0,
            'gpu_detected': 'NVIDIA RTX 4090',
            'gpu_vram_gb': 24.0
        }

        tier = HardwareProfiler._classify_hardware_tier(profile)
        assert tier == 'Optimal'

    def test_recommended_tier_classification(self):
        """Test recommended tier classification (mid GPU + sufficient RAM)."""
        profile = {
            'ram_available_gb': 20.0,
            'gpu_detected': 'NVIDIA RTX 3060',
            'gpu_vram_gb': 8.0
        }

        tier = HardwareProfiler._classify_hardware_tier(profile)
        assert tier == 'Recommended'

    def test_minimum_tier_classification(self):
        """Test minimum tier classification (CPU-only with sufficient RAM)."""
        profile = {
            'ram_available_gb': 18.0,
            'gpu_detected': None,
            'gpu_vram_gb': None
        }

        tier = HardwareProfiler._classify_hardware_tier(profile)
        assert tier == 'Minimum'

    def test_insufficient_tier_classification(self):
        """Test insufficient tier classification (low RAM)."""
        profile = {
            'ram_available_gb': 8.0,
            'gpu_detected': None,
            'gpu_vram_gb': None
        }

        tier = HardwareProfiler._classify_hardware_tier(profile)
        assert tier == 'Insufficient'


class TestPerformanceEstimation:
    """Test performance estimation."""

    def test_performance_estimation_optimal(self):
        """Test performance estimation for optimal hardware."""
        profile = {'hardware_tier': 'Optimal'}
        tokens_per_sec = HardwareProfiler._estimate_performance(profile)

        assert tokens_per_sec == 120

    def test_performance_estimation_recommended(self):
        """Test performance estimation for recommended hardware."""
        profile = {'hardware_tier': 'Recommended'}
        tokens_per_sec = HardwareProfiler._estimate_performance(profile)

        assert tokens_per_sec == 75

    def test_performance_estimation_minimum(self):
        """Test performance estimation for minimum hardware."""
        profile = {'hardware_tier': 'Minimum'}
        tokens_per_sec = HardwareProfiler._estimate_performance(profile)

        assert tokens_per_sec == 15

    def test_performance_estimation_insufficient(self):
        """Test performance estimation for insufficient hardware."""
        profile = {'hardware_tier': 'Insufficient'}
        tokens_per_sec = HardwareProfiler._estimate_performance(profile)

        assert tokens_per_sec == 5


class TestModelRecommendation:
    """Test model recommendation logic."""

    def test_recommend_model_8gb_vram(self):
        """Test model recommendation with 8GB VRAM."""
        profile = {'gpu_vram_gb': 8.0}
        model = HardwareProfiler._recommend_model(profile)

        assert model == 'llama3.1:8b-instruct-q4_K_M'

    def test_recommend_model_6gb_vram(self):
        """Test model recommendation with 6GB VRAM."""
        profile = {'gpu_vram_gb': 6.0}
        model = HardwareProfiler._recommend_model(profile)

        assert model == 'mistral:7b-instruct-q4_K_M'

    def test_recommend_model_4gb_vram(self):
        """Test model recommendation with 4GB VRAM."""
        profile = {'gpu_vram_gb': 4.0}
        model = HardwareProfiler._recommend_model(profile)

        assert model == 'llama3.2:3b-instruct-q4_K_M'

    def test_recommend_model_no_gpu(self):
        """Test model recommendation with no GPU."""
        profile = {'gpu_vram_gb': None}
        model = HardwareProfiler._recommend_model(profile)

        # Should still recommend a model (CPU fallback)
        assert model == 'llama3.1:8b-instruct-q4_K_M'


class TestResourceMonitoring:
    """Test real-time resource monitoring."""

    def test_monitor_resources_returns_metrics(self):
        """Test resource monitoring returns current metrics."""
        resources = HardwareProfiler.monitor_resources()

        assert 'cpu_percent' in resources
        assert 'ram_used_gb' in resources
        assert 'ram_percent' in resources
        assert 'ram_available_gb' in resources
        assert 'timestamp' in resources

    def test_monitor_resources_performance(self):
        """Test resource monitoring completes in <100ms."""
        start = time.time()
        resources = HardwareProfiler.monitor_resources()
        monitoring_time_ms = (time.time() - start) * 1000

        assert monitoring_time_ms < 100, f"Resource monitoring took {monitoring_time_ms:.2f}ms (expected <100ms)"

    def test_monitor_resources_valid_ranges(self):
        """Test resource monitoring returns valid value ranges."""
        resources = HardwareProfiler.monitor_resources()

        assert 0 <= resources['cpu_percent'] <= 100
        assert 0 <= resources['ram_percent'] <= 100
        assert resources['ram_used_gb'] >= 0
        assert resources['ram_available_gb'] >= 0

    def test_check_memory_pressure(self):
        """Test memory pressure detection."""
        # Test with reasonable threshold
        is_under_pressure = HardwareProfiler.check_memory_pressure(threshold_percent=90.0)

        assert isinstance(is_under_pressure, bool)

        # Test with impossible threshold (should never trigger)
        is_under_pressure = HardwareProfiler.check_memory_pressure(threshold_percent=101.0)
        assert is_under_pressure is False


class TestOptimizationSettings:
    """Test optimization settings recommendations."""

    def test_optimization_settings_optimal(self):
        """Test optimization settings for optimal hardware."""
        profile = {
            'hardware_tier': 'Optimal',
            'gpu_detected': 'NVIDIA RTX 4090'
        }

        settings = HardwareProfiler.get_optimization_settings(profile)

        assert settings['batch_size'] == 15
        assert settings['timeout_seconds'] == 10
        assert settings['max_concurrent'] == 3
        assert settings['enable_gpu'] is True

    def test_optimization_settings_recommended(self):
        """Test optimization settings for recommended hardware."""
        profile = {
            'hardware_tier': 'Recommended',
            'gpu_detected': 'NVIDIA RTX 3060'
        }

        settings = HardwareProfiler.get_optimization_settings(profile)

        assert settings['batch_size'] == 10
        assert settings['timeout_seconds'] == 15
        assert settings['max_concurrent'] == 2
        assert settings['enable_gpu'] is True

    def test_optimization_settings_minimum(self):
        """Test optimization settings for minimum hardware (CPU-only)."""
        profile = {
            'hardware_tier': 'Minimum',
            'gpu_detected': None
        }

        settings = HardwareProfiler.get_optimization_settings(profile)

        assert settings['batch_size'] == 5
        assert settings['timeout_seconds'] == 30
        assert settings['max_concurrent'] == 1
        assert settings['enable_gpu'] is False

    def test_optimization_settings_insufficient(self):
        """Test optimization settings for insufficient hardware."""
        profile = {
            'hardware_tier': 'Insufficient',
            'gpu_detected': None
        }

        settings = HardwareProfiler.get_optimization_settings(profile)

        assert settings['batch_size'] == 1
        assert settings['timeout_seconds'] == 60
        assert settings['max_concurrent'] == 1
        assert settings['context_window'] == 1024
