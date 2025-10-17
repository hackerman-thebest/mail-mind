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
import re
import yaml
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from colorama import Fore, Style, init

# Initialize colorama for Windows compatibility
init()

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mailmind.utils.config import load_config, get_ollama_config
from mailmind.core.ollama_manager import OllamaManager, OllamaConnectionError, OllamaModelError
from mailmind.utils.system_diagnostics import check_system_resources

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
        logger.error("❌ Some diagnostics failed.")
        logger.error("   Let's try to fix this automatically...")
        logger.info("=" * 60)
        logger.info("")

        # Story 0.4: Offer automated remediation menu
        resolved = offer_remediations()
        if resolved:
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ Issue resolved! Ollama should now work correctly.")
            logger.info("=" * 60)
            logger.info("")
            return True
        else:
            logger.info("")
            logger.info("=" * 60)
            logger.error("❌ Could not automatically resolve the issue.")
            logger.error("   Please see TROUBLESHOOTING_OLLAMA.md for manual steps.")
            logger.info("=" * 60)
            logger.info("")
            return False

    logger.info("=" * 60)
    logger.info("")

    return all_passed


def show_system_resources() -> None:
    """
    Option 3: Display system resources with bottleneck highlighting.

    Reuses check_system_resources() from Story 0.1 and adds color-coded
    bottleneck warnings (RAM >90%, low disk space, etc.).
    """
    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}🔍 System Resource Report{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")

    try:
        resources = check_system_resources()

        # RAM Section
        ram = resources.get('ram', {})
        ram_total = ram.get('total_gb', 0)
        ram_available = ram.get('available_gb', 0)
        ram_used = ram_total - ram_available
        ram_percent = (ram_used / ram_total * 100) if ram_total > 0 else 0

        print(f"{Fore.CYAN}💾 RAM:{Style.RESET_ALL}")
        print(f"  Total: {ram_total:.1f} GB")
        print(f"  Used: {ram_used:.1f} GB ({ram_percent:.1f}%)")
        print(f"  Available: {ram_available:.1f} GB")

        if ram_percent > 90:
            print(f"  {Fore.RED}⚠️  WARNING: RAM usage >90%{Style.RESET_ALL}")
        elif ram_percent > 75:
            print(f"  {Fore.YELLOW}⚠️  WARNING: RAM usage >75%{Style.RESET_ALL}")
        else:
            print(f"  {Fore.GREEN}✓ RAM usage healthy{Style.RESET_ALL}")

        # CPU Section
        cpu = resources.get('cpu', {})
        cpu_cores = cpu.get('physical_cores', 0)
        cpu_usage = cpu.get('usage_percent', 0)

        print(f"\n{Fore.CYAN}🖥️  CPU:{Style.RESET_ALL}")
        print(f"  Cores: {cpu_cores}")
        print(f"  Current Usage: {cpu_usage:.1f}%")

        if cpu_usage > 90:
            print(f"  {Fore.RED}⚠️  WARNING: CPU usage >90%{Style.RESET_ALL}")
        elif cpu_usage > 75:
            print(f"  {Fore.YELLOW}⚠️  WARNING: CPU usage >75%{Style.RESET_ALL}")
        else:
            print(f"  {Fore.GREEN}✓ CPU usage healthy{Style.RESET_ALL}")

        # GPU Section
        gpu = resources.get('gpu', {})
        gpu_available = gpu.get('available', False)
        gpu_name = gpu.get('name', 'Not detected')

        print(f"\n{Fore.CYAN}🎮 GPU:{Style.RESET_ALL}")
        if gpu_available:
            print(f"  Status: {Fore.GREEN}Detected{Style.RESET_ALL}")
            print(f"  Name: {gpu_name}")
            if 'vram_gb' in gpu:
                print(f"  VRAM: {gpu['vram_gb']} GB")
        else:
            print(f"  Status: {Fore.YELLOW}Not detected (CPU-only mode){Style.RESET_ALL}")

        # Disk Section
        disk = resources.get('disk', {})
        disk_total = disk.get('total_gb', 0)
        disk_free = disk.get('free_gb', 0)
        disk_percent = ((disk_total - disk_free) / disk_total * 100) if disk_total > 0 else 0

        print(f"\n{Fore.CYAN}💿 Disk:{Style.RESET_ALL}")
        print(f"  Total: {disk_total:.1f} GB")
        print(f"  Free: {disk_free:.1f} GB")
        print(f"  Used: {disk_percent:.1f}%")

        if disk_free < 5:
            print(f"  {Fore.RED}⚠️  WARNING: Low disk space (<5GB free){Style.RESET_ALL}")
        elif disk_free < 20:
            print(f"  {Fore.YELLOW}⚠️  WARNING: Disk space running low (<20GB free){Style.RESET_ALL}")
        else:
            print(f"  {Fore.GREEN}✓ Disk space healthy{Style.RESET_ALL}")

        # Recommendations
        print(f"\n{Fore.CYAN}💡 Recommendations:{Style.RESET_ALL}")
        if ram_percent > 75:
            print(f"  • Close memory-intensive applications (Chrome, Outlook, etc.)")
            print(f"  • Consider switching to a smaller model (llama3.2:3b or 1b)")
        if disk_free < 20:
            print(f"  • Free up disk space to ensure model downloads work")
        if not gpu_available:
            print(f"  • Using CPU-only mode - inference will be slower")
            print(f"  • Consider a smaller model for better performance")

        if ram_percent <= 75 and disk_free >= 20:
            print(f"  {Fore.GREEN}✓ System resources look good!{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}✗ Failed to check system resources: {e}{Style.RESET_ALL}")

    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")


def show_ollama_logs() -> None:
    """
    Option 4: Show last 50 lines of Ollama logs with error highlighting.

    Auto-detects platform-specific log location and highlights
    ERROR/WARNING lines in red.
    """
    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}📋 Ollama Logs (Last 50 Lines){Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")

    # Detect platform-specific log location
    system = platform.system()
    log_paths = {
        'Windows': Path(os.getenv('LOCALAPPDATA', '')) / 'Ollama' / 'logs' / 'server.log',
        'Darwin': Path.home() / '.ollama' / 'logs' / 'server.log',
        'Linux': Path.home() / '.ollama' / 'logs' / 'server.log'
    }

    log_path = log_paths.get(system)

    if not log_path:
        print(f"{Fore.YELLOW}⚠️  Unknown platform: {system}{Style.RESET_ALL}")
        print(f"Please manually check Ollama logs.")
        return

    if not log_path.exists():
        print(f"{Fore.YELLOW}⚠️  Log file not found: {log_path}{Style.RESET_ALL}")
        print(f"\nPossible reasons:")
        print(f"  • Ollama hasn't been run yet")
        print(f"  • Logs are in a different location")
        print(f"  • Ollama is not installed")
        return

    try:
        # Read last 50 lines
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines

        print(f"Log file: {log_path}")
        print(f"Total lines: {len(lines)}\n")
        print(f"{Fore.CYAN}Last 50 lines:{Style.RESET_ALL}")
        print("-" * 60)

        error_count = 0
        warning_count = 0

        for line in last_lines:
            line = line.rstrip()
            # Highlight errors and warnings
            if 'ERROR' in line.upper() or 'FATAL' in line.upper():
                print(f"{Fore.RED}{line}{Style.RESET_ALL}")
                error_count += 1
            elif 'WARN' in line.upper():
                print(f"{Fore.YELLOW}{line}{Style.RESET_ALL}")
                warning_count += 1
            else:
                print(line)

        print("-" * 60)
        print(f"\nSummary:")
        if error_count > 0:
            print(f"  {Fore.RED}✗ Errors found: {error_count}{Style.RESET_ALL}")
        if warning_count > 0:
            print(f"  {Fore.YELLOW}⚠️  Warnings found: {warning_count}{Style.RESET_ALL}")
        if error_count == 0 and warning_count == 0:
            print(f"  {Fore.GREEN}✓ No errors or warnings in recent logs{Style.RESET_ALL}")

        # Offer to save full logs
        save = input(f"\n{Fore.CYAN}Save full logs to file? (y/n): {Style.RESET_ALL}").strip().lower()
        if save == 'y':
            output_path = f"ollama_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"{Fore.GREEN}✓ Full logs saved to: {output_path}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}✗ Failed to read log file: {e}{Style.RESET_ALL}")

    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")


