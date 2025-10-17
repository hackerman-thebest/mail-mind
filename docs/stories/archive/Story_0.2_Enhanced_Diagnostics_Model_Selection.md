# Story 0.2: Enhanced Ollama Diagnostics & Automated Model Selection

## Problem Statement

**Current Issues:**
1. Diagnostic tool identifies problems but requires manual remediation
2. Unicode decode errors when testing model inference on Windows (cp1252 encoding issue)
3. Setup assumes all users can run 8B parameter model (requires 8GB+ RAM)
4. No automated resource checking before model selection
5. No way to easily switch to smaller models when issues occur
6. Ollama logs location is shown but not automatically retrieved

**Real-World Impact:**
- User experienced 45-second timeout with no automated fix
- Unicode errors prevented proper diagnostic output capture
- Manual troubleshooting required extensive technical knowledge
- Resource-constrained systems fail silently

## User Story

**As a** MailMind user with limited system resources
**I want** automated diagnostics that can fix common issues and help me select an appropriate model
**So that** I can get MailMind running without manual troubleshooting or technical expertise

## Acceptance Criteria

### AC1: Automated System Resource Checking ✅
- [ ] Check available RAM (total, used, available)
- [ ] Check CPU usage over 5-second window
- [ ] Display resource information during diagnostics
- [ ] Warn if insufficient resources for selected model
- [ ] Recommend appropriate model based on available RAM

**Success Metric:** Resource checks complete in <5 seconds

### AC2: Interactive Model Selection in Setup Wizard ✅
- [ ] Present 3 model options with clear descriptions:
  - **Small (llama3.2:1b)**: ~1GB download, 4GB RAM required, fastest
  - **Medium (llama3.2:3b)**: ~2GB download, 6GB RAM required, balanced
  - **Large (llama3.1:8b-instruct-q4_K_M)**: ~5GB download, 8GB+ RAM, best quality
- [ ] Auto-detect system resources and recommend appropriate model
- [ ] Automatically download selected model
- [ ] Save selection to `config/user_config.yaml`
- [ ] Update MailMind to use selected model

**Success Metric:** User can select and configure model in <5 minutes

### AC3: Automated Log Retrieval ✅
- [ ] Automatically locate Ollama logs by platform:
  - Windows: `%LOCALAPPDATA%\Ollama\logs\`
  - macOS: `~/.ollama/logs/`
  - Linux: `~/.ollama/logs/`
- [ ] Display last 50 lines of server.log
- [ ] Handle missing log files gracefully
- [ ] Parse and highlight error lines
- [ ] Offer to save full logs to file for support

**Success Metric:** Logs retrieved and displayed automatically

### AC4: Interactive Remediation Menu ✅
When diagnostics fail, offer automated fixes:
1. **Switch to smaller model**
   - Detect current model
   - Offer next smaller size
   - Auto-download and configure
2. **Re-pull corrupted model**
   - Remove current model
   - Re-download from Ollama registry
3. **Restart Ollama service**
   - Attempt graceful restart (platform-specific)
   - Verify service comes back up
4. **Show detailed system info**
   - Full resource report
   - Process list for Ollama
   - Port usage check
5. **Generate support report**
   - Collect all diagnostic data
   - Save to `support_report_<timestamp>.txt`

**Success Metric:** 80% of issues resolvable without manual intervention

### AC5: Fix Unicode Handling ✅
- [ ] Add `encoding='utf-8', errors='replace'` to all subprocess calls
- [ ] Handle binary/special characters in model output
- [ ] Test with non-ASCII characters in responses
- [ ] Ensure Windows cp1252 compatibility

**Success Metric:** No Unicode errors in diagnostic output

### AC6: Model Switching in Running System ✅
- [ ] Add command: `python main.py --switch-model`
- [ ] Show current model and available alternatives
- [ ] Allow selection and automatic configuration
- [ ] Restart MailMind with new model

**Success Metric:** Users can switch models without editing config files

## Technical Design

### 1. System Resource Checker
**New File:** `src/mailmind/utils/system_diagnostics.py`

```python
def check_system_resources() -> Dict[str, Any]:
    """
    Check system resources and return comprehensive report.

    Returns:
        dict: {
            'ram': {'total': int, 'available': int, 'percent': float},
            'cpu': {'percent': float, 'count': int},
            'disk': {'total': int, 'free': int},
            'recommendations': List[str]
        }
    """
    pass

def recommend_model(available_ram_gb: float) -> str:
    """
    Recommend appropriate model based on available RAM.

    Args:
        available_ram_gb: Available RAM in GB

    Returns:
        str: Recommended model name
    """
    if available_ram_gb >= 8:
        return 'llama3.1:8b-instruct-q4_K_M'
    elif available_ram_gb >= 6:
        return 'llama3.2:3b'
    else:
        return 'llama3.2:1b'
