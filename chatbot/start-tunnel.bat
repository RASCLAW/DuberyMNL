@echo off
REM Auto-start Cloudflare tunnel for chatbot.duberymnl.com. Called by Task Scheduler at logon.
REM Logs to .tmp/cloudflared.log (appended).
if not exist C:\Users\RAS\projects\DuberyMNL\.tmp mkdir C:\Users\RAS\projects\DuberyMNL\.tmp
call C:\Users\RAS\projects\DuberyMNL\tools\rotate-logs.bat "C:\Users\RAS\projects\DuberyMNL\.tmp\cloudflared.log"
C:\Users\RAS\bin\cloudflared.exe tunnel run dubery-chatbot >> C:\Users\RAS\projects\DuberyMNL\.tmp\cloudflared.log 2>&1
