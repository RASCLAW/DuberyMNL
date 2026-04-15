@echo off
REM Auto-start DuberyMNL chatbot Flask server. Called by Task Scheduler at logon.
REM Logs to .tmp/cloud-run-server.log (appended, rotates manually if it gets big).
REM PYTHONIOENCODING forces UTF-8 stdout/stderr so print() doesn't crash on
REM customer emoji or Filipino characters (session 123 cp1252 incident).
set PYTHONIOENCODING=utf-8
cd /d C:\Users\RAS\projects\DuberyMNL\cloud-run
if not exist C:\Users\RAS\projects\DuberyMNL\.tmp mkdir C:\Users\RAS\projects\DuberyMNL\.tmp
python messenger_webhook.py >> C:\Users\RAS\projects\DuberyMNL\.tmp\cloud-run-server.log 2>&1
