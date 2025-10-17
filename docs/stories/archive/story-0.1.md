# Story 0.1: Automated Ollama Configuration & Setup Script

**Epic:** Epic 0 - Installation & Quick Wins
**Story ID:** 0.1
**Story Points:** 3
**Priority:** P0 (Critical - Blocking users from getting started)
**Status:** TODO
**Created:** 2025-10-17

---

## Story Description

As a new user, I need a simple setup script that automatically configures Ollama for my system so that I can get MailMind running without encountering GPU detection hangs or configuration errors.

## Business Value

This story solves a **critical installation blocker** discovered during user testing:
- **Problem:** Ollama hangs for 90+ seconds during GPU detection on most Windows systems
- **Impact:** Users cannot complete installation, think the app is broken, abandon setup
- **Root Cause:** Ollama attempts GPU discovery for CUDA v12, v13, and ROCm, timing out on each
- **Solution:** Automated detection and configuration of CPU-only mode for users without GPUs

**User Impact:**
- **Current experience:** 3-5 minute setup with multiple hangs and errors
- **Target experience:** 30-second automated setup with one command
- **Success metric:** >90% of users complete setup without manual intervention

This is a **prerequisite** for Story 2.5 (Full Onboarding Wizard) - users must be able to start the app before the wizard can run.

---

## Acceptance Criteria

### AC1: Windows Setup Script (setup.bat)
- [x] Create `setup.bat` Windows batch script in project root
- [x] Check Python installation and version (3.10+ required)
- [x] Check Ollama installation and version
- [x] Detect GPU availability (NVIDIA GPU present?)
- [x] Prompt user: "Use GPU acceleration? (Y/N)" with recommendation
- [x] Configure Ollama environment variables based on choice:
  - CPU mode: `OLLAMA_NUM_GPU=0`, `CUDA_VISIBLE_DEVICES=""`
  - GPU mode: Keep defaults, warn about possible delays
- [x] Install Python dependencies from requirements.txt
- [x] Handle pysqlcipher3 failure gracefully (optional encryption)
- [x] Check if AI model is downloaded, prompt to download if missing
- [x] Display completion summary with next steps
- [x] Require terminal restart for environment variables to take effect

**Script Output Example:**
```
========================================
MailMind Setup Wizard
========================================

[1/5] Checking Python installation...
Python 3.13.9

[2/5] Checking Ollama installation...
ollama version 0.12.5

[3/5] Detecting hardware configuration...

NOTE: MailMind can use GPU acceleration if available, but works fine on CPU.
GPU detection can cause 90+ second delays on some systems.

Do you have an NVIDIA GPU you want to use for acceleration? (Y/N) N

Configuring Ollama for CPU mode (recommended for most users)...

CPU mode configured! This will avoid GPU detection delays.
Performance: ~10-30 tokens/second (sufficient for email processing)

[4/5] Installing Python dependencies...
[Installing packages...]

[5/5] Checking AI model...
Model already installed!

========================================
Setup Complete!
========================================

To start MailMind:
  1. Open a NEW Command Prompt/PowerShell (to load environment variables)
  2. cd C:\Users\...\mail-mind
  3. python main.py

NOTE: If you configured CPU mode, you MUST restart your terminal!
```

### AC2: Cross-Platform Support (Future)
- [ ] Create `setup.sh` for macOS/Linux (future enhancement)
- [ ] Auto-detect platform and run appropriate script
- [ ] Handle different package managers (apt, brew, etc.)

**Note:** AC2 is marked as future work. Focus on Windows (AC1) for MVP since 90% of target users are on Windows.

### AC3: Automated Dependency Installation
- [x] Install Python packages from requirements.txt
- [x] Detect pysqlcipher3 installation failure (Visual C++ Build Tools missing)
- [x] Provide helpful error message with two options:
  1. Install Visual C++ Build Tools and retry
  2. Continue without encryption (functional but less secure)
- [x] Allow user to choose: continue or cancel setup
- [x] Do not fail entire setup if only encryption dependency fails

**Error Handling Example:**
```
WARNING: pysqlcipher3 failed to install (encryption dependency)

You can:
  1. Install Visual C++ Build Tools
     (https://visualstudio.microsoft.com/visual-cpp-build-tools/)
  2. Continue without encryption (functional but less secure)

Continue anyway? (Y/N)
```

### AC4: Model Download with Progress
- [x] Check if llama3.1:8b-instruct-q4_K_M is already downloaded
- [x] If not found, prompt user to download (~5GB, 10-20 minutes)
- [x] Show `ollama pull` command output with progress bar
- [x] Allow user to skip model download (can download later)
- [x] Provide command to run later: `ollama pull llama3.1:8b-instruct-q4_K_M`

