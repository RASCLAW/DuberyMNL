@echo off
REM Start the chatbot monitor (replaces start-chatbot.bat for Task Scheduler).
REM monitor.py owns the chatbot subprocess -- do not run start-chatbot.bat alongside this.
REM Logs: .tmp/monitor.log (monitor) + .tmp/chatbot-server.log (chatbot stdout)
set PYTHONIOENCODING=utf-8
cd /d C:\Users\RAS\projects\DuberyMNL\chatbot
if not exist C:\Users\RAS\projects\DuberyMNL\.tmp mkdir C:\Users\RAS\projects\DuberyMNL\.tmp
python monitor.py >> C:\Users\RAS\projects\DuberyMNL\.tmp\monitor.log 2>&1
