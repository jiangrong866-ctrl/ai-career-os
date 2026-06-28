import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


heartbeat = read_json(STATE / "daemon_heartbeat.json", {})
system_state = read_json(STATE / "system_state.json", {})

ok = True
reasons = []
if not heartbeat:
    ok = False
    reasons.append("missing heartbeat")
else:
    try:
        heartbeat_time = dt.datetime.fromisoformat(heartbeat["time"])
        if (dt.datetime.now() - heartbeat_time).total_seconds() > 900:
            ok = False
            reasons.append("heartbeat older than 15 minutes")
    except Exception:
        ok = False
        reasons.append("invalid heartbeat")

if system_state.get("current_stage") not in (None, "idle"):
    reasons.append(f"stage not idle: {system_state.get('current_stage')}")

print(json.dumps({"ok": ok, "reasons": reasons}, indent=2))
raise SystemExit(0 if ok else 1)

