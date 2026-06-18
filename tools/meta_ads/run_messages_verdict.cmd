@echo off
REM One-shot runner for the Messages-vs-Traffic FD verdict (Task Scheduler, 2026-06-23 21:00).
cd /d c:\Users\RAS\projects\DuberyMNL
"C:\Users\RAS\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 tools\meta_ads\messages_vs_traffic_verdict.py >> .tmp\messages_verdict.log 2>&1
