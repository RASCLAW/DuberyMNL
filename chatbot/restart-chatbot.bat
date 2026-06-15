@echo off
REM Restart the live DuberyMNL chatbot to load new code.
REM Kills EVERY process listening on :8085 first -- this is deliberate.
REM Stop-ScheduledTask only ends the instance the scheduler tracks and MISSES
REM orphaned processes (e.g. one started before the task was re-registered),
REM which causes a two-bots-on-one-port split-brain. Killing by port guarantees
REM a single clean instance. Then starts one fresh via the task.
echo Killing any process listening on :8085...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8085 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Write-Host ('  killing PID ' + $_); Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
timeout /t 2 >nul
echo Starting DuberyMNL-Chatbot...
powershell -NoProfile -Command "Start-ScheduledTask -TaskName 'DuberyMNL-Chatbot'"
echo Waiting for warmup...
timeout /t 9 >nul
curl -s -o nul -w "chatbot :8085 -> HTTP %%{http_code} (expect 200)\n" http://localhost:8085/status
echo If you saw "Access Denied" above, close this and re-run as Administrator.
