@echo off
REM Quick Ollama diagnostic script
echo ========================================
echo Ollama Diagnostic Tool
echo ========================================
echo.

echo [1/5] Checking if Ollama is running...
ollama ps
if errorlevel 1 (
    echo PROBLEM: Ollama service not responding
    echo Try: Restart the Ollama application
    pause
    exit /b 1
)
echo.

echo [2/5] Listing installed models...
ollama list
echo.

echo [3/5] Checking which model is configured...
if exist config\user_config.yaml (
    type config\user_config.yaml
) else (
    echo WARNING: user_config.yaml not found
)
echo.

echo [4/5] Testing model manually (you will see the output)...
echo This will show you exactly what happens when we try to run the model.
echo.
pause
echo.
echo Running: ollama run llama3.2:1b "Say hello in 3 words"
echo.
ollama run llama3.2:1b "Say hello in 3 words"
echo.

echo [5/5] Diagnostic complete!
echo.
echo If you saw a response above, Ollama is working fine.
echo If it hung or errored, we need to troubleshoot further.
echo.
pause
