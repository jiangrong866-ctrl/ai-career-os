import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


state = read_json(STATE / "system_state.json", {})
heartbeat = read_json(STATE / "daemon_heartbeat.json", {})
now = dt.datetime.now()
last_success = state.get("last_successful_run")
last_heartbeat = heartbeat.get("time")

status = {
    "ok": True,
    "last_successful_run": last_success,
    "last_heartbeat": last_heartbeat,
    "issues": [],
}

if last_success:
    age = (now - dt.datetime.fromisoformat(last_success)).total_seconds()
    if age > 36 * 3600:
        status["ok"] = False
        status["issues"].append("last successful run older than 36h")
else:
    status["ok"] = False
    status["issues"].append("no successful run recorded")

if heartbeat:
    age = (now - dt.datetime.fromisoformat(last_heartbeat)).total_seconds()
    if age > 3600:
        status["issues"].append("heartbeat older than 1h")

(STATE / "uptime_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
print(json.dumps(status, indent=2))
raise SystemExit(0 if status["ok"] else 1)

