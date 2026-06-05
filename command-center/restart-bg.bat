@echo off
REM ============================================================================
REM CC self-restart relauncher.
REM
REM Launched by the transient "DuberyMNL-CC-Restart" one-time scheduled task that
REM /api/restart creates. Running under Task Scheduler (not as a child of the
REM exiting CC process) is what lets it survive CC's own shutdown.
REM
REM Flow: wait for the outgoing CC to release :8090, give the canonical task a
REM moment to go Running->Ready, then re-run the canonical DuberyMNL-CommandCenter
REM task so CC comes back exactly as the system normally starts it (Session 0,
REM task-owned). Finally delete this transient task so it doesn't linger.
REM ============================================================================
setlocal enabledelayedexpansion

set /a tries=0
:wait
timeout /t 1 /nobreak >nul
set /a tries+=1
netstat -ano | findstr "LISTENING" | findstr ":8090" >nul
if !errorlevel! equ 0 if !tries! lss 20 goto wait

REM Buffer so the canonical task transitions out of "Running" before we re-run it.
timeout /t 2 /nobreak >nul

schtasks /run /tn "DuberyMNL-CommandCenter" >nul 2>&1
schtasks /delete /tn "DuberyMNL-CC-Restart" /f >nul 2>&1
