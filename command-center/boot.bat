@echo off
REM DuberyMNL Command Center launcher. Wire to Task Scheduler at-logon.
cd /d C:\Users\RAS\projects\DuberyMNL
chcp 65001 >NUL
python command-center\app.py
