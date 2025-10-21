@echo off
REM Aggressive Ollama troubleshooting and repair script
echo ========================================
echo Ollama Repair Tool
echo ========================================
echo.

echo PROBLEM: Model inference hanging even with plenty of RAM (10.87 GB)
echo This suggests Ollama might need to be reset or reconfigured.
echo.

echo [Step 1/6] Checking if model is fully downloaded...
ollama list | findstr "llama3.2:1b"
if errorlevel 1 (
    echo Model NOT found! Downloading now...
    ollama pull llama3.2:1b
    if errorlevel 1 (
        echo ERROR: Failed to download model!
        pause
        exit /b 1
    )
) else (
    echo Model found in list.
)
echo.

echo [Step 2/6] Stopping any hung Ollama processes...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul
echo.

echo [Step 3/6] Checking Ollama logs for errors...
echo Recent log entries:
if exist "%LOCALAPPDATA%\Ollama\logs\server.log" (
    powershell -Command "Get-Content '%LOCALAPPDATA%\Ollama\logs\server.log' -Tail 20"
) else (
    echo No log file found at %LOCALAPPDATA%\Ollama\logs\server.log
)
echo.
pause

echo [Step 4/6] Restarting Ollama service...
echo Please manually start Ollama application now if it's not running.
echo Look for the Ollama icon in your system tray.
timeout /t 5
echo.

echo [Step 5/6] Verifying Ollama is responsive...
ollama ps
if errorlevel 1 (
    echo ERROR: Ollama still not responding!
    echo Please ensure Ollama application is running.
    pause
    exit /b 1
)
echo.

echo [Step 6/6] Testing with a VERY simple prompt (5 second timeout)...
echo We'll use PowerShell to add a timeout to prevent infinite hangs.
echo.

powershell -Command "$job = Start-Job -ScriptBlock { echo 'hi' | ollama run llama3.2:1b 2>&1 }; Wait-Job -Job $job -Timeout 30; if ($job.State -eq 'Running') { Stop-Job -Job $job; Remove-Job -Job $job; Write-Host 'TIMEOUT: Model took longer than 30 seconds' -ForegroundColor Red; exit 1 } else { Receive-Job -Job $job; Remove-Job -Job $job }"

if errorlevel 1 (
    echo.
    echo ========================================
    echo DIAGNOSIS: Model inference timing out
    echo ========================================
    echo.
    echo Possible causes:
    echo 1. CPU is too slow (Ollama uses CPU heavily on first load)
    echo 2. Antivirus/Windows Defender blocking Ollama file access
    echo 3. Corrupted model files
    echo 4. Ollama needs reinstallation
    echo.
    echo RECOMMENDED FIXES:
    echo.
    echo Option 1 - Disable real-time protection temporarily:
    echo   - Open Windows Security
    echo   - Go to Virus and threat protection
    echo   - Manage settings
    echo   - Turn off Real-time protection (temporarily)
    echo   - Try running setup.bat again
    echo.
    echo Option 2 - Reinstall the model:
    echo   ollama rm llama3.2:1b
    echo   ollama pull llama3.2:1b
    echo.
    echo Option 3 - Check if your system meets minimum requirements:
    echo   - CPU: 2+ cores recommended
    echo   - First inference can take 1-2 minutes on slower CPUs
    echo.
    echo Option 4 - Skip Ollama diagnostics in setup:
    echo   - Run setup.bat and choose "N" to skip inference test
    echo   - MailMind might still work even if this diagnostic fails
    echo.
) else (
    echo.
    echo ========================================
    echo SUCCESS: Model is working!
    echo ========================================
    echo.
    echo If you saw a response above, Ollama is functioning properly.
    echo The hang in setup.bat was likely just slow first-time loading.
    echo.
    echo You can now run: python main.py
    echo.
)

pause
