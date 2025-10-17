"""
Unit tests for system resource detection and model recommendation.

Tests Story 0.1: System Resource Detection & Model Recommendation
"""

import pytest
from unittest.mock import patch, MagicMock
from mailmind.utils.system_diagnostics import (
    check_system_resources,
    recommend_model,
    format_resource_report,
    format_model_recommendation,
    _detect_gpu,
    _detect_nvidia_gpu,
    _detect_windows_gpu_wmic,
    _detect_macos_gpu,
    _detect_linux_gpu_lspci
)


class TestCheckSystemResources:
    """Test system resource detection."""

    @patch('mailmind.utils.system_diagnostics.psutil')
    @patch('mailmind.utils.system_diagnostics.platform')
    @patch('mailmind.utils.system_diagnostics._detect_gpu')
    def test_check_system_resources_basic(self, mock_gpu, mock_platform, mock_psutil):
        """Test basic resource detection."""
        # Mock RAM
        mock_ram = MagicMock()
        mock_ram.total = 16 * (1024**3)  # 16GB
        mock_ram.available = 8 * (1024**3)  # 8GB
        mock_ram.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_ram

        # Mock CPU
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_percent.return_value = 25.0

        # Mock disk
        mock_disk = MagicMock()
        mock_disk.total = 500 * (1024**3)  # 500GB
        mock_disk.free = 100 * (1024**3)  # 100GB
        mock_psutil.disk_usage.return_value = mock_disk

        # Mock GPU
        mock_gpu.return_value = {'detected': True, 'name': 'NVIDIA RTX 3080', 'vram_gb': 10.0}

        # Mock platform
        mock_platform.system.return_value = 'Windows'

        resources = check_system_resources()

        assert resources['ram']['total_gb'] == pytest.approx(16.0, rel=0.01)
        assert resources['ram']['available_gb'] == pytest.approx(8.0, rel=0.01)
        assert resources['ram']['percent_used'] == 50.0
        assert resources['cpu']['cores'] == 4
        assert resources['cpu']['percent_avg'] == 25.0
        assert resources['gpu']['detected'] is True
        assert resources['gpu']['name'] == 'NVIDIA RTX 3080'
        assert resources['disk']['total_gb'] == pytest.approx(500.0, rel=0.01)
        assert resources['disk']['free_gb'] == pytest.approx(100.0, rel=0.01)
        assert resources['platform'] == 'Windows'