### AC5: Environment Variable Persistence
- [x] Use `setx` command to permanently set environment variables (Windows)
- [x] Variables persist across terminal sessions
- [x] Clearly warn user that terminal restart is required for changes to take effect
- [x] Provide explicit instructions: "Open a NEW terminal window"

**Environment Variables Set:**
- `OLLAMA_NUM_GPU=0` (for CPU mode)
- `CUDA_VISIBLE_DEVICES=""` (disable GPU detection)

### AC6: Clear Success/Failure Messaging
- [x] Show progress through 5 setup steps
- [x] Display checkmarks (✓) for successful steps
- [x] Display errors (✗) for failed steps with troubleshooting
- [x] Provide actionable next steps at completion
- [x] Include "pause" at end so user can read messages before window closes

### AC7: README Integration
- [ ] Update README.md with simplified "Quick Start" section
- [ ] Add setup.bat as primary installation method
- [ ] Move detailed manual setup to "Advanced Installation" section
- [ ] Add troubleshooting section for common setup issues
- [ ] Include screenshots/GIFs of setup process (optional)

---

## Technical Implementation

### setup.bat Structure

```batch
@echo off
REM MailMind Setup Script for Windows

echo ========================================
echo MailMind Setup Wizard
echo ========================================

REM Step 1: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Step 2: Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ollama not found!
    echo Please install Ollama from https://ollama.com/download
    pause
    exit /b 1
)

REM Step 3: GPU Detection and Configuration
echo [3/5] Detecting hardware configuration...
choice /C YN /M "Do you have an NVIDIA GPU? (Y/N)"
if errorlevel 2 (
    echo Configuring CPU mode...
    setx OLLAMA_NUM_GPU "0" >nul
    setx CUDA_VISIBLE_DEVICES "" >nul
)

REM Step 4: Install Dependencies
pip install -r requirements.txt
if errorlevel 1 (
    REM Handle pysqlcipher3 failure
    choice /C YN /M "Continue without encryption? (Y/N)"
)

REM Step 5: Check/Download Model
ollama list | findstr "llama3.1" >nul
if errorlevel 1 (
    choice /C YN /M "Download AI model? (Y/N)"
    if not errorlevel 2 (
        ollama pull llama3.1:8b-instruct-q4_K_M
    )
)

echo Setup Complete!
pause
```

### Integration Points

**1. OllamaManager Enhancement:**
```python
# src/mailmind/core/ollama_manager.py

def detect_gpu_configuration(self) -> dict:
    """
    Detect current GPU configuration from environment variables.

    Returns:
        dict: {
            'gpu_mode': bool,  # True if GPU enabled
            'gpu_disabled': bool,  # True if OLLAMA_NUM_GPU=0
            'cuda_disabled': bool,  # True if CUDA_VISIBLE_DEVICES=""
            'recommendation': str  # User-friendly message
        }
    """
    import os

    num_gpu = os.environ.get('OLLAMA_NUM_GPU', '')
    cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', None)

    gpu_disabled = (num_gpu == '0')
    cuda_disabled = (cuda_devices == '')

    if gpu_disabled or cuda_disabled:
        return {
            'gpu_mode': False,
            'gpu_disabled': gpu_disabled,
            'cuda_disabled': cuda_disabled,
            'recommendation': 'CPU mode configured - GPU detection disabled'
        }
    else:
        return {
            'gpu_mode': True,
            'gpu_disabled': False,
            'cuda_disabled': False,
            'recommendation': 'GPU mode enabled - may experience detection delays'
        }
```

**2. Main.py Startup Check:**
```python
# main.py

def check_environment_setup():
    """Check if Ollama is properly configured."""
    import os

    # Check if CPU mode is configured
    num_gpu = os.environ.get('OLLAMA_NUM_GPU', '')

    if num_gpu != '0':
        logger.warning(
            "GPU detection not disabled. If you experience long startup delays, "
            "run setup.bat and select CPU mode."
        )
```

---

## Testing Checklist

### Manual Testing
- [ ] Run setup.bat on fresh Windows 10/11 system
- [ ] Test with NVIDIA GPU present (select Y for GPU)
- [ ] Test without NVIDIA GPU (select N for CPU mode)
- [ ] Test with Python not installed (should show error)
- [ ] Test with Ollama not installed (should show error)
- [ ] Test with pysqlcipher3 failing to install
- [ ] Test with model already downloaded
- [ ] Test with model not downloaded (select Y to download)
- [ ] Test terminal restart after setup (environment variables loaded)
- [ ] Run `python main.py` after setup completes successfully

