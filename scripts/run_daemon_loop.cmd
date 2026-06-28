@echo off
cd /d D:\.codex专属工作间\ai-career-os
if not exist logs mkdir logs
python scripts\daemon_loop.py >> logs\daemon_stdout.log 2>> logs\daemon_stderr.log

