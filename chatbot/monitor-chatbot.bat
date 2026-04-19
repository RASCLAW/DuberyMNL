@echo off
title DuberyMNL Chatbot Monitor
set PYTHONIOENCODING=utf-8
set LOGFILE=C:\Users\RAS\projects\DuberyMNL\.tmp\chatbot-server.log

cd /d C:\Users\RAS\projects\DuberyMNL

if not exist .tmp mkdir .tmp

REM Kill any existing chatbot process on port 8080
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080 "') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Start chatbot silently in background
echo Starting DuberyMNL chatbot...
start /B cmd /C "set PYTHONIOENCODING=utf-8 && cd /d C:\Users\RAS\projects\DuberyMNL\chatbot && python messenger_webhook.py >> %LOGFILE% 2>&1"

REM Wait for bot to come up
timeout /t 3 /nobreak >nul

REM Check status
curl -s http://localhost:8080/status >nul 2>&1
if %errorlevel%==0 (
    echo Bot is RUNNING on port 8080
) else (
    echo WARNING: Bot may not have started. Check log below.
)

echo.
echo ============================================================
echo  LIVE LOG -- chatbot-server.log
echo  Press Ctrl+C to stop monitoring (bot keeps running)
echo ============================================================
echo.

powershell -Command "Get-Content -Path '%LOGFILE%' -Wait -Tail 30"
