@echo off
REM DuberyMNL Command Center launcher. Wire to Task Scheduler at-logon.
cd /d C:\Users\RAS\projects\DuberyMNL
chcp 65001 >NUL
"C:\Users\RAS\AppData\Local\Programs\Python\Python312\python.exe" command-center\app.py
