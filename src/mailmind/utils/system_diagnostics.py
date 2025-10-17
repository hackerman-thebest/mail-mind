"""
System Resource Detection & Model Recommendation

Part of Story 0.1: System Resource Detection & Model Recommendation
Detects hardware resources and recommends appropriate AI model.
"""

import psutil
import platform
import subprocess
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


def check_system_resources() -> Dict[str, Any]:
    """
    Comprehensive system resource check.

    Returns:
        dict: {
            'ram': {'total_gb': float, 'available_gb': float, 'percent_used': float},
            'cpu': {'cores': int, 'percent_avg': float},
            'gpu': {'detected': bool, 'name': str, 'vram_gb': float},
            'disk': {'total_gb': float, 'free_gb': float},
            'platform': str
        }
    """
    logger.info("Checking system resources...")

    # RAM check
    ram = psutil.virtual_memory()
    ram_info = {
        'total_gb': ram.total / (1024**3),
        'available_gb': ram.available / (1024**3),
        'percent_used': ram.percent
    }

    # CPU check (5-second average)
    logger.info("Measuring CPU usage (5-second average)...")
    cpu_percent = psutil.cpu_percent(interval=5)
    cpu_info = {
        'cores': psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True),
        'percent_avg': cpu_percent
    }

    # GPU check (platform-specific)
    gpu_info = _detect_gpu()

    # Disk check
    disk = psutil.disk_usage('/')
    disk_info = {
        'total_gb': disk.total / (1024**3),
        'free_gb': disk.free / (1024**3)
    }

    resources = {
        'ram': ram_info,
        'cpu': cpu_info,
        'gpu': gpu_info,
        'disk': disk_info,
        'platform': platform.system()
    }

    logger.info(f"Resource check complete: {ram_info['available_gb']:.1f}GB RAM available")
    return resources