```

### 2. Enhanced Setup Wizard
**File:** `setup.bat` (Windows) and `setup.sh` (Unix)

```batch
REM New section after dependency installation
echo ========================================
echo AI Model Selection
echo ========================================
echo.
echo Checking your system resources...
python -c "from src.mailmind.utils.system_diagnostics import check_system_resources, recommend_model; r = check_system_resources(); print(f'Available RAM: {r['ram']['available']/1024/1024/1024:.1f}GB'); print(f'Recommended: {recommend_model(r['ram']['available']/1024/1024/1024)}')"
echo.
echo Choose your AI model:
echo   1. Small  - llama3.2:1b (1GB download, 4GB RAM, fastest, good for testing)
echo   2. Medium - llama3.2:3b (2GB download, 6GB RAM, balanced performance)
echo   3. Large  - llama3.1:8b (5GB download, 8GB+ RAM, best quality)
echo.
choice /C 123 /M "Select model size"
```

### 3. Interactive Remediation
**File:** `main.py`

```python
def offer_remediations(diagnostic_results: dict) -> bool:
    """
    Offer interactive remediations based on diagnostic failures.

    Args:
        diagnostic_results: Results from run_ollama_diagnostics()

    Returns:
        bool: True if issue was resolved, False otherwise
    """
    print("\n" + "=" * 60)
    print("Automated Remediation Options")
    print("=" * 60)
    print("\nWhat would you like to try?")
    print("  1. Switch to smaller model (recommended)")
    print("  2. Re-download current model")
    print("  3. Show system resources")
    print("  4. Show Ollama logs")
    print("  5. Generate support report")
    print("  6. Exit")

    choice = input("\nEnter choice (1-6): ").strip()

    if choice == '1':
        return switch_to_smaller_model()
    elif choice == '2':
        return repull_model()
    # ... etc
```

### 4. Unicode Fix
**File:** All subprocess calls in `main.py`

```python
# Before (causes Unicode errors):
result = subprocess.run(
    ['ollama', 'run', 'llama3.1:8b-instruct-q4_K_M'],
    input='Test',
    capture_output=True,
    text=True,
    timeout=45
)

# After (handles Unicode properly):
result = subprocess.run(
    ['ollama', 'run', 'llama3.1:8b-instruct-q4_K_M'],
    input='Test',
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace',  # Replace invalid characters instead of crashing
    timeout=45
)
```

### 5. Model Configuration
**File:** `config/user_config.yaml` (new)

```yaml
# User-specific configuration (overrides defaults)
ollama:
  selected_model: "llama3.2:1b"  # User's choice from setup
  selected_model_size: "small"   # small, medium, large
  auto_fallback: true            # Auto-fallback to smaller model on failure

system:
  ram_gb: 8.0                     # Detected during setup
  model_selection_date: "2025-10-17"
```

## Dependencies

Add to `requirements.txt`:
```
psutil>=5.9.0  # Cross-platform system resource monitoring
```

## Implementation Plan

### Phase 1: Quick Fixes (1-2 hours)
1. Fix Unicode errors in subprocess calls
2. Add encoding='utf-8', errors='replace' everywhere
3. Test on Windows with special characters

### Phase 2: Resource Checking (2-3 hours)
1. Create `system_diagnostics.py`
2. Implement RAM/CPU checking
3. Add recommendation logic
4. Integrate into diagnostics

### Phase 3: Model Selection Wizard (3-4 hours)
1. Update `setup.bat` with model selection
2. Create `setup.sh` for Unix systems
3. Implement user_config.yaml handling
4. Add model download with progress

### Phase 4: Interactive Remediation (4-5 hours)
1. Create remediation menu in main.py
2. Implement model switching function
3. Implement model re-pulling
4. Add log retrieval and display
5. Create support report generator

### Phase 5: Testing & Documentation (2-3 hours)
1. Test on low-resource systems (4GB RAM)
2. Test model switching workflow
3. Update TROUBLESHOOTING_OLLAMA.md
4. Create MODEL_SELECTION_GUIDE.md

**Total Estimate:** 12-17 hours

## Success Metrics

- [ ] 80% of timeout issues resolved via automated remediation
- [ ] Users can select and configure model in <5 minutes
- [ ] Zero Unicode decode errors in diagnostics
- [ ] Resource checks complete in <5 seconds
- [ ] 90% of users select appropriate model for their system

## Testing Scenarios

### Test 1: Low-Resource System (4GB RAM)
- Run setup.bat
- Should recommend llama3.2:1b
- Should complete inference test in <30s

### Test 2: Model Switching
- Start with llama3.1:8b
- Timeout occurs
- Select "Switch to smaller model"
- Should auto-configure llama3.2:3b
- Should work without timeout

### Test 3: Unicode Handling
- Run diagnostic with model that outputs emojis/special chars
- Should not crash with UnicodeDecodeError
- Should display output with replacement characters

### Test 4: Automated Remediation
- Corrupt model intentionally
- Run diagnostics
- Select "Re-download model"
- Should auto-fix and work

## Risks & Mitigations

**Risk 1:** Smaller models may not perform well enough for email tasks
- **Mitigation:** Test llama3.2:3b performance, may be sufficient for most tasks
- **Fallback:** Allow easy upgrade to larger model later

**Risk 2:** Model downloads may fail on slow connections
- **Mitigation:** Show progress bar, allow resume if interrupted
- **Fallback:** Provide offline model installation instructions

**Risk 3:** Automated Ollama restart may not work on all platforms
- **Mitigation:** Graceful fallback to manual restart instructions
- **Monitoring:** Track success rate per platform

## Future Enhancements

- GPU detection and CUDA model recommendations
- Automatic model quantization selection (Q4 vs Q8)
- Model performance benchmarking tool
- Automatic model updates when new versions released
- Multi-model support (different models for different tasks)

## Open Questions

1. Should we support custom models (user-provided)?
2. Should setup wizard offer "expert mode" with full control?
3. How to handle users who want to switch back to larger model later?
4. Should we cache multiple models or only keep one at a time?

## References

- Ollama Model Library: https://ollama.com/library
- llama3.2 announcement: https://ollama.com/blog/llama3.2
- psutil documentation: https://psutil.readthedocs.io/
