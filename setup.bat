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
if errorlevel 2 (
    echo.
    echo Configuring Ollama for CPU mode (recommended for most users)...
    setx OLLAMA_NUM_GPU "0" >nul
    setx CUDA_VISIBLE_DEVICES "" >nul
    echo.
    echo CPU mode configured! This will avoid GPU detection delays.
    echo Performance: ~10-30 tokens/second (sufficient for email processing)
) else (
    echo.
    echo GPU mode enabled. If you experience delays, run this script again and select 'N'.
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
    if errorlevel 2 (
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
    if errorlevel 2 (
        echo.
        echo Skipping model download. You can download it later with:
        echo   ollama pull llama3.1:8b-instruct-q4_K_M
    ) else (
        ollama pull llama3.1:8b-instruct-q4_K_M
    )
) else (
    echo Model already installed!
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
pause