class TestRecommendModel:
    """Test model recommendation logic."""

    def test_recommend_8b_model_high_ram_no_gpu(self):
        """Test 8B model recommended for 16GB+ RAM without GPU."""
        resources = {
            'ram': {'total_gb': 16.0, 'available_gb': 12.0, 'percent_used': 25.0},
            'cpu': {'cores': 8, 'percent_avg': 20.0},
            'gpu': {'detected': False, 'name': 'None', 'vram_gb': 0.0},
            'disk': {'total_gb': 500.0, 'free_gb': 100.0},
            'platform': 'Windows'
        }

        model, reasoning, performance = recommend_model(resources)

        assert model == 'llama3.1:8b-instruct-q4_K_M'
        assert 'sufficient RAM' in reasoning
        assert performance['quality'] == 'Best'
        assert performance['size_gb'] == 5
        assert performance['tokens_per_second'] == '1-3 t/s'  # No GPU

    def test_recommend_8b_model_high_ram_with_gpu(self):
        """Test 8B model recommended for 16GB+ RAM with GPU."""
        resources = {
            'ram': {'total_gb': 16.0, 'available_gb': 12.0, 'percent_used': 25.0},
            'cpu': {'cores': 8, 'percent_avg': 20.0},
            'gpu': {'detected': True, 'name': 'NVIDIA RTX 3080', 'vram_gb': 10.0},
            'disk': {'total_gb': 500.0, 'free_gb': 100.0},
            'platform': 'Windows'
        }

        model, reasoning, performance = recommend_model(resources)

        assert model == 'llama3.1:8b-instruct-q4_K_M'
        assert performance['tokens_per_second'] == '10-30 t/s'  # With GPU

    def test_recommend_3b_model_medium_ram(self):
        """Test 3B model recommended for 8GB RAM."""
        resources = {
            'ram': {'total_gb': 8.0, 'available_gb': 6.5, 'percent_used': 18.0},
            'cpu': {'cores': 4, 'percent_avg': 30.0},
            'gpu': {'detected': False, 'name': 'None', 'vram_gb': 0.0},
            'disk': {'total_gb': 250.0, 'free_gb': 50.0},
            'platform': 'Windows'
        }

        model, reasoning, performance = recommend_model(resources)

        assert model == 'llama3.2:3b'
        assert 'Balanced' in reasoning
        assert performance['quality'] == 'Good'
        assert performance['size_gb'] == 2
        assert performance['tokens_per_second'] == '3-8 t/s'

    def test_recommend_1b_model_low_ram(self):
        """Test 1B model recommended for 4GB RAM."""
        resources = {
            'ram': {'total_gb': 4.0, 'available_gb': 3.0, 'percent_used': 25.0},
            'cpu': {'cores': 2, 'percent_avg': 40.0},
            'gpu': {'detected': False, 'name': 'None', 'vram_gb': 0.0},
            'disk': {'total_gb': 128.0, 'free_gb': 30.0},
            'platform': 'Windows'
        }

        model, reasoning, performance = recommend_model(resources)

        assert model == 'llama3.2:1b'
        assert 'Lightweight' in reasoning
        assert performance['quality'] == 'Basic'
        assert performance['size_gb'] == 1
        assert performance['tokens_per_second'] == '5-10 t/s'

    def test_recommend_boundary_10gb_ram(self):
        """Test boundary condition at exactly 10GB RAM."""
        resources = {
            'ram': {'total_gb': 12.0, 'available_gb': 10.0, 'percent_used': 16.0},
            'cpu': {'cores': 4, 'percent_avg': 25.0},
            'gpu': {'detected': False, 'name': 'None', 'vram_gb': 0.0},
            'disk': {'total_gb': 256.0, 'free_gb': 50.0},
            'platform': 'Linux'
        }

        model, reasoning, performance = recommend_model(resources)

        assert model == 'llama3.1:8b-instruct-q4_K_M'

    def test_recommend_boundary_6gb_ram(self):
        """Test boundary condition at exactly 6GB RAM."""
        resources = {
            'ram': {'total_gb': 8.0, 'available_gb': 6.0, 'percent_used': 25.0},
            'cpu': {'cores': 4, 'percent_avg': 25.0},
            'gpu': {'detected': False, 'name': 'None', 'vram_gb': 0.0},
            'disk': {'total_gb': 256.0, 'free_gb': 50.0},
            'platform': 'Darwin'
        }

        model, reasoning, performance = recommend_model(resources)

        assert model == 'llama3.2:3b'

    def test_recommend_boundary_below_6gb_ram(self):
        """Test boundary condition just below 6GB RAM."""
        resources = {
            'ram': {'total_gb': 8.0, 'available_gb': 5.9, 'percent_used': 26.0},
            'cpu': {'cores': 4, 'percent_avg': 25.0},
            'gpu': {'detected': False, 'name': 'None', 'vram_gb': 0.0},
            'disk': {'total_gb': 256.0, 'free_gb': 50.0},
            'platform': 'Windows'
        }

        model, reasoning, performance = recommend_model(resources)

        assert model == 'llama3.2:1b'


