"""
Hardware Profiler for MailMind

This module provides system hardware detection and profiling.
Implements Story 1.6: Performance Optimization & Caching (AC2, AC9)

Key Features:
- CPU cores and architecture detection
- RAM total and available detection
- GPU presence, model, and VRAM detection (NVIDIA)
- Hardware tier classification (Optimal/Recommended/Minimum/Insufficient)
- Expected tokens/second estimation based on hardware
- Model recommendation based on available VRAM
- Real-time resource monitoring (CPU%, RAM%, available RAM)

Integration:
- Used at application startup to configure optimal settings
- Standalone class with static methods
- Graceful fallback if GPU detection fails

Performance Targets:
- Hardware profiling: <2s target, <5s max
- Resource monitoring: <100ms per call
"""

import logging
import platform
import psutil
from typing import Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class HardwareProfiler:
    """
    Detects and profiles system hardware capabilities.

    Provides comprehensive hardware detection for CPU, RAM, and GPU,
    and classifies hardware into performance tiers for optimization.

    Example:
        # Detect hardware at startup
        profile = HardwareProfiler.detect_hardware()
        print(f"Hardware Tier: {profile['hardware_tier']}")
        print(f"Expected Performance: {profile['expected_tokens_per_second']} t/s")

        # Monitor resources during operation
        resources = HardwareProfiler.monitor_resources()
        print(f"RAM Usage: {resources['ram_percent']}%")
    """

    @staticmethod
    def detect_hardware() -> Dict[str, Any]:
        """
        Detect system hardware and capabilities.

        Returns:
            Hardware profile dictionary:
            {
                "cpu_cores": 8,
                "cpu_logical_cores": 16,
                "cpu_architecture": "x86_64",
                "cpu_frequency_mhz": 3600.0,
                "ram_total_gb": 32.0,
                "ram_available_gb": 24.0,
                "os": "Windows",
                "os_version": "10",
                "gpu_detected": "NVIDIA RTX 4060" or None,
                "gpu_vram_gb": 8.0 or None,
                "gpu_driver_version": "535.104.05" or None,
                "recommended_model": "llama3.1:8b-instruct-q4_K_M",
                "expected_tokens_per_second": 85,
                "hardware_tier": "Recommended"
            }
        """
        logger.info("Detecting hardware configuration...")

        profile = {
            'cpu_cores': psutil.cpu_count(logical=False) or 1,
            'cpu_logical_cores': psutil.cpu_count(logical=True) or 1,
            'cpu_architecture': platform.machine(),
            'cpu_frequency_mhz': 0.0,
            'ram_total_gb': 0.0,
            'ram_available_gb': 0.0,
            'os': platform.system(),
            'os_version': platform.release(),
            'gpu_detected': None,
            'gpu_vram_gb': None,
            'gpu_driver_version': None,
            'recommended_model': 'llama3.1:8b-instruct-q4_K_M',
            'expected_tokens_per_second': 0,
            'hardware_tier': 'Unknown'
        }

        # CPU frequency detection
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                profile['cpu_frequency_mhz'] = round(cpu_freq.current, 2)
        except Exception as e:
            logger.debug(f"CPU frequency detection failed: {e}")

        # RAM detection
        try:
            memory = psutil.virtual_memory()
            profile['ram_total_gb'] = round(memory.total / (1024**3), 2)
            profile['ram_available_gb'] = round(memory.available / (1024**3), 2)
        except Exception as e:
            logger.error(f"RAM detection failed: {e}")

        # GPU detection (NVIDIA only via py3nvml)
        profile = HardwareProfiler._detect_gpu(profile)

        # Determine hardware tier and recommendations
        profile['hardware_tier'] = HardwareProfiler._classify_hardware_tier(profile)
        profile['expected_tokens_per_second'] = HardwareProfiler._estimate_performance(profile)
        profile['recommended_model'] = HardwareProfiler._recommend_model(profile)

        logger.info(f"Hardware detected: {profile['hardware_tier']} tier, "
                   f"{profile['cpu_cores']} cores, "
                   f"{profile['ram_total_gb']}GB RAM, "
                   f"GPU: {profile['gpu_detected'] or 'None'}")

        return profile

    @staticmethod
    def _detect_gpu(profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect NVIDIA GPU using py3nvml.

        Args:
            profile: Hardware profile dict to update

        Returns:
            Updated hardware profile
        """
        try:
            import py3nvml.py3nvml as nvml

            nvml.nvmlInit()

            device_count = nvml.nvmlDeviceGetCount()
            if device_count > 0:
                # Get first GPU
                handle = nvml.nvmlDeviceGetHandleByIndex(0)

                # GPU name
                gpu_name = nvml.nvmlDeviceGetName(handle)
                if isinstance(gpu_name, bytes):
                    gpu_name = gpu_name.decode('utf-8')
                profile['gpu_detected'] = gpu_name

                # VRAM
                mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                profile['gpu_vram_gb'] = round(mem_info.total / (1024**3), 2)

                # Driver version
                driver_version = nvml.nvmlSystemGetDriverVersion()
                if isinstance(driver_version, bytes):
                    driver_version = driver_version.decode('utf-8')
                profile['gpu_driver_version'] = driver_version

                logger.info(f"GPU detected: {gpu_name} with {profile['gpu_vram_gb']}GB VRAM")

            nvml.nvmlShutdown()

        except ImportError:
            logger.debug("py3nvml not installed, GPU detection skipped (CPU-only mode)")
        except Exception as e:
            logger.debug(f"GPU detection failed: {e} (CPU-only mode)")

        return profile

    @staticmethod
    def _classify_hardware_tier(profile: Dict[str, Any]) -> str:
        """
        Classify hardware into Minimum/Recommended/Optimal tiers.

        Args:
            profile: Hardware profile dictionary

        Returns:
            Hardware tier string
        """
        ram = profile['ram_available_gb']
        has_gpu = profile['gpu_detected'] is not None
        vram = profile.get('gpu_vram_gb', 0) or 0

        if has_gpu and vram >= 8 and ram >= 24:
            return 'Optimal'  # High-end GPU, plenty of RAM
        elif has_gpu and vram >= 6 and ram >= 16:
            return 'Recommended'  # Mid-range GPU, sufficient RAM
        elif ram >= 16:
            return 'Minimum'  # CPU-only but enough RAM
        else:
            return 'Insufficient'  # Below minimum specs

    @staticmethod
    def _estimate_performance(profile: Dict[str, Any]) -> int:
        """
        Estimate tokens/second based on hardware.

        Args:
            profile: Hardware profile dictionary

        Returns:
            Estimated tokens per second
        """
        tier = profile['hardware_tier']

        performance_map = {
            'Optimal': 120,      # 100-200 t/s
            'Recommended': 75,   # 50-100 t/s
            'Minimum': 15,       # 10-30 t/s (CPU-only)
            'Insufficient': 5,   # 5-15 t/s (very slow)
            'Unknown': 10        # Default conservative estimate
        }

        return performance_map.get(tier, 10)

    @staticmethod
    def _recommend_model(profile: Dict[str, Any]) -> str:
        """
        Recommend model based on available VRAM.

        Args:
            profile: Hardware profile dictionary

        Returns:
            Recommended model string
        """
        vram = profile.get('gpu_vram_gb', 0) or 0

        if vram >= 8:
            return 'llama3.1:8b-instruct-q4_K_M'  # Best quality
        elif vram >= 6:
            return 'mistral:7b-instruct-q4_K_M'   # Good balance
        elif vram >= 4:
            return 'llama3.2:3b-instruct-q4_K_M'  # Smaller model for limited VRAM
        else:
            return 'llama3.1:8b-instruct-q4_K_M'  # CPU-only (fallback to standard model)

    @staticmethod
    def monitor_resources() -> Dict[str, Any]:
        """
        Monitor current resource usage.

        Returns:
            Resource usage dictionary:
            {
                "cpu_percent": 45.2,
                "ram_used_gb": 18.5,
                "ram_percent": 57.8,
                "ram_available_gb": 13.5,
                "timestamp": "2025-10-13T14:30:00"
            }
        """
        try:
            memory = psutil.virtual_memory()

            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'ram_used_gb': round((memory.total - memory.available) / (1024**3), 2),
                'ram_percent': memory.percent,
                'ram_available_gb': round(memory.available / (1024**3), 2),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Resource monitoring failed: {e}")
            return {
                'cpu_percent': 0.0,
                'ram_used_gb': 0.0,
                'ram_percent': 0.0,
                'ram_available_gb': 0.0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    @staticmethod
    def check_memory_pressure(threshold_percent: float = 85.0) -> bool:
        """
        Check if system is under memory pressure.

        Args:
            threshold_percent: Memory usage threshold (default: 85%)

        Returns:
            True if memory usage exceeds threshold
        """
        try:
            memory = psutil.virtual_memory()
            return memory.percent >= threshold_percent
        except Exception as e:
            logger.error(f"Memory pressure check failed: {e}")
            return False

    @staticmethod
    def get_optimization_settings(profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recommended optimization settings based on hardware profile.

        Args:
            profile: Hardware profile dictionary

        Returns:
            Optimization settings dictionary:
            {
                "batch_size": 5,
                "timeout_seconds": 30,
                "max_concurrent": 1,
                "enable_gpu": True
            }
        """
        tier = profile['hardware_tier']
        has_gpu = profile['gpu_detected'] is not None

        # Optimization settings by tier
        if tier == 'Optimal':
            return {
                'batch_size': 15,           # High throughput
                'timeout_seconds': 10,      # Fast inference expected
                'max_concurrent': 3,        # Can handle parallel requests
                'enable_gpu': True,
                'context_window': 8192,     # Large context window
                'num_predict': 500          # Generous token limit
            }
        elif tier == 'Recommended':
            return {
                'batch_size': 10,           # Good throughput
                'timeout_seconds': 15,      # Moderate inference time
                'max_concurrent': 2,        # Some parallelism
                'enable_gpu': True,
                'context_window': 4096,     # Standard context
                'num_predict': 400          # Standard token limit
            }
        elif tier == 'Minimum':
            return {
                'batch_size': 5,            # Reduced batch for CPU
                'timeout_seconds': 30,      # Slower CPU inference
                'max_concurrent': 1,        # Sequential only
                'enable_gpu': False,
                'context_window': 2048,     # Smaller context for speed
                'num_predict': 300          # Reduced tokens
            }
        else:  # Insufficient
            return {
                'batch_size': 1,            # Minimal batching
                'timeout_seconds': 60,      # Very slow inference
                'max_concurrent': 1,        # Sequential only
                'enable_gpu': has_gpu,      # Try GPU if available
                'context_window': 1024,     # Minimal context
                'num_predict': 200          # Minimal tokens
            }
