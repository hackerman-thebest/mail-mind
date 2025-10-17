@echo off
REM MailMind Setup Script for Windows
REM Configures Ollama and Python dependencies

echo ========================================
echo MailMind Setup Wizard
echo ========================================
echo.

REM Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Check Ollama installation
echo [2/5] Checking Ollama installation...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ollama not found!
    echo Please install Ollama from https://ollama.com/download
    pause
    exit /b 1
)
ollama --version
echo.

REM Detect GPU availability
echo [3/5] Detecting hardware configuration...
echo.
echo NOTE: MailMind can use GPU acceleration if available, but works fine on CPU.
echo GPU detection can cause 90+ second delays on some systems.
echo.
choice /C YN /M "Do you have an NVIDIA GPU you want to use for acceleration"
if %ERRORLEVEL%==2 (
    echo.
    echo Configuring Ollama for CPU mode ^(recommended for most users^)...
    REM Set for current session
    set OLLAMA_NUM_GPU=0
    set CUDA_VISIBLE_DEVICES=
    REM Set permanently for future sessions
    setx OLLAMA_NUM_GPU "0" >nul
    setx CUDA_VISIBLE_DEVICES "" >nul
    echo.
    echo CPU mode configured! This will avoid GPU detection delays.
    echo Performance: ~10-30 tokens/second ^(sufficient for email processing^)
) else if %ERRORLEVEL%==1 (
    echo.
    echo GPU mode enabled. If you experience delays, run this script again and select N.
)
echo.

REM Install Python dependencies
echo [4/5] Installing Python dependencies...
echo This may take a few minutes...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo WARNING: Some dependencies failed to install.
    echo.
    echo If pysqlcipher3 failed ^(encryption^), you can:
    echo   1. Install Visual C++ Build Tools (https://visualstudio.microsoft.com/visual-cpp-build-tools/)
    echo   2. Continue without encryption (functional but less secure)
    echo.
    choice /C YN /M "Continue anyway"
    if %ERRORLEVEL%==2 (
        echo Setup cancelled.
        pause
        exit /b 1
    )
)
echo.

REM Download AI model
echo [5/5] Checking AI model...
ollama list | findstr "llama3.1:8b-instruct-q4_K_M" >nul
if errorlevel 1 (
    echo.
    echo Downloading AI model ^(llama3.1:8b-instruct-q4_K_M^)...
    echo This is ~5GB and may take 10-20 minutes depending on your internet speed.
    echo.
    choice /C YN /M "Download now"
    if %ERRORLEVEL%==2 (
        echo.
        echo Skipping model download. You can download it later with:
        echo   ollama pull llama3.1:8b-instruct-q4_K_M
    ) else if %ERRORLEVEL%==1 (
        ollama pull llama3.1:8b-instruct-q4_K_M
    )
) else (
    echo Model already installed!
)
echo.

REM Run Ollama diagnostics
echo ========================================
echo Running Ollama Diagnostics...
echo ========================================
echo.
echo This will help verify your Ollama installation is working correctly.
echo.

REM Test 1: Check Ollama service
echo [Test 1/4] Checking Ollama service status...
ollama ps >nul 2>&1
if errorlevel 1 (
    echo   ❌ FAILED: Ollama service not responding
    echo   This usually means Ollama is not running properly.
    echo.
    echo   Troubleshooting steps:
    echo   1. Restart Ollama application (close it completely and reopen)
    echo   2. Check Task Manager - ensure "ollama" process is running
    echo   3. Try running: ollama serve
    echo   4. Reinstall Ollama from https://ollama.com/download
    echo.
) else (
    echo   ✓ Ollama service is running
)
echo.

REM Test 2: Check model list
echo [Test 2/4] Verifying model list access...
ollama list >nul 2>&1
if errorlevel 1 (
    echo   ❌ FAILED: Cannot access model list
    echo   This indicates Ollama API is not responding.
    echo.
    echo   Troubleshooting steps:
    echo   1. Check if Windows Defender/antivirus is blocking Ollama
    echo   2. Verify firewall isn't blocking localhost connections
    echo   3. Try running Command Prompt as Administrator
    echo   4. Check if port 11434 is available (default Ollama port)
    echo.
) else (
    echo   ✓ Model list accessible
)
echo.

REM Test 3: Simple inference test
echo [Test 3/4] Testing basic model inference...
echo This may take 10-30 seconds on first run...
echo.
echo Test | ollama run llama3.1:8b-instruct-q4_K_M >nul 2>&1
if errorlevel 1 (
    echo   ❌ FAILED: Model inference not working
    echo.
    echo   This is the most common issue. Possible causes:
    echo   1. Model not fully downloaded - try: ollama pull llama3.1:8b-instruct-q4_K_M
    echo   2. Corrupted model - try: ollama rm llama3.1:8b-instruct-q4_K_M then pull again
    echo   3. Insufficient RAM - need at least 8GB available for this model
    echo   4. Windows Defender real-time protection blocking model access
    echo   5. Ollama process needs restart - close and reopen Ollama app
    echo.
    echo   Advanced troubleshooting:
    echo   - Check Ollama logs: %%LOCALAPPDATA%%\Ollama\logs\
    echo   - Try smaller model: ollama run llama3.2:1b
    echo   - Verify model files: dir %%USERPROFILE%%\.ollama\models\
    echo.
) else (
    echo   ✓ Model inference working!
)
echo.

REM Test 4: Connection test
echo [Test 4/4] Testing HTTP connection to Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  WARNING: Direct HTTP connection failed
    echo   This may indicate port conflicts or firewall issues.
    echo.
    echo   Troubleshooting steps:
    echo   1. Check if another application is using port 11434
    echo   2. Try: netstat -ano ^| findstr "11434"
    echo   3. Configure firewall to allow Ollama connections
    echo.
) else (
    echo   ✓ HTTP connection working
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start MailMind:
echo   1. Open a NEW Command Prompt/PowerShell (to load environment variables)
echo   2. cd %CD%
echo   3. python main.py
echo.
echo NOTE: If you configured CPU mode, you MUST restart your terminal for changes to take effect!
echo.
echo If any diagnostic tests failed above, please resolve those issues before running MailMind.
echo You can run this setup script again to re-test after making changes.
echo.
pause
