@echo off
cd /d D:\.codex专属工作间\ai-career-os
if not exist logs mkdir logs
python scripts\daily_loop.py >> logs\daily_loop.log 2>> logs\daily_loop_error.log