def recommend_model(resources: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Recommend appropriate model based on system resources.

    Args:
        resources: Output from check_system_resources()

    Returns:
        Tuple of (model_name, reasoning, expected_performance)
    """
    available_ram = resources['ram']['available_gb']
    has_gpu = resources['gpu']['detected']

    logger.info(f"Recommending model for {available_ram:.1f}GB available RAM, GPU: {has_gpu}")

    # Model selection logic
    if available_ram >= 10:
        model = 'llama3.1:8b-instruct-q4_K_M'
        reasoning = "Your system has sufficient RAM for the highest quality model"
        performance = {
            'tokens_per_second': '10-30 t/s' if has_gpu else '1-3 t/s',
            'quality': 'Best',
            'size_gb': 5
        }
    elif available_ram >= 6:
        model = 'llama3.2:3b'
        reasoning = "Balanced model recommended for your system (good performance + quality)"
        performance = {
            'tokens_per_second': '20-40 t/s' if has_gpu else '3-8 t/s',
            'quality': 'Good',
            'size_gb': 2
        }
    else:
        model = 'llama3.2:1b'
        reasoning = "Lightweight model recommended due to limited available RAM"
        performance = {
            'tokens_per_second': '30-50 t/s' if has_gpu else '5-10 t/s',
            'quality': 'Basic',
            'size_gb': 1
        }

    logger.info(f"Recommended model: {model} ({reasoning})")
    return model, reasoning, performance


def _detect_gpu() -> Dict[str, Any]:
    """
    Detect GPU presence and specs (platform-specific).

    Returns:
        dict: {'detected': bool, 'name': str, 'vram_gb': float}
    """
    gpu_info = {
        'detected': False,
        'name': 'None',
        'vram_gb': 0.0
    }

    system = platform.system()

    try:
        if system == 'Windows':
            # Try nvidia-smi for NVIDIA GPUs
            gpu_info = _detect_nvidia_gpu()
            if not gpu_info['detected']:
                # Try wmic for other GPUs (AMD, Intel)
                gpu_info = _detect_windows_gpu_wmic()

        elif system == 'Darwin':  # macOS
            gpu_info = _detect_macos_gpu()

        elif system == 'Linux':
            # Try nvidia-smi first
            gpu_info = _detect_nvidia_gpu()
            if not gpu_info['detected']:
                # Try lspci
                gpu_info = _detect_linux_gpu_lspci()

    except Exception as e:
        logger.warning(f"GPU detection failed: {e}")

    return gpu_info


def _detect_nvidia_gpu() -> Dict[str, Any]:
    """Detect NVIDIA GPU using nvidia-smi."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            if lines:
                parts = lines[0].split(',')
                if len(parts) >= 2:
                    name = parts[0].strip()
                    vram_mb = float(parts[1].strip())
                    return {
                        'detected': True,
                        'name': name,
                        'vram_gb': vram_mb / 1024
                    }

    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    return {'detected': False, 'name': 'None', 'vram_gb': 0.0}


def _detect_windows_gpu_wmic() -> Dict[str, Any]:
    """Detect GPU on Windows using wmic."""
    try:
        result = subprocess.run(
            ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            # Skip header line
            if len(lines) > 1:
                gpu_name = lines[1]
                if gpu_name and gpu_name.lower() != 'name':
                    return {
                        'detected': True,
                        'name': gpu_name,
                        'vram_gb': 0.0  # WMIC doesn't reliably report VRAM
                    }

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return {'detected': False, 'name': 'None', 'vram_gb': 0.0}


def _detect_macos_gpu() -> Dict[str, Any]:
    """Detect GPU on macOS using system_profiler."""
    try:
        result = subprocess.run(
            ['system_profiler', 'SPDisplaysDataType'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )

        if result.returncode == 0 and result.stdout:
            # Parse system_profiler output for GPU name and VRAM
            lines = result.stdout.split('\n')
            gpu_name = None
            vram_gb = 0.0

            for i, line in enumerate(lines):
                if 'Chipset Model:' in line:
                    gpu_name = line.split(':', 1)[1].strip()
                elif 'VRAM' in line or 'Memory' in line:
                    # Try to extract VRAM size (e.g., "8 GB")
                    parts = line.split(':')
                    if len(parts) > 1:
                        vram_str = parts[1].strip()
                        # Parse "8 GB" or "8192 MB"
                        if 'GB' in vram_str:
                            vram_gb = float(vram_str.split()[0])
                        elif 'MB' in vram_str:
                            vram_gb = float(vram_str.split()[0]) / 1024

            if gpu_name:
                return {
                    'detected': True,
                    'name': gpu_name,
                    'vram_gb': vram_gb
                }

    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    return {'detected': False, 'name': 'None', 'vram_gb': 0.0}


def _detect_linux_gpu_lspci() -> Dict[str, Any]:
    """Detect GPU on Linux using lspci."""
    try:
        result = subprocess.run(
            ['lspci'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )

        if result.returncode == 0 and result.stdout:
            # Look for VGA or 3D controller lines
            for line in result.stdout.split('\n'):
                if 'VGA' in line or '3D controller' in line:
                    # Extract GPU name (everything after the first colon and ID)
                    parts = line.split(':')
                    if len(parts) >= 3:
                        gpu_name = parts[2].strip()
                        return {
                            'detected': True,
                            'name': gpu_name,
                            'vram_gb': 0.0  # lspci doesn't report VRAM
                        }

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return {'detected': False, 'name': 'None', 'vram_gb': 0.0}


def format_resource_report(resources: Dict[str, Any]) -> str:
    """
    Format system resources as a human-readable report.

    Args:
        resources: Output from check_system_resources()

    Returns:
        Formatted string report
    """
    ram = resources['ram']
    cpu = resources['cpu']
    gpu = resources['gpu']
    disk = resources['disk']

    lines = [
        "=" * 60,
        "System Resource Report",
        "=" * 60,
        "",
        f"Platform: {resources['platform']}",
        "",
        "Memory (RAM):",
        f"  Total: {ram['total_gb']:.1f} GB",
        f"  Available: {ram['available_gb']:.1f} GB",
        f"  Used: {ram['percent_used']:.1f}%",
        "",
        "CPU:",
        f"  Physical Cores: {cpu['cores']}",
        f"  Average Usage: {cpu['percent_avg']:.1f}%",
        "",
        "GPU:",
        f"  Detected: {'Yes' if gpu['detected'] else 'No'}",
    ]

    if gpu['detected']:
        lines.append(f"  Name: {gpu['name']}")
        if gpu['vram_gb'] > 0:
            lines.append(f"  VRAM: {gpu['vram_gb']:.1f} GB")

    lines.extend([
        "",
        "Disk Space:",
        f"  Total: {disk['total_gb']:.1f} GB",
        f"  Free: {disk['free_gb']:.1f} GB",
        "",
        "=" * 60,
    ])

    return '\n'.join(lines)


def format_model_recommendation(
    model: str,
    reasoning: str,
    performance: Dict[str, Any],
    resources: Dict[str, Any]
) -> str:
    """
    Format model recommendation as a human-readable report.

    Args:
        model: Recommended model name
        reasoning: Reasoning for recommendation
        performance: Expected performance dict
        resources: System resources dict

    Returns:
        Formatted string report
    """
    lines = [
        "",
        "=" * 60,
        "AI Model Recommendation",
        "=" * 60,
        "",
        f"Recommended Model: {model}",
        f"Reasoning: {reasoning}",
        "",
        "Expected Performance:",
        f"  Speed: {performance['tokens_per_second']}",
        f"  Quality: {performance['quality']}",
        f"  Download Size: {performance['size_gb']} GB",
        "",
        f"Available RAM: {resources['ram']['available_gb']:.1f} GB",
        f"GPU Acceleration: {'Yes' if resources['gpu']['detected'] else 'No'}",
        "",
        "=" * 60,
    ]

    return '\n'.join(lines)
