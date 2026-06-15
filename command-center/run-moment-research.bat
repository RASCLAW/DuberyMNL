@echo off
REM DuberyMNL Moment Scout — daily content-calendar researcher.
REM Runs the /moment-research skill headless and logs output.
REM Wire to Task Scheduler (daily ~8 AM PHT) the same way as DuberyMNL-Chatbot/-Tunnel,
REM OR run manually to test. Needs the local .env + token.json (Sheets + Telegram creds).

set PYTHONIOENCODING=utf-8
cd /d C:\Users\RAS\projects\DuberyMNL

echo ==== moment-research run %DATE% %TIME% ==== >> .tmp\moment-research.log

REM Headless Claude Code: invoke the skill non-interactively, unattended.
REM --dangerously-skip-permissions so the scheduled run doesn't hang on prompts
REM (trusted local automation writing to its own Sheet + private TG channel).
claude -p "Use the moment-research skill to run today's DuberyMNL Moment Scout end-to-end: research upcoming PH moments (holidays, sports/events, viral/weather), score them, write suggestions to the content_calendar Sheet, and send the Telegram digest." --dangerously-skip-permissions >> .tmp\moment-research.log 2>&1

echo ==== done %DATE% %TIME% ==== >> .tmp\moment-research.log
