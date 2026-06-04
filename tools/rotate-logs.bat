@echo off
REM ── DuberyMNL log rotation ────────────────────────────────────────────────
REM Rotate .tmp service logs past a 10 MB cap, keeping 1 backup (<log> -> <log>.1).
REM Called by each service launcher BEFORE it starts (the file has no open handle
REM at start, so the move is safe and never disrupts a running service). Also
REM runnable by hand to rotate everything now.
REM
REM Usage:
REM   rotate-logs.bat               rotate ALL known logs that are over the cap
REM   rotate-logs.bat "<logpath>"   rotate just that one log if it is over the cap
REM
REM Note: a live log held open by a running service can't be moved (Windows
REM sharing lock) -- that's by design. Rotation lands at the next service start.
setlocal
set "TMP_DIR=C:\Users\RAS\projects\DuberyMNL\.tmp"
set "CAP=10485760"

if not "%~1"=="" (
    call :rotate "%~1"
    goto :done
)
for %%L in (cc.log cloudflared.log chatbot-server.log monitor.log content-gen.log stock_cron.log) do call :rotate "%TMP_DIR%\%%L"

:done
endlocal
exit /b 0

:rotate
if not exist "%~1" exit /b 0
for %%I in ("%~1") do if %%~zI GTR %CAP% (
    if exist "%~1.1" del "%~1.1"
    move /Y "%~1" "%~1.1" >nul
    echo [rotate-logs] rotated %~1 to %~1.1
)
exit /b 0
