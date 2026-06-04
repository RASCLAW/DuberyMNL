@echo off
REM Start the chatbot monitor (replaces start-chatbot.bat for Task Scheduler).
REM monitor.py owns the chatbot subprocess -- do not run start-chatbot.bat alongside this.
REM Logs: .tmp/monitor.log (monitor) + .tmp/chatbot-server.log (chatbot stdout)
set PYTHONIOENCODING=utf-8
cd /d C:\Users\RAS\projects\DuberyMNL\chatbot
if not exist C:\Users\RAS\projects\DuberyMNL\.tmp mkdir C:\Users\RAS\projects\DuberyMNL\.tmp
call C:\Users\RAS\projects\DuberyMNL\tools\rotate-logs.bat "C:\Users\RAS\projects\DuberyMNL\.tmp\monitor.log"
call C:\Users\RAS\projects\DuberyMNL\tools\rotate-logs.bat "C:\Users\RAS\projects\DuberyMNL\.tmp\chatbot-server.log"
"C:\Users\RAS\AppData\Local\Programs\Python\Python312\python.exe" monitor.py
