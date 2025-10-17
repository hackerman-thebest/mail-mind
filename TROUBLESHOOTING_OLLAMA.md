# Ollama Troubleshooting Guide

## Quick Diagnostic Tool

If you're experiencing issues with Ollama (especially timeout errors), run the built-in diagnostic tool:

```bash
python main.py --diagnose
```

This will automatically check:
1. Ollama service status
2. Model list accessibility
3. Basic inference functionality
4. HTTP endpoint connectivity

## Common Issue: Test Inference Timeout (30 seconds)

### Symptoms
- `python main.py` hangs and times out after 30 seconds
- Error message: "Test inference TIMED OUT after 30s"
- Ollama installed but not responding

### Solutions (Try in order)

#### 1. Restart Ollama (Most Common Fix)
```bash
# Windows:
# - Right-click Ollama icon in system tray
# - Click "Quit"
# - Reopen Ollama from Start Menu
# - Wait 10 seconds
# - Run: python main.py
```

#### 2. Verify Ollama Service
```bash
ollama ps
# Should show running models or empty list (not an error)

ollama list
# Should show installed models including llama3.1:8b-instruct-q4_K_M
```

#### 3. Re-pull Model (If Corrupted)
```bash
# Remove and re-download the model
ollama rm llama3.1:8b-instruct-q4_K_M
ollama pull llama3.1:8b-instruct-q4_K_M
```

#### 4. Check System Resources
- **RAM**: Need at least 8GB free
- **CPU**: Should not be at 100% usage
- **Disk**: Check if %USERPROFILE%\.ollama\models\ has space

#### 5. Windows Defender / Antivirus
```bash
# Add Ollama to Windows Defender exclusions:
# 1. Open Windows Security
# 2. Virus & threat protection
# 3. Manage settings
# 4. Add or remove exclusions
# 5. Add: C:\Users\<username>\AppData\Local\Programs\Ollama\
# 6. Add: C:\Users\<username>\.ollama\
```

#### 6. Port Conflicts
```bash
# Check if port 11434 is in use:
netstat -ano | findstr "11434"

# If another process is using it, stop that process
```

#### 7. Try Smaller Model (Testing)
```bash
# Test with a smaller model to isolate the issue
ollama pull llama3.2:1b
# Then update config.yaml to use llama3.2:1b as primary_model
```

## Running Without Test Inference (Debugging Only)

If you need to skip the test inference to debug other parts of the system:

```bash
# Windows:
set MAILMIND_SKIP_TEST=1
python main.py

# Note: This skips verification that Ollama is working!
# Only use for debugging, not production.
```

## Setup Script Diagnostics

The `setup.bat` script now includes built-in diagnostics at the end:
- Test 1: Ollama service status
- Test 2: Model list access
- Test 3: Basic inference test
- Test 4: HTTP connection test

Run setup again to see detailed diagnostic output:
```bash
setup.bat
```

## Advanced Troubleshooting

### Check Ollama Logs
```bash
# Windows:
# Logs are in: %LOCALAPPDATA%\Ollama\logs\
dir %LOCALAPPDATA%\Ollama\logs\
type %LOCALAPPDATA%\Ollama\logs\server.log
```

### Verify Ollama Installation
```bash
ollama --version
# Should show version number

where ollama
# Should show path to ollama.exe
```

### Test Direct HTTP API
```bash
curl http://localhost:11434/api/tags
# Should return JSON with list of models
```

### Clean Reinstall
```bash
# 1. Uninstall Ollama from Windows Settings
# 2. Delete folders:
#    - %LOCALAPPDATA%\Ollama
#    - %LOCALAPPDATA%\Programs\Ollama
#    - %USERPROFILE%\.ollama
# 3. Restart computer
# 4. Install Ollama from https://ollama.com/download
# 5. Run setup.bat again
```

## Getting Help

If none of these solutions work:

1. Run diagnostics and save output:
   ```bash
   python main.py --diagnose > diagnostics.txt
   ```

2. Check Ollama logs:
   ```bash
   type %LOCALAPPDATA%\Ollama\logs\server.log > ollama_logs.txt
   ```

3. Report the issue with:
   - diagnostics.txt
   - ollama_logs.txt
   - Your system specs (RAM, CPU, OS version)
   - Steps you've already tried