def generate_support_report() -> str:
    """
    Option 5: Generate comprehensive support report with sanitized data.

    Collects system resources, Ollama version, model list, logs, and
    diagnostics. Sanitizes sensitive data (paths, emails, API keys).

    Returns:
        str: Path to saved support report file
    """
    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}📊 Generating Support Report...{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("MAILMIND SUPPORT REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 60)
    report_lines.append("")

    # Section 1: System Resources
    print(f"{Fore.CYAN}Collecting system resources...{Style.RESET_ALL}")
    report_lines.append("1. SYSTEM RESOURCES")
    report_lines.append("-" * 60)
    try:
        resources = check_system_resources()

        ram = resources.get('ram', {})
        report_lines.append(f"RAM Total: {ram.get('total_gb', 0):.1f} GB")
        report_lines.append(f"RAM Available: {ram.get('available_gb', 0):.1f} GB")

        cpu = resources.get('cpu', {})
        report_lines.append(f"CPU Cores: {cpu.get('physical_cores', 0)}")
        report_lines.append(f"CPU Usage: {cpu.get('usage_percent', 0):.1f}%")

        gpu = resources.get('gpu', {})
        report_lines.append(f"GPU Available: {gpu.get('available', False)}")
        if gpu.get('available'):
            report_lines.append(f"GPU Name: {gpu.get('name', 'Unknown')}")

        disk = resources.get('disk', {})
        report_lines.append(f"Disk Total: {disk.get('total_gb', 0):.1f} GB")
        report_lines.append(f"Disk Free: {disk.get('free_gb', 0):.1f} GB")

        report_lines.append(f"Platform: {resources.get('platform', 'Unknown')}")
    except Exception as e:
        report_lines.append(f"ERROR: Failed to collect system resources: {e}")
    report_lines.append("")

    # Section 2: Ollama Version
    print(f"{Fore.CYAN}Collecting Ollama version...{Style.RESET_ALL}")
    report_lines.append("2. OLLAMA VERSION")
    report_lines.append("-" * 60)
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        if result.returncode == 0:
            report_lines.append(result.stdout.strip())
        else:
            report_lines.append("ERROR: Could not get Ollama version")
    except Exception as e:
        report_lines.append(f"ERROR: {e}")
    report_lines.append("")

    # Section 3: Model List
    print(f"{Fore.CYAN}Collecting model list...{Style.RESET_ALL}")
    report_lines.append("3. INSTALLED MODELS")
    report_lines.append("-" * 60)
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
            report_lines.append(result.stdout.strip())
        else:
            report_lines.append("ERROR: Could not list models")
    except Exception as e:
        report_lines.append(f"ERROR: {e}")
    report_lines.append("")

    # Section 4: Recent Logs
    print(f"{Fore.CYAN}Collecting Ollama logs...{Style.RESET_ALL}")
    report_lines.append("4. OLLAMA LOGS (Last 100 lines)")
    report_lines.append("-" * 60)
    try:
        system = platform.system()
        log_paths = {
            'Windows': Path(os.getenv('LOCALAPPDATA', '')) / 'Ollama' / 'logs' / 'server.log',
            'Darwin': Path.home() / '.ollama' / 'logs' / 'server.log',
            'Linux': Path.home() / '.ollama' / 'logs' / 'server.log'
        }
        log_path = log_paths.get(system)

        if log_path and log_path.exists():
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                last_lines = lines[-100:] if len(lines) > 100 else lines
                report_lines.extend([line.rstrip() for line in last_lines])
        else:
            report_lines.append(f"Log file not found: {log_path}")
    except Exception as e:
        report_lines.append(f"ERROR: {e}")
    report_lines.append("")

    # Section 5: Configuration
    print(f"{Fore.CYAN}Collecting configuration...{Style.RESET_ALL}")
    report_lines.append("5. CONFIGURATION")
    report_lines.append("-" * 60)
    try:
        config_dir = Path(__file__).parent / "config"
        user_config = config_dir / "user_config.yaml"

        if user_config.exists():
            with open(user_config, 'r') as f:
                config_content = f.read()
            report_lines.append("User Config (user_config.yaml):")
            report_lines.append(config_content)
        else:
            report_lines.append("No user_config.yaml found")
    except Exception as e:
        report_lines.append(f"ERROR: {e}")
    report_lines.append("")

    # Sanitize sensitive data
    print(f"{Fore.CYAN}Sanitizing sensitive data...{Style.RESET_ALL}")
    report_text = '\n'.join(report_lines)
    report_text = _sanitize_report(report_text)

    # Save to file
    filename = f"support_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"{Fore.GREEN}✓ Support report generated: {filename}{Style.RESET_ALL}")
        print(f"\nYou can share this file with support for troubleshooting.")
        print(f"The report has been sanitized to remove sensitive information.")

        # Offer clipboard copy (if possible)
        try:
            copy = input(f"\n{Fore.CYAN}Display file path for copying? (y/n): {Style.RESET_ALL}").strip().lower()
            if copy == 'y':
                full_path = Path(filename).absolute()
                print(f"\nFull path: {full_path}")
        except:
            pass

        return filename
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to save support report: {e}{Style.RESET_ALL}")
        return ""


def _sanitize_report(text: str) -> str:
    """
    Remove sensitive data from support report.

    Sanitizes:
    - User paths (replace with <user_home>)
    - Email addresses (replace with <email>)
    - API keys (long hex strings, replace with <redacted>)
    - Potential passwords

    Args:
        text: Report text to sanitize

    Returns:
        str: Sanitized report text
    """
    # Replace user home directory
    home = str(Path.home())
    text = text.replace(home, '<user_home>')
    text = text.replace(home.replace('\\', '/'), '<user_home>')

    # Replace email patterns
    text = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '<email>', text)

    # Replace potential API keys (long hex strings)
    text = re.sub(r'\b[0-9a-fA-F]{32,}\b', '<redacted>', text)

    # Replace potential tokens
    text = re.sub(r'(token|key|password|secret)[\s:=]+\S+', r'\1: <redacted>', text, flags=re.IGNORECASE)

    return text


def switch_to_smaller_model() -> bool:
    """
    Option 1: Switch to a smaller model to reduce resource usage.

    Detects current model, recommends next smaller size (8B→3B→1B),
    downloads it, updates config, and reruns inference test.

    Returns:
        bool: True if switch succeeded and test passed, False otherwise
    """
    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}🔧 Switch to Smaller Model{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")

    # Model fallback chain
    fallback_chain = {
        'llama3.1:8b-instruct-q4_K_M': 'llama3.2:3b',
        'llama3.2:3b': 'llama3.2:1b',
        'llama3.2:1b': None  # No smaller model available
    }

    try:
        # Load current config to detect current model
        config = load_config()
        ollama_config = get_ollama_config(config)
        current_model = ollama_config.get('primary_model', 'llama3.1:8b-instruct-q4_K_M')

        print(f"Current model: {Fore.CYAN}{current_model}{Style.RESET_ALL}")

        # Find next smaller model
        next_model = fallback_chain.get(current_model)

        if next_model is None:
            print(f"{Fore.YELLOW}⚠️  Already using the smallest model (llama3.2:1b){Style.RESET_ALL}")
            print(f"Cannot switch to a smaller model.")
            print(f"\nOther options:")
            print(f"  • Try Option 2 (Re-download model) if model is corrupted")
            print(f"  • Try Option 3 (Check system resources) to find bottlenecks")
            print(f"  • Close other applications to free up RAM")
            return False

        print(f"Recommended smaller model: {Fore.GREEN}{next_model}{Style.RESET_ALL}")
        print(f"\nThis smaller model will:")
        print(f"  • Use less RAM")
        print(f"  • Run faster on your system")
        print(f"  • Still provide good performance")

        # Confirm with user
        confirm = input(f"\n{Fore.CYAN}Download and switch to {next_model}? (y/n): {Style.RESET_ALL}").strip().lower()
        if confirm != 'y':
            print(f"{Fore.YELLOW}Operation cancelled{Style.RESET_ALL}")
            return False

        # Download the model
        print(f"\n{Fore.CYAN}Downloading {next_model}...{Style.RESET_ALL}")
        print(f"This may take a few minutes depending on your internet connection.\n")

        result = subprocess.run(
            ['ollama', 'pull', next_model],
            encoding='utf-8',
            errors='replace',
            timeout=600  # 10 minute timeout for download
        )

        if result.returncode != 0:
            print(f"{Fore.RED}✗ Failed to download model{Style.RESET_ALL}")
            return False

        print(f"{Fore.GREEN}✓ Model downloaded successfully{Style.RESET_ALL}")

        # Update config/user_config.yaml
        print(f"\n{Fore.CYAN}Updating configuration...{Style.RESET_ALL}")
        config_dir = Path(__file__).parent / "config"
        user_config_path = config_dir / "user_config.yaml"

        user_config = {}
        if user_config_path.exists():
            with open(user_config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}

        if 'ollama' not in user_config:
            user_config['ollama'] = {}

        user_config['ollama']['selected_model'] = next_model

        # Determine model size for tracking
        if '8b' in next_model.lower():
            user_config['ollama']['model_size'] = 'large'
        elif '3b' in next_model.lower():
            user_config['ollama']['model_size'] = 'medium'
        else:
            user_config['ollama']['model_size'] = 'small'

        with open(user_config_path, 'w') as f:
            yaml.dump(user_config, f, default_flow_style=False)

        print(f"{Fore.GREEN}✓ Configuration updated{Style.RESET_ALL}")

        # Rerun inference test
        print(f"\n{Fore.CYAN}Testing new model...{Style.RESET_ALL}")
        result = subprocess.run(
            ['ollama', 'run', next_model],
            input='Test',
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=45
        )

        if result.returncode == 0 and result.stdout:
            print(f"{Fore.GREEN}✓ Model test passed! New model is working correctly.{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗ Model test failed{Style.RESET_ALL}")
            print(f"The smaller model may still have issues.")
            return False

    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}✗ Operation timed out{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        return False


def repull_current_model() -> bool:
    """
    Option 2: Re-download current model to fix corruption.

    Removes and re-downloads the current model, then reruns inference test.
    Prompts for confirmation before destructive operation.

    Returns:
        bool: True if re-download succeeded and test passed, False otherwise
    """
    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}🔄 Re-download Current Model{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")

    try:
        # Load current config to detect current model
        config = load_config()
        ollama_config = get_ollama_config(config)
        current_model = ollama_config.get('primary_model', 'llama3.1:8b-instruct-q4_K_M')

        print(f"Current model: {Fore.CYAN}{current_model}{Style.RESET_ALL}")
        print(f"\nThis will:")
        print(f"  1. Remove the current model from your system")
        print(f"  2. Download it again fresh")
        print(f"  3. Test the new download")

        # Confirm with user (destructive operation)
        confirm = input(f"\n{Fore.YELLOW}⚠️  This will remove and re-download the model. Continue? (y/n): {Style.RESET_ALL}").strip().lower()
        if confirm != 'y':
            print(f"{Fore.YELLOW}Operation cancelled{Style.RESET_ALL}")
            return False

        # Remove the model
        print(f"\n{Fore.CYAN}Removing {current_model}...{Style.RESET_ALL}")
        result = subprocess.run(
            ['ollama', 'rm', current_model],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )

        if result.returncode != 0:
            print(f"{Fore.YELLOW}⚠️  Model removal had issues (may not have been installed){Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✓ Model removed{Style.RESET_ALL}")

        # Download the model fresh
        print(f"\n{Fore.CYAN}Downloading {current_model}...{Style.RESET_ALL}")
        print(f"This may take a few minutes depending on your internet connection.\n")

        result = subprocess.run(
            ['ollama', 'pull', current_model],
            encoding='utf-8',
            errors='replace',
            timeout=600  # 10 minute timeout for download
        )

        if result.returncode != 0:
            print(f"{Fore.RED}✗ Failed to download model{Style.RESET_ALL}")
            print(f"Check your internet connection and try again.")
            return False

        print(f"{Fore.GREEN}✓ Model downloaded successfully{Style.RESET_ALL}")

        # Rerun inference test
        print(f"\n{Fore.CYAN}Testing model...{Style.RESET_ALL}")
        result = subprocess.run(
            ['ollama', 'run', current_model],
            input='Test',
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=45
        )

        if result.returncode == 0 and result.stdout:
            print(f"{Fore.GREEN}✓ Model test passed! Re-download fixed the issue.{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗ Model test failed{Style.RESET_ALL}")
            print(f"The issue may not be model corruption.")
            print(f"Try Option 3 (System Resources) to check for other issues.")
            return False

    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}✗ Operation timed out{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        return False


def offer_remediations(diagnostic_results: Optional[Dict[str, Any]] = None) -> bool:
    """
    Main remediation menu controller.

    Displays interactive menu with 6 remediation options, accepts user input,
    executes selected option, and loops until issue is resolved or user exits.

    Args:
        diagnostic_results: Results from run_ollama_diagnostics() (optional)

    Returns:
        bool: True if issue was resolved, False otherwise
    """
    print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}🔧 Automated Remediation Menu{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")

    print(f"Let's try to fix the issue automatically. Choose an option:\n")

    while True:
        # Display menu
        print(f"{Fore.CYAN}Available Options:{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}1{Style.RESET_ALL} - Switch to Smaller Model (reduce RAM usage)")
        print(f"  {Fore.GREEN}2{Style.RESET_ALL} - Re-download Current Model (fix corruption)")
        print(f"  {Fore.GREEN}3{Style.RESET_ALL} - Show System Resources (check bottlenecks)")
        print(f"  {Fore.GREEN}4{Style.RESET_ALL} - Show Ollama Logs (view errors)")
        print(f"  {Fore.GREEN}5{Style.RESET_ALL} - Generate Support Report (for manual help)")
        print(f"  {Fore.GREEN}6{Style.RESET_ALL} - Exit (manual troubleshooting)")
        print()

        # Get user input
        try:
            choice = input(f"{Fore.CYAN}Select option (1-6): {Style.RESET_ALL}").strip()

            if not choice.isdigit() or int(choice) not in range(1, 7):
                print(f"{Fore.RED}✗ Invalid choice. Please enter a number between 1 and 6.{Style.RESET_ALL}\n")
                continue

            choice = int(choice)

            # Execute selected option
            if choice == 1:
                success = switch_to_smaller_model()
                if success:
                    print(f"\n{Fore.GREEN}✓ Issue resolved! Exiting remediation menu.{Style.RESET_ALL}")
                    return True
                else:
                    print(f"\n{Fore.YELLOW}⚠️  Returning to menu. Try another option?{Style.RESET_ALL}\n")

            elif choice == 2:
                success = repull_current_model()
                if success:
                    print(f"\n{Fore.GREEN}✓ Issue resolved! Exiting remediation menu.{Style.RESET_ALL}")
                    return True
                else:
                    print(f"\n{Fore.YELLOW}⚠️  Returning to menu. Try another option?{Style.RESET_ALL}\n")

            elif choice == 3:
                show_system_resources()
                print(f"{Fore.YELLOW}Returning to menu...{Style.RESET_ALL}\n")

            elif choice == 4:
                show_ollama_logs()
                print(f"{Fore.YELLOW}Returning to menu...{Style.RESET_ALL}\n")

            elif choice == 5:
                report_path = generate_support_report()
                if report_path:
                    print(f"\n{Fore.GREEN}✓ Support report saved: {report_path}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Returning to menu...{Style.RESET_ALL}\n")

            elif choice == 6:
                # Exit option
                print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}📖 Manual Troubleshooting{Style.RESET_ALL}")
                print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")
                print(f"For manual troubleshooting, please see:")
                print(f"  {Fore.CYAN}TROUBLESHOOTING_OLLAMA.md{Style.RESET_ALL}")
                print(f"\nYou can also:")
                print(f"  • Visit Ollama documentation: https://ollama.com/docs")
                print(f"  • Check Ollama GitHub issues: https://github.com/ollama/ollama/issues")
                print(f"  • Contact MailMind support with your support report (Option 5)")
                print(f"\nExiting remediation menu.")
                print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")
                return False

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}\n")
            continue


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
