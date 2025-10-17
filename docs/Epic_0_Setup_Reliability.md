# Epic 0: Setup & Reliability

**Epic Owner:** Dawson
**Created:** 2025-10-17
**Priority:** P0 (Blocks all other work)
**Status:** IN PROGRESS
**Target Completion:** Week 0-1 (Before main epics begin)

---

## Epic Goal

Build a bulletproof installation and diagnostic system that automatically detects system resources, selects appropriate AI models, and provides automated troubleshooting for common issues - ensuring 90%+ of users can successfully set up MailMind without manual intervention.

## Business Value

**Critical Blocker Discovered:** Real-world testing revealed installation failures that prevent users from ever reaching the actual product:
- **45-second timeout errors** on resource-constrained systems (client's 8GB RAM machine)
- **Unicode decode errors** causing diagnostic crashes on Windows
- **No resource-aware model selection** - assumes all users can run 8B model
- **Manual troubleshooting required** - poor UX for non-technical users

**Impact if not fixed:**
- 50-70% of users will fail during setup and abandon the product
- High support burden from installation issues
- Negative reviews: "doesn't work," "crashes during setup"
- Unable to scale to broader market (need 16GB+ RAM is too limiting)

**Value proposition:**
- **Automated installation** that "just works" on 4GB+ RAM systems
- **Intelligent model selection** based on detected hardware
- **Self-healing diagnostics** that fix 80% of issues automatically
- **Professional UX** from first contact with product

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Setup Success Rate | >90% | Users complete setup without errors |
| Model Selection Accuracy | >95% | Recommended model works on user's system |
| Diagnostic Auto-Fix Rate | >80% | Issues resolved without manual steps |
| Time to First Success | <5 minutes | From download to working inference |
| Unicode Error Rate | 0% | No encoding crashes in diagnostics |

## Epic Stories

### Story 0.1: System Resource Detection & Model Recommendation

**Story Points:** 3
**Priority:** P0 (Critical - Blocks Setup)

**User Story:**
As a new user installing MailMind, I need the system to automatically detect my hardware and recommend an appropriate AI model so that I don't experience timeout failures or poor performance.

**Acceptance Criteria:**

**AC1: Cross-Platform Resource Detection**
- [ ] Detect total and available RAM using `psutil`
- [ ] Detect CPU cores and average usage over 5-second window
- [ ] Detect GPU presence and VRAM (Windows: via nvidia-smi, Mac: via system_profiler)
- [ ] Detect available disk space for model storage
- [ ] Resource check completes in <5 seconds
- [ ] Display resource report in setup wizard

**AC2: Intelligent Model Recommendation**
- [ ] Model recommendation algorithm based on available RAM:
  - `llama3.2:1b` - 4-6 GB available RAM (1GB download, fastest)
  - `llama3.2:3b` - 6-10 GB available RAM (2GB download, balanced) **[RECOMMENDED DEFAULT]**
  - `llama3.1:8b-instruct-q4_K_M` - 10+ GB available RAM (5GB download, best quality)
- [ ] Highlight recommended model in setup UI with reasoning
- [ ] Allow user to override recommendation with warning
- [ ] Store selected model in `config/user_config.yaml`

**AC3: Performance Expectation Setting**
- [ ] Display expected performance for selected model:
  - 1B model: ~5-10 tokens/second (CPU), ~30-50 t/s (GPU)
  - 3B model: ~3-8 t/s (CPU), ~20-40 t/s (GPU)
  - 8B model: ~1-3 t/s (CPU), ~10-30 t/s (GPU)
- [ ] Warn if system resources are below recommended minimum
- [ ] Show upgrade path: "For faster performance, consider upgrading RAM"

**Technical Implementation:**

```python
# src/mailmind/utils/system_diagnostics.py

import psutil
import platform
from typing import Dict, Any, Tuple

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
    # RAM check
    ram = psutil.virtual_memory()
    ram_info = {
        'total_gb': ram.total / (1024**3),
        'available_gb': ram.available / (1024**3),
        'percent_used': ram.percent
    }

    # CPU check (5-second average)
    cpu_percent = psutil.cpu_percent(interval=5)
    cpu_info = {
        'cores': psutil.cpu_count(logical=False),
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

    return {
        'ram': ram_info,
        'cpu': cpu_info,
        'gpu': gpu_info,
        'disk': disk_info,
        'platform': platform.system()
    }

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

    return model, reasoning, performance
```

**Dependencies:**
- Add `psutil>=5.9.0` to requirements.txt

**Testing:**
- [ ] Test on 4GB RAM system → recommends llama3.2:1b
- [ ] Test on 8GB RAM system → recommends llama3.2:3b
- [ ] Test on 16GB RAM system → recommends llama3.1:8b
- [ ] Test resource check completes in <5 seconds

**Definition of Done:**
- [ ] All ACs met
- [ ] Tested on 3 different hardware configurations
- [ ] Resource detection works on Windows, macOS, Linux
- [ ] Model recommendations stored in user_config.yaml
- [ ] Documentation updated

---

### Story 0.2: Interactive Model Selection in Setup Wizard

**Story Points:** 5
**Priority:** P0 (Critical - Setup UX)

**User Story:**
As a new user running the setup script, I need to choose from model options with clear descriptions so that I can make an informed decision about performance vs. quality trade-offs.

**Acceptance Criteria:**

**AC1: Enhanced setup.bat with Model Selection**
- [ ] After dependency installation, show model selection menu
- [ ] Display detected system resources (RAM, CPU, GPU)
- [ ] Show recommended model with ⭐ indicator
- [ ] Present 3 options with clear descriptions:
  - **Option 1**: Small (llama3.2:1b) - "Fast & Lightweight (1GB, 4GB RAM needed)"
  - **Option 2**: Medium (llama3.2:3b) - "Balanced Performance (2GB, 6GB RAM needed)" **⭐ Recommended**
  - **Option 3**: Large (llama3.1:8b) - "Best Quality (5GB, 10GB+ RAM needed)"
- [ ] Accept user choice (1/2/3) via interactive prompt
- [ ] Automatically download selected model with progress
- [ ] Save selection to config/user_config.yaml
- [ ] Display post-selection confirmation with expected performance

**AC2: Model Configuration Persistence**
- [ ] Create `config/user_config.yaml` if it doesn't exist
- [ ] Store selected model and metadata:
  ```yaml
  ollama:
    selected_model: "llama3.2:3b"
    model_size: "medium"
    selection_date: "2025-10-17"
    auto_selected: false  # true if user accepted recommendation without changing

  system:
    ram_gb: 8.0
    cpu_cores: 4
    gpu_detected: false
  ```
- [ ] Main application reads user_config.yaml on startup
- [ ] Fallback to default config if user_config missing

**AC3: Model Download with Progress**
- [ ] Use `ollama pull <model>` with output piped to console
- [ ] Show download progress (Ollama shows progress bars natively)
- [ ] Handle download failures gracefully (resume on retry)
- [ ] Verify model downloaded successfully before proceeding
- [ ] Option to skip download and do it later

**Technical Implementation:**

```batch
REM setup.bat enhancement (after dependency installation)

echo.
echo ========================================
echo AI Model Selection
echo ========================================
echo.
echo Checking your system resources...

REM Run Python resource checker
python -c "import sys; sys.path.insert(0, 'src'); from mailmind.utils.system_diagnostics import check_system_resources, recommend_model; r = check_system_resources(); model, reasoning, perf = recommend_model(r); print(f'Available RAM: {r[\"ram\"][\"available_gb\"]:.1f}GB'); print(f'CPU Cores: {r[\"cpu\"][\"cores\"]}'); print(f'GPU: {\"Yes\" if r[\"gpu\"][\"detected\"] else \"No\"}'); print(''); print('RECOMMENDED MODEL:'); print(f'  {model} - {reasoning}'); print(f'  Expected speed: {perf[\"tokens_per_second\"]}'); print(f'  Download size: {perf[\"size_gb\"]}GB')"

echo.
echo Choose your AI model:
echo   1. Small  - llama3.2:1b (1GB download, 4GB RAM, fastest)
echo   2. Medium - llama3.2:3b (2GB download, 6GB RAM, balanced) ⭐ RECOMMENDED
echo   3. Large  - llama3.1:8b (5GB download, 10GB+ RAM, best quality)
echo.

choice /C 123 /M "Select model size (1/2/3)"

if %ERRORLEVEL%==1 (
    set MODEL=llama3.2:1b
    set SIZE=small
)
if %ERRORLEVEL%==2 (
    set MODEL=llama3.2:3b
    set SIZE=medium
)
if %ERRORLEVEL%==3 (
    set MODEL=llama3.1:8b-instruct-q4_K_M
    set SIZE=large
)

echo.
echo Downloading %MODEL%...
echo This may take 5-15 minutes depending on your internet speed.
echo.

ollama pull %MODEL%

if errorlevel 1 (
    echo.
    echo ERROR: Model download failed!
    echo You can download it later with: ollama pull %MODEL%
    echo.
    pause
    exit /b 1
)

REM Save to user_config.yaml
python -c "import yaml; import pathlib; pathlib.Path('config').mkdir(exist_ok=True); config = {'ollama': {'selected_model': '%MODEL%', 'model_size': '%SIZE%'}}; yaml.dump(config, open('config/user_config.yaml', 'w'))"

echo.
echo ✓ Model configured successfully!
echo.
```

**Dependencies:**
- Story 0.1 (System Resource Detection) must be complete
- Requires PyYAML for config file handling

**Testing:**
- [ ] Test selection of each model option (1/2/3)
- [ ] Test config file created correctly
- [ ] Test main.py reads user_config.yaml on startup
- [ ] Test download failure handling
- [ ] Test skipping download option

**Definition of Done:**
- [ ] All ACs met
- [ ] Tested on Windows 10/11
- [ ] Model selection saves correctly
- [ ] Application uses selected model on startup
- [ ] Documentation updated with model comparison table

---

### Story 0.3: Unicode Error Fixes & Robust Subprocess Handling

**Story Points:** 2
**Priority:** P0 (Critical - Blocks Diagnostics)

**User Story:**
As a user running diagnostics on Windows, I need the diagnostic tool to handle all character encodings properly so that it doesn't crash with Unicode errors when testing model inference.

**Root Cause Analysis:**
```
Exception in thread Thread-6 (_readerthread):
UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f in position 332: character maps to <undefined>
```

**Problem:** Windows subprocess uses default `cp1252` encoding, but Ollama outputs UTF-8 (including emojis/special characters from AI model responses).

**Acceptance Criteria:**

**AC1: Fix All Subprocess Calls**
- [ ] Add `encoding='utf-8', errors='replace'` to ALL subprocess.run() calls
- [ ] Identify all subprocess calls in codebase (main.py, setup.bat Python helpers, diagnostics)
- [ ] Update each call to explicitly handle UTF-8 with error replacement
- [ ] Test with model outputs containing emojis, special characters, non-ASCII

**AC2: Robust Error Handling**
- [ ] Replace invalid characters with '�' instead of crashing
- [ ] Log warnings when character replacement occurs
- [ ] Ensure diagnostic output remains readable after replacement
- [ ] Test on Windows with various locales (en-US, ja-JP, de-DE)

**AC3: Documentation & Testing**
- [ ] Document encoding handling in CONTRIBUTING.md
- [ ] Add test cases for Unicode edge cases
- [ ] Create regression test: model output with emojis
- [ ] Verify zero Unicode errors in diagnostics after fix

**Technical Implementation:**

```python
# BEFORE (vulnerable to Unicode errors):
result = subprocess.run(
    ['ollama', 'run', 'llama3.1:8b-instruct-q4_K_M'],
    input='Test',
    capture_output=True,
    text=True,
    timeout=45
)

# AFTER (robust Unicode handling):
result = subprocess.run(
    ['ollama', 'run', 'llama3.1:8b-instruct-q4_K_M'],
    input='Test',
    capture_output=True,
    text=True,
    encoding='utf-8',           # Explicit UTF-8 encoding
    errors='replace',            # Replace invalid chars instead of crashing
    timeout=45
)

# Files to update:
# - main.py: run_ollama_diagnostics() function (4 subprocess calls)
# - setup.bat Python helpers (if any)
# - src/mailmind/core/ollama_manager.py (if any subprocess calls)
```

**Grep Command to Find All Subprocess Calls:**
```bash
grep -rn "subprocess.run" src/ main.py setup.bat --include="*.py"
```

**Dependencies:**
- None (standalone fix)

**Testing:**
- [ ] Run diagnostics with model that outputs emojis
- [ ] Test on Windows 10/11 with various locales
- [ ] Verify no UnicodeDecodeError exceptions
- [ ] Verify diagnostic output displays correctly with replaced chars

**Definition of Done:**
- [ ] All subprocess calls updated
- [ ] Zero Unicode errors in test suite
- [ ] Tested on Windows with emoji outputs
- [ ] Regression test added
- [ ] Documentation updated

---

### Story 0.4: Interactive Diagnostic Remediation Menu

**Story Points:** 5
**Priority:** P1 (High - Improves UX)

**User Story:**
As a user experiencing setup issues, I need an interactive menu that offers automated fixes so that I can resolve problems without reading documentation or seeking support.

**Acceptance Criteria:**

**AC1: Remediation Menu on Diagnostic Failure**
- [ ] When diagnostics fail, automatically show remediation menu
- [ ] Present numbered options (1-6) with clear descriptions
- [ ] Accept user input and execute selected remediation
- [ ] Show progress/results of remediation attempt
- [ ] Loop back to menu if remediation fails
- [ ] Option to exit and try manually

**AC2: Automated Remediation Actions**

**Option 1: Switch to Smaller Model** (Recommended for timeouts)
- [ ] Detect current configured model
- [ ] Recommend next smaller size:
  - 8B → 3B: "Switch to faster 3B model?"
  - 3B → 1B: "Switch to lightweight 1B model?"
  - 1B → Already smallest: "Already using smallest model"
- [ ] Auto-run: `ollama pull <smaller_model>`
- [ ] Update config/user_config.yaml
- [ ] Rerun inference test with new model

**Option 2: Re-download Current Model** (Fix corrupted model)
- [ ] Remove current model: `ollama rm <model>`
- [ ] Re-download: `ollama pull <model>`
- [ ] Verify download successful
- [ ] Rerun inference test

**Option 3: Show System Resources**
- [ ] Display detailed resource report:
  - RAM: Total, Used, Available
  - CPU: Cores, Current Usage, Temperature (if available)
  - GPU: Detected, Name, VRAM
  - Disk: Total, Free, Model Storage Location
  - Running Processes: Ollama, Python, other high-memory apps
- [ ] Highlight resource bottlenecks in red
- [ ] Provide recommendations: "Close Chrome (using 4GB RAM)"

**Option 4: Show Ollama Logs**
- [ ] Auto-detect log location by platform:
  - Windows: `%LOCALAPPDATA%\Ollama\logs\`
  - macOS: `~/.ollama/logs/`
  - Linux: `~/.ollama/logs/`
- [ ] Display last 50 lines of server.log
- [ ] Highlight errors/warnings in red
- [ ] Offer to save full logs to file for support

**Option 5: Generate Support Report**
- [ ] Collect all diagnostic data:
  - System resources
  - Ollama version
  - Model list
  - Last 100 lines of Ollama logs
  - Diagnostic test results
  - Config files (sanitized)
- [ ] Save to `support_report_<timestamp>.txt`
- [ ] Display file location
- [ ] Copy report to clipboard option

**Option 6: Exit**
- [ ] Return to command prompt
- [ ] Display manual troubleshooting guide URL

**AC3: User Experience**
- [ ] Clear visual formatting with separators
- [ ] Color-coded output (errors=red, success=green, info=blue)
- [ ] Progress indicators for long operations
- [ ] Confirmation prompts for destructive actions
- [ ] Success/failure feedback after each remediation

**Technical Implementation:**

```python
# main.py enhancement

def offer_remediations(diagnostic_results: dict) -> bool:
    """
    Interactive remediation menu for diagnostic failures.

    Args:
        diagnostic_results: Results from run_ollama_diagnostics()

    Returns:
        bool: True if issue was resolved, False otherwise
    """
    print("\n" + "=" * 60)
    print("🔧 Automated Remediation Options")
    print("=" * 60)
    print("\nWhat would you like to try?")
    print("  1. Switch to smaller model (recommended for timeouts)")
    print("  2. Re-download current model (fix corrupted model)")
    print("  3. Show detailed system resources")
    print("  4. Show Ollama logs")
    print("  5. Generate support report")
    print("  6. Exit")
    print()

    while True:
        choice = input("Enter choice (1-6): ").strip()

        if choice == '1':
            success = switch_to_smaller_model()
            if success:
                return True
            print("\nWould you like to try something else? (y/n)")
            if input().lower() != 'y':
                return False

        elif choice == '2':
            success = repull_current_model()
            if success:
                return True
            print("\nWould you like to try something else? (y/n)")
            if input().lower() != 'y':
                return False

        elif choice == '3':
            show_system_resources()
            print("\nPress Enter to return to menu...")
            input()

        elif choice == '4':
            show_ollama_logs()
            print("\nPress Enter to return to menu...")
            input()

        elif choice == '5':
            report_path = generate_support_report()
            print(f"\n✓ Support report saved to: {report_path}")
            print("Press Enter to return to menu...")
            input()

        elif choice == '6':
            print("\nExiting remediation menu.")
            print("For manual troubleshooting, see: TROUBLESHOOTING_OLLAMA.md")
            return False

        else:
            print("Invalid choice. Please enter 1-6.")

def switch_to_smaller_model() -> bool:
    """Auto-switch to next smaller model size."""
    # Implementation
    pass

def repull_current_model() -> bool:
    """Remove and re-download current model."""
    # Implementation
    pass

def show_system_resources():
    """Display detailed system resource report."""
    # Implementation
    pass

def show_ollama_logs():
    """Display last 50 lines of Ollama logs."""
    # Implementation
    pass

def generate_support_report() -> str:
    """Generate comprehensive support report."""
    # Implementation
    pass
```

**Dependencies:**
- Story 0.1 (System Resource Detection) for resource display
- Story 0.3 (Unicode Fixes) for subprocess calls

**Testing:**
- [ ] Test each remediation option (1-6)
- [ ] Test model switching flow
- [ ] Test model re-download flow
- [ ] Test support report generation
- [ ] Test menu loop behavior
- [ ] Test on Windows, macOS, Linux

**Definition of Done:**
- [ ] All 6 remediation options implemented
- [ ] All ACs met
- [ ] Tested on 3 platforms
- [ ] User feedback positive (resolves 80%+ of issues)
- [ ] Documentation updated

---

### Story 0.5: Dynamic Model Loading & Runtime Switching

**Story Points:** 3
**Priority:** P2 (Nice to Have - Future Enhancement)

**User Story:**
As a user running MailMind, I need the ability to switch AI models at runtime without reinstalling so that I can upgrade/downgrade based on performance needs.

**Acceptance Criteria:**

**AC1: Runtime Model Switching Command**
- [x] Add command-line flag: `python main.py --switch-model`
- [x] Show current model and detected system resources
- [x] Present model options with recommendations
- [x] Download new model if not present
- [x] Update user_config.yaml
- [x] Restart application with new model

**AC2: Automatic Model Fallback**
- [x] If inference timeout occurs 3 times consecutively:
  - Log warning: "Model inference timing out repeatedly"
  - Prompt user: "Switch to faster model? (y/n)"
  - If yes: Auto-switch to next smaller model
  - If no: Continue with current model
- [x] Store fallback history to prevent infinite loops
- [x] Display notification in UI when fallback occurs

**AC3: Model Performance Monitoring**
- [x] Track average inference time per model
- [x] Store in performance_metrics table
- [x] Display in settings UI: "Current model: llama3.2:3b (avg: 4.2s)"
- [x] Recommend upgrade if system resources improve: "Your RAM is now 12GB - consider upgrading to 8B model"

**Technical Implementation:**

```python
# main.py enhancement

def handle_model_switch():
    """Interactive model switching."""
    resources = check_system_resources()
    current_model = get_current_model_from_config()

    print(f"Current model: {current_model}")
    print(f"Available RAM: {resources['ram']['available_gb']:.1f}GB")
    print()

    recommended, reasoning, perf = recommend_model(resources)

    print("Available models:")
    print("  1. llama3.2:1b (fastest, basic quality)")
    print("  2. llama3.2:3b (balanced) ⭐ RECOMMENDED" if recommended == "llama3.2:3b" else "")
    print("  3. llama3.1:8b (best quality, slowest)")
    print()

    choice = input("Select model (1/2/3) or 'c' to cancel: ").strip()

    if choice == 'c':
        return

    model_map = {
        '1': 'llama3.2:1b',
        '2': 'llama3.2:3b',
        '3': 'llama3.1:8b-instruct-q4_K_M'
    }

    new_model = model_map.get(choice)
    if not new_model:
        print("Invalid choice.")
        return

    # Download if needed
    if not model_exists(new_model):
        print(f"Downloading {new_model}...")
        subprocess.run(['ollama', 'pull', new_model])

    # Update config
    update_user_config(new_model)

    print(f"\n✓ Switched to {new_model}")
    print("Restart MailMind for changes to take effect.")

# src/mailmind/core/ollama_manager.py enhancement

class OllamaManager:
    def __init__(self, config):
        # ...existing code...
        self.timeout_count = 0
        self.timeout_threshold = 3

    def test_inference(self, timeout=30):
        """Enhanced test inference with fallback logic."""
        success = super().test_inference(timeout)

        if not success:
            self.timeout_count += 1

            if self.timeout_count >= self.timeout_threshold:
                logger.warning(
                    f"Model inference timed out {self.timeout_count} times. "
                    "Consider switching to a smaller model."
                )

                # Prompt for auto-fallback
                response = input("\nSwitch to smaller model automatically? (y/n): ")
                if response.lower() == 'y':
                    return self._auto_fallback_to_smaller_model()
        else:
            self.timeout_count = 0  # Reset on success

        return success

    def _auto_fallback_to_smaller_model(self) -> bool:
        """Automatically switch to next smaller model."""
        current = self.current_model

        fallback_chain = {
            'llama3.1:8b-instruct-q4_K_M': 'llama3.2:3b',
            'llama3.2:3b': 'llama3.2:1b',
            'llama3.2:1b': None  # No smaller model available
        }

        next_model = fallback_chain.get(current)

        if next_model is None:
            logger.error("Already using smallest model - cannot fallback further")
            return False

        logger.info(f"Auto-falling back from {current} to {next_model}")

        # Download if needed
        if not self._model_exists(next_model):
            subprocess.run(['ollama', 'pull', next_model])

        # Update config
        self.current_model = next_model
        update_user_config(next_model)

        # Retry test inference
        return self.test_inference()
```

**Dependencies:**
- Story 0.1 (System Resource Detection)
- Story 0.2 (Model Selection)

**Testing:**
- [x] Test manual model switch command
- [x] Test automatic fallback on repeated timeouts
- [x] Test fallback chain (8B → 3B → 1B)
- [x] Test config persistence after switch
- [x] Test with model not downloaded (auto-downloads)

**Definition of Done:**
- [x] All ACs met
- [x] Manual switching works
- [x] Automatic fallback works
- [x] Config updated correctly
- [x] Documentation updated

---

## Epic Dependencies

**Blocks:**
- Epic 1: AI-Powered Email Intelligence (all stories require working Ollama setup)
- Epic 2: Desktop Application (Story 2.5 Onboarding Wizard integrates with setup)
- Epic 3: Security & MVP Readiness (requires stable foundation)

**Depends On:**
- None (foundational work, no upstream dependencies)

**External Dependencies:**
- Ollama installed and running (user responsibility, but we guide them)
- Python 3.10+ with pip
- Windows 10/11 for setup.bat (Unix scripts in future)

---

## Implementation Sequence

**Phase 1 (Week 0): Critical Fixes**
1. Story 0.3: Unicode Error Fixes (2 points) - **START HERE**
2. Story 0.1: System Resource Detection (3 points)

**Phase 2 (Week 1): Enhanced Setup**
3. Story 0.2: Interactive Model Selection (5 points)
4. Story 0.4: Interactive Remediation (5 points)

**Phase 3 (Future): Advanced Features**
5. Story 0.5: Dynamic Model Loading (3 points) - Nice to have

**Total Epic Points:** 18 points (excluding Story 0.5)
**Critical Path Points:** 10 points (Stories 0.1, 0.2, 0.3)

---

## Success Metrics - Detailed

| Phase | Metric | Before | After | Target |
|-------|--------|--------|-------|--------|
| **Setup Success** |
| | Complete setup without errors | 30% | 90%+ | >90% |
| | Time to first successful inference | 15-30 min | <5 min | <5 min |
| | Manual intervention required | 70% | <10% | <10% |
| **Diagnostics** |
| | Issues resolved automatically | 0% | 80%+ | >80% |
| | Unicode errors | Common | 0 | 0 |
| | Average diagnostic runtime | N/A | <2 min | <2 min |
| **Model Selection** |
| | Users select appropriate model | 0% | 95%+ | >95% |
| | Model works on user's system | 50% | 95%+ | >95% |
| | Users understand performance trade-offs | 10% | 90%+ | >90% |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| psutil fails to detect resources accurately | Low | Medium | Graceful fallback to manual selection |
| Model downloads fail on slow connections | Medium | High | Resume support, skip option, offline instructions |
| Automated remediation makes things worse | Low | High | Confirmation prompts, backup config before changes |
| Different Windows versions behave differently | Medium | Medium | Test on Win 10/11, provide platform-specific guidance |
| Users ignore resource warnings and select wrong model | High | Medium | Show expected performance, allow trial and easy switching |

---

## Out of Scope (Future Enhancements)

**Not in Epic 0:**
- macOS/Linux setup scripts (focus on Windows for MVP)
- GUI installer (batch script sufficient for MVP)
- Automatic model updates
- Multi-model caching (keep only selected model for MVP)
- Advanced hardware profiling (GPU selection, etc.)
- Telemetry for setup success tracking

**Future Epics:**
- Epic 4: Cross-Platform Support (macOS, Linux)
- Epic 5: GUI Installer & Auto-Updates
- Epic 6: Multi-Model Management

---

## Definition of Done (Epic Level)

- [ ] All P0 stories complete (0.1, 0.2, 0.3)
- [ ] P1 story complete (0.4)
- [ ] Setup success rate >90% in testing
- [ ] Zero Unicode errors in test suite
- [ ] Model selection works on 4GB, 8GB, 16GB RAM systems
- [ ] Interactive remediation resolves 80%+ of issues
- [ ] Documentation complete (TROUBLESHOOTING_OLLAMA.md updated)
- [ ] Tested on Windows 10 and 11
- [ ] All tests passing
- [ ] Code reviewed and approved

---

## Related Documentation

- [TROUBLESHOOTING_OLLAMA.md](/Users/dawsonhulme/Downloads/Projects/mail-mind/TROUBLESHOOTING_OLLAMA.md) - User-facing troubleshooting guide
- [Story 0.1](/Users/dawsonhulme/Downloads/Projects/mail-mind/docs/stories/story-0.1.md) - Deprecated, replaced by this epic
- [Story 0.2](/Users/dawsonhulme/Downloads/Projects/mail-mind/docs/stories/Story_0.2_Enhanced_Diagnostics_Model_Selection.md) - Deprecated, replaced by this epic
- [Epic 1 - AI Intelligence](/Users/dawsonhulme/Downloads/Projects/mail-mind/docs/epic-stories.md#epic-1) - Depends on this epic

---

_This epic addresses critical installation and setup issues discovered during real-world testing, ensuring MailMind can be successfully installed and configured on a wide range of hardware before users ever see the main application._