class TestGPUDetection:
    """Test GPU detection functions."""

    @patch('mailmind.utils.system_diagnostics.subprocess.run')
    def test_detect_nvidia_gpu_success(self, mock_run):
        """Test successful NVIDIA GPU detection."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NVIDIA GeForce RTX 3080, 10240\n"
        mock_run.return_value = mock_result

        gpu_info = _detect_nvidia_gpu()

        assert gpu_info['detected'] is True
        assert gpu_info['name'] == 'NVIDIA GeForce RTX 3080'
        assert gpu_info['vram_gb'] == pytest.approx(10.0, rel=0.01)

    @patch('mailmind.utils.system_diagnostics.subprocess.run')
    def test_detect_nvidia_gpu_not_found(self, mock_run):
        """Test NVIDIA GPU not found."""
        mock_run.side_effect = FileNotFoundError()

        gpu_info = _detect_nvidia_gpu()

        assert gpu_info['detected'] is False
        assert gpu_info['name'] == 'None'
        assert gpu_info['vram_gb'] == 0.0

    @patch('mailmind.utils.system_diagnostics.subprocess.run')
    def test_detect_windows_gpu_wmic_success(self, mock_run):
        """Test successful Windows GPU detection via wmic."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Name  \nIntel UHD Graphics 630\n"
        mock_run.return_value = mock_result

        gpu_info = _detect_windows_gpu_wmic()

        assert gpu_info['detected'] is True
        assert gpu_info['name'] == 'Intel UHD Graphics 630'

    @patch('mailmind.utils.system_diagnostics.subprocess.run')
    def test_detect_macos_gpu_success(self, mock_run):
        """Test successful macOS GPU detection."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """Graphics/Displays:

    Apple M1:

      Chipset Model: Apple M1
      Type: GPU
      Bus: Built-In
      Total Number of Cores: 8
      Vendor: Apple (0x106b)
      Metal Support: Metal 3
"""
        mock_run.return_value = mock_result

        gpu_info = _detect_macos_gpu()

        assert gpu_info['detected'] is True
        assert gpu_info['name'] == 'Apple M1'

    @patch('mailmind.utils.system_diagnostics.subprocess.run')
    def test_detect_linux_gpu_lspci_success(self, mock_run):
        """Test successful Linux GPU detection via lspci."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "00:02.0 VGA compatible controller: Intel Corporation Device 9a49 (rev 01)\n"
        mock_run.return_value = mock_result

        gpu_info = _detect_linux_gpu_lspci()

        assert gpu_info['detected'] is True
        assert 'Intel Corporation' in gpu_info['name']


class TestFormatting:
    """Test formatting functions."""

    def test_format_resource_report(self):
        """Test resource report formatting."""
        resources = {
            'ram': {'total_gb': 16.0, 'available_gb': 8.0, 'percent_used': 50.0},
            'cpu': {'cores': 8, 'percent_avg': 25.0},
            'gpu': {'detected': True, 'name': 'NVIDIA RTX 3080', 'vram_gb': 10.0},
            'disk': {'total_gb': 500.0, 'free_gb': 100.0},
            'platform': 'Windows'
        }

        report = format_resource_report(resources)

        assert 'System Resource Report' in report
        assert '16.0 GB' in report
        assert '8.0 GB' in report
        assert 'NVIDIA RTX 3080' in report
        assert 'Windows' in report

    def test_format_model_recommendation(self):
        """Test model recommendation formatting."""
        resources = {
            'ram': {'total_gb': 16.0, 'available_gb': 12.0, 'percent_used': 25.0},
            'gpu': {'detected': True, 'name': 'NVIDIA RTX 3080', 'vram_gb': 10.0}
        }

        model = 'llama3.1:8b-instruct-q4_K_M'
        reasoning = 'Your system has sufficient RAM'
        performance = {
            'tokens_per_second': '10-30 t/s',
            'quality': 'Best',
            'size_gb': 5
        }

        report = format_model_recommendation(model, reasoning, performance, resources)

        assert 'AI Model Recommendation' in report
        assert model in report
        assert reasoning in report
        assert '10-30 t/s' in report
        assert 'Best' in report
        assert '5 GB' in report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
