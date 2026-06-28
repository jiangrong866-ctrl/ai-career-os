import datetime as dt
from pathlib import Path
from typing import Any


TASK_NAME = "AI Career OS v5"
RUN_TIME = "20:30"


def next_daily_run(now: dt.datetime | None = None) -> str:
    current = now or dt.datetime.now()
    hour, minute = [int(part) for part in RUN_TIME.split(":", 1)]
    candidate = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= current:
        candidate = candidate + dt.timedelta(days=1)
    return candidate.isoformat(timespec="seconds")


def task_summary(project_root: Path) -> dict[str, Any]:
    return {
        "task_name": TASK_NAME,
        "daily_trigger": RUN_TIME,
        "logon_trigger": True,
        "run_level": "Highest",
        "program": "python",
        "arguments": str(project_root / "scripts" / "run_v5.py"),
        "start_in": str(project_root),
        "cmd_entry": str(project_root / "run_v5.cmd"),
        "next_run": next_daily_run(),
    }