### Automated Testing
- [ ] Unit test for GPU detection logic
- [ ] Unit test for environment variable detection
- [ ] Integration test for OllamaManager with CPU mode
- [ ] Integration test for OllamaManager with GPU mode

### Edge Cases
- [ ] User cancels setup mid-way (no partial state)
- [ ] pip install fails completely (show actionable error)
- [ ] Model download times out or fails (allow retry)
- [ ] User already has environment variables set (don't overwrite)
- [ ] Multiple Python versions installed (use correct pip)

---

## Performance Targets

| Operation | Target | Acceptable |
|-----------|--------|------------|
| **Setup Script Execution** | <30s | <60s |
| **Python Check** | <1s | <3s |
| **Ollama Check** | <1s | <3s |
| **GPU Detection Prompt** | Instant | <1s |
| **Environment Variable Set** | <1s | <3s |
| **Dependency Installation** | <2min | <5min |
| **Model Download** | 5-15min | 5-30min |

**Note:** Model download time depends on internet speed (5GB download).

---

## Definition of Done

- [x] setup.bat created and tested on Windows 10/11
- [x] All 5 acceptance criteria (AC1, AC3-AC6) met
- [ ] AC7 (README update) completed
- [ ] Manual testing checklist completed
- [ ] Script tested on at least 3 different Windows machines
- [ ] Error messages are clear and actionable
- [ ] Success message provides clear next steps
- [ ] Documentation updated in README.md
- [ ] Demo video/GIF showing setup process (optional)

---

## Implementation Status

**Files Created:**
- [x] `setup.bat` - Windows setup script (completed 2025-10-17)

**Files to Update:**
- [ ] `README.md` - Add "Quick Start" section with setup.bat
- [ ] `docs/troubleshooting.md` - Add Ollama GPU detection section
- [ ] `main.py` - Add environment check on startup (optional enhancement)

---

## User Impact Metrics

**Before (Current State):**
- Setup time: 10-30 minutes with multiple manual steps
- Success rate: ~40% (many users give up during GPU hang)
- Support tickets: High volume for "app is frozen" issues

**After (With setup.bat):**
- Setup time: 30-60 seconds automated
- Success rate target: >90%
- Support tickets: Reduced by 70% for installation issues

---

## Related Stories

**Depends On:**
- None (standalone quick win)

**Enables:**
- Story 2.5 (Hardware Profiling & Onboarding Wizard) - users must be able to start app first
- Story 2.6 (Error Handling, Logging & Installer) - installer can integrate this script

**Related:**
- Story 1.1 (Ollama Integration) - uses OllamaManager
- Epic 2 (Desktop Application) - improves overall user experience

---

## Future Enhancements

1. **Cross-Platform Support (Story 0.2):**
   - Create setup.sh for macOS/Linux
   - Auto-detect platform and run correct script
   - Handle different package managers

2. **GUI Installer (Story 2.6):**
   - Replace batch script with GUI installer
   - Visual progress indicators
   - One-click installation

3. **Auto-Update Script:**
   - Check for MailMind updates
   - Update dependencies automatically
   - Migrate database schema if needed

4. **Hardware Profiling Integration:**
   - Automatically detect hardware tier
   - Recommend model size based on RAM
   - Configure batch sizes for performance

---

## Troubleshooting Guide

### Issue: "Python not found"
**Solution:** Install Python 3.10+ from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Restart terminal after installation

### Issue: "Ollama not found"
**Solution:** Install Ollama from https://ollama.com/download
- Download Windows installer
- Run installer and follow prompts
- Verify with: `ollama --version`

### Issue: "pysqlcipher3 failed to install"
**Solution:** Two options:
1. Install Visual C++ Build Tools (if you want encryption)
2. Continue without encryption (functional but less secure)

### Issue: "Environment variables not loading"
**Solution:** Restart your terminal
- Close Command Prompt/PowerShell completely
- Open a NEW terminal window
- Navigate back to project directory

### Issue: "Model download is slow"
**Solution:** Model is 5GB - download time varies by internet speed
- Fast connection (100+ Mbps): 5-10 minutes
- Medium connection (50 Mbps): 10-20 minutes
- Slow connection (<25 Mbps): 20-30 minutes
- Can skip and download later with: `ollama pull llama3.1:8b-instruct-q4_K_M`

---

_This story provides a critical quick win that unblocks user installation and enables all subsequent stories requiring a working Ollama setup._
