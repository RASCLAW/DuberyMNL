@echo off
REM DuberyMNL hourly stock job: refresh orders from Sheets, then low-stock TG alert.
REM Registered as Task Scheduler task "DuberyMNL-StockAlert".
set PYTHONIOENCODING=utf-8
cd /d C:\Users\RAS\projects\DuberyMNL
call C:\Users\RAS\projects\DuberyMNL\tools\rotate-logs.bat "C:\Users\RAS\projects\DuberyMNL\.tmp\stock_cron.log"
python tools\orders\sync_orders.py  >> .tmp\stock_cron.log 2>&1
python tools\orders\stock_alert.py  >> .tmp\stock_cron.log 2>&1
