@echo off
REM Check if Ollama API is responding at all
echo ========================================
echo Ollama API Health Check
echo ========================================
echo.

echo [Test 1] Checking if Ollama service is running...
curl -s http://localhost:11434/api/tags 2>nul
if errorlevel 1 (
    echo FAILED: Cannot connect to Ollama API on port 11434
    echo.
    echo This means Ollama is either:
    echo   1. Not installed properly
    echo   2. Not running
    echo   3. Running on a different port
    echo   4. Blocked by firewall
    echo.
    goto ollama_not_working
) else (
    echo SUCCESS: Ollama API is responding!
)
echo.

echo [Test 2] Checking Ollama version...
ollama --version
echo.

echo [Test 3] Checking running models...
curl -s http://localhost:11434/api/ps
echo.

echo [Test 4] Listing available models...
curl -s http://localhost:11434/api/tags
echo.

echo ========================================
echo API is responding but inference hangs
echo ========================================
echo.
echo This suggests the model loading/inference is the problem, not Ollama itself.
echo.
goto check_alternatives

:ollama_not_working
echo ========================================
echo Ollama API Not Responding
echo ========================================
echo.
echo RECOMMENDED ACTIONS:
echo.
echo 1. Check if Ollama is running:
echo    - Look for Ollama icon in system tray
echo    - If not found, launch Ollama application
echo.
echo 2. Reinstall Ollama:
echo    - Download from: https://ollama.com/download
echo    - Uninstall current version first
echo    - Restart computer after reinstall
echo.
echo 3. Check port 11434:
echo    netstat -ano | findstr "11434"
echo    (If another process is using this port, Ollama won't work)
echo.

:check_alternatives
echo.
echo ========================================
echo WORKAROUND: Skip Ollama for now
echo ========================================
echo.
echo Since Ollama inference is timing out, you have options:
echo.
echo Option A: Use MailMind without AI features (email management only)
echo   - MailMind can still organize emails
echo   - AI features will be disabled
echo.
echo Option B: Wait and try again later
echo   - Sometimes first inference takes 2-5 minutes on slow systems
echo   - Let it run for 5 full minutes without interrupting
echo.
echo Option C: Try a different Ollama model
echo   - Current model: llama3.2:1b
echo   - Try: qwen2.5:0.5b (even smaller - 0.5B parameters)
echo   - Download: ollama pull qwen2.5:0.5b
echo.
echo Option D: Use cloud API instead (requires API key)
echo   - OpenAI API
echo   - Anthropic Claude API
echo   - (Not implemented yet in MailMind)
echo.
pause
