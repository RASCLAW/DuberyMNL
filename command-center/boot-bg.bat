@echo off
REM DuberyMNL Command Center -- background launcher (no console).
REM Uses pythonw.exe so no cmd window appears. Logs go to .tmp\cc.log.
REM For visible/debugging launches, use boot.bat instead.
cd /d C:\Users\RAS\projects\DuberyMNL
if not exist .tmp mkdir .tmp
call C:\Users\RAS\projects\DuberyMNL\tools\rotate-logs.bat "C:\Users\RAS\projects\DuberyMNL\.tmp\cc.log"
call C:\Users\RAS\projects\DuberyMNL\tools\rotate-logs.bat "C:\Users\RAS\projects\DuberyMNL\.tmp\content-gen.log"
"C:\Users\RAS\AppData\Local\Programs\Python\Python312\pythonw.exe" command-center\app.py >> .tmp\cc.log 2>&1
